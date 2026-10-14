"""Method replicate/1: his OWN photo redone through a recipe and the 8 stages (2026-10-08).

Why: the own-photo pictures of 2026-10-07 went downhill at stage 01, the method. They went through Route G (the whole photo sent at 2048 px,
the whole frame redrawn, a ~1 MP preview back, his face ~77 px wide) instead of replicate, which edits a full-resolution crop of the head and
pastes it back into the untouched original. That is how both earlier best versions were made. A Route G recipe for his own photo is now refused
(recipe.own_photo_of), and replicate became a recipe method so it is just as frozen and visible as Route G.

What a replicate/1 recipe freezes (recipe new --method replicate), so every run sends the identical request:
  the crop rectangle (from the face box, grown to the whole head by ONE recorded AI head-box reading), the reflection copies inside it,
  ONE recorded AI scene reading (it goes into the prompt), the expression rule, and the references = the character's four face photos as
  head crops (characters.py: the same photos for every goal). The lock is the edit prompt + [4 face crops, the crop to edit] + the model.
What a run does (stages 04-08 here; 01-03 are the runner's):
  (opt-in, --place-from: one more frozen reference, a rendered head placed at the photo's position and size: the placement pass, see below)
  05  the SAME request for every attempt (no retry note and no extra face reference: both made every attempt a different request), each return
      merged only when its outer ring matches (replicate.paste_return), saved as the complete picture v<N>_0.png, measured with replicate's
      gates (replicate.measure_candidate) and judged by the AI (replicate.judge_candidate), until `samples` pass or `max_attempts` are spent;
      two or more passing pictures are ranked by the AI's pairwise face choice (both orders)
  06  record-only measures beside the gate results: head pose, his character measures (character.py), faces found
  07  audit sheets; 08 ranking (AI face wins, then accept over uncertain, then identity), best.png, export and ledger lines.
The gate limits are replicate's own (facecard.json gates / identity_thresholds), unchanged.
"""
from __future__ import annotations

import asyncio
import contextlib
import difflib
import inspect
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

import provenance as P

ROOT = Path(__file__).resolve().parent
COMPILER = "replicate/1"
CROP_NAME = "photo_to_edit.png"


class _Log:
    """The small log object replicate's helpers expect (say / data / save / meter); everything printed also reaches the run's run.log."""

    def __init__(self, d: Path):
        self.dir, self.data, self.meter = d, {}, None

    def say(self, msg: str) -> None:
        print(msg, flush=True)

    def save(self) -> None:
        pass


def template_sha256() -> str:
    import replicate as RP
    return P.sha256_text("".join(inspect.getsource(f) for f in (RP.edit_prompt, RP.scene_block, RP.expression_rule)))


def compiled_with() -> dict:
    vers = P.package_versions()
    return {"code": P.code_label(), "compiler": COMPILER, "template_sha256": template_sha256(), "pillow": vers.get("Pillow"),
            "opencv": vers.get("opencv-python")}


def compile_prompt(inp: dict) -> str:
    """The edit prompt from the frozen inputs, with replicate's own prompt builder (no randomness left: the readings are frozen)."""
    import replicate as RP
    if inp.get("zone") == "build":
        return build_prompt_text(inp)
    scene = (inp["readings"].get("describe") or {}).get("reply")
    n_faces = sum(1 for r in inp["references"] if r["role"] == "face")
    n_expr = sum(1 for r in inp["references"] if r["role"] == "expression")
    # --place-from (2026-10-12): the placement reference, absent in older versions (n_place 0, rescue False), so they compile unchanged
    n_place = sum(1 for r in inp["references"] if r["role"] == "placement")
    prompt = RP.edit_prompt(n_faces + n_expr + n_place, inp["kind"], inp["glasses"], inp["look"], scene, inp["expression"], inp["attractiveness"],
                            None, reflection=len(inp["head_boxes"]) > 1, rescue=n_place > 0, far=inp["far"], whole_head=(inp["kind"] == "face"),
                            face_share=inp.get("face_share"))
    if inp.get("hair_note"):          # --current-hair (2026-10-08): absent in older versions, so they compile unchanged
        prompt += "\n\n" + inp["hair_note"]
    if inp.get("face_note"):          # --current-look (2026-10-08)
        prompt += "\n\n" + inp["face_note"]
    if n_expr:                        # --expression-ref (2026-10-10): absent in older versions, so they compile unchanged
        first = n_faces + 1
        span = f"Image {first} shows" if n_expr == 1 else f"Images {first}-{first + n_expr - 1} show"
        intro = inp.get("expression_ref_intro") or "close crops of his OWN smile from other photos of him, the candid smiles he chose as his best."
        prompt += f"\n\n{span} {intro} " + (inp.get("expression_ref_label") or EXPRESSION_REF_LABEL)   # --expression-ref-intro; older versions: the default
    return prompt


EXPRESSION_REF_LABEL = ("From them take only how he smiles: the shape of his lips, how much of his upper teeth shows (his own teeth as they are: their shape, size and colour),"
                        "the lift of his cheeks and the crinkle at his eyes. Never take their light, angle, skin, beard, hair or glasses.")
# ^ the user, 2026-10-10: "my smile reference image itself is bad ... when captured in candid it can look different"; teeth: "mine, slightly whiter"


CURRENT_HAIR = ("His hair is his CURRENT cut, from the reference photos, not the cut of the man in the last image: dense tight black curls on top, the "
                "sides above and in front of his ears tapered short and close to the scalp so that his ears and temples show, and the curls longer at "
                "the back toward the nape. So the hair outline changes at the sides; on top it stays within the size it has in the last image.")
# ^ kayak v5/v6 (2026-10-08) kept the old photo's full curly sides: "the head, including the hair, exactly the same size" held the old outline
CURRENT_FACE = ("His face is his CURRENT face from the reference photos: lean, with low facial fat, never fuller than in the reference photos. Only his "
                "full dense beard may make his jaw outline a little wider than in the last image; the rest of his head keeps its size.")
# ^ the user, 2026-10-08: "if the beard makes the face fuller, up to 1.1 is permitted; if it is leanness, stick to the leaner look"
CURRENT_LOOK_SIZE = (0.94, 1.10)    # head-size gate of a current-look own photo's head pass (the user's rule above); every other photo keeps facecard.json's

# ---- zone build: his own older photo's BODY changed to his current physique (pass A of a current-look own photo, 2026-10-08)
# The user, 2026-10-08: "body and hair rework needed for both, since the current physique and face has been changed as can be seen in the reference
# images". replicate keeps every pixel outside the head crop, so his old body stayed; pass A edits a crop of his body (from the measured keypoints) and
# pastes it back, pass B then redoes the head on the pass-A picture (--from-picture). Both are frozen recipes.
BUILD_READ_PROMPT = (
    "Both images show the same man, at different times. Compare his body in image 2 with his body in image 1, part by part. Judge the body "
    "only: ignore the clothes, the pose, the light and the camera distance. Reply with ONLY a JSON object, no other text, with the keys "
    "shoulders, upper_arms, forearms, chest, stomach and waist; each value is one of: much slimmer, slimmer, a little slimmer, the same, "
    "a little fuller, fuller, much fuller (image 2 compared with image 1).")
BUILD_SCALE = {"much slimmer": -3, "slimmer": -2, "a little slimmer": -1, "the same": 0, "a little fuller": 1, "fuller": 2, "much fuller": 3}
BUILD_PARTS = ("shoulders", "upper_arms", "forearms", "chest", "stomach", "waist")
BODY_JUDGE_PROMPT = (
    "Image 1 is an original photo crop. Image 2 is an edited version of it in which ONLY the man's body build (shoulders, arms, chest, "
    "stomach, waist) was supposed to change. Compare them and reply with ONLY a JSON object, no other text, with these keys:\n"
    "same_pose: true or false, whether his posture and the position of both arms and both hands are the same in both\n"
    "same_clothes: true or false, whether he wears the same garments in the same colours and fabric (a looser or tighter fit is allowed)\n"
    "background_unchanged: true or false, whether everything that is not his body (objects, background, light) is unchanged\n"
    "anatomy_ok: true or false, whether his body is natural in image 2: two arms, natural hands with five fingers, no extra or missing limbs\n"
    "seam_visible: true or false, whether a seam, halo, patch or colour step is visible in image 2\n"
    "body_change: one of slimmer, the same, fuller (his body in image 2 compared with image 1)\n"
    "notes: one short sentence naming the single biggest problem, or 'none'")
BODY_JUDGE_PROMPT_2 = (
    "Image 1 is an original photo crop. Image 2 is an edited version of it in which the man's body (shoulders, arms, chest, stomach, waist) was "
    "redrawn and his clothes were allowed to change. Compare them and reply with ONLY a JSON object, no other text, with these keys:\n"
    "same_pose: true or false, whether his posture and the position of both arms and both hands (and what they hold) are the same in both\n"
    "background_unchanged: true or false, whether everything that is not him or his clothes (objects, background, light) is unchanged\n"
    "anatomy_ok: true or false, whether his body is natural in image 2: two arms, natural hands with five fingers, no extra or missing limbs\n"
    "seam_visible: true or false, whether a seam, halo, patch or colour step is visible in image 2\n"
    "body_change: one of slimmer, the same, fuller (his body in image 2 compared with image 1)\n"
    "notes: one short sentence naming the single biggest problem, or 'none'")
