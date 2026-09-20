"""68-point landmarks (FaceFusion 2dfan4, CPU) for face alignment and head pose that hold up at large yaw.

YuNet gives only 5 landmarks and they collapse on profile faces (a true right profile was read as "three-quarter",
a kayak profile as nose_norm -2.52), which corrupted both the ArcFace alignment and the pose gating. 2dfan4 was
trained on large-pose faces, so it is used here for both.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

import paths

MODEL_PATH = paths.facefusion_dir() / ".assets" / "models" / "2dfan4.onnx"

ARCFACE_DST = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
                        [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32)

# Generic 3D head model (mm) in OpenCV camera axes (x right, y down, z away from the camera):
# nose tip, chin, outer eye corners, mouth corners.
_MODEL_3D = np.array([[0.0, 0.0, 0.0], [0.0, 330.0, 65.0], [-225.0, -170.0, 135.0],
                      [225.0, -170.0, 135.0], [-150.0, 150.0, 125.0], [150.0, 150.0, 125.0]], dtype=np.float64)
_PNP_IDX = [30, 8, 36, 45, 48, 54]


@lru_cache(maxsize=1)
def _session():
    import onnxruntime as ort

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"2dfan4 model missing: {MODEL_PATH}")
    return ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])


def landmarks68(img_bgr: np.ndarray, box: tuple[int, int, int, int]) -> tuple[np.ndarray, float]:
    """68 landmarks in image coordinates for the face in `box` (x, y, w, h), plus a mean heatmap confidence."""
    x, y, w, h = box
    x1, y1, x2, y2 = x, y, x + w, y + h
    scale = 195.0 / max(x2 - x1, y2 - y1, 1)
    tx, ty = (256 - (x1 + x2) * scale) * 0.5, (256 - (y1 + y2) * scale) * 0.5
    m = np.float32([[scale, 0, tx], [0, scale, ty]])
    crop = cv2.warpAffine(img_bgr, m, (256, 256))
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    if float(lab[:, :, 0].mean()) < 30:
        lab[:, :, 0] = cv2.createCLAHE(clipLimit=2).apply(lab[:, :, 0])
        crop = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    blob = crop.transpose(2, 0, 1).astype(np.float32)[None] / 255.0
    lm, heat = _session().run(None, {_session().get_inputs()[0].name: blob})
    pts = lm[0, :, :2] / 64.0 * 256.0
    pts = (pts - np.array([tx, ty])) / scale
    conf = float(np.mean(np.amax(heat[0], axis=(1, 2))))
    return pts.astype(np.float32), conf


def five_points(lm68: np.ndarray) -> np.ndarray:
    """Eye centres, nose tip and mouth corners (image-left first), the order ArcFace alignment expects."""
    return np.array([lm68[36:42].mean(axis=0), lm68[42:48].mean(axis=0), lm68[30], lm68[48], lm68[54]], dtype=np.float32)


# 68-point index map under a horizontal mirror (jaw reversed, brows/eyes/mouth corners swapped left-right).
FLIP_INDEX = np.array(
    list(range(16, -1, -1)) + [26, 25, 24, 23, 22] + [21, 20, 19, 18, 17] + [27, 28, 29, 30] + [35, 34, 33, 32, 31]
    + [45, 44, 43, 42, 47, 46] + [39, 38, 37, 36, 41, 40] + [54, 53, 52, 51, 50, 49, 48] + [59, 58, 57, 56, 55]
    + [64, 63, 62, 61, 60] + [67, 66, 65])

MIRROR_USABLE = 0.06    # measured: correct fits 0.007-0.025, failed fits 0.31-0.50 (2026-09-20)
MIRROR_MARGINAL = 0.10


def _mirror_offset(img_bgr: np.ndarray, box: tuple[int, int, int, int], lm: np.ndarray) -> float:
    """Mean disagreement (in face widths) between this fit and the fit on the mirrored image."""
    w = img_bgr.shape[1]
    x, y, bw, bh = box
    lm_f, _ = landmarks68(cv2.flip(img_bgr, 1), (w - x - bw, y, bw, bh))
    lm_back = lm_f.copy()
    lm_back[:, 0] = w - lm_back[:, 0]
    return float(np.linalg.norm(lm - lm_back[FLIP_INDEX], axis=1).mean() / max(1, bw))


def _rotated_view(img_bgr: np.ndarray, box: tuple[int, int, int, int], deg: float, min_face: int = 320
                  ) -> tuple[np.ndarray, tuple[int, int, int, int], np.ndarray]:
    """Upright, upscaled square view of the face, plus the 2x3 matrix that produced it."""
    x, y, w, h = box
    cx, cy = x + w / 2.0, y + h / 2.0
    fs = max(w, h)
    k = max(1.0, min_face / fs)
    side = int(fs * 3.2 * k)
    m = cv2.getRotationMatrix2D((cx, cy), deg, k)
    m[0, 2] += side / 2.0 - cx
    m[1, 2] += side / 2.0 - cy
    view = cv2.warpAffine(img_bgr, m, (side, side), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
    nb = (int(side / 2 - w * k / 2), int(side / 2 - h * k / 2), max(8, int(w * k)), max(8, int(h * k)))
    return view, nb, m


def landmarks68_searched(img_bgr: np.ndarray, box: tuple[int, int, int, int]) -> tuple[np.ndarray, dict]:
    """Landmarks with a small search over in-plane rotation when the plain fit fails its mirror test.

    2dfan4 is sensitive to how the face sits in its crop: a head tilted in the frame scored a 0.50 mirror offset
    upright and 0.034 when the view was rotated 30 degrees (measured on the rocky-plateau photo, 2026-09-20). The
    plain fit is tried first, so a normal photo costs nothing extra.
    """
    lm, q = landmarks68_checked(img_bgr, box)
    if q["reliable"]:
        return lm, {**q, "view": "upright"}
    best = (q["mirror_offset"], lm, q, "upright")
    for deg in (-30, 30, -15, 15):
        try:
            view, vbox, m = _rotated_view(img_bgr, box, deg)
            lm_v, conf_v = landmarks68(view, vbox)
            off = _mirror_offset(view, vbox, lm_v)
        except Exception:
            continue
        if off < best[0]:
            inv = cv2.invertAffineTransform(m)
            lm_orig = (lm_v @ inv[:, :2].T + inv[:, 2]).astype(np.float32)
            best = (off, lm_orig, {"usable": off <= MIRROR_MARGINAL, "reliable": off <= MIRROR_USABLE,
                                   "mirror_offset": round(off, 3), "heatmap_conf": round(float(conf_v), 3)}, f"rotated {deg:+d}")
        if best[0] <= MIRROR_USABLE:
            break
    return best[1], {**best[2], "view": best[3]}


def landmarks68_checked(img_bgr: np.ndarray, box: tuple[int, int, int, int]) -> tuple[np.ndarray, dict]:
    """Landmarks plus a reliability verdict from MIRROR CONSISTENCY: fit the face again on the mirrored image and
    measure how far the two fits disagree, in face widths.

    Neither the heatmap confidence nor agreement with YuNet works as a reliability test here. The confidence scored a
    correct 520 px fit at 0.28 and a correct true-profile fit at 0.84, while YuNet's own 5 points are themselves wrong
    on profiles (it assumes a frontal face), so cross-checking against it rejects good landmarks. A landmarker that has
    actually locked onto a face gives the same answer on the mirrored copy; one that has not, does not.
    """
    lm, conf = landmarks68(img_bgr, box)
    d = _mirror_offset(img_bgr, box, lm)
    return lm, {"usable": d <= MIRROR_MARGINAL, "reliable": d <= MIRROR_USABLE, "mirror_offset": round(d, 3),
                "heatmap_conf": round(float(conf), 3)}


def align_arcface(img_bgr: np.ndarray, lm68: np.ndarray) -> np.ndarray:
    """112x112 ArcFace-aligned crop from 2dfan4 landmarks."""
    t, _ = cv2.estimateAffinePartial2D(five_points(lm68), ARCFACE_DST, method=cv2.LMEDS)
    if t is None:
        raise ValueError("could not estimate alignment transform")
    return cv2.warpAffine(img_bgr, t, (112, 112), borderValue=0.0)


def head_pose(lm68: np.ndarray, img_shape: tuple[int, ...]) -> dict:
    """Yaw / pitch / roll in degrees from landmarks. Positive yaw = the subject turned toward image-right.

    Coarse: a generic 3D head model saturates near 60-65 degrees for true profiles, and on some real photos it is
    plainly wrong (a frontal photo read +132). Reported for context only; pose is compared by landmark SHAPE distance
    (identity.py) and described in words by orientation_text (replicate.py).
    """
    h, w = img_shape[:2]
    cam = np.array([[w, 0, w / 2.0], [0, w, h / 2.0], [0, 0, 1]], dtype=np.float64)
    pts = lm68[_PNP_IDX].astype(np.float64)
    ok, rvec, tvec = cv2.solvePnP(_MODEL_3D, pts, cam, np.zeros((4, 1)), flags=cv2.SOLVEPNP_EPNP)
    if ok:
        ok, rvec, tvec = cv2.solvePnP(_MODEL_3D, pts, cam, np.zeros((4, 1)), rvec, tvec, useExtrinsicGuess=True,
                                      flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "ok": False}
    rot, _ = cv2.Rodrigues(rvec)
    yaw = -float(np.degrees(np.arctan2(rot[0, 2], rot[2, 2])))  # sign flipped so + = turned toward image-right
    pitch = float(np.degrees(np.arcsin(np.clip(-rot[1, 2], -1.0, 1.0))))
    roll = float(np.degrees(np.arctan2(rot[1, 0], rot[1, 1])))
    return {"yaw": yaw, "pitch": pitch, "roll": roll, "ok": True}
