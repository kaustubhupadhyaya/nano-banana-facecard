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


def vault_dir() -> Path:
    """The secure-vault skill, which holds vault.py. Defaults to the user's home folder."""
    return _resolve("SECURE_VAULT_DIR", "vault_dir", Path.home() / ".agents" / "skills" / "secure-vault")


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

    print("Ready." if problems == 0 else f"{problems} required item(s) missing.")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(report())
