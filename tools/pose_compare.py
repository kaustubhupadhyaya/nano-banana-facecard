"""Measure posture and position, goal vs render: body keypoints from a local YOLO11 pose model, so checklist items 12/14/29/30 stop resting on
my eye alone. The user, 2026-09-27: table tennis v7 v3_0 was called "posture fixed" while its legs stood in a wide stride where the goal's feet
are close together, and the pin renders put him in the middle of the bike where the goal has him left of centre behind the seat. Both were
visible in the pictures and slipped through a by-eye check; these numbers and overlays do not.

Runs in the YOLO environment (it has torch + ultralytics; the repo .venv does not):

    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\pose_compare.py "<goal>" "<render>" [<render> ...]
        -> per render: PASS/FAIL per measure, <render>_pose.jpg (goal skeleton ghosted over the render + onion-skin blend), <render>_pose.json
    D:\\VisionModels\\yolo\\.venv\\Scripts\\python.exe tools\\pose_compare.py "<goal>" --save-goal
        -> .cache\\poses\\<goal stem>.json: the goal's keypoints and objects, read by facecard.py route G (--pose-image / POSE POINTS)

Limits are fixed below (POSE_GATE) and printed with every result; they are never loosened for a render that fails them.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()
ROOT = Path(__file__).resolve().parents[1]
POSES = ROOT / ".cache" / "poses"
MODELS = Path(r"D:\VisionModels\yolo")

# Fixed limits (2026-09-27). Frame units are shares of the frame's width/height.
POSE_GATE = {
    "body_shift_max": 0.04,          # shoulder-midpoint position vs the goal's (item 14)
    "head_shift_max": 0.04,          # head centre vs the goal's (items 12/14)
    "scale_ratio": (0.93, 1.07),     # body size in the frame vs the goal's (item 29)
    "angle_max_deg": 15.0,           # each visible limb segment's direction vs the goal's (items 12/30)
    "torso_angle_max_deg": 10.0,     # the torso: an 11-degree lean read as visibly different (table tennis v7 v3_0)
    "wrist_shift_max": 0.06,         # each hand's position vs the goal's (item 30)
    "stance_ratio": (0.75, 1.33),    # feet apart / torso length vs the goal's (item 30)
    "object_rel_shift_max": 0.08,    # his centre along the main object (the bike, the table) vs the goal's (item 14)
    "head_pitch_max": 0.08,          # head bow: (nose below the eye line) / eye distance vs the goal's (item 12). Added 2026-09-27 after the user
                                     # caught the pin chain's level, eyes-to-camera heads (0.40-0.42 vs the goal's 0.52; the good pin versions
                                     # read 0.46-0.58). The neck-line angle alone passed them.
}
KP = ["nose", "l_eye", "r_eye", "l_ear", "r_ear", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist",
      "l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle"]
SEGMENTS = {  # name: (from, to); "mid_sh"/"mid_hip" are midpoints
    "torso": ("mid_sh", "mid_hip"), "neck/head": ("mid_sh", "nose"),
    "his right upper arm": ("r_shoulder", "r_elbow"), "his right forearm": ("r_elbow", "r_wrist"),
    "his left upper arm": ("l_shoulder", "l_elbow"), "his left forearm": ("l_elbow", "l_wrist"),
    "his right thigh": ("r_hip", "r_knee"), "his right shin": ("r_knee", "r_ankle"),
    "his left thigh": ("l_hip", "l_knee"), "his left shin": ("l_knee", "l_ankle"),
}
LIMBS = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
OBJECT_CLASSES = {3: "motorcycle", 2: "car", 7: "truck", 60: "table", 38: "tennis racket", 32: "sports ball", 56: "chair", 57: "couch"}
CONF = 0.5


def load(p: Path) -> np.ndarray:
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


_models = {}


def model(name: str):
    from ultralytics import YOLO
    if name not in _models:
        _models[name] = YOLO(str(MODELS / name))
    return _models[name]


def read(img: np.ndarray) -> dict:
    """Main person's 17 keypoints (normalized x, y, confidence) and the largest object of each tracked class."""
    H, W = img.shape[:2]
    r = model("yolo11m-pose.pt").predict(img, imgsz=1024, conf=0.25, verbose=False)[0]
    person = None
    if r.boxes is not None and len(r.boxes):
        boxes = r.boxes.xyxy.cpu().numpy()
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        i = int(np.argmax(areas))
        k = r.keypoints.data[i].cpu().numpy()          # 17 x 3 (x px, y px, conf)
        person = {"box": [float(boxes[i][0] / W), float(boxes[i][1] / H), float(boxes[i][2] / W), float(boxes[i][3] / H)],
                  "kp": {KP[j]: [float(k[j][0] / W), float(k[j][1] / H), float(k[j][2])] for j in range(17)}}
    d = model("yolo11m.pt").predict(img, imgsz=1024, conf=0.30, classes=list(OBJECT_CLASSES), verbose=False)[0]
    objects = {}
    for b, c in zip(d.boxes.xyxy.cpu().numpy(), d.boxes.cls.cpu().numpy()):
        name = OBJECT_CLASSES[int(c)]
        box = [float(b[0] / W), float(b[1] / H), float(b[2] / W), float(b[3] / H)]
        if name not in objects or (box[2] - box[0]) * (box[3] - box[1]) > _area(objects[name]):
            objects[name] = box
    return {"wh": [W, H], "person": person, "objects": objects}


