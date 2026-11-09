"""Paste-back compositing for replicate mode.

Gemini edits a CROP of the source photo. This module aligns that edit back onto the source crop, matches
its exposure, and writes only the masked zone into the FULL-RESOLUTION original. Every pixel outside the
zone is copied from the source, so background, clothes and body outside the zone are identical by
construction; verify_outside() asserts that instead of trusting it.

Crops are rectangles (x0, y0, w, h) clamped inside the image: no reflected padding is ever sent to Gemini.
"""

from __future__ import annotations

import cv2
import numpy as np

from segment import clean

Rect = tuple[int, int, int, int]


def rect_crop(shape: tuple[int, ...], cx: float, cy: float, w: float, h: float) -> Rect:
    """Rectangle of about w x h centred on (cx, cy), shifted/shrunk to lie inside an image of `shape`."""
    H, W = shape[:2]
    w, h = min(int(round(w)), W), min(int(round(h)), H)
    x0 = int(round(cx - w / 2))
    y0 = int(round(cy - h / 2))
    return max(0, min(W - w, x0)), max(0, min(H - h, y0)), w, h


def take(img: np.ndarray, rect: Rect) -> np.ndarray:
    x0, y0, w, h = rect
    return img[y0:y0 + h, x0:x0 + w]


def place(mask_crop: np.ndarray, rect: Rect, shape: tuple[int, ...]) -> np.ndarray:
    """Put a crop-space mask back into a full-frame mask (zero outside the crop)."""
    x0, y0, w, h = rect
    out = np.zeros(shape[:2], np.uint8)
    out[y0:y0 + h, x0:x0 + w] = mask_crop
    return out


def _gray_small(img: np.ndarray, max_side: int = 512) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    s = min(1.0, max_side / max(h, w))
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if s < 1.0:
        g = cv2.resize(g, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(g, (5, 5), 0).astype(np.float32), s


def align_ecc(src_crop: np.ndarray, edit: np.ndarray, zone_crop: np.ndarray, exclude_px: int) -> tuple[np.ndarray, float, np.ndarray]:
    """Warp `edit` into the frame of `src_crop` using only pixels OUTSIDE the zone.

    Returns (aligned_edit, ecc_correlation, warp_2x3). The edit is first resized to the crop size (Gemini
    returns its own resolution). ecc_correlation is 0.0 when alignment could not be computed.
    """
    h, w = src_crop.shape[:2]
    edit = cv2.resize(edit, (w, h), interpolation=cv2.INTER_CUBIC if edit.shape[0] < h else cv2.INTER_AREA)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (exclude_px * 2 + 1,) * 2)
    trusted = (cv2.dilate(zone_crop, k) == 0).astype(np.uint8) * 255
    if int((trusted > 0).sum()) < 0.05 * w * h:
        return edit, 0.0, np.eye(2, 3, dtype=np.float32)

    g_src, s = _gray_small(src_crop)
    g_edit, _ = _gray_small(edit)
    m_small = cv2.resize(trusted, (g_src.shape[1], g_src.shape[0]), interpolation=cv2.INTER_NEAREST)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(g_src, g_edit, warp, cv2.MOTION_AFFINE,
                                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), m_small, 5)
    except cv2.error:
        return edit, 0.0, np.eye(2, 3, dtype=np.float32)
    warp_full = warp.copy()
    warp_full[:, 2] /= s
    aligned = cv2.warpAffine(edit, warp_full, (w, h), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                             borderMode=cv2.BORDER_REPLICATE)
    return aligned, float(cc), warp_full


def warp_magnitude(warp: np.ndarray, size: tuple[int, int]) -> dict:
    """Scale and shift of an ECC warp, as fractions, to catch a diverged alignment."""
    a = warp[:, :2]
    scale = float(np.sqrt(abs(np.linalg.det(a))))
    shift = float(np.hypot(warp[0, 2], warp[1, 2]) / max(size))
    return {"scale": round(scale, 4), "shift_frac": round(shift, 4)}


def _lapvar(img: np.ndarray, mask: np.ndarray) -> float:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F)[mask > 0].var())


