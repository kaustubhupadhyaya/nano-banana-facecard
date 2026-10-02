"""End hook of the gemini-identity-gen skill: copy the PASSED pictures out of outputs\\<run>\\ into one flat results folder outside the repo.

The user, 2026-10-01: "not everything has to be added, only passed ones need to be brought here, that too without forming any more subfolders,
photo name itself should be sufficient to identify." So:

    D:\\FacecardResults\\                                          (paths.results_dir(): FACECARD_RESULTS_DIR env var, results_dir in facecard.json, or this default)
        motorcycle-outfit-men_02_porch-reading-smoking-grey-tee_v01.jpg
        motorcycle-outfit-men_02_porch-reading-smoking-grey-tee_v02.jpg
        motorcycle-outfit-men_06_shirtless-pencil-in-mouth-bw_v01.jpg
        ...                                                        no subfolders, no index to read: <collection>_<NN>_<title>_v<N>

  * PASSED = the picture's checklist (tools\\best_check.py, BEST_CHECKLIST.md) says BEST, or the user accepted it (best_check.py --user-approved "<their words>",
    verdict "BEST (user-approved)"). Anything else (failed items, no checklist yet, pose-gate failures) is never copied.
  * vN counts the passed versions of one goal in the order they were generated (v1, v2, ...); a number is never reused or renumbered. Which run and
    candidate a file came from is kept in the hidden state file .export_index.json (not needed to read the names).
  * A picture that stops passing (its checklist is re-recorded with failed items) is withdrawn: its copy in the results folder is deleted.
  * Goal names come from results_names.json (goal picture stem -> collection, number, title); a goal that is not listed is named misc_<stem>_v<N>.
  * Pictures are COPIED; outputs\\ keeps its run folders untouched.

    .venv\\Scripts\\python.exe tools\\export_results.py                   every run folder in outputs\\ (idempotent)
    .venv\\Scripts\\python.exe tools\\export_results.py outputs\\<run> ...     only these runs
    .venv\\Scripts\\python.exe tools\\export_results.py --dry-run          say what would be copied or withdrawn

tools\\best_check.py calls safe_export() itself whenever it records a checklist or a user approval, and facecard.py gen / replicate call it when a run
ends, so nothing has to be run by hand.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NAMES_FILE = ROOT / "results_names.json"
STATE_NAME = ".export_index.json"
LOCK_NAME = ".export.lock"
GEN_RE = re.compile(r"^v(\d+)_(\d+)\.(jpg|jpeg|png)$", re.I)
PICKED = ("best.jpg", "best.png", "not_passing_closest.jpg")     # replicate's picture of a run, and gen's copy of its top candidate


# ------------------------------------------------------------------------------------------------------------------------------ helpers
def results_dir() -> Path:
    import paths
    return paths.results_dir()


def slug(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s[:maxlen].strip("-") or "untitled"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


@contextlib.contextmanager
def locked(dest: Path, wait: float = 90.0):
    """Runs started in parallel (the user, 2026-09-30) finish at the same time; one exporter at a time writes the state file."""
    dest.mkdir(parents=True, exist_ok=True)
    lock = dest / LOCK_NAME
    t0 = time.time()
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            with contextlib.suppress(OSError):
                if time.time() - lock.stat().st_mtime > 120:      # a crashed exporter's leftover
                    lock.unlink()
                    continue
            if time.time() - t0 > wait:
                raise TimeoutError(f"results folder locked for {wait:.0f} s: {lock}")
            time.sleep(0.4)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def goal_path_of(run: dict) -> Path | None:
    raw = (run.get("route_g") or {}).get("goal") or run.get("scene_image") or run.get("scene")
    if not raw:
        return None
    p = Path(str(raw).replace("\\", "/"))
    return p if p.is_absolute() else ROOT / p


def goal_key(run: dict) -> str:
    p = goal_path_of(run)
    if p is not None:
        return re.sub(r"_clean$", "", p.stem)
    prompt = str(run.get("prompt") or "from-text")
    pp = Path(prompt.replace("\\", "/"))
    return pp.stem if len(prompt) < 200 and pp.suffix == ".txt" else " ".join(prompt.split()[:6])


def base_name(key: str) -> str:
    """<collection>_<NN>_<title> for a goal stem, from results_names.json; a goal that is not listed is misc_<stem>."""
    entry = read_json(NAMES_FILE, {}).get(key) or {}
    collection = slug(entry.get("collection") or "misc")
    title = slug(entry.get("title") or key)
    number = entry.get("number")
    return f"{collection}_{int(number):02d}_{title}" if number is not None else f"{collection}_{title}"


def passed(pic: Path) -> tuple[bool, str]:
    """Only a recorded checklist can pass a picture: BEST, or accepted by the user (their words are kept in the checklist file)."""
    chk = read_json(pic.with_name(pic.name + ".checklist.json"), None)
    if not chk:
        return False, "no checklist recorded"
    if chk.get("user_approved"):
        return True, "user-approved: " + str(chk["user_approved"].get("words", ""))[:120]
    if chk.get("keep_in_results"):
        return True, "kept in the results folder at the user's request although the checklist failed items " + ", ".join(sorted(chk.get("failed", {}), key=int))
    if chk.get("verdict") == "BEST":
        return True, "all checklist items passed"
    return False, "checklist failed items " + ", ".join(sorted(chk.get("failed", {}), key=int))


def identity_of(pic: Path, run: dict):
    for r in run.get("results") or []:
        for e in r.get("evaluations") or []:
            if e.get("raw_file") == pic.name and e.get("raw_score") is not None:
                return round(float(e["raw_score"]), 3)
    return None


def candidates_of(run_dir: Path) -> list[Path]:
    files = sorted((p for p in run_dir.iterdir() if p.is_file()), key=lambda p: p.name)
    gen = [p for p in files if GEN_RE.match(p.name)]
    gen.sort(key=lambda p: tuple(int(x) for x in GEN_RE.match(p.name).groups()[:2]))
    return gen + [p for p in files if p.name in PICKED]


# ------------------------------------------------------------------------------------------------------------------------------ export
def export_run(run_dir: Path, dest: Path, state: dict, dry: bool = False) -> list[str]:
    """Copy one run's passed pictures into `dest` (flat) and withdraw the ones that no longer pass. Mutates `state`; returns one line per action."""
    run_dir = Path(run_dir)
    run = read_json(run_dir / "run.json", None)
    if run is None or not run_dir.is_dir():
        return []
    lines: list[str] = []
    files: dict[str, dict] = state.setdefault("files", {})
    base = base_name(goal_key(run))
    pics = candidates_of(run_dir)
    candidate_digests = {md5(p_) for p_ in pics if GEN_RE.match(p_.name)}
    for pic in pics:
        digest = md5(pic)
        if pic.name in PICKED and digest in candidate_digests:
            continue          # gen's best.jpg is a copy of one vN_M.jpg, which carries the checklist
        ok, why = passed(pic)
        e = files.get(digest)
        if not ok:
            if e and e.get("file") and e.get("run") == run_dir.name:
                target = dest / e["file"]
                lines.append(f"withdraw {e['file']} ({why})")
                if not dry:
                    with contextlib.suppress(OSError):
                        target.unlink()
                    e["withdrawn"] = datetime.now().isoformat(timespec="seconds")
                    e["file"] = None
            continue
        if e is None or e.get("base") != base:
            ver = 1 + max([v["version"] for v in files.values() if v.get("base") == base] or [0])
            e = {"md5": digest, "base": base, "version": ver}
            files[digest] = e
        ext = pic.suffix.lower().replace(".jpeg", ".jpg")
        name = f"{base}_v{e['version']}{ext}"
        if e.get("file") != name or not (dest / name).exists():
            lines.append(f"copy    {run_dir.name}/{pic.name} -> {name}")
            if not dry:
                shutil.copy2(pic, dest / name)
        e.update({"file": name, "status": why, "identity": identity_of(pic, run), "run": run_dir.name,
                  "source_file": pic.name, "run_timestamp": str(run.get("timestamp") or run_dir.name[:15]), "goal": str(goal_path_of(run) or ""),
                  "exported": datetime.now().isoformat(timespec="seconds")})
        e.pop("withdrawn", None)
    return lines


