"""Exact bytes and exact records: the foundation of consistent runs (the user, 2026-10-07: "even if the generation is faulty, it is still
consistent; each step pronounced and visible, so we can debug it later").

  * canonical_json / sha256_*      one hashing convention for everything (UTF-8, LF line endings, sorted keys, no spaces)
  * blob store                     every byte ever sent to Gemini, content-addressed outside the public repo (paths.blobs_dir(), default
                                   D:\\FacecardData\\blobs\\<sha[:2]>\\<sha256>.<ext>); written once, read-only, never deleted. A recipe pins its
                                   files by sha256, so the request it sends is byte-identical every time, whatever happens to .cache.
  * env_snapshot                   what a run ran with: argv, git commit and dirty state, package and model versions, the method-relevant
                                   facecard.json keys and the gate limits in effect
  * attach_run_log                 run.log = everything printed + gemini_webapi's own log lines (retries, preview fallbacks), secrets redacted
  * atomic_write_json              tmp file + os.replace (retried: Windows refuses a replace while another process reads the file)

Nothing here judges a picture or changes a request.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.metadata as md
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HASH_CACHE = ROOT / ".cache" / "hash_cache.json"

# ------------------------------------------------------------------------------------------------------------------------------ hashing


def canonical_json(obj) -> bytes:
    """The one serialisation that hashes are taken over: sorted keys, no spaces, UTF-8, non-ASCII kept as is."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(s: str) -> str:
    """Text hashes are over UTF-8 with LF line endings (git autocrlf rewrites files on checkout; the text, not the file, is hashed)."""
    return sha256_bytes(s.replace("\r\n", "\n").encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file_cached(path: Path) -> str:
    """sha256 of a big file (a model), cached by (path, size, mtime) in .cache/hash_cache.json, so a run does not re-hash 170 MB each time."""
    p = Path(path)
    st = p.stat()
    key = f"{p.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    cache = read_json(HASH_CACHE, {})
    if key in cache:
        return cache[key]
    digest = sha256_file(p)
    cache[key] = digest
    with contextlib.suppress(Exception):
        atomic_write_json(HASH_CACHE, cache)
    return digest


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def write_bytes_atomic(path: Path, data: bytes, retries: int = 5) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    for i in range(retries):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == retries - 1:
                raise
            time.sleep(0.3 * (i + 1))


def atomic_write_json(path: Path, data, indent: int = 1) -> None:
    write_bytes_atomic(path, json.dumps(data, indent=indent, ensure_ascii=False, default=str).encode("utf-8"))


def write_text_lf(path: Path, text: str) -> None:
    """Text whose hash is recorded is written as bytes, so Windows never turns its LF into CRLF."""
    write_bytes_atomic(path, text.replace("\r\n", "\n").encode("utf-8"))


# ------------------------------------------------------------------------------------------------------------------------------ blob store


def blobs_dir() -> Path:
    import paths
    return paths.blobs_dir()


def blob_path(sha: str, ext: str = "") -> Path | None:
    """Where the blob with this sha256 lives (any extension when `ext` is empty), or None."""
    d = blobs_dir() / sha[:2]
    if ext:
        p = d / f"{sha}{ext.lower()}"
        return p if p.is_file() else None
    hits = sorted(d.glob(f"{sha}.*")) if d.is_dir() else []
    return hits[0] if hits else None


def put_file(path: Path) -> str:
    """Copy a file into the blob store (if not there yet) and return its sha256. Written to a temp name, then renamed; made read-only."""
    path = Path(path)
    sha = sha256_file(path)
    ext = path.suffix.lower() or ".bin"
    if blob_path(sha, ext):
        return sha
    dest = blobs_dir() / sha[:2] / f"{sha}{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f"{dest.name}.{os.getpid()}.tmp")
    shutil.copyfile(path, tmp)
    if sha256_file(tmp) != sha:                      # the source changed while it was copied
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{path} changed while it was copied into the blob store")
    try:
        os.replace(tmp, dest)
    except PermissionError:                          # another process put the same blob first (it is read-only)
        tmp.unlink(missing_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(dest, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    return sha


def verify(sha: str, ext: str = "") -> bool:
    p = blob_path(sha, ext)
    return bool(p) and sha256_file(p) == sha


def stage(sha: str, dest_dir: Path, name: str) -> Path:
    """Materialise a blob as a real file `dest_dir/name` (gemini_webapi names each upload after the file it reads, so the upload name is a file
    name). The copy is verified against the sha before it is used."""
    src = blob_path(sha)
    if src is None:
        raise FileNotFoundError(f"blob {sha[:12]} is missing from {blobs_dir()}")
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    shutil.copyfile(src, dest)
    os.chmod(dest, stat.S_IREAD | stat.S_IWRITE)
    if sha256_file(dest) != sha:
        raise RuntimeError(f"staged copy of blob {sha[:12]} does not match its sha256")
    return dest


# ------------------------------------------------------------------------------------------------------------------------------ environment

PACKAGES = ["gemini_webapi", "Pillow", "opencv-python", "numpy", "onnxruntime", "curl_cffi", "loguru", "pydantic"]
METHOD_CONFIG_KEYS = ["model", "models", "subject_profiles", "pose_bins", "anchors", "face_ref_presets", "identity_threshold", "identity_thresholds",
                      "thresholds", "gates", "credit_guard", "refs"]


def _git(*args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        return out.stdout
    except Exception:
        return ""


def git_state() -> dict:
    head = _git("rev-parse", "HEAD").strip()
    dirty = [ln[3:] for ln in _git("status", "--porcelain").splitlines() if ln.strip()]
    diff = _git("diff", "HEAD")
    return {"commit": head, "branch": _git("rev-parse", "--abbrev-ref", "HEAD").strip(), "dirty_files": dirty,
            "diff_sha256": sha256_text(diff) if diff else None, "_diff": diff}


def code_label() -> str:
    g = git_state()
    return (g["commit"][:12] or "nogit") + ("+dirty" if g["dirty_files"] else "")


def package_versions() -> dict:
    out = {}
    for p in PACKAGES:
        try:
            out[p] = md.version(p)
        except Exception:
            out[p] = None
    return out


def yolo_versions() -> dict:
    """Versions inside the YOLO venv, read from its *.dist-info folder names (no subprocess, no import)."""
    import paths
    site = paths.yolo_python().parent.parent / "Lib" / "site-packages"
    out = {}
    if site.is_dir():
        for d in site.glob("*.dist-info"):
            name, _, ver = d.name[: -len(".dist-info")].partition("-")
            if name.lower() in ("ultralytics", "torch", "opencv_python", "opencv_python_headless", "numpy", "pillow", "pillow_heif"):
                out[name.lower()] = ver
    return out


def model_files() -> dict:
    import paths
    files = {
        "arcface w600k_r50": ROOT / "models" / "w600k_r50.onnx",
        "yunet": ROOT / "models" / "face_detection_yunet_2023mar.onnx",
        "yolo11m-pose": paths.yolo_models_dir() / "yolo11m-pose.pt",
        "yolo11m": paths.yolo_models_dir() / "yolo11m.pt",
    }
    return {k: (sha256_file_cached(p) if p.is_file() else None) for k, p in files.items()}


def config_shas(config: dict) -> dict:
    """sha256 of each method-relevant facecard.json key (the file also holds records that change all the time, so the whole file is not hashed)."""
    return {k: sha256_bytes(canonical_json(config.get(k))) for k in METHOD_CONFIG_KEYS if k in config}


def gate_limits() -> dict:
    """The limits in effect, read from the code that applies them: POSE_GATE (by ast from tools/pose_compare.py, which cannot be imported here),
    the light limits, and gen's identity rule."""
    import ast
    import lighting
    pose_gate = None
    try:
        tree = ast.parse((ROOT / "tools" / "pose_compare.py").read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "POSE_GATE" for t in node.targets):
                pose_gate = ast.literal_eval(node.value)
    except Exception:
        pass
    from runner import IDENTITY_RULE
    return {"pose_gate": pose_gate, "light_ratio": list(lighting.LIGHT_RATIO), "neck_ratio_tol": lighting.NECK_RATIO_TOL, "identity": IDENTITY_RULE}


def env_snapshot(config: dict, argv: list[str] | None = None) -> tuple[dict, str | None]:
    """(env, git diff text). The env dict never holds a cookie or anything derived from one."""
    import paths
    g = git_state()
    diff = g.pop("_diff")
    env = {"recorded": datetime.now().isoformat(timespec="seconds"), "argv": list(argv if argv is not None else sys.argv),
           "python": sys.version.split()[0], "platform": platform.platform(), "packages": package_versions(), "yolo_venv": yolo_versions(),
           "yolo_python": str(paths.yolo_python()), "models": model_files(), "git": g, "config_sha256": config_shas(config),
           "gate_limits": gate_limits()}
    return env, diff


def c2pa_info(path: Path) -> dict | None:
    """Google signs every Gemini picture with a C2PA manifest. Read it with c2pa-python (MIT/Apache, adopted 2026-10-07, record-only):
    'Valid' means the file's bytes are exactly what Google produced. None when c2pa-python is not installed."""
    try:
        import c2pa
    except Exception:
        return None
    try:
        with c2pa.Reader(str(path)) as r:
            js = json.loads(r.json())
        man = (js.get("manifests") or {}).get(js.get("active_manifest"), {})
        sig = man.get("signature_info") or {}
        gen = man.get("claim_generator_info") or man.get("claim_generator")
        return {"state": js.get("validation_state"), "issuer": sig.get("issuer"), "signed": sig.get("time"),
                "generator": gen[0].get("name") if isinstance(gen, list) and gen else gen,
                "problems": sorted({v.get("code") for v in js.get("validation_status") or [] if v.get("code") != "signingCredential.untrusted"})}
    except Exception as exc:
        return {"state": "no manifest or unreadable", "error": f"{type(exc).__name__}: {exc}"[:200]}


# ------------------------------------------------------------------------------------------------------------------------------ run log

SECRET_RES = [re.compile(r"g\.a000[\w\-.]+"), re.compile(r"sidts-[\w\-.]+"), re.compile(r"__Secure-[\w-]+=[^;\s]+"),
              re.compile(r"(?i)(cookie|authorization|x-goog-[\w-]+)\s*[:=]\s*[^\s,;]+")]


def redact(text: str) -> str:
    for rx in SECRET_RES:
        text = rx.sub("[redacted]", text)
    return text


class _Tee(io.TextIOBase):
    def __init__(self, stream, log):
        self.stream, self.log = stream, log

    def write(self, s):
        try:
            self.stream.write(s)
        except UnicodeEncodeError:             # cp1252 consoles
            self.stream.write(s.encode(self.stream.encoding or "utf-8", "replace").decode(self.stream.encoding or "utf-8", "replace"))
        self.log.write(redact(s))
        self.log.flush()
        return len(s)

    def flush(self):
        self.stream.flush()
        self.log.flush()

    @property
    def encoding(self):
        return getattr(self.stream, "encoding", "utf-8")


@contextlib.contextmanager
def attach_run_log(run_dir: Path):
    """Everything printed during the run, plus gemini_webapi's own DEBUG lines (its silent retries, stream recovery and full-size fallbacks),
    goes to <run_dir>/run.log. Secrets are redacted on the way."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    log = (run_dir / "run.log").open("a", encoding="utf-8")
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = _Tee(old_out, log), _Tee(old_err, log)
    sink = None
    try:
        from loguru import logger
        sink = logger.add(lambda m: (log.write(redact(str(m))), log.flush()), level="DEBUG",
                          filter=lambda r: r["extra"].get("name") == "gemini_webapi",
                          format="{time:HH:mm:ss} gemini_webapi {level}: {message}\n")
    except Exception:
        pass
    try:
        yield log
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        if sink is not None:
            with contextlib.suppress(Exception):
                from loguru import logger
                logger.remove(sink)
        log.close()