BUILD_GATES = {"bg_mad_max": 10.0, "bg_ssim_min": 0.80, "person_dilate": 0.03}   # replicate's own drift limits, measured outside his silhouette


def body_rect(shape, pose: dict, face_box) -> list[int]:
    """His body below the chin: shoulders, both arms and hands, the torso to the hips (the goal's measured keypoints), with a margin."""
    import composite
    import replicate as RP
    H, W = shape[:2]
    kp = pose["person"]["kp"]
    pts = [(kp[n][0] * W, kp[n][1] * H) for n in ("l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist", "l_hip", "r_hip")
           if n in kp and kp[n][2] >= 0.3]
    if len(pts) < 3:
        raise SystemExit("zone build: fewer than 3 body keypoints in the goal's pose (tools/pose_compare.py --save-goal)")
    fx, fy, fw, fh = face_box
    x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts)
    y0, y1 = fy + 0.85 * fh, max(q[1] for q in pts)
    w, h = max(x1 - x0, fw), max(y1 - y0, fh)
    m = 0.12 * max(w, h)
    rect = composite.rect_crop(shape, (x0 + x1) / 2, (y0 + y1) / 2, w + 2 * m, h + 2 * m)
    return [int(v) for v in RP.snap_aspect(rect, shape)]


def build_change(r1: dict | None, r2: dict | None) -> dict:
    """The two orders of the build reading made into one: r1 = his OLD body (image 2) vs his current body (image 1); r2 = the reverse. A part is
    used only when both orders agree on the direction; its size is the smaller of the two. {part: signed level, old relative to current}."""
    out = {}
    for part in BUILD_PARTS:
        a = BUILD_SCALE.get(str((r1 or {}).get(part, "")).strip().lower())
        b = BUILD_SCALE.get(str((r2 or {}).get(part, "")).strip().lower())
        if a is None or b is None or a == 0 or b == 0 or (a > 0) == (b > 0):
            continue
        out[part] = (1 if a > 0 else -1) * min(abs(a), abs(b))
    return out


def expected_change(change: dict) -> str | None:
    """The direction the frozen build reading asks for: 'slimmer' when his OLD body reads fuller than today on most parts, 'fuller' when slimmer."""
    lv = list((change or {}).values())
    if not lv:
        return None
    pos, neg = sum(1 for v in lv if v > 0), sum(1 for v in lv if v < 0)
    return "slimmer" if pos > neg else ("fuller" if neg > pos else None)


def source_glasses_of(inp: dict) -> bool | None:
    """Whether the photo to edit shows him in glasses, from the frozen scene reading ('none' = no), or None when it was not read."""
    g = str((((inp.get("readings") or {}).get("describe") or {}).get("reply") or {}).get("glasses") or "").strip().lower()
    return None if not g else not (g.startswith("none") or g.startswith("no ") or g in ("no", "false"))


def build_prompt_text(inp: dict) -> str:
    if int(inp.get("build_prompt") or 1) >= 2:
        return build_prompt_text_2(inp)
    words = {1: "a little", 2: "clearly", 3: "much"}
    names = {"upper_arms": "upper arms", "forearms": "forearms", "shoulders": "shoulders", "chest": "chest", "stomach": "stomach", "waist": "waist"}
    plural = {"upper_arms", "forearms", "shoulders"}
    parts = []
    for part, lvl in (inp.get("build_change") or {}).items():
        verb = "are" if part in plural else "is"
        want = "slimmer" if lvl > 0 else ("broader" if part == "shoulders" else "fuller")
        parts.append(f"his {names[part]} {verb} {words[abs(lvl)]} {want} than in the last image")
    n = sum(1 for r in inp["references"] if r["role"] == "body")
    char_build = str(inp.get("character_build") or "").replace("{BODY}", "1")
    return (f"The first {n} images show this man's CURRENT physique (shoulders, arms, chest, stomach and waist), as he looks today. The last image is an "
            "older photo of him, from a time when his body was different.\n\n"
            f"Edit the last image so that his body has his current physique, exactly as in the first {n} images: {char_build}"
            + (" Compared with the last image: " + "; ".join(parts) + "." if parts else "")
            + "\n\nKeep everything else in the last image exactly as it is: his head, face, hair and beard; his exact pose and the position of both arms "
              "and both hands; everything he holds or wears, the same garments in the same colours, fabric and fit style, refitted only as far as his "
              "body requires; any reflection of him, given the same body; and the whole background, light, colour and grain. Return the image with "
              "exactly the same framing, crop and scale as the last image.")


def build_prompt_text_2(inp: dict) -> str:
    """Body pass, version 2 (the user, 2026-10-09: "it's fine to change everything on top of the body, like the dress, if that helps; remove the
    contradicting instructions"). Version 1 asked for his current body AND for "the same garments in the same colours, fabric and fit style,
    refitted only as far as his body requires" with "everything else exactly as it is": the garments' outline is the old body's outline, and both
    pass-A runs came back unchanged (judge "the same", widths 1.00). Here the clothes may change; only his head, his pose and the scene stay."""
    words = {1: "a little", 2: "clearly", 3: "much"}
    names = {"upper_arms": "upper arms", "forearms": "forearms", "shoulders": "shoulders", "chest": "chest", "stomach": "stomach", "waist": "waist"}
    plural = {"upper_arms", "forearms", "shoulders"}
    parts = []
    for part, lvl in (inp.get("build_change") or {}).items():
        verb = "are" if part in plural else "is"
        want = ("narrower" if part == "shoulders" else "slimmer") if lvl > 0 else ("broader" if part == "shoulders" else "fuller")
        parts.append(f"his {names[part]} {verb} {words[abs(lvl)]} {want} than in the last image")
    n = sum(1 for r in inp["references"] if r["role"] == "body")
    char_build = str(inp.get("character_build") or "").replace("{BODY}", "1")
    then = {"slimmer": "fuller than he is today", "fuller": "slimmer than he is today"}.get(inp.get("expected_change"), "different from how he is today")
    return (f"The first {n} images show this man's body as it is today. The last image is an older photo of him, from a time when his body was {then}.\n\n"
            f"Redraw his body in the last image (shoulders, arms, chest, stomach and waist) as it is today, as in the first {n} images: {char_build}"
            + (" Compared with the last image: " + "; ".join(parts) + "." if parts else "")
            + "\n\nHis clothes may change so that they fit his body as it is today: a similar outfit is right, and it does not need the old photo's "
              "fit, folds or shape."
            + (" His reflection in the glass shows the same body and the same clothes." if inp.get("reflection") else "")
            + "\n\nKeep his head, his pose (where his arms and hands are, and what he holds) and the scene around him, and return the "
              "image with the same framing and scale as the last image.")