# ------------------------------------------------------------------------------------------------------------------------------ feedback ledger
# The user, 2026-10-01: the pictures that do not pass are not kept in the results folder, so what was WRONG and what went RIGHT in each of them must be kept
# somewhere permanent. FEEDBACK_LEDGER.md / feedback_ledger.json (repo root, text only) get one row for EVERY generated picture, passed or not, and rows are
# never deleted: when outputs\ is pruned and a picture's file is gone, its row stays.
LEDGER_JSON = ROOT / "feedback_ledger.json"
LEDGER_MD = ROOT / "FEEDBACK_LEDGER.md"


def band(score) -> str:
    if score is None:
        return "no face could be scored"
    return "accept band" if score >= 0.52 else ("gray zone, needs a human eye" if score >= 0.20 else "rejected band, not meaningful when the face is hidden, bowed or in profile")


def pose_detail(pic: Path, run: dict) -> tuple[str, str]:
    for g in run.get("pose_gate") or []:
        if Path(g.get("render", "")).name == pic.name:
            if not g.get("fails"):
                return "PASS", "pose gate passed every measured item"
            bad = "; ".join(f"{c['name']} {c['value']}" for c in g.get("checks", []) if not c.get("ok"))
            return "FAIL", "pose gate failed: " + bad
    return "", ""


