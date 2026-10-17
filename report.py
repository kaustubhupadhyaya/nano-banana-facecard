"""One page per run, and the diff between two runs (the user, 2026-10-06/07: "unable to find images, put it somewhere else"; "each step of the image
generation pronounced and visible, so we can debug it later").

  write(run_dir)    report.html in the run folder: the 8 stages in order, each with its status, numbers and pictures (embedded, so the file stands alone)
  publish(run_dir)  copies it to paths.review_dir() as <collection>_<NN>_<title>__<stamp>.html and rebuilds index.html there (one flat folder)
  refresh(run_dir)  write + publish again (tools/best_check.py calls it after recording a checklist)
  diff(a, b)        what differs between two runs, stage by stage: the request first (prompt, files, model), then the code, then the outcomes

    .venv\\Scripts\\python.exe facecard.py diff <runA> <runB>
"""
from __future__ import annotations

import base64
import difflib
import html
import io
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import provenance as P

ROOT = Path(__file__).resolve().parent
STATUS_COLOUR = {"ok": "#1f7a3a", "failed": "#b3261e", "not_applicable": "#6b6b6b", "not_run": "#9a9a9a", "running": "#a36b00"}


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def img_uri(path: Path, max_w: int = 900, quality: int = 80) -> str | None:
    try:
        from PIL import Image
        with Image.open(path) as im:
            im = im.convert("RGB")
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=quality)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def img(path: Path, caption: str = "", max_w: int = 900) -> str:
    uri = img_uri(Path(path), max_w) if Path(path).is_file() else None
    if not uri:
        return f"<p class='muted'>(no picture: {esc(Path(path).name)})</p>"
    return f"<figure><img src='{uri}' alt='{esc(caption or Path(path).name)}'><figcaption>{esc(caption or Path(path).name)}</figcaption></figure>"


