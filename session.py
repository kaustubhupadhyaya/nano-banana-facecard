"""
Authenticated GeminiClient factory, reading cookies from the local DPAPI vault.

Vault layout:
    gemini-cookies-psid.password   __Secure-1PSID    (user-entered only, via vault GUI)
    gemini-cookies.password        __Secure-1PSIDTS   (user-entered only, via vault GUI)
    gemini-cookies-psid.browser    __Secure-1PSID read from the signed-in google-1 browser profile (written by this module, 2026-10-09)
    gemini-cookies.rotated         latest __Secure-1PSIDTS (written by this module)

How the session stays alive without the user (2026-10-09, after it died overnight): runs NEVER renew the cookie (auto_refresh off by
default), because parallel long-waiting runs renewing the same session got HTTP 429 and invalidated each other. A run saves a changed
__Secure-1PSIDTS at close only when no other process saved one since it started (fingerprints under a lock), so a stale value can never
overwrite a newer one. tools/gemini_keepalive.py renews once, under the same lock, when no run is in flight. When every vault cookie fails,
the cookies are read from the signed-in google-1 browser profile (gemini_cookies.py, the user's choice: "From your browser").

gemini_webapi persists cookies to a plaintext JSON cache file under its cookie-cache
directory (keyed by the raw __Secure-1PSID value) whenever it rotates the session or
closes the client. That directory is redirected per-run to an isolated temp folder via
GEMINI_COOKIE_PATH and deleted afterwards, so no plaintext cookie file is left on disk.
"""

import asyncio
import shutil
import sys
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import paths

sys.path.insert(0, str(paths.vault_dir()))
import vault

from gemini_webapi import GeminiClient
from gemini_webapi.constants import AccountStatus

PSID_LABEL = "gemini-cookies-psid"
PSIDTS_LABEL = "gemini-cookies"
REFRESH_COMMAND = (
    'python vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account" '
    '--hint "gemini-cookies-psid=Password = value of the __Secure-1PSID cookie (starts with g.a000)" '
    '--hint "gemini-cookies=Password = value of the __Secure-1PSIDTS cookie (starts with sidts-)"'
)


class AuthError(RuntimeError):
    pass


# Measured 2026-09-27 (FEEDBACK_LOG section 13): the web app charges 64-86 credits per Pro image, 1-2 per text call.
# The window itself (2,400 per 5 hours, 48,384 per week on this account) is read from Gemini, never assumed.
CREDITS_PER_IMAGE = 85


def usage_of(client) -> dict:
    """Gemini's Settings -> Usage Limits as the client last read it: {'tier', 'current_5h', 'weekly'}; {} before the first reading."""
    return getattr(client, "usage_info", None) or (getattr(client, "_quotas", None) or {}).get("usage_info") or {}


def credits_left(client) -> int | None:
    """Credits left in the current 5-hour window (gemini_webapi refreshes this after every generation)."""
    v = (usage_of(client).get("current_5h") or {}).get("remaining_credits")
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _in(reset_at: str | None, now: datetime) -> str:
    try:
        secs = int((datetime.fromisoformat(reset_at) - now).total_seconds())
    except (TypeError, ValueError):
        return ""
    if secs <= 0:
        return "resets now"
    return f"resets {datetime.fromisoformat(reset_at):%H:%M} in {secs // 3600}h{secs % 3600 // 60:02d}m"


def describe_usage(info: dict, now: datetime | None = None) -> str:
    """One line for a person: '5h 1,820 left (24% used), resets 21:31 in 2h13m | week 41,200 left (15% used)'. 'no reading' if empty."""
    now = now or datetime.now().astimezone()
    parts = []
    for key, label in (("current_5h", "5h"), ("weekly", "week")):
        w = info.get(key) or {}
        if w.get("remaining_credits") is None:
            continue
        used = f" ({w['usage_percentage']}% used)" if w.get("usage_percentage") is not None else ""
        when = _in(w.get("reset_at"), now)
        parts.append(f"{label} {int(w['remaining_credits']):,} left{used}" + (f", {when}" if when and key == "current_5h" else ""))
    return " | ".join(parts) if parts else "no reading"


