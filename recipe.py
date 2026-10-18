"""Recipes: the frozen METHOD for one goal (the user, 2026-10-07: "even if the generation is faulty, it is still consistent; the method used to
generate the image is followed consistently each time").

A recipe version is one immutable file, recipes/<collection>/<NN>-<title>/v<N>.json, tracked in git (text only: never an image). It holds
  inputs  what was decided: the goal, the flags, the inventory, every reference photo by role with sha256 and WHY it was chosen
  lock    what goes over the wire: the exact prompt, the files in send order (sha256 + upload file name), the model; request_sha256 hashes exactly that
Any change is a new version (`recipe bump --because "<failed item / the user's words>"`); a version is never edited. `facecard.py run <recipe>`
sends the lock, byte for byte (the bytes come from the blob store, provenance.py), so the same recipe version always sends the same request.
Gemini cannot be seeded, so the pictures still differ; everything else is identical and recorded.

Drift: a run also recompiles the recipe's inputs with today's template, face/build text and compiler. A difference is shown as METHOD DRIFT
(the run still sends the lock); a new method needs a bump.

compile_route_g() is the Route G prompt compiler, moved here unchanged from facecard.build_goal_request (2026-10-07) so that it can run on
frozen inputs: it only counts and labels images, it never reads a file.
"""
from __future__ import annotations

import difflib
import json
import math
import re
from datetime import datetime
from pathlib import Path

import provenance as P

ROOT = Path(__file__).resolve().parent
RECIPES = ROOT / "recipes"
SCHEMA = "facecard.recipe/1"
REQUEST_SCHEMA = "facecard.request/1"
COMPILER = "route_g/1"

# ------------------------------------------------------------------------------------------------------------------------------ prompt pieces
# (moved from facecard.py; facecard re-exports them, tools/goal_layout.py imports layout_text from there)


def layout_text(lay: dict) -> str:
    """The goal's frame layout in Gemini's own box format (normalized 0-1000, [ymin, xmin, ymax, xmax]), read by tools/goal_layout.py. The user
    asked (2026-09-26) for something Gemini understands better than a 3x3 grid to hold the camera distance and the subject's boundary."""
    fmt = lambda b: f"[{b[0]}, {b[1]}, {b[2]}, {b[3]}]"
    parts = [f"his whole body {fmt(lay['person'])}", f"his head {fmt(lay['head'])}"]
    parts += [f"the {o['name']} {fmt(o['box'])}" for o in lay.get("objects", [])]
    return ("LAYOUT: Frame positions as bounding boxes normalized to 0-1000, [ymin, xmin, ymax, xmax]: " + "; ".join(parts) + ". Place him, "
            "his head and these things exactly inside these boxes: the same size in the frame and so the same camera distance.")


_KP_WORDS = [("nose", "his nose"), ("r_shoulder", "his right shoulder"), ("l_shoulder", "his left shoulder"), ("r_elbow", "his right elbow"),
             ("r_wrist", "his right hand"), ("l_elbow", "his left elbow"), ("l_wrist", "his left hand"), ("r_hip", "his right hip"),
             ("l_hip", "his left hip"), ("r_knee", "his right knee"), ("l_knee", "his left knee"), ("r_ankle", "his right foot"),
             ("l_ankle", "his left foot")]


def pose_points_text(pose: dict) -> str:
    """POSE POINTS: the goal's measured joints in Gemini's own point format ([y, x], 0-1000), plus plain facts computed from them by code
    (stance, legs straight or bent, torso lean, hand heights). The user, 2026-09-27: the checklist has to be built into the request; a posture
    written from my reading of the goal left the legs out entirely (table tennis v7 drew a stride where the goal stands with feet together)."""
    kp, (W, H) = pose["person"]["kp"], pose["wh"]
    ok = {k: v for k, v in kp.items() if v[2] >= 0.5}
    pt = lambda k: f"[{round(ok[k][1] * 1000)}, {round(ok[k][0] * 1000)}]"
    parts = [f"{w} {pt(k)}" for k, w in _KP_WORDS if k in ok]
    facts = []
    mid = lambda a, b: ((ok[a][0] + ok[b][0]) / 2, (ok[a][1] + ok[b][1]) / 2) if a in ok and b in ok else None
    sh, hip = mid("l_shoulder", "r_shoulder"), mid("l_hip", "r_hip")
    if sh and hip:
        lean = math.degrees(math.atan2((sh[0] - hip[0]) * W, (hip[1] - sh[1]) * H))
        facts.append(f"his torso is {'upright' if abs(lean) < 6 else 'leaning'} ({abs(lean):.0f} degrees from vertical"
                     + ("" if abs(lean) < 6 else f", toward picture-{'right' if lean > 0 else 'left'}") + ")")
        torso = math.hypot((hip[0] - sh[0]) * W, (hip[1] - sh[1]) * H)
        if "l_ankle" in ok and "r_ankle" in ok:
            apart = math.hypot((ok["l_ankle"][0] - ok["r_ankle"][0]) * W, (ok["l_ankle"][1] - ok["r_ankle"][1]) * H) / torso
            words = "both feet close together under his hips" if apart < 0.35 else ("feet about hip-width apart" if apart < 0.6 else "feet wide apart")
            facts.append(f"{words} (ankles {apart:.2f} of his torso length apart)")
        for s_, k_, a_ in (("his right", "r_knee", ("r_hip", "r_ankle")), ("his left", "l_knee", ("l_hip", "l_ankle"))):
            if k_ in ok and a_[0] in ok and a_[1] in ok:
                v1 = ((ok[a_[0]][0] - ok[k_][0]) * W, (ok[a_[0]][1] - ok[k_][1]) * H)
                v2 = ((ok[a_[1]][0] - ok[k_][0]) * W, (ok[a_[1]][1] - ok[k_][1]) * H)
                ang = math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2) + 1e-9)))))
                facts.append(f"{s_} leg {'straight' if ang > 165 else ('slightly bent' if ang > 145 else 'bent')} ({ang:.0f} degrees at the knee)")
    if sh:
        span = hip[1] - sh[1] if hip else None
        for w, name in (("r_wrist", "his right hand"), ("l_wrist", "his left hand")):
            if w in ok:
                if span:
                    f = (ok[w][1] - sh[1]) / span
                    h = ("at shoulder height" if f < 0.2 else "at chest height" if f < 0.6 else "at waist height" if f < 1.05 else "below his waist")
                else:
                    h = "above his shoulders" if ok[w][1] < sh[1] else "below his shoulders"
                dx = ok[w][0] - sh[0]
                where = (f"{abs(dx):.2f} of the frame width out to picture-{'left' if dx < 0 else 'right'} of the middle of his chest"
                         if abs(dx) >= 0.03 else "in front of the middle of his chest")
                facts.append(f"{name} is {h}, {where}")
    return ("POSE POINTS, measured from the goal (normalized 0-1000 as [y, x]; his own right and left): " + "; ".join(parts) + ". Put each of "
            "his joints exactly at these points: the same posture and the same place in the frame. In words: " + "; ".join(facts) + ".")


def scene_text_of(res: dict) -> str:
    """The --prompt text with the layout and POSE POINTS appended exactly as build_goal_request always did (before any inventory replaces it)."""
    st, flags = res["scene_text_base"], res["flags"]
    if res.get("layout") and not flags.get("replace_subject"):
        # (replace-subject: the photo to edit carries the layout itself; the box text made tt-W v3_0 draw black boxes, 2026-09-27)
        st = st + "\n\n" + layout_text(res["layout"])
    if res.get("pose") and flags.get("pose_points"):
        st = st + "\n\n" + pose_points_text(res["pose"])
    return st


# ------------------------------------------------------------------------------------------------------------------------------ the compiler


