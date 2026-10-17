"""Run a wave of generations from one spec file, after the credit window resets or at a time, with the credit guard doing the pacing (replaces the ad-hoc .cache\\waveN.sh scripts).

    .venv\\Scripts\\python.exe tools\\wave.py <spec.json> [--after-reset | --at HH:MM | --not-before HH:MM] [--parallel N] [--stagger SECONDS] [--dry-run]
        --parallel N: at most N runs at the same time, each started --stagger seconds (default 5) after the previous one; default all at once.
        Stage 06 (the segmentation models) runs out of memory when four runs measure together on this 16 GB box: use --parallel 2 --stagger 240.
        A job with "restore": true gets tools/background_restore.py run on its run folder when its run has ended (recipes with restore_background).
        --min-free-gb G (default 1.5): a run starts only after G GB has been free for 60 s and while no overnight local render (sd-cli.exe) runs.
        Before every start the Gemini sign-in is checked (tools/session_check.py); a refusal is checked again after 2 and 5 minutes, and only a
        refusal that lasts halts the wave (--no-session-check skips it). A run that exits 3 (credit guard) also halts it: later runs would fail
        the same way. Each run's processes (PID + start time) are kept in .cache\\wave_<tag>.runs.json, which other waves read to know what runs.
    .venv\\Scripts\\python.exe tools\\wave.py --stop <tag> [--now]
        No new run of that wave starts; running runs finish. --now also ends its runs that have not signed in yet (stage 01-03, nothing spent)
        and checks none is left; a signed-in run always finishes. A halted or stopped wave lists its runs not started in .cache\\failures.jsonl.

spec.json (the consistent form, 2026-10-07: a job names a RECIPE version; the run sends exactly its locked request through the 8 stages):
  {"tag": "wave12",
   "jobs": [{"name": "pin5", "recipe": "pin_783485666539777054@v1", "samples": 2, "repeat": 2}]}

Legacy jobs (a gen command assembled from parts) still work:
  {"tag": "wave11",
   "jobs": [{"name": "pin5", "goal": ".cache/pin_783485666539777054.jpg", "inventory": ".cache/inventories/pin_783485666539777054_v6.json",
             "prompt": ".cache/loop_prompts/pin_783485666539777054_route.txt",   (default: .cache/loop_prompts/<goal stem>_route.txt)
             "model": "pro",                       ("pro" | "flash" | a model id; default: the config model)
             "count": 1, "repeat": 3,              (repeat = how many separate runs of this job; each is its own process and run folder)
             "extra": ["--face-refs", "@clean_studio"]}]}

Every run is a plain `facecard.py gen --replace-subject ... --stop-after-fails 2` process; the guard inside gen (credit_guard.py) lets at most 4 generate at once and makes the
rest wait for a free slot or for the window to refill, so the wave never overspends and never needs to be sized by hand. Logs: .cache\\wave_<tag>_<job><k>.log; when every run
has ended: .cache\\wave_<tag>.done and a one-line-per-run summary in .cache\\wave_<tag>.summary.txt (tools\\run_status.py shows the scores).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PY = ROOT / ".venv" / "Scripts" / "python.exe"
PRO = "e6fa609c3fa255c0"


def wait_until(args) -> None:
    if args.not_before:    # never rolls over to tomorrow: a task that starts late runs at once
        hh, mm = (int(x) for x in args.not_before.split(":"))
        t = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
        print(f"waiting until {t:%H:%M} (starts at once if that has passed)", flush=True)
        while datetime.now() < t:
            time.sleep(20)
    elif args.at:
        hh, mm = (int(x) for x in args.at.split(":"))
        t = datetime.now().replace(hour=hh, minute=mm, second=0, microsecond=0)
        if t <= datetime.now():
            t += timedelta(days=1)
        print(f"waiting until {t:%Y-%m-%d %H:%M}", flush=True)
        while datetime.now() < t:
            time.sleep(20)
    elif args.after_reset:
        import credit_guard
        eta = credit_guard.reset_in_seconds()
        if eta is None or eta <= 0:
            print("no future reset time in .cache/quota.json (run tools\\quota.py first): starting now", flush=True)
            return
        print(f"waiting {eta / 60:.0f} min for the window to reset, plus 2 min", flush=True)
        time.sleep(eta + 120)


def free_gb() -> float:
    """Available physical memory in GB (GlobalMemoryStatusEx)."""
    import ctypes

    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ("total", "avail", "tpf", "apf", "tv", "av", "aev")]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2 ** 30


def local_render_running() -> bool:
    """The overnight Qwen render (tools/overnight.py -> sd-cli.exe) holds most of the RAM while it runs. From the moment the night makes
    room until its picture ends, its claim (tools/room.py) counts too: a wave must not take the memory freed for the picture (2026-10-10)."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from room import claimed
        if claimed():
            return True
    except Exception:
        pass
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq sd-cli.exe", "/NH"], capture_output=True, text=True).stdout
    return "sd-cli.exe" in out


