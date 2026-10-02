"""His right head on his own body, both from edits of the SAME goal frame (the user's option A for the pin, 2026-09-27).

Gemini could give either the right head (pin-W v2_0: bowed, sunglasses, him) or his lean body (the slim chain), never both: every whole-photo
pass that slimmed the body re-levelled the head, and a body crop was not reshaped at all (1-3%). Code copies: the head source is aligned to the
body source on the background (ECC, persons masked out), shifted so its nose sits on the body source's head position, and only its HEAD is
pasted - face, beard, brows, eyes, glasses, ears, nose, mouth, hair from a face parser (FaceFusion's BiSeNet) - never its neck or clothes.
Leftovers of the body source's old head that the new head does not cover get the head source's background, or are inpainted.

    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\head_transplant.py <head_src.jpg> <body_src.jpg> <out.jpg> --chin-y PX
        -> out.jpg, out_seam.jpg (2.5x zoom: body source | head source aligned | result), out_transplant.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pose_compare as PC  # noqa: E402
from body_crop_edit import person_mask  # noqa: E402

PARSER = Path(r"C:\Users\Admin\GitHub\facefusion\.assets\models\bisenet_resnet_34.onnx")
HEAD = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18]     # CelebAMask: skin .. lips, hair, hat (not 14 neck, 15 necklace, 16 cloth)
_parser = None


def parse(img: np.ndarray, box) -> np.ndarray:
    """Per-pixel CelebAMask class of img inside box, as a full-size map (0 outside the box)."""
    global _parser
    import onnxruntime as ort
    if _parser is None:
        _parser = ort.InferenceSession(str(PARSER), providers=["CPUExecutionProvider"])
    x0, y0, x1, y1 = box
    crop = img[y0:y1, x0:x1]
    t = cv2.resize(crop, (512, 512))[:, :, ::-1].astype(np.float32) / 255.0
    t = ((t - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)).transpose(2, 0, 1)[None]
    lab = _parser.run(None, {"input": t})[0][0].argmax(0).astype(np.uint8)
    full = np.zeros(img.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = cv2.resize(lab, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)
    return full


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("head_src")
    ap.add_argument("body_src")
    ap.add_argument("out")
    ap.add_argument("--chin-y", type=int, required=True, help="the beard's bottom line in body-source pixels (from a head box read)")
    a = ap.parse_args()
    A, B = PC.load(Path(a.head_src)), PC.load(Path(a.body_src))
    H, W = B.shape[:2]
    if A.shape[:2] != B.shape[:2]:
        A = cv2.resize(A, (W, H), interpolation=cv2.INTER_AREA)
    mA, mB = person_mask(A), person_mask(B)
    bg = (cv2.dilate(np.maximum(mA, mB), np.ones((25, 25), np.uint8)) == 0).astype(np.uint8)
    warp = np.eye(2, 3, dtype=np.float32)
    cc, warp = cv2.findTransformECC(cv2.cvtColor(B, cv2.COLOR_BGR2GRAY), cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), warp, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), bg, 5)
    A = cv2.warpAffine(A, warp, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    ka, kb = PC.read(A)["person"]["kp"], PC.read(B)["person"]["kp"]
    dx, dy = (kb["nose"][0] - ka["nose"][0]) * W, (kb["nose"][1] - ka["nose"][1]) * H
    A = cv2.warpAffine(A, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    mA = person_mask(A)

    ys_, xs_ = np.where(np.maximum(mA, mB)[: a.chin_y + 40] > 0)
    top, bot = max(0, int(ys_.min()) - 20), min(H, a.chin_y + 60)
    side = bot - top
    cx = int(np.median(xs_))
    x0 = max(0, min(W - side, cx - side // 2))
    box = (x0, top, x0 + side, top + side)
    pa, pb = parse(A, box), parse(B, box)
    a_head = cv2.morphologyEx(np.isin(pa, HEAD).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    b_head = np.isin(pb, HEAD).astype(np.uint8)
    left = (b_head > 0) & (a_head == 0)
    use_a_bg = left & (pa == 0)
    fill = (left & (pa != 0)).astype(np.uint8)
    m = cv2.dilate(np.maximum(a_head, use_a_bg.astype(np.uint8)).astype(np.float32), np.ones((3, 3), np.uint8))
    fm = cv2.GaussianBlur(m, (0, 0), 1.8)[..., None]
    out = (A * fm + B * (1 - fm)).astype(np.uint8)
    if fill.any():
        out = cv2.inpaint(out, cv2.dilate(fill, np.ones((5, 5), np.uint8)), 6, cv2.INPAINT_TELEA)
    cv2.imwrite(a.out, out, [cv2.IMWRITE_JPEG_QUALITY, 95])

    y0, y1 = top, min(H, bot + 60)
    zx0, zx1 = max(0, x0 - 20), min(W, x0 + side + 20)
    sep = np.full((y1 - y0, 4, 3), 255, np.uint8)
    z = np.hstack([B[y0:y1, zx0:zx1], sep, A[y0:y1, zx0:zx1], sep, out[y0:y1, zx0:zx1]])
    cv2.imwrite(str(Path(a.out).with_name(Path(a.out).stem + "_seam.jpg")), cv2.resize(z, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC))
    info = {"head_src": a.head_src, "body_src": a.body_src, "background_ecc": round(float(cc), 3), "nose_shift_px": [round(dx, 1), round(dy, 1)],
            "parse_box": list(box), "head_px": int(a_head.sum()), "bg_from_head_src_px": int(use_a_bg.sum()), "inpainted_px": int(fill.sum())}
    Path(a.out).with_name(Path(a.out).stem + "_transplant.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(a.out, info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
