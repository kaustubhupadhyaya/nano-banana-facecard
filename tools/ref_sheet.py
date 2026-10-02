"""Reference images by role for an inventory run, cut by code from his own photos (the user, 2026-09-27: his tank pattern, helmet, watch and the
bike's accessories kept coming out as the goal's). Also a clean photo to edit: the goal's watermark inpainted so it cannot be carried over.

    .venv\\Scripts\\python.exe tools\\ref_sheet.py pin     -> .cache\\inventories\\pin_refs\\*.jpg  (+ the clean goal)

Panel boxes are in each source photo's own pixels and were read off the photos by eye (2026-09-28).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replicate import load_source  # noqa: E402

BIKE = Path(r"C:\Users\Admin\Downloads\CB350 bike photos\bike alone")
OUT = ROOT / ".cache" / "inventories" / "pin_refs"


def crop(img, box, height=560):
    x0, y0, x1, y1 = box
    c = img[y0:y1, x0:x1]
    k = height / c.shape[0]
    return cv2.resize(c, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def labelled(panel, text):
    bar = np.full((44, panel.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 0, 0), 2, cv2.LINE_AA)
    return np.vstack([bar, panel])


def pin() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    side = load_source(BIKE / "01_BEST_side_day_facing_right__IMG_5857.jpg")      # 4032x2268
    tq = load_source(BIKE / "06_front34_street_plate__IMG_5162.jpg")                 # 4032x2268
    arms = load_source(Path(r"D:\Downloads\FaceCard_Originals\IMG_0440_Original.jpg"))  # 1908x2746

    # bike, side: the whole bike (his helmet stays on the seat: it is his helmet)
    s = side[330:2020, 520:3480]
    k = 2048 / max(s.shape[:2])
    cv2.imwrite(str(OUT / "bike_side.jpg"), cv2.resize(s, None, fx=k, fy=k, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 94])

    # bike, front three-quarter: the number plate is blurred (the user did not choose the plate)
    t = tq.copy()
    px0, py0, px1, py1 = 2700, 980, 3110, 1210
    t[py0:py1, px0:px1] = cv2.GaussianBlur(t[py0:py1, px0:px1], (0, 0), 25)
    t = t[180:2268, 500:3900]
    k = 2048 / max(t.shape[:2])
    cv2.imwrite(str(OUT / "bike_3q.jpg"), cv2.resize(t, None, fx=k, fy=k, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 94])

    # HIS ITEMS sheet: A tank close-up, B helmet, C watch
    a = labelled(crop(tq, (1500, 500, 2420, 1120)), "A: HIS TANK PAINT")
    b = labelled(crop(side, (900, 380, 1480, 780)), "B: HIS HELMET")
    c = labelled(crop(arms, (1130, 1260, 1480, 1600)), "C: HIS WATCH")
    h = max(p.shape[0] for p in (a, b, c))
    row = np.hstack([cv2.copyMakeBorder(p, 0, h - p.shape[0], 0, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for p in (a, b, c)])
    cv2.imwrite(str(OUT / "his_items.jpg"), row, [cv2.IMWRITE_JPEG_QUALITY, 94])

    # the photo to edit: the goal with its watermark inpainted (bottom-left white text over grass)
    g = cv2.imread(str(ROOT / ".cache" / "pin_783485666539775315.jpg"))
    H, W = g.shape[:2]
    m = np.zeros((H, W), np.uint8)
    y0, x1 = H - 18, 150
    zone = cv2.cvtColor(g[y0:H, 0:x1], cv2.COLOR_BGR2GRAY)
    m[y0:H, 0:x1] = (zone > 170).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    clean = cv2.inpaint(g, m, 5, cv2.INPAINT_TELEA)
    cv2.imwrite(str(ROOT / ".cache" / "pin_783485666539775315_clean.jpg"), clean, [cv2.IMWRITE_JPEG_QUALITY, 96])
    cv2.imwrite(str(OUT / "_watermark_check.jpg"), cv2.resize(np.vstack([g[H - 40:H, 0:220], clean[H - 40:H, 0:220]]), None, fx=4, fy=4,
                                                               interpolation=cv2.INTER_CUBIC))
    print("refs in", OUT, "| clean goal written; watermark pixels", int((m > 0).sum()))
    return 0


if __name__ == "__main__":
    sys.exit(pin() if sys.argv[1:] == ["pin"] else (print(__doc__) or 1))
