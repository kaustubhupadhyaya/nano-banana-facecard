"""Record the best-picture checklist (BEST_CHECKLIST.md) for one picture. The user's rule (2026-09-26): no picture is called best until every item
is checked by eye; one failed or unverifiable item means NOT BEST, and the picture goes back into the loop with think-again. Since 2026-10-17 the
current-look items (NOTE_ITEMS: 19, 26, 28, 31, 32) are pointed out as NOTE and never make a picture NOT BEST (the user: "No, just point them out").

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
import contextlib
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


# The user, 2026-10-08: "body and hair rework needed for both, since the current physique and face has been changed as can be seen in the
# reference images, hence can't be considered best; fix the QC that qualifies best to not make this mistake again". I had passed his kayak and
# mirror pictures with the OLD photo's body (replicate keeps every pixel below the head crop) and "curly" hair that was not his current cut.
# The user, 2026-10-09: background people, text in the picture and a candid capture look are rules I kept forgetting (items 33-35): a PASS of them
# names what was looked at (every person and every text, at 100%, beside the goal) too.
EVIDENCE_ITEMS = (19, 21, 26, 28, 31, 32, 33, 34, 35, 36, 38)   # a PASS of these needs a line naming what was compared, at the same scale, with what (36: the janeu, 2026-10-10; 38: his teeth, 2026-10-18)
OLD_BODY_ITEMS = (26, 32)
# The user, 2026-10-17, asked whether the current-look items should reject pictures: "No, just point them out". Their favourite pictures fail them
# (kayak, beach, TT, tt2). A FAIL of these is kept under "noted" and printed as NOTE, and never makes a picture NOT BEST. Item 26's first
# sentence (scenery, background and clothes unchanged) is not a current-look rule: it moved to item 37, which still rejects.
NOTE_ITEMS = (19, 26, 28, 31, 32)


def evidence_of(specs: list[str]) -> dict[int, str]:
    out = {}
    for spec in specs or []:
        m = re.match(r"\s*(\d+)\s*[=:]\s*(.+)", spec, re.S)
        if not m:
            raise SystemExit(f"--evidence {spec!r}: use N=what was compared and what was seen")
        out[int(m.group(1))] = m.group(2).strip()
    return out


def old_body_kept(run_dir: Path) -> str | None:
    """Why this picture's body is provably an older photo's, or None: a CURRENT-LOOK goal (results_names.json target_look "current", or a recipe
    with inputs.current_look) made by replicate with no body pass in its lineage keeps every pixel outside the head crop."""
    rec = None
    with contextlib.suppress(Exception):
        rec = json.loads((run_dir / "01_method" / "recipe.json").read_text(encoding="utf-8"))
    run = {}
    with contextlib.suppress(Exception):
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import export_results
    key = (rec or {}).get("id") or export_results.goal_key(run)
    names = {}
    with contextlib.suppress(Exception):
        names = json.loads((ROOT / "results_names.json").read_text(encoding="utf-8"))
    current = ((names.get(key) or {}).get("target_look") == "current") or bool(((rec or {}).get("inputs") or {}).get("current_look"))
    if not current:
        return None
    replicate_made = (rec or {}).get("method", {}).get("route") == "replicate" or (rec is None and "replicate" in run_dir.name)
    if not replicate_made:
        return None
    inp = (rec or {}).get("inputs") or {}
    if inp.get("zone") == "build" or (inp.get("from_picture") or {}).get("zone") == "build":
        return None
    return ("the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop "
            "(no body pass in its lineage)")


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
    ap.add_argument("--superseded-by", default=None, metavar="FILE::WORDS", dest="superseded_by",
                    help="this picture's corrected copy (e.g. vN_Ms.jpg, the sparkle mark removed) replaces it in the results folder; every item stays "
                         "on record and the verdict is unchanged, it is only no longer exported (the user, 2026-10-21: 'Replace it')")
    ap.add_argument("--user-rejected", default=None, metavar="WORDS",
                    help="the user called this picture bad, also one they had approved: every recorded item and the earlier approval stay on record, "
                         "the verdict becomes NOT BEST (user-rejected) and the results folder withdraws it")
    ap.add_argument("--evidence", action="append", default=[], metavar="N=TEXT",
                    help=f"what was compared for item N and what was seen (required for a PASS of items {', '.join(map(str, EVIDENCE_ITEMS))}), e.g. "
                         "32=\"torso beside IMG_6923 at the same shoulder width: arms and shoulders as lean as his\"")
    args = ap.parse_args()
    its = items()
    pic = Path(args.picture)
    out = pic.with_name(pic.name + ".checklist.json")
    if args.superseded_by is not None:
        if not out.exists():
            print(f"no checklist recorded for {pic} yet: nothing to supersede")
            return 2
        rec = json.loads(out.read_text(encoding="utf-8"))
        file_, _, why = args.superseded_by.partition("::")
        rec["superseded_by"] = {"file": file_.strip(), "words": why.strip(), "date": datetime.now().isoformat(timespec="seconds")}
        out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"superseded by {file_.strip()}: {why.strip()[:160]} -> {out}")
        if (pic.parent / "run.json").exists():
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from export_results import safe_export
            safe_export(pic.parent)
        return 0
    if args.user_rejected is not None:
        # the user, 2026-10-17, on two exported pictures they had approved in dialogs on 10-12 and 10-13: "these are bad". Their latest word wins;
        # the earlier approval stays on record under "history", and the results folder withdraws the picture (tools\export_results.py)
        if not out.exists():
            print(f"no checklist recorded for {pic} yet: record it first (--source / --fail / --na), then --user-rejected")
            return 2
        rec = json.loads(out.read_text(encoding="utf-8"))
        earlier = {k: rec.pop(k) for k in ("user_approved", "keep_in_results") if k in rec}
        if earlier:
            rec.setdefault("history", []).append({**earlier, "verdict": rec.get("verdict")})
        rec["user_rejected"] = {"words": args.user_rejected, "date": datetime.now().isoformat(timespec="seconds")}
        rec["verdict"] = "NOT BEST (user-rejected)"
        out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"NOT BEST (user-rejected): {args.user_rejected[:160]} -> {out}")
        if (pic.parent / "run.json").exists():
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from export_results import safe_export
            safe_export(pic.parent)
        refresh_report(pic.parent)
        return 1
    if args.user_approved is not None and out.exists() and not (args.fail or args.na or args.note or args.source):
        rec = json.loads(out.read_text(encoding="utf-8"))          # approval of an already-checked picture: keep every recorded item as it was
        if rec.get("user_rejected"):                               # a new approval replaces the user's rejection, which stays on record
            rec.setdefault("history", []).append({"user_rejected": rec.pop("user_rejected"), "verdict": rec.get("verdict")})
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
        refresh_report(pic.parent)
        return 0
    fail, na = nums(args.fail), nums(args.na)
    unknown = (fail | na) - set(its)
    if unknown:
        print(f"no such checklist item(s): {sorted(unknown)}")
        return 2
    evidence = evidence_of(args.evidence)
    sheet = pic.parent / "07_review" / f"{pic.stem}_character.jpg"
    if sheet.is_file():
        print(f"character sheet (items 19, 21, 28, 31, 32): {sheet}")
    forced = {}
    why_old = old_body_kept(pic.parent)
    if why_old:
        for n in OLD_BODY_ITEMS:
            if n not in fail:
                forced[n] = why_old
        fail |= set(OLD_BODY_ITEMS)
        na -= set(OLD_BODY_ITEMS)
        print(f"  FORCED 26, 32 (pointed out as NOTE since 2026-10-17): {why_old}")
    missing = [n for n in EVIDENCE_ITEMS if n in its and n not in fail and n not in na and n not in evidence]
    if missing:
        print(f"REFUSED: items {', '.join(map(str, missing))} would PASS without evidence. Compare each with the character's photos at the same scale "
              "and give --evidence \"N=what was compared and what was seen\", or list it under --fail (unverifiable is a fail). Nothing was written.")
        return 2
    noted = fail & set(NOTE_ITEMS)
    blocking = fail - noted
    result = {n: ("NOTE" if n in noted else "FAIL" if n in fail else "N/A" if n in na else "PASS") for n in sorted(its)}
    verdict = "NOT BEST" if blocking else "BEST"
    rec = {"picture": args.picture, "source": args.source, "date": datetime.now().isoformat(timespec="seconds"), "verdict": verdict,
           "failed": {n: its[n] for n in sorted(blocking)}, "noted": {n: its[n] for n in sorted(noted)}, "na": sorted(na), "note": args.note + (f" FORCED: {why_old}." if forced else ""),
           "right": args.right, "items": result, "evidence": {str(k): v for k, v in sorted(evidence.items())}}
    if forced:
        rec["forced"] = {str(k): v for k, v in forced.items()}
    if args.keep_in_results:
        rec["keep_in_results"] = True
    if args.user_approved is not None:
        rec["user_approved"] = {"words": args.user_approved, "date": rec["date"], "checklist_verdict": verdict}
        rec["verdict"] = verdict = "BEST (user-approved)"
    prior = {}
    with contextlib.suppress(Exception):
        prior = json.loads(out.read_text(encoding="utf-8"))
    if prior.get("user_rejected"):
        if args.user_approved is not None:                           # a new approval replaces the user's rejection, which stays on record
            rec["history"] = prior.get("history", []) + [{"user_rejected": prior["user_rejected"], "verdict": prior.get("verdict")}]
        else:                                                        # the user's own verdict outlives a re-check of mine
            rec["user_rejected"], rec["history"] = prior["user_rejected"], prior.get("history", [])
            rec["verdict"] = verdict = "NOT BEST (user-rejected)"
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    for n in sorted(blocking):
        print(f"  FAIL {n:2d}. {its[n]}")
    for n in sorted(noted):
        print(f"  NOTE {n:2d}. {its[n]}")
    print(f"{verdict}: {len(blocking)} failed, {len(noted)} pointed out, {len(na)} n/a, {len(its) - len(fail) - len(na)} passed -> {out}")
    if (pic.parent / "run.json").exists():     # the results folder's file name carries the verdict (tools/export_results.py)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from export_results import safe_export
        safe_export(pic.parent)
    refresh_report(pic.parent)
    return 0 if not blocking and not rec.get("user_rejected") else 1


def refresh_report(run_dir: Path) -> None:
    """A staged run's report (and its copy in the review folder) shows the checklist verdicts: rewrite it after each record. Never fatal."""
    if not (run_dir / "manifest.json").exists():
        return
    try:
        sys.path.insert(0, str(ROOT))
        import report
        report.refresh(run_dir)
        print(f"[Report] refreshed: {run_dir / 'report.html'}")
    except Exception as exc:
        print(f"[Report] not refreshed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
