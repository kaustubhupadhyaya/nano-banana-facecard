"""Build check by eye, done fairly: upper bodies (head to hips) of his body references, the goal and each render, all cropped around the
body keypoints and scaled to the SAME torso length, side by side. The user, 2026-09-27: "pinterest generations any versions are not using
my body" -- the renders kept the goal man's heavy build. An automatic build measure (arm/shoulder ratios from masks) failed validation the
same day (it read the goal man as slimmer than him), so this sheet is how item 26's physique is judged, with the user's eye as the check.

    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\body_sheet.py --out <sheet.jpg> <his ref> [<his ref>] <goal> <render> [...]
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pose_compare as PC  # noqa: E402

TORSO_PX = 260      # every panel's shoulder-to-hip length in pixels


def panel(path: Path):
    img = PC.load(path)
    H, W = img.shape[:2]
    p = PC.read(img)["person"]
    if not p:
        return None
    kp = p["kp"]
    sh, hp = PC.point(kp, "mid_sh"), PC.point(kp, "mid_hip")
    if not (sh and hp):
        return None
    torso = math.hypot((hp[0] - sh[0]) * W, (hp[1] - sh[1]) * H)
    k = TORSO_PX / torso
    big = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    cx, cy = sh[0] * W * k, sh[1] * H * k
    x0, y0 = int(cx - 1.3 * TORSO_PX), int(cy - 0.9 * TORSO_PX)
    x1, y1 = int(cx + 1.3 * TORSO_PX), int(cy + 1.25 * TORSO_PX)
    canvas = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8)
    sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, big.shape[1]), min(y1, big.shape[0])
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = big[sy0:sy1, sx0:sx1]
    cv2.putText(canvas, path.stem[:28], (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 220), 2)
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pictures", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    panels = [q for q in (panel(Path(p)) for p in a.pictures) if q is not None]
    h = max(p.shape[0] for p in panels)
    row = np.hstack([cv2.copyMakeBorder(p, 0, h - p.shape[0], 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for p in panels])
    cv2.imwrite(a.out, row, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(a.out, len(panels), "panels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