def memory_block(min_free: float, tag: str, own_running: int = 0) -> str | None:
    """Why a run must not start now, or None. 2026-10-10 03:41: a run started beside the overnight Qwen render was paged out (working set 0.2 of
    2.2 GB, 0.37 GB free) and made no progress for 10 minutes; so a run starts only when no local render is running and min_free GB is free.
    Two waves waiting on the same render would start together when it ends, so a run also waits CROSS_STAGGER s after another wave's start."""
    if local_render_running():
        return "the overnight local render (sd-cli.exe) is running"
    free = free_gb()
    if free < min_free:
        return f"free memory {free:.2f} GB < {min_free:g} GB"
    now = time.time()
    for p in (ROOT / ".cache").glob("wave_*_*.log"):
        if p.name.startswith(f"wave_{tag}_") or p.name.endswith(".restore.log"):
            continue
        age = now - p.stat().st_ctime          # Windows: the creation time, i.e. when that run started
        if age < CROSS_STAGGER:
            return f"another wave started {p.stem[5:]} {age:.0f} s ago (< {CROSS_STAGGER} s)"
    others = other_waves_running(tag)
    if own_running + len(others) >= MAX_TOTAL:
        return f"{own_running + len(others)} run(s) already going ({', '.join(others) or 'this wave'}); at most {MAX_TOTAL} at once"
    return None


CROSS_STAGGER = 240
MAX_TOTAL = 2            # runs at once over every wave (the plan, 2026-10-10: "at most 2 runs at once, 4 minutes apart")


