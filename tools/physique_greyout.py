"""The next-cut physique test, method A (the user, 2026-10-10: "Let's test out the full grayout method for now ... I want you to retain as many
unique features of my body, muscle ratio, and proportions"): his torso and upper arms are painted grey in the crop sent, so Gemini must redraw
them (an edit that only says "change his body" returned it unchanged 8 of 8), while his own un-greyed crop goes along as THE BODY reference.
His head, neck, forearms, hands, trousers and the background stay his real pixels: tools/region_edit.py pastes back only the grey area.

    .venv\\Scripts\\python.exe tools\\physique_greyout.py make <photo> <out dir>          crop, grey mask, send copy, body reference, preview
    .venv\\Scripts\\python.exe tools\\physique_greyout.py measure <photo> <picture> [...] [--ai <crop .json>]
        the plan's targets, measured on the same photo; --ai also asks the AI part by part (waist, belly, love handles, abs, obliques, chest,
        deltoids, arm size, veins, janeu, chain) on the crop's box

Targets (the approved plan, step 5; a picture outside them is rejected): waist -4 to -8%, deltoid width +1 to +4%, shoulder-bone width within
+-2%, upper arm 0 to +5%. Widths come from character.measure (YOLO keypoints and silhouette, ATR labels); only arm_shoulder of these passed
validation (character.TRUSTED), so the numbers are a check beside the user's eye, never the verdict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GREY = (128, 128, 128)
# measure --ai (2026-10-10, the user on round 1: "the fat around the waist even got increased further ... you shrank the arm size and have
# reduced my vascularity"): what widths cannot say, part by part, on the same crop of the base photo and of the picture. A diagnosis for the next
# round's wording beside the widths, never the verdict.
BODY_MATCH_PROMPT = (
    "Image 1 is a real photo of a man's body today. Image 2 is a generated picture of the same man in the same pose, meant to show his body a few "
    "weeks further into a cutting phase: about five points of body fat lower, slightly fuller shoulders and arms, the same frame. Compare image 2 "
    "with image 1 part by part, ignoring the light, the sharpness and the background. Reply with ONLY a JSON object with these keys: "
    "\"waist\": \"narrower|same|wider\", \"lower_belly\": \"flatter|same|softer\", \"love_handles\": \"smaller|same|bigger\", "
    "\"abs\": \"clearer|same|less clear\", \"obliques\": \"clearer|same|less clear\", \"chest\": \"firmer|same|softer\", "
    "\"deltoids\": \"rounder|same|smaller\", \"arm_size\": \"bigger|same|smaller\", \"biceps_vein\": \"visible|missing\" (in image 2), "
    "\"forearm_veins\": \"visible|missing\" (in image 2), \"janeu\": \"present|missing|moved\" (the thin white thread over his left shoulder "
    "and across his chest and stomach to his right hip, compared with image 1), \"chain\": \"present|missing\", \"natural\": true or false "
    "(whether image 2's body looks like a real photo of this man), \"biggest\": \"one short sentence naming the biggest problem, or none\"}")
SEND_LONG = 1024
TARGETS = {"waist_px": (-8.0, -4.0), "bideltoid_px": (1.0, 4.0), "sw_px": (-2.0, 2.0), "arm_mean": (0.0, 5.0)}


def _reading(photo: Path) -> tuple[dict, dict, np.ndarray]:
    import character
    m = character.measure(photo)
    raw = character.raw_of(m["sha256"])
    atr = cv2.imread(str(ROOT / ".cache" / "character_masks" / f"{m['sha256']}_atr.png"), cv2.IMREAD_GRAYSCALE)
    return m, raw, atr


def make(photo: Path, out: Path, arms_to: str = "elbow") -> int:
    """arms_to 'elbow' (round 1-2) or 'wrist' (round 3, 2026-10-10: Gemini's upper arm met the real forearm with a visible step at the elbow, and
    redrawing the whole arm lets the forearm veins the user has be drawn; the hands stay real)."""
    import character
    from scorer import analyze_face
    out.mkdir(parents=True, exist_ok=True)
    img = character.load(photo)
    H, W = img.shape[:2]
    m, raw, atr = _reading(photo)
    if atr is None or atr.shape[:2] != (H, W):
        print("no ATR labels at the photo's size: run character.measure first")
        return 1
    kpd = raw["body_raw"]["person"]["kp"]                        # {name: [x, y, conf]} (YOLO pose, COCO names)
    pt = lambda n: np.array(kpd[n][:2], float)
    sh_l, sh_r, el_l, el_r = pt("l_shoulder"), pt("r_shoulder"), pt("l_elbow"), pt("r_elbow")
    sw = float(np.linalg.norm(sh_l - sh_r))
    a = analyze_face(cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    fx, fy, fw, fh = (v * 2 for v in a["box"])
    chin = fy + fh
    sh_y = (sh_l[1] + sh_r[1]) / 2
    neck_cut = chin + 0.45 * (sh_y - chin)                       # the neck stays real: no seam under the chin
    belt = np.isin(atr, (6, 8))
    cols = slice(int(min(sh_l[0], sh_r[0])), int(max(sh_l[0], sh_r[0])))
    rows_belt = np.where(belt[:, cols].any(axis=1))[0]
    waist_top = int(rows_belt.min()) if rows_belt.size else int((pt("l_hip")[1] + pt("r_hip")[1]) / 2)
    yy = np.arange(H)[:, None]
    torso = (atr == 11) & (yy > neck_cut) & (yy < waist_top)
    arms = np.zeros_like(torso)
    arm_end = max(el_l[1], el_r[1]) if arms_to == "elbow" else min(pt("l_wrist")[1], pt("r_wrist")[1]) - 0.06 * sw
    for lab in (14, 15):
        part = atr == lab
        arms |= part & (yy < arm_end) & (yy > sh_y - 0.25 * sw)
    grey = (torso | arms).astype(np.uint8)
    # room for the outline to move (a narrower waist, rounder shoulders): dilate by 5% of the shoulder width, and fill each row between the
    # arms and the torso from the armpits down to the elbows
    k = max(3, int(0.05 * sw) | 1)
    grey = cv2.dilate(grey, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    elbow_y = int(max(el_l[1], el_r[1]))
    for y in range(int(sh_y), elbow_y):
        xs = np.where(grey[y])[0]
        if xs.size:
            grey[y, xs.min():xs.max() + 1] = 1
    # down to the waistband in every column, so no strip of real stomach is left between the grey and the trousers (a seam)
    ref_row = max(int(neck_cut) + 1, waist_top - int(0.02 * H))
    for c in np.where(grey[ref_row] > 0)[0]:
        col = belt[ref_row:, c]
        if col.any():
            grey[ref_row:ref_row + int(np.argmax(col)), c] = 1
    grey[:int(neck_cut)] = 0
    grey[waist_top + int(0.04 * H):] = 0
    ys, xs = np.where(grey > 0)
    x0 = max(0, int(xs.min() - 0.30 * sw)); x1 = min(W, int(xs.max() + 0.30 * sw))
    y0 = max(0, int(fy - 0.9 * fh)); y1 = min(H, int(max(pt("l_wrist")[1], pt("r_wrist")[1]) + 0.25 * sw))
    crop = img[y0:y1, x0:x1]
    gmask = grey[y0:y1, x0:x1] * 255
    sent = crop.copy()
    sent[gmask > 0] = GREY
    s = SEND_LONG / max(crop.shape[:2])
    size = (int(round(crop.shape[1] * s)), int(round(crop.shape[0] * s)))
    cv2.imwrite(str(out / "body_crop.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 97])
    cv2.imwrite(str(out / "body_crop_mask.png"), gmask)
    cv2.imwrite(str(out / "body_grey_send.jpg"), cv2.resize(sent, size, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 95])
    cv2.imwrite(str(out / "his_body_ref.jpg"), cv2.resize(crop, size, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 95])
    meta = {"render": str(photo), "box": [x0, y0, x1, y1], "mask": str(out / "body_crop_mask.png"),
            "why": "next-cut physique, method A (full grey-out, the user 2026-10-10); only the grey area is pasted back"}
    (out / "body_crop.jpg.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    prev = crop.copy()
    prev[gmask > 0] = (0.45 * prev[gmask > 0] + 0.55 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imwrite(str(out / "preview.jpg"), cv2.resize(prev, (size[0] // 2, size[1] // 2)), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(json.dumps({"crop": meta["box"], "grey_px": int((gmask > 0).sum()), "shoulder_px": round(sw), "neck_cut": round(neck_cut),
                      "waist_top": waist_top, "send": list(size)}))
    return 0


WAIST_SHRINK = 0.06       # the target outline's waist, narrower than his own at the love handles (the plan: -4 to -8%)
ARM_GROW = 0.012          # of the shoulder width, added on each side of his arms (upper arm 0 to +5%)
DELT_GROW = 0.02          # of the shoulder width, added around the shoulder caps (deltoids +1 to +4%)


def make_target(photo: Path, out: Path, back: bool = False) -> int:
    """Round 4 (2026-10-10): the grey area IS the target outline. Rounds 1-3 measured how Gemini treats a grey area: with his own body as a reference
    it copies that outline (waist +1%), without one it fills the grey shape (round 3: the grey, grown 5% past his outline, came back as a waist 3-7%
    wider at the love handles). So the shape is drawn by code from his own measured silhouette: the waist pulled in by WAIST_SHRINK at the love
    handles (ramping in from below the chest), the shoulder caps and arms a touch fuller; the strip of his old waist outside it is filled from the
    door and wall around it (cv2.inpaint), so Gemini sees background there. Gemini renders everything inside; code fixes only the outline."""
    import character
    from scorer import analyze_face
    out.mkdir(parents=True, exist_ok=True)
    img = character.load(photo)
    H, W = img.shape[:2]
    m, raw, atr = _reading(photo)
    kpd = raw["body_raw"]["person"]["kp"]
    pt = lambda n: np.array(kpd[n][:2], float)
    sh_l, sh_r = pt("l_shoulder"), pt("r_shoulder")
    sw = float(np.linalg.norm(sh_l - sh_r))
    a = analyze_face(cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
    if a.get("box") is not None:
        fx, fy, fw, fh = (v * 2 for v in a["box"])
    else:
        # seen from straight behind there is no face (his back video, frame 74, 2026-10-10): the head is his hair (ATR 2) above the shoulders
        hy, hx = np.where((atr == 2)[:int((sh_l[1] + sh_r[1]) / 2)])
        if not hy.size:
            print("no face and no hair found: cannot place the head")
            return 1
        fx, fy, fw, fh = float(hx.min()), float(hy.min()), float(hx.max() - hx.min()), float(hy.max() - hy.min())
    sh_y = (sh_l[1] + sh_r[1]) / 2
    neck_cut = fy + fh + 0.45 * (sh_y - fy - fh)
    seg = cv2.imread(str(ROOT / ".cache" / "character_masks" / f"{m['sha256']}.png"), cv2.IMREAD_GRAYSCALE)
    if back and seg is not None and seg.shape[:2] == (H, W):
        # the neck from his silhouette, not from the chin: on a back view his head turns and the chin sits far below the nape, so the chin rule cut
        # the grey straight across the middle of his trapezius (IMG_6929, 2026-10-10). The narrowest silhouette row between the face box's top and
        # the shoulder line is the neck; the grey starts a quarter of the way from it to the shoulders.
        ys = np.arange(int(fy + fh), int(sh_y))                    # from the chin line down (the head can sit outside the shoulder span)
        wid = np.array([(seg[y] > 0).sum() for y in ys])
        good = wid > 0
        if good.any():
            neck_row = int(ys[good][int(np.argmin(wid[good]))])
            neck_cut = min(neck_cut, neck_row + 0.25 * (sh_y - neck_row))
    belt = np.isin(atr, (6, 8))
    cols = slice(int(min(sh_l[0], sh_r[0])), int(max(sh_l[0], sh_r[0])))
    rows_belt = np.where(belt[:, cols].any(axis=1))[0]
    waist_top = int(rows_belt.min())
    wrist_y = min(pt("l_wrist")[1], pt("r_wrist")[1]) - 0.06 * sw
    yy = np.arange(H)[:, None]
    torso = ((atr == 11) | (atr == 4)) & (yy > neck_cut) & (yy < waist_top + int(0.02 * H)) & ~belt
    # a bare back (IMG_6929, 2026-10-10): ATR leaves the upper trapezius between his neck and shoulders unlabelled, so a straight grey edge would
    # cross his upper back; the person silhouette (YOLO-seg, character.measure's mask) fills those rows between the shoulders
    if back and seg is not None and seg.shape[:2] == (H, W):
        # a back view: in every column of his upper back the grey starts just below his hair (ATR 2: curls and beard) and runs down his
        # silhouette to the labelled torso, so its top edge follows his hairline and the shoulder contour, never a straight line across the
        # trapezius (2026-10-10, IMG_6929: both the chin rule and a silhouette neck row cut straight across it)
        hair = atr == 2
        xa, xb = max(0, int(min(sh_l[0], sh_r[0]) - 0.2 * sw)), min(W, int(max(sh_l[0], sh_r[0]) + 0.2 * sw))
        for x in range(xa, xb):
            col_t = np.where(torso[:int(sh_y + 0.5 * sw), x])[0]
            col_h = np.where(hair[:int(sh_y), x])[0]
            col_s = np.where(seg[:int(sh_y + 0.5 * sw), x] > 0)[0]
            if not col_s.size:
                continue
            start = (int(col_h.max()) + int(0.03 * sw)) if col_h.size else int(col_s.min())
            end = int(col_t.min()) if col_t.size else int(sh_y)
            if end > start:
                torso[start:end, x] |= seg[start:end, x] > 0
        torso[:int(fy + fh * 0.6)] = False                         # never the face
    arms = np.isin(atr, (14, 15)) & (yy > sh_y - 0.25 * sw) & (yy < wrist_y)
    real = (torso | arms).astype(np.uint8)
    # the target torso: each row's torso run around the body's centre pulled in at both edges, by a share ramping from 0 (below the chest) to
    # WAIST_SHRINK (the love handles, from 75% of the way to the waistband down)
    cx = int((sh_l[0] + sh_r[0]) / 2)
    t_torso = torso.copy()
    y_a, y_b = sh_y + 0.45 * (waist_top - sh_y), sh_y + 0.75 * (waist_top - sh_y)
    for y in range(int(y_a), waist_top + int(0.02 * H)):
        xs = np.where(torso[y])[0]
        if not xs.size:
            continue
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        run = next((r for r in runs if r[0] <= cx <= r[-1]), None)
        if run is None:
            continue
        share = WAIST_SHRINK * min(1.0, max(0.0, (y - y_a) / max(1.0, y_b - y_a)))
        d = int(round(0.5 * share * (run[-1] - run[0] + 1)))
        if d:
            t_torso[y, run[0]:run[0] + d] = False
            t_torso[y, run[-1] - d + 1:run[-1] + 1] = False
    t_arms = cv2.dilate(arms.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(ARM_GROW * sw) + 1,) * 2)) > 0
    caps = np.zeros_like(arms)
    caps[int(sh_y - 0.25 * sw):int(sh_y + 0.30 * sw)] = True
    cap_grow = cv2.dilate((real > 0).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(DELT_GROW * sw) + 1,) * 2)) > 0
    target = t_torso | t_arms | (cap_grow & caps & (yy > neck_cut))
    target &= ~belt
    if not back:                                                  # a back view: the hairline-following start is the top edge
        target[:int(neck_cut)] = False
    band = (real > 0) & ~target                                   # his old outline outside the target: becomes background
    ys, xs = np.where(target | band)
    x0 = max(0, int(xs.min() - 0.30 * sw)); x1 = min(W, int(xs.max() + 0.30 * sw))
    y0 = max(0, int(fy - 0.9 * fh)); y1 = min(H, int(max(pt("l_wrist")[1], pt("r_wrist")[1]) + 0.25 * sw))
    crop = img[y0:y1, x0:x1].copy()
    tm, bm = target[y0:y1, x0:x1], band[y0:y1, x0:x1]
    bg = cv2.inpaint(crop, (cv2.dilate(bm.astype(np.uint8), np.ones((5, 5), np.uint8)) | tm.astype(np.uint8)) * 255, 9, cv2.INPAINT_TELEA)
    sent = crop.copy()
    sent[bm] = bg[bm]
    sent[tm] = GREY
    s = SEND_LONG / max(crop.shape[:2])
    size = (int(round(crop.shape[1] * s)), int(round(crop.shape[0] * s)))
    paste_mask = ((tm | bm) * 255).astype(np.uint8)
    cv2.imwrite(str(out / "body_crop.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 97])
    cv2.imwrite(str(out / "body_crop_mask.png"), paste_mask)
    cv2.imwrite(str(out / "body_grey_send.jpg"), cv2.resize(sent, size, interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 95])
    meta = {"render": str(photo), "box": [x0, y0, x1, y1], "mask": str(out / "body_crop_mask.png"),
            "why": ("next-cut physique round 4: the grey is the target outline (waist -%.0f%% at the love handles, arms +%.1f%% of the shoulder "
                    "width a side, shoulder caps +%.0f%%); his old outline outside it was filled from the background; the grey and that strip "
                    "are pasted back") % (WAIST_SHRINK * 100, ARM_GROW * 100, DELT_GROW * 100)}
    (out / "body_crop.jpg.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    prev = crop.copy()
    prev[tm] = (0.45 * prev[tm] + 0.55 * np.array([0, 0, 255])).astype(np.uint8)
    prev[bm] = (0.3 * prev[bm] + 0.7 * np.array([0, 255, 255])).astype(np.uint8)
    cv2.imwrite(str(out / "preview.jpg"), cv2.resize(prev, (size[0] // 2, size[1] // 2)), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(json.dumps({"crop": meta["box"], "target_px": int(tm.sum()), "band_px": int(bm.sum()), "send": list(size)}))
    return 0


def lower_waist_rows(photo: Path) -> tuple[list[int], int]:
    """The rows of the love handles (from 60% of the way between his shoulders and the waistband down to it) and the body's centre column, on the
    base photo; every picture of the same photo is measured on the same rows."""
    m, raw, atr = _reading(photo)
    kpd = raw["body_raw"]["person"]["kp"]
    sh_y = (kpd["l_shoulder"][1] + kpd["r_shoulder"][1]) / 2
    cx = int((kpd["l_shoulder"][0] + kpd["r_shoulder"][0]) / 2)
    belt = np.isin(atr, (6, 8))
    rows_belt = np.where(belt[:, int(min(kpd["l_shoulder"][0], kpd["r_shoulder"][0])):int(max(kpd["l_shoulder"][0], kpd["r_shoulder"][0]))].any(axis=1))[0]
    waist_top = int(rows_belt.min())
    return list(range(int(sh_y + 0.6 * (waist_top - sh_y)), waist_top - 5, 8)), cx


def lower_waist(img: np.ndarray, rows: list[int], cx: int) -> float | None:
    """Mean torso width (ATR torso labels, the run through the centre column, arms excluded) over the love-handle rows. Round 3 (2026-10-10): the
    single waist row read +1.2% and the AI 'narrower' while these rows were 3-7% wider, what the user had seen in round 1."""
    import segment
    lab = segment.atr_labels(img)
    if lab.shape[:2] != img.shape[:2]:
        lab = cv2.resize(lab.astype(np.uint8), (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    torso = (lab == 11) | (lab == 4)
    widths = []
    for y in rows:
        xs = np.where(torso[y])[0]
        if not xs.size:
            continue
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        run = next((r for r in runs if r[0] <= cx <= r[-1]), None)
        if run is not None:
            widths.append(run[-1] - run[0] + 1)
    return float(np.mean(widths)) if widths else None


def warp_waist(photo: Path, pic: Path, out: Path, shrink: float = WAIST_SHRINK) -> int:
    """The one code change to a Gemini picture the user allowed (2026-10-10: "Since you're recommending it, let's go with the waist-only wrap on
    round 4"; it bends the 2026-09-20 rule 'AI renders, code only copies' for this change alone). In 4 rounds Gemini never narrowed his waist
    (love handles +1.8, -1.6, +3.1, +2.5%), even inside a grey outline drawn 6% narrower. Here only the waist outline moves in: on the love-handle
    rows each side's edge goes in by shrink/2 of the row's width (ramping in from below the chest, as make_target), the strip of background between
    the edge and his forearm is stretched to follow (never past the arm), and the torso between the two edges is compressed to fit; rows above,
    the arms, the trousers and everything else keep every pixel."""
    import segment
    img = cv2.imread(str(pic))
    H, W = img.shape[:2]
    m, raw, atr0 = _reading(photo)
    kpd = raw["body_raw"]["person"]["kp"]
    sh_y = (kpd["l_shoulder"][1] + kpd["r_shoulder"][1]) / 2
    cx = (kpd["l_shoulder"][0] + kpd["r_shoulder"][0]) / 2
    belt0 = np.isin(atr0, (6, 8))
    waist_top = int(np.where(belt0[:, int(min(kpd["l_shoulder"][0], kpd["r_shoulder"][0])):int(max(kpd["l_shoulder"][0], kpd["r_shoulder"][0]))].any(axis=1))[0].min())
    lab = segment.atr_labels(img)
    if lab.shape[:2] != (H, W):
        lab = cv2.resize(lab.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
    torso, arm = (lab == 11) | (lab == 4), np.isin(lab, (14, 15))
    y_a, y_b = sh_y + 0.45 * (waist_top - sh_y), sh_y + 0.75 * (waist_top - sh_y)
    rows = np.arange(int(y_a), waist_top)
    L, R, GL, GR = (np.full(len(rows), np.nan) for _ in range(4))
    ic = int(cx)
    for i, y in enumerate(rows):
        xs = np.where(torso[y])[0]
        if not xs.size:
            continue
        runs = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
        run = next((r for r in runs if r[0] <= ic <= r[-1]), None)
        if run is None:
            continue
        L[i], R[i] = run[0], run[-1]
        al = np.where(arm[y, :run[0]])[0]                         # the forearm's inner edge left of the waist
        ar = np.where(arm[y, run[-1] + 1:])[0]
        GL[i] = run[0] - (al.max() if al.size else run[0] - 80)
        GR[i] = (ar.min() + 1 if ar.size else 80)
    ok = ~np.isnan(L)
    if ok.sum() < 10:
        print("waist edges not found")
        return 1
    def smooth(v):
        """Gaps filled, then a running median (9 rows) and a Gaussian (sigma 6 rows) along the waist, so the edge cannot jitter row to row."""
        v = v.copy(); v[~ok] = np.interp(np.where(~ok)[0], np.where(ok)[0], v[ok])
        p = np.pad(v, 4, mode="edge")
        v = np.median(np.lib.stride_tricks.sliding_window_view(p, 9), axis=1)
        return cv2.GaussianBlur(v.reshape(-1, 1).astype(np.float64), (1, 0), 6, borderType=cv2.BORDER_REPLICATE).ravel()
    L, R, GL, GR = smooth(L), smooth(R), smooth(GL), smooth(GR)
    ramp = np.clip((rows - y_a) / max(1.0, y_b - y_a), 0, 1)
    tail = np.clip((waist_top - rows) / 12.0, 0, 1)               # the last rows ease out into the waistband
    d = 0.5 * shrink * (R - L) * ramp * tail
    map_x = np.tile(np.arange(W, dtype=np.float32), (H, 1))
    map_y = np.tile(np.arange(H, dtype=np.float32)[:, None], (1, W))
    for i, y in enumerate(rows):
        di = float(d[i])
        if di < 0.5:
            continue
        l, r = float(L[i]), float(R[i])
        rl, rr = max(4.0, min(60.0, 0.8 * float(GL[i]))), max(4.0, min(60.0, 0.8 * float(GR[i])))
        nl, nr = l + di, r - di                                    # the new edges
        x = np.arange(W, dtype=np.float32)
        src = x.copy()
        a0 = l - rl                                                # left: background [l-rl, nl] <- [l-rl, l]; torso [nl, cx] <- [l, cx]
        sel = (x >= a0) & (x < nl)
        src[sel] = a0 + (x[sel] - a0) * (rl / (rl + di))
        sel = (x >= nl) & (x <= cx)
        src[sel] = l + (x[sel] - nl) * ((cx - l) / max(1.0, cx - nl))
        b0 = r + rr                                                # right: torso [cx, nr] <- [cx, r]; background [nr, r+rr] <- [r, r+rr]
        sel = (x >= cx) & (x <= nr)
        src[sel] = cx + (x[sel] - cx) * ((r - cx) / max(1.0, nr - cx))
        sel = (x > nr) & (x <= b0)
        src[sel] = r + (x[sel] - nr) * (rr / (rr + di))
        map_x[y] = src
    outimg = cv2.remap(img, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    cv2.imwrite(str(out), outimg, [cv2.IMWRITE_JPEG_QUALITY, 95])
    moved = np.abs(map_x - np.arange(W, dtype=np.float32)[None, :]) > 0.25
    print(json.dumps({"out": str(out), "rows": [int(rows[0]), int(rows[-1])], "max_inward_px_per_side": round(float(d.max()), 1),
                      "pixels_moved": int(moved.sum()), "shrink": shrink}))
    return 0


def warp_shoulders(photo: Path, pic: Path, out: Path, grow: float = 0.025) -> int:
    """The user, 2026-10-10, on the approved back: "yes very slightly increase shoulder breadth" (Gemini kept his shoulder width: shoulder/hip
    +0.2% against the plan's +2..+5%). Like warp_waist, only the outline moves: on the shoulder-cap rows each side's outer edge goes out by grow/2
    of the row's width, peaking just below the shoulder line and fading to nothing at the top of the shoulders and at the armpits; the strip of
    background beside the edge is compressed to make room (it never reaches into his head, hair or anything that is not background) and the body
    between the edge and his spine is stretched to match. Rows outside the shoulder band keep every pixel."""
    import segment
    img = cv2.imread(str(pic))
    H, W = img.shape[:2]
    m, raw, atr0 = _reading(photo)
    kpd = raw["body_raw"]["person"]["kp"]
    sh_l, sh_r = np.array(kpd["l_shoulder"][:2], float), np.array(kpd["r_shoulder"][:2], float)
    sh_y, sw, cx = (sh_l[1] + sh_r[1]) / 2, float(abs(sh_r[0] - sh_l[0])), (sh_l[0] + sh_r[0]) / 2
    lab = segment.atr_labels(img)
    if lab.shape[:2] != (H, W):
        lab = cv2.resize(lab.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
    body = np.isin(lab, (4, 11, 14, 15))
    y_top, y_peak, y_end = sh_y - 0.20 * sw, sh_y + 0.10 * sw, sh_y + 0.45 * sw
    rows = np.arange(int(y_top), int(y_end))
    Ls, Rs, BL, BR = (np.full(len(rows), np.nan) for _ in range(4))
    for i, y in enumerate(rows):
        xs = np.where(body[y])[0]
        if not xs.size:
            continue
        Ls[i], Rs[i] = xs.min(), xs.max()
        bg = lab[y] == 0                                           # how much plain background lies beyond each edge
        l = int(xs.min()); k = 0
        while l - k - 1 >= 0 and bg[l - k - 1] and k < 80:
            k += 1
        BL[i] = k
        r = int(xs.max()); k = 0
        while r + k + 1 < W and bg[r + k + 1] and k < 80:
            k += 1
        BR[i] = k
    ok = ~np.isnan(Ls)
    if ok.sum() < 10:
        print("shoulder edges not found")
        return 1

    def smooth(v):
        v = v.copy(); v[~ok] = np.interp(np.where(~ok)[0], np.where(ok)[0], v[ok])
        p = np.pad(v, 4, mode="edge")
        v = np.median(np.lib.stride_tricks.sliding_window_view(p, 9), axis=1)
        return cv2.GaussianBlur(v.reshape(-1, 1).astype(np.float64), (1, 0), 6, borderType=cv2.BORDER_REPLICATE).ravel()
    Ls, Rs = smooth(Ls), smooth(Rs)
    BL, BR = np.nan_to_num(BL, nan=0.0), np.nan_to_num(BR, nan=0.0)
    bump = np.where(rows < y_peak, (rows - y_top) / max(1.0, y_peak - y_top), (y_end - rows) / max(1.0, y_end - y_peak))
    bump = np.clip(bump, 0, 1) ** 1.5
    d = 0.5 * grow * (Rs - Ls) * bump
    map_x = np.tile(np.arange(W, dtype=np.float32), (H, 1))
    map_y = np.tile(np.arange(H, dtype=np.float32)[:, None], (1, W))
    x = np.arange(W, dtype=np.float32)
    for i, y in enumerate(rows):
        l, r = float(Ls[i]), float(Rs[i])
        dl = min(float(d[i]), 0.6 * float(BL[i]))                  # never push the edge further than the plain background beside it
        dr = min(float(d[i]), 0.6 * float(BR[i]))
        if dl < 0.5 and dr < 0.5:
            continue
        src = x.copy()
        rl, rr = float(BL[i]), float(BR[i])                        # left: background [l-rl, l-dl] <- [l-rl, l]; body [l-dl, cx] <- [l, cx]
        if dl >= 0.5:
            a0 = l - rl
            sel = (x >= a0) & (x < l - dl)
            src[sel] = a0 + (x[sel] - a0) * (rl / max(1.0, rl - dl))
            sel = (x >= l - dl) & (x <= cx)
            src[sel] = l + (x[sel] - (l - dl)) * ((cx - l) / max(1.0, cx - (l - dl)))
        if dr >= 0.5:
            b0 = r + rr
            sel = (x >= cx) & (x <= r + dr)
            src[sel] = cx + (x[sel] - cx) * ((r - cx) / max(1.0, (r + dr) - cx))
            sel = (x > r + dr) & (x <= b0)                         # right: background [r+dr, r+rr] <- [r, r+rr]
            src[sel] = r + (x[sel] - (r + dr)) * (rr / max(1.0, rr - dr))
        map_x[y] = src
    outimg = cv2.remap(img, map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    cv2.imwrite(str(out), outimg, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(json.dumps({"out": str(out), "rows": [int(rows[0]), int(rows[-1])], "max_outward_px_per_side": round(float(d.max()), 1), "grow": grow}))
    return 0


def measure_cmd(photo: Path, pics: list[Path]) -> int:
    import character
    rows, cx = lower_waist_rows(photo)
    lw_base = lower_waist(character.load(photo), rows, cx)
    base = character.measure(photo)["body"]

    def vals(b: dict) -> dict:
        arms = b.get("arms") or {}
        aw = [arms[s]["width_px"] for s in ("l", "r") if (arms.get(s) or {}).get("measured")]
        return {"waist_px": b.get("waist_px"), "bideltoid_px": b.get("bideltoid_px"), "sw_px": b.get("sw_px"),
                "arm_mean": float(np.mean(aw)) if aw else None}
    bv = vals(base)
    print(f"{'picture':48s} " + " ".join(f"{k:>14s}" for k in TARGETS) + "   verdict")
    print(f"{'BASE ' + photo.name:48s} " + " ".join(f"{(bv[k] or 0):14.1f}" for k in TARGETS))
    for p in pics:
        b = character.measure(p)["body"]
        v = vals(b)
        row, ok = [], True
        for k, (lo, hi) in TARGETS.items():
            if v[k] is None or not bv[k]:
                row.append(f"{'n/a':>14s}"); ok = False
                continue
            d = (v[k] - bv[k]) / bv[k] * 100
            inside = lo <= d <= hi
            ok &= inside
            row.append(f"{d:+12.1f}%{' ' if inside else '!'}")
        lw = lower_waist(cv2.imread(str(p)), rows, cx)
        if lw and lw_base:
            dl = (lw - lw_base) / lw_base * 100
            inside = TARGETS["waist_px"][0] <= dl <= TARGETS["waist_px"][1]
            ok &= inside
            row.append(f"   love handles {dl:+.1f}%{'' if inside else '!'}")
        print(f"{p.parent.name[-20:] + '/' + p.name:48s} " + " ".join(row) + ("   IN the targets" if ok else "   outside (! = missed)"))
    print("targets: " + ", ".join(f"{k} {lo:+g}..{hi:+g}%" for k, (lo, hi) in TARGETS.items()) + "; love handles (mean torso width over the "
          f"love-handle rows) {TARGETS['waist_px'][0]:+g}..{TARGETS['waist_px'][1]:+g}%")
    return 0


def ai_compare(photo: Path, pics: list[Path], box: list[int]) -> int:
    """BODY_MATCH_PROMPT on the same crop (box: x0, y0, x1, y1 of the photo) of the base and of each picture; answers in .cache/physique_match/."""
    import asyncio
    from datetime import datetime
    import character
    import replicate as RP
    from facecard import load_config
    from session import authenticated_client
    x0, y0, x1, y1 = box
    d = ROOT / ".cache" / "physique_match" / datetime.now().strftime("%Y%m%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=True)

    def crop_to(src: Path, dst: Path) -> Path:
        im = character.load(src)[y0:y1, x0:x1]
        s = 1024 / max(im.shape[:2])
        cv2.imwrite(str(dst), cv2.resize(im, (round(im.shape[1] * s), round(im.shape[0] * s)), interpolation=cv2.INTER_AREA),
                    [cv2.IMWRITE_JPEG_QUALITY, 94])
        return dst
    base = crop_to(photo, d / "base.jpg")
    cfg = load_config()
    models = [m for m in dict.fromkeys([cfg.get("vision_model"), "56fdd199312815e2"]) if m]
    log = RP.RunLog(d, {"base": str(photo), "pictures": [str(p) for p in pics], "box": box})

    async def go():
        out = {}
        async with authenticated_client(verbose=False) as client:
            for k, p in enumerate(pics):
                out[str(p)] = await RP.gemini_text(client, models, BODY_MATCH_PROMPT, [base, crop_to(p, d / f"pic{k + 1}.jpg")], log, "body match")
        return out
    res = asyncio.run(go())
    (d / "ai.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("\nAI, part by part against the base photo:")
    for p, r in res.items():
        name = Path(p).parent.name[-20:] + "/" + Path(p).name
        if not r:
            print(f"  {name}: no usable answer")
            continue
        parts = " ".join(f"{k}={r.get(k)}" for k in ("waist", "lower_belly", "love_handles", "abs", "obliques", "chest", "deltoids", "arm_size",
                                                     "biceps_vein", "forearm_veins", "janeu", "chain"))
        print(f"  {name}: {parts} | natural {r.get('natural')} | {r.get('biggest')}")
    print(f"-> {d / 'ai.json'}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["warp-shoulders"] and len(a) in (4, 6):            # warp-shoulders <photo> <picture> <out> [--grow 0.025]
        sys.exit(warp_shoulders(Path(a[1]), Path(a[2]), Path(a[3]), float(a[5]) if len(a) == 6 else 0.025))
    if a[:1] == ["warp-waist"] and len(a) in (4, 6):                # warp-waist <photo> <picture> <out> [--shrink 0.06]
        sys.exit(warp_waist(Path(a[1]), Path(a[2]), Path(a[3]), float(a[5]) if len(a) == 6 else WAIST_SHRINK))
    if a[:1] == ["make-target"] and len(a) in (3, 4):            # make-target <photo> <out dir> [--back]
        sys.exit(make_target(Path(a[1]), Path(a[2]), back=a[3:] == ["--back"]))
    if a[:1] == ["make"] and len(a) in (3, 5):
        sys.exit(make(Path(a[1]), Path(a[2]), a[4] if len(a) == 5 and a[3] == "--arms-to" else "elbow"))
    if a[:1] == ["measure"] and len(a) >= 3:
        ai = "--ai" in a
        if ai:                                   # --ai <crop .json>: the region-edit crop's box is the comparison crop
            j = a[a.index("--ai") + 1]
            a = a[:a.index("--ai")] + a[a.index("--ai") + 2:]
        rc = measure_cmd(Path(a[1]), [Path(x) for x in a[2:]])
        if ai:
            rc = rc or ai_compare(Path(a[1]), [Path(x) for x in a[2:]], json.loads(Path(j).read_text(encoding="utf-8"))["box"])
        sys.exit(rc)
    print(__doc__)
    sys.exit(1)