def background_drift(src, out, rect, person_mask, dilate_frac: float) -> dict:
    """Mean difference and SSIM inside the crop, OUTSIDE his (dilated) silhouette: the background must not be redrawn by a body edit."""
    import composite
    import cv2
    import numpy as np
    a, b = composite.take(src, rect), composite.take(out, rect)
    h, w = a.shape[:2]
    pm = composite.take(person_mask, rect) > 0
    r = max(3, int(dilate_frac * max(h, w)))
    pm = cv2.dilate(pm.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
    keep = ~pm
    if int(keep.sum()) < 500:
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


def measure_build_candidate(src, base, rect, zone_mask, person_mask, main_box, png: Path, crop_jpg: Path, t0: float, bg: dict):
    """A body-pass candidate: saved lossless, 0 px changed outside the crop, background drift outside his silhouette within replicate's limits;
    record-only: his silhouette widths source vs output (replicate.physique_report)."""
    import composite
    import cv2
    import replicate as RP
    problems, warnings = [], []
    cv2.imwrite(str(png), base, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    saved = cv2.imread(str(png))
    ver = composite.verify_outside(src, saved, zone_mask)
    out_crop = composite.take(saved, rect)
    cv2.imwrite(str(crop_jpg), RP.resized_for_send(out_crop), [cv2.IMWRITE_JPEG_QUALITY, 95])
    m = {"file": png.name, "elapsed_sec": round(time.time() - t0, 1), "bg_drift": background_drift(src, saved, rect, person_mask, bg["person_dilate"])}
    with contextlib.suppress(Exception):
        m["physique"] = RP.physique_report(src, saved, tuple(main_box))
    if not ver["same_size"] or ver["changed_outside"] != 0:
        problems.append(f"{ver['changed_outside']} px changed outside the crop")
    d = m["bg_drift"]
    if d["mean_abs_diff"] is not None and (d["mean_abs_diff"] > bg["bg_mad_max"] or d["ssim"] < bg["bg_ssim_min"]):
        problems.append(f"the background around his body was redrawn (mean diff {d['mean_abs_diff']}, SSIM {d['ssim']})")
    return m, problems, warnings, ver, saved, out_crop


async def judge_body(client, text_models, source_file: Path, cand_file: Path, log, cand: dict, problems: list, warnings: list,
                     version: int = 1, expected: str | None = None) -> None:
    """Version 1: clothes must stay, an unchanged body is only a warning. Version 2 (2026-10-09): clothes may change, and a body that did not
    change in the frozen reading's direction fails (the pass exists to change it)."""
    import replicate as RP
    j = await RP.gemini_text(client, text_models, BODY_JUDGE_PROMPT_2 if version >= 2 else BODY_JUDGE_PROMPT, [source_file, cand_file], log, "body judge")
    cand["judge"] = j
    if not j:
        (problems if version >= 2 else warnings).append("the AI body judge gave no usable answer")
        return
    checks = [("same_pose", True, "pose changed")] + ([] if version >= 2 else [("same_clothes", True, "clothes changed")]) + [
        ("background_unchanged", True, "background changed"), ("anatomy_ok", True, "anatomy is wrong (arms or hands)"),
        ("seam_visible", False, "a seam or patch is visible")]
    for key, want, msg in checks:
        v = j.get(key)
        if v is None:
            warnings.append(f"body judge did not answer {key}")
        elif bool(v) != want:
            problems.append(f"AI body judge: {msg}")
    change = str(j.get("body_change", "")).strip().lower()
    if version >= 2 and expected and change != expected:
        problems.append(f"AI body judge: his body did not become {expected} (judge: {change or 'no answer'})")
    elif change == "the same":
        warnings.append("AI body judge: the body did not visibly change")


def base_picture(rec: dict, goal_pinned: Path) -> Path:
    """The picture a replicate/1 recipe edits: the pinned --from-picture (pass B of a current-look own photo), else his original photo."""
    fp = rec["inputs"].get("from_picture")
    return P.blob_path(fp["sha256"]) if fp else goal_pinned


def drift(rec: dict) -> dict:
    prompt = compile_prompt(rec["inputs"])
    lock = rec["lock"]
    same = prompt == lock["prompt"]
    out = {"same": same, "same_prompt": same, "same_files": True, "compiled_with_lock": lock.get("compiled_with"),
           "compiled_with_now": compiled_with(), "notices": []}
    if not same:
        out["prompt_diff"] = "".join(difflib.unified_diff(lock["prompt"].splitlines(True), prompt.splitlines(True), "lock (recipe)",
                                                          "today's replicate.edit_prompt", n=1))
    return out


# ------------------------------------------------------------------------------------------------------------------------------ freeze (recipe new)


async def freeze(args, because: str, version: int | None = None, parent: str | None = None) -> dict:
    """Read the photo once (crop, head box, scene reading), take the character's face photos, compile and lock. Two text calls on the vision
    model; no image is generated."""
    import characters
    import composite
    import cv2
    import facecard
    import identity
    import recipe as R
    import replicate as RP
    from scorer import ArcFaceScorer
    from session import authenticated_client
    config = facecard.load_config()
    thr, gates = RP.thresholds(config), RP.gate_values(config)
    model = args.model or config.get("model")
    # the readings are frozen once, so a reliable answer matters more than its few credits: Flash first, Pro last (10-08: Flash text calls timed out)
    pro = next((k for k, v in (config.get("models") or {}).items() if v == "pro"), None)
    text_models = list(dict.fromkeys([config.get("vision_model") or model, model] + ([pro] if pro else [])))
    goal = Path(args.goal)
    if not goal.is_file():
        raise SystemExit(f"goal photo not found: {goal}")
    if not getattr(args, "character", None):
        raise SystemExit("a replicate/1 recipe needs --character (e.g. me@v1): its face photos are the references")
    ch, _ = characters.load(args.character)
    problems = characters.check(ch)
    if problems:
        raise SystemExit("; ".join(problems))
    from_pic = Path(args.from_picture) if getattr(args, "from_picture", None) else None
    if from_pic is not None and not from_pic.is_file():
        raise SystemExit(f"--from-picture not found: {from_pic}")
    edit_path = from_pic or goal
    current = bool(getattr(args, "current_look", False))
    src = RP.load_source(edit_path)
    H, W = src.shape[:2]
    scorer = ArcFaceScorer()
    pool = identity.build_pool(config, scorer, verbose=False)
    region = head_region_px(getattr(args, "head_region", None), W, H)      # --head-region (F43): None keeps the largest face, as before
    expect = None
    if region is not None:
        expect = face_in_region(src, region)
        if expect is None:
            raise SystemExit(f"--head-region: no face has its box centre inside {region} (pixels)")
    src_res = identity.score_image(src, pool, scorer, expect_box=expect)
    if not src_res.get("detected"):
        raise SystemExit("no face found in the goal photo")
    dups = identity.duplicates_of(src_res["emb"], pool)
    src_res = identity.score_image(src, pool, scorer, exclude_names=dups, expect_box=expect)
    if region is not None and not _centre_in(src_res["box"], region):
        raise SystemExit(f"--head-region: the measured face {list(src_res['box'])} lies outside {region}")
    source = getattr(args, "source", None) or "auto"
    source_kind = source if source in ("own", "foreign") else ("own" if src_res["score"] >= thr["own_min"] else "foreign")
    zone = getattr(args, "zone", None) or "auto"
    zone = zone if zone != "auto" else ("face" if source_kind == "own" else "head")
    if zone == "head+build":
        raise SystemExit("head+build is not part of replicate/1 (use --zone build, then --from-picture with --zone face)")
    if zone == "build":
        if getattr(args, "place_from", None):
            raise SystemExit("--place-from places a rendered head: it applies to zone face, head or expression, not to a body pass")
        if getattr(args, "eye_gate", None):
            raise SystemExit("--eye-gate measures his eyes: it applies to zone face, head or expression, not to a body pass")
        return await _freeze_build(args, because, version, parent, ch, config, src, goal, src_res, model, text_models, thr, gates)
    kind = "face" if zone in ("face", "expression") else "head"
    expression = getattr(args, "expression", None) or ("same" if source_kind == "foreign" else "auto")
    if zone == "expression" and expression in ("same", "auto", "none"):
        raise SystemExit("--zone expression needs --expression with the new expression in words")
    main_box = src_res["box"]
    main_rect, _ = RP.crop_for_face(src.shape, main_box, kind)
    far = main_box[2] < RP.FAR_FACE_PX
    work = ROOT / ".cache" / "replicate_freeze" / f"{datetime.now():%Y%m%d_%H%M%S}_{goal.stem}"
    work.mkdir(parents=True, exist_ok=True)
    log = _Log(work)
    readings: dict = {}
    print(f"freezing {goal.name}: {W}x{H}, face {src_res['face_w']} px, pool score {src_res['score']:.3f} -> {source_kind}, zone {zone}")
    async with authenticated_client(verbose=False) as client:
        head = None
        if not far:
            head = await RP.read_head_box(client, text_models, src, main_box, work, log)
        readings["head_box"] = {"prompt_sha256": P.sha256_text(RP.HEAD_BOX_PROMPT), "models": text_models,
                                "box": None if head is None else [round(v) for v in head], "skipped": "far face" if far else None}
        crop_before = None
        if getattr(args, "loose_crop", None) and head is None and not far:
            # 2026-10-14 (F64): the head-box reading timed out on both Gemini models, and a recipe saved as loose_crop kept the tight crop,
            # which would have spent 450 credits on the framing that already failed. Refuse instead; the reading is retried by freezing again.
            raise SystemExit("--loose-crop needs the head box, but the head-box reading returned nothing (Gemini text calls timed out?): "
                             "nothing was frozen; freeze again later")
        grown = RP.fit_whole_head(src.shape, main_rect, head) if head is not None else None
        if grown is not None:
            crop_before, main_rect = list(main_rect), grown
        if (zone == "expression" or getattr(args, "loose_crop", None)) and head is not None:   # --loose-crop: the same framing for a face edit
            loose = RP.expression_crop(src.shape, head)
            if loose[2] > main_rect[2]:
                crop_before, main_rect = crop_before or list(main_rect), loose
        head_boxes, rects, copies_left = [main_box], [main_rect], []
        others = RP.find_identity_faces(src, scorer, pool, src_res["emb"], dups)
        if region is None:
            others = others[1:]
        else:   # --head-region: only faces centred inside the region, and never the main face again
            others = [f for f in others if _centre_in(f["box"], region) and identity._iou(tuple(f["box"]), tuple(main_box)) < 0.5]
        for f in others:
            if f.get("role") != "copy":
                continue
            r_c, _ = RP.crop_for_face(src.shape, f["box"], "face")
            u = RP.union_rect(rects + [r_c])
            if max(u[2], u[3]) > RP.UNION_MAX * RP.SEND_PX:
                copies_left.append(list(f["box"]))
                continue
            rects.append(r_c)
            head_boxes.append(f["box"])
        rect = RP.snap_aspect(RP.union_rect(rects), src.shape) if len(rects) > 1 else main_rect
        src_crop = composite.take(src, rect)
        main_in_crop = (main_box[0] - rect[0], main_box[1] - rect[1], main_box[2], main_box[3])
        crop_p = work / CROP_NAME
        cv2.imwrite(str(crop_p), RP.resized_for_send(src_crop))
        scene = None
        if expression != "none":
            scene = await RP.gemini_text(client, text_models, RP.DESCRIBE_PROMPT, [crop_p], log, "describe")
            if (expression == "auto" and not getattr(args, "expression", None) and source_kind == "own" and scene
                    and RP.LAUGH_WORDS.search(str(scene.get("expression") or ""))):
                expression = "same"
        readings["describe"] = {"prompt_sha256": P.sha256_text(RP.DESCRIBE_PROMPT), "models": text_models, "file": CROP_NAME, "reply": scene}
    if scene is None and expression != "none":
        raise SystemExit("the scene reading gave no usable answer; nothing frozen (run recipe new again)")
    # the character's four face photos as head crops (replicate.head_ref_crop), sent under neutral names
    items = []
    for r in characters.faces_for(ch, "replicate"):
        p = characters.ref_path(r["name"], config)
        if p is None or P.sha256_file(p) != r["sha256"]:
            raise SystemExit(f"{r['name']}: the photo on disk is not the character's (sha256 differs or missing)")
        up = work / f"face_{r['slot']}.jpg"
        shutil.copyfile(RP.head_ref_crop(p, scorer), up)
        items.append({"role": "face", "name": up.name, "path": up, "sha256": P.put_file(up), "from": r["name"],
                      "prep": "head768_q95 (replicate.head_ref_crop)", "why": f"character {characters.ref_of(ch)}: {r['slot'].replace('_', ' ')}"})
    expr_label = None
    for k, spec in enumerate(getattr(args, "expression_ref", None) or [], 1):
        path_s, _, label = spec.partition("::")
        src_p = Path(path_s)
        if not src_p.is_file():
            raise SystemExit(f"--expression-ref not found: {src_p}")
        up = work / f"expression_{k}.jpg"
        cv2.imwrite(str(up), RP.resized_for_send(cv2.imread(str(src_p))), [cv2.IMWRITE_JPEG_QUALITY, 95])
        items.append({"role": "expression", "name": up.name, "path": up, "sha256": P.put_file(up), "from": str(src_p).replace("\\", "/"),
                      "prep": "resized_for_send q95", "why": "his own candid smile, chosen by the user (2026-10-10)"})
        expr_label = expr_label or (label.strip() or None)
    place = None
    if getattr(args, "place_from", None):         # --place-from (2026-10-12): one rendered head, just before the photo to edit; absent unless set
        place_item, place = placement_item(Path(args.place_from), {"zone": zone, "source_size": [W, H], "crop": [int(v) for v in rect]}, work)
        items.append(place_item)
    items.append({"role": "photo_to_edit", "name": CROP_NAME, "path": crop_p, "sha256": P.put_file(crop_p), "from": str(goal).replace("\\", "/"),
                  "prep": f"crop {list(rect)} of the {W}x{H} original, long side {RP.SEND_PX} px",
                  "why": "the crop of his photo that is edited and pasted back into the untouched original"})
    src_eval = identity.score_image(src_crop, pool, scorer, exclude_names=dups, expect_box=main_in_crop)
    if not src_eval.get("detected"):
        src_eval = src_res
    attractiveness = config.get("attractiveness_note") or RP.DEFAULT_ATTRACTIVENESS
    inputs = {"flags": {}, "own": source_kind == "own", "own_score": round(src_res["score"], 3), "source_kind": source_kind,
              "duplicates_excluded": sorted(dups), "zone": zone, "kind": kind, "expression": expression,
              "glasses": getattr(args, "glasses", None) or "same", "look": getattr(args, "look", None) or "any", "far": far,
              "face_share": round(main_in_crop[3] / rect[3], 4) if far else None, "crop": [int(v) for v in rect],
              "crop_before_head_fit": crop_before, "head_boxes": [[int(v) for v in b] for b in head_boxes], "copies_left_unedited": copies_left,
              "main_box": [int(v) for v in main_box], "main_in_crop": [int(v) for v in main_in_crop], "source_size": [W, H],
              "source_face": {"box": [int(v) for v in src_eval["box"]], "score": round(float(src_eval["score"]), 3), "face_w": src_res["face_w"]},
              "readings": readings, "attractiveness": attractiveness, "thresholds": thr, "gates": gates,
              "character": {"ref": characters.ref_of(ch), "sha256": ch["sha256"]}, "face_choice": {"decided_by": f"character {characters.ref_of(ch)}",
              "names": [it["from"] for it in items if it["role"] == "face"], "count": sum(1 for it in items if it["role"] == "face")},
              "references": R.references_of(items, {})}
    if any(it["role"] == "expression" for it in items):
        inputs["expression_refs"] = [it["from"] for it in items if it["role"] == "expression"]
        if expr_label:
            inputs["expression_ref_label"] = expr_label
        if getattr(args, "expression_ref_intro", None):
            inputs["expression_ref_intro"] = args.expression_ref_intro.strip()
    rank = getattr(args, "rank", None) or ("smile" if zone == "expression" else None)
    if rank and rank != "face":
        inputs["rank"] = rank
    if getattr(args, "current_hair", False) or current:
        inputs["hair_note"] = CURRENT_HAIR
    if current:
        inputs.update({"current_look": True, "face_note": CURRENT_FACE, "gates": {**gates, "size_own": list(CURRENT_LOOK_SIZE)}})
    if from_pic is not None:
        inputs["from_picture"] = lineage_of(from_pic)
        items[-1]["from"] = inputs["references"][-1]["from"] = str(from_pic).replace("\\", "/")
    if place is not None:
        inputs["place_from"] = place
    if getattr(args, "eye_gate", None):           # --eye-gate (2026-10-12): selects among returns; not in the prompt
        inputs["eye_gate"] = eye_gate_record(args.eye_gate)
    if region is not None:                        # --head-region (2026-10-12, F43): which face is his head; not in the prompt
        inputs["head_region"] = {"spec": args.head_region, "box_px": region, "face": [int(v) for v in main_box],
                                 "why": "only faces whose box centre lies inside this part of the frame count as the subject or a copy"}
    prompt = compile_prompt(inputs)
    lock = R.make_lock(prompt, items, model, compiled_with())
    key = R.goal_key_of(goal)
    count = int(getattr(args, "samples", None) or 2)
    method = {"route": "replicate", "compiler": COMPILER, "subject": "me",
              "args": {"goal": str(goal).replace("\\", "/"), "zone": zone, "source": source, "glasses": inputs["glasses"], "look": inputs["look"],
                       "expression": getattr(args, "expression", None), "character": characters.ref_of(ch), "current_look": current,
                       "from_picture": str(from_pic).replace("\\", "/") if from_pic else None,
                       **({"expression_ref": list(getattr(args, "expression_ref", None) or [])} if getattr(args, "expression_ref", None) else {}),
                       **({"rank": inputs["rank"]} if inputs.get("rank") else {}),
                       **({"loose_crop": True} if getattr(args, "loose_crop", None) else {}),
                       **({"expression_ref_intro": args.expression_ref_intro} if getattr(args, "expression_ref_intro", None) else {}),
                       **({"place_from": str(args.place_from).replace("\\", "/")} if getattr(args, "place_from", None) else {}),
                       **({"eye_gate": args.eye_gate} if getattr(args, "eye_gate", None) else {}),
                       **({"head_region": args.head_region} if region is not None else {})},
              "model": {"id": model, "label": R.model_label(model, config)}, "text_models": text_models, "samples": count,
              "max_attempts": int(getattr(args, "max_attempts", None) or max(6, count * 3)), "stop": {"after_pose_fails": 0, "on_pass": False}}
    gp = {"key": key, "path": str(goal).replace("\\", "/"), "sha256": P.put_file(goal), "pose": None, "layout": None, "source": None}
    v = version or R.next_version(key)
    return {"schema": R.SCHEMA, "id": key, "version": v, "created": datetime.now().isoformat(timespec="seconds"), "because": because,
            "parent": parent, "origin": {"kind": "bump" if parent else "new", "freeze_dir": str(work), "notices": []},
            "goal": gp, "method": method, "inputs": inputs, "lock": lock}


def lineage_of(pic: Path) -> dict:
    """The picture a pass B edits, pinned: its bytes, its run, and the recipe and zone that made it (best_check reads the zone: a body pass)."""
    run_dir = pic.parent
    rec = P.read_json(run_dir / "01_method" / "recipe.json", None) or {}
    return {"path": str(pic).replace("\\", "/"), "sha256": P.put_file(pic), "run": run_dir.name, "file": pic.name,
            "recipe": f"{rec.get('id')}@v{rec.get('version')}" if rec else None, "zone": (rec.get("inputs") or {}).get("zone")}


# ---- the placement pass (--place-from, 2026-10-12, FAILURE_LOG F34). The method that made the only ideal on another man's photo (Pinterest
# 064221 attempt 4, FEEDBACK_LOG: a good face rendered at size 0.923, its raw return's head sent back as one more reference with "keep the head at
# exactly the position, size, turn and tilt it has in the last image", 0.981, light dE 5.7). replicate/1 left it out so every attempt sends the
# identical request; here it is one frozen reference, so the request stays identical across attempts. Opt-in only: the head is a generated
# image, which goes back in as a reference only with the user's approval (AGENTS.md, the 2026-10-10 override). On another man's photo a
# placement never fixed a too-bright face (FEEDBACK_LOG), so it is for size and position, with references lit like the photo.
PLACE_NAME = "placement_head.jpg"


def placement_source(pic: Path) -> tuple[Path, str]:
    """The pixels the placement head is cut from: a run's vN_0.png comes from its raw return (05_generate/raw/vN_raw.*, the crop as Gemini sent
    it back, before the paste scaled it down to the photo's size), as the old rescue did; any other picture is used as it is."""
    m = re.fullmatch(r"v(\d+)_0\.png", pic.name)
    if m:
        call = P.read_json(pic.parent / "05_generate" / f"call_{m.group(1)}.json", None) or {}
        raw = (call.get("merge") or {}).get("raw")
        if raw and (pic.parent / "05_generate" / raw).is_file():
            return pic.parent / "05_generate" / raw, f"the raw return behind {pic.name} (05_generate/{raw})"
    return pic, pic.name


def placement_item(pic: Path, inp: dict, work: Path) -> tuple[dict, dict]:
    """The placement reference (the head of `pic`, cut like the identity references by replicate.raw_head_crop) and its record."""
    import cv2
    import composite
    import replicate as RP
    if not pic.is_file():
        raise SystemExit(f"--place-from not found: {pic}")
    if inp.get("zone") == "build":
        raise SystemExit("--place-from places a rendered head: it applies to zone face, head or expression, not to a body pass")
    work.mkdir(parents=True, exist_ok=True)
    src, desc = placement_source(pic)
    cut_from = src
    if src == pic:
        img = RP.load_source(pic)
        if [img.shape[1], img.shape[0]] == list(inp.get("source_size") or []):     # a picture of this goal: the head inside the recipe's crop
            cut_from = work / "placement_source.png"
            cv2.imwrite(str(cut_from), composite.take(img, tuple(inp["crop"])))
            desc += f", inside the crop {list(inp['crop'])}"
    head = RP.raw_head_crop(cut_from, work / PLACE_NAME)
    if head is None:
        raise SystemExit(f"--place-from: no face found in {desc}")
    item = {"role": "placement", "name": PLACE_NAME, "path": head, "sha256": P.put_file(head), "from": str(pic).replace("\\", "/"),
            "prep": f"head768_q95 (replicate.raw_head_crop) of {desc}",
            "why": "the placement pass: this rendered head, placed at the position, size, turn and tilt of the photo to edit"}
    record = lineage_of(pic)
    record["head_from"] = {"path": str(src).replace("\\", "/"), "sha256": P.put_file(src)}
    return item, record


# ---- the head region (--head-region, 2026-10-12, pin 14, FAILURE_LOG F43): pin 14's torso read as a face larger than the real near-profile head,
# so the freeze took the torso as the subject. With the option only faces whose box centre lies inside the region count, for the main face and
# for any copy; without it the largest face is the subject exactly as before.
def head_region_px(spec: str | None, W: int, H: int) -> list[int] | None:
    """'x0,y0,x1,y1' in fractions of the frame (0-1) -> pixels, or None."""
    if not spec:
        return None
    try:
        v = [float(t) for t in str(spec).split(",")]
    except ValueError:
        raise SystemExit(f"--head-region: four numbers x0,y0,x1,y1 in fractions of the frame, not {spec!r}")
    if len(v) != 4 or not all(0.0 <= t <= 1.0 for t in v) or v[0] >= v[2] or v[1] >= v[3]:
        raise SystemExit(f"--head-region: four numbers x0,y0,x1,y1 in fractions of the frame (0-1, x0 < x1, y0 < y1), not {spec!r}")
    return [int(round(v[0] * W)), int(round(v[1] * H)), int(round(v[2] * W)), int(round(v[3] * H))]


def _centre_in(box, region) -> bool:
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
    return region[0] <= cx <= region[2] and region[1] <= cy <= region[3]


def face_in_region(src: np.ndarray, region: list[int]) -> tuple[int, int, int, int] | None:
    """The largest face (replicate.detect_faces) whose box centre lies inside the region, or None."""
    import replicate as RP
    faces = [f for f in RP.detect_faces(src, min_px=24) if _centre_in(f["box"], region)]
    return tuple(int(v) for v in faces[0]["box"]) if faces else None


# ---- the eye gate (--eye-gate, 2026-10-12, pin 16): his eyes measured on each return (eye_measure.py) against bands from his real photos at
# the same head turn. It only selects among returns; it never moves a pixel and is not in the prompt, so the request stays the recipe's lock.
def eye_gate_record(spec: str, why: str | None = None) -> dict:
    import eye_measure
    return {"spec": spec, "band": eye_measure.parse_spec(spec), "measured_on": "each raw return (05_generate/raw/vN_raw.*), eye_measure.measure",
            "why": why or "bands from his real photos at the same head turn (eye_measure.py)"}


def eye_gate_problems(raw: Path, gate: dict, m: dict) -> list[str]:
    import cv2
    import eye_measure
    em = eye_measure.measure(cv2.imread(str(raw)))
    m["eyes"] = {k: em.get(k) for k in ("detected", "yaw", "iod_px", "vergence", "ear_near", "ear_far")}
    out = eye_measure.check(em, gate["band"])
    print(f"  eye gate: turn {em.get('yaw')}, vergence {em.get('vergence')}, near-eye EAR {em.get('ear_near')} -> {'FAIL' if out else 'pass'}")
    return out


def with_eye_gate(old: dict, spec: str, version: int, because: str) -> dict:
    """recipe bump --eye-gate: a copy of a replicate/1 version with the eye gate recorded. The lock is untouched (the gate only selects), so the
    request is the same bytes as the version it copies."""
    import copy
    if old["inputs"].get("zone") == "build":
        raise SystemExit("--eye-gate measures his eyes: it applies to zone face, head or expression, not to a body pass")
    rec = copy.deepcopy(old)
    rec["inputs"]["eye_gate"] = eye_gate_record(spec)
    rec["method"]["args"]["eye_gate"] = spec
    rec.update({"version": version, "parent": f"v{old['version']}", "because": because, "created": datetime.now().isoformat(timespec="seconds"),
                "origin": {"kind": "bump", "from": f"v{old['version']}", "notices": []}})
    return rec


def with_placement(old: dict, pic: Path, version: int, because: str) -> dict:
    """recipe bump --place-from: a copy of a replicate/1 version with the placement reference added (or replaced) just before the photo to edit.
    The crop, the readings and every other file stay byte-identical, nothing is read again: the request differs only by that image and the
    rescue sentence."""
    import copy
    from PIL import Image
    import recipe as R
    rec = copy.deepcopy(old)
    inp, lock = rec["inputs"], dict(rec["lock"])
    work = ROOT / ".cache" / "replicate_freeze" / f"{datetime.now():%Y%m%d_%H%M%S}_{rec['id']}_place"
    item, record = placement_item(Path(pic), inp, work)
    refs = [r for r in inp["references"] if r["role"] != "placement"]
    files = [f for f in lock["files"] if f["role"] != "placement"]
    if len(refs) != len(files) or any(r["sha256"] != f["sha256"] for r, f in zip(refs, files)) or files[-1]["role"] != "photo_to_edit":
        raise SystemExit("this version's references and lock files do not line up, or its last image is not the photo to edit")
    with Image.open(item["path"]) as im:
        px = list(im.size)
    refs.insert(len(refs) - 1, R.references_of([item], {})[0])
    files.insert(len(files) - 1, {"n": 0, "role": "placement", "sha256": item["sha256"], "upload_name": item["name"],
                                  "bytes": item["path"].stat().st_size, "px": px})
    for n, (r, f) in enumerate(zip(refs, files), 1):
        r["n"] = f["n"] = n
    inp["references"], inp["place_from"] = refs, record
    rec["method"]["args"]["place_from"] = str(pic).replace("\\", "/")
    prompt = compile_prompt(inp)
    lock.update({"files": files, "prompt": prompt, "prompt_sha256": P.sha256_text(prompt), "compiled_with": compiled_with()})
    lock["request_sha256"] = R.request_sha256(lock)
    rec.update({"version": version, "parent": f"v{old['version']}", "because": because, "lock": lock,
                "created": datetime.now().isoformat(timespec="seconds"),
                "origin": {"kind": "bump", "from": f"v{old['version']}", "freeze_dir": str(work), "notices": []}})
    return rec


async def _freeze_build(args, because, version, parent, ch, config, src, goal, src_res, model, text_models, thr, gates) -> dict:
    """Pass A of a current-look own photo: the body crop, the character's body photos, ONE frozen build reading (both orders), compiled and locked."""
    import characters
    import composite
    import cv2
    import facecard
    import recipe as R
    import replicate as RP
    from session import authenticated_client
    H, W = src.shape[:2]
    pose = facecard.goal_pose(goal)
    if not pose:
        raise SystemExit(f"zone build needs the goal's keypoints: .cache/poses/{goal.stem}.json (tools/pose_compare.py --save-goal)")
    main_box = [int(v) for v in src_res["box"]]
    rect = body_rect(src.shape, pose, main_box)
    work = ROOT / ".cache" / "replicate_freeze" / f"{datetime.now():%Y%m%d_%H%M%S}_{goal.stem}_build"
    work.mkdir(parents=True, exist_ok=True)
    log = _Log(work)
    crop_p = work / CROP_NAME
    cv2.imwrite(str(crop_p), RP.resized_for_send(composite.take(src, rect)))
    # his current physique: the character's body photo (full length) and its front studio photo (waist up: shoulders and arms), whole, neutral names
    items = []
    picks = [(r, "body_full.jpg", "his current physique, full length") for r in characters.body(ch)]
    picks += [(r, "body_waist_up.jpg", "his current shoulders and arms, waist up") for r in characters.faces(ch) if r.get("slot") == "front"]
    for r, up_name, why in picks:
        p = characters.ref_path(r["name"], config)
        if p is None or P.sha256_file(p) != r["sha256"]:
            raise SystemExit(f"{r['name']}: the photo on disk is not the character's (sha256 differs or missing)")
        up = work / up_name
        shutil.copyfile(RP.whole_ref(p, 1600), up)
        items.append({"role": "body", "name": up.name, "path": up, "sha256": P.put_file(up), "from": r["name"], "prep": "full1600_q95 (replicate.whole_ref)",
                      "why": f"character {characters.ref_of(ch)}: {why}"})
    print(f"freezing the body pass of {goal.name}: {W}x{H}, body crop {rect}")
    async with authenticated_client(verbose=False) as client:
        r1 = await RP.gemini_text(client, text_models, BUILD_READ_PROMPT, [items[0]["path"], crop_p], log, "build reading (old as image 2)")
        r2 = await RP.gemini_text(client, text_models, BUILD_READ_PROMPT, [crop_p, items[0]["path"]], log, "build reading (current as image 2)")
    if r1 is None or r2 is None:
        raise SystemExit("the build reading gave no usable answer; nothing frozen (run recipe new again)")
    change = build_change(r1, r2)
    print(f"build reading: old vs current {r1}; current vs old {r2}; used {change}")
    items.append({"role": "photo_to_edit", "name": CROP_NAME, "path": crop_p, "sha256": P.put_file(crop_p), "from": str(goal).replace("\\", "/"),
                  "prep": f"body crop {rect} of the {W}x{H} original, long side {RP.SEND_PX} px",
                  "why": "the crop of his body that is edited to his current physique and pasted back into the untouched original"})
    inputs = {"flags": {}, "own": True, "own_score": round(src_res["score"], 3), "source_kind": "own", "zone": "build", "kind": "build",
              "current_look": True, "crop": rect, "main_box": main_box, "head_boxes": [main_box], "source_size": [W, H], "far": False,
              "readings": {"build": {"prompt_sha256": P.sha256_text(BUILD_READ_PROMPT), "models": text_models, "old_vs_current": r1,
                                     "current_vs_old": r2, "used": change}},
              "build_change": change, "character_build": characters.description_text(ch, "build"), "build_gates": BUILD_GATES,
              "build_prompt": 2, "body_judge": 2, "expected_change": expected_change(change),
              "thresholds": thr, "gates": gates, "expression": "none", "glasses": "same", "look": "any",
              "character": {"ref": characters.ref_of(ch), "sha256": ch["sha256"]},
              "face_choice": {"decided_by": f"character {characters.ref_of(ch)}", "names": [], "count": 0},
              "references": R.references_of(items, {})}
    prompt = compile_prompt(inputs)
    lock = R.make_lock(prompt, items, model, compiled_with())
    key = R.goal_key_of(goal)
    count = int(getattr(args, "samples", None) or 2)
    method = {"route": "replicate", "compiler": COMPILER, "subject": "me",
              "args": {"goal": str(goal).replace("\\", "/"), "zone": "build", "character": characters.ref_of(ch), "current_look": True},
              "model": {"id": model, "label": R.model_label(model, config)}, "text_models": text_models, "samples": count,
              "max_attempts": int(getattr(args, "max_attempts", None) or max(6, count * 3)), "stop": {"after_pose_fails": 0, "on_pass": False}}
    gp = {"key": key, "path": str(goal).replace("\\", "/"), "sha256": P.put_file(goal), "pose": None, "layout": None, "source": None}
    v = version or R.next_version(key)
    return {"schema": R.SCHEMA, "id": key, "version": v, "created": datetime.now().isoformat(timespec="seconds"), "because": because,
            "parent": parent, "origin": {"kind": "bump" if parent else "new", "freeze_dir": str(work), "notices": []},
            "goal": gp, "method": method, "inputs": inputs, "lock": lock}


# ------------------------------------------------------------------------------------------------------------------------------ the run (stages 02 extra, 04-08)


def draw_crop(goal_pinned: Path, rec: dict, out: Path) -> None:
    """02_inputs/crop_on_original.jpg: the frozen crop (green) and the faces inside it (yellow) on the full original, at most 1600 px."""
    import cv2
    import replicate as RP
    img = RP.load_source(base_picture(rec, goal_pinned))
    x, y, w, h = rec["inputs"]["crop"]
    t = max(3, img.shape[1] // 400)
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 200, 0), t)
    for b in rec["inputs"]["head_boxes"]:
        cv2.rectangle(img, (b[0], b[1]), (b[0] + b[2], b[1] + b[3]), (0, 220, 255), t)
    k = 1600 / max(img.shape[:2])
    if k < 1:
        img = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 88])


