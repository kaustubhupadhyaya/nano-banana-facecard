"""Face restoration wrapper using FaceFusion headless mode.

Runs face_swapper (inswapper_128) + face_enhancer (gfpgan_1.4) on CPU
with occlusion masking for sunglasses/accessories.
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
from typing import List, Optional

logger = logging.getLogger("facecard.restore")

FACEFUSION_DIR = Path(r"C:\Users\Admin\GitHub\facefusion")
FACEFUSION_PYTHON = FACEFUSION_DIR / ".venv" / "Scripts" / "python.exe"
DEFAULT_FRONTAL_REFS = [
    "IMG_6858.jpg",
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


def get_default_source_paths(config_path: str = "facecard.json") -> List[Path]:
    cfg = load_config(config_path)
    refs_dir = Path(cfg.get("refs_dir", r"C:\Users\Admin\Downloads\FaceCard_Originals"))
    ref_names = cfg.get("restore_refs", DEFAULT_FRONTAL_REFS)
    source_paths = []
    for name in ref_names:
        full_path = refs_dir / name
        if full_path.exists():
            source_paths.append(full_path)
        else:
            logger.warning("Restore reference %s not found in %s", name, refs_dir)
    if not source_paths:
        raise FileNotFoundError(f"No valid restore reference images found in {refs_dir}")
    return source_paths


def restore_face(
    target_path: str | Path,
    output_path: Optional[str | Path] = None,
    source_paths: Optional[List[str | Path]] = None,
    config_path: str = "facecard.json",
    swapper_model: str = "inswapper_128",
    pixel_boost: str = "512x512",
    enhancer_model: str = "codeformer",
    enhancer_weight: float = 0.8,
    mask_types: Optional[List[str]] = None,
    timeout: int = 180,
) -> dict:
    target = Path(target_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target image not found: {target}")

    if output_path is None:
        output = target.parent / f"{target.stem}_restored{target.suffix}"
    else:
        output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if source_paths is None:
        sources = get_default_source_paths(config_path)
    else:
        sources = [Path(s).resolve() for s in source_paths]

    if not sources:
        raise ValueError("No source images provided for face restoration.")

    if mask_types is None:
        mask_types = ["box", "occlusion"]

    if not FACEFUSION_PYTHON.exists():
        raise FileNotFoundError(f"FaceFusion Python not found at {FACEFUSION_PYTHON}")

    facefusion_py = FACEFUSION_DIR / "facefusion.py"
    if not facefusion_py.exists():
        raise FileNotFoundError(f"FaceFusion main script not found at {facefusion_py}")

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
        "face_swapper",
        "face_enhancer",
        "--face-swapper-model",
        swapper_model,
        "--face-swapper-pixel-boost",
        pixel_boost,
        "--face-enhancer-model",
        enhancer_model,
        "--face-enhancer-weight",
        str(enhancer_weight),
        "--face-mask-types",
        *mask_types,
        "--execution-providers",
        "cpu",
    ]

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
            "error": err_msg.strip(),
        }

    if not output.exists():
        return {
            "success": False,
            "target": str(target),
            "output": str(output),
            "elapsed_sec": elapsed,
            "error": "FaceFusion exited with 0 but output file was not created",
        }

    return {
        "success": True,
        "target": str(target),
        "output": str(output),
        "elapsed_sec": elapsed,
        "size_bytes": output.stat().st_size,
    }


def main():
    parser = argparse.ArgumentParser(description="Restore face using FaceFusion")
    parser.add_argument("targets", nargs="+", help="Target image path(s)")
    parser.add_argument("-o", "--output", help="Output path (for single target)")
    parser.add_argument("-s", "--sources", nargs="+", help="Source reference image path(s)")
    parser.add_argument("--config", default="facecard.json", help="Path to facecard.json")
    parser.add_argument("--swapper", default="inswapper_128", help="Face swapper model")
    parser.add_argument("--pixel-boost", default="512x512", help="Face swapper pixel boost")
    parser.add_argument("--enhancer", default="codeformer", help="Face enhancer model")
    parser.add_argument("--enhancer-weight", type=float, default=0.8, help="Face enhancer weight")
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
            pixel_boost=args.pixel_boost,
            enhancer_model=args.enhancer,
            enhancer_weight=args.enhancer_weight,
        )
        if res["success"]:
            print(f"  -> {res['output']} ({res['elapsed_sec']}s, {res['size_bytes']//1024} KB)")
        else:
            print(f"  FAILED: {res.get('error')}")


if __name__ == "__main__":
    main()
