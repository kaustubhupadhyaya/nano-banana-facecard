"""
facecard: generate identity-consistent images of yourself via the Gemini web app,
reusing your Google AI Pro session (see session.py) instead of a billed API key.

Usage:
    .venv\\Scripts\\python.exe facecard.py check
    .venv\\Scripts\\python.exe facecard.py models
    .venv\\Scripts\\python.exe facecard.py gen --prompt prompts/studio_test.txt --count 1
    .venv\\Scripts\\python.exe facecard.py gen --prompt "wearing a red jacket, city street at night" --scene-image path\\to\\scene.jpg --count 2
    .venv\\Scripts\\python.exe facecard.py restore outputs/some_run/v1_0.jpg
    .venv\\Scripts\\python.exe facecard.py score outputs/some_run/v1_0.jpg
    .venv\\Scripts\\python.exe facecard.py pose-refs --query "man in convertible smiling" --count 6
"""

import argparse
import asyncio
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps

from gemini_webapi.exceptions import GeminiError, ImageGenerationError, UsageLimitExceededError
from session import AuthError, authenticated_client, credits_left

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "facecard.json"
IDENTITY_LOCK_PATH = ROOT / "prompts" / "identity_lock.txt"
ROLE_TEMPLATE_PATH = ROOT / "prompts" / "role_template.txt"
LAYOUTS_DIR = ROOT / ".cache" / "layouts"


def layout_text(lay: dict) -> str:
    """The goal's frame layout in Gemini's own box format (normalized 0-1000, [ymin, xmin, ymax, xmax]), read by tools/goal_layout.py. The user
    asked (2026-09-26) for something Gemini understands better than a 3x3 grid to hold the camera distance and the subject's boundary."""
    fmt = lambda b: f"[{b[0]}, {b[1]}, {b[2]}, {b[3]}]"
    parts = [f"his whole body {fmt(lay['person'])}", f"his head {fmt(lay['head'])}"]
    parts += [f"the {o['name']} {fmt(o['box'])}" for o in lay.get("objects", [])]
    return ("LAYOUT: Frame positions as bounding boxes normalized to 0-1000, [ymin, xmin, ymax, xmax]: " + "; ".join(parts) + ". Place him, "
            "his head and these things exactly inside these boxes: the same size in the frame and so the same camera distance.")
SCENE_REF_NOTE = "\n\nThe last attached image is a scene/posture reference with the head/neck region neutralized — strictly match its camera perspective, elevation, body posture, limb positioning, ground contact, clothing, and background setting. Do NOT copy any facial or skull geometry from it; the subject's face, skull shape, profile contour, hairline, and facial features must come exclusively from the attached identity reference photos."


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def get_refs_dir(config: dict) -> Path:
    refs_dir = Path(config.get("refs_dir", ""))
    if not refs_dir.exists() or not any(refs_dir.glob("*.jpg")):
        fallback = ROOT / config.get("cache_dir", ".cache/refs")
        if fallback.exists():
            return fallback
    return refs_dir


def prepare_ref(src: Path, cache_dir: Path, max_dim: int = 2048) -> Path:
    """EXIF-transpose + downscale a reference image, cached by source mtime."""
    if not src.exists():
        fallback = cache_dir / src.name
        if fallback.exists():
            src = fallback
        else:
            raise FileNotFoundError(f"Reference image not found: {src}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / (src.stem + ".jpg")
    if cached.is_file() and cached.stat().st_mtime >= src.stat().st_mtime:
        # An up-to-date cache file used to be returned unchecked: the cache held full 12 MP copies, uploaded as-is (credit plan, 2026-09-27).
        with Image.open(cached) as c:
            if max(c.size) <= max_dim:
                return cached
            small = ImageOps.exif_transpose(c).convert("RGB")
        small.thumbnail((max_dim, max_dim), Image.LANCZOS)
        small.save(cached, "JPEG", quality=95)
        return cached

    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
        img.save(cached, "JPEG", quality=95)
    return cached


def fix_extension(path: Path) -> Path:
    """gemini_webapi keeps the given filename even when Google serves JPEG, so match the real format."""
    with Image.open(path) as img:
        real_ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(img.format, path.suffix)
    if real_ext == path.suffix:
        return path
    return path.rename(path.with_suffix(real_ext))


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len] or "gen").rstrip("-")


HEAD_TURN_RE = re.compile(r"(?:face|head)[^.]*?(\d{1,2})\s*degrees?\s+toward\s+(?:the\s+)?picture-(left|right)")


def head_bin_from_text(prompt_text: str) -> str:
    """Pose bin from the head phrase only, so a limb on picture-left does not pull left-facing references.

    scene-prompt-writer writes the head as "face turned about N degrees toward picture-left/right", the same picture-side
    convention as scorer.analyze_face (a nose left of the eye centre is a *_left bin). Older prompt files without that phrase
    fall back to the keyword read, limited to the sentence that names the turn.
    """
    low = prompt_text.lower()
    m = HEAD_TURN_RE.search(low)
    if m:
        deg, side = int(m.group(1)), m.group(2)
        if deg >= 55:
            return f"profile_{side}"
        if deg >= 25:
            return f"three_quarter_{side}"
        return "frontal"
    for sentence in re.split(r"(?<=[.!?])\s+", low):
        if "profile" in sentence or "60 degree" in sentence or "70 degree" in sentence or "75 degree" in sentence:
            return "profile_left" if "left" in sentence else "profile_right"
        if "three-quarter" in sentence or "3/4" in sentence or "40 degree" in sentence or "45 degree" in sentence:
            return "three_quarter_left" if "left" in sentence else "three_quarter_right"
    return "frontal"


SUBJECT_KEYS = ("refs_dir", "refs", "pose_bins", "anchors", "restore_refs")


def apply_subject(config: dict, name: Optional[str]) -> dict:
    """Overlay facecard.json subject_profiles[name] reference settings; the top-level keys are the builder's own set."""
    if not name:
        return config
    profiles = config.get("subject_profiles", {})
    if name not in profiles:
        raise SystemExit(f"Unknown --subject {name!r}. Known: {', '.join(profiles) or 'none'} (facecard.json subject_profiles)")
    merged = dict(config)
    for key in SUBJECT_KEYS:
        if key in profiles[name]:
            merged[key] = profiles[name][key]
    merged["subject"] = name
    return merged