def _area(b):
    return (b[2] - b[0]) * (b[3] - b[1])


def point(kp: dict, name: str):
    if name == "mid_sh":
        a, b = kp["l_shoulder"], kp["r_shoulder"]
    elif name == "mid_hip":
        a, b = kp["l_hip"], kp["r_hip"]
    else:
        p = kp[name]
        return (p[0], p[1]) if p[2] >= CONF else None
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) if a[2] >= CONF and b[2] >= CONF else None


def head_centre(kp: dict):
    pts = [kp[n] for n in ("nose", "l_eye", "r_eye", "l_ear", "r_ear") if kp[n][2] >= CONF]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


def head_pitch(kp: dict, wh):
    """How far the nose sits below the eye line, in eye distances: larger = head bowed, smaller = chin level or up."""
    le, re, n = point(kp, "l_eye"), point(kp, "r_eye"), point(kp, "nose")
    if not (le and re and n):
        return None
    ed = math.hypot((le[0] - re[0]) * wh[0], (le[1] - re[1]) * wh[1])
    return ((n[1] - (le[1] + re[1]) / 2) * wh[1]) / ed if ed else None


def seg_angle(kp: dict, a: str, b: str, wh):
    p, q = point(kp, a), point(kp, b)
    if p is None or q is None:
        return None
    return math.degrees(math.atan2((q[1] - p[1]) * wh[1], (q[0] - p[0]) * wh[0]))


def scale(kp: dict, wh):
    """Body size in the frame: torso length (shoulder midpoint to hip midpoint) as a share of the frame height, or the shoulder-to-nose
    distance x 2.2 when the hips are hidden (behind a motorcycle)."""
    s, h = point(kp, "mid_sh"), point(kp, "mid_hip")
    if s and h:
        return math.hypot((h[0] - s[0]) * wh[0] / wh[1], h[1] - s[1]), "torso"
    n = point(kp, "nose")
    if s and n:
        return 2.2 * math.hypot((n[0] - s[0]) * wh[0] / wh[1], n[1] - s[1]), "shoulders-to-nose x2.2"
    return None, "none"


