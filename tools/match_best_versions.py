"""Match every picture in D:\\Downloads\\AI me (the user's best versions, which the user may add by hand) to the run and attempt that made it, by pixel
content, and record the new ones in facecard.json "best_versions" (md5, run, attempt). A source whose file content equals a best version is returned
unchanged by replicate unless --force.

    .venv\\Scripts\\python.exe tools\\match_best_versions.py            # report only
    .venv\\Scripts\\python.exe tools\\match_best_versions.py --record   # also record new matches in facecard.json
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import BEST_DIR, FEEDBACK, OUTPUTS, load_config, md5, run_dirs, save_config  # noqa: E402


def load(p: Path):
    img = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if img is None:
        try:
            from PIL import Image
            img = cv2.cvtColor(np.asarray(Image.open(p).convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception:
            return None
    return img


def small(img, w=192):
    return cv2.resize(img, (w, int(round(img.shape[0] * w / img.shape[1]))), interpolation=cv2.INTER_AREA).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()
    pool = []
    for d in run_dirs(OUTPUTS, FEEDBACK):
        for p in d.iterdir():
            if p.is_file() and (re.fullmatch(r"cand\d+\.png", p.name) or p.name.startswith(("best.", "not_passing_closest", "v1_0"))):
                img = load(p)
                if img is not None:
                    pool.append((p, img.shape[1] / img.shape[0], small(img)))
    cfg = load_config()
    best = cfg.setdefault("best_versions", {})
    known = {v.get("md5") for v in best.values() if isinstance(v, dict)}
    added = 0
    for t in sorted(BEST_DIR.iterdir()) if BEST_DIR.is_dir() else []:
        img = load(t)
        if img is None:
            continue
        h = md5(t)
        ar, st = img.shape[1] / img.shape[0], small(img)
        hits = sorted((float(np.abs(s - st).mean()), p) for p, a, s in pool if abs(a - ar) < 0.01 and s.shape == st.shape)
        top = hits[0] if hits else None
        status = "recorded" if h in known else "NEW"
        print(f"{t.name:40s} {status:9s} " + (f"best match {top[1]} (difference {top[0]:.2f})" if top else "no matching run"))
        if args.record and h not in known and top and top[0] < 1.0:
            p = top[1]
            m = re.match(r"cand(\d+)\.png", p.name)
            best[str(t).replace("\\", "/")] = {"md5": h, "run": p.parent.name, "which": f"attempt {m.group(1)}" if m else p.name,
                                               "what": "added by the user to D:/Downloads/AI me; matched by pixel content"}
            added += 1
    if args.record:
        save_config(cfg)
        print(f"{added} new best version(s) recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
