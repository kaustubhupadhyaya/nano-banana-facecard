"""Characters: ONE frozen set of his reference photos and ONE description, used by every recipe (the user, 2026-10-08: "if I make you generate
10 images of the same character using the same reference images, all should look the same").

A character version is one immutable file, characters/<name>/v<N>.json, tracked in git (text only):
  references  the fixed photos by role (face: front, three-quarter left, three-quarter right, profile; body), each with sha256 (blob store),
              the date it was taken, the measured head turn, and why it is in the set
  excluded    photos that were used before and are not in the set, each with the reason
  description his face, hair, beard, skin and build in words read from these photos (no wish words: the text must agree with the photos)
  band        each record-only face / body measure (character.py) as min..max over his own photos: "the same man" in numbers
What each method sends from it is fixed here too (faces_for): Route G sends 3 faces + the body photo (4 images of him), replicate the 4 faces.
A change is a new version (`facecard.py character bump`), never an edit. Measured why (2026-10-08 survey): the face set changed with every goal
(11 sets in 79 runs), a January photo with fuller arms and short hair was sent beside the slim September body photo in 76 runs, and the build text
contradicted the photos.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import provenance as P

ROOT = Path(__file__).resolve().parent
CHARACTERS = ROOT / "characters"
SCHEMA = "facecard.character/1"
FACE_ORDER = ("front", "three_quarter_left", "three_quarter_right", "profile")
ROUTE_G_FACES = ("front", "three_quarter_left", "three_quarter_right")    # + the body photo = 4 images of him (Nano Banana 2.1: up to 4 per character)


def ref_path(name: str, config: dict | None = None) -> Path | None:
    """A reference photo by file name: the originals folder first, then the prepared copies in .cache/refs."""
    import facecard
    config = config or facecard.load_config()
    for base in (facecard.get_refs_dir(config), ROOT / config.get("cache_dir", ".cache/refs")):
        if (base / name).is_file():
            return base / name
    return None


def taken_on(path: Path) -> str | None:
    from PIL import Image
    try:
        with Image.open(path) as im:
            ex = im.getexif()
            dt = (ex.get_ifd(0x8769) or {}).get(36867) or ex.get(306)
    except Exception:
        return None
    return str(dt).replace(":", "-", 2) if dt else None


def describe_ref(name: str, role: str, slot: str | None, why: str, config: dict | None = None) -> dict:
    import headpose
    p = ref_path(name, config)
    if p is None:
        raise SystemExit(f"reference photo {name!r} not found in the references folder or .cache/refs")
    hp = headpose.measure(p)
    r = {"role": role, "name": name, "sha256": P.put_file(p), "from": str(p).replace("\\", "/"), "taken": taken_on(p),
         "head_pose": {k: hp.get(k) for k in ("detected", "yaw", "pitch", "roll", "side")}, "why": why}
    if slot:
        r["slot"] = slot
    return r


def char_dir(name: str) -> Path:
    return CHARACTERS / re.sub(r"[^a-z0-9_-]+", "-", name.lower())


def versions(d: Path) -> list[Path]:
    return sorted((p for p in Path(d).glob("v*.json") if re.fullmatch(r"v\d+\.json", p.name)), key=lambda p: int(p.stem[1:]))


def load(ref: str) -> tuple[dict, Path]:
    """'<name>[@vN]' or a character file."""
    p = Path(ref)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8")), p
    m = re.fullmatch(r"(.+?)(?:@v(\d+))?", str(ref))
    d = char_dir(m.group(1))
    vs = versions(d)
    if not vs:
        raise SystemExit(f"no character {m.group(1)!r} (looked in {d})")
    path = d / f"v{m.group(2)}.json" if m.group(2) else vs[-1]
    if not path.is_file():
        raise SystemExit(f"character {m.group(1)} has no version v{m.group(2)}")
    return json.loads(path.read_text(encoding="utf-8")), path


def ref_of(ch: dict) -> str:
    return f"{ch['name']}@v{ch['version']}"


def faces(ch: dict) -> list[dict]:
    order = {s: i for i, s in enumerate(FACE_ORDER)}
    return sorted((r for r in ch["references"] if r["role"] == "face"), key=lambda r: order.get(r.get("slot"), 99))


def body(ch: dict) -> list[dict]:
    return [r for r in ch["references"] if r["role"] == "body"]


def faces_for(ch: dict, method: str) -> list[dict]:
    """The face photos a method sends, always the same ones: Route G the first three slots (with the body photo, 4 images of him), replicate all four."""
    fs = faces(ch)
    return [r for r in fs if r.get("slot") in ROUTE_G_FACES] if method == "G" else fs


def description_text(ch: dict, part: str) -> str:
    """'face' = face + hair + beard + skin (the FACE section), 'build' = his build (the BUILD section)."""
    d = ch.get("description") or {}
    if part == "build":
        return str(d.get("build") or "").strip()
    return " ".join(str(d.get(k) or "").strip() for k in ("face", "hair", "beard", "skin") if d.get(k)).strip()


def sha256_of(ch: dict) -> str:
    """The identity of a character version: its references (role, name, sha256) and description."""
    return P.sha256_bytes(P.canonical_json({"references": [[r["role"], r["name"], r["sha256"]] for r in ch["references"]],
                                            "description": ch.get("description")}))


def measure_band(names: list[str], config: dict | None = None) -> tuple[dict | None, list[dict]]:
    """min..max of every record-only measure (character.py) over these photos of him; (None, []) when the measures module is not available.
    The photos are the same-session studio set + his body photo, not only the sent four: three of those are turned past the 25 degrees the face
    measures need (2026-10-08 audit), so a band from them alone would rest on one face."""
    try:
        import character
    except Exception:
        return None, []
    ms, used = [], []
    for n in names:
        p = ref_path(n, config)
        if p is not None:
            ms.append(character.measure(p))
            used.append({"name": n, "sha256": P.sha256_file(p)})
    return (character.band(ms) if ms else None), used


def new(name: str, slots: dict[str, str], body_names: list[str], description: dict, excluded: list[dict], because: str,
        parent: str | None = None, band_names: list[str] | None = None) -> dict:
    import facecard
    config = facecard.load_config()
    refs = [describe_ref(n, "face", s, f"the fixed {s.replace('_', ' ')} photo of the current look", config) for s, n in slots.items()]
    refs += [describe_ref(n, "body", None, "his true build in the current look: standing, full length", config) for n in body_names]
    d = char_dir(name)
    v = int(versions(d)[-1].stem[1:]) + 1 if versions(d) else 1
    ch = {"schema": SCHEMA, "name": name, "version": v, "created": datetime.now().isoformat(timespec="seconds"), "because": because,
          "parent": parent, "references": refs, "excluded": excluded, "description": description,
          "sends": {"G": [r["name"] for r in faces_for({"references": refs}, "G")] + [r["name"] for r in refs if r["role"] == "body"],
                    "replicate": [r["name"] for r in faces_for({"references": refs}, "replicate")]}}
    band, used = measure_band(band_names or [r["name"] for r in refs], config)
    ch["band"], ch["band_from"] = band, used
    ch["sha256"] = sha256_of(ch)
    return ch


def save_new(ch: dict) -> Path:
    d = char_dir(ch["name"])
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"v{ch['version']}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(ch, indent=1, ensure_ascii=False) + "\n")
    return path


def check(ch: dict) -> list[str]:
    """Problems that stop a run: a hand-edited character, or a missing / changed blob."""
    out = []
    if sha256_of(ch) != ch.get("sha256"):
        out.append(f"character {ref_of(ch)} was edited by hand (its sha256 no longer matches its references and description)")
    for r in ch["references"]:
        p = P.blob_path(r["sha256"])
        if p is None or P.sha256_file(p) != r["sha256"]:
            out.append(f"character {ref_of(ch)}: {r['name']} blob {r['sha256'][:12]} missing or changed")
    return out


def show(ref: str) -> int:
    ch, path = load(ref)
    print(f"{ref_of(ch)}  ({path.relative_to(ROOT) if ROOT in path.resolve().parents else path})  sha {ch['sha256'][:12]}")
    print(f"  because: {ch.get('because')}")
    for r in ch["references"]:
        hp = r.get("head_pose") or {}
        print(f"  {r['role']:4s} {r.get('slot') or '':20s} {r['name']:22s} taken {r.get('taken') or '?':19s} yaw {hp.get('yaw')} pitch {hp.get('pitch')}  {r['sha256'][:12]}")
    print(f"  Route G sends: {', '.join(ch['sends']['G'])}")
    print(f"  replicate sends: {', '.join(ch['sends']['replicate'])}")
    for e in ch.get("excluded") or []:
        print(f"  excluded {e['name']}: {e['why']}")
    for k, v in (ch.get("description") or {}).items():
        print(f"  {k}: {v}")
    if ch.get("band"):
        print(f"  band: {json.dumps(ch['band'], ensure_ascii=False)[:600]}")
    return 0
