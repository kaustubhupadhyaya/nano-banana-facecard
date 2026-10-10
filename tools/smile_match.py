"""How closely a generated picture's expression matches a real photo of him (the user, 2026-10-10: "Until it is matched, you can keep improving
the Gemini generation"): 68 landmarks (2dfan4, mirror-checked, landmarks.landmarks68_searched) turned upright on the eye line and divided by the
distance between the eye centres, so "matched" is a number.

    .venv\\Scripts\\python.exe tools\\smile_match.py <target: the real photo> <picture> [<picture> ...] [--sheet out.jpg]

    eye_open    how far the lids are apart for the eye's width (both eyes): a real smile narrows it, a polite one leaves it open
    mouth_w     mouth corner to corner
    mouth_open  inner lips apart
    lift        mouth corners above the line through the lip centres (a smile lifts them)
    brow        brows above the upper lids
Each picture's row gives its values and the difference from the target (percent of the target's value; lift in percent of the eye distance).
Teeth, skin and identity are judged elsewhere (by eye and identity.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import landmarks  # noqa: E402
from scorer import analyze_face  # noqa: E402

METRICS = ("eye_open", "mouth_w", "mouth_open", "lift", "brow")
# --ai: what the landmarks cannot see (IMG_3884 route B v2_0 measured within 7% on all five above, and the user still saw "the other facial
# expressions are not matching"): a part-by-part comparison with the real photo, on eye-aligned face tiles. A diagnosis for the next prompt,
# never a gate; the user's eye decides.
EXPRESSION_MATCH_PROMPT = (
    "Image 1 is a real photo of a man smiling. Image 2 is a generated picture of the same man. Compare ONLY his facial expression, part by part, "
    "and ignore his hair, beard, skin, the light, the background and the size of his face. For each part say whether image 2 shows it the SAME "
    "as image 1, WEAKER (less of it) or STRONGER (more of it): eyes (how narrowed they are, the lower lids pushed up, the crinkles at the outer "
    "corners); cheeks (how high and round they lift); smile_lines (the folds from the nose to the corners of the mouth); brows; mouth (how open "
    "it is and the shape of the lips); teeth (how much of them shows). Reply with ONLY a JSON object: {\"eyes\": \"same|weaker|stronger\", "
    "\"cheeks\": \"...\", \"smile_lines\": \"...\", \"brows\": \"...\", \"mouth\": \"...\", \"teeth\": \"...\", \"match\": true or false "
    "(true only when every part is the same), \"biggest\": \"one short sentence naming the biggest difference\"}")


async def ai_compare(target: dict, cands: list[tuple[str, dict]]) -> dict:
    import json
    from datetime import datetime
    import replicate as RP
    from facecard import load_config
    from session import authenticated_client
    cfg = load_config()
    models = [m for m in dict.fromkeys([cfg.get("vision_model"), "56fdd199312815e2"]) if m]
    d = ROOT / ".cache" / "smile_match" / datetime.now().strftime("%Y%m%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=True)
    tf = d / "target.jpg"
    cv2.imwrite(str(tf), aligned_face(target, 512), [cv2.IMWRITE_JPEG_QUALITY, 94])
    log = RP.RunLog(d, {"target": "target.jpg", "pictures": [n for n, _ in cands]})
    out = {}
    async with authenticated_client(verbose=False) as client:
        for k, (name, c) in enumerate(cands):
            cf = d / f"cand{k + 1}.jpg"
            cv2.imwrite(str(cf), aligned_face(c, 512), [cv2.IMWRITE_JPEG_QUALITY, 94])
            out[name] = await RP.gemini_text(client, models, EXPRESSION_MATCH_PROMPT, [tf, cf], log, "match")
    (d / "ai.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def face_box(img: np.ndarray):
    """YuNet's box; a big close face that YuNet misses at full size is found on a smaller copy (2026-10-10: IMG_3931, DC8F5024)."""
    for s in (1.0, 0.5, 0.25):
        im = img if s == 1.0 else cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        a = analyze_face(im)
        if a.get("detected"):
            return tuple(int(round(v / s)) for v in a["box"])
    return None