def compile_route_g(res: dict, profile: dict, template: str) -> tuple[str, list[dict], dict, list[tuple[str, str]]]:
    """Route G (2026-09-26, the user's own prompt structure): his reference photos labelled by ROLE (face refs chosen by the goal's head pose,
    his true-build body photo, his shoulder-and-arm photo), his fixed FACE and BUILD text from subject_profiles, and the goal written as text
    (POSE / WARDROBE / SCENE / LIGHT / CAMERA, from scene-prompt-writer). The goal photo itself is never sent when it shows another man: sent
    photos leak their model's skull, jaw and neck (measured 2026-09-19), and a public figure's photo is refused. When the goal is his OWN photo
    it is sent too, labelled as the original photo to recreate.

    `res` holds resolved items (facecard.resolve_goal_inputs, or a recipe's frozen references): this only counts and labels them.
    Returns (prompt, items in send order, log, notices). Notices are ("drop", msg) for a flag whose text the inventory throws away and ("info", msg)."""
    items, flags, inv = res["items"], res["flags"], res.get("inventory")
    goal = res["goal"]
    scene_text = scene_text_of(res)
    notices: list[tuple[str, str]] = []
    files: list[dict] = []
    lines: list[str] = []

    def add(group: list[dict], one: str, many: str) -> tuple[int, int]:
        if not group:
            return 0, 0
        a = len(files) + 1
        files.extend(group)
        b = len(files)
        lines.append(f"Image {a} is {one}" if a == b else f"Images {a}-{b} are {many}")
        return a, b

    faces = list(items.get("faces") or [])
    body_only = bool(flags.get("body_only"))
    edit_photo = flags.get("edit_photo")
    if inv and inv.get("mode") == "objects":
        ref_n = {}
        for it in items.get("inv_refs") or []:
            ref_n[it["key"]], _ = add([it], it["label"], "")
        edit_n, _ = add([items["photo_to_edit"]], "the PHOTO TO EDIT.", "")
        change = [f"- {c['item']}: the PHOTO TO EDIT shows {c['goal']}; make it {c['his']}"
                  + (f" (image {ref_n[c['ref']]})" if c.get("ref") in ref_n else "") + "." for c in inv.get("change", [])]
        keep = [f"- {k}." for k in inv.get("keep", [])]
        prompt = ("REFERENCE IMAGES BY ROLE:\n" + "\n".join(lines) + f"\n\nEdit image {edit_n}, the PHOTO TO EDIT: make exactly the changes "
                  "in the CHANGE LIST and nothing else. Its framing and everything not in the CHANGE LIST stay exactly as they are.\n\n"
                  "CHANGE LIST:\n" + "\n".join(change) + "\n\nKEEP LIST (exactly as in the PHOTO TO EDIT):\n" + "\n".join(keep)
                  + "\n\nPhotorealistic photograph with the same light, colour, grain and sharpness as the PHOTO TO EDIT.")
        log = {"route": "G", "mode": "objects", "goal": str(goal), "goal_sent": False, "layout": None, "goal_own_score": None,
               "roles": {"face": [], "body": [], "arms": []}, "props": [], "layout_sketch": None, "scene_text": "\n".join(change),
               "goal_role": "photo to edit", "pose_points": False, "body_only": False, "edit_photo": None, "inventory": res.get("inventory_path")}
        return prompt, files, log, notices
    body, arms = list(items.get("body") or []), list(items.get("arms") or [])
    if edit_photo:   # his own photo is the photo to edit, so it also carries his build: no separate body/arm references
        body, arms = [], []
    if not body_only:   # body-only edits keep the head's pixels: no face photos to redraw it from (faces still score identity)
        add(faces, "the FACE reference of this man.", "FACE references of this man.")
    build_sheet = items.get("build_sheet")
    body_end = None
    if build_sheet and not edit_photo:
        # --build-sheet (2026-10-07 research: Nano Banana 2 documents up to 4 images of a character): his body and arm photos travel as ONE image
        body, arms = [], []
        body_n, _ = add([build_sheet], "the BUILD reference: two photos of his body side by side, for his build only (shoulders, arms, chest, "
                        "waist), never for his face, hair or clothes.", "")
    elif res.get("physique"):
        # --physique (the user's yardstick, 2026-10-10): the standard's approved physique photo(s), labelled by the standard
        body_n, body_end = add(body, res["physique"]["label"], res["physique"]["label"])
    else:
        body_n, _ = add(body, "the BODY reference — his true build and proportion.", "BODY references — his true build and proportion.")
    add(arms, "the SHOULDER AND ARM reference.", "SHOULDER AND ARM references.")
    ref_n = {}
    for it in items.get("inv_refs") or []:
        ref_n[it["key"]], _ = add([it], it["label"], "")
    # Objects of his own, by role (the user, 2026-09-27: his Honda CB350 found in his photos, as the pin's motorcycle). PATH::LABEL.
    props = []
    for it in items.get("props") or []:
        add([it], it["label"], "")
        props.append({"path": it.get("arg"), "label": it["label"]})
    sketch = items.get("sketch")
    if sketch:
        stick = (" The black stick figure is his exact posture: every limb, both hands and both feet where the stick figure has them."
                 if sketch.get("stick") else "")
        add([sketch], f"a LAYOUT SKETCH, not a photograph: flat coloured boxes marking where things sit in the frame ({sketch['colour_key']}).{stick} The "
            "photograph has exactly this frame: he, his head and these things fill exactly these boxes, the same size and the same camera "
            "distance. Draw nothing of the sketch itself: the photograph shows no coloured rectangles, box outlines or lines.", "")
        # ^ named only after it happened: pin v9 v3_0 drew the sketch's boxes into the photo (2026-09-27)
    replace = bool(flags.get("replace_subject"))
    goal_role = flags.get("goal_as_image") == "goal" and not replace
    own = bool(res.get("own"))
    if edit_photo:
        ep_n, _ = add([items["edit_photo"]], "the PHOTO TO EDIT: his own full-length photo. His body in it — his "
                      "shoulders, arms, chest, waist and height — is his true build.", "")
    if goal_role and edit_photo:
        add([items["goal_image"]], "the GOAL IMAGE, a reference for the scene, pose, clothes, framing and light only. The man in the GOAL "
            "IMAGE is NOT the subject: nothing of his face, hair, beard, head shape, neck, skin or body build is carried over.", "")
    elif goal_role:
        # The user, 2026-09-27: send the goal itself, labelled as the goal, with the subject taken only from the references.
        add([items["goal_image"]], "the GOAL IMAGE. Recreate this photograph exactly: the same composition and framing, the same "
            "camera distance and angle, his exact posture (torso, both arms, both hands, both legs and feet) and exactly where he stands in the "
            "frame and against every object, the same scene, clothes and light. The man in the GOAL IMAGE is NOT the subject and must not "
            "appear: nothing of his face, hair, beard, head shape, jaw, neck, skin, body build or height is carried over. The subject is only "
            f"the man of images 1-{len(faces) + len(body) + len(arms)}.", "")
    if replace:
        # The user, 2026-09-27: "replace the newer me (the reference images: body, face, hair, beard, everything) in place of the goal image's
        # subject". The goal is the photo to edit, so posture, position and framing come from its own pixels.
        edit_n, _ = add([items["photo_to_edit"]], "the PHOTO TO EDIT.", "")
    if own and not replace and not goal_role:
        add([items["original"]], "the ORIGINAL PHOTO of this moment: recreate exactly its pose, framing, camera distance, "
            "clothes, background and light; his face, hair, beard and moustache come only from the FACE references, never from this photo.", "")
    char = res.get("character")
    # a character recipe (2026-10-08): his face and build in words come from the character's description, read from the same photos that are
    # sent, instead of subject_profiles' face_text / build_text (which described him leaner than his current photos). Older recipes: unchanged.
    face_text = str(profile.get("face_text", "")) if not char else character_face_text(char)
    if body_only:
        face_text = ("Do not redraw his head. His head stays exactly as it is in the PHOTO TO EDIT, pixel for pixel: the same face, hair, beard, "
                     "eyewear, head tilt and bow, and the same gaze direction.")
    elif own or replace or goal_role:
        # The user, 2026-09-26: even when the goal is his own photo, his face, hair, beard and moustache come from the FACE references, never
        # from the goal's face (table tennis v5: a bigger beard and moustache than his references). The original gives the scene only.
        role_word = "photo to edit" if replace else ("goal image" if goal_role else "original photo")
        face_text += (f" His face, hair, beard and moustache come only from the FACE references (images 1-{len(faces)}), never from the "
                      f"{role_word}: his hair is the full tight curly black hair of the references even where the {role_word} shows it "
                      "cut shorter.")   # table tennis v6 copied the photo's short cut; item 28 fail confirmed by the user 2026-09-27
    template = template.strip()
    build = (str(profile.get("build_text", "")) if not char else character_build_text(char)).replace("{BODY}", str(body_n or 5))
    phys = res.get("physique") if body_n and not build_sheet and not edit_photo else None
    # with --physique the BODY numbers name every physique photo ("5" or "5-6"); without it they read exactly as before
    body_ref = (f"{body_n}" if body_end == body_n else f"{body_n}-{body_end}") if phys else str(body_n or 5)
    body_word = "images" if phys and body_end != body_n else "image"
    if phys:
        build = phys["build"].replace("{BODY}", body_ref)
    if (replace or goal_role) and not own and char:
        # The goal man's build is not described by a fixed sentence (the old one called every pin's man "broader and far more muscular", true or
        # not); his own build is named by its reference image.
        # Pin 14 v3 (FAILURE_LOG F28): face-leanness words caused the user's complaint, and a body-only edit keeps the pin man's head, so an
        # inventory with "no_face_words": true names only his body here. Every recipe without that key compiles exactly as before.
        lean_of = "his body is" if body_only and (inv or {}).get("no_face_words") else "his face and body are"
        build += (f" His whole body is his own, from {body_word} {body_ref}: his shoulders, arms, chest and waist, and how lean or full {lean_of}, "
                  f"exactly as in his references, never as the man in the {'photo to edit' if replace else 'goal image'}.")
    elif (replace or goal_role) and not own:
        # The user, 2026-09-27: every Pinterest version kept the goal man's heavy build (broad thick shoulders, big arms), not his.
        # Named only now that it has happened (the image-prompt rule).
        arms_n = f" and {body_n + 1}" if arms else ""
        build += (f" His whole body is his own, from images {body_n or 5}{arms_n}: never the build of the man in the "
                  f"{'photo to edit' if replace else 'goal image'}, who is broader and far more muscular, with thicker arms and a bigger "
                  "chest. His shoulders, arms, chest and waist are the slimmer ones of his references.")
    if edit_photo:
        build = (f"His body stays exactly his own, as in image {ep_n}: the same slim shoulders, slim arms, flat chest and narrow waist, "
                 "the same proportions and height. Never the broader, more muscular build of the man in the GOAL IMAGE.")
        template = template.replace("Generate a new photograph of THIS EXACT MAN — not a lookalike.",
            f"Edit image {ep_n}, the PHOTO TO EDIT, which shows THIS EXACT MAN: keep him, his own face and his own slim body, and change "
            "everything else so that the photograph recreates the GOAL IMAGE: move him into the goal's scene, in the goal's exact pose, "
            "wearing the goal's clothes, holding what the goal's man holds, at the goal's framing, camera distance and light.")
    elif replace and body_only:
        template = template.replace("Generate a new photograph of THIS EXACT MAN — not a lookalike.",
            f"Edit image {edit_n}, the PHOTO TO EDIT: change ONLY his body below the neck (shoulders, arms, chest, waist) to his own build from "
            "the BODY references. Everything else in the PHOTO TO EDIT stays exactly as it is: his whole head, his exact posture, both hands, "
            "the clothes (refitted to his build), every object, the background, the framing and the light.")
    elif replace and flags.get("head_swap"):
        # --head-swap (2026-10-07 research: face-only wording keeps the target's hair; a head swap replaces it)
        template = template.replace("Generate a new photograph of THIS EXACT MAN — not a lookalike.",
            f"Edit image {edit_n}, the PHOTO TO EDIT: remove the whole head of the man in it — face, hair, beard, moustache and ears — and draw "
            f"the head of THIS EXACT MAN in its place from the FACE references (images 1-{len(faces)}), not a lookalike. From the PHOTO TO EDIT take "
            "only the head's turn and tilt, the direction of his eyes and the light that falls on his neck. His skin tone and build come only from "
            "the references. Keep everything else in the PHOTO TO EDIT exactly as it is: his exact posture (torso, both arms, both hands, both legs "
            "and feet), where he stands, his size in the frame, the camera and framing, the clothes, every object, the background and the light. "
            "Only who he is changes.")
    elif replace:
        template = template.replace("Generate a new photograph of THIS EXACT MAN — not a lookalike.",
            f"Edit image {edit_n}, the PHOTO TO EDIT: replace the man in it — his whole body and head, not only his face — with THIS EXACT "
            "MAN of the references, not a lookalike. His face, hair, beard, moustache, skin tone and build come only from the references. "
            "Keep everything else in the PHOTO TO EDIT exactly as it is: his exact posture (torso, both arms, both hands, both legs and feet), "
            "where he stands, his size in the frame, the camera and framing, the clothes, every object, the background and the light. Only "
            "who he is changes.")
    if inv:
        if res.get("pose") and flags.get("pose_points"):
            notices.append(("drop", "--pose-points: the POSE POINTS text is replaced by the inventory's CHANGE / KEEP lists and never reaches the prompt"))
        if res.get("layout") and not replace:
            notices.append(("info", "the goal's LAYOUT text is replaced by the inventory's CHANGE / KEEP lists"))
        notices.append(("info", "the --prompt (route) text is replaced by the inventory's CHANGE / KEEP lists; it only decided the face references"))

        def his_of(c: dict) -> str:
            # a character recipe: what HIS build, face, hair and beard are comes from the character, never from a goal's inventory (pin 8's inventory
            # asked for "slim upper arms only a little thicker than his forearms ... NO visible abs"; pin 6's for "fuller cheeks ... not leaner", while
            # the user wants the leaner look, 2026-10-08)
            item = str(c.get("item", "")).strip().lower()
            if char and item == "build" and phys:
                return (f"his own build exactly as in the BODY {'references' if body_word == 'images' else 'reference'} ({body_word} {body_ref}): "
                        + phys["build"].replace("{BODY}", body_ref)).rstrip(". ")
            if char and item == "build":
                return (f"his own build exactly as in the BODY reference (image {body_n or 5}): "
                        + character_build_text(char).replace("Match image {BODY} precisely. ", "").replace("{BODY}", str(body_n or 5))).rstrip(". ")
            if char and item in ("face", "hair", "beard"):
                text = str((char.get("description") or {}).get(item) or "").strip()
                if text:
                    return f"his own {item} exactly as in the FACE references (images 1-{len(faces)}): {text}".rstrip(". ")
            return c["his"]

        change = [f"- {c['item']}: the PHOTO TO EDIT shows {c['goal']}; make it {his_of(c)}"
                  + (f" (image {ref_n[c['ref']]})" if c.get("ref") in ref_n else "") + "." for c in inv.get("change", [])]
        keep = [f"- {k}." for k in inv.get("keep", [])]
        scene_text = ("CHANGE LIST (every item here changes from what the PHOTO TO EDIT shows to his own):\n" + "\n".join(change)
                      + "\n\nKEEP LIST (exactly as in the PHOTO TO EDIT):\n" + "\n".join(keep))
        if replace and not body_only:
            template = template.replace("Only who he is changes.", "Only who he is and the items in the CHANGE LIST change; nothing else.")
    if len(files) > 10:
        raise SystemExit(f"{len(files)} reference files: the Gemini app takes at most 10 per prompt")
    prompt = (template.replace("{ROLES}", "\n".join(lines)).replace("{FACE}", face_text)
              .replace("{BUILD}", build).replace("{SCENE}", scene_text))
    bible = (res.get("identity_bible") or "").strip()
    if flags.get("identity_bible") and bible:
        # --identity-bible (2026-10-07 research: a frozen trait list, stated first and repeated last): prompts/identity_bible.txt, frozen in the recipe
        prompt = prompt.replace("\n\nFACE: ", "\n\nIDENTITY:\n" + bible + "\n\nFACE: ", 1)
        prompt += "\n\nBefore you draw, check his face, hair, beard and skin once more against the IDENTITY:\n" + bible
    elif flags.get("identity_bible"):
        notices.append(("drop", "--identity-bible: no identity bible text was given, so nothing was added"))
    own_score = res.get("own_score")
    log = {"route": "G", "goal": str(goal), "goal_sent": own, "layout": res.get("layout"), "character": (char or {}).get("ref"),
           "goal_own_score": None if own_score is None else round(own_score, 3),
           "roles": {"face": [it["name"] for it in faces], "body": [it["name"] for it in body], "arms": [it["name"] for it in arms]}, "props": props,
           "layout_sketch": str(sketch.get("path") or sketch["name"]) if sketch else None, "scene_text": scene_text,
           "goal_role": "photo to edit" if replace else ("goal image" if goal_role else ("original photo" if own else None)),
           "pose_points": bool(res.get("pose") and flags.get("pose_points")), "body_only": body_only, "edit_photo": edit_photo,
           "inventory": res.get("inventory_path")}
    return prompt, files, log, notices


