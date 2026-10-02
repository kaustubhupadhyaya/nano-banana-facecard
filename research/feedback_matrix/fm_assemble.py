"""Assemble every row of the ranking: the curated rows (fm_rows, fm_rows2), one pick row for every other replicate run, one row for every gen
picture; then fill in paths, recorded and measured numbers, validity and the rank. Returns plain dicts; the workbook writer only formats them."""
import ast
import json
import re
from pathlib import Path

import cv2

from fm_measure import Measurer, ROOT, scene_path
from fm_rows import (B_INHERIT, B_NONE, B_PENDING, BATCH_R1, BATCH_R2, BATCH_TEXT, CLASSES, CODE_STATE, NO_VERDICT_RUNS, ROWS)
from fm_rows2 import ROWS2
from fm_rows3 import ROWS3
from fm_rows4 import ROWS4

FB = ROOT / ".cache" / "feedback"
OUTS = ROOT / "outputs"
GATES = {"size": (0.94, 1.04), "shift": 0.12, "dE_own": 14.0, "dE_foreign": 20.0, "neck": 10.0, "ssim": 0.80, "mad": 10.0, "unchanged": 0.90,
         "accept": 0.52, "hard_reject": 0.20}

KIND_LABEL = {"composite": "complete picture (head pasted back into the photo)", "gen": "complete picture (generated from scratch)",
              "offline_merge": "complete picture (offline merge of a saved return)", "head_raw": "head crop (raw return of Gemini)",
              "head_send": "crop sent to Gemini (= the source crop)"}

# review round by run time (2026-09-20 / 21); the explicit batch lists win
ROUND_BOUNDS = [("20260920_000000", "R1"), ("20260920_034000", "R2"), ("20260920_053000", "R3"), ("20260920_140000", "R4"), ("20260920_164000", "R5"),
                ("20260921_002000", "R6"), ("20260921_010000", "R7a"), ("20260921_021000", "R7b"), ("20260921_164000", "R8"), ("20260921_210000", "RULE"), ("20260923_000000", "R9")]


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def round_of(run: str) -> str:
    if run in BATCH_R1:
        return "R1"
    if run in BATCH_R2:
        return "R2"
    ts = run[:15]
    r = "R1"
    for bound, name in ROUND_BOUNDS:
        if ts >= bound:
            r = name
    return r


def flags(j: dict | None) -> str:
    if not j:
        return ""
    out = []
    if j.get("same_head_angle") is False:
        out.append("head angle changed")
    if j.get("same_expression") is False:
        out.append("expression differs")
    if j.get("glasses_preserved") is False:
        out.append("glasses changed")
    if j.get("jaw_clean") is False:
        out.append("jaw / neck artefact")
    if j.get("double_image"):
        out.append("double image")
    if j.get("seam_visible"):
        out.append("seam visible")
    if j.get("lighting_consistent") is False:
        out.append("lighting inconsistent")
    if j.get("anything_else_changed"):
        out.append("clothes/body/background changed")
    if j.get("reflection_matches") is False:
        out.append("reflection mismatch")
    return "; ".join(out) if out else "all clear"


def ai_wins(run_dir: Path) -> dict:
    p = run_dir / "run.log"
    if not p.exists():
        return {}
    m = re.search(r"AI face wins (\{[^}]*\})", p.read_text(encoding="utf-8", errors="replace"))
    try:
        return ast.literal_eval(m.group(1)) if m else {}
    except Exception:
        return {}


def closest_of(run_dir: Path, d: dict | None):
    c = ((d or {}).get("not_passing_closest") or {}).get("candidate")
    if c:
        return c
    p = run_dir / "run.log"
    if p.exists():
        m = re.search(r"The closest one \(attempt (\d+);", p.read_text(encoding="utf-8", errors="replace"))
        if m:
            return int(m.group(1))
    return None


def cand_index(file: str, d: dict | None, run_dir: Path):
    m = re.match(r"cand(\d+)\.png$", file) or re.match(r"c(\d+)_", file)
    if m:
        return int(m.group(1))
    if file.startswith("best"):
        return ((d or {}).get("best") or {}).get("candidate")
    if file.startswith("not_passing_closest"):
        return closest_of(run_dir, d)
    return None