def table(rows: list[list], head: list[str]) -> str:
    out = ["<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c if isinstance(c, Raw) else esc(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


class Raw(str):
    """Already-escaped HTML for a table cell."""


def base_of(run_dir: Path) -> str:
    """<collection>_<NN>_<title> of the run's goal: from the recipe the run names (a run that stopped early has no goal in run.json yet)."""
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import export_results
    m = P.read_json(Path(run_dir) / "manifest.json", {}) or {}
    if (m.get("recipe") or {}).get("id"):
        return export_results.base_name(m["recipe"]["id"])
    run = P.read_json(Path(run_dir) / "run.json", {}) or {}
    return export_results.base_name(export_results.goal_key(run)) if run else Path(run_dir).name


def character_cell(cm) -> str:
    """The record-only character measures of one picture: each measure, and how far outside his band it is (when compared)."""
    if not cm:
        return "-"
    out = []
    for part in ("face", "body"):
        sub = cm.get(part) if isinstance(cm, dict) else None
        if not isinstance(sub, dict):
            continue
        for k, v in sub.items():
            if isinstance(v, dict) and "value" in v:
                val = v.get("value")
                if val is None:
                    continue
                flag = "" if v.get("inside", True) else f" <b class='bad'>off {esc(v.get('off_by'))}</b>"
                out.append(f"{esc(k)} {esc(round(val, 3) if isinstance(val, float) else val)}{flag}")
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ("yaw", "pitch", "roll", "face_px", "confidence"):
                out.append(f"{esc(k)} {esc(round(v, 3) if isinstance(v, float) else v)}")
    return "<br>".join(out) or "not measurable"


def write_replicate_tail(d: Path, parts: list, section, rec: dict) -> None:
    """Sections 05-08 of a replicate/1 run: attempts of the identical request, replicate's gates, the AI judge, the ranking."""
    calls = sorted((d / "05_generate").glob("call_*.json"), key=lambda p: int(p.stem.split("_")[1])) if (d / "05_generate").is_dir() else []
    rows, b = [], []
    for cp in calls:
        c = P.read_json(cp, {}) or {}
        cand = c.get("candidate") or {}
        m = cand.get("metrics") or {}
        merge = c.get("merge") or {}
        rows.append([c.get("index"), c.get("outcome"), c.get("secs"), c.get("credits_used"), "; ".join(f"{i.get('px')}" for i in c.get("images") or []),
                     merge.get("failed") or (f"merged (ecc {merge.get('ecc')})" if merge else ""), m.get("file") or "-",
                     Raw(f"<b class='{'ok' if cand.get('verdict') in ('accept', 'uncertain') else 'bad'}'>{esc(cand.get('verdict'))}</b>")])
    if rows:
        b.append(table(rows, ["attempt", "outcome", "secs", "credits", "returned px", "merged into the original", "picture", "verdict"]))
    for cp in calls:
        i = (P.read_json(cp, {}) or {}).get("index")
        b.append(img(d / "05_generate" / f"compare_head_{i}.jpg", f"attempt {i}: his photo's crop | the edited crop | difference x4", 1200))
    section(5, "".join(b))
    ms = P.read_json(d / "06_measure" / "measure.json", {}) or {}
    rows, b = [], []
    for s_ in ms.get("samples") or []:
        m = s_.get("metrics") or {}
        ro = s_.get("record_only") or {}
        lt = m.get("light") or {}
        hp = ro.get("head_pose") or {}
        rows.append([s_["file"], s_.get("verdict"), m.get("score"), m.get("gt_sim"), m.get("size_ratio"), m.get("face_shift_frac"), lt.get("dE"),
                     m.get("neck_gap"), (m.get("drift") or {}).get("ssim"), (s_.get("judge") or {}).get("notes"),
                     "; ".join(s_.get("problems") or []) or "none", (f"yaw {hp['yaw']:+.0f} pitch {hp['pitch']:+.0f}" if hp.get("detected") else "-"),
                     (ro.get("edge_step") or {}).get("max"), Raw(character_cell(ro.get("character_vs_band") or ro.get("character")))])
    if rows:
        b.append(table(rows, ["picture", "verdict", "identity (pool)", "similarity to his old face", "head size x", "head shift", "light dE",
                              "neck gap", "drift SSIM", "AI judge", "gate failures", "head pose", "edge step (record-only; kayak patches read 3.5-3.8)",
                              "character measures (record-only)"]))
        b.append(f"<p class='muted'>{esc(ms.get('rule'))}; gates {esc(json.dumps(ms.get('gates')))}</p>")
    for x in ms.get("not_merged") or []:
        b.append(f"<p>attempt {esc(x['index'])} not merged: {esc('; '.join(x.get('problems') or []))}</p>")
    section(6, "".join(b))
    rv = P.read_json(d / "07_review" / "review.json", {}) or {}
    b = []
    for s_ in ms.get("samples") or []:
        stem = Path(s_["file"]).stem
        chk = P.read_json(d / (s_["file"] + ".checklist.json"), None)
        verdict = chk.get("verdict") if chk else (rv.get("checklist") or {}).get(s_["file"], "not checked yet")
        b.append(f"<h3>{esc(s_['file'])} · checklist: {esc(verdict)}</h3>")
        if chk and chk.get("failed"):
            b.append("<p>Failed items on record: " + esc("; ".join(f"{k}" for k in chk["failed"])) + (f" · {esc(chk.get('note'))}" if chk.get("note") else "") + "</p>")
        if chk and chk.get("noted"):
            b.append("<p>Pointed out, not rejecting (the current look; the user, 2026-10-17): " + esc("; ".join(f"{k}" for k in chk["noted"]))
                     + (f" · {esc(chk.get('note'))}" if chk.get("note") and not chk.get("failed") else "") + "</p>")
        b.append(img(d / s_["file"], "the complete picture (full resolution, only the crop changed)", 1100))
        b.append(img(d / "07_review" / f"{stem}_details.jpg", "head row beside his references (items 19, 21, 28)", 1400))
        b.append(img(d / "07_review" / f"{stem}_character.jpg", "character sheet: face and torso beside the character's photos at the same scale (items 31, 32)", 1400))
    if rv.get("lines"):
        b.append("<pre>" + esc("\n".join(rv["lines"])) + "</pre>")
    section(7, "".join(b))
    res = P.read_json(d / "08_result" / "result.json", {}) or {}
    b = []
    if res.get("ranking"):
        b.append(table([[i + 1, c["file"], c["verdict"], c["sort_key"]["face_wins"], c["sort_key"]["band"], c["sort_key"]["identity"]]
                        for i, c in enumerate(res["ranking"])], ["rank", "picture", "verdict", "AI face wins", "band", "identity"]))
    b.append(f"<p>best.png: {esc((res.get('best') or {}).get('source') or 'none')} · rule: {esc(res.get('best_rule'))}</p>")
    exp = res.get("export")
    if exp is not None:
        b.append(f"<p>Export: {esc(exp if isinstance(exp, str) else ('; '.join(exp) or 'nothing to copy (no passed picture)'))}</p>")
    section(8, "".join(b))


# ------------------------------------------------------------------------------------------------------------------------------ write


def write(run_dir: Path) -> Path:
    d = Path(run_dir)
    m = P.read_json(d / "manifest.json", {}) or {}
    run = P.read_json(d / "run.json", {}) or {}
    rec = P.read_json(d / "01_method" / "recipe.json", {}) or {}
    method = P.read_json(d / "01_method" / "method.json", {}) or {}
    env = P.read_json(d / "01_method" / "env.json", {}) or {}
    st = {s["n"]: s for s in m.get("stages", [])}
    title = f"{base_of(d)} · run {d.name[:15]}"
    drift = m.get("method_drift")
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
             f"<meta name='facecard-status' content='{esc(m.get('status'))}'><meta name='facecard-goal' content='{esc(base_of(d))}'>"
             f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>",
             f"<h1>{esc(base_of(d))}</h1>",
             f"<p class='sub'>run <b>{esc(d.name)}</b> · {esc(m.get('kind'))} · status <b class='st-{esc(m.get('status'))}'>{esc(m.get('status'))}</b>"
             + (f" (stopped at stage {m.get('failed_stage'):02d})" if m.get("failed_stage") else "") + "</p>",
             f"<p class='sub'>recipe <b>{esc(rec.get('id'))} v{esc(rec.get('version'))}</b>: {esc(rec.get('because'))}</p>",
             f"<p class='sub mono'>request {esc(m.get('request_sha256'))}</p>"]
    route = (rec.get("method") or {}).get("route", "G")
    chm = method.get("character") or {}
    parts.append(f"<p class='sub'>method <b>{esc(route)}</b>{' (' + esc((rec.get('method') or {}).get('compiler')) + ')' if route != 'G' else ''}"
                 + (f" · character <b>{esc(chm.get('ref'))}</b>" if chm.get("ref") else " · no character (references chosen per goal)") + "</p>")
    cr0 = P.read_json(d / "04_credits" / "credits.json", {}) or {}
    if cr0.get("model_change"):
        parts.append(f"<p class='banner'>MODEL CHANGED: {esc(cr0['model_change'])}. Same request, a different model behind the same id.</p>")
    if drift:
        parts.append("<p class='banner'>METHOD DRIFT: today's code would compile this recipe into a different request. This run sent the recipe's "
                     "locked request; a new method needs <code>facecard.py recipe bump</code>. See 01 method below.</p>")
    # stage strip
    parts.append("<ol class='strip'>")
    for n in range(1, 9):
        s = st.get(n, {"name": "?", "status": "not_run"})
        parts.append(f"<li style='border-top-color:{STATUS_COLOUR.get(s.get('status'), '#999')}'><a href='#s{n}'><b>{n:02d} {esc(s.get('name'))}</b>"
                     f"<span>{esc(s.get('status'))}{' · ' + esc(s.get('secs')) + ' s' if s.get('secs') is not None else ''}</span></a></li>")
    parts.append("</ol>")

    def section(n: int, body: str) -> None:
        s = st.get(n, {})
        parts.append(f"<section id='s{n}'><h2><span class='dot' style='background:{STATUS_COLOUR.get(s.get('status'), '#999')}'></span>{n:02d} {esc(s.get('name'))}"
                     f" <small>{esc(s.get('status'))}</small></h2><p>{esc(s.get('summary') or '')}</p>"
                     + (f"<pre class='err'>{esc(s.get('error'))}</pre>" if s.get("error") else "") + body + "</section>")

    # 01 method
    b = []
    integ = method.get("integrity")
    b.append(f"<p>Integrity: <b>{esc('ok' if integ == 'ok' else integ)}</b></p>")
    dd = (method.get("drift") or {})
    b.append(f"<p>Drift: <b>{'none' if dd.get('same') else 'METHOD DRIFT'}</b> (prompt same: {esc(dd.get('same_prompt'))}, files same: {esc(dd.get('same_files'))})</p>")
    if (d / "01_method" / "drift.diff").is_file():
        b.append(f"<details open><summary>drift.diff</summary><pre>{esc((d / '01_method' / 'drift.diff').read_text(encoding='utf-8')[:20000])}</pre></details>")
    own = method.get("own_photo") or {}
    if own:
        b.append(f"<p>Own-photo check (Route G refuses his own photo): <b>{'his own photo' if own.get('own') else 'not his own photo' if own.get('own') is False else 'not applicable'}</b>: {esc(own.get('by'))}</p>")
    if chm.get("ref"):
        b.append(f"<p>Character <b>{esc(chm['ref'])}</b> ({esc((chm.get('sha256') or '')[:12])}): " + (esc("; ".join(chm["problems"])) if chm.get("problems") else "the references sent are the character's, unchanged") + "</p>")
    prev = method.get("earlier_runs_same_request") or []
    if prev:
        b.append(f"<p>Earlier runs that sent this same request: <b>{len(prev)}</b> ({esc(', '.join(p['run'] for p in prev[-6:]))}); "
                 "compare them with <code>facecard.py diff</code>.</p>")
    g = env.get("git") or {}
    b.append(table([["code", f"{g.get('commit', '')[:12]} on {g.get('branch')}" + (f", {len(g.get('dirty_files') or [])} uncommitted file(s)" if g.get("dirty_files") else "")],
                    ["python", env.get("python")], ["packages", ", ".join(f"{k} {v}" for k, v in (env.get("packages") or {}).items())],
                    ["YOLO venv", ", ".join(f"{k} {v}" for k, v in (env.get("yolo_venv") or {}).items())],
                    ["models", ", ".join(f"{k} {str(v)[:10]}" for k, v in (env.get("models") or {}).items())],
                    ["preflight", ", ".join(f"{p['what']}: {'ok' if p['ok'] else 'MISSING'}" for p in method.get("preflight") or [])]], ["", ""]))
    gl = env.get("gate_limits") or {}
    b.append(f"<details><summary>gate limits in effect</summary><pre>{esc(json.dumps(gl, indent=1))}</pre></details>")
    section(1, "".join(b))
    # 02 inputs
    b = []
    fc = (rec.get("inputs") or {}).get("face_choice") or {}
    if fc:
        b.append(f"<p>Face references: bin <b>{esc(fc.get('bin'))}</b>, decided by <b>{esc(fc.get('decided_by'))}</b>: {esc(fc.get('evidence'))}</p>")
        hp = fc.get("measured") or {}
        if hp.get("detected"):
            b.append(f"<p>Measured head turn of the goal (record-only): yaw {hp['yaw']:+.0f} ({esc(hp.get('side'))}), pitch {hp['pitch']:+.0f}, roll {hp['roll']:+.0f}</p>")
        if fc.get("warning"):
            b.append(f"<p class='banner'>FACE CHOICE: {esc(fc['warning'])}</p>")
    sd = d / "02_inputs"
    b.append(img(sd / "references.jpg", "everything sent, in order", 1400))
    goal_file = sd / Path((rec.get("goal") or {}).get("path", "x")).name
    if route == "replicate":
        b.append(img(sd / "crop_on_original.jpg", "his original photo: the frozen crop (green) is edited and pasted back, every other pixel stays", 1100))
    else:
        b.append("<div class='row'>" + img(goal_file, "the goal (pinned copy)", 600) + img(sd / "goal_pose.jpg", "the goal's measured skeleton", 600) + "</div>")
    refs = (rec.get("inputs") or {}).get("references") or []
    b.append(table([[r["n"], r["role"], r["name"], r["sha256"][:12], r.get("why", "")] for r in refs], ["image", "role", "file name sent", "sha256", "why"]))
    section(2, "".join(b))
    # 03 request
    b = []
    rq = P.read_json(d / "03_request" / "request.json", {}) or {}
    if (d / "03_request" / "prompt.txt").is_file():
        b.append(f"<details><summary>prompt ({len((d / '03_request' / 'prompt.txt').read_text(encoding='utf-8'))} characters)</summary>"
                 f"<pre>{esc((d / '03_request' / 'prompt.txt').read_text(encoding='utf-8'))}</pre></details>")
    b.append(f"<p class='mono'>request_sha256 {esc(rq.get('request_sha256'))} · model {esc(rq.get('model'))}</p>")
    lint = P.read_json(d / "03_request" / "lint.json", []) or []
    if lint:
        b.append("<ul>" + "".join(f"<li><b>{esc(x['level'])}</b> {esc(x['msg'])}</li>" for x in lint) + "</ul>")
    notices = P.read_json(d / "03_request" / "notices.json", []) or []
    if notices:
        b.append("<ul>" + "".join(f"<li>{esc(n[0])}: {esc(n[1])}</li>" for n in notices) + "</ul>")
    section(3, "".join(b))
    # 04 credits
    cr = P.read_json(d / "04_credits" / "credits.json", {}) or {}
    section(4, table([[k, json.dumps(v) if isinstance(v, (dict, list)) else v] for k, v in cr.items()], ["", ""]) if cr else "")
    if route == "replicate":
        write_replicate_tail(d, parts, section, rec)
        parts.append(f"<footer>written {datetime.now():%Y-%m-%d %H:%M} · run folder {esc(d)}</footer></main></body></html>")
        out = d / "report.html"
        out.write_text("".join(parts), encoding="utf-8")
        return out
    # 05 generate
    b = []
    calls = sorted((d / "05_generate").glob("call_*.json"), key=lambda p: int(p.stem.split("_")[1])) if (d / "05_generate").is_dir() else []
    rows = []
    for cp in calls:
        c = P.read_json(cp, {}) or {}
        ims = c.get("images") or []
        rows.append([c.get("index", 0) + 1, c.get("outcome"), c.get("secs"), c.get("credits_used"),
                     "; ".join(f"{i.get('file')} {i.get('px')} {'full size' if i.get('full_size') else 'PREVIEW'}{' c2pa' if i.get('c2pa_present') else ''}" for i in ims),
                     (c.get("text") or c.get("error") or "")[:300], len(c.get("library_log") or [])])
    if rows:
        b.append(table(rows, ["call", "outcome", "secs", "credits", "pictures", "reply / error", "library log lines"]))
    if run.get("remeasure_of"):
        b.append(f"<p>Re-measure of run {esc(run['remeasure_of'])}: no Gemini call.</p>")
    section(5, "".join(b))
    # 06 measure
    b = []
    ms = P.read_json(d / "06_measure" / "measure.json", {}) or {}
    rows = []
    for s_ in ms.get("samples") or []:
        lt = s_.get("light") or {}
        ro = s_.get("record_only") or {}
        rows.append([s_["file"], Raw(f"<b class='{'ok' if s_['pose_gate'] == 'PASS' else 'bad'}'>{esc(s_['pose_gate'])}</b>"), ", ".join(s_.get("pose_fails") or []), s_.get("identity"), s_.get("identity_status"),
                     lt.get("face_vs_goal"), f"{lt.get('face_neck')} vs {lt.get('goal_face_neck')}" if lt else "not measurable",
                     ro.get("faces_found"), ro.get("mean_grey_diff_to_goal"), ro.get("pool_identity_top3"),
                     (f"yaw {ro['head_pose']['yaw']:+.0f} pitch {ro['head_pose']['pitch']:+.0f}" if (ro.get("head_pose") or {}).get("detected") else "-"),
                     ((ro.get("c2pa") or {}).get("state") or "-"), Raw(character_cell(ro.get("character_vs_band") or ro.get("character")))])
    if rows:
        b.append(table(rows, ["picture", "pose gate", "failed items", "identity", "status", "face light x goal", "face/neck vs goal", "faces", "grey diff to goal", "pool identity", "head pose", "C2PA", "character measures (record-only)"]))
        b.append(f"<p class='muted'>identity rule: {esc((ms.get('identity_rule') or {}).get('accept'))}; light limits {esc(ms.get('light_limits'))}. "
                 "Record-only measures never reject a picture. Grey diff below about 10 with the face still the goal man's = the goal handed back.</p>")
        for s_ in ms.get("samples") or []:
            bad = [c for c in s_.get("pose_checks") or [] if not c.get("ok")]
            if bad:
                b.append(f"<p><b>{esc(s_['file'])}</b> pose gate: " + "; ".join(f"item {esc(c['item'])} {esc(c['name'])}: {esc(c['value'])} (limit {esc(c['limit'])})" for c in bad) + "</p>")
    section(6, "".join(b))
    # 07 review
    b = []
    rv = P.read_json(d / "07_review" / "review.json", {}) or {}
    for s_ in ms.get("samples") or []:
        stem = Path(s_["file"]).stem
        verdict = (rv.get("checklist") or {}).get(s_["file"], "not checked yet")
        chk = P.read_json(d / (s_["file"] + ".checklist.json"), None)
        if chk:
            verdict = chk.get("verdict")
        b.append(f"<h3>{esc(s_['file'])} · checklist: {esc(verdict)}</h3>")
        if chk and chk.get("user_approved"):
            b.append(f"<p>Approved by the user: {esc(chk['user_approved'].get('words'))}</p>")
        if chk and chk.get("user_rejected"):
            b.append(f"<p>Rejected by the user: {esc(chk['user_rejected'].get('words'))}</p>")
        if chk and chk.get("failed"):
            b.append("<p>Failed items on record: " + esc("; ".join(f"{k}" for k in chk["failed"])) + (f" · {esc(chk.get('note'))}" if chk.get("note") else "") + "</p>")
        if chk and chk.get("noted"):
            b.append("<p>Pointed out, not rejecting (the current look; the user, 2026-10-17): " + esc("; ".join(f"{k}" for k in chk["noted"]))
                     + (f" · {esc(chk.get('note'))}" if chk.get("note") and not chk.get("failed") else "") + "</p>")
        b.append("<div class='row'>" + img(d / s_["file"], "the picture", 600) + img(d / f"{stem}_pose.jpg", "pose gate overlay (green = goal, red = picture)", 900) + "</div>")
        b.append(img(d / "07_review" / f"{stem}_details.jpg", "head row beside his references (items 19, 21, 28) and the hands", 1400))
        b.append(img(d / "07_review" / f"{stem}_character.jpg", "character sheet: face and torso beside the character's photos at the same scale (items 31, 32)", 1400))
    lines = rv.get("lines") or []
    if lines:
        b.append("<pre>" + esc("\n".join(lines)) + "</pre>")
    section(7, "".join(b))
    # 08 result
    b = []
    res = P.read_json(d / "08_result" / "result.json", {}) or {}
    if res.get("ranking"):
        b.append(table([[i + 1, c["file"], c["sort_key"]["accepted"], c["sort_key"]["light_ok"], c["sort_key"]["identity"], c["pose_gate"]]
                        for i, c in enumerate(res["ranking"])], ["rank", "picture", "accepted", "light ok", "identity", "pose gate"]))
        b.append(f"<p>best.jpg: {esc((res.get('best') or {}).get('source') or 'none')} · rule: {esc(res.get('best_rule'))}</p>")
        exp = res.get("export")
        b.append(f"<p>Export: {esc(exp if isinstance(exp, str) else ('; '.join(exp) or 'nothing to copy (no passed picture)'))}</p>")
    section(8, "".join(b))
    parts.append(f"<footer>written {datetime.now():%Y-%m-%d %H:%M} · run folder {esc(d)}</footer></main></body></html>")
    out = d / "report.html"
    out.write_text("".join(parts), encoding="utf-8")
    return out


