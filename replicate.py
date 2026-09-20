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
from gemini_webapi.exceptions import GeminiError, ImageGenerationError, UsageLimitExceededError
from scorer import DETECTOR_PATH, ArcFaceScorer, analyze_face
from session import AuthError, authenticated_client

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
SIZE_MIN, SIZE_MAX = 0.85, 1.15   # output head width over source head width (own photos)
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
            "light_de_max_foreign": float(g.get("light_de_max_foreign", LIGHT_DE_MAX_FOREIGN))}


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

# Pairwise expression comparison. Measured 2026-09-20: asked to RATE one image the judge gave the user's "awkward" and "perfect emotion"
# kayak outputs the same 6/10; asked to COMPARE the two, in both orders, it picked the one the user preferred 4 of 4 times.
EXPRESSION_PAIR_PROMPT = (
    "Both images show the same man in the same photo, but with two different renderings of his face. Which image shows the more "
    "relaxed, natural, confident and attractive facial expression, like a flattering candid photo? Ignore lighting and sharpness; judge "
    "only the expression (mouth, eyes, brows, tension). Reply with ONLY a JSON object: {\"better\": 1 or 2, \"why\": one short sentence}")


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
                out = await client.generate_content(prompt, files=[str(f) for f in files], model=model, temporary=True)
            except UsageLimitExceededError:
                raise
            except (ImageGenerationError, GeminiError) as e:
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
                attractiveness: str, retry_note: str | None = None, reflection: bool = False) -> str:
    what = "face" if zone == "face" else "head"
    if zone == "face":
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
    ident = ("lips, skin tone and beard exactly as in the reference photos." if zone == "face" else
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
    return (f"The first {n_refs} images are photos of the same man: the identity reference. The last image is the photo to edit.\n\n"
            f"Edit the last image so that the man in it has this exact man's {what}: his face structure, jawline, nose, eyes, brows, "
            f"{ident}{hair}{gl}{expression_rule(expression, attractiveness, scene)}"
            f"{scene_block(scene, zone)}\n\n"
            "Keep his head at the same position, turn and tilt as in the last image, and the head, including the hair, exactly the same "
            "size as there, never larger. Keep his jaw, chin and neck exactly as clean as in the last image: no extra fold or double chin. "
            "The face has exactly the exposure, colour, contrast and grain of the photo around it, lit from the same direction, so it "
            "belongs in the picture like a real phone photo and not a studio portrait.\n"
            f"Keep everything else in the last image exactly as it is: neck, clothing, body, hands, pose, background and framing.{refl}{retry}")


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
async def gemini_edit(client, model: str | None, prompt: str, files: list[Path], run_dir: Path, tag: str, verbose: bool,
                      log: RunLog, retries: int = 2) -> tuple[Path, str]:
    last = "unknown"
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
        if not cand.generated_images:
            text = cand.text or ""
            # Gemini answers an image request with plain text when the image quota is spent; retrying just burns time.
            if "limit resets" in text or "image limit" in text.lower():
                raise UsageLimitExceededError(f"Gemini image limit reached: {text.strip()[:200]}")
            last = f"no image returned; text: {text[:300]}"
            log.say(f"    [{tag}] attempt {attempt + 1}: {last}")
            continue
        saved = Path(await cand.generated_images[0].save(path=str(run_dir), filename=f"{tag}_raw.png", verbose=verbose))
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
    return composite.rect_crop(shape, x + w / 2, y + h / 2 - dy, fs * scale, fs * scale), scale


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
def align_to_ring(crop: np.ndarray, edit: np.ndarray) -> tuple[np.ndarray, float, dict, str, np.ndarray | None]:
    """Fit the returned crop to the source crop using only the outer ring, where nothing was supposed to change.

    Returns (edit at crop size, ECC correlation, warp magnitude, how, validity mask or None). The warp is applied only
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
        return plain, cc, mag, "resize only", None
    valid = cv2.warpAffine(np.full((h, w), 255, np.uint8), warp, (w, h), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return aligned, cc, mag, "ECC on the border ring", valid


async def edit_stage(client, model, log: RunLog, run_dir: Path, tag: str, base: np.ndarray, rect: composite.Rect, prompt: str,
                     ref_files: list[Path], verbose: bool) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """Send the crop to Gemini, take the returned crop and paste it back with a soft border. Returns (image, zone, meta)."""
    crop = composite.take(base, rect)
    h, w = crop.shape[:2]
    send_p = run_dir / f"{tag}_send.png"
    cv2.imwrite(str(send_p), resized_for_send(crop))
    raw_p, txt = await gemini_edit(client, model, prompt, ref_files + [send_p], run_dir, tag, verbose, log)
    edit = cv2.imread(str(raw_p))
    eh, ew = edit.shape[:2]
    dev = abs((ew / eh) / (w / h) - 1)
    meta: dict = {"stage": tag, "raw": raw_p.name, "raw_size": [ew, eh], "crop": list(rect), "aspect_dev": round(dev, 4), "text": txt[:200]}
    if dev > ASPECT_TOL:
        meta["failed"] = f"Gemini returned a {ew}x{eh} image for a {w}x{h} crop (different aspect ratio)"
        return base, None, meta
    aligned, cc, mag, how, valid = align_to_ring(crop, edit)
    meta.update({"ecc": round(cc, 4), "warp": mag, "aligned_by": how})
    if cc < ECC_FAIL or abs(mag["scale"] - 1) > ALIGN_MAX_SCALE or mag["shift_frac"] > ALIGN_MAX_SHIFT:
        meta["failed"] = f"returned crop does not line up with the source (ecc {cc:.3f}, warp {mag})"
        return base, None, meta
    sx, sy = w / ew, h / eh
    holes = [((ew - SPARKLE_OFFSET) * sx, (eh - SPARKLE_OFFSET) * sy, SPARKLE_RADIUS * sx)]
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
def turn_degrees(scene: dict | None) -> float | None:
    """The head turn, in degrees, as Gemini read it (the largest number in its description; 'profile' alone counts as 80)."""
    txt = str((scene or {}).get("head_turn") or "")
    nums = [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", txt)]
    if nums:
        return max(nums)
    return 80.0 if "profile" in txt.lower() else None


def retry_note_from(problems: list[str], judge: dict | None) -> str | None:
    """Turn a failed candidate's problems and the judge's own note into a sentence for the next prompt (AI feedback loop)."""
    bits: list[str] = []
    for p in problems:
        low = p.lower()
        if "head angle" in low:
            bits.append("his head was turned more toward the camera than in the last image; keep it turned exactly as it is there")
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


def judge_failures(judge: dict | None, expression_must_match: bool = False) -> tuple[list[str], list[str]]:
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
    if judge.get("same_expression") is False:
        if expression_must_match:
            hard.append("AI judge: expression differs from the source (it must match under the same-expression policy)")
        else:
            soft.append("AI judge: expression differs from the source (by design, see the attractiveness policy)")
    return hard, soft


# ---------------------------------------------------------------------------------------------- main
async def rank_by_expression(client, models: list[str | None], run_dir: Path, cands: list[dict], log: RunLog) -> dict[int, float]:
    """Score the passing candidates by the AI's pairwise choice of the better expression (wins per attempt index).

    Every pair is asked in BOTH orders (position bias cancels; a split answer counts as a tie). Wins decide, ties fall back to the
    identity score. The AI does the visual judgement it was validated for; nothing about the images is changed.
    """
    wins = {c["index"]: 0.0 for c in cands}
    log_pairs = []
    for a in range(len(cands)):
        for b in range(a + 1, len(cands)):
            ca, cb = cands[a], cands[b]
            fa, fb = run_dir / f"cand{ca['index']}_crop.jpg", run_dir / f"cand{cb['index']}_crop.jpg"
            r1 = await gemini_text(client, models, EXPRESSION_PAIR_PROMPT, [fa, fb], log, "pair")
            r2 = await gemini_text(client, models, EXPRESSION_PAIR_PROMPT, [fb, fa], log, "pair")
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
            log.say(f"  expression comparison attempt {ca['index']} vs {cb['index']}: {verdict}")
    log.data["expression_ranking"] = {"wins": wins, "pairs": log_pairs}
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

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / config.get("out_dir", "outputs") / f"{stamp}_replicate_{src_path.stem[:30]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log = RunLog(run_dir, {"timestamp": stamp, "scene": str(src_path), "size": [W, H], "args": vars(args) | {"func": None},
                           "thresholds": thr, "gates": gates, "text_models": text_models, "candidates": [], "status": "started"})
    log.say(f"run dir: {run_dir}")
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
    if source_kind == "own" and not args.force:
        log.say("This photo is already you, so there is nothing to replace. Re-run with --force to run the pipeline on it "
                "anyway (own-photo benchmark: the output should stay the same person).")
        log.data["status"] = "own_photo_no_force"
        log.save()
        return 0
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
            if expression != "none":
                scene = await gemini_text(client, text_models, DESCRIBE_PROMPT, [run_dir / "source_crop.png"], log, "describe")
                log.say(f"scene as read by Gemini: {json.dumps(scene, ensure_ascii=False) if scene else 'no usable answer (edit prompt has no description)'}")
                log.data["scene_reading"] = scene
            # ---- identity references: head crops nearest in head shape (never the source photo itself). Frontal anchors
            # help skin tone and eyes, but pull a strongly turned head toward the camera, so the AI's own reading of the
            # turn decides whether they are sent.
            turn = turn_degrees(scene)
            skip_anchors = turn is not None and turn >= ANCHOR_TURN_MAX
            near = identity.nearest_by_shape(src_res["shape"], pool, n=4 if skip_anchors else 3, exclude_names=dups)
            ref_names = [e.name for e, _ in near]
            if not skip_anchors:
                for anchor in config.get("anchors", ["IMG_6873.jpg", "IMG_6858.jpg"]):
                    if anchor not in ref_names and anchor not in dups and anchor in by_name:
                        ref_names.append(anchor)
            head_refs = [head_ref_crop(by_name[n].path, scorer) for n in ref_names]
            log.say(f"identity refs (head crops): {', '.join(ref_names)}"
                    + (f"  [no frontal anchors: Gemini read the head as turned {turn:.0f} degrees]" if skip_anchors else ""))
            log.data["identity_refs"] = ref_names
            retry_note: str | None = None

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
                        prompt = edit_prompt(len(head_refs), kind, args.glasses, args.look, scene, expression, attractiveness, retry_note,
                                             reflection=len(head_boxes) > 1)
                        base, z, meta = await edit_stage(client, model, log, run_dir, f"c{i}_head", base, rect, prompt, head_refs, args.verbose)
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

                # ---- save lossless, then verify on the saved file
                png = run_dir / f"cand{i}.png"
                cv2.imwrite(str(png), base, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                saved = cv2.imread(str(png))
                ver = composite.verify_outside(src, saved, union)
                cand["outside_check"] = ver
                out_crop = composite.take(saved, rect)
                cv2.imwrite(str(run_dir / f"cand{i}_crop.jpg"), resized_for_send(out_crop), [cv2.IMWRITE_JPEG_QUALITY, 95])

                # ---- deterministic measurements: they measure, they do not interpret
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
                cand["metrics"] = m

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

                # ---- the AI judges what code cannot: angle, glasses, seam, lighting, anything else changed
                judge = await gemini_text(client, text_models, JUDGE_PROMPT, [run_dir / "source_crop.png", run_dir / f"cand{i}_crop.jpg"], log, "judge")
                cand["judge"] = judge
                hard, soft = judge_failures(judge, expression_must_match=(expression == "same"))
                problems += hard
                warnings += soft
                cand["problems"], cand["warnings"] = problems, warnings

                if problems:
                    cand["verdict"] = "invalid"
                elif m["score"] >= thr["accept"]:
                    cand["verdict"] = "accept"
                elif m["score"] >= thr["hard_reject"]:
                    cand["verdict"] = "uncertain"
                else:
                    cand["verdict"] = "reject"
                if cand["verdict"] in ("accept", "uncertain"):
                    passing += 1
                else:
                    retry_note = retry_note_from(problems, judge)

                log.say(f"  outside-crop changed px: {ver['changed_outside']}")
                log.say(f"  score={m.get('score')} gt_sim={m.get('gt_sim')} shape_dist={m.get('shape_dist')} size_ratio={m.get('size_ratio')} "
                        f"face_shift={m.get('face_shift_frac')} sharp_ratio={m.get('sharp_ratio')} light={m.get('light')} "
                        f"drift={m.get('drift')} -> {cand['verdict'].upper()}")
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
                log.say(f"\n{len(passing_now)} candidates passed; asking Gemini which has the better expression (each pair in both orders)")
                expr_wins = await rank_by_expression(client, text_models, run_dir, passing_now, log)
                log.save()
    except UsageLimitExceededError as e:
        log.say(f"Gemini quota reached, stopping the batch: {e}")
        log.data["status"] = "usage_limit"
    except AuthError as e:
        log.say(str(e))
        log.data["status"] = "auth_error"
        log.save()
        return 1

    log.data["attempts"] = attempts
    ranked = [c for c in candidates if c.get("verdict") in ("accept", "uncertain")]
    # Order: the AI's pairwise expression wins first, then the identity band (accept > uncertain) as a tiebreak, then the identity number.
    # The band used to come first; that let "accept" (score >= 0.52) beat a candidate the AI and the user both preferred, although the
    # calibration shows the score cannot tell good from bad below 0.52, and a 0.96 similarity to the source only means the face was
    # barely edited (stained-glass run 151934: the user's promising attempt 1 lost to an almost untouched attempt 3).
    rank = {"accept": 2, "uncertain": 1}
    key = (lambda c: (expr_wins.get(c["index"], 0.0), rank[c["verdict"]],
                      c["metrics"].get("gt_sim", 0) if source_kind == "own" else c["metrics"]["score"]))
    if ranked:
        best = max(ranked, key=key)
        img = cv2.imread(str(run_dir / best["metrics"]["file"]))
        cv2.imwrite(str(run_dir / "best.png"), img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        cv2.imwrite(str(run_dir / "best.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
        log.data["best"] = {"candidate": best["index"], "verdict": best["verdict"],
                            **{k: best["metrics"].get(k) for k in ("score", "gt_sim", "shape_dist", "size_ratio")}}
        why = (f"; AI expression wins {expr_wins}" if expr_wins else "")
        log.say(f"\n[BEST] attempt {best['index']} ({best['verdict']}) after {attempts} attempts{why} -> best.png / best.jpg")
    else:
        # Nothing passed every gate. Keep the closest candidate visible for the user's own eye, clearly labelled as not passing.
        usable = [c for c in candidates if c.get("metrics", {}).get("score") is not None and c["metrics"].get("file")
                  and not any("changed outside" in p for p in c.get("problems", []))]
        if usable:
            near = min(usable, key=lambda c: (len(c.get("problems", [])), -c["metrics"]["score"]))  # fewest problems, then identity
            img = cv2.imread(str(run_dir / near["metrics"]["file"]))
            cv2.imwrite(str(run_dir / "not_passing_closest.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
            log.data["not_passing_closest"] = {"candidate": near["index"], "problems": near.get("problems")}
            log.say(f"\nNo candidate passed every gate in {attempts} attempts. The closest one (attempt {near['index']}; "
                    f"{'; '.join(near.get('problems', []))}) is saved as not_passing_closest.jpg for your review. Nothing was promoted to best.png.")
        else:
            log.say(f"\nNo candidate passed in {attempts} attempts and none produced a usable image. Every attempt and reason is above.")
    log.data["status"] = log.data.get("status") if log.data.get("status") not in ("started", None) else "done"
    log.save()
    return 0
