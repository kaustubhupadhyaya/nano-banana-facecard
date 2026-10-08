"""Character measures, record-only (2026-10-08): how full his face is and how heavy his build is, as numbers, so that pictures made from the
same references can be compared (the user: the pictures show different body types and body fat, visible in the face too).

Never a gate: nothing here decides, ranks or rejects a picture. A measure is trusted only after tools/character_audit.py has validated it
(an earlier arm measure from YOLO masks read a pin man as slimmer-armed than him and was deleted; FEEDBACK_LOG section 14).

Face: 2dfan4 68 landmarks (landmarks.py, FaceFusion model), in-plane roll removed. Measured only when headpose.py reads |yaw| and |pitch| <= 25,
the SCRFD face box is at least 1.1 times as tall as wide (HeadPoseONNX read pin 9's steeply bowed face as pitch -22; its box is 0.84), the
eye centres are at least 30 px apart, the landmark fit passes its mirror test, no wrist keypoint is beside the face box or up to 1.2 face
heights below it (a phone, camera or hand there hides the jaw and 2dfan4 traces the jaw along its edge: in the pin 8 mirror selfies the
phone hand's wrist is 2.0 face-box heights below the box top), at least 90 % of the face
outline is face to BiSeNet, and eye-to-mouth / eye distance is 0.75-1.25 (his studio photos 0.82-1.01; bowed or covered faces that passed the
pose reading read 1.38-1.69). The last three rules were added after the audit's face strip showed them. The facial-adiposity cues of Coetzee, Perrett & Stephen
2009 ("Facial adiposity: a cue to health?") and Coetzee et al. 2010 ("Deciphering faces: quantifiable visual cues to weight"), plus three widths:
  cjwr       bizygomatic width (widest point of the jaw outline between the eye corners and the nose base) / jaw width at the mouth corners'
             height. Lower = a squarer, wider lower face (heavier).
  fwhr       bizygomatic width / upper-face height (highest upper-eyelid point to the top of the upper lip). Higher = heavier.
  par        perimeter / area of the face below the eyes (the jaw outline closed along the lower eyelids), times the interocular distance so it has
             no unit (the papers aligned faces on the pupils). Lower = rounder (heavier).
  jaw_iod    jaw width at the mouth corners / interocular distance (eye centres). Higher = a wider lower face.
  cheek_iod  bizygomatic width / interocular distance.
  neck_face  neck width (20th percentile of the FaceFusion BiSeNet 'neck' widths from just below the chin to 0.6 face heights down) /
             bizygomatic width. Higher = a thicker neck.
  His full beard: the jaw points sit on the beard's outline, not on the bone. That is the same in every photo of him, but a render with a
  longer or fuller beard reads as a wider jaw.

Body: tools/body_measure_yolo.py in the YOLO venv (yolo11m-pose keypoints + the yolo11m-seg silhouette of the largest person) and the ATR human
parser (segment.py, which labels each arm separately from the torso, so an arm resting against the body can still be measured). The head unit
is the interocular distance / cos(yaw) of the same person's face, at |yaw| <= 25 and any pitch (eye positions do not change with fat, unlike
the face's width, and their distance does not change when the head bows), from a landmark fit that passes its mirror test.
"Frontal" = both shoulders and both hips at confidence >= 0.5, torso within 25 degrees of vertical, shoulder/hip keypoint width 1.15-2.2 and
shoulder width >= 0.45 torso length (a side-on or bent-over torso fails):
  shoulder_iod    shoulder keypoint width / head unit (frontal)
  bideltoid_iod   silhouette width along the shoulder line (deltoid to deltoid) / head unit (frontal)
  arm_iod         upper-arm width / head unit. Width = the ATR arm region across the shoulder-elbow line at 45/55/65 % (median of >= 2);
                  an upper arm covered by a sleeve is not measured.
  arm_shoulder    upper-arm width / shoulder keypoint width (frontal)
  arm_length      upper-arm width / the upper arm's own keypoint length (needs no face and no frontal torso)
  waist_shoulder  ATR torso width (clothes or skin, arms excluded) at 60 % from the shoulder line to the hip line / shoulder width (frontal)
  waist_iod       the same width / head unit (frontal)
  torso_head      shoulder midpoint to hip midpoint / head height (eye line to chin) (frontal)
  shoulder_ears   shoulder keypoint width / ear-to-ear keypoint width (frontal, both ears >= 0.5)

measure(path) caches by the file's sha256 in .cache/character_measures.json (raw model readings + the measures; a new MEASURE_VERSION recomputes
the measures from the cached readings and the masks in .cache/character_masks without running a model again).

    .venv\\Scripts\\python.exe character.py <image> [<image> ...] [--overlay DIR]
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

import paths
import provenance as P

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".cache" / "character_measures.json"
MASKS = ROOT / ".cache" / "character_masks"
YOLO_SCRIPT = ROOT / "tools" / "body_measure_yolo.py"

FACE_RAW_VERSION = 2     # what is read from the face models (2: landmarks at every head pose, for the sheets); a change re-runs them
MEASURE_VERSION = 7      # how measures are computed from the readings; a change recomputes from the cache

FACE_POSE_MAX = 25.0
FACE_BOX_ASPECT_MIN = 1.1
FACE_IOD_MIN = 30.0      # px between the eye centres; below it a 1-2 px landmark error is 5-10 % of every width
FACE_VISIBLE_MIN = 0.9   # share of the face outline BiSeNet labels as face parts (added after the audit's face strip showed phones over jaws)
EMD_IOD = (0.75, 1.25)   # eye-to-mouth / eye distance; his studio photos read 0.82-1.01, pin 8's man 1.16; HeadPoseONNX-passed faces that
                         # were steeply bowed or had the eyes covered read 1.38-1.69 (added after the audit's face strip)
FACE_VIS_VERSION = 1
KP_CONF = 0.5
TORSO_TILT_MAX = 25.0
SH_HIP = (1.15, 2.2)
SH_TORSO_MIN = 0.45
ARM_T = (0.45, 0.55, 0.65)
ATR_ARMS = (14, 15)
ATR_TORSO = (4, 5, 6, 7, 8, 11, 17)      # upper clothes, skirt, pants, dress, belt, 'face' (ATR also gives bare torso skin this label), scarf

# key -> (label, which way reads heavier / fuller: +1 higher, -1 lower, 0 not a fat cue)
MEASURES = {
    "face.cjwr": ("cheek-to-jaw width ratio (CJWR)", -1),
    "face.fwhr": ("face width / upper-face height (fWHR)", +1),
    "face.par": ("perimeter / area below the eyes x IOD (PAR)", -1),
    "face.jaw_iod": ("jaw width at the mouth / interocular distance", +1),
    "face.cheek_iod": ("bizygomatic width / interocular distance", +1),
    "face.neck_face": ("neck width / face width", +1),
    "body.shoulder_iod": ("shoulder keypoint width / head unit", +1),
    "body.bideltoid_iod": ("silhouette width at the shoulder line / head unit", +1),
    "body.arm_iod": ("upper-arm width / head unit", +1),
    "body.arm_shoulder": ("upper-arm width / shoulder keypoint width", +1),
    "body.arm_length": ("upper-arm width / upper-arm length", +1),
    "body.waist_shoulder": ("waist width / shoulder keypoint width", +1),
    "body.waist_iod": ("waist width / head unit", +1),
    "body.torso_head": ("torso length / head height (eye line to chin)", 0),
    "body.shoulder_ears": ("shoulder keypoint width / ear-to-ear width", +1),
}
PAR_RING = list(range(17)) + [45, 46, 47, 42, 39, 40, 41, 36]

# Measures that passed tools/character_audit.py's validation (run 2026-10-08, D:\FacecardReview\character_audit_2026-10-08.html); everything
# else is an unvalidated number. The face ones are tight on his studio photos (3-10 %) and repeat within 0.5 % on copies of the same photo,
# but only one goal man's face was measurable, so whether they read fat rather than beard is untested. arm_shoulder separates pins 7 and 8
# from him by under one band width only: a man with heavier arms usually has wider shoulder keypoints too.
TRUSTED: frozenset[str] = frozenset({"face.cjwr", "face.par", "face.jaw_iod", "face.cheek_iod", "body.arm_shoulder"})


# ------------------------------------------------------------------------------------------------------------------------------ files


def load(path) -> np.ndarray:
    """BGR pixels with the EXIF orientation applied (the same reading tools/body_measure_yolo.py makes, so the coordinates agree)."""
    from PIL import Image, ImageOps
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    with Image.open(path) as im:
        rgb = np.array(ImageOps.exif_transpose(im).convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_cache() -> dict:
    try:
        d = json.loads(CACHE.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) and "entries" in d else {"entries": {}}
    except Exception:
        return {"entries": {}}


def _write_cache(cache: dict) -> None:
    P.atomic_write_json(CACHE, cache, indent=None)


# ------------------------------------------------------------------------------------------------------------------------------ geometry


def line_runs(mask: np.ndarray, origin, direction, half_len: float) -> list[tuple[float, float]]:
    """Runs of mask pixels along the line origin + s * direction, s in [-half_len, half_len] (1 px steps), as (s_start, s_end)."""
    s = np.arange(-int(half_len), int(half_len) + 1, dtype=np.float64)
    xs = np.rint(origin[0] + s * direction[0]).astype(int)
    ys = np.rint(origin[1] + s * direction[1]).astype(int)
    h, w = mask.shape[:2]
    inside = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    vals = np.zeros(len(s), bool)
    vals[inside] = mask[ys[inside], xs[inside]] > 0
    runs, start = [], None
    for i, v in enumerate(vals):
        if v and start is None:
            start = s[i]
        if not v and start is not None:
            runs.append((float(start), float(s[i - 1])))
            start = None
    if start is not None:
        runs.append((float(start), float(s[-1])))
    return runs


def _run_at(runs, s0: float = 0.0, tol: float = 2.0):
    for a, b in runs:
        if a - tol <= s0 <= b + tol:
            return a, b
    return None


def _x_at(poly: np.ndarray, y: float, side: str):
    """x where a polyline crosses height y (outermost crossing: smallest x for side 'left', largest for 'right'), or None."""
    xs = []
    for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
    if not xs:
        return None
    return min(xs) if side == "left" else max(xs)


def _width_at(lm: np.ndarray, y: float):
    xl, xr = _x_at(lm[0:9], y, "left"), _x_at(lm[8:17], y, "right")
    return None if xl is None or xr is None else (xr - xl, xl, xr)


def _roll_frame(lm: np.ndarray):
    """Landmarks in a frame centred on the eye midpoint with the eye line horizontal (x right, y down), and the inverse mapping."""
    le, re_ = lm[36:42].mean(axis=0), lm[42:48].mean(axis=0)
    c = (le + re_) / 2.0
    th = math.atan2(re_[1] - le[1], re_[0] - le[0])
    ux, uy = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
    rot = (lm - c) @ np.stack([ux, uy]).T

    def back(p):
        return c + p[0] * ux + p[1] * uy

    return rot, back, ux, uy, float(np.linalg.norm(re_ - le)), math.degrees(th)


def _seg(p, q) -> list[int]:
    return [int(round(p[0])), int(round(p[1])), int(round(q[0])), int(round(q[1]))]


# ------------------------------------------------------------------------------------------------------------------------------ face


def face_raw(img: np.ndarray) -> dict:
    """Head pose, the SCRFD face box and (for a usable pose) the 68 landmarks and the neck width profile."""
    import headpose
    import landmarks
    hp = headpose.measure(img)
    out = {"pose": hp}
    if not hp.get("detected"):
        return out
    det, _ = headpose._models()
    boxes, _kps = det.detect(img)
    if boxes is None or not len(boxes):
        return out
    b = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    box = (int(b[0]), int(b[1]), int(b[2] - b[0]), int(b[3] - b[1]))
    out["box"] = list(box)
    lm, q = landmarks.landmarks68_searched(img, box)       # at every pose: the sheets align on the eyes; measures use them only in range
    out["lm"] = np.round(lm, 1).tolist()
    out["lm_quality"] = q
    if abs(hp["yaw"]) <= FACE_POSE_MAX and abs(hp["pitch"]) <= FACE_POSE_MAX:
        out["neck"] = neck_profile(img, lm, box)
    return out


FACE_PARTS = (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 17)     # BiSeNet: skin, brows, eyes, glasses, ears, nose, mouth, lips, hair (beard)


def face_visible(img: np.ndarray, lm: np.ndarray, box) -> dict:
    """Share of the face outline (jaw points closed along the brows) that BiSeNet labels as face parts. A phone, camera or hand over the
    face is not a face part; 2dfan4 still places the hidden jaw points (it guesses them), so an occluded face must not be measured."""
    import segment
    if not segment.BISENET_PATH.is_file():
        return {"available": False, "why": f"BiSeNet model missing: {segment.BISENET_PATH}"}
    x, y, w, h = box
    fs = float(max(w, h))
    crop, cbox = segment.square_crop(img, x + w / 2, y + h / 2, 1.5 * fs)
    lab = segment.bisenet_labels(crop)
    poly = np.vstack([lm[0:17], lm[26:16:-1]]) - np.array([cbox[0], cbox[1]])
    m = np.zeros(lab.shape, np.uint8)
    cv2.fillPoly(m, [np.round(poly * lab.shape[0] / cbox[2]).astype(np.int32)], 1)
    inside = lab[m > 0]
    if not inside.size:
        return {"available": True, "share": 0.0, "pixels": 0}
    vals, counts = np.unique(inside, return_counts=True)
    return {"available": True, "share": round(float(np.isin(inside, FACE_PARTS).mean()), 3), "pixels": int(inside.size),
            "labels": {str(int(v)): int(c) for v, c in zip(vals, counts)}}


def neck_profile(img: np.ndarray, lm: np.ndarray, box) -> dict:
    """Widths of the BiSeNet neck region below the chin, along the eye-line direction, at steps of 1/40 face height."""
    import segment
    if not segment.BISENET_PATH.is_file():
        return {"available": False, "why": f"BiSeNet model missing: {segment.BISENET_PATH}"}
    x, y, w, h = box
    fs = float(max(w, h))
    crop, cbox = segment.square_crop(img, x + w / 2, y + h / 2 + 0.35 * fs, 2.0 * fs)
    lab = segment.bisenet_labels(crop)
    neck = segment.uncrop(((lab == segment.BISENET["neck"]) * 255).astype(np.uint8), cbox, img.shape)
    rot, back, ux, uy, iod, _ = _roll_frame(lm)
    chin = rot[8]
    face_h = float(chin[1] - rot[17:27, 1].mean())
    rows = []
    for i in range(0, 33):                     # 0 .. 0.8 face heights below the chin
        t = i / 40.0
        p = back(np.array([chin[0], chin[1] + t * face_h]))
        runs = line_runs(neck, p, ux, 1.5 * fs)
        if not runs:
            continue
        a, b = min(runs, key=lambda r: 0 if r[0] <= 0 <= r[1] else min(abs(r[0]), abs(r[1])))
        rows.append([round(t, 3), round(b - a + 1, 1), _seg(back(np.array([chin[0] + a, chin[1] + t * face_h])),
                                                          back(np.array([chin[0] + b, chin[1] + t * face_h])))])
    return {"available": True, "face_h": round(face_h, 1), "rows": rows, "neck_px": int((neck > 0).sum())}


def face_from(raw: dict) -> dict:
    pose = raw.get("pose") or {}
    out = {"usable": False, "reason": None, "values": {}, "yaw": pose.get("yaw"), "pitch": pose.get("pitch"), "roll": pose.get("roll"),
           "notes": [], "draw": []}
    if not pose.get("detected"):
        out["reason"] = "no face found" + (f" ({pose.get('error')})" if pose.get("error") else "")
        return out
    q0 = raw.get("lm_quality") or {}
    if raw.get("lm") and q0.get("usable") and abs(pose["yaw"]) <= FACE_POSE_MAX:
        # the body's head unit: the eye distance does not change when the head bows or lifts (pitch), only when it turns (yaw, corrected)
        lm0 = np.array(raw["lm"], np.float64)
        le0, re0 = lm0[36:42].mean(axis=0), lm0[42:48].mean(axis=0)
        iod0 = float(np.linalg.norm(re0 - le0))
        if iod0 >= FACE_IOD_MIN:
            out.update({"head_unit_px": round(iod0 / max(0.5, math.cos(math.radians(pose["yaw"]))), 1),
                        "centre": [round(float(x), 1) for x in (le0 + re0) / 2]})
    if abs(pose["yaw"]) > FACE_POSE_MAX or abs(pose["pitch"]) > FACE_POSE_MAX:
        out["reason"] = f"head pose out of range (yaw {pose['yaw']:+.0f}, pitch {pose['pitch']:+.0f}; limit +/-{FACE_POSE_MAX:.0f})"
        return out
    box = raw.get("box") or [0, 0, 1, 1]
    out["box_aspect"] = round(box[3] / max(1, box[2]), 2)
    if out["box_aspect"] < FACE_BOX_ASPECT_MIN:
        out["reason"] = f"face box {out['box_aspect']} times as tall as wide (< {FACE_BOX_ASPECT_MIN}: a steep bow or raised chin)"
        return out
    if "lm" not in raw:
        out["reason"] = "no landmarks"
        return out
    q = raw.get("lm_quality") or {}
    out["lm_conf"], out["mirror_offset"], out["lm_view"] = q.get("heatmap_conf"), q.get("mirror_offset"), q.get("view")
    if not q.get("usable"):
        out["reason"] = f"landmark fit failed its mirror test (offset {q.get('mirror_offset')})"
        return out
    bx, by, bw, bh = raw.get("box") or [0, 0, 1, 1]
    for name, w in (raw.get("wrists") or {}).items():
        if w and w[2] >= KP_CONF and bx - 0.5 * bw <= w[0] <= bx + 1.5 * bw and by - 0.5 * bh <= w[1] <= by + 2.2 * bh:
            out["reason"] = (f"a hand at the face ({name} keypoint beside the face or up to 1.2 faces below it): a phone, camera or hand there "
                             "hides the jaw, and 2dfan4 traces the jaw along its edge")
            return out
    vis = raw.get("visible") or {}
    out["visible"] = vis.get("share")
    if vis.get("available") and vis.get("share", 0) < FACE_VISIBLE_MIN:
        out["reason"] = f"face covered: {vis['share']:.0%} of the face outline is face (< {FACE_VISIBLE_MIN:.0%}; phone, camera or hand)"
        return out
    lm = np.array(raw["lm"], np.float64)
    r0, _b, _ux, _uy, iod0, _r = _roll_frame(lm)
    out["emd_iod"] = round(float((r0[51][1] + r0[57][1]) / 2 / iod0), 2) if iod0 > 0 else None
    if out["emd_iod"] is None or not (EMD_IOD[0] <= out["emd_iod"] <= EMD_IOD[1]):
        out["reason"] = (f"eye-to-mouth / eye distance {out['emd_iod']} outside {EMD_IOD[0]}-{EMD_IOD[1]} (a bowed or covered face read as "
                         "frontal, or a failed fit)")
        return out
    rot, back, ux, uy, iod, roll = _roll_frame(lm)
    y_top, y_bot = max(rot[0][1], rot[16][1]), rot[33][1]
    best = None
    for y in np.linspace(min(y_top, y_bot), max(y_top, y_bot), 25):
        wa = _width_at(rot, y)
        if wa and (best is None or wa[0] > best[0][0]):
            best = (wa, y)
    y_m = (rot[48][1] + rot[54][1]) / 2.0
    jaw = _width_at(rot, y_m)
    if best is None or jaw is None or iod <= 0:
        out["reason"] = "jaw outline incomplete"
        return out
    if iod < FACE_IOD_MIN:
        out["reason"] = f"face too small (eye centres {iod:.0f} px apart, {FACE_IOD_MIN:.0f} needed)"
        return out
    (biz, bl, br), y_b = best
    jw, jl, jr = jaw
    ufh = rot[51][1] - min(rot[i][1] for i in (37, 38, 43, 44))
    ring = rot[PAR_RING]
    perim = float(np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1).sum())
    area = 0.5 * abs(float(np.dot(ring[:, 0], np.roll(ring[:, 1], -1)) - np.dot(ring[:, 1], np.roll(ring[:, 0], -1))))
    v = {"cjwr": biz / jw, "fwhr": biz / ufh if ufh > 0 else None, "par": perim / area * iod if area > 0 else None,
         "jaw_iod": jw / iod, "cheek_iod": biz / iod}
    out["draw"] += [_seg(back((bl, y_b)), back((br, y_b))), _seg(back((jl, y_m)), back((jr, y_m)))]
    neck = raw.get("neck") or {}
    if not neck.get("available"):
        out["notes"].append("neck not measured: " + str(neck.get("why") or "no BiSeNet reading"))
    else:
        rows = [r for r in neck["rows"] if 0.05 <= r[0] <= 0.6]
        if len(rows) >= 5:
            widths = np.array([r[1] for r in rows])
            nw = float(np.percentile(widths, 20))
            v["neck_face"] = nw / biz
            pick = min(rows, key=lambda r: abs(r[1] - nw))
            out["draw"].append(pick[2])
            out["neck_rows"] = len(rows)
        else:
            out["notes"].append(f"neck not measured: BiSeNet found neck on {len(rows)} rows below the chin (5 needed)")
    out["values"] = {k: round(float(x), 4) for k, x in v.items() if x is not None and math.isfinite(x)}
    yaw_c = max(0.5, math.cos(math.radians(pose["yaw"])))
    out.update({"usable": True, "face_px": round(biz, 1), "iod_px": round(iod, 1), "head_unit_px": round(iod / yaw_c, 1),
                "head_h_px": round(float(rot[8][1]), 1), "lm_roll": round(roll, 1),
                "centre": [round(float(x), 1) for x in back((0.0, 0.0))]})
    out["notes"].append("jaw points sit on the beard outline (full beard)")
    return out


# ------------------------------------------------------------------------------------------------------------------------------ body


def yolo_raw(paths_: list[Path], masks: list[Path], say=print) -> dict[str, dict]:
    """Run tools/body_measure_yolo.py once over many pictures in the YOLO venv; {path: reading}."""
    py = paths.yolo_python()
    if not py.is_file():
        return {str(p): {"error": f"YOLO interpreter missing: {py}"} for p in paths_}
    jobs = [{"path": str(p), "mask": str(m), "models_dir": str(paths.yolo_models_dir())} for p, m in zip(paths_, masks)]
    fd, jf = tempfile.mkstemp(suffix=".json", prefix="character_jobs_")
    os.close(fd)
    Path(jf).write_text(json.dumps(jobs), encoding="utf-8")
    out: dict[str, dict] = {}
    try:
        proc = subprocess.Popen([str(py), str(YOLO_SCRIPT), jf], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                encoding="utf-8", cwd=str(ROOT))
        for line in proc.stdout:
            if line.startswith("CHAR_JSON "):
                d = json.loads(line[10:])
                out[d["path"]] = d
                say(f"  [body] {len(out)}/{len(jobs)} {Path(d['path']).name}")
        proc.wait()
    finally:
        Path(jf).unlink(missing_ok=True)
    return out


def atr_raw(img: np.ndarray, body: dict, out_png: Path) -> dict:
    """ATR human-parsing labels of the person (parsed from a crop around YOLO's person box so the parser sees enough pixels), saved full size."""
    import segment
    if not segment.ATR_PATH.is_file():
        return {"error": f"ATR model missing: {segment.ATR_PATH}"}
    person = body.get("person")
    if not person:
        return {"error": "no person"}
    H, W = img.shape[:2]
    x0, y0, x1, y1 = person["box"]
    mx, my = 0.1 * (x1 - x0), 0.1 * (y1 - y0)
    x0, y0, x1, y1 = max(0, int(x0 - mx)), max(0, int(y0 - my)), min(W, int(x1 + mx)), min(H, int(y1 + my))
    if (x1 - x0) * (y1 - y0) > 0.85 * W * H:
        x0, y0, x1, y1 = 0, 0, W, H
    lab = np.zeros((H, W), np.uint8)
    lab[y0:y1, x0:x1] = segment.atr_labels(img[y0:y1, x0:x1])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_png), lab)
    return {"labels": str(out_png), "crop": [x0, y0, x1, y1]}


