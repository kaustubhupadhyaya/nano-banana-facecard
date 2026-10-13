"""Fix a few objects in a finished render without touching the rest: cut a region (no head in it), let Gemini edit only that crop (gen with an
inventory in "objects" mode), and paste the edited crop back with a feathered border. A re-framed return is refused (ECC < 0.8), as in
replicate. Plan step 7 (2026-09-28): the pin's handguards and frame sliders were the only inventory items missing.

    .venv\\Scripts\\python.exe tools\\region_edit.py make  <render> <x0> <y0> <x1> <y1> <crop.jpg>      (fractions of the frame)
    .venv\\Scripts\\python.exe tools\\region_edit.py paste <render> <crop.jpg> <returned> <result.jpg>
    .venv\\Scripts\\python.exe tools\\region_edit.py paste-run <render> <crop.jpg> <run folder>      (each vN_M.jpg -> vN_Mr.jpg, paste.json)
A crop's .json may hold "below": [[x, y], [x, y]] (picture pixels): then only the part of the crop below that line is pasted back; and/or
"mask": a crop-sized PNG (white = pasted back, e.g. the grey area of tools/physique_greyout.py); "feather": the soft edge's blur in picture
pixels (default 6; pin 16's eyes-only paste uses 2).
`--affine` (paste, paste-run): the return is aligned by scale + shift fitted on the background outside the mask only (refused below ECC 0.85,
or when the fit is not a plain scale), instead of a shift fitted on the whole crop: when the grey area is large, the whole-crop fit refuses an
aligned return (back round 4, 2026-10-10: ECC 0.76 whole, 0.97 on the background at scale 1.00).
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


SHIFT_MAX = 0.015      # a return shifted by more than this share of the crop is refused (2026-10-10: 120 px pasted a second waistband);
                       # `--max-shift 0.03` raises it for one call (2026-10-14, pin 13: a head that really turned, ECC 0.909, 5 px on a 280 px crop)


def paste(render: Path, crop: Path, ret: Path, result: Path, affine: bool = False) -> int:
    img = cv2.imread(str(render))
    meta = json.loads(Path(str(crop) + ".json").read_text(encoding="utf-8"))
    x0, y0, x1, y1 = meta["box"]
    orig = img[y0:y1, x0:x1]
    returned = cv2.imread(str(ret))
    eh, ew = returned.shape[:2]
    new = cv2.resize(returned, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    warp = np.eye(2, 3, dtype=np.float32)
    if affine:
        # --affine (2026-10-10, back round 4): the whole-crop fit refused both returns as re-framed (ECC 0.76-0.77), yet on the background alone they
        # fit at scale 1.00 and a 3 px shift (ECC 0.97): the grey body, half the crop, differs on purpose. Fitted here on the background only (outside
        # the grey area grown by 6%), as scale + shift, so a return that really is zoomed is aligned too
        g = None
        if meta.get("mask"):
            g = cv2.imread(meta["mask"], cv2.IMREAD_GRAYSCALE)
            g = cv2.resize(g, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_NEAREST) if g.shape[:2] != orig.shape[:2] else g
            k = int(0.06 * max(orig.shape[:2])) | 1
            g = (cv2.dilate((g > 0).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) == 0).astype(np.uint8)
        try:
            cc, warp = cv2.findTransformECC(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), cv2.cvtColor(new, cv2.COLOR_BGR2GRAY), warp,
                                            cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), g, 5)
        except cv2.error:
            cc = 0.0
        sx, sy = float(np.hypot(warp[0, 0], warp[1, 0])), float(np.hypot(warp[0, 1], warp[1, 1]))
        if cc < 0.85 or abs(sx - sy) > 0.02 or not 0.8 <= sx <= 1.25:
            print(f"refused: no clean scale + shift fit on the background (ECC {cc:.3f}, scale {sx:.3f} / {sy:.3f})")
            return 2
    else:
        try:
            cc, warp = cv2.findTransformECC(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), cv2.cvtColor(new, cv2.COLOR_BGR2GRAY), warp,
                                            cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), None, 5)
        except cv2.error:
            cc = 0.0
        if cc < 0.8:
            print(f"refused: the return is re-framed (ECC {cc:.3f} < 0.8)")
            return 2
        shift = float(np.hypot(warp[0, 2], warp[1, 2]))
        if shift > SHIFT_MAX * max(orig.shape[:2]):
            # 2026-10-10, physique round 3: a return shifted 120 px (ECC 0.87) pasted a second waistband into the picture
            print(f"refused: the return is shifted {shift:.0f} px (> 1.5% of the crop), ECC {cc:.3f}")
            return 2
    new = cv2.warpAffine(new, warp, (new.shape[1], new.shape[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    h, w = orig.shape[:2]
    m = np.zeros((h, w), np.float32)
    b = 14
    # the 14 px kept from the picture only on sides inside the picture: a side on the frame's edge has no seam to hide (2026-10-11, pin 16
    # calf: the bottom 14 px kept the pin man's tattoo where the crop ended at the frame's bottom edge)
    ih, iw = img.shape[:2]
    m[0 if y0 <= 0 else b:h if y1 >= ih else h - b, 0 if x0 <= 0 else b:w if x1 >= iw else w - b] = 1
    below = meta.get("below")
    if below:
        # only the part of the crop below this line (full-picture pixels) is pasted; above it the render keeps its own pixels (2026-10-10, pizza
        # beard: Gemini sees his whole head, but the eyes the user liked stay byte-identical)
        (ax, ay), (bx, by) = [(px - x0, py - y0) for px, py in below]
        nx, ny = -(by - ay), bx - ax
        if ny < 0:
            nx, ny = -nx, -ny
        yy, xx = np.mgrid[0:h, 0:w]
        m *= (((xx - ax) * nx + (yy - ay) * ny) > 0).astype(np.float32)
    if meta.get("mask"):
        # only this area is pasted back (tools/physique_greyout.py: the grey torso and upper arms); grown a little so the soft edge lies on
        # Gemini's redraw, never on a grey pixel left behind
        gm = cv2.imread(meta["mask"], cv2.IMREAD_GRAYSCALE)
        gm = cv2.resize(gm, (w, h), interpolation=cv2.INTER_NEAREST) if gm.shape[:2] != (h, w) else gm
        k = max(3, int(0.012 * max(h, w)) | 1)
        m *= (cv2.dilate((gm > 0).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0).astype(np.float32)
    # Gemini's sparkle watermark (replicate.SPARKLE_OFFSET/RADIUS: 120 px in from the returned image's bottom-right corner, about 52 px wide) is
    # never pasted (2026-10-10: the pizza beard fix pasted it onto the sweater). It moved with the alignment shift: aligned = returned - t.
    sx = w / ew
    hx, hy, hr = (ew - 120.0) * sx - float(warp[0, 2]), (eh - 120.0) * (h / eh) - float(warp[1, 2]), 52.0 * sx * 1.35
    if affine:
        # the aligned picture is the return scaled: the sparkle's place there is A^-1 (p - t), its size divided by the scale
        a = np.linalg.inv(warp[:, :2].astype(np.float64))
        hx, hy = a @ np.array([(ew - 120.0) * sx - float(warp[0, 2]), (eh - 120.0) * (h / eh) - float(warp[1, 2])])
        hr = hr / float(np.sqrt(abs(np.linalg.det(warp[:, :2].astype(np.float64)))))
    yy, xx = np.mgrid[0:h, 0:w]
    m[np.hypot(xx - hx, yy - hy) < hr] = 0
    # "feather" in the crop's .json (2026-10-12, pin 16's eyes, picture px): the soft edge's blur. A crop without it keeps 6. An eyes-only mask on a
    # 30 px eye distance needs about 2: the brows sit 5 px above the lids, and 6 would blend the old and the new eye at the lid line
    m = cv2.GaussianBlur(m, (0, 0), float(meta.get("feather", 6)))[..., None]
    if meta.get("soft_mask"):
        # a weight map (0-255) multiplied in after the blur, e.g. a long ramp along an edge where Gemini's patch is a shade lighter than the picture
        # around it (2026-10-10, the back wrist fix: a hard 20 px border showed as a seam across his forearm)
        sm = cv2.imread(meta["soft_mask"], cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
        sm = cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR) if sm.shape[:2] != (h, w) else sm
        m = m * sm[..., None]
    out = img.copy()
    out[y0:y1, x0:x1] = (new * m + orig * (1 - m)).astype(np.uint8)
    cv2.imwrite(str(result), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    fit = {"ecc": round(float(cc), 3), "shift": [round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1)]}
    if affine:
        fit["scale"] = [round(float(np.hypot(warp[0, 0], warp[1, 0])), 3), round(float(np.hypot(warp[0, 1], warp[1, 1])), 3)]
    print(result, fit)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["make"] and len(a) == 7:
        sys.exit(make(Path(a[1]), *map(float, a[2:6]), Path(a[6])))
    affine = "--affine" in a
    a = [x for x in a if x != "--affine"]
    if "--max-shift" in a:
        i = a.index("--max-shift")
        SHIFT_MAX = float(a[i + 1])
        print(f"shift limit raised for this call: {SHIFT_MAX:.3f} of the crop (default 0.015)")
        a = a[:i] + a[i + 2:]
    if a[:1] == ["paste"] and len(a) == 5:
        sys.exit(paste(*map(Path, a[1:]), affine=affine))
    if a[:1] == ["paste-run"] and len(a) == 4:
        # every returned picture vN_M.jpg of a region-edit recipe run pasted back into <render>, written as vN_Mr.jpg beside it
        # (2026-10-10: the pizza third picture, _v1 with v2_0r's eyes); a re-framed return is refused and recorded in paste.json
        import re
        render, crop, run = map(Path, a[1:])
        rows, ok = [], 0
        for ret in sorted(run.iterdir()):
            if not re.match(r"^v\d+_\d+\.(jpg|jpeg|png)$", ret.name, re.I):
                continue
            out = ret.with_name(ret.stem + "r.jpg")
            rc = paste(render, crop, ret, out, affine=affine)
            rows.append({"returned": ret.name, "result": out.name if rc == 0 else None, "refused": rc != 0})
            ok += rc == 0
        (run / "paste.json").write_text(json.dumps({"render": str(render), "crop": str(crop), "affine": affine, "pictures": rows}, indent=1),
                                        encoding="utf-8")
        print(f"{ok} of {len(rows)} pasted back -> {run / 'paste.json'}")
        sys.exit(0 if ok else 1)
    print(__doc__)
    sys.exit(1)
