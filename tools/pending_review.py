"""Session end: the new pictures waiting for the user's review, numbered, with complete file paths (and the queue record_review.py reads).

A picture is pending when its run folder is newer than the session start (tools\\session_prune.py --apply marks it; --all ignores it) and the user has
not reviewed that run yet (facecard.json approved_outputs, reviews, best_versions). Runs that only returned a best version unchanged are left out.

    .venv\\Scripts\\python.exe tools\\pending_review.py          # this session's pictures
    .venv\\Scripts\\python.exe tools\\pending_review.py --all    # every unreviewed picture
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import OUTPUTS, REVIEW_QUEUE, SESSION_MARK, attempt_table, picture_of, reviewed_runs, run_dirs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="every unreviewed picture, not only this session's")
    ap.add_argument("--since", help="only runs at or after this stamp (YYYYMMDD_HHMMSS)")
    args = ap.parse_args()
    since = args.since or ("" if args.all else (json.loads(SESSION_MARK.read_text(encoding="utf-8")).get("session_start", "")
                                                if SESSION_MARK.exists() else ""))
    done = reviewed_runs()
    queue = []
    for d in run_dirs(OUTPUTS):
        if d.name[:15] < since or d.name in done or "_angle_refs" in d.name:
            continue
        pic = picture_of(d)
        if pic is None:
            continue
        j = json.loads((d / "run.json").read_text(encoding="utf-8")) if (d / "run.json").exists() else {}
        if j.get("status") == "already_best_version":
            continue
        best = (j.get("best") or {}).get("candidate")
        closest = (j.get("not_passing_closest") or {}).get("candidate")
        idx = best or closest
        row = next((r for r in attempt_table(d) if r["attempt"] == idx), {})
        queue.append({"n": len(queue) + 1, "run": d.name, "file": pic.name, "path": str(pic), "source": str(j.get("scene") or (j.get("args") or {}).get("scene")),
                      "passed": bool(best), "attempt": idx, "identity": row.get("identity"), "source_identity": row.get("source_identity"),
                      "light_dE": row.get("light_dE"), "size": row.get("size"), "problems": row.get("problems", [])})
    REVIEW_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_QUEUE.write_text(json.dumps(queue, indent=1, ensure_ascii=False), encoding="utf-8")
    if not queue:
        print("No pictures waiting for review" + (f" since {since}" if since else "") + ".")
        return 0
    print(f"{len(queue)} picture(s) waiting for your review" + (f" (runs since {since})" if since else "") + ":\n")
    for q in queue:
        state = "passed every gate" if q["passed"] else "closest; did not pass: " + "; ".join(p.split(" (")[0] for p in q["problems"])[:120]
        print(f"{q['n']}. {q['path']}")
        print(f"   source {q['source']} | attempt {q['attempt']}, {state} | identity {q['identity']} (source {q['source_identity']}), light dE {q['light_dE']}, size {q['size']}")
    print(f"\nqueue written to {REVIEW_QUEUE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