def match_sharpness(edit: np.ndarray, src: np.ndarray, zone: np.ndarray, target_ratio: float = 1.1) -> tuple[np.ndarray, float]:
    """Soften the edit so its high-frequency energy inside the zone is about that of the source photo.

    Gemini re-renders faces with far more fine detail than a typical phone photo of a small face, which looks pasted-on.
    Only ever softens (sigma >= 0). Returns (edit, sigma).
    """
    if int((zone > 0).sum()) < 500:
        return edit, 0.0
    target = target_ratio * _lapvar(src, zone)
    if _lapvar(edit, zone) <= target:
        return edit, 0.0
    lo, hi = 0.0, 4.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if _lapvar(cv2.GaussianBlur(edit, (0, 0), mid), zone) > target:
            lo = mid
        else:
            hi = mid
    return cv2.GaussianBlur(edit, (0, 0), hi), round(hi, 2)


def _noise_sigma(img: np.ndarray, mask: np.ndarray) -> float:
    """Immerkaer fast noise estimate (luminance) over the masked pixels; robust to most image structure."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    r = np.abs(cv2.filter2D(g, -1, k))
    m = cv2.erode((mask > 0).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    if int(m.sum()) < 200:
        return 0.0
    return float(np.sqrt(np.pi / 2.0) / 6.0 * r[m].mean())


def match_grain(edit: np.ndarray, src: np.ndarray, zone: np.ndarray, ring_px: int, seed: int = 0) -> tuple[np.ndarray, float]:
    """Add noise to the edit so its grain inside the zone matches the source photo's grain just outside it.

    Phone photos and downloaded reference images carry grain or compression noise; a re-rendered patch is much smoother
    and looks pasted on. Only ever adds noise. Returns (edit, added_sigma).
    """
    ring = ((cv2.dilate(zone, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ring_px * 4 + 1,) * 2)) > 0) & (zone == 0)).astype(np.uint8)
    target = _noise_sigma(src, ring)
    current = _noise_sigma(edit, zone)
    if target <= current + 0.4:
        return edit, 0.0
    add = float(np.sqrt(target ** 2 - current ** 2)) * 0.9
    rng = np.random.default_rng(seed)
    luma = rng.normal(0.0, add, edit.shape[:2]).astype(np.float32)[:, :, None]
    chroma = rng.normal(0.0, add * 0.35, edit.shape).astype(np.float32)
    return np.clip(edit.astype(np.float32) + luma + chroma, 0, 255).astype(np.uint8), round(add, 2)


def relight(edit: np.ndarray, src: np.ndarray, zone: np.ndarray, face_w: float, chroma: bool = True,
            strength: str = "normal") -> tuple[np.ndarray, dict]:
    """Carry the photo's own light onto the edited face: a smooth low-frequency correction field, not one global average.

    A single LAB mean/std match over the whole face cannot reproduce light that falls from one side or carries a colour
    cast (the stained-glass window lights one cheek yellow-green), so the pasted face reads as a flat sticker. Here the
    source and the edit are both blurred far below face-feature scale; their difference is what the LIGHT does, not what
    the identity is. Applying that difference relights the new face while leaving its own detail intact.

    The field is computed only where the zone is, then extended outward by blurring with the mask so the border matches
    too, and clamped so a bad estimate cannot invent light that is not there.
    """
    if int((zone > 0).sum()) < 400:
        return edit, {"relit": False, "reason": "zone too small"}
    sigma = max(4.0, face_w * 0.22)  # well above pores and features, below the scale of a lit cheek
    m = (zone > 0).astype(np.float32)
    m_blur = cv2.GaussianBlur(m, (0, 0), sigma) + 1e-6
    e_lab = cv2.cvtColor(edit, cv2.COLOR_BGR2LAB).astype(np.float32)
    s_lab = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    out = e_lab.copy()
    stats = {}
    for c in (0, 1, 2) if chroma else (0,):
        e_low = cv2.GaussianBlur(e_lab[..., c] * m, (0, 0), sigma) / m_blur
        s_low = cv2.GaussianBlur(s_lab[..., c] * m, (0, 0), sigma) / m_blur
        delta = s_low - e_low
        # A reflection in glass is far dimmer and more tinted than a re-rendered face, so its correction needs room:
        # with the normal clamp the stained-glass reflection sat at the limit in every channel and came back too bright.
        lim = (28.0 if c == 0 else 14.0) if strength == "normal" else (70.0 if c == 0 else 35.0)
        delta = np.clip(delta, -lim, lim)
        stats[f"delta_{'Lab'[c]}"] = [round(float(delta[zone > 0].min()), 1), round(float(delta[zone > 0].max()), 1)]
        out[..., c] = e_lab[..., c] + delta
    return cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR), {"relit": True, "sigma": round(sigma, 1),
                                                                                       "strength": strength, **stats}


def match_exposure(edit: np.ndarray, src: np.ndarray, zone: np.ndarray, mode: str, ring_px: int) -> np.ndarray:
    """Match the edit to the source using a ring of unchanged pixels just outside the zone.

    mode "ring": match L, a, b mean/std (own photos: same skin, only the light differs).
    mode "luma": match only L mean/std, leaving chroma alone so the user's own skin tone is not pulled
                 toward the tone of the person who posed for a foreign source photo.
    mode "none": untouched.
    """
    if mode == "none":
        return edit
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ring_px * 2 + 1,) * 2)
    ring = (cv2.dilate(zone, k) > 0) & (zone == 0)
    if int(ring.sum()) < 200:
        return edit
    e = cv2.cvtColor(edit, cv2.COLOR_BGR2LAB).astype(np.float32)
    s = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    chans = range(3) if mode == "ring" else range(1)
    for c in chans:
        me, se = e[..., c][ring].mean(), e[..., c][ring].std() + 1e-3
        ms, ss = s[..., c][ring].mean(), s[..., c][ring].std() + 1e-3
        gain = float(np.clip(ss / se, 0.8, 1.25))
        e[..., c] = (e[..., c] - me) * gain + ms
    return cv2.cvtColor(np.clip(e, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def feather_alpha(zone: np.ndarray, feather_px: int) -> np.ndarray:
    """Soft alpha that is exactly 0 outside `zone` and reaches ~1 about `feather_px` inside its border."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (feather_px * 2 + 1,) * 2)
    inner = cv2.erode(zone, k)
    alpha = cv2.GaussianBlur(inner.astype(np.float32) / 255.0, (0, 0), max(1.0, feather_px / 2.0))
    alpha[zone == 0] = 0.0
    return np.clip(alpha, 0.0, 1.0)


