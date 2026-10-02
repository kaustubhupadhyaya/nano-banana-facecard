"""Where he is in the frame, in Gemini's own language: bounding boxes normalized to 0-1000 as [ymin, xmin, ymax, xmax] (the format Gemini's
object detection answers in; its head boxes were right on 6 of 6 photos, 2026-09-23). The user asked (2026-09-26) for something Gemini understands
better than a 3x3 grid to hold the camera distance and the subject's boundary (checklist items 14 and 29).

    .venv\\Scripts\\python.exe tools\\goal_layout.py "<goal>"                  # read and cache .cache\\layouts\\<goal stem>.json (text call, no image credits)
    .venv\\Scripts\\python.exe tools\\goal_layout.py "<goal>" --compare <render> [<render> ...]
                                                                           # read each render's boxes and compare with the goal's

The cached layout is picked up by `facecard.py gen --goal` (route G) and written into the prompt as a LAYOUT section.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import replicate as R  # noqa: E402
from session import authenticated_client  # noqa: E402

LAYOUTS = ROOT / ".cache" / "layouts"
PROMPT = (
    "Look at this photo. Reply with ONLY a JSON object, no other text, with bounding boxes normalized to 0-1000 as [ymin, xmin, ymax, xmax]:\n"
    "person: the box around the main man's whole visible body, from the top of his hair to the lowest visible part of him\n"
    "head: the box around his head, from the top of his hair to the bottom of his chin or beard, including his ears\n"
    "objects: a list of up to 3 of the largest things he stands with, holds or sits on (a vehicle, a table, furniture), each as "
    "{\"name\": short name, \"box\": [ymin, xmin, ymax, xmax]}")


class _Log:
    def say(self, s):
        print(s, flush=True)


def layout_path(goal: Path) -> Path:
    return LAYOUTS / f"{goal.stem}.json"


def _view(img_path: Path) -> Path:
    img = cv2.imread(str(img_path)) if img_path.suffix.lower() not in (".heic", ".heif") else None
    if img is None:
        img = R.load_source(img_path)
    k = 1024 / max(img.shape[:2])
    out = LAYOUTS / f"_view_{img_path.stem}.jpg"
    LAYOUTS.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
    return out


async def read_layout(client, text_models, img_path: Path) -> dict | None:
    d = await R.gemini_text(client, text_models, PROMPT, [_view(img_path)], _Log(), f"layout {img_path.name}")
    if not d or "person" not in d or "head" not in d:
        return None
    return {"person": [int(v) for v in d["person"]], "head": [int(v) for v in d["head"]],
            "objects": [{"name": str(o.get("name")), "box": [int(v) for v in o.get("box", [])]} for o in (d.get("objects") or []) if len(o.get("box", [])) == 4]}


def describe(lay: dict) -> str:
    """The LAYOUT section route G writes into the prompt (facecard.layout_text)."""
    from facecard import layout_text
    return layout_text(lay)


def compare(goal: dict, render: dict) -> dict:
    def c(b):
        return ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2)
    def hgt(b):
        return max(1, b[2] - b[0])
    out = {}
    for key in ("person", "head"):
        g, r = goal[key], render[key]
        (gx, gy), (rx, ry) = c(g), c(r)
        out[key] = {"height_ratio": round(hgt(r) / hgt(g), 2), "center_shift": round(((rx - gx) ** 2 + (ry - gy) ** 2) ** 0.5 / 1000, 3)}
    return out


async def main_async(args) -> int:
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    model = config.get("model")
    text_models = [config.get("vision_model") or model, model]
    goal = Path(args.goal)
    async with authenticated_client(verbose=False) as client:
        lp = layout_path(goal)
        if lp.exists() and not args.refresh:
            lay = json.loads(lp.read_text(encoding="utf-8"))
        else:
            lay = await read_layout(client, text_models, goal)
            if lay is None:
                print("no layout read for the goal")
                return 1
            lp.write_text(json.dumps(lay, indent=1), encoding="utf-8")
        print(f"goal {goal.name}: {json.dumps(lay)}")
        print(describe(lay))
        for r in args.compare or []:
            rl = await read_layout(client, text_models, Path(r))
            if rl is None:
                print(f"{r}: no layout read")
                continue
            cmp_ = compare(lay, rl)
            print(f"{Path(r).parent.name}/{Path(r).name}: person height x{cmp_['person']['height_ratio']} shift {cmp_['person']['center_shift']}, "
                  f"head height x{cmp_['head']['height_ratio']} shift {cmp_['head']['center_shift']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("goal")
    ap.add_argument("--compare", nargs="*")
    ap.add_argument("--refresh", action="store_true")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
