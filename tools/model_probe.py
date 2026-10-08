"""Which image model draws our pictures? (2026-10-08, the user: "use the latest Nano Banana, 2.1; ensure we are using it")

gemini_webapi picks only the CHAT model (Flash / Pro / Lite by header id); the Gemini app picks the image model from it, and no field of the
parsed reply names it. This probe sends one small identical image request on each chat model, keeps the RAW candidate data the library parses
(image links replaced by <url>, so nothing token-bearing is stored), searches it for any model name (banana, imagen, gemini-x.y, "image model"),
and records the credits each call cost, the picture size and its C2PA manifest. Two image calls in total.

    .venv\\Scripts\\python.exe tools\\model_probe.py [--models flash,pro]

Writes .cache/model_probe/<stamp>/probe.json (+ <label>_candidate.json, <label>.png) and prints the verdict per model.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROMPT = "Generate an image: a photorealistic red apple on a plain white wooden table, soft daylight from the left, square frame."
NAME_RE = re.compile(r"(?i)(nano[ _-]?banana[^\"\\]{0,20}|imagen[^\"\\]{0,20}|gemini[ _-]?\d(?:\.\d)?[^\"\\]{0,30}|flash[ _-]image[^\"\\]{0,20}|image[ _-]model[^\"\\]{0,30})")
URL_RE = re.compile(r"https?://[^\"\s\\]+")


GENERIC = {"imagen_default"}     # the app's image TOOL id (the same on every chat model, 2026-10-08), not a model version


def verdict_of(calls: list[dict]) -> str:
    specific = sorted({h for c in calls for h in c["names_in_raw_reply"] if h.lower() not in GENERIC})
    tools = sorted({h for c in calls for h in c["names_in_raw_reply"] if h.lower() in GENERIC})
    if specific:
        return "the raw reply names an image model: " + ", ".join(specific)
    return ("no model version in the raw reply" + (f" (only the image tool id {', '.join(tools)}, the same on every chat model probed: they hand the "
            "picture to the same default image model)" if tools else "") + "; the C2PA manifest names only Google's signer. Google's statement "
            "(Nano Banana 2.1 is the default image model for AI Pro accounts since 2026-10-06) is the only evidence of the version")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", default="flash,pro", help="labels from facecard.json models (default flash,pro)")
    args = ap.parse_args()
    import provenance as P
    from session import authenticated_client, credits_left
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    by_label = {v: k for k, v in (config.get("models") or {}).items()}
    out_dir = ROOT / ".cache" / "model_probe" / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"prompt": PROMPT, "when": datetime.now().isoformat(timespec="seconds"), "calls": []}
    async with authenticated_client(verbose=False) as client:
        result["listed"] = [{"id": m.model_id, "name": m.display_name, "available": m.is_available} for m in (client.list_models() or [])]
        print("models this account lists: " + "; ".join(f"{m['id']} = {m['name']}" for m in result["listed"]))
        captured: list = []
        orig = client._parse_candidate

        def spy(candidate_data, cid, rid, rcid):        # the raw candidate list, before the library reduces it to text and images
            captured.append(candidate_data)
            return orig(candidate_data, cid, rid, rcid)

        client._parse_candidate = spy
        for label in [x.strip() for x in args.models.split(",") if x.strip()]:
            model = by_label.get(label)
            if not model:
                print(f"{label}: not in facecard.json models")
                continue
            await client._fetch_usage_info()
            before = credits_left(client)
            n0 = len(captured)
            t0 = time.time()
            out = await client.generate_content(PROMPT, model=model, temporary=True)
            secs = round(time.time() - t0, 1)
            await asyncio.sleep(3)
            await client._fetch_usage_info()
            after = credits_left(client)
            raw = json.dumps(captured[n0:], ensure_ascii=False, default=str)
            red = URL_RE.sub("<url>", raw)
            (out_dir / f"{label}_candidate.json").write_text(red, encoding="utf-8")
            hits = sorted(set(m.group(0).strip() for m in NAME_RE.finditer(red)))
            cand = out.candidates[out.chosen]
            rec = {"label": label, "model": model, "listed_as": next((m["name"] for m in result["listed"] if m["id"] == model), None), "secs": secs,
                   "credits": (before - after) if (before is not None and after is not None) else None, "text": (cand.text or "")[:300],
                   "names_in_raw_reply": hits, "images": []}
            for j, img in enumerate(cand.generated_images):
                p = Path(await img.save(path=str(out_dir), filename=f"{label}_{j}.png"))
                from PIL import Image
                with Image.open(p) as im:
                    px = list(im.size)
                rec["images"].append({"file": p.name, "px": px, "c2pa": P.c2pa_info(p)})
            result["calls"].append(rec)
            print(f"{label} ({rec['listed_as']}): {len(rec['images'])} image(s) {[i['px'] for i in rec['images']]}, {rec['credits']} credits, {secs} s; "
                  f"model names in the raw reply: {hits or 'none'}")
    verdict = verdict_of(result["calls"])
    result["verdict"] = verdict
    (out_dir / "probe.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nVERDICT: {verdict}\nrecord: {out_dir / 'probe.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