def paste_back(base: np.ndarray, edit_aligned: np.ndarray, rect: Rect, zone_full: np.ndarray, feather_px: int,
               opacity: float = 1.0) -> np.ndarray:
    """Blend the aligned edit into a copy of the full-resolution base inside `zone_full` only.

    `opacity` below 1 keeps some of the original underneath, which is what a reflection needs: it stays a reflection
    instead of becoming a second crisp face in the glass.
    """
    x0, y0, w, h = rect
    zone_roi = zone_full[y0:y0 + h, x0:x0 + w]
    alpha = feather_alpha(zone_roi, feather_px)[:, :, None] * float(np.clip(opacity, 0.0, 1.0))
    out = base.copy()
    b = base[y0:y0 + h, x0:x0 + w].astype(np.float32)
    out[y0:y0 + h, x0:x0 + w] = np.clip(b * (1.0 - alpha) + edit_aligned.astype(np.float32) * alpha, 0, 255).astype(np.uint8)
    return out


def paste_rect_soft(base: np.ndarray, edit_aligned: np.ndarray, rect: Rect, border_frac: float = 0.10,
                    holes: list[tuple[float, float, float]] | None = None,
                    valid: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Paste a whole edited crop back with a wide soft border at the rectangle edge. Returns (image, zone mask).

    Round 3 principle: the model rendered the crop as one coherent piece (face, hair, neck, collar, light), so the
    seam belongs at the crop edge in low-detail areas, not along the jaw. Nothing inside is altered; the alpha only
    ramps from 0 at the edge to 1 `border_frac` of the way in. Pixels outside the rectangle are untouched.

    `holes` are (cx, cy, radius) discs in crop coordinates that keep the SOURCE: used only for Gemini's sparkle
    watermark, a fixed non-content overlay 120 px in from the bottom-right corner of every returned image.
    `valid` (uint8, 255 where the aligned edit really has content) keeps a large alignment warp from pasting the
    edge pixels it had to invent: the paste fades out inside the valid area instead.
    """
    x0, y0, w, h = rect
    bw, bh = max(2, int(w * border_frac)), max(2, int(h * border_frac))
    ramp_x = np.minimum(np.arange(w) / bw, (w - 1 - np.arange(w)) / bw)
    ramp_y = np.minimum(np.arange(h) / bh, (h - 1 - np.arange(h)) / bh)
    alpha = np.clip(np.minimum(ramp_y[:, None], ramp_x[None, :]), 0.0, 1.0)
    alpha = alpha * alpha * (3 - 2 * alpha)  # smoothstep, no visible ramp edge
    if valid is not None:
        dist = cv2.distanceTransform((valid > 0).astype(np.uint8), cv2.DIST_L2, 3)
        ramp = np.clip(dist / float(max(bw, bh)), 0.0, 1.0)
        alpha = alpha * (ramp * ramp * (3 - 2 * ramp))
    for (cx, cy, r) in holes or []:
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        soft = np.clip((d - r) / max(2.0, 0.3 * r), 0.0, 1.0)  # 0 inside the disc, ramps back to 1 just outside it
        alpha = alpha * soft
    out = base.copy()
    b = base[y0:y0 + h, x0:x0 + w].astype(np.float32)
    e = edit_aligned.astype(np.float32)
    out[y0:y0 + h, x0:x0 + w] = np.clip(b * (1.0 - alpha[:, :, None]) + e * alpha[:, :, None], 0, 255).astype(np.uint8)
    zone = np.zeros(base.shape[:2], np.uint8)
    zone[y0:y0 + h, x0:x0 + w] = (alpha > 0).astype(np.uint8) * 255
    return out, zone


def inside_drift(src: np.ndarray, out: np.ndarray, rect: Rect, head_boxes: list[Rect], margin_frac: float = 0.35) -> dict:
    """How much changed inside the crop but away from the heads: clothes and background must not be redrawn.

    Compares the source and output crops on the pixels outside every head box (grown by `margin_frac` so hair and
    neck do not count), at half resolution to ignore resampling noise. Returns mean absolute difference (0-255) and
    a structural similarity on luminance.
    """
    a, b = take(src, rect), take(out, rect)
    h, w = a.shape[:2]
    keep = np.ones((h, w), bool)
    for (hx, hy, hw, hh) in head_boxes:
        m = int(max(hw, hh) * margin_frac)
        x1, y1 = max(0, hx - rect[0] - m), max(0, hy - rect[1] - m)
        x2, y2 = min(w, hx - rect[0] + hw + m), min(h, hy - rect[1] + hh + m)
        keep[y1:y2, x1:x2] = False
    if int(keep.sum()) < 200:
        return {"pixels": int(keep.sum()), "mean_abs_diff": None, "ssim": None}
    ga = cv2.cvtColor(cv2.resize(a, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = cv2.resize(keep.astype(np.uint8), (w // 2, h // 2), interpolation=cv2.INTER_NEAREST) > 0
    mad = float(np.abs(ga - gb)[k].mean())
    mu_a, mu_b = cv2.GaussianBlur(ga, (0, 0), 3), cv2.GaussianBlur(gb, (0, 0), 3)
    va = cv2.GaussianBlur(ga * ga, (0, 0), 3) - mu_a * mu_a
    vb = cv2.GaussianBlur(gb * gb, (0, 0), 3) - mu_b * mu_b
    cov = cv2.GaussianBlur(ga * gb, (0, 0), 3) - mu_a * mu_b
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    return {"pixels": int(keep.sum()), "mean_abs_diff": round(mad, 2), "ssim": round(float(ssim[k].mean()), 3)}


def face_light(img: np.ndarray, box: tuple[int, int, int, int]) -> dict:
    """Mean lightness and colour of the central face area, in LAB (L 0-100). A measurement, never applied to pixels."""
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    rw, rh = max(2, int(w * 0.32)), max(2, int(h * 0.32))
    roi = img[max(0, cy - rh):cy + rh, max(0, cx - rw):cx + rw]
    lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).astype(np.float32)
    return {"L": float(lab[..., 0].mean() * 100 / 255), "a": float(lab[..., 1].mean() - 128), "b": float(lab[..., 2].mean() - 128)}


def light_delta(src: np.ndarray, out: np.ndarray, box: tuple[int, int, int, int]) -> dict:
    """How far the output face's light and colour are from the source face's: dL (+ = brighter), da, db, and the colour
    distance dE. Gemini tends to render faces brighter and cleaner than a dim phone photo; measured 2026-09-20 on the
    user's own judgements (outputs he called fine: dE 12.2 and 5.5, the one he called worse: 16.5)."""
    a, b = face_light(src, box), face_light(out, box)
    dl, da, db = b["L"] - a["L"], b["a"] - a["a"], b["b"] - a["b"]
    return {"dL": round(dl, 1), "da": round(da, 1), "db": round(db, 1), "dE": round(float(np.sqrt(dl * dl + da * da + db * db)), 1)}


def verify_outside(base: np.ndarray, out: np.ndarray, zone_full: np.ndarray) -> dict:
    """Count pixels that changed outside the zone. Must be zero."""
    if base.shape != out.shape:
        return {"same_size": False, "changed_outside": -1, "changed_inside": -1, "zone_px": int((zone_full > 0).sum())}
    diff = np.any(base != out, axis=2)
    inside = zone_full > 0
    return {"same_size": True, "changed_outside": int((diff & ~inside).sum()), "changed_inside": int((diff & inside).sum()),
            "zone_px": int(inside.sum())}


def component_at(mask: np.ndarray, pt: tuple[int, int]) -> np.ndarray:
    """Keep only the connected component containing `pt` (falls back to the largest), then fill holes."""
    n, cc = cv2.connectedComponents((mask > 0).astype(np.uint8))
    px, py = min(mask.shape[1] - 1, max(0, pt[0])), min(mask.shape[0] - 1, max(0, pt[1]))
    lab = cc[py, px]
    if lab == 0:
        if n <= 1:
            return mask
        counts = np.bincount(cc.ravel())[1:]
        lab = 1 + int(np.argmax(counts))
    comp = ((cc == lab) * 255).astype(np.uint8)
    n2, cc2 = cv2.connectedComponents((comp == 0).astype(np.uint8))
    border = set(np.unique(np.concatenate([cc2[0, :], cc2[-1, :], cc2[:, 0], cc2[:, -1]])))
    holes = np.zeros_like(comp)
    for i in range(1, n2):
        if i not in border:
            holes[cc2 == i] = 255
    return np.maximum(comp, holes)


def build_face_zone(parts: dict[str, np.ndarray], face_box: tuple[int, int, int, int]) -> np.ndarray:
    """Facial-feature zone: skin (beard included), brows, eyes, nose, mouth, glasses. Excludes hair, ears, neck."""
    x, y, w, h = face_box
    fs = max(w, h)
    z = np.zeros_like(parts["skin"])
    for k in ("skin", "brows", "eyes", "nose", "mouth", "glasses_b", "glasses_a"):
        z = np.maximum(z, parts[k])
    z = clean(z, close=max(3, int(fs * 0.06)) | 1, dilate=max(3, int(fs * 0.02)) | 1)
    return component_at(z, (x + w // 2, y + h // 2))


def build_head_zone(parts: dict[str, np.ndarray], face_box: tuple[int, int, int, int]) -> np.ndarray:
    """Whole-head zone: face zone plus hair, ears and neck."""
    x, y, w, h = face_box
    fs = max(w, h)
    z = build_face_zone(parts, face_box)
    for k in ("hair_a", "ears", "neck_b"):
        z = np.maximum(z, parts[k])
    z = clean(z, close=max(3, int(fs * 0.08)) | 1, dilate=max(3, int(fs * 0.02)) | 1)
    return component_at(z, (x + w // 2, y + h // 2))