async def stages(run, rec: dict, config: dict, sent: list[Path], goal_pinned: Path, n_samples: int, no_guard: bool, no_wait: bool,
                 wait_max: float, verbose: bool, remeasure: str | None) -> None:
    """Stages 04-08 of a replicate/1 run."""
    from runner import StageFail
    if remeasure:
        raise StageFail("--remeasure is not available for replicate/1 runs: its gates include the AI judge, which needs Gemini calls", code=2)
    cands = await _generate(run, rec, config, sent, goal_pinned, n_samples, no_guard, no_wait, wait_max, verbose)
    _measure_review_result(run, rec, config, sent, goal_pinned, cands)


async def _generate(run, rec, config, sent, goal_pinned, n_samples, no_guard, no_wait, wait_max, verbose) -> list[dict]:
    import composite
    import cv2
    import identity
    import numpy as np
    import replicate as RP
    import runner
    from credit_guard import Guard, GuardRefused
    from gemini_webapi.exceptions import APIError, GeminiError, ImageGenerationError, UsageLimitExceededError
    from runner import StageFail
    from scorer import ArcFaceScorer
    from session import AuthError, authenticated_client, credits_left, describe_usage, usage_of
    lock, inp, meth = rec["lock"], rec["inputs"], rec["method"]
    model = lock["model"]
    label = meth["model"].get("label") or model
    text_models = meth.get("text_models") or [config.get("vision_model") or model, model]
    thr, gates = inp["thresholds"], inp["gates"]
    gates = {**gates, "size_own": tuple(gates["size_own"]), "size_foreign": tuple(gates["size_foreign"])}
    max_attempts = int(meth.get("max_attempts") or max(6, n_samples * 3))
    d = run.dir
    guard = Guard(config.get("credit_guard"))
    build = inp.get("zone") == "build"
    # the measuring side, rebuilt from the pinned picture it edits (his original, or pass A's picture for a pass B): deterministic
    src = RP.load_source(base_picture(rec, goal_pinned))
    rect = tuple(inp["crop"])
    head_boxes = [tuple(b) for b in inp["head_boxes"]]
    src_crop = composite.take(src, rect)
    if build:
        import segment
        person = segment.person_mask(src, tuple(inp["main_box"]))
        main_in_crop, scorer, pool, dups, src_eval, src_gap = None, None, None, set(), None, None
    else:
        main_in_crop = tuple(inp["main_in_crop"])
        scorer = ArcFaceScorer()
        pool = identity.build_pool(config, scorer, verbose=False)
        # --head-region (F43): the frozen main face, not the largest one; absent, exactly as before
        sres = identity.score_image(src, pool, scorer, expect_box=tuple(inp["main_box"])) if inp.get("head_region") else identity.score_image(src, pool, scorer)
        dups = identity.duplicates_of(sres["emb"], pool) if sres.get("detected") else set()
        src_eval = identity.score_image(src_crop, pool, scorer, exclude_names=dups, expect_box=main_in_crop)
        if not src_eval.get("detected"):
            src_eval = identity.score_image(src, pool, scorer, exclude_names=dups)
        src_gap = RP.face_neck_gap(src_crop, src_eval["box"])
    run.legacy["replicate"] = {"crop": list(rect), "source_kind": inp["source_kind"], "zone": inp["zone"], "expression": inp["expression"],
                               "source_face_neck_gap": None if src_gap is None else round(src_gap, 1), "duplicates_excluded": sorted(dups)}
    log = _Log(d)
    cands: list[dict] = []
    try:
        async with authenticated_client(verbose=verbose) as client:
            # ---------------------------------------------------------------- 04 credits
            with run.stage(4) as s:
                sd = run.stage_dir(4)
                info = {"account_status": client.account_status.name, "model": model, "model_label": label, "text_models": text_models}
                with contextlib.suppress(Exception):
                    m_ = [x for x in client.list_models() if x.model_id == model]
                    info["model_listed"] = {"display_name": m_[0].display_name, "available": m_[0].is_available} if m_ else "not in this account's list"
                with contextlib.suppress(Exception):
                    await client._fetch_usage_info()
                info["usage_at_start"] = describe_usage(usage_of(client))
                info["credits_left_at_start"] = credits_left(client)
                waited0 = time.time()
                if no_guard:
                    info["guard"] = "skipped (--no-guard)"
                else:
                    async def _fresh():
                        with contextlib.suppress(Exception):
                            await client._fetch_usage_info()
                        return credits_left(client)
                    try:
                        info["guard"] = await guard.acquire(is_pro=label == "pro", images=n_samples, label=d.name, refresh=_fresh,
                                                            wait_max=0.0 if no_wait else float(wait_max))
                    except GuardRefused as e:
                        info["guard"] = f"refused: {e}"
                        P.atomic_write_json(sd / "credits.json", info)
                        raise StageFail(f"credit guard refused, nothing was generated: {e}", code=3)
                info["waited_secs"] = round(time.time() - waited0, 1)
                # the session can expire while a run waits for credits (2026-10-09: 49 min of waiting, then UNAUTHENTICATED on every attempt)
                if info["waited_secs"] > 60 and credits_left(client) is None:
                    P.atomic_write_json(sd / "credits.json", info)
                    raise StageFail("the Gemini session expired while this run waited for credits: refresh the cookies (vault popup) and run again", code=1)
                runner.note_model_change(run, rec, info)
                P.atomic_write_json(sd / "credits.json", info)
                s["summary"] = (f"{info['account_status']}; model {label} {model}" + (f" ({info['model_listed']['display_name']})" if isinstance(info.get('model_listed'), dict) else "")
                                + f"; {info['usage_at_start']}; guard " + ("skipped" if no_guard else f"ok after {info['waited_secs']} s")
                                + (f"; MODEL CHANGED: {info['model_change']}" if info.get("model_change") else ""))

            # ---------------------------------------------------------------- 05 generate
            with run.stage(5) as s:
                sd = run.stage_dir(5)
                (sd / "raw").mkdir(exist_ok=True)
                credit_log = {"model": model, "start": credits_left(client), "calls": []}
                run.legacy["credits"] = credit_log
                last = [credit_log["start"]]
                passing, stopped = 0, None
                for i in range(1, max_attempts + 1):
                    if passing >= n_samples:
                        break
                    print(f"\nAttempt {i}/{max_attempts} (want {n_samples} passing, have {passing}): the identical request")
                    call: dict = {"index": i, "started": runner.now(), "upload_retries": 0, "request_sha256": lock["request_sha256"]}
                    cand: dict = {"index": i, "stages": []}
                    t0 = time.time()
                    output = None
                    try:
                        for up_try in range(3):
                            try:
                                output = await client.generate_content(lock["prompt"], files=[str(p) for p in sent], model=model, temporary=True)
                                break
                            except (GeminiError, APIError, UsageLimitExceededError):
                                raise
                            except Exception as e:   # a 5xx from Google's file-upload service: nothing generated yet
                                if "HTTP Error 5" not in str(e) or up_try == 2:
                                    raise
                                call["upload_retries"] += 1
                                await asyncio.sleep(20 * (up_try + 1))
                    except UsageLimitExceededError:
                        call["outcome"], stopped = "usage_limit", "usage limit"
                    except (APIError, GeminiError) as e:     # APIError: e.g. code 1099, a temporary Google issue (2026-10-08): this call's outcome, the run goes on
                        call.update({"outcome": "error", "error": f"{type(e).__name__}: {e}"})
                        if "UNAUTHENTICATED" in str(e):      # an expired session fails every later attempt too: stop here, nothing is charged
                            stopped = "the Gemini session expired (refresh the cookies)"
                    raw = None
                    if output is not None:
                        c_ = output.candidates[output.chosen]
                        call.update({"metadata": list(output.metadata or []), "text": c_.text, "thoughts": (c_.thoughts or "")[:4000] or None})
                        if c_.generated_images:
                            img = c_.generated_images[0]
                            raw = RP.fix_extension(Path(await img.save(path=str(sd / "raw"), filename=f"v{i}_raw.png", verbose=verbose)))
                            ir = runner.image_record(raw)
                            ir["full_size"] = not str(getattr(img, "url", "")).endswith(("=s2048-rj", "=s1024-rj"))
                            call.update({"outcome": "image", "images": [ir]})
                        else:
                            call["outcome"] = "no_image"
                            if "limit resets" in (c_.text or "") or "image limit" in (c_.text or "").lower():
                                stopped = "image limit (text reply)"
                    call["secs"] = round(time.time() - t0, 1)
                    if raw is not None:
                        base, zone_mask, meta = RP.paste_return(src.copy(), rect, raw, call.get("text") or "", f"v{i}")
                        cand["stages"].append(meta)
                        call["merge"] = meta
                        if "failed" in meta:
                            cand.update({"problems": [f"v{i}: {meta['failed']}"], "verdict": "invalid"})
                            print(f"  not merged: {meta['failed']}")
                        else:
                            png = d / f"v{i}_0.png"
                            if build:
                                m, problems, warnings, ver, saved, out_crop = measure_build_candidate(
                                    src, base, rect, zone_mask, person, inp["main_box"], png, sd / f"cand{i}_crop.jpg", t0, inp["build_gates"])
                                cand.update({"metrics": m, "outside_check": ver})
                                await judge_body(client, text_models, sent[-1], sd / f"cand{i}_crop.jpg", log, cand, problems, warnings,
                                                 version=int(inp.get("body_judge") or 1), expected=inp.get("expected_change"))
                                cand.update({"problems": problems, "warnings": warnings, "verdict": "invalid" if problems else "accept"})
                            else:
                                m, problems, warnings, ver, saved, out_crop = RP.measure_candidate(
                                    src, base, rect, zone_mask, src_crop, src_eval, pool, scorer, dups, gates, inp["source_kind"], inp["far"], head_boxes,
                                    src_gap, inp["zone"], main_in_crop, png, sd / f"cand{i}_crop.jpg", t0, expression_edit=(inp["zone"] == "expression"))
                                cand.update({"metrics": m, "outside_check": ver})
                                if inp.get("eye_gate"):     # --eye-gate (2026-10-12): absent in older versions, which run as before
                                    problems += eye_gate_problems(raw, inp["eye_gate"], m)
                                await RP.judge_candidate(client, text_models, sent[-1], sd / f"cand{i}_crop.jpg", log, cand, problems, warnings, m, thr,
                                                         inp["expression"], inp["source_kind"], glasses=inp.get("glasses") or "same",
                                                         expression_edit=(inp["zone"] == "expression"), source_glasses=source_glasses_of(inp))
                                cand["verdict"] = RP.verdict_of(problems, m, thr)
                            passing += cand["verdict"] in ("accept", "uncertain")
                            a, b = src_crop, out_crop
                            dd = np.clip(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(axis=2) * 4, 0, 255).astype(np.uint8)
                            T = 512
                            panels = [cv2.resize(p_, (T, int(T * p_.shape[0] / p_.shape[1]))) for p_ in (a, b, cv2.applyColorMap(dd, cv2.COLORMAP_JET))]
                            cv2.imwrite(str(sd / f"compare_head_{i}.jpg"), np.hstack(panels), [cv2.IMWRITE_JPEG_QUALITY, 90])
                            if build:
                                print(f"  v{i}_0.png: body pass: background drift {m.get('bg_drift')}, silhouette widths "
                                      f"{(m.get('physique') or {}).get('output_over_source')}, judge {(cand.get('judge') or {}).get('body_change')} -> "
                                      f"{cand['verdict'].upper()}" + "".join(f"\n    FAIL: {p_}" for p_ in cand.get("problems", [])))
                            else:
                                print(f"  v{i}_0.png: identity {m.get('score')} size {m.get('size_ratio')} shift {m.get('face_shift_frac')} light dE "
                                      f"{(m.get('light') or {}).get('dE')} neck gap {m.get('neck_gap')} -> {cand['verdict'].upper()}"
                                      + "".join(f"\n    FAIL: {p_}" for p_ in cand.get("problems", [])))
                    now_left = credits_left(client)
                    used = (last[0] - now_left) if (now_left is not None and last[0] is not None) else None
                    last[0] = now_left
                    credit_log["calls"].append({"index": i, "outcome": call.get("outcome"), "credits": used, "left": now_left})
                    call.update({"credits_used": used, "credits_left": now_left, "candidate": cand})
                    P.atomic_write_json(sd / f"call_{i}.json", call)
                    cands.append(cand)
                    print(f"[Credits] this attempt {used} (edit + judge), window left {now_left}")
                    if stopped:
                        break
                passing_c = [c for c in cands if c.get("verdict") in ("accept", "uncertain")]
                if len(passing_c) >= 2 and not build:
                    print(f"\n{len(passing_c)} pictures passed; the AI compares their faces pair by pair, both orders")
                    wins = await RP.rank_by_face(client, text_models, sd, passing_c, log,
                                                 prompt=RP.SMILE_PAIR_PROMPT if inp.get("rank") == "smile" else None)
                    for c in cands:
                        c["face_wins"] = wins.get(c["index"])
                    P.atomic_write_json(sd / "face_ranking.json", log.data.get("face_ranking") or {})
                with contextlib.suppress(Exception):
                    await asyncio.sleep(3)
                    await client._fetch_usage_info()
                credit_log["end"] = credits_left(client)
                if credit_log["start"] is not None and credit_log["end"] is not None:
                    credit_log["total"] = credit_log["start"] - credit_log["end"]
                P.atomic_write_json(sd / "credits.json", credit_log)
                n_img = sum(1 for c in cands if c.get("metrics"))
                s["summary"] = (f"{len(cands)} attempt(s) of the identical request: {n_img} merged picture(s), {len(passing_c)} passing the gates"
                                + (f"; stopped: {stopped}" if stopped else "") + f"; credits {credit_log.get('total')} (window left {credit_log.get('end')})")
                if not n_img:
                    raise StageFail("no picture could be merged into the original", code=1)
    except AuthError as e:
        print(str(e))
        run.manifest["failed_stage"] = 4
        run.mark(4, "failed", "authentication failed: refresh the Gemini cookies in the vault popup (see the message above)")
        raise StageFail(f"authentication failed: {e}", code=1)
    finally:
        guard.release()
    return cands


