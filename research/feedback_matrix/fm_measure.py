"""Measurements for FEEDBACK_MATRIX.xlsx. Uses the pipeline's own functions (identity, composite, replicate) so the numbers mean exactly what the
run.json numbers mean; nothing here interprets, it only measures.

  composite_metrics : identity, similarity to the source face, size, shift, light, neck gap, non-head drift of a complete picture (as replicate.run does)
  raw_metrics       : identity / similarity / relative size / shift of a returned head crop (a raw return is a crop, not a picture)
  divergence        : how many pixels differ from the SOURCE outside the crop (JPEG files get a tolerance of 24 of 255, PNG files none)
"""
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

_HERE = Path(__file__).resolve()
ROOT = next((p for p in _HERE.parents if (p / "facecard.json").exists()), Path(r"C:\Users\Admin\GitHub\nano-banana-facecard"))
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import composite  # noqa: E402
import identity  # noqa: E402
import replicate  # noqa: E402
from scorer import ArcFaceScorer  # noqa: E402

JPEG_TOL = 24   # calibrated 2026-09-21: a JPEG re-encode of a pixel-identical picture differs by <= 16 of 255 outside the crop (0 px above 24)


def scene_path(d: dict) -> Path | None:
    """The source photo of a replicate run. Runs of round 3 stored the scene READING (a dict) under `scene`; their photo is `args.scene`."""
    s = d.get("scene")
    if not isinstance(s, str) or not s:
        s = (d.get("args") or {}).get("scene")
    if not isinstance(s, str) or not s:
        return None
    p = Path(s)
    return p if p.is_absolute() else ROOT / p


class Measurer:
    def __init__(self):
        cfg = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
        self.sc = ArcFaceScorer()
        self.pool = identity.build_pool(cfg, self.sc, verbose=False)
        self._ctx: dict[str, dict | None] = {}

    # ------------------------------------------------------------------ context of a run: the source, the crop, the measured source face
    def context(self, run_dir: Path, d: dict | None) -> dict | None:
        key = str(run_dir)
        if key in self._ctx:
            return self._ctx[key]
        ctx = None
        try:
            if d and d.get("crop") and d.get("head_boxes"):
                sp = scene_path(d)
                src = replicate.load_source(sp) if sp is not None and sp.exists() else None
                if src is None:
                    raise FileNotFoundError('source photo not found: ' + str(sp))
                rect = tuple(int(v) for v in d["crop"])
                hb = [tuple(int(v) for v in b) for b in d["head_boxes"]]
                main = hb[0]
                mic = (main[0] - rect[0], main[1] - rect[1], main[2], main[3])
                src_crop = composite.take(src, rect)
                dups = set(d.get("duplicates_excluded") or [])
                se = identity.score_image(src_crop, self.pool, self.sc, exclude_names=dups, expect_box=mic)
                if se.get("detected"):
                    gap = replicate.face_neck_gap(src_crop, se["box"])
                    ctx = dict(src=src, rect=rect, head_boxes=hb, mic=mic, src_crop=src_crop, dups=dups, src_eval=se, src_gap=gap,
                               kind=d.get("source_kind"))
        except Exception as e:  # keep the workbook going; the row will say the number could not be measured
            print("  context failed for", run_dir.name, type(e).__name__, e)
        self._ctx[key] = ctx
        return ctx

    # ------------------------------------------------------------------ a complete picture, measured the way replicate.run measures a candidate
    def composite_metrics(self, ctx: dict, img: np.ndarray) -> dict | None:
        if img.shape != ctx["src"].shape:
            return None
        out_crop = composite.take(img, ctx["rect"])
        res = identity.score_image(out_crop, self.pool, self.sc, exclude_names=ctx["dups"], expect_box=ctx["mic"])
        if not res.get("detected"):
            return None
        se = ctx["src_eval"]
        fs = max(se["box"][2:])
        m = {"identity": round(float(res["score"]), 3),
             "gt_sim": round(float(np.dot(se["emb"], res["emb"])), 3),
             "size": round(res["box"][2] / max(1, se["box"][2]), 3),
             "shift": round(float(np.hypot(res["box"][0] + res["box"][2] / 2 - (se["box"][0] + se["box"][2] / 2),
                                           res["box"][1] + res["box"][3] / 2 - (se["box"][1] + se["box"][3] / 2))) / fs, 3)}
        dr = composite.inside_drift(ctx["src"], img, ctx["rect"], ctx["head_boxes"])
        m["ssim"], m["mad"] = dr.get("ssim"), dr.get("mean_abs_diff")
        lt = composite.light_delta(ctx["src_crop"], out_crop, se["box"])
        m["dE"], m["dL"] = lt["dE"], lt["dL"]
        gap = replicate.face_neck_gap(out_crop, res["box"])
        m["neck"] = round(gap - ctx["src_gap"], 1) if (gap is not None and ctx["src_gap"] is not None) else None
        return m

    # ------------------------------------------------------------------ a returned head crop (not a picture)
    def raw_metrics(self, ctx: dict | None, img: np.ndarray) -> dict | None:
        dups = ctx["dups"] if ctx else None
        res = identity.score_image(img, self.pool, self.sc, exclude_names=dups)
        if not res.get("detected"):
            return None
        m = {"identity": round(float(res["score"]), 3)}
        if ctx:
            se = ctx["src_eval"]
            rh, rw = img.shape[:2]
            sh, sw = ctx["src_crop"].shape[:2]
            fw_r, fw_s = res["box"][2] / rw, se["box"][2] / sw          # face width as a fraction of the crop
            m["gt_sim"] = round(float(np.dot(se["emb"], res["emb"])), 3)
            m["size"] = round(fw_r / fw_s, 3)
            cr = ((res["box"][0] + res["box"][2] / 2) / rw, (res["box"][1] + res["box"][3] / 2) / rh)
            cs = ((se["box"][0] + se["box"][2] / 2) / sw, (se["box"][1] + se["box"][3] / 2) / sh)
            m["shift"] = round(float(np.hypot(cr[0] - cs[0], cr[1] - cs[1])) / fw_s, 3)
        return m

    def whole_identity(self, img: np.ndarray) -> dict | None:
        res = identity.score_image(img, self.pool, self.sc)
        if not res.get("detected"):
            return None
        return {"identity": round(float(res["score"]), 3)}

    # ------------------------------------------------------------------ non-crop divergence of a complete picture against the source
    def divergence(self, ctx: dict, path: Path, img: np.ndarray) -> dict:
        src = ctx["src"]
        if img.shape != src.shape:
            return {"same_size": False}
        x, y, w, h = ctx["rect"]
        outside = np.ones(src.shape[:2], bool)
        outside[y:y + h, x:x + w] = False
        tol = 0 if path.suffix.lower() == ".png" else JPEG_TOL
        diff = np.abs(img.astype(np.int16) - src.astype(np.int16)).max(axis=2)
        out_px = int((diff[outside] > tol).sum())
        in_px = int((diff[~outside] > JPEG_TOL).sum())   # inside the crop one tolerance for every file type, so the shares are comparable
        return {"same_size": True, "outside_px": out_px, "outside_pct": round(100.0 * out_px / max(1, int(outside.sum())), 4),
                "inside_pct": round(100.0 * in_px / max(1, int((~outside).sum())), 1), "tol": tol}
