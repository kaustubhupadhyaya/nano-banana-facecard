"""Audit views for the 30-item checklist, built so the defects the user found on 2026-10-01 (pin 5 and pin 6 "wrong": hair and beard were the pin man's, not
his; the face was lit far brighter than the pin's) can no longer pass by eye alone.

    .venv\\Scripts\\python.exe tools\\audit_views.py <label> "<goal>" "<render>" "<run folder>" [--out DIR]

Writes <label>_full.jpg (goal | render, whole picture) and <label>_details.jpg to --out (default: .cache\\audit):
  row 1: goal head | render head | HIS reference heads (front + the run's own angle references; converted to black and white when the goal is)
         -> items 19 and 28: compare HAIR (tight curls, short faded sides, ear and scalp visible?) and BEARD (full and dense along the whole jaw?) with his references
  row 2: both wrists of the render and of the goal (hands)
and prints FACE LIGHT: mean brightness of the face region in the render and in the goal and their ratio (items 9 and 10). A ratio above 1.3 or below 0.77 is a FAIL:
the user rejected a poolside picture whose face measured 103 against the pin's 61 (ratio 1.7).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import review_sheet as RS  # noqa: E402
from replicate import load_source  # noqa: E402

REFS = Path(r"D:\Downloads\FaceCard_Originals")
ALWAYS = ["IMG_6858.jpg", "IMG_6862.jpg", "IMG_6863.jpg"]          # front, right profile, left profile
LIGHT_RATIO = (0.77, 1.30)


def find_ref(name: str):
    for base in (REFS, ROOT / ".cache" / "refs", ROOT / ".cache"):
        p = base / name
        if p.exists():
            return p
    hits = list((ROOT / ".cache").rglob(name))
    return hits[0] if hits else None


def fit_h(img, h):
    k = h / img.shape[0]
    return cv2.resize(img, (max(1, int(img.shape[1] * k)), h), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def label(img, text):
    bar = np.full((30, img.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 200), 2, cv2.LINE_AA)
    return np.vstack([bar, img])


def hstack_pad(imgs):
    h = max(i.shape[0] for i in imgs)
    return np.hstack([np.vstack([i, np.full((h - i.shape[0], i.shape[1], 3), 255, np.uint8)]) if i.shape[0] < h else i for i in imgs])


def is_bw(img) -> bool:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return float(hsv[..., 1].mean()) < 12


def to_bw(img):
    return cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)


def wrist_crops(img, kp, size_frac=0.2, out=420):
    H, W = img.shape[:2]
    crops = []
    for name in ("l_wrist", "r_wrist"):
        if name in kp and kp[name][2] > 0.3:
            x, y = kp[name][0] * W, kp[name][1] * H
            s = int(size_frac * H)
            x0, y0 = int(max(0, min(W - s, x - s / 2))), int(max(0, min(H - s, y - s / 2)))
            c = img[y0:y0 + s, x0:x0 + s]
            if c.size:
                crops.append(label(cv2.resize(c, (out, out), interpolation=cv2.INTER_CUBIC), name))
    return crops


def face_mean(img, kp):
    """Mean grey level of the face region from the eye and nose keypoints (None when the face is a profile or hidden: keypoints unreliable)."""
    H, W = img.shape[:2]
    need = [kp.get(k) for k in ("nose", "l_eye", "r_eye")]
    if any(n is None or n[2] < 0.3 for n in need):
        return None
    pts = np.array([[n[0] * W, n[1] * H] for n in need])
    eye_d = float(np.hypot(*(pts[1] - pts[2])))
    cx, cy = pts.mean(axis=0)
    r = 0.9 * max(eye_d, 8)
    x0, x1, y0, y1 = int(max(0, cx - r)), int(min(W, cx + r)), int(max(0, cy - 0.6 * r)), int(min(H, cy + 1.4 * r))
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    return float(g.mean()) if g.size else None


def neck_mean(img, kp):
    """Mean grey level of the neck / upper-chest strip below the chin (None when the eye keypoints are not reliable)."""
    H, W = img.shape[:2]
    need = [kp.get(k) for k in ("nose", "l_eye", "r_eye")]
    if any(n is None or n[2] < 0.3 for n in need):
        return None
    pts = np.array([[n[0] * W, n[1] * H] for n in need])
    ed = float(np.hypot(*(pts[1] - pts[2])))
    cx, cy = pts.mean(axis=0)
    x0, x1, y0, y1 = int(max(0, cx - 0.9 * ed)), int(min(W, cx + 0.9 * ed)), int(max(0, cy + 2.2 * ed)), int(min(H, cy + 3.4 * ed))
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    return float(np.median(g)) if g.size else None


NECK_RATIO_TOL = 0.12      # |face/neck in the render - face/neck in the goal| (the user, 2026-10-02: pin 5 'lighting off, face seems lasso-ed in': old picture 1.27 vs the pin's 0.97)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("label")
    ap.add_argument("goal")
    ap.add_argument("render")
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=str(ROOT / ".cache" / "audit"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    goal, render = RS.read(a.goal), RS.read(a.render)
    run = json.loads((Path(a.run_dir) / "run.json").read_text(encoding="utf-8"))
    bw = is_bw(goal)
    h = 1000
    cv2.imwrite(str(out / f"{a.label}_full.jpg"), hstack_pad([label(fit_h(goal, h), "goal"), label(fit_h(render, h), "render")]), [cv2.IMWRITE_JPEG_QUALITY, 92])
    row = [label(RS.head_zoom(goal), "goal head"), label(RS.head_zoom(render), "render head")]
    names = list(ALWAYS) + [n for n in (run.get("route_g", {}).get("roles", {}).get("face", []))[:2] if n not in ALWAYS]
    for n in names[:5]:
        p = find_ref(n)
        if p is not None:
            try:
                im = load_source(p)
                row.append(label(RS.head_zoom(to_bw(im) if bw else im), "his ref " + n[:16] + (" (bw)" if bw else "")))
            except Exception:
                pass
    rows = [hstack_pad([fit_h(i, 380) for i in row])]
    rj = Path(a.render).with_name(Path(a.render).stem + "_pose.json")
    gj = ROOT / ".cache" / "poses" / (Path(a.goal).stem + ".json")
    rk = json.loads(rj.read_text(encoding="utf-8")).get("render_pose", {}).get("person", {}).get("kp", {}) if rj.exists() else {}
    gk = json.loads(gj.read_text(encoding="utf-8")).get("person", {}).get("kp", {}) if gj.exists() else {}
    hands = [label(c, "render hand") for c in wrist_crops(render, rk)] + [label(c, "goal hand") for c in wrist_crops(goal, gk)]
    if hands:
        rows.append(hstack_pad(hands))
    W = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], W - r.shape[1], 3), 255, np.uint8)]) if r.shape[1] < W else r for r in rows]
    cv2.imwrite(str(out / f"{a.label}_details.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    fr, fg = face_mean(render, rk), face_mean(goal, gk)
    if fr is None or fg is None:
        print(f"{a.label}: FACE LIGHT not measurable (profile or hidden face): compare the head crops by eye against the goal")
    else:
        ratio = fr / max(fg, 1e-6)
        verdict = "ok" if LIGHT_RATIO[0] <= ratio <= LIGHT_RATIO[1] else "FAIL items 9/10: the face is " + ("brighter" if ratio > 1 else "darker") + " than the goal's"
        print(f"{a.label}: FACE LIGHT render {fr:.0f} vs goal {fg:.0f} (ratio {ratio:.2f}, limit {LIGHT_RATIO[0]}-{LIGHT_RATIO[1]}): {verdict}")
    nr, ng = neck_mean(render, rk), neck_mean(goal, gk)
    if None in (fr, fg, nr, ng):
        print(f"{a.label}: FACE vs NECK not measurable (profile or hidden face): judge the pasted-in look (items 4, 10, 11) by eye on the head row")
    else:
        rr, gr = fr / max(nr, 1e-6), fg / max(ng, 1e-6)
        ok = abs(rr - gr) <= NECK_RATIO_TOL
        print(f"{a.label}: FACE vs NECK render {rr:.2f} vs goal {gr:.2f} (tolerance {NECK_RATIO_TOL}): " + ("ok" if ok else "FAIL items 4/10/11: the face is " + ("brighter" if rr > gr else "darker") + " than its own neck compared with the goal: it reads pasted in"))
    print(f"{a.label}: views written to {out}  (black-and-white references: {bw}); judge HAIR and BEARD (items 19/28) on the head row against his references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