class CreditMeter:
    """Credits spent by this process, read from Gemini's own meter: a start reading, one entry per image call, a settled end reading.
    A text-only call costs 1-2 credits and is not noted; its cost lands in the next image call's delta."""

    def __init__(self, client, say=print):
        self.client, self.say = client, say
        self.start = credits_left(client)
        self.calls: list[dict] = []
        self.end: int | None = None
        self._last = self.start
        self.info = usage_of(client)

    def preflight(self, image_calls: int) -> str:
        """What is left now and what up to `image_calls` image calls may cost. A warning only: it never blocks or changes the run."""
        need = image_calls * CREDITS_PER_IMAGE
        msg = f"[Credits] window left at start: {describe_usage(self.info)}; up to {image_calls} image calls may cost about {need}"
        if self.start is not None and self.start < need:
            msg += f" -- {self.start} may not be enough: the run can stop at the quota and wait for the reset"
        return msg

    def note(self, tag: str, outcome: str) -> None:
        """Call right after an image call returned ('image', 'no_image')."""
        self.info = usage_of(self.client)
        now = credits_left(self.client)
        used = (self._last - now) if (now is not None and self._last is not None) else None
        self.calls.append({"tag": tag, "outcome": outcome, "credits": used, "left": now})
        spent = sum(c["credits"] or 0 for c in self.calls)
        self.say(f"[Credits] {tag}: window dropped {used} during this call, {spent} since the start of the run, {describe_usage(self.info)}")
        self._last = now

    async def settle(self) -> None:
        """A settled end reading: a single reading can lag by a call (measured in facecard.py gen)."""
        try:
            await asyncio.sleep(3)
            await self.client._fetch_usage_info()
        except Exception:
            pass
        self.info = usage_of(self.client)
        self.end = credits_left(self.client)

    def as_dict(self) -> dict:
        d = {"start": self.start, "calls": self.calls, "end": self.end}
        if self.start is not None and self.end is not None:
            d["total"] = self.start - self.end
            n_img = sum(1 for c in self.calls if c["outcome"] == "image")
            d["per_image"] = round(d["total"] / n_img, 1) if n_img else None
        return d

    def summary(self) -> str:
        d = self.as_dict()
        if "total" not in d:
            return "[Credits] run total unknown (no reading)"
        return (f"[Credits] run total {d['total']} for {sum(1 for c in self.calls if c['outcome'] == 'image')} images ({d['per_image']} per image; "
                f"the meter is account-wide, so another run or the app on the same account is counted too); {describe_usage(self.info)}")


def _psidts_candidates() -> list[str]:
    candidates = []
    for value in (vault.get_secret(PSIDTS_LABEL, "rotated"), vault.get_secret(PSIDTS_LABEL, "password")):
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def _pairs() -> list[tuple[str, str]]:
    """Every (__Secure-1PSID, __Secure-1PSIDTS) pair to try, newest first: the browser-read session, then the user-entered one."""
    out = []
    for psid in (vault.get_secret(PSID_LABEL, "browser"), vault.get_secret(PSID_LABEL, "password")):
        for ts in _psidts_candidates():
            if psid and ts and (psid, ts) not in out:
                out.append((psid, ts))
    return out


def _fp(value: str | None) -> str | None:
    """A short fingerprint of a cookie (never the cookie): tells whether the vault value changed since a run started."""
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12] if value else None


LOCK_PATH = Path(__file__).resolve().parent / ".cache" / "gemini_session.lock"


