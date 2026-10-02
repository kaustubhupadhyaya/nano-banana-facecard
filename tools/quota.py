"""Gemini quota of the logged-in account: credits left in the current 5-hour window and in the week, and when the 5-hour window resets.

    .venv\\Scripts\\python.exe tools\\quota.py                 # one reading
    .venv\\Scripts\\python.exe tools\\quota.py --watch         # live: one line, refreshed every 60 s, also written to .cache\\quota.json
    .venv\\Scripts\\python.exe tools\\quota.py --watch --every 30

The numbers are Gemini's own (Settings -> Usage Limits); reading them costs no image credits. The watcher keeps one login open and never rotates
the session cookies (so it does not compete with a running replicate/batch); if its session dies it logs in again from the vault, and if the
cookies are really gone it stops and prints the refresh step. `.cache\\quota.json` holds the last reading for any other tool to read.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

QUOTA_JSON = ROOT / ".cache" / "quota.json"


async def get_quota() -> dict:
    """{'tier', 'remaining_5h', 'reset_at' (ISO), 'remaining_week'} from the client's own quota fetch at login; {} if unavailable."""
    from session import authenticated_client
    async with authenticated_client(verbose=False) as client:
        info = (getattr(client, "_quotas", None) or {}).get("usage_info") or {}
    cur, week = info.get("current_5h") or {}, info.get("weekly") or {}
    return {"tier": (info.get("tier") or {}).get("label"), "remaining_5h": cur.get("remaining_credits"), "reset_at": cur.get("reset_at"),
            "remaining_week": week.get("remaining_credits")}


def _publish(info: dict) -> None:
    """Atomic write of the last reading, for any other tool or status display."""
    QUOTA_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUOTA_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"read_at": datetime.now().astimezone().isoformat(), **info}, indent=1), encoding="utf-8")
    os.replace(tmp, QUOTA_JSON)


def _show(text: str, tty: bool) -> None:
    line = f"{datetime.now():%H:%M:%S}  {text}"
    if tty:
        print("\r" + line.ljust(118), end="", flush=True)
    else:
        print(line, flush=True)


async def watch(every: float) -> int:
    from gemini_webapi.constants import AccountStatus
    from session import AuthError, authenticated_client, describe_usage, usage_of
    tty = sys.stdout.isatty()
    while True:
        try:
            async with authenticated_client(verbose=False, auto_refresh=False) as client:
                failures = 0
                while failures < 3:
                    try:
                        await client._fetch_usage_info()
                        if client.account_status != AccountStatus.AVAILABLE:
                            raise RuntimeError(f"account_status={client.account_status.name}")
                        info = usage_of(client)
                        if not info:
                            raise RuntimeError("empty usage reading")
                        failures = 0
                        _publish(info)
                        _show(f"tier {(info.get('tier') or {}).get('label')}: {describe_usage(info)}", tty)
                    except Exception as e:
                        failures += 1
                        _show(f"reading failed ({type(e).__name__}: {str(e)[:60]}), try {failures}/3", tty)
                    await asyncio.sleep(every)
        except AuthError as e:
            print("\n" + str(e))
            return 2
        _show("session lost, logging in again", tty)
        await asyncio.sleep(every)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watch", action="store_true", help="keep running and refresh the reading")
    ap.add_argument("--every", type=float, default=60.0, help="seconds between readings with --watch (minimum 15)")
    a = ap.parse_args()
    import session  # noqa: F401  (imports gemini_webapi first, so its log sink can be replaced after it)
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level="ERROR")   # the library logs every login step at INFO; this tool prints its own line
    if a.watch:
        try:
            return asyncio.run(watch(max(15.0, a.every)))
        except KeyboardInterrupt:
            print()
            return 0
    from session import describe_usage, usage_of, authenticated_client

    async def once() -> dict:
        async with authenticated_client(verbose=False) as client:
            return dict(usage_of(client))

    info = asyncio.run(once())
    if not info:
        print("quota not available")
        return 1
    _publish(info)
    print(f"tier {(info.get('tier') or {}).get('label')}: {describe_usage(info)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
