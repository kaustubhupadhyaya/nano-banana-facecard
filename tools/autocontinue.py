"""Auto-continue (the user, 2026-10-11: "did you not autoresume when credits got refreshed? create a system to auto-continue for claude code
when gemini image credits refresh"). On 2026-10-10 the work sat idle for three hours after a question to the user, through a full refill.

Two layers:
1. The hidden task `facecard-autocontinue` runs `tick` every 15 minutes. When the Gemini window holds the credits the next queued wave needs,
   no wave is running and the overnight local render holds no claim, it starts that wave as its own hidden one-time task (tools/wave.py,
   which then checks the sign-in before every run). No Claude session is needed, and it survives a closed one.
2. A Claude Code session wakes on its own schedule (CronCreate, session-only, 7 days) and reads `status`: waves that ended since the last
   look are listed under TO REVIEW; the session checks their pictures (BEST_CHECKLIST.md), records failures (FAILURE_LOG.md), marks the
   wave reviewed, works the [claude] to-dos, and queues the next versions.

Claude's work never reads as idle (the user, 2026-10-11 22:2x: "why is the decision idle and nothing is queued when you already know there
are so many to-do items in the list?"; from 17:18 to 22:24 nothing advanced while three [claude] to-dos waited behind questions to the user):
- The decision is `work: ...` while a wave waits for review or a [claude] to-do is ready, whatever the queue holds; `idle` only when there is
  no wave queued or running, nothing to review and no [claude] to-do.
- `STALLED` when that work has seen no progress (a wave queued, started, ended or reviewed, a to-do done) for STALL_MIN minutes; the tick then
  sends the user one Windows toast per stall.
- A [user] item is only the user's own approval or choice, and never holds up a [claude] item. A question that has a sensible answer is
  filed with `--default`: the recommended step becomes a [claude] item, done at once, and the user can redirect it.
- `--after <tag>` marks a [claude] item that waits for a queued or running wave; every other [claude] item is ready now.

Questions are asked at once and never wait (the user, 2026-10-11 23:0x: "immediately ask using ask-user-question tool and on top of that
still not be blocked by it and just choose the recommended option to keep working on until i answer"):
1. Claude starts the recommended option's step (queues it), then files the question: `ask "<question>" --header <chip> --option
   "<label>|<what it means>" ...` (2-4 options, the recommended one first), linked to that step (`--default` or `--default-todo`).
2. `questions --mark-asked` prints the AskUserQuestion payload (4 questions per call) and the session asks it at once, itself: a background
   agent cannot (AskUserQuestion is not available to subagents: "No matching deferred tools found", 2026-10-11 23:15). Before the call the
   session starts every default step and hands any long preparation to background agents, so the waves (this task) and those agents keep
   working while the question waits; the session alone pauses.
3. `answer <n> "<label>"` records the reply; a choice other than the recommended one closes the default item and files a READY redirect.
An open question is never Claude's work; a question not yet asked is (`work: ... question(s) to ask`). Asked questions still open are named
in the decision, so a STALLED toast also tells the user that a question is waiting for him in Claude Code.

    .venv\\Scripts\\python.exe tools\\autocontinue.py status
    .venv\\Scripts\\python.exe tools\\autocontinue.py tick                       (the task's command; also safe by hand)
    .venv\\Scripts\\python.exe tools\\autocontinue.py add <spec.json> [--credits N] [--parallel 2] [--stagger 240] [--note TEXT]
    .venv\\Scripts\\python.exe tools\\autocontinue.py todo "<what>" [--who claude|user] [--after TAG] [--default "<step Claude takes now>"]
    .venv\\Scripts\\python.exe tools\\autocontinue.py done-todo <n> [--note TEXT]   |   edit-todo <n> [--who] [--what] [--after]
    .venv\\Scripts\\python.exe tools\\autocontinue.py ask "<question>" --header CHIP --option "label|meaning" ... [--default "<step>" | --default-todo N] [--multi]
    .venv\\Scripts\\python.exe tools\\autocontinue.py questions [--mark-asked] [--all]   |   answer <n> "<label>" [--note TEXT]
    .venv\\Scripts\\python.exe tools\\autocontinue.py reviewed <tag>   |   remove <tag>
    .venv\\Scripts\\python.exe tools\\autocontinue.py install                    (register the 15-minute task)

State: .cache/autocontinue.json (queue, to-do list, last progress); decisions: .cache/autocontinue.log (one line when the decision changes,
and at most hourly while it stays the same).
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
PY = ROOT / ".venv" / "Scripts" / "python.exe"
RUNHIDDEN = Path(r"C:\Users\Admin\bin\runhidden\runhidden.exe")
STATE = ROOT / ".cache" / "autocontinue.json"
LOG = ROOT / ".cache" / "autocontinue.log"
QUOTA = ROOT / ".cache" / "quota.json"
HOLD = ROOT / ".cache" / "GENERATION_HOLD"   # the user, 2026-10-17: "Do not generate any more images. Keep the to-dos on hold": while it exists nothing starts
TASK = "facecard-autocontinue"
PER_PICTURE = 200          # credits planned per Flash picture (measured 95-196 on 2026-10-10, FAILURE_LOG.md F8)
STALL_MIN = 60             # minutes without progress while Claude has work: STALLED, and one toast to the user per stall
SPARE_MIN = 600            # credits left in the 5-hour window (after what is queued) from which they count as spare: they are lost at the reset
TOAST_APP = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"   # job-tracker's Show-Toast uses the same


def now() -> datetime:
    return datetime.now().astimezone()


def load() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"queue": [], "todo": []}


LOCK = ROOT / ".cache" / "autocontinue.lock"


class state_lock:
    """One command at a time on the state file (2026-10-14: several agents wrote it together: a save failed with WinError 32 and writes could
    overwrite each other). The lock is a file made with O_EXCL; a lock older than 10 minutes is a dead holder's and is taken over."""

    def __enter__(self):
        import os
        import time
        end = time.time() + 150
        while True:
            try:
                fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}".encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - LOCK.stat().st_mtime > 600:
                        LOCK.unlink()
                        continue
                except OSError:
                    pass
                if time.time() > end:
                    raise SystemExit("autocontinue: the state file is locked by another command for over 150 s; try again")
                time.sleep(0.3)

    def __exit__(self, *exc):
        try:
            LOCK.unlink()
        except OSError:
            pass
        return False