def character_face_text(char: dict) -> str:
    d = char.get("description") or {}
    return " ".join(str(d.get(k) or "").strip() for k in ("face", "hair", "beard", "skin") if d.get(k)).strip()


def character_build_text(char: dict) -> str:
    return "Match image {BODY} precisely. " + str((char.get("description") or {}).get("build") or "").strip()


# ------------------------------------------------------------------------------------------------------------------------------ the method must fit the goal


def pool_score(path: Path, config: dict | None = None) -> dict:
    """His photo pool's similarity to the face in a picture, excluding copies of that picture itself (as replicate decides own vs foreign)."""
    import facecard
    import identity
    import replicate as RP
    from scorer import ArcFaceScorer
    config = config or facecard.load_config()
    sc = ArcFaceScorer()
    pool = identity.build_pool(config, sc, verbose=False)
    src = RP.load_source(Path(path))
    res = identity.score_image(src, pool, sc)
    if not res.get("detected"):
        return {"detected": False, "score": None, "own_min": RP.thresholds(config)["own_min"]}
    dups = identity.duplicates_of(res["emb"], pool)
    res = identity.score_image(src, pool, sc, exclude_names=dups)
    return {"detected": True, "score": round(float(res["score"]), 3), "own_min": RP.thresholds(config)["own_min"], "excluded": sorted(dups)}