def publish(run_dir: Path) -> Path:
    import sys
    import paths
    sys.path.insert(0, str(ROOT / "tools"))
    import export_results
    d = Path(run_dir)
    dest = paths.review_dir()
    dest.mkdir(parents=True, exist_ok=True)
    m = P.read_json(d / "manifest.json", {}) or {}
    name = f"{base_of(d)}__{d.name[:15]}" + ("_remeasure" if m.get("kind") == "remeasure" else "") + (d.name[15:] if re.search(r"_\d+$", d.name[15:]) else "") + ".html"
    target = dest / name
    shutil.copyfile(d / "report.html", target)
    with export_results.locked(dest):
        write_index(dest)
    return target


def write_index(dest: Path) -> None:
    rows = []
    for f in sorted(dest.glob("*__*.html"), key=lambda p: p.name, reverse=True):
        head = f.read_text(encoding="utf-8", errors="replace")[:1200]
        stt = re.search(r"facecard-status' content='([^']*)'", head)
        goal = f.name.split("__")[0]
        rows.append((goal, f.name, stt.group(1) if stt else "?"))
    by: dict[str, list] = {}
    for goal, name, s in rows:
        by.setdefault(goal, []).append((name, s))
    body = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>Facecard runs</title><style>{CSS}</style></head><body><main><h1>Facecard runs</h1>"
            "<p class='sub'>Every staged run's report, newest first. Passed pictures are in D:\\FacecardResults.</p>"]
    for goal in sorted(by):
        body.append(f"<h2>{esc(goal)}</h2><ul>")
        for name, s in by[goal]:
            body.append(f"<li><a href='{esc(name)}'>{esc(name.split('__')[1].replace('.html', ''))}</a> · <span class='st-{esc(s)}'>{esc(s)}</span></li>")
        body.append("</ul>")
    body.append("</main></body></html>")
    (dest / "index.html").write_text("".join(body), encoding="utf-8")


