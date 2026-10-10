"""replicate: put the user's identity into a source photo by EDITING a crop and pasting it back.

Round 3 principle (2026-09-20): the AI does all the visual work and all the scene reading; deterministic code only
copies pixels that must not change, measures, and retries. Nothing Gemini renders is altered by a heuristic.

    .venv\\Scripts\\python.exe facecard.py replicate --scene photo.jpg
        [--zone auto|face|head|head+build] [--source auto|own|foreign] [--glasses same|yes|no]
        [--look any|curly|short] [--count 2] [--max-attempts 6] [--force]

What happens:
  1. A crop around the head (and any other copy of the face in the frame, such as a window reflection) is cut from the
     full-resolution source.
  2. Gemini (text call) describes that crop: head turn and tilt, gaze, expression, glasses, hair, light, reflection.
  3. Gemini (image call) edits the crop, with that description in the prompt, so it keeps all of it and swaps identity.
  4. The WHOLE returned crop is pasted back with a wide soft border at the crop edge. Face, hair, neck, collar and
     light were rendered together, so they agree with each other. Pixels outside the crop rectangle are identical to
     the source, and that is asserted on the saved PNG.
  5. Gemini (text call) judges source crop vs output crop: same head angle, glasses kept, seam or lighting mismatch,
     anything else changed. Deterministic checks measure identity score, head size and position, and drift.
  6. A candidate that fails a gate is retried, up to --max-attempts, until --count candidates pass.

Zones:  face        the prompt asks for a new face and keeps the hair
        head        the prompt asks for a new face and hair
        head+build  opt-in: the whole person is reshaped first (measured 2026-09-20: Gemini keeps the silhouette within
                    2 percent, so this rarely changes the body), then the head is replaced
        auto        own photo -> face, someone else -> head

Measured to make results WORSE and therefore removed from the paste path (functions remain in composite.py, unused):
relighting the face from a blurred field, grain matching, sharpness softening, landmark similarity warps, opacity tricks,
cutting the face out along a BiSeNet/ATR mask. See skills/gemini-identity-gen/SKILL.md.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

import composite
import identity
import segment
from gemini_webapi.exceptions import APIError, GeminiError, ImageGenerationError, UsageLimitExceededError
from scorer import DETECTOR_PATH, ArcFaceScorer, analyze_face
from session import AuthError, CreditMeter, authenticated_client, describe_usage

ROOT = Path(__file__).parent
REFCROPS = ROOT / ".cache" / "refcrops"
# Used until the user approves numbers for facecard.json ("identity_thresholds"). From calibrate.py, 2026-09-20:
# genuine photos of the user score 0.26-0.88 against each other, outputs he called good 0.53-0.68, ones he called bad
# 0.23-0.58, a different man 0.11. So only the extremes are decidable; the middle needs his eye on the compare sheet.
PROPOSED_THRESHOLDS = {"hard_reject": 0.20, "accept": 0.52, "own_min": 0.40}
ASPECTS = [(1, 1), (3, 4), (4, 3), (2, 3), (3, 2), (9, 16), (16, 9)]  # ratios Gemini returns
SEND_PX = 1024          # long side of the crop sent to Gemini
UNION_MAX = 1.5         # a crop that must cover several faces may be this many SEND_PX wide before copies are dropped
# Alignment of the returned crop on its border ring, measured 2026-09-20: most returns land at scale 1.000 / shift < 0.003
# (ecc 0.99+); Gemini sometimes re-frames the crop by up to ~12 percent with the ring still matching at ecc 0.94-0.99
# (table-tennis photo), which is a registration problem, not a bad render, so a warp is applied and the pixels the warp
# had to invent are never pasted (composite.paste_rect_soft `valid`). A return that does not match the ring (ecc 0.53,
# scale 1.05, shift 0.30) or was re-framed by 20 percent or more is still rejected.
ECC_FAIL = 0.80
ALIGN_MAX_SCALE = 0.20
# Checked 2026-09-20 (table-tennis run 153036): two returns registered perfectly (ecc 1.000) at scale 0.799 and were rejected by this limit by
# 0.001, but once aligned they fail the size gate anyway (head 1.19x and 1.36x the source), so widening this limit gains nothing.
ALIGN_MAX_SHIFT = 0.30
ASPECT_TOL = 0.03
# Light on the face vs the source face. PROVISIONAL: calibrated on two of the user's own judgements (outputs he called
# fine measure dE 12.2 and 5.5, the one he called worse 16.5), so a candidate above this is retried, not proof of a defect.
LIGHT_DE_MAX = 14.0
# Another man's photo (his skin legitimately differs from the user's, so the limit is looser). PROVISIONAL, by the same rule as the own-photo limit:
# just above the brightest render the user accepted. cand3 (run 165702, "lighting all right") measured dE 18.4; the renders he called pasted or
# mismatched measured 31 to 35 (run 173847), and 3 of 4 hair-fix attempts (31 to 36) looked the same. Not a proof of a defect: it makes the retries
# fish for a render as dark and warm as the photo.
LIGHT_DE_MAX_FOREIGN = 20.0
ANCHOR_TURN_MAX = 65.0  # when Gemini reads the head as turned this many degrees or more, no frontal anchor references are sent
# Own photos: the limit was 0.85-1.15 until car2 (own mode, size 1.04, face 12 lightness units brighter than the source) was called "not proportional to
# the rest of the body and scene"; every output the user approved measures 0.959-1.018. PROVISIONAL, from that review. (1.03 was a slip: the approved
# value is 1.04, and 1.03 rejected car2 attempts 5 and 6, complete pictures with no other problem.)
SIZE_MIN, SIZE_MAX = 0.94, 1.04   # output head width over source head width (own photos)
# Foreign photos: the user called a head at size_ratio 1.054 (run 064235) "too big". PROVISIONAL, from that one review; Gemini returns heads
# anywhere from 0.87 to 1.21 of the source, so this only makes the retries fish for a matching size. A text judge cannot see head size
# (measured 2026-09-20: it read the too-big head as smaller, 43% vs 45% of shoulder width), so this is a geometric gate.
# The floor was 0.95 until cand3 (run 165702), whose size the user approved, measured 0.949 and was rejected by it; the floor has no evidence for "too small".
SIZE_MIN_FOREIGN, SIZE_MAX_FOREIGN = 0.94, 1.04
DEFAULT_ATTRACTIVENESS = ("Render him at his best, as he looks in the reference photos: a defined jawline, calm confident eyes, and a relaxed "
                          "closed-lip smile or a calm focused expression. Never tense, awkward, forced, smirking or caught mid-motion.")
SHIFT_MAX = 0.12                  # how far the head may move, in head widths
BORDER_FRAC = 0.10                # soft border width at the crop edge, as a fraction of the crop
# Gemini's sparkle watermark: a semi-transparent star centred 120 px in from the bottom-right corner of every returned
# image, about 48 px in radius (measured on six outputs of different sizes, 2026-09-20). It is never pasted.
SPARKLE_OFFSET, SPARKLE_RADIUS = 120.0, 52.0
# drift inside the crop but away from the heads (clothes and background must not be redrawn). Measured 2026-09-20:
# good returns 1.3-3.7 mean abs diff / SSIM 0.95-0.996; a return with the wrong framing 54.5 / 0.35.
DRIFT_MAD_MAX, DRIFT_SSIM_MIN = 10.0, 0.80
# Round 7 (2026-09-21), all PROVISIONAL, each from the user's reviews (FEEDBACK_LOG.md):
# unchanged: the face similarity to the SOURCE face (gt_sim) of everything the user approved is 0.23-0.75, of everything the user called "as it is" 0.93-0.99.
UNCHANGED_GT_SIM = 0.90
# neck gap: (face L minus neck L) of the output minus the same in the source, in Lab lightness. Approved outputs stay within +6.5; car2, called out of
# proportion with the scene, is +13.7. It is the measurable form of a head that looks pasted in.
NECK_GAP_MAX = 10.0
RESCUE_ATTEMPTS = 3      # placements of a good face into the complete picture (Pinterest 064221 needed 1; night out 042258 used 2 and needed more)
# his own photo whose source shows a laugh or a broad open smile keeps that expression (car.png, the user's best car2, kept the laugh; the run that
# replaced it with a closed smile was "not the same as the reference image at all", 2026-09-23). Matched on Gemini's own reading of the source.
LAUGH_WORDS = re.compile(r"\b(broad|laugh\w*|grin\w*|open[- ]mouth\w*)\b", re.I)
# ---- any angle, any distance (plan of 2026-09-23)
# Identity references are chosen by head pose as the AI reads it (turn and chin in degrees), because the landmark shape used before is unreliable on
# looking-down and close photos (rocky, table tennis, IMG_0862 read roll -145, -144, +164 degrees). Readings of the references are cached by file content.
REF_POSES = ROOT / ".cache" / "ref_poses.json"
SYN_DIR = ROOT / ".cache" / "synthetic_refs"
STUDIO_RE = re.compile(r"^IMG_68\d\d", re.I)   # the studio set: his best look (curls, no glasses)
STUDIO_BONUS = 15.0      # a studio photo within this many degrees of a closer non-studio one is preferred
SELF_MAX = 20.0          # his own photo stays among the references only when no other reference is this close in pose
SYN_MATCH = 15.0         # a rendered reference is kept only if its read pose is this close to the target
SYN_ID_MIN = 0.60        # ... and its identity against his photos at least this
FAR_FACE_PX = 130        # a source face narrower than this is far from the camera (table tennis 109 px; 142-227 px faces work)
FAR_MAX_UPSCALE = 1.5    # a far face's crop is widened so the image sent is upscaled at most this much, with shoulders and body for scale
# A far face much sharper than the photo reads as pasted in. PROVISIONAL, far faces only: every best version is 0.17-4.6x the source's sharpness, the
# far-face renders 7-60x; kayak P-06 (called perfect, 219 px face) is 8.3x, so the gate does not apply to faces of normal size.
SHARP_MAX = 6.0
POSE_PROMPT = (
    "Look at the man's head in this image. Reply with ONLY a JSON object, no other text, with these keys:\n"
    "turn: a number, the degrees his face is turned away from facing the camera: positive when his face points toward the right side of the "
    "picture, negative toward the left side, 0 when he faces the camera, about 90 or -90 in full profile\n"
    "chin: a number, the degrees his head is tilted: positive when he looks down with the chin lowered, negative when he looks up, 0 when level\n"
    "camera: above, level or below: where the camera is compared with his eyes\n"
    "face_share: a number between 0 and 1, the width of his face as a fraction of the image width")
# A close face (IMG_0862, 2026-09-23): the crop capped at 1.8x the face cut his hair off, Gemini zoomed out to draw the whole head with the hair the
# prompt asks for, and the re-framed return fused two heads. So the AI marks his whole head, hair included, on a wide look around the face, and a
# crop that cuts it is grown until the head sits HEAD_MARGIN inside every edge. A crop that already holds the whole head is left exactly as it was.
HEAD_MARGIN = 0.08       # of the crop side, kept free around the whole head when the crop has to grow (the soft paste border is 0.10)
HEAD_CUT_TOL = 0.02      # of the crop side: the AI's box may poke out this much before the crop counts as cutting the head
# An expression edit (zone expression, 2026-10-10): on his front photo IMG_6858 the whole head filled 84% of the crop height and Gemini zoomed out
# in all 8 returns (5 to scale 0.76, past the alignment limit; the other 3, once aligned, held the head 4-5% too big). Its own re-framed returns
# put the whole head at about 62-65% of the height with the hair top near 12%, so an expression crop is framed that way from the start.
EXPR_HEAD_SHARE = 0.62   # the whole head (the AI's box, hair included) as a fraction of the expression crop's side
EXPR_HEAD_TOP = 0.12     # the top of his hair, as a fraction of the side from the crop's top edge
TEXT_TIMEOUT = 150      # seconds per text call; a stalled answer stream (2026-09-23) otherwise waits forever
HEAD_BOX_PROMPT = (
    "Find the head of the man in the middle of this image. Reply with ONLY a JSON object, no other text: "
    "{\"box_2d\": [ymin, xmin, ymax, xmax]}, the tightest box around his whole head: from the top of his hair, across both sides of his hair "
    "and his ears, down to the bottom of his chin or beard. Coordinates are normalized to 0-1000 of the image height (y) and width (x).")
GEOMETRY_PROBLEMS = ("head size changed", "head moved", "were redrawn", "head angle changed", "clothes, body, hands or background changed",
                     "a seam or cut-out edge")


# ---------------------------------------------------------------------------------------------- helpers
def load_source(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def gate_values(config: dict) -> dict:
    """Light and head-size limits from facecard.json "gates" (approved by the user), falling back to the built-in defaults."""
    g = config.get("gates") or {}
    return {"light_de_max": float(g.get("light_de_max", LIGHT_DE_MAX)),
            "size_own": tuple(g.get("size_own", (SIZE_MIN, SIZE_MAX))),
            "size_foreign": tuple(g.get("size_foreign", (SIZE_MIN_FOREIGN, SIZE_MAX_FOREIGN))),
            "light_de_max_foreign": float(g.get("light_de_max_foreign", LIGHT_DE_MAX_FOREIGN)),
            "unchanged_gt_sim": float(g.get("unchanged_gt_sim", UNCHANGED_GT_SIM)),
            "neck_gap_max": float(g.get("neck_gap_max", NECK_GAP_MAX)),
            "rescue_attempts": int(g.get("rescue_attempts", RESCUE_ATTEMPTS)),
            "sharp_max": float(g.get("sharp_max", SHARP_MAX))}


def thresholds(config: dict) -> dict:
    t = config.get("identity_thresholds")
    if t:
        return {**PROPOSED_THRESHOLDS, **t, "approved": True}
    return {**PROPOSED_THRESHOLDS, "approved": False}


def fix_extension(path: Path) -> Path:
    with Image.open(path) as im:
        real = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(im.format, path.suffix)
    return path if real == path.suffix else path.rename(path.with_suffix(real))


def snap_aspect(rect: composite.Rect, shape: tuple[int, ...]) -> composite.Rect:
    """Grow the rectangle to the nearest aspect ratio Gemini returns, staying inside the image."""
    x0, y0, w, h = rect
    cx, cy = x0 + w / 2, y0 + h / 2
    target = min(ASPECTS, key=lambda a: abs(np.log((a[0] / a[1]) / (w / h))))
    r = target[0] / target[1]
    if w / h < r:
        w = h * r
    else:
        h = w / r
    return composite.rect_crop(shape, cx, cy, w, h)


def head_ref_crop(path: Path, scorer: ArcFaceScorer, side: int = 768) -> Path:
    """Head-and-shoulders crop of a reference photo, so the reference backgrounds and clothes do not bleed into the edit."""
    REFCROPS.mkdir(parents=True, exist_ok=True)
    out = REFCROPS / f"{path.stem}_head{side}_{int(path.stat().st_mtime)}.jpg"
    if out.exists():
        return out
    img = load_source(path)
    info = analyze_face(img)
    if not info["detected"]:
        raise RuntimeError(f"no face in reference {path.name}")
    x, y, w, h = info["box"]
    fs = max(w, h)
    rect = composite.rect_crop(img.shape, x + w / 2, y + h / 2 + fs * 0.1, fs * 3.0, fs * 3.0)
    crop = composite.take(img, rect)
    k = side / max(crop.shape[:2])
    crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out


def raw_head_crop(raw_path: Path, out_path: Path, side: int = 768) -> Path | None:
    """Head-and-shoulders crop of the largest face in a returned image, made exactly like the identity references. The placement attempt sends
    THIS, not the whole return, so the model can copy the face but not the framing or the pose of that attempt (night out 042258: a whole-return
    reference made the next attempt copy its upright pose). None when no face is found."""
    img = cv2.imread(str(raw_path))
    if img is None:
        return None
    faces = detect_faces(img)
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f["box"][2] * f["box"][3])["box"]
    fs = max(w, h)
    rect = composite.rect_crop(img.shape, x + w / 2, y + h / 2 + fs * 0.1, fs * 3.0, fs * 3.0)
    crop = composite.take(img, rect)
    k = side / max(crop.shape[:2])
    crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    cv2.imwrite(str(out_path), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out_path


def whole_ref(path: Path, max_dim: int = 1600) -> Path:
    REFCROPS.mkdir(parents=True, exist_ok=True)
    out = REFCROPS / f"{path.stem}_full{max_dim}_{int(path.stat().st_mtime)}.jpg"
    if out.exists():
        return out
    img = load_source(path)
    k = max_dim / max(img.shape[:2])
    if k < 1:
        img = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return out


def resized_for_send(img: np.ndarray, long_side: int = SEND_PX) -> np.ndarray:
    k = long_side / max(img.shape[:2])
    if abs(k - 1) < 0.02:
        return img
    return cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)


class RunLog:
    def __init__(self, run_dir: Path, data: dict):
        self.dir, self.data = run_dir, data
        self.log_path = run_dir / "run.log"
        self.save()

    def say(self, msg: str) -> None:
        print(msg, flush=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def save(self) -> None:
        tmp = self.dir / "run.json.tmp"
        tmp.write_text(json.dumps(self.data, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.dir / "run.json")


# ---------------------------------------------------------------------------------------------- Gemini text (the AI reads and judges)
DESCRIBE_PROMPT = (
    "Look at this photo crop of a man. Reply with ONLY a JSON object, no other text, with these keys, each a short plain "
    "description:\n"
    "head_turn: which way his head is turned relative to the camera and by roughly how many degrees "
    "(for example: turned about 60 degrees to the left of the picture, close to profile)\n"
    "head_tilt: whether his chin is level, dropped or raised, and any sideways tilt\n"
    "gaze: where his eyes are looking\n"
    "expression: his mouth, eyes and brows\n"
    "glasses: none, or a short description of them\n"
    "hair: style, length and colour\n"
    "light: the direction of the main light on his face, its colour cast and how bright it is\n"
    "face_exposure: how dark or bright his face is compared with the rest of the picture (much darker, slightly darker, "
    "similar, brighter), and whether his skin looks smooth and clean or grainy and textured like a phone photo\n"
    "reflection_present: true or false, whether a reflection or second image of this same man is visible in glass or a mirror\n"
    "reflection_where: if so, where in the picture, otherwise an empty string\n"
    "other_people: true or false, whether anyone else is in the picture")

JUDGE_PROMPT = (
    "Image 1 is an original photo crop. Image 2 is an edited version of it in which ONLY the man's face and head identity "
    "was supposed to change. Compare them and reply with ONLY a JSON object, no other text, with these keys:\n"
    "same_head_angle: true or false, whether his head is turned and tilted at the same angle in both\n"
    "same_expression: true or false, whether his expression is the same in both\n"
    "glasses_preserved: true or false. True if he wears glasses in BOTH images or in NEITHER. False only if glasses are present in one "
    "image and missing or newly added in the other. Small differences in the frame shape or the lens tint do NOT count.\n"
    "jaw_clean: true or false, whether his jaw, chin and neck in image 2 look as clean as in image 1, with no extra fold, double "
    "chin or bulge under the chin that image 1 does not have\n"
    "double_image: true or false, whether image 2 shows any ghosting, a duplicate or overlapping face, a doubled ear, or an outline "
    "of a second head (do not count a genuine reflection in glass that image 1 also has)\n"
    "seam_visible: true or false, whether any cut-out edge, halo, patch or mismatch between his face and his hair, neck, "
    "collar or the background is visible in image 2\n"
    "lighting_consistent: true or false, whether the light on his face in image 2 matches the light on the rest of the "
    "picture in direction, colour and brightness\n"
    "anything_else_changed: true or false, whether clothes, body, hands, pose or background differ between the two\n"
    "reflection_matches: true or false, true if a reflection of him in glass shows the same man as his real face in "
    "image 2 (the same beard, glasses and face structure, allowing for the softness of a reflection), or if there is no "
    "reflection\n"
    "notes: one short sentence naming the single biggest problem, or 'none'")

# Pairwise comparison of two renderings of the same photo. Measured 2026-09-20: asked to RATE one image the judge gave the user's "awkward" and
# "perfect emotion" kayak outputs the same 6/10; asked to COMPARE the two, in both orders, it picked the one the user preferred 4 of 4 times.
# Round 7 widens the question from the expression to the whole face, with the user's own criteria from every review (FEEDBACK_LOG.md).
FACE_PAIR_PROMPT = (
    "Both images are the same photo of the same man, with two different renderings of his face and head. Which image is the better photograph of "
    "him: the more attractive AND the more natural one, like a flattering candid photo that a real camera took? Judge: calm confident eyes; a "
    "defined jawline; a relaxed closed-lip smile or a slight smile with soft eyes, never tense, awkward, forced or smirking; natural full hair; "
    "skin lit exactly like his neck, hands and the rest of the picture (not brighter, paler or cleaner than the scene); a head and face in "
    "proportion with his body; and no sign that the head was pasted in. Reply with ONLY a JSON object: "
    "{\"better\": 1 or 2, \"why\": one short sentence}")

# The user, 2026-10-10: "smile always is turning out bad ... when captured in candid it can look different". FACE_PAIR_PROMPT rewards a
# closed-lip smile and calls any smirk a fault, so an open smile with teeth always lost; ranking smile candidates asks about the smile itself.
SMILE_PAIR_PROMPT = (
    "Both images are the same photo of the same man, with two different renderings of his smile. Which image shows the better smile of HIM: "
    "a genuine candid smile, the kind a friend's camera catches when he is really amused, with the cheeks lifted, the eyes crinkled and alive, "
    "the upper teeth showing naturally (his own teeth exactly as they are: their shape, size and colour), relaxed lips and no forced grin or "
    "squint that closes the eyes, while his face stays clearly the same man as in the photo and the head is lit and sized like the rest of "
    "the picture? Reply with ONLY a JSON object: {\"better\": 1 or 2, \"why\": one short sentence}")

# The same question about the FACE alone. Used to decide whether a return whose framing failed still carries a face worth keeping: measured 2026-09-21,
# the general question preferred the source over the night-out return the user liked, because it also weighs head angle, posture and blending.
FACE_ONLY_PAIR_PROMPT = (
    "Both images are the same photo of the same man, with two different renderings of his face and hair. Ignore the head angle, the posture, the "
    "framing, the size of the head and the background. Judge only the face and hair: which image shows the more attractive AND more natural face, "
    "with calm confident eyes, a defined jawline, a relaxed slight smile or calm expression (never tense, awkward, forced or smirking), natural skin "
    "and natural full hair? Reply with ONLY a JSON object: {\"better\": 1 or 2, \"why\": one short sentence}")


def parse_json_reply(text: str) -> dict | None:
    """Pull the JSON object out of a chatty reply."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        try:
            return json.loads(re.sub(r",\s*}", "}", m.group(0)))
        except json.JSONDecodeError:
            return None


