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
from recipe import layout_text, pose_points_text  # noqa: F401  (moved to recipe.py 2026-10-07; re-exported for tools/goal_layout.py)
from session import AuthError, authenticated_client, credits_left

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "facecard.json"
IDENTITY_LOCK_PATH = ROOT / "prompts" / "identity_lock.txt"
ROLE_TEMPLATE_PATH = ROOT / "prompts" / "role_template.txt"
LAYOUTS_DIR = ROOT / ".cache" / "layouts"
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


PREP_INDEX = "_prep_index.json"
RENDER_STEM = re.compile(r"^(v\d+_\d+|best|cand\d+|not_passing_closest)$", re.I)


def _prep_index(cache_dir: Path) -> dict:
    try:
        return json.loads((cache_dir / PREP_INDEX).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _note_prep(cache_dir: Path, cached: Path, src: Path) -> None:
    """Remember which source file each cached copy was made from (the cache is keyed by file stem, so two runs' v1_0.jpg share one name)."""
    idx = _prep_index(cache_dir)
    key = str(src.resolve())
    if (idx.get(cached.name) or {}).get("source") != key:
        idx[cached.name] = {"source": key, "noted": datetime.now().isoformat(timespec="seconds")}
        import provenance
        provenance.atomic_write_json(cache_dir / PREP_INDEX, idx)


def prepare_ref(src: Path, cache_dir: Path, max_dim: int = 2048) -> Path:
    """EXIF-transpose + downscale a reference image, cached by source mtime.

    Collision guard (2026-10-07): the cache is keyed by file stem, so an earlier run's v1_0.jpg (a stage-2 photo to edit) could be sent in place
    of another run's v1_0.jpg whenever the cached copy was newer. .cache/refs/_prep_index.json now records each copy's source; a copy made from a
    different source, or a render-named copy with no record, is made again. Reference photos with no record are trusted as before (unchanged
    bytes, unchanged upload names)."""
    if not src.exists():
        fallback = cache_dir / src.name
        if fallback.exists():
            src = fallback
        else:
            raise FileNotFoundError(f"Reference image not found: {src}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / (src.stem + ".jpg")
    same_file = cached.is_file() and cached.resolve() == src.resolve()
    entry = _prep_index(cache_dir).get(cached.name)
    foreign = not same_file and ((entry is not None and entry.get("source") != str(src.resolve())) or (entry is None and RENDER_STEM.match(src.stem)))
    if cached.is_file() and not foreign and (same_file or cached.stat().st_mtime >= src.stat().st_mtime):
        if not same_file:
            _note_prep(cache_dir, cached, src)
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
    if not same_file:
        _note_prep(cache_dir, cached, src)
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


def head_bin_from_text_ev(prompt_text: str) -> tuple[str, str]:
    """(bin, the words that decided it). See head_bin_from_text."""
    low = prompt_text.lower()
    m = HEAD_TURN_RE.search(low)
    if m:
        deg, side = int(m.group(1)), m.group(2)
        if deg >= 55:
            return f"profile_{side}", m.group(0)
        if deg >= 25:
            return f"three_quarter_{side}", m.group(0)
        return "frontal", m.group(0)
    for sentence in re.split(r"(?<=[.!?])\s+", low):
        if "profile" in sentence or "60 degree" in sentence or "70 degree" in sentence or "75 degree" in sentence:
            return ("profile_left" if "left" in sentence else "profile_right"), sentence[:160]
        if "three-quarter" in sentence or "3/4" in sentence or "40 degree" in sentence or "45 degree" in sentence:
            return ("three_quarter_left" if "left" in sentence else "three_quarter_right"), sentence[:160]
    return "frontal", "no head-turn phrase in the text"


def head_bin_from_text(prompt_text: str) -> str:
    """Pose bin from the head phrase only, so a limb on picture-left does not pull left-facing references.

    scene-prompt-writer writes the head as "face turned about N degrees toward picture-left/right", the same picture-side
    convention as scorer.analyze_face (a nose left of the eye centre is a *_left bin). Older prompt files without that phrase
    fall back to the keyword read, limited to the sentence that names the turn.
    """
    return head_bin_from_text_ev(prompt_text)[0]


def face_choice_of(config: dict, scene_image_path, prompt_text: str, info: dict | None = None) -> str:
    """The head-pose bin that picks the FACE references: YuNet on the goal first, then the head phrase of the text. `info` (if given) receives
    {'bin', 'decided_by', 'evidence'} so the choice is visible in the recipe (2026-10-07: pin 5's face set was decided by one sentence,
    "about 25 degrees", exactly on the cut-off, because YuNet found no face in the bowed goal)."""
    from scorer import analyze_face
    target_bin, decided, evidence = "frontal", "default", "no goal picture and no text"
    if scene_image_path and Path(scene_image_path).exists():
        fi = analyze_face(scene_image_path)
        if fi.get("detected"):
            target_bin, decided = fi.get("pose_bin", "frontal"), "yunet"
            evidence = f"YuNet found the goal's face: {fi.get('direction')}, yaw ratio {fi.get('yaw_ratio')}"
        else:
            evidence = "YuNet found no face in the goal"
    if target_bin == "frontal" and prompt_text:
        tb, words = head_bin_from_text_ev(prompt_text)
        target_bin = tb
        decided = "text" if decided != "yunet" else "yunet+text"
        evidence = f"{evidence}; the text says: \"{words}\""
    if info is not None:
        info.update({"bin": target_bin, "decided_by": decided, "evidence": evidence})
        # Record-only (2026-10-07): the measured head turn of the goal (headpose.py). It never changes the bin; a contradiction is shown, because
        # pin 5's text said "toward picture-left" while its measured turn is 18 degrees toward picture-right.
        if scene_image_path and Path(scene_image_path).exists():
            import headpose
            hp = headpose.measure(scene_image_path)
            info["measured"] = hp
            bin_side = "picture-left" if target_bin.endswith("_left") else ("picture-right" if target_bin.endswith("_right") else "frontal")
            if hp.get("detected") and hp.get("side") and hp["side"] != bin_side and hp["side"] != "frontal":
                info["warning"] = (f"the face references were chosen for a head turned {bin_side} ({decided}), but the goal's measured head turn is "
                                   f"{abs(hp['yaw']):.0f} degrees toward {hp['side']} (yaw {hp['yaw']:+.0f}, pitch {hp['pitch']:+.0f})")
    return target_bin


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
    info: Optional[dict] = None,
) -> list[Path]:
    """Select angle-targeted identity references for Gemini generation.

    If scene reference or prompt specifies a profile or 3/4 angle, concentrates Gemini's
    attention on angle-matched photos (plus 1-2 frontal anchors) to avoid diluting
    cross-attention with conflicting frontal faces.
    """
    pose_bins = config.get("pose_bins", {})
    all_refs = config.get("refs", [])

    # Detect target angle from scene image or prompt (the decision and its evidence go into `info`)
    target_bin = face_choice_of(config, scene_image_path, prompt_text, info)

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


def pose_python() -> Path:
    import paths
    return paths.yolo_python()


_LIMBS = [("l_shoulder", "r_shoulder"), ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"), ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
          ("l_shoulder", "l_hip"), ("r_shoulder", "r_hip"), ("l_hip", "r_hip"), ("l_hip", "l_knee"), ("l_knee", "l_ankle"), ("r_hip", "r_knee"),
          ("r_knee", "r_ankle")]


def goal_pose(goal: Path) -> dict | None:
    """The goal's measured keypoints (tools/pose_compare.py --save-goal)."""
    f = POSES_DIR / f"{goal.stem}.json"
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    return d if d and d.get("person") else None


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


def run_pose_gate(goal: Path, renders: list[Path], strict: bool = False, record: dict | None = None) -> list[dict]:
    """tools/pose_compare.py on every render (the YOLO environment); returns one result per render. Fixed limits live in that tool.
    It used to return nothing, silently, when the YOLO environment was missing (no render gated, none rejected). Now that is printed, and with
    strict=True (the staged runner) it is an error; `record` receives the tool's exit code and stderr."""
    import subprocess
    if not renders:
        return []
    py = pose_python()
    if not py.exists():
        if strict:
            raise RuntimeError(f"the pose gate cannot run: {py} not found")
        print(f"  [Pose gate] SKIPPED: {py} not found, no render was gated")
        return []
    cmd = [str(py), str(ROOT / "tools" / "pose_compare.py"), str(goal), *map(str, renders), "--json"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    if record is not None:
        record.update({"returncode": out.returncode, "stderr": (out.stderr or "")[-6000:]})
    res = []
    for line in out.stdout.splitlines():
        if line.startswith("{"):
            try:
                res.append(json.loads(line))
            except Exception:
                pass
    if strict and len(res) != len(renders):
        raise RuntimeError(f"the pose gate returned {len(res)} result(s) for {len(renders)} render(s) (exit {out.returncode}): {(out.stderr or '')[-400:]}")
    return res


def resolve_goal_inputs(config: dict, refs_dir: Path, cache_dir: Path, args) -> dict:
    """Every FILE decision of Route G, made once (2026-10-07: build_goal_request split into resolve + compile, so a recipe can freeze the result).
    Which reference photo goes in which role and WHY, their prepared copies, the photo to edit, props, the layout sketch, whether the goal is his
    own photo. Returns the compiler's input (recipe.compile_route_g). Each item carries its prepared path, its upload name (the file name Gemini
    sees), where it came from and why it was chosen; `face_choice` records the head-pose bin decision and its evidence."""
    from scorer import ArcFaceScorer
    import recipe as R

    profile = config.get("subject_profiles", {}).get(args.subject or "me", {})
    roles = profile.get("roles", {})
    goal = Path(args.goal)
    prompt_arg = Path(args.prompt)
    scene_text = prompt_arg.read_text(encoding="utf-8").strip() if prompt_arg.is_file() else args.prompt
    inv = json.loads(Path(args.inventory).read_text(encoding="utf-8")) if getattr(args, "inventory", None) else None
    lay_p = LAYOUTS_DIR / f"{goal.stem}.json"
    layout = json.loads(lay_p.read_text(encoding="utf-8")) if lay_p.exists() else None
    pose = goal_pose(goal) if (getattr(args, "pose_points", False) or getattr(args, "pose_image", False)) else None
    flags = {"replace_subject": bool(getattr(args, "replace_subject", False)), "goal_as_image": getattr(args, "goal_as_image", "auto"),
             "body_only": bool(getattr(args, "body_only", False)), "edit_photo": getattr(args, "edit_photo", None),
             "layout_image": bool(getattr(args, "layout_image", False)), "pose_points": bool(getattr(args, "pose_points", False)),
             "pose_image": bool(getattr(args, "pose_image", False))}
    for opt in ("identity_bible", "build_sheet", "head_swap"):        # research options of 2026-10-07; absent = off, so older recipes compile unchanged
        if getattr(args, opt, False):
            flags[opt] = True
    res = {"goal": str(goal), "scene_text_base": scene_text, "scene_from": str(args.prompt).replace("\\", "/") if prompt_arg.is_file() else "inline text",
           "layout": layout, "pose": pose, "inventory": inv, "inventory_path": getattr(args, "inventory", None), "flags": flags}
    choice_text = R.scene_text_of(res)      # the text the face choice has always read: --prompt + layout + POSE POINTS

    def item(role, path, why, src=None, prep="fit2048_q95", **kw):
        p = Path(path)
        return {"role": role, "path": p, "name": p.name, "from": str(src if src is not None else p).replace("\\", "/"), "prep": prep, "why": why, **kw}

    def refs_of(names, role, why):
        out = []
        for n in names:
            if (refs_dir / n).exists() or (cache_dir / n).exists():
                out.append(item(role, prepare_ref(refs_dir / n, cache_dir), why, refs_dir / n))
        return out

    ch = None
    if getattr(args, "character", None):
        # a character (2026-10-08): the same face photos and the same body photo for every goal, and the character's description as the text
        import characters
        ch, _ = characters.load(args.character)
        problems = characters.check(ch)
        if problems:
            raise SystemExit("; ".join(problems))
        if getattr(args, "face_refs", None):
            raise SystemExit("--character and --face-refs both name the face photos: use one")
        res["character"] = {"ref": characters.ref_of(ch), "sha256": ch["sha256"], "description": ch.get("description")}
        roles = {**roles, "body": [r["name"] for r in characters.body(ch)], "arms": []}
    body = refs_of(roles.get("body", []), "body", f"character {characters.ref_of(ch)}: his true build" if ch else "subject_profiles.roles.body: his true build")
    phys_name = getattr(args, "physique", None)
    if phys_name:
        # --physique (the user's yardstick, 2026-10-10: "any shirtless picture will get the fully pumped version of mine, and casual outdoor
        # dressed versions will get the casual in-between version of my body"): the standard's approved photo is the BODY reference, with its
        # own build text, in place of the character's body photo. Absent = unchanged.
        stds = profile.get("physique") or {}
        std = stds.get(phys_name) if not phys_name.startswith("_") else None
        if not std:
            raise SystemExit(f"--physique {phys_name}: no such standard in facecard.json subject_profiles.{args.subject or 'me'}.physique "
                             f"({', '.join(k for k in stds if not k.startswith('_'))})")
        body = [item("body", prepare_ref(Path(f), cache_dir), f"physique {phys_name}: the user's yardstick of 2026-10-10", Path(f)) for f in std["files"]]
        res["physique"] = {"name": phys_name, "files": [Path(f).name for f in std["files"]], "label": std["label"], "build": std["build"]}
    arms = refs_of(roles.get("arms", []), "arms", "subject_profiles.roles.arms: his shoulders and arms")
    skip = {Path(n).stem for n in roles.get("body", []) + roles.get("arms", [])}
    choice: dict = {}
    angle_routed = get_generation_refs(config, refs_dir, cache_dir, scene_image_path=goal, prompt_text=choice_text, info=choice)
    face_paths = [r for r in angle_routed if r.stem not in skip][: int(getattr(args, "face_count", None) or roles.get("face_count", 4))]
    why_bin = f"head-pose bin {choice.get('bin')} ({choice.get('decided_by')}: {choice.get('evidence')})"
    # Whole-scene photos from his favourites ("_fav" in the name) go as head-and-shoulders crops: sent whole as a FACE reference, one was
    # edited instead of the PHOTO TO EDIT (slimming edit 2026-09-27: IMG_4861_fav_right returned his rocky boulder-and-dog photo).
    import replicate as _R
    faces = [(item("face", _R.head_ref_crop(r, None), why_bin + "; a _fav photo, sent as its head-and-shoulders crop", r, "head768_q95")
              if "_fav" in r.stem else item("face", r, why_bin, r)) for r in face_paths]
    if ch:
        faces = [item("face", prepare_ref(refs_dir / r["name"], cache_dir), f"character {characters.ref_of(ch)}: {r['slot'].replace('_', ' ')}",
                      refs_dir / r["name"]) for r in characters.faces_for(ch, "G")]
        choice = {"bin": None, "decided_by": f"character {characters.ref_of(ch)}", "evidence": "the same face photos for every goal",
                  "measured": choice.get("measured"), "angle_routed_would_have_been": [p.name for p in face_paths]}
    if getattr(args, "face_refs", None):
        # The user, 2026-10-02 (think-again): the angle-routed set always includes a _fav photo (IMG_5850_fav: glasses, short neat hair, a purple/yellow double exposure;
        # IMG_4861_fav_right: glasses, short hair) that contradicts his clean curly references; 139 renders never varied it. Name the exact photos instead.
        names, decided = args.face_refs, "names"
        if names.startswith("@"):
            preset = (config.get("face_ref_presets") or {}).get(names[1:])
            if not preset:
                raise SystemExit(f"--face-refs {names}: no such preset in facecard.json face_ref_presets ({', '.join(k for k in (config.get('face_ref_presets') or {}) if not k.startswith('_'))})")
            names, decided = ",".join(preset), f"preset {names}"
        faces = [item("face", prepare_ref(refs_dir / n.strip(), cache_dir), f"--face-refs {args.face_refs}", refs_dir / n.strip())
                 for n in names.split(",") if n.strip()]
        choice = {"bin": None, "decided_by": decided, "evidence": f"--face-refs {args.face_refs}", "measured": choice.get("measured")}
    res["face_choice"] = {**choice, "count": len(faces), "names": [f["name"] for f in faces]}

    # his own photo as the goal: included as the original photo to recreate (auto = his face scores as him against the face refs)
    own = args.goal_as_image == "yes"
    own_score = None
    if args.goal_as_image == "auto":
        try:
            sc = ArcFaceScorer()
            g = sc.embed(prepare_ref(goal, cache_dir))
            own_score = max(sc.similarity(g, sc.embed(f["path"])) for f in faces)
            # (identity_thresholds.own_min: the code read a 'thresholds' key that facecard.json never had; the value is 0.40 either way)
            own = own_score >= float(config.get("identity_thresholds", {}).get("own_min", 0.40))
        except Exception:
            own = False
    res.update({"own": own, "own_score": own_score})
    items: dict = {"faces": faces, "body": body, "arms": arms, "inv_refs": [], "props": []}
    res["items"] = items
    if flags.get("identity_bible"):
        res["identity_bible"] = (ROOT / "prompts" / "identity_bible.txt").read_text(encoding="utf-8").strip()
    if flags.get("build_sheet") and (body or arms):
        items["build_sheet"] = item("build_sheet", build_sheet_of([b["path"] for b in body + arms], cache_dir),
                                    "--build-sheet: his body and arm photos side by side as one reference (at most 4 images of him)",
                                    " + ".join(b["from"] for b in body + arms), "build_sheet")
    # --teeth (the user, 2026-10-18): his own teeth from his two REAL smile photos (subject_profiles.teeth_refs), sent after the inventory's own
    # references. Only for a goal whose man smiles or when the user asks (WHY); never the generated E2, never "whiter"; the words must say how
    # his mouth is, with his teeth showing (the teeth diagnosis of 2026-10-17: nothing had ever asked for them).
    teeth_items: list = []
    teeth_why = getattr(args, "teeth", None)
    if teeth_why:
        tr = (profile.get("teeth_refs") or {}).get("refs") or []
        if not tr:
            raise SystemExit(f"--teeth: no teeth_refs in facecard.json subject_profiles.{args.subject or 'me'}")
        # the words that are sent and ask for something: with an inventory its CHANGE ("make it ...") and KEEP lists and labels (the route text
        # then only picks the face photos), never what the goal shows now (a CHANGE item's "goal" side); without one, the route text
        words = (json.dumps({**inv, "change": [{k: v for k, v in c.items() if k != "goal"} for c in inv.get("change", [])]}, ensure_ascii=False)
                 if inv else scene_text)
        bad = re.search(r"(?<!never )(?<!not )\bwhit(?:er|en|ened)\b|closed[- ]lip\w*|lips (?:closed|together|pressed)|no teeth|teeth (?:hidden|not show\w*)",
                        words, re.I)
        if bad:
            raise SystemExit(f"--teeth: the route text or the inventory still says '{bad.group(0)}'. With --teeth his lips part and his own teeth show "
                             "as in his teeth photos, never whiter (the user, 2026-10-10: 'There is no need to change the color of the teeth')")
        if not re.search(r"\bteeth\b", words, re.I):
            raise SystemExit("--teeth: say how his mouth is in the CHANGE list (or the route text), e.g. 'his lips parted in his natural open smile, "
                             "his own upper teeth showing as in HIS TEETH, FRONT'")
        teeth_items = [item("inv_ref", prepare_ref(Path(r["path"]), cache_dir), f"--teeth ({teeth_why})", Path(r["path"]), label=r["label"],
                            key=r["key"]) for r in tr]
        res["teeth"] = {"because": teeth_why, "refs": [{"key": r["key"], "file": Path(r["path"]).name} for r in tr]}
    if inv and inv.get("mode") == "objects":
        items["inv_refs"] = [item("inv_ref", prepare_ref(ROOT / r["path"], cache_dir), "inventory reference", ROOT / r["path"], label=r["label"], key=r["key"])
                             for r in inv.get("refs", [])] + teeth_items
        items["photo_to_edit"] = item("photo_to_edit", prepare_ref(ROOT / inv["photo_to_edit"], cache_dir), "the inventory's photo_to_edit", ROOT / inv["photo_to_edit"])
        return res
    items["inv_refs"] = [item("inv_ref", prepare_ref(ROOT / r["path"], cache_dir), "inventory reference", ROOT / r["path"], label=r["label"], key=r["key"])
                         for r in (inv or {}).get("refs", [])] + teeth_items
    # Objects of his own, by role (the user, 2026-09-27: his Honda CB350 found in his photos, as the pin's motorcycle). PATH::LABEL.
    for spec in getattr(args, "prop", None) or []:
        path, _, label = spec.partition("::")
        items["props"].append(item("prop", prepare_ref(Path(path), cache_dir), "--prop", Path(path), label=label.strip(), arg=path))
    if layout and flags["layout_image"]:
        sketch, colour_key = layout_sketch(goal, layout, cache_dir)
        stick = False
        if pose and flags["pose_image"]:
            from PIL import Image as _Image
            with _Image.open(sketch) as im:
                im = im.convert("RGB")
                draw_pose(im, pose)
                sketch = cache_dir / f"layout_pose_sketch_{goal.stem}.png"
                im.save(sketch)
            stick = True
        items["sketch"] = item("layout_sketch", sketch, "--layout-image: the goal's layout boxes" + (" with its skeleton" if stick else ""), sketch,
                               "layout_sketch", colour_key=colour_key, stick=stick)
    replace = flags["replace_subject"]
    goal_role = flags["goal_as_image"] == "goal" and not replace
    if flags["edit_photo"]:
        items["edit_photo"] = item("edit_photo", prepare_ref(Path(flags["edit_photo"]), cache_dir), "--edit-photo: his own photo to edit", flags["edit_photo"])
    if goal_role:
        items["goal_image"] = item("goal_image", prepare_ref(goal, cache_dir), "--goal-as-image goal", goal)
    if replace:
        edit_src = (ROOT / inv["photo_to_edit"]) if inv and inv.get("photo_to_edit") else goal
        items["photo_to_edit"] = item("photo_to_edit", prepare_ref(edit_src, cache_dir),
                                      "the inventory's photo_to_edit" if inv and inv.get("photo_to_edit") else "the goal (--replace-subject)", edit_src)
    if own and not replace and not goal_role:
        items["original"] = item("original", prepare_ref(goal, cache_dir), "his own photo: the original to recreate", goal)
    return res


def build_sheet_of(paths: list[Path], cache_dir: Path, height: int = 1536, gap: int = 24) -> Path:
    """His body and arm photos side by side as ONE image (his real photos only, nothing generated), at one height with a white gap. Same inputs ->
    same bytes; the recipe freezes it by sha256 anyway."""
    ims = []
    for p in paths:
        with Image.open(p) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            ims.append(im.resize((round(im.width * height / im.height), height), Image.LANCZOS))
    sheet = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) - 1), height), (255, 255, 255))
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0))
        x += i.width + gap
    out = cache_dir / ("build_sheet_" + "_".join(Path(p).stem.replace(" ", "-") for p in paths) + ".jpg")
    sheet.save(out, "JPEG", quality=95)
    return out


