"""Vendored verbatim from https://github.com/yakhyo/head-pose-estimation (MIT, Copyright (c) 2024 Yakhyokhuja Valikhujaev), commit 0aad20b23a48526605d4e185de0d45ab05914ba2.
onnx_inference.py: the class HeadPoseONNX and the function expand_bbox, unchanged; the file's demo code and its demo-only imports
(models.scrfd as a package import, utils.general drawing helpers) are not copied. Licence: LICENSE in this folder."""
from typing import List, Tuple

import cv2
import numpy as np
import onnxruntime as ort


class HeadPoseONNX:
    """Head pose estimation using ONNXRuntime.

    The ONNX model outputs a (B, 3, 3) rotation matrix (ortho6D decoded inside the graph).
    This class converts the rotation matrix to Euler angles (pitch, yaw, roll) in degrees.
    """

    def __init__(self, model_path: str, session: ort.InferenceSession | None = None) -> None:
        self.session = session
        if self.session is None:
            assert model_path is not None, "Model path is required for the first time initialization."
            self.session = ort.InferenceSession(
                model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )

        self.input_mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.input_std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        input_cfg = self.session.get_inputs()[0]
        self.input_name = input_cfg.name
        self.input_size = tuple(input_cfg.shape[2:][::-1])  # (W, H)

        outputs = self.session.get_outputs()
        self.output_names = [o.name for o in outputs]

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, self.input_size)
        image = image.astype(np.float32) / 255.0
        image = (image - self.input_mean) / self.input_std
        image = np.transpose(image, (2, 0, 1))  # HWC -> CHW
        return np.expand_dims(image, axis=0).astype(np.float32)  # CHW -> BCHW

    @staticmethod
    def rotation_matrix_to_euler(rotation_matrix: np.ndarray) -> np.ndarray:
        """Convert (B, 3, 3) rotation matrices to Euler angles (pitch, yaw, roll) in degrees."""
        R = rotation_matrix
        sy = np.sqrt(R[:, 0, 0] ** 2 + R[:, 1, 0] ** 2)
        singular = sy < 1e-6

        x = np.where(singular, np.arctan2(-R[:, 1, 2], R[:, 1, 1]), np.arctan2(R[:, 2, 1], R[:, 2, 2]))
        y = np.arctan2(-R[:, 2, 0], sy)
        z = np.where(singular, np.zeros_like(sy), np.arctan2(R[:, 1, 0], R[:, 0, 0]))

        return np.degrees(np.stack([x, y, z], axis=1))  # (B, 3) — pitch, yaw, roll

    def estimate(self, face_image: np.ndarray) -> Tuple[float, float, float]:
        """Estimate head pose from a face crop.

        Returns:
            (pitch, yaw, roll) in degrees.
        """
        input_tensor = self.preprocess(face_image)
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        rotation_matrix = outputs[0]  # (1, 3, 3)
        euler = self.rotation_matrix_to_euler(rotation_matrix)  # (1, 3)
        return float(euler[0, 0]), float(euler[0, 1]), float(euler[0, 2])


def expand_bbox(x_min: int, y_min: int, x_max: int, y_max: int, factor: float = 0.2) -> List[int]:
    """Expand the bounding box by a given factor."""
    width = x_max - x_min
    height = y_max - y_min

    x_min_new = x_min - int(factor * height)
    y_min_new = y_min - int(factor * width)
    x_max_new = x_max + int(factor * height)
    y_max_new = y_max + int(factor * width)

    return [max(0, x_min_new), max(0, y_min_new), x_max_new, y_max_new]
