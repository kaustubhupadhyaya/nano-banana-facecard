"""Identity pool and scoring.

The pool is every photo of the user (FaceCard_Originals plus the "super favs"), each with its ArcFace embedding
and a normalized 68-landmark head shape. A candidate scores as the mean of its K most similar pool photos, not the
single best match (one lucky, easy reference decided the score before). Derived files (mirrored copies, headless
scene images) are not photos of the user and are never part of the pool.

Near-duplicates of the photo being scored (for example a downscaled copy of the source photo itself) are excluded so
an own-photo check is leave-one-out and cannot score 1.0 against itself.

Pose is compared with landmark SHAPE distance (2dfan4 landmarks, scale/position/roll removed), not with yaw angles:
the generic-3D-model yaw estimate was measured to be unreliable on real photos (a frontal photo read as +132 degrees).
Shape distance needs no angle maths and covers yaw, pitch and expression in one number.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

import landmarks
from scorer import ArcFaceScorer, NoFaceError, analyze_face

ROOT = Path(__file__).parent
POOL_CACHE = ROOT / ".cache" / "pool"
SUPER_FAVS = ROOT / ".cache" / "super_favs"
DUP_SIM = 0.95


@dataclass
class PoolEntry:
    name: str
    path: Path
    emb: np.ndarray
    shape: np.ndarray
    yaw: float
    pitch: float
    face_w: int


def _is_derived(p: Path) -> bool:
    low = p.name.lower()
    return "mirror" in low or "headless" in low or low.startswith("crop_") or low.startswith("scene_")


def _candidate_files(config: dict) -> list[Path]:
    refs_dir = Path(config.get("refs_dir", ""))
    if not refs_dir.is_dir() or not any(refs_dir.iterdir()):
        refs_dir = ROOT / config.get("cache_dir", ".cache/refs")
    files = [p for p in sorted(refs_dir.iterdir()) if p.suffix.lower() in (".jpg", ".jpeg", ".png") and not _is_derived(p)]
    if SUPER_FAVS.is_dir():
        files += [p for p in sorted(SUPER_FAVS.iterdir()) if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    return files


def _cache_key(p: Path) -> str:
    return f"v4_{p.stem}_{int(p.stat().st_mtime)}_{p.stat().st_size}"


def norm_shape(lm68: np.ndarray) -> np.ndarray:
    """Landmarks with position, scale and in-plane roll removed (roll from the nose-bridge to chin axis)."""
    x = lm68.astype(np.float64) - lm68.mean(axis=0)
    axis = lm68[8] - lm68[27]
    ang = np.arctan2(axis[0], axis[1])  # 0 when the bridge-to-chin axis is vertical
    c, s = np.cos(ang), np.sin(ang)
    x = x @ np.array([[c, -s], [s, c]]).T
    return (x / np.sqrt((x ** 2).sum(axis=1).mean())).astype(np.float32)


def shape_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Mean per-landmark distance between two normalized head shapes (0 = same pose and expression)."""
    return float(np.linalg.norm(a - b, axis=1).mean())


def measure_head(img: np.ndarray, box: tuple[int, int, int, int]) -> dict:
    """2dfan4 landmarks -> normalized shape, plus a coarse yaw/pitch (for reports only; see the module docstring)."""
    lm, q = landmarks.landmarks68_searched(img, box)
    pose = landmarks.head_pose(lm, img.shape)
    return {"lm": lm, "shape": norm_shape(lm), "yaw": pose["yaw"], "pitch": pose["pitch"], "conf": q["heatmap_conf"],
            "landmark_quality": q}


def build_pool(config: dict, scorer: ArcFaceScorer | None = None, verbose: bool = True) -> list[PoolEntry]:
    scorer = scorer or ArcFaceScorer()
    POOL_CACHE.mkdir(parents=True, exist_ok=True)
    entries: list[PoolEntry] = []
    for p in _candidate_files(config):
        key = _cache_key(p)
        meta_f, emb_f = POOL_CACHE / f"{key}.json", POOL_CACHE / f"{key}.npy"
        if meta_f.exists() and emb_f.exists():
            meta = json.loads(meta_f.read_text(encoding="utf-8"))
            if meta.get("detected"):
                entries.append(PoolEntry(p.name, p, np.load(emb_f), np.array(meta["shape"], np.float32), meta["yaw"], meta["pitch"], meta["face_w"]))
            continue
        try:
            info = analyze_face(p)
            if not info["detected"]:
                raise NoFaceError("no face")
            img = cv2.imread(str(p))
            head = measure_head(img, info["box"])
            emb = scorer.embed_head(img)
        except (NoFaceError, FileNotFoundError):
            meta_f.write_text(json.dumps({"detected": False}), encoding="utf-8")
            if verbose:
                print(f"  [pool] skip {p.name}: no face")
            continue
        meta = {"detected": True, "shape": head["shape"].tolist(), "yaw": head["yaw"], "pitch": head["pitch"], "face_w": int(info["box"][2])}
        np.save(emb_f, emb)
        meta_f.write_text(json.dumps(meta), encoding="utf-8")
        entries.append(PoolEntry(p.name, p, emb, head["shape"], head["yaw"], head["pitch"], meta["face_w"]))

    # Drop near-duplicate photos (same picture saved twice at different sizes); keep the first.
    kept: list[PoolEntry] = []
    for e in entries:
        if all(float(np.dot(e.emb, k.emb)) < 0.985 for k in kept):
            kept.append(e)
    return kept


