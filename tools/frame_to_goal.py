"""Crop a render so he sits in the frame exactly as in the goal: same height in the frame, head top at the same place, same horizontal centre.

For a long-lens goal (flat perspective, like the pin) a crop is the same as moving the camera closer, so this measures and copies; it draws
nothing. It only crops (never pads or rescales past the render), keeps the goal's aspect ratio, and says when the render leaves too little room.

    .venv\\Scripts\\python.exe tools\\frame_to_goal.py "<goal>" "<render>" [--out "<render>_framed.jpg"]
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
sys.path.insert(0, str(ROOT / "tools"))
import goal_layout as GL  # noqa: E402
from session import authenticated_client  # noqa: E402


def crop_box(goal: dict, render: dict, W: int, H: int, aspect: float) -> tuple[list[int], dict]:
    gp, rp = goal["person"], render["person"]
    gh, rh = (gp[2] - gp[0]) / 1000, (rp[2] - rp[0]) / 1000          # person heights as shares of each frame
    ch = rh / gh                                                        # crop height as a share of the render's height
    cw_px = ch * H * aspect
    top = rp[0] / 1000 - gp[0] / 1000 * ch                             # head top lands where the goal's does
    cx = (rp[1] + rp[3]) / 2000 * W
    left = cx - (gp[1] + gp[3]) / 2000 * cw_px                          # his centre lands where the goal's does
    box = [int(round(left)), int(round(top * H)), int(round(left + cw_px)), int(round((top + ch) * H))]
    need = {"left": box[0] < 0, "top": box[1] < 0, "right": box[2] > W, "bottom": box[3] > H}
    # shift inside the render when it leaves too little room (reported, never padded)
    dx = -box[0] if box[0] < 0 else (W - box[2] if box[2] > W else 0)
    dy = -box[1] if box[1] < 0 else (H - box[3] if box[3] > H else 0)
    box = [box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy]
    return box, {"crop_share": round(ch, 3), "short_of_room": [k for k, v in need.items() if v], "shift_px": [dx, dy]}


async def main_async(args) -> int:
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    text_models = [config.get("vision_model") or config.get("model"), config.get("model")]
    goal, render = Path(args.goal), Path(args.render)
    lay = json.loads(GL.layout_path(goal).read_text(encoding="utf-8"))
    img = cv2.imread(str(render))
    H, W = img.shape[:2]
    gimg = cv2.imread(str(goal))
    aspect = gimg.shape[1] / gimg.shape[0]
    async with authenticated_client(verbose=False) as client:
        rl = await GL.read_layout(client, text_models, render)
        if rl is None:
            print("no layout read for the render")
            return 1
        box, info = crop_box(lay, rl, W, H, aspect)
        if box[2] - box[0] > W or box[3] - box[1] > H:
            print(f"render is framed tighter than the goal (crop share {info['crop_share']}): nothing to crop")
            return 1
        out = Path(args.out) if args.out else render.with_name(render.stem + "_framed.jpg")
        crop = img[box[1]:box[3], box[0]:box[2]]
        cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"{out}  crop {box} of {W}x{H} -> {crop.shape[1]}x{crop.shape[0]}  {info}")
        fl = await GL.read_layout(client, text_models, out)
        if fl:
            c = GL.compare(lay, fl)
            print(f"framed vs goal: person height x{c['person']['height_ratio']} shift {c['person']['center_shift']}, "
                  f"head height x{c['head']['height_ratio']} shift {c['head']['center_shift']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("goal")
    ap.add_argument("render")
    ap.add_argument("--out")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