def _kp(raw: dict, name: str):
    p = ((raw.get("person") or {}).get("kp") or {}).get(name)
    return (np.array(p[:2], np.float64), float(p[2])) if p else (None, 0.0)


def _ok(raw, name):
    p, c = _kp(raw, name)
    return p if c >= KP_CONF else None


def _arm(lab: np.ndarray, s, e) -> dict:
    """Upper-arm width from the ATR arm labels, across the shoulder-elbow line at ARM_T."""
    L = float(np.linalg.norm(e - s))
    info = {"measured": False, "len_px": round(L, 1)}
    if L < 8:
        info["why"] = "upper arm too short in the picture"
        return info
    d = (e - s) / L
    n = np.array([-d[1], d[0]])
    arm = np.isin(lab, ATR_ARMS).astype(np.uint8)
    rec, why = [], []
    for t in ARM_T:
        m = s + t * (e - s)
        xi, yi = int(round(m[0])), int(round(m[1]))
        if not (0 <= yi < lab.shape[0] and 0 <= xi < lab.shape[1]) or lab[yi, xi] not in ATR_ARMS:
            why.append(f"{t:.2f}: not arm skin (label {int(lab[yi, xi]) if 0 <= yi < lab.shape[0] and 0 <= xi < lab.shape[1] else '-'})")
            continue
        run = _run_at(line_runs(arm, m, n, 0.9 * L))
        if run is None:
            continue
        a, b = run
        width = b - a + 1
        if width > 0.8 * L:
            why.append(f"{t:.2f}: run {width:.0f} px > 0.8 arm lengths (crossed arms?)")
            continue
        rec.append({"t": t, "width": width, "seg": _seg(m + a * n, m + b * n)})
    info["samples"] = len(rec)
    if len(rec) >= 2:
        info.update({"measured": True, "width_px": round(float(np.median([r["width"] for r in rec])), 1)})
    else:
        info["why"] = "; ".join(why) or "too few samples"
    info["segs"] = [r["seg"] for r in rec]
    return info


