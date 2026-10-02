"""Gemini credits per run folder (the user, 2026-09-27: what does one output folder cost, and can it cost less).

facecard.py gen records the credits of every call in run.json ("credits": start, calls, end, total, per_image) since 2026-09-27 14:00,
and the pose gate result ("pose_gate"). This lists the runs that have them:

    .venv\\Scripts\\python.exe tools\\credit_report.py [--since 20260927]

Columns: run, model (Pro/Flash), images, credits, credits per image, pose-gate passes, credits per passing image, early stop.
Older runs have no per-call record; their window-level measurements are in FEEDBACK_LOG section 13.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"e6fa609c3fa255c0": "Pro", "56fdd199312815e2": "Flash", "8c46e95b1a07cecc": "Lite"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default="", help="only run folders whose name sorts at or after this prefix, e.g. 20260927_14")
    a = ap.parse_args()
    rows = []
    for rj in sorted((ROOT / "outputs").glob("*/run.json")):
        if rj.parent.name < a.since:
            continue
        try:
            d = json.loads(rj.read_text(encoding="utf-8"))
        except Exception:
            continue
        c = d.get("credits")
        if not c:
            continue
        images = sum(1 for x in c.get("calls", []) if x.get("outcome") == "image")
        refused = sum(1 for x in c.get("calls", []) if x.get("outcome") == "no_image")
        gate = d.get("pose_gate") or []
        passes = sum(1 for g in gate if not g.get("fails"))
        total = c.get("total")
        rows.append((rj.parent.name, MODELS.get(c.get("model"), c.get("model")), images, refused, total,
                     c.get("per_image"), f"{passes}/{len(gate)}" if gate else "-",
                     round(total / passes, 1) if (total and passes) else None, (d.get("early_stop") or {}).get("after")))
    if not rows:
        print("no run folder has a credit record yet (facecard.py gen records them from 2026-09-27 14:00)")
        return 0
    head = ("run", "model", "images", "refused", "credits", "per image", "gate pass", "per passing", "stopped after")
    print(" | ".join(head))
    for r in rows:
        print(" | ".join("-" if v is None else str(v) for v in r))
    tot = sum(r[4] or 0 for r in rows)
    imgs = sum(r[2] for r in rows)
    print(f"\ntotal {tot} credits for {imgs} images ({round(tot / imgs, 1) if imgs else '-'} per image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