def compare(g: dict, r: dict) -> dict:
    G = POSE_GATE
    res = {"checks": [], "fails": []}

    def check(item, name, ok, value, limit):
        res["checks"].append({"item": item, "name": name, "ok": bool(ok), "value": value, "limit": limit})
        if not ok:
            res["fails"].append(item)

    if not g["person"] or not r["person"]:
        check("14/29/30", "person found", False, "no person in " + ("goal" if not g["person"] else "render"), "a person")
        return res
    gk, rk = g["person"]["kp"], r["person"]["kp"]
    gs, rs = point(gk, "mid_sh"), point(rk, "mid_sh")
    if gs and rs:
        d = math.hypot(rs[0] - gs[0], rs[1] - gs[1])
        check(14, "body position (shoulder midpoint)", d <= G["body_shift_max"],
              f"shift {d:.3f} (goal x{gs[0]:.2f} y{gs[1]:.2f}, render x{rs[0]:.2f} y{rs[1]:.2f})", f"<= {G['body_shift_max']}")
    gh, rh = head_centre(gk), head_centre(rk)
    if gh and rh:
        d = math.hypot(rh[0] - gh[0], rh[1] - gh[1])
        check("12/14", "head position", d <= G["head_shift_max"],
              f"shift {d:.3f} (goal x{gh[0]:.2f} y{gh[1]:.2f}, render x{rh[0]:.2f} y{rh[1]:.2f})", f"<= {G['head_shift_max']}")
    gp_, rp_ = head_pitch(gk, g["wh"]), head_pitch(rk, r["wh"])
    if gp_ is not None and rp_ is not None:
        check(12, "head bow (nose below eye line / eye distance)", abs(rp_ - gp_) <= G["head_pitch_max"],
              f"goal {gp_:+.2f}, render {rp_:+.2f} ({'more level, chin up' if rp_ < gp_ else 'bowed lower'})", f"<= {G['head_pitch_max']} apart")
    (gsc, gm), (rsc, rm) = scale(gk, g["wh"]), scale(rk, r["wh"])
    if gsc and rsc and gm == rm:
        ratio = rsc / gsc
        lo, hi = G["scale_ratio"]
        check(29, f"size in the frame ({gm})", lo <= ratio <= hi, f"x{ratio:.2f}", f"{lo}-{hi}")
    for name, (a, b) in SEGMENTS.items():
        ga, ra = seg_angle(gk, a, b, g["wh"]), seg_angle(rk, a, b, r["wh"])
        if ga is None or ra is None:
            continue
        diff = abs((ra - ga + 180) % 360 - 180)
        lim = G["torso_angle_max_deg"] if name == "torso" else G["angle_max_deg"]
        check("12" if name == "neck/head" else 30, f"{name} direction", diff <= lim, f"{diff:.0f} deg off", f"<= {lim:.0f}")
    for w in ("r_wrist", "l_wrist"):
        gp, rp = point(gk, w), point(rk, w)
        if gp and rp:
            d = math.hypot(rp[0] - gp[0], rp[1] - gp[1])
            label = "his right hand" if w == "r_wrist" else "his left hand"
            check(30, f"{label} position", d <= G["wrist_shift_max"],
                  f"shift {d:.3f} (goal x{gp[0]:.2f} y{gp[1]:.2f}, render x{rp[0]:.2f} y{rp[1]:.2f})", f"<= {G['wrist_shift_max']}")
    ga_, ra_ = (point(gk, "l_ankle"), point(gk, "r_ankle")), (point(rk, "l_ankle"), point(rk, "r_ankle"))
    gsc_t, rsc_t = scale(gk, g["wh"]), scale(rk, r["wh"])
    if all(ga_) and all(ra_) and gsc_t[1] == "torso" and rsc_t[1] == "torso":
        gst = math.hypot((ga_[0][0] - ga_[1][0]) * g["wh"][0] / g["wh"][1], ga_[0][1] - ga_[1][1]) / gsc_t[0]
        rst = math.hypot((ra_[0][0] - ra_[1][0]) * r["wh"][0] / r["wh"][1], ra_[0][1] - ra_[1][1]) / rsc_t[0]
        ratio = rst / max(gst, 1e-6)
        lo, hi = G["stance_ratio"]
        check(30, "feet apart (stance)", lo <= ratio <= hi, f"x{ratio:.2f} (goal {gst:.2f}, render {rst:.2f} torso lengths)", f"{lo}-{hi}")
    for name in g["objects"]:
        if name not in r["objects"] or name in ("car", "truck", "chair", "couch") or not (gs and rs):
            continue
        go, ro = g["objects"][name], r["objects"][name]
        grel = (gs[0] - go[0]) / max(go[2] - go[0], 1e-6)
        rrel = (rs[0] - ro[0]) / max(ro[2] - ro[0], 1e-6)
        check(14, f"where he stands along the {name}", abs(rrel - grel) <= G["object_rel_shift_max"],
              f"goal {grel:.2f}, render {rrel:.2f} of its length from picture-left", f"<= {G['object_rel_shift_max']} apart")
    return res


def draw_skeleton(img, kp: dict, colour, thick=4):
    H, W = img.shape[:2]
    pts = {j: (int(kp[KP[j]][0] * W), int(kp[KP[j]][1] * H)) for j in range(17) if kp[KP[j]][2] >= CONF}
    for a, b in LIMBS:
        if a in pts and b in pts:
            cv2.line(img, pts[a], pts[b], colour, thick, cv2.LINE_AA)
    for p in pts.values():
        cv2.circle(img, p, thick + 2, colour, -1, cv2.LINE_AA)


