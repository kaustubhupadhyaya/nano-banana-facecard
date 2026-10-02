"""Where every goal stands, and what to change next. The loop-until-perfect rule of the gemini-identity-gen skill (the user, 2026-10-01: "when you
already know exactly which one is failing, then why did you stop? keep running until a perfect outcome is generated") is driven by this table:
a goal is DONE only when a picture of it passed all 30 checklist items (or the user accepted it); every other goal is OPEN and gets another wave.

    .venv\\Scripts\\python.exe tools\\goal_status.py            all goals in results_names.json
    .venv\\Scripts\\python.exe tools\\goal_status.py --open      only the goals that still need work (exit code 1 while any is open)

Per open goal it prints: attempts so far, what failed most in the last attempts, what has already been tried (models, inventory variants), the closest
picture, and the fix that the ledger's lessons say belongs to each failed item. Nothing here judges a picture: the 30 items are still checked by eye
(tools\\best_check.py), and a threshold or gate is never loosened to make a goal DONE.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

# failed checklist item -> what to change in the NEXT request (only the section that controls it; each line is a lesson from FEEDBACK_LEDGER.md)
RECIPES = {
    12: "head pose: write the pose gate's own numbers (head bow, turn, tilt) as geometry in the first keep line, never 'exactly as in the PHOTO TO EDIT'; try the other model (Flash <-> Pro)",
    14: "position: first keep line = the measured FRAMING from .cache/poses/<goal>.json (shoulder / head / hip positions as % of the frame, torso share of the height)",
    29: "camera distance: same measured FRAMING line, plus 'the camera is as far as in the PHOTO TO EDIT, never closer, his head no bigger'",
    30: "posture: --pose-points is dropped when an inventory is used; put the measured limb facts into the keep list; compare against the pose overlay limb by limb",
    21: "identity: Pro model; the sharp-face keep line (real skin texture, pores, beard hairs, never smoothed); more samples; a bowed or profile face cannot be scored, so judge hair, beard, jaw, nose, ears by eye at zoom and report the number",
    26: "physique / accessories / eyewear: slim-build measure line ('upper arm barely thicker than his forearm, flat chest, narrow waist; the pin man's broad shoulders and big arms are not his'); name every accessory and colour; 'eyes open in the shadow of his curls, no glasses'",
    19: "the pin man came back unchanged: remove 'exactly as in the PHOTO TO EDIT' about head or arms; describe pose in geometry; name that all his hair is his",
    23: "the source came back as is: same fix as 19",
    28: "his face, hair and beard must come from the references: say so in the change list and keep the FACE references first",
    6: "head too big (hair a ball): say 'curls sit close to the head, no bigger than the pin man's hairstyle'",
    8: "something unreal: regenerate; check hands and the head-neck join at full zoom",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--open", action="store_true", help="only goals that are not DONE; exit code 1 while any is open")
    args = ap.parse_args()
    names = {k: v for k, v in json.loads((ROOT / "results_names.json").read_text(encoding="utf-8")).items() if isinstance(v, dict)}
    rows = json.loads((ROOT / "feedback_ledger.json").read_text(encoding="utf-8")).get("rows", {}) if (ROOT / "feedback_ledger.json").exists() else {}
    from export_results import base_name
    n_open = 0
    for key in sorted(names, key=lambda k: names[k].get("number", 0)):
        base = base_name(key)
        rs = sorted((r for r in rows.values() if r["goal"] == base), key=lambda r: (r["time"], r["file"]))
        done = [r for r in rs if r["result"].startswith("PASS")]
        if done:
            if not args.open:
                print(f"DONE  {base}: {len(rs)} attempts, passed by {done[-1]['run']}/{done[-1]['file']}")
            continue
        n_open += 1
        checked = [r for r in rs if r["result"].startswith("FAIL (checklist)")]
        gate = [r for r in rs if r["result"].startswith("FAIL (pose gate")]
        last = checked[-8:]
        hist = Counter(i for r in last for i in r.get("failed_items", []))
        tried = sorted({f"{r.get('model') or '?'}:{r.get('inventory') or '?'}" for r in rs if r.get("inventory")})
        print(f"OPEN  {base}: {len(rs)} attempts ({len(checked)} judged, {len(gate)} failed the pose gate only, {len(rs) - len(checked) - len(gate)} not judged yet)")
        if hist:
            print("      failed most (last judged): " + ", ".join(f"item {i} x{c}" for i, c in hist.most_common()))
        if tried:
            print("      already tried (model:inventory): " + "; ".join(tried))
        if checked:
            best = min(checked, key=lambda r: (len(r.get("failed_items", [])), r.get("pose_gate") != "PASS"))
            print(f"      closest: {best['run']}/{best['file']} fails {best.get('failed_items')}")
        for i, _ in hist.most_common(3):
            print(f"      next for item {i}: {RECIPES.get(i, 'read its row in BEST_CHECKLIST.md and change only the request section that controls it')}")
        if not hist and gate:
            print("      next: every attempt failed the pose gate: " + RECIPES[14])
    print(f"\n{n_open} open goal(s)." + ("  Keep going: another wave for each, in parallel." if n_open else "  Every goal has a picture that passed."))
    return 1 if n_open else 0


if __name__ == "__main__":
    sys.exit(main())
