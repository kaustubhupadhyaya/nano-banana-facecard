"""Face restoration wrapper with automatic angle-binned pose routing.

Analyzes the target face's yaw and orientation via YuNet landmarks, selects the
optimal angle-matched reference photos (frontal, 3/4, or full profile), and adapts
FaceFusion parameters (weight, pixel-boost, expression restoration) to deliver
flawless identity preservation across all camera angles.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("facecard.restore")

FACEFUSION_DIR = Path(r"C:\Users\Admin\GitHub\facefusion")
FACEFUSION_PYTHON = FACEFUSION_DIR / ".venv" / "Scripts" / "python.exe"

DETECTOR_PATH = Path(__file__).parent / "models" / "face_detection_yunet_2023mar.onnx"

DEFAULT_FRONTAL_REFS = [
    "IMG_6858.jpg",
    "IMG_6859.jpg",
    "IMG_6873.jpg",
    "IMG_6875.jpg",
    "IMG_6923 Copy.JPG",
]


def load_config(config_path: str = "facecard.json") -> dict:
    p = Path(config_path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def detect_pose(target_path: str | Path) -> dict:
    """Analyze face orientation using YuNet landmarks."""
    img = cv2.imread(str(target_path))
    if img is None:
        raise FileNotFoundError(f"Target image not found: {target_path}")

    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.5)
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)

    if faces is None or len(faces) == 0:
        return {
            "detected": False,
            "bin": "frontal",
            "yaw_ratio": 1.0,
            "nose_norm": 0.0,
            "direction": "Frontal",
        }

    areas = faces[:, 2] * faces[:, 3]
    f = faces[int(np.argmax(areas))]
    landmarks = f[4:14].reshape(5, 2)
    le, re, nose = landmarks[0], landmarks[1], landmarks[2]

    eye_mid = (le + re) / 2.0
    eye_dist = float(np.linalg.norm(re - le))
    nose_norm = float((nose[0] - eye_mid[0]) / (eye_dist + 1e-5))

    d_l = float(np.linalg.norm(le - nose))
    d_r = float(np.linalg.norm(re - nose))
    yaw_ratio = float(d_l / (d_r + 1e-5))

    # Angle classification
    if abs(nose_norm) < 0.12 and 0.80 <= yaw_ratio <= 1.25:
        pose_bin = "frontal"
        direction = "Frontal"
    elif nose_norm < -0.12 or yaw_ratio < 0.80:
        # Turned Left
        direction = "Left"
        if nose_norm < -0.25 or yaw_ratio < 0.65:
            pose_bin = "profile_left"
        else:
            pose_bin = "three_quarter_left"
    else:
        # Turned Right
        direction = "Right"
        if nose_norm > 0.25 or yaw_ratio > 1.45:
            pose_bin = "profile_right"
        else:
            pose_bin = "three_quarter_right"

    return {
        "detected": True,
        "bin": pose_bin,
        "yaw_ratio": round(yaw_ratio, 2),
        "nose_norm": round(nose_norm, 2),
        "direction": direction,
    }


def get_routed_source_paths(target_path: str | Path, config_path: str = "facecard.json") -> Tuple[List[Path], dict]:
    """Inspect target face angle and return the optimal reference image paths."""
    cfg = load_config(config_path)
    refs_dir = Path(cfg.get("refs_dir", r"D:\Downloads\FaceCard_Originals"))
    fallback_dir = Path(__file__).parent / cfg.get("cache_dir", ".cache/refs")

    pose_info = detect_pose(target_path)
    pose_bin = pose_info.get("bin", "frontal")
    pose_bins = cfg.get("pose_bins", {})

    target_ref_names = pose_bins.get(pose_bin, DEFAULT_FRONTAL_REFS)
    source_paths = []

    for name in target_ref_names:
        full_path = refs_dir / name
        if full_path.exists():
            source_paths.append(full_path)
        elif (fallback_dir / name).exists():
            source_paths.append(fallback_dir / name)
        else:
            logger.warning("Restore reference %s not found in %s or %s", name, refs_dir, fallback_dir)

    # Fallback to frontal if bin had no valid refs
    if not source_paths:
        for name in DEFAULT_FRONTAL_REFS:
            p = refs_dir / name
            if p.exists():
                source_paths.append(p)
            elif (fallback_dir / name).exists():
                source_paths.append(fallback_dir / name)

    return source_paths, pose_info


def restore_face(
    target_path: str | Path,
    output_path: Optional[str | Path] = None,
    source_paths: Optional[List[str | Path]] = None,
    config_path: str = "facecard.json",
    swapper_model: str = "inswapper_128",
    swapper_weight: Optional[float] = None,
    pixel_boost: str = "512x512",
    enhancer_model: Optional[str] = "none",
    enhancer_weight: float = 0.8,
    expression_factor: Optional[int] = None,
    mask_types: Optional[List[str]] = None,
    timeout: int = 240,
) -> dict:
    target = Path(target_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target image not found: {target}")

    if output_path is None:
        output = target.parent / f"{target.stem}_restored{target.suffix}"
    else:
        output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    pose_info = detect_pose(target)
    pose_bin = pose_info.get("bin", "frontal")

    if source_paths is None:
        sources, _ = get_routed_source_paths(target, config_path)
    else:
        sources = [Path(s).resolve() for s in source_paths]

    if not sources:
        raise ValueError("No source images provided for face restoration.")

    # Adaptive parameter selection based on target pose
    if swapper_weight is None:
        if "profile" in pose_bin:
            swapper_weight = 1.0  # complete profile match
        elif "three_quarter" in pose_bin:
            swapper_weight = 0.85
        else:
            swapper_weight = 0.75  # blend slightly with native generation on frontal

    if expression_factor is None:
        if "profile" in pose_bin:
            # Disable expression restorer at steep yaw to eliminate teeth smear and far-eye warping
            expression_factor = 0
        elif "three_quarter" in pose_bin:
            expression_factor = 0
        else:
            expression_factor = 80  # allow natural laugh/smile restoration on frontal

    if mask_types is None:
        mask_types = ["box", "occlusion"]

    if not FACEFUSION_PYTHON.exists():
        raise FileNotFoundError(f"FaceFusion Python not found at {FACEFUSION_PYTHON}")

    facefusion_py = FACEFUSION_DIR / "facefusion.py"
    if not facefusion_py.exists():
        raise FileNotFoundError(f"FaceFusion main script not found at {facefusion_py}")

    processors = ["face_swapper"]
    use_enhancer = enhancer_model and enhancer_model.lower() not in ("none", "off", "false", "0")
    if use_enhancer:
        processors.append("face_enhancer")
    use_expr = expression_factor and expression_factor > 0
    if use_expr:
        processors.append("expression_restorer")

    cmd = [
        str(FACEFUSION_PYTHON),
        str(facefusion_py),
        "headless-run",
        "-s",
        *[str(s) for s in sources],
        "-t",
        str(target),
        "-o",
        str(output),
        "--processors",
        *processors,
        "--face-swapper-model",
        swapper_model,
        "--face-swapper-pixel-boost",
        pixel_boost,
        "--face-swapper-weight",
        str(swapper_weight),
    ]
    if use_expr:
        cmd.extend([
            "--expression-restorer-model",
            "live_portrait",
            "--expression-restorer-factor",
            str(expression_factor),
        ])
    if use_enhancer:
        cmd.extend([
            "--face-enhancer-model",
            enhancer_model,
            "--face-enhancer-weight",
            str(enhancer_weight),
        ])
    cmd.extend([
        "--face-mask-types",
        *mask_types,
        "--execution-providers",
        "cpu",
    ])

    start_time = time.time()
    res = subprocess.run(
        cmd,
        cwd=str(FACEFUSION_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = round(time.time() - start_time, 2)

    if res.returncode != 0:
        err_msg = res.stderr or res.stdout
        logger.error("FaceFusion failed (code %d): %s", res.returncode, err_msg)
        return {
            "success": False,
            "target": str(target),
            "output": str(output),
            "elapsed_sec": elapsed,
            "pose": pose_info,
            "sources": [s.name for s in sources],
            "error": err_msg.strip(),
        }

    if not output.exists():
        return {
            "success": False,
            "target": str(target),
            "output": str(output),
            "elapsed_sec": elapsed,
            "pose": pose_info,
            "sources": [s.name for s in sources],
            "error": "FaceFusion exited with 0 but output file was not created",
        }

    return {
        "success": True,
        "target": str(target),
        "output": str(output),
        "elapsed_sec": elapsed,
        "size_bytes": output.stat().st_size,
        "pose": pose_info,
        "sources": [s.name for s in sources],
    }


def main():
    parser = argparse.ArgumentParser(description="Restore face using FaceFusion with automated angle-binned pose routing")
    parser.add_argument("targets", nargs="+", help="Target image path(s)")
    parser.add_argument("-o", "--output", help="Output path (for single target)")
    parser.add_argument("-s", "--sources", nargs="+", help="Explicit source reference image path(s)")
    parser.add_argument("--config", default="facecard.json", help="Path to facecard.json")
    parser.add_argument("--swapper", default="inswapper_128", help="Face swapper model")
    parser.add_argument("--swapper-weight", type=float, default=None, help="Face swapper blend weight (auto by pose)")
    parser.add_argument("--pixel-boost", default="512x512", help="Face swapper pixel boost (default 512x512)")
    parser.add_argument("--enhancer", default="none", help="Face enhancer model (default: none to avoid plastic smoothing)")
    parser.add_argument("--enhancer-weight", type=float, default=0.8, help="Face enhancer weight")
    parser.add_argument("--expression-factor", type=int, default=None, help="Expression restoration factor (auto by pose)")
    args = parser.parse_args()

    for target_path in args.targets:
        out_path = args.output if len(args.targets) == 1 else None
        print(f"Restoring: {target_path} ...", flush=True)
        res = restore_face(
            target_path=target_path,
            output_path=out_path,
            source_paths=args.sources,
            config_path=args.config,
            swapper_model=args.swapper,
            swapper_weight=args.swapper_weight,
            pixel_boost=args.pixel_boost,
            enhancer_model=args.enhancer,
            enhancer_weight=args.enhancer_weight,
            expression_factor=args.expression_factor,
        )
        if res["success"]:
            pose_str = f"{res['pose']['bin']} ({res['pose']['direction']}, yaw={res['pose']['yaw_ratio']})"
            print(f"  [Routed] Pose: {pose_str} -> Sources: {', '.join(res['sources'])}")
            print(f"  -> {res['output']} ({res['elapsed_sec']}s, {res['size_bytes']//1024} KB)")
        else:
            print(f"  FAILED: {res.get('error')}")


if __name__ == "__main__":
    main()