def own_photo_of(rec_or_goal, config: dict | None = None) -> dict:
    """Is the goal HIS OWN photo? (2026-10-08: the own-photo pictures went downhill because his photo went through Route G.) Yes when the recipe
    marks it (inputs.own), when results_names.json files the goal under own-photos, or when his photo pool scores its face >= own_min (0.40),
    the rule replicate has always used. {'own': bool, 'by': why}."""
    if isinstance(rec_or_goal, dict):
        rec = rec_or_goal
        key = rec["goal"]["key"]
        if rec["inputs"].get("own"):
            return {"own": True, "by": "the recipe marks the goal as his own photo (inputs.own)"}
        path = P.blob_path(rec["goal"]["sha256"]) if rec["goal"].get("sha256") else None
    else:
        path = Path(rec_or_goal)
        key = goal_key_of(path)
    e = (P.read_json(ROOT / "results_names.json", {}) or {}).get(key)
    if isinstance(e, dict) and e.get("collection") == "own-photos":
        return {"own": True, "by": "results_names.json files this goal under own-photos"}
    if isinstance(e, dict) and e.get("source") == "foreign":
        # the opposite mark (2026-10-10, pin 14): a Pinterest pin of another man whose turned-away face his pool scored 0.461, inside the 0.20-0.50
        # gray zone where a turned face scores either way; replicate takes --source foreign for the same case. The threshold itself is unchanged.
        return {"own": False, "by": f"results_names.json marks this goal as another man's photo: {e.get('source_why') or 'source foreign'}"}
    if path is None or not Path(path).is_file():
        return {"own": False, "by": "the goal picture is not available to measure"}
    ps = pool_score(path, config)
    if not ps["detected"]:
        return {"own": False, "by": "no face found in the goal (a hidden or bowed face)", "pool": ps}
    own = ps["score"] >= ps["own_min"]
    return {"own": own, "by": f"his photo pool scores the goal's face {ps['score']} ({'>=' if own else '<'} own_min {ps['own_min']})", "pool": ps}


def character_check(rec: dict) -> dict:
    """A character recipe sends only the character's photos, and the character file is the one it was frozen with."""
    c = rec["inputs"].get("character")
    if not c:
        return {"ref": None}
    import characters
    try:
        ch, _ = characters.load(c["ref"])
    except SystemExit as e:
        return {"ref": c["ref"], "problems": [str(e)]}
    problems = characters.check(ch)
    if ch["sha256"] != c["sha256"]:
        problems.append(f"the recipe was frozen with {c['ref']} {c['sha256'][:12]}; that file is now {ch['sha256'][:12]}")
    names = {r["name"] for r in ch["references"]}
    names |= set((rec["inputs"].get("physique") or {}).get("files") or [])   # --physique: its approved photo is the body, by the user's yardstick
    for r in rec["inputs"]["references"]:
        if r["role"] in ("face", "body", "arms") and Path(str(r.get("from") or "")).name not in names and r["name"] not in names:
            problems.append(f"image {r['n']} ({r['role']}, {r['name']}) is not one of character {c['ref']}'s photos")
    return {"ref": c["ref"], "sha256": c["sha256"], "problems": problems}


# ------------------------------------------------------------------------------------------------------------------------------ request + lock


def request_of(lock: dict) -> dict:
    """Exactly what goes over the wire: the model, the prompt, and each file's bytes (sha256) and upload file name, in send order."""
    return {"schema": REQUEST_SCHEMA, "model": lock["model"], "prompt": lock["prompt"],
            "files": [{"sha256": f["sha256"], "upload_name": f["upload_name"]} for f in lock["files"]], "options": lock.get("options") or {"temporary": True}}


def request_sha256(lock: dict) -> str:
    return P.sha256_bytes(P.canonical_json(request_of(lock)))


def live_profile_and_template(subject: str = "me") -> tuple[dict, str, dict]:
    import facecard
    config = facecard.apply_subject(facecard.load_config(), subject)
    profile = config.get("subject_profiles", {}).get(subject or "me", {})
    return profile, facecard.ROLE_TEMPLATE_PATH.read_text(encoding="utf-8"), config


def compiled_with(profile: dict, template: str) -> dict:
    vers = P.package_versions()
    return {"code": P.code_label(), "compiler": COMPILER, "template_sha256": P.sha256_text(template.strip()),
            "face_text_sha256": P.sha256_text(str(profile.get("face_text", ""))), "build_text_sha256": P.sha256_text(str(profile.get("build_text", ""))),
            "pillow": vers.get("Pillow"), "opencv": vers.get("opencv-python")}


def model_label(model_id: str, config: dict | None = None) -> str:
    if config is None:
        import facecard
        config = facecard.load_config()
    return str((config.get("models") or {}).get(model_id) or model_id)