async def gemini_text(client, models: list[str | None], prompt: str, files: list[Path], log: RunLog, tag: str) -> dict | None:
    """One text-only Gemini call (no image quota) that must return JSON. Tries each model in turn."""
    for model in models:
        for attempt in range(2):
            try:
                out = await asyncio.wait_for(client.generate_content(prompt, files=[str(f) for f in files], model=model, temporary=True),
                                             TEXT_TIMEOUT)
            except UsageLimitExceededError:
                raise
            except (APIError, GeminiError, asyncio.TimeoutError) as e:
                log.say(f"    [{tag}] text call failed on model {model}: {type(e).__name__}: {e}")
                break
            data = parse_json_reply(out.candidates[out.chosen].text)
            if data is not None:
                return data
            log.say(f"    [{tag}] reply was not JSON (attempt {attempt + 1}): {out.candidates[out.chosen].text[:120]!r}")
    return None


def scene_block(scene: dict | None, zone: str = "face") -> str:
    """The AI's own description of the crop for the edit prompt: what must stay. The expression is deliberately NOT here:
    copying it produced 'lips slightly parted' and 'open smile with the teeth showing', both reviewed as bad; the expression
    comes from the attractiveness policy instead."""
    if not scene:
        return ""
    g = lambda k: str(scene.get(k) or "").strip()
    # zone "head" (another man's photo): his hair replaces the source man's, so the source hair must not be listed as something that stays
    parts = [f"head: {g('head_turn')}", f"chin: {g('head_tilt')}", f"eyes: {g('gaze')}", f"glasses: {g('glasses')}",
             f"hair: {g('hair')}" if zone == "face" else "", f"light on his face: {g('light')}", f"how bright his face is: {g('face_exposure')}"]
    return "\n\nThis is what the last image shows before the edit. The head angle, gaze, glasses and light must stay exactly as they are:\n" + "\n".join(
        f"- {p}" for p in parts if p and not p.endswith(": "))


def expression_rule(expression: str, attractiveness: str, scene: dict | None) -> str:
    if expression == "same":
        return (" Give him exactly the expression of the man in the last image: the same mouth, eyes and brows at the same strength, but "
                "natural and relaxed on his face, never tense or forced.")
    if expression not in ("auto", "none"):
        return f" His expression: {expression}."
    return f" {attractiveness.strip()}"