def ledger_row(run_dir: Path, run: dict, pic: Path) -> dict:
    chk = read_json(pic.with_name(pic.name + ".checklist.json"), None)
    pose, pose_txt = pose_detail(pic, run)
    ident = identity_of(pic, run)
    failed = {int(n): t for n, t in ((chk or {}).get("failed") or {}).items()}
    if chk and chk.get("user_approved"):
        result = "PASS (accepted by the user)"
    elif chk and chk.get("verdict") == "BEST":
        result = "PASS (all 30 items)"
    elif chk:
        result = "FAIL (checklist)"
    elif pose == "FAIL":
        result = "FAIL (pose gate, not checked)"
    else:
        result = "NOT CHECKED YET"
    wrong: list[str] = []
    if failed:
        wrong.append("failed checklist items: " + "; ".join(f"{n} ({t.split(chr(58))[0].split(chr(46) + chr(32))[0][:110]})" for n, t in sorted(failed.items())))
    if chk and chk.get("note") and (failed or not chk.get("verdict", "").startswith("BEST")):
        wrong.append(str(chk["note"]))
    if not chk and pose == "FAIL":
        wrong.append(pose_txt)
    if chk and chk.get("user_approved"):
        wrong.append("the user accepted it anyway: " + str(chk["user_approved"].get("words", "")))
    right: list[str] = []
    if chk and chk.get("right"):
        right.append(str(chk["right"]))
    if pose == "PASS":
        right.append(pose_txt)
    if ident is not None:
        right.append(f"identity {ident:.2f} ({band(ident)})")
    if chk:
        right.append(f"{len(chk.get('items', {})) - len(failed) - len(chk.get('na', []))} of {len(chk.get('items', {}))} checklist items passed, {len(chk.get('na', []))} not applicable")
    return {"key": f"{run_dir.name}/{pic.name}", "goal": base_name(goal_key(run)), "run": run_dir.name, "file": pic.name,
            "time": str(run.get("timestamp") or run_dir.name[:15]), "result": result, "identity": ident, "pose_gate": pose,
            "model": {"e6fa609c3fa255c0": "Pro", "56fdd199312815e2": "Flash"}.get(str(run.get("model")), str(run.get("model") or "")),
            "inventory": Path(str((run.get("route_g") or {}).get("inventory") or "")).name,
            "failed_items": sorted(failed), "wrong": " | ".join(wrong), "right": " | ".join(right),
            "recorded": datetime.now().isoformat(timespec="seconds")}


