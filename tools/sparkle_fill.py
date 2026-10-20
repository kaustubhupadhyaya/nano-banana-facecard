"""Remove Gemini's sparkle watermark from ONE picture by filling only the star's own pixels from the picture's wall around it (OpenCV inpainting),
with the wall's own grain added back. Every other pixel stays byte-identical (asserted). For a render whose framing no longer lines up with the
pin, where `background_restore.py --only-sparkle` cannot copy the pin's pixels, or where the pin's corner is a different brightness (2026-10-21:
the pin's patch showed as a dark disc on pin 4's 10-01 render; this fill was clean at 2x and the user replaced the export with it).

    .venv\\Scripts\\python.exe tools\\sparkle_fill.py <picture> <out vN_Ms.jpg> [--sheet <corner sheet.jpg>]

Only for a plain corner (wall, sky): when objects sit under the star (pin 6's knife and jar, pin 8's table edge) it exits 3 and writes nothing, since a
fill there smears them (2026-10-21). Then show the user the corner sheet; record the copy with tools\\best_check.py (--user-approved) and the original with --superseded-by.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

OFFSET, RADIUS = 120, 75          # px: the star sits about 120 px in from the bottom-right corner (background_restore.SPARKLE_OFFSET)


BUSY = 9.0                        # corner texture above which the fill is refused: plain walls measured 1.1-7.3, pin 6's knife and jar 18-24, pin 8's table edge 13


def corner_texture(img: np.ndarray) -> float:
    """How busy the ring around the star is (the standard deviation of the picture minus its own blur): a plain wall is low, objects are high."""
    h, w = img.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    d2 = (xx - (w - OFFSET)) ** 2 + (yy - (h - OFFSET)) ** 2
    ring = (d2 <= 100 ** 2) & (d2 >= 45 ** 2)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float((g - cv2.GaussianBlur(g, (0, 0), 6))[ring].std())


EXPECTED_AREA_922 = 2970         # px: the dilated star mask on the 922-px-wide render of 2026-10-01 (pin 4); it scales with the picture's width squared


def star_mask(img: np.ndarray) -> np.ndarray:
    """The star's own pixels. First the plain rule (brighter than the wall's median around it); when that picks up far more than a star (2026-10-21,
    pin 15: a bright patch of wall beside the star was taken too, and the fill smeared it), a stricter threshold is tried until the one compact shape
    nearest the expected spot is left."""
    h, w = img.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    zone = ((xx - (w - OFFSET)) ** 2 + (yy - (h - OFFSET)) ** 2) <= RADIUS ** 2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    local = cv2.medianBlur(gray, 151).astype(np.float32)        # wider than the star, so its core is compared with the wall, not itself
    diff = gray.astype(np.float32) - local
    expected = EXPECTED_AREA_922 * (w / 922.0) ** 2
    grow = lambda m: cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2) > 0      # noqa: E731
    first = grow(zone & (diff > 10))
    if first.sum() <= 1.6 * expected:
        return first
    cx, cy = w - OFFSET, h - OFFSET
    for t in (14, 18, 24, 30, 40, 55):
        n, lab, st, cen = cv2.connectedComponentsWithStats((zone & (diff > t)).astype(np.uint8), connectivity=8)
        best, best_d = None, 1e9
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 150:
                continue
            d = float(np.hypot(cen[i][0] - cx, cen[i][1] - cy))
            if d < best_d:
                best, best_d = i, d
        if best is not None and grow(lab == best).sum() <= 1.6 * expected:
            return grow(lab == best)
    return first


def fill(img: np.ndarray) -> tuple[np.ndarray, int]:
    h, w = img.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    zone = ((xx - (w - OFFSET)) ** 2 + (yy - (h - OFFSET)) ** 2) <= RADIUS ** 2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    star = star_mask(img)
    filled = cv2.inpaint(img, star.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA)
    ring = zone & ~cv2.dilate(star.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    hp = img.astype(np.float32) - cv2.GaussianBlur(img.astype(np.float32), (0, 0), 1.5)
    sigma = hp[ring].std(axis=0)                                # the wall's own grain, per channel
    noise = np.random.default_rng(7).normal(0.0, 1.0, img.shape).astype(np.float32) * sigma
    out = img.copy()
    out[star] = np.clip(filled.astype(np.float32)[star] + noise[star], 0, 255).astype(np.uint8)
    assert (out[~star] == img[~star]).all()
    return out, int(star.sum())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture")
    ap.add_argument("out")
    ap.add_argument("--sheet", default=None, help="a before/after sheet of the corner at 2x")
    ap.add_argument("--max-busy", type=float, default=BUSY, dest="max_busy",
                    help=f"refuse a corner busier than this (default {BUSY}); raise it for a borderline corner and judge the sheet by eye")
    a = ap.parse_args()
    img = cv2.imread(a.picture)
    busy = corner_texture(img)
    if busy > a.max_busy:
        print(f"busy corner (texture {busy:.1f} > {BUSY}): objects sit under the star, a fill would smear them; left as Gemini drew it, no copy written")
        return 3
    out, n = fill(img)
    cv2.imwrite(a.out, out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    h, w = img.shape[:2]
    print(f"{Path(a.out).name}: {n} star pixels filled ({n / (h * w) * 100:.2f}% of the frame); every other pixel unchanged")
    if a.sheet:
        box = (w - 260, h - 260, w, h)
        s = Image.new("RGB", (1048, 520), "white")
        s.paste(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).crop(box).resize((520, 520)), (0, 0))
        s.paste(Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).crop(box).resize((520, 520)), (528, 0))
        s.save(a.sheet, quality=92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