def score_against_pool(emb: np.ndarray, pool: list[PoolEntry], k: int = 3, exclude_names: set[str] | None = None) -> dict:
    """Mean of the k highest similarities over the pool (photos in exclude_names skipped)."""
    exclude_names = exclude_names or set()
    usable = [e for e in pool if e.name not in exclude_names]
    sims = sorted(((float(np.dot(emb, e.emb)), e.name) for e in usable), reverse=True)
    top = sims[:k]
    return {"score": float(np.mean([s for s, _ in top])), "top": [(n, round(s, 3)) for s, n in top], "pool_size": len(usable)}


def nearest_by_shape(shape: np.ndarray, pool: list[PoolEntry], n: int = 4, exclude_names: set[str] | None = None) -> list[tuple[PoolEntry, float]]:
    """The n pool photos whose head shape is closest to `shape`."""
    exclude_names = exclude_names or set()
    ranked = sorted(((e, shape_distance(shape, e.shape)) for e in pool if e.name not in exclude_names), key=lambda t: t[1])
    return ranked[:n]


def duplicates_of(emb: np.ndarray, pool: list[PoolEntry]) -> set[str]:
    """Names of pool photos that are the same picture as `emb`."""
    return {e.name for e in pool if float(np.dot(emb, e.emb)) >= DUP_SIM}


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw, ih = max(0, min(ax2, bx2) - max(a[0], b[0])), max(0, min(ay2, by2) - max(a[1], b[1]))
    inter = iw * ih
    return inter / float(a[2] * a[3] + b[2] * b[3] - inter + 1e-6)


def face_near(img: np.ndarray, expect_box: tuple[int, int, int, int]) -> dict:
    """Like analyze_face, but for the face that overlaps `expect_box` most, not the largest face in the frame.

    A crop that holds the man and his reflection has two faces; picking the largest measured the wrong one on the
    stained-glass photo (face_shift 0.66 against a paste that had not moved).
    """
    from scorer import DETECTOR_PATH

    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.5)
    det.setInputSize((w, h))
    _, faces = det.detect(img)
    if faces is None or not len(faces):
        return analyze_face(img)
    boxes = [(int(max(0, r[0])), int(max(0, r[1])), int(r[2]), int(r[3])) for r in faces]
    best = max(range(len(boxes)), key=lambda i: _iou(boxes[i], tuple(int(v) for v in expect_box)))
    if _iou(boxes[best], tuple(int(v) for v in expect_box)) < 0.05:
        return analyze_face(img)
    x, y, bw, bh = boxes[best]
    m = int(max(bw, bh) * 0.6)
    sub = img[max(0, y - m):min(h, y + bh + m), max(0, x - m):min(w, x + bw + m)]
    info = analyze_face(sub)
    if info["detected"]:
        ox, oy = max(0, x - m), max(0, y - m)
        bx, by, bw2, bh2 = info["box"]
        info["box"] = (bx + ox, by + oy, bw2, bh2)
        info["landmarks"] = [[px + ox, py + oy] for px, py in info["landmarks"]]
    return info


def score_image(image: str | Path | np.ndarray, pool: list[PoolEntry], scorer: ArcFaceScorer, exclude_names: set[str] | None = None,
                k: int = 3, expect_box: tuple[int, int, int, int] | None = None) -> dict:
    """Score one image (path or BGR array) against the pool. Also returns its head shape and coarse pose.

    `expect_box` (x, y, w, h in the image) selects the face to measure when the image holds more than one.
    """
    img = image if isinstance(image, np.ndarray) else cv2.imread(str(image))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image}")
    if expect_box is not None:
        info = face_near(img, expect_box)
    else:
        tmp = ROOT / ".cache" / "_score_tmp.jpg"
        cv2.imwrite(str(tmp), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
        info = analyze_face(tmp)
    if not info["detected"]:
        return {"detected": False, "score": None}
    head = measure_head(img, info["box"])
    try:
        emb = scorer.embed_head(img, box=info["box"])
    except NoFaceError:
        return {"detected": False, "score": None, "reason": "embedder could not align the face"}
    out = score_against_pool(emb, pool, k=k, exclude_names=exclude_names)
    out.update({"detected": True, "shape": head["shape"], "yaw": head["yaw"], "pitch": head["pitch"], "pose_conf": head["conf"],
                "face_w": int(info["box"][2]), "box": info["box"], "sharpness": info["sharpness"], "emb": emb})
    return out