def build_goal_request(config: dict, refs_dir: Path, cache_dir: Path, args) -> tuple[str, list[Path], list[Path], dict]:
    """Route G request: resolve_goal_inputs (files and decisions) + recipe.compile_route_g (the prompt; moved there unchanged on 2026-10-07).
    Returns (prompt, files in role order, face refs for scoring, log), exactly as before the split."""
    import recipe as R
    res = resolve_goal_inputs(config, refs_dir, cache_dir, args)
    profile = config.get("subject_profiles", {}).get(args.subject or "me", {})
    prompt, ordered, log, notices = R.compile_route_g(res, profile, ROLE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    for level, msg in notices:
        if level == "drop":
            print(f"NOTE: {msg}")
    return prompt, [it["path"] for it in ordered], [f["path"] for f in res["items"]["faces"]], log


GEN_ROUTE_ARGS = ["goal", "prompt", "inventory", "goal_as_image", "replace_subject", "body_only", "edit_photo", "layout_image", "pose_points",
                  "pose_image", "prop", "face_refs", "face_count", "subject", "identity_bible", "build_sheet", "head_swap", "character",
                  "restore_background", "physique", "teeth"]
REPLICATE_ARGS = ["zone", "source", "glasses", "look", "expression", "current_hair", "from_picture", "current_look", "expression_ref", "rank",
                  "loose_crop", "expression_ref_intro", "head_region"]


def cmd_character(args) -> int:
    """character new | show: the fixed reference photos and description of one man (characters.py, 2026-10-08)."""
    import characters
    if args.character_cmd == "show":
        return characters.show(args.ref)
    if not args.because:
        raise SystemExit("--because is required: say why this version exists")
    slots = {}
    for spec in args.face:
        slot, _, name = spec.partition("=")
        if slot not in characters.FACE_ORDER or not name:
            raise SystemExit(f"--face {spec!r}: use SLOT=NAME with SLOT one of {', '.join(characters.FACE_ORDER)}")
        slots[slot] = name
    desc = json.loads(Path(args.description).read_text(encoding="utf-8"))
    excluded = []
    for spec in args.exclude or []:
        name, _, why = spec.partition("::")
        excluded.append({"name": name.strip(), "why": why.strip()})
    ch = characters.new(args.name, slots, args.body, desc, excluded, args.because,
                        band_names=[n.strip() for n in args.band_from.split(",")] if args.band_from else None)
    path = characters.save_new(ch)
    print(f"character {characters.ref_of(ch)} written: {path}  sha {ch['sha256'][:12]}")
    return characters.show(str(path))


def cmd_recipe(args) -> int:
    """recipe new | bump | import-run | show: a recipe is the frozen method of one goal (recipe.py)."""
    import recipe as R
    if args.recipe_cmd == "show":
        return R.show(args.ref)
    if args.recipe_cmd == "new" and getattr(args, "method", "G") == "replicate":
        # replicate/1 (2026-10-08): his own photo, edited as a crop and pasted back, frozen like Route G
        import replicate_recipe
        if not args.because:
            raise SystemExit("--because is required: say why this version exists (the user's words, or the failed checklist item)")
        if not args.goal:
            raise SystemExit("recipe new --method replicate needs --goal (his own photo, full resolution)")
        rec = asyncio.run(replicate_recipe.freeze(args, because=args.because))
        path = R.save_new(rec)
        inp = rec["inputs"]
        print(f"recipe {rec['id']} v{rec['version']} written: {path}\n  method replicate/1, character {inp['character']['ref']}, {inp['source_kind']} photo "
              f"(pool {inp['own_score']}), zone {inp['zone']}, crop {inp['crop']}, expression {inp['expression']}\n  request {rec['lock']['request_sha256']}"
              f"  files {len(rec['lock']['files'])}  model {rec['method']['model']['label']} x{rec['method']['samples']} (max {rec['method']['max_attempts']} attempts)")
        if inp.get("place_from"):
            print(f"  placement pass: the head of {inp['place_from']['path']} (made by {inp['place_from'].get('recipe')}), a generated image: run only with the user's yes")
        return 0
    for opt in ("place_from", "eye_gate", "head_region"):
        if getattr(args, opt, None) and (args.recipe_cmd == "new" or R.load(args.ref)[0]["method"].get("route") != "replicate"):
            raise SystemExit(f"--{opt.replace('_', '-')} is a replicate/1 option (recipe new --method replicate, or recipe bump of a replicate/1 version)")
    if args.recipe_cmd == "import-run":
        bad = 0
        for rd in args.runs:
            out = R.import_run(Path(rd), because=args.because or "", check_only=args.check_only, samples=args.samples,
                               stop_after_fails=args.stop_after_fails, prompt_path=args.prompt)
            if args.check_only:
                bad += not (out and out.get("prompt_equal") and not out.get("problems"))
                continue
            if out is None:
                return 1
            if not args.because:
                raise SystemExit("--because is required: say why this version exists (the user's words, or the failed checklist item)")
            path = R.save_new(out)
            print(f"recipe {out['id']} v{out['version']} written: {path}\n  request {out['lock']['request_sha256']}  prompt {out['lock']['prompt_sha256'][:16]}"
                  f"  files {len(out['lock']['files'])}  model {out['method']['model']['label']}")
        if args.check_only:
            print(f"{len(args.runs) - bad}/{len(args.runs)} run(s) reproduce exactly from today's code and provable files")
        return 0 if not bad else 1
    if not args.because:
        raise SystemExit("--because is required: say why this version exists (the user's words, or the failed checklist item)")
    if args.recipe_cmd == "new":
        if not (args.goal and args.prompt):
            raise SystemExit("recipe new needs --goal and --prompt")
        args.count = args.samples or 2                                    # explicit in the recipe, never an implicit default at run time
        args.stop_after_fails = 2 if args.stop_after_fails is None else args.stop_after_fails
        rec = R.from_gen_args(args, because=args.because)
        path = R.save_new(rec)
        fc = rec["inputs"].get("face_choice") or {}
        print(f"recipe {rec['id']} v{rec['version']} written: {path}\n  request {rec['lock']['request_sha256']}  files {len(rec['lock']['files'])}"
              f"  face choice: bin {fc.get('bin')} decided by {fc.get('decided_by')}: {fc.get('evidence')}")
        if fc.get("warning"):
            print(f"  WARNING (face choice): {fc['warning']}")
        for lvl, msg in rec["origin"].get("notices") or []:
            print(f"  {lvl}: {msg}")
        return 0
    if args.recipe_cmd == "bump":
        old, _ = R.load(args.ref)
        given = {k: getattr(args, k) for k in GEN_ROUTE_ARGS if getattr(args, k, None) is not None}
        if old["method"].get("route") == "replicate" and getattr(args, "build_prompt", None):
            # a body pass's prompt version (2026-10-09: version 2 lets the clothes change); the frozen crop and build reading stay byte-identical
            import copy
            import provenance
            import replicate_recipe as RR
            if old["inputs"].get("zone") != "build":
                raise SystemExit("--build-prompt applies to a body pass (a replicate/1 recipe with --zone build)")
            rec = copy.deepcopy(old)
            n = int(args.build_prompt)
            rec["inputs"].update({"build_prompt": n, "body_judge": n, "expected_change": RR.expected_change(rec["inputs"].get("build_change"))})
            if n >= 2:      # a reflection of him (a second copy of his face, found as replicate finds it) gets the same new body
                import identity
                import replicate as RP
                from scorer import ArcFaceScorer
                sc = ArcFaceScorer()
                pool = identity.build_pool(load_config(), sc, verbose=False)
                img = RP.load_source(provenance.blob_path(old["goal"]["sha256"]))
                main = identity.score_image(img, pool, sc)
                copies = ([f for f in RP.find_identity_faces(img, sc, pool, main["emb"], identity.duplicates_of(main["emb"], pool))[1:]
                           if f.get("role") == "copy"] if main.get("detected") else [])
                rec["inputs"]["reflection"] = bool(copies)
            prompt = RR.compile_prompt(rec["inputs"])
            lock = dict(rec["lock"])
            lock.update({"prompt": prompt, "prompt_sha256": provenance.sha256_text(prompt), "compiled_with": RR.compiled_with()})
            if args.model:
                lock["model"] = args.model
                rec["method"]["model"] = R.model_record(args.model, load_config())
            lock["request_sha256"] = R.request_sha256(lock)
            rec.update({"version": R.next_version(old["id"]), "parent": f"v{old['version']}", "because": args.because, "lock": lock,
                        "created": datetime.now().isoformat(timespec="seconds"), "origin": {"kind": "bump", "from": f"v{old['version']}"}})
            if args.samples:
                rec["method"]["samples"] = args.samples
            if getattr(args, "max_attempts", None):
                rec["method"]["max_attempts"] = args.max_attempts
            print(f"{old['id']}: v{old['version']} -> v{rec['version']}\n" + R.lock_diff(old, rec))
            if args.dry_run:
                print("(dry run: nothing written)")
                return 0
            path = R.save_new(rec)
            print(f"written: {path}  request {rec['lock']['request_sha256']}")
            return 0
        if old["method"].get("route") == "replicate" and getattr(args, "eye_gate", None):
            # the eye gate (2026-10-12, pin 16): this version plus the gate; the lock is untouched, so the request is the same bytes
            import replicate_recipe as RR
            if given or any(getattr(args, k, None) is not None for k in REPLICATE_ARGS) or getattr(args, "build_prompt", None) \
                    or getattr(args, "place_from", None) or args.model:
                raise SystemExit("bump --eye-gate changes only the gate (with --samples and --max-attempts)")
            rec = RR.with_eye_gate(old, args.eye_gate, R.next_version(old["id"]), args.because)
            if args.samples:
                rec["method"]["samples"] = args.samples
            if getattr(args, "max_attempts", None):
                rec["method"]["max_attempts"] = args.max_attempts
            print(f"{old['id']}: v{old['version']} -> v{rec['version']}\n" + R.lock_diff(old, rec)
                  + f"\neye gate: {rec['inputs']['eye_gate']['band']}; max attempts {old['method'].get('max_attempts')} -> {rec['method'].get('max_attempts')}")
            if args.dry_run:
                print("(dry run: nothing written)")
                return 0
            path = R.save_new(rec)
            print(f"written: {path}  request {rec['lock']['request_sha256']}")
            return 0
        if old["method"].get("route") == "replicate" and getattr(args, "place_from", None):
            # the placement pass (2026-10-12, FAILURE_LOG F34): this version plus one reference, the given rendered head, before the photo to
            # edit; the crop, the readings and every other file stay byte-identical (nothing is read again)
            import replicate_recipe as RR
            if given or any(getattr(args, k, None) is not None for k in REPLICATE_ARGS) or getattr(args, "build_prompt", None):
                raise SystemExit("bump --place-from changes only the placement reference (with --model, --samples and --max-attempts)")
            rec = RR.with_placement(old, Path(args.place_from), R.next_version(old["id"]), args.because)
            if args.model:
                rec["lock"]["model"] = args.model
                rec["method"]["model"] = R.model_record(args.model, load_config())
                rec["lock"]["request_sha256"] = R.request_sha256(rec["lock"])
            if args.samples:
                rec["method"]["samples"] = args.samples
            if getattr(args, "max_attempts", None):
                rec["method"]["max_attempts"] = args.max_attempts
            print(f"{old['id']}: v{old['version']} -> v{rec['version']}\n" + R.lock_diff(old, rec))
            print(f"placement pass: the head of {rec['inputs']['place_from']['path']} (made by {rec['inputs']['place_from'].get('recipe')}), "
                  "a generated image: run only with the user's yes")
            if args.dry_run:
                print("(dry run: nothing written)")
                return 0
            path = R.save_new(rec)
            print(f"written: {path}  request {rec['lock']['request_sha256']}")
            return 0
        if old["method"].get("route") == "replicate" and (given or any(getattr(args, k, None) is not None for k in REPLICATE_ARGS)):
            raise SystemExit("a replicate/1 recipe changes its inputs only through `recipe new --method replicate` (it reads the photo again); "
                             "bump changes only --model, --samples and --max-attempts")
        method_only = not given
        if method_only:
            import copy
            rec = copy.deepcopy(old)
            rec.update({"version": R.next_version(old["id"]), "parent": f"v{old['version']}", "because": args.because,
                        "created": datetime.now().isoformat(timespec="seconds"), "origin": {"kind": "bump", "from": f"v{old['version']}"}})
            if args.model:
                rec["method"]["model"] = R.model_record(args.model, load_config())
                rec["lock"]["model"] = args.model
            if args.samples:
                rec["method"]["samples"] = args.samples
            if getattr(args, "max_attempts", None):
                rec["method"]["max_attempts"] = args.max_attempts
            if args.stop_after_fails is not None:
                rec["method"]["stop"]["after_pose_fails"] = args.stop_after_fails
            rec["lock"]["request_sha256"] = R.request_sha256(rec["lock"])
        else:
            import argparse as _ap
            merged = {**old["method"]["args"], **given}
            if given.get("character"):           # the character names the face photos: an older version's --face-refs / --face-count give way
                merged.update({"face_refs": None, "face_count": None})
            ns = _ap.Namespace(**merged, model=args.model or old["method"]["model"]["id"],
                               count=args.samples or old["method"]["samples"],
                               stop_after_fails=old["method"]["stop"]["after_pose_fails"] if args.stop_after_fails is None else args.stop_after_fails,
                               stop_on_pass=old["method"]["stop"].get("on_pass", False))
            rec = R.from_gen_args(ns, because=args.because, version=R.next_version(old["id"]), parent=f"v{old['version']}")
        print(f"{old['id']}: v{old['version']} -> v{rec['version']}\n" + R.lock_diff(old, rec))
        if args.dry_run:
            print("(dry run: nothing written)")
            return 0
        path = R.save_new(rec)
        print(f"written: {path}  request {rec['lock']['request_sha256']}")
        return 0
    return 2


async def cmd_run(args) -> int:
    import runner
    return await runner.run(args.ref, samples=args.samples, dry_run=args.dry_run, remeasure=args.remeasure, no_guard=args.no_guard,
                            no_wait=args.no_wait, wait_max=args.wait_max, stop_after_fails=args.stop_after_fails, verbose=args.verbose)


def cmd_diff(args) -> int:
    import report
    print(report.diff(Path(args.a), Path(args.b)))
    return 0


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

    if getattr(args, "goal", None):
        # Route G goes through the staged runner (2026-10-07): the flags become an ad-hoc recipe (resolved and frozen once, kept in the run's
        # 01_method/recipe.json and in .cache/adhoc_recipes/), so an exploratory run leaves the same 8 stages and report as a recipe run. Adopt a
        # good one as a recipe version with `facecard.py recipe import-run <run> --because "..."`. (The loop below now serves from-text gen only.)
        import recipe as R
        import runner
        rec = R.from_gen_args(args, because="ad-hoc gen (exploration): " + " ".join(sys.argv[2:]), adhoc=True)
        for level, msg in (rec.get("origin") or {}).get("notices") or []:
            if level == "drop":
                print(f"NOTE: {msg}")
        adhoc_dir = ROOT / ".cache" / "adhoc_recipes"
        adhoc_dir.mkdir(parents=True, exist_ok=True)
        rpath = adhoc_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{rec['id']}.json"
        rpath.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        return await runner.run(str(rpath), samples=args.count, dry_run=getattr(args, "dry_run", False), no_guard=getattr(args, "no_guard", False),
                                no_wait=getattr(args, "no_wait", False), wait_max=float(getattr(args, "wait_max", 21600.0)),
                                stop_after_fails=getattr(args, "stop_after_fails", 0), verbose=args.verbose)

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
    from credit_guard import Guard, GuardRefused

    candidates = []
    saved_count = 0
    guard, guard_refused = Guard(config.get("credit_guard")), False
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            print(f"Authenticated. account_status={client.account_status.name}")
            # Credits of every call (the user, 2026-09-27: what does one run folder cost, and can it cost less).
            credit_log = {"model": model, "start": credits_left(client), "calls": []}
            run_log["credits"] = credit_log
            last_left = [credit_log["start"]]
            print(f"[Credits] window left at start: {credit_log['start']}")

            if not getattr(args, "no_guard", False):
                # Credit guard (plan 2026-10-02): a free slot (<= 4 generations at once) and a window that can pay for this run, or wait for the reset.
                async def _fresh_reading():
                    try:
                        await client._fetch_usage_info()
                    except Exception:
                        pass
                    return credits_left(client)
                await guard.acquire(is_pro=(config.get("models") or {}).get(model) == "pro", images=args.count, label=run_dir.name, refresh=_fresh_reading,
                                    wait_max=0.0 if getattr(args, "no_wait", False) else float(getattr(args, "wait_max", 21600.0)))
                credit_log["start"] = credits_left(client)      # after a wait the window may have reset
                last_left[0] = credit_log["start"]

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
    except GuardRefused as e:
        guard_refused = True
        print(f"[Guard] refused, nothing was generated: {e}")
        run_log["status"] = "guard_refused"
        run_log["guard"] = str(e)
    finally:
        guard.release()
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
            # Light consistency (the user, 2026-10-02: pin 5 'lighting off, face seems lasso-ed in'): face light and face-vs-neck against the goal, written into run.json
            # and used to rank the candidates (a face brighter than its own neck than in the goal reads pasted in). Never a gate: a profile or hidden face is judged by eye.
            try:
                import lighting
                goal_img = lighting.read_bgr(args.goal)
                goal_kp = lighting.goal_keypoints(Path(args.goal), ROOT)
                for c in candidates:
                    r_kp, r_img = lighting.render_keypoints(c[1]), lighting.read_bgr(c[1])
                    if goal_img is None or goal_kp is None or r_kp is None or r_img is None:
                        continue
                    c[2]["light"] = lm = lighting.metrics(r_img, r_kp, goal_img, goal_kp)
                    print(f"  [Light] {c[1].name}: {lighting.describe(lm)}")
            except Exception as exc:   # never let a measurement stop a run
                print(f"  [Light] skipped: {exc}")
        # Pick best.jpg
        if candidates:
            # Sort by accepted status, then by light consistency (measured, when the face is measurable), then by identity score
            candidates.sort(key=lambda x: (1 if x[2].get("status") == "accepted" else 0, 1 if (x[2].get("light") or {}).get("ok") else 0, x[0]), reverse=True)
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

    if guard_refused:
        return 3
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
    gen.add_argument("--wait-max", type=float, default=21600.0, help="credit guard: the longest to wait for a free slot or for the window to refill, in seconds (default 6 h); then exit code 3, nothing generated")
    gen.add_argument("--no-wait", action="store_true", help="credit guard: do not wait, refuse at once (exit code 3) when no slot is free or the window cannot pay for this run")
    gen.add_argument("--no-guard", action="store_true", help="skip the credit guard (the old behaviour: start at once, no slot or window check)")
    gen.add_argument("--face-refs", default=None, help="Route G: the exact FACE reference photos to send, comma separated names from the references folder (replaces the angle-routed set, "
                     "which always contains a _fav photo of him with glasses or different hair)")
    gen.add_argument("--face-count", type=int, default=None, help="Route G: how many FACE reference photos of him to send (default: facecard.json roles.face_count = 4). "
                     "For a turned or profile goal the cut at 4 drops the two frontal anchors (IMG_6873, IMG_6858), the clearest photos of his face shape (2026-10-01, identity regression on pins 5 and 6)")
    gen.add_argument("--subject", default=None, help="Whose photo this is: a key of facecard.json subject_profiles (reference set and traits for scene-prompt-writer). Omit for the top-level reference set")
    gen.add_argument("--dry-run", action="store_true", help="Route G: stages 01-03 only (free): the request that would be sent, with its hash")
    gen.add_argument("--identity-bible", action="store_true", help="Route G: add prompts/identity_bible.txt (his frozen traits), stated first and repeated last")
    gen.add_argument("--build-sheet", action="store_true", help="Route G: send his body and arm photos as ONE side-by-side image")
    gen.add_argument("--head-swap", action="store_true", help="Route G with --replace-subject: word the edit as a whole-head swap")

    # recipes: the frozen method of one goal (recipe.py, 2026-10-07)
    rec_p = sub.add_parser("recipe", help="Recipes, the frozen method of one goal: new | bump | import-run | show", parents=[common])
    rsub = rec_p.add_subparsers(dest="recipe_cmd", required=True)

    def route_args(p, bump: bool = False):
        d = None if bump else argparse.SUPPRESS
        flag = (lambda: {"action": "store_const", "const": True, "default": None}) if bump else (lambda: {"action": "store_true"})
        p.add_argument("--goal", default=None, help="the goal picture")
        p.add_argument("--prompt", default=None, help="the route text file (scene-prompt-writer); with an inventory it only decides the face references")
        p.add_argument("--inventory", default=None, help="the element inventory JSON")
        p.add_argument("--goal-as-image", choices=["auto", "yes", "no", "goal"], default=None if bump else "no")
        p.add_argument("--replace-subject", **flag())
        p.add_argument("--body-only", **flag())
        p.add_argument("--edit-photo", default=None)
        p.add_argument("--layout-image", **flag())
        p.add_argument("--pose-points", **flag())
        p.add_argument("--pose-image", **flag())
        p.add_argument("--prop", action="append", default=None, help="PATH::LABEL, repeatable")
        p.add_argument("--face-refs", default=None, help="exact FACE photo names, or @preset")
        p.add_argument("--face-count", type=int, default=None)
        p.add_argument("--identity-bible", **flag(), help="add prompts/identity_bible.txt (his frozen traits), stated first and repeated last")
        p.add_argument("--build-sheet", **flag(), help="send his body and arm photos as ONE side-by-side image (with --face-count 3: 4 images of him)")
        p.add_argument("--head-swap", **flag(), help="replace-subject worded as a whole-head swap (face, hair, beard, ears), not only the person")
        p.add_argument("--restore-background", **flag(), help="after the run, copy the pin's own background pixels back around him (tools/background_restore.py, the user's "
                       "decision of 2026-10-09): only the two person silhouettes come from Gemini; the raw samples stay untouched, the copies are vN_0r.jpg")
        p.add_argument("--subject", default=None if bump else "me")
        p.add_argument("--character", default=None, help="the character (characters/<name>/vN.json, e.g. me@v1): the same face and body photos and "
                       "the same description for every goal")
        p.add_argument("--physique", default=None, help="the body for this goal by the user's yardstick (facecard.json subject_profiles.me.physique): "
                       "pumped-front | pumped-back | pumped-side for a shirtless picture, casual-front for a dressed one; replaces the character's "
                       "body photo and build text")
        p.add_argument("--teeth", default=None, metavar="WHY",
                       help="his own teeth for this goal: his two REAL smile photos (facecard.json subject_profiles.me.teeth_refs: IMG_6875 front, the "
                            "crop that made E2; IMG_3884 turned) go in as labelled references. Only for a goal whose man smiles or when the user asks: "
                            "WHY says which (the user, 2026-10-18). The CHANGE list or route text must say how his mouth is with his teeth showing; "
                            "closed-lip or 'whiter' wording is refused")
        p.add_argument("--model", default=None, help="model id (facecard.json models: e6fa609c3fa255c0 = pro, 56fdd199312815e2 = flash)")
        p.add_argument("--samples", type=int, default=None, help="pictures per run (default 2 for new); replicate: pictures that must pass")
        p.add_argument("--max-attempts", type=int, default=None, dest="max_attempts", help="replicate: the most edit calls per run (default max(6, 3 x samples))")
        p.add_argument("--stop-after-fails", type=int, default=None, help="stop a run after N pictures in a row fail the pose gate")
        p.add_argument("--because", default=None, help="REQUIRED: why this version exists (the user's words, or the failed checklist item)")
        # replicate/1 (his own photo): the method and its options
        p.add_argument("--zone", choices=["auto", "face", "head", "build", "expression"], default=None, help="replicate: what is redrawn (auto: own photo -> face with the whole head redrawn; build: his body only, pass A of a current-look own photo; expression: his own photo with only his expression changed, from --expression text and --expression-ref crops)")
        p.add_argument("--expression-ref", action="append", default=None, dest="expression_ref", metavar="PATH::LABEL",
                       help="replicate: a crop of his OWN expression (his best candid smile), sent after his face photos; repeatable (the user, 2026-10-10)")
        p.add_argument("--expression-ref-intro", default=None, dest="expression_ref_intro", metavar="TEXT",
                       help="replicate: what the --expression-ref images are, after 'Image N shows' (default: close crops of his own best candid smiles "
                            "from other photos); e.g. 'a photo of him smiling in this same session, the same light and camera.'")
        p.add_argument("--loose-crop", **flag(), dest="loose_crop",
                       help="replicate: frame the crop with his whole head at 62%% of it (replicate.expression_crop), as zone expression does; for a big "
                            "close face, whose usual crop holds the head at about 84%% and comes back re-composed (2026-10-10, IMG_3929 0 of 6)")
        p.add_argument("--rank", choices=["face", "smile"], default=None,
                       help="replicate: how passing pictures are ranked pair by pair (smile: the smile question; default face: the attractiveness question)")
        p.add_argument("--from-picture", default=None, help="replicate: edit this picture (a pass-A body picture, pinned by sha) instead of the original photo")
        p.add_argument("--place-from", default=None, dest="place_from", metavar="PICTURE",
                       help="replicate, opt-in: the placement pass (2026-10-12, FAILURE_LOG F34). The head of PICTURE (a vN_0.png of an earlier run: "
                            "cut from its raw return) goes in as ONE more reference just before the photo to edit, with the old rescue wording 'keep "
                            "the head at exactly the position, size, turn and tilt it has in the last image'. It is a generated image: only with the "
                            "user's yes. With bump: a copy of that version plus this reference, nothing read again")
        p.add_argument("--eye-gate", default=None, dest="eye_gate", metavar="SPEC",
                       help="replicate, opt-in (2026-10-12, pin 16): his eyes measured on every return (eye_measure.py) against bands from his real "
                            "photos at the same turn, e.g. 'yaw=24:34,vergence=-0.34:-0.18' (measures: yaw, vergence, ear_near, ear_far; LO:HI, "
                            "either side may be empty). Selects among returns, never moves a pixel, not in the prompt. With bump: a copy of that "
                            "version plus the gate (the same request)")
        p.add_argument("--head-region", default=None, dest="head_region", metavar="X0,Y0,X1,Y1",
                       help="replicate new, opt-in (2026-10-12, pin 14, FAILURE_LOG F43): fractions of the frame (0-1); only faces whose box "
                            "centre lies inside count as his head (the main face, its AI head box and any copy), e.g. when the body reads as a "
                            "larger face than a turned-away head. Recorded in the recipe; without it the largest face is the subject as before")
        p.add_argument("--current-look", **flag(), help="replicate: his own older photo made his CURRENT look: current haircut, lean current face, head size up to 1.10 for the beard")
        p.add_argument("--build-prompt", type=int, default=None, help="replicate body pass (bump): the prompt and judge version (2: the clothes may change, nothing else asked to stay but his head, pose and the scene)")
        p.add_argument("--source", choices=["auto", "own", "foreign"], default=None, help="replicate: is the photo his own (auto: pool score)")
        p.add_argument("--glasses", choices=["same", "yes", "no"], default=None, help="replicate: glasses (same = as the photo shows)")
        p.add_argument("--look", choices=["any", "curly", "short"], default=None, help="replicate: hair when the head is replaced")
        p.add_argument("--expression", default=None, help="replicate: same | auto | none | free text (default: auto for his own photo)")
        p.add_argument("--current-hair", **flag(), help="replicate: his current cut from the references (tapered sides), not the photo's own cut")

    rnew = rsub.add_parser("new", help="Resolve the references once, freeze every file into the blob store, compile and lock version 1 (or the next)")
    route_args(rnew)
    rnew.add_argument("--method", choices=["G", "replicate"], default="G", help="G: Route G (another man's photo, a pin). replicate: HIS OWN photo, "
                      "a crop edited and pasted back into the untouched original (Route G refuses his own photo)")
    rbump = rsub.add_parser("bump", help="A new version of a recipe with some inputs changed (prints what changed in the request)")
    rbump.add_argument("ref", help="recipe file, folder, or <goal key>[@vN]")
    route_args(rbump, bump=True)
    rbump.add_argument("--dry-run", action="store_true", help="print the change, write nothing")
    rimp = rsub.add_parser("import-run", help="Adopt a past gen run as a recipe, only if today's code reproduces its prompt from provable files")
    rimp.add_argument("runs", nargs="+")
    rimp.add_argument("--check-only", action="store_true", help="report whether each run reproduces; write nothing")
    rimp.add_argument("--because", default=None)
    rimp.add_argument("--samples", type=int, default=None)
    rimp.add_argument("--stop-after-fails", type=int, default=None)
    rimp.add_argument("--prompt", default=None, help="the route text the run used (default .cache/loop_prompts/<goal>_route.txt), for the face-choice record")
    rshow = rsub.add_parser("show", help="Versions of a recipe, their request hashes and their track record")
    rshow.add_argument("ref")

    ch_p = sub.add_parser("character", help="Characters, the fixed reference photos and description of one man: new | show", parents=[common])
    csub = ch_p.add_subparsers(dest="character_cmd", required=True)
    cnew = csub.add_parser("new", help="Freeze a new character version (the next vN)")
    cnew.add_argument("--name", default="me")
    cnew.add_argument("--face", action="append", required=True, help="SLOT=NAME, SLOT one of front, three_quarter_left, three_quarter_right, profile")
    cnew.add_argument("--body", action="append", required=True, help="his full-length body photo (repeatable)")
    cnew.add_argument("--description", required=True, help="JSON file {face, hair, beard, skin, build}: what the photos show")
    cnew.add_argument("--exclude", action="append", default=None, help="NAME::why, a photo used before and left out")
    cnew.add_argument("--band-from", default=None, help="comma-separated photos of him the measure band is taken from (default: the character's own)")
    cnew.add_argument("--because", default=None)
    cshow = csub.add_parser("show")
    cshow.add_argument("ref", help="<name>[@vN] or a character file")

    run_p = sub.add_parser("run", help="Run a recipe through the 8 fixed stages (runner.py); a run folder re-sends that run's exact request", parents=[common])
    run_p.add_argument("ref", help="a recipe file or folder, <goal key>[@vN] (e.g. pin_783485666539777054@v1), or a staged run folder")
    run_p.add_argument("--samples", type=int, default=None, help="pictures this run (default: the recipe's)")
    run_p.add_argument("--stop-after-fails", type=int, default=None, help="default: the recipe's")
    run_p.add_argument("--dry-run", action="store_true", help="stages 01-03 only (free): proves the request is the recipe's, byte for byte")
    run_p.add_argument("--remeasure", default=None, metavar="RUN", help="no Gemini call: measure, review and rank the pictures of RUN again")
    run_p.add_argument("--wait-max", type=float, default=21600.0, help="credit guard: longest wait in seconds (default 6 h), then exit 3")
    run_p.add_argument("--no-wait", action="store_true", help="credit guard: refuse at once instead of waiting")
    run_p.add_argument("--no-guard", action="store_true", help="skip the credit guard (only when the user said so)")
    diff_p = sub.add_parser("diff", help="What differs between two runs, stage by stage: the request, the code, the outcomes")
    diff_p.add_argument("a")
    diff_p.add_argument("b")

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
        "recipe": cmd_recipe,
        "character": cmd_character,
        "diff": cmd_diff,
    }
    if args.command in sync_handlers:
        return sync_handlers[args.command](args)
    async_handlers = {"check": cmd_check, "models": cmd_models, "gen": cmd_gen, "replicate": cmd_replicate, "run": cmd_run}
    hold = Path(__file__).resolve().parent / ".cache" / "GENERATION_HOLD"
    if hold.exists() and args.command in ("gen", "replicate", "run") and not getattr(args, "dry_run", False):
        # the user, 2026-10-17: "Do not generate any more images": nothing that calls Gemini for a picture starts while the hold file exists.
        # One exception, set per run and never in a task: FACECARD_HOLD_PASS="<recipe ref>::<the user's words>" lets exactly that one recipe run
        # (the user, 2026-10-19: "Run pin 8 now"); the hold file stays, so everything else is still held.
        import os
        pass_ref, _, pass_words = os.environ.get("FACECARD_HOLD_PASS", "").partition("::")
        if args.command == "run" and pass_ref and pass_ref == getattr(args, "ref", None) and pass_words.strip():
            print(f"HOLD lifted by the user for this one run only: {args.ref} ({pass_words.strip()[:160]})", file=sys.stderr)
        else:
            print(f"HOLD: image generation is stopped by the user ({hold.read_text(encoding='utf-8', errors='replace').strip()[:200]}); "
                  f"remove {hold} only on the user's word", file=sys.stderr)
            return 6
    return asyncio.run(async_handlers[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
