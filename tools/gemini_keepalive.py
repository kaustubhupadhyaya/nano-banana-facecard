"""Keep the facecard Gemini session alive without the user (2026-10-09).

The session rests on __Secure-1PSIDTS, which Google wants renewed now and then. Runs no longer renew it (session.py: parallel long runs renewing
the same session got HTTP 429 and invalidated each other on 2026-10-08), so this is the ONLY renewer: it renews once, under the session lock,
and only when no generation is in flight (the credit guard's registry, .cache/inflight). The new value goes to the vault's
gemini-cookies.rotated (never printed). If every vault cookie is dead, logging in reads the session from the signed-in google-1 browser
profile (gemini_cookies.py). Scheduled every 6 hours (task facecard-gemini-keepalive, hidden); a stored value has stayed valid for 36 hours.

    .venv\\Scripts\\python.exe tools\\gemini_keepalive.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LOG = ROOT / ".cache" / "gemini_keepalive.log"


def say(msg: str) -> None:
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def runs_in_flight() -> list[str]:
    from credit_guard import INFLIGHT, pid_alive
    out = []
    for f in INFLIGHT.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if pid_alive(int(d.get("pid") or f.stem)):
                out.append(str(d.get("label") or f.stem))
        except Exception:
            continue
    return out


async def main() -> int:
    busy = runs_in_flight()
    if busy:
        say(f"skipped: {len(busy)} generation(s) in flight ({', '.join(busy[:3])})")
        return 0
    from gemini_webapi.utils.rotate_1psidts import rotate_1psidts
    from session import PSIDTS_LABEL, AuthError, _fp, authenticated_client, session_lock, vault
    try:
        async with authenticated_client(verbose=False, auto_refresh=False) as client:
            async with session_lock(wait=120):
                new = await rotate_1psidts(client._live_client, False)
                if new:
                    vault.set_value(PSIDTS_LABEL, "rotated", new)
                    say(f"renewed the session cookie (fingerprint {_fp(new)})")
                else:
                    say("renewal answered without a new cookie; the stored one stays")
    except AuthError as e:
        say(f"FAILED: {str(e).splitlines()[0]}")
        return 1
    except Exception as e:
        say(f"FAILED: {type(e).__name__}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
