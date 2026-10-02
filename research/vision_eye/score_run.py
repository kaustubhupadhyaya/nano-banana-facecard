"""Score every attempt of one or more runs with TruFor's pasted-look measure (his own photos only; see README: on another man's photo it is blind).

    .venv\\Scripts\\python.exe research\\vision_eye\\score_run.py outputs\\<run> [outputs\\<run> ...]

Per attempt: how much more the face lights up than the real photo around the crop, minus the same on the untouched source. On the benchmark the
picture the user disliked scored higher than the one they liked in 16 of 17 same-photo pairs (rocky "lasso-ed" 1.18, liked 0.02-0.58;
IMG_0862 two heads 1.04, perfect 0.33). Lower = less pasted-looking. A ranking signal, not a verdict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from eyes import trufor  # noqa: E402


def cases_of(run_dir: Path) -> list[dict]:
    data = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    scene = (data.get("args") or {}).get("scene") or data.get("scene")
    src = Path(scene) if isinstance(scene, str) else None
    if src is not None and not src.is_absolute():
        src = ROOT / src
    W, H = data["size"]
    out = []
    for c in data.get("candidates", []):
        pic = run_dir / f"cand{c['index']}.png"
        if pic.exists():
            out.append({"id": f"L{run_dir.name[:15]}_c{c['index']}", "picture": str(pic), "source": str(src) if src and src.exists() else None,
                        "region": data["crop"], "size": [W, H], "kind": data.get("source_kind"), "verdict_pipeline": c.get("verdict")})
    return out


def main() -> int:
    runs = [Path(a) if Path(a).is_absolute() else ROOT / a for a in sys.argv[1:]]
    cases = [c for r in runs for c in cases_of(r)]
    trufor.prepare(cases)
    for c in cases:
        r = trufor.judge(c)
        sc = "-" if r.get("score") is None else f"{r['score']:+.3f}"
        print(f"{c['id']:32s} {c['kind'] or '':7s} pipeline {str(c['verdict_pipeline']):9s} pasted-look {sc:>7s}   {r['why']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