def write_ledger_md(rows: dict) -> None:
    by: dict[str, list[dict]] = {}
    for r in rows.values():
        by.setdefault(r["goal"], []).append(r)
    out = ["# Feedback ledger", "",
           "One entry for EVERY generated picture, passed or not (written by `tools/export_results.py`, the end hook of the gemini-identity-gen skill). "
           "Only passed pictures are copied to the results folder; everything that failed is recorded here, with what was wrong and what went right, so the lesson "
           "outlives the file in `outputs\\` (the session-start prune deletes those). Entries are never removed. Add the human notes with "
           "`tools\\best_check.py <picture> --fail ... --note \"what was wrong\" --right \"what went right\"`.", "",
           f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}. {len(rows)} pictures.", ""]
    for goal in sorted(by):
        rs = sorted(by[goal], key=lambda r: (r["time"], r["file"]))
        passed_n = sum(1 for r in rs if r["result"].startswith("PASS"))
        out += [f"## {goal}", "", f"{len(rs)} pictures, {passed_n} passed.", ""]
        for n, r in enumerate(rs, 1):
            ident = "" if r.get("identity") is None else f", identity {r['identity']:.2f}"
            how = ", ".join(x for x in (r.get("model"), r.get("inventory")) if x)
            out.append(f"- **attempt {n}** `{r['run']}/{r['file']}`: **{r['result']}**{ident}" + (f" ({how})" if how else ""))
            if r["wrong"]:
                out.append(f"  - wrong: {r['wrong']}")
            if r["right"]:
                out.append(f"  - right: {r['right']}")
        out.append("")
    LEDGER_MD.write_text("\n".join(out), encoding="utf-8")


def update_ledger(run_dirs: list[Path]) -> int:
    with locked(ROOT):
        data = read_json(LEDGER_JSON, {"rows": {}})
        rows = data.setdefault("rows", {})
        for rd in sorted(run_dirs, key=lambda p: p.name):
            run = read_json(Path(rd) / "run.json", None)
            if run is None or not Path(rd).is_dir():
                continue
            pics = candidates_of(Path(rd))
            cand_digests = {md5(p_) for p_ in pics if GEN_RE.match(p_.name)}
            for pic in pics:
                if pic.name in PICKED and md5(pic) in cand_digests:
                    continue
                row = ledger_row(Path(rd), run, pic)
                old = rows.get(row["key"])
                if old and not row["wrong"] and not row["right"] and old.get("result", "").startswith(("PASS", "FAIL")) and row["result"] == "NOT CHECKED YET":
                    continue          # never overwrite a recorded verdict with a blank
                rows[row["key"]] = row
        write_json(LEDGER_JSON, data)
        write_ledger_md(rows)
    return len(rows)


def export_many(run_dirs: list[Path], dest: Path | None = None, dry: bool = False) -> list[str]:
    dest = Path(dest) if dest else results_dir()
    lines: list[str] = []
    with locked(dest):
        state = read_json(dest / STATE_NAME, {"files": {}})
        for rd in sorted(run_dirs, key=lambda p: p.name):
            lines += export_run(rd, dest, state, dry)
        if not dry:
            write_json(dest / STATE_NAME, state)
    if not dry:
        update_ledger(run_dirs)
    return lines


