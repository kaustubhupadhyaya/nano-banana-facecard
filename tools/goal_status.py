"""Where every goal stands, and what to change next. The loop-until-perfect rule of the gemini-identity-gen skill (the user, 2026-10-01: "when you
already know exactly which one is failing, then why did you stop? keep running until a perfect outcome is generated") is driven by this table:
a goal is DONE only when a picture of it passed all 35 checklist items (or the user accepted it); every other goal is OPEN and gets another wave.

    .venv\\Scripts\\python.exe tools\\goal_status.py            all goals in results_names.json
    .venv\\Scripts\\python.exe tools\\goal_status.py --open      only the goals that still need work (exit code 1 while any is open)

Per open goal it prints: attempts so far, what failed most in the last attempts, what has already been tried (models, inventory variants), the closest
picture, and the fix that the ledger's lessons say belongs to each failed item. Nothing here judges a picture: the 35 items are still checked by eye
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

# failed checklist item -> what to change in the NEXT request (only the section that controls it; each line is a lesson from FEEDBACK_LEDGER.md).
# (Named FIXES since 2026-10-07: a 'recipe' is now the frozen method of a goal, recipes/<collection>/<NN>-<title>/v<N>.json.)
FIXES = {
    12: "head pose: write the pose gate's own numbers (head bow, turn, tilt) as geometry in the first keep line, never 'exactly as in the PHOTO TO EDIT'; try the other model (Flash <-> Pro)",
    14: "position: first keep line = the measured FRAMING from .cache/poses/<goal>.json (shoulder / head / hip positions as % of the frame, torso share of the height)",
    29: "camera distance: same measured FRAMING line, plus 'the camera is as far as in the PHOTO TO EDIT, his head no bigger' (on a CLOSE crop a 'never closer' line returned the goal's man on pin 6: check the difference to the goal)",
    30: "posture: --pose-points is dropped when an inventory is used; put the measured limb facts into the keep list; compare against the pose overlay limb by limb",
    21: "identity: ASK THE USER what looks off, in their words, before optimising (pin 5: ArcFace was chased for ~10 attempts, the complaint was lighting); ArcFace on one pose is a lottery "
        "(0.01-0.73 on identical inputs) and the best-ArcFace sample was the one rejected; judge on tools/audit_views.py (head row beside ALL his references, FACE vs NECK); "
        "FEEDBACK_LOG items 12-17 list what already failed (own hair/beard wording, shade line, face swap, 6 photos, head redraw, brighter face, clean-only references)",
    26: "physique / accessories / eyewear: slim-build measure line ('upper arm barely thicker than his forearm, flat chest, narrow waist; the pin man's broad shoulders and big arms are not his'); name every accessory and colour; 'eyes open in the shadow of his curls, no glasses'",
    19: "the pin man came back unchanged: remove 'exactly as in the PHOTO TO EDIT' about head or arms; describe pose in geometry; name that all his hair is his",
    23: "the source came back as is: same fix as 19",
    28: "his face, hair and beard must come from the references: say so in the change list and keep the FACE references first",
    6: "head too big (hair a ball): say 'curls sit close to the head, no bigger than the pin man's hairstyle'",
    8: "something unreal: regenerate; check hands and the head-neck join at full zoom",
}


def next_step(key: str, rows: list[dict]) -> None:
    """The next move for an open goal, the consistent way (2026-10-07): its latest RECIPE version and that version's track record, and the command
    that runs exactly that version again; with no recipe yet, the `recipe new` command from the newest inventory (linted here, free)."""
    import inventory_lint
    import recipe as R
    gid = key.replace("pin_", "")
    d = R.recipe_dir(key)
    vs = R.versions(d)
    if vs:
        rec = json.loads(vs[-1].read_text(encoding="utf-8"))
        runs = [r for r in R.runs_of(key) if r["version"] == rec["version"] and not r["adhoc"]]
        mine = [r for r in rows if r["run"] in {x["run"] for x in runs} or r["run"] == (rec.get("origin") or {}).get("run")]
        passed = sum(1 for r in mine if r["result"].startswith("PASS"))
        inv = (rec["inputs"].get("inventory") or {}).get("data")
        findings = inventory_lint.lint(inv, files=len(rec["lock"]["files"])) if inv else []
        print(f"      recipe: {d.relative_to(ROOT)} v{rec['version']} ({rec['method']['model']['label']} x{rec['method']['samples']}, request "
              f"{rec['lock']['request_sha256'][:12]}): {len(runs)} run(s), {len(mine)} picture(s), {passed} passed; because: {rec.get('because')}")
        for level, msg in findings:
            print(f"        lint {level}: {msg[:200]}")
        print(f"      run the same method again:  .venv/Scripts/python.exe facecard.py run {key}@v{rec['version']} --samples 2")
        print(f"      change the method:          .venv/Scripts/python.exe facecard.py recipe bump {key}@v{rec['version']} --<what changes> --because \"<failed item / the user's words>\"")
        return
    invs = sorted((ROOT / ".cache" / "inventories").glob(f"pin_{gid}*.json"), key=lambda f: f.stat().st_mtime)
    if not invs:
        print("      next: no inventory yet: write .cache/inventories/pin_%s.json first (HIS / GOAL / REMOVE per element)" % gid)
        return
    inv_path = invs[-1]
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    findings = inventory_lint.lint(inv)
    print(f"      no recipe yet; lint of the newest inventory ({inv_path.name}): " + ("clean" if not findings else ""))
    for level, msg in findings:
        print(f"        {level}: {msg[:200]}")
    passes: dict[str, int] = {}
    for r in rows:
        # a pose pass on the goal's own man handed back (items 19 / 23 / 28 failed) is not a real pass (pins 6 and 9: the pin returned nearly unchanged)
        if r.get("pose_gate") == "PASS" and r.get("model") and not ({19, 23, 28} & set(r.get("failed_items", []))):
            passes[r["model"]] = passes.get(r["model"], 0) + 1
    model = max(passes, key=passes.get) if passes else "Pro"
    print(f"      pose-gate passes by model so far: {passes or 'none'}; canary on the SAME model as production: {model} (a Flash canary does not predict Pro, 1 sample fails a good recipe ~70% of the time)")
    goal = f".cache/pin_{gid}.jpg"
    prompt = f".cache/loop_prompts/pin_{gid}_route.txt"
    print("      freeze the method first, then run it (2 samples; scale up only after >= 1 pose pass):")
    print(f"        .venv/Scripts/python.exe facecard.py recipe new --goal {goal} --prompt {prompt} --inventory .cache/inventories/{inv_path.name} "
          f"--replace-subject --samples 2 --stop-after-fails 2" + (" --model e6fa609c3fa255c0" if model == "Pro" else " --model 56fdd199312815e2")
          + " --because \"<the user's words / the failed item>\"")
    print(f"        .venv/Scripts/python.exe facecard.py run pin_{gid}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--open", action="store_true", help="only goals that are not DONE; exit code 1 while any is open")
    ap.add_argument("--next", action="store_true", help="for each open goal: lint of its latest inventory, the model that passed the pose gate most, and the 2-sample canary command (plan 2026-10-02)")
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
            print(f"      next for item {i}: {FIXES.get(i, 'read its row in BEST_CHECKLIST.md and change only the request section that controls it')}")
        if not hist and gate:
            print("      next: every attempt failed the pose gate: " + FIXES[14])
        if args.next:
            next_step(key, rs)
    print(f"\n{n_open} open goal(s)." + ("  Keep going: another wave for each, in parallel." if n_open else "  Every goal has a picture that passed."))
    return 1 if n_open else 0


if __name__ == "__main__":
    sys.exit(main())
