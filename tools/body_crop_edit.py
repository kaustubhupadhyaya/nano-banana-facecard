"""His body under an untouched head: edit only a body crop with Gemini, then paste it back (the user's option A, 2026-09-27).

Every extra Gemini edit pass of the whole photo re-levelled his bowed head into a camera stare, and a single pass kept the goal man's heavy
build. Here Gemini sees only the body, from just below the beard down to the hips, so there is no head for it to redraw; code copies the new
body back inside the body outline (union of the old and new person masks, feathered), and every pixel outside that stays the base's.

    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\body_crop_edit.py make  <base.jpg> <out_dir>
        -> <out_dir>\\body_crop.jpg + body_crop.json (the crop box in base pixels)
    (Gemini edit of body_crop.jpg: facecard.py gen --goal <out_dir>\\body_crop.jpg --replace-subject --body-only ...)
    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\body_crop_edit.py paste <base.jpg> <out_dir> <returned.jpg> <result.jpg>
        -> the composite + <result>_paste.json (alignment of the return, mask area) and <result>_seam.jpg (zoom on the neck edge)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pose_compare as PC  # noqa: E402


def person_mask(img: np.ndarray) -> np.ndarray | None:
    r = PC.model("yolo11m-seg.pt").predict(img, imgsz=1024, conf=0.25, classes=[0], retina_masks=True, verbose=False)[0]
    if r.masks is None or not len(r.masks):
        return None
    m = r.masks.data.cpu().numpy()
    return (m[int(np.argmax(m.reshape(len(m), -1).sum(1)))] > 0.5).astype(np.uint8)


def make(base: Path, out: Path) -> int:
    img = PC.load(base)
    H, W = img.shape[:2]
    kp = PC.read(img)["person"]["kp"]
    P = lambda k: (kp[k][0] * W, kp[k][1] * H)
    nose, ls, rs = P("nose"), P("l_shoulder"), P("r_shoulder")
    sh_y = (ls[1] + rs[1]) / 2
    top = nose[1] + 0.62 * (sh_y - nose[1])            # just below the beard, above the collar
    xs = [P(k)[0] for k in ("l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist") if kp[k][2] >= PC.CONF]
    ys = [P(k)[1] for k in ("l_hip", "r_hip", "l_elbow", "r_elbow", "l_wrist", "r_wrist") if kp[k][2] >= PC.CONF]
    span = max(xs) - min(xs)
    x0, x1 = int(max(0, min(xs) - 0.30 * span)), int(min(W, max(xs) + 0.20 * span))
    y0, y1 = int(max(0, top)), int(min(H, max(ys) + 0.15 * span))
    out.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out / "body_crop.jpg"), img[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 96])
    (out / "body_crop.json").write_text(json.dumps({"base": str(base), "box": [x0, y0, x1, y1]}), encoding="utf-8")
    print(f"crop {x1 - x0}x{y1 - y0} at {x0},{y0} -> {out / 'body_crop.jpg'}")
    return 0


def paste(base: Path, out: Path, ret: Path, result: Path) -> int:
    img = PC.load(base)
    x0, y0, x1, y1 = json.loads((out / "body_crop.json").read_text(encoding="utf-8"))["box"]
    crop = img[y0:y1, x0:x1]
    new = cv2.resize(PC.load(ret), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    # Refuse a re-framed return: the frame's outer ring (background) must line up with the original crop's.
    g0, g1 = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(g0, g1, warp, cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), None, 5)
    except cv2.error:
        cc = 0.0
    new = cv2.warpAffine(new, warp, (new.shape[1], new.shape[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    m0, m1 = person_mask(crop), person_mask(new)
    if m0 is None or m1 is None:
        print("no person mask in the crop or the return")
        return 1
    m = cv2.dilate(np.maximum(m0, m1), np.ones((9, 9), np.uint8))
    m[:6, :] = 0                                        # never touch the top rows: the neck edge under the beard stays the base's
    fm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 4)[..., None]
    comp = img.copy()
    comp[y0:y1, x0:x1] = (new * fm + crop * (1 - fm)).astype(np.uint8)
    cv2.imwrite(str(result), comp, [cv2.IMWRITE_JPEG_QUALITY, 95])
    info = {"ecc": round(float(cc), 3), "shift_px": [round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1)],
            "mask_share": round(float(m.mean()), 3), "box": [x0, y0, x1, y1]}
    Path(str(result) + "_paste.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    zy0, zy1 = max(0, y0 - 60), min(img.shape[0], y0 + 120)
    zx0, zx1 = x0 + (x1 - x0) // 4, x0 + 3 * (x1 - x0) // 4
    z = np.hstack([img[zy0:zy1, zx0:zx1], np.full((zy1 - zy0, 6, 3), 255, np.uint8), comp[zy0:zy1, zx0:zx1]])
    cv2.imwrite(str(result.with_name(result.stem + "_seam.jpg")), cv2.resize(z, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
    print(f"{result}  {info}")
    return 0 if cc >= 0.8 else 2


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "make" and len(a) == 3:
        sys.exit(make(Path(a[1]), Path(a[2])))
    if a and a[0] == "paste" and len(a) == 5:
        sys.exit(paste(Path(a[1]), Path(a[2]), Path(a[3]), Path(a[4])))
    print(__doc__)
    sys.exit(1)