def edge_step(src, pic, rect, inset: int = 5, width: int = 20) -> dict:
    """Record-only (2026-10-08): the colour step of the pasted crop at its edge, the mean BGR difference to the original in a strip just inside
    each side of the crop. Kayak v5/v6 showed a lighter rectangle of sky (steps of about 3-4 levels) that the drift gate (SSIM / mean diff) passes."""
    import numpy as np
    x, y, w, h = (int(v) for v in rect)
    strips = {"top": (slice(y + inset, y + inset + width), slice(x, x + w)), "bottom": (slice(y + h - inset - width, y + h - inset), slice(x, x + w)),
              "left": (slice(y, y + h), slice(x + inset, x + inset + width)), "right": (slice(y, y + h), slice(x + w - inset - width, x + w - inset))}
    out = {}
    for k, (sy, sx) in strips.items():
        a, b = pic[sy, sx].astype(np.float32), src[sy, sx].astype(np.float32)
        if a.size and a.shape == b.shape:
            d = (a - b).reshape(-1, 3).mean(axis=0)
            out[k] = round(float(np.abs(d).max()), 2)
    out["max"] = max(out.values()) if out else None
    return out


def _measure_review_result(run, rec, config, sent, goal_pinned, cands) -> None:
    import headpose
    import runner
    d = run.dir
    pics = [c for c in cands if c.get("metrics")]
    # ---------------------------------------------------------------- 06 measure
    ch = runner.character_of(rec)
    import cv2
    import replicate as RP
    src_full = RP.load_source(base_picture(rec, goal_pinned))
    with run.stage(6) as s:
        sd = run.stage_dir(6)
        out = []
        for c in pics:
            p = d / c["metrics"]["file"]
            rec_only = {"head_pose": headpose.measure(p), **runner.character_record(p, ch)}
            with contextlib.suppress(Exception):
                rec_only["edge_step"] = edge_step(src_full, cv2.imread(str(p)), rec["inputs"]["crop"])
            out.append({"file": p.name, "verdict": c["verdict"], "problems": c.get("problems", []), "warnings": c.get("warnings", []),
                        "metrics": c["metrics"], "judge": c.get("judge"), "face_vs_source": c.get("face_vs_source"), "face_wins": c.get("face_wins"),
                        "pose_gate": "not applicable: replicate keeps every pixel outside the crop (checked: 0 px changed outside)",
                        "record_only": rec_only})
        P.atomic_write_json(sd / "measure.json", {"gates": rec["inputs"]["gates"], "thresholds": rec["inputs"]["thresholds"],
                                                  "rule": "replicate's gates (facecard.json gates, identity_thresholds); identity = pool score of the edited crop",
                                                  "samples": out, "not_merged": [{"index": c["index"], "problems": c.get("problems")} for c in cands if not c.get("metrics")]})
        status = {"accept": "accepted", "uncertain": "uncertain"}
        run.legacy["results"] = [{"index": c["index"], "files": [c["metrics"]["file"]], "evaluations": [
            {"raw_file": c["metrics"]["file"], "raw_score": c["metrics"].get("score"), "restored_file": None, "restored_score": None,
             "status": status.get(c["verdict"], "rejected"), "problems": c.get("problems", [])}]} for c in pics]
        run.legacy["identity_threshold"] = rec["inputs"]["thresholds"].get("accept")
        s["summary"] = f"{len(pics)} picture(s): " + ", ".join(f"{c['metrics']['file']} {c['verdict']} (identity {c['metrics'].get('score')})" for c in pics)

    # ---------------------------------------------------------------- 07 review
    import sys
    with run.stage(7) as s:
        sd = run.stage_dir(7)
        sys.path.insert(0, str(ROOT / "tools"))
        import audit_views
        lines = []
        face_files = [p for f, p in zip(rec["lock"]["files"], sent) if f["role"] == "face"]
        for c in pics:
            p = d / c["metrics"]["file"]
            try:
                lines += audit_views.make_views(p.stem, goal_pinned, p, d, sd, ref_paths=face_files, goal_kp=None)
            except Exception as exc:
                lines.append(f"{p.name}: audit views failed: {type(exc).__name__}: {exc}")
            lines.append(runner.character_sheet(p, ch, sd / f"{p.stem}_character.jpg"))
        chk = {c["metrics"]["file"]: (P.read_json(d / (c["metrics"]["file"] + ".checklist.json"), None) or {}).get("verdict", "not checked yet") for c in pics}
        P.atomic_write_json(sd / "review.json", {"lines": lines, "checklist": chk})
        s["summary"] = f"audit sheets for {len(pics)} picture(s) in {sd.name}; checklist: " + ", ".join(f"{k} {v}" for k, v in chk.items())

    # ---------------------------------------------------------------- 08 result
    with run.stage(8) as s:
        sd = run.stage_dir(8)
        rank = {"accept": 2, "uncertain": 1}
        ranked = sorted(pics, key=lambda c: (c.get("face_wins") or 0.0, rank.get(c["verdict"], 0), c["metrics"].get("score") or -1.0), reverse=True)
        rows = [{"file": c["metrics"]["file"], "verdict": c["verdict"], "sort_key": {"face_wins": c.get("face_wins") or 0.0,
                 "band": rank.get(c["verdict"], 0), "identity": c["metrics"].get("score")}} for c in ranked]
        best = next((c for c in ranked if c["verdict"] in rank), None)
        if best:
            shutil.copy2(d / best["metrics"]["file"], d / "best.png")
            run.legacy["best"] = {"file": "best.png", "source": best["metrics"]["file"], "score": best["metrics"].get("score"), "status": best["verdict"]}
        export_lines = []
        if run.kind == "run":
            try:
                sys.path.insert(0, str(ROOT / "tools"))
                import export_results
                run.save()
                export_lines = export_results.export_many([d])
            except Exception as exc:
                export_lines = [f"export skipped: {type(exc).__name__}: {exc}"]
        P.atomic_write_json(sd / "result.json", {"ranking": rows, "best": run.legacy.get("best"),
                                                  "best_rule": "the AI's pairwise face wins, then accept over uncertain, then identity, among pictures that "
                                                               "passed every gate; a candidate only until the 35-item checklist passes",
                                                  "export": export_lines})
        s["summary"] = ((f"best.png = {best['metrics']['file']}" if best else "no best.png (no picture passed every gate)") + "; ranking "
                        + " > ".join(r["file"] for r in rows) + f"; {len(export_lines)} export line(s)")