def measure(path: Path) -> dict:
    img = cv2.imread(str(path))
    if img is None:
        return {"error": "unreadable"}
    box = face_box(img)
    if box is None:
        return {"error": "no face found"}
    lm, q = landmarks.landmarks68_searched(img, box)
    c1, c2 = lm[36:42].mean(0), lm[42:48].mean(0)
    ang = np.arctan2(c2[1] - c1[1], c2[0] - c1[0])
    rot = np.array([[np.cos(-ang), -np.sin(-ang)], [np.sin(-ang), np.cos(-ang)]])
    p = (lm - c1) @ rot.T                       # upright on the eye line, picture-left eye at the origin
    iod = float(np.linalg.norm(c2 - c1))

    def ear(e):
        return (np.linalg.norm(e[1] - e[5]) + np.linalg.norm(e[2] - e[4])) / (2 * np.linalg.norm(e[0] - e[3]))
    m = {"eye_open": float((ear(p[36:42]) + ear(p[42:48])) / 2),
         "mouth_w": float(np.linalg.norm(p[48] - p[54]) / iod),
         "mouth_open": float(np.mean([np.linalg.norm(p[a] - p[b]) for a, b in ((61, 67), (62, 66), (63, 65))]) / iod),
         "lift": float(((p[51, 1] + p[57, 1]) / 2 - (p[48, 1] + p[54, 1]) / 2) / iod),
         "brow": float(((p[37:39, 1].mean() - p[17:22, 1].mean()) + (p[43:45, 1].mean() - p[22:27, 1].mean())) / 2 / iod)}
    return {**m, "reliable": bool(q.get("reliable")), "mirror": q.get("mirror_offset"), "img": img, "c1": c1, "c2": c2}


def diff(t: dict, c: dict) -> dict:
    out = {}
    for k in METRICS:
        out[k] = (c[k] - t[k]) * 100 if k == "lift" else (c[k] - t[k]) / max(abs(t[k]), 1e-6) * 100
    return out


def aligned_face(r: dict, size: int = 360) -> np.ndarray:
    """The face turned and scaled so both eyes land on the same two points in every tile."""
    src = np.float32([r["c1"], r["c2"]])
    dst = np.float32([[size * 0.33, size * 0.40], [size * 0.67, size * 0.40]])
    m, _ = cv2.estimateAffinePartial2D(src, dst)
    return cv2.warpAffine(r["img"], m, (size, size), borderMode=cv2.BORDER_REPLICATE)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("pictures", nargs="+")
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--ai", action="store_true", help="also ask the AI to compare each picture's expression with the target, part by part")
    a = ap.parse_args()
    t = measure(Path(a.target))
    if "error" in t:
        print(f"target {a.target}: {t['error']}")
        return 1
    print(f"{'picture':58s} " + " ".join(f"{k:>11s}" for k in METRICS) + "   worst")
    print(f"{'TARGET ' + Path(a.target).name:58s} " + " ".join(f"{t[k]:11.3f}" for k in METRICS) + f"   (landmarks {'ok' if t['reliable'] else 'UNRELIABLE'})")
    tiles = [(Path(a.target).name + " (real)", aligned_face(t))]
    measured = []
    for pic in a.pictures:
        c = measure(Path(pic))
        name = Path(pic).parent.name[-22:] + "/" + Path(pic).name
        if "error" in c:
            print(f"{name:58s} {c['error']}")
            continue
        measured.append((name, c))
        d = diff(t, c)
        worst = max(d, key=lambda k: abs(d[k]))
        print(f"{name:58s} " + " ".join(f"{d[k]:+10.0f}%" for k in METRICS) + f"   {worst} {d[worst]:+.0f}%"
              + ("" if c["reliable"] else "  (landmarks unreliable)"))
        tiles.append((f"{name[-30:]}  eyes {d['eye_open']:+.0f}% mouth {d['mouth_open']:+.0f}%", aligned_face(c)))
    if a.ai and measured:
        import asyncio
        res = asyncio.run(ai_compare(t, measured))
        print("\nAI, part by part against the target (same / weaker / stronger):")
        for name, r in res.items():
            if not r:
                print(f"  {name}: no usable answer")
                continue
            parts = " ".join(f"{k}={r.get(k)}" for k in ("eyes", "cheeks", "smile_lines", "brows", "mouth", "teeth"))
            print(f"  {name}: {parts} | match {r.get('match')} | {r.get('biggest')}")
    if a.sheet:
        cells = []
        for lab, im in tiles:
            im = im.copy()
            cv2.rectangle(im, (0, 0), (im.shape[1], 22), (30, 30, 30), -1)
            cv2.putText(im, lab[:46], (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
            cells.append(im)
        while len(cells) % 4:
            cells.append(np.full_like(cells[0], 30))
        rows = [np.hstack(cells[i:i + 4]) for i in range(0, len(cells), 4)]
        Path(a.sheet).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(a.sheet, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print(f"-> {a.sheet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