def refresh(run_dir: Path) -> None:
    d = Path(run_dir)
    if not (d / "manifest.json").is_file():
        return
    write(d)
    if (P.read_json(d / "manifest.json", {}) or {}).get("kind") != "dry-run":
        publish(d)


# ------------------------------------------------------------------------------------------------------------------------------ diff


def request_of_run(d: Path) -> tuple[dict | None, str]:
    """The exact request a run sent: its 03_request/request.json (staged runs), or the lock of the recipe imported from it (legacy runs)."""
    rq = P.read_json(d / "03_request" / "request.json", None)
    if rq:
        return rq, "03_request/request.json"
    import recipe as R
    for vp in sorted(R.RECIPES.glob("*/*/v*.json")):
        rec = P.read_json(vp, {}) or {}
        if (rec.get("origin") or {}).get("run") == d.name:
            return {**R.request_of(rec["lock"]), "request_sha256": rec["lock"]["request_sha256"]}, f"recipe {vp.relative_to(ROOT)} (imported from this run)"
    run = P.read_json(d / "run.json", {}) or {}
    if run.get("prompt"):
        return {"model": run.get("model"), "prompt": run["prompt"], "files": [{"upload_name": n, "sha256": None} for n in run.get("refs", [])]}, "run.json (partial: no file hashes)"
    return None, "nothing recorded"


