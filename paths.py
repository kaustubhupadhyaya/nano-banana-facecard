"""Every location outside this repo, resolved in one place.

Each path resolves in this order: environment variable, then facecard.json, then a default.
Defaults are relative to this repo or to the home folder, not fixed drive paths, so the same
checkout works on another machine or under another username.

Keep external paths here and nowhere else. A moved folder should be a one-line change.

Run `python paths.py` (or `facecard.py check`) to see what resolved and what is missing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
CONFIG_FILE = REPO / "facecard.json"

FACEFUSION_REPO_URL = "https://github.com/facefusion/facefusion.git"

# Models restore.py drives. FaceFusion downloads any that are missing on first use,
# which is roughly 2.5 GB for the full set, so report them instead of fetching silently.
FACEFUSION_MODELS = [
    "inswapper_128.onnx",         # face_swapper, always on
    "live_portrait_generator.onnx",  # expression_restorer, frontal poses
]


def _config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _resolve(env_var: str, config_key: str, default: Path) -> Path:
    value = os.environ.get(env_var)
    if value:
        return Path(value)
    value = _config().get(config_key)
    if value:
        return Path(value)
    return default


def facefusion_dir() -> Path:
    """Local clone of upstream FaceFusion. Defaults to a sibling of this repo."""
    return _resolve("FACEFUSION_DIR", "facefusion_dir", REPO.parent / "facefusion")


def facefusion_python() -> Path:
    """FaceFusion's own interpreter. It needs Python 3.12, separate from this repo's venv."""
    return facefusion_dir() / ".venv" / "Scripts" / "python.exe"


def refs_dir() -> Path:
    """Folder of the user's reference photos."""
    return _resolve("FACECARD_REFS_DIR", "refs_dir", Path(r"D:\Downloads\FaceCard_Originals"))


def results_dir() -> Path:
    """Where tools/export_results.py (the end hook of the gemini-identity-gen skill) copies every generated picture, named and versioned for people."""
    return _resolve("FACECARD_RESULTS_DIR", "results_dir", Path(r"D:\FacecardResults"))


def vault_dir() -> Path:
    """The secure-vault skill, which holds vault.py. Defaults to the user's home folder."""
    return _resolve("SECURE_VAULT_DIR", "vault_dir", Path.home() / ".agents" / "skills" / "secure-vault")


def blobs_dir() -> Path:
    """The content-addressed store of every byte a recipe sends (provenance.py). Outside the repo on purpose: the repo is public, and a
    `git clean` must never be able to take the method's inputs with it."""
    return _resolve("FACECARD_BLOBS_DIR", "blobs_dir", Path(r"D:\FacecardData\blobs"))


def review_dir() -> Path:
    """Where every run's self-contained report.html is published, one flat folder (the user, 2026-10-06: the review images must be easy to find)."""
    return _resolve("FACECARD_REVIEW_DIR", "review_dir", Path(r"D:\FacecardReview"))


def yolo_python() -> Path:
    """The YOLO environment's interpreter (torch + ultralytics) that runs tools/pose_compare.py, the pose gate."""
    return _resolve("FACECARD_YOLO_PYTHON", "yolo_python", Path(r"D:\VisionModels\yolo\.venv\Scripts\python.exe"))


def yolo_models_dir() -> Path:
    """Folder of yolo11m-pose.pt and yolo11m.pt (read by tools/pose_compare.py)."""
    return _resolve("FACECARD_YOLO_MODELS", "yolo_models_dir", Path(r"D:\VisionModels\yolo"))


# ---- the local overnight system (local_gen.py, tools/overnight.py; 2026-10-09). Separate from the Gemini pipeline: nothing above uses these.
def sdcpp_dir() -> Path:
    """stable-diffusion.cpp builds (sd-cli.exe), one folder per release. Outside the repo: an external MIT program, never vendored."""
    return _resolve("FACECARD_SDCPP_DIR", "sdcpp_dir", Path(r"C:\LocalGen\sd.cpp"))


