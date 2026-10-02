"""Score an eye on the labelled benchmark (build it first with build_bench.py).

    .venv\\Scripts\\python.exe research\\vision_eye\\bench.py texture          # runs research\\vision_eye\\eyes\\texture.py

An eye is a module in eyes\\ with   judge(case: dict) -> {"flag": bool | None, "score": float | None, "why": str}
(case = one manifest entry: label, verdict, picture, source, region, context_box, views). The go/no-go rule is the one used since 2026-09-24:
an eye is usable only if it flags every "flag" picture and passes every "pass" picture. A score, when the eye gives one, is also reported as the
best threshold on this set: that number is fitted on the same 31 pictures, so it only says whether the signal separates them at all.
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
BENCH = ROOT / ".cache" / "vision_bench"


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "texture"
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    eye = importlib.import_module(f"eyes.{name}")
    cases = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    if hasattr(eye, "prepare"):   # an eye that runs once over all pictures (a model loaded once, results cached)
        eye.prepare([c for c in cases if not only or c["id"] in only])
    rows = []
    for c in cases:
        if only and c["id"] not in only:
            continue
        t0 = time.time()
        try:
            r = eye.judge(c)
        except Exception as e:  # an eye that cannot judge a case says so; it does not stop the benchmark
            r = {"flag": None, "score": None, "why": f"error {type(e).__name__}: {e}"}
        r["sec"] = round(time.time() - t0, 1)
        right = None if c["label"] == "info" or r.get("flag") is None else (r["flag"] == (c["label"] == "flag"))
        rows.append({**{k: c[k] for k in ("id", "label", "verdict")}, **r, "right": right})
        sc = "-" if r.get("score") is None else f"{r['score']:+.3f}"
        mark = "" if right is None else ("ok" if right else "WRONG")
        print(f"{c['id']} {c['label']:4s} {'FLAG' if r.get('flag') else 'pass' if r.get('flag') is False else '----'} {sc:>8s} {mark:5s} "
              f"{r['sec']:5.1f}s  {str(r.get('why', ''))[:110]}", flush=True)
    (BENCH / f"results_{name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    fl = [r for r in rows if r["label"] == "flag" and r.get("flag") is not None]
    ps = [r for r in rows if r["label"] == "pass" and r.get("flag") is not None]
    caught = sum(1 for r in fl if r["flag"])
    false_alarms = sum(1 for r in ps if r["flag"])
    print(f"\n{name}: caught {caught}/{len(fl)} flag pictures, false alarms on {false_alarms}/{len(ps)} pass pictures "
          f"-> {'USABLE' if fl and ps and caught == len(fl) and false_alarms == 0 else 'not usable as a gate'}")
    scored = [r for r in rows if r["label"] in ("flag", "pass") and r.get("score") is not None]
    if scored:
        best = None
        for t in sorted({r["score"] for r in scored}):
            for sign in (1, -1):   # flag when score >= t, or when score <= t
                ok = sum(1 for r in scored if ((sign * r["score"] >= sign * t) == (r["label"] == "flag")))
                if best is None or ok > best[0]:
                    best = (ok, t, sign)
        print(f"best single threshold on this set (fitted, optimistic): flag when score {'>=' if best[2] == 1 else '<='} {best[1]:+.3f} "
              f"-> {best[0]}/{len(scored)} right")
    return 0


if __name__ == "__main__":
    sys.exit(main())