def edit_prompt(n_refs: int, zone: str, glasses: str, look: str, scene: dict | None, expression: str,
                attractiveness: str, retry_note: str | None = None, reflection: bool = False, rescue: bool = False, far: bool = False,
                whole_head: bool = False, face_share: float | None = None) -> str:
    what = "face" if zone == "face" else "head"
    if zone == "face" and whole_head:
        # Loop v3 (2026-09-26): his own photo at normal distance gets its whole head redrawn as one. With the hair kept and only the face redrawn,
        # the user saw "my face alone has been lasso-ed and edited in" (rocky 183350); the picture they called perfect (IMG_0862 201520) had the
        # hair, face, ears and neck redrawn together. The outline and size stay the photo's, so the head cannot grow.
        # Item 28 (the user, 2026-09-26): hair, beard and moustache come from the reference photos, never from the photo being edited.
        hair = (" Redraw his whole head as one, the hair included: his hair, beard and moustache exactly as in the reference photos (his own "
                "tight curly black hair), so that hair, face, ears and neck belong together like one real photograph.")
    elif zone == "face":
        hair = " Keep his hair exactly as it is in the last image, the same size and shape."
    elif look == "curly":
        hair = " His hair is his own tight dark curls, at exactly the same size and volume as the hair in the last image."
    elif look == "short":
        hair = " His hair is his own short dark hair, at exactly the same size and volume as the hair in the last image."
    else:
        hair = (" All of his hair is his own, copied from the reference photos over the whole head: the front, the top, the crown, the temples "
                "and sides, around the ears and the back down to the nape. Use his curl pattern, density, cut and the way it tapers at the "
                "sides. None of the hair of the man in the last image is kept.")
    # Another man's photo: the references leaked their exposure into the render (face lightness 57-65 against the photo's 37, measured 2026-09-20; the prompt
    # used to say "skin tone exactly as in the reference photos"), so they are named as the source of who he is only. His own photo keeps the original wording.
    # His own or look-alike photo (zone face): the source face already resembles him, and Gemini returned it as it was (gt_sim 0.93-0.99, 2026-09-21),
    # so the prompt says it is only a look-alike to be replaced by the real face.
    ident = ("lips, skin tone and beard exactly as in the reference photos. The man in the last image is only a look-alike: do not keep his face, "
             "render this man's own face from the reference photos in its place." if zone == "face" else
             "lips, natural complexion and beard as in the reference photos. Use the reference photos only for who he is: ignore their lighting, "
             "exposure, colour cast and head angle; those come from the last image.")
    gl = {"same": " If the man in the last image wears glasses, he keeps wearing the same glasses.",
          "yes": " He wears thin metal-framed glasses.", "no": " He is not wearing glasses."}[glasses]
    refl = ""
    if reflection or (scene and scene.get("reflection_present")):
        where = str((scene or {}).get("reflection_where") or "in the glass")
        refl = (f"\nThe last image also contains a reflection of this same man ({where}). Give that reflection the same new face and the "
                "same expression as his real face, as a reflection: keep its softness, its colour cast and its partial transparency, and "
                "keep it consistent with the man himself.")
    retry = (f"\n\nA previous attempt at this edit had these problems, so avoid them: {retry_note}" if retry_note else "")
    rescue_txt = (f"\n\nImage {n_refs} (the one just before the last image) shows his face, hair and expression exactly as they must look in the result. "
                  "The last image is the only source of the framing: keep the head at exactly the position, size, turn and tilt it has in the last image, "
                  "keep everything else in the last image untouched, and do not return the last image unchanged.") if rescue else ""
    return (f"The first {n_refs} images are photos of the same man: the identity reference. The last image is the photo to edit.\n\n"
            f"Edit the last image so that the man in it has this exact man's {what}: his face structure, jawline, nose, eyes, brows, "
            f"{ident}{hair}{gl}{expression_rule(expression, attractiveness, scene)}"
            f"{scene_block(scene, zone)}"
            + ("\n\nHe is far from the camera: his head is small in the last image and exactly as soft and grainy as the rest of the photo. Keep it "
               "that small and that soft." + (f" His face, from the top of his forehead to his chin, is {face_share * 100:.0f} percent of the image height "
                                             "in the last image and stays exactly that." if face_share else "") if far else "")
            + "\n\n"
            "Keep his head at the same position, turn and tilt as in the last image, and the head, including the hair, exactly the same "
            "size as there, never larger. Keep his jaw, chin and neck exactly as clean as in the last image: no extra fold or double chin. "
            "The face has exactly the exposure, colour, contrast and grain of the photo around it, lit from the same direction, so it "
            "belongs in the picture like a real phone photo and not a studio portrait.\n"
            f"Keep everything else in the last image exactly as it is: neck, clothing, body, hands, pose, background and framing.{refl}{retry}{rescue_txt}")


def build_prompt(n_refs: int, strength: str = "normal") -> str:
    if strength == "strong":
        return (f"The first {n_refs} images show one man's physique. The last image shows a different man with a slimmer build.\n\n"
                "Edit the last image so that the man in it has a clearly broader, more muscular upper body, like the man in the "
                "reference photos: noticeably wider shoulders with rounded, well-developed deltoids, a thicker neck, thicker upper "
                "arms and forearms, and a broader chest tapering to a narrower waist. The outline of his body must visibly change "
                "and become wider at the shoulders and arms.\n"
                "Re-fit the same clothes onto the broader body: the same garments, colours, fabric and fit style, stretched over the "
                "new proportions. Keep his pose, hand positions, head, camera angle and the whole background exactly as they are.")
    return (f"The first {n_refs} images show one man's physique: his shoulder width, neck, arms, chest and waist. The last image "
            "shows a different man.\n\n"
            "Edit the last image so that the man in it has the physique of the man in the reference photos: the same shoulder "
            "width, neck thickness, arm and forearm size, chest and waist proportions.\n"
            "Keep his clothes as they are: the same garments, colours, fabric and fit style, adjusted only as far as the new "
            "proportions require. Keep his pose, hand positions, head, camera angle and the whole background exactly as they are.")


# ---------------------------------------------------------------------------------------------- Gemini image edit
# Raw returns are intermediates, never results: they go to raw/ inside the run folder, and only complete pictures are written to the run folder itself.
async def gemini_edit(client, model: str | None, prompt: str, files: list[Path], run_dir: Path, tag: str, verbose: bool,
                      log: RunLog, retries: int = 2) -> tuple[Path, str]:
    last = "unknown"
    # The exact request of every edit call (2026-10-07, consistency): the prompt text and each file sent by name and sha256. The run used to keep
    # only the crops; the prompt (which carries the random scene reading) was lost.
    import provenance
    log.data.setdefault("edit_calls", []).append({"tag": tag, "model": model, "prompt": prompt, "prompt_sha256": provenance.sha256_text(prompt),
                                                  "sent": [{"name": Path(f).name, "sha256": provenance.sha256_file(Path(f))} for f in files]})
    for attempt in range(retries + 1):
        try:
            out = await client.generate_content(prompt, files=[str(f) for f in files], model=model, temporary=True)
        except UsageLimitExceededError:
            raise
        except (ImageGenerationError, GeminiError) as e:
            last = f"{type(e).__name__}: {e}"
            log.say(f"    [{tag}] attempt {attempt + 1} failed: {last}")
            continue
        cand = out.candidates[out.chosen]
        meter = getattr(log, "meter", None)
        if meter is not None:
            meter.note(tag, "image" if cand.generated_images else "no_image")
            log.data["credits"] = meter.as_dict()
            log.save()
        if not cand.generated_images:
            text = cand.text or ""
            # Gemini answers an image request with plain text when the image quota is spent; retrying just burns time.
            if "limit resets" in text or "image limit" in text.lower():
                raise UsageLimitExceededError(f"Gemini image limit reached: {text.strip()[:200]}")
            last = f"no image returned; text: {text[:300]}"
            log.say(f"    [{tag}] attempt {attempt + 1}: {last}")
            continue
        raw_dir = run_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        saved = Path(await cand.generated_images[0].save(path=str(raw_dir), filename=f"{tag}_raw.png", verbose=verbose))
        return fix_extension(saved), cand.text or ""
    raise RuntimeError(f"Gemini returned no edited image for {tag}: {last}")


# ---------------------------------------------------------------------------------------------- faces in the frame
def detect_faces(img: np.ndarray, min_px: int = 48) -> list[dict]:
    """Every face in the frame, largest first."""
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.6)
    det.setInputSize((w, h))
    _, faces = det.detect(img)
    if faces is None:
        return []
    out = []
    for row in faces:
        x, y, bw, bh = (int(max(0, row[0])), int(max(0, row[1])), int(row[2]), int(row[3]))
        bw, bh = min(w - x, bw), min(h - y, bh)
        if min(bw, bh) < min_px:
            continue
        out.append({"box": (x, y, bw, bh), "face_w": bw, "det_score": float(row[-1])})
    return sorted(out, key=lambda f: -f["face_w"])


def find_identity_faces(img: np.ndarray, scorer: ArcFaceScorer, pool: list, main_emb: np.ndarray, dups: set[str],
                        floor: float = 0.30) -> list[dict]:
    """Faces in the frame that are the same person as the main face: the subject plus any reflection or second copy."""
    found = []
    for i, f in enumerate(detect_faces(img)):
        try:
            emb = scorer.embed_head(img, box=f["box"])
        except Exception as e:
            f.update({"role": "unknown", "reason": f"could not embed: {type(e).__name__}"})
            found.append(f)
            continue
        to_main = float(np.dot(emb, main_emb))
        to_pool = identity.score_against_pool(emb, pool, exclude_names=dups)["score"]
        f.update({"sim_to_main": round(to_main, 3), "sim_to_pool": round(to_pool, 3),
                  "role": "main" if i == 0 else ("copy" if max(to_main, to_pool) >= floor else "other person")})
        found.append(f)
    return found


# ---------------------------------------------------------------------------------------------- crops
def crop_for_face(shape: tuple[int, ...], box: tuple[int, int, int, int], kind: str, send_px: int = SEND_PX) -> tuple[composite.Rect, float]:
    """Crop rectangle around a face, sized so the face keeps as many real pixels as possible in the image sent."""
    x, y, w, h = box
    fs = max(w, h)
    want = 2.4 if kind == "face" else 3.0
    scale = max(1.8, min(want, send_px / max(1.0, fs)))
    dy = 0.15 * fs if kind == "head" else 0.0
    if w < FAR_FACE_PX:
        # Far from the camera (2026-09-23): the usual 2.4-3x crop reached Gemini as a 2-4x upscaled, blurry head close-up and every render came back
        # with the head 9-17 percent bigger and 7-17x sharper than the photo. A wider crop keeps the upscale at most FAR_MAX_UPSCALE and shows the
        # shoulders and body, so the head is drawn at the photo's scale; the face sits in the upper part of the crop.
        side = max(fs * scale, send_px / FAR_MAX_UPSCALE)
        return composite.rect_crop(shape, x + w / 2, y + h / 2 + side * 0.2, side, side), side / fs
    return composite.rect_crop(shape, x + w / 2, y + h / 2 - dy, fs * scale, fs * scale), scale