def body_from(raw: dict, face: dict, atr: dict) -> dict:
    out = {"usable": False, "frontal": False, "reason": None, "values": {}, "notes": [], "draw": [], "arms": {}}
    if raw.get("error"):
        out["reason"] = "YOLO failed: " + raw["error"]
        return out
    if not raw.get("person"):
        out["reason"] = "no person found"
        return out
    ls, rs, lh, rh = (_ok(raw, n) for n in ("l_shoulder", "r_shoulder", "l_hip", "r_hip"))
    lab = cv2.imread(atr["labels"], cv2.IMREAD_GRAYSCALE) if atr.get("labels") and Path(atr["labels"]).is_file() else None
    sil = cv2.imread(raw["mask"], cv2.IMREAD_GRAYSCALE) if raw.get("mask") and Path(raw["mask"]).is_file() else None
    if lab is None:
        out["notes"].append("no ATR parse: " + str(atr.get("error")))
    # head unit (eye distance / cos yaw) from this person's face: its eye midpoint inside the person's box and near the shoulders
    unit = None
    if face.get("head_unit_px") and face.get("centre"):
        fc, u = np.array(face["centre"]), face["head_unit_px"]
        bx = raw["person"]["box"]
        anchor = [p for p in (ls, rs) if p is not None]
        inside = bx[0] - 0.1 * (bx[2] - bx[0]) <= fc[0] <= bx[2] + 0.1 * (bx[2] - bx[0]) and fc[1] <= bx[3]
        if anchor and inside:
            ax_ = np.mean(anchor, axis=0)
            span = float(np.linalg.norm(ls - rs)) if ls is not None and rs is not None else 4 * u
            if float(np.linalg.norm(fc - ax_)) <= 1.2 * span + 3 * u:
                unit = u
        if unit is None:
            out["notes"].append("the face found is not this person's (not near his shoulders): head-scaled measures skipped")
    v = {}
    # arms: arm_length needs neither the face nor a frontal torso
    widths = {}
    for side in ("l", "r"):
        s, e = _ok(raw, f"{side}_shoulder"), _ok(raw, f"{side}_elbow")
        if s is None or e is None:
            out["arms"][side] = {"measured": False, "why": "shoulder or elbow not visible (confidence < 0.5)"}
            continue
        if lab is None:
            out["arms"][side] = {"measured": False, "why": "no ATR parse"}
            continue
        info = _arm(lab, s, e)
        out["draw"] += info.pop("segs", [])
        out["arms"][side] = info
        if info["measured"]:
            widths[side] = (info["width_px"], info["len_px"])
    if widths:
        v["arm_length"] = float(np.mean([w / L for w, L in widths.values()]))
        if unit:
            v["arm_iod"] = float(np.mean([w for w, _ in widths.values()])) / unit
    if ls is None or rs is None:
        out["reason"] = "a shoulder is not visible (confidence < 0.5)"
    elif lh is None or rh is None:
        out["reason"] = "a hip is not visible (confidence < 0.5)"
    else:
        sw, hw = float(np.linalg.norm(ls - rs)), float(np.linalg.norm(lh - rh))
        msh, mhp = (ls + rs) / 2, (lh + rh) / 2
        torso = float(np.linalg.norm(mhp - msh))
        tilt = abs(math.degrees(math.atan2(mhp[0] - msh[0], mhp[1] - msh[1])))
        out.update({"sw_px": round(sw, 1), "hw_px": round(hw, 1), "torso_px": round(torso, 1), "tilt": round(tilt, 1),
                    "sh_hip": round(sw / hw, 3) if hw else None, "sh_torso": round(sw / torso, 3) if torso else None})
        problems = []
        if tilt > TORSO_TILT_MAX:
            problems.append(f"torso {tilt:.0f} deg from vertical (limit {TORSO_TILT_MAX:.0f})")
        if not hw or not (SH_HIP[0] <= sw / hw <= SH_HIP[1]):
            problems.append(f"shoulder/hip width {sw / hw if hw else 0:.2f} outside {SH_HIP[0]}-{SH_HIP[1]} (torso turned or twisted)")
        if not torso or sw / torso < SH_TORSO_MIN:
            problems.append(f"shoulder width {sw / torso if torso else 0:.2f} torso lengths < {SH_TORSO_MIN} (torso side-on)")
        out["reason"] = "; ".join(problems) or None
        if not problems:
            out["frontal"] = True
            if widths:
                v["arm_shoulder"] = float(np.mean([w for w, _ in widths.values()])) / sw
            if unit:
                v["shoulder_iod"] = sw / unit
                if face.get("head_h_px"):
                    v["torso_head"] = torso / face["head_h_px"]
            if sil is not None:
                run = _run_at(line_runs(sil, msh, (rs - ls) / sw, 1.6 * sw))
                if run is not None and unit:
                    a, b = run
                    out["bideltoid_px"] = round(b - a + 1, 1)
                    v["bideltoid_iod"] = (b - a + 1) / unit
                    out["draw"].append(_seg(msh + a * (rs - ls) / sw, msh + b * (rs - ls) / sw))
            if lab is not None:
                ax = (mhp - msh) / torso
                nn = np.array([-ax[1], ax[0]])
                wpt = msh + 0.6 * (mhp - msh)
                tor = np.isin(lab, ATR_TORSO).astype(np.uint8)
                run = _run_at(line_runs(tor, wpt, nn, 1.2 * sw), tol=0.15 * sw)
                if run is None:
                    out["notes"].append("waist: no torso label on the torso axis at 60 %")
                else:
                    a, b = run
                    wpx = b - a + 1
                    out["waist_px"] = round(wpx, 1)
                    out["draw"].append(_seg(wpt + a * nn, wpt + b * nn))
                    v["waist_shoulder"] = wpx / sw
                    if unit:
                        v["waist_iod"] = wpx / unit
            le_, re_ = _ok(raw, "l_ear"), _ok(raw, "r_ear")
            if le_ is not None and re_ is not None and np.linalg.norm(le_ - re_) > 5:
                v["shoulder_ears"] = sw / float(np.linalg.norm(le_ - re_))
            out["draw"] += [_seg(ls, rs), _seg(lh, rh), _seg(msh, mhp)]
    out["usable"] = bool(v)
    if not unit:
        out["notes"].append("no head unit (no usable face of this person): only arm_length" + (", arm_shoulder, waist_shoulder" if out["frontal"] else ""))
    out["values"] = {k: round(float(x), 4) for k, x in v.items() if x is not None and math.isfinite(x)}
    return out


