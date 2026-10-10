"""The night queue of the local system: several Qwen-Image-2.1 pictures, one after another, while the user sleeps (2026-10-09).

The user, 2026-10-09: "a parallel system of dedicated overnight runs with multiple image generations ... using the Qwen local image model";
"the device will likely take a lot of time to generate, it is still fine. We can use this for overnight runs." Each picture is made by
local_gen.py. This file decides WHEN: inside the night window, on AC power, with enough free memory, never two at once, and it stops a run
that makes no progress. It never touches the Gemini system (no .cache\\inflight, nothing under outputs\\).

Before the picture it makes room (tools/room.py), as the user allowed on 2026-10-10: "Apart from VS Code, which has multiple tabs of
Claude Code running, everything else can be closed. Even inside VS Code, ideal Claude Code tabs can be closed as well, and only active,
running ones can be kept". It waits until he is away, closes, and puts back what he asked for: Wispr Flow, opencode and Edge when he is
back (his first input after 06:00), the job bots when the picture ends.

    .venv\\Scripts\\python.exe tools\\overnight.py plan        # what tonight would run, with predicted times
    .venv\\Scripts\\python.exe tools\\overnight.py room-plan   # what making room would close and keep right now; changes nothing
    .venv\\Scripts\\python.exe tools\\overnight.py run         # the night (the 04:00 task); --now ignores the start time
    .venv\\Scripts\\python.exe tools\\overnight.py status      # the queue, the room, the running picture's progress, the last results
    .venv\\Scripts\\python.exe tools\\overnight.py summary     # the morning page D:\\FacecardLocal\\summary\\<date>.html
    .venv\\Scripts\\python.exe tools\\overnight.py register    # the hidden tasks facecard-local-overnight (04:00) and facecard-local-restore
    schtasks /Run /TN facecard-local-restore                 # puts back a room a crashed night left (not from a Claude Code tab)

Queue (D:\\FacecardLocal\\queue.json, schema facecard.local_queue/1):
    {"schema": "facecard.local_queue/1", "window": {"start": "04:00", "last_start": "06:00", "hard_stop": "11:00"},
     "jobs": [{"id": "pin06-v2", "recipe": "pin_783485666539777055@v2", "seeds": [1], "W": 768, "H": 960, "steps": 25,
               "refs_cap": 589824, "cache_type": "q8_0", "threads": 4, "enabled": true}]}
A picture is done once per (job id, seed, settings); state.json keeps that. Measured times and memory come from earlier local_run.json files
of the same shape (size, steps, reference cap, cache type, threads).
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import io
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import local_gen as L  # noqa: E402
import paths  # noqa: E402
import provenance as P  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import room as RM  # noqa: E402

TASK = "facecard-local-overnight"
RESTORE_TASK = "facecard-local-restore"
RUNHIDDEN = Path(r"C:\Users\Admin\bin\runhidden\runhidden.exe")
ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
MEM_MARGIN = 1.15
MEM_WAIT_S, MEM_POLL_S = 1800, 60


def home() -> Path:
    return paths.local_dir()


def log(msg: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    try:
        with (home() / "overnight.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        fallback = Path(r"C:\LocalGen\logs\overnight_fallback.log")
        fallback.parent.mkdir(parents=True, exist_ok=True)
        with fallback.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def read(path: Path, default):
    return P.read_json(path, default)


def queue() -> dict:
    q = read(home() / "queue.json", None)
    if not q:
        raise SystemExit(f"no queue at {home() / 'queue.json'}")
    if q.get("schema") != "facecard.local_queue/1":
        raise SystemExit("queue.json has no schema facecard.local_queue/1")
    return q


def state() -> dict:
    return read(home() / "state.json", {"schema": "facecard.local_state/1", "done": {}, "nights": []})


def save_state(st: dict) -> None:
    L.save_json(home() / "state.json", st, tries=10, say=log)      # never crashes the night (see L.save_json)


def shape_of(job: dict) -> dict:
    s = {k: job[k] for k in ("W", "H", "steps", "refs_cap", "cache_type", "threads")}
    s.update({"cfg": job.get("cfg", 1.0), "engine": job.get("engine", "cpu"), "backend": job.get("backend"), "te": job.get("te", "int8")})
    return s


def done_key(job: dict, seed: int) -> str:
    return f"{job['id']}|{seed}|" + P.sha256_bytes(P.canonical_json({**shape_of(job), "recipe": job["recipe"], "release": L.SDCPP_RELEASE,
                                                                       "models": {k: v[1] for k, v in L.MODEL_FILES.items()}}))[:12]


# ------------------------------------------------------------------------------------------------------------------ measured values
def runs() -> list[tuple[Path, dict]]:
    out = []
    for f in sorted((home() / "runs").glob("*/local_run.json")):
        r = read(f, None)
        if r and not r.get("dry_run"):
            out.append((f.parent, r))
    return out


def from_progress(run: Path) -> dict | None:
    """The attempt of a run whose supervisor died before recording it (both runs of 2026-10-10): its progress.json still holds the step
    times, the text encoder's own timing and the memory peaks."""
    g = read(run / "progress.json", None)
    if not g:
        return None
    secs, mem = g.get("step_secs") or [], g.get("memory") or {}
    return {"peak_working_set_gb": mem.get("peak_ws_gb"), "peak_commit_gb": mem.get("peak_commit_gb"), "own_timings_s": g.get("own_timings_s") or {},
            "phases_s": {}, "first_step_s": g.get("first_step_s"), "s_per_step_median": sorted(secs)[len(secs) // 2] if secs else None}


def measured(job: dict) -> dict:
    """Times and memory of earlier local runs: the same shape first; peak memory from any run with the same size and reference cap."""
    sh = shape_of(job)
    m: dict = {}
    for run, r in runs():
        j = r["job"]
        same_mem = all(j.get(k) == sh[k] for k in ("W", "H", "refs_cap", "cache_type")) and j.get("engine", "cpu") == sh["engine"] \
            and j.get("backend") == sh["backend"]
        same_speed = same_mem and j.get("threads") == sh["threads"] and j.get("cfg", 1.0) == sh["cfg"]
        attempts = [a for img in r.get("images", []) for a in img.get("attempts", [])]
        if not attempts:
            attempts = [a for a in [from_progress(run)] if a]
        for img in [{"attempts": attempts}]:
            for a in img.get("attempts", []):
                if same_mem:
                    m["peak_ws_gb"] = max(m.get("peak_ws_gb", 0), a.get("peak_working_set_gb") or 0)
                    m["peak_commit_gb"] = max(m.get("peak_commit_gb", 0), a.get("peak_commit_gb") or 0)
                if same_speed:
                    ph, own = a.get("phases_s") or {}, a.get("own_timings_s") or {}
                    for k in ("load", "ref_encode", "condition", "decode"):
                        v = own.get(k) or (ph.get(k) if k == "load" else None)
                        if v:
                            m[f"{k}_s"] = max(m.get(f"{k}_s", 0), v)
                    if a.get("first_step_s"):
                        m["first_step_s"] = max(m.get("first_step_s", 0), a["first_step_s"])
                    if a.get("s_per_step_median"):
                        m["s_per_step"] = max(m.get("s_per_step", 0), a["s_per_step_median"])
    return m


def predicted_s(job: dict, m: dict) -> float | None:
    """load + references + text encoder + first step (it builds the reference cache) + the other steps + decode, from runs of this shape."""
    if not m.get("s_per_step") or not m.get("first_step_s"):
        return None
    return (m.get("load_s", 0) + m.get("ref_encode_s", 0) + m.get("condition_s", 0) + m["first_step_s"]
            + (job["steps"] - 1) * m["s_per_step"] + m.get("decode_s", 0))


# ------------------------------------------------------------------------------------------------------------------------ the checks
def at(hhmm: str, now: datetime) -> datetime:
    """The next occurrence of hh:mm that belongs to this night (a time before noon belongs to the morning after the evening start)."""
    h, mi = map(int, hhmm.split(":"))
    t = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    if h < 12 and now.hour >= 12:
        t += timedelta(days=1)
    return t


def top_memory_users(n: int = 6) -> str:
    try:
        return ", ".join(f"{name} {gb:.1f} GB" for name, gb in L.top_memory_users(n))
    except Exception as e:
        return f"(could not list: {type(e).__name__}: {e})"


LLAMA_TASK = "llama-router"
UNMEASURED_NEED_GB = 6.0    # free RAM / commit headroom before a shape is measured: the 4.4 GB diffusion model resident + buffers (2026-10-09)


def _ps(script: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=120,
                       creationflags=L.CREATE_NO_WINDOW)
    return (r.stdout or r.stderr).strip()


def router_marker() -> Path:
    return home() / "llama_router_paused.json"


def _run(*argv: str) -> tuple[int, str]:
    """A native command, hidden. schtasks/taskkill, not PowerShell: under memory pressure PowerShell took over 2 minutes just to start
    (2026-10-09), and a resume that times out would leave llama-router off."""
    try:
        r = subprocess.run(list(argv), capture_output=True, text=True, timeout=300, creationflags=L.CREATE_NO_WINDOW)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timed out"


def router_state() -> str | None:
    """'Ready', 'Running', 'Disabled' ... (schtasks' status column), or None when the task does not exist."""
    rc, out = _run("schtasks", "/Query", "/TN", LLAMA_TASK, "/FO", "CSV", "/NH")
    if rc != 0 or not out:
        return None
    return out.splitlines()[-1].split('","')[-1].strip('"')


def pause_llama_router(by: str = "overnight") -> str:
    """The user, 2026-10-09: "Pause llama-router during Qwen runs" (the local-LLM router for Pi held 7.5 GB and starved the trial).
    The task restarts itself on failure every minute (measured: a plain stop came back 63 s later), so it is DISABLED first, then ended,
    then every llama-server.exe (the router and its model child; nothing else runs llama-server on this PC) is ended. A marker file records
    the pause, so resume_llama_router() always undoes it, also after a crash (status and run call resume_if_stale).
    Returns 'paused', 'idle' or 'absent'."""
    state = router_state()
    if state is None:
        return "absent"
    _rc, listing = _run("tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/NH")
    running = "llama-server.exe" in listing
    if state != "Running" and not running:
        return "idle"
    L.save_json(router_marker(), {"paused": datetime.now().isoformat(timespec="seconds"), "by": by, **RM.me()}, tries=5)
    _run("schtasks", "/Change", "/TN", LLAMA_TASK, "/DISABLE")
    _run("schtasks", "/End", "/TN", LLAMA_TASK)
    _run("taskkill", "/F", "/T", "/IM", "llama-server.exe")
    return "paused"


def resume_llama_router() -> str:
    """Enable and start the task, check that it runs (one retry), and only then drop the marker."""
    for _attempt in range(2):
        _run("schtasks", "/Change", "/TN", LLAMA_TASK, "/ENABLE")
        _run("schtasks", "/Run", "/TN", LLAMA_TASK)
        time.sleep(5)
        state = router_state()
        if state == "Running":
            router_marker().unlink(missing_ok=True)
            return state
    return f"NOT running ({router_state()}): start it with schtasks /Change /TN {LLAMA_TASK} /ENABLE and schtasks /Run /TN {LLAMA_TASK}"


def resume_if_stale() -> str | None:
    """A pause whose process is gone (a crash, a reboot) is undone here: llama-router must never stay off by accident."""
    m = read(router_marker(), None)
    if m and not holder_alive(m):
        return resume_llama_router()
    return None


def holder_alive(rec: dict) -> bool:
    """The process a lock or marker names is alive only with the same creation time: pids are reused, and after a reboot a reused pid
    would make a dead night's lock look live. Records written before 2026-10-10 hold only a pid."""
    if rec.get("ctime") is not None:
        return RM.alive(rec.get("pid"), rec.get("ctime"))
    return parent_alive(int(rec.get("pid") or 0))


RAM_FLOOR_GB = 3.5          # the least free RAM to start with: the 2026-10-09 trial started at 3.55 GB and ran at 2.5 cores


def stop_idle_helpers() -> list[str]:
    """The user, 2026-10-09: "make space on your own by smartly tracking what processes the ongoing claudecode tasks require and eliminating
    others". The DaVinci and Kinocut MCP servers of the open Claude Code sessions (a session that needs them reconnects with /mcp). Found
    with psutil and ended by (pid, creation time): PowerShell took minutes just to start under memory pressure."""
    snap = RM.snapshot()
    kids = RM.children(snap)
    stopped = []
    for r in RM.roots(snap, lambda p: any(h in RM.lc(p, "cmd") or h == RM.lc(p, "name") for h in RM.MCP_HELPERS)):
        stopped += RM.kill_tree(RM.tree(r, snap, kids))["ended"]
    return stopped


ROOM_MARGIN_GB = 1.5


def wait_for_room_memory(m: dict, wait_s: float = MEM_WAIT_S) -> bool:
    """Start once the picture's measured peak + 1.5 GB is free, taking the larger of peak commit and peak working set (on the iGPU its
    graphics memory is ordinary RAM: 7.45 GB commit against a 5.6 GB working set, 2026-10-10). After wait_s it starts anyway with
    RAM_FLOOR_GB free: the room is made, and putting everything back would only waste the night (with --mmap the model's pages come from
    its file, so a short machine pages instead of failing). Commit headroom must always cover 1.15 x the peak commit: Windows refusing
    memory crashes Claude Code and others (0xC0000409)."""
    target = max(m.get("peak_commit_gb") or 0, m.get("peak_ws_gb") or 0, UNMEASURED_NEED_GB) + ROOM_MARGIN_GB
    need_commit = MEM_MARGIN * m["peak_commit_gb"] if m.get("peak_commit_gb") else UNMEASURED_NEED_GB
    t0, said, helpers_done = time.time(), 0.0, False
    while True:
        ms = L.memory_status()
        commit_ok = ms["commit_headroom_gb"] >= need_commit
        if commit_ok and ms["avail_gb"] >= target:
            return True
        if not helpers_done:
            helpers_done = True
            gone = stop_idle_helpers()
            if gone:
                log(f"memory: stopped {len(gone)} idle video-editing MCP helper process(es)")
                continue
        if time.time() - t0 > wait_s:
            if commit_ok and ms["avail_gb"] >= RAM_FLOOR_GB:
                log(f"memory: {ms['avail_gb']} GB free after {wait_s / 60:.0f} min (target {target:.1f} GB); starting with it")
                return True
            log(f"memory: still short after {wait_s / 60:.0f} min (free {ms['avail_gb']} GB, commit headroom {ms['commit_headroom_gb']} GB;"
                f" need {RAM_FLOOR_GB} / {need_commit:.1f} GB); top users: {top_memory_users()}")
            return False
        if time.time() - said > 600:
            log(f"memory: waiting for {target:.1f} GB free (now {ms['avail_gb']} GB, commit headroom {ms['commit_headroom_gb']} GB);"
                f" top users: {top_memory_users()}")
            said = time.time()
        time.sleep(MEM_POLL_S)


def parent_alive(ppid: int) -> bool:
    h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, ppid)          # SYNCHRONIZE
    if not h:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(h, 0) == 0x102   # WAIT_TIMEOUT: still running
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


class Guard(threading.Thread):
    """While a picture is made: stop it when AC power is lost, or when the task that started this process is gone. The hard stop applies
    only when the queue's window says finish_started: false. By default a started picture always finishes (the user, 2026-10-10: "just
    because my own machine is not capable of generating quickly doesn't mean you start making compromises": a full-quality picture takes
    about 10 h on the iGPU, longer than a night)."""

    def __init__(self, hard_stop: datetime | None, ppid: int | None):
        super().__init__(daemon=True)
        self.stop = threading.Event()
        self.stop.reason = None
        self.hard_stop = hard_stop
        self.parent = {"pid": ppid, "ctime": RM.ctime_of(ppid)} if ppid else None
        self.done = threading.Event()

    def run(self):
        while not self.done.wait(30):
            reason = None
            if L.on_ac_power() is False:
                reason = "AC power lost"
            elif self.hard_stop and datetime.now() >= self.hard_stop:
                reason = f"hard stop {self.hard_stop:%H:%M}"
            elif self.parent and not holder_alive(self.parent):
                reason = "the scheduled task that started the night is gone"
            if reason:
                self.stop.reason = reason
                self.stop.set()
                return


# ------------------------------------------------------------------------------------------------------------------------- commands
def lock_holder(lk: Path) -> dict:
    """{pid, ctime} from the lock; a lock from before 2026-10-10 holds a bare pid."""
    try:
        text = lk.read_text().strip()
    except OSError:
        return {}
    try:
        return json.loads(text) if text.startswith("{") else {"pid": int(text or 0)}
    except ValueError:
        return {}


def lock_or_exit() -> Path:
    lk = home() / "overnight.lock"
    try:
        fd = os.open(str(lk), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, json.dumps(RM.me()).encode())
        os.close(fd)
        return lk
    except FileExistsError:
        holder = lock_holder(lk)
        if holder.get("pid") and holder_alive(holder):
            raise SystemExit(f"the night queue is already running (pid {holder['pid']})")
        lk.unlink(missing_ok=True)
        return lock_or_exit()


def cmd_plan(now: datetime | None = None) -> int:
    q, st = queue(), state()
    now = now or datetime.now()
    print(f"window: start {q['window']['start']}, last start {q['window']['last_start']}, hard stop {q['window']['hard_stop']}")
    for job in q["jobs"]:
        m = measured(job)
        pred = predicted_s(job, m)
        for seed in job["seeds"]:
            k = done_key(job, seed)
            flag = "done" if k in st["done"] else ("disabled" if not job.get("enabled", True) else "to do")
            print(f"  {job['id']} seed {seed}: {flag}; {job['W']}x{job['H']} {job['steps']} steps, {job['threads']} threads;"
                  f" predicted {f'{pred / 3600:.1f} h' if pred else 'unknown (no measured run of this shape)'};"
                  f" memory {m.get('peak_ws_gb', '?')} GB working set / {m.get('peak_commit_gb', '?')} GB commit")
    return 0


def cmd_run(ignore_start: bool = False, mem_wait_s: float = MEM_WAIT_S) -> int:
    q = queue()
    w = q["window"]
    now = datetime.now()
    start, last_start, hard_stop = at(w["start"], now), at(w["last_start"], now), at(w["hard_stop"], now)
    finish_started = w.get("finish_started", True)      # a started picture finishes (the user, 2026-10-10: no compromises)
    if not ignore_start and now < start - timedelta(minutes=5) and now.hour >= 12:
        log(f"night: not started, {now:%H:%M} is before the window ({w['start']})")
        return 0
    st = state()
    todo = [(j["id"], s) for j in q["jobs"] if j.get("enabled", True) for s in j["seeds"] if done_key(j, s) not in st["done"]]
    if not todo:
        log("night: nothing to do (every enabled picture is done)")
        return 0
    lk = lock_or_exit()
    stale = resume_if_stale()
    if stale:
        log(f"night: an earlier pause of llama-router was left behind; restarted it ({stale})")
    try:
        left = RM.restore_if_stale(say=log)
        if left:
            log(f"night: {left}")
    except Exception as e:
        log(f"night: could not put back an earlier room ({type(e).__name__}: {e})")
    ppid = os.getppid()
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    night = {"started": now.isoformat(timespec="seconds"), "images": []}
    room_cfg = q.get("room") or {}
    router, room_m, watcher = None, None, None
    log(f"night: start; {len(todo)} picture(s) to do; hard stop {hard_stop:%Y-%m-%d %H:%M}; memory {L.memory_status()}")
    try:
        # the room (the user, 2026-10-10): wait until he is away, then close what he allowed; if he comes back meanwhile, put it all back
        # and wait again. llama-router is paused only now, so it keeps serving while he still works.
        while True:
            if room_cfg.get("enabled", True) and not RM.wait_until_away(last_start, say=log):
                night["room"] = "he was not away before the last start"
                return 0
            RM.claim()
            RM.wait_for_facecard_runs(90 * 60, say=log)
            router = pause_llama_router()
            night["llama_router"] = router
            log(f"night: llama-router {router}")
            if not room_cfg.get("enabled", True):
                break
            try:
                room_m = RM.make_room(room_cfg.get("keep_sessions", []), say=log)
                night["room"] = {"planned": room_m["planned"], "memory_before": room_m["memory_before"],
                                 "memory_after": room_m.get("memory_after")}
                break
            except RM.UserBack:
                log("room: you came back; putting everything back, then waiting for you to be away again")
                RM.restore(groups=("bots", "apps"), say=log)
                if router == "paused":
                    log(f"night: llama-router restarted ({resume_llama_router()})")
                router = None
                RM.release_claim()
            except Exception as e:
                log(f"room: making room FAILED ({type(e).__name__}: {e}); no picture tonight, putting back what was closed")
                night["room"] = f"failed: {type(e).__name__}: {e}"
                return 1
        if room_m:
            watcher = RM.ReturnWatcher(say=log)
            watcher.start()
        for job in q["jobs"]:
            if not job.get("enabled", True):
                continue
            for seed in job["seeds"]:
                k = done_key(job, seed)
                if k in st["done"]:
                    continue
                now = datetime.now()
                if not home().exists():
                    log("night: D:\\FacecardLocal is not reachable; stopping")
                    return 1
                if L.on_ac_power() is False:
                    log("night: on battery; stopping (runs only on AC power)")
                    return 0
                m = measured(job)
                pred = predicted_s(job, m)
                if now >= last_start:
                    log(f"night: {now:%H:%M} is past the last start ({w['last_start']}); stopping")
                    return 0
                if pred and not finish_started and now + timedelta(seconds=pred) > hard_stop:
                    log(f"{job['id']} seed {seed}: skipped tonight, predicted {pred / 3600:.1f} h would end after the hard stop")
                    continue
                if not wait_for_room_memory(m, mem_wait_s):
                    night["images"].append({"job": job["id"], "seed": seed, "outcome": "skipped: not enough free memory"})
                    continue
                guard = Guard(None if finish_started else hard_stop, ppid)
                guard.start()
                log(f"{job['id']} seed {seed}: start ({job['W']}x{job['H']}, {job['steps']} steps, {job['threads']} threads;"
                    f" predicted {f'{pred / 3600:.1f} h' if pred else 'unknown'}; free {L.memory_status()['avail_gb']} GB)")
                try:
                    run = L.generate(job["recipe"], seed, job["W"], job["H"], job["steps"], job["threads"], job["refs_cap"], job["cache_type"],
                                     cfg=job.get("cfg", 1.0), measured=m, stop=guard.stop, retries=1, priority=job.get("priority", "below_normal"),
                                     engine=job.get("engine", "cpu"), backend=job.get("backend"), te=job.get("te", "int8"), say=log)
                finally:
                    guard.done.set()
                rec = read(run / "local_run.json", {})
                img = (rec.get("images") or [{}])[-1]
                last = (img.get("attempts") or [{}])[-1]
                entry = {"job": job["id"], "seed": seed, "run": str(run), "outcome": "picture" if img.get("output") else "no picture",
                         "killed_by": last.get("killed_by"), "elapsed_s": last.get("elapsed_s"), "s_per_step": last.get("s_per_step_median"),
                         "peak_ws_gb": last.get("peak_working_set_gb"), "peak_commit_gb": last.get("peak_commit_gb"), "phases_s": last.get("phases_s")}
                night["images"].append(entry)
                if img.get("output"):
                    st["done"][k] = {"run": str(run), "output": img["output"], "date": datetime.now().isoformat(timespec="seconds")}
                save_state(st)
                log(f"{job['id']} seed {seed}: {entry['outcome']}" + (f" ({entry['killed_by']})" if entry["killed_by"] else "")
                    + f", {((entry['elapsed_s'] or 0) / 3600):.2f} h")
                if guard.stop.is_set():
                    log(f"night: stopping ({guard.stop.reason})")
                    return 0
        log("night: queue finished")
        return 0
    finally:
        # each step on its own: one failing must never leave the bots or llama-router off. Keep-awake ends after the bots are back.
        if router == "paused":
            try:
                log(f"night: llama-router restarted ({resume_llama_router()})")
            except Exception as e:
                log(f"night: llama-router restart FAILED ({type(e).__name__}: {e}); start it with schtasks /Run /TN {LLAMA_TASK}")
        try:
            room_m = room_m or RM.own_room()                # also a room this night was still making when something failed
            if room_m:
                RM.restore(groups=("bots",), say=log)
        except Exception as e:
            log(f"room: putting the bots back FAILED ({type(e).__name__}: {e}); the facecard-local-restore task retries every 30 min")
        try:
            night["ended"] = datetime.now().isoformat(timespec="seconds")
            st = state()
            st["nights"] = (st.get("nights") or [])[-30:] + [night]
            save_state(st)
        except Exception as e:
            log(f"night: saving the night FAILED ({type(e).__name__}: {e})")
        try:
            cmd_summary(quiet=True)
        except Exception as e:
            log(f"summary failed: {type(e).__name__}: {e}")
        try:
            RM.release_claim()
        except Exception as e:
            log(f"room: releasing the claim FAILED ({type(e).__name__}: {e})")
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        try:
            wait_for_return(room_m, watcher)
        except Exception as e:
            log(f"room: waiting for you FAILED ({type(e).__name__}: {e}); the facecard-local-restore task reopens your apps")
        lk.unlink(missing_ok=True)


def wait_for_return(room_m: dict | None, watcher) -> None:
    """The user's answer: Wispr Flow, opencode and Edge reopen when he is back (his first input after 06:00). After the picture this
    process waits for that until 18:00, then leaves it to the facecard-local-restore task."""
    if not room_m or not RM.apps_pending():
        return
    if watcher:
        watcher.done.set()
    until = RM.morning(room_m.get("made")).replace(hour=RM.RETURN_UNTIL_HOUR)
    log(f"room: the night is over; Wispr Flow, opencode and Edge reopen when you are back (this waits until {until:%H:%M})")
    while datetime.now() < until and RM.apps_pending():
        m = RM.load()
        if m and RM.back_after_morning(m):
            log("room: you are back; reopening what was open")
            RM.restore(m, groups=("apps",), say=log)
            return
        time.sleep(15)


def cmd_status() -> int:
    q, st = queue(), state()
    lk = home() / "overnight.lock"
    m = read(router_marker(), None)
    if m:
        alive = holder_alive(m)
        print(f"llama-router: paused since {m.get('paused')} by {m.get('by')} (pid {m.get('pid')}, {'running' if alive else 'GONE'})")
        if not alive:
            print(f"llama-router: restarted ({resume_if_stale()})")
    holder = lock_holder(lk) if lk.exists() else {}
    running = bool(holder) and holder_alive(holder)
    print(f"queue {home() / 'queue.json'}: {len(q['jobs'])} job(s); night running: {'yes (pid ' + str(holder.get('pid')) + ')' if running else 'no'}")
    rm = RM.load()
    if rm:
        closed = [it.get("name") or it["id"] for it in rm["items"] if it.get("status") in ("closed", "stopped")]
        waiting = [it.get("name") or it["id"] for it in rm["items"] if RM.needs_restore(it)]
        print(f"room: {rm.get('state')} (planned {rm.get('planned')}, made {rm.get('made')}); free {rm['memory_before']['avail_gb']} GB before,"
              f" {(rm.get('memory_after') or {}).get('avail_gb')} GB after; closed: {', '.join(closed) or 'nothing yet'};"
              f" still to put back: {', '.join(waiting) or 'nothing'}")
    print(f"Gemini waves held off by the night's claim: {'yes' if RM.claimed() else 'no'}")
    cmd_plan()
    live = sorted((home() / "runs").glob("*/progress.json"), key=lambda p: p.stat().st_mtime)[-1:] if (home() / "runs").exists() else []
    for p in live:
        g = read(p, {})
        print(f"latest progress ({p.parent.name}): phase {g.get('phase')}, step {g.get('step')}/{g.get('steps')}, elapsed "
              f"{(g.get('elapsed_s') or 0) / 60:.1f} min, last progress {(g.get('since_progress_s') or 0) / 60:.1f} min ago"
              + (f", finished exit {g.get('exit_code')}" if g.get("finished") else "") + (f", stopped: {g['killed_by']}" if g.get("killed_by") else ""))
    for n in (st.get("nights") or [])[-3:]:
        print(f"night {n.get('started')} -> {n.get('ended')}: " + "; ".join(f"{i['job']} s{i['seed']} {i['outcome']}" for i in n.get("images", [])))
    return 0


def thumb(path: Path, w: int = 360) -> str:
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((w, w * 2))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def cmd_summary(quiet: bool = False, day: str | None = None) -> int:
    day = day or datetime.now().strftime("%Y-%m-%d")
    since = datetime.strptime(day, "%Y-%m-%d") - timedelta(hours=12)
    rows = []
    for run, r in runs():
        if datetime.fromisoformat(r["created"]) < since:
            continue
        img = (r.get("images") or [{}])[-1]
        a = (img.get("attempts") or [{}])[-1]
        pic = run / img["output"] if img.get("output") else None
        j = r["job"]
        qc = (f'.venv\\Scripts\\python.exe facecard.py run {r["recipe"]["ref"]} --remeasure "{run}"<br>'
              f'.venv\\Scripts\\python.exe tools\\best_check.py "{pic}" --source "&lt;goal&gt;" ...') if pic else ""
        rows.append(f"<tr><td>{'<img src=' + chr(34) + thumb(pic) + chr(34) + '>' if pic else 'no picture'}</td><td><b>{r['recipe']['ref']}</b>"
                    f" seed {img.get('seed')}<br>{j['W']}x{j['H']}, {j['steps']} steps, {j['threads']} threads, refs cap {j['refs_cap']}, cache"
                    f" {j['cache_type']}<br>{(a.get('elapsed_s') or 0) / 3600:.2f} h; phases {a.get('phases_s')}; s/step {a.get('s_per_step_median')}"
                    f"<br>peak working set {a.get('peak_working_set_gb')} GB, peak commit {a.get('peak_commit_gb')} GB, lowest free RAM"
                    f" {a.get('min_avail_gb')} GB<br>{('stopped: ' + a['killed_by']) if a.get('killed_by') else ''}<br><code>{run}</code>"
                    f"<br><small>{qc}</small></td></tr>")
    out = home() / "summary" / f"{day}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("<!doctype html><meta charset=utf-8><title>Local night " + day + "</title><style>body{font:14px system-ui;margin:16px}"
                   "td{vertical-align:top;padding:8px;border-bottom:1px solid #ddd}img{max-width:360px}</style><h1>Local night " + day +
                   "</h1><p>Qwen-Image-2.1 on this laptop (stable-diffusion.cpp " + L.SDCPP_RELEASE + "). Log: <code>" + str(home() / "overnight.log") +
                   "</code></p><table>" + ("".join(rows) or "<tr><td>nothing ran</td></tr>") + "</table>" + room_html(since), encoding="utf-8")
    if not quiet:
        print(out)
    return 0


