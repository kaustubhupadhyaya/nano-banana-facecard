"""Study his real smiles before any smile reference is made (the user, 2026-10-10: "smile always is turning out bad ... my smile reference image
itself is bad i agree since i dont have a photogenic smile, but when captured in candid it can look different"; 13 smile photos from two years).

    .venv\\Scripts\\python.exe tools\\character_study.py smiles [<photo> ...] [--out D:\\FacecardData\\smile_study]
        each photo (default: the 13 he sent plus IMG_6858 neutral, IMG_6873 closed-lip and IMG_6875 open smile from his references): measured head
        pose (headpose.py), pool identity (identity.py), face size; a face crop and a lower-face crop (nose to chin, cheek to cheek: no glasses, no
        old haircut) at ONE scale (eye distance 160 px), two contact sheets and study.json in the out folder
    .venv\\Scripts\\python.exe tools\\character_study.py exemplar <name> <stem>[,<stem>...] [--part lower|face] [--out <jpg>]
        the chosen crops side by side as one reference image (e.g. his_smile_E2.jpg) plus <jpg>.json with the sources' sha256 and crop boxes
    .venv\\Scripts\\python.exe tools\\character_study.py compare <picture> [...] --out <jpg> [--with IMG_3884,DSC07985,IMG_6637,IMG_6875]
        candidate pictures' faces beside his real smiles at the same scale, with identity: the sheet he approves an ideal smile from

The copies stay out of D:\\Downloads\\FaceCard_Originals: that folder is the identity pool (identity._candidate_files), and a smile crop there would
change every identity score. Nothing here is generated; these are his own photos, cut and measured.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DOWNLOADS = Path(r"D:\Downloads")
SMILES = ["IMG_6371_Original.jpg", "IMG_5684_Original.jpg", "IMG_0141_Original.jpg", "IMG_4892_Original.jpg", "IMG_3931_Original.jpg",
          "IMG_3929_Original.jpg", "IMG_3884_Original.jpg", "DC8F5024-9C73-4264-9E3F-FED4B65F0B7B_Original.jpg", "IMG_5759_Original.jpg",
          "90395a1b-75e5-4028-884e-feb7091d8e4b_Original.jpg", "DSC07985_Original.jpg", "IMG_3346_Original_Original.PNG", "IMG_6637_Original.jpg"]
REFS = ["IMG_6858.jpg", "IMG_6873.jpg", "IMG_6875.jpg"]          # neutral front, closed-lip smile, open smile (his current references)
# read by eye on 2026-10-10 (glasses in the photo; an old haircut); the crops below leave both out
GLASSES = {"IMG_6371", "IMG_0141", "DC8F5024-9C73-4264-9E3F-FED4B65F0B7B", "IMG_5759", "90395a1b-75e5-4028-884e-feb7091d8e4b", "DSC07985",
           "IMG_3346", "IMG_6637"}
OUT = Path(r"D:\FacecardData\smile_study")
EYE_PX = 160            # every crop is scaled so his eyes are this far apart: one scale for the sheet and the exemplars


def stem_of(p: Path) -> str:
    return p.stem.replace("_Original", "")


def load(p: Path) -> np.ndarray:
    im = ImageOps.exif_transpose(Image.open(p))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (128, 128, 128, 255))
        im = Image.alpha_composite(bg, im)
    return cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def boxes_from_landmarks(lm: np.ndarray) -> tuple[list[int], list[int], float]:
    """Face and lower-face boxes (x0, y0, x1, y1) from YuNet's five points (right eye, left eye, nose, right and left mouth corner)."""
    eyes = lm[:2]
    eye_mid = eyes.mean(axis=0)
    eye_d = float(np.linalg.norm(eyes[0] - eyes[1]))
    nose = lm[2]
    mouth = lm[3:5].mean(axis=0)
    cx = float((eye_mid[0] + mouth[0]) / 2)
    face = [cx - 1.35 * eye_d, eye_mid[1] - 1.05 * eye_d, cx + 1.35 * eye_d, mouth[1] + 1.25 * eye_d]
    lower = [mouth[0] - 1.25 * eye_d, nose[1] - 0.20 * eye_d, mouth[0] + 1.25 * eye_d, mouth[1] + 1.15 * eye_d]
    return [int(round(v)) for v in face], [int(round(v)) for v in lower], eye_d


