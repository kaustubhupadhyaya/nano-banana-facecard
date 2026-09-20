"""
Objective face-identity scoring, so identity checks never rely on a human (or agent) eyeballing
a generated image and guessing. Detection: YuNet. Embedding: SFace. Both from OpenCV Zoo, run
entirely through opencv-python's built-in FaceDetectorYN/FaceRecognizerSF — no insightface build.

Score = cosine similarity between two 128-d SFace embeddings, roughly in [-1, 1]. Same-person pairs
cluster high, different-person pairs cluster low; the actual threshold is calibrated per identity
by comparing known-good vs known-bad labelled examples (see calibrate()), not assumed from a
generic "0.5 = same person" rule of thumb, since that varies by embedding model and image quality.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent
MODELS = ROOT / "models"
DETECTOR_PATH = MODELS / "face_detection_yunet_2023mar.onnx"
RECOGNIZER_PATH = MODELS / "face_recognition_sface_2021dec.onnx"
ARCFACE_PATH = MODELS / "w600k_r50.onnx"

# insightface's canonical 112x112 landmark targets (arcface_dst), order: left eye, right eye,
# nose tip, left mouth corner, right mouth corner - "left/right" as in the SUBJECT's own left/right,
# which is mirrored relative to image left/right for a front-facing photo.
_ARCFACE_DST = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
     [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32
)


class NoFaceError(RuntimeError):
    pass


def analyze_face(image_path: str | Path | np.ndarray) -> dict:
    """Analyze face geometry, yaw ratio, and sharpness to identify profiles and blurriness."""
    img = image_path if isinstance(image_path, np.ndarray) else cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.6)
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    if faces is None or len(faces) == 0:
        return {
            "detected": False,
            "box": None,
            "yaw_ratio": 1.0,
            "nose_norm": 0.0,
            "direction": "Frontal",
            "pose_bin": "frontal",
            "is_profile": False,
            "sharpness": 0.0,
        }

    areas = faces[:, 2] * faces[:, 3]
    f = faces[int(np.argmax(areas))]
    fx, fy, fw, fh = map(int, f[:4])
    fx, fy = max(0, fx), max(0, fy)
    fw, fh = min(w - fx, fw), min(h - fy, fh)

    sharpness = 0.0
    if fw > 4 and fh > 4:
        face_roi = img[fy:fy + fh, fx:fx + fw]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray_roi, cv2.CV_64F).var())

    landmarks = f[4:14].reshape(5, 2)
    le, re, nose = landmarks[0], landmarks[1], landmarks[2]

    eye_mid = (le + re) / 2.0
    eye_dist = float(np.linalg.norm(re - le))
    nose_norm = float((nose[0] - eye_mid[0]) / (eye_dist + 1e-5))

    d_l = float(np.linalg.norm(le - nose))
    d_r = float(np.linalg.norm(re - nose))
    yaw_ratio = float(d_l / (d_r + 1e-5))

    # Unified angle classification matching restore.py
    if abs(nose_norm) < 0.12 and 0.80 <= yaw_ratio <= 1.25:
        pose_bin = "frontal"
        direction = "Frontal"
        is_profile = False
    elif nose_norm < -0.12 or yaw_ratio < 0.80:
        direction = "Left"
        if nose_norm < -0.25 or yaw_ratio < 0.65:
            pose_bin = "profile_left"
            is_profile = True
        else:
            pose_bin = "three_quarter_left"
            is_profile = False
    else:
        direction = "Right"
        if nose_norm > 0.25 or yaw_ratio > 1.45:
            pose_bin = "profile_right"
            is_profile = True
        else:
            pose_bin = "three_quarter_right"
            is_profile = False

    return {
        "detected": True,
        "box": (fx, fy, fw, fh),
        "landmarks": landmarks.tolist(),
        "yaw_ratio": round(yaw_ratio, 2),
        "nose_norm": round(nose_norm, 2),
        "direction": direction,
        "pose_bin": pose_bin,
        "is_profile": is_profile,
        "sharpness": round(sharpness, 1),
    }


class ArcFaceScorer:
    """Independent embedder/scorer, used only as a fallback when SFace fails calibration."""

    def __init__(self):
        import onnxruntime as ort

        if not DETECTOR_PATH.is_file() or not ARCFACE_PATH.is_file():
            raise FileNotFoundError(f"Face models missing in {MODELS}.")
        self.detector = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (320, 320), score_threshold=0.7)
        self.session = ort.InferenceSession(str(ARCFACE_PATH), providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def _detect(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        if faces is None or len(faces) == 0:
            raise NoFaceError("No face detected")
        areas = faces[:, 2] * faces[:, 3]
        return faces[int(np.argmax(areas))]

    def _align(self, img: np.ndarray, face_row: np.ndarray) -> np.ndarray:
        # YuNet's 5 landmark points map directly to _ARCFACE_DST in the same order - both are
        # IMAGE-relative (left = left side of the image/crop), not subject-relative. Verified
        # empirically: this direct mapping produces an upright, undistorted 112x112 crop; the
        # subject-relative eye/mouth swap tried earlier produced a visibly skewed crop.
        src = face_row[4:14].reshape(5, 2).astype(np.float32)
        transform, _ = cv2.estimateAffinePartial2D(src, _ARCFACE_DST, method=cv2.LMEDS)
        if transform is None:
            raise NoFaceError("Could not estimate alignment transform")
        return cv2.warpAffine(img, transform, (112, 112), borderValue=0.0)

    def _embed_aligned(self, aligned: np.ndarray) -> np.ndarray:
        blob = cv2.dnn.blobFromImage(aligned, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        emb = self.session.run(None, {self.input_name: blob})[0][0]
        return emb / np.linalg.norm(emb)

    def embed_array(self, img: np.ndarray) -> np.ndarray:
        """Embedding with YuNet 5-point alignment (unreliable beyond ~30 degrees of yaw)."""
        return self._embed_aligned(self._align(img, self._detect(img)))

    def embed_array_fan(self, img: np.ndarray, box: tuple[int, int, int, int] | None = None) -> np.ndarray:
        """Embedding with 2dfan4 68-landmark alignment (built for large poses). `box` skips detection when known."""
        import landmarks

        box = tuple(int(v) for v in box) if box is not None else tuple(int(v) for v in self._detect(img)[:4])
        # searched, not plain: a failed landmark fit produces a skewed 112x112 crop and therefore a meaningless embedding
        lm, _ = landmarks.landmarks68_searched(img, box)
        return self._embed_aligned(landmarks.align_arcface(img, lm))

    def embed(self, image_path: str | Path) -> np.ndarray:
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        return self.embed_array(img)

    def embed_head(self, image: str | Path | np.ndarray, min_face: int = 320, align: str = "fan",
                   box: tuple[int, int, int, int] | None = None) -> np.ndarray:
        """Embed the largest face from a tight head crop upscaled so the face is at least `min_face` px wide.

        Full-body frames leave faces ~50 px wide, which the aligner and embedder handle poorly. Cropping first and
        upscaling gives the detector and the 112x112 alignment warp a stable input. align="fan" uses 2dfan4
        landmarks and falls back to YuNet if they cannot be computed.
        """
        img = cv2.imread(str(image)) if not isinstance(image, np.ndarray) else image
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image}")
        fx, fy, fw, fh = map(int, box) if box is not None else map(int, self._detect(img)[:4])
        fs = max(fw, fh)
        side = int(fs * 2.4)
        cx, cy = fx + fw // 2, fy + fh // 2
        m = np.float32([[1, 0, -(cx - side // 2)], [0, 1, -(cy - side // 2)]])
        crop = cv2.warpAffine(img, m, (side, side), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        k = 1.0
        if fs < min_face:
            k = min_face / fs
            crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_LANCZOS4)
        box_in_crop = (int((side - fw) / 2 * k), int((side - fh) / 2 * k), int(fw * k), int(fh * k)) if box is not None else None
        try:
            return self.embed_array_fan(crop, box_in_crop) if align == "fan" else self.embed_array(crop)
        except (NoFaceError, ValueError, FileNotFoundError):
            return self.embed_array(img)  # raises NoFaceError when the stricter embedder-side detector finds nothing

    def embed_many(self, paths: list[str | Path]) -> dict[str, np.ndarray | None]:
        cache_dir = Path(__file__).parent / ".cache" / "embeddings"
        cache_dir.mkdir(parents=True, exist_ok=True)
        result = {}
        for p in paths:
            p_obj = Path(p)
            mtime = int(p_obj.stat().st_mtime) if p_obj.exists() else 0
            cached_file = cache_dir / f"{p_obj.stem}_{mtime}.npy"
            if cached_file.exists():
                try:
                    result[str(p)] = np.load(str(cached_file))
                    continue
                except Exception:
                    pass
            try:
                emb = self.embed(p)
                result[str(p)] = emb
                if emb is not None:
                    np.save(str(cached_file), emb)
            except (NoFaceError, FileNotFoundError) as e:
                print(f"  [skip] {p}: {e}")
                result[str(p)] = None
        return result

    @staticmethod
    def similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a.flatten(), b.flatten()))

    @staticmethod
    def centroid(embeddings: list[np.ndarray]) -> np.ndarray:
        stacked = np.stack([e.flatten() for e in embeddings])
        mean = stacked.mean(axis=0, keepdims=True)
        return (mean / np.linalg.norm(mean)).astype(np.float32)


class FaceScorer:
    def __init__(self):
        if not DETECTOR_PATH.is_file() or not RECOGNIZER_PATH.is_file():
            raise FileNotFoundError(f"Face models missing in {MODELS}. See README for download step.")
        self.detector = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (320, 320), score_threshold=0.7)
        self.recognizer = cv2.FaceRecognizerSF.create(str(RECOGNIZER_PATH), "")

    def _largest_face(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        if faces is None or len(faces) == 0:
            raise NoFaceError("No face detected")
        # faces columns: x,y,w,h,5 landmark pairs...,score. Pick the largest box (main subject).
        areas = faces[:, 2] * faces[:, 3]
        return faces[int(np.argmax(areas))]

    def embed(self, image_path: str | Path) -> np.ndarray:
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        face = self._largest_face(img)
        aligned = self.recognizer.alignCrop(img, face)
        return self.recognizer.feature(aligned)

    def similarity(self, emb_a: np.ndarray, emb_b: np.ndarray) -> float:
        return float(self.recognizer.match(emb_a, emb_b, cv2.FaceRecognizerSF_FR_COSINE))

    def embed_many(self, paths: list[str | Path]) -> dict[str, np.ndarray | None]:
        result = {}
        for p in paths:
            try:
                result[str(p)] = self.embed(p)
            except (NoFaceError, FileNotFoundError) as e:
                print(f"  [skip] {p}: {e}")
                result[str(p)] = None
        return result

    def centroid(self, embeddings: list[np.ndarray]) -> np.ndarray:
        stacked = np.stack([e.flatten() for e in embeddings])
        mean = stacked.mean(axis=0, keepdims=True)
        return (mean / np.linalg.norm(mean)).astype(np.float32)


def refs_matrix(ref_paths: list[Path]) -> None:
    scorer = FaceScorer()
    embeddings = scorer.embed_many(ref_paths)
    valid = [(p, e) for p, e in embeddings.items() if e is not None]
    if len(valid) < 2:
        print("Not enough faces detected among refs to build a matrix.")
        return

    names = [Path(p).name for p, _ in valid]
    width = max(len(n) for n in names) + 1
    print(" " * width + " ".join(f"{n[:10]:>10}" for n in names))
    for i, (_, ei) in enumerate(valid):
        row = []
        for _, ej in valid:
            row.append(f"{scorer.similarity(ei, ej):>10.3f}")
        print(f"{names[i]:<{width}}" + " ".join(row))

    print("\nPer-ref average similarity to all other refs (low = possible outlier):")
    for i, (p, ei) in enumerate(valid):
        others = [ej for j, (_, ej) in enumerate(valid) if j != i]
        avg = float(np.mean([scorer.similarity(ei, ej) for ej in others]))
        print(f"  {Path(p).name:<{width}} avg={avg:.3f}")


def score_images(image_paths: list[Path], ref_paths: list[Path]) -> None:
    scorer = ArcFaceScorer()
    ref_embeddings = scorer.embed_many(ref_paths)
    valid_refs = [(p, e) for p, e in ref_embeddings.items() if e is not None]
    if not valid_refs:
        print("No faces detected in any reference image.")
        return
    centroid = scorer.centroid([e for _, e in valid_refs])

    for img_path in image_paths:
        try:
            emb = scorer.embed(img_path)
            info = analyze_face(img_path)
        except (NoFaceError, FileNotFoundError) as e:
            print(f"{img_path}: {e}")
            continue

        per_ref = [(Path(p).name, scorer.similarity(emb, e)) for p, e in valid_refs]
        per_ref.sort(key=lambda x: x[1], reverse=True)
        max_sim = per_ref[0][1]
        mean_sim = float(np.mean([s for _, s in per_ref]))
        centroid_sim = scorer.similarity(emb, centroid)

        profile_tag = "PROFILE" if info.get("is_profile") else "FRONTAL/3/4"
        yaw_r = info.get("yaw_ratio", 1.0)
        norm_val = info.get("nose_norm", 0.0)
        p_bin = info.get("pose_bin", "frontal")
        direction = info.get("direction", "Frontal")
        sharp = info.get("sharpness", 0.0)

        print(f"{img_path.name}:")
        print(f"  Pose: {p_bin} ({direction}, yaw={yaw_r:.2f}, norm={norm_val:+.2f}) | Sharpness: {sharp:.1f} | [{profile_tag}]")
        print(f"  max_ref_sim={max_sim:.3f} (top: {per_ref[0][0]}) | mean={mean_sim:.3f} | centroid={centroid_sim:.3f}")
        if len(per_ref) > 1:
            top_3 = ", ".join(f"{name}:{sim:.3f}" for name, sim in per_ref[:3])
            print(f"  top matches: {top_3}")
