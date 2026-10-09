"""Free pre-flight check of an element inventory, before any Gemini credit is spent (plan approved 2026-10-02, step 3). Each rule is a lesson that cost real credits:

    .venv\\Scripts\\python.exe tools\\inventory_lint.py <inventory.json> [--face-count N]

  ERROR  the photo to edit does not exist; more than 10 files would be sent (the Gemini app takes at most 10 per prompt)
  WARN   the goal is cropped by the left, right or top edge and no keep line names the FRAMING (pin 3: the man was re-centred, 2 renders lost)
  WARN   the keep list says 'exactly as in the PHOTO TO EDIT' about the head or arms while the PHOTO TO EDIT is the goal itself (it hands the goal's own man back; pins 6 and 9)
  NOTE   'never closer / never zoomed' on a close crop (it handed the goal back on pin 6, worked on pins 3 and 9): check the difference to the goal after the first render
  WARN   the build item has no measure (thinner / narrower / loose / flat ...): a build sentence alone is ignored (pins 3, 9)
  WARN   the goal's head is bowed steeply (bow >= 0.7) and no keep line asks for a DEEPER bow than the goal's (renders land about 0.12 short; pin 9)
  NOTE   the goal's face is hidden or bowed past ArcFace: identity cannot be scored, judge hair, beard and the pasted-in look by eye (tools/audit_views.py)
  NOTE   no keep line names the background PEOPLE (checklist item 33: the user, 2026-10-09, "humans in the background are hard to handle and adding more makes it more complex"):
         write one even when there are none ("no other person in the frame")
  NOTE   no keep line names the LETTERING / signs / screens (item 34: "same goes for text in AI images"): write one even when there is none ("no other text")

    .venv\\Scripts\\python.exe tools\\inventory_lint.py --scene <scene paragraph .txt>      (a text-mode recipe's scene, item 33/34/35)
  WARN   the paragraph names crowds, shoppers, passers-by, a busy place, people other than him, or readable shop names (the setting is written empty; signs are unreadable glow)
  NOTE   no candid capture words (motion blur, handheld, tilt, grain, off-centre): item 35, unless the user asked for a polished look
Exit code 0 = clean, 1 = warnings, 2 = errors.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASURE = re.compile(r"thin|narrow|loose|flat|slim|third|fifth|quarter|barely thicker|gape|baggy|visible", re.I)
PEOPLE_WORDS = re.compile(r"\b(people|person|persons|crowd|passers?-?by|bystanders?|companions?|friends?|child|children|someone|nobody|no one|man in|men in|woman|women)\b", re.I)
TEXT_WORDS = re.compile(r"\b(lettering|letters|text|texts|sign|signs|signage|wording|logo|logos|label|labels|caption|screens?|writing|words|inscription|print)\b", re.I)
CROWD_WORDS = re.compile(r"\b(crowd(ed|s)?|shoppers?|passers?-?by|people|pedestrians?|bystanders?|busy|bustling|visitors|customers|families|other (men|women|people))\b", re.I)
SHOP_WORDS = re.compile(r"\b(shop names?|store names?|brand names?|neon signs? reading|signs? (that )?(read|reading|says?)|storefront lettering|readable signs?|shop signs? (with|reading))\b", re.I)
CANDID_WORDS = re.compile(r"motion blur|handheld|hand-held|tilt|grain|off-centre|off-center|caught in a rush|candid", re.I)


def goal_pose(inv: dict) -> dict | None:
    g = inv.get("goal")
    if not g:
        return None
    p = ROOT / ".cache" / "poses" / (Path(g).stem + ".json")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def lint(inv: dict, face_count: int = 4, files: int | None = None) -> list[tuple[str, str]]:
    """`files`: the exact number of files a recipe sends (its lock); otherwise estimated from the face count."""
    out: list[tuple[str, str]] = []
    pte = inv.get("photo_to_edit")
    if not pte or not (ROOT / pte).exists():
        out.append(("ERROR", f"photo_to_edit missing or not found: {pte}"))
    if files is None:
        files = face_count + 1 + 1 + len(inv.get("refs", [])) + 1          # faces + body + arms + inventory refs + the photo to edit
    if files > 10:
        out.append(("ERROR", f"{files} files would be sent (limit 10): lower --face-count or drop inventory refs"))
    keep = [str(k) for k in inv.get("keep", [])]
    change = inv.get("change", [])
    own_render = bool(pte) and str(pte).replace("\\", "/").startswith("outputs/")        # stage 2: an earlier render of HIM, not the goal's man
    pose = goal_pose(inv)
    if pose and pose.get("person"):
        box = pose["person"].get("box") or [0, 0, 1, 1]          # x0, y0, x1, y1 as shares of the frame
        cropped = box[0] < 0.02 or box[2] > 0.98 or box[1] < 0.02
        if cropped and not any("framing" in k.lower() for k in keep):
            out.append(("WARN", f"the goal is cropped by the frame edge (box {[round(v, 2) for v in box]}) but no keep line names the FRAMING (head position, which edge cuts him)"))
        kp = pose["person"].get("kp") or {}
        eyes = [kp.get(k) for k in ("nose", "l_eye", "r_eye")]
        if all(e and e[2] >= 0.3 for e in eyes):
            ed = math.hypot(eyes[1][0] - eyes[2][0], eyes[1][1] - eyes[2][1])
            bow = (eyes[0][1] - (eyes[1][1] + eyes[2][1]) / 2) / max(ed, 1e-6)
            if bow >= 0.7 and not any(re.search(r"more steep|deeper|steeper", k, re.I) for k in keep):
                out.append(("WARN", f"the goal's head bow is {bow:.2f} (steep) and no keep line asks for a bow DEEPER than the goal's (renders land ~0.12 short)"))
        else:
            out.append(("NOTE", "the goal's face is hidden or bowed past the keypoints: identity cannot be scored; judge hair, beard and the pasted-in look by eye (tools/audit_views.py)"))
    if not own_render:
        for k in keep:
            if re.search(r"(head|arm)[^.]{0,120}exactly as (it is )?in the PHOTO TO EDIT", k, re.I):
                out.append(("WARN", f"keep line hands the goal's own man back: '{k[:90]}...'"))
    if pose and pose.get("person") and not own_render:
        box = pose["person"].get("box") or [0, 0, 1, 1]
        area = (box[2] - box[0]) * (box[3] - box[1])
        if area > 0.4 and any(re.search(r"never (closer|zoomed)", k, re.I) for k in keep):
            out.append(("NOTE", "a 'never closer / never zoomed' framing line on a CLOSE crop returned the goal's own man on pin 6 (it worked on pins 3 and 9): after the first render check the "
                                "mean difference to the goal (below ~10 with the face still his = the goal handed back, reject it)"))
    for c in change:
        if str(c.get("item", "")).lower() in ("build", "arms"):
            if not MEASURE.search(str(c.get("his", ""))):
                out.append(("WARN", f"the {c['item']} item has no measure (thinner / narrower / loose / flat ...): a build sentence alone is ignored"))
    # The user, 2026-10-09 (checklist items 33 and 34): background people and text are where an edit goes wrong, so every inventory says what happens to them
    if not any(PEOPLE_WORDS.search(k) for k in keep):
        out.append(("NOTE", "no keep line names the background PEOPLE (item 33): write one, even 'no other person in the frame'; the goal's own people stay as they are"))
    if not any(TEXT_WORDS.search(k) for k in keep):
        out.append(("NOTE", "no keep line names the LETTERING, signs or screens (item 34): write one, even 'no other text'; every goal text stays letter for letter"))
    return out


def lint_scene(text: str) -> list[tuple[str, str]]:
    """A text-mode recipe's scene paragraph (no goal is sent): the setting is written empty, signs are unreadable glow, and the picture is a candid snapshot."""
    out: list[tuple[str, str]] = []
    for m in CROWD_WORDS.finditer(text):
        out.append(("WARN", f"the scene names people or a busy place ('{m.group(0)}'): item 33, the setting is written with no one in it but him"))
    for m in SHOP_WORDS.finditer(text):
        out.append(("WARN", f"the scene names readable signs or shop names ('{m.group(0)}'): item 34, signs are soft unreadable glow unless the user asked for the words"))
    if not CANDID_WORDS.search(text):
        out.append(("NOTE", "no candid capture words (motion blur, handheld, tilt, grain, off-centre): item 35, unless the user asked for a polished look"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inventory", nargs="?")
    ap.add_argument("--face-count", type=int, default=4)
    ap.add_argument("--scene", default=None, help="lint a text-mode scene paragraph (.txt) instead of an inventory")
    a = ap.parse_args()
    if a.scene:
        findings = lint_scene(Path(a.scene).read_text(encoding="utf-8"))
        for level, msg in findings:
            print(f"  {level}: {msg}")
        if not findings:
            print("  clean")
        return 1 if any(l == "WARN" for l, _ in findings) else 0
    if not a.inventory:
        ap.error("an inventory (or --scene <file>) is required")
    inv = json.loads(Path(a.inventory).read_text(encoding="utf-8"))
    files = None
    if inv.get("schema", "").startswith("facecard.recipe/"):          # a recipe: lint its embedded inventory, with the exact number of files it sends
        files = len(inv["lock"]["files"])
        inv = (inv["inputs"].get("inventory") or {}).get("data") or {}
        if not inv:
            print("  this recipe has no inventory")
            return 0
    findings = lint(inv, a.face_count, files=files)
    for level, msg in findings:
        print(f"  {level}: {msg}")
    if not findings:
        print("  clean")
    return 2 if any(l == "ERROR" for l, _ in findings) else (1 if any(l == "WARN" for l, _ in findings) else 0)


if __name__ == "__main__":
    sys.exit(main())