def cut(img: np.ndarray, box: list[int], eye_d: float) -> np.ndarray:
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    pad = [max(0, -x0), max(0, -y0), max(0, x1 - w), max(0, y1 - h)]
    big = cv2.copyMakeBorder(img, pad[1], pad[3], pad[0], pad[2], cv2.BORDER_REPLICATE) if any(pad) else img
    c = big[y0 + pad[1]:y1 + pad[1], x0 + pad[0]:x1 + pad[0]]
    k = EYE_PX / max(1.0, eye_d)
    return cv2.resize(c, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def label(img: np.ndarray, lines: list[str]) -> np.ndarray:
    bar = np.full((18 * len(lines) + 6, img.shape[1], 3), 30, np.uint8)
    for i, t in enumerate(lines):
        cv2.putText(bar, t, (4, 16 + 18 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (235, 235, 235), 1, cv2.LINE_AA)
    return np.vstack([img, bar])


def grid(tiles: list[np.ndarray], cols: int) -> np.ndarray:
    h = max(t.shape[0] for t in tiles)
    w = max(t.shape[1] for t in tiles)
    pads = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, w - t.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30)) for t in tiles]
    rows = [np.hstack(pads[i:i + cols] + [np.full((h, w, 3), 30, np.uint8)] * (cols - len(pads[i:i + cols]))) for i in range(0, len(pads), cols)]
    return np.vstack(rows)


