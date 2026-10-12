"""His eyes in a picture, measured (2026-10-12, pin 16; the user: "it is less open ... it might be that one eye is looking 75 deg to the left and
another is likely looking 80 or 85 deg to the left. Hence, it looks like an eye condition, which I actually don't have").

Landmarks: 2dfan4 (landmarks.py, roll search included), head turn: headpose.py (yaw + = the face turned toward picture-left). Per eye:
  ear       lid-to-lid height (mean of the two vertical landmark pairs) / corner-to-corner width. It rises with the turn (the width foreshortens),
            so it is compared with his photos at the same turn only.
  u         where the iris sits between its own corners along the corner line: 0 = the picture-left corner, 1 = the picture-right corner.
            Iris locator: the darkness-weighted centroid of the pixels darker than the median grey inside the landmark eye outline (the dark
            iris against the white of the eye), on the outline's box upsampled to 96 px. No iris model exists on this machine.
  vergence  u(picture-left eye) - u(picture-right eye). Both irises move together when he looks around, so this changes only with the turn;
            it reads the same for a face turned the other way (mirror-invariant). His real photos at 27-31 degrees (IMG_6868, 6869, 6852,
            6861; full size, shrunk, mirrored): -0.32 to -0.20; another man's real photo at 31 degrees looking at the camera (pin 16's own
            man): -0.32 to -0.30; pin 16's base and redraws at 27 degrees: -0.08 to -0.07 (at 20-21 degrees -0.14 to -0.10): the far eye's
            iris sits too far toward the nose, the "eye condition" look.
  ear_near  ear of the near eye (picture-right when yaw >= 0). On pin 16 the renders' ear (near 0.248-0.257, far 0.333-0.360) sat inside his
            band at the same turn (near 0.244-0.283, far 0.326-0.382), and so did the inner eye corners' distance to the nose line.
Reliability (his photos shrunk to the renders' size): at 32-46 px between the eye centres, vergence moves by at most 0.04 and ear by at most 0.013.

A gate (replicate/1 --eye-gate, opt-in): it selects among returns and never moves a pixel.
    .venv\\Scripts\\python.exe eye_measure.py <image> [<image> ...]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent


def _iris(gray: np.ndarray, pts: np.ndarray):
    x0, y0 = pts.min(axis=0) - 2
    x1, y1 = pts.max(axis=0) + 2
    s = 96.0 / max(1.0, x1 - x0)
    m = np.array([[s, 0, -s * x0], [0, s, -s * y0]])
    W, H = int(round((x1 - x0) * s)), int(round((y1 - y0) * s))
    if W < 4 or H < 4:
        return None
    g = cv2.warpAffine(gray, m, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [np.round((pts - [x0, y0]) * s).astype(np.int32)], 1)
    vals = g[mask > 0]
    if vals.size < 20:
        return None
    d = np.clip(float(np.median(vals)) - g, 0, None) * (mask > 0)
    if d.sum() <= 0:
        return None
    ys, xs = np.mgrid[0:H, 0:W]
    return np.array([(xs * d).sum() / d.sum(), (ys * d).sum() / d.sum()]) / s + [x0, y0]


def _eye(gray, lm, a) -> dict:
    p = lm[a:a + 6]
    h = (np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])) / 2
    e = p[3] - p[0]
    w = float(np.linalg.norm(e))
    out = {"ear": float(h / w), "corners": [p[0].tolist(), p[3].tolist()]}
    ir = _iris(gray, p)
    if ir is not None:
        out.update({"u": float(np.dot(ir - p[0], e) / w ** 2), "iris": ir.tolist()})
    return out


def measure(img: np.ndarray) -> dict:
    """{'detected', 'yaw', 'iod_px', 'left', 'right' (per eye: ear, u, iris, corners), 'vergence', 'ear_near', 'ear_far'} of the largest face."""
    import headpose
    import landmarks
    hp = headpose.measure(img)
    if not hp.get("detected"):
        return {"detected": False}
    det, _ = headpose._models()
    boxes, _ = det.detect(img)
    if boxes is None or not len(boxes):
        return {"detected": False}
    b = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    lm, q = landmarks.landmarks68_searched(img, (int(b[0]), int(b[1]), int(b[2] - b[0]), int(b[3] - b[1])))
    lm = np.asarray(lm, np.float64)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    L, R = _eye(gray, lm, 36), _eye(gray, lm, 42)
    near, far = (R, L) if hp["yaw"] >= 0 else (L, R)
    out = {"detected": True, "yaw": hp["yaw"], "pitch": hp["pitch"], "iod_px": round(float(np.linalg.norm(lm[42:48].mean(0) - lm[36:42].mean(0))), 1),
           "fit_mirror_offset": q.get("mirror_offset"), "left": L, "right": R,
           "ear_near": round(near["ear"], 3), "ear_far": round(far["ear"], 3)}
    if "u" in L and "u" in R:
        out["vergence"] = round(L["u"] - R["u"], 3)
    return out


def parse_spec(text: str) -> dict:
    """'yaw=24:34,vergence=-0.33:-0.18,ear_near=0.25:' -> {'yaw': [24.0, 34.0], 'vergence': [-0.33, -0.18], 'ear_near': [0.25, None]}."""
    out = {}
    for part in str(text).replace(";", ",").split(","):
        if not part.strip():
            continue
        k, _, rng = part.partition("=")
        lo, _, hi = rng.partition(":")
        k = k.strip()
        if k not in ("yaw", "vergence", "ear_near", "ear_far"):
            raise SystemExit(f"--eye-gate: unknown measure {k!r} (yaw, vergence, ear_near, ear_far)")
        out[k] = [float(lo) if lo.strip() else None, float(hi) if hi.strip() else None]
    if not out:
        raise SystemExit("--eye-gate: give at least one measure, e.g. yaw=24:34,vergence=-0.33:-0.18")
    return out


def _outside(v, rng) -> bool:
    lo, hi = rng
    return v is None or (lo is not None and v < lo) or (hi is not None and v > hi)


def check(m: dict, band: dict) -> list[str]:
    """Problems of one measured face against the gate's bands (empty = passes)."""
    if not m.get("detected"):
        return ["eye gate: no face or landmarks found in the return"]
    out = []
    if "yaw" in band and _outside(abs(m["yaw"]), band["yaw"]):
        out.append(f"eye gate: head turn {abs(m['yaw']):.0f} deg outside {band['yaw']} (the turns his eye bands come from)")
    if "vergence" in band:
        if m.get("vergence") is None:
            out.append("eye gate: an iris was not found")
        elif _outside(m["vergence"], band["vergence"]):
            out.append(f"eye gate: the two eyes disagree (vergence {m['vergence']:+.3f}, his photos {band['vergence']}): an eye-condition look")
    for k, what in (("ear_near", "near"), ("ear_far", "far")):
        if k in band and _outside(m.get(k), band[k]):
            out.append(f"eye gate: the {what} eye is {'less' if band[k][0] is not None and (m.get(k) or 0) < band[k][0] else 'more'} open "
                       f"than in his photos (EAR {m.get(k)}, his {band[k]})")
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    import character
    for p in sys.argv[1:]:
        r = measure(character.load(p))
        print(p, {k: r.get(k) for k in ("yaw", "iod_px", "vergence", "ear_near", "ear_far")})
