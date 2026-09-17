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

    def embed(self, image_path: str | Path) -> np.ndarray:
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        face = self._detect(img)
        aligned = self._align(img, face)
        blob = cv2.dnn.blobFromImage(aligned, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        emb = self.session.run(None, {self.input_name: blob})[0][0]
        return emb / np.linalg.norm(emb)

    def embed_many(self, paths: list[str | Path]) -> dict[str, np.ndarray | None]:
        result = {}
        for p in paths:
            try:
                result[str(p)] = self.embed(p)
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
    valid_refs = [e for e in ref_embeddings.values() if e is not None]
    if not valid_refs:
        print("No faces detected in any reference image.")
        return
    centroid = scorer.centroid(valid_refs)

    for img_path in image_paths:
        try:
            emb = scorer.embed(img_path)
        except (NoFaceError, FileNotFoundError) as e:
            print(f"{img_path}: {e}")
            continue
        per_ref = [scorer.similarity(emb, r) for r in valid_refs]
        centroid_sim = scorer.similarity(emb, centroid)
        print(f"{img_path}")
        print(f"  max_ref_sim={max(per_ref):.3f}  mean_ref_sim={np.mean(per_ref):.3f}  centroid_sim={centroid_sim:.3f}")