def overlay(goal_img, g, render_img, r, out: Path, res: dict):
    H, W = render_img.shape[:2]
    gi = cv2.resize(goal_img, (W, H), interpolation=cv2.INTER_AREA)
    a = render_img.copy()
    if r["person"]:
        draw_skeleton(a, r["person"]["kp"], (40, 40, 230), 4)          # render: red
    if g["person"]:
        draw_skeleton(a, g["person"]["kp"], (60, 220, 60), 3)          # goal: green, ghosted onto the render frame
    blend = cv2.addWeighted(gi, 0.5, render_img, 0.5, 0)
    if g["person"]:
        draw_skeleton(blend, g["person"]["kp"], (60, 220, 60), 3)
    if r["person"]:
        draw_skeleton(blend, r["person"]["kp"], (40, 40, 230), 3)
    g2 = gi.copy()
    if g["person"]:
        draw_skeleton(g2, g["person"]["kp"], (60, 220, 60), 3)
    sheet = np.hstack([g2, np.full((H, 8, 3), 255, np.uint8), a, np.full((H, 8, 3), 255, np.uint8), blend])
    bar = np.full((34 + 22 * max(1, len(res["fails"])), sheet.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, "goal (green skeleton) | render (red = render, green = goal) | 50/50 blend", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    y = 50
    for c in res["checks"]:
        if not c["ok"]:
            cv2.putText(bar, f"FAIL item {c['item']}: {c['name']}: {c['value']} (limit {c['limit']})", (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 200), 1)
            y += 22
    cv2.imwrite(str(out), np.vstack([bar, sheet]), [cv2.IMWRITE_JPEG_QUALITY, 88])


def frame_crop(g: dict, r: dict) -> tuple[list[int], dict] | None:
    """The crop that puts the render's body where the goal has it: same size (torso or shoulders-to-nose) and same shoulder-midpoint position,
    at the goal's aspect ratio. Crop only (never pads or upscales past the render's pixels); for a long-lens goal a crop equals moving the
    camera closer. Returns ([x0, y0, x1, y1] px, info) or None when the render is already tighter than the goal or no body is found."""
    if not g["person"] or not r["person"]:
        return None
    gk, rk = g["person"]["kp"], r["person"]["kp"]
    (gsc, gm), (rsc, rm) = scale(gk, g["wh"]), scale(rk, r["wh"])
    gs, rs = point(gk, "mid_sh"), point(rk, "mid_sh")
    if not (gsc and rsc and gs and rs) or gm != rm:
        return None
    W, H = r["wh"]
    ch = rsc / gsc                              # crop height as a share of the render's height
    if ch >= 1.0:
        return None
    aspect = g["wh"][0] / g["wh"][1]
    cw, chp = ch * H * aspect, ch * H
    x0, y0 = rs[0] * W - gs[0] * cw, rs[1] * H - gs[1] * chp
    need = [n for n, v in (("left", x0 < 0), ("top", y0 < 0), ("right", x0 + cw > W), ("bottom", y0 + chp > H)) if v]
    x0, y0 = min(max(x0, 0), W - cw), min(max(y0, 0), H - chp)
    return [int(round(x0)), int(round(y0)), int(round(x0 + cw)), int(round(y0 + chp))], {"crop_share": round(ch, 3), "short_of_room": need}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("goal")
    ap.add_argument("renders", nargs="*")
    ap.add_argument("--save-goal", action="store_true", help="write .cache/poses/<goal stem>.json for route G")
    ap.add_argument("--json", action="store_true", help="print one JSON line per render instead of text")
    ap.add_argument("--frame", action="store_true", help="also write <render>_framed.jpg: the render cropped so his body sits where the goal's "
                    "does (measured from the keypoints), and gate that crop too")
    a = ap.parse_args()
    goal = Path(a.goal)
    gimg = load(goal)
    g = read(gimg)
    if a.save_goal:
        POSES.mkdir(parents=True, exist_ok=True)
        (POSES / f"{goal.stem}.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
        print(f"goal pose saved: {POSES / (goal.stem + '.json')}  person found: {bool(g['person'])}  objects: {list(g['objects'])}")
    renders = [Path(x) for x in a.renders]
    if a.frame:
        for rp in list(renders):
            rimg = load(rp)
            fc = frame_crop(g, read(rimg))
            if fc is None:
                print(f"{rp.name}: no crop (already as tight as the goal, or no body found)")
                continue
            (x0, y0, x1, y1), info = fc
            out = rp.with_name(rp.stem + "_framed.jpg")
            cv2.imwrite(str(out), rimg[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"{rp.name}: framed -> {out.name} {x1 - x0}x{y1 - y0} {info}")
            renders.append(out)
    for rp in renders:
        rimg = load(rp)
        r = read(rimg)
        res = compare(g, r)
        res["render"] = str(rp)
        res["limits"] = POSE_GATE
        rp.with_name(rp.stem + "_pose.json").write_text(json.dumps({"result": res, "render_pose": r}, indent=1), encoding="utf-8")
        overlay(gimg, g, rimg, r, rp.with_name(rp.stem + "_pose.jpg"), res)
        if a.json:
            print(json.dumps({"render": str(rp), "fails": res["fails"], "checks": res["checks"]}))
            continue
        verdict = "PASS" if not res["fails"] else f"FAIL items {sorted(set(map(str, res['fails'])))}"
        print(f"\n{rp.parent.name}/{rp.name}: {verdict}")
        for c in res["checks"]:
            print(f"  {'ok  ' if c['ok'] else 'FAIL'} [{c['item']}] {c['name']}: {c['value']} (limit {c['limit']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