def save(st: dict) -> None:
    import os
    tmp = STATE.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE)


def log(decision: str) -> None:
    """One line per change of decision (the reason without its numbers), and at most hourly while it stays the same."""
    key = re.sub(r"[0-9][0-9:.,]*", "#", decision)
    last = ""
    try:
        last = LOG.read_text(encoding="utf-8").splitlines()[-1]
    except (OSError, IndexError):
        pass
    last_key = re.sub(r"[0-9][0-9:.,]*", "#", last.split(" ", 1)[-1]) if last else ""
    try:
        last_t = datetime.fromisoformat(last.split(" ", 1)[0]) if last else None
    except ValueError:
        last_t = None
    if key == last_key and last_t and now() - last_t < timedelta(hours=1):
        return
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now().isoformat(timespec='seconds')} {decision}\n")


def alert(title: str, body: str) -> str:
    """A Windows toast to the user (an alert, no window): PowerShell 5.1's WinRT notifier, the call job-tracker's Show-Toast makes."""
    esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))
    ps = ("$ProgressPreference = 'SilentlyContinue'\n"            # loading the WinRT types writes a progress record to stderr otherwise
          "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
          "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null\n"
          "$x = New-Object Windows.Data.Xml.Dom.XmlDocument\n"
          f"$x.LoadXml('<toast><visual><binding template=\"ToastGeneric\"><text>{esc(title)}</text><text>{esc(body)}</text>"
          "</binding></visual></toast>')\n"
          f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{TOAST_APP}').Show("
          "[Windows.UI.Notifications.ToastNotification]::new($x))\n")
    r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand",
                        base64.b64encode(ps.encode("utf-16-le")).decode("ascii")],
                       capture_output=True, text=True, timeout=60, creationflags=0x08000000)       # CREATE_NO_WINDOW
    ok = r.returncode == 0 and 'S="Error"' not in r.stderr and "Exception" not in r.stderr
    return "toast sent" if ok else f"toast failed: {(r.stderr or r.stdout).strip()[:200]}"


