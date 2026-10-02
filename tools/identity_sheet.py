"""A numbered identity sheet for the USER to judge by eye (the user, 2026-10-01: 'none look like me'; ArcFace cannot score a bowed or profile face, so for those the user's eye
is the only identity check). Candidates are cropped to the head, numbered, and set beside his reference photos (black and white when the goal is) with the ArcFace similarity
printed under each candidate where a face is found.

    .venv\\Scripts\\python.exe tools\\identity_sheet.py <goal picture> <out.jpg> <candidate> [<candidate> ...]

The sheet is for choosing; it never records or exports anything.
"""
from __future__ import annotations

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
SHOW = ["IMG_6858.jpg", "IMG_6873.jpg", "IMG_6862.jpg", "IMG_6863.jpg", "IMG_6864.jpg"]
H = 360


def fit(img):
    k = H / img.shape[0]
    return cv2.resize(img, (max(1, int(img.shape[1] * k)), H), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def tag(img, text, colour=(0, 0, 200)):
    bar = np.full((30, img.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.62, colour, 2, cv2.LINE_AA)
    return np.vstack([bar, img])


def pad_to(img, h):
    return np.vstack([img, np.full((h - img.shape[0], img.shape[1], 3), 255, np.uint8)]) if img.shape[0] < h else img


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    goal_p, out_p, cands = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
    goal = RS.read(goal_p)
    bw = float(cv2.cvtColor(goal, cv2.COLOR_BGR2HSV)[..., 1].mean()) < 12
    sims = {}
    try:
        from scorer import ArcFaceScorer
        sc = ArcFaceScorer()
        ref_emb = []
        for n in SHOW:
            try:
                ref_emb.append(sc.embed(REFS / n))
            except Exception:
                pass
        for c in cands:
            try:
                e = sc.embed(Path(c))
                sims[c] = float(np.mean(sorted((sc.similarity(e, r) for r in ref_emb), reverse=True)[:3]))
            except Exception:
                sims[c] = None
    except Exception:
        pass
    row_refs = []
    for n in SHOW:
        try:
            im = load_source(REFS / n)
            im = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) if bw else im
            row_refs.append(tag(fit(RS.head_zoom(im)), "HIS " + n[4:8], (0, 120, 0)))
        except Exception:
            pass
    row_goal = [tag(fit(RS.head_zoom(goal)), "the pin's man")]
    row_c = []
    for i, c in enumerate(cands, 1):
        s = sims.get(c)
        row_c.append(tag(fit(RS.head_zoom(RS.read(c))), f"#{i}  " + ("ArcFace n/a" if s is None else f"ArcFace {s:.2f}")))
    rows = []
    for r in (row_goal + row_refs, row_c):
        if r:
            h = max(x.shape[0] for x in r)
            rows.append(np.hstack([pad_to(x, h) for x in r]))
    W = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], W - r.shape[1], 3), 255, np.uint8)]) if r.shape[1] < W else r for r in rows]
    out_p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_p), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"sheet: {out_p}")
    for i, c in enumerate(cands, 1):
        print(f"  #{i}: {c}" + ("" if sims.get(c) is None else f"  (ArcFace {sims[c]:.2f})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
