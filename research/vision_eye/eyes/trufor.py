"""TruFor eye (grip-unina, CVPR 2023): a forensic network that reads camera noise traces (Noiseprint++) and maps spliced or generated regions.
Licence: nonprofit use only. Fine for checking the user's own pictures; never inside a paid product (Facecard Studio).

Installed at D:\\VisionModels\\TruFor (its own Python 3.11 venv, CPU torch, weights in test_docker\\weights). Every picture in the benchmark
IS a pasted AI crop, so TruFor's "something was edited" signal is expected on all of them. The question tested here is whether HOW STRONGLY the
face lights up, relative to the real photo around the crop and to the same place in the untouched source, tracks the user's verdicts.

prepare() writes lossless crops at native resolution (TruFor needs the original pixels, never the resized views) of the output and the source,
and runs TruFor once over all of them (the model loads once; results are cached, so a rerun only processes new crops).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np

import composite
from replicate import detect_faces, load_source

TRUFOR = Path(r"D:\VisionModels\TruFor")
PY = TRUFOR / "venv" / "Scripts" / "python.exe"
SRC = TRUFOR / "test_docker" / "src"
ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / ".cache" / "vision_bench" / "trufor"
CONTEXT = 1.25     # the edited crop plus a ring of real photo around it (12.5 percent each side)
MAX_SIDE = 1600    # larger crops are halved (only the 1757 px IMG_0862 crop): CPU time and memory; applied to output and source alike
FLAG_AT = 0.30     # provisional; bench.py reports the best threshold on the set


def _read(p: str) -> np.ndarray | None:
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    if img is None and Path(p).exists():
        img = load_source(Path(p))
    return img


def _box(case: dict) -> tuple[int, int, int, int] | None:
    if not case.get("region"):
        return None
    x, y, w, h = case["region"]
    W, H = case["size"]
    return composite.rect_crop((H, W), x + w / 2, y + h / 2, w * CONTEXT, h * CONTEXT)


def _save(img: np.ndarray, box, path: Path) -> float:
    c = composite.take(img, box)
    k = 0.5 if max(c.shape[:2]) > MAX_SIDE else 1.0
    if k != 1.0:
        c = cv2.resize(c, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), c)
    return k


def prepare(cases: list[dict]) -> None:
    inp = WORK / "inputs"
    for c in cases:
        box = _box(c)
        if box is None:
            continue
        for tag, p in (("out", c["picture"]), ("src", c.get("source"))):
            f = inp / f"{c['id']}_{tag}.png"
            if p and not f.exists():
                img = _read(p)
                if img is not None and [img.shape[1], img.shape[0]] == c["size"]:
                    _save(img, box, f)
    todo = [f for f in sorted(inp.glob("*.png")) if not (WORK / "outputs" / (f.name + ".npz")).exists()]
    print(f"TruFor: {len(todo)} crops to analyse (cached: {len(list(inp.glob('*.png'))) - len(todo)})", flush=True)
    if todo:
        # the trailing separator matters on Windows: trufor_test.py strips the input root from each path and only removes a leading "/",
        # so without it every output became "\name.npz" and landed in C:\ (PermissionError)
        subprocess.run([str(PY), "trufor_test.py", "-gpu", "-1", "-in", str(inp) + "\\", "-out", str(WORK / "outputs")], cwd=str(SRC), check=False)


def _load(cid: str, tag: str):
    f = WORK / "outputs" / f"{cid}_{tag}.png.npz"
    if not f.exists():
        return None
    d = np.load(f)
    return {"map": d["map"], "score": float(d["score"]) if "score" in d else None}


def _masks(shape, case, face_box):
    """face: inner ellipse of the detected face; ring: the real photo outside the edited crop, inside the CONTEXT box."""
    h, w = shape[:2]
    face = np.zeros((h, w), np.uint8)
    x, y, bw, bh = face_box
    cv2.ellipse(face, (int(x + bw / 2), int(y + bh / 2)), (int(bw * 0.38), int(bh * 0.45)), 0, 0, 360, 255, -1)
    cb = _box(case)
    rx, ry, rw, rh = case["region"]
    k = w / cb[2]
    ring = np.full((h, w), 255, np.uint8)
    cv2.rectangle(ring, (int((rx - cb[0]) * k), int((ry - cb[1]) * k)), (int((rx - cb[0] + rw) * k), int((ry - cb[1] + rh) * k)), 0, -1)
    return face > 0, ring > 0


def judge(case: dict) -> dict:
    o, s = _load(case["id"], "out"), _load(case["id"], "src")
    if o is None:
        return {"flag": None, "score": None, "why": "no TruFor result (no region or picture)"}
    crop = cv2.imread(str(WORK / "inputs" / f"{case['id']}_out.png"))
    faces = detect_faces(crop, min_px=20)
    if not faces:
        return {"flag": None, "score": None, "why": f"no face found in the crop; global score {o['score']}"}
    face, ring = _masks(o["map"].shape, case, faces[0]["box"])
    if ring.sum() < 100:
        return {"flag": None, "score": None, "why": "no real-photo ring around the crop (crop at the photo edge)"}
    lift = float(o["map"][face].mean() - o["map"][ring].mean())
    if s is not None and s["map"].shape == o["map"].shape:
        lift_src = float(s["map"][face].mean() - s["map"][ring].mean())
        delta = lift - lift_src
        why = f"face vs photo ring: {lift:+.2f} (source {lift_src:+.2f}); global score {o['score']:.2f} (source {s['score']:.2f})"
    else:
        delta = lift
        why = f"face vs photo ring: {lift:+.2f} (no source); global score {o['score']:.2f}"
    return {"flag": delta >= FLAG_AT, "score": round(delta, 3), "why": why}
