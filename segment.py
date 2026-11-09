"""Segmentation for replicate mode.

Face parts (skin, brows, eyes, nose, mouth, ears, neck) come from FaceFusion BiSeNet. Hair, hats and the
whole-person silhouette come from the ATR human-parsing model (parsing_atr.onnx from OOTDiffusion, CPU).
Measured on the reference photos (2026-09-20): BiSeNet misses thin glasses at every crop scale and often
labels dark curly hair as "hat" or "cloth", so it is used for face parts only. Hair comes from ATR, and
glasses are an explicit flag rather than a detector output.

All returned masks are uint8 {0, 255} at the resolution of the source image.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

import paths

ROOT = Path(__file__).parent
ATR_PATH = ROOT / ".cache" / "models" / "parsing_atr.onnx"
ATR_URL = "https://huggingface.co/levihsu/OOTDiffusion/resolve/main/checkpoints/humanparsing/parsing_atr.onnx"
BISENET_PATH = paths.facefusion_dir() / ".assets" / "models" / "bisenet_resnet_34.onnx"

BISENET = {"bg": 0, "skin": 1, "l_brow": 2, "r_brow": 3, "l_eye": 4, "r_eye": 5, "glasses": 6, "l_ear": 7,
           "r_ear": 8, "earring": 9, "nose": 10, "mouth": 11, "u_lip": 12, "l_lip": 13, "neck": 14,
           "necklace": 15, "cloth": 16, "hair": 17, "hat": 18}
ATR = {"bg": 0, "hat": 1, "hair": 2, "sunglasses": 3, "upper": 4, "skirt": 5, "pants": 6, "dress": 7,
       "belt": 8, "l_shoe": 9, "r_shoe": 10, "face": 11, "l_leg": 12, "r_leg": 13, "l_arm": 14,
       "r_arm": 15, "bag": 16, "scarf": 17}
ATR_BODY = ("hat", "hair", "sunglasses", "upper", "skirt", "pants", "dress", "belt", "l_shoe", "r_shoe",
            "face", "l_leg", "r_leg", "l_arm", "r_arm", "scarf")

_ATR_MEAN = np.array([0.406, 0.456, 0.485], np.float32)  # applied to BGR input, as in OOTDiffusion
_ATR_STD = np.array([0.225, 0.224, 0.229], np.float32)


@lru_cache(maxsize=None)
def _session(path: str):
    import onnxruntime as ort

    if not Path(path).is_file():
        raise FileNotFoundError(f"Segmentation model missing: {path}" + (f" (download: {ATR_URL})" if "parsing_atr" in path else ""))
    return ort.InferenceSession(path, providers=["CPUExecutionProvider"])


def square_crop(img: np.ndarray, cx: float, cy: float, size: float) -> tuple[np.ndarray, tuple[int, int, int]]:
    """Square crop centred on (cx, cy); regions outside the image are reflected. Returns (crop, (x0, y0, size))."""
    size = max(8, int(round(size)))
    x0, y0 = int(round(cx - size / 2)), int(round(cy - size / 2))
    m = np.float32([[1, 0, -x0], [0, 1, -y0]])
    crop = cv2.warpAffine(img, m, (size, size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return crop, (x0, y0, size)


def uncrop(mask_crop: np.ndarray, box: tuple[int, int, int], shape: tuple[int, ...]) -> np.ndarray:
    """Place a crop-space mask back into a full-frame mask (zero outside the crop)."""
    x0, y0, size = box
    h, w = shape[:2]
    m = mask_crop if mask_crop.shape[0] == size else cv2.resize(mask_crop, (size, size), interpolation=cv2.INTER_NEAREST)
    out = np.zeros((h, w), np.uint8)
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + size), min(h, y0 + size)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0:sy1, sx0:sx1] = m[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    return out


def _resize(img: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    down = size[0] < img.shape[1]
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA if down else cv2.INTER_CUBIC)


def bisenet_labels(crop_bgr: np.ndarray) -> np.ndarray:
    """Per-pixel BiSeNet labels for a face-centred crop, at the resolution of the crop."""
    s = _session(str(BISENET_PATH))
    inp = _resize(crop_bgr, (512, 512))[:, :, ::-1].astype(np.float32) / 127.5 - 1.0
    out = s.run(None, {"input": inp.transpose(2, 0, 1)[None]})[0][0]
    lab = out.argmax(0).astype(np.uint8)
    n = crop_bgr.shape[0]
    return lab if n == 512 else cv2.resize(lab, (n, n), interpolation=cv2.INTER_NEAREST)


def atr_labels(bgr: np.ndarray) -> np.ndarray:
    """Per-pixel ATR human-parsing labels for a BGR image, at the resolution of the image."""
    h, w = bgr.shape[:2]
    scale = 512.0 / max(h, w)
    nh, nw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    small = _resize(bgr, (nw, nh))
    canvas = np.zeros((512, 512, 3), np.uint8)
    canvas[:nh, :nw] = small
    x = (canvas.astype(np.float32) / 255.0 - _ATR_MEAN) / _ATR_STD
    logits = _session(str(ATR_PATH)).run(None, {"input.1": x.transpose(2, 0, 1)[None].astype(np.float32)})[1][0]
    up = np.stack([cv2.resize(c, (512, 512), interpolation=cv2.INTER_LINEAR) for c in logits])
    lab = up.argmax(0).astype(np.uint8)[:nh, :nw]
    return cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)


def _isin(lab: np.ndarray, table: dict[str, int], names: tuple[str, ...]) -> np.ndarray:
    return np.isin(lab, [table[n] for n in names]).astype(np.uint8) * 255


def head_parts(img: np.ndarray, box: tuple[int, int, int, int]) -> dict[str, np.ndarray]:
    """Named full-frame masks for the head of the person whose YuNet face box is `box` (x, y, w, h)."""
    x, y, w, h = box
    cx, cy, fs = x + w / 2, y + h / 2, float(max(w, h))

    crop_b, box_b = square_crop(img, cx, cy, fs * 1.5)
    lb = bisenet_labels(crop_b)

    def b(*names: str) -> np.ndarray:
        return uncrop(_isin(lb, BISENET, names), box_b, img.shape)

    crop_a, box_a = square_crop(img, cx, cy - fs * 0.2, fs * 3.0)
    la = atr_labels(crop_a)

    def a(*names: str) -> np.ndarray:
        return uncrop(_isin(la, ATR, names), box_a, img.shape)

    return {
        "skin": b("skin"), "brows": b("l_brow", "r_brow"), "eyes": b("l_eye", "r_eye"), "nose": b("nose"),
        "mouth": b("mouth", "u_lip", "l_lip"), "glasses_b": b("glasses"), "ears": b("l_ear", "r_ear"),
        "neck_b": b("neck"), "hair_a": a("hair", "hat"), "face_a": a("face"), "glasses_a": a("sunglasses"),
    }


def person_mask(img: np.ndarray, face_box: tuple[int, int, int, int]) -> np.ndarray:
    """Whole-person silhouette (hair, face, clothes, arms, legs, shoes): the ATR foreground connected to the face.

    A person occupying a small part of the frame is parsed from a crop around them so ATR sees enough pixels.
    """
    h, w = img.shape[:2]
    x, y, fw, fh = face_box
    cx = x + fw / 2
    bx0, bx1 = max(0, int(cx - fw * 3.5)), min(w, int(cx + fw * 3.5))
    by0, by1 = max(0, int(y - fh * 1.2)), min(h, int(y + fh * 10.0))
    if (bx1 - bx0) * (by1 - by0) > 0.85 * w * h:
        bx0, by0, bx1, by1 = 0, 0, w, h
    crop = img[by0:by1, bx0:bx1]
    lab = atr_labels(crop)
    fg = _isin(lab, ATR, ATR_BODY)
    n, cc = cv2.connectedComponents(fg)
    fx = min(crop.shape[1] - 1, max(0, int(cx - bx0)))
    fy = min(crop.shape[0] - 1, max(0, int(y + fh / 2 - by0)))
    seed = cc[fy, fx]
    keep = ((cc == seed) * 255).astype(np.uint8) if seed > 0 else fg
    out = np.zeros((h, w), np.uint8)
    out[by0:by1, bx0:bx1] = keep
    return out


def clean(mask: np.ndarray, close: int = 0, dilate: int = 0, keep_largest: bool = False) -> np.ndarray:
    """Morphological tidy-up: optional close, largest-component filter, and dilate (kernel sizes in px)."""
    m = mask.copy()
    if close:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    if keep_largest:
        n, cc, stats, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8))
        if n > 1:
            m = ((cc == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))) * 255).astype(np.uint8)
    if dilate:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate, dilate)))
    return m