def samples_of(d: Path) -> list[dict]:
    ms = P.read_json(d / "06_measure" / "measure.json", None)
    if ms:
        return ms.get("samples") or []
    run = P.read_json(d / "run.json", {}) or {}
    gate = {Path(g.get("render", "")).name: g for g in run.get("pose_gate") or []}
    out = []
    for r in run.get("results") or []:
        for e in r.get("evaluations") or []:
            g = gate.get(e.get("raw_file"))
            out.append({"file": e.get("raw_file"), "identity": e.get("raw_score"), "identity_status": e.get("status"),
                        "pose_gate": ("PASS" if g and not g.get("fails") else ("FAIL" if g else "?")), "light": e.get("light"), "pose_checks": (g or {}).get("checks", [])})
    return out


def diff(a: Path, b: Path) -> str:
    a, b = Path(a), Path(b)
    out = [f"A {a.name}\nB {b.name}\n"]
    ra, wa = request_of_run(a)
    rb, wb = request_of_run(b)
    out.append(f"REQUEST  A from {wa}\n         B from {wb}")
    if ra and rb:
        ha, hb = ra.get("request_sha256"), rb.get("request_sha256")
        same = bool(ha and hb and ha == hb)
        out.append(f"  request_sha256  A {ha}\n                  B {hb}\n  -> {'IDENTICAL request (same model, prompt and file bytes)' if same else 'DIFFERENT request'}")
        if not same:
            if ra.get("model") != rb.get("model"):
                out.append(f"  model: {ra.get('model')} -> {rb.get('model')}")
            fa = [(f.get("upload_name"), (f.get("sha256") or "")[:12]) for f in ra.get("files", [])]
            fb = [(f.get("upload_name"), (f.get("sha256") or "")[:12]) for f in rb.get("files", [])]
            if fa != fb:
                out.append("  files:")
                out += ["    " + ln.rstrip("\n") for ln in difflib.unified_diff([f"{x[0]} {x[1]}\n" for x in fa], [f"{x[0]} {x[1]}\n" for x in fb], "A", "B", n=0)]
            if ra.get("prompt") != rb.get("prompt"):
                out.append("  prompt:")
                out += ["    " + ln.rstrip("\n") for ln in difflib.unified_diff(str(ra.get("prompt")).splitlines(True), str(rb.get("prompt")).splitlines(True), "A", "B", n=1)]
    ea, eb = P.read_json(a / "01_method" / "env.json", None), P.read_json(b / "01_method" / "env.json", None)
    if ea and eb:
        ch = []
        if (ea.get("git") or {}).get("commit") != (eb.get("git") or {}).get("commit") or (ea.get("git") or {}).get("diff_sha256") != (eb.get("git") or {}).get("diff_sha256"):
            ch.append(f"code {ea['git'].get('commit', '')[:12]} (diff {str(ea['git'].get('diff_sha256'))[:8]}) -> {eb['git'].get('commit', '')[:12]} (diff {str(eb['git'].get('diff_sha256'))[:8]})")
        for k in sorted(set(ea.get("packages") or {}) | set(eb.get("packages") or {})):
            if (ea.get("packages") or {}).get(k) != (eb.get("packages") or {}).get(k):
                ch.append(f"{k} {(ea.get('packages') or {}).get(k)} -> {(eb.get('packages') or {}).get(k)}")
        if ea.get("gate_limits") != eb.get("gate_limits"):
            ch.append("gate limits changed")
        out.append("CODE / ENVIRONMENT: " + ("same" if not ch else "; ".join(ch)))
    else:
        out.append("CODE / ENVIRONMENT: not recorded for " + " and ".join(x.name for x, e in ((a, ea), (b, eb)) if not e) + " (runs before 2026-10-07)")
    sa, sb = samples_of(a), samples_of(b)
    out.append("OUTCOMES (pictures differ by nature: Gemini cannot be seeded)")
    for label, ss in (("A", sa), ("B", sb)):
        for s in ss:
            lt = s.get("light") or {}
            out.append(f"  {label} {s.get('file')}: pose gate {s.get('pose_gate')}, identity {s.get('identity') if s.get('identity') is None else round(s['identity'], 4)} "
                       f"{s.get('identity_status')}, light x{lt.get('face_vs_goal')} face/neck {lt.get('face_neck')}")
    sha = lambda d_, f_: P.sha256_file(d_ / f_) if f_ and (d_ / f_).is_file() else None
    same_pictures = bool(sa) and [sha(a, s.get("file")) for s in sa] == [sha(b, s.get("file")) for s in sb] and None not in [sha(a, s.get("file")) for s in sa]
    if not same_pictures:
        out.append("  -> different pictures (new samples of the request): compare them on the two reports, item by item")
    if same_pictures:
        same_measures = all(
            (x.get("identity") is None and y.get("identity") is None or (x.get("identity") is not None and y.get("identity") is not None and abs(x["identity"] - y["identity"]) < 1e-6))
            and x.get("pose_gate") == y.get("pose_gate")
            and [(c.get("name"), c.get("value")) for c in x.get("pose_checks") or []] == [(c.get("name"), c.get("value")) for c in y.get("pose_checks") or []]
            and (x.get("light") or {}).get("face_vs_goal") == (y.get("light") or {}).get("face_vs_goal")
            and (x.get("light") or {}).get("face_neck") == (y.get("light") or {}).get("face_neck") for x, y in zip(sa, sb))
        out.append(f"  -> the same pictures (byte-identical) measured twice: {'IDENTICAL measures' if same_measures else 'measures DIFFER: the measuring code or its inputs changed'}")
    return "\n".join(out)