def recorded(d: dict | None, idx) -> dict:
    if not d or idx is None:
        return {}
    c = next((c for c in d.get("candidates", []) if c.get("index") == idx), None)
    if not c:
        return {}
    m = c.get("metrics") or {}
    if "score" not in m:
        return {"verdict": c.get("verdict"), "problems": "; ".join(c.get("problems", [])), "warnings": "; ".join(c.get("warnings", []))}
    return {"identity": m.get("score"), "gt_sim": m.get("gt_sim"), "size": m.get("size_ratio"), "shift": m.get("face_shift_frac"),
            "dE": (m.get("light") or {}).get("dE"), "neck": m.get("neck_gap"), "ssim": (m.get("drift") or {}).get("ssim"),
            "mad": (m.get("drift") or {}).get("mean_abs_diff"), "outside_rec": (c.get("outside_check") or {}).get("changed_outside"),
            "same_size_rec": (c.get("outside_check") or {}).get("same_size"), "judge": flags(c.get("judge")),
            "vs_src": (c.get("face_vs_source") or {}).get("winner") or "", "verdict": c.get("verdict") or "",
            "problems": "; ".join(c.get("problems", [])), "warnings": "; ".join(c.get("warnings", [])), "source_score": m.get("source_score")}


def gen_picture(d: Path):
    for f in ("best.jpg", "v1_0_restored.jpg", "v1_0.jpg"):
        if (d / f).exists():
            return f
    return None


import os
import pickle

_CACHE_PATH = os.environ.get("FM_CACHE", "")
MEAS_CACHE: dict = {}
if _CACHE_PATH and Path(_CACHE_PATH).exists():
    try:
        MEAS_CACHE = pickle.loads(Path(_CACHE_PATH).read_bytes())
    except Exception:
        MEAS_CACHE = {}


def save_cache():
    """Optional (env FM_CACHE=<file>): keeps the slow image measurements between runs; texts are always rebuilt fresh."""
    if _CACHE_PATH:
        Path(_CACHE_PATH).write_bytes(pickle.dumps(MEAS_CACHE))


