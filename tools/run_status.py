"""Where the generation runs of one goal stand, in one line each: model, request variant, faces sent, per-render identity score and pose-gate result, credits used.

    .venv\\Scripts\\python.exe tools\\run_status.py <goal pin id or any part of the run folder name> [--since 20261001_2150]

Reads outputs\\<run>\\run.json only (never starts anything). A run that has no run.json yet is still generating.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("goal", help="e.g. 783485666539777054 (matched against the run folder name)")
    ap.add_argument("--since", default="", help="only run folders whose name starts at or after this stamp, e.g. 20261001_2150")
    a = ap.parse_args()
    for d in sorted((ROOT / "outputs").glob(f"*{a.goal}*")):
        if d.name < a.since:
            continue
        rj = d / "run.json"
        if not rj.exists():
            print(f"{d.name[:15]}  generating (no run.json yet)")
            continue
        try:
            j = json.loads(rj.read_text(encoding="utf-8"))
        except Exception:
            print(f"{d.name[:15]}  run.json being written")
            continue
        rg = j.get("route_g") or {}
        inv = Path(str(rg.get("inventory") or "")).name.replace("pin_" + a.goal, "").replace(".json", "") or "-"
        model = "Pro" if str(j.get("model", "")).startswith("e6fa") else "Flash"
        gate = {Path(g.get("render", "")).name: ("PASS" if not g.get("fails") else "FAIL " + ",".join(sorted(set(map(str, g["fails"]))))) for g in j.get("pose_gate") or []}
        cells = []
        for r in j.get("results") or []:
            for e in r.get("evaluations") or []:
                s = e.get("raw_score")
                cells.append(f"{e['raw_file'][:2]} id={'none' if s is None else f'{s:.2f}'} {gate.get(e['raw_file'], '?')}")
        calls = (j.get("credits") or {}).get("calls") or []
        noimg = sum(1 for c in calls if c.get("outcome") != "image")
        faces = len((rg.get("roles") or {}).get("face") or [])
        print(f"{d.name[:15]}  {model:5s} {inv:6s} faces={faces}  " + ("; ".join(cells) or "no render") + (f"  ({noimg} call(s) without an image)" if noimg else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