CSS = """
:root{--bg:#fbfbf9;--fg:#1c1c1a;--muted:#6b6b66;--line:#e2e1dc;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29c;--line:#34332f;--card:#1f1f1d}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1500px;margin:0 auto;padding:16px}h1{font-size:1.5rem;margin:.2em 0}h2{font-size:1.15rem;margin:1.6em 0 .4em;display:flex;gap:.5em;align-items:center}
h2 small{color:var(--muted);font-weight:400}.sub{margin:.2em 0;color:var(--muted)}.mono{font-family:ui-monospace,Consolas,monospace;font-size:.85rem}
.banner{background:#b3261e;color:#fff;padding:10px 14px;border-radius:6px}.dot{width:12px;height:12px;border-radius:50%;display:inline-block}
.strip{list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.strip li{background:var(--card);border:1px solid var(--line);border-top:5px solid;border-radius:6px;padding:8px}
.strip a{color:inherit;text-decoration:none;display:flex;flex-direction:column}.strip span{color:var(--muted);font-size:.85rem}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px 16px 14px;margin:12px 0;overflow-x:auto}
table{border-collapse:collapse;font-size:.85rem;margin:8px 0;width:100%}th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--line);padding:10px;border-radius:6px;font-size:.8rem;max-height:520px;overflow:auto}
pre.err{border-color:#b3261e}figure{margin:8px 0}figure img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:4px}
figcaption{color:var(--muted);font-size:.8rem}.row{display:flex;flex-wrap:wrap;gap:12px}.row figure{flex:1 1 320px}
.ok{color:#1f7a3a}.bad{color:#b3261e}.muted{color:var(--muted);font-size:.85rem}.st-failed{color:#b3261e}.st-done{color:#1f7a3a}
footer{color:var(--muted);font-size:.8rem;margin:24px 0}a{color:#2a5db0}
"""
