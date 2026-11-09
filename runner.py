"""Staged runs (the user, 2026-10-07): "even if the generation is faulty, it is still consistent; the method is followed consistently each time, so that
each step of the image generation is very pronounced and visible, which can help us debug this later easily."

    .venv\\Scripts\\python.exe facecard.py run <recipe ref | run folder> [--samples N] [--dry-run] [--remeasure <run>] [--wait-max S | --no-wait | --no-guard]

Every run goes through the same 8 numbered stages, in this order, and every stage leaves its evidence in the run folder:

    01_method    the recipe copy, its integrity (hand-edited lock? missing blob?), METHOD DRIFT (today's compiler vs the lock), env.json, preflight
    02_inputs    the pinned goal and its measurement, references.jpg ("Image N - ROLE - name - why")
    03_request   prompt.txt, request.json (request_sha256), the exact files sent (sent/NN/<upload name>), the inventory lint
    04_credits   authentication, account, model availability, the credit guard's decision
    05_generate  one record per Gemini call: outcome, reply text, conversation ids, image size, full-size or preview, retries, credits
    06_measure   pose gate (fixed limits), identity (the rule gen always applied), light, and record-only measures
    07_review    audit sheets per picture (head row beside his references), checklist status
    08_result    the ranking with every sort key, best.jpg (never a picture that failed the pose gate), export and ledger lines

plus manifest.json (each stage's status, time, inputs and outputs with sha256; rewritten after every stage), run.log (everything printed and
gemini_webapi's own log lines, secrets redacted), run.json (the legacy record every tool reads) and report.html, which is also published to
paths.review_dir(). The run sends the recipe's LOCK, byte for byte. A stage that cannot run fails the run visibly; nothing is skipped silently.
Exit codes: 0 done, 1 no picture / authentication, 2 the method stage refused (before any credit), 3 credit guard refused, 4 a later stage failed.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import provenance as P
import recipe as R

ROOT = Path(__file__).resolve().parent
STAGES = [(1, "method"), (2, "inputs"), (3, "request"), (4, "credits"), (5, "generate"), (6, "measure"), (7, "review"), (8, "result")]
# gen's identity rule on Route G, reproduced exactly (restore is forced off there, so sharpness is never checked for a non-profile face)
IDENTITY_RULE = {"accept": "ArcFace max cosine vs the FACE references sent >= identity_threshold (facecard.json, 0.60)",
                 "profile_accept": "profile faces: >= 0.50 and YuNet sharpness >= 200", "profile_min": 0.50, "profile_sharpness_min": 200.0,
                 "note": "a bowed or hidden face scores low even when it is him: identity is judged by eye on 07_review (checklist item 21)"}
# Which IMAGE model drew a picture is not in the reply, the library or the C2PA manifest (checked 2026-10-08). gemini_webapi picks only the CHAT
# model; the app picks the image model from it. Google: AI Pro accounts draw with Nano Banana 2.1 since its rollout began on 2026-10-06.
IMAGE_MODEL_NOTE = ("image model: not reported by the app; the chat model decides it (Google, 2026-10-06: Nano Banana 2.1 for AI Pro accounts, "
                    "Nano Banana Pro only through the app's 'Redo with Pro', which the library cannot reach)")
MODELS_SEEN = ROOT / ".cache" / "models_seen.json"


def note_model_change(run: "Run", rec: dict, info: dict) -> None:
    """MODEL CHANGED (2026-10-08): the same model id now lists under another name than the recipe was frozen with, or than the last run saw
    (the flash id 56fdd199312815e2 lists as '3.8 Flash' since Google swapped the model behind it). Shown in stage 04, never a stop."""
    listed = info["model_listed"].get("display_name") if isinstance(info.get("model_listed"), dict) else None
    info["image_model"] = IMAGE_MODEL_NOTE
    model = rec["lock"]["model"]
    seen = P.read_json(MODELS_SEEN, {}) or {}
    frozen = (rec["method"].get("model") or {}).get("display")
    before = frozen or (seen.get(model) or {}).get("display_name")
    if listed and before and listed != before:
        info["model_change"] = (f"recipe frozen on '{frozen}'" if frozen else f"the last run saw '{before}' ({(seen.get(model) or {}).get('seen')})") + f"; the account now lists '{listed}'"
        print(f"MODEL CHANGED: {info['model_change']}")
    if listed:
        seen[model] = {"display_name": listed, "seen": now()}
        with contextlib.suppress(Exception):
            P.atomic_write_json(MODELS_SEEN, seen)
    run.manifest["model_display"] = listed


class StageFail(Exception):
    def __init__(self, msg: str, code: int = 4):
        super().__init__(msg)
        self.code = code


# Exit code of a run whose Gemini sign-in failed (2026-10-10): every later run of a wave would fail the same way, so tools/wave.py checks the
# session again and halts instead of starting the next run. 1 stays "no picture", 2 the method refused, 3 the credit guard refused.
SIGN_IN_FAILED = 5
FAILURES = Path(__file__).resolve().parent / ".cache" / "failures.jsonl"


def record_failure(run: "Run") -> None:
    """One line in .cache/failures.jsonl for a run that ended without an accepted picture (the user, 2026-10-10: "Keep a record of why each of
    those is happening"). The why is added by hand in FAILURE_LOG.md; this line is the evidence: stage, error, credits, the pose gate."""
    if run.kind != "run":
        return
    m = run.manifest
    stages = {s["n"]: s for s in m["stages"]}
    best = (run.legacy or {}).get("best")
    if run.code == 0 and m.get("status") == "done" and best:
        return
    row = {"time": now(), "run": m["run"], "recipe": f"{m['recipe']['id']}@v{m['recipe']['version']}", "exit": run.code,
           "status": m.get("status"), "failed_stage": m.get("failed_stage"),
           "error": next((s.get("error") for s in m["stages"] if s.get("error")), None),
           "generate": (stages.get(5) or {}).get("summary"), "measure": (stages.get(6) or {}).get("summary"),
           "result": (stages.get(8) or {}).get("summary")}
    with contextlib.suppress(Exception):
        FAILURES.parent.mkdir(parents=True, exist_ok=True)
        with FAILURES.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Run:
    """One run folder: the manifest, the legacy run.json mirror, and the stage context manager."""

    def __init__(self, run_dir: Path, kind: str, rec: dict, rec_path: Path, argv: list[str]):
        self.dir, self.kind, self.rec = run_dir, kind, rec
        self.manifest = {"schema": "facecard.run/1", "run": run_dir.name, "kind": kind, "status": "running", "failed_stage": None, "argv": argv,
                         "started": now(), "ended": None,
                         "recipe": {"ref": str(rec_path), "id": rec["id"], "version": rec["version"], "adhoc": rec.get("origin", {}).get("kind") == "adhoc",
                                    "file_sha256": P.sha256_file(rec_path) if Path(rec_path).is_file() else None, "because": rec.get("because")},
                         "request_sha256": rec["lock"]["request_sha256"], "env_sha256": None, "method_drift": None,
                         "stages": [{"n": n, "name": name, "status": "not_run"} for n, name in STAGES]}
        self.legacy: dict = {"timestamp": run_dir.name[:15], "prompt": rec["lock"]["prompt"], "subject": rec["method"].get("subject"),
                             "refs": [f["upload_name"] for f in rec["lock"]["files"] if f["role"] == "face"], "scene_image": None,
                             "model": rec["lock"]["model"], "results": [], "route_g": {"goal": rec["goal"]["path"]},
                             "recipe": {"id": rec["id"], "version": rec["version"], "adhoc": self.manifest["recipe"]["adhoc"],
                                        "request_sha256": rec["lock"]["request_sha256"], "file": str(rec_path)}}
        self.code = 0

    def stage_dir(self, n: int) -> Path:
        d = self.dir / f"{n:02d}_{STAGES[n - 1][1]}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self) -> None:
        P.atomic_write_json(self.dir / "manifest.json", self.manifest)
        self.legacy["status"] = "guard_refused" if self.code == 3 else self.manifest["status"]
        P.atomic_write_json(self.dir / "run.json", self.legacy, indent=2)

    def mark(self, n: int, status: str, summary: str) -> None:
        s = self.manifest["stages"][n - 1]
        s.update({"status": status, "summary": summary})
        self.save()

    @contextlib.contextmanager
    def stage(self, n: int):
        s = self.manifest["stages"][n - 1]
        s.update({"status": "running", "started": now()})
        self.save()
        t0 = time.time()
        print(f"\n[{n:02d}/08 {s['name']}]", flush=True)
        try:
            yield s
            if s["status"] == "running":
                s["status"] = "ok"
        except StageFail as e:
            s.update({"status": "failed", "error": str(e)})
            self.manifest.update({"status": "failed", "failed_stage": n})
            self.code = e.code
            raise
        except Exception as e:
            s.update({"status": "failed", "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()[-3000:]})
            self.manifest.update({"status": "failed", "failed_stage": n})
            self.code = 4
            raise
        finally:
            s["secs"] = round(time.time() - t0, 1)
            print(f"[{n:02d}/08 {s['name']}] {s['status'].upper()}: {s.get('summary') or s.get('error') or ''} ({s['secs']} s)", flush=True)
            self.save()

    def io(self, s: dict, kind: str, path: Path, what: str = "") -> None:
        p = Path(path)
        entry = {"what": what, "path": str(p.relative_to(self.dir) if self.dir in p.resolve().parents else p),
                 "sha256": P.sha256_file(p) if p.is_file() else None}
        s.setdefault(kind, []).append(entry)


# ------------------------------------------------------------------------------------------------------------------------------ helpers


def new_run_dir(kind: str, goal_stem: str) -> Path:
    import facecard
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = {"run": ROOT / "outputs", "dry-run": ROOT / ".cache" / "dryrun", "remeasure": ROOT / ".cache" / "remeasure"}[kind]
    base.mkdir(parents=True, exist_ok=True)
    name = f"{stamp}_{facecard.slugify('goal ' + goal_stem)}"
    d, k = base / name, 1
    while True:                     # atomic: parallel runs of one goal in the same second never share a folder
        try:
            d.mkdir(exist_ok=False)
            return d
        except FileExistsError:
            k += 1
            d = base / f"{name}_{k}"


def sheet_of_refs(lock: dict, rec: dict, staged: dict[int, Path], out: Path) -> None:
    """references.jpg: every file sent, in order, labelled 'Image N - ROLE - name' with the reason it was chosen."""
    import cv2
    import numpy as np
    refs = {r["n"]: r for r in rec["inputs"]["references"]}
    tiles = []
    for f in lock["files"]:
        img = cv2.imdecode(np.fromfile(str(staged[f["n"]]), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        h = 360
        img = cv2.resize(img, (max(1, int(img.shape[1] * h / img.shape[0])), h), interpolation=cv2.INTER_AREA)
        w = max(img.shape[1], 300)
        canvas = np.full((h + 74, w, 3), 255, np.uint8)
        canvas[74:, :img.shape[1]] = img
        cv2.putText(canvas, f"Image {f['n']} - {f['role'].upper().replace('_', ' ')}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2, cv2.LINE_AA)
        cv2.putText(canvas, f["upload_name"][:42], (6, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        why = (refs.get(f["n"]) or {}).get("why", "")
        cv2.putText(canvas, why[:46], (6, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (90, 90, 90), 1, cv2.LINE_AA)
        tiles.append(canvas)
    if not tiles:
        return
    rows, row, width = [], [], 0
    for t in tiles:
        if width + t.shape[1] > 2200 and row:
            rows.append(row)
            row, width = [], 0
        row.append(t)
        width += t.shape[1] + 8
    rows.append(row)
    W = max(sum(t.shape[1] + 8 for t in r) for r in rows)
    out_rows = []
    for r in rows:
        line = np.hstack([np.hstack([t, np.full((t.shape[0], 8, 3), 255, np.uint8)]) for t in r])
        out_rows.append(np.hstack([line, np.full((line.shape[0], W - line.shape[1], 3), 255, np.uint8)]))
    cv2.imwrite(str(out), np.vstack(out_rows), [cv2.IMWRITE_JPEG_QUALITY, 88])


def face_count_and_size(img) -> tuple[int, list[int] | None]:
    import cv2
    from scorer import DETECTOR_PATH
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.6)
    det.setInputSize((w, h))
    _, faces = det.detect(img)
    if faces is None or len(faces) == 0:
        return 0, None
    big = max(faces, key=lambda f: f[2] * f[3])
    return int(len(faces)), [int(big[2]), int(big[3])]


def grey_diff_to_goal(img, goal) -> float:
    import cv2
    g = cv2.resize(goal, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
    a, b = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype("float32"), cv2.cvtColor(g, cv2.COLOR_BGR2GRAY).astype("float32")
    return round(float(abs(a - b).mean()), 2)


def identity_status(score, info: dict, threshold: float) -> str:
    """The rule gen has always applied on Route G (restore off): see IDENTITY_RULE."""
    if info.get("is_profile"):
        return "accepted" if (score is not None and score >= IDENTITY_RULE["profile_min"] and info.get("sharpness", 0.0) >= IDENTITY_RULE["profile_sharpness_min"]) else "rejected"
    return "accepted" if (score and score >= threshold) else "rejected"


def image_record(path: Path) -> dict:
    from PIL import Image
    b = path.read_bytes()
    rec = {"file": path.name, "bytes": len(b), "sha256": P.sha256_bytes(b), "c2pa_present": b"c2pa" in b}
    with contextlib.suppress(Exception):
        with Image.open(path) as im:
            rec["px"] = list(im.size)
            uid = im.getexif().get(0xA420)
            if uid:
                rec["image_unique_id"] = str(uid)
    return rec


# ------------------------------------------------------------------------------------------------------------------------------ the run


async def run(ref: str, samples: int | None = None, dry_run: bool = False, remeasure: str | None = None, no_guard: bool = False,
              no_wait: bool = False, wait_max: float = 21600.0, stop_after_fails: int | None = None, verbose: bool = False, argv=None) -> int:
    import facecard
    rec, rec_path = R.load(ref)
    if not dry_run and not remeasure:
        # the retrospective of 2026-10-17 (RETROSPECTIVE_2026-10-17.md): every picture of the user's best set took at most two generation passes (one
        # whole render, at most one small fix); the ones that went downhill were edits stacked on edits (pin 14: six). An edit of an edit is refused
        # before any credit is spent, unless the user asked for that exact edit (FACECARD_DEEP_EDIT_OK = their words; wave.py sets it from a job's
        # "deep_edit_ok").
        import os
        sys.path.insert(0, str(ROOT / "tools"))
        ok_words = os.environ.get("FACECARD_DEEP_EDIT_OK", "").strip()
        try:
            import edit_depth
            n_out, behind = edit_depth.recipe_output_depth(rec)
            too_deep = n_out > edit_depth.MAX_DEPTH
            why = (f"would make pictures of {n_out} generation passes (limit {edit_depth.MAX_DEPTH}: one render plus one fix); what it edits is "
                   f"already an edit: {' <- '.join(behind)}. Make a new whole render instead")
        except Exception as exc:          # refused as well: no credit goes to a picture whose passes cannot be counted
            n_out, too_deep = "unknown", True
            why = f"has a lineage the guard cannot read ({type(exc).__name__}: {exc}). Fix tools/edit_depth.py for it"
        if too_deep and not ok_words:
            print(f"REFUSED: recipe {rec['id']} v{rec['version']} {why}, or run it with FACECARD_DEEP_EDIT_OK set to the user's own words asking "
                  f"for this edit.")
            return 7
        if too_deep:
            print(f"deep edit allowed by the user ({ok_words[:160]}): {n_out} passes")
        # facecard.py checks the hold first; this stops a caller that reaches run() some other way (the user, 2026-10-17: "Do not generate")
        hold = ROOT / ".cache" / "GENERATION_HOLD"
        pass_ref, _, pass_words = os.environ.get("FACECARD_HOLD_PASS", "").partition("::")   # the one-run pass of facecard.py, for this exact ref only
        if hold.exists() and not (pass_ref and pass_ref == ref and pass_words.strip()):
            print(f"HOLD: image generation is stopped by the user ({hold.read_text(encoding='utf-8', errors='replace').strip()[:200]}); "
                  f"remove {hold} only on the user's word", file=sys.stderr)
            return 6
    kind = "dry-run" if dry_run else ("remeasure" if remeasure else "run")
    goal_stem = Path(rec["goal"]["path"]).stem
    run_dir = new_run_dir(kind, goal_stem)
    run = Run(run_dir, kind, rec, rec_path, list(argv if argv is not None else sys.argv))
    run.save()
    import paths
    print(f"RUN {run_dir}")
    print(f"recipe {rec['id']} v{rec['version']} ({rec.get('because') or ''})")
    print(f"request {rec['lock']['request_sha256']}")
    with P.attach_run_log(run_dir):
        try:
            await _stages(run, rec, rec_path, facecard, samples, remeasure, no_guard, no_wait, wait_max, stop_after_fails, verbose, dry_run)
            if run.manifest["status"] == "running":
                run.manifest["status"] = {"dry-run": "dry-run", "remeasure": "remeasure"}.get(kind, "done")
        except StageFail as e:
            # a StageFail raised outside a stage block (the authentication failure) keeps its code too: on 2026-10-10 a run that never
            # generated exited 0 and the wave logged it as "exit 0 (rendered)"
            if not run.code:
                run.code = e.code
            if run.manifest.get("status") == "running":
                run.manifest["status"] = "failed"
            print(f"\nSTOPPED at stage {run.manifest['failed_stage']:02d}: {e}")
        except Exception as e:      # an unexpected error is still a visible, recorded stage failure
            print(f"\nSTOPPED at stage {run.manifest.get('failed_stage')}: {type(e).__name__}: {e}")
            if not run.code:
                run.code = 4
        finally:
            run.manifest["ended"] = now()
            run.save()
            record_failure(run)
            try:
                import report
                path = report.write(run_dir)
                print(f"\nREPORT {path}")
                if kind != "dry-run":
                    pub = report.publish(run_dir)
                    print(f"REVIEW {pub}  (all runs: {paths.review_dir() / 'index.html'})")
            except Exception as exc:
                print(f"[report] could not be written: {type(exc).__name__}: {exc}")
    return run.code


async def _stages(run: Run, rec: dict, rec_path: Path, facecard, samples, remeasure, no_guard, no_wait, wait_max, stop_after_fails, verbose, dry_run):
    import cv2
    import numpy as np
    config = facecard.apply_subject(facecard.load_config(), rec["method"].get("subject") or "me")
    lock = rec["lock"]
    d = run.dir
    n_samples = int(samples or rec["method"].get("samples") or 1)
    stop_n = int(rec["method"]["stop"].get("after_pose_fails") or 0) if stop_after_fails is None else int(stop_after_fails)
    run.manifest["controls"] = {"samples": n_samples, "stop_after_pose_fails": stop_n, "stop_on_pass": bool(rec["method"]["stop"].get("on_pass")),
                                "guard": "off" if no_guard else ("no wait" if no_wait else f"wait up to {wait_max:.0f} s")}

    # ---------------------------------------------------------------- 01 method
    with run.stage(1) as s:
        sd = run.stage_dir(1)
        shutil.copyfile(rec_path, sd / "recipe.json")
        run.io(s, "outputs", sd / "recipe.json", "the recipe version, byte copy")
        problems = R.check_integrity(rec)
        dr = R.drift(rec)
        env, diff = P.env_snapshot(config, run.manifest["argv"])
        P.atomic_write_json(sd / "env.json", env)
        run.manifest["env_sha256"] = P.sha256_file(sd / "env.json")
        if diff:
            P.write_bytes_atomic(sd / "dirty.patch", diff.encode("utf-8"))
        if not dr["same"]:
            P.write_text_lf(sd / "drift.diff", (dr.get("prompt_diff") or "") + ("\nFILES\n" + json.dumps(dr.get("files_diff"), indent=1) if dr.get("files_diff") else ""))
        run.manifest["method_drift"] = not dr["same"]
        # earlier runs that sent this exact request (any recipe version or ad-hoc run with the same lock): the consistency check across runs
        prev = [r for r in R.runs_of(rec["id"]) if r["request"] == lock["request_sha256"] and r["run"] != d.name]
        origin_run = (rec.get("origin") or {}).get("run")
        if origin_run and (rec.get("origin") or {}).get("kind") == "import-run" and origin_run not in {r["run"] for r in prev}:
            prev.insert(0, {"run": origin_run, "version": 0, "adhoc": False, "request": lock["request_sha256"]})     # proven equal at import
        pre: list[dict] = []
        paths_ok(pre)
        # the method must fit the goal (2026-10-08): his own photo is never sent through Route G (the step where the own-photo pictures went downhill)
        route = rec["method"].get("route", "G")
        own = R.own_photo_of(rec) if route == "G" else {"own": None, "by": "replicate/1 recipe"}
        # the character (2026-10-08): the recipe's references must be the character's, unchanged
        ch_check = R.character_check(rec)
        method = {"integrity": problems or "ok", "drift": {k: v for k, v in dr.items() if k not in ("prompt_diff",)},
                  "earlier_runs_same_request": [{"run": r["run"], "version": r["version"], "adhoc": r["adhoc"]} for r in prev],
                  "preflight": pre, "route": route, "own_photo": own, "character": ch_check}
        P.atomic_write_json(sd / "method.json", method)
        if problems:
            raise StageFail("the recipe cannot be sent as it is: " + "; ".join(problems), code=2)
        inv_data = (rec["inputs"].get("inventory") or {}).get("data") or {}
        region_edit = inv_data.get("mode") == "objects" and bool(inv_data.get("region_edit"))   # a crop pasted back (recipe.from_gen_args)
        if route == "G" and own.get("own") and not region_edit:
            raise StageFail(f"own photo ({own['by']}): method must be replicate. Route G sends the whole photo and redraws every pixel; make a "
                            "replicate/1 recipe: facecard.py recipe new --method replicate --goal <photo> --character me@v1 --because \"...\"", code=2)
        if ch_check.get("problems"):
            raise StageFail("character: " + "; ".join(ch_check["problems"]), code=2)
        if pre and not dry_run and any(not p["ok"] for p in pre):
            raise StageFail("preflight: " + "; ".join(p["what"] + ": " + p["detail"] for p in pre if not p["ok"]), code=2)
        s["summary"] = (f"recipe {rec['id']} v{rec['version']} intact; method {route}" + (f" ({rec['method'].get('compiler')})" if route != "G" else "")
                        + (f"; character {ch_check['ref']}" if ch_check.get("ref") else "; no character (references chosen per goal)") + "; "
                        + ("METHOD DRIFT: today's compiler differs from the lock (the lock is sent; see drift.diff)"
                        if not dr["same"] else "no drift") + f"; code {env['git']['commit'][:12]}{' +dirty' if env['git']['dirty_files'] else ''}"
                        + (f"; {len(prev)} earlier run(s) sent this same request" if prev else ""))
        if not dr["same"]:
            print("METHOD DRIFT: the recipe's inputs compile to a different request with today's code; the run sends the recipe's lock.")

    # ---------------------------------------------------------------- 02 inputs
    with run.stage(2) as s:
        sd = run.stage_dir(2)
        g = rec["goal"]
        goal_pinned = P.stage(g["sha256"], sd, Path(g["path"]).name)
        run.io(s, "outputs", goal_pinned, "the goal picture (pinned)")
        goal_kp = None
        if g.get("pose"):
            pj = P.stage(g["pose"]["sha256"], sd, Path(g["pose"]["path"]).name)
            run.io(s, "outputs", pj, "the goal's measured keypoints (pinned)")
            gp = P.read_json(pj, {}) or {}
            goal_kp = (gp.get("person") or {}).get("kp")
            if gp.get("person"):
                from PIL import Image
                with Image.open(goal_pinned) as im:
                    im = im.convert("RGB")
                    facecard.draw_pose(im, gp)
                    im.save(sd / "goal_pose.jpg", quality=88)
        staged = {}
        for f in lock["files"]:
            staged[f["n"]] = P.stage(f["sha256"], sd / "refs", f"{f['n']:02d}_{f['upload_name']}")
        sheet_of_refs(lock, rec, staged, sd / "references.jpg")
        if rec["method"].get("route") == "replicate":
            import replicate_recipe
            replicate_recipe.draw_crop(goal_pinned, rec, sd / "crop_on_original.jpg")
            run.io(s, "outputs", sd / "crop_on_original.jpg", "the frozen crop (green) on the full-resolution original")
        P.atomic_write_json(sd / "inputs.json", {"goal": g, "face_choice": rec["inputs"].get("face_choice"), "references": rec["inputs"]["references"],
                                                 "flags": rec["inputs"].get("flags")})
        fc = rec["inputs"].get("face_choice") or {}
        s["summary"] = (f"goal {Path(g['path']).name}; {len(lock['files'])} files: " + ", ".join(f"{f['n']} {f['role']}" for f in lock["files"])
                        + (f"; face set: bin {fc.get('bin')} decided by {fc.get('decided_by')}" if fc else ""))

    # ---------------------------------------------------------------- 03 request
    with run.stage(3) as s:
        sd = run.stage_dir(3)
        sent = []
        for f in lock["files"]:
            p = P.stage(f["sha256"], sd / "sent" / f"{f['n']:02d}", f["upload_name"])
            sent.append(p)
            run.io(s, "outputs", p, f"image {f['n']} {f['role']}")
        P.write_text_lf(sd / "prompt.txt", lock["prompt"])
        if P.sha256_file(sd / "prompt.txt") != P.sha256_text(lock["prompt"]):
            raise StageFail("prompt.txt does not hash to the lock's prompt", code=2)
        req = R.request_of(lock)
        sha = P.sha256_bytes(P.canonical_json(req))
        if sha != lock["request_sha256"]:
            raise StageFail("the request does not hash to the lock's request_sha256", code=2)
        P.atomic_write_json(sd / "request.json", {**req, "request_sha256": sha, "sent": [str(p.relative_to(d)) for p in sent]})
        lint = []
        inv = (rec["inputs"].get("inventory") or {}).get("data")
        if inv:
            sys.path.insert(0, str(ROOT / "tools"))
            import inventory_lint
            lint = [{"level": lvl, "msg": msg} for lvl, msg in inventory_lint.lint(inv, files=len(lock["files"]))]
        P.atomic_write_json(sd / "lint.json", lint)
        P.atomic_write_json(sd / "notices.json", (rec.get("origin") or {}).get("notices") or [])
        if rec["method"].get("route", "G") == "G":
            run.legacy["route_g"] = R.compile_route_g(R.res_from_recipe(rec), *R.live_profile_and_template(rec["method"].get("subject") or "me")[:2])[2]
        s["summary"] = (f"request {sha[:16]} = the lock; prompt {len(lock['prompt'])} chars; {len(sent)} files staged"
                        + (f"; lint: {', '.join(x['level'] for x in lint)}" if lint else "; lint clean" if inv else ""))
    if dry_run:
        for n in range(4, 9):
            run.mark(n, "not_run", "dry run: stops after the request")
        return
    if rec["method"].get("route") == "replicate":
        import replicate_recipe
        await replicate_recipe.stages(run, rec, config, sent, run.stage_dir(2) / Path(rec["goal"]["path"]).name, n_samples, no_guard, no_wait,
                                      wait_max, verbose, remeasure)
        return

    goal_pinned = run.stage_dir(2) / Path(rec["goal"]["path"]).name
    pj = run.stage_dir(2) / Path(rec["goal"]["pose"]["path"]).name if rec["goal"].get("pose") else None
    goal_kp = ((P.read_json(pj, {}) or {}).get("person") or {}).get("kp") if pj else None
    gated: dict[str, dict] = {}
    pose_record: dict = {}

    if remeasure:
        src = Path(remeasure)
        n_copied = 0
        for p in sorted(src.iterdir()):
            import re as _re
            if p.is_file() and _re.fullmatch(r"v\d+_\d+\.(jpg|png|webp)", p.name, _re.I):
                shutil.copyfile(p, d / p.name)
                n_copied += 1
        run.mark(4, "not_applicable", f"remeasure: no Gemini call")
        run.mark(5, "not_applicable", f"remeasure: {n_copied} picture(s) copied from {src.name}")
        run.legacy["remeasure_of"] = src.name
        if not n_copied:
            raise StageFail(f"no pictures in {src}", code=1)
    else:
        await _generate(run, rec, config, sent, goal_pinned, n_samples, stop_n, no_guard, no_wait, wait_max, verbose, gated, pose_record)

    # ---------------------------------------------------------------- 06 measure
    from scorer import ArcFaceScorer, analyze_face
    import headpose
    import lighting
    with run.stage(6) as s:
        sd = run.stage_dir(6)
        samples_ = sorted((p for p in d.iterdir() if p.is_file() and p.suffix.lower() in (".jpg", ".png", ".webp") and p.stem[:1] == "v" and "_" in p.stem
                           and p.stem.replace("v", "", 1).replace("_", "").isdigit()), key=lambda p: tuple(int(x) for x in p.stem[1:].split("_")))
        if not samples_:
            raise StageFail("no picture to measure", code=1)
        todo = [p for p in samples_ if p.name not in gated]
        if todo:
            rec_ = {}
            for gres in facecard.run_pose_gate(goal_pinned, todo, strict=True, record=rec_):
                gated[Path(gres["render"]).name] = gres
            pose_record.setdefault("calls", []).append(rec_)
        (sd / "pose_compare.stderr.txt").write_text("\n\n".join(c.get("stderr", "") for c in pose_record.get("calls", [])), encoding="utf-8")
        threshold = float(config.get("identity_threshold", 0.60))
        sc = ArcFaceScorer()
        face_files = [p for f, p in zip(lock["files"], sent) if f["role"] == "face"]
        if not face_files and rec["inputs"].get("scoring_faces"):
            face_files = [P.stage(x["sha256"], sd / "scoring_faces", x["name"]) for x in rec["inputs"]["scoring_faces"]]
        ref_embeds = []
        for fpath in face_files:
            with contextlib.suppress(Exception):
                ref_embeds.append(sc.embed(fpath))
        pool_names = config.get("refs", [])
        pool_paths = [p for n in pool_names for p in (paths_ref(n, config),) if p]
        pool = [e for e in sc.embed_many(pool_paths).values() if e is not None] if pool_paths else []
        goal_img = lighting.read_bgr(goal_pinned)
        ch = character_of(rec)
        measures = []
        for p in samples_:
            img = lighting.read_bgr(p)
            info = analyze_face(p)
            score, pool_top3 = None, None
            with contextlib.suppress(Exception):
                emb = sc.embed(p)
                score = float(max(sc.similarity(emb, r) for r in ref_embeds)) if ref_embeds else None
                if pool:
                    sims = sorted((sc.similarity(emb, e) for e in pool), reverse=True)
                    pool_top3 = round(float(sum(sims[:3]) / min(3, len(sims))), 3)
                else:
                    pool_top3 = None
            status = identity_status(score, info, threshold)
            g = gated.get(p.name)
            pose = "PASS" if (g and not g.get("fails")) else ("FAIL" if g else "missing")
            if g is None:
                raise StageFail(f"the pose gate gave no result for {p.name}")
            if pose == "FAIL":
                status = "rejected"
            r_kp = lighting.render_keypoints(p)
            light = lighting.metrics(img, r_kp, goal_img, goal_kp) if (img is not None and goal_img is not None and r_kp and goal_kp) else None
            n_faces, face_px = face_count_and_size(img) if img is not None else (0, None)
            m = {"file": p.name, "pose_gate": pose, "pose_fails": sorted(set(map(str, (g or {}).get("fails", [])))),
                 "pose_checks": (g or {}).get("checks", []), "identity": score, "identity_status": status,
                 "face": {k: info.get(k) for k in ("detected", "pose_bin", "direction", "yaw_ratio", "is_profile", "sharpness")}, "light": light,
                 "record_only": {"faces_found": n_faces, "largest_face_px": face_px,
                                 "mean_grey_diff_to_goal": grey_diff_to_goal(img, goal_img) if (img is not None and goal_img is not None) else None,
                                 "pool_identity_top3": pool_top3, "head_pose": headpose.measure(p), "c2pa": P.c2pa_info(p),
                                 **character_record(p, ch)}}
            measures.append(m)
            print(f"  {p.name}: pose gate {pose}" + (f" (items {', '.join(m['pose_fails'])})" if m["pose_fails"] else "")
                  + f" | identity {'none' if score is None else format(score, '.4f')} {status}" + (f" | light {lighting.describe(light)}" if light else " | light not measurable")
                  + f" | faces {n_faces}, grey diff to goal {m['record_only']['mean_grey_diff_to_goal']}"
                  + (f" | head yaw {m['record_only']['head_pose']['yaw']:+.0f} pitch {m['record_only']['head_pose']['pitch']:+.0f}" if m['record_only']['head_pose'].get('detected') else "")
                  + (f" | C2PA {m['record_only']['c2pa'].get('state')}" if m['record_only']['c2pa'] else ""))
        P.atomic_write_json(sd / "measure.json", {"identity_threshold": threshold, "identity_rule": IDENTITY_RULE,
                                                   "light_limits": {"ratio": list(lighting.LIGHT_RATIO), "neck_tol": lighting.NECK_RATIO_TOL},
                                                   "pose_gate_limits": (next(iter(gated.values()), {}) or {}).get("limits") or P.gate_limits().get("pose_gate"),
                                                   "samples": measures})
        run.legacy["identity_threshold"] = threshold
        run.legacy["pose_gate"] = [gated[m["file"]] for m in measures if m["file"] in gated]
        run.legacy["results"] = [{"index": i, "files": [m["file"]], "evaluations": [{"raw_file": m["file"], "raw_score": m["identity"], "restored_file": None,
                                   "restored_score": None, "status": m["identity_status"], **({"pose_gate": "fail"} if m["pose_gate"] == "FAIL" else {}),
                                   **({"light": m["light"]} if m["light"] else {})}]} for i, m in enumerate(measures)]
        n_pass = sum(m["pose_gate"] == "PASS" for m in measures)
        s["summary"] = f"{len(measures)} picture(s): pose gate {n_pass} pass / {len(measures) - n_pass} fail; identity " + ", ".join(
            f"{m['file']} {'none' if m['identity'] is None else format(m['identity'], '.4f')}" for m in measures)

    # ---------------------------------------------------------------- 07 review
    with run.stage(7) as s:
        sd = run.stage_dir(7)
        sys.path.insert(0, str(ROOT / "tools"))
        import audit_views
        lines = []
        for m in measures:
            p = d / m["file"]
            try:
                lines += audit_views.make_views(Path(m["file"]).stem, goal_pinned, p, d, sd, ref_paths=face_files, goal_kp=goal_kp)
            except Exception as exc:
                lines.append(f"{m['file']}: audit views failed: {type(exc).__name__}: {exc}")
            lines.append(character_sheet(p, ch, sd / f"{Path(m['file']).stem}_character.jpg"))
        chk = {m["file"]: (P.read_json(d / (m["file"] + ".checklist.json"), None) or {}).get("verdict", "not checked yet") for m in measures}
        P.atomic_write_json(sd / "review.json", {"lines": lines, "checklist": chk})
        s["summary"] = f"audit sheets for {len(measures)} picture(s) in {sd.name}; checklist: " + ", ".join(f"{k} {v}" for k, v in chk.items())

    # ---------------------------------------------------------------- 08 result
    with run.stage(8) as s:
        sd = run.stage_dir(8)
        threshold = run.legacy["identity_threshold"]
        cands = []
        for m in measures:
            ok_light = 1 if (m["light"] or {}).get("ok") else 0
            key = (1 if m["identity_status"] == "accepted" else 0, ok_light, m["identity"] if m["identity"] is not None else -1.0)
            cands.append({"file": m["file"], "sort_key": {"accepted": key[0], "light_ok": key[1], "identity": key[2]}, "pose_gate": m["pose_gate"]})
        cands.sort(key=lambda c: (c["sort_key"]["accepted"], c["sort_key"]["light_ok"], c["sort_key"]["identity"]), reverse=True)
        top = cands[0]
        # best.jpg: the top candidate only if accepted, or scored >= threshold WITHOUT failing the pose gate ("a render that fails it is never picked as best")
        best_ok = top["sort_key"]["accepted"] == 1 or (top["sort_key"]["identity"] >= threshold and top["pose_gate"] != "FAIL")
        if best_ok:
            shutil.copy2(d / top["file"], d / "best.jpg")
            run.legacy["best"] = {"file": "best.jpg", "source": top["file"], "score": round(top["sort_key"]["identity"], 3), "status": "accepted"}
        export_lines = []
        if run.kind == "run":
            try:
                sys.path.insert(0, str(ROOT / "tools"))
                import export_results
                run.save()
                export_lines = export_results.export_many([d])
                for ln in export_lines:
                    print(f"[Export] {ln}")
            except Exception as exc:
                export_lines = [f"export skipped: {type(exc).__name__}: {exc}"]
        P.atomic_write_json(sd / "result.json", {"ranking": cands, "best": run.legacy.get("best"), "best_rule": "accepted, or identity >= threshold "
                                                  "without a pose-gate fail; a candidate only until the 35-item checklist passes",
                                                  "export": export_lines if run.kind == "run" else "not applicable (" + run.kind + ")"})
        s["summary"] = (f"best.jpg = {top['file']}" if best_ok else "no best.jpg (no picture accepted)") + "; ranking " + " > ".join(c["file"] for c in cands) + (
            f"; {len(export_lines)} export line(s)" if run.kind == "run" else "")


def character_of(rec: dict) -> dict | None:
    """The recipe's character, or, for an older recipe without one, the latest character 'me' (its band is still the measure of 'him')."""
    import characters
    c = rec["inputs"].get("character")
    try:
        return characters.load(c["ref"] if c else "me")[0]
    except SystemExit:
        return None


def character_record(p: Path, ch: dict | None) -> dict:
    """Record-only (2026-10-08): his face-fullness and build measures of one picture (character.py) and how far each is from the character's band.
    Never a gate, never a stop: an unmeasurable picture records the reason."""
    try:
        import character
        import characters
        m = character.measure(p)
        out = {"character": m}
        if ch and ch.get("band"):
            out["character_vs_band"] = character.compare(m, ch["band"])
            out["character_band_of"] = characters.ref_of(ch)
        return out
    except Exception as e:
        return {"character": {"error": f"{type(e).__name__}: {e}"}}


def character_sheet(p: Path, ch: dict | None, out: Path) -> str:
    """07_review/<picture>_character.jpg: the picture's face and torso beside the character's photos at the same scale (checklist items 31, 32)."""
    if not ch:
        return f"{p.name}: no character to compare with (characters/me missing)"
    try:
        import character
        import characters
        refs = [q for q in (characters.ref_path(r["name"]) for r in ch["references"]) if q]
        made = character.character_sheet(p, refs, out)
        return f"{p.name}: character sheet {'written: ' + out.name if made else 'not made (nothing measurable)'}"
    except Exception as e:
        return f"{p.name}: character sheet failed: {type(e).__name__}: {e}"


def paths_ok(pre: list) -> bool:
    """Preflight: everything a run needs after it has spent credits (so it is checked before)."""
    import paths
    from scorer import ARCFACE_PATH, DETECTOR_PATH
    checks = [("YOLO python (pose gate)", paths.yolo_python()), ("tools/pose_compare.py", ROOT / "tools" / "pose_compare.py"),
              ("yolo11m-pose.pt", paths.yolo_models_dir() / "yolo11m-pose.pt"), ("yolo11m.pt", paths.yolo_models_dir() / "yolo11m.pt"),
              ("ArcFace model", ARCFACE_PATH), ("YuNet model", DETECTOR_PATH)]
    for what, p in checks:
        pre.append({"what": what, "ok": Path(p).is_file(), "detail": str(p)})
    return all(x["ok"] for x in pre)


def paths_ref(name: str, config: dict) -> Path | None:
    import facecard
    for base in (facecard.get_refs_dir(config), ROOT / config.get("cache_dir", ".cache/refs")):
        if (base / name).is_file():
            return base / name
    return None


async def _generate(run: Run, rec: dict, config: dict, sent: list[Path], goal_pinned: Path, n_samples: int, stop_n: int, no_guard: bool, no_wait: bool,
                    wait_max: float, verbose: bool, gated: dict, pose_record: dict) -> None:
    import facecard
    from credit_guard import Guard, GuardRefused
    from gemini_webapi.exceptions import APIError, GeminiError, ImageGenerationError, UsageLimitExceededError
    from session import AuthError, authenticated_client, credits_left, describe_usage, usage_of
    lock = rec["lock"]
    model = lock["model"]
    label = rec["method"]["model"].get("label") or R.model_label(model, config)
    guard = Guard(config.get("credit_guard"))
    d = run.dir
    try:
        async with authenticated_client(verbose=verbose) as client:
            # ---------------------------------------------------------------- 04 credits
            with run.stage(4) as s:
                sd = run.stage_dir(4)
                info = {"account_status": client.account_status.name, "model": model, "model_label": label}
                with contextlib.suppress(Exception):
                    m = [x for x in client.list_models() if x.model_id == model]
                    info["model_listed"] = {"display_name": m[0].display_name, "available": m[0].is_available} if m else "not in this account's list"
                with contextlib.suppress(Exception):
                    await client._fetch_usage_info()
                info["usage_at_start"] = describe_usage(usage_of(client))
                info["credits_left_at_start"] = credits_left(client)
                waited0 = time.time()
                if no_guard:
                    info["guard"] = "skipped (--no-guard)"
                else:
                    async def _fresh():
                        with contextlib.suppress(Exception):
                            await client._fetch_usage_info()
                        return credits_left(client)
                    try:
                        info["guard"] = await guard.acquire(is_pro=label == "pro", images=n_samples, label=d.name, refresh=_fresh,
                                                            wait_max=0.0 if no_wait else float(wait_max))
                    except GuardRefused as e:
                        info["guard"] = f"refused: {e}"
                        P.atomic_write_json(sd / "credits.json", info)
                        run.legacy["status"] = "guard_refused"
                        raise StageFail(f"credit guard refused, nothing was generated: {e}", code=3)
                info["waited_secs"] = round(time.time() - waited0, 1)
                # the session can expire while a run waits for credits (2026-10-09: 49 min of waiting, then UNAUTHENTICATED on every attempt)
                if info["waited_secs"] > 60 and credits_left(client) is None:
                    P.atomic_write_json(sd / "credits.json", info)
                    raise StageFail("the Gemini session expired while this run waited for credits: refresh the cookies (vault popup) and run again",
                                    code=SIGN_IN_FAILED)
                info["credits_left_after_guard"] = credits_left(client)
                note_model_change(run, rec, info)
                P.atomic_write_json(sd / "credits.json", info)
                s["summary"] = (f"{info['account_status']}; model {label} {model}"
                                + (f" ({info['model_listed']['display_name']})" if isinstance(info.get("model_listed"), dict) else "")
                                + f"; {info['usage_at_start']}; guard " + ("skipped" if no_guard else f"ok after {info['waited_secs']} s")
                                + (f"; MODEL CHANGED: {info['model_change']}" if info.get("model_change") else ""))

            # ---------------------------------------------------------------- 05 generate
            with run.stage(5) as s:
                sd = run.stage_dir(5)
                credit_log = {"model": model, "start": credits_left(client), "calls": []}
                run.legacy["credits"] = credit_log
                last = [credit_log["start"]]
                fails_in_row, saved, stopped = 0, 0, None
                for i in range(n_samples):
                    print(f"\nGenerating picture {i + 1}/{n_samples}...")
                    call = {"index": i, "started": now(), "upload_retries": 0}
                    lib_lines: list[str] = []
                    sink = None
                    with contextlib.suppress(Exception):
                        from loguru import logger
                        sink = logger.add(lambda msg: lib_lines.append(P.redact(str(msg)).strip()), level="DEBUG",
                                          filter=lambda r: r["extra"].get("name") == "gemini_webapi", format="{level}: {message}")
                    t0 = time.time()
                    output = None
                    try:
                        for up_try in range(3):
                            try:
                                output = await client.generate_content(lock["prompt"], files=[str(p) for p in sent], model=model, temporary=True)
                                break
                            except (GeminiError, APIError, UsageLimitExceededError):
                                raise
                            except Exception as e:   # a 5xx from Google's file-upload service: nothing generated yet
                                if "HTTP Error 5" not in str(e) or up_try == 2:
                                    raise
                                call["upload_retries"] += 1
                                print(f"  upload failed ({e}); retrying in {20 * (up_try + 1)} s")
                                await asyncio.sleep(20 * (up_try + 1))
                    except UsageLimitExceededError:
                        call.update({"outcome": "usage_limit", "secs": round(time.time() - t0, 1)})
                        print("Usage limit hit on this account. Stopping.")
                        stopped = "usage limit"
                    except (APIError, GeminiError) as e:     # APIError: e.g. code 1099, a temporary Google issue (2026-10-08): this call's outcome, the run goes on
                        call.update({"outcome": "error", "error": f"{type(e).__name__}: {e}", "secs": round(time.time() - t0, 1)})
                        print(f"Generation {i + 1} failed: {type(e).__name__}: {e}")
                        if "UNAUTHENTICATED" in str(e):      # an expired session fails every later call too: stop here, nothing is charged
                            stopped = "the Gemini session expired (refresh the cookies)"
                    if output is not None:
                        cand = output.candidates[output.chosen]
                        call.update({"secs": round(time.time() - t0, 1), "metadata": list(output.metadata or []), "candidates": len(output.candidates),
                                     "chosen": output.chosen, "text": cand.text, "thoughts": (cand.thoughts or "")[:4000] or None})
                        images = cand.generated_images
                        call["outcome"] = "image" if images else "no_image"
                        call["images"] = []
                        for j, img in enumerate(images):
                            # the library tries the full-size download only when the image carries all of these; otherwise it silently keeps the preview
                            missing = [k for k in ("client_ref", "cid", "rid", "rcid", "image_id") if not getattr(img, k, None)]
                            saved_path = Path(await img.save(path=str(d), filename=f"v{i + 1}_{j}.png", verbose=verbose))
                            saved_path = facecard.fix_extension(saved_path)
                            ir = image_record(saved_path)
                            ir["full_size"] = not str(getattr(img, "url", "")).endswith(("=s2048-rj", "=s1024-rj"))
                            if not ir["full_size"]:
                                ir["full_size_note"] = (f"not attempted: the image has no {', '.join(missing)}" if missing
                                                        else "attempted, but no full-size image came back (the library kept the preview)")
                            call["images"].append(ir)
                            saved += 1
                            print(f"Saved {saved_path.name} ({ir.get('px')}, {'full size' if ir['full_size'] else 'PREVIEW size: full size ' + ir['full_size_note']})")
                        if not images:
                            print(f"Generation {i + 1}: no image returned. Reply: {cand.text[:300]}")
                    if sink is not None:          # the library's log of this call, through the picture download
                        with contextlib.suppress(Exception):
                            from loguru import logger
                            logger.remove(sink)
                    now_left = credits_left(client)
                    used = (last[0] - now_left) if (now_left is not None and last[0] is not None) else None
                    credit_log["calls"].append({"index": i, "outcome": call.get("outcome"), "credits": used, "left": now_left})
                    last[0] = now_left
                    call.update({"credits_used": used, "credits_left": now_left, "library_log": lib_lines[-60:]})
                    P.atomic_write_json(sd / f"call_{i + 1}.json", call)
                    print(f"[Credits] this call {used}, window left {now_left}")
                    if stopped:
                        break
                    # early stop: gate this picture now (same rule as gen's --stop-after-fails / --stop-on-pass)
                    mine = [d / ir["file"] for ir in call.get("images", [])]
                    if mine and (stop_n or rec["method"]["stop"].get("on_pass")):
                        rec_ = {}
                        for gres in facecard.run_pose_gate(goal_pinned, mine, strict=True, record=rec_):
                            gated[Path(gres["render"]).name] = gres
                            passed = not gres.get("fails")
                            fails_in_row = 0 if passed else fails_in_row + 1
                            print(f"  [Pose gate] {Path(gres['render']).name}: " + ("PASS" if passed else "FAIL items " + ", ".join(sorted(set(map(str, gres["fails"]))))))
                        pose_record.setdefault("calls", []).append(rec_)
                        if rec["method"]["stop"].get("on_pass") and any(not x.get("fails") for x in gated.values()):
                            stopped = "a picture passed the pose gate (stop on pass)"
                            break
                        if stop_n and fails_in_row >= stop_n:
                            stopped = f"{fails_in_row} pictures in a row failed the pose gate"
                            print(f"  [Early stop] {stopped}: {n_samples - i - 1} picture(s) not spent.")
                            run.legacy["early_stop"] = {"after": i + 1, "fails_in_row": fails_in_row}
                            break
                with contextlib.suppress(Exception):
                    await asyncio.sleep(3)
                    await client._fetch_usage_info()
                credit_log["end"] = credits_left(client)
                if credit_log["start"] is not None and credit_log["end"] is not None:
                    credit_log["total"] = credit_log["start"] - credit_log["end"]
                    n_img = sum(1 for c in credit_log["calls"] if c["outcome"] == "image")
                    credit_log["per_image"] = round(credit_log["total"] / n_img, 1) if n_img else None
                P.atomic_write_json(sd / "credits.json", credit_log)
                s["summary"] = (f"{saved} picture(s) from {len(credit_log['calls'])} call(s)"
                                + (f"; stopped: {stopped}" if stopped else "") + f"; credits {credit_log.get('total')} (window left {credit_log.get('end')})")
                if not saved:
                    raise StageFail("no picture was returned", code=1)
    except AuthError as e:
        print(str(e))
        run.manifest["failed_stage"] = 4
        run.mark(4, "failed", "authentication failed: refresh the Gemini cookies in the vault popup (see the message above)")
        raise StageFail(f"authentication failed: {e}", code=SIGN_IN_FAILED)
    finally:
        guard.release()
