"""Build the vision benchmark: for every labelled picture in cases.py, find its run, its source photo and the region the pipeline edited, and
save the views an eye is shown (all under .cache\\vision_bench\\, never in git: they show the user's face).

    .venv\\Scripts\\python.exe research\\vision_eye\\build_bench.py

Views per case (long side 1024 px, JPEG 95):
  <id>_full.jpg      the whole picture
  <id>_region.jpg    the edited region (the pipeline's crop; for old runs without a recorded crop, the box of pixels that differ from the source)
  <id>_context.jpg   the edited region widened 1.5x: the head on its neck and shoulders
  <id>_src_region.jpg, <id>_src_context.jpg   the same boxes in the source photo, when the source still exists
The manifest .cache\\vision_bench\\manifest.json lists every case with its label, the user's verdict, the paths and the region.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import composite  # noqa: E402
from cases import CASES  # noqa: E402
from replicate import load_source  # noqa: E402

OUT = ROOT / ".cache" / "vision_bench"
SUPER_FAVS = [ROOT / ".cache" / "super_favs", Path(r"C:\Users\Admin\Downloads\super favs")]
LONG = 1024
CONTEXT = 1.5


def run_dir(run: str) -> Path | None:
    for d in [ROOT / "outputs" / run] + [Path(p) for p in glob.glob(str(ROOT / ".cache" / "feedback" / "**" / run), recursive=True)]:
        if (d / "run.json").exists():
            return d
    return None


def read_any(p: Path) -> np.ndarray | None:
    img = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if img is None and p.exists():
        try:
            img = load_source(p)
        except Exception:
            img = None
    return img


def source_of(data: dict) -> Path | None:
    # args.scene is the path; some runs of 2026-09-20 wrote the scene reading (a dict) into "scene"
    scene = (data.get("args") or {}).get("scene") or data.get("scene")
    if not isinstance(scene, str) or not scene:
        return None
    p = Path(scene)
    cands = [p if p.is_absolute() else ROOT / p]
    for d in SUPER_FAVS:
        cands += sorted(d.glob(p.stem + ".*"))
    for c in cands:
        if c.exists():
            return c
    return None


def changed_box(pic: np.ndarray, src: np.ndarray) -> tuple[int, int, int, int] | None:
    """Box of the pixels that differ from the source (outputs change nothing outside the crop; JPEG noise is blurred away)."""
    if pic.shape != src.shape:
        return None
    d = np.abs(pic.astype(np.int16) - src.astype(np.int16)).max(axis=2).astype(np.float32)
    d = cv2.blur(d, (15, 15))
    ys, xs = np.where(d > 10)
    if len(xs) < 400:
        return None
    x0, x1 = np.percentile(xs, [0.2, 99.8]).astype(int)
    y0, y1 = np.percentile(ys, [0.2, 99.8]).astype(int)
    return int(x0), int(y0), int(x1 - x0), int(y1 - y0)


def save_view(img: np.ndarray, path: Path) -> str:
    k = LONG / max(img.shape[:2])
    v = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    cv2.imwrite(str(path), v, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return str(path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, missing = [], []
    for cid, label, run, pic_name, verdict in CASES:
        d = run_dir(run)
        if d is None:
            missing.append(f"{cid} {run}: run folder not found")
            continue
        data = json.loads((d / "run.json").read_text(encoding="utf-8"))
        pic_p = Path(pic_name) if Path(pic_name).is_absolute() else d / pic_name
        if not pic_p.exists() and pic_name == "best.jpg" and (d / "best.png").exists():
            pic_p = d / "best.png"
        pic = read_any(pic_p)
        if pic is None:
            missing.append(f"{cid} {pic_p}: picture not found")
            continue
        src_p = source_of(data)
        src = read_any(src_p) if src_p else None
        if src is not None and src.shape != pic.shape:
            src = None
        region = changed_box(pic, src) if src is not None else None
        how = "diff with the source"
        if data.get("crop"):
            region, how = tuple(int(v) for v in data["crop"]), "the run's crop"
        if region is None:
            missing.append(f"{cid}: no region (no recorded crop and no source to diff against)")
        e = {"id": cid, "label": label, "verdict": verdict, "run": run, "run_dir": str(d), "picture": str(pic_p),
             "source": str(src_p) if src is not None else None, "size": [pic.shape[1], pic.shape[0]], "region": list(region) if region else None,
             "region_from": how if region else None, "kind": data.get("source_kind"), "views": {}}
        e["views"]["full"] = save_view(pic, OUT / f"{cid}_full.jpg")
        if region:
            x, y, w, h = region
            ctx = composite.rect_crop(pic.shape, x + w / 2, y + h / 2, w * CONTEXT, h * CONTEXT)
            e["context_box"] = list(ctx)
            e["views"]["region"] = save_view(composite.take(pic, region), OUT / f"{cid}_region.jpg")
            e["views"]["context"] = save_view(composite.take(pic, ctx), OUT / f"{cid}_context.jpg")
            if src is not None:
                e["views"]["src_region"] = save_view(composite.take(src, region), OUT / f"{cid}_src_region.jpg")
                e["views"]["src_context"] = save_view(composite.take(src, ctx), OUT / f"{cid}_src_context.jpg")
        manifest.append(e)
        print(f"{cid} {label:4s} region {e['region']} ({e['region_from']}), source {'yes' if src is not None else 'NO'}  {verdict[:60]}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {k: sum(1 for m in manifest if m["label"] == k) for k in ("flag", "pass", "info")}
    print(f"\n{len(manifest)} cases saved to {OUT} ({counts}); problems: {len(missing)}")
    for m in missing:
        print("  " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
