"""Review sheet for the best-picture checklist: the goal (or source) next to each render, whole picture on top and the head zoomed below, so every
item of BEST_CHECKLIST.md is judged on the same view every time.

    .venv\\Scripts\\python.exe tools\\review_sheet.py --goal "<goal or source>" "<render1>" ["<render2>" ...] [--out "<sheet.jpg>"]

Writes <folder of the first render>\\_review.jpg unless --out is given, and prints its path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replicate import detect_faces, load_source  # noqa: E402

H_TOP, H_HEAD = 700, 360


def read(p: str) -> np.ndarray:
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    return img if img is not None else load_source(Path(p))


def head_zoom(img: np.ndarray) -> np.ndarray:
    faces = detect_faces(img, min_px=16)
    if not faces:
        z = img
    else:
        x, y, w, h = faces[0]["box"]
        s = int(max(w, h) * 1.6)
        cx, cy = x + w // 2, y + h // 2
        z = img[max(0, cy - s):cy + s, max(0, cx - s):cx + s]
    return cv2.resize(z, (int(H_HEAD * z.shape[1] / z.shape[0]), H_HEAD), interpolation=cv2.INTER_AREA)


def column(img: np.ndarray, label: str) -> np.ndarray:
    top = cv2.resize(img, (int(H_TOP * img.shape[1] / img.shape[0]), H_TOP), interpolation=cv2.INTER_AREA)
    head = head_zoom(img)
    w = max(top.shape[1], head.shape[1])
    col = np.full((H_TOP + H_HEAD + 10, w, 3), 255, np.uint8)
    col[:H_TOP, :top.shape[1]] = top
    col[H_TOP + 10:, :head.shape[1]] = head
    cv2.putText(col, label, (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    return col


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--goal", required=True)
    ap.add_argument("renders", nargs="+")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    cols = [column(read(args.goal), "goal")] + [column(read(r), Path(r).stem) for r in args.renders]
    h = max(c.shape[0] for c in cols)
    sheet = np.hstack([np.vstack([c, np.full((h - c.shape[0], c.shape[1], 3), 255, np.uint8)]) for c in cols])
    out = Path(args.out) if args.out else Path(args.renders[0]).parent / "_review.jpg"
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