async def read_head_box(client, text_models: list[str | None], src: np.ndarray, box: tuple[int, int, int, int], run_dir: Path,
                        log: RunLog) -> tuple[float, float, float, float] | None:
    """His whole head, hair included, as the AI reads it on a wide look (5x the face) around the face: (x0, y0, x1, y1) in photo pixels, or None."""
    x, y, w, h = box
    fs = max(w, h)
    look = composite.rect_crop(src.shape, x + w / 2, y + h / 2, fs * 5, fs * 5)
    (run_dir / "raw").mkdir(exist_ok=True)
    p = run_dir / "raw" / "head_look.jpg"
    cv2.imwrite(str(p), resized_for_send(composite.take(src, look)), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for model in text_models:
        try:
            out = await asyncio.wait_for(client.generate_content(HEAD_BOX_PROMPT, files=[str(p)], model=model, temporary=True), TEXT_TIMEOUT)
        except UsageLimitExceededError:
            raise
        except (asyncio.TimeoutError, APIError, GeminiError) as e:
            log.say(f"    [head box] no answer from model {model}: {type(e).__name__}: {e}")
            continue
        b = (parse_json_reply(out.candidates[out.chosen].text) or {}).get("box_2d")
        try:
            y0, x0, y1, x1 = (float(v) for v in b)
        except (TypeError, ValueError):
            log.say(f"    [head box] unusable reply from model {model}: {out.candidates[out.chosen].text[:120]!r}")
            continue
        hb = (look[0] + x0 / 1000 * look[2], look[1] + y0 / 1000 * look[3], look[0] + x1 / 1000 * look[2], look[1] + y1 / 1000 * look[3])
        cx, cy = x + w / 2, y + h / 2
        hw, hh = hb[2] - hb[0], hb[3] - hb[1]
        if not (hb[0] <= cx <= hb[2] and hb[1] <= cy <= hb[3] and 0.8 * w <= hw <= 4 * fs and 0.8 * h <= hh <= 4 * fs):
            log.say(f"    [head box] implausible box {[round(v) for v in hb]} for the face {list(box)}; ignored")
            continue
        return hb
    return None


def fit_whole_head(shape: tuple[int, ...], rect: composite.Rect, head: tuple[float, float, float, float]) -> composite.Rect | None:
    """The crop grown (never shrunk) and centred on his whole head so it sits HEAD_MARGIN inside every edge; None when the crop does not cut it."""
    x0, y0, x1, y1 = head
    tol = HEAD_CUT_TOL * rect[2]
    if x0 >= rect[0] - tol and y0 >= rect[1] - tol and x1 <= rect[0] + rect[2] + tol and y1 <= rect[1] + rect[3] + tol:
        return None
    side = max(rect[2], max(x1 - x0, y1 - y0) / (1 - 2 * HEAD_MARGIN))
    return composite.rect_crop(shape, (x0 + x1) / 2, (y0 + y1) / 2, side, side)


def expression_crop(shape: tuple[int, ...], head: tuple[float, float, float, float]) -> composite.Rect:
    """The crop for an expression edit: his whole head at EXPR_HEAD_SHARE of the side, the hair top EXPR_HEAD_TOP below the crop's top edge."""
    x0, y0, x1, y1 = head
    side = max(x1 - x0, y1 - y0) / EXPR_HEAD_SHARE
    return composite.rect_crop(shape, (x0 + x1) / 2, y0 - EXPR_HEAD_TOP * side + side / 2, side, side)


def union_rect(rects: list[composite.Rect]) -> composite.Rect:
    x1 = min(r[0] for r in rects)
    y1 = min(r[1] for r in rects)
    x2 = max(r[0] + r[2] for r in rects)
    y2 = max(r[1] + r[3] for r in rects)
    return x1, y1, x2 - x1, y2 - y1


def person_rect(shape: tuple[int, ...], box: tuple[int, int, int, int]) -> composite.Rect:
    """Whole-person crop estimated from the face box (used only by the opt-in head+build stage)."""
    x, y, w, h = box
    return snap_aspect(composite.rect_crop(shape, x + w / 2, y + 4.4 * h, w * 7.0, h * 11.2), shape)


# ---------------------------------------------------------------------------------------------- one edit stage
def align_to_ring(crop: np.ndarray, edit: np.ndarray) -> tuple[np.ndarray, float, dict, str, np.ndarray | None, np.ndarray | None]:
    """Fit the returned crop to the source crop using only the outer ring, where nothing was supposed to change.

    Returns (edit at crop size, ECC correlation, warp magnitude, how, validity mask or None, warp matrix or None). The warp is applied only
    when it is measurably needed; otherwise the plain resize is used, so no resampling softness is added for nothing.
    When a warp is applied, the validity mask marks the pixels it could actually fill.
    """
    h, w = crop.shape[:2]
    inner = np.zeros((h, w), np.uint8)
    mx, my = int(w * 0.25), int(h * 0.25)
    inner[my:h - my, mx:w - mx] = 255
    aligned, cc, warp = composite.align_ecc(crop, edit, inner, exclude_px=2)
    mag = composite.warp_magnitude(warp, (w, h))
    plain = cv2.resize(edit, (w, h), interpolation=cv2.INTER_CUBIC if edit.shape[0] < h else cv2.INTER_AREA)
    if cc > 0 and abs(mag["scale"] - 1) < 0.004 and mag["shift_frac"] < 0.002:
        return plain, cc, mag, "resize only", None, None
    valid = cv2.warpAffine(np.full((h, w), 255, np.uint8), warp, (w, h), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return aligned, cc, mag, "ECC on the border ring", valid, warp


async def edit_stage(client, model, log: RunLog, run_dir: Path, tag: str, base: np.ndarray, rect: composite.Rect, prompt: str,
                     ref_files: list[Path], verbose: bool) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """Send the crop to Gemini, take the returned crop and paste it back with a soft border. Returns (image, zone, meta).

    THE RULE (2026-09-21): a rendered head is never a result; only complete pictures are. A return is merged into the picture only when its outer
    ring matches the crop sent. A re-framed return (Gemini zoomed or shifted the picture) is refused and the next attempt asks for the exact
    framing: merging it on the face box (2026-09-21 to 09-23) laid a head drawn at another scale over the real one, and the user saw two heads
    fused into one (IMG_0862, 2026-09-23: second hairline, second ear, smeared collar, "unreal and monsterish"). None of the 8 face-box merges
    ever passed, and every best version came from a return whose ring matched (ECC >= 0.90, scale <= 1.048, shift <= 0.092).
    """
    crop = composite.take(base, rect)
    send_p = run_dir / f"{tag}_send.png"
    cv2.imwrite(str(send_p), resized_for_send(crop))
    raw_p, txt = await gemini_edit(client, model, prompt, ref_files + [send_p], run_dir, tag, verbose, log)
    return paste_return(base, rect, raw_p, txt, tag)


def paste_return(base: np.ndarray, rect: composite.Rect, raw_p: Path, txt: str, tag: str) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """The returned crop merged into the picture, only when its outer ring matches the crop sent (edit_stage's rule, moved here unchanged on
    2026-10-08 so the recipe method replicate/1 pastes exactly the same way). Returns (image, zone, meta); meta['failed'] says why it was not merged."""
    crop = composite.take(base, rect)
    h, w = crop.shape[:2]
    edit = cv2.imread(str(raw_p))
    eh, ew = edit.shape[:2]
    dev = abs((ew / eh) / (w / h) - 1)
    meta: dict = {"stage": tag, "raw": f"raw/{raw_p.name}", "raw_size": [ew, eh], "crop": list(rect), "aspect_dev": round(dev, 4), "text": txt[:200]}
    if dev > ASPECT_TOL:
        meta["failed"] = f"Gemini returned a {ew}x{eh} image for a {w}x{h} crop (different aspect ratio)"
        return base, None, meta
    aligned, cc, mag, how, valid, warp = align_to_ring(crop, edit)
    meta.update({"ecc": round(cc, 4), "warp": mag, "aligned_by": how})
    if cc < ECC_FAIL or abs(mag["scale"] - 1) > ALIGN_MAX_SCALE or mag["shift_frac"] > ALIGN_MAX_SHIFT:
        meta["failed"] = f"Gemini re-framed the crop (ring: ecc {cc:.3f}, warp {mag}); not merged"
        meta["reframed"] = True
        return base, None, meta
    sx, sy = w / ew, h / eh
    hx, hy, hr = (ew - SPARKLE_OFFSET) * sx, (eh - SPARKLE_OFFSET) * sy, SPARKLE_RADIUS * sx
    if warp is not None:
        # The aligned return was warped, so the watermark moved with it (night out, 2026-09-21: a 3 percent shift let the star leak into the paste).
        # The warp maps aligned coordinates to the resized return (cv2.WARP_INVERSE_MAP), so the star's place in the aligned image is the inverse.
        hx, hy = (cv2.invertAffineTransform(warp) @ np.array([hx, hy, 1.0])).tolist()
        hr = hr / max(0.5, mag["scale"]) * 1.15
    holes = [(hx, hy, hr)]
    out, zone = composite.paste_rect_soft(base, aligned, rect, BORDER_FRAC, holes, valid)
    return out, zone, meta


# ---------------------------------------------------------------------------------------------- physique measurement (measurement only)
ROW_FACTORS = (0.7, 1.6, 3.0)  # rows measured this many face-heights below the chin: shoulders, chest, waist


def person_widths(img: np.ndarray, box: tuple[int, int, int, int]) -> dict:
    """Horizontal extent of the person silhouette at fixed rows below the chin. Measurement only."""
    x, y, w, h = box
    m = segment.person_mask(img, box) > 0
    H = img.shape[0]
    out = {}
    for f in ROW_FACTORS:
        r = int(y + h + f * h)
        if r >= H - 2:
            out[f] = None
            continue
        xs = np.where(m[max(0, r - 2):r + 3].any(axis=0))[0]
        out[f] = int(xs.max() - xs.min()) if len(xs) else 0
    return out


def physique_report(src: np.ndarray, out: np.ndarray, src_box: tuple[int, int, int, int]) -> dict:
    ws, wo = person_widths(src, src_box), person_widths(out, src_box)
    return {"rows_in_face_heights_below_chin": list(ROW_FACTORS), "source_px": {str(k): v for k, v in ws.items()},
            "output_px": {str(k): v for k, v in wo.items()},
            "output_over_source": {str(f): (round(wo[f] / ws[f], 3) if ws[f] and wo[f] else None) for f in ROW_FACTORS}}


# ---------------------------------------------------------------------------------------------- verdict
def face_neck_gap(img: np.ndarray, box) -> float | None:
    """Lab lightness of the face skin minus that of the neck skin inside the same image (BiSeNet masks, eroded), or None when either
    mask is too small. A head that was rendered brighter than its own neck reads as pasted in; the source's own gap is the baseline."""
    try:
        parts = segment.head_parts(img, tuple(int(v) for v in box))
    except Exception:
        return None
    lab = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    lightness = {}
    for name, key in (("face", "skin"), ("neck", "neck_b")):
        mask = cv2.erode((parts[key] > 0).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
        if int(mask.sum()) < 150:
            return None
        lightness[name] = float(lab[mask][:, 0].mean())
    return lightness["face"] - lightness["neck"]


def good_face_in(raw_path: Path, pool: list, scorer: ArcFaceScorer, dups: set, thr: dict, own: bool, judge: dict | None,
                 expression_must_match: bool, composite_gt_sim: float | None = None, unchanged_gt: float | None = None) -> dict | None:
    """Is the face in this raw return worth placing into the picture? Judged on the FACE alone, never on which gates the composite failed
    (round 7 only rescued composites that failed geometry gates, so good faces were dropped whenever a lighting or expression check also fired).

    Worth placing = a face is found, its identity against the pool is at or above the accept line, it is not the source face returned unchanged,
    and, when the expression must match the source, the judge did not say it differs. Returns {"score", "raw"} or None.
    """
    img = cv2.imread(str(raw_path))
    if img is None:
        return None
    res = identity.score_image(img, pool, scorer, exclude_names=dups)
    if not res.get("detected") or res["score"] < thr["accept"]:
        return None
    if expression_must_match and (judge or {}).get("same_expression") is False:
        return None
    # The source face handed back is not a new face (2026-09-23: beach's three placements and nerd's first placed the source's own face, gt_sim 0.944 / 0.902)
    if own and composite_gt_sim is not None and unchanged_gt is not None and composite_gt_sim > unchanged_gt:
        return None
    return {"score": round(res["score"], 3), "raw": raw_path}


def turn_degrees(scene: dict | None) -> float | None:
    """The head turn, in degrees, as Gemini read it (the largest number in its description; 'profile' alone counts as 80)."""
    txt = str((scene or {}).get("head_turn") or "")
    nums = [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", txt)]
    if nums:
        return max(nums)
    return 80.0 if "profile" in txt.lower() else None


def pose_of(reading: dict | None) -> tuple[float, float] | None:
    """(turn, chin) in degrees from a POSE_PROMPT reply, or None."""
    try:
        return float(reading["turn"]), float(reading["chin"])
    except (TypeError, KeyError, ValueError):
        return None


def pose_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def pose_words(turn: float, chin: float, camera: str | None = None) -> str:
    t = ("facing the camera" if abs(turn) < 10 else
         f"turned about {abs(turn):.0f} degrees toward the {'right' if turn > 0 else 'left'} side of the picture")
    c = ("level" if abs(chin) < 8 else f"tilted down about {chin:.0f} degrees, looking down" if chin > 0 else
         f"tilted up about {-chin:.0f} degrees, looking up")
    cam = {"above": ", seen from slightly above", "below": ", seen from slightly below"}.get(str(camera or "").lower(), "")
    return f"his head {t} and {c}{cam}"


async def ref_pose(client, text_models: list[str | None], path: Path, log: RunLog) -> dict | None:
    """The AI's pose reading of one reference image, cached by file content (text call only, once per image)."""
    key = hashlib.md5(path.read_bytes()).hexdigest()
    cache = json.loads(REF_POSES.read_text(encoding="utf-8")) if REF_POSES.exists() else {}
    if key in cache:
        return cache[key]
    reading = await gemini_text(client, text_models, POSE_PROMPT, [path], log, f"pose {path.name}")
    if pose_of(reading) is not None:
        cache[key] = dict(reading, file=path.name)
        REF_POSES.parent.mkdir(parents=True, exist_ok=True)
        REF_POSES.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
    return reading


async def synthetic_refs(client, model, text_models, target: tuple[float, float], camera: str | None, studio: list[tuple[str, Path, tuple]],
                         pool: list, scorer: ArcFaceScorer, run_dir: Path, log: RunLog, verbose: bool) -> list[tuple[str, Path, tuple]]:
    """The angle his photos lack, made from his studio photos (plan of 2026-09-23): Gemini renders him at the target pose; code keeps a render only if
    its identity against his photos is at least SYN_ID_MIN and the AI reads its pose within SYN_MATCH degrees of the target. Kept renders are cached
    per 15-degree pose bin in .cache/synthetic_refs and reused. Returns [(name, path, pose)]."""
    bin_key = f"turn{int(round(target[0] / 15) * 15):+d}_chin{int(round(target[1] / 15) * 15):+d}"
    folder = SYN_DIR / bin_key
    index = folder / "index.json"
    kept = json.loads(index.read_text(encoding="utf-8")) if index.exists() else []
    if len(kept) >= 2:
        log.say(f"  rendered references for {bin_key}: {len(kept)} cached")
        return [(k["name"], folder / k["name"], tuple(k["pose"])) for k in kept]
    base = sorted(studio, key=lambda s: abs(s[2][0] - target[0]))[:3]
    prompt = (f"The {len(base)} images are photos of the same man. Make one new photo of this same man, head and shoulders, with "
              f"{pose_words(target[0], target[1], camera)}, a plain soft background and soft even daylight. His face, hair, beard, skin and build "
              "exactly as in the photos, as a real phone photo.")
    log.say(f"  no reference of him within {SELF_MAX:g} degrees of this pose: rendering {bin_key} from {', '.join(b[0] for b in base)}")
    folder.mkdir(parents=True, exist_ok=True)
    for k in range(3):
        if len(kept) >= 2:
            break
        try:
            raw, _ = await gemini_edit(client, model, prompt, [b[1] for b in base], run_dir, f"synref_{bin_key}_{k + 1}", verbose, log)
        except UsageLimitExceededError:
            raise
        except Exception as e:
            log.say(f"    render {k + 1}: failed ({type(e).__name__}: {e})")
            continue
        img = cv2.imread(str(raw))
        res = identity.score_image(img, pool, scorer) if img is not None else {}
        reading = await gemini_text(client, text_models, POSE_PROMPT, [raw], log, f"pose synref {k + 1}")
        pose = pose_of(reading)
        ok = res.get("detected") and res["score"] >= SYN_ID_MIN and pose is not None and pose_distance(pose, target) <= SYN_MATCH
        log.say(f"    render {k + 1}: identity {round(res.get('score', 0), 3) if res.get('detected') else 'no face'}, pose {pose} "
                f"(target {target}) -> {'KEPT' if ok else 'not kept'}")
        if ok:
            name = f"synref_{bin_key}_{len(kept) + 1}.jpg"
            cv2.imwrite(str(folder / name), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            kept.append({"name": name, "pose": list(pose), "identity": round(res["score"], 3), "target": list(target), "from": [b[0] for b in base]})
            index.write_text(json.dumps(kept, indent=1), encoding="utf-8")
    return [(k_["name"], folder / k_["name"], tuple(k_["pose"])) for k_ in kept]


def gate_excess(cand: dict, gates: dict, source_kind: str) -> float:
    """How far a candidate is from passing: each measured gate adds how far outside its limit the value is, in units of the allowed range; each
    yes/no failure (a judge flag, no face, pixels outside the crop) adds 1. Used to pick the closest picture when nothing passed (loop v3 of
    2026-09-26: the old "fewest problems" key showed table tennis attempt 2, the worst by eye: a curly mop at size 1.217, over attempt 6 at 1.057)."""
    m = cand.get("metrics") or {}
    own = source_kind == "own"
    ex = 0.0
    for p_ in cand.get("problems", []):
        if p_.startswith("head size changed"):
            lo, hi = gates["size_own"] if own else gates["size_foreign"]
            sz = float(m.get("size_ratio") or 1.0)
            ex += max(lo - sz, sz - hi, 0.0) / (hi - lo)
        elif p_.startswith("head moved"):
            ex += max(0.0, float(m.get("face_shift_frac") or 0.0) - SHIFT_MAX) / SHIFT_MAX
        elif p_.startswith("face is lit differently"):
            lim = gates["light_de_max"] if own else gates["light_de_max_foreign"]
            ex += max(0.0, float((m.get("light") or {}).get("dE") or lim) - lim) / lim
        elif p_.startswith("face is brighter than the neck"):
            ex += max(0.0, float(m.get("neck_gap") or 0.0) - gates["neck_gap_max"]) / gates["neck_gap_max"]
        elif p_.startswith("face is much sharper"):
            ex += max(0.0, float(m.get("sharp_ratio") or 0.0) - gates["sharp_max"]) / gates["sharp_max"]
        elif p_.startswith("clothes or background inside the crop were redrawn"):
            ssim = (m.get("drift") or {}).get("ssim")
            ex += max(0.0, DRIFT_SSIM_MIN - float(ssim)) / (1.0 - DRIFT_SSIM_MIN) if ssim is not None else 1.0
        else:
            ex += 1.0
    return ex


def retry_note_from(problems: list[str], judge: dict | None) -> str | None:
    """Turn a failed candidate's problems and the judge's own note into a sentence for the next prompt (AI feedback loop)."""
    bits: list[str] = []
    for p in problems:
        low = p.lower()
        if "head angle" in low:
            bits.append("his head was turned more toward the camera than in the last image; keep it turned exactly as it is there")
        elif "much sharper than the photo" in low:
            bits.append("the face came out much sharper and cleaner than the photo; render it exactly as soft, blurred and grainy as the rest of the picture")
        elif "returned unchanged" in low:
            bits.append("the man in the last image only resembles him: replace his whole face with the real man's from the reference photos, and keep "
                        "only the pose, framing and light of the last image")
        elif "not better than the source" in low:
            bits.append("the previous face was no improvement on the last image; render him at his best: calm confident eyes, a defined jawline, a "
                        "relaxed natural expression, full natural hair")
        elif "brighter than the neck" in low:
            bits.append("his face came out brighter than his neck; face and neck have the same skin brightness as in the last image, lit like the "
                        "rest of the picture")
        elif "expression differs" in low:
            bits.append("his expression did not match the last image; copy that expression exactly, the same mouth, eyes and brows")
        elif "lit differently" in low or "lighting" in low:
            bits.append("the face came out brighter, cleaner and cooler than the rest of the picture; keep it as dark, warm and "
                        "grainy as it is in the last image")
        elif "head size" in low:
            bits.append("his head and hair came out a different size from the last image; keep the head and hair exactly the size they are there")
        elif "ghost" in low or "duplicate" in low or "doubled" in low:
            bits.append("a ghost or second outline appeared around the head; render one clean head")
        elif "glasses" in low:
            bits.append("his glasses changed; keep exactly the same glasses")
        elif "seam" in low:
            bits.append("a seam or edge showed around the face; render the face, hair and neck as one continuous piece")
        elif "reflection" in low:
            bits.append("the reflection did not show the same man as his real face; give it that same face, softened as a reflection")
        elif "redrawn" in low or "changed" in low:
            bits.append("something outside the face changed; leave clothes, background and framing exactly as they are")
    note = str((judge or {}).get("notes") or "").strip().rstrip(".")
    if note and note.lower() != "none":
        bits.append(note)
    return "; ".join(dict.fromkeys(bits)) or None


def judge_failures(judge: dict | None, expression_must_match: bool = False, glasses_policy: str = "same",
                   expression_edit: bool = False, source_glasses: bool | None = None) -> tuple[list[str], list[str]]:
    """Split the AI judge's answer into (hard failures, warnings)."""
    if not judge:
        return [], ["the AI judge gave no usable answer, so the visual checks were skipped"]
    hard, soft = [], []
    # Hard: same_head_angle and double_image (double_image caught the flagged Pinterest round-2 output twice and raised no false alarm on
    # four outputs the user called perfect; it missed the flagged kayak one, so recall is partial), glasses, seam, lighting, drift.
    checks = [("same_head_angle", True, "head angle changed"), ("glasses_preserved", True, "glasses not preserved"),
              ("double_image", False, "a ghost, duplicate face or doubled outline is visible"),
              ("seam_visible", False, "a seam or cut-out edge is visible"), ("lighting_consistent", True, "lighting does not match the picture"),
              ("anything_else_changed", False, "clothes, body, hands or background changed")]
    for key, want, msg in checks:
        if key == "glasses_preserved" and glasses_policy in ("yes", "no"):
            # --glasses no|yes (2026-10-10): the glasses change on purpose, so the check asks for the change. Skipping it let both DSC07985
            # pictures pass with his glasses still on under --glasses no.
            if source_glasses is None:
                soft.append(f"glasses check skipped: --glasses {glasses_policy}, and the source's glasses were not read")
                continue
            want = source_glasses == (glasses_policy == "yes")      # nothing to change: the same in both; a change: they must differ
            v = judge.get(key)
            if v is None:
                soft.append(f"judge did not answer {key}")
            elif bool(v) != want:
                hard.append("AI judge: " + ("glasses not removed (--glasses no)" if glasses_policy == "no" else "glasses not added (--glasses yes)")
                            if not want else "AI judge: glasses changed though the photo already matches --glasses " + glasses_policy)
            continue
        v = judge.get(key)
        if v is None:
            soft.append(f"judge did not answer {key}")
        elif bool(v) != want:
            hard.append(f"AI judge: {msg}")
    # Warnings only: not validated against the user's reviews (jaw fold: the reported double chin was in the source photo), or expected to differ.
    if judge.get("jaw_clean") is False:
        soft.append("AI judge: a fold or double chin may have appeared under the chin (unvalidated question)")
    if judge.get("reflection_matches") is False:
        soft.append("AI judge: the reflection does not clearly show the same man as his real face")
    if expression_edit:
        # zone expression (2026-10-10): the edit exists to change his expression, so an unchanged one is the failure
        if judge.get("same_expression") is not False:
            hard.append("AI judge: the expression did not change (an expression edit must change it)")
    elif judge.get("same_expression") is False:
        if expression_must_match:
            hard.append("AI judge: expression differs from the source (it must match under the same-expression policy)")
        else:
            soft.append("AI judge: expression differs from the source (by design, see the attractiveness policy)")
    return hard, soft


def measure_candidate(src: np.ndarray, base: np.ndarray, rect: composite.Rect, union: np.ndarray, src_crop: np.ndarray, src_eval: dict, pool: list,
                      scorer: ArcFaceScorer, dups: set, gates: dict, source_kind: str, far: bool, head_boxes: list, src_gap: float | None,
                      zone_mode: str, main_in_crop: tuple, png: Path, crop_jpg: Path, t0: float, expression_edit: bool = False
                      ) -> tuple[dict, list[str], list[str], dict, np.ndarray, np.ndarray]:
    """Save the complete picture lossless, verify it on the saved file, and measure it against the source: identity, head size and position,
    light, neck gap, sharpness (far faces), drift inside the crop, pixels changed outside the crop. Deterministic measurements: they measure, they
    do not interpret. Moved unchanged out of run() on 2026-10-08, so the recipe method replicate/1 measures exactly the same way.
    Returns (metrics, problems, warnings, outside check, saved picture, output crop)."""
    problems: list[str] = []
    warnings: list[str] = []
    cv2.imwrite(str(png), base, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    saved = cv2.imread(str(png))
    ver = composite.verify_outside(src, saved, union)
    out_crop = composite.take(saved, rect)
    cv2.imwrite(str(crop_jpg), resized_for_send(out_crop), [cv2.IMWRITE_JPEG_QUALITY, 95])
    res = identity.score_image(out_crop, pool, scorer, exclude_names=dups, expect_box=main_in_crop)
    m: dict = {"file": png.name, "elapsed_sec": round(time.time() - t0, 1)}
    if res.get("detected"):
        fs_s = max(src_eval["box"][2:])
        m.update({"score": round(res["score"], 3), "top": res["top"], "face_w": res["face_w"],
                  "gt_sim": round(float(np.dot(src_eval["emb"], res["emb"])), 3),
                  "shape_dist": round(identity.shape_distance(src_eval["shape"], res["shape"]), 3),
                  "face_shift_frac": round(float(np.hypot(res["box"][0] + res["box"][2] / 2 - (src_eval["box"][0] + src_eval["box"][2] / 2),
                                                          res["box"][1] + res["box"][3] / 2 - (src_eval["box"][1] + src_eval["box"][3] / 2))) / fs_s, 3),
                  "size_ratio": round(res["box"][2] / max(1, src_eval["box"][2]), 3),
                  "sharp_ratio": round(res["sharpness"] / max(1.0, src_eval["sharpness"]), 3),
                  "source_score": round(src_eval["score"], 3)})
    if zone_mode != "head+build":
        m["drift"] = composite.inside_drift(src, saved, rect, [tuple(b) for b in head_boxes])
        dr = m["drift"]
        if dr["mean_abs_diff"] is not None and (dr["mean_abs_diff"] > DRIFT_MAD_MAX or dr["ssim"] < DRIFT_SSIM_MIN):
            problems.append(f"clothes or background inside the crop were redrawn (mean diff {dr['mean_abs_diff']}, SSIM {dr['ssim']})")
    if not ver["same_size"] or ver["changed_outside"] != 0:
        problems.append(f"{ver['changed_outside']} px changed outside the crop")
    if "score" not in m:
        problems.append("no face detected in the output crop")
    else:
        lo, hi = gates["size_own"] if source_kind == "own" else gates["size_foreign"]
        if not (lo <= m["size_ratio"] <= hi):
            problems.append(f"head size changed (size_ratio {m['size_ratio']}, allowed {lo}-{hi})")
        if m["face_shift_frac"] > SHIFT_MAX:
            problems.append(f"head moved (face_shift {m['face_shift_frac']} > {SHIFT_MAX})")
        # Light on the face vs the source face. The limit is looser for another man's photo, because his skin legitimately
        # differs from the user's (14 for his own photos, 20 for another man's).
        m["light"] = composite.light_delta(src_crop, out_crop, src_eval["box"])
        lt = m["light"]
        light_max = gates["light_de_max"] if source_kind == "own" else gates["light_de_max_foreign"]
        if lt["dE"] > light_max:
            problems.append(f"face is lit differently from the source (light dE {lt['dE']} > {light_max}, dL {lt['dL']:+}: "
                            "rendered brighter and cleaner than the photo)")
        # far faces only: a kayak picture the user called perfect (P-06, 219 px face) measures 8.3x; every table-tennis render 7-60x
        if far and m.get("sharp_ratio") is not None and m["sharp_ratio"] > gates["sharp_max"]:
            problems.append(f"face is much sharper than the photo (sharpness x{m['sharp_ratio']} > {gates['sharp_max']:g}): it reads as pasted in")
        # Neck gap: the face must not be brighter than its own neck by more than in the source (the cut-and-paste look).
        gap_out = face_neck_gap(out_crop, res["box"]) if src_gap is not None else None
        if gap_out is not None:
            m["neck_gap"] = round(gap_out - src_gap, 1)
            if m["neck_gap"] > gates["neck_gap_max"]:
                problems.append(f"face is brighter than the neck ({m['neck_gap']:+} more than in the source, limit {gates['neck_gap_max']:g}): "
                                "the head reads as pasted in")
        else:
            warnings.append("face and neck lightness could not be measured, so the neck-gap check was skipped")
        # Unchanged: a look-alike source returned as it is (gt_sim 0.93-0.99 for what the user called "as it is", 0.23-0.75 for what he approved).
        if expression_edit:
            # zone expression (the user's approval, 2026-10-10): his own photo keeps his own face by design, so the 'returned unchanged' gate
            # is replaced by the judge's 'expression changed' check (judge_failures)
            m["unchanged_gate"] = "skipped: expression edit"
        elif source_kind == "own" and m["gt_sim"] > gates["unchanged_gt_sim"]:
            problems.append(f"face returned unchanged (similarity to the source face {m['gt_sim']} > {gates['unchanged_gt_sim']:g})")
    return m, problems, warnings, ver, saved, out_crop


async def judge_candidate(client, text_models: list, source_file: Path, cand_file: Path, log, cand: dict, problems: list[str], warnings: list[str],
                          m: dict, thr: dict, expression: str, source_kind: str, glasses: str = "same", expression_edit: bool = False,
                          source_glasses: bool | None = None) -> dict | None:
    """The AI judges what code cannot (angle, glasses, seam, lighting, anything else changed); for his own photo it also compares the face with the
    source face in both orders (ranking only). Appends to problems / warnings in place and records both on the candidate. Moved out of run()
    unchanged on 2026-10-08."""
    judge = await gemini_text(client, text_models, JUDGE_PROMPT, [source_file, cand_file], log, "judge")
    cand["judge"] = judge
    hard, soft = judge_failures(judge, expression_must_match=(expression == "same" and not expression_edit), glasses_policy=glasses,
                                expression_edit=expression_edit, source_glasses=source_glasses)
    problems += hard
    warnings += soft
    # His own or look-alike photo: the AI compares the rendering with the SOURCE face, both orders. A candidate the AI prefers the source over is
    # no improvement. Asked only when everything else passed, so the text calls are not spent on candidates that are rejected anyway.
    if source_kind == "own" and not problems and m.get("score", 0) >= thr["hard_reject"]:
        who, whys = await face_pair(client, text_models, source_file, cand_file, log)
        cand["face_vs_source"] = {"winner": {"a": "source", "b": "candidate", "tie": "tie"}[who], "why": whys}
        log.say(f"  face comparison against the source: {cand['face_vs_source']['winner']} ({'; '.join(w_ for w_ in whys if w_)})")
        if who == "a":
            # Ranking only (2026-09-21): as a veto it rejected car2 attempt 1, whose face the user rated an improvement in both
            # attractiveness and identity, and the probe showed this question agrees with the user in 1 of 3 cases.
            warnings.append("AI: the source rendering looked better than this face (ranking only, not a gate)")
    cand["problems"], cand["warnings"] = problems, warnings
    return judge


def verdict_of(problems: list[str], m: dict, thr: dict) -> str:
    if problems:
        return "invalid"
    if m["score"] >= thr["accept"]:
        return "accept"
    return "uncertain" if m["score"] >= thr["hard_reject"] else "reject"


# ---------------------------------------------------------------------------------------------- main
async def face_pair(client, models: list[str | None], file_a: Path, file_b: Path, log: RunLog, prompt: str | None = None) -> tuple[str, list]:
    """The AI's pairwise choice between two renderings, asked in BOTH orders so position bias cancels: returns ("a", "b" or "tie", the reasons).
    A split answer, or no answer, is a tie."""
    r1 = await gemini_text(client, models, prompt or FACE_PAIR_PROMPT, [file_a, file_b], log, "pair")
    r2 = await gemini_text(client, models, prompt or FACE_PAIR_PROMPT, [file_b, file_a], log, "pair")
    v1, v2 = (r1 or {}).get("better"), (r2 or {}).get("better")
    first = "a" if v1 == 1 else "b" if v1 == 2 else None      # order (a, b)
    second = "b" if v2 == 1 else "a" if v2 == 2 else None      # order (b, a)
    whys = [(r1 or {}).get("why"), (r2 or {}).get("why")]
    return (first if first is not None and first == second else "tie"), whys


async def rank_by_face(client, models: list[str | None], run_dir: Path, cands: list[dict], log: RunLog, prompt: str | None = None) -> dict[int, float]:
    """Score the passing candidates by the AI's pairwise choice of the better face (wins per attempt index).

    Every pair is asked in BOTH orders (position bias cancels; a split answer counts as a tie). Wins decide, ties fall back to the
    identity score. The AI does the visual judgement it was validated for; nothing about the images is changed.
    """
    wins = {c["index"]: 0.0 for c in cands}
    log_pairs = []
    for a in range(len(cands)):
        for b in range(a + 1, len(cands)):
            ca, cb = cands[a], cands[b]
            fa, fb = run_dir / f"cand{ca['index']}_crop.jpg", run_dir / f"cand{cb['index']}_crop.jpg"
            r1 = await gemini_text(client, models, prompt or FACE_PAIR_PROMPT, [fa, fb], log, "pair")
            r2 = await gemini_text(client, models, prompt or FACE_PAIR_PROMPT, [fb, fa], log, "pair")
            v1 = (r1 or {}).get("better")
            v2 = (r2 or {}).get("better")
            first = ca["index"] if v1 == 1 else cb["index"] if v1 == 2 else None      # order (a, b)
            second = cb["index"] if v2 == 1 else ca["index"] if v2 == 2 else None      # order (b, a)
            if first is not None and first == second:
                wins[first] += 1.0
                verdict = f"attempt {first}"
            else:
                wins[ca["index"]] += 0.5
                wins[cb["index"]] += 0.5
                verdict = "tie (the two orders disagreed or no answer)"
            log_pairs.append({"a": ca["index"], "b": cb["index"], "orders": [first, second], "winner": verdict,
                              "why": [(r1 or {}).get("why"), (r2 or {}).get("why")]})
            log.say(f"  face comparison attempt {ca['index']} vs {cb['index']}: {verdict}")
    log.data["face_ranking"] = {"wins": wins, "pairs": log_pairs}
    return wins


async def run(args) -> int:
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    thr = thresholds(config)
    gates = gate_values(config)
    model = args.model or config.get("model")
    text_models = [config.get("vision_model") or model, model]
    src_path = Path(args.scene)
    if not src_path.is_file():
        print(f"Scene photo not found: {src_path}")
        return 1
    src = load_source(src_path)
    H, W = src.shape[:2]
    src_md5 = hashlib.md5(src_path.read_bytes()).hexdigest()
    best_version = next((k for k, v in (config.get("best_versions") or {}).items() if isinstance(v, dict) and v.get("md5") == src_md5), None)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / config.get("out_dir", "outputs") / f"{stamp}_replicate_{src_path.stem[:30]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log = RunLog(run_dir, {"timestamp": stamp, "scene": str(src_path), "size": [W, H], "args": vars(args) | {"func": None},
                           "thresholds": thr, "gates": gates, "text_models": text_models, "candidates": [], "status": "started"})
    log.say(f"run dir: {run_dir}")
    try:      # what the run ran with (code, packages, models, gate limits): the same env record the staged runner keeps (2026-10-07)
        import provenance
        log.data["env"] = provenance.env_snapshot(config)[0]
        log.save()
    except Exception as exc:
        log.say(f"  [env] not recorded: {exc}")
    if best_version and not args.force:
        # The user (2026-09-23) on beach.jpg: "it was already perfect and was being used as reference, hence it wasn't required to change again".
        cv2.imwrite(str(run_dir / "best.png"), src, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        cv2.imwrite(str(run_dir / "best.jpg"), src, [cv2.IMWRITE_JPEG_QUALITY, 97])
        log.data.update({"status": "already_best_version", "best_version": best_version, "best": None})
        log.say(f"This photo is one of your best versions ({best_version}): returned unchanged as best.png / best.jpg. Pass --force to re-render it.")
        log.save()
        return 0
    if not thr["approved"]:
        log.say(f"NOTE: identity thresholds are PROPOSED, not approved: hard_reject<{thr['hard_reject']}, accept>={thr['accept']}")

    scorer = ArcFaceScorer()
    pool = identity.build_pool(config, scorer, verbose=False)
    src_res = identity.score_image(src, pool, scorer)
    if not src_res.get("detected"):
        log.say("No face detected in the source photo.")
        log.data["status"] = "no_face"
        log.save()
        return 1
    dups = identity.duplicates_of(src_res["emb"], pool)
    src_res = identity.score_image(src, pool, scorer, exclude_names=dups)
    log.say(f"source: {W}x{H}, face {src_res['face_w']}px, similarity to the pool {src_res['score']:.3f} "
            f"(excluding {sorted(dups) or 'no duplicates'})")

    source_kind = args.source
    if source_kind == "auto":
        source_kind = "own" if src_res["score"] >= thr["own_min"] else "foreign"
        log.say(f"source classified as {source_kind.upper()} (own if score >= {thr['own_min']})")
        if 0.20 <= src_res["score"] < 0.50:
            log.say(f"  NOTE: a similarity of {src_res['score']:.3f} is in the gray zone: a small, turned or blurry face scores low even "
                    "when it is you (your own table-tennis photo scored 0.40). If this classification is wrong, pass --source own or "
                    "--source foreign.")
    zone_mode = args.zone
    if zone_mode == "auto":
        zone_mode = "face" if source_kind == "own" else "head"
    if source_kind == "own":
        # Applied anyway (the user, 2026-09-21: "just apply it", never skip on the pipeline's own choice): a look-alike is replaced by the real
        # face, a real photo is re-rendered at its best.
        log.say(f"This photo already looks like you (similarity {src_res['score']:.3f}); applying the pipeline anyway (--force is no longer needed).")
    log.data.update({"source_kind": source_kind, "zone_mode": zone_mode, "duplicates_excluded": sorted(dups)})
    kind = "face" if zone_mode == "face" else "head"
    # Expression: the attractiveness policy suits his own photos (approved kayak and rocky). Another man's photo is a reference whose expression
    # is the target (user, 2026-09-20: cand3's calm closed mouth did not match the reference, which has a subtle smile; the same-expression
    # run was called closer).
    expression = args.expression or ("same" if source_kind == "foreign" else "auto")
    log.data["expression_policy"] = expression
    log.say(f"expression policy: {expression}" + (" (the reference photo's own; --expression auto forces the attractiveness policy)"
                                                  if expression == "same" and not args.expression else ""))

    # ---- ONE crop: the main head plus any other copy of the face (a window reflection is a real second face). The user
    # judged the single-pass render of both faces (060631) "perfect" and the separate reflection stage (063313) as not
    # mirroring him at all, so a reflection is never edited in its own call.
    main_box = src_res["box"]
    main_rect, _ = crop_for_face(src.shape, main_box, kind)
    far = main_box[2] < FAR_FACE_PX
    if far:
        log.say(f"far from the camera: face {main_box[2]} px wide (< {FAR_FACE_PX}); wider crop {main_rect[2]} px, sent upscaled x{SEND_PX / main_rect[2]:.2f}")
    log.data["far_face"] = far
    if not far:
        head = None
        try:
            async with authenticated_client(verbose=args.verbose) as hc:
                head = await read_head_box(hc, text_models, src, main_box, run_dir, log)
        except Exception as e:  # the usual crop is kept; the main client below reports login and quota problems properly
            log.say(f"head box reading skipped: {type(e).__name__}: {e}")
        log.data["head_box_ai"] = None if head is None else [round(v) for v in head]
        grown = fit_whole_head(src.shape, main_rect, head) if head is not None else None
        if grown is not None:
            log.say(f"the crop {main_rect[2]} px cut his head (hair included, AI box {[round(v) for v in head]}); grown to {grown[2]} px so the whole "
                    f"head is inside, sent x{SEND_PX / grown[2]:.2f}")
            log.data["crop_before_head_fit"] = list(main_rect)
            main_rect = grown
        elif head is not None:
            log.say(f"his whole head (AI box {[round(v) for v in head]}) is inside the crop; crop unchanged")
    head_boxes: list[tuple[int, int, int, int]] = [main_box]
    rects = [main_rect]
    copies_left: list[tuple[int, int, int, int]] = []
    for f in find_identity_faces(src, scorer, pool, src_res["emb"], dups)[1:]:
        if f.get("role") != "copy":
            log.say(f"  other face at {f['box']} ({f['face_w']}px, similarity to you {f.get('sim_to_main')}): left untouched")
            continue
        r_c, _ = crop_for_face(src.shape, f["box"], "face")
        u = union_rect(rects + [r_c])
        if max(u[2], u[3]) > UNION_MAX * SEND_PX:
            copies_left.append(f["box"])
            log.say(f"  WARNING second copy of your face at {f['box']} ({f['face_w']}px) is too far from the main face to share one "
                    "crop; the OLD face stays visible there")
            continue
        rects.append(r_c)
        head_boxes.append(f["box"])
        log.say(f"  second copy of your face at {f['box']} ({f['face_w']}px, similarity {f['sim_to_main']}): inside the same crop")
    rect = snap_aspect(union_rect(rects), src.shape) if len(rects) > 1 else main_rect
    src_crop = composite.take(src, rect)
    main_in_crop = (main_box[0] - rect[0], main_box[1] - rect[1], main_box[2], main_box[3])  # the face to measure in every crop
    log.say(f"crop {rect[2]}x{rect[3]} at ({rect[0]}, {rect[1]}); {len(head_boxes)} face(s) of you inside")
    log.data.update({"crop": list(rect), "head_boxes": [list(b) for b in head_boxes], "copies_left_unedited": [list(b) for b in copies_left]})
    cv2.imwrite(str(run_dir / "source_crop.png"), resized_for_send(src_crop))

    by_name = {e.name: e for e in pool}
    build_refs: list[Path] = []
    if zone_mode == "head+build":
        for n in config.get("build_refs", ["IMG_6923 Copy.JPG", "IMG_6858.jpg", "IMG_6864.jpg", "IMG_6862.jpg"]):
            if n in by_name and n not in dups:
                build_refs.append(whole_ref(by_name[n].path))
        log.say(f"physique refs: {[p.name for p in build_refs]}")

    # ---- measurements of the source crop, taken once
    src_eval = identity.score_image(src_crop, pool, scorer, exclude_names=dups, expect_box=main_in_crop)
    if not src_eval.get("detected"):
        src_eval = src_res
    attractiveness = config.get("attractiveness_note") or DEFAULT_ATTRACTIVENESS
    log.data["attractiveness_note"] = attractiveness if expression in ("auto", "none") else None

    candidates: list[dict] = []
    expr_wins: dict[int, float] = {}
    passing = attempts = 0
    scene: dict | None = None
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            log.meter = CreditMeter(client, log.say)
            log.say(log.meter.preflight(args.max_attempts))
            log.data["credits"] = log.meter.as_dict()
            if expression != "none":
                scene = await gemini_text(client, text_models, DESCRIBE_PROMPT, [run_dir / "source_crop.png"], log, "describe")
                log.say(f"scene as read by Gemini: {json.dumps(scene, ensure_ascii=False) if scene else 'no usable answer (edit prompt has no description)'}")
                log.data["scene_reading"] = scene
                if (expression == "auto" and not args.expression and source_kind == "own" and scene
                        and LAUGH_WORDS.search(str(scene.get("expression") or ""))):
                    expression = "same"
                    log.data.update({"expression_policy": expression, "attractiveness_note": None})
                    log.say(f"expression policy: same (the source shows a laugh or broad smile: \"{scene.get('expression')}\"; it is kept)")
            # ---- identity references: head crops nearest in head shape (never the source photo itself). Frontal anchors
            # help skin tone and eyes, but pull a strongly turned head toward the camera, so the AI's own reading of the
            # turn decides whether they are sent.
            turn = turn_degrees(scene)
            skip_anchors = turn is not None and turn >= ANCHOR_TURN_MAX
            src_pose_read = await gemini_text(client, text_models, POSE_PROMPT, [run_dir / "source_crop.png"], log, "pose")
            src_pose = pose_of(src_pose_read)
            log.data["source_pose"] = src_pose_read
            chosen: list[tuple[str, Path, tuple | None, str]] = []
            if src_pose is not None:
                # Any angle (plan of 2026-09-23): the references nearest in pose as the AI reads it, the studio look preferred within STUDIO_BONUS
                # degrees; his own photo only when nothing else is within SELF_MAX; the missing angle rendered from the studio photos.
                exclude = set(config.get("ref_exclude", ["IMG_6923 Copy.JPG"]))
                cands = []
                for e in pool:
                    if e.name in exclude:
                        continue
                    try:
                        crop_p = head_ref_crop(e.path, scorer)
                    except Exception:
                        continue
                    p_ = pose_of(await ref_pose(client, text_models, crop_p, log))
                    if p_ is None:
                        continue
                    is_self = e.name in dups or e.path.stem.lower() == src_path.stem.lower()
                    cands.append((e.name, crop_p, p_, "self" if is_self else ("studio" if STUDIO_RE.match(e.name) else "photo")))
                # the angle library (angle_refs.py): every render kept so far, at any pose, is a candidate too
                for index in sorted(SYN_DIR.glob("*/index.json")):
                    for k_ in json.loads(index.read_text(encoding="utf-8")):
                        if (index.parent / k_["name"]).exists():
                            cands.append((k_["name"], index.parent / k_["name"], tuple(k_["pose"]), "rendered"))
                others = [c for c in cands if c[3] != "self"]
                nearest = min((pose_distance(c[2], src_pose) for c in others), default=999.0)
                if nearest > SELF_MAX:
                    studio = [c for c in others if c[3] == "studio"]
                    try:
                        for nm, pth, ps in await synthetic_refs(client, model, text_models, src_pose, (src_pose_read or {}).get("camera"), studio,
                                                                pool, scorer, run_dir, log, args.verbose):
                            cands.append((nm, pth, ps, "rendered"))
                    except UsageLimitExceededError:
                        raise
                    others = [c for c in cands if c[3] != "self"]
                    nearest = min((pose_distance(c[2], src_pose) for c in others), default=999.0)
                pickable, seen_ = [], set()
                for c in cands:
                    if (c[3] != "self" or nearest > SELF_MAX) and str(c[1]) not in seen_:
                        seen_.add(str(c[1]))
                        pickable.append(c)
                key_ = lambda c: pose_distance(c[2], src_pose) - (STUDIO_BONUS if c[3] in ("studio", "rendered") else 0.0)
                chosen = sorted(pickable, key=key_)[:4]
                if source_kind == "own" and config.get("own_photo_as_reference", False):
                    # OFF since 2026-09-26 (checklist item 28: face, hair and beard only from his references, never from the goal; table
                    # tennis v5 took the photo's short cut and a different beard). Before: his own photo was always the FIRST reference (the user chose this 2026-09-24; loop v2 of 2026-09-26). Without it the face
                    # came back at the references' pose and hair under the photo's own head: rocky 183350 "lasso-ed" (4 renders labelled
                    # chin +30, really near level), table tennis 192017 (a curly mop and a lifted chin on a short-haired, bowed head). Every
                    # rocky picture the user liked (mt1, P-04, P-05) had rocky itself among its references.
                    try:
                        self_p = head_ref_crop(src_path, scorer)
                        chosen = [(src_path.name, self_p, src_pose, "self")] + [c for c in chosen if c[3] != "self"][:3]
                    except Exception as e_:
                        log.say(f"  (the source photo could not be cropped as a reference: {type(e_).__name__}: {e_})")
            if chosen:
                ref_names = [c[0] for c in chosen]
                head_refs = [c[1] for c in chosen]
                log.say(f"source pose (AI): turn {src_pose[0]:+.0f}, chin {src_pose[1]:+.0f}, camera {(src_pose_read or {}).get('camera')}")
                log.say("identity refs by pose: " + ", ".join(f"{c[0]} ({c[3]}, turn {c[2][0]:+.0f} chin {c[2][1]:+.0f})" for c in chosen))
                log.data["identity_refs_pose"] = [{"name": c[0], "kind": c[3], "pose": list(c[2])} for c in chosen]
            else:
                # no pose reading: the head-shape choice of before
                near = identity.nearest_by_shape(src_res["shape"], pool, n=4 if skip_anchors else 3, exclude_names=dups)
                ref_names = [e.name for e, _ in near]
                if not skip_anchors:
                    for anchor in config.get("anchors", ["IMG_6873.jpg", "IMG_6858.jpg"]):
                        if anchor not in ref_names and anchor not in dups and anchor in by_name:
                            ref_names.append(anchor)
                head_refs = [head_ref_crop(by_name[n].path, scorer) for n in ref_names]
                log.say(f"identity refs (head crops, no pose reading): {', '.join(ref_names)}")
            log.data["identity_refs"] = ref_names
            retry_note: str | None = None
            good_face: dict | None = None      # best rendered face so far: it gets placed into the complete picture by the next attempts
            rescues = 0
            returned_unchanged = False         # a placement handed the source back untouched: the last placement blurs the head out
            src_gap = face_neck_gap(src_crop, src_eval["box"])
            log.data["source_face_neck_gap"] = None if src_gap is None else round(src_gap, 1)

            while passing < args.count and attempts < args.max_attempts:
                attempts += 1
                i = attempts
                t0 = time.time()
                log.say(f"\n== attempt {attempts}/{args.max_attempts} (want {args.count} passing, have {passing})")
                cand: dict = {"index": i, "stages": []}
                candidates.append(cand)
                log.data["candidates"] = candidates
                base = src.copy()
                union = np.zeros((H, W), np.uint8)
                try:
                    if zone_mode == "head+build":
                        prect = person_rect(base.shape, main_box)
                        base, z, meta = await edit_stage(client, model, log, run_dir, f"c{i}_build", base, prect,
                                                         build_prompt(len(build_refs), args.build), build_refs, args.verbose)
                        cand["stages"].append(meta)
                        if z is not None:
                            union = np.maximum(union, z)
                        log.say(f"  build stage: {meta.get('failed') or ('ecc ' + str(meta['ecc']) + ', ' + meta['aligned_by'])}")

                    if not any("failed" in s for s in cand["stages"]):
                        use_rescue = good_face is not None and rescues < gates["rescue_attempts"]
                        stage_refs = head_refs + ([good_face["head"]] if use_rescue else [])
                        prompt = edit_prompt(len(stage_refs), kind, args.glasses, args.look, scene, expression, attractiveness, retry_note, far=far,
                                             whole_head=(kind == "face"), face_share=(main_in_crop[3] / rect[3] if far else None),
                                             reflection=len(head_boxes) > 1, rescue=use_rescue)
                        if use_rescue:
                            rescues += 1
                            cand["placement_of_attempt"] = good_face["index"]
                            log.say(f"  placement {rescues}/{gates['rescue_attempts']}: the face of attempt {good_face['index']} "
                                    f"(identity {good_face['score']}) goes in as a head crop")
                            if returned_unchanged and rescues >= gates["rescue_attempts"]:
                                # An earlier placement handed the source crop back untouched: send it with the head blurred out, so there is no
                                # source face left to copy while the head's place and size still show. Input preparation only.
                                try:
                                    from pose_refs import mask_head_from_scene
                                    blur_src = run_dir / "raw" / f"c{i}_blurred_source.jpg"
                                    cv2.imwrite(str(run_dir / "raw" / f"c{i}_source_for_blur.jpg"), src_crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                                    mask_head_from_scene(run_dir / "raw" / f"c{i}_source_for_blur.jpg", blur_src)
                                    base = src.copy()
                                    base[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = cv2.imread(str(blur_src))
                                    cand["blurred_head_escalation"] = True
                                    log.say("    and the head in the crop sent is blurred out, so there is no old face to copy")
                                except Exception as e_:
                                    log.say(f"    (blurred-head escalation skipped: {type(e_).__name__}: {e_})")
                        base, z, meta = await edit_stage(client, model, log, run_dir, f"c{i}_head", base, rect, prompt, stage_refs, args.verbose)
                        cand["stages"].append(meta)
                        if z is not None:
                            union = np.maximum(union, z)
                        log.say(f"  head stage: {meta.get('failed') or ('ecc ' + str(meta['ecc']) + ', warp ' + str(meta['warp']) + ', ' + meta['aligned_by'])}")
                except UsageLimitExceededError:
                    raise
                except Exception as e:  # keep the batch going; the failure is recorded
                    cand["error"] = f"{type(e).__name__}: {e}"
                    log.say(f"  FAILED: {cand['error']}")
                    log.save()
                    continue

                problems, warnings = [], []
                for s in cand["stages"]:
                    if "failed" in s:
                        problems.append(f"{s['stage']}: {s['failed']}")
                if problems:
                    cand["problems"], cand["verdict"] = problems, "invalid"
                    for p_ in problems:
                        log.say(f"    FAIL: {p_}")
                    retry_note = ("the returned picture was framed differently from the last image (zoomed or shifted); return it with exactly "
                                  "the same framing, crop and scale as the last image")
                    log.data["candidates"] = candidates
                    log.save()
                    continue

                # ---- save lossless, verify on the saved file, measure (measure_candidate: the same code the recipe method replicate/1 uses)
                png = run_dir / f"cand{i}.png"
                m, more, warnings, ver, saved, out_crop = measure_candidate(src, base, rect, union, src_crop, src_eval, pool, scorer, dups, gates,
                                                                            source_kind, far, head_boxes, src_gap, zone_mode, main_in_crop, png,
                                                                            run_dir / f"cand{i}_crop.jpg", t0)
                problems += more
                cand["outside_check"] = ver
                cand["metrics"] = m

                # ---- the AI judges what code cannot: angle, glasses, seam, lighting, anything else changed
                judge = await judge_candidate(client, text_models, run_dir / "source_crop.png", run_dir / f"cand{i}_crop.jpg", log, cand, problems,
                                              warnings, m, thr, expression, source_kind)
                cand["verdict"] = verdict_of(problems, m, thr)
                if cand["verdict"] in ("accept", "uncertain"):
                    passing += 1
                else:
                    retry_note = retry_note_from(problems, judge)
                    if cand.get("placement_of_attempt") and m.get("gt_sim", 0) > gates["unchanged_gt_sim"]:
                        returned_unchanged = True      # this placement handed the source crop back: the last one will blur the head out
                # THE RULE: a face worth having is kept and placed into the complete picture, whatever the composite failed on. Judged on the face
                # alone (good_face_in); code never warps or pastes that face, the AI places it.
                raw_rel = cand["stages"][-1].get("raw") if cand["stages"] else None
                if raw_rel and (good_face is None or m.get("score", 0) > good_face["score"]):
                    gf = good_face_in(run_dir / raw_rel, pool, scorer, dups, thr, source_kind == "own", judge, expression == "same",
                                      composite_gt_sim=m.get("gt_sim"), unchanged_gt=gates["unchanged_gt_sim"])
                    if gf and (good_face is None or gf["score"] > good_face["score"]):
                        head = raw_head_crop(gf["raw"], run_dir / "raw" / f"good_face_head_{i}.jpg")
                        if head is not None:
                            cand["good_face"] = {"score": gf["score"], "head": head.name}
                            good_face = {"index": i, "score": gf["score"], "head": head}
                            if cand["verdict"] not in ("accept", "uncertain"):
                                log.say(f"  the face of this attempt is worth keeping (identity {gf['score']}): its head crop will be placed into the picture")

                log.say(f"  outside-crop changed px: {ver['changed_outside']}")
                log.say(f"  score={m.get('score')} gt_sim={m.get('gt_sim')} shape_dist={m.get('shape_dist')} size_ratio={m.get('size_ratio')} "
                        f"face_shift={m.get('face_shift_frac')} sharp_ratio={m.get('sharp_ratio')} light={m.get('light')} "
                        f"drift={m.get('drift')} neck_gap={m.get('neck_gap')} -> {cand['verdict'].upper()}")
                log.say(f"  AI judge: {json.dumps(judge, ensure_ascii=False) if judge else 'no answer'}")
                for p_ in problems:
                    log.say(f"    FAIL: {p_}")
                for w_ in warnings:
                    log.say(f"    warn: {w_}")

                if zone_mode == "head+build":
                    try:
                        cand["physique"] = physique_report(src, saved, main_box)
                        log.say(f"  physique widths source {list(cand['physique']['source_px'].values())} -> output "
                                f"{list(cand['physique']['output_px'].values())} px")
                    except Exception as e:
                        cand["physique"] = {"error": f"{type(e).__name__}: {e}"}

                # ---- compare sheets
                a, b = src_crop, out_crop
                d = np.clip(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(axis=2) * 4, 0, 255).astype(np.uint8)
                ov = a.copy()
                bd = max(2, int(min(a.shape[:2]) * BORDER_FRAC))
                cv2.rectangle(ov, (bd, bd), (a.shape[1] - bd, a.shape[0] - bd), (0, 200, 0), 3)
                T = 512
                panels = [cv2.resize(p_, (T, int(T * p_.shape[0] / p_.shape[1]))) for p_ in (a, b, cv2.applyColorMap(d, cv2.COLORMAP_JET), ov)]
                cv2.imwrite(str(run_dir / f"compare_head_{i}.jpg"), np.hstack(panels), [cv2.IMWRITE_JPEG_QUALITY, 90])
                s_ = 900 / max(H, W)
                pair = np.hstack([cv2.resize(src, None, fx=s_, fy=s_, interpolation=cv2.INTER_AREA),
                                  cv2.resize(saved, None, fx=s_, fy=s_, interpolation=cv2.INTER_AREA)])
                cv2.imwrite(str(run_dir / f"compare_full_{i}.jpg"), pair, [cv2.IMWRITE_JPEG_QUALITY, 90])
                log.save()

            # ---- several candidates passed the objective gates: the AI picks the better expression, pair by pair, in both orders
            passing_now = [c for c in candidates if c.get("verdict") in ("accept", "uncertain") and c.get("metrics", {}).get("file")]
            if len(passing_now) >= 2:
                log.say(f"\n{len(passing_now)} candidates passed; asking Gemini which has the better face (each pair in both orders)")
                expr_wins = await rank_by_face(client, text_models, run_dir, passing_now, log)
                log.save()
            await log.meter.settle()
            log.data["credits"] = log.meter.as_dict()
            log.say(log.meter.summary())
            log.save()
    except UsageLimitExceededError as e:
        log.say(f"Gemini quota reached, stopping the batch: {e}")
        meter = getattr(log, "meter", None)
        if meter is not None:
            log.say(f"[Credits] at the stop: {describe_usage(meter.info)}")
        log.data["status"] = "usage_limit"
    except AuthError as e:
        log.say(str(e))
        log.data["status"] = "auth_error"
        log.save()
        return 1

    log.data["attempts"] = attempts
    ranked = [c for c in candidates if c.get("verdict") in ("accept", "uncertain")]
    # Round 7: gt_sim (the similarity to the SOURCE face) is no longer part of the key. For his own or look-alike photos it made the candidate closest to
    # the source win, so a better face was never rewarded (nerd, beach, night out came back "as it is", 2026-09-21).
    # Order: the AI's pairwise face wins first, then the identity band (accept > uncertain) as a tiebreak, then the identity number.
    # The band used to come first; that let "accept" (score >= 0.52) beat a candidate the AI and the user both preferred, although the
    # calibration shows the score cannot tell good from bad below 0.52, and a 0.96 similarity to the source only means the face was
    # barely edited (stained-glass run 151934: the user's promising attempt 1 lost to an almost untouched attempt 3).
    rank = {"accept": 2, "uncertain": 1}
    key = (lambda c: (expr_wins.get(c["index"], 0.0), rank[c["verdict"]], c["metrics"]["score"]))
    def complete_picture(path: Path) -> np.ndarray:
        """Read a candidate and prove it is a COMPLETE picture before it can be called a result: the source's dimensions, and nothing changed
        outside the edited crop. A rendered head (a raw return) can never pass this, which is the rule."""
        img_ = cv2.imread(str(path))
        assert img_ is not None and img_.shape == src.shape, f"{path.name} is not a complete picture ({None if img_ is None else img_.shape} vs {src.shape})"
        x0, y0, cw, ch = rect
        outside = np.ones(src.shape[:2], bool)
        outside[y0:y0 + ch, x0:x0 + cw] = False
        assert not (src[outside] != img_[outside]).any(), f"{path.name} changed pixels outside the crop"
        return img_

    if ranked:
        best = max(ranked, key=key)
        img = complete_picture(run_dir / best["metrics"]["file"])
        cv2.imwrite(str(run_dir / "best.png"), img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        cv2.imwrite(str(run_dir / "best.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
        log.data["best"] = {"candidate": best["index"], "verdict": best["verdict"],
                            **{k: best["metrics"].get(k) for k in ("score", "gt_sim", "shape_dist", "size_ratio")}}
        why = (f"; AI face wins {expr_wins}" if expr_wins else "")
        log.say(f"\n[BEST] attempt {best['index']} ({best['verdict']}) after {attempts} attempts{why} -> best.png / best.jpg")
        # The user's rule (2026-09-26): this is a CANDIDATE. Nothing is called best until BEST_CHECKLIST.md passes by eye (tools/best_check.py);
        # one failed item and it goes back into the loop with think-again.
        log.say("  candidate only: not best until every item of BEST_CHECKLIST.md passes by eye (tools\\best_check.py)")
    else:
        # Nothing passed every gate. Keep the closest candidate visible for the user's own eye, clearly labelled as not passing.
        usable = [c for c in candidates if c.get("metrics", {}).get("score") is not None and c["metrics"].get("file")
                  and not any("changed outside" in p for p in c.get("problems", []))]
        if usable:
            # the candidate closest to passing: the smallest total distance outside the gates, then identity (loop v3, 2026-09-26)
            near = min(usable, key=lambda c: (gate_excess(c, gates, source_kind), -c["metrics"]["score"]))
            img = complete_picture(run_dir / near["metrics"]["file"])
            cv2.imwrite(str(run_dir / "not_passing_closest.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
            log.data["not_passing_closest"] = {"candidate": near["index"], "problems": near.get("problems"),
                                               "gate_excess": round(gate_excess(near, gates, source_kind), 3)}
            log.say(f"\nNo candidate passed every gate in {attempts} attempts. The closest one (attempt {near['index']}; "
                    f"{'; '.join(near.get('problems', []))}) is saved as not_passing_closest.jpg for your review. Nothing was promoted to best.png.")
        else:
            log.say(f"\nNo candidate passed in {attempts} attempts and none produced a usable image. Every attempt and reason is above.")
    log.data["status"] = log.data.get("status") if log.data.get("status") not in ("started", None) else "done"
    log.save()
    # End hook of the skill (the user, 2026-10-01): copy the picture out of outputs/ into the named, versioned results folder.
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
    from export_results import safe_export
    safe_export(run_dir)
    return 0
