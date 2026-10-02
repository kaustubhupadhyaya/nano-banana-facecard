"""Training-free eye (code measures): is the face's grain and sharpness out of step with the hair, neck and background around it, compared with the
same places in the source photo? The user's word for the defect is "lasso-ed and edited in"; a face re-rendered cleaner or sharper than the
photo it sits in is the measurable part of that.

Per picture, at native resolution inside the edited region:
  noise  = standard deviation of the fine residual (gray minus its 3x3 median) on the face (inner ellipse of the face box) and on a ring around
           it (between 1.3x and 2.2x the face box), as log(face / ring); the same in the source; shift = output minus source
  sharp  = the same with the variance of the Laplacian
score = the larger of |noise shift| and |sharp shift| (0 = the face sits in the photo exactly as the original face did).
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

import composite
from replicate import detect_faces, load_source

FLAG_AT = 0.35   # provisional; bench.py reports the threshold that would separate the set best


def _read(p: str) -> np.ndarray | None:
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    if img is None and Path(p).exists():
        img = load_source(Path(p))
    return img


def _face(img: np.ndarray):
    f = detect_faces(img, min_px=24)
    return f[0]["box"] if f else None


def _masks(shape, box):
    h, w = shape[:2]
    x, y, bw, bh = box
    cx, cy = x + bw / 2, y + bh / 2
    face = np.zeros((h, w), np.uint8)
    cv2.ellipse(face, (int(cx), int(cy)), (int(bw * 0.35), int(bh * 0.40)), 0, 0, 360, 255, -1)
    outer = np.zeros((h, w), np.uint8)
    cv2.rectangle(outer, (int(cx - bw * 1.1), int(cy - bh * 1.1)), (int(cx + bw * 1.1), int(cy + bh * 1.1)), 255, -1)
    inner = np.zeros((h, w), np.uint8)
    cv2.rectangle(inner, (int(cx - bw * 0.65), int(cy - bh * 0.65)), (int(cx + bw * 0.65), int(cy + bh * 0.65)), 255, -1)
    ring = cv2.bitwise_and(outer, cv2.bitwise_not(inner))
    return face > 0, ring > 0


def _stats(img: np.ndarray, box) -> tuple[float, float] | None:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    resid = g - cv2.medianBlur(g.astype(np.uint8), 3).astype(np.float32)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    face, ring = _masks(img.shape, box)
    if face.sum() < 200 or ring.sum() < 200:
        return None
    noise = np.log((resid[face].std() + 1e-3) / (resid[ring].std() + 1e-3))
    sharp = np.log((lap[face].var() + 1e-3) / (lap[ring].var() + 1e-3))
    return float(noise), float(sharp)


def judge(case: dict) -> dict:
    if not case.get("source") or not case.get("region"):
        return {"flag": None, "score": None, "why": "no source photo or region to compare with"}
    pic, src = _read(case["picture"]), _read(case["source"])
    region = tuple(case["region"])
    out_c, src_c = composite.take(pic, region), composite.take(src, region)
    b_src = _face(src_c)
    b_out = _face(out_c) or b_src
    b_src = b_src or b_out
    if b_out is None:
        return {"flag": None, "score": None, "why": "no face found in the region"}
    so, ss = _stats(out_c, b_out), _stats(src_c, b_src)
    if so is None or ss is None:
        return {"flag": None, "score": None, "why": "face or ring too small to measure"}
    dn, dsh = so[0] - ss[0], so[1] - ss[1]
    score = max(abs(dn), abs(dsh))
    return {"flag": score >= FLAG_AT, "score": round(score, 3),
            "why": f"noise shift {dn:+.2f}, sharpness shift {dsh:+.2f} (log face/ring, output minus source)"}