ROLE_GROUPS = [("face", "faces"), ("body", "body"), ("arms", "arms"), ("inv_ref", "inv_refs"), ("prop", "props"), ("expression", "expression_refs")]
ROLE_SINGLE = [("layout_sketch", "sketch"), ("edit_photo", "edit_photo"), ("goal_image", "goal_image"), ("photo_to_edit", "photo_to_edit"),
               ("original", "original"), ("build_sheet", "build_sheet")]


def res_from_recipe(rec: dict) -> dict:
    """The compiler's input rebuilt from a recipe's frozen inputs (files are not needed: the compiler only counts and labels)."""
    inp = rec["inputs"]
    refs = inp["references"]
    items: dict = {k: [] for _, k in ROLE_GROUPS}
    for r in refs:
        it = {"role": r["role"], "name": r["name"], "sha256": r["sha256"], "label": r.get("label"), "key": r.get("key"), "arg": r.get("arg"),
              "colour_key": r.get("colour_key"), "stick": r.get("stick")}
        group = dict(ROLE_GROUPS).get(r["role"])
        if group:
            items[group].append(it)
        else:
            items[dict(ROLE_SINGLE)[r["role"]]] = it
    # face references exist for scoring even when not sent (body-only edits): kept under scoring_faces
    if not items["faces"] and inp.get("scoring_faces"):
        items["faces"] = [{"role": "face", "name": f["name"], "sha256": f["sha256"]} for f in inp["scoring_faces"]]
    inv = (inp.get("inventory") or {}).get("data")
    return {"goal": rec["goal"]["path"], "scene_text_base": (inp.get("scene_text") or {}).get("text", ""), "layout": inp.get("layout"),
            "pose": inp.get("pose"), "inventory": inv, "inventory_path": (inp.get("inventory") or {}).get("from"), "flags": inp["flags"],
            "own": inp.get("own", False), "own_score": inp.get("own_score"), "items": items,
            "identity_bible": (inp.get("identity_bible") or {}).get("text"), "character": inp.get("character"), "physique": inp.get("physique")}


def recompile(rec: dict) -> tuple[str, list[dict], list[tuple[str, str]], dict]:
    """Compile a recipe's inputs with TODAY's template, face/build text and compiler (the drift check)."""
    profile, template, _ = live_profile_and_template(rec["method"].get("subject") or "me")
    prompt, ordered, _log, notices = compile_route_g(res_from_recipe(rec), profile, template)
    return prompt, ordered, notices, compiled_with(profile, template)


def drift(rec: dict) -> dict:
    """{'same': bool, 'prompt_diff': unified diff text, 'files_diff': [...], 'compiled_with_now': {...}} against the recipe's lock."""
    if rec["method"].get("route") == "replicate":
        import replicate_recipe
        return replicate_recipe.drift(rec)
    prompt, ordered, notices, cw = recompile(rec)
    lock = rec["lock"]
    same_prompt = prompt == lock["prompt"]
    now_files = [(it["role"], it["name"], it.get("sha256")) for it in ordered]
    lock_files = [(f["role"], f["upload_name"], f["sha256"]) for f in lock["files"]]
    out = {"same": same_prompt and now_files == lock_files, "same_prompt": same_prompt, "same_files": now_files == lock_files,
           "compiled_with_lock": lock.get("compiled_with"), "compiled_with_now": cw, "notices": notices}
    if not same_prompt:
        out["prompt_diff"] = "".join(difflib.unified_diff(lock["prompt"].splitlines(True), prompt.splitlines(True), "lock (recipe)", "today's compiler", n=1))
    if now_files != lock_files:
        out["files_diff"] = {"lock": lock_files, "now": now_files}
    return out


def make_lock(prompt: str, ordered: list[dict], model: str, cw: dict) -> dict:
    files = []
    for n, it in enumerate(ordered, 1):
        sha = it.get("sha256")
        f = {"n": n, "role": it["role"], "sha256": sha, "upload_name": it["name"]}
        if it.get("path") and Path(it["path"]).is_file():
            from PIL import Image
            p = Path(it["path"])
            f["bytes"] = p.stat().st_size
            with Image.open(p) as im:
                f["px"] = list(im.size)
        files.append(f)
    lock = {"compiled_with": cw, "prompt": prompt, "prompt_sha256": P.sha256_text(prompt), "files": files, "model": model,
            "options": {"temporary": True}}
    lock["request_sha256"] = request_sha256(lock)
    return lock


def check_integrity(rec: dict) -> list[str]:
    """Problems that must stop a run before any credit is spent: a hand-edited lock, or a missing / changed blob."""
    problems = []
    lock = rec["lock"]
    if request_sha256(lock) != lock.get("request_sha256"):
        problems.append("the lock's request_sha256 does not match its own prompt / files / model: the recipe file was edited by hand")
    if P.sha256_text(lock["prompt"]) != lock.get("prompt_sha256"):
        problems.append("the lock's prompt_sha256 does not match its prompt")
    for f in lock["files"]:
        p = P.blob_path(f["sha256"])
        if p is None:
            problems.append(f"image {f['n']} ({f['role']}, {f['upload_name']}): blob {f['sha256'][:12]} missing from {P.blobs_dir()}")
        elif P.sha256_file(p) != f["sha256"]:
            problems.append(f"image {f['n']} ({f['role']}, {f['upload_name']}): blob {f['sha256'][:12]} is corrupted")
    return problems


# ------------------------------------------------------------------------------------------------------------------------------ files


def goal_key_of(goal_path: str | Path) -> str:
    return re.sub(r"_clean$", "", Path(str(goal_path).replace("\\", "/")).stem)


def recipe_dir(key: str) -> Path:
    """recipes/<collection>/<NN>-<title>/ from results_names.json (the same names as the results folder), else recipes/misc/<key>/."""
    names = P.read_json(ROOT / "results_names.json", {})
    e = names.get(key) if isinstance(names.get(key), dict) else None
    slug = lambda s: re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    if e and e.get("number") is not None:
        return RECIPES / slug(e.get("collection") or "misc") / f"{int(e['number']):02d}-{slug(e.get('title') or key)}"
    return RECIPES / "misc" / slug(key)


def versions(d: Path) -> list[Path]:
    return sorted((p for p in Path(d).glob("v*.json") if re.fullmatch(r"v\d+\.json", p.name)), key=lambda p: int(p.stem[1:]))