@asynccontextmanager
async def session_lock(wait: float = 120.0):
    """One process at a time renews, saves or re-reads the session (a lock file; a crashed holder's lock is taken over after 3 minutes)."""
    import os
    import time as _t
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    t0 = _t.time()
    while True:
        try:
            fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if _t.time() - LOCK_PATH.stat().st_mtime > 180:
                    LOCK_PATH.unlink()
                    continue
            except OSError:
                pass
            if _t.time() - t0 > wait:
                raise TimeoutError("the Gemini session lock is held by another process")
            await asyncio.sleep(0.5)
    try:
        yield
    finally:
        try:
            LOCK_PATH.unlink()
        except OSError:
            pass


async def _try_pair(psid: str, psidts: str, verbose: bool, auto_refresh: bool):
    candidate = GeminiClient(psid, psidts)
    try:
        await candidate.init(timeout=120, verbose=verbose, auto_refresh=auto_refresh)
    except Exception as e:
        return None, e
    if candidate.account_status == AccountStatus.AVAILABLE:
        return candidate, None
    await candidate.close()
    return None, AuthError(f"account_status={candidate.account_status.name}")


@asynccontextmanager
async def authenticated_client(verbose: bool = False, auto_refresh: bool = False):
    """Yield an authenticated GeminiClient, or raise AuthError with no secret in the message.
    auto_refresh is OFF by default (2026-10-09): runs never renew the session cookie; tools/gemini_keepalive.py renews it, alone."""
    pairs = _pairs()
    start_fp = _fp(vault.get_secret(PSIDTS_LABEL, "rotated"))
    cookie_tmp_dir = Path(tempfile.mkdtemp(prefix="gemini_webapi_cookies_"))
    client: GeminiClient | None = None
    used_psidts = None
    try:
        import os

        os.environ["GEMINI_COOKIE_PATH"] = str(cookie_tmp_dir)

        last_error: Exception | None = None
        for psid, psidts in pairs:
            client, last_error = await _try_pair(psid, psidts, verbose, auto_refresh)
            if client is not None:
                used_psidts = psidts
                break

        if client is None:
            # every vault cookie failed: read the session from the signed-in google-1 browser profile (the user's choice, 2026-10-09)
            async with session_lock(wait=300):
                pairs_now = _pairs()
                if pairs_now != pairs:          # another process restarted the session while this one waited: use that
                    for psid, psidts in pairs_now:
                        client, last_error = await _try_pair(psid, psidts, verbose, auto_refresh)
                        if client is not None:
                            used_psidts = psidts
                            break
                if client is None:
                    import gemini_cookies
                    found = await asyncio.to_thread(gemini_cookies.from_browser)
                    if found:
                        client, last_error = await _try_pair(found["__Secure-1PSID"], found["__Secure-1PSIDTS"], verbose, auto_refresh)
                        if client is not None:
                            vault.set_value(PSID_LABEL, "browser", found["__Secure-1PSID"])
                            vault.set_value(PSIDTS_LABEL, "rotated", found["__Secure-1PSIDTS"])
                            used_psidts = found["__Secure-1PSIDTS"]
                            start_fp = _fp(used_psidts)

        if client is None:
            raise AuthError(
                "Authentication failed with all known cookies and the google-1 browser profile (session likely expired). "
                f"Underlying: {type(last_error).__name__ if last_error else 'unknown'}\n"
                f"Refresh from the secure-vault folder: {REFRESH_COMMAND}"
            )

        yield client

    finally:
        if client is not None:
            try:
                fresh_psidts = None
                for cookie in client.cookies.jar:
                    if cookie.name == "__Secure-1PSIDTS":
                        fresh_psidts = cookie.value
                        break
                await client.close()
                if fresh_psidts and fresh_psidts != used_psidts:
                    # save only if no other process saved a newer value since this one started (a stale value must never win)
                    async with session_lock(wait=60):
                        if _fp(vault.get_secret(PSIDTS_LABEL, "rotated")) == start_fp:
                            vault.set_value(PSIDTS_LABEL, "rotated", fresh_psidts)
            except Exception:
                pass

        shutil.rmtree(cookie_tmp_dir, ignore_errors=True)
