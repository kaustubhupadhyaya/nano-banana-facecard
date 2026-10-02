"""Record the best-picture checklist (BEST_CHECKLIST.md) for one picture. The user's rule (2026-09-26): no picture is called best until every item
is checked by eye; one failed or unverifiable item means NOT BEST, and the picture goes back into the loop with think-again.

    .venv\\Scripts\\python.exe tools\\best_check.py "<picture>" --source "<source photo>" --fail 4,26 --na 3,17,20 --note "why each failed"

Items not listed as --fail or --na count as PASS, so list every failed and every unverifiable item. Writes <picture>.checklist.json next to the
picture and prints the verdict.

When the USER accepts a picture that the checklist failed ("pencil in mouth pass v1 - sufficient", 2026-10-01), record it with their words:

    .venv\\Scripts\\python.exe tools\\best_check.py "<picture>" --user-approved "<their words>"

The failed items stay on record (nothing is rewritten as a pass); the verdict becomes "BEST (user-approved)" and the picture counts as passed for
the results folder (tools\\export_results.py brings only passed pictures there). If the picture has no checklist yet, add --source / --fail / --na as usual.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "BEST_CHECKLIST.md"


def items() -> dict[int, str]:
    out = {}
    for line in CHECKLIST.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def nums(s: str | None) -> set[int]:
    return {int(x) for x in re.findall(r"\d+", s or "")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture")
    ap.add_argument("--source", default=None)
    ap.add_argument("--fail", default="", help="failed or unverifiable item numbers, e.g. 4,26")
    ap.add_argument("--na", default="", help="item numbers that do not apply")
    ap.add_argument("--note", default="", help="why each item failed (what was WRONG)")
    ap.add_argument("--right", default="", help="what went RIGHT in this picture, kept in FEEDBACK_LEDGER.md so a later round can reuse it")
    ap.add_argument("--keep-in-results", action="store_true", help="record the failing verdict but leave the picture where it is in the results folder (the user said not to remove it)")
    ap.add_argument("--user-approved", default=None, metavar="WORDS", help="the user accepted this picture; keeps the recorded failed items, verdict becomes BEST (user-approved)")
    args = ap.parse_args()
    its = items()
    pic = Path(args.picture)
    out = pic.with_name(pic.name + ".checklist.json")
    if args.user_approved is not None and out.exists() and not (args.fail or args.na or args.note or args.source):
        rec = json.loads(out.read_text(encoding="utf-8"))          # approval of an already-checked picture: keep every recorded item as it was
        if args.right:
            rec["right"] = args.right
        rec["user_approved"] = {"words": args.user_approved, "date": datetime.now().isoformat(timespec="seconds"), "checklist_verdict": rec.get("verdict")}
        rec["verdict"] = "BEST (user-approved)"
        out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"BEST (user-approved): failed items kept on record {sorted(map(int, rec.get('failed', {})))} -> {out}")
        if (pic.parent / "run.json").exists():
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from export_results import safe_export
            safe_export(pic.parent)
        return 0
    fail, na = nums(args.fail), nums(args.na)
    unknown = (fail | na) - set(its)
    if unknown:
        print(f"no such checklist item(s): {sorted(unknown)}")
        return 2
    result = {n: ("FAIL" if n in fail else "N/A" if n in na else "PASS") for n in sorted(its)}
    verdict = "NOT BEST" if fail else "BEST"
    rec = {"picture": args.picture, "source": args.source, "date": datetime.now().isoformat(timespec="seconds"), "verdict": verdict,
           "failed": {n: its[n] for n in sorted(fail)}, "na": sorted(na), "note": args.note, "right": args.right, "items": result}
    if args.keep_in_results:
        rec["keep_in_results"] = True
    if args.user_approved is not None:
        rec["user_approved"] = {"words": args.user_approved, "date": rec["date"], "checklist_verdict": verdict}
        rec["verdict"] = verdict = "BEST (user-approved)"
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    for n in sorted(fail):
        print(f"  FAIL {n:2d}. {its[n]}")
    print(f"{verdict}: {len(fail)} failed, {len(na)} n/a, {len(its) - len(fail) - len(na)} passed -> {out}")
    if (pic.parent / "run.json").exists():     # the results folder's file name carries the verdict (tools/export_results.py)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from export_results import safe_export
        safe_export(pic.parent)
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