def assemble(meas: Measurer, verbose: bool = True) -> list[dict]:
    rows = [dict(r) for r in ROWS + ROWS2 + ROWS3 + ROWS4]
    covered = set()
    head_row_of_run: dict[str, str] = {}
    for r in rows:
        f = r["file"]
        covered.add((r["run"], "best" if f.startswith("best") else f))
        for extra in r.get("covers", []):
            covered.add((r["run"], extra))
        if r["kind"] == "head_raw":
            head_row_of_run.setdefault(r["run"], r["id"])

    # ---- one pick row for every other replicate run
    n_auto = 0
    fb_names = {p.name for p in FB.iterdir()}
    for d in sorted([p for p in FB.iterdir() if p.is_dir() and "_replicate_" in p.name]
                    + [p for p in OUTS.iterdir() if p.is_dir() and "_replicate_" in p.name and p.name not in fb_names], key=lambda p: p.name):
        pick = next((f for f in ("best.png", "best.jpg", "not_passing_closest.jpg") if (d / f).exists()), None)
        if not pick or (d.name, "best" if pick.startswith("best") else pick) in covered:
            continue
        n_auto += 1
        rd = load_json(d / "run.json") or {}
        rnd = round_of(d.name)
        idx = cand_index(pick, rd, d)
        rec = recorded(rd, idx)
        row = dict(id=f"A-{n_auto:02d}", group=(re.sub(r"^\d{8}_\d{6}_replicate_", "", d.name)), rnd=rnd, run=d.name, file=pick, kind="composite",
                   a="", i="", extra_paths=[])
        if d.name in BATCH_R1 or d.name in BATCH_R2:
            row.update(cls="BATCH_REJECTED", verdict=BATCH_TEXT["R1" if d.name in BATCH_R1 else "R2"], basis="none: a batch verdict, not a verdict on this picture",
                       fine="-", notfine="The batch was judged worse than the idea; this picture was not reviewed on its own.",
                       use="Old design (" + rnd + "); not evidence for the current code.")
        else:
            problems = rec.get("problems") or ""
            unchanged_only = bool(problems) and all("returned unchanged" in p for p in problems.split("; ") if p)
            if pick.startswith("best"):
                cls = "PENDING_PASS"
            else:
                cls = "PENDING_UNCHANGED" if unchanged_only else "PENDING_FAIL"
            note = ""
            if d.name in head_row_of_run:
                note = f" The user reviewed the head crop of this run (row {head_row_of_run[d.name]}), not this picture."
            if rnd == "R8":
                note += " Round-8 experiment, rolled back at the user's request: not evidence for the current code."
            if d.name in NO_VERDICT_RUNS:
                note += " Listed in FEEDBACK_LOG as: no verdict given."
            row.update(cls=cls, verdict="(no verdict given)", basis=B_PENDING,
                       fine=("Pipeline pick (" + (rec.get("verdict") or "?") + "): it passed every gate its version had." if pick.startswith("best")
                             else "Closest attempt of the run: nothing passed every gate."),
                       notfine=("; ".join(p for p in [problems, rec.get("warnings")] if p) or "-") + (". " + note.strip() if note else ""),
                       use="Not reviewed by the user. Numbers are the pipeline's own.")
        rows.append(row)

    # ---- gen pictures (from-scratch generations, 2026-09-17..19)
    n_gen = 0
    for d in sorted(p for p in FB.iterdir() if p.is_dir() and "_replicate_" not in p.name and p.name not in ("ideal", "rule_check_offline")):
        f = gen_picture(d)
        if not f or d.name.startswith("20260917_144731"):
            continue
        n_gen += 1
        slug = re.sub(r"^\d{8}_\d{6}_", "", d.name).replace("-", " ")
        rows.append(dict(id=f"G-{n_gen:02d}", group="gen: " + slug, rnd="gen", run=d.name, file=f, kind="gen", cls="BATCH_REJECTED", a="", i="",
                         verdict=BATCH_TEXT["gen"], basis="none: a batch verdict, not a verdict on this picture", fine="-",
                         notfine="Whole picture regenerated: scenery, background, clothes and physique are not guaranteed to be the source's.",
                         use="Old design; not evidence for the current code. The single exception the user named is the ideal I-02.", extra_paths=[]))

    # ---- complete every row
    for k, r in enumerate(rows, 1):
        run_dir = FB / r["run"] if (FB / r["run"]).exists() else OUTS / r["run"]
        if r.get("rnd") is None:
            r["rnd"] = round_of(r["run"])
        d = load_json(run_dir / "run.json")
        base = ROOT / r["dirpath"] if r.get("dirpath") else run_dir
        path = base / r["file"]
        r["path"] = str(path) if path.exists() else ""
        others = []
        w = OUTS / r["run"] / r["file"]
        if w.exists() and not r.get("dirpath"):
            others.append(str(w))
        for e in r.get("extra_paths", []):
            ep = (base / e).resolve()
            if ep.exists() and str(ep) != r["path"]:
                others.append(str(ep))
        if r["id"] == "I-02":
            for extra in (Path(r"D:\Downloads\AI me\beach.jpg"), FB / "ideal" / "beach_gen_20260917_144731_v1_0.jpg"):
                if extra.exists():
                    others.append(str(extra))
        if r["id"] == "I-01":
            ip = FB / "ideal" / "pinterest_20260921_064221_attempt4_best.png"
            if ip.exists():
                others.append(str(ip))
        r["other"] = "\n".join(dict.fromkeys(others))
        r["runjson"] = str(run_dir / "run.json") if (run_dir / "run.json").exists() else ""
        r["code_state"] = CODE_STATE.get(r["rnd"], r["rnd"])
        r["kind_label"] = KIND_LABEL[r["kind"]]
        r["class_label"] = CLASSES[r["cls"]][1]
        r["points"] = CLASSES[r["cls"]][0]
        r["source_kind"] = (d or {}).get("source_kind") or ("" if r["kind"] == "gen" else "")
        if r.get("source_photo"):
            r["source_photo"] = r["source_photo"]
        elif d and scene_path(d) is not None:
            sp_ = scene_path(d)
            r["source_photo"] = str(sp_) if sp_.exists() else "(deleted by the user since) " + str(sp_)
        else:
            r["source_photo"] = "none: generated from scratch"
        r["a_pts"] = {"P": 1, "O": 0, "N": -1}.get(r["a"])
        r["i_pts"] = {"P": 1, "O": 0, "N": -1}.get(r["i"])

        idx = cand_index(r["file"], d, run_dir) if not r.get("dirpath") else None
        rec = recorded(d, idx) if r["kind"] == "composite" else {}
        have_img = bool(r["path"]) and Path(r["path"]).exists()
        ckey = (r["path"], r["kind"], r["run"], json.dumps(rec, sort_keys=True, default=str))
        if ckey in MEAS_CACHE:
            m, by = MEAS_CACHE[ckey]
        else:
            ctx = meas.context(run_dir, d) if r["kind"] != "gen" else None
            img = cv2.imread(r["path"]) if have_img else None
            m = {}
            by = ""
            if img is None:
                by = "file not found"
            elif r["kind"] in ("composite", "offline_merge"):
                if rec.get("identity") is not None:
                    m, by = dict(rec), "recorded in run.json by the pipeline at the time"
                elif ctx:
                    m, by = (meas.composite_metrics(ctx, img) or {}), "recomputed from this file with the pipeline's own functions"
                if ctx:
                    dv = meas.divergence(ctx, Path(r["path"]), img)
                    m.update({k: dv.get(k) for k in ("outside_px", "outside_pct", "inside_pct", "same_size")})
                if r["kind"] == "offline_merge":
                    m.setdefault("judge", "not judged (offline merge, no Gemini call)")
            elif r["kind"] in ("head_raw", "head_send"):
                rm = meas.raw_metrics(ctx, img) or {}
                m, by = dict(rm), "recomputed from this crop; size and shift are the head crop's own framing against the source crop, not gates"
                if r["kind"] == "head_raw":
                    comp = recorded(d, idx)
                    m["comp_verdict"], m["comp_problems"] = comp.get("verdict"), comp.get("problems")
            elif r["kind"] == "gen":
                m, by = (meas.whole_identity(img) or {}), "recomputed from this picture (largest face); no source to compare"
            MEAS_CACHE[ckey] = (m, by)
        img = True if have_img else None    # from here on only 'is the file there' matters
        r["m"] = m
        r["measured_by"] = by
        r["idx"] = idx
        wins = ai_wins(run_dir)
        r["ai_rank"] = (f"this attempt {wins[idx]:g} (compared: " + ", ".join(f"attempt {k}: {v:g}" for k, v in wins.items()) + ")" if (idx in wins) else "")
        # validity: a complete picture with the source's dimensions and nothing changed outside the crop
        kind = r["kind"]
        if kind == "head_raw":
            r["valid"] = "NO - a head crop, not a picture"
        elif kind == "head_send":
            r["valid"] = "NO - the source crop, not an output"
        elif kind == "gen":
            r["valid"] = "YES (from scratch)" if img is not None else "NO - file missing"
        elif img is None:
            r["valid"] = "NO - file missing"
        elif m.get("same_size") is False:
            r["valid"] = "NO - dimensions differ from the source"
        elif m.get("outside_px") is not None:
            r["valid"] = "YES" if m["outside_px"] == 0 else f"NO - {m['outside_px']} px changed outside the crop"
        elif rec.get("outside_rec") == 0 and rec.get("same_size_rec"):
            r["valid"] = "YES (per run.json; crop not recorded)"
        else:
            r["valid"] = "UNKNOWN (no crop recorded)"
        if verbose and k % 20 == 0:
            print(f"  ...{k}/{len(rows)} rows measured")

    # ---- rank
    rows.sort(key=lambda r: (-r["points"], 0 if r["valid"].startswith("YES") else 1, -(r["m"].get("identity") or 0), r["id"]))
    n = 0
    for pos, r in enumerate(rows, 1):
        r["rank"] = pos
        if r["valid"].startswith("YES"):
            n += 1
            r["rank_valid"] = n
        else:
            r["rank_valid"] = None
    return rows