# ------------------------------------------------------------------------------------------------------------------------------ API


def _derive(entry: dict) -> None:
    try:
        kp = ((entry.get("body_raw") or {}).get("person") or {}).get("kp") or {}
        face = face_from({**(entry.get("face_raw") or {}), "visible": entry.get("face_vis"),
                          "wrists": {"his left wrist": kp.get("l_wrist"), "his right wrist": kp.get("r_wrist")}})
    except Exception as exc:
        face = {"usable": False, "reason": f"face measure failed: {type(exc).__name__}: {exc}", "values": {}, "notes": [], "draw": []}
    try:
        body = body_from(entry.get("body_raw") or {"error": "no YOLO reading yet"}, face, entry.get("atr") or {})
    except Exception as exc:
        body = {"usable": False, "frontal": False, "reason": f"body measure failed: {type(exc).__name__}: {exc}", "values": {}, "notes": [],
                "draw": [], "arms": {}}
    entry.update({"face": face, "body": body, "measure_version": MEASURE_VERSION})


def _unmeasured(path, why: str, sha: str | None = None) -> dict:
    sec = {"usable": False, "reason": why, "values": {}, "notes": [], "draw": []}
    return {"sha256": sha, "path": str(path), "face": dict(sec), "body": {**sec, "frontal": False, "arms": {}}}