def room_html(since: datetime) -> str:
    """What the rooms of this night closed and what came back (tools/room.py records)."""
    parts = []
    for f in sorted(RM.home().glob("room*.json")):
        m = RM.load(f)
        if not m or datetime.fromisoformat(m.get("planned", "1970-01-01T00:00:00")) < since:
            continue
        rows = []
        for it in m["items"]:
            if it["kind"] == "task" or (it["kind"] == "app" and not it.get("status")) or (it["kind"] == "session" and it.get("status") != "closed"):
                continue
            what = it.get("status") or "-"
            back = it.get("restore_result") or ("waits for you" if RM.needs_restore(it) else "not reopened" if what == "closed" else "")
            rows.append(f"<tr><td>{it.get('name') or it['id']}</td><td>{what} {it.get('why') or ''}</td><td>{back}</td></tr>")
        unknown = ", ".join(f"{u['name']} {u['ws_gb']} GB" for u in m.get("unknown", [])) or "none"
        parts.append(f"<h2>Room {m['planned']} ({m.get('state')})</h2><p>Free RAM {m['memory_before']['avail_gb']} GB before,"
                     f" {(m.get('memory_after') or {}).get('avail_gb')} GB after. Left running, unknown: {unknown}. Record: <code>{f}</code></p>"
                     "<table><tr><th>what</th><th>at night</th><th>put back</th></tr>" + "".join(rows) + "</table>")
    return "".join(parts)


