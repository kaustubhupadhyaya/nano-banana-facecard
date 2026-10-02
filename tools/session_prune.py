"""Session start: keep only what matters, delete the rest (the user's rule, 2026-09-23).

In every run folder of outputs\\ and .cache\\feedback\\ this KEEPS
  - the picture of the run (best.jpg / best.png / not_passing_closest.jpg; gen: v1_0*.jpg)
  - its metadata (run.json, run.log)
  - every file the user reviewed or the records name (facecard.json, FEEDBACK_LOG.md, the workbook rows, best_versions)
and DELETES everything else (candidates, raw returns, crops sent, compare sheets, head crops). Folders that are not run folders (.cache\\feedback\\ideal,
rule_check_offline, .cache\\synthetic_refs, refcrops, patches) and the source photos are never touched. The user's best versions in
D:\\Downloads\\AI me are never touched.

    .venv\\Scripts\\python.exe tools\\session_prune.py           # dry run: what would be deleted, and how much space
    .venv\\Scripts\\python.exe tools\\session_prune.py --apply   # delete, and mark the session start (for pending_review.py)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import FEEDBACK, METADATA, OUTPUTS, PICTURES, SESSION_MARK, referenced_files, run_dirs  # noqa: E402


def plan() -> tuple[list[Path], list[Path], int, int]:
    refs = referenced_files()
    keep, drop = [], []
    kb = db = 0
    for d in run_dirs(OUTPUTS, FEEDBACK):
        # a run still being written (status "started", or touched in the last 15 minutes) is left alone
        rj = d / "run.json"
        try:
            status = json.loads(rj.read_text(encoding="utf-8")).get("status") if rj.exists() else None
        except (OSError, ValueError):
            status = "started"
        newest = max((p.stat().st_mtime for p in d.rglob("*") if p.is_file()), default=0)
        now = datetime.now().timestamp()
        if newest > now - 900 or (status == "started" and newest > now - 6 * 3600):
            print(f"  skipped (still running or just written): {d.name}")
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file():
                continue
            rel_top = p.relative_to(d).parts[0]
            name = p.name
            ref = (d.name, name) in refs or (d.name, p.relative_to(d).as_posix()) in refs
            # the best-checklist verdicts (tools/best_check.py) are records too (2026-09-29): tiny, and the only item-by-item evidence
            if (rel_top == name and (name in PICTURES or name in METADATA)) or ref or name.endswith(".checklist.json"):
                keep.append(p)
                kb += p.stat().st_size
            else:
                drop.append(p)
                db += p.stat().st_size
    return keep, drop, kb, db


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="delete (default: dry run)")
    args = ap.parse_args()
    keep, drop, kb, db = plan()
    print(f"keep   {len(keep):5d} files  {kb / 1e6:8.1f} MB  (pictures, run.json, run.log, reviewed files)")
    print(f"delete {len(drop):5d} files  {db / 1e6:8.1f} MB  (candidates, raw returns, sent crops, compare sheets, head crops)")
    if not args.apply:
        print("dry run: nothing deleted. Pass --apply to delete.")
        return 0
    for p in drop:
        try:
            p.unlink()
        except OSError as e:
            print("  could not delete", p, e)
    # empty sub-folders (raw\) left behind
    for d in run_dirs(OUTPUTS, FEEDBACK):
        for sub in sorted((x for x in d.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
            if not any(sub.iterdir()):
                shutil.rmtree(sub, ignore_errors=True)
    SESSION_MARK.parent.mkdir(parents=True, exist_ok=True)
    SESSION_MARK.write_text(json.dumps({"session_start": datetime.now().strftime("%Y%m%d_%H%M%S")}), encoding="utf-8")
    print(f"deleted {len(drop)} files ({db / 1e6:.1f} MB); session start marked in {SESSION_MARK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