def smiles(photos: list[Path], out: Path) -> int:
    import headpose
    import identity
    from facecard import load_config
    from scorer import ArcFaceScorer, analyze_face
    out.mkdir(parents=True, exist_ok=True)
    scorer = ArcFaceScorer()
    pool = identity.build_pool(load_config(), scorer, verbose=False)
    rows, faces, lowers = [], [], []
    for p in photos:
        img = load(p)
        st = stem_of(p)
        info = analyze_face(img)
        row: dict = {"photo": str(p), "sha256": sha256(p), "size": [img.shape[1], img.shape[0]], "glasses_by_eye": st in GLASSES}
        if not info.get("detected"):
            row["note"] = "no face found (YuNet)"
            rows.append(row)
            print(f"{st}: no face found")
            continue
        lm = np.array(info["landmarks"], np.float32)
        face_box, lower_box, eye_d = boxes_from_landmarks(lm)
        hp = headpose.measure(img)
        res = identity.score_image(img, pool, scorer)
        if res.get("detected"):           # his reference photos are in the pool: leave their own copies out of their score
            res = identity.score_image(img, pool, scorer, exclude_names=identity.duplicates_of(res["emb"], pool))
        row.update({"face_w": int(info["box"][2]), "eye_dist_px": round(eye_d, 1), "face_box": face_box, "lower_box": lower_box,
                    "yaw": hp.get("yaw"), "pitch": hp.get("pitch"), "roll": hp.get("roll"),
                    "identity": round(float(res["score"]), 3) if res.get("detected") and res.get("score") is not None else None})
        fc, lc = cut(img, face_box, eye_d), cut(img, lower_box, eye_d)
        cv2.imwrite(str(out / f"{st}_face.jpg"), fc, [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(str(out / f"{st}_lower.jpg"), lc, [cv2.IMWRITE_JPEG_QUALITY, 95])
        txt = [st[:22], f"yaw {row['yaw']} pitch {row['pitch']} roll {row['roll']}",
               f"id {row['identity']} face {row['face_w']}px{' glasses' if row['glasses_by_eye'] else ''}"]
        faces.append(label(fc, txt))
        lowers.append(label(lc, txt[:1]))
        rows.append(row)
        print(f"{st}: face {row['face_w']} px, yaw {row['yaw']} pitch {row['pitch']} roll {row['roll']}, identity {row['identity']}")
    cv2.imwrite(str(out / "sheet_faces.jpg"), grid(faces, 4), [cv2.IMWRITE_JPEG_QUALITY, 90])
    cv2.imwrite(str(out / "sheet_lower.jpg"), grid(lowers, 4), [cv2.IMWRITE_JPEG_QUALITY, 90])
    (out / "study.json").write_text(json.dumps({"kind": "smile_study/1", "eye_px": EYE_PX, "rows": rows}, indent=1), encoding="utf-8")
    print(f"-> {out / 'sheet_faces.jpg'}, {out / 'sheet_lower.jpg'}, {out / 'study.json'}")
    return 0


def exemplar(name: str, stems: list[str], part: str, out: Path, study_dir: Path, trim_top: float = 0.0) -> int:
    study = json.loads((study_dir / "study.json").read_text(encoding="utf-8"))
    by = {stem_of(Path(r["photo"])): r for r in study["rows"]}
    tiles, used = [], []
    for st in stems:
        r = by.get(st)
        f = study_dir / f"{st}_{part}.jpg"
        if r is None or not f.is_file():
            raise SystemExit(f"{st}: not in {study_dir / 'study.json'} (run smiles first)")
        t = cv2.imread(str(f))
        tiles.append(t[int(t.shape[0] * trim_top):])      # --trim-top: drops the rims of glasses that reach the top of a lower-face crop
        used.append({"photo": r["photo"], "sha256": r["sha256"], "box": r[f"{part}_box"], "crop": str(f), "crop_sha256": sha256(f)})
    h = min(t.shape[0] for t in tiles)
    tiles = [cv2.resize(t, (int(t.shape[1] * h / t.shape[0]), h), interpolation=cv2.INTER_AREA) for t in tiles]
    gap = np.full((h, 12, 3), 30, np.uint8)
    sheet = tiles[0]
    for t in tiles[1:]:
        sheet = np.hstack([sheet, gap, t])
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 95])
    rec = {"kind": "smile_exemplar/1", "name": name, "part": part, "trim_top": trim_top, "eye_px": study.get("eye_px"), "sources": used, "out": str(out), "out_sha256": sha256(out)}
    Path(str(out) + ".json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"{out} {sheet.shape[1]}x{sheet.shape[0]} from {', '.join(stems)}")
    return 0


def compare(pics: list[Path], out: Path, with_stems: list[str], study_dir: Path) -> int:
    """Candidate pictures' faces beside his real smiles (study crops), all at one scale (eye distance EYE_PX), with identity, for his approval."""
    import identity
    from facecard import load_config
    from scorer import ArcFaceScorer, analyze_face
    scorer = ArcFaceScorer()
    pool = identity.build_pool(load_config(), scorer, verbose=False)
    head = []
    for st in with_stems:
        f = study_dir / f"{st}_face.jpg"
        if f.is_file():
            head.append(label(cv2.imread(str(f)), [f"REAL: {st}"]))
    tiles = []
    for p in pics:
        img = load(p)
        info = analyze_face(img)
        if not info.get("detected"):
            tiles.append(label(cv2.resize(img, (360, int(360 * img.shape[0] / img.shape[1]))), [p.parent.name[-22:] + "/" + p.name, "no face found"]))
            continue
        face_box, _lower, eye_d = boxes_from_landmarks(np.array(info["landmarks"], np.float32))
        res = identity.score_image(img, pool, scorer)
        sc = round(float(res["score"]), 3) if res.get("detected") and res.get("score") is not None else None
        tiles.append(label(cut(img, face_box, eye_d), [p.parent.name[:15] + ".." + p.parent.name[-18:], f"{p.name}  id {sc}"]))
        print(f"{p}: identity {sc}")
    sheet = grid(head, max(1, len(head))) if head else None
    body = grid(tiles, 4)
    if sheet is not None:
        w = max(sheet.shape[1], body.shape[1])
        sheet = cv2.copyMakeBorder(sheet, 0, 12, 0, w - sheet.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30))
        body = cv2.copyMakeBorder(body, 0, 0, 0, w - body.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30))
        body = np.vstack([sheet, body])
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), body, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"-> {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smiles")
    s.add_argument("photos", nargs="*")
    s.add_argument("--out", default=str(OUT))
    e = sub.add_parser("exemplar")
    e.add_argument("name")
    e.add_argument("stems", help="comma-separated stems as in study.json (e.g. DSC07985,IMG_6637,IMG_3884)")
    e.add_argument("--part", choices=["lower", "face"], default="lower")
    e.add_argument("--out", default=None, help="default .cache/inventories/pin_refs/his_smile_<name>.jpg")
    e.add_argument("--study", default=str(OUT))
    e.add_argument("--trim-top", type=float, default=0.0, help="fraction of each crop's height cut off at the top (glasses rims)")
    c = sub.add_parser("compare")
    c.add_argument("pictures", nargs="+")
    c.add_argument("--out", required=True)
    c.add_argument("--with", dest="with_stems", default="IMG_3884,DSC07985,IMG_6637,IMG_6875",
                   help="his real photos shown first (study stems; default his three best candid smiles and today's open-smile reference)")
    c.add_argument("--study", default=str(OUT))
    a = ap.parse_args()
    if a.cmd == "compare":
        return compare([Path(x) for x in a.pictures], Path(a.out), [x.strip() for x in a.with_stems.split(",") if x.strip()], Path(a.study))
    if a.cmd == "smiles":
        import paths
        photos = [Path(x) for x in a.photos] or ([DOWNLOADS / n for n in SMILES] + [paths.refs_dir() / n for n in REFS])
        missing = [str(p) for p in photos if not p.is_file()]
        if missing:
            raise SystemExit("missing: " + ", ".join(missing))
        return smiles(photos, Path(a.out))
    out = Path(a.out) if a.out else ROOT / ".cache" / "inventories" / "pin_refs" / f"his_smile_{a.name}.jpg"
    return exemplar(a.name, [x.strip() for x in a.stems.split(",") if x.strip()], a.part, out, Path(a.study), a.trim_top)


if __name__ == "__main__":
    sys.exit(main())
