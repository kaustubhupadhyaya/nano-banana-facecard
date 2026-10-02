"""Check a render against an element inventory, item by item (the user, 2026-09-27: his tank paint, wheels, helmet, watch and the goal's
watermark kept coming out wrong). Writes a parts sheet (the render's crops beside his reference crops) to judge by eye, and optionally asks
Gemini's text model a yes/no question per inventory item as a second opinion (about 2 credits a render).

    .venv\\Scripts\\python.exe tools\\inventory_check.py <inventory.json> <render> [<render> ...] [--ask]
        -> <render>_parts.jpg (+ <render>_inventory.json with --ask)

Part boxes are fractions of the frame for the pin's composition (renders keep the goal's framing; checked with the pose gate first).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PARTS = {  # name: (x0, y0, x1, y1) as fractions of the render frame (pin composition)
    "head": (0.40, 0.03, 0.66, 0.21), "tank": (0.42, 0.49, 0.74, 0.64), "helmet": (0.13, 0.33, 0.37, 0.54),
    "watch (left wrist)": (0.50, 0.28, 0.70, 0.41), "bars, mirror, handguards": (0.55, 0.24, 0.88, 0.52),
    "crash guard, fog lamp, engine": (0.35, 0.60, 0.72, 0.90), "front wheel, disc, mudguard": (0.60, 0.64, 1.0, 0.97),
    "rear wheel, tyre": (0.03, 0.64, 0.38, 0.97), "watermark corner": (0.0, 0.93, 0.30, 1.0),
}


def tile(img, text, h=300):
    k = h / img.shape[0]
    t = cv2.resize(img, (max(1, int(img.shape[1] * k)), h), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    bar = np.full((30, t.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    return np.vstack([bar, t])


def rows_of(tiles, width=2400):
    rows, cur, w = [], [], 0
    for t in tiles:
        if cur and w + t.shape[1] > width:
            rows.append(cur)
            cur, w = [], 0
        cur.append(t)
        w += t.shape[1] + 8
    rows.append(cur)
    out = []
    for r in rows:
        h = max(t.shape[0] for t in r)
        row = np.hstack([cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in r])
        out.append(cv2.copyMakeBorder(row, 0, 8, 0, width + 400 - row.shape[1] if row.shape[1] < width + 400 else 0, cv2.BORDER_CONSTANT,
                                      value=(255, 255, 255)))
    W = max(o.shape[1] for o in out)
    return np.vstack([cv2.copyMakeBorder(o, 0, 0, 0, W - o.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for o in out])


def parts_sheet(inv: dict, render: Path) -> Path:
    img = cv2.imread(str(render))
    H, W = img.shape[:2]
    refs = [tile(cv2.imread(str(ROOT / r["path"])), "HIS: " + r["key"], 260) for r in inv["refs"]]
    parts = [tile(img[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)], name) for name, (x0, y0, x1, y1) in PARTS.items()]
    top, bottom = rows_of(refs), rows_of(parts)
    Wd = max(top.shape[1], bottom.shape[1])
    pad = lambda x: cv2.copyMakeBorder(x, 0, 0, 0, Wd - x.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))
    sheet = np.vstack([pad(top), np.full((6, Wd, 3), 0, np.uint8), pad(bottom)])
    out = render.with_name(render.stem + "_parts.jpg")
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out


async def ask(inv: dict, renders: list[Path]) -> None:
    import replicate as R
    from session import authenticated_client
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    models = [config.get("vision_model") or config.get("model"), config.get("model")]
    items = [c["item"] for c in inv["change"]] + ["no watermark or website text anywhere in the photo"]
    prompt = ("The first image is a photo. The other images are reference photos of one man's own motorcycle and items (his tank paint, helmet "
              "and watch). For each item below, answer whether the FIRST photo shows exactly his version as in the references. Reply with ONLY "
              "a JSON object mapping each item to {\"match\": true or false, \"why\": a few words}. Items:\n"
              + "\n".join(f"- {c['item']}: {c['his']}" for c in inv["change"]) + "\n- no watermark or website text anywhere in the photo")
    refs = [ROOT / r["path"] for r in inv["refs"]]
    async with authenticated_client(verbose=False) as client:
        for r in renders:
            d = await R.gemini_text(client, models, prompt, [r] + refs, _Log(), f"inventory {r.name}")
            r.with_name(r.stem + "_inventory.json").write_text(json.dumps(d, indent=1), encoding="utf-8")
            if isinstance(d, dict):
                bad = [k for k, v in d.items() if isinstance(v, dict) and not v.get("match")]
                print(f"{r.parent.name}/{r.name}: {len(d) - len(bad)}/{len(d)} match" + (f"; not: {bad}" if bad else ""))
            else:
                print(f"{r.name}: no answer")
    _ = items


class _Log:
    def say(self, s):
        print(s, flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inventory")
    ap.add_argument("renders", nargs="+")
    ap.add_argument("--ask", action="store_true")
    a = ap.parse_args()
    inv = json.loads(Path(a.inventory).read_text(encoding="utf-8"))
    renders = [Path(r) for r in a.renders]
    for r in renders:
        print(parts_sheet(inv, r))
    if a.ask:
        asyncio.run(ask(inv, renders))
    return 0


if __name__ == "__main__":
    sys.exit(main())
