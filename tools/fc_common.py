"""Shared helpers for the facecard-session tools: paths, run folders, the picture of a run, reviewed runs, facecard.json read/write."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
FEEDBACK = ROOT / ".cache" / "feedback"
CONFIG = ROOT / "facecard.json"
BEST_DIR = Path(r"D:\Downloads\AI me")                      # the user's best versions
SESSION_MARK = ROOT / ".cache" / "session_start.json"
REVIEW_QUEUE = ROOT / ".cache" / "review_queue.json"
RUN_RE = re.compile(r"^\d{8}_\d{6}_")
PICTURES = ("best.jpg", "best.png", "not_passing_closest.jpg", "v1_0.jpg", "v1_0_restored.jpg")
METADATA = ("run.json", "run.log")
RUN_REF_RE = re.compile(r"(\d{8}_\d{6}_[^/\\`|\"'\n]+?)[/\\]([\w.\-]+\.(?:jpg|jpeg|png))", re.I)
TAGS = ("hair", "light", "size", "angle", "expression", "pasted", "blur", "glasses", "clothes")


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    """Same format as the repo keeps it: indent 2, UTF-8, CRLF on Windows."""
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def md5(p: Path) -> str:
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def run_dirs(*roots: Path) -> list[Path]:
    out = []
    for r in roots or (OUTPUTS, FEEDBACK):
        if r.is_dir():
            out += [d for d in sorted(r.iterdir()) if d.is_dir() and RUN_RE.match(d.name)]
    return out


def picture_of(run_dir: Path) -> Path | None:
    for n in PICTURES:
        if (run_dir / n).exists():
            return run_dir / n
    return None


def referenced_files() -> set[tuple[str, str]]:
    """(run folder, file) pairs the user reviewed or the records point to: facecard.json (approved_outputs, reviews, best_versions), FEEDBACK_LOG.md
    and the workbook's curated rows. Files named there are never pruned."""
    refs: set[tuple[str, str]] = set()
    texts = [CONFIG.read_text(encoding="utf-8")]
    log = ROOT / "FEEDBACK_LOG.md"
    if log.exists():
        texts.append(log.read_text(encoding="utf-8", errors="replace"))
    for m in (ROOT / "research" / "feedback_matrix").glob("fm_rows*.py"):
        texts.append(m.read_text(encoding="utf-8", errors="replace"))
    for t in texts:
        for run, f in RUN_REF_RE.findall(t):
            refs.add((run.strip(), f))
    # curated workbook rows name the run and the file separately: run="...", file="..."
    for m in (ROOT / "research" / "feedback_matrix").glob("fm_rows*.py"):
        t = m.read_text(encoding="utf-8", errors="replace")
        for run, f in re.findall(r'run="(\d{8}_\d{6}_[^"]+)",\s*file="([^"]+)"', t):
            refs.add((run, f))
    # best versions name the run and the attempt
    for v in (load_config().get("best_versions") or {}).values():
        if isinstance(v, dict) and v.get("run"):
            which = str(v.get("which", ""))
            m = re.search(r"attempt (\d+)", which)
            refs.add((v["run"], f"cand{m.group(1)}.png" if m else which))
    return refs


def reviewed_runs() -> set[str]:
    """Run folders the user has given a verdict on (any file in them)."""
    cfg = load_config()
    runs: set[str] = set()
    for group in (cfg.get("approved_outputs") or {}).values():
        if isinstance(group, dict):
            for k in group:
                m = RUN_REF_RE.match(k)
                if m:
                    runs.add(m.group(1))
    for k in (cfg.get("reviews") or {}):
        runs.add(k.split("/")[0])
    for v in (cfg.get("best_versions") or {}).values():
        if isinstance(v, dict) and v.get("run"):
            runs.add(v["run"])
    return runs


def attempt_table(run_dir: Path) -> list[dict]:
    j = json.loads((run_dir / "run.json").read_text(encoding="utf-8")) if (run_dir / "run.json").exists() else {}
    rows = []
    for c in j.get("candidates", []):
        m = c.get("metrics") or {}
        judge = c.get("judge") or {}
        flags = [k for k, want in (("same_head_angle", True), ("same_expression", True), ("glasses_preserved", True), ("lighting_consistent", True),
                                   ("double_image", False), ("seam_visible", False), ("anything_else_changed", False), ("reflection_matches", True))
                 if judge.get(k) is not None and bool(judge[k]) != want]
        rows.append({"attempt": c.get("index"), "verdict": c.get("verdict") or ("no picture" if "score" not in m else ""),
                     "identity": m.get("score"), "source_identity": m.get("source_score"), "gt_sim": m.get("gt_sim"), "size": m.get("size_ratio"),
                     "shift": m.get("face_shift_frac"), "light_dE": (m.get("light") or {}).get("dE"), "neck": m.get("neck_gap"),
                     "sharp": m.get("sharp_ratio"), "ssim": (m.get("drift") or {}).get("ssim"), "judge": ",".join(flags) or ("clear" if judge else "-"),
                     "placement_of": c.get("placement_of_attempt"), "problems": c.get("problems", [])})
    return rows