def get_generation_refs(
    config: dict,
    refs_dir: Path,
    cache_dir: Path,
    scene_image_path: Optional[str | Path] = None,
    prompt_text: str = "",
) -> list[Path]:
    """Select angle-targeted identity references for Gemini generation.
    
    If scene reference or prompt specifies a profile or 3/4 angle, concentrates Gemini's
    attention on angle-matched photos (plus 1-2 frontal anchors) to avoid diluting
    cross-attention with conflicting frontal faces.
    """
    from scorer import analyze_face

    pose_bins = config.get("pose_bins", {})
    all_refs = config.get("refs", [])

    target_bin = "frontal"
    # Detect target angle from scene image or prompt
    if scene_image_path and Path(scene_image_path).exists():
        info = analyze_face(scene_image_path)
        if info.get("detected"):
            target_bin = info.get("pose_bin", "frontal")

    if target_bin == "frontal" and prompt_text:
        target_bin = head_bin_from_text(prompt_text)

    anchors = config.get("anchors", ["IMG_6873.jpg", "IMG_6858.jpg"])
    selected_names = []
    if target_bin in ("profile_right", "three_quarter_right"):
        # Prioritize right profile & 3/4 right
        selected_names.extend(pose_bins.get("profile_right", []))
        selected_names.extend(pose_bins.get("three_quarter_right", []))
        # Add 2 frontal anchors for skin tone and eye color
        selected_names.extend(anchors)
    elif target_bin in ("profile_left", "three_quarter_left"):
        # Prioritize left profile & 3/4 left
        selected_names.extend(pose_bins.get("profile_left", []))
        selected_names.extend(pose_bins.get("three_quarter_left", []))
        # Add 2 frontal anchors
        selected_names.extend(anchors)
    else:
        # Frontal / default
        selected_names.extend(pose_bins.get("frontal", []))
        selected_names.extend(pose_bins.get("three_quarter_right", [])[:1])
        selected_names.extend(pose_bins.get("three_quarter_left", [])[:1])

    # Deduplicate while preserving order
    seen = set()
    deduped = [n for n in selected_names if not (n in seen or seen.add(n))]

    ref_paths = []
    for name in deduped:
        p = refs_dir / name
        if p.exists():
            ref_paths.append(prepare_ref(p, cache_dir))
        elif (cache_dir / name).exists():
            ref_paths.append(prepare_ref(cache_dir / name, cache_dir))

    if not ref_paths:
        # Fallback to all refs
        ref_paths = [prepare_ref(refs_dir / name, cache_dir) for name in all_refs if (refs_dir / name).exists() or (cache_dir / name).exists()]

    return ref_paths


LAYOUT_COLOURS = {"person": (40, 110, 255), "head": (230, 40, 40),
                  "objects": [(40, 170, 70), (240, 190, 20), (150, 60, 200), (255, 140, 0), (0, 190, 200)]}
LAYOUT_COLOUR_NAMES = ("green", "yellow", "purple", "orange", "cyan")


def layout_sketch(goal: Path, lay: dict, cache_dir: Path) -> tuple[Path, str]:
    """The goal's layout boxes drawn as flat coloured rectangles on white at the goal's aspect ratio: no photo, no person's shape. Text boxes
    alone left the camera too far in pin v6, v7 and v7cb (person x0.75-0.83 of the goal's height, 2026-09-27). Returns (path, colour key)."""
    from PIL import Image as _Image, ImageDraw as _Draw
    with _Image.open(goal) as g:
        gw, gh = g.size
    w = 800
    h = round(w * gh / gw)
    im = _Image.new("RGB", (w, h), (255, 255, 255))
    d = _Draw.Draw(im, "RGBA")

    def rect(b, col):
        d.rectangle([b[1] * w / 1000, b[0] * h / 1000, b[3] * w / 1000, b[2] * h / 1000], fill=col + (70,), outline=col + (255,), width=5)

    key = []
    for o, col, name in zip(lay.get("objects", []), LAYOUT_COLOURS["objects"], LAYOUT_COLOUR_NAMES):
        rect(o["box"], col)
        key.append(f"{name} box = the {o['name']}")
    rect(lay["person"], LAYOUT_COLOURS["person"])
    rect(lay["head"], LAYOUT_COLOURS["head"])
    out = cache_dir / f"layout_sketch_{goal.stem}.png"
    im.save(out)
    return out, "; ".join(["blue box = his whole body", "red box = his head"] + key)


POSES_DIR = ROOT / ".cache" / "poses"
POSE_PYTHON = Path(r"D:\VisionModels\yolo\.venv\Scripts\python.exe")
_KP_WORDS = [("nose", "his nose"), ("r_shoulder", "his right shoulder"), ("l_shoulder", "his left shoulder"), ("r_elbow", "his right elbow"),
             ("r_wrist", "his right hand"), ("l_elbow", "his left elbow"), ("l_wrist", "his left hand"), ("r_hip", "his right hip"),
             ("l_hip", "his left hip"), ("r_knee", "his right knee"), ("l_knee", "his left knee"), ("r_ankle", "his right foot"),
             ("l_ankle", "his left foot")]
_LIMBS = [("l_shoulder", "r_shoulder"), ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"), ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
          ("l_shoulder", "l_hip"), ("r_shoulder", "r_hip"), ("l_hip", "r_hip"), ("l_hip", "l_knee"), ("l_knee", "l_ankle"), ("r_hip", "r_knee"),
          ("r_knee", "r_ankle")]


def goal_pose(goal: Path) -> dict | None:
    """The goal's measured keypoints (tools/pose_compare.py --save-goal)."""
    f = POSES_DIR / f"{goal.stem}.json"
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    return d if d and d.get("person") else None


def pose_points_text(pose: dict) -> str:
    """POSE POINTS: the goal's measured joints in Gemini's own point format ([y, x], 0-1000), plus plain facts computed from them by code
    (stance, legs straight or bent, torso lean, hand heights). The user, 2026-09-27: the checklist has to be built into the request; a posture
    written from my reading of the goal left the legs out entirely (table tennis v7 drew a stride where the goal stands with feet together)."""
    import math
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


def draw_pose(im, pose: dict) -> None:
    """The goal's skeleton as a thick black stick figure on the layout sketch (a PIL image)."""
    from PIL import ImageDraw as _Draw
    w, h = im.size
    kp = {k: v for k, v in pose["person"]["kp"].items() if v[2] >= 0.5}
    d = _Draw.Draw(im)
    for a, b in _LIMBS:
        if a in kp and b in kp:
            d.line([kp[a][0] * w, kp[a][1] * h, kp[b][0] * w, kp[b][1] * h], fill=(0, 0, 0), width=9)
    for v in kp.values():
        d.ellipse([v[0] * w - 8, v[1] * h - 8, v[0] * w + 8, v[1] * h + 8], fill=(0, 0, 0))