def measure_all(paths_: list, say=print, save_every: int = 10) -> dict[str, dict]:
    """{str(path): measure} for many pictures: one YOLO subprocess for all of them, everything cached by sha256. Never raises for a
    picture: an unreadable one comes back with usable False and the reason."""
    cache = _read_cache()
    ent = cache["entries"]
    shas, out = {}, {}
    for p in paths_:
        try:
            shas[str(p)] = sha256(p)
        except OSError as exc:
            out[str(p)] = _unmeasured(p, f"cannot read the file: {exc}")
    first = {}
    for p, s in shas.items():
        first.setdefault(s, p)
    todo_face = [p for s, p in first.items() if (ent.get(s) or {}).get("face_raw_v") != FACE_RAW_VERSION]
    for i, p in enumerate(todo_face, 1):
        e = ent.setdefault(shas[p], {})
        try:
            e["face_raw"] = face_raw(load(p))
        except Exception as exc:
            e["face_raw"] = {"pose": {"detected": False, "error": f"{type(exc).__name__}: {exc}"}}
        e["face_raw_v"], e["seen_as"] = FACE_RAW_VERSION, p
        e.pop("measure_version", None)
        say(f"  [face] {i}/{len(todo_face)} {Path(p).name}")
        if i % save_every == 0:
            _write_cache(cache)
    if todo_face:
        _write_cache(cache)
    todo_body = [p for s, p in first.items() if "body_raw" not in ent[s]]
    if todo_body:
        MASKS.mkdir(parents=True, exist_ok=True)
        try:
            got = yolo_raw([Path(p) for p in todo_body], [MASKS / f"{shas[p]}.png" for p in todo_body], say)
        except Exception as exc:
            say(f"  [body] YOLO subprocess failed: {type(exc).__name__}: {exc}")
            got = {}
        for p in todo_body:
            r = got.get(str(Path(p))) or got.get(p)
            if r:                                   # a picture the subprocess never answered is retried on the next call
                ent[shas[p]]["body_raw"] = r
                ent[shas[p]].pop("measure_version", None)
        _write_cache(cache)
    def in_range(e):
        fr = e.get("face_raw") or {}
        pose = fr.get("pose") or {}
        return bool(fr.get("lm") and fr.get("box") and pose.get("detected") and abs(pose["yaw"]) <= FACE_POSE_MAX
                    and abs(pose["pitch"]) <= FACE_POSE_MAX)

    todo_vis = [p for s, p in first.items() if in_range(ent[s]) and (ent[s].get("face_vis") or {}).get("v") != FACE_VIS_VERSION]
    for i, p in enumerate(todo_vis, 1):
        e = ent[shas[p]]
        try:
            e["face_vis"] = {**face_visible(load(p), np.array(e["face_raw"]["lm"], np.float64), e["face_raw"]["box"]), "v": FACE_VIS_VERSION}
        except Exception as exc:
            e["face_vis"] = {"available": False, "why": f"{type(exc).__name__}: {exc}", "v": FACE_VIS_VERSION}
        e.pop("measure_version", None)
        say(f"  [visible] {i}/{len(todo_vis)} {Path(p).name}")
    todo_atr = [p for s, p in first.items() if "atr" not in ent[s] and "body_raw" in ent[s]]
    for i, p in enumerate(todo_atr, 1):
        e = ent[shas[p]]
        try:
            e["atr"] = atr_raw(load(p), e.get("body_raw") or {}, MASKS / f"{shas[p]}_atr.png")
        except Exception as exc:
            e["atr"] = {"error": f"{type(exc).__name__}: {exc}"}
        e.pop("measure_version", None)
        say(f"  [parse] {i}/{len(todo_atr)} {Path(p).name}")
        if i % save_every == 0:
            _write_cache(cache)
    changed = bool(todo_atr)
    for p, s in shas.items():
        e = ent[s]
        if e.get("measure_version") != MEASURE_VERSION or "body_raw" not in e:
            _derive(e)
            changed = True
        out[p] = {"sha256": s, "path": p, "face": e["face"], "body": e["body"]}
    if changed:
        _write_cache(cache)
    return out