def safe_export(run_dir) -> None:
    """The end hook: never raises, so a full results disk or a locked folder cannot fail a generation run or a checklist record."""
    try:
        lines = export_many([Path(run_dir)])
        for ln in lines:
            print(f"[Export] {ln}")
        if lines:
            print(f"[Export] {len(lines)} change(s) in {results_dir()}")
    except Exception as exc:
        print(f"[Export] skipped: {exc}")


def import_picture(pic: Path, key: str, dest: Path | None = None, dry: bool = False) -> list[str]:
    """Bring a picture that already qualified but lives outside outputs\\ (an archived run folder, the user's best-versions folder) into the results
    folder (the user, 2026-10-01: "populate them if they are already present elsewhere"). It must pass like any other picture: a BEST or user-approved
    checklist recorded next to it. `key` is its goal's stem in results_names.json."""
    pic = Path(pic)
    ok, why = passed(pic)
    if not ok:
        return [f"not imported, it does not qualify: {pic} ({why})"]
    dest = Path(dest) if dest else results_dir()
    lines: list[str] = []
    with locked(dest):
        state = read_json(dest / STATE_NAME, {"files": {}})
        files = state.setdefault("files", {})
        digest, base = md5(pic), base_name(key)
        e = files.get(digest)
        if e is None or e.get("base") != base:
            ver = 1 + max([v["version"] for v in files.values() if v.get("base") == base] or [0])
            e = files[digest] = {"md5": digest, "base": base, "version": ver}
        name = f"{base}_v{e['version']}{pic.suffix.lower().replace('.jpeg', '.jpg')}"
        if not (dest / name).exists():
            lines.append(f"copy    {pic} -> {name}")
            if not dry:
                shutil.copy2(pic, dest / name)
        e.update({"file": name, "status": why, "identity": None, "run": str(pic.parent), "source_file": pic.name, "goal": key,
                  "exported": datetime.now().isoformat(timespec="seconds")})
        if not dry:
            write_json(dest / STATE_NAME, state)
    if not dry:
        chk = read_json(pic.with_name(pic.name + ".checklist.json"), {})
        with locked(ROOT):
            data = read_json(LEDGER_JSON, {"rows": {}})
            data.setdefault("rows", {})[f"import:{pic}"] = {
                "key": f"import:{pic}", "goal": base, "run": str(pic.parent), "file": pic.name, "time": str(chk.get("date", ""))[:16].replace("-", "").replace("T", "_").replace(":", ""),
                "result": "PASS (accepted by the user)" if chk.get("user_approved") else "PASS (all 30 items)", "identity": None, "pose_gate": "",
                "failed_items": [], "wrong": "", "right": str(chk.get("right") or chk.get("note") or ""), "recorded": datetime.now().isoformat(timespec="seconds")}
            write_json(LEDGER_JSON, data)
            write_ledger_md(data["rows"])
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="*", help="run folders (default: every run folder in outputs/)")
    ap.add_argument("--dest", default=None, help="results folder (default: paths.results_dir())")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--import", dest="import_pic", default=None, metavar="PICTURE", help="bring in an already-qualified picture from outside outputs/ (needs --goal-key)")
    ap.add_argument("--goal-key", default=None, help="with --import: the goal's stem in results_names.json, e.g. pin_783485666539775315")
    args = ap.parse_args()
    if args.import_pic:
        if not args.goal_key:
            ap.error("--import needs --goal-key")
        for ln in import_picture(Path(args.import_pic), args.goal_key, Path(args.dest) if args.dest else None, args.dry_run):
            print(ln)
        return 0
    runs = [Path(r) for r in args.runs] or [p for p in sorted((ROOT / "outputs").iterdir()) if (p / "run.json").exists()]
    lines = export_many(runs, Path(args.dest) if args.dest else None, args.dry_run)
    for ln in lines:
        print(("[dry run] " if args.dry_run else "") + ln)
    print(f"{len(lines)} change(s){' (dry run, nothing written)' if args.dry_run else ''} -> {args.dest or results_dir()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