def _slug(s) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def recipe_files(key: str) -> list[tuple[int, Path, dict]]:
    """Every version file of THIS recipe id, in its results-name folder and in recipes/misc/<key>/, by version. A fix of another goal shares
    that goal's results name (results_names.json, for the export) but keeps its own recipes (2026-10-11: pin15janeu_send was written as v4 into
    pin 15's folder, and loading pin 15 then returned it)."""
    out = []
    for d in dict.fromkeys([recipe_dir(key), RECIPES / "misc" / _slug(key)]):
        for v in versions(d):
            try:
                r = json.loads(v.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if r.get("id") == key:
                out.append((int(r.get("version") or v.stem[1:]), v, r))
    return sorted(out, key=lambda t: t[0])


def home_dir(key: str) -> Path:
    """Where a NEW version of this recipe goes: beside its earlier versions; a folder that holds only other recipes' versions is never used."""
    mine = recipe_files(key)
    if mine:
        return mine[-1][1].parent
    d = recipe_dir(key)
    return RECIPES / "misc" / _slug(key) if versions(d) else d


def save_new(rec: dict) -> Path:
    """Write a NEW version file; an existing version is never overwritten (open mode 'x')."""
    d = home_dir(rec["id"])
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"v{rec['version']}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    return path


def next_version(key: str) -> int:
    mine = recipe_files(key)
    return mine[-1][0] + 1 if mine else 1


def load(ref: str | Path) -> tuple[dict, Path]:
    """A recipe from: a v<N>.json file; a recipe folder (its latest version); '<goal key>[@vN]'; or a run folder (the recipe copy it ran).
    A goal key finds only files whose recipe id is that key."""
    s = str(ref)
    p = Path(s)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8")), p
    if p.is_dir():
        if (p / "01_method" / "recipe.json").is_file():
            q = p / "01_method" / "recipe.json"
            return json.loads(q.read_text(encoding="utf-8")), q
        vs = versions(p)
        if vs:
            return json.loads(vs[-1].read_text(encoding="utf-8")), vs[-1]
    m = re.fullmatch(r"(.+?)(?:@v(\d+))?", s)
    key, ver = m.group(1), m.group(2)
    mine = recipe_files(key)
    if not mine:
        raise SystemExit(f"no recipe for {key!r} (looked in {recipe_dir(key)} and {RECIPES / 'misc' / _slug(key)})")
    if ver:
        hit = [t for t in mine if t[0] == int(ver)]
        if not hit:
            raise SystemExit(f"{key} has no version v{ver} (versions: {', '.join('v' + str(t[0]) for t in mine)})")
        return hit[-1][2], hit[-1][1]
    return mine[-1][2], mine[-1][1]


# ------------------------------------------------------------------------------------------------------------------------------ freezing


def freeze_items(res: dict) -> None:
    """Put every resolved file into the blob store and note its sha256 (in place)."""
    for _, group in ROLE_GROUPS:
        for it in res["items"].get(group) or []:
            it["sha256"] = P.put_file(Path(it["path"]))
    for _, key in ROLE_SINGLE:
        it = res["items"].get(key)
        if it:
            it["sha256"] = P.put_file(Path(it["path"]))


def references_of(ordered: list[dict], res: dict) -> list[dict]:
    out = []
    for n, it in enumerate(ordered, 1):
        r = {"n": n, "role": it["role"], "name": it["name"], "sha256": it["sha256"], "from": str(it.get("from") or it.get("path") or ""),
             "prep": it.get("prep") or "", "why": it.get("why") or ""}
        for k in ("label", "key", "arg", "colour_key", "stick"):
            if it.get(k) is not None:
                r[k] = it[k]
        out.append(r)
    return out


def build_recipe(res: dict, method: dict, because: str, origin: dict, prompt: str, ordered: list[dict], cw: dict, version: int,
                 parent: str | None, extra_goal: dict | None = None) -> dict:
    goal_path = str(res["goal"])
    gp = Path(goal_path)
    gp_abs = gp if gp.is_absolute() else ROOT / gp
    key = goal_key_of(goal_path)
    pose_file = ROOT / ".cache" / "poses" / f"{Path(goal_path).stem}.json"
    lay_file = ROOT / ".cache" / "layouts" / f"{Path(goal_path).stem}.json"
    goal = {"key": key, "path": goal_path.replace("\\", "/"), "sha256": P.put_file(gp_abs) if gp_abs.is_file() else None,
            "pose": {"path": str(pose_file.relative_to(ROOT)).replace("\\", "/"), "sha256": P.put_file(pose_file)} if pose_file.is_file() else None,
            "layout": {"path": str(lay_file.relative_to(ROOT)).replace("\\", "/"), "sha256": P.put_file(lay_file)} if lay_file.is_file() else None,
            "source": None}
    goal.update(extra_goal or {})
    inv = res.get("inventory")
    # body-only edits send no face photos, but the faces still score identity: keep them in the recipe
    scoring = ([{"name": it["name"], "sha256": it["sha256"]} for it in res["items"].get("faces") or []]
               if res["flags"].get("body_only") else [])
    inputs = {"flags": res["flags"], "own": bool(res.get("own")), "own_score": res.get("own_score"),
              "scene_text": {"text": res["scene_text_base"], "from": res.get("scene_from"), "sha256": P.sha256_text(res["scene_text_base"]),
                             "used_for": "face choice only: the inventory's CHANGE / KEEP lists replace it in the prompt" if inv else "the SCENE section"},
              "inventory": {"from": res.get("inventory_path"), "sha256": P.sha256_bytes(P.canonical_json(inv)), "data": inv} if inv else None,
              "layout": res.get("layout"), "pose": res.get("pose"), "face_choice": res.get("face_choice"),
              "references": references_of(ordered, res)}
    if scoring:
        inputs["scoring_faces"] = scoring
    if res["flags"].get("identity_bible") and res.get("identity_bible"):
        inputs["identity_bible"] = {"text": res["identity_bible"], "sha256": P.sha256_text(res["identity_bible"]), "from": "prompts/identity_bible.txt"}
    if res.get("character"):
        inputs["character"] = res["character"]
    if res.get("physique"):       # --physique: the standard's name, files, label and build text, frozen with the recipe
        inputs["physique"] = res["physique"]
    if res.get("teeth"):          # --teeth: why, and which of his real smile photos went in (the files themselves are in references)
        inputs["teeth"] = res["teeth"]
    lock = make_lock(prompt, ordered, method["model"]["id"], cw)
    return {"schema": SCHEMA, "id": key, "version": version, "created": datetime.now().isoformat(timespec="seconds"), "because": because,
            "parent": parent, "origin": origin, "goal": goal, "method": method, "inputs": inputs, "lock": lock}


def model_record(model: str, config: dict) -> dict:
    """The model id and label, plus the name the account last listed it under (.cache/models_seen.json, written by every run's stage 04), so a
    later run can show MODEL CHANGED when Google swaps the model behind the id."""
    m = {"id": model, "label": model_label(model, config)}
    seen = (P.read_json(ROOT / ".cache" / "models_seen.json", {}) or {}).get(model)
    if seen:
        m.update({"display": seen.get("display_name"), "display_seen": seen.get("seen")})
    return m


def method_of(args, config: dict, samples: int | None = None) -> dict:
    model = getattr(args, "model", None) or config.get("model")
    keep = ["goal", "prompt", "inventory", "goal_as_image", "replace_subject", "body_only", "edit_photo", "layout_image", "pose_points",
            "pose_image", "prop", "face_refs", "face_count", "subject", "identity_bible", "build_sheet", "head_swap"]
    args_ = {k: getattr(args, k, None) for k in keep}
    if getattr(args, "character", None):          # absent unless set, so older recipes keep their exact method record
        args_["character"] = args.character
    if getattr(args, "restore_background", None):  # likewise: the pin's own background is copied back after the run (tools/background_restore.py, 2026-10-09)
        args_["restore_background"] = True
    if getattr(args, "physique", None):            # likewise: the body by the user's yardstick (2026-10-10)
        args_["physique"] = args.physique
    if getattr(args, "teeth", None):               # likewise: his own teeth from his real smile photos, and why (the user, 2026-10-18)
        args_["teeth"] = args.teeth
    return {"route": "G", "subject": getattr(args, "subject", None) or "me", "args": args_,
            "model": model_record(model, config), "samples": int(samples or getattr(args, "count", 1) or 1),
            "stop": {"after_pose_fails": int(getattr(args, "stop_after_fails", 0) or 0), "on_pass": bool(getattr(args, "stop_on_pass", False))}}


def from_gen_args(args, because: str, adhoc: bool = False, version: int | None = None, parent: str | None = None, strict: bool = True) -> dict:
    """Resolve gen-style arguments once (reference choice, preparation), freeze every file into the blob store, compile, lock."""
    import facecard
    config = facecard.apply_subject(facecard.load_config(), getattr(args, "subject", None) or "me")
    own = own_photo_of(Path(args.goal), config)
    # A region edit (objects mode, "region_edit": true in the inventory) sends a crop of his own finished picture and tools/region_edit.py pastes
    # back only that crop (or the part below a line), so the rest stays byte-identical: the whole-photo redraw this rule guards against cannot
    # happen (2026-10-10, the pizza beard crop scored 0.522 as his own photo; the eye band had no detectable face).
    inv = P.read_json(Path(args.inventory), {}) if getattr(args, "inventory", None) else {}
    region_edit = (inv or {}).get("mode") == "objects" and bool((inv or {}).get("region_edit"))
    if own["own"] and not getattr(args, "edit_photo", None) and not region_edit:
        raise SystemExit(f"own photo ({own['by']}): method must be replicate, not Route G (Route G sends the whole photo and redraws every pixel; "
                         "2026-10-07 the own-photo pictures went downhill exactly there). Use: facecard.py recipe new --method replicate --goal "
                         f"{args.goal} --character me@v1 --because \"...\"")
    refs_dir = facecard.get_refs_dir(config)
    cache_dir = ROOT / config.get("cache_dir", ".cache/refs")
    res = facecard.resolve_goal_inputs(config, refs_dir, cache_dir, args)
    freeze_items(res)
    profile = config.get("subject_profiles", {}).get(getattr(args, "subject", None) or "me", {})
    template = facecard.ROLE_TEMPLATE_PATH.read_text(encoding="utf-8")
    prompt, ordered, _log, notices = compile_route_g(res, profile, template)
    drops = [m for lvl, m in notices if lvl == "drop"]
    if drops and strict and not adhoc:
        raise SystemExit("A recipe never holds a flag whose text would be dropped silently:\n  " + "\n  ".join(drops))
    key = goal_key_of(res["goal"])
    v = version or (0 if adhoc else next_version(key))          # ad-hoc recipes (gen --goal) are version 0: never counted as a real version
    origin = {"kind": "adhoc" if adhoc else ("bump" if parent else "new"), "notices": [list(n) for n in notices]}
    return build_recipe(res, method_of(args, config), because, origin, prompt, ordered, compiled_with(profile, template), v, parent)


# ------------------------------------------------------------------------------------------------------------------------------ import a past run


def pin_source(goal_stem: str) -> dict | None:
    """The Pinterest board file a .cache/pin_<id>.jpg goal was copied from (the copy is a re-encode whose making was never recorded)."""
    if not goal_stem.startswith("pin_"):
        return None
    pid = goal_stem[4:].removesuffix("_clean")
    hits = sorted(Path(r"D:\PinterestBoards").glob(f"*/{pid}.*"))
    if not hits:
        return None
    return {"path": str(hits[0]), "sha256": P.sha256_file(hits[0]), "derivation": "the goal is a re-encoded copy of this board file; how it was made was not recorded"}


def run_start(run_dir: Path, run: dict) -> datetime:
    ts = str(run.get("timestamp") or run_dir.name[:15])
    return datetime.strptime(ts[:15], "%Y%m%d_%H%M%S")


def import_run(run_dir: Path, because: str = "", check_only: bool = False, samples: int | None = None, stop_after_fails: int | None = None,
               prompt_path: str | None = None, say=print) -> dict | None:
    """Adopt a past gen run as a recipe, WITHOUT guessing: every file comes from what run.json names, every file must predate the run (so today's
    bytes are the bytes that were sent), and today's compiler must reproduce run.json's prompt byte for byte. Otherwise it stops and says why."""
    import facecard
    run_dir = Path(run_dir)
    staged = P.read_json(run_dir / "01_method" / "recipe.json", None)
    if staged:
        # a staged run (runner.py) carries its own recipe; adopting it only needs proof that this is what it sent
        rq = P.read_json(run_dir / "03_request" / "request.json", {}) or {}
        ok = rq.get("request_sha256") == staged["lock"]["request_sha256"] == request_sha256(staged["lock"])
        say(f"{run_dir.name}: staged run; request {'matches its recipe' if ok else 'DOES NOT match its recipe'}")
        if check_only or not ok:
            return {"run": run_dir.name, "prompt_equal": ok, "problems": [] if ok else ["request.json does not match the run's recipe"]} if check_only else None
        rec = dict(staged)
        rec.update({"version": next_version(staged["id"]), "created": datetime.now().isoformat(timespec="seconds"), "because": because,
                    "parent": None, "origin": {"kind": "import-run", "run": run_dir.name, "from": "the staged run's own recipe",
                                               "proof": {"request_sha256_matches": True}, "was": staged.get("origin")}})
        if samples:
            rec["method"] = {**rec["method"], "samples": int(samples)}
        if stop_after_fails is not None:
            rec["method"] = {**rec["method"], "stop": {**rec["method"]["stop"], "after_pose_fails": int(stop_after_fails)}}
        return rec
    run = P.read_json(run_dir / "run.json", None)
    if not run or not run.get("route_g"):
        say(f"{run_dir.name}: not a Route G gen run (no route_g in run.json)")
        return None
    rg = run["route_g"]
    t0 = run_start(run_dir, run)
    config = facecard.apply_subject(facecard.load_config(), run.get("subject") or "me")
    cache = ROOT / config.get("cache_dir", ".cache/refs")
    problems: list[str] = []

    def find(name: str, places: list[Path]) -> Path | None:
        hits = [d / name for d in places if (d / name).is_file()]
        if len(hits) != 1:
            problems.append(f"{name}: {'not found' if not hits else 'found twice'} in {', '.join(str(d.relative_to(ROOT)) for d in places)}")
            return None
        f = hits[0]
        if datetime.fromtimestamp(f.stat().st_mtime) >= t0:
            problems.append(f"{f.relative_to(ROOT)} was written after the run started ({datetime.fromtimestamp(f.stat().st_mtime):%Y-%m-%d %H:%M:%S}): "
                            "today's bytes are not provably the bytes that were sent")
        return f

    inv_path = rg.get("inventory")
    inv = None
    if inv_path:
        ip = ROOT / inv_path if not Path(inv_path).is_absolute() else Path(inv_path)
        inv = P.read_json(ip, None)
        if inv is None:
            problems.append(f"inventory {inv_path} not readable")
        elif datetime.fromtimestamp(ip.stat().st_mtime) >= t0:
            problems.append(f"inventory {inv_path} was modified after the run started")
    replace = rg.get("goal_role") == "photo to edit"
    flags = {"replace_subject": replace, "goal_as_image": ("goal" if rg.get("goal_role") == "goal image" else ("yes" if rg.get("goal_sent") else "no")),
             "body_only": bool(rg.get("body_only")), "edit_photo": rg.get("edit_photo"), "layout_image": bool(rg.get("layout_sketch")),
             "pose_points": bool(rg.get("pose_points")), "pose_image": False}
    places = [cache, ROOT / ".cache" / "refcrops"]
    mk = lambda role, f, why, **kw: {"role": role, "path": f, "name": f.name, "from": str(f.relative_to(ROOT)).replace("\\", "/"), "why": why, **kw}
    faces = [mk("face", f, "face reference recorded by the run") for n in rg["roles"].get("face", []) if (f := find(n, places))]
    body = [mk("body", f, "subject_profiles.roles.body") for n in rg["roles"].get("body", []) if (f := find(n, [cache]))]
    arms = [mk("arms", f, "subject_profiles.roles.arms") for n in rg["roles"].get("arms", []) if (f := find(n, [cache]))]
    inv_refs = []
    for r in (inv or {}).get("refs", []):
        f = find(Path(r["path"]).stem + ".jpg", [cache])
        if f:
            inv_refs.append(mk("inv_ref", f, "inventory reference", label=r["label"], key=r["key"]))
    props = []
    for pr in rg.get("props") or []:
        f = find(Path(pr["path"]).stem + ".jpg", [cache])
        if f:
            props.append(mk("prop", f, "--prop", label=pr["label"], arg=pr["path"]))
    items = {"faces": faces, "body": body, "arms": arms, "inv_refs": inv_refs, "props": props}
    if rg.get("layout_sketch"):
        problems.append("runs with a layout sketch are not imported (the sketch file is regenerated per run)")
    goal = rg["goal"]
    goal_stem = Path(str(goal).replace("\\", "/")).stem
    if replace:
        src = (inv or {}).get("photo_to_edit") or goal
        f = find(Path(str(src).replace("\\", "/")).stem + ".jpg", [cache])
        if f:
            items["photo_to_edit"] = mk("photo_to_edit", f, "the inventory's photo_to_edit" if (inv or {}).get("photo_to_edit") else "the goal")
    if flags["goal_as_image"] == "goal":
        f = find(goal_stem + ".jpg", [cache])
        if f:
            items["goal_image"] = mk("goal_image", f, "--goal-as-image goal")
    if rg.get("goal_sent") and not replace and flags["goal_as_image"] != "goal":
        f = find(goal_stem + ".jpg", [cache])
        if f:
            items["original"] = mk("original", f, "his own photo as the original")
    if rg.get("edit_photo"):
        f = find(Path(rg["edit_photo"]).stem + ".jpg", [cache])
        if f:
            items["edit_photo"] = mk("edit_photo", f, "--edit-photo")
    # scene text: only the face choice used it when there is an inventory; read the conventional route file for the record
    route = Path(prompt_path) if prompt_path else ROOT / ".cache" / "loop_prompts" / f"{goal_stem}_route.txt"
    scene_base = route.read_text(encoding="utf-8").strip() if route.is_file() else ""
    lay = rg.get("layout")
    res = {"goal": goal, "scene_text_base": scene_base, "scene_from": str(route.relative_to(ROOT)).replace("\\", "/") if route.is_file() and ROOT in route.resolve().parents else str(route),
           "layout": lay, "pose": None, "inventory": inv, "inventory_path": inv_path, "flags": flags, "own": bool(rg.get("goal_sent")),
           "own_score": rg.get("goal_own_score"), "items": items}
    if flags["pose_points"]:
        res["pose"] = P.read_json(ROOT / ".cache" / "poses" / f"{goal_stem}.json", None)
    profile = config.get("subject_profiles", {}).get(run.get("subject") or "me", {})
    template = facecard.ROLE_TEMPLATE_PATH.read_text(encoding="utf-8")
    try:
        prompt, ordered, _log, notices = compile_route_g(res, profile, template)
    except Exception as exc:
        problems.append(f"compile failed: {type(exc).__name__}: {exc}")
        prompt, ordered, notices = "", [], []
    equal = prompt == run.get("prompt")
    report = {"run": run_dir.name, "prompt_equal": equal, "problems": problems}
    if not equal and prompt:
        report["prompt_diff"] = "".join(difflib.unified_diff(str(run.get("prompt", "")).splitlines(True), prompt.splitlines(True),
                                                             "run.json prompt", "today's compiler", n=1))
    say(f"{run_dir.name}: prompt {'EQUAL' if equal else 'DIFFERS'}; " + ("files provable" if not problems else f"{len(problems)} problem(s)"))
    for pr in problems:
        say(f"  - {pr}")
    if not equal and report.get("prompt_diff"):
        say(report["prompt_diff"][:4000])
    if check_only or problems or not equal:
        return report if check_only else None
    # face choice: re-derive the decision the run made, from the goal and the route text (the run did not record it)
    info: dict = {}
    facecard.face_choice_of(config, ROOT / str(goal).replace("\\", "/"), scene_text_of(res), info)
    res["face_choice"] = {**info, "count": len(faces), "names": [f["name"] for f in faces],
                          "note": "re-derived at import from the goal picture and the route text; the run itself did not record it"}
    for f in faces:
        f["why"] = f"face reference, bin {info.get('bin')} ({info.get('decided_by')}: {info.get('evidence')})"
    freeze_items(res)
    method = {"route": "G", "subject": run.get("subject") or "me",
              "args": {"goal": goal, "prompt": res["scene_from"], "inventory": inv_path, "goal_as_image": flags["goal_as_image"],
                       "replace_subject": replace, "body_only": flags["body_only"], "edit_photo": flags["edit_photo"], "layout_image": False,
                       "pose_points": flags["pose_points"], "pose_image": False, "prop": [p["arg"] for p in props] or None, "face_refs": None,
                       "face_count": None, "subject": run.get("subject") or "me"},
              "model": {"id": run["model"], "label": model_label(run["model"], config)},
              "samples": int(samples or len(run.get("results") or []) or 1),
              "stop": {"after_pose_fails": int(stop_after_fails or 0), "on_pass": False}}
    extra = {"source": pin_source(goal_stem)}
    origin = {"kind": "import-run", "run": run_dir.name, "proof": {"prompt_equal": True, "files_predate_run": True, "run_started": t0.isoformat()},
              "notices": [list(n) for n in notices]}
    rec = build_recipe(res, method, because, origin, run["prompt"], ordered, compiled_with(profile, template), next_version(goal_key_of(goal)), None, extra)
    return rec


# ------------------------------------------------------------------------------------------------------------------------------ show / diff of versions


def lock_diff(a: dict, b: dict) -> str:
    """What changed between two recipe versions' locks: model, files (role, name, sha) and the prompt text."""
    out = []
    la, lb = a["lock"], b["lock"]
    if la["model"] != lb["model"]:
        out.append(f"model: {la['model']} -> {lb['model']}")
    fa = [(f["role"], f["upload_name"], f["sha256"][:12]) for f in la["files"]]
    fb = [(f["role"], f["upload_name"], f["sha256"][:12]) for f in lb["files"]]
    if fa != fb:
        out.append("files:")
        for line in difflib.unified_diff([" ".join(x) + "\n" for x in fa], [" ".join(x) + "\n" for x in fb], f"v{a['version']}", f"v{b['version']}", n=0):
            out.append("  " + line.rstrip("\n"))
        same_name_new_bytes = {x[1] for x in fa} & {x[1] for x in fb} - {x[1] for x in set(fa) & set(fb)}
        if same_name_new_bytes:
            out.append("  NOTE: same file name, different bytes: " + ", ".join(sorted(same_name_new_bytes)))
    if la["prompt"] != lb["prompt"]:
        out.append("prompt:")
        out += ["  " + ln.rstrip("\n") for ln in difflib.unified_diff(la["prompt"].splitlines(True), lb["prompt"].splitlines(True),
                                                                      f"v{a['version']}", f"v{b['version']}", n=1)]
    for k in ("samples", "stop"):
        if a["method"].get(k) != b["method"].get(k):
            out.append(f"{k}: {a['method'].get(k)} -> {b['method'].get(k)}")
    return "\n".join(out) or "no difference in the request"


def runs_of(key: str) -> list[dict]:
    """Every staged or legacy run of this goal that names a recipe, from outputs/*/run.json."""
    out = []
    for rj in sorted((ROOT / "outputs").glob("*/run.json")):
        run = P.read_json(rj, None) or {}
        r = run.get("recipe") or {}
        if r.get("id") == key:
            out.append({"run": rj.parent.name, "version": r.get("version"), "adhoc": bool(r.get("adhoc")), "request": r.get("request_sha256"), "status": run.get("status")})
    return out


def show(ref: str) -> int:
    rec, path = load(ref)
    d = path.parent if path.parent.name != "01_method" else recipe_dir(rec["id"])
    ledger = (P.read_json(ROOT / "feedback_ledger.json", {}) or {}).get("rows", {})
    print(f"{rec['id']}  ({d.relative_to(ROOT) if ROOT in d.resolve().parents else d})")
    runs = runs_of(rec["id"])
    for vp in versions(d):
        v = json.loads(vp.read_text(encoding="utf-8"))
        rs = [r for r in runs if r["version"] == v["version"] and not r["adhoc"]]
        rows = [row for row in ledger.values() if row.get("run") in {r["run"] for r in rs} or row.get("run") == (v.get("origin") or {}).get("run")]
        passed = sum(1 for row in rows if str(row.get("result", "")).startswith("PASS"))
        print(f"  v{v['version']}  {v['created'][:16]}  {v['method']['model']['label']} x{v['method']['samples']}  request {v['lock']['request_sha256'][:12]}"
              f"  runs {len(rs)}  pictures {len(rows)} (passed {passed})")
        print(f"      because: {v.get('because')}")
    return 0