def credit_block(min_credits: int) -> str | None:
    """Why a run must not start now for credits, or None. F69 (2026-10-14): a run that started with 124 credits left sat 113 minutes at its own credit guard,
    signed in, and its session expired (exit 5), so the wait belongs here, before the sign-in. Reads .cache/quota.json (tools/quota.py refreshes it when it is
    older than 10 minutes or past its reset); a meter that cannot be read never blocks."""
    qf = ROOT / ".cache" / "quota.json"

    def load():
        try:
            d = json.loads(qf.read_text(encoding="utf-8"))
            w = d["current_5h"]
            return (int(w["remaining_credits"]), datetime.fromisoformat(w["reset_at"]), datetime.fromisoformat(d["read_at"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    q = load()
    nowd = datetime.now().astimezone()
    if q is None or nowd - q[2] > timedelta(minutes=10) or nowd >= q[1]:
        try:
            subprocess.run([sys.executable, "tools/quota.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=240)
        except (OSError, subprocess.SubprocessError):
            pass
        q = load() or q
    if q is None:
        return None
    left, reset, _ = q
    if left < min_credits and nowd < reset:
        return f"the window holds {left} credits < {min_credits}; it resets at {reset:%H:%M}"
    return None


def other_waves_running(tag: str) -> list[str]:
    """Runs of other waves that are really running. A wave with a runs file (wave_<tag>.runs.json, since 2026-10-10) is asked by process: each
    run's PID with its start time, and the child the venv launcher starts. An older wave without one falls back to its log: started, no exit
    line, job log grown in the last 20 minutes. (2026-10-10: that fallback counted a stopped run for 20 minutes and missed nothing else.)"""
    import re
    out, now = [], time.time()
    for p in (ROOT / ".cache").glob("wave_*.log"):
        m = re.fullmatch(r"wave_([^_]+)\.log", p.name)
        if not m or m.group(1) == tag:
            continue
        other = m.group(1)
        table = load_runs(other)
        if table is not None:
            out += [f"{other}/{name}" for name, e in table.items() if e.get("ended") is None and alive(e)]
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        for name in re.findall(r" start (\S+?): ", t):
            if f"{name}: exit" in t:
                continue
            jl = ROOT / ".cache" / f"wave_{other}_{name}.log"
            if jl.is_file() and now - jl.stat().st_mtime < 1200:
                out.append(f"{other}/{name}")
    return out


# ------------------------------------------------------------------------------------------------ runs by process, the session, stopping
# The user, 2026-10-10, after an evening of repeated failures (FAILURE_LOG.md F1-F4): a wave kept starting runs into a failure all of them
# shared, counted "running" from log growth, and could only be stopped by hand, which left a run going on its own that spent 346 credits.


def runs_path(tag: str) -> Path:
    return ROOT / ".cache" / f"wave_{tag}.runs.json"


def load_runs(tag: str) -> dict | None:
    p = runs_path(tag)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_runs(tag: str, table: dict) -> None:
    p = runs_path(tag)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(table, indent=1), encoding="utf-8")
    tmp.replace(p)


def proc_ids(pid: int) -> list[list[float]]:
    """[pid, start time] of a process and of every child it has now (the venv's python.exe starts the real interpreter as its child)."""
    import psutil
    try:
        p = psutil.Process(pid)
        return [[p.pid, p.create_time()]] + [[c.pid, c.create_time()] for c in p.children(recursive=True)]
    except psutil.Error:
        return []


def alive(entry: dict) -> bool:
    """Any of the run's recorded processes still running: a PID counts only with its own start time, so a reused PID is never mistaken."""
    import psutil
    for pid, ctime in entry.get("procs") or []:
        try:
            if abs(psutil.Process(int(pid)).create_time() - float(ctime)) < 1.0:
                return True
        except psutil.Error:
            continue
    return False


def signed_in_yet(tag: str, name: str) -> bool:
    """Has the run reached stage 04 (sign-in, credits)? Before it, stopping it costs nothing and holds no session."""
    jl = ROOT / ".cache" / f"wave_{tag}_{name}.log"
    try:
        return "[04/08 credits]" in jl.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def session_check(env: dict) -> tuple[bool, str]:
    """tools/session_check.py: (signed in, its one line). A check that cannot run counts as not signed in."""
    try:
        r = subprocess.run([str(PY), "tools/session_check.py"], cwd=str(ROOT), capture_output=True, text=True, env=env, timeout=600)
        line = next((ln for ln in reversed(r.stdout.splitlines()) if ln.startswith(("signed in", "not signed in"))), r.stdout.strip()[-200:])
        return r.returncode == 0, line
    except Exception as e:
        return False, f"session check failed to run: {type(e).__name__}: {e}"


def pose_summary(tag: str, name: str) -> str:
    """'pose gate 1 pass / 1 fail' from the run's stage 06 line, so the wave log shows more than 'rendered'."""
    import re
    jl = ROOT / ".cache" / f"wave_{tag}_{name}.log"
    try:
        m = re.findall(r"pose gate (\d+) pass / (\d+) fail", jl.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""
    return f"; pose gate {m[-1][0]} pass / {m[-1][1]} fail" if m else ""


def record_failure(row: dict) -> None:
    """The wave's own failures (a halt, runs not started) in .cache/failures.jsonl, beside the runs' (runner.record_failure)."""
    with contextlib.suppress(Exception):
        with (ROOT / ".cache" / "failures.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), **row}, ensure_ascii=False) + "\n")


def stop_wave(tag: str, now: bool) -> int:
    """--stop TAG: no new run starts; the running ones finish (the wave sees .cache/wave_<tag>.stop before every start). --now also ends the
    runs that have not signed in yet (stage 01-03: nothing spent, no session held), each with every child it has at this moment, and checks
    that none is left. A run that has signed in always finishes: a logged-in run is never force-killed (AGENTS.md)."""
    import psutil
    (ROOT / ".cache" / f"wave_{tag}.stop").write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    print(f"wave {tag}: stop requested; no new run will start")
    table = load_runs(tag) or {}
    live = {name: e for name, e in table.items() if e.get("ended") is None and alive(e)}
    if not now:
        for name in live:
            print(f"  {name}: running, it finishes on its own")
        return 0
    not_stopped = []
    for name, e in live.items():
        if signed_in_yet(tag, name):
            print(f"  {name}: signed in, left to finish")
            continue
        procs = []
        for pid, ctime in e.get("procs") or []:
            for q_pid, q_ctime in proc_ids(int(pid)):          # the tree as it is now, not as it was recorded
                with contextlib.suppress(psutil.Error):
                    q = psutil.Process(q_pid)
                    if abs(q.create_time() - q_ctime) < 1.0:
                        procs.append(q)
        for q in reversed(procs):
            with contextlib.suppress(psutil.Error):
                q.kill()
        psutil.wait_procs(procs, timeout=10)
        still = [q.pid for q in procs if q.is_running()]
        print(f"  {name}: stopped before sign-in" + (f"; STILL RUNNING: {still}" if still else ", nothing left"))
        if still:
            not_stopped.append(name)
    return 1 if not_stopped else 0


def command(job: dict, tag: str) -> list[str]:
    if job.get("recipe"):
        cmd = [str(PY), "facecard.py", "run", str(job["recipe"])]
        if job.get("samples") or job.get("count"):
            cmd += ["--samples", str(job.get("samples") or job.get("count"))]
        if job.get("stop_after_fails") is not None:
            cmd += ["--stop-after-fails", str(job["stop_after_fails"])]
        return cmd + [str(x) for x in job.get("extra", [])]
    goal = job["goal"]
    prompt = job.get("prompt") or f".cache/loop_prompts/{Path(goal).stem}_route.txt"
    model = {"pro": PRO, "flash": None}.get(str(job.get("model", "")).lower(), job.get("model"))
    cmd = [str(PY), "facecard.py", "gen", "--subject", "me", "--count", str(job.get("count", 1)), "--goal", goal, "--prompt", prompt,
           "--goal-as-image", "no", "--replace-subject", "--inventory", job["inventory"], "--stop-after-fails", str(job.get("stop_after_fails", 2))]
    if model:
        cmd += ["--model", model]
    return cmd + [str(x) for x in job.get("extra", [])]


def restore_after(name: str, tag: str, env: dict, say) -> str:
    """tools/background_restore.py on the run folder a finished run printed ("RUN <folder>" in its log); one line for the summary."""
    logp = ROOT / ".cache" / f"wave_{tag}_{name}.log"
    run_dir = None
    for line in logp.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("RUN "):
            run_dir = line[4:].strip()
            break
    if not run_dir or not Path(run_dir).is_dir():
        return "; background restore skipped: no run folder in the log"
    say(f"restore {name}: {Path(run_dir).name}")
    rlog = ROOT / ".cache" / f"wave_{tag}_{name}.restore.log"
    with open(rlog, "w", encoding="utf-8") as f:
        rc = subprocess.run([str(PY), "tools/background_restore.py", run_dir], cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT, env=env).returncode
    return f"; background restore exit {rc} ({rlog.name})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--after-reset", action="store_true", help="wait for the 5-hour window to reset (reset time from .cache/quota.json) plus 2 minutes")
    ap.add_argument("--at", default=None, help="start at HH:MM (today, or tomorrow if already past)")
    ap.add_argument("--not-before", default=None, help="start at HH:MM today, or at once when that has already passed (never tomorrow)")
    ap.add_argument("--dry-run", action="store_true", help="print the commands and stop")
    ap.add_argument("--parallel", type=int, default=0, help="at most N runs at the same time (default: all at once)")
    ap.add_argument("--stagger", type=int, default=5, help="seconds between two run starts (default 5)")
    ap.add_argument("--min-free-gb", type=float, default=1.5, help="a run starts only when this much memory has been free for 60 s and no overnight "
                    "local render (sd-cli.exe) is running (default 1.5; 0 turns the check off)")
    ap.add_argument("--min-credits", type=int, default=390, help="a run starts only when the 5-hour window holds this many credits (the credit guard's own rule for a "
                    "2-sample run: need 240 + margin 150); a run that waits at its own guard stays signed in and its session expires (F69). 0 turns the check off")
    ap.add_argument("--stop", metavar="TAG", default=None, help="stop wave TAG: no new run starts, the running ones finish")
    ap.add_argument("--now", action="store_true", help="with --stop: also end the runs that have not signed in yet (nothing spent), then check "
                    "that none of them is left; a signed-in run always finishes")
    ap.add_argument("--no-session-check", action="store_true", help="start runs without checking the Gemini session first")
    a = ap.parse_args()
    if a.stop:
        return stop_wave(a.stop, a.now)
    if not a.spec:
        ap.error("a spec file is needed (or --stop TAG)")
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    tag = spec.get("tag") or Path(a.spec).stem
    runs = []
    for job in spec["jobs"]:
        for k in range(int(job.get("repeat", 1))):
            # "deep_edit_ok": the user's own words asking for an edit of an edit (runner.py refuses one otherwise: RETROSPECTIVE_2026-10-17.md)
            runs.append((f"{job.get('name', 'job')}{k + 1}", command(job, tag), bool(job.get("restore")), str(job.get("deep_edit_ok") or "")))
    if a.dry_run:
        for name, cmd, restore, deep_ok in runs:
            print(name, " ".join(cmd), "  [+ background_restore]" if restore else "", f"  [deep edit allowed: {deep_ok[:60]}]" if deep_ok else "")
        return 0
    if (ROOT / ".cache" / "GENERATION_HOLD").exists():
        print("HOLD: image generation is stopped by the user (.cache/GENERATION_HOLD); no run of this wave starts", flush=True)
        return 6
    done = ROOT / ".cache" / f"wave_{tag}.done"
    done.unlink(missing_ok=True)
    stop_file = ROOT / ".cache" / f"wave_{tag}.stop"
    stop_file.unlink(missing_ok=True)                  # a stop meant for an earlier wave with this tag
    logfile = ROOT / ".cache" / f"wave_{tag}.log"

    def say(msg: str) -> None:
        line = f"{datetime.now():%H:%M:%S} {msg}"
        print(line, flush=True)
        with logfile.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    wait_until(a)
    say(f"=== wave {tag} start: {len(runs)} run(s)" + (f", at most {a.parallel} at once, {a.stagger} s apart" if a.parallel else ""))
    env = {**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    table: dict = {}
    save_runs(tag, table)
    pending, running, lines = list(runs), [], []
    last_start, mem_ok_since, mem_said, mem_reason = 0.0, None, 0.0, None
    cred_said, cred_reason = 0.0, None
    halt = None                     # why no further run starts: a stop, a sign-in that stays refused, the credit guard
    sess_fails, sess_next = 0, 0.0
    session_retry = (120, 300)      # a refused sign-in is checked again after 2 and after 5 more minutes, then the wave halts
    while pending or running:
        for item in list(running):
            name, p, log, restore = item
            e = table.get(name)
            if e is not None and len(e["procs"]) < 2:         # pick up the interpreter the venv launcher starts as its child
                ids = proc_ids(p.pid)
                if len(ids) > len(e["procs"]):
                    e["procs"] = ids
                    save_runs(tag, table)
            rc = p.poll()
            if rc is None:
                continue
            running.remove(item)
            log.close()
            msg = f"{name}: exit {rc}" + {0: " (rendered)", 1: " (no render)", 2: " (the method stage refused: see the run's report)",
                                          3: " (credit guard refused)", 4: " (rendered or stopped, a later stage failed: see the run's report)",
                                          5: " (the Gemini sign-in failed)", 6: " (generation is on hold by the user)",
                                          7: " (refused: an edit of an edit, more than one render plus one fix)"}.get(rc, "")
            if rc in (0, 4):
                msg += pose_summary(tag, name)
            if restore and rc in (0, 4):
                try:
                    msg += restore_after(name, tag, env, say)
                except Exception as exc:       # a restore problem must never stop the queue
                    msg += f"; background restore failed: {type(exc).__name__}: {exc}"
            if e is not None:
                e.update({"ended": datetime.now().isoformat(timespec="seconds"), "rc": rc})
                save_runs(tag, table)
            lines.append(msg)
            say(msg)
            if rc == 3 and not halt:
                halt = "the credit guard refused a run (exit 3): every later run would be refused the same way"
        if stop_file.exists() and not halt:
            halt = f"stop requested ({stop_file.name})"
        if halt and pending:
            names = [item[0] for item in pending]
            say(f"halt: {halt}; {len(names)} run(s) not started: {', '.join(names)}")
            record_failure({"wave": tag, "halted": halt, "not_started": names})
            lines += [f"{n}: not started ({halt})" for n in names]
            pending = []
            continue
        ready = pending and (not a.parallel or len(running) < a.parallel) and time.time() - last_start >= a.stagger
        if ready and a.min_free_gb > 0:
            why = memory_block(a.min_free_gb, tag, len(running))
            if why:
                mem_ok_since = None
                if why.split(" ")[0:3] != (mem_reason or "").split(" ")[0:3] or time.time() - mem_said >= 600:   # the reason, not its numbers
                    say(f"memory: {pending[0][0]} waits ({why})")
                    mem_said, mem_reason = time.time(), why
                ready = False
            else:
                mem_ok_since = mem_ok_since or time.time()
                ready = time.time() - mem_ok_since >= 60
        if ready and a.min_credits > 0:
            why_c = credit_block(a.min_credits)
            if why_c:
                if why_c.split(" ")[0:3] != (cred_reason or "").split(" ")[0:3] or time.time() - cred_said >= 900:
                    say(f"credits: {pending[0][0]} waits ({why_c})")
                    cred_said, cred_reason = time.time(), why_c
                ready = False
            else:
                cred_reason = None
        if ready and not a.no_session_check:
            # signed in? checked before every start (2026-10-10 20:20: every sign-in was refused for ten minutes); a refusal waits and checks
            # again, and only a refusal that lasts halts the wave, instead of every queued run failing into it
            if time.time() < sess_next:
                ready = False
            else:
                ok, line = session_check(env)
                if ok:
                    if sess_fails:
                        say(f"session: signed in again ({line})")
                    sess_fails = 0
                else:
                    sess_fails += 1
                    if sess_fails > len(session_retry):
                        halt = f"the Gemini sign-in was refused {sess_fails} times in a row ({line})"
                    else:
                        wait_s = session_retry[sess_fails - 1]
                        say(f"session: {pending[0][0]} waits {wait_s // 60} min, sign-in refused ({line})")
                        sess_next = time.time() + wait_s
                    ready = False
        if ready:
            mem_ok_since, mem_reason = None, None
            name, cmd, restore, deep_ok = pending.pop(0)
            log = open(ROOT / ".cache" / f"wave_{tag}_{name}.log", "w", encoding="utf-8")
            job_env = {**env, "FACECARD_DEEP_EDIT_OK": deep_ok} if deep_ok else {k: v for k, v in env.items() if k != "FACECARD_DEEP_EDIT_OK"}
            proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, env=job_env)
            running.append((name, proc, log, restore))
            table[name] = {"procs": proc_ids(proc.pid), "started": datetime.now().isoformat(timespec="seconds"), "ended": None, "rc": None,
                           "cmd": " ".join(cmd[2:5])}
            save_runs(tag, table)
            last_start = time.time()
            say(f"start {name}: {' '.join(cmd[2:5])}")
        time.sleep(5)
    (ROOT / ".cache" / f"wave_{tag}.summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    done.write_text(datetime.now().isoformat(), encoding="utf-8")
    say(f"=== wave {tag} done" + (f" early: {halt}" if halt else ""))
    return 1 if halt else 0


if __name__ == "__main__":
    sys.exit(main())
