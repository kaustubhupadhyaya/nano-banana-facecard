"""Character audit (2026-10-08): where the pictures made of him from the same reference photos differ in face fullness and build, with
numbers, before anything in generation is changed (the user: the pictures show different body types and body fat, visible in the face too:
cheeks, jaw, neck).

Record-only. It measures with character.py and writes one self-contained page and its JSON; it changes no picture, recipe or record.
Every measure is validated before it is read (an earlier arm measure from YOLO masks read a pin man as slimmer-armed than him and was
deleted, FEEDBACK_LOG section 14):
  1. his own photos: the spread over the studio set (IMG_6858-6875) must be tight, and copies of the same photo (another size or crop) must
     read the same;
  2. other men: the goal men judged by eye BEFORE any number was read (BUILD_BY_EYE below) must land outside his band on the heavier side,
     and the build words already written in feedback_ledger.json ("heavy arms", "slim arms") must agree;
  3. a face measure must tell other men from him at all (most measurable goal faces outside his band).
Only measures marked KEEP are used in the per-picture table, the grouped spread and the Route G comparison.

    .venv\\Scripts\\python.exe tools\\character_audit.py                    # measure everything (cached by sha256), write the page and JSON
    .venv\\Scripts\\python.exe tools\\character_audit.py --ai-pairs 10      # also ask Gemini (flash, text calls) to compare 10 pictures with
                                                                        # his photos, in both orders, and read the credit meter around it
    .venv\\Scripts\\python.exe tools\\character_audit.py --limit 20         # a quick look on the first 20 pictures

Output: D:\\FacecardReview\\character_audit_<date>.html and .json beside it (--out to change). D:\\FacecardReview\\index.html is not touched.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import html
import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import character as C  # noqa: E402
import paths  # noqa: E402
import provenance as P  # noqa: E402

ARCHIVE = Path(r"D:\FacecardArchive")
GOOGLE_21 = date(2026, 10, 6)          # Google moved the Gemini app to Nano Banana 2.1 that day
FLASH = "56fdd199312815e2"
# Shown beside the KEEP measures in the tables, always labelled UNVALIDATED, when they fail validation: the head-scaled arm and shoulder widths
# separate pin 8's man from him by 2-3 band widths but have too few independent checks (only pin 8's man has a measurable face).
EXPLORE = ["body.arm_iod", "body.shoulder_iod"]

# Judged by eye on 2026-10-08 from the nine goal pictures, BEFORE any measure was read: the goal man's build against his slim, lean build.
BUILD_BY_EYE = {
    "pin_783485666539775315": "heavier",   # pin 1: big, broad man, thick arms in a tee
    "pin_783485666539775327": "unclear",   # pin 2: average build, seated sideways
    "pin_783485666539775340": "heavier",   # pin 3: muscular arms and shoulders, tank top
    "pin_783485666539777050": "heavier",   # pin 4: muscular shirtless torso and arm
    "pin_783485666539777054": "unclear",   # pin 5: average build in a tee, bowed over a table
    "pin_783485666539777055": "heavier",   # pin 6: muscular shoulders and arms, shirtless
    "pin_783485666539777115": "heavier",   # pin 7: very big arms in a tee
    "pin_783485666539777118": "heavier",   # pin 8: very muscular, big arms, broad shoulders
    "pin_783485666539779317": "heavier",   # pin 9: heavy arms and shoulders in a polo
}
HEAVY_WORDS = re.compile(r"\b(heavy (build|arms|muscle|muscular|rounded)|heavier|heavily muscular|muscular|thick arms|thicker than his|"
                         r"broader|big pecs|big arms|huge arms)\b", re.I)
SLIM_WORDS = re.compile(r"\b(slim arms|slimmest body|slim body|lean build)\b", re.I)
FULL_FACE_WORDS = re.compile(r"\b(rounder|fuller face|face is rounder|chubb|puffy)\w*", re.I)

# Decision rule, fixed before the full run (printed on the page):
RULE = {
    "min_his": 2,              # measurable on at least 2 of his band photos
    "max_spread": 0.15,        # his band: (max - min) / median
    "max_repeat": 0.05,        # copies of the same photo: median |difference| / median value
    "min_evidence": 2,         # body: independent heavier-build checks the measure can be tried on (each goal man judged heavier, + the
                               # ledger words when testable). Was "2 goal men" until a 12-picture trial showed only pin 8 has a usable face.
    "heavier_share": 0.75,     # the share of the heavier goal men that must read above his band
    "min_auc": 0.65,           # ledger build words, when >= 3 'heavy' and >= 3 'slim' pictures have a value
    "face_outside_share": 0.5,  # face: share of the measurable other men outside his band (at least 2 men)
}


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def say(msg: str) -> None:
    print(msg, flush=True)


# ------------------------------------------------------------------------------------------------------------------------------ inputs


def run_index() -> dict[str, Path]:
    """run folder name -> folder: outputs\\ first, then every archive folder (one or two levels down)."""
    idx: dict[str, Path] = {}
    roots = [ROOT / "outputs"]
    if ARCHIVE.is_dir():
        for d in ARCHIVE.iterdir():
            if d.is_dir():
                roots += [d, d / "outputs"]
    for r in roots:
        if r.is_dir():
            for d in r.iterdir():
                if d.is_dir():
                    idx.setdefault(d.name, d)
    return idx


def find_ci(folder: Path, name: str) -> Path | None:
    p = folder / name
    if p.is_file():
        return p
    if folder.is_dir():
        low = name.lower()
        for q in folder.iterdir():
            if q.name.lower() == low:
                return q
    return None


def ref_kind(name: str) -> str:
    stem = Path(name).stem
    if "_fav_" in stem:
        return "fav"
    if stem.startswith("IMG_6923"):
        return "body"
    if stem.startswith("IMG_0440"):
        return "arms"
    m = re.match(r"IMG_(\d{4})$", stem)
    if m and 6858 <= int(m.group(1)) <= 6875:
        return "studio"
    return "other ref"


def norm_ref(name: str) -> str:
    stem = Path(str(name)).stem
    return re.sub(r"_(head768|full1600)_\d+$", "", stem)


def collect_refs(config: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """His reference photos (primary files), copies of the same photos for repeatability, his earlier photos; and the (primary, copy) pairs."""
    rd, cache_refs, crops = paths.refs_dir(), ROOT / ".cache" / "refs", ROOT / ".cache" / "refcrops"
    items, pairs = [], []
    for name in config.get("refs", []):
        prim = find_ci(rd, name) or find_ci(cache_refs, name)
        if not prim:
            say(f"  [refs] not found: {name}")
            continue
        rid = f"R:{norm_ref(name)}"
        items.append({"id": rid, "kind": ref_kind(name), "name": norm_ref(name), "path": str(prim)})
        copies = []
        cr = find_ci(cache_refs, name)
        if cr and cr.resolve() != prim.resolve():
            copies.append(("prepared copy", cr))
        for c in sorted(crops.glob(f"{norm_ref(name)}_*.jpg")) if crops.is_dir() else []:
            copies.append(("head crop (sent)" if "_head768_" in c.name else "1600 px copy", c))
        for what, c in copies:
            cid = f"C:{norm_ref(name)}:{what}"
            kind = "fav (sent crop)" if (ref_kind(name) == "fav" and "head" in what) else "copy"
            items.append({"id": cid, "kind": kind, "name": f"{norm_ref(name)} ({what})", "path": str(c), "copy_of": rid})
            pairs.append((rid, cid))
    sf = ROOT / ".cache" / "super_favs"
    for p in sorted(sf.glob("*.jpg")) if sf.is_dir() else []:
        items.append({"id": f"E:{p.stem}", "kind": "earlier", "name": p.stem, "path": str(p)})
    return items, pairs


def goal_base(stem: str, names: dict) -> str:
    r = names.get(stem)
    if not r:
        return f"misc_{stem}"
    return f"{r['collection']}_{int(r['number']):02d}_{str(r['title']).replace(' ', '-')}"


def short_goal(goal: str) -> str:
    m = re.match(r"motorcycle-outfit-men_(\d+)_", goal or "")
    if m:
        return f"pin {int(m.group(1))}"
    m = re.match(r"own-photos_(\d+)_([a-z\-]+?)-current-look", goal or "")
    if m:
        return f"own {int(m.group(1))} {m.group(2)}"
    return (goal or "?").replace("misc_", "")


def collect_goals(names: dict) -> list[dict]:
    out = []
    for stem in names:
        if stem.startswith("_"):
            continue
        p = find_ci(ROOT / ".cache", stem + ".jpg") or find_ci(ROOT / ".cache" / "super_favs", stem + ".jpg")
        if p:
            out.append({"id": f"G:{short_goal(goal_base(stem, names))}", "kind": "goal", "name": stem, "goal": goal_base(stem, names),
                        "path": str(p), "by_eye_build": BUILD_BY_EYE.get(stem)})
    return out


def run_meta(run_dir: Path | None, row: dict, models: dict) -> dict:
    run = P.read_json(run_dir / "run.json", {}) if run_dir else {}
    man = P.read_json(run_dir / "manifest.json", {}) if run_dir else {}
    run = run or {}
    rg = run.get("route_g") or {}
    name = run_dir.name if run_dir else str(row.get("run"))
    route = "G" if rg else ("replicate" if "_replicate_" in name else "import")
    roles = rg.get("roles") or {}
    face = roles.get("face") or run.get("refs") or run.get("identity_refs") or []
    face = [norm_ref(x if isinstance(x, str) else (x.get("name") or x.get("file") or "")) for x in face]
    body = [norm_ref(x) for x in (roles.get("body") or []) + (roles.get("arms") or []) if isinstance(x, str)]
    sent = [o.get("what", "") + " " + o.get("path", "") for s in (man.get("stages") or []) if s.get("n") == 3 for o in s.get("outputs", [])]
    if any("build_sheet" in x for x in sent):
        body_refs = "build sheet (IMG_6923 + IMG_0440 side by side)"
    elif body:
        body_refs = " + ".join(body) + " (separate)"
    else:
        body_refs = "none"
    mid = run.get("model") or ((run.get("text_models") or [None, None])[-1])
    model = (models.get(mid) or row.get("model") or "?") if mid else (row.get("model") or "?")
    m = re.match(r"(\d{8})_(\d{4,6})", name) or re.match(r"(\d{8})_(\d{4,6})", str(row.get("time") or ""))
    d = datetime.strptime(m.group(1), "%Y%m%d").date() if m else None
    goal_path = rg.get("goal") or run.get("scene")
    if goal_path and not Path(goal_path).is_absolute():
        goal_path = str(ROOT / goal_path)
    return {"route": route, "face_refs": "+".join(sorted(set(face))) or "?", "body_refs": body_refs, "model": str(model).lower(),
            "date": d.isoformat() if d else None, "era": ("2.1 (from 10-06)" if d and d >= GOOGLE_21 else "before 10-06") if d else "?",
            "goal_path": goal_path, "recipe": (man.get("recipe") or run.get("recipe") or {}).get("id")}


def collect_pictures(limit: int | None) -> list[dict]:
    rows = (P.read_json(ROOT / "feedback_ledger.json", {}) or {}).get("rows", {})
    cfg = P.read_json(ROOT / "facecard.json", {}) or {}
    models = {k: v for k, v in (cfg.get("models") or {}).items() if not k.startswith("_")}
    idx = run_index()
    out = []
    for key, row in rows.items():
        if key.startswith("import:"):
            path = Path(key[7:])
            run_dir = path.parent if path.parent.is_dir() else None
        else:
            run_dir = idx.get(str(row.get("run")))
            path = (run_dir / row["file"]) if run_dir else None
        if not path or not path.is_file():
            continue
        text = f"{row.get('wrong') or ''} | {row.get('right') or ''}"
        build, words = None, None
        mh, ms = HEAVY_WORDS.search(row.get("wrong") or ""), SLIM_WORDS.search(text)
        if mh:
            build, words = "heavy", mh.group(0)
        elif ms:
            build, words = "slim", ms.group(0)
        meta = run_meta(run_dir, row, models)
        out.append({"kind": "picture", "key": key, "path": str(path), "goal": row.get("goal"), "goal_label": short_goal(row.get("goal")),
                    "run": run_dir.name if run_dir else row.get("run"), "file": row.get("file"), "result": row.get("result"),
                    "by_eye_build": build, "by_eye_words": words, "by_eye_face": "fuller" if FULL_FACE_WORDS.search(row.get("wrong") or "") else None, **meta})
    out.sort(key=lambda p: (p["goal"] or "", p["run"] or "", p["file"] or ""))
    for i, p in enumerate(out, 1):
        p["id"] = f"p{i:03d}"
    return out[:limit] if limit else out


# ------------------------------------------------------------------------------------------------------------------------------ statistics


def spread(values: list[float]) -> dict | None:
    if not values:
        return None
    v = np.array(values, float)
    med = float(np.median(v))
    return {"n": len(v), "min": float(v.min()), "max": float(v.max()), "median": med,
            "rel_spread": float((v.max() - v.min()) / abs(med)) if med else None}


def auc(hi: list[float], lo: list[float]) -> float | None:
    if not hi or not lo:
        return None
    wins = sum((a > b) + 0.5 * (a == b) for a in hi for b in lo)
    return wins / (len(hi) * len(lo))


def variance_explained(values: list[float], groups: list[str]) -> dict | None:
    v, g = np.array(values, float), np.array(groups)
    n = len(v)
    labels = sorted(set(groups))
    k = len(labels)
    if n < 4 or k < 2:
        return None
    gm = v.mean()
    sst = float(((v - gm) ** 2).sum())
    if sst <= 0:
        return None
    ssb = float(sum((g == lab).sum() * (v[g == lab].mean() - gm) ** 2 for lab in labels))
    ssw = sst - ssb
    eps = (ssb - (k - 1) * ssw / (n - k)) / sst if n > k else None
    return {"eta2": ssb / sst, "eps2": eps, "k": k, "n": n,
            "groups": {lab: {"n": int((g == lab).sum()), "mean": float(v[g == lab].mean())} for lab in labels}}


# ------------------------------------------------------------------------------------------------------------------------------ validation


def band_flat(ms: list[dict]) -> dict[str, dict]:
    b = C.band(ms)
    return {f"{sec}.{k}": v for sec in b for k, v in b[sec].items()}


def ledger_word_test(val: dict[str, dict], pics: list[dict]) -> dict:
    """Per measure: the pictures whose ledger lines call the build heavy vs slim, and the AUC (heavy read heavier than slim)."""
    out = {}
    for key, (_, direction) in C.MEASURES.items():
        hi = [val[p["id"]][key] for p in pics if p.get("by_eye_build") == "heavy" and key in val.get(p["id"], {})]
        lo = [val[p["id"]][key] for p in pics if p.get("by_eye_build") == "slim" and key in val.get(p["id"], {})]
        a = auc(hi, lo)
        out[key] = {"n_heavy": len(hi), "n_slim": len(lo), "auc": None if a is None else (a if direction >= 0 else 1 - a),
                    "median_heavy": float(np.median(hi)) if hi else None, "median_slim": float(np.median(lo)) if lo else None}
    return out


def validate(items: list[dict], meas: dict, pairs: list[tuple[str, str]], words: dict) -> tuple[dict, dict]:
    """Per measure: the numbers of every test and KEEP / DROP. Also returns his bands (face: studio set; body: studio + IMG_6923 + IMG_0440)."""
    by_id = {it["id"]: it for it in items}
    val = {it["id"]: C.flat(meas[it["path"]]) for it in items if it["path"] in meas}
    studio = [i for i in items if i["kind"] == "studio"]
    his_body = [i for i in items if i["kind"] in ("studio", "body", "arms")]
    bands = {"face": band_flat([meas[i["path"]] for i in studio]), "body": band_flat([meas[i["path"]] for i in his_body])}
    out = {}
    for key, (label, direction) in C.MEASURES.items():
        sec = key.split(".")[0]
        band_ = bands[sec].get(key)
        rec = {"key": key, "label": label, "direction": direction, "band_from": "studio set" if sec == "face" else "studio set + IMG_6923 + IMG_0440",
               "band": band_, "why": [], "notes": []}
        rec["studio"] = {i["name"]: val[i["id"]].get(key) for i in studio}
        rec["studio_spread"] = spread([x for x in rec["studio"].values() if x is not None])
        rec["his"] = {i["name"]: val[i["id"]].get(key) for i in his_body}
        rec["his_spread"] = spread([x for x in rec["his"].values() if x is not None])
        rec["named"] = {i["name"]: {"kind": i["kind"], "value": val[i["id"]].get(key)} for i in items
                        if i["kind"] in ("body", "arms", "fav", "fav (sent crop)", "earlier")}
        diffs = []
        for a, b in pairs:
            va, vb = val.get(a, {}).get(key), val.get(b, {}).get(key)
            if va is not None and vb is not None:
                diffs.append({"photo": by_id[a]["name"], "copy": by_id[b]["name"], "a": va, "b": vb, "diff": vb - va})
        rec["repeat"] = diffs
        sp = rec["studio_spread"] if sec == "face" else rec["his_spread"]
        med = abs(sp["median"]) if sp else None
        rec["repeat_rel"] = float(np.median([abs(d["diff"]) for d in diffs])) / med if diffs and med else None
        goals = []
        for g in (i for i in items if i["kind"] == "goal" and i["name"].startswith("pin_")):
            x = val.get(g["id"], {}).get(key)
            if x is None or not band_:
                continue
            goals.append({"goal": g["id"], "by_eye": g.get("by_eye_build"), "value": x, "off_by": C.off_by(x, band_)})
        rec["goals"] = goals
        w = words.get(key) or {}
        rec["ledger_words"] = w
        # verdict (RULE)
        n_his = (sp or {}).get("n", 0)
        ok = True
        if n_his < RULE["min_his"]:
            ok = False
            rec["why"].append(f"measurable on {n_his} of his band photos (needs {RULE['min_his']})")
        if sp and sp["rel_spread"] is not None and sp["rel_spread"] > RULE["max_spread"]:
            ok = False
            rec["why"].append(f"his own photos spread {sp['rel_spread']:.0%} (limit {RULE['max_spread']:.0%})")
        if rec["repeat_rel"] is not None and rec["repeat_rel"] > RULE["max_repeat"]:
            ok = False
            rec["why"].append(f"copies of the same photo differ by {rec['repeat_rel']:.1%} (limit {RULE['max_repeat']:.0%})")
        elif rec["repeat_rel"] is None:
            rec["notes"].append("repeatability untested (no copy measurable)")
        if sec == "body" and direction:
            heav = [g for g in goals if g["by_eye"] == "heavier"]
            above = [g for g in heav if g["off_by"] * direction > 0]
            testable = w.get("n_heavy", 0) >= 3 and w.get("n_slim", 0) >= 3 and w.get("auc") is not None
            evidence = len(heav) + (1 if testable else 0)
            rec["heavier_test"] = (f"{len(above)} of {len(heav)} goal men judged heavier read above his band"
                                   + (f"; ledger words AUC {w['auc']:.2f}" if testable else "; ledger words not testable"))
            if evidence < RULE["min_evidence"]:
                ok = False
                rec["why"].append(f"{evidence} independent heavier-build checks available (needs {RULE['min_evidence']}: goal men judged heavier "
                                  "+ the ledger words)")
            if heav and len(above) / len(heav) < RULE["heavier_share"]:
                ok = False
                rec["why"].append(f"only {len(above)} of {len(heav)} heavier goal men read above his band")
            if testable and w["auc"] < RULE["min_auc"]:
                ok = False
                rec["why"].append(f"disagrees with the ledger's build words (AUC {w['auc']:.2f} < {RULE['min_auc']})")
        if sec == "face":
            outside = [g for g in goals if g["off_by"] != 0]
            rec["face_test"] = f"{len(outside)} of {len(goals)} measurable goal men outside his band"
            if len(goals) < 2:
                rec["notes"].append(f"only {len(goals)} goal face measurable: whether it tells other men from him is untested; whether it reads "
                                    "fat (and not beard) is untested")
            elif len(outside) / len(goals) < RULE["face_outside_share"]:
                ok = False
                rec["why"].append(f"only {len(outside)} of {len(goals)} other men fall outside his band (it cannot tell men apart)")
        if sec == "body" and not direction:
            rec["notes"].append("a body proportion, not a fat cue: kept only as a check of head-to-body scale")
        rec["verdict"] = "KEEP" if ok else "DROP"
        out[key] = rec
    return out, bands


# ------------------------------------------------------------------------------------------------------------------------------ strips


def grid(tiles: list[np.ndarray], per_row: int) -> np.ndarray | None:
    if not tiles:
        return None
    h = max(t.shape[0] for t in tiles)
    w = max(t.shape[1] for t in tiles)
    pad = [cv2.copyMakeBorder(t, 0, h - t.shape[0] + 6, 0, w - t.shape[1] + 6, cv2.BORDER_CONSTANT, value=(235, 235, 235)) for t in tiles]
    rows = []
    for i in range(0, len(pad), per_row):
        r = pad[i:i + per_row]
        r += [np.full_like(pad[0], 235)] * (per_row - len(r)) if len(pad) > per_row else []
        rows.append(np.hstack(r))
    return np.vstack(rows)


def uri(img: np.ndarray, q: int = 78) -> str:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


# ------------------------------------------------------------------------------------------------------------------------------ AI pairs

PAIR_PROMPT = (
    "Image 1 and image 2 each show a man. Compare only how heavily built each man is and how much body fat he carries, not who he is, his "
    "clothes, his pose or the picture quality. {q} Reply with ONLY a JSON object, no other text: {schema}")
Q_BUILD = ("Is the man in image 2 heavier (more body fat or more muscle bulk), about the same build, or leaner than the man in image 1? "
           "Also compare their faces: is the face of the man in image 2 fuller (rounder cheeks, wider jaw, thicker neck), about the same, or "
           "leaner than the face of the man in image 1?")
S_BUILD = '{"build": "heavier" | "same" | "leaner", "face": "fuller" | "same" | "leaner", "why": "<one short sentence>"}'
Q_FACE = ("Look only at the faces and necks: is the face of the man in image 2 fuller (rounder cheeks, wider jaw, thicker neck), about the "
          "same, or leaner than the face of the man in image 1?")
S_FACE = '{"face": "fuller" | "same" | "leaner", "why": "<one short sentence>"}'
FLIP = {"heavier": "leaner", "leaner": "heavier", "fuller": "leaner", "same": "same"}


class _Log:
    def say(self, msg: str) -> None:
        say(msg)


def _norm(word, kind: str):
    w = str(word or "").strip().lower()
    if kind == "face" and w == "heavier":
        w = "fuller"
    return w if w in ("heavier", "leaner", "fuller", "same") else None


def _flip(word, kind: str):
    if word is None:
        return None
    if kind == "face":
        return {"fuller": "leaner", "leaner": "fuller", "same": "same"}.get(word)
    return FLIP.get(word)


async def ai_pairs(chosen: list[dict], body_ref: Path, face_ref: Path) -> dict:
    from replicate import gemini_text
    from session import authenticated_client, credits_left, describe_usage, usage_of
    out = {"model": FLASH, "pairs": [], "body_ref": str(body_ref), "face_ref": str(face_ref)}
    log = _Log()
    async with authenticated_client(verbose=False) as client:
        out["credits_start"] = credits_left(client)
        out["usage_start"] = describe_usage(usage_of(client))
        say(f"[AI pairs] credit meter at the start: {out['usage_start']}")
        for p in chosen:
            img = Path(p["path"])
            rec = {"id": p["id"], "path": p["path"]}
            b1 = await gemini_text(client, [FLASH], PAIR_PROMPT.format(q=Q_BUILD, schema=S_BUILD), [body_ref, img], log, "pair")
            b2 = await gemini_text(client, [FLASH], PAIR_PROMPT.format(q=Q_BUILD, schema=S_BUILD), [img, body_ref], log, "pair")
            f1 = await gemini_text(client, [FLASH], PAIR_PROMPT.format(q=Q_FACE, schema=S_FACE), [face_ref, img], log, "pair")
            f2 = await gemini_text(client, [FLASH], PAIR_PROMPT.format(q=Q_FACE, schema=S_FACE), [img, face_ref], log, "pair")
            rec["raw"] = {"build_ref_first": b1, "build_pic_first": b2, "face_ref_first": f1, "face_pic_first": f2}
            bA, bB = _norm((b1 or {}).get("build"), "build"), _flip(_norm((b2 or {}).get("build"), "build"), "build")
            fA, fB = _norm((f1 or {}).get("face"), "face"), _flip(_norm((f2 or {}).get("face"), "face"), "face")
            gA, gB = _norm((b1 or {}).get("face"), "face"), _flip(_norm((b2 or {}).get("face"), "face"), "face")
            rec["build"] = bA if bA and bA == bB else "split"
            rec["face"] = fA if fA and fA == fB else "split"
            rec["face_vs_6923"] = gA if gA and gA == gB else "split"
            rec["orders"] = {"build": [bA, bB], "face": [fA, fB], "face_vs_6923": [gA, gB]}
            say(f"  [AI pairs] {p['id']}: build {rec['build']} {rec['orders']['build']}, face {rec['face']} {rec['orders']['face']}")
            out["pairs"].append(rec)
        await asyncio.sleep(3)
        try:
            await client._fetch_usage_info()
        except Exception:
            pass
        out["credits_end"] = credits_left(client)
        out["usage_end"] = describe_usage(usage_of(client))
    if out.get("credits_start") is not None and out.get("credits_end") is not None:
        out["credits_spent"] = out["credits_start"] - out["credits_end"]
    out["calls"] = 4 * len(chosen)
    say(f"[AI pairs] credit meter at the end: {out['usage_end']} (spent {out.get('credits_spent')} on {out['calls']} text calls; the meter is account-wide)")
    return out


# ------------------------------------------------------------------------------------------------------------------------------ page

CSS = """
:root{--bg:#fbfbf9;--fg:#1c1c1a;--muted:#6b6b66;--line:#e2e1dc;--card:#fff;--hi:#fbe3e1;--lo:#e1ecfb;--in:#e3f3e6;--keep:#1f7a3a;--drop:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#ecebe6;--muted:#a3a29c;--line:#34332f;--card:#1f1f1d;--hi:#4a2421;--lo:#1f3050;--in:#1f3a26;--keep:#6fcf8a;--drop:#ff8a80}}
:root[data-theme="dark"]{--bg:#161615;--fg:#ecebe6;--muted:#a3a29c;--line:#34332f;--card:#1f1f1d;--hi:#4a2421;--lo:#1f3050;--in:#1f3a26;--keep:#6fcf8a;--drop:#ff8a80}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1500px;margin:0 auto;padding:16px}h1{font-size:1.5rem;margin:.2em 0}h2{font-size:1.15rem;margin:1.4em 0 .4em}
h3{font-size:1rem;margin:1em 0 .3em}.sub{margin:.2em 0;color:var(--muted)}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px 16px 14px;margin:12px 0;overflow-x:auto}
table{border-collapse:collapse;font-size:.82rem;margin:8px 0;width:100%}th,td{border-bottom:1px solid var(--line);padding:3px 7px;text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.hi{background:var(--hi)}.lo{background:var(--lo)}.in{background:var(--in)}.KEEP{color:var(--keep);font-weight:700}.DROP{color:var(--drop);font-weight:700}
.muted{color:var(--muted);font-size:.85rem}img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:4px}
ul{margin:.3em 0 .6em 1.2em;padding:0}li{margin:.15em 0}code{font-family:ui-monospace,Consolas,monospace;font-size:.85em}
"""


def fmt(x, nd=3) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def tbl(head: list[str], rows: list[list], cls_rows: list[list] | None = None) -> str:
    out = ["<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"]
    for i, r in enumerate(rows):
        cells = []
        for j, c in enumerate(r):
            cls = (cls_rows[i][j] if cls_rows and cls_rows[i][j] else "")
            num = isinstance(c, (int, float)) and not isinstance(c, bool)
            text = fmt(c) if num else (c if isinstance(c, Raw) else esc(c))
            cells.append(f"<td class='{cls}{' n' if num else ''}'>{text}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


class Raw(str):
    """Already-escaped HTML for a table cell."""


def off_class(off, direction) -> str:
    if off is None:
        return ""
    if off == 0:
        return "in"
    return "hi" if off * (direction or 1) > 0 else "lo"


# ------------------------------------------------------------------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(paths.review_dir() / f"character_audit_{date.today().isoformat()}.html"))
    ap.add_argument("--ai-pairs", type=int, default=0, help="compare N pictures (at most 10) with his photos through Gemini flash text calls")
    ap.add_argument("--limit", type=int, default=None, help="only the first N pictures (a quick look)")
    a = ap.parse_args()
    t0 = time.time()
    cfg = P.read_json(ROOT / "facecard.json", {}) or {}
    names = {k: v for k, v in (P.read_json(ROOT / "results_names.json", {}) or {}).items() if not k.startswith("_")}

    refs, pairs = collect_refs(cfg)
    goals = collect_goals(names)
    pics = collect_pictures(a.limit)
    goal_by_base = {g["goal"]: g for g in goals}
    for p in pics:          # goals that are not in results_names (misc) are added from the run's own goal path
        if p["goal"] not in goal_by_base and p.get("goal_path") and Path(p["goal_path"]).is_file():
            g = {"id": f"G:{short_goal(p['goal'])}", "kind": "goal", "name": Path(p["goal_path"]).stem, "goal": p["goal"],
                 "path": p["goal_path"], "by_eye_build": None}
            goals.append(g)
            goal_by_base[p["goal"]] = g
    items = refs + goals
    say(f"Inputs: {len(pics)} pictures from the ledger, {len(refs)} reference files (with copies and earlier photos), {len(goals)} goal pictures")

    meas = C.measure_all([it["path"] for it in items] + [p["path"] for p in pics], say=say)
    t_measure = time.time() - t0
    val = {it["id"]: C.flat(meas[it["path"]]) for it in items + pics if it["path"] in meas}

    words = ledger_word_test(val, pics)
    validation, bands = validate(items, meas, pairs, words)
    keep = [k for k, r in validation.items() if r["verdict"] == "KEEP"]
    shown = keep + [k for k in EXPLORE if k not in keep]       # EXPLORE: failed validation, shown only as pointers, always labelled so
    say("Validation: " + ", ".join(f"{k} {r['verdict']}" for k, r in validation.items()))

    def his_band(key):
        return bands[key.split(".")[0]].get(key)

    def col(k: str) -> str:
        return k.split(".")[1] + ("" if k in keep else " (UNVALIDATED)")

    def vs(values: dict, k: str) -> dict:
        off = C.off_by(values[k], his_band(k))
        return {"value": values[k], "inside": off == 0.0, "off_by": off}

    # per picture against his band
    for p in pics:
        m = meas.get(p["path"])
        if not m:
            continue
        p["face_usable"], p["face_reason"] = m["face"]["usable"], m["face"].get("reason")
        p["body_usable"], p["body_reason"] = m["body"]["usable"], m["body"].get("reason")
        p["yaw"], p["pitch"], p["face_px"] = m["face"].get("yaw"), m["face"].get("pitch"), m["face"].get("face_px")
        p["values"] = val.get(p["id"], {})
        p["vs_band"] = {k: vs(p["values"], k) for k in shown if k in p["values"] and his_band(k)}

    # grouped spread (pictures only), raw and within the same goal
    groupings = {"face_refs": "face-reference set", "body_refs": "body/arms references", "goal": "goal", "route": "route",
                 "model": "chat model", "era": "before / after Nano Banana 2.1 (10-06)"}
    grouped = {}
    for k in shown:
        rows = [p for p in pics if k in p.get("values", {})]
        vals = [p["values"][k] for p in rows]
        gmeans = {}
        for p in rows:
            gmeans.setdefault(p["goal"], []).append(p["values"][k])
        resid = [p["values"][k] - float(np.mean(gmeans[p["goal"]])) for p in rows]
        grouped[k] = {}
        for gk in groupings:
            labels = [str(p.get(gk)) for p in rows]
            ve = variance_explained(vals, labels)
            within = variance_explained(resid, labels) if gk != "goal" else None
            grouped[k][gk] = {"all": ve, "within_goal": within}

    # Route G: closer to the goal man's value or to his band?
    goal_vals = {g["goal"]: val.get(g["id"], {}) for g in goals}
    follow = {}
    for k in shown:
        b = his_band(k)
        if not b:
            continue
        width = max(b["max"] - b["min"], 0.02 * abs(b["median"]))
        rows = []
        for p in pics:
            if p["route"] != "G" or k not in p.get("values", {}):
                continue
            g = goal_vals.get(p["goal"], {}).get(k)
            if g is None:
                continue
            v = p["values"][k]
            rows.append({"id": p["id"], "goal": p["goal_label"], "value": v, "goal_value": g, "his_median": b["median"],
                         "closer_to": "goal man" if abs(v - g) < abs(v - b["median"]) else "him",
                         "t": (v - b["median"]) / (g - b["median"]) if abs(g - b["median"]) > width else None})
        ts = [r["t"] for r in rows if r["t"] is not None]
        follow[k] = {"rows": rows, "n": len(rows), "closer_to_goal": sum(r["closer_to"] == "goal man" for r in rows),
                     "median_t": float(np.median(ts)) if ts else None, "n_t": len(ts)}

    # AI pairs
    ai = None
    if a.ai_pairs:
        n = min(10, a.ai_pairs)
        # the extremes of the head-scaled arm width (the candidate that most needs another check) and of the first KEEP face measure
        body_k = next((k for k in shown if k == "body.arm_iod"), next((k for k in keep if k.startswith("body.")), None))
        face_k = next((k for k in keep if k.startswith("face.")), None)
        cand = []
        for k, hi_n, lo_n in ((body_k, 3, 2), (face_k, 3, 2)):
            if not k:
                continue
            d = C.MEASURES[k][1] or 1
            rows = sorted((p for p in pics if k in p.get("values", {})), key=lambda p: p["values"][k] * d)
            cand += rows[::-1][:hi_n] + rows[:lo_n]
        chosen = list({p["id"]: p for p in cand}.values())[:n]
        body_ref = find_ci(ROOT / ".cache" / "refs", "IMG_6923 Copy.jpg") or Path(next(r["path"] for r in refs if r["kind"] == "body"))
        face_ref = find_ci(ROOT / ".cache" / "refs", "IMG_6858.jpg") or Path(next(r["path"] for r in refs if r["kind"] == "studio"))
        try:
            ai = asyncio.run(ai_pairs(chosen, body_ref, face_ref))
        except Exception as exc:
            ai = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}
            say(f"[AI pairs] skipped: {ai['error']}")
    else:       # keep the last run's paid answers on the page (matched by picture path), with today's measures beside them
        prev = (P.read_json(Path(a.out).with_suffix(".json"), {}) or {}).get("ai_pairs")
        if prev and prev.get("pairs"):
            by_path = {p["path"]: p for p in pics}
            ai = {**prev, "pairs": [r for r in prev["pairs"] if r.get("path") in by_path]}
            for rec in ai["pairs"]:
                rec["id"] = by_path[rec["path"]]["id"]
            say(f"[AI pairs] reusing the {len(ai['pairs'])} answers of the last run (no new calls)")
    if ai and ai.get("pairs"):
        for rec in ai["pairs"]:
            rec["measure"] = {}
            p = next(q for q in pics if q["id"] == rec["id"])
            for k in shown:
                c = (p.get("vs_band") or {}).get(k)
                d = C.MEASURES[k][1]
                if not c or not d:
                    continue
                field, words_ = ("build", ("heavier", "leaner")) if k.startswith("body.") else ("face", ("fuller", "leaner"))
                mword = "same" if c["off_by"] == 0 else (words_[0] if c["off_by"] * d > 0 else words_[1])
                rec["measure"][k] = {"field": field, "off_by": c["off_by"], "says": mword,
                                     "agrees": None if rec[field] == "split" else rec[field] == mword}

    # strips
    say("Building the face and torso strips")
    order = [it for it in refs if it["kind"] in ("studio", "body", "arms", "fav", "fav (sent crop)")] + \
            [it for it in refs if it["kind"] == "earlier"] + goals + pics
    face_k = next((k for k in keep if k.startswith("face.")), "face.cjwr")
    arm_k = next((k for k in keep if k.startswith("body.arm")), "body.arm_iod")
    face_tiles, torso_tiles = [], []
    for it in order:
        m = meas.get(it["path"])
        if not m:
            continue
        lab = it["id"] if it["kind"] == "picture" else it["id"].split(":", 1)[1][:28]
        sub = f"{it.get('goal_label', '')} {it.get('model', '')} {(it.get('date') or '')[5:]}".strip() if it["kind"] == "picture" else it["kind"]
        v = C.flat(m)
        if m["face"]["usable"]:
            t = C.face_tile(it["path"], m["sha256"], [lab, sub, f"{face_k.split('.')[1]} {fmt(v.get(face_k))}"])
            if t is not None:
                face_tiles.append(t)
        tt = C.torso_tile(it["path"], m["sha256"], [lab, sub, f"{arm_k.split('.')[1]} {fmt(v.get(arm_k))}"])
        if tt is not None:
            torso_tiles.append(tt)
    face_grid, torso_grid = grid(face_tiles, 12), grid(torso_tiles, 10)

    # ---------------------------------------------------------------- page
    runtime = time.time() - t0
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n_face = sum(1 for p in pics if p.get("face_usable"))
    n_body = sum(1 for p in pics if p.get("body_usable"))
    H = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
         f"<title>Character audit</title><style>{CSS}</style></head><body><main>",
         "<h1>Character audit: face fullness and build across the pictures</h1>",
         f"<p class='sub'>{datetime.now():%Y-%m-%d %H:%M} · {len(pics)} pictures from feedback_ledger.json, {len(refs)} reference files, "
         f"{len(goals)} goals · face measurable on {n_face}, body on {n_body} pictures · runtime {runtime / 60:.1f} min "
         f"(measuring {t_measure / 60:.1f} min) · record-only, nothing was changed</p>"]

    # validation
    rows, cls = [], []
    for k, r in validation.items():
        sp = r["studio_spread"] if k.startswith("face.") else r["his_spread"]
        lw = r["ledger_words"]
        g = "; ".join(f"{x['goal'][2:]} {x['value']:.2f} ({x['off_by']:+.1f}){'*' if x['by_eye'] == 'heavier' else ''}" for x in r["goals"])
        rows.append([Raw(f"<span class='{r['verdict']}'>{r['verdict']}</span>"), k, r["label"],
                     f"{sp['n']}: {sp['min']:.3f}-{sp['max']:.3f} (med {sp['median']:.3f}, spread {sp['rel_spread']:.0%})" if sp else "-",
                     "-" if r["repeat_rel"] is None else f"{r['repeat_rel']:.1%} over {len(r['repeat'])} copies",
                     g or "-", r.get("heavier_test") or r.get("face_test") or "-",
                     f"heavy {lw['n_heavy']} / slim {lw['n_slim']}, AUC {fmt(lw['auc'], 2)}" if lw["n_heavy"] or lw["n_slim"] else "-",
                     ("; ".join(r["why"]) or "passes every test") + ("; NOTE: " + "; ".join(r["notes"]) if r["notes"] else "")])
        cls.append([""] * 9)
    H.append("<section><h2>1. Validation first: which measures can be trusted</h2>"
             "<p class='muted'>His band: face measures over the studio set (IMG_6858-6875); body measures over the studio set + IMG_6923 + "
             "IMG_0440. Goal values are shown with how far outside his band they fall, in band widths (+ = above, 0 = inside); * = judged "
             "heavier than him by eye before measuring. Rule: " + esc(json.dumps(RULE)) + "</p>"
             + tbl(["verdict", "measure", "what", "his band photos", "same photo, other file", "goal men", "separation test",
                    "ledger build words", "why"], rows, cls) + "</section>")

    # his references
    rows = []
    for it in refs:
        m = meas.get(it["path"])
        if not m:
            continue
        v = C.flat(m)
        rows.append([it["id"], it["kind"], ("ok" if m["face"]["usable"] else m["face"].get("reason")),
                     ("ok" if m["body"]["usable"] else m["body"].get("reason"))] +
                    [v.get(k) for k in C.MEASURES])
    H.append("<section><h2>2. His photos, one by one</h2><p class='muted'>Every measure, KEEP or not. 'fav' = his earlier photos used as "
             "face references (the full prepared file, and the head crop that was sent); 'earlier' = .cache/super_favs.</p>"
             + tbl(["photo", "kind", "face", "body"] + [k.split(".")[1] for k in C.MEASURES], rows) + "</section>")
    for it in refs:
        m = meas.get(it["path"])
        if m and it["kind"] in ("body", "arms", "fav", "fav (sent crop)", "earlier"):
            it["vs_band"] = {k: vs(C.flat(m), k) for k in shown if k in C.flat(m) and his_band(k)}
    rows, cls = [], []
    for it in [i for i in refs if i.get("vs_band")]:
        rows.append([it["id"], it["kind"]] + [(it["vs_band"].get(k) or {}).get("off_by") for k in shown])
        cls.append(["", ""] + [off_class((it["vs_band"].get(k) or {}).get("off_by"), C.MEASURES[k][1]) for k in shown])
    H.append("<section><h3>IMG_6923, IMG_0440, the _fav photos and his earlier photos against the studio band (KEEP measures, band widths)</h3>"
             + tbl(["photo", "kind"] + [col(k) for k in shown], rows, cls) + "</section>")

    # grouped spread
    parts = ["<section><h2>3. Which grouping explains the spread (pictures only, KEEP measures)</h2><p class='muted'>eta² = between-group "
             "variance / total variance; eps² corrects it for the number of groups (a grouping with many small groups explains variance by "
             "chance). 'within goal' = the same after removing each goal's mean, i.e. differences between pictures of the SAME goal. "
             "Groupings are confounded: the face-reference set was chosen per goal. Measures marked UNVALIDATED failed validation and are "
             "shown only to point where to look.</p>"]
    for k in shown:
        rows = []
        for gk, label in groupings.items():
            ve, wi = grouped[k][gk]["all"], grouped[k][gk]["within_goal"]
            if not ve:
                continue
            means = "; ".join(f"{esc(lab)[:60]} {d['mean']:.3f} (n {d['n']})" for lab, d in sorted(ve["groups"].items(), key=lambda t: t[1]["mean"]))
            rows.append([label, ve["k"], ve["n"], ve["eta2"], ve["eps2"], wi["eta2"] if wi else None, wi["eps2"] if wi else None, Raw(means)])
        parts.append(f"<h3>{esc(k)}: {esc(C.MEASURES[k][0])}{'' if k in keep else ' (UNVALIDATED: failed validation)'}</h3>" + tbl(["grouping", "groups", "pictures", "eta²", "eps²", "within goal eta²",
                                                                            "within goal eps²", "group means (low to high)"], rows))
    parts.append("</section>")
    H += parts

    # Route G
    rows = []
    for k, f in follow.items():
        rows.append([col(k), f["n"], f"{f['closer_to_goal']} of {f['n']}", f["median_t"], f["n_t"]])
    H.append("<section><h2>4. Route G: does the render follow the goal man or him?</h2><p class='muted'>closer = the render's value is nearer the "
             "goal man's value than his band median. t = (render - his median) / (goal man - his median): 0 = his value, 1 = the goal man's "
             "(only where the goal man is more than one band width from him).</p>"
             + tbl(["measure", "Route G pictures with a goal value", "closer to the goal man", "median t", "pictures with t"], rows) + "</section>")

    # AI pairs
    if ai is not None:
        if ai.get("error"):
            H.append(f"<section><h2>5. AI pairs</h2><p>Skipped: {esc(ai['error'])}</p></section>")
        else:
            rows = []
            for rec in ai.get("pairs", []):
                ms = rec.get("measure") or {}
                said = "; ".join(f"{col(k)}: {v['says']} ({v['off_by']:+.1f})" + ("" if v["agrees"] is None else (" agrees" if v["agrees"] else " DISAGREES"))
                                 for k, v in ms.items())
                rows.append([rec["id"], rec["build"], " / ".join(map(str, rec["orders"]["build"])), rec["face"],
                             " / ".join(map(str, rec["orders"]["face"])), rec["face_vs_6923"], said or "-"])
            H.append(f"<section><h2>5. AI pairs (Gemini flash, text calls, both orders)</h2><p class='muted'>Build: image A = {esc(Path(ai['body_ref']).name)}; "
                     f"face: image A = {esc(Path(ai['face_ref']).name)}. A verdict counts only when both orders agree, else 'split'. Credits: "
                     f"{esc(ai.get('usage_start'))} before, {esc(ai.get('usage_end'))} after: {esc(ai.get('credits_spent'))} for {ai.get('calls')} "
                     "text calls (the meter is account-wide).</p>"
                     + tbl(["picture", "AI build (vs IMG_6923)", "orders", "AI face (vs IMG_6858)", "orders", "AI face (vs IMG_6923)",
                            "what the measures say (band widths)"], rows) + "</section>")

    # strips
    H.append("<section><h2>6. Strips</h2><p class='muted'>Faces: aligned on the eye centres, the same interocular distance and box (usable faces "
             "only). Torsos: scaled to the same shoulder-keypoint width (every picture with both shoulders). Order: his photos, his earlier "
             "photos, goals, then pictures by goal and run.</p>")
    if face_grid is not None:
        H.append(f"<h3>Faces ({len(face_tiles)})</h3><img alt='face strip' src='{uri(face_grid)}'>")
    if torso_grid is not None:
        H.append(f"<h3>Torsos ({len(torso_tiles)})</h3><img alt='torso strip' src='{uri(torso_grid, 72)}'>")
    H.append("</section>")

    # per picture
    rows, cls = [], []
    for p in pics:
        vb = p.get("vs_band") or {}
        rows.append([p["id"], p["goal_label"], p["route"], p["model"], p.get("date"), p["face_refs"][:70], p["body_refs"][:40],
                     p.get("by_eye_build") or "", p.get("result") or ""] +
                    [(vb.get(k) or {}).get("value") for k in shown] + [(vb.get(k) or {}).get("off_by") for k in shown] +
                    ["" if p.get("face_usable") else (p.get("face_reason") or ""), "" if p.get("body_usable") else (p.get("body_reason") or "")])
        cls.append([""] * 9 + [off_class((vb.get(k) or {}).get("off_by"), C.MEASURES[k][1]) for k in shown] * 2 + ["", ""])
    H.append("<section><h2>7. Every picture against his band (KEEP measures)</h2><p class='muted'>Values, then how far outside his band "
             "(band widths; red = the heavier / fuller side, blue = the leaner side, green = inside).</p>"
             + tbl(["id", "goal", "route", "model", "date", "face refs", "body refs", "ledger build", "result"] + [col(k) for k in shown]
                   + [f"off {col(k)}" for k in shown] + ["face not measured", "body not measured"], rows, cls)
             + "<p class='muted'>Picture files: " + esc("; ".join(f"{p['id']} = {p['path']}" for p in pics)) + "</p></section>")
    H.append("<section><h2>Method</h2><pre style='white-space:pre-wrap'>" + esc(C.__doc__) + "</pre></section>")
    H.append("</main></body></html>")
    out.write_text("".join(H), encoding="utf-8")

    data = {"written": datetime.now().isoformat(timespec="seconds"), "rule": RULE, "build_by_eye": BUILD_BY_EYE, "keep": keep, "explore": EXPLORE,
            "validation": validation, "bands": bands, "grouped": grouped, "route_g_follow": follow, "ai_pairs": ai,
            "refs": [{**it, "values": C.flat(meas[it["path"]]) if it["path"] in meas else None} for it in refs],
            "goals": [{**g, "values": val.get(g["id"])} for g in goals],
            "pictures": pics, "runtime_s": round(runtime, 1), "measure_s": round(t_measure, 1)}
    P.atomic_write_json(out.with_suffix(".json"), data)
    say(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB) and {out.with_suffix('.json').name}; runtime {runtime / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
