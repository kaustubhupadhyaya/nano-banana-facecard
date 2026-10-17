"""How many generation passes made a picture (the retrospective of 2026-10-17, RETROSPECTIVE_2026-10-17.md).

    depth 0  a real photo, a pin or any other goal picture
    depth 1  one whole render made from it
    depth 2  that render plus one edit pass on it (a region edit, or a render that used it as the photo to edit)
    ...      every further edit on an edit adds one

Every picture of the user's best set (D:\\Downloads\\AI me) has depth 2 or less: one whole render, at most one small fix (Pin_Best: the engine;
the pizza: the beard; surf: the marks). The pictures that went downhill were chains: pin 14's Gokarna picture was the sixth edit stacked on one
render, and the eye fixes of pin 16 were edits of surf.jpg itself. So `facecard.py run` refuses a recipe whose output would have depth 3 or more
(MAX_DEPTH) unless the user asked for that exact edit (environment variable FACECARD_DEEP_EDIT_OK holding their words, set by wave.py from a job's
"deep_edit_ok").

Code copies (background restore `r`, `_strip`, `_seam`, `_nostar` repairs) stay inside their run and add nothing; a head pasted in by a scratch
script cannot be seen here, which is why AGENTS.md forbids it.

    .venv\\Scripts\\python.exe tools\\edit_depth.py <picture> [<picture> ...]     (prints the depth and the chain of runs)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = re.compile(r"^\d{8}_\d{6}_")
MAX_DEPTH = 2


def _run_folder(p: Path) -> Path | None:
    for q in [p.parent] + list(p.parents):
        if RUN.match(q.name) and (q.parent.name.startswith("outputs") or q.parent.name in ("dryrun",)):
            return q
    return None


def _abs(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def _crop_for_send(send: Path) -> dict | None:
    """The crop record (.cache/region_edits/<x>/<name>_crop.jpg.json) of this picture: the one whose 'send' names it, or for older records
    (region_edit.py make writes only render and box) the <name>_crop.jpg.json beside <name>_send.jpg, or <picture>.json itself."""
    if not send.parent.exists():
        return None
    for cand in (Path(str(send) + ".json"), send.with_name(send.name.replace("_send", "_crop") + ".json"),
                 send.with_name(send.name.replace("_send", "") + ".json")):
        if cand.exists() and cand.name != send.name:
            try:
                d = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(d, dict) and isinstance(d.get("render"), str):
                    return d
            except (OSError, ValueError):
                pass
    for j in send.parent.glob("*.json"):
        try:
            d = json.loads(j.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and isinstance(d.get("send"), str) and Path(d["send"]).name == send.name and isinstance(d.get("render"), str):
            return d
    return None


def _goal_of_run(run: Path) -> Path | None:
    """The picture a run was made from (its recipe's goal: a pin, a real photo, a region-edit crop or a render)."""
    man = run / "manifest.json"
    if man.exists():
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
            ref = (m.get("recipe") or {}).get("ref")
            if ref and Path(ref).exists():
                rec = json.loads(Path(ref).read_text(encoding="utf-8"))
                g = (rec.get("goal") or {}).get("path")
                if g:
                    return (ROOT / g) if not Path(g).is_absolute() else Path(g)
        except (OSError, ValueError, TypeError):
            pass
    sends = sorted((run / "02_inputs").glob("*_send.jpg")) if (run / "02_inputs").exists() else []
    return sends[0] if sends else None


def chain(picture: Path, _guard: int = 0) -> list[str]:
    """The generation passes behind a picture, newest first: run folder names, with 'edit of <render>' links followed back. Empty for a real photo."""
    p = Path(picture)
    if _guard > 25:
        return ["(chain too long)"]
    run = _run_folder(p)
    if run is None:
        crop = _crop_for_send(p)            # a region-edit crop of a render: its depth is the render's
        return chain(_abs(crop["render"]), _guard + 1) if crop and crop.get("render") else []
    goal = _goal_of_run(run)
    if goal is None:
        return [run.name]
    crop = _crop_for_send(goal)
    base = _abs(crop["render"]) if crop and crop.get("render") else goal
    return [run.name] + chain(base, _guard + 1)


def depth(picture: Path) -> int:
    return len(chain(picture))


def recipe_output_depth(rec: dict) -> tuple[int, list[str]]:
    """The depth a recipe's pictures will have: 1 + the depth of what it edits (a region edit's base render, or its goal)."""
    g = (rec.get("goal") or {}).get("path")
    if not g:
        return 1, []
    goal = (ROOT / g) if not Path(g).is_absolute() else Path(g)
    crop = _crop_for_send(goal)
    base = _abs(crop["render"]) if crop and crop.get("render") else goal
    ch = chain(base)
    return 1 + len(ch), ch


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for a in sys.argv[1:]:
        ch = chain(Path(a))
        print(f"depth {len(ch)}  {a}")
        for c in ch:
            print(f"    <- {c}")
