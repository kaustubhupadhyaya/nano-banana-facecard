"""Apply the image creation to a list of photos: the default replicate pipeline, no flags, one photo after another (the user's rule: "when I say apply
our image creation, just apply it"). Resumable: a photo that finished is recorded in the state file and skipped next time. When the Gemini image
quota runs out it waits for the reset and repeats that photo; when the session cookies stop working it stops and prints the refresh step.

    .venv\\Scripts\\python.exe tools\\batch_run.py "D:\\photos\\a.jpg" "D:\\photos\\b.HEIC"
    .venv\\Scripts\\python.exe tools\\batch_run.py --list photos.txt --state .cache\\batch_state_mytest.json
Each run's full output goes to .cache\\batch_logs\\; one summary line per photo is printed.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import ROOT  # noqa: E402
from quota import get_quota  # noqa: E402

PY = ROOT / ".venv" / "Scripts" / "python.exe"
LOGS = ROOT / ".cache" / "batch_logs"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
SUMMARY = re.compile(r"^(run dir:|source classified|expression policy|far from the camera|source pose|identity refs by pose|This photo is one of your|"
                     r"\[BEST\]|No candidate passed|Gemini quota reached|\[Credits\] (window left|run total|at the stop))")


def wait_for_reset() -> None:
    q: dict = {}
    try:
        q = asyncio.run(get_quota())
        reset = datetime.fromisoformat(q["reset_at"]).timestamp() if q.get("reset_at") else None
    except Exception:
        reset = None
    wait = max(120.0, (reset - time.time() + 120.0) if reset else 1200.0)
    print(f"    image quota exhausted; waiting {wait / 60:.0f} min for the reset ({q.get('reset_at') if reset else 'reset time unknown'})", flush=True)
    time.sleep(wait)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", nargs="*")
    ap.add_argument("--list", help="a text file with one photo path per line")
    ap.add_argument("--state", default=str(ROOT / ".cache" / "batch_state.json"), help="which photos are done (resumable)")
    args = ap.parse_args()
    photos = list(args.photos) + ([ln.strip().strip('"') for ln in Path(args.list).read_text(encoding="utf-8").splitlines() if ln.strip()] if args.list else [])
    state_p = Path(args.state)
    done = set(json.loads(state_p.read_text(encoding="utf-8"))) if state_p.exists() else set()
    LOGS.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        if photo in done:
            print(f"=== {photo}: already done, skipped")
            continue
        while True:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_p = LOGS / f"{stamp}_{Path(photo).stem[:40]}.out"
            print(f"=== {photo}  start {datetime.now():%H:%M:%S}", flush=True)
            with out_p.open("w", encoding="utf-8") as f:
                rc = subprocess.call([str(PY), str(ROOT / "facecard.py"), "replicate", "--scene", photo], cwd=str(ROOT), stdout=f,
                                     stderr=subprocess.STDOUT, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"})
            text = ANSI.sub("", out_p.read_text(encoding="utf-8", errors="replace"))
            print(f"    exit {rc}  end {datetime.now():%H:%M:%S}  (full output: {out_p})")
            for ln in text.splitlines():
                if SUMMARY.match(ln):
                    print("    " + ln[:260])
            if "Authentication failed" in text or "Missing cookies in vault" in text:
                print("    AUTHENTICATION FAILED: the Gemini cookies need refreshing (vault popup, see the skill). Stopped; run again afterwards.")
                return 2
            if "Gemini quota reached" in text:
                wait_for_reset()
                continue
            break
        done.add(photo)
        state_p.parent.mkdir(parents=True, exist_ok=True)
        state_p.write_text(json.dumps(sorted(done), indent=1), encoding="utf-8")
    print(f"ALL DONE {datetime.now():%H:%M:%S}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
