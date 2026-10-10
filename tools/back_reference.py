"""His back, from the user's own video: the back reference for the back-view pins, and the record-only back readings.

The user, 2026-10-09: "D:\\Downloads\\B9F9CBB0-9336-4E0A-83BF-F6E6BF72BA79.MP4 this video has all details of my current back physique" (the gym back pin: "you are
removing the back definition that I actually have"). Frames are cut from that video by exact frame index, so the reference is reproducible, never from a screenshot.

    .venv\\Scripts\\python.exe tools\\back_reference.py build [--video V] [--frames 54,74] [--crop x0,y0,x1,y1] [--out .cache\\inventories\\pin_refs\\his_back.jpg]
        decodes the frames with ffmpeg, keeps his janeu (the thin white sacred thread across his back; the user, 2026-10-10: "It is the holy thread that
        Brahmins wear, called jenu", in every bare-torso picture; --remove-thread paints it out, the 2026-10-09 behaviour that took it for an earphone wire), sets
        the crops side by side and writes the picture plus <out>.json: the video's sha256, frame indexes and times, the crop, the pixels the cleaning changed
    .venv\\Scripts\\python.exe tools\\back_reference.py measure <image> [<image> ...] [--record <json>]
        record-only back readings (YOLO pose keypoints + silhouette) in the same units for his frames, the pin man and a result:
        sw_px / hw_px / torso_px (shoulder width, hip width, shoulder-hip distance), sw_hw, sw_torso, and the silhouette width at 25 / 45 / 65 % down the
        shoulder-hip line over the shoulder width (arms hang beside the torso, so these include them). No gate uses them (BEST_CHECKLIST item 32 is by eye).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

VIDEO = Path(r"D:\Downloads\B9F9CBB0-9336-4E0A-83BF-F6E6BF72BA79.MP4")
FRAMES = (54, 74)                    # 0-based frame indexes of f_06 (1.800 s, light across the back, square) and f_08 (2.467 s, relaxed)
CROP = (300, 100, 1080, 1250)        # x0, y0, x1, y1 of the 1080x1920 frame: head top to a hand's length below the waistband
OUT = ROOT / ".cache" / "inventories" / "pin_refs" / "his_back.jpg"
RECORD = Path(r"D:\FacecardData\back_video\back_measures.json")
GAP = 12
# His janeu (the thin white sacred thread, first mistaken for an earphone wire) lying along his spine, traced by eye on 2x zoomed grids of the two frames (2026-10-09), in FULL-FRAME pixels (1080x1920). Automatic
# detection (top-hat, local colour contrast, a Hessian ridge filter) kept finding the silhouette and the door's edges instead of the wire. Each trace is
# snapped to the wire's own ridge before it is painted over.
WIRE_TRACES: dict[int, list[tuple[int, int]]] = {
    54: [(553, 466), (552, 472), (551, 505), (547, 545), (540, 575), (537, 600), (540, 620), (550, 635), (570, 642), (582, 652), (590, 675), (597, 700), (607, 730),
         (617, 760), (627, 790), (637, 817), (645, 840), (660, 870), (680, 900), (695, 915), (710, 930), (730, 937), (770, 945), (810, 947), (835, 949)],
    74: [(575, 442), (582, 480), (585, 530), (587, 570), (595, 620), (602, 650), (615, 690), (625, 720), (637, 755), (647, 790), (655, 810), (665, 850), (675, 875),
         (687, 900), (702, 917), (722, 930), (750, 937), (780, 942), (810, 947), (830, 950)],
}
WIRE_SNAP, WIRE_BAND = 6, 11     # px: how far a trace point may move to the ridge, and the painted band's width (the wire is about 3 px; its thin shadow beside it needs the rest)
WIRE_WAIST_Y = 915               # full-frame y of the waistband: below it the band lies on the black elastic, where a skin fill would smear, so it is inpainted instead
WIRE_SIGMA = 6.0                 # px: the skin fill is the neighbourhood average outside the band at this scale, plus grain of the skin's own strength


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def decode_frame(video: Path, n: int, out_png: Path) -> np.ndarray:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-fps_mode", "passthrough", str(out_png)], check=True)
    im = cv2.imread(str(out_png))
    if im is None:
        raise SystemExit(f"ffmpeg wrote no frame {n} from {video}")
    return im


def ridge(ch: np.ndarray, sigma: float, bright: bool = True) -> np.ndarray:
    """Line strength from the Hessian of one channel (bright or dark thin lines; blobs and corners are suppressed)."""
    g = cv2.GaussianBlur(ch.astype(np.float32), (0, 0), sigma)
    ixx = cv2.Sobel(g, cv2.CV_32F, 2, 0, ksize=3) / 8.0
    iyy = cv2.Sobel(g, cv2.CV_32F, 0, 2, ksize=3) / 8.0
    ixy = cv2.Sobel(g, cv2.CV_32F, 1, 1, ksize=3) / 4.0
    t = np.sqrt(((ixx - iyy) / 2) ** 2 + ixy ** 2)
    l1, l2 = (ixx + iyy) / 2 + t, (ixx + iyy) / 2 - t
    if not bright:
        l1, l2 = -l2, -l1
    r = np.maximum(0.0, -l2) * sigma * sigma
    r[np.abs(l1) > 0.45 * np.abs(l2)] = 0.0
    return r


def snapped(pts: list[tuple[int, int]], rmap: np.ndarray) -> np.ndarray:
    """Densify the traced polyline to ~2 px steps and move every point along its normal (+-WIRE_SNAP px) onto the strongest ridge; offsets are median- and mean-smoothed."""
    P = np.array(pts, np.float32)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.arange(0, s[-1], 2.0)
    D = np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], axis=1)
    Ds = np.stack([np.convolve(np.pad(D[:, i], 3, mode="edge"), np.ones(7, np.float32) / 7, mode="valid") for i in (0, 1)], axis=1)
    T = np.gradient(Ds, axis=0)
    T /= np.maximum(1e-6, np.linalg.norm(T, axis=1, keepdims=True))
    N = np.stack([-T[:, 1], T[:, 0]], axis=1)
    offs = np.arange(-WIRE_SNAP, WIRE_SNAP + 1, dtype=np.float32)
    best = np.zeros(len(D), np.float32)
    for k in range(len(D)):
        q = (D[k][None, :] + offs[:, None] * N[k][None, :]).astype(np.float32)
        vals = cv2.remap(rmap, q[:, 0].reshape(1, -1), q[:, 1].reshape(1, -1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).ravel()
        best[k] = offs[int(np.argmax(vals))] if vals.max() > 0 else 0.0
    k9 = 9
    med = np.array([np.median(best[max(0, k - k9 // 2):k + k9 // 2 + 1]) for k in range(len(best))], np.float32)
    sm = np.convolve(np.pad(med, 4, mode="edge"), np.ones(9, np.float32) / 9, mode="valid")
    return D + sm[:, None] * N


def wire_mask(full: np.ndarray, n: int) -> np.ndarray:
    pts = WIRE_TRACES.get(n)
    if not pts:
        raise SystemExit(f"no wire trace for frame {n}: trace it on a 2x grid (WIRE_TRACES) or build without --remove-thread")
    hsv, lab = cv2.cvtColor(full, cv2.COLOR_BGR2HSV), cv2.cvtColor(full, cv2.COLOR_BGR2LAB)
    r = ridge(lab[:, :, 0], 1.4) / 6.0 + 0.5 * ridge(hsv[:, :, 1], 1.4, bright=False) / 6.0
    line = snapped(pts, r)
    m = np.zeros(full.shape[:2], np.uint8)
    cv2.polylines(m, [line.round().astype(np.int32).reshape(-1, 1, 2)], False, 1, WIRE_BAND, cv2.LINE_AA)
    return cv2.dilate((m > 0).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))


def clean(full: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """The wire and its shadow replaced by the skin around them: a smooth neighbourhood fill plus the skin's own grain (TELEA inpainting left a dark ghost line)."""
    m_all = wire_mask(full, n)
    m = m_all.copy()
    m[WIRE_WAIST_Y:] = 0                  # above the waistband: the wide band with the smooth skin fill
    f = full.astype(np.float32)
    w = (1 - m).astype(np.float32)
    fill = cv2.GaussianBlur(f * w[..., None], (0, 0), WIRE_SIGMA) / np.maximum(cv2.GaussianBlur(w, (0, 0), WIRE_SIGMA)[..., None], 1e-3)
    ring = (cv2.dilate(m, np.ones((41, 41), np.uint8)) > 0) & (cv2.dilate(m, np.ones((21, 21), np.uint8)) == 0)
    hp = f - cv2.GaussianBlur(f, (0, 0), 2.0)
    sigma = hp[ring].std(axis=0) if ring.any() else np.zeros(3, np.float32)
    noise = cv2.GaussianBlur(np.random.default_rng(54).normal(0, 1, f.shape).astype(np.float32), (0, 0), 0.8) * sigma
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)[..., None]
    out = np.clip(f * (1 - mf) + (fill + noise) * mf, 0, 255).astype(np.uint8)
    low = m_all.copy()                    # on the waistband: only the wire itself (a thin band), inpainted, so the black elastic's edge stays sharp
    low[:WIRE_WAIST_Y] = 0
    low = cv2.erode(low, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    if low.any():
        out = cv2.inpaint(out, low * 255, 3, cv2.INPAINT_TELEA)
    return out, m_all


def build(video: Path, frames: tuple[int, ...], crop: tuple[int, int, int, int], out: Path, wire: bool) -> int:
    if not video.is_file():
        raise SystemExit(f"the video is missing: {video}")
    pieces, rec_frames = [], []
    with tempfile.TemporaryDirectory(prefix="back_frames_") as td:
        for n in frames:
            full = decode_frame(video, n, Path(td) / f"f{n}.png")
            removed = 0
            if wire:
                full, m = clean(full, n)
                removed = int(m.sum())
            pieces.append(full[crop[1]:crop[3], crop[0]:crop[2]])
            rec_frames.append({"frame_index": n, "time_s": round(n / 30.0, 3), "wire_pixels_changed": removed})
    h = max(p.shape[0] for p in pieces)
    sheet = np.full((h, sum(p.shape[1] for p in pieces) + GAP * (len(pieces) - 1), 3), 30, np.uint8)
    x = 0
    for p in pieces:
        sheet[:p.shape[0], x:x + p.shape[1]] = p
        x += p.shape[1] + GAP
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 95])
    rec = {"kind": "his_back/1", "video": str(video), "video_sha256": sha256(video), "video_bytes": video.stat().st_size, "frames": rec_frames,
           "crop_xyxy": list(crop), "wire_removed": wire, "out": str(out), "out_sha256": sha256(out), "out_size": [int(sheet.shape[1]), int(sheet.shape[0])]}
    out.with_suffix(".json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"{out} {rec['out_size'][0]}x{rec['out_size'][1]}  frames {frames}  wire pixels changed {[f['wire_pixels_changed'] for f in rec_frames]}")
    return 0


def readings(img_path: Path, rd: dict) -> dict:
    """Record-only back readings from one YOLO reading (pose keypoints + silhouette mask)."""
    p = rd.get("person")
    out: dict = {"image": str(img_path), "persons": rd.get("persons")}
    if not p:
        out["note"] = "no person found"
        return out
    kp = p["kp"]
    need = ("l_shoulder", "r_shoulder", "l_hip", "r_hip")
    conf = {n: round(kp[n][2], 2) for n in need}
    out["conf"] = conf
    ls, rs, lh, rh = (np.array(kp[n][:2]) for n in need)
    sw, hw = float(np.linalg.norm(ls - rs)), float(np.linalg.norm(lh - rh))
    sm, hm = (ls + rs) / 2, (lh + rh) / 2
    torso = float(np.linalg.norm(sm - hm))
    out.update({"sw_px": round(sw, 1), "hw_px": round(hw, 1), "torso_px": round(torso, 1), "sw_hw": round(sw / hw, 3) if hw else None,
                "sw_torso": round(sw / torso, 3) if torso else None, "usable": all(c >= 0.5 for c in conf.values())})
    mp = rd.get("mask")
    if mp and torso > 0 and sw > 0:
        m = cv2.imread(mp, cv2.IMREAD_GRAYSCALE) > 0
        ax = (hm - sm) / torso
        perp = np.array([-ax[1], ax[0]])
        widths = {}
        for f in (0.25, 0.45, 0.65):
            c = sm + (hm - sm) * f
            ts = np.arange(-3.0 * sw, 3.0 * sw, 1.0)
            pts = (c[None, :] + ts[:, None] * perp[None, :]).round().astype(int)
            ok = (pts[:, 0] >= 0) & (pts[:, 0] < m.shape[1]) & (pts[:, 1] >= 0) & (pts[:, 1] < m.shape[0])
            on = np.zeros(len(ts), bool)
            on[ok] = m[pts[ok, 1], pts[ok, 0]]
            idx = np.where(on)[0]
            if len(idx):
                # the run of mask pixels that contains the axis point, so a second person or a rail beside him is not counted
                z = int(np.argmin(np.abs(ts)))
                if on[z]:
                    a = z
                    while a > 0 and on[a - 1]:
                        a -= 1
                    b = z
                    while b < len(on) - 1 and on[b + 1]:
                        b += 1
                    widths[str(f)] = round((b - a + 1) / sw, 3)
        out["sil_width_over_sw"] = widths
    return out


def measure(images: list[Path], record: Path | None) -> int:
    from tools.background_restore import yolo_masks
    td = Path(tempfile.mkdtemp(prefix="back_measure_"))
    jobs = [{"path": str(p), "mask": str(td / f"{i}_mask.png")} for i, p in enumerate(images)]
    got = yolo_masks(jobs)
    rows = [readings(p, got.get(str(p), {})) for p in images]
    for r in rows:
        print(json.dumps(r))
    if record:
        prev = json.loads(record.read_text(encoding="utf-8")) if record.is_file() else {"kind": "back_measures/1", "rows": []}
        prev["rows"] = [x for x in prev["rows"] if x.get("image") not in {r["image"] for r in rows}] + rows
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps(prev, indent=1), encoding="utf-8")
        print("recorded ->", record)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--video", default=str(VIDEO))
    b.add_argument("--frames", default=",".join(str(n) for n in FRAMES), help="0-based frame indexes, comma separated")
    b.add_argument("--crop", default=",".join(str(v) for v in CROP), help="x0,y0,x1,y1 of the frame")
    b.add_argument("--out", default=str(OUT))
    b.add_argument("--remove-thread", action="store_true", help="paint his janeu out (only on request: it is part of him, the user 2026-10-10)")
    m = sub.add_parser("measure")
    m.add_argument("images", nargs="+")
    m.add_argument("--record", nargs="?", const=str(RECORD), default=None, help=f"append to this json (default {RECORD})")
    a = ap.parse_args()
    if a.cmd == "build":
        return build(Path(a.video), tuple(int(v) for v in a.frames.split(",")), tuple(int(v) for v in a.crop.split(",")), Path(a.out), a.remove_thread)
    return measure([Path(p) for p in a.images], Path(a.record) if a.record else None)


if __name__ == "__main__":
    sys.exit(main())
