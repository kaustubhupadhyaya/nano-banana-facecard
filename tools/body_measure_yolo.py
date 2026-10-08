"""Raw body readings for character.py, run inside the YOLO environment (torch + ultralytics; the repo .venv has neither).

For each picture: the largest person's 17 keypoints (yolo11m-pose) and that person's silhouette mask (yolo11m-seg, the mask whose box overlaps
the pose box most), written as a full-size PNG. One JSON line per picture on stdout, prefixed "CHAR_JSON ", so character.py can read it past
any library chatter. Nothing is decided here; character.py turns these readings into measures and decides what is usable.

    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\body_measure_yolo.py <jobs.json>
        jobs.json = [{"path": "<image>", "mask": "<png to write>"}, ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass
KP = ["nose", "l_eye", "r_eye", "l_ear", "r_ear", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist",
      "l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle"]
_models: dict = {}


def model(models_dir: Path, name: str):
    from ultralytics import YOLO
    if name not in _models:
        _models[name] = YOLO(str(models_dir / name))
    return _models[name]


def load(p: Path) -> np.ndarray:
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def iou(a, b) -> float:
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    return inter / max(1e-6, (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)


def read(img: np.ndarray, models_dir: Path, mask_out: Path) -> dict:
    H, W = img.shape[:2]
    out = {"wh": [W, H], "person": None, "mask": None, "mask_iou": None, "persons": 0}
    r = model(models_dir, "yolo11m-pose.pt").predict(img, imgsz=1024, conf=0.25, verbose=False)[0]
    if r.boxes is None or not len(r.boxes):
        return out
    boxes = r.boxes.xyxy.cpu().numpy()
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    i = int(np.argmax(areas))
    k = r.keypoints.data[i].cpu().numpy()
    box = [float(v) for v in boxes[i]]
    out["persons"] = int(len(boxes))
    out["person"] = {"box": box, "kp": {KP[j]: [float(k[j][0]), float(k[j][1]), float(k[j][2])] for j in range(17)}}
    s = model(models_dir, "yolo11m-seg.pt").predict(img, imgsz=1024, conf=0.25, classes=[0], retina_masks=True, verbose=False)[0]
    if s.masks is None or s.boxes is None or not len(s.boxes):
        return out
    sb = s.boxes.xyxy.cpu().numpy()
    best = max(range(len(sb)), key=lambda j: iou(box, sb[j]))
    out["mask_iou"] = round(float(iou(box, sb[best])), 3)
    m = (s.masks.data[best].cpu().numpy() > 0.5).astype(np.uint8) * 255
    if m.shape != (H, W):
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST)
    mask_out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(mask_out), m)
    out["mask"] = str(mask_out)
    return out


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    jobs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    models_dir = Path(jobs[0].get("models_dir")) if jobs and jobs[0].get("models_dir") else Path(r"D:\VisionModels\yolo")
    for job in jobs:
        try:
            res = read(load(Path(job["path"])), models_dir, Path(job["mask"]))
        except Exception as exc:
            res = {"error": f"{type(exc).__name__}: {exc}"}
        res["path"] = job["path"]
        print("CHAR_JSON " + json.dumps(res), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
