"""Credit guard for Gemini image generation (plan approved by the user 2026-10-02, after the overnight bursts).

What went wrong without it (all measured 2026-10-01/02):
  * the quota READING LAGS: it said 1,141 credits left when 96 were, because several runs were still in flight;
  * per-run credit totals are contaminated when runs overlap (each run reports the shared window);
  * a burst of six parallel generations returned nothing yet was charged (about 160 credits);
  * nothing stopped a wave from starting when the window could not pay for it.

So every `facecard.py gen` registers itself here before it generates anything:
  * at most `max_concurrent` generations run at once (default 4), the rest wait for a free slot;
  * the window must hold  (fresh reading - the reservations of the runs already in flight)  >=  (this run's images x per-image estimate) + margin (default 150);
    when it does not, the run WAITS until the window resets (reset time from the reading) instead of dying midway through a batch;
  * the registry is one small file per running process in .cache/inflight/ (dead processes are removed), so it works across separate terminals.

Per-image estimates are deliberately conservative (Flash 120, Pro 150 since 2026-10-08; it was 260): solo calls measured 20-110 and 60-90, but a window drains faster than the sum of
solo calls (text calls, synthetic references, uploads, charged no-image calls). Override in facecard.json  "credit_guard": {"max_concurrent", "margin", "per_image": {"flash","pro"}}
or with the environment variables FACECARD_GUARD_MAX / FACECARD_GUARD_MARGIN.
"""
from __future__ import annotations

import asyncio
import atexit
import contextlib
import ctypes
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INFLIGHT = ROOT / ".cache" / "inflight"
QUOTA_JSON = ROOT / ".cache" / "quota.json"
# per_image, re-measured 2026-10-08: medians of 103 image calls in run records 132 (Flash) and 148 (Pro); those readings include overlapping runs, so the
# 90th percentiles (326 / 412) are not used. A solo probe (tools/model_probe.py, no references) cost 33 and 38: both chat models hand the picture to
# the same image tool (imagen_default), so Pro no longer needs twice Flash's reservation (it was 260 when Pro was thought to draw with Nano Banana Pro).
DEFAULTS = {"max_concurrent": 4, "margin": 150, "per_image": {"flash": 120, "pro": 150}, "stale_minutes": 60}


class GuardRefused(Exception):
    """The guard would not let this run generate (waited past --wait-max, or --no-wait)."""


def pid_alive(pid: int) -> bool:
    """True while a process with this pid exists (Windows: OpenProcess + STILL_ACTIVE; elsewhere os.kill 0)."""
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))     # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259     # STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


@contextlib.contextmanager
def _registry_lock(wait: float = 30.0):
    """One process at a time checks the slots and registers, so two runs starting in the same second cannot both take the last slot."""
    INFLIGHT.mkdir(parents=True, exist_ok=True)
    lock = INFLIGHT / ".lock"
    t0 = time.time()
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            with contextlib.suppress(OSError):
                if time.time() - lock.stat().st_mtime > 30:      # a crashed holder's leftover
                    lock.unlink()
                    continue
            if time.time() - t0 > wait:
                raise TimeoutError("credit guard registry locked")
            time.sleep(0.2)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def list_inflight(stale_minutes: float = 60) -> list[dict]:
    """The generations running right now (files of dead or stale processes are deleted)."""
    out = []
    if not INFLIGHT.exists():
        return out
    for f in INFLIGHT.glob("*.json"):
        try:
            e = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        old = (time.time() - float(e.get("started", 0))) > stale_minutes * 60
        if old or not pid_alive(int(e.get("pid", 0))):
            with contextlib.suppress(OSError):
                f.unlink()
            continue
        out.append(e)
    return out


def reset_in_seconds() -> float | None:
    """Seconds until the 5-hour window resets, from the last reading in .cache/quota.json (None if unknown)."""
    try:
        q = json.loads(QUOTA_JSON.read_text(encoding="utf-8"))
        ra = q.get("reset_at") or (q.get("current_5h") or {}).get("reset_at")      # quota.json keeps it under current_5h (found 2026-10-09: this returned None, so wave.py --after-reset started at once)
        if not ra:
            return None
        t = datetime.fromisoformat(str(ra).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.astimezone()
        return (t - datetime.now(timezone.utc)).total_seconds()
    except Exception:
        return None


class Guard:
    def __init__(self, cfg: dict | None = None):
        c = dict(DEFAULTS)
        c.update(cfg or {})
        c["per_image"] = {**DEFAULTS["per_image"], **((cfg or {}).get("per_image") or {})}
        if os.environ.get("FACECARD_GUARD_MAX"):
            c["max_concurrent"] = int(os.environ["FACECARD_GUARD_MAX"])
        if os.environ.get("FACECARD_GUARD_MARGIN"):
            c["margin"] = int(os.environ["FACECARD_GUARD_MARGIN"])
        self.cfg = c
        self.file: Path | None = None
        self.reserve = 0

    def estimate(self, is_pro: bool, images: int) -> int:
        return int(images * self.cfg["per_image"]["pro" if is_pro else "flash"])

    async def acquire(self, *, is_pro: bool, images: int, label: str, refresh, wait_max: float = 21600.0, say=print) -> dict:
        """Block until a slot is free and the window can pay for this run; register the run. `refresh()` is an async callable returning the fresh credits left (or None).
        Returns {'reading', 'reserved_by_others', 'need'}; raises GuardRefused when `wait_max` seconds pass first."""
        need, margin, cap = self.estimate(is_pro, images), int(self.cfg["margin"]), int(self.cfg["max_concurrent"])
        t0, last_say, why = time.time(), 0.0, ""
        while True:
            reading = await refresh()
            with _registry_lock():
                others = [e for e in list_inflight(self.cfg["stale_minutes"]) if int(e.get("pid", -1)) != os.getpid()]
                reserved = sum(int(e.get("reserve", 0)) for e in others)
                slots_ok = len(others) < cap
                credits_ok = reading is None or (reading - reserved) >= need + margin
                if slots_ok and credits_ok:
                    self.reserve = need
                    INFLIGHT.mkdir(parents=True, exist_ok=True)
                    self.file = INFLIGHT / f"{os.getpid()}.json"
                    self.file.write_text(json.dumps({"pid": os.getpid(), "started": time.time(), "label": label, "images": images, "reserve": need,
                                                     "model": "pro" if is_pro else "flash"}), encoding="utf-8")
                    atexit.register(self.release)
                    say(f"[Guard] ok: window {reading} - reserved by {len(others)} other run(s) {reserved} >= need {need} + margin {margin}; slots {len(others) + 1}/{cap}")
                    return {"reading": reading, "reserved_by_others": reserved, "need": need}
                why = (f"all {cap} generation slots are taken ({len(others)} running)" if not slots_ok else
                       f"window {reading} - reserved by running generations {reserved} < need {need} + margin {margin}")
            waited = time.time() - t0
            if waited >= wait_max:
                raise GuardRefused(f"{why}; waited {waited:.0f} s (--wait-max {wait_max:.0f})")
            if time.time() - last_say > 120 or last_say == 0.0:
                eta = reset_in_seconds()
                say(f"[Guard] waiting: {why}" + (f"; the window resets in {eta / 60:.0f} min" if (eta is not None and eta > 0 and not credits_ok) else ""))
                last_say = time.time()
            await asyncio.sleep(30.0 if wait_max > 60 else min(5.0, wait_max))

    def release(self) -> None:
        if self.file is not None:
            with contextlib.suppress(OSError):
                self.file.unlink()
            self.file = None
