"""Angle library: render the head poses his reference photos lack, once, from his studio photos (plan of 2026-09-23).

A grid of head poses (turn -90..90 in 30-degree steps x chin level / looking down / looking up) is checked against the poses the AI read on his
studio photos and on renders already kept. Every grid pose with nothing within SELF_MAX degrees is rendered by `replicate.synthetic_refs`: Gemini
renders him from the three studio photos nearest in turn; a render is kept only if its identity against his photos is at least SYN_ID_MIN and the
AI reads its pose within SYN_MATCH degrees of the target. Kept renders live in .cache/synthetic_refs/<pose bin>/ and are used as identity
references by `replicate` for photos at that angle.

    .venv\\Scripts\\python.exe angle_refs.py            # render every missing pose (image calls: about 2-3 per pose)
    .venv\\Scripts\\python.exe angle_refs.py --dry-run  # only list which poses are covered and which would be rendered (text calls only)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import identity
import replicate as R
from gemini_webapi.exceptions import UsageLimitExceededError
from scorer import ArcFaceScorer
from session import authenticated_client

ROOT = Path(__file__).parent
TURNS = (-90, -60, -30, 0, 30, 60, 90)
CHINS = (0, 30, -30)          # level, looking down, looking up


def cached_renders() -> list[tuple[str, Path, tuple[float, float]]]:
    out = []
    for index in sorted(R.SYN_DIR.glob("*/index.json")):
        for k in json.loads(index.read_text(encoding="utf-8")):
            p = index.parent / k["name"]
            if p.exists():
                out.append((k["name"], p, tuple(k["pose"])))
    return out


async def main(args) -> int:
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    model = config.get("model")
    text_models = [config.get("vision_model") or model, model]
    run_dir = ROOT / config.get("out_dir", "outputs") / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_angle_refs"
    run_dir.mkdir(parents=True, exist_ok=True)
    log = R.RunLog(run_dir, {"command": "angle_refs", "dry_run": args.dry_run, "grid": [], "status": "started"})
    scorer = ArcFaceScorer()
    pool = identity.build_pool(config, scorer, verbose=False)
    exclude = set(config.get("ref_exclude", []))
    async with authenticated_client(verbose=False) as client:
        studio = []
        for e in pool:
            if e.name in exclude or not R.STUDIO_RE.match(e.name):
                continue
            crop = R.head_ref_crop(e.path, scorer)
            p = R.pose_of(await R.ref_pose(client, text_models, crop, log))
            if p is not None:
                studio.append((e.name, crop, p))
        log.say("studio photos by pose: " + ", ".join(f"{n} ({p[0]:+.0f}, {p[1]:+.0f})" for n, _, p in studio))
        for chin in CHINS:
            for turn in TURNS:
                target = (float(turn), float(chin))
                have = [(n, R.pose_distance(p, target)) for n, _, p in studio] + [(n, R.pose_distance(p, target)) for n, _, p in cached_renders()]
                near = min(have, key=lambda t: t[1]) if have else ("-", 999.0)
                entry = {"target": list(target), "nearest": near[0], "distance": round(near[1], 1)}
                if near[1] <= R.SELF_MAX:
                    log.say(f"pose turn {turn:+d} chin {chin:+d}: covered by {near[0]} ({near[1]:.0f} degrees)")
                    entry["result"] = "covered"
                elif args.dry_run:
                    log.say(f"pose turn {turn:+d} chin {chin:+d}: MISSING (nearest {near[0]} at {near[1]:.0f} degrees) -> would be rendered")
                    entry["result"] = "missing"
                else:
                    camera = "above" if chin > 0 else ("below" if chin < 0 else "level")
                    try:
                        got = await R.synthetic_refs(client, model, text_models, target, camera, studio, pool, scorer, run_dir, log, False)
                    except UsageLimitExceededError as e:
                        log.say(f"Gemini image quota reached at turn {turn:+d} chin {chin:+d}: {e}. Run again after the reset; kept renders stay cached.")
                        log.data["status"] = "usage_limit"
                        log.data["grid"].append(entry)
                        log.save()
                        return 3
                    entry["result"] = f"rendered {len(got)} kept"
                    log.say(f"pose turn {turn:+d} chin {chin:+d}: {len(got)} renders kept")
                log.data["grid"].append(entry)
                log.save()
    log.data["status"] = "done"
    log.save()
    covered = sum(1 for g in log.data["grid"] if g["result"] == "covered")
    log.say(f"\nangle library: {covered} of {len(log.data['grid'])} poses were already covered; renders in {R.SYN_DIR}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="only list covered and missing poses (text calls only)")
    sys.exit(asyncio.run(main(ap.parse_args())))