def measure(path) -> dict:
    """{'sha256', 'path', 'face': {...}, 'body': {...}} for one picture (cached by sha256; never raises).

    face: usable, reason (why not usable), values {cjwr, fwhr, par, jaw_iod, cheek_iod, neck_face: those measurable}, yaw, pitch, roll,
          box_aspect, lm_conf, mirror_offset, lm_view, visible, emd_iod, face_px (bizygomatic px), iod_px, head_unit_px (also set when only
          the body's head unit is readable), head_h_px, lm_roll, centre, neck_rows, notes, draw (each key only when it was reached)
    body: usable, frontal, reason (why not frontal / not usable), values {shoulder_iod, bideltoid_iod, arm_iod, arm_shoulder, arm_length,
          waist_shoulder, waist_iod, torso_head, shoulder_ears: those measurable}, arms {l, r: measured, width_px, len_px, samples, why},
          sw_px, hw_px, torso_px, tilt, sh_hip, sh_torso, bideltoid_px, waist_px, notes, draw
    Only the keys in TRUSTED passed tools/character_audit.py's validation."""
    try:
        return measure_all([path], say=lambda *_: None)[str(path)]
    except Exception as exc:
        return _unmeasured(path, f"measure failed: {type(exc).__name__}: {exc}")


def raw_of(sha: str) -> dict:
    """The cached raw readings of a picture (landmarks under face_raw.lm, keypoints under body_raw.person.kp), or {}."""
    return _read_cache()["entries"].get(sha) or {}


