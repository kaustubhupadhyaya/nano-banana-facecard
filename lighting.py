"""Light consistency of a render, measured against its goal (the user, 2026-10-02: pin 5 "lighting off, face seems lasso-ed in").

Two numbers, both from the eye and nose keypoints of tools/pose_compare.py (the render's `<render>_pose.json`, the goal's `.cache/poses/<goal>.json`):
  * face light  = mean grey level of the face region, render / goal. Limit 0.77-1.30 (the user rejected a face lit 1.6-1.7x the pin's).
  * face vs neck = (face / neck brightness in the render) compared with the same ratio in the goal. Tolerance 0.12: a face brighter than its own neck
    than in the goal reads pasted in (old pin 5 picture: 1.20 against the pin's 0.82).
A profile or hidden face has no reliable eye keypoints: both are then None and the head row is judged by eye (items 4, 9, 10, 11).
Used by facecard.py gen (written into run.json, used to rank passing candidates) and tools/audit_views.py (printed under the head row).
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

LIGHT_RATIO = (0.77, 1.30)
NECK_RATIO_TOL = 0.12


def read_bgr(path) -> np.ndarray | None:
    return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)


def _eyes(img, kp):
    H, W = img.shape[:2]
    need = [kp.get(k) for k in ("nose", "l_eye", "r_eye")]
    if any(n is None or n[2] < 0.3 for n in need):
        return None
    pts = np.array([[n[0] * W, n[1] * H] for n in need])
    ed = float(np.hypot(*(pts[1] - pts[2])))
    cx, cy = pts.mean(axis=0)
    return H, W, ed, cx, cy


def face_mean(img, kp):
    """Mean grey level of the face region (None when the face is a profile or hidden: keypoints unreliable)."""
    e = _eyes(img, kp)
    if e is None:
        return None
    H, W, ed, cx, cy = e
    r = 0.9 * max(ed, 8)
    x0, x1, y0, y1 = int(max(0, cx - r)), int(min(W, cx + r)), int(max(0, cy - 0.6 * r)), int(min(H, cy + 1.4 * r))
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    return float(g.mean()) if g.size else None


def neck_mean(img, kp):
    """Median grey level of the neck / upper-chest strip below the chin (None when the eye keypoints are not reliable)."""
    e = _eyes(img, kp)
    if e is None:
        return None
    H, W, ed, cx, cy = e
    x0, x1, y0, y1 = int(max(0, cx - 0.9 * ed)), int(min(W, cx + 0.9 * ed)), int(max(0, cy + 2.2 * ed)), int(min(H, cy + 3.4 * ed))
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    return float(np.median(g)) if g.size else None


def metrics(render_img, render_kp, goal_img, goal_kp) -> dict:
    """{'face', 'neck', 'goal_face', 'goal_neck', 'face_vs_goal', 'face_neck', 'goal_face_neck', 'light_ok', 'neck_ok', 'ok'}; values None when not measurable."""
    fr, nr = face_mean(render_img, render_kp), neck_mean(render_img, render_kp)
    fg, ng = face_mean(goal_img, goal_kp), neck_mean(goal_img, goal_kp)
    out = {"face": fr, "neck": nr, "goal_face": fg, "goal_neck": ng, "face_vs_goal": None, "face_neck": None, "goal_face_neck": None,
           "light_ok": None, "neck_ok": None, "ok": None}
    if fr is not None and fg:
        out["face_vs_goal"] = fr / fg
        out["light_ok"] = LIGHT_RATIO[0] <= out["face_vs_goal"] <= LIGHT_RATIO[1]
    if None not in (fr, nr, fg, ng) and nr and ng:
        out["face_neck"], out["goal_face_neck"] = fr / nr, fg / ng
        out["neck_ok"] = abs(out["face_neck"] - out["goal_face_neck"]) <= NECK_RATIO_TOL
    flags = [v for v in (out["light_ok"], out["neck_ok"]) if v is not None]
    out["ok"] = (all(flags) if flags else None)
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items()}


def render_keypoints(render_path: Path):
    """kp of the person in `<render>_pose.json` (written by tools/pose_compare.py), or None."""
    pj = Path(render_path).with_name(Path(render_path).stem + "_pose.json")
    try:
        return json.loads(pj.read_text(encoding="utf-8"))["render_pose"]["person"]["kp"]
    except Exception:
        return None


def goal_keypoints(goal_path: Path, root: Path):
    """kp of the goal's man in `.cache/poses/<goal stem>.json` (tools/pose_compare.py --save-goal), or None."""
    try:
        return json.loads((root / ".cache" / "poses" / (Path(goal_path).stem + ".json")).read_text(encoding="utf-8"))["person"]["kp"]
    except Exception:
        return None


def describe(m: dict) -> str:
    if m.get("face_vs_goal") is None and m.get("face_neck") is None:
        return "not measurable (profile or hidden face): judge the pasted-in look by eye on the head row"
    parts = []
    if m.get("face_vs_goal") is not None:
        parts.append(f"face {m['face']:.0f} = x{m['face_vs_goal']:.2f} of the goal's ({'ok' if m['light_ok'] else 'OUT of ' + str(LIGHT_RATIO)})")
    if m.get("face_neck") is not None:
        parts.append(f"face/neck {m['face_neck']:.2f} vs the goal's {m['goal_face_neck']:.2f} ({'ok' if m['neck_ok'] else 'OUT: reads pasted in'})")
    return "; ".join(parts)