def cmd_register() -> int:
    """Two hidden tasks. The night (at the queue window's start, 04:00 since 2026-10-11) no longer stops on battery itself: its Guard stops the picture and puts everything back, which
    Task Scheduler's own stop would skip. The restore task (every 30 min and at sign-in, also on battery) puts back a room whose night is
    gone; it exits at once when there is nothing to do."""
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    script = ROOT / "tools" / "overnight.py"
    start = queue()["window"]["start"]                       # the user, 2026-10-11: "from 4am ist to 11am or beyond"
    ps = (f"$a = New-ScheduledTaskAction -Execute '{RUNHIDDEN}' -Argument '\"{py}\" \"{script}\" run' -WorkingDirectory '{ROOT}';"
          f"$t = New-ScheduledTaskTrigger -Daily -At {start};"
          "$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 23) -MultipleInstances IgnoreNew -DontStopIfGoingOnBatteries;"
          "$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited;"
          f"Register-ScheduledTask -TaskName '{TASK}' -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null;"
          f"$a2 = New-ScheduledTaskAction -Execute '{RUNHIDDEN}' -Argument '\"{py}\" \"{script}\" restore --if-stale' -WorkingDirectory '{ROOT}';"
          "$t2 = @((New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),"
          " (New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)));"
          "$s2 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries"
          " -DontStopIfGoingOnBatteries;"
          f"Register-ScheduledTask -TaskName '{RESTORE_TASK}' -Action $a2 -Trigger $t2 -Settings $s2 -Principal $p -Force | Out-Null;"
          f"foreach ($n in @('{TASK}', '{RESTORE_TASK}')) {{ $k = Get-ScheduledTask -TaskName $n; \"== $n ($($k.State))\";"
          " $k.Settings | Select-Object DisallowStartIfOnBatteries, StopIfGoingOnBatteries, ExecutionTimeLimit, MultipleInstances | Format-List;"
          " ($k | Get-ScheduledTaskInfo).NextRunTime }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def cmd_restore(if_stale: bool) -> int:
    """--if-stale (the restore task): llama-router and a room whose night is gone. Without it: put the room back now, all of it."""
    stale = resume_if_stale()
    if stale:
        log(f"restore: llama-router restarted ({stale})")
    if if_stale:
        left = RM.restore_if_stale(say=log)
        if left:
            log(f"restore: {left}")
        return 0
    holder = lock_holder(home() / "overnight.lock")
    if holder.get("pid") and holder_alive(holder):
        print(f"the night is running (pid {holder['pid']}); it puts things back itself")
        return 1
    RM.restore(groups=("bots", "apps"), say=log)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--now", action="store_true", help="start now even before the window's start time")
    r.add_argument("--mem-wait-min", type=float, default=MEM_WAIT_S / 60, help="how long to wait for free memory before skipping a picture")
    sub.add_parser("plan")
    sub.add_parser("status")
    s = sub.add_parser("summary")
    s.add_argument("--day", default=None)
    sub.add_parser("register")
    sub.add_parser("router-resume", help="re-enable and start llama-router (after a manual pause)")
    sub.add_parser("room-plan", help="what making room would close, keep and leave right now; changes nothing")
    rs = sub.add_parser("restore", help="put back what the room closed (the facecard-local-restore task runs --if-stale)")
    rs.add_argument("--if-stale", action="store_true", help="only a room whose night is gone; the apps only once he is back")
    a = ap.parse_args()
    if a.cmd == "router-resume":
        print(resume_llama_router())
        return 0
    if a.cmd == "run":
        return cmd_run(ignore_start=a.now, mem_wait_s=a.mem_wait_min * 60)
    if a.cmd == "summary":
        return cmd_summary(day=a.day)
    if a.cmd == "room-plan":
        RM.print_plan(RM.plan((queue().get("room") or {}).get("keep_sessions", [])))
        return 0
    if a.cmd == "restore":
        return cmd_restore(a.if_stale)
    return {"plan": cmd_plan, "status": cmd_status, "register": cmd_register}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