def flat(m: dict) -> dict[str, float]:
    """{'face.cjwr': value, 'body.arm_iod': value, ...} of one measure dict."""
    out = {}
    for sec in ("face", "body"):
        for k, x in ((m.get(sec) or {}).get("values") or {}).items():
            out[f"{sec}.{k}"] = x
    return out


def band(measures: list[dict]) -> dict[str, dict]:
    """{'face': {name: {min, max, median, n}}, 'body': {...}} over the given measure dicts (usable values only)."""
    vals: dict[str, list] = {}
    for m in measures:
        for k, x in flat(m).items():
            vals.setdefault(k, []).append(x)
    out: dict[str, dict] = {"face": {}, "body": {}}
    for k, v in vals.items():
        sec, name = k.split(".", 1)
        out[sec][name] = {"min": min(v), "max": max(v), "median": float(np.median(v)), "n": len(v)}
    return out


def off_by(value: float, b: dict) -> float:
    """How far a value lies outside a band, signed, in band widths beyond the edge (0 inside). A band of one value (or of equal values)
    gets a width of 2 % of its median so the number stays finite."""
    width = max(b["max"] - b["min"], 0.02 * abs(b["median"]), 1e-9)
    if b["min"] <= value <= b["max"]:
        return 0.0
    return round((value - b["max"]) / width if value > b["max"] else (value - b["min"]) / width, 2)


def compare(measure_: dict, band_: dict) -> dict[str, dict]:
    """{'face': {name: {value, inside, off_by, trusted}}, 'body': {...}} for the usable measures that the band also has. `trusted` = the measure
    passed the audit's validation (TRUSTED); read the others as unvalidated numbers."""
    out: dict[str, dict] = {"face": {}, "body": {}}
    for k, x in flat(measure_).items():
        sec, name = k.split(".", 1)
        b = (band_.get(sec) or {}).get(name)
        if not b:
            continue
        off = off_by(x, b)
        out[sec][name] = {"value": x, "inside": off == 0.0, "off_by": off, "trusted": k in TRUSTED}
    return out


# ------------------------------------------------------------------------------------------------------------------------------ sheets

BOX_H_PER_IOD = 2.95     # SCRFD box height / interocular distance on his frontal studio photos (IMG_6858 2.97, IMG_6923 2.93)


def warp(img: np.ndarray, m: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """warpAffine with a box-filtered downscale first when the matrix shrinks the picture a lot (plain warping would alias)."""
    k = float(np.sqrt(abs(np.linalg.det(m[:, :2]))))
    if k < 0.5:
        f = 2 * k
        img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
        m = m.copy()
        m[:, :2] /= f
    return cv2.warpAffine(img, m, size, flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))


def label_tile(tile: np.ndarray, lines: list[str], chars: int = 34) -> np.ndarray:
    bar = np.full((17 * len(lines) + 6, tile.shape[1], 3), 255, np.uint8)
    for i, t in enumerate(lines):
        cv2.putText(bar, str(t)[:chars], (4, 15 + 17 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([tile, bar])


def face_tile(path, sha: str, lines: list[str], iod: float = 60.0, size: tuple[int, int] = (180, 235)) -> np.ndarray | None:
    """The face aligned on the eye centres (2dfan4) at a fixed interocular distance, or, without landmarks, its SCRFD box scaled to the
    same height a frontal face of that interocular distance has (a profile); None when no face was found."""
    fr = raw_of(sha).get("face_raw") or {}
    w, h = size
    el, er = np.array([w / 2 - iod / 2, 0.34 * h]), np.array([w / 2 + iod / 2, 0.34 * h])
    lm = fr.get("lm")
    if lm and (fr.get("lm_quality") or {}).get("usable", True):
        lm = np.array(lm, np.float64)
        le, re_ = lm[36:42].mean(axis=0), lm[42:48].mean(axis=0)
        z = complex(*(er - el)) / complex(*(re_ - le))
        a, b = z.real, z.imag
        t = el - np.array([a * le[0] - b * le[1], b * le[0] + a * le[1]])
        m = np.float32([[a, -b, t[0]], [b, a, t[1]]])
    elif fr.get("box"):
        x, y, bw, bh = fr["box"]
        s = BOX_H_PER_IOD * iod / max(1, bh)
        m = np.float32([[s, 0, w / 2 - s * (x + bw / 2)], [0, s, 0.5 * h - s * (y + bh / 2)]])
        lines = list(lines) + ["(aligned by the face box)"]
    else:
        return None
    try:
        return label_tile(warp(load(path), m, size), lines)
    except Exception:
        return None


def torso_tile(path, sha: str, lines: list[str], sw_px: float = 70.0, size: tuple[int, int] = (220, 270)) -> np.ndarray | None:
    """The upper body scaled so the shoulder keypoints are sw_px apart, shoulder midpoint at a fixed place; None without both shoulders."""
    kp = ((raw_of(sha).get("body_raw") or {}).get("person") or {}).get("kp") or {}
    ls, rs = kp.get("l_shoulder"), kp.get("r_shoulder")
    if not ls or not rs or ls[2] < KP_CONF or rs[2] < KP_CONF:
        return None
    ls, rs = np.array(ls[:2]), np.array(rs[:2])
    sw = float(np.linalg.norm(ls - rs))
    if sw < 10:
        return None
    w, h = size
    s = sw_px / sw
    msh = (ls + rs) / 2
    m = np.float32([[s, 0, w / 2 - s * msh[0]], [0, s, 0.35 * h - s * msh[1]]])
    try:
        return label_tile(warp(load(path), m, size), lines)
    except Exception:
        return None


def _has_torso(sha: str) -> bool:
    kp = ((raw_of(sha).get("body_raw") or {}).get("person") or {}).get("kp") or {}
    return all((kp.get(n) or [0, 0, 0])[2] >= KP_CONF for n in ("l_shoulder", "r_shoulder", "l_hip", "r_hip"))


def _row(tiles: list[np.ndarray], gap: int = 8) -> np.ndarray:
    h = max(t.shape[0] for t in tiles)
    padded = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, gap, cv2.BORDER_CONSTANT, value=(235, 235, 235)) for t in tiles]
    return np.hstack(padded)