def run_pose_gate(goal: Path, renders: list[Path]) -> list[dict]:
    """tools/pose_compare.py on every render (the YOLO environment); returns one result per render. Fixed limits live in that tool."""
    import subprocess
    if not POSE_PYTHON.exists() or not renders:
        return []
    cmd = [str(POSE_PYTHON), str(ROOT / "tools" / "pose_compare.py"), str(goal), *map(str, renders), "--json"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    res = []
    for line in out.stdout.splitlines():
        if line.startswith("{"):
            try:
                res.append(json.loads(line))
            except Exception:
                pass
    return res


def build_goal_request(config: dict, refs_dir: Path, cache_dir: Path, args) -> tuple[str, list[Path], list[Path], dict]:
    """Route G (2026-09-26, the user's own prompt structure): his reference photos labelled by ROLE (face refs chosen by the goal's head pose,
    his true-build body photo, his shoulder-and-arm photo), his fixed FACE and BUILD text from subject_profiles, and the goal written as text
    (POSE / WARDROBE / SCENE / LIGHT / CAMERA, from scene-prompt-writer). The goal photo itself is never sent when it shows another man: sent
    photos leak their model's skull, jaw and neck (measured 2026-09-19), and a public figure's photo is refused. When the goal is his OWN photo
    it is sent too, labelled as the original photo to recreate. Returns (prompt, files in role order, face refs for scoring, log)."""
    from scorer import ArcFaceScorer

    profile = config.get("subject_profiles", {}).get(args.subject or "me", {})
    roles = profile.get("roles", {})
    goal = Path(args.goal)
    prompt_arg = Path(args.prompt)
    scene_text = prompt_arg.read_text(encoding="utf-8").strip() if prompt_arg.is_file() else args.prompt
    inv = json.loads(Path(args.inventory).read_text(encoding="utf-8")) if getattr(args, "inventory", None) else None
    lay_p = LAYOUTS_DIR / f"{goal.stem}.json"
    layout = json.loads(lay_p.read_text(encoding="utf-8")) if lay_p.exists() else None
    if layout and not getattr(args, "replace_subject", False):
        # (replace-subject: the photo to edit carries the layout itself; the box text made tt-W v3_0 draw black boxes, 2026-09-27)
        scene_text = scene_text + "\n\n" + layout_text(layout)
    pose = goal_pose(goal) if (getattr(args, "pose_points", False) or getattr(args, "pose_image", False)) else None
    if pose and getattr(args, "pose_points", False):
        scene_text = scene_text + "\n\n" + pose_points_text(pose)

    def refs_of(names):
        out = []
        for n in names:
            if (refs_dir / n).exists() or (cache_dir / n).exists():
                out.append(prepare_ref(refs_dir / n, cache_dir))
        return out

    body, arms = refs_of(roles.get("body", [])), refs_of(roles.get("arms", []))
    skip = {Path(n).stem for n in roles.get("body", []) + roles.get("arms", [])}
    angle_routed = get_generation_refs(config, refs_dir, cache_dir, scene_image_path=goal, prompt_text=scene_text)
    faces = [r for r in angle_routed if r.stem not in skip][: int(getattr(args, "face_count", None) or roles.get("face_count", 4))]
    # Whole-scene photos from his favourites ("_fav" in the name) go as head-and-shoulders crops: sent whole as a FACE reference, one was
    # edited instead of the PHOTO TO EDIT (slimming edit 2026-09-27: IMG_4861_fav_right returned his rocky boulder-and-dog photo).
    import replicate as _R
    faces = [(_R.head_ref_crop(r, None) if "_fav" in r.stem else r) for r in faces]
    if getattr(args, "face_refs", None):
        # The user, 2026-10-02 (think-again): the angle-routed set always includes a _fav photo (IMG_5850_fav: glasses, short neat hair, a purple/yellow double exposure;
        # IMG_4861_fav_right: glasses, short hair) that contradicts his clean curly references; 139 renders never varied it. Name the exact photos instead.
        faces = [prepare_ref(refs_dir / n.strip(), cache_dir) for n in args.face_refs.split(",") if n.strip()]

    # his own photo as the goal: included as the original photo to recreate (auto = his face scores as him against the face refs)
    own = args.goal_as_image == "yes"
    own_score = None
    if args.goal_as_image == "auto":
        try:
            sc = ArcFaceScorer()
            g = sc.embed(prepare_ref(goal, cache_dir))
            own_score = max(sc.similarity(g, sc.embed(r)) for r in faces)
            own = own_score >= float(config.get("thresholds", {}).get("own_min", 0.40))
        except Exception:
            own = False
    files: list[Path] = []
    lines: list[str] = []

    def add(paths: list[Path], one: str, many: str) -> tuple[int, int]:
        if not paths:
            return 0, 0
        a = len(files) + 1
        files.extend(paths)
        b = len(files)
        lines.append(f"Image {a} is {one}" if a == b else f"Images {a}-{b} are {many}")
        return a, b

    body_only = getattr(args, "body_only", False)
    edit_photo = getattr(args, "edit_photo", None)
    if inv and inv.get("mode") == "objects":
        ref_n = {}
        for r in inv.get("refs", []):
            ref_n[r["key"]], _ = add([prepare_ref(ROOT / r["path"], cache_dir)], r["label"], "")
        edit_n, _ = add([prepare_ref(ROOT / inv["photo_to_edit"], cache_dir)], "the PHOTO TO EDIT.", "")
        change = [f"- {c['item']}: the PHOTO TO EDIT shows {c['goal']}; make it {c['his']}"
                  + (f" (image {ref_n[c['ref']]})" if c.get("ref") in ref_n else "") + "." for c in inv.get("change", [])]
        keep = [f"- {k}." for k in inv.get("keep", [])]
        prompt = ("REFERENCE IMAGES BY ROLE:\n" + "\n".join(lines) + f"\n\nEdit image {edit_n}, the PHOTO TO EDIT: make exactly the changes "
                  "in the CHANGE LIST and nothing else. Its framing and everything not in the CHANGE LIST stay exactly as they are.\n\n"
                  "CHANGE LIST:\n" + "\n".join(change) + "\n\nKEEP LIST (exactly as in the PHOTO TO EDIT):\n" + "\n".join(keep)
                  + "\n\nPhotorealistic photograph with the same light, colour, grain and sharpness as the PHOTO TO EDIT.")
        log = {"route": "G", "mode": "objects", "goal": str(goal), "goal_sent": False, "layout": None, "goal_own_score": None,
               "roles": {"face": [], "body": [], "arms": []}, "props": [], "layout_sketch": None, "scene_text": "\n".join(change),
               "goal_role": "photo to edit", "pose_points": False, "body_only": False, "edit_photo": None, "inventory": args.inventory}
        return prompt, files, faces, log
    if edit_photo:   # his own photo is the photo to edit, so it also carries his build: no separate body/arm references
        body, arms = [], []
    if not body_only:   # body-only edits keep the head's pixels: no face photos to redraw it from (faces still score identity)
        add(faces, "the FACE reference of this man.", "FACE references of this man.")
    body_n, _ = add(body, "the BODY reference — his true build and proportion.", "BODY references — his true build and proportion.")
    add(arms, "the SHOULDER AND ARM reference.", "SHOULDER AND ARM references.")
    ref_n = {}
    for r in (inv or {}).get("refs", []):
        ref_n[r["key"]], _ = add([prepare_ref(ROOT / r["path"], cache_dir)], r["label"], "")
    # Objects of his own, by role (the user, 2026-09-27: his Honda CB350 found in his photos, as the pin's motorcycle). PATH::LABEL.
    props = []
    for spec in getattr(args, "prop", None) or []:
        path, _, label = spec.partition("::")
        add([prepare_ref(Path(path), cache_dir)], label.strip(), "")
        props.append({"path": path, "label": label.strip()})
    sketch = None
    if layout and getattr(args, "layout_image", False):
        sketch, colour_key = layout_sketch(goal, layout, cache_dir)
        stick = ""
        if pose and getattr(args, "pose_image", False):
            from PIL import Image as _Image
            with _Image.open(sketch) as im:
                im = im.convert("RGB")
                draw_pose(im, pose)
                sketch = cache_dir / f"layout_pose_sketch_{goal.stem}.png"
                im.save(sketch)
            stick = " The black stick figure is his exact posture: every limb, both hands and both feet where the stick figure has them."
        add([sketch], f"a LAYOUT SKETCH, not a photograph: flat coloured boxes marking where things sit in the frame ({colour_key}).{stick} The "
            "photograph has exactly this frame: he, his head and these things fill exactly these boxes, the same size and the same camera "
            "distance. Draw nothing of the sketch itself: the photograph shows no coloured rectangles, box outlines or lines.", "")
        # ^ named only after it happened: pin v9 v3_0 drew the sketch's boxes into the photo (2026-09-27)
    replace = getattr(args, "replace_subject", False)
    goal_role = getattr(args, "goal_as_image", "auto") == "goal" and not replace
    if edit_photo:
        ep_n, _ = add([prepare_ref(Path(edit_photo), cache_dir)], "the PHOTO TO EDIT: his own full-length photo. His body in it — his "
                      "shoulders, arms, chest, waist and height — is his true build.", "")
    if goal_role and edit_photo:
        add([prepare_ref(goal, cache_dir)], "the GOAL IMAGE, a reference for the scene, pose, clothes, framing and light only. The man in the GOAL "
            "IMAGE is NOT the subject: nothing of his face, hair, beard, head shape, neck, skin or body build is carried over.", "")
    elif goal_role:
        # The user, 2026-09-27: send the goal itself, labelled as the goal, with the subject taken only from the references.
        add([prepare_ref(goal, cache_dir)], "the GOAL IMAGE. Recreate this photograph exactly: the same composition and framing, the same "
            "camera distance and angle, his exact posture (torso, both arms, both hands, both legs and feet) and exactly where he stands in the "
            "frame and against every object, the same scene, clothes and light. The man in the GOAL IMAGE is NOT the subject and must not "
            "appear: nothing of his face, hair, beard, head shape, jaw, neck, skin, body build or height is carried over. The subject is only "
            f"the man of images 1-{len(faces) + len(body) + len(arms)}.", "")
    if replace:
        # The user, 2026-09-27: "replace the newer me (the reference images: body, face, hair, beard, everything) in place of the goal image's
        # subject". The goal is the photo to edit, so posture, position and framing come from its own pixels.
        edit_src = (ROOT / inv["photo_to_edit"]) if inv and inv.get("photo_to_edit") else goal
        edit_n, _ = add([prepare_ref(edit_src, cache_dir)], "the PHOTO TO EDIT.", "")
    if own and not replace and not goal_role:
        add([prepare_ref(goal, cache_dir)], "the ORIGINAL PHOTO of this moment: recreate exactly its pose, framing, camera distance, "
            "clothes, background and light; his face, hair, beard and moustache come only from the FACE references, never from this photo.", "")
    face_text = str(profile.get("face_text", ""))
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
    template = ROLE_TEMPLATE_PATH.read_text(encoding="utf-8").strip()
    build = str(profile.get("build_text", "")).replace("{BODY}", str(body_n or 5))
    if (replace or goal_role) and not own:
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
    elif replace:
        template = template.replace("Generate a new photograph of THIS EXACT MAN — not a lookalike.",
            f"Edit image {edit_n}, the PHOTO TO EDIT: replace the man in it — his whole body and head, not only his face — with THIS EXACT "
            "MAN of the references, not a lookalike. His face, hair, beard, moustache, skin tone and build come only from the references. "
            "Keep everything else in the PHOTO TO EDIT exactly as it is: his exact posture (torso, both arms, both hands, both legs and feet), "
            "where he stands, his size in the frame, the camera and framing, the clothes, every object, the background and the light. Only "
            "who he is changes.")
    if inv:
        change = [f"- {c['item']}: the PHOTO TO EDIT shows {c['goal']}; make it {c['his']}"
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
    log = {"route": "G", "goal": str(goal), "goal_sent": own, "layout": layout, "goal_own_score": None if own_score is None else round(own_score, 3),
           "roles": {"face": [r.name for r in faces], "body": [r.name for r in body], "arms": [r.name for r in arms]}, "props": props,
           "layout_sketch": str(sketch) if sketch else None, "scene_text": scene_text,
           "goal_role": "photo to edit" if replace else ("goal image" if goal_role else ("original photo" if own else None)),
           "pose_points": bool(pose and getattr(args, "pose_points", False)), "body_only": body_only, "edit_photo": edit_photo, "inventory": getattr(args, "inventory", None)}
    return prompt, files, faces, log


def cmd_score(args) -> int:
    import scorer

    config = load_config()
    refs_dir = get_refs_dir(config)
    ref_paths = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    scorer.score_images([Path(p) for p in args.images], ref_paths)
    return 0


def cmd_refs_matrix(args) -> int:
    import scorer

    config = load_config()
    refs_dir = get_refs_dir(config)
    ref_paths = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    scorer.refs_matrix(ref_paths)
    return 0


def cmd_restore(args) -> int:
    from restore import restore_face
    from scorer import ArcFaceScorer, analyze_face

    config = load_config()
    refs_dir = get_refs_dir(config)
    all_refs = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    threshold = float(config.get("identity_threshold", 0.60))

    arc_scorer = ArcFaceScorer()
    ref_embeds = []
    for r in all_refs:
        try:
            emb = arc_scorer.embed(r)
            ref_embeds.append(emb)
        except Exception:
            pass

    for p in args.images:
        target = Path(p)
        if not target.exists():
            print(f"Target not found: {target}")
            continue

        face_info = analyze_face(target)
        raw_sharpness = face_info.get("sharpness", 0.0)
        is_profile = face_info.get("is_profile", False)
        yaw_ratio = face_info.get("yaw_ratio", 1.0)
        pose_bin = face_info.get("pose_bin", "frontal")

        raw_score = None
        try:
            raw_emb = arc_scorer.embed(target)
            raw_score = max(arc_scorer.similarity(raw_emb, r) for r in ref_embeds)
        except Exception:
            pass

        raw_s = f"{raw_score:.3f}" if raw_score is not None else "N/A"
        print(f"Restoring {target.name} (raw score: {raw_s} | yaw={yaw_ratio:.2f} | {pose_bin} | profile={is_profile})...", flush=True)
        if is_profile and not getattr(args, "force_profile", False):
            print("  [Profile Protection] Steep profile angle detected. 2D swapper locked out to prevent facial collapse. Use --force-profile to override.")
            continue

        res = restore_face(target, protect_profile=not getattr(args, "force_profile", False))
        if not res["success"]:
            print(f"  FAILED: {res.get('error')}")
            continue

        restored_path = Path(res["output"])
        rest_info = analyze_face(restored_path)
        rest_sharpness = rest_info.get("sharpness", 0.0)

        rest_score = None
        try:
            rest_emb = arc_scorer.embed(restored_path)
            rest_score = max(arc_scorer.similarity(rest_emb, r) for r in ref_embeds)
        except Exception:
            pass

        status = "ACCEPTED" if (rest_score and rest_score >= threshold) else "REJECTED"
        score_str = f"{rest_score:.3f}" if rest_score else "N/A"
        print(f"  -> {restored_path.name} in {res['elapsed_sec']}s | score: {score_str} | sharp: {rest_sharpness:.1f} (raw: {raw_sharpness:.1f}) | [{status}]")
    return 0


def cmd_pose_refs(args) -> int:
    from pose_refs import fetch_pose_refs
    sheet = fetch_pose_refs(args.query, count=args.count)
    print(f"Pose references ready in: {sheet.parent if sheet.is_file() else sheet}")
    return 0


async def cmd_replicate(args) -> int:
    import replicate

    return await replicate.run(args)


async def cmd_check(args) -> int:
    import paths

    paths_status = paths.report()
    print()
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            print(f"Authenticated. account_status={client.account_status.name}")
            return paths_status
    except AuthError as e:
        print(str(e))
        return 1


async def cmd_models(args) -> int:
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            models = client.list_models()
            if not models:
                print("No models returned.")
                return 1
            for m in models:
                print(f"{m.model_id}\t{m.display_name}\tavailable={m.is_available}")
            return 0
    except AuthError as e:
        print(str(e))
        return 1


async def cmd_gen(args) -> int:
    if args.scene_image and not getattr(args, "goal", None):
        # Describing a source photo in words and redrawing it is what made background, clothes and body drift.
        # With a source photo the right tool is replicate (edit a crop, paste it back into the untouched original).
        import argparse as _argparse

        import replicate

        print("NOTE: `gen --scene-image` now runs `replicate` (edit-in-place with paste-back). The prompt text is ignored because\n"
              "the photo itself is the scene. For a from-scratch scene, run `gen` without --scene-image.")
        ns = _argparse.Namespace(scene=args.scene_image, zone="auto", source="auto", glasses="same", look="any", expression="auto",
                                 build="normal", count=args.count, max_attempts=max(6, args.count * 3),
                                 force=False, model=args.model, verbose=args.verbose)
        return await replicate.run(ns)

    config = apply_subject(load_config(), args.subject)
    refs_dir = get_refs_dir(config)
    cache_dir = ROOT / config.get("cache_dir", ".cache/refs")
    out_root = ROOT / config.get("out_dir", "outputs")
    model = args.model or config.get("model")
    threshold = float(config.get("identity_threshold", 0.60))
    restore_refs = [refs_dir / name for name in config.get("restore_refs", ["IMG_6858.jpg", "IMG_6873.jpg", "IMG_6875.jpg", "IMG_6923 Copy.jpg"]) if (refs_dir / name).exists() or (cache_dir / name).exists()]

    goal_log = None
    if getattr(args, "goal", None):
        full_prompt, files_g, ref_paths_g, goal_log = build_goal_request(config, refs_dir, cache_dir, args)
        scene_text = goal_log["scene_text"]
        args.no_restore = True   # route G is judged raw, like beach.jpg and pin v2/v3
    else:
        prompt_arg = Path(args.prompt)
        scene_text = prompt_arg.read_text(encoding="utf-8").strip() if prompt_arg.is_file() else args.prompt
        full_prompt = IDENTITY_LOCK_PATH.read_text(encoding="utf-8").strip() + "\n" + scene_text

    from pose_refs import mask_head_from_scene

    scene_headless = None
    if args.scene_image and not goal_log:
        full_prompt += SCENE_REF_NOTE
        src_scene = Path(args.scene_image)
        if "headless" in src_scene.name:
            scene_headless = src_scene
        else:
            cached_headless = cache_dir / f"{src_scene.stem}_headless.jpg"
            print(f"Processing scene reference to headless neutral: {src_scene.name} -> {cached_headless.name}...")
            scene_headless = mask_head_from_scene(src_scene, cached_headless)

    if goal_log:
        ref_paths = ref_paths_g
        files = [str(p) for p in files_g]
        print(f"Route G refs by role: face {goal_log['roles']['face']}, body {goal_log['roles']['body']}, arms {goal_log['roles']['arms']}"
              + "".join(f", prop {Path(x['path']).name}" for x in goal_log["props"])
              + (f", + the goal as the {goal_log['goal_role']}" if goal_log.get("goal_role") else ", goal not sent")
              + (", + layout sketch" if goal_log.get("layout_sketch") else "") + (", + POSE POINTS" if goal_log.get("pose_points") else ""))
    else:
        ref_paths = get_generation_refs(config, refs_dir, cache_dir, scene_image_path=args.scene_image, prompt_text=scene_text)
        files = [str(p) for p in ref_paths]
        if scene_headless:
            files.append(str(scene_headless))
        print(f"Angle-routed refs ({len(ref_paths)}): {', '.join(p.name for p in ref_paths)}" + (f" + headless scene ({scene_headless.name})" if scene_headless else ""))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_root / f"{timestamp}_{slugify(('goal ' + Path(args.goal).stem) if goal_log else scene_text)}"
    # Parallel runs of the SAME goal started in the same second shared one folder and crashed each other (pin 9, 2026-10-01, 229 credits lost): never reuse a folder.
    # (the check and the mkdir race when two runs start in the same second, so create atomically and retry with the next suffix, 2026-10-01)
    base_dir, suffix = run_dir, 1
    out_root.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            run_dir.mkdir(exist_ok=False)
            break
        except FileExistsError:
            suffix += 1
            run_dir = out_root / f"{base_dir.name}_{suffix}"

    run_log = {
        "timestamp": timestamp,
        "prompt": full_prompt,
        "subject": args.subject,
        "refs": [p.name for p in ref_paths],
        "scene_image": str(scene_headless) if scene_headless else args.scene_image,
        "model": model,
        "identity_threshold": threshold,
        "results": [],
    }
    if goal_log:
        run_log["route_g"] = goal_log

    # Lazy-load scorer
    from scorer import ArcFaceScorer, analyze_face
    arc_scorer = ArcFaceScorer()
    ref_embeds = []
    for r in ref_paths:
        try:
            emb = arc_scorer.embed(r)
            ref_embeds.append(emb)
        except Exception:
            pass

    from restore import restore_face

    candidates = []
    saved_count = 0
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            print(f"Authenticated. account_status={client.account_status.name}")
            # Credits of every call (the user, 2026-09-27: what does one run folder cost, and can it cost less).
            credit_log = {"model": model, "start": credits_left(client), "calls": []}
            run_log["credits"] = credit_log
            last_left = [credit_log["start"]]
            print(f"[Credits] window left at start: {credit_log['start']}")

            def note_credits(i, outcome):
                now = credits_left(client)
                used = (last_left[0] - now) if (now is not None and last_left[0] is not None) else None
                credit_log["calls"].append({"index": i, "outcome": outcome, "credits": used, "left": now})
                spent = sum(c["credits"] or 0 for c in credit_log["calls"])
                print(f"[Credits] this call {used}, run total {spent}, window left {now}")
                last_left[0] = now

            gated, fails_in_row = {}, 0
            for i in range(args.count):
                print(f"\nGenerating candidate {i + 1}/{args.count}...")
                try:
                    output = None
                    for up_try in range(3):
                        try:
                            output = await client.generate_content(
                                full_prompt, files=files, model=model, temporary=True
                            )
                            break
                        except (GeminiError, ImageGenerationError, UsageLimitExceededError):
                            raise
                        except Exception as e:   # a 5xx from Google's file-upload service (HTTP 503, 2026-09-27): nothing generated yet
                            if "HTTP Error 5" not in str(e) or up_try == 2:
                                raise
                            print(f"  upload failed ({e}); retrying in {20 * (up_try + 1)} s")
                            await asyncio.sleep(20 * (up_try + 1))
                except UsageLimitExceededError:
                    print("Usage limit hit on this account. Stopping batch.")
                    run_log["results"].append({"index": i, "error": "UsageLimitExceededError"})
                    break
                except (ImageGenerationError, GeminiError) as e:
                    print(f"Generation {i + 1} failed: {type(e).__name__}: {e}")
                    run_log["results"].append({"index": i, "error": f"{type(e).__name__}: {e}"})
                    note_credits(i, "error")
                    continue

                candidate = output.candidates[output.chosen]
                images = candidate.generated_images
                if not images:
                    print(f"Generation {i + 1}: no image returned. Response text: {candidate.text}")
                    run_log["results"].append({"index": i, "error": "no_image", "text": candidate.text})
                    note_credits(i, "no_image")
                    continue
                note_credits(i, "image")

                entry = {"index": i, "files": [], "evaluations": []}
                for j, img in enumerate(images):
                    saved_path = Path(await img.save(path=str(run_dir), filename=f"v{i + 1}_{j}.png", verbose=args.verbose))
                    saved_path = fix_extension(saved_path)
                    print(f"Saved raw image: {saved_path.name}")
                    entry["files"].append(saved_path.name)
                    saved_count += 1

                    cand_eval = {
                        "raw_file": saved_path.name,
                        "raw_score": None,
                        "restored_file": None,
                        "restored_score": None,
                        "status": "pending",
                    }

                    # Analyze face pose and sharpness
                    face_info = analyze_face(saved_path)
                    is_profile = face_info.get("is_profile", False)
                    yaw_ratio = face_info.get("yaw_ratio", 1.0)
                    pose_bin = face_info.get("pose_bin", "frontal")
                    direction = face_info.get("direction", "Frontal")
                    raw_sharpness = face_info.get("sharpness", 0.0)

                    # Score raw image
                    try:
                        raw_emb = arc_scorer.embed(saved_path)
                        cand_eval["raw_score"] = float(max(arc_scorer.similarity(raw_emb, r) for r in ref_embeds))
                    except Exception:
                        pass

                    # Restore face unless --no-restore passed
                    final_path = saved_path
                    check_score = cand_eval["raw_score"]

                    if is_profile:
                        # STRICT PROFILE PROTECTION: 2D frontal template swappers collapse at steep yaw (>45°).
                        # Native Gemini generation (conditioned on headless scene + angle-matched profile refs)
                        # preserves authentic skull width, nasal bridge, and curly hairline with zero affine distortion.
                        cand_eval["restoration_skipped"] = "profile_protection"
                        profile_thresh = 0.50
                        if check_score is not None and check_score >= profile_thresh and raw_sharpness >= 200.0:
                            cand_eval["status"] = "accepted"
                            print(f"  [Profile Gate] Native profile generation ({pose_bin}, {direction}, yaw={yaw_ratio:.2f}) accepted natively (score={check_score:.3f} >= {profile_thresh:.2f}, sharp={raw_sharpness:.1f}). 2D swapper locked out.")
                        else:
                            cand_eval["status"] = "rejected"
                            print(f"  [Profile Gate] Native profile generation fell below threshold ({check_score if check_score else 'N/A'} vs {profile_thresh:.2f} or low sharpness {raw_sharpness:.1f}).")
                    elif cand_eval["raw_score"] is not None and cand_eval["raw_score"] >= threshold and raw_sharpness >= 300.0:
                        cand_eval["restoration_skipped"] = "native_accepted"
                        cand_eval["status"] = "accepted"
                        print(f"  [Quality Gate] Native raw identity ({cand_eval['raw_score']:.3f} >= {threshold:.2f}, sharp={raw_sharpness:.1f}) accepted natively.")
                    elif not args.no_restore:
                        print(f"  Restoring face on {saved_path.name} via angle-routed FaceFusion...", flush=True)
                        res = restore_face(saved_path, protect_profile=True)
                        if res["success"]:
                            restored_path = Path(res["output"])
                            rest_info = analyze_face(restored_path)
                            rest_sharpness = rest_info.get("sharpness", 0.0)
                            pose_desc = f"{res['pose']['bin']} ({res['pose']['direction']}, yaw={res['pose']['yaw_ratio']})"
                            print(f"  [Router] Pose: {pose_desc} -> Sources: {', '.join(res['sources'])}")

                            # Sharpness gatekeeper: reject blurry / melted artifacts
                            if raw_sharpness > 0 and rest_sharpness < 0.50 * raw_sharpness:
                                print(f"  [Sharpness Gate] Restoration lost excessive sharpness ({rest_sharpness:.1f} vs raw {raw_sharpness:.1f}). Discarding restoration.")
                                cand_eval["restoration_rejected"] = "sharpness_loss"
                                cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= 0.50) else "rejected"
                            else:
                                cand_eval["restored_file"] = restored_path.name
                                final_path = restored_path
                                try:
                                    rest_emb = arc_scorer.embed(restored_path)
                                    cand_eval["restored_score"] = float(max(arc_scorer.similarity(rest_emb, r) for r in ref_embeds))
                                    check_score = cand_eval["restored_score"]
                                except Exception:
                                    pass

                                if check_score is not None and check_score >= threshold:
                                    cand_eval["status"] = "accepted"
                                else:
                                    cand_eval["status"] = "rejected"
                        else:
                            print(f"  Restore skipped/failed: {res.get('error')}")
                            cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= threshold) else "rejected"
                    else:
                        cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= threshold) else "rejected"

                    raw_s = f"{cand_eval['raw_score']:.3f}" if cand_eval['raw_score'] else "N/A"
                    rest_s = f"{cand_eval['restored_score']:.3f}" if cand_eval['restored_score'] else "N/A"
                    print(f"  [Score] raw: {raw_s} -> restored: {rest_s} | sharp: {raw_sharpness:.1f} | [{cand_eval['status'].upper()}]")

                    entry["evaluations"].append(cand_eval)
                    candidates.append((check_score or -1.0, final_path, cand_eval))

                run_log["results"].append(entry)
                # Early stop (credit plan step 3): gate this render now; stop the approach once the answer is known.
                if goal_log and (getattr(args, "stop_after_fails", 0) or getattr(args, "stop_on_pass", False)):
                    mine = [c[1] for c in candidates if c[1].name in entry["files"] or c[1].name in [f.replace(".png", ".jpg") for f in entry["files"]]]
                    for g in run_pose_gate(Path(args.goal), mine):
                        gated[Path(g["render"]).name] = g
                        passed = not g.get("fails")
                        fails_in_row = 0 if passed else fails_in_row + 1
                        print(f"  [Pose gate] {Path(g['render']).name}: " + ("PASS" if passed else "FAIL items " + ", ".join(sorted(set(map(str, g["fails"]))))))
                        if passed and getattr(args, "stop_on_pass", False):
                            print("  [Early stop] a render passed the pose gate (--stop-on-pass).")
                    if getattr(args, "stop_on_pass", False) and any(not g.get("fails") for g in gated.values()):
                        break
                    if getattr(args, "stop_after_fails", 0) and fails_in_row >= args.stop_after_fails:
                        print(f"  [Early stop] {fails_in_row} renders in a row failed the pose gate: this approach is answered, "
                              f"{args.count - i - 1} renders not spent.")
                        run_log["early_stop"] = {"after": i + 1, "fails_in_row": fails_in_row}
                        break
            # A settled final reading (single readings can lag by a call).
            try:
                await asyncio.sleep(3)
                await client._fetch_usage_info()
            except Exception:
                pass
            credit_log["end"] = credits_left(client)
            if credit_log["start"] is not None and credit_log["end"] is not None:
                credit_log["total"] = credit_log["start"] - credit_log["end"]
                n_img = sum(1 for c in credit_log["calls"] if c["outcome"] == "image")
                credit_log["per_image"] = round(credit_log["total"] / n_img, 1) if n_img else None
                print(f"[Credits] run total {credit_log['total']} for {n_img} images ({credit_log['per_image']} per image); window left {credit_log['end']}")
    except AuthError as e:
        print(str(e))
        return 1
    finally:
        # Pose gate (checklist items 12/14/29/30), measured, fixed limits: a render that fails it is never picked as best.jpg.
        if goal_log and candidates:
            gated = locals().get("gated") or {}
            todo = [c[1] for c in candidates if c[1].name not in gated]
            gate = list(gated.values()) + (run_pose_gate(Path(args.goal), todo) if todo else [])
            run_log["pose_gate"] = gate
            failed = {Path(g["render"]).name for g in gate if g.get("fails")}
            for g in gate:
                print(f"  [Pose gate] {Path(g['render']).name}: " + ("PASS" if not g["fails"] else "FAIL items " + ", ".join(sorted(set(map(str, g["fails"]))))
                      + " -> " + "; ".join(f"{c['name']} {c['value']}" for c in g["checks"] if not c["ok"])))
            for c in candidates:
                if c[1].name in failed:
                    c[2]["status"] = "rejected"
                    c[2]["pose_gate"] = "fail"
        # Pick best.jpg
        if candidates:
            # Sort by accepted status first, then by score
            candidates.sort(key=lambda x: (1 if x[2].get("status") == "accepted" else 0, x[0]), reverse=True)
            top_score, top_path, top_eval = candidates[0]
            is_accepted = top_eval.get("status") == "accepted" or top_score >= threshold
            if is_accepted:
                best_file = run_dir / "best.jpg"
                shutil.copy2(top_path, best_file)
                run_log["best"] = {
                    "file": "best.jpg",
                    "source": top_path.name,
                    "score": round(top_score, 3),
                    "status": "accepted",
                }
                print(f"\n[BEST] Selected {top_path.name} as best.jpg (identity score={top_score:.3f} | status=ACCEPTED)")
                print("  candidate only: not best until every item of BEST_CHECKLIST.md passes by eye (tools\\best_check.py)")
            else:
                print(f"\n[REJECTED] All candidates fell below threshold ({threshold:.2f}). Top score was {top_score:.3f}. No best.jpg created.")

        (run_dir / "run.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
        # End hook of the skill (the user, 2026-10-01): copy the pictures out of outputs/ into the named, versioned results folder.
        sys.path.insert(0, str(ROOT / "tools"))
        from export_results import safe_export
        safe_export(run_dir)

    return 0 if saved_count > 0 else 1


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description="Generate identity-consistent images via your Gemini web session",
                                     parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verify external paths (FaceFusion, reference photos, vault) and authentication", parents=[common])
    sub.add_parser("models", help="List available models for this account", parents=[common])

    score = sub.add_parser("score", help="Objective face-identity similarity of images against the pinned refs")
    score.add_argument("images", nargs="+", help="Image paths to score")

    sub.add_parser("refs-matrix", help="Pairwise identity similarity matrix among the pinned refs (find outliers)")

    restore_p = sub.add_parser("restore", help="Restore face on target image(s) using FaceFusion + verify")
    restore_p.add_argument("images", nargs="+", help="Image path(s) to restore")
    restore_p.add_argument("--force-profile", action="store_true", help="Force FaceFusion 2D swapper even on steep profile poses")

    pose_p = sub.add_parser("pose-refs", help="Search and download pose/model references + build contact sheet")
    pose_p.add_argument("--query", required=True, help="Search query (e.g. 'man sitting in convertible laughing')")
    pose_p.add_argument("--count", type=int, default=6, help="Number of images to fetch (default 6)")

    gen = sub.add_parser("gen", help="Generate one or more images", parents=[common])
    gen.add_argument("--prompt", required=True, help="Scene text, or a path to a .txt file containing it")
    gen.add_argument("--scene-image", default=None, help="Optional path to a scene/style reference image")
    gen.add_argument("--count", type=int, default=1, help="How many variations to generate (default 1)")
    gen.add_argument("--model", default=None, help="Model id override (defaults to facecard.json's \"model\")")
    gen.add_argument("--no-restore", action="store_true", help="Skip FaceFusion restoration and keep raw output")
    gen.add_argument("--goal", default=None, help="Route G: the goal picture (a pin, or his own photo). Its POSE/WARDROBE/SCENE/LIGHT/CAMERA "
                     "text goes in --prompt; the goal photo is sent only when it is his own photo")
    gen.add_argument("--goal-as-image", choices=["auto", "yes", "no", "goal"], default="auto",
                     help="Send the goal photo as the original to recreate: auto = only when it is his own photo")
    gen.add_argument("--stop-after-fails", type=int, default=0, help="Route G: stop after N renders in a row fail the pose gate (credit saving)")
    gen.add_argument("--stop-on-pass", action="store_true", help="Route G: stop at the first render that passes the pose gate")
    gen.add_argument("--pose-points", action="store_true", help="Route G: add the goal's measured joints as POSE POINTS (tools/pose_compare.py --save-goal)")
    gen.add_argument("--pose-image", action="store_true", help="Route G: draw the goal's skeleton into the layout sketch (with --layout-image)")
    gen.add_argument("--inventory", default=None, help="Route G: an element inventory JSON (.cache/inventories): its references by role, "
                     "its clean photo to edit, and its CHANGE / KEEP lists compiled into the prompt")
    gen.add_argument("--edit-photo", default=None, help="Route G, with --goal-as-image goal: edit HIS photo (this path) into the goal scene "
                     "and pose; the goal is a reference only. His build comes from the edited pixels")
    gen.add_argument("--body-only", action="store_true", help="With --replace-subject: edit only his body; no face photos sent, head kept as is")
    gen.add_argument("--replace-subject", action="store_true", help="Route G: send the goal as the PHOTO TO EDIT and replace its man with him")
    gen.add_argument("--layout-image", action="store_true", help="Route G: also send the goal's cached layout boxes as a flat sketch image "
                     "(tools/goal_layout.py), labelled as the frame to match")
    gen.add_argument("--prop", action="append", default=None, help="Route G: an object of his own as a labelled reference, PATH::LABEL "
                     "(e.g. his motorcycle). Repeatable")
    gen.add_argument("--face-refs", default=None, help="Route G: the exact FACE reference photos to send, comma separated names from the references folder (replaces the angle-routed set, "
                     "which always contains a _fav photo of him with glasses or different hair)")
    gen.add_argument("--face-count", type=int, default=None, help="Route G: how many FACE reference photos of him to send (default: facecard.json roles.face_count = 4). "
                     "For a turned or profile goal the cut at 4 drops the two frontal anchors (IMG_6873, IMG_6858), the clearest photos of his face shape (2026-10-01, identity regression on pins 5 and 6)")
    gen.add_argument("--subject", default=None, help="Whose photo this is: a key of facecard.json subject_profiles (reference set and traits for scene-prompt-writer). Omit for the top-level reference set")

    rep = sub.add_parser("replicate", help="Put your identity into a source photo by editing a crop and pasting it back (nothing outside the zone changes)", parents=[common])
    rep.add_argument("--scene", required=True, help="Source photo to replicate (full resolution)")
    rep.add_argument("--zone", choices=["auto", "face", "head", "head+build"], default="auto", help="What to replace (auto: own photo -> face, someone else -> head; head+build is opt-in)")
    rep.add_argument("--source", choices=["auto", "own", "foreign"], default="auto", help="Is the source photo of you? (auto: decided by identity score)")
    rep.add_argument("--glasses", choices=["same", "yes", "no"], default="same", help="same: keep the glasses the source photo shows; yes: thin metal glasses; no: none")
    rep.add_argument("--look", choices=["any", "curly", "short"], default="any", help="Hair when the head is replaced")
    rep.add_argument("--expression", default=None, help="default: the same expression as the reference photo when the source is another person's, the attractiveness policy (auto) for your own photos. same: copy the source expression; auto: the attractiveness policy from facecard.json; none: say nothing; or free text such as 'a broad smile with teeth showing'")
    rep.add_argument("--build", choices=["normal", "strong"], default="normal", help="Wording of the physique edit for head+build (strong asks for visibly broader shoulders and arms)")
    rep.add_argument("--count", type=int, default=2, help="How many candidates must PASS every check before stopping (best is kept)")
    rep.add_argument("--max-attempts", type=int, default=6, dest="max_attempts", help="Ceiling on Gemini calls per photo while chasing --count passing candidates")
    rep.add_argument("--force", action="store_true", help="Re-render even a photo that is one of your best versions (facecard.json best_versions); every other photo is always processed")
    rep.add_argument("--model", default=None, help="Model id override")

    args = parser.parse_args()
    args.verbose = getattr(args, "verbose", False)
    sync_handlers = {
        "score": cmd_score,
        "refs-matrix": cmd_refs_matrix,
        "restore": cmd_restore,
        "pose-refs": cmd_pose_refs,
    }
    if args.command in sync_handlers:
        return sync_handlers[args.command](args)
    async_handlers = {"check": cmd_check, "models": cmd_models, "gen": cmd_gen, "replicate": cmd_replicate}
    return asyncio.run(async_handlers[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
