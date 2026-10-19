"""Copy the pin's OWN background back around him, so background people, signs and lettering are the pin's pixels, not Gemini's redraw.

The user, 2026-10-09: "humans in the background are hard to handle and adding more makes it more complex; same goes for text in AI images", and yes to
"copy the pin's own background pixels back around you after Gemini's edit". An edit-mode pin (Route G, replace-subject) sends the pin as the PHOTO TO EDIT and
Gemini redraws parts of the scene it should have kept (pin 4's screens came back as "Simply ean the ntar to view out money"). This step is the code-copies half of
"the AI renders, code copies": only the union of the two person silhouettes (the pin man's and the new man's, dilated and feathered) comes from Gemini; every
other pixel is the pin's. Nothing Gemini drew is altered, and the raw sample is never touched: the copy is written beside it as vN_0r.jpg.

    .venv\\Scripts\\python.exe tools\\background_restore.py <run folder> [--sample v1_0.jpg ...] [--dilate 0.02] [--feather 0.008]
        a run whose recipe sets restore_background (facecard.py recipe new|bump --restore-background): every sample gets vN_Mr.jpg; one record in 06_measure/restore.json
    .venv\\Scripts\\python.exe tools\\background_restore.py --goal <pin.jpg> --sample <vN_0.jpg> --out <vN_0r.jpg>
        one sample, any files (a free test on pictures that exist)

Gemini's sparkle watermark (about 120 px in from the bottom-right corner) is replaced by the pin's pixels unless a silhouette reaches it; the restored picture is a composite already (AGENTS.md exception), and replicate.py never pastes the star either.

Overlays that are not part of the photograph (Pinterest's '1/7' slideshow counter, a watermark, a username) are NOT copied back: boxes in fractions of the frame, in `.cache/restore_exclude/<goal key>.json` (a list of [x0, y0, x1, y1]) or `--exclude x0,y0,x1,y1`, keep Gemini's pixels there (scene-prompt-writer: "app interface, caption, watermark, username: left out").

Person masks come from the YOLO segmentation of tools/body_measure_yolo.py (it needs no face box, so back views work). A sample is REFUSED, and no file is
written, when it re-framed the picture: the alignment of the background (ECC) must reach 0.80 with a scale inside 0.97-1.03 and a shift under 3%, and the
background outside both silhouettes must still resemble the pin (SSIM >= 0.45). Such a sample fails checklist item 26 anyway.
Checklist: record the restored picture with tools\\best_check.py on the vN_0r.jpg; items 33 (people) and 34 (text) are then identical to the pin by construction,
and the seams at the silhouette are looked at at 100%.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SAMPLE_RE = re.compile(r"^v(\d+)_(\d+)\.(jpg|jpeg|png)$", re.I)
ECC_MIN = 0.80
SCALE_RANGE = (0.97, 1.03)
SHIFT_MAX = 0.03             # of the frame's longer side
SSIM_MIN = 0.45
DIFF_T = 28                  # gray levels: where the sample and the pin differ more than this NEAR the person, the old man's leftovers (a bun, strands, a shadow) are Gemini's too
NEAR = 0.06                  # of the longer side: how far from the silhouettes the leftovers are looked for (text and people further away are never touched)
SPARKLE_OFFSET, SPARKLE_RADIUS = 120.0, 70.0   # px: Gemini's sparkle watermark sits about 120 px in from the bottom-right corner (replicate.py measured 120 / 52; the radius has a margin for the star's tips)


def load(path: Path) -> np.ndarray:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def yolo_masks(jobs: list[dict]) -> dict[str, dict]:
    """Run tools/body_measure_yolo.py in the YOLO venv: {image path: reading with 'mask' (a full-size png of the largest person) and 'persons'}."""
    import paths
    py = paths.yolo_python()
    if not py.is_file():
        raise SystemExit(f"the YOLO python is missing: {py}")
    with tempfile.TemporaryDirectory(prefix="restore_jobs_") as td:
        jf = Path(td) / "jobs.json"
        jf.write_text(json.dumps(jobs), encoding="utf-8")
        p = subprocess.run([str(py), str(ROOT / "tools" / "body_measure_yolo.py"), str(jf)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
    out = {}
    for line in p.stdout.splitlines():
        if line.startswith("CHAR_JSON "):
            d = json.loads(line[len("CHAR_JSON "):])
            out[d["path"]] = d
    return out


def ssim_outside(a: np.ndarray, b: np.ndarray, keep: np.ndarray) -> tuple[float | None, float | None]:
    """Mean absolute difference and SSIM of two BGR pictures over the pixels in `keep` (the formula of replicate_recipe.background_drift)."""
    h, w = a.shape[:2]
    if int(keep.sum()) < 500:
        return None, None
    ga = cv2.cvtColor(cv2.resize(a, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = cv2.resize(keep.astype(np.uint8), (w // 2, h // 2), interpolation=cv2.INTER_NEAREST) > 0
    mad = float(np.abs(ga - gb)[k].mean())
    mu_a, mu_b = cv2.GaussianBlur(ga, (0, 0), 3), cv2.GaussianBlur(gb, (0, 0), 3)
    va = cv2.GaussianBlur(ga * ga, (0, 0), 3) - mu_a * mu_a
    vb = cv2.GaussianBlur(gb * gb, (0, 0), 3) - mu_b * mu_b
    cov = cv2.GaussianBlur(ga * gb, (0, 0), 3) - mu_a * mu_b
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    return round(mad, 2), round(float(ssim[k].mean()), 3)


def align(pin: np.ndarray, sample: np.ndarray, bg: np.ndarray) -> tuple[float, np.ndarray | None]:
    """ECC (affine) of the pin (resized to the sample's size) onto the sample, over the background `bg` only; the warp is in full-size pixels."""
    h, w = sample.shape[:2]
    k = 480.0 / max(h, w)
    gs = cv2.cvtColor(cv2.resize(sample, None, fx=k, fy=k, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    gp = cv2.cvtColor(cv2.resize(pin, None, fx=k, fy=k, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    m = cv2.resize(bg, (gp.shape[1], gp.shape[0]), interpolation=cv2.INTER_NEAREST)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(gs, gp, warp, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), m, 5)
    except cv2.error:
        return 0.0, None
    warp = warp.copy()
    warp[:, 2] /= k
    return float(cc), warp


HEAD_SCORE = 0.8             # YuNet score of a human face: the men in pin 8 read 0.91-0.93, the kitten he holds 0.63-0.64 (2026-10-19)


def head_mask(img: np.ndarray) -> tuple[np.ndarray, list[list[float]]]:
    """Ellipses over every human head, hair included: each face the repo's YuNet finder sees at a score of HEAD_SCORE or more (none, as in a back
    view: an empty mask). 2026-10-19, pin 8 (the user: "the hair is not [right]"): YOLO's person mask stopped at the shoulders in the render AND
    the pin (a dark head against a dark wall), and dark curls over the pin man's dark straight hair differ too little for the leftovers rule, so
    the pin man's hair was copied over his curls while his face survived. Every head is Gemini's now. The largest face is not used: in one
    alignment that was the kitten's."""
    from scorer import DETECTOR_PATH
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    boxes: list[list[float]] = []
    for s in (1.0, 0.5, 0.25):          # a big close face that YuNet misses at full size is found on a smaller copy (smile_match.face_box)
        im = img if s == 1.0 else cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        det = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (im.shape[1], im.shape[0]), score_threshold=HEAD_SCORE)
        det.setInputSize((im.shape[1], im.shape[0]))
        _, faces = det.detect(im)
        if faces is not None and len(faces):
            boxes = [[float(v) / s for v in row[:4]] + [float(row[14])] for row in faces]
            break
    for x, y, bw, bh, _score in boxes:
        centre = (int(round(x + bw / 2)), int(round(y + 0.2 * bh)))       # the face box runs brow to chin: the hair sits above it
        cv2.ellipse(m, centre, (int(round(0.85 * bw)), int(round(1.05 * bh))), 0, 0, 360, 1, -1)
    return m > 0, [[round(x / w, 4), round(y / h, 4), round(bw / w, 4), round(bh / h, 4), round(sc, 2)] for x, y, bw, bh, sc in boxes]


def excluded_boxes(key: str, cli: list[str] | None) -> list[list[float]]:
    """The overlay boxes for a goal: .cache/restore_exclude/<goal key>.json plus --exclude x0,y0,x1,y1 (fractions of the frame)."""
    boxes: list[list[float]] = []
    f = ROOT / ".cache" / "restore_exclude" / f"{key}.json"
    if f.is_file():
        boxes += [list(map(float, b)) for b in json.loads(f.read_text(encoding="utf-8"))]
    for spec in cli or []:
        boxes.append([float(v) for v in spec.split(",")])
    return boxes


def restore_one(goal_path: Path, sample_path: Path, out_path: Path, dilate: float, feather: float, masks: dict, exclude: list | None = None, say=print,
                only_sparkle: bool = False) -> dict:
    """One sample. `masks` is yolo_masks() output for the goal and the sample. Returns the record; writes `out_path` unless refused.
    only_sparkle (2026-10-19, pin 8): every pixel stays Gemini's except the sparkle watermark, which becomes the pin's; for a pin whose background
    has no people and no text to protect, where copying the background back only costs seams (a dark mirror selfie)."""
    G, S = load(goal_path), load(sample_path)
    h, w = S.shape[:2]
    rec: dict = {"sample": sample_path.name, "out": out_path.name, "size": [w, h], "goal_size": [G.shape[1], G.shape[0]]}
    if abs((w / h) / (G.shape[1] / G.shape[0]) - 1) > 0.03:
        rec["refused"] = f"the sample's aspect ratio {w / h:.3f} is not the goal's {G.shape[1] / G.shape[0]:.3f}"
        return rec
    mg, ms = masks.get(str(goal_path)), masks.get(str(sample_path))
    if not mg or not mg.get("mask") or not ms or not ms.get("mask"):
        rec["refused"] = "no person mask for " + ("the goal" if not (mg and mg.get("mask")) else "the sample")
        return rec
    rec["persons_in_goal"], rec["persons_in_sample"] = mg.get("persons"), ms.get("persons")
    Gp = cv2.resize(G, (w, h), interpolation=cv2.INTER_AREA if G.shape[1] > w else cv2.INTER_CUBIC)
    mG = cv2.resize(cv2.imread(mg["mask"], cv2.IMREAD_GRAYSCALE), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    mS = cv2.imread(ms["mask"], cv2.IMREAD_GRAYSCALE)
    mS = (cv2.resize(mS, (w, h), interpolation=cv2.INTER_NEAREST) if mS.shape != (h, w) else mS) > 0
    r = max(3, int(dilate * max(h, w)))
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    union0 = (mG | mS).astype(np.uint8)
    wide = cv2.dilate(union0, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * r + 1, 4 * r + 1)))
    bg = ((1 - wide) * 255).astype(np.uint8)
    rec["person_pct"] = {"goal": round(float(mG.mean()) * 100, 1), "sample": round(float(mS.mean()) * 100, 1), "union": round(float(union0.mean()) * 100, 1)}
    cc, warp = align(Gp, S, bg)
    rec["ecc"] = round(cc, 3)
    if warp is None or cc < ECC_MIN:
        rec["refused"] = f"the sample re-framed the picture (background ECC {cc:.3f} < {ECC_MIN})"
        return rec
    scale = float(np.sqrt(abs(np.linalg.det(warp[:, :2]))))
    shift = float(max(abs(warp[0, 2]), abs(warp[1, 2]))) / max(h, w)
    rec["warp"] = {"scale": round(scale, 4), "shift_frac": round(shift, 4), "m": [[round(float(v), 5) for v in row] for row in warp]}
    if not (SCALE_RANGE[0] <= scale <= SCALE_RANGE[1]) or shift > SHIFT_MAX:
        rec["refused"] = f"the sample re-framed the picture (scale {scale:.3f}, shift {shift:.3f} of the frame)"
        return rec
    identity = abs(warp[0, 0] - 1) < 0.002 and abs(warp[1, 1] - 1) < 0.002 and abs(warp[0, 1]) < 0.002 and abs(warp[1, 0]) < 0.002 and max(abs(warp[0, 2]), abs(warp[1, 2])) < 0.7
    rec["warp_applied"] = not identity
    if identity:
        Ga, mGa = Gp, mG
    else:
        flags = cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP
        Ga = cv2.warpAffine(Gp, warp, (w, h), flags=flags, borderMode=cv2.BORDER_REPLICATE)
        mGa = cv2.warpAffine(mG.astype(np.uint8) * 255, warp, (w, h), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP) > 0
    hS, boxS = head_mask(S)                 # his head in the render and the pin man's head (the aligned pin, so in the render's frame): both Gemini's
    hG, boxG = head_mask(Ga)
    rec["heads"] = {"sample_faces": boxS, "goal_faces": boxG, "pct": round(float((hS | hG).mean()) * 100, 1)}
    union = (mGa | mS | hS | hG).astype(np.uint8)
    yy, xx = np.ogrid[:h, :w]
    sparkle = ((xx - (w - SPARKLE_OFFSET)) ** 2 + (yy - (h - SPARKLE_OFFSET)) ** 2) <= SPARKLE_RADIUS ** 2
    sparkle_free = not bool((union > 0)[sparkle].any())      # nobody stands under the star: the pin's pixels replace it; otherwise it stays Gemini's and the QC sees it
    rec["sparkle"] = "replaced by the pin's pixels" if sparkle_free else "left as Gemini produced it: a silhouette reaches it"
    # leftovers of the old man next to the new one (the pin's bun or hair strands outside the segmentation mask): where the sample differs strongly from the pin
    # inside a band around the silhouettes, the sample's pixels are kept too
    near = cv2.dilate(union, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(NEAR * max(h, w)) + 1, 2 * int(NEAR * max(h, w)) + 1))) > 0
    dgray = cv2.GaussianBlur(cv2.absdiff(cv2.cvtColor(S, cv2.COLOR_BGR2GRAY), cv2.cvtColor(Ga, cv2.COLOR_BGR2GRAY)), (0, 0), 2.0)
    grown = ((dgray > DIFF_T) & near & (union == 0) & ~(sparkle if sparkle_free else np.zeros_like(sparkle)))
    grown = cv2.morphologyEx(grown.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n_g, lab_g, st_g, _ = cv2.connectedComponentsWithStats(grown, connectivity=8)
    for i in range(1, n_g):
        if st_g[i, cv2.CC_STAT_AREA] < 30:
            grown[lab_g == i] = 0
    rec["grown_pct"] = round(float(grown.mean()) * 100, 2)
    union = ((union > 0) | (grown > 0)).astype(np.uint8)
    union_d = cv2.dilate(union, kern)
    m = cv2.GaussianBlur(union_d.astype(np.float32), (0, 0), max(1.0, feather * max(h, w)))
    m = np.clip(m * 1.0, 0, 1)
    for box in exclude or []:          # overlays of the pin that are not the photograph: Gemini's pixels stay there
        x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
        e = np.zeros((h, w), np.float32)
        e[y0:y1, x0:x1] = 1
        m = np.maximum(m, cv2.GaussianBlur(e, (0, 0), max(1.0, feather * max(h, w) / 2)))
    soft_star = np.clip(cv2.GaussianBlur(sparkle.astype(np.float32), (0, 0), 2.0), 0, 1)
    m = m * (1 - soft_star) if sparkle_free else np.maximum(m, soft_star)      # the whole star is the pin's pixels or the whole star stays as Gemini produced it, never half of it
    if only_sparkle:
        m = (1 - soft_star) if sparkle_free else np.ones_like(m)
        rec["only_sparkle"] = True
    rec["excluded_boxes"] = [list(map(float, b)) for b in exclude or []]
    m = m[..., None]
    copied = (m[..., 0] < 0.01)
    mad, ssim = ssim_outside(S, Ga, copied)
    rec["background_before"] = {"copied_pct": round(float(copied.mean()) * 100, 1), "mean_abs_diff": mad, "ssim": ssim}
    if ssim is not None and ssim < SSIM_MIN:
        rec["refused"] = f"the background outside both silhouettes is not the pin's any more (SSIM {ssim:.3f} < {SSIM_MIN}): the scene was redrawn"
        return rec
    out = (S.astype(np.float32) * m + Ga.astype(np.float32) * (1 - m)).round().clip(0, 255).astype(np.uint8)
    after = float(np.abs(out.astype(np.int16) - Ga.astype(np.int16))[copied].mean()) if copied.any() else None
    rec["background_after"] = {"mean_abs_diff_to_pin": None if after is None else round(after, 3)}
    rec["dilate_px"], rec["feather_px"] = r, round(max(1.0, feather * max(h, w)), 1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
    say(f"  {sample_path.name} -> {out_path.name}: ECC {cc:.3f}, background before: mean diff {mad}, SSIM {ssim}; copied {rec['background_before']['copied_pct']}% of the frame from the pin")
    return rec


def restore_run(run_dir: Path, samples: list[str] | None, dilate: float, feather: float, exclude_cli: list[str] | None = None) -> int:
    import provenance as P
    rp = run_dir / "01_method" / "recipe.json"
    rec = json.loads(rp.read_text(encoding="utf-8")) if rp.is_file() else None
    if rec is None:
        raise SystemExit(f"{run_dir}: no 01_method/recipe.json (not a staged run)")
    if not (rec.get("method", {}).get("args") or {}).get("restore_background"):
        raise SystemExit(f"{run_dir.name}: the recipe does not set restore_background (use recipe bump --restore-background)")
    gsha = rec["goal"]["sha256"]
    gp = P.blob_path(gsha)
    if gp is None:
        raise SystemExit(f"the goal's blob {gsha[:12]} is missing from the blob store")
    files = sorted((p for p in run_dir.iterdir() if p.is_file() and SAMPLE_RE.match(p.name)), key=lambda p: p.name)
    if samples:
        files = [p for p in files if p.name in samples]
    if not files:
        raise SystemExit(f"{run_dir.name}: no vN_M samples found")
    mdir = run_dir / "06_measure" / "restore_masks"
    mdir.mkdir(parents=True, exist_ok=True)
    jobs = [{"path": str(gp), "mask": str(mdir / "goal_mask.png")}] + [{"path": str(f), "mask": str(mdir / f"{f.stem}_mask.png")} for f in files]
    masks = yolo_masks(jobs)
    exclude = excluded_boxes(rec["goal"]["key"], exclude_cli)
    records = []
    for f in files:
        out = f.with_name(f.stem + "r.jpg")
        records.append(restore_one(gp, f, out, dilate, feather, masks, exclude))
        if records[-1].get("refused"):
            print(f"  {f.name}: REFUSED, {records[-1]['refused']}")
    (run_dir / "06_measure" / "restore.json").write_text(json.dumps({"kind": "pin_background/1", "goal_sha256": gsha, "dilate": dilate, "feather": feather,
                                                                     "samples": records}, indent=1, ensure_ascii=False), encoding="utf-8")
    done = sum(1 for r in records if not r.get("refused"))
    print(f"{run_dir.name}: {done} of {len(records)} sample(s) restored -> 06_measure/restore.json")
    return 0 if done else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", nargs="?", help="a staged run folder (outputs/<stamp>_goal-...)")
    ap.add_argument("--sample", action="append", default=None, help="run mode: only this sample (repeatable); single mode: the sample picture")
    ap.add_argument("--goal", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--exclude", action="append", default=None, help="x0,y0,x1,y1 (fractions of the frame): an overlay of the pin that stays Gemini's (repeatable)")
    ap.add_argument("--dilate", type=float, default=0.02, help="dilation of the person union, as a share of the longer side (default 0.02)")
    ap.add_argument("--feather", type=float, default=0.008, help="feather of the seam, as a share of the longer side (default 0.008)")
    ap.add_argument("--only-sparkle", action="store_true", dest="only_sparkle",
                    help="single mode: keep every pixel of the render except Gemini's sparkle watermark (the pin's pixels there); for a pin with no "
                         "background people or text")
    a = ap.parse_args()
    if a.goal:
        if not (a.sample and len(a.sample) == 1 and a.out):
            ap.error("single mode needs --goal, one --sample and --out")
        goal, sample, out = Path(a.goal), Path(a.sample[0]), Path(a.out)
        mdir = out.parent / (out.stem + "_masks")
        masks = yolo_masks([{"path": str(goal), "mask": str(mdir / "goal_mask.png")}, {"path": str(sample), "mask": str(mdir / "sample_mask.png")}])
        rec = restore_one(goal, sample, out, a.dilate, a.feather, masks, excluded_boxes(goal.stem, a.exclude), only_sparkle=a.only_sparkle)
        print(json.dumps(rec, indent=1, ensure_ascii=False))
        return 1 if rec.get("refused") else 0
    if not a.run:
        ap.error("a run folder (or --goal/--sample/--out) is required")
    return restore_run(Path(a.run), a.sample, a.dilate, a.feather, a.exclude)


if __name__ == "__main__":
    sys.exit(main())