def character_sheet(picture, ref_paths: list, out, ref_band: dict | None = None) -> Path | None:
    """One JPEG: row 1 = the picture's face beside each reference's face, all aligned on the eyes at the same interocular distance and crop;
    row 2 = the picture's upper body beside the references that show a torso (both shoulders and hips), all at the same shoulder width.
    Each tile is labelled with its name and the measures (trusted ones marked *; with `ref_band`, the picture's distance outside it).
    Returns None when the picture has neither a face nor shoulders to show. Never raises."""
    try:
        picture = Path(picture)
        refs = [Path(r) for r in ref_paths]
        ms = measure_all([picture] + refs, say=lambda *_: None)
        pm = ms.get(str(picture))
        if not pm or not pm.get("sha256"):
            return None
        cmp_ = compare(pm, ref_band) if ref_band else {}

        def vals(m, sec):
            v = (m.get(sec) or {}).get("values") or {}
            keys = sorted(v, key=lambda k: (f"{sec}.{k}" not in TRUSTED, k))
            out_ = []
            for k in keys[:3]:
                c = (cmp_.get(sec) or {}).get(k) if m is pm else None
                out_.append(f"{k}{'*' if f'{sec}.{k}' in TRUSTED else ''} {v[k]:.2f}" + (f" ({c['off_by']:+.1f})" if c else ""))
            return out_ or [str((m.get(sec) or {}).get("reason") or "not measured")[:34]]

        faces = [face_tile(picture, pm["sha256"], ["THIS PICTURE: " + picture.stem] + vals(pm, "face"), 64.0, (240, 300))]
        torsos = [torso_tile(picture, pm["sha256"], ["THIS PICTURE: " + picture.stem] + vals(pm, "body"), 90.0, (280, 340))]
        if faces[0] is None and torsos[0] is None:
            return None
        for r in refs:
            m = ms.get(str(r))
            if not m or not m.get("sha256"):
                continue
            if faces[0] is not None:
                faces.append(face_tile(r, m["sha256"], [r.stem] + vals(m, "face"), 64.0, (240, 300)))
            if torsos[0] is not None and _has_torso(m["sha256"]):
                torsos.append(torso_tile(r, m["sha256"], [r.stem] + vals(m, "body"), 90.0, (280, 340)))
        rows = [_row([t for t in faces if t is not None])] if faces[0] is not None else []
        if torsos[0] is not None:
            rows.append(_row([t for t in torsos if t is not None]))
        width = max(r.shape[1] for r in rows)
        sheet = np.vstack([cv2.copyMakeBorder(r, 0, 10, 0, width - r.shape[1], cv2.BORDER_CONSTANT, value=(235, 235, 235)) for r in rows])
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        ok, buf = cv2.imencode(".jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if not ok:
            return None
        P.write_bytes_atomic(out, buf.tobytes())
        return out
    except Exception:
        return None


def overlay(path, m: dict, out: Path) -> Path:
    """The picture with what was measured drawn on it: landmarks, face widths, neck, keypoints, arm, shoulder and waist runs, silhouette."""
    img = load(path)
    e = raw_of(m["sha256"])
    t = max(2, img.shape[1] // 500)
    lm = (e.get("face_raw") or {}).get("lm")
    if lm:
        for x, y in lm:
            cv2.circle(img, (int(x), int(y)), t, (0, 255, 255), -1)
    for s in m["face"].get("draw", []):
        cv2.line(img, (s[0], s[1]), (s[2], s[3]), (255, 0, 255), t)
    mp = (e.get("body_raw") or {}).get("mask")
    if mp and Path(mp).is_file():
        mk = cv2.imread(mp, cv2.IMREAD_GRAYSCALE)
        if mk is not None and mk.shape == img.shape[:2]:
            cs, _ = cv2.findContours(mk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, cs, -1, (255, 160, 0), t)
    ap = (e.get("atr") or {}).get("labels")
    if ap and Path(ap).is_file():
        lab = cv2.imread(ap, cv2.IMREAD_GRAYSCALE)
        if lab is not None and lab.shape == img.shape[:2]:
            arms = np.isin(lab, ATR_ARMS).astype(np.uint8) * 255
            cs, _ = cv2.findContours(arms, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, cs, -1, (0, 220, 120), t)
    kp = ((e.get("body_raw") or {}).get("person") or {}).get("kp") or {}
    for name, (x, y, c) in kp.items():
        if c >= KP_CONF:
            cv2.circle(img, (int(x), int(y)), 2 * t, (0, 200, 0), -1)
    for s in m["body"].get("draw", []):
        cv2.line(img, (s[0], s[1]), (s[2], s[3]), (0, 0, 255), t)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--overlay", help="folder for <stem>_character.jpg overlays")
    a = ap.parse_args()
    res = measure_all(a.images)
    for p, m in res.items():
        print(f"\n{p}")
        for sec in ("face", "body"):
            d = m[sec]
            vals = ", ".join(f"{k} {x:.3f}" for k, x in d["values"].items())
            print(f"  {sec}: {'usable' if d['usable'] else 'NOT usable: ' + str(d['reason'])}" + (f"; {vals}" if vals else ""))
            if sec == "body" and d["usable"] and d.get("reason"):
                print(f"    not frontal: {d['reason']}")
            for n in d.get("notes", []):
                print(f"    note: {n}")
        if m["body"].get("arms"):
            print("    arms: " + json.dumps(m["body"]["arms"]))
        if a.overlay:
            print("  overlay: " + str(overlay(p, m, Path(a.overlay) / (Path(p).stem + "_character.jpg"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