def credit_window(max_age_min: float = 20.0) -> dict:
    """{left, reset_at, read_at} from .cache/quota.json; read again (tools/quota.py signs in) when older than max_age_min or when the window
    has reset since the last reading."""
    def read() -> dict | None:
        try:
            q = json.loads(QUOTA.read_text(encoding="utf-8"))
            c = q.get("current_5h") or {}
            return {"left": c.get("remaining_credits"), "reset_at": datetime.fromisoformat(c["reset_at"]),
                    "read_at": datetime.fromisoformat(q["read_at"])}
        except (OSError, ValueError, KeyError, TypeError):
            return None
    q = read()
    if q is None or now() - q["read_at"] > timedelta(minutes=max_age_min) or now() >= q["reset_at"]:
        subprocess.run([str(PY), "tools/quota.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        q = read() or q
    return q or {"left": None, "reset_at": None, "read_at": None}


def waves_running() -> list[str]:
    """Waves whose driver (tools/wave.py) is alive, by process: the spec file names."""
    import psutil
    out = []
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            cl = " ".join(p.info["cmdline"] or [])
        except psutil.Error:
            continue
        m = re.search(r"tools[\\/]wave\.py\"?\s+\"?([^\"\s]+)", cl)
        if m and "--stop" not in cl and "--dry-run" not in cl:
            out.append(Path(m.group(1)).stem)
    return sorted(set(out))


def night_claim() -> bool:
    """The overnight local render's claim (tools/wave.py local_render_running), loaded by path: `import wave` can be Python's own audio module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("facecard_wave", ROOT / "tools" / "wave.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.local_render_running()


def spec_tag(spec: Path) -> str:
    s = json.loads(spec.read_text(encoding="utf-8"))
    return s.get("tag") or spec.stem


def spec_credits(spec: Path) -> int:
    s = json.loads(spec.read_text(encoding="utf-8"))
    pics = sum(int(j.get("samples") or j.get("count") or 2) * int(j.get("repeat", 1)) for j in s.get("jobs", []))
    return pics * PER_PICTURE


def user_sid() -> str:
    out = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"], capture_output=True, text=True).stdout.strip()
    return out.split(",")[-1].strip('"')


def task_xml(desc: str, command: str, arguments: str, start: datetime, repeat: str | None, limit: str) -> str:
    rep = f"<Repetition><Interval>{repeat}</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>" if repeat else ""
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>{esc(desc)}</Description></RegistrationInfo>
  <Principals><Principal id="Author"><UserId>{user_sid()}</UserId><LogonType>InteractiveToken</LogonType></Principal></Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>{limit}</ExecutionTimeLimit>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Hidden>true</Hidden>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
  </Settings>
  <Triggers><TimeTrigger>{rep}<StartBoundary>{start.strftime("%Y-%m-%dT%H:%M:%S")}</StartBoundary></TimeTrigger></Triggers>
  <Actions Context="Author"><Exec><Command>{esc(command)}</Command><Arguments>{esc(arguments)}</Arguments><WorkingDirectory>{ROOT}</WorkingDirectory></Exec></Actions>
</Task>
'''


def register(name: str, xml: str, run_now: bool) -> str:
    x = ROOT / ".cache" / f"{name}.xml"
    x.write_text(xml, encoding="utf-16")
    r = subprocess.run(["schtasks", "/create", "/tn", name, "/xml", str(x), "/f"], capture_output=True, text=True)
    msg = (r.stdout or r.stderr).strip()
    if run_now and r.returncode == 0:
        subprocess.run(["schtasks", "/run", "/tn", name], capture_output=True, text=True)
    return msg


def start_wave(item: dict) -> str:
    """The wave as its own hidden one-time task (it outlives this tick), started at once."""
    name = f"facecard-wave-{item['id']}"
    args = (f'"{PY}" "{ROOT / "tools" / "wave.py"}" "{ROOT / item["spec"]}" --parallel {item.get("parallel", 2)} '
            f'--stagger {item.get("stagger", 240)} --min-free-gb 1.5')
    xml = task_xml(f"Facecard wave {item['id']} (started by tools/autocontinue.py): {item.get('note') or ''} Delete after use.",
                   str(RUNHIDDEN), args, now() + timedelta(minutes=1), None, "PT6H")
    return register(name, xml, run_now=True)


MEM_WAIT_MIN = 10          # minutes a running wave may sit on the memory gate before the ping hands Claude a FREE MEMORY task


def memory_blocked(running: list[str]) -> list[tuple[str, int, str]]:
    """Running waves whose log ends in an unbroken run of `memory: ... waits (free memory X GB < Y GB)` lines older than MEM_WAIT_MIN:
    the driver is alive but nothing renders (pin12b, 2026-10-14: 55 minutes at 0.7 GB free read as 'busy'). Returns (wave, minutes, last line)."""
    out = []
    for w in running:
        log = ROOT / ".cache" / (f"{w}.log" if w.startswith("wave_") else f"wave_{w}.log")     # waves_running() names the spec: wave_<tag>
        try:
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
        except OSError:
            continue
        first = last = None
        for ln in reversed(lines):
            m = re.match(r"(\d\d:\d\d:\d\d) memory: .* waits \(free memory", ln)
            if not m:
                break
            first = m.group(1)
            last = last or ln
        if not first:
            continue
        t = datetime.strptime(first, "%H:%M:%S").time()
        since = now().replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
        if since > now():
            since -= timedelta(days=1)
        waited = int((now() - since).total_seconds() // 60)
        if waited >= MEM_WAIT_MIN:
            out.append((w, waited, last[9:]))
    return out


def progress(st: dict, what: str) -> None:
    """Something advanced: the stall clock starts again."""
    st["progress_at"] = now().isoformat(timespec="seconds")
    st["progress_what"] = what
    st.pop("stall_alerted", None)


def last_progress(st: dict) -> tuple[datetime | None, str]:
    if st.get("progress_at"):
        return datetime.fromisoformat(st["progress_at"]), st.get("progress_what", "")
    ev = [(it[k], f"{it['id']} {k}") for it in st["queue"] for k in ("added", "started", "ended", "reviewed") if isinstance(it.get(k), str)]
    ev += [(t["done"], f"TODO {n} done") for n, t in enumerate(st.get("todo") or [], 1) if isinstance(t.get("done"), str)]
    if not ev:
        return None, ""
    t, what = max(ev, key=lambda e: datetime.fromisoformat(e[0]))
    return datetime.fromisoformat(t), what


def window_text(q: dict) -> str:
    """'2240 credits left, resets 19:33 (in 1 h 28 min)': the 5-hour window the credits belong to."""
    if q.get("left") is None or not q.get("reset_at"):
        return "credits unread"
    mins = max(0, int((q["reset_at"] - now()).total_seconds() // 60))
    return f"{q['left']} credits left, resets {q['reset_at']:%H:%M} (in {mins // 60} h {mins % 60:02d} min)"


def backlog_open(st: dict) -> list[tuple[int, dict]]:
    """Standing goals the user already asked for, not yet queued: they take spare credits when nothing else does."""
    return [(n, b) for n, b in enumerate(st.get("backlog") or [], 1) if not b.get("done")]


def todo_open(st: dict, who: str) -> list[tuple[int, dict]]:
    return [(n, t) for n, t in enumerate(st.get("todo") or [], 1) if not t.get("done") and t.get("who", "claude") == who]


def todo_ready(st: dict) -> list[tuple[int, dict]]:
    """[claude] items Claude can do now: all but those `after` a wave that is still queued or running."""
    pending = {it["id"] for it in st["queue"] if it["status"] in ("queued", "started")}
    return [(n, t) for n, t in todo_open(st, "claude") if t.get("after") not in pending and not t.get("started")]


def questions_open(st: dict, unasked_only: bool) -> list[tuple[int, dict]]:
    return [(n, t) for n, t in todo_open(st, "user") if t.get("kind") == "question" and not (unasked_only and t.get("asked"))]


def ask_payload(items: list[tuple[int, dict]]) -> dict:
    """AskUserQuestion's input for these questions (at most 4 per call): the recommended option first, marked."""
    qs = []
    for n, t in items[:4]:
        opts = []
        for i, o in enumerate(t["options"]):
            label = o["label"]
            if i == 0 and not t.get("multi") and "(Recommended)" not in label:
                label += " (Recommended)"
            opts.append({"label": label, "description": o["description"]})
        qs.append({"question": t["what"], "header": t["header"], "multiSelect": bool(t.get("multi")), "options": opts})
    return {"questions": qs, "todo": [n for n, _ in items[:4]]}


def refresh(st: dict) -> None:
    """Started waves that ended: done, waiting for review."""
    for it in st["queue"]:
        if it["status"] == "started" and (ROOT / ".cache" / f"wave_{it['id']}.done").is_file():
            it.update({"status": "done", "ended": now().isoformat(timespec="seconds"), "reviewed": False})
            progress(st, f"{it['id']} ended")
            subprocess.run(["schtasks", "/delete", "/tn", f"facecard-wave-{it['id']}", "/f"], capture_output=True, text=True)


def decide(st: dict, act: bool) -> str:
    """The waves (start the next queued one when it can) and Claude's part (waves to review, [claude] to-dos ready), in one line.
    Claude's part comes first and never reads as idle: 'work', or 'STALLED' once nothing has advanced for STALL_MIN minutes."""
    refresh(st)
    if HOLD.exists():           # the user's stop: no wave starts, no to-do or backlog item is handed out, until the file is removed
        return f"hold: generation is stopped by the user ({HOLD.read_text(encoding='utf-8', errors='replace').strip()[:160]})"
    queued = [it for it in st["queue"] if it["status"] == "queued"]
    running = waves_running()
    review = [it["id"] for it in st["queue"] if it["status"] == "done" and not it.get("reviewed")]
    ready = todo_ready(st)
    to_ask = questions_open(st, unasked_only=True)
    work = []
    if review:
        work.append(f"{len(review)} wave(s) to review ({', '.join(review)})")
    if ready:
        work.append(f"{len(ready)} [claude] to-do(s) ready (TODO {', '.join(str(n) for n, _ in ready)})")
    if to_ask:
        work.append(f"{len(to_ask)} question(s) to ask (TODO {', '.join(str(n) for n, _ in to_ask)})")
    started = False
    if running:
        waves = f"busy: wave(s) running ({', '.join(running)})"
        for w, minutes, line in memory_blocked(running):
            work.append(f"FREE MEMORY: wave {w} has waited {minutes} min on the memory gate ({line})")
    elif not queued:
        waves = "no wave queued"
    elif night_claim():
        waves = "waiting: the overnight local render holds the machine"
    else:
        it = queued[0]
        q = credit_window()
        need = int(it.get("credits") or 0)
        if q["left"] is None or q["reset_at"] is None:
            waves = "waiting: the credit window could not be read (sign-in?)"
        elif q["left"] < need:
            waves = f"waiting: {it['id']} needs {need} credits, {q['left']} left, the window resets {q['reset_at']:%H:%M}"
        elif not act:
            waves = f"ready: {it['id']} can start ({q['left']} credits left, needs {need})"
        else:
            msg = start_wave(it)
            it.update({"status": "started", "started": now().isoformat(timespec="seconds")})
            progress(st, f"{it['id']} started")
            started = True
            waves = f"started: {it['id']} ({q['left']} credits left, needs {need}); {msg[:120]}"
    waiting = [n for n, t in questions_open(st, unasked_only=False) if t.get("asked")]
    asked = f" | {len(waiting)} question(s) waiting for his answer in Claude Code (TODO {', '.join(map(str, waiting))})" if waiting else ""
    q = credit_window()
    credits = window_text(q)
    # Spare credits (the user, 2026-10-13: "since so much credit is left, why are you not processing anything?"): what the window still
    # holds after the queued waves, with fewer than 2 waves running, goes to the backlog's first goal; unused credits are lost at the reset.
    reserved = sum(int(it.get("credits") or 0) for it in queued)
    spare = q.get("left") is not None and q["left"] - reserved >= SPARE_MIN
    bl = backlog_open(st)
    free = [(n, b) for n, b in bl if not b.get("started")]          # an item an agent is already preparing is not handed out again
    preparing = len(bl) - len(free)                                # at most 2 preparations at once: each freeze loads the face models (RAM)
    if free and spare and not queued and len(running) < 2 and preparing < 2 and not any(w.startswith("spare credits") for w in work):
        n, b = free[0]
        work.append(f"spare credits ({credits}): take backlog {n}: {b['what'][:100]}")
    # Claimed items (start-todo / backlog start) that nobody has finished: a claim hides them from the ping, so it must not read as idle, and a claim
    # that sees no progress for STALL_MIN minutes is work again (2026-10-14: three claims in a row answered 'idle: no [claude] to-do').
    claimed = [f"TODO {n}" for n, t in todo_open(st, "claude") if t.get("started") and not t.get("after")]
    claimed += [f"backlog {n}" for n, b in bl if b.get("started")]
    if not work and claimed:
        t, what = last_progress(st)
        quiet_min = (now() - t).total_seconds() / 60 if t else 0.0
        if quiet_min >= STALL_MIN:
            return (f"STALLED (no progress for {quiet_min / 60:.1f} h, last {t:%H:%M} {what}): CLAIMED WORK has not finished: "
                    f"{', '.join(claimed)}; {waves}; {credits}{asked}")
        return f"busy: claimed work in progress ({', '.join(claimed)}); {waves} | {credits}{asked}"
    if not work:
        base = "idle: nothing queued, nothing to review, no [claude] to-do" if waves == "no wave queued" else waves
        if bl and not spare:
            base += f" | backlog: {len(bl)} goal(s) wait for credits"
        elif not bl and spare:
            base += " | credits spare but the backlog is empty (file the next goals with `backlog add`)"
        return f"{base} | {credits}{asked}"
    t, what = last_progress(st)
    quiet_min = (now() - t).total_seconds() / 60 if t else 0.0
    head = "work"
    if quiet_min >= STALL_MIN and not started:
        head = f"STALLED (no progress for {quiet_min / 60:.1f} h, last {t:%H:%M} {what})"
    return f"{head}: {'; '.join(work)}; {waves}; {credits}{asked}"


def cmd_status(st: dict) -> int:
    decision = decide(st, act=False)
    save(st)
    q = credit_window(max_age_min=60)
    print(f"decision: {decision}")
    if q.get("left") is not None and q.get("reset_at") is not None:
        line = f"credits: 5-hour window: {window_text(q)} (read {q['read_at']:%H:%M})"
        try:
            w = (json.loads(QUOTA.read_text(encoding="utf-8")).get("weekly") or {})
            line += f"; weekly: {w['remaining_credits']} left, resets {datetime.fromisoformat(w['reset_at']):%a %H:%M}"
        except (OSError, ValueError, KeyError, TypeError):
            pass
        print(line)
    t, what = last_progress(st)
    if t:
        print(f"last progress: {t:%Y-%m-%d %H:%M} {what}")
    for n, b in backlog_open(st):
        print(f"  BACKLOG {n} (~{b.get('credits', '?')} credits){' [being prepared since ' + b['started'][11:16] + ']' if b.get('started') else ''}: {b['what']}")
    for it in st["queue"]:
        if it["status"] != "done" or not it.get("reviewed"):
            print(f"  {it['status'].upper():8s} {it['id']}: {it.get('note') or ''} (needs {it.get('credits')}){'  TO REVIEW' if it['status'] == 'done' and not it.get('reviewed') else ''}")
    ready = {n for n, _ in todo_ready(st)}
    for n, t in todo_open(st, "claude"):
        state = "READY" if n in ready else ("in progress" if t.get("started") and not t.get("after") else "after " + str(t.get("after")))
        print(f"  TODO {n} [claude] {state}: {t['what']}")
    users = todo_open(st, "user")
    for n, t in users:
        if t.get("kind") == "question":
            state = f"asked {t['asked'][11:16]}" if t.get("asked") else "TO ASK"
            dflt = f", default TODO {t['default']}" if t.get("default") else ""
            opts = " | ".join(o["label"] + ("*" if i == 0 and not t.get("multi") else "") for i, o in enumerate(t["options"]))
            print(f"  TODO {n} [user] QUESTION ({state}{dflt}): {t['what']}  [{opts}]")
        else:
            print(f"  TODO {n} [user] {t['what']}")
    if users:
        print("  ([user] items are the user's approvals and own choices; none of them holds up a [claude] item: a question's"
              " recommended option (*) is started at once, then the session asks it with AskUserQuestion; background agents and"
              " waves keep working while it waits)")
    return 0


RULES = ("Rules: no unit tests (real runs only); never stop a running wave abruptly; never kill PIDs by hand; waves only through "
         "tools\\wave.py and `autocontinue.py add`; long preparations go to background agents (Agent tool, run_in_background), and the "
         "to-do or backlog item you hand to one is claimed first (`start-todo <n>` / `backlog start <n>`) so no ping hands it out twice; "
         "a question never waits: start its recommended step, file it with `autocontinue.py ask`, ask it with AskUserQuestion yourself.")


def work_order(st: dict, decision: str) -> str:
    """What the periodic ping hands the Claude session when there is something to do: the tasks themselves, not a report."""
    out = [f"WORK ORDER {now():%Y-%m-%d %H:%M}: {decision}", "Do every task below now, in order, before you reply."]
    k = 0
    for it in st["queue"]:
        if it["status"] == "done" and not it.get("reviewed"):
            k += 1
            out.append(f"{k}. REVIEW wave {it['id']} ({it.get('note') or ''}): check each of its pictures against BEST_CHECKLIST.md with "
                       f"tools\\best_check.py and evidence, record every failure with its cause in FAILURE_LOG.md, export what passes, run "
                       f"`autocontinue.py reviewed {it['id']}`, and tell the user in one short message with links to the pictures.")
    for n, t in todo_ready(st):
        k += 1
        out.append(f"{k}. TODO {n}: {t['what']} Then `autocontinue.py done-todo {n} --note \"...\"`; file follow-ups that wait for a wave "
                   f"with `todo \"...\" --after <tag>`.")
    asks = questions_open(st, unasked_only=True)
    if asks:
        k += 1
        out.append(f"{k}. ASK: run `autocontinue.py questions --mark-asked` and ask exactly that JSON (without its \"todo\" key) with "
                   f"AskUserQuestion, as the LAST call of the turn after every default step is started; record each answer with "
                   f"`autocontinue.py answer <n> \"<label>\" [--note \"<his notes>\"]` and do any redirect it files.")
    if "CLAIMED WORK" in decision:
        k += 1
        out.append(f"{k}. CLAIMED WORK: items claimed with start-todo / backlog start have shown no progress for an hour (named in the line above). "
                   "For each: if a background agent holds it, read its result or state (SendMessage to it, or its output file only by tail of the last lines), "
                   "finish what it left, or release it: set its `started` off (scratchpad unclaim.py <n> under the state lock) and do the work yourself now; "
                   "then `autocontinue.py done-todo <n>` / `backlog done <n>`. A claim is never a reason to answer 'no change'.")
    if "FREE MEMORY" in decision:
        k += 1
        out.append(f"{k}. FREE MEMORY: a running wave is stuck on the memory gate (the wave's log, .cache\\wave_<tag>.log, shows the numbers). "
                   "The gate stays as it is (a lower one starved the machine and the job bots before). Close only what the user allowed as idle "
                   "(2026-10-10/14: idle Claude Code tabs, anything idle for a while): a tab counts only when its sessions\\<pid>.json says idle "
                   "for over 1 h, its transcript shows no timer or background job, and it is not this tab; check an app's children and CPU before "
                   "calling it idle (opencode runs research sessions); never the job bots' browsers, the user's Edge or VS Code itself. Then "
                   "re-read the free memory; if the wave still waits after a few minutes, tell the user in chat which choice is left (restart "
                   "Pylance, pause the appliers) instead of waiting.")
    if "spare credits" in decision:
        n, b = [(n, b) for n, b in backlog_open(st) if not b.get("started")][0]
        k += 1
        out.append(f"{k}. SPARE CREDITS: backlog {n}: {b['what']} First `autocontinue.py backlog start {n}` (so no one else takes it), "
                   f"then prepare it (inventory, recipe, dry run that equals the lock), queue it with `autocontinue.py add <spec>`, then "
                   f"`autocontinue.py backlog done {n} --note \"queued as <tag>\"`; if it needs the user's own choice, file a question "
                   f"with a default instead of waiting.")
    out.append(RULES)
    return "\n".join(out)


def cmd_ping(st: dict) -> int:
    """The cheap periodic entry for the Claude session: NOOP when nothing needs doing, the work order when something does."""
    decision = decide(st, act=False)
    save(st)
    if decision.split(":", 1)[0].split(" ", 1)[0] in ("idle", "busy", "waiting", "ready", "hold"):
        print(f"NOOP: {decision}")
    else:
        print(work_order(st, decision))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("ping")
    sub.add_parser("tick")
    a_bl = sub.add_parser("backlog")
    bl_sub = a_bl.add_subparsers(dest="bcmd", required=True)
    b_add = bl_sub.add_parser("add")
    b_add.add_argument("what")
    b_add.add_argument("--credits", type=int, default=None, help="rough credits the goal needs")
    b_start = bl_sub.add_parser("start")
    b_start.add_argument("n", type=int)
    b_done = bl_sub.add_parser("done")
    b_done.add_argument("n", type=int)
    b_done.add_argument("--note", default=None)
    bl_sub.add_parser("list")
    a_add = sub.add_parser("add")
    a_add.add_argument("spec")
    a_add.add_argument("--credits", type=int, default=None)
    a_add.add_argument("--parallel", type=int, default=2)
    a_add.add_argument("--stagger", type=int, default=240)
    a_add.add_argument("--note", default="")
    a_todo = sub.add_parser("todo")
    a_todo.add_argument("what")
    a_todo.add_argument("--who", choices=["claude", "user"], default="claude")
    a_todo.add_argument("--after", default=None, help="a queued or running wave's tag this [claude] item waits for")
    a_todo.add_argument("--default", default=None, help="with --who user: the recommended step, filed as a [claude] item done at once")
    a_st = sub.add_parser("start-todo")
    a_st.add_argument("n", type=int)
    a_dt = sub.add_parser("done-todo")
    a_dt.add_argument("n", type=int)
    a_dt.add_argument("--note", default=None)
    a_et = sub.add_parser("edit-todo")
    a_et.add_argument("n", type=int)
    a_et.add_argument("--who", choices=["claude", "user"], default=None)
    a_et.add_argument("--what", default=None)
    a_et.add_argument("--after", default=None, help="a wave tag, or '' to clear")
    a_ask = sub.add_parser("ask")
    a_ask.add_argument("question")
    a_ask.add_argument("--header", required=True, help="the chip AskUserQuestion shows, at most 12 characters")
    a_ask.add_argument("--option", action="append", required=True, help="'label|what it means', 2-4 times; the recommended one first")
    a_ask.add_argument("--default", default=None, help="the recommended option's step: filed as a [claude] item, done at once")
    a_ask.add_argument("--default-todo", type=int, default=None, help="an existing [claude] item that is the recommended option's step")
    a_ask.add_argument("--multi", action="store_true", help="several options may be chosen (an approval list); no option is recommended")
    a_qs = sub.add_parser("questions")
    a_qs.add_argument("--mark-asked", action="store_true", help="mark the printed questions asked (a background agent asks them now)")
    a_qs.add_argument("--all", action="store_true", help="every open question, asked or not")
    a_ans = sub.add_parser("answer")
    a_ans.add_argument("n", type=int)
    a_ans.add_argument("choice", help="the label the user chose (several: joined with ' + ')")
    a_ans.add_argument("--note", default=None, help="the user's notes or 'Other' text, verbatim")
    a_rev = sub.add_parser("reviewed")
    a_rev.add_argument("tag")
    a_rm = sub.add_parser("remove")
    a_rm.add_argument("tag")
    sub.add_parser("install")
    a = ap.parse_args()
    st = load()
    st.setdefault("queue", [])
    st.setdefault("todo", [])
    st.setdefault("backlog", [])
    if a.cmd == "status":
        return cmd_status(st)
    if a.cmd == "ping":
        return cmd_ping(st)
    if a.cmd == "backlog":
        if a.bcmd == "add":
            st["backlog"].append({"what": a.what, "credits": a.credits, "added": now().isoformat(timespec="seconds"), "done": False})
            save(st)
            print(f"backlog {len(st['backlog'])}: {a.what}")
        elif a.bcmd == "start":
            st["backlog"][a.n - 1]["started"] = now().isoformat(timespec="seconds")
            progress(st, f"backlog {a.n} started")
            save(st)
            print(f"backlog {a.n} claimed: no ping hands it out again until it is done")
        elif a.bcmd == "done":
            b = st["backlog"][a.n - 1]
            b["done"] = now().isoformat(timespec="seconds")
            if a.note:
                b["note"] = a.note
            progress(st, f"backlog {a.n} taken")
            save(st)
        else:
            for n, b in backlog_open(st):
                print(f"{n}: (~{b.get('credits', '?')}) {b['what']}")
        return 0
    if a.cmd == "tick":
        d = decide(st, act=True)
        if d.startswith("STALLED") and not st.get("stall_alerted"):
            st["stall_alerted"] = now().isoformat(timespec="seconds")
            d += f" | {alert('Facecard: work stalled', d[len('STALLED '):])}"
        save(st)
        log(d)
        print(d)
        return 0
    if a.cmd == "add":
        spec = Path(a.spec)
        rel = str((spec if spec.is_absolute() else ROOT / spec).resolve().relative_to(ROOT)).replace("\\", "/")
        tag = spec_tag(ROOT / rel)
        if any(it["id"] == tag and it["status"] in ("queued", "started") for it in st["queue"]):
            print(f"{tag} is already queued or running")
            return 1
        st["queue"].append({"id": tag, "spec": rel, "credits": a.credits or spec_credits(ROOT / rel), "parallel": a.parallel,
                            "stagger": a.stagger, "note": a.note, "status": "queued", "added": now().isoformat(timespec="seconds")})
        progress(st, f"{tag} queued")
        save(st)
        print(f"queued {tag} (needs {st['queue'][-1]['credits']} credits)")
        return 0
    if a.cmd == "todo":
        if a.after and a.who != "claude":
            print("--after is for [claude] items")
            return 2
        item = {"what": a.what, "who": a.who, "added": now().isoformat(timespec="seconds"), "done": False}
        if a.after:
            item["after"] = a.after
        st["todo"].append(item)
        n = len(st["todo"])
        print(f"todo {n} [{a.who}]: {a.what}")
        if a.who == "user" and a.default:
            st["todo"].append({"what": a.default, "who": "claude", "added": now().isoformat(timespec="seconds"), "done": False,
                               "default_for": n})
            item["default"] = len(st["todo"])
            print(f"todo {len(st['todo'])} [claude] (the default for {n}, done now; the user can redirect it): {a.default}")
        elif a.who == "user":
            print("  (a [user] item is the user's approval or own choice; a question with a sensible answer takes --default)")
        save(st)
        return 0
    if a.cmd == "start-todo":
        st["todo"][a.n - 1]["started"] = now().isoformat(timespec="seconds")
        progress(st, f"TODO {a.n} started")
        save(st)
        print(f"todo {a.n} claimed: a ping does not hand it out again until it is done")
        return 0
    if a.cmd == "done-todo":
        t = st["todo"][a.n - 1]
        t["done"] = now().isoformat(timespec="seconds")
        if a.note:
            t["note"] = a.note
        progress(st, f"TODO {a.n} done")
        save(st)
        return 0
    if a.cmd == "edit-todo":
        t = st["todo"][a.n - 1]
        if a.who:
            t["who"] = a.who
        if a.what:
            t["what"] = a.what
        if a.after is not None:
            if a.after:
                t["after"] = a.after
            else:
                t.pop("after", None)
        save(st)
        print(f"todo {a.n} [{t.get('who', 'claude')}]{' after ' + t['after'] if t.get('after') else ''}: {t['what']}")
        return 0
    if a.cmd == "ask":
        opts = []
        for o in a.option:
            label, _, desc = o.partition("|")
            opts.append({"label": label.strip(), "description": desc.strip() or label.strip()})
        if len(a.header) > 12 or not 2 <= len(opts) <= 4:
            print("AskUserQuestion takes a header of at most 12 characters and 2-4 options")
            return 2
        if a.default and a.default_todo:
            print("--default or --default-todo, not both")
            return 2
        item = {"what": a.question, "who": "user", "kind": "question", "header": a.header, "options": opts, "multi": a.multi,
                "asked": False, "answer": None, "added": now().isoformat(timespec="seconds"), "done": False}
        st["todo"].append(item)
        n = len(st["todo"])
        if a.default:
            st["todo"].append({"what": a.default, "who": "claude", "added": now().isoformat(timespec="seconds"), "done": False,
                               "default_for": n})
            item["default"] = len(st["todo"])
        elif a.default_todo:
            item["default"] = a.default_todo
            st["todo"][a.default_todo - 1]["default_for"] = n
        save(st)
        print(f"question {n} [{a.header}]: {a.question}")
        if item.get("default"):
            print(f"  default (done now, the user can redirect it): TODO {item['default']}: {st['todo'][item['default'] - 1]['what']}")
        elif not a.multi:
            print("  no default step: nothing may wait on this question")
        return 0
    if a.cmd == "questions":
        items = questions_open(st, unasked_only=not a.all)
        payload = ask_payload(items)
        if a.mark_asked:
            for n in payload["todo"]:
                st["todo"][n - 1]["asked"] = now().isoformat(timespec="seconds")
            save(st)
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if a.cmd == "answer":
        t = st["todo"][a.n - 1]
        if t.get("kind") != "question":
            print(f"todo {a.n} is not a question")
            return 2
        rec = t["options"][0]["label"]
        same = not t.get("multi") and a.choice.strip().lower().startswith(rec.lower())
        t.update({"answer": a.choice, "done": now().isoformat(timespec="seconds")})
        if a.note:
            t["note"] = a.note
        progress(st, f"question {a.n} answered")
        print(f"question {a.n} answered: {a.choice}" + (f" (notes: {a.note})" if a.note else ""))
        d = t.get("default")
        if d and same:
            print(f"  the user chose the recommended option: TODO {d} stands")
        elif d or (not t.get("multi") and not same):
            if d and not st["todo"][d - 1].get("done"):
                st["todo"][d - 1].update({"done": now().isoformat(timespec="seconds"),
                                          "note": f"superseded: the user chose '{a.choice}' on question {a.n}"})
            what = (f"redirect after question {a.n} ('{t['what'][:120]}'): the user chose '{a.choice}'"
                    + (f" (notes: {a.note})" if a.note else "") + f", not the recommended '{rec}'"
                    + (f"; undo or replace what TODO {d} queued or made" if d else "") + "; do what he chose")
            st["todo"].append({"what": what, "who": "claude", "added": now().isoformat(timespec="seconds"), "done": False,
                               "redirect_for": a.n})
            print(f"  todo {len(st['todo'])} [claude] READY: {what}")
        save(st)
        return 0
    if a.cmd in ("reviewed", "remove"):
        hit = [it for it in st["queue"] if it["id"] == a.tag]
        if not hit:
            print(f"no queue item {a.tag}")
            return 1
        if a.cmd == "reviewed":
            hit[-1]["reviewed"] = now().isoformat(timespec="seconds")
            progress(st, f"{a.tag} reviewed")
        else:
            st["queue"] = [it for it in st["queue"] if it["id"] != a.tag or it["status"] == "started"]
        save(st)
        return 0
    if a.cmd == "install":
        xml = task_xml("Facecard auto-continue (tools/autocontinue.py tick, every 15 minutes, hidden): starts the next queued Gemini wave "
                       "when the credit window holds what it needs, no wave runs and the overnight render holds no claim; tells the user "
                       "with a toast when Claude's work has stalled.",
                       str(RUNHIDDEN), f'"{PY}" "{ROOT / "tools" / "autocontinue.py"}" tick', now() + timedelta(minutes=2), "PT15M", "PT10M")
        print(register(TASK, xml, run_now=False))
        return 0
    return 2


if __name__ == "__main__":
    with state_lock():
        code = main()
    sys.exit(code)
