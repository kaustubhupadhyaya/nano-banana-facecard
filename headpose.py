"""Measured head pose, record-only (adopted 2026-10-07 after a fit check; vendor/head_pose/SOURCE.md).

SCRFD finds the face (it finds the bowed faces of pins 5 and 6 that YuNet misses), HeadPoseONNX reads pitch / yaw / roll from the expanded face
box, both used as-is from yakhyo/head-pose-estimation (MIT). Sign of yaw, checked on his references and on YuNet's bins: positive = the face
turned toward picture-LEFT (IMG_6862 reads +51), negative = toward picture-RIGHT. The reading is written into a recipe's face-choice evidence
and into each picture's record; it never decides which references are sent (that is a method change the user approves).

    .venv\\Scripts\\python.exe headpose.py <image> [<image> ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models" / "head_pose"
_cache: dict = {}


def available() -> bool:
    return (MODELS / "det_10g.onnx").is_file() and (MODELS / "resnet18.onnx").is_file()


def _models():
    if "hp" not in _cache:
        import warnings
        sys.path.insert(0, str(ROOT))
        from vendor.head_pose import SCRFD, HeadPoseONNX
        with warnings.catch_warnings():             # the class asks for CUDA first; this laptop has the CPU provider only
            warnings.simplefilter("ignore")
            _cache["det"] = SCRFD(str(MODELS / "det_10g.onnx"))
            _cache["hp"] = HeadPoseONNX(str(MODELS / "resnet18.onnx"))
    return _cache["det"], _cache["hp"]


def side_of(yaw: float | None, dead: float = 10.0) -> str | None:
    if yaw is None:
        return None
    return "picture-left" if yaw >= dead else ("picture-right" if yaw <= -dead else "frontal")


def measure(image) -> dict:
    """{'detected', 'yaw', 'pitch', 'roll', 'side', 'score'} for the largest face; {'detected': False} when SCRFD finds none; {'error'} on failure."""
    try:
        import cv2
        import numpy as np
        from vendor.head_pose import expand_bbox
        if not available():
            return {"detected": False, "error": f"models missing in {MODELS}"}
        img = image if not isinstance(image, (str, Path)) else cv2.imdecode(np.fromfile(str(image), np.uint8), cv2.IMREAD_COLOR)
        det, hp = _models()
        boxes, _kps = det.detect(img)
        if boxes is None or len(boxes) == 0:
            return {"detected": False}
        b = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        x0, y0, x1, y1 = expand_bbox(*map(int, b[:4]))
        pitch, yaw, roll = hp.estimate(img[y0:y1, x0:x1])
        return {"detected": True, "yaw": round(yaw, 1), "pitch": round(pitch, 1), "roll": round(roll, 1), "side": side_of(yaw),
                "score": round(float(b[4]), 2), "by": "SCRFD + HeadPoseONNX (yakhyo/head-pose-estimation)"}
    except Exception as exc:
        return {"detected": False, "error": f"{type(exc).__name__}: {exc}"}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, measure(p))
