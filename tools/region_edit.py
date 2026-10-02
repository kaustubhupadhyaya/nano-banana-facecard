"""Fix a few objects in a finished render without touching the rest: cut a region (no head in it), let Gemini edit only that crop (gen with an
inventory in "objects" mode), and paste the edited crop back with a feathered border. A re-framed return is refused (ECC < 0.8), as in
replicate. Plan step 7 (2026-09-28): the pin's handguards and frame sliders were the only inventory items missing.

    .venv\\Scripts\\python.exe tools\\region_edit.py make  <render> <x0> <y0> <x1> <y1> <crop.jpg>      (fractions of the frame)
    .venv\\Scripts\\python.exe tools\\region_edit.py paste <render> <crop.jpg> <returned> <result.jpg>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np


def make(render: Path, fx0, fy0, fx1, fy1, crop: Path) -> int:
    img = cv2.imread(str(render))
    H, W = img.shape[:2]
    box = [int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H)]
    x0, y0, x1, y1 = box
    crop.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(crop), img[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 97])
    Path(str(crop) + ".json").write_text(json.dumps({"render": str(render), "box": box}), encoding="utf-8")
    print(crop, box)
    return 0


def paste(render: Path, crop: Path, ret: Path, result: Path) -> int:
    img = cv2.imread(str(render))
    x0, y0, x1, y1 = json.loads(Path(str(crop) + ".json").read_text(encoding="utf-8"))["box"]
    orig = img[y0:y1, x0:x1]
    new = cv2.resize(cv2.imread(str(ret)), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), cv2.cvtColor(new, cv2.COLOR_BGR2GRAY), warp,
                                        cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), None, 5)
    except cv2.error:
        cc = 0.0
    if cc < 0.8:
        print(f"refused: the return is re-framed (ECC {cc:.3f} < 0.8)")
        return 2
    new = cv2.warpAffine(new, warp, (new.shape[1], new.shape[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    h, w = orig.shape[:2]
    m = np.zeros((h, w), np.float32)
    b = 14
    m[b:h - b, b:w - b] = 1
    m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]
    out = img.copy()
    out[y0:y1, x0:x1] = (new * m + orig * (1 - m)).astype(np.uint8)
    cv2.imwrite(str(result), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(result, {"ecc": round(float(cc), 3), "shift": [round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1)]})
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["make"] and len(a) == 7:
        sys.exit(make(Path(a[1]), *map(float, a[2:6]), Path(a[6])))
    if a[:1] == ["paste"] and len(a) == 5:
        sys.exit(paste(*map(Path, a[1:])))
    print(__doc__)
    sys.exit(1)