def localgen_models_dir() -> Path:
    """Qwen-Image-2.1 model files for the local system (on the NVMe: stable-diffusion.cpp reads weights from disk when RAM runs short)."""
    return _resolve("FACECARD_LOCALGEN_MODELS", "localgen_models_dir", Path(r"C:\LocalGen\models\qwen-image-2.1"))


def local_dir() -> Path:
    """The local system's runs, queue, state, logs and morning summaries (never under outputs/, which the Gemini tools scan)."""
    return _resolve("FACECARD_LOCAL_DIR", "local_dir", Path(r"D:\FacecardLocal"))


def room_dir() -> Path:
    """tools/room.py's record of what the night closed and how it comes back. On the NVMe, not D: (a USB disk): putting things back must
    never depend on a disk that can go away."""
    return _resolve("FACECARD_ROOM_DIR", "room_dir", Path(r"C:\LocalGen\room"))


def _python_version(exe: Path) -> str | None:
    try:
        out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr).strip().replace("Python ", "")
    except Exception:
        return None


def report() -> int:
    """Print what resolved and what is missing. Returns 0 when everything required is present."""
    problems = 0

    def line(ok: bool, label: str, detail: str) -> None:
        print(f"  [{'ok' if ok else 'MISSING'}] {label}: {detail}")

    print("External paths:")

    ff = facefusion_dir()
    ff_ok = (ff / "facefusion.py").exists()
    line(ff_ok, "FaceFusion clone", str(ff))
    if not ff_ok:
        problems += 1
        print(f"      Clone it:  git clone --depth 1 {FACEFUSION_REPO_URL} \"{ff}\"")
        print("      Or point elsewhere with the FACEFUSION_DIR env var or a facefusion_dir key in facecard.json.")

    py = facefusion_python()
    version = _python_version(py) if py.exists() else None
    py_ok = version is not None and version.startswith("3.12")
    line(py_ok, "FaceFusion Python", f"{py} ({version or 'not found'})")
    if not py_ok:
        problems += 1
        if version is None:
            print(f"      Create it:  py -3.12 -m venv \"{ff / '.venv'}\", then run FaceFusion's install.py with it.")
        else:
            print(f"      FaceFusion needs Python 3.12, found {version}.")

    models_dir = ff / ".assets" / "models"
    for name in FACEFUSION_MODELS:
        present = (models_dir / name).exists()
        # Missing models are not fatal: FaceFusion downloads them on first run.
        line(present, "model", f"{name}" + ("" if present else "  (FaceFusion will download it on first run)"))

    refs = refs_dir()
    count = len([p for p in refs.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")]) if refs.exists() else 0
    refs_ok = count > 0
    line(refs_ok, "Reference photos", f"{refs} ({count} images)")
    if not refs_ok:
        problems += 1
        print("      Set refs_dir in facecard.json or the FACECARD_REFS_DIR env var.")

    vault = vault_dir()
    vault_ok = (vault / "vault.py").exists()
    line(vault_ok, "secure-vault", str(vault))
    if not vault_ok:
        problems += 1
        print("      Set the SECURE_VAULT_DIR env var or a vault_dir key in facecard.json.")

    yp = yolo_python()
    yp_ok = yp.exists() and (yolo_models_dir() / "yolo11m-pose.pt").exists()
    line(yp_ok, "YOLO pose gate", f"{yp} + {yolo_models_dir() / 'yolo11m-pose.pt'}")
    if not yp_ok:
        problems += 1
        print("      The pose gate cannot run without it: set FACECARD_YOLO_PYTHON / FACECARD_YOLO_MODELS or yolo_python / yolo_models_dir in facecard.json.")

    blobs = blobs_dir()
    n_blobs = sum(1 for _ in blobs.rglob("*") if _.is_file()) if blobs.exists() else 0
    line(blobs.parent.exists(), "Blob store (exact bytes of every recipe)", f"{blobs} ({n_blobs} files)")
    line(True, "Review reports", str(review_dir()))
    line(True, "Results (passed pictures only)", str(results_dir()))

    print("Ready." if problems == 0 else f"{problems} required item(s) missing.")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(report())
