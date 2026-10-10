"""Making room for the overnight local picture, and putting everything back (the user, 2026-10-10).

The user, 2026-10-10: "Apart from VS Code, which has multiple tabs of Claude Code running, everything else can be closed. Even inside VS
Code, ideal Claude Code tabs can be closed as well, and only active, running ones can be kept to make up space for our local Qwen run."
His answers on what comes back: "only wispr flow, opencode, and edge that too reopen only if they were open at night and got closed for
ram"; they reopen when he is back (his first keyboard or mouse use after 06:00); the job bots restart after the picture.

tools/overnight.py drives it. By hand:
    .venv\\Scripts\\python.exe tools\\overnight.py room-plan      # what would close, stay, or is unknown; changes nothing
    schtasks /Run /TN facecard-local-restore                  # puts back a room that a crashed night left behind

How it stays safe (each rule was learned on this machine; AGENTS.md "Making room"):
- A process is (pid, creation time), never a bare pid: pids are reused, and a reused pid once made the night's lock look live.
- Never `taskkill /T` (it follows stale parent pids: memory-guard's runhidden has a dead parent whose pid Edge could get) and never `/IM`
  (the bots share msedge.exe and python.exe with everything else). A tree is its root plus the children psutil saw (a "child" older than
  its parent is a stale link and is dropped); the root dies first, so it cannot start new children.
- A Claude Code tab is a ~/.claude/sessions/<pid>.json whose pid runs the extension's own claude.exe with the same start time (Claude
  Desktop is also named claude.exe). An idle one ends with exit code 0xFFFFFFFF, as Stop-Process does: the extension then shows no error
  line, and typing in the tab resumes it. The sessions\\*.key files are secrets and are never read.
- A bot stops only between applications (a Naukri drawer closed mid-questionnaire is submitted incomplete: verdict 406) and comes back
  only through its own task, the supervised chain; two supervisors started together both quit, so a restart checks first.
- Apps reopen through Explorer, so they inherit neither this process's environment (a Claude Code shell sets ELECTRON_RUN_AS_NODE=1,
  which breaks Electron apps) nor the night task's job.
- Everything it changes is written to room.json first and updated item by item, so a crash halfway can always be undone
  (restore_if_stale, run by the facecard-local-restore task every 30 min and at sign-in).
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths  # noqa: E402

SCHEMA = "facecard.room/1"
GITHUB = paths.REPO.parent                 # the folder that holds the user's repos; the job bots live beside this one
CLAUDE_HOME = Path.home() / ".claude"
STARTUP = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
CREATE_NO_WINDOW = 0x08000000
EXIT_QUIET = 0xFFFFFFFF                    # Stop-Process's exit code: the Claude Code extension shows no error line for it
GB = 1024 ** 3
AWAY_S, AWAY_SCREEN_ON_S = 10 * 60, 45 * 60   # no keyboard or mouse for 10 min; 45 if something (a video) keeps the screen on
BACK_S = 120                               # input this recent while the room is being made: he is back
BOT_BUDGET_S = 90 * 60                     # one shared wait for the bots to reach a safe moment
RECENT_S = 3600                            # a tab that did anything in the last hour stays
RETURN_HOUR, RETURN_UNTIL_HOUR = 6, 18     # "when I'm back": his first input after 06:00 (the night waits for it until 18:00)

NAUKRI = GITHUB / "Naukri-autoapply-bot-for-claude"
BOTS = {   # id -> its task (the supervised chain), its supervisor script, how to tell it is between applications, its browser profiles
    "naukri1": {"task": "NaukriKeepalive", "script": "naukri_keepalive.ps1", "profile": None, "log": NAUKRI / "naukri_bot.log",
                "browsers": ("browser_profile",)},
    "naukri2": {"task": "NaukriKeepalive2", "script": "naukri_keepalive.ps1", "profile": "naukri2",
                "log": NAUKRI / "profiles" / "naukri2" / "naukri_bot.log", "browsers": ("profiles\\naukri2\\edge_profile",)},
    "instahyre": {"task": "InstahyreApply", "script": "instahyre_apply_keepalive.ps1",
                  "state": GITHUB / "job-tracker" / "logs" / "instahyre_apply.state.json", "browsers": ("apply-instahyre",)},
    "linkedin": {"task": "LinkedInKeepalive", "script": "linkedin_keepalive.ps1", "browsers": ("linkedin-1",)},
}
OPENCODE_TASKS = ("opencode-shared-server", "opencode-server-guard")      # :4599, and the guard that starts :4600 when nothing listens
OPENCODE_PORTS = (4599, 4600)
MCP_HELPERS = ("davinci-resolve-mcp", "kino.exe")      # video-editing MCP servers every Claude Code tab starts; none uses them (10-09)
NAUKRI_LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d{3} - [A-Z]+ - (.*)$")
NAUKRI_WAKE = re.compile(r"Next search cycle starts at:\s*(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")


class UserBack(Exception):
    """He used the keyboard or mouse while the room was being made: stop, put everything back, wait for him to leave again."""


def home() -> Path:
    d = paths.room_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def manifest_path() -> Path:
    return home() / "room.json"


def edge_shortcut() -> Path:
    return home() / "Edge - restore last session.lnk"


def ascii_(s: str) -> str:
    return (s or "").encode("ascii", "replace").decode()


def save(path: Path, data: dict, tries: int = 10) -> bool:
    """Atomic write that retries when another process holds the file (Windows refuses to replace an open file)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    for i in range(tries):
        try:
            tmp.write_text(json.dumps(data, indent=1, ensure_ascii=True), encoding="utf-8")
            os.replace(tmp, path)
            return True
        except OSError:
            time.sleep(1 + i)
    return False


def load(path: Path | None = None) -> dict | None:
    try:
        return json.loads((path or manifest_path()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------------------------------------------------------------- Windows calls
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.GetProcessTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(wt.FILETIME)] * 4
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.GetTickCount.restype = wt.DWORD
PROCESS_TERMINATE, PROCESS_QUERY_LIMITED_INFORMATION, STILL_ACTIVE = 0x0001, 0x1000, 259


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


u32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [WNDENUMPROC, wt.LPARAM]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextLengthW.argtypes = [wt.HWND]


def _ctime_h(h) -> int | None:
    c, e, kt, ut = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if not k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut)):
        return None
    return (c.dwHighDateTime << 32) | c.dwLowDateTime


def ctime_of(pid: int) -> int | None:
    """A running process's creation time (100-ns ticks since 1601, the value Claude Code stores as procStart), or None."""
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return None
    try:
        code = wt.DWORD()
        if not k32.GetExitCodeProcess(h, ctypes.byref(code)) or code.value != STILL_ACTIVE:
            return None
        return _ctime_h(h)
    finally:
        k32.CloseHandle(h)


def alive(pid, ctime) -> bool:
    """True only while the same process runs: a pid with another creation time is another process."""
    try:
        return bool(pid) and ctime is not None and ctime_of(int(pid)) == int(ctime)
    except (TypeError, ValueError):
        return False


def me() -> dict:
    return {"pid": os.getpid(), "ctime": ctime_of(os.getpid())}


def ft_to_epoch(ft: int) -> float:
    return (int(ft) - 116444736000000000) / 1e7


def terminate_exact(pid: int, ctime: int, code: int = 1) -> bool:
    """End one process, only while it is still the one we saw. True when it is gone."""
    h = k32.OpenProcess(PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return ctime_of(pid) != ctime
    try:
        if _ctime_h(h) != ctime:
            return True
        now = wt.DWORD()
        if k32.GetExitCodeProcess(h, ctypes.byref(now)) and now.value != STILL_ACTIVE:
            return True
        return bool(k32.TerminateProcess(h, code))
    finally:
        k32.CloseHandle(h)


def memory() -> dict:
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    k32.GlobalMemoryStatusEx(ctypes.byref(m))
    return {"avail_gb": round(m.ullAvailPhys / GB, 2), "commit_headroom_gb": round(m.ullAvailPageFile / GB, 2)}


def idle_s() -> float:
    """Seconds since his last keyboard or mouse input in this session."""
    li = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    if not u32.GetLastInputInfo(ctypes.byref(li)):
        return 0.0
    return ((k32.GetTickCount() - li.dwTime) & 0xFFFFFFFF) / 1000.0


def last_input() -> datetime:
    return datetime.now() - timedelta(seconds=idle_s())


def screen_kept_on() -> bool:
    """Something (a playing video) asks Windows to keep the display on: ES_DISPLAY_REQUIRED in the system execution state."""
    try:
        state = wt.ULONG()
        rc = ctypes.WinDLL("powrprof").CallNtPowerInformation(16, None, 0, ctypes.byref(state), ctypes.sizeof(state))
        return rc == 0 and bool(state.value & 0x2)
    except OSError:
        return True


def locked() -> bool:
    import psutil
    return any((p.info.get("name") or "").lower() == "logonui.exe" for p in psutil.process_iter(["name"]))


def away() -> tuple[bool, str]:
    s = idle_s()
    if s >= AWAY_SCREEN_ON_S:
        return True, f"no keyboard or mouse for {s / 60:.0f} min"
    if s >= AWAY_S and (locked() or not screen_kept_on()):
        return True, f"no keyboard or mouse for {s / 60:.0f} min" + (", screen locked" if locked() else "")
    return False, f"last input {s / 60:.1f} min ago" + (" (screen kept on: waiting for 45 min)" if s >= AWAY_S else "")


def visible_windows(pids: set[int]) -> int:
    n = 0

    @WNDENUMPROC
    def cb(h, _):
        nonlocal n
        pid = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u32.IsWindowVisible(h) and u32.GetWindowTextLengthW(h) > 0:
            n += 1
        return True

    u32.EnumWindows(cb, 0)
    return n


def _run(*argv: str, timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(list(argv), capture_output=True, text=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "timed out"


# ------------------------------------------------------------------------------------------------------------------- processes
def snapshot() -> dict[int, dict]:
    """Every process: pid, parent pid, creation time, name, exe, command line (None when Windows will not show it), memory."""
    import psutil
    snap = {}
    for p in psutil.process_iter():
        try:
            info = {"pid": p.pid, "ppid": p.ppid(), "name": p.name()}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        info["ctime"] = ctime_of(p.pid)
        for key, fn in (("exe", p.exe), ("cmd", p.cmdline)):
            try:
                v = fn()
                info[key] = " ".join(v) if isinstance(v, list) else v
            except Exception:
                info[key] = None
        try:
            mi = p.memory_info()
            info["ws"], info["priv"] = int(mi.rss), int(getattr(mi, "private", 0))
        except Exception:
            info["ws"] = info["priv"] = 0
        snap[p.pid] = info
    return snap


def parent(p: dict, snap: dict) -> dict | None:
    """The real parent: a recorded parent created after its child is a stale link (Windows reuses pids)."""
    par = snap.get(p["ppid"])
    if not par or par["pid"] == p["pid"] or par["ctime"] is None or p["ctime"] is None or par["ctime"] > p["ctime"]:
        return None
    return par


def children(snap: dict) -> dict[int, list[int]]:
    kids: dict[int, list[int]] = {}
    for pid, p in snap.items():
        if parent(p, snap):
            kids.setdefault(p["ppid"], []).append(pid)
    return kids


def descendants(pid: int, kids: dict) -> list[int]:
    out, stack = [], [pid]
    while stack:
        for c in kids.get(stack.pop(), []):
            if c not in out:
                out.append(c)
                stack.append(c)
    return out


def ancestors(pid: int, snap: dict) -> list[int]:
    out, cur = [], snap.get(pid)
    while cur:
        par = parent(cur, snap)
        if not par or par["pid"] in out:
            break
        out.append(par["pid"])
        cur = par
    return out


def tree(root: dict, snap: dict, kids: dict) -> list[dict]:
    return [root] + [snap[c] for c in descendants(root["pid"], kids)]


def ref(p: dict) -> dict:
    return {"pid": p["pid"], "ctime": p["ctime"], "name": p["name"]}


def kill_tree(procs: list[dict], code: int = 1) -> dict:
    """The root (procs[0]) first so it cannot start new children, then the children as snapshotted; each by (pid, creation time)."""
    gone, left = [], []
    for i, p in enumerate(procs):
        if p.get("ctime") is None:
            continue
        (gone if terminate_exact(p["pid"], p["ctime"], code if i == 0 else 1) else left).append(f"{p['name']} {p['pid']}")
    time.sleep(1.5)
    left += [f"{p['name']} {p['pid']}" for p in procs if p.get("ctime") is not None and alive(p["pid"], p["ctime"])
             and f"{p['name']} {p['pid']}" not in left]
    return {"ended": [g for g in gone if g not in left], "left": left}


def roots(snap: dict, pred) -> list[dict]:
    """Matching processes whose parent does not match: the top of each matching tree."""
    out = []
    for p in snap.values():
        if pred(p):
            par = parent(p, snap)
            if not (par and pred(par)):
                out.append(p)
    return out


def lc(p: dict, key: str) -> str:
    return (p.get(key) or "").lower()


def sizes(procs: list[dict]) -> dict:
    return {"ws_gb": round(sum(p.get("ws", 0) for p in procs) / GB, 2), "priv_gb": round(sum(p.get("priv", 0) for p in procs) / GB, 2)}


# ----------------------------------------------------------------------------------------------------------------- the programs
def is_user_edge(p: dict, snap: dict) -> bool:
    """His own Edge: a browser process (no --type) without the bots' --user-data-dir or debugging port, not started by msedgedriver.
    A process whose command line Windows will not show is never taken for his Edge."""
    if lc(p, "name") != "msedge.exe" or not p.get("cmd"):
        return False
    c = lc(p, "cmd")
    if "--type=" in c or "--user-data-dir" in c or "--remote-debugging-port" in c:
        return False
    par = parent(p, snap)
    return not (par and lc(par, "name") in ("msedgedriver.exe", "msedge.exe"))


APPS = {   # id -> (top processes, reopened when he is back?)
    "herdr": (lambda p, s: lc(p, "name") == "herdr.exe", False),
    "pi": (lambda p, s: lc(p, "name") == "pi.exe", False),
    "opencode": (lambda p, s: lc(p, "name") == "opencode.exe", True),
    "claude-desktop": (lambda p, s: lc(p, "name") == "claude.exe" and "\\windowsapps\\claude_" in lc(p, "exe"), False),
    "teams": (lambda p, s: lc(p, "name") == "ms-teams.exe", False),
    "wispr": (lambda p, s: lc(p, "name") == "wispr flow.exe", True),
    "edge": (is_user_edge, True),
}
APP_NAMES = {"herdr": "herdr (with Pi in it)", "pi": "Pi outside herdr", "opencode": "opencode (servers 4599/4600)",
             "claude-desktop": "Claude Desktop", "teams": "Teams", "wispr": "Wispr Flow", "edge": "your Edge"}

KEEP = [   # (why, test): reported as kept; only the VS Code tree and the runner's own family are protected by rule (see plan())
    ("a Gemini picture run or wave", lambda p: "facecard.py" in lc(p, "cmd") or "wave.py" in lc(p, "cmd")),
    ("memory-guard", lambda p: "memory-guard" in lc(p, "cmd")),
    ("Google Drive (the G: second brain)", lambda p: lc(p, "name") == "googledrivefs.exe"),
    ("Blip (forcing it closed breaks it)", lambda p: "blip" in lc(p, "name")),
    ("OneDrive", lambda p: lc(p, "name") == "onedrive.exe"),
    ("QuickLook", lambda p: lc(p, "name") == "quicklook.exe"),
    ("Ungate proxy", lambda p: "ungate" in lc(p, "cmd")),
    ("Antigravity proxy", lambda p: "antigravity" in lc(p, "cmd")),
    ("claude-adhd", lambda p: "claude-adhd" in lc(p, "cmd")),
    ("popup hider", lambda p: "hide-opencode-popups" in lc(p, "cmd")),
    ("VS Code patch watcher", lambda p: "vscode-headless-patch" in lc(p, "cmd")),
    ("job dashboard", lambda p: "dashboard\\server.py" in lc(p, "cmd")),
    ("llama-router (paused by the night itself)", lambda p: "llama" in lc(p, "cmd") or lc(p, "name") == "llama-server.exe"),
    ("small utility", lambda p: lc(p, "name") in ("autohotkey64.exe", "autohotkey.exe", "autohotkeyux.exe", "snippingtool.exe")
     or "powertoys" in lc(p, "exe")),
]


# ------------------------------------------------------------------------------------------------------------------------- bots
def supervisors(bot: dict, snap: dict) -> list[dict]:
    out = []
    for p in snap.values():
        c = lc(p, "cmd")
        if lc(p, "name") not in ("powershell.exe", "pwsh.exe") or bot["script"] not in c or "-status" in c:
            continue
        if bot["script"] == "naukri_keepalive.ps1":
            m = re.search(r"-profile\s+(\S+)", c)
            prof = m.group(1) if m and m.group(1) not in ("default", "profile1") else None
            if prof != bot.get("profile"):
                continue
        out.append(p)
    return sorted(out, key=lambda p: p["ctime"] or 0)


def naukri_between(log: Path) -> tuple[bool, str]:
    """Between applications: the log's last line is the cooldown's 'Next search cycle starts at: <time>', at least 2 min away."""
    try:
        with open(log, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            tail = f.read().decode("utf-8", "replace").splitlines()
    except OSError as e:
        return False, f"log unreadable ({type(e).__name__})"
    for line in reversed(tail):
        m = NAUKRI_LINE.match(line.strip())
        if not m:
            continue
        w = NAUKRI_WAKE.search(m.group(2))
        if not w:
            return False, "working: " + ascii_(m.group(2))[:70]
        wake = datetime.strptime(w.group(1), "%Y-%m-%d %H:%M:%S")
        if wake - datetime.now() >= timedelta(minutes=2):
            return True, f"cooling down until {wake:%H:%M}"
        return False, f"its next search starts at {wake:%H:%M}"
    return False, "no log line"


def bot_state(bot_id: str, snap: dict, kids: dict) -> tuple[str, dict | None, str]:
    """('absent' | 'safe' | 'busy', its supervisor, why)."""
    bot = BOTS[bot_id]
    sup = supervisors(bot, snap)
    if not sup:
        return "absent", None, "no supervisor running"
    s = sup[0]
    busy = [snap[c] for c in descendants(s["pid"], kids) if lc(snap[c], "name") != "conhost.exe"]
    if not busy:
        return "safe", s, "supervisor resting, no bot running"
    if "log" in bot:
        ok, why = naukri_between(bot["log"])
        return ("safe" if ok else "busy"), s, why
    if "state" in bot:
        try:
            st = json.loads(Path(bot["state"]).read_text(encoding="utf-8-sig"))       # Windows PowerShell writes a BOM
        except (OSError, ValueError) as e:
            return "busy", s, f"state unreadable ({type(e).__name__})"
        return ("safe", s, "not in a cycle") if st.get("InCycle") is False else ("busy", s, "in a cycle")
    return "busy", s, "its bot is running: " + ", ".join(sorted({p["name"] for p in busy}))


def bot_browsers(bot: dict, snap: dict) -> list[dict]:
    return roots(snap, lambda p: lc(p, "name") in ("msedge.exe", "chrome.exe") and "--type=" not in lc(p, "cmd")
                 and any(m in lc(p, "cmd") for m in bot["browsers"]))


# ------------------------------------------------------------------------------------------------------------------------ tasks
def task_state(name: str) -> str | None:
    """schtasks' status ('Ready', 'Running', 'Disabled', ...), or None when there is no such task."""
    rc, out = _run("schtasks", "/Query", "/TN", name, "/FO", "CSV", "/NH")
    if rc != 0 or not out:
        return None
    return out.splitlines()[-1].split('","')[-1].strip('"')


def task_set(name: str, enabled: bool) -> bool:
    return _run("schtasks", "/Change", "/TN", name, "/ENABLE" if enabled else "/DISABLE")[0] == 0


def task_run(name: str) -> bool:
    return _run("schtasks", "/Run", "/TN", name)[0] == 0


# --------------------------------------------------------------------------------------------------------------- Claude Code tabs
def transcript_of(sid: str) -> Path | None:
    return next((CLAUDE_HOME / "projects").glob(f"*/{sid}.jsonl"), None)


def _ts(entry: dict) -> float | None:
    try:
        return datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).timestamp()
    except (KeyError, ValueError, AttributeError):
        return None


def transcript_facts(path: Path, since: float, now: float) -> dict:
    """Last user/assistant entry, and timers set since the process started: only assistant tool calls count (the tool names also appear
    in tool lists inside attachments). A ScheduleWakeup with stop:true cancels; a CronCreate counts for 7 days unless deleted."""
    facts = {"last": None, "timer": None}
    wake, crons = None, []
    with open(path, "rb") as f:
        for raw in f:
            if b'"ScheduleWakeup"' not in raw and b'"CronCreate"' not in raw and b'"CronDelete"' not in raw:
                continue
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get("type") != "assistant" or (_ts(e) or 0) < since:
                continue
            for b in (e.get("message") or {}).get("content") or []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                inp = b.get("input") or {}
                if b.get("name") == "ScheduleWakeup":
                    wake = None if inp.get("stop") else (_ts(e) or 0) + float(inp.get("delaySeconds") or 0)
                elif b.get("name") == "CronCreate":
                    crons.append(_ts(e) or 0)
                elif b.get("name") == "CronDelete":
                    crons = crons[:-1]
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 262144))
        for raw in reversed(f.read().splitlines()):
            try:
                e = json.loads(raw)
            except ValueError:
                continue
            if e.get("type") in ("user", "assistant") and _ts(e):
                facts["last"] = _ts(e)
                break
    if wake and wake > now:
        facts["timer"] = f"wake-up set for {datetime.fromtimestamp(wake):%H:%M}"
    elif any(now - c < 7 * 86400 for c in crons):
        facts["timer"] = "a cron job is set"
    return facts


def sessions(snap: dict, kids: dict, keep_ids=(), protected=frozenset()) -> list[dict]:
    """Every Claude Code session in ~/.claude/sessions with its verdict: 'active' (kept) with the reasons, or 'idle'."""
    now = time.time()
    out = []
    for f in sorted((CLAUDE_HOME / "sessions").glob("*.json")):          # never the *.key files: they hold secrets
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            pid, start = int(d["pid"]), int(d["procStart"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        p = snap.get(pid)
        if not p or p["ctime"] != start:
            continue                                                       # a stale file, or the pid now belongs to another process
        sid, reasons = d.get("sessionId") or "?", []
        vscode = d.get("entrypoint") == "claude-vscode" and "\\anthropic.claude-code-" in lc(p, "exe") \
            and lc(p, "exe").endswith("\\resources\\native-binary\\claude.exe")
        if not vscode:
            reasons.append(f"not a VS Code tab ({d.get('entrypoint')})")
        if sid in keep_ids or pid in protected:
            reasons.append("the tab watching the night")
        if d.get("status") in ("busy", "waiting"):
            reasons.append(f"status {d.get('status')}")
        mcp, running = [], []
        for c in kids.get(pid, []):
            q = snap[c]
            if lc(q, "name") == "conhost.exe":
                continue
            (mcp if any(h in lc(q, "cmd") or h == lc(q, "name") for h in MCP_HELPERS) else running).append(q)
        if running:
            reasons.append("running: " + ", ".join(f"{q['name']} {q['pid']}" for q in running[:3]))
        recent = [float(d.get("statusUpdatedAt") or 0) / 1000.0]
        tr = transcript_of(sid) if not reasons else None      # an active tab needs no transcript read (this one's runs to 100 MB)
        if tr:
            try:
                facts = transcript_facts(tr, ft_to_epoch(start), now)
                if facts["timer"]:
                    reasons.append(facts["timer"])
                recent.append(facts["last"] or 0)
                sub = tr.parent / sid / "subagents"
                recent += [x.stat().st_mtime for x in sub.glob("*.jsonl")] if sub.exists() else []
            except Exception as e:
                reasons.append(f"transcript unreadable ({type(e).__name__})")
        elif not reasons:
            reasons.append("transcript not found")
        ago = now - max(recent)
        if ago < RECENT_S and not reasons:
            reasons.append(f"active {ago / 60:.0f} min ago")
        tree_procs = [p] + [snap[c] for c in descendants(pid, kids)]
        out.append({"pid": pid, "ctime": start, "sid": sid, "name": ascii_(d.get("name") or ""), "host": d.get("entrypoint"),
                    "exe": p.get("exe"), "verdict": "active" if reasons else "idle", "reasons": reasons, "idle_min": round(ago / 60),
                    "mcp": [ref(q) for q in mcp], **sizes(tree_procs)})
    return out


def protected_pids(snap: dict, kids: dict) -> set[int]:
    """The process making room, its parents (a test run from a Claude Code tab sits under that tab) and its children."""
    mine = os.getpid()
    return set(ancestors(mine, snap)) | {mine} | set(descendants(mine, kids))


# ---------------------------------------------------------------------------------------------------------------------- the plan
def plan(keep_sessions=(), snap: dict | None = None) -> dict:
    """What making room would do right now, changing nothing (also the dry run)."""
    snap = snap or snapshot()
    kids = children(snap)
    mine = me()
    protected = protected_pids(snap, kids)
    vscode = set()
    for r in roots(snap, lambda p: lc(p, "name") == "code.exe"):
        vscode |= {r["pid"]} | set(descendants(r["pid"], kids))
    sess = sessions(snap, kids, keep_ids=set(keep_sessions), protected=protected)
    idle = {s["pid"] for s in sess if s["verdict"] == "idle"}
    closing: set[int] = set()
    items = []
    for bot_id, bot in BOTS.items():
        state, sup, why = bot_state(bot_id, snap, kids)
        procs = tree(sup, snap, kids) if sup else []
        items.append({"id": f"bot:{bot_id}", "kind": "bot", "group": "bots", "bot": bot_id, "task": bot["task"], "state": state, "why": why,
                      "supervisor": ref(sup) if sup else None, "task_was": task_state(bot["task"]), **sizes(procs)})
    for name in OPENCODE_TASKS:
        items.append({"id": f"task:{name}", "kind": "task", "group": "apps", "task": name, "task_was": task_state(name)})
    desktop_session = any("\\appdata\\roaming\\claude\\" in (s.get("exe") or "").lower() for s in sess)
    for app_id, (pred, reopen) in APPS.items():
        tops = [r for r in roots(snap, lambda p, pr=pred: pr(p, snap))
                if r["pid"] not in protected and r["pid"] not in vscode and r["pid"] not in closing]   # Pi inside herdr goes with herdr
        why = ""
        if app_id == "claude-desktop" and tops and desktop_session:
            tops, why = [], "kept: it hosts a Claude Code session"
        procs = [q for r in tops for q in tree(r, snap, kids)]
        closing |= {q["pid"] for q in procs}
        extra = {}
        if app_id == "edge":
            extra["windows"] = visible_windows({q["pid"] for q in procs})
            extra["exe"] = tops[0].get("exe") if tops else None
            reopen = reopen and extra["windows"] > 0          # "only if they were open": an Edge with no window was not open
        items.append({"id": f"app:{app_id}", "kind": "app", "group": "apps" if reopen else None, "app": app_id, "name": APP_NAMES[app_id],
                      "running": bool(tops), "reopen": bool(reopen and tops), "roots": [ref(r) for r in tops], "why": why,
                      **extra, **sizes(procs)})
    helpers = [r for r in roots(snap, lambda p: any(h in lc(p, "cmd") or h == lc(p, "name") for h in MCP_HELPERS))
               if r["pid"] not in protected and r["ppid"] not in idle]
    hprocs = [q for r in helpers for q in tree(r, snap, kids)]
    items.append({"id": "helpers", "kind": "helpers", "group": None, "name": "DaVinci/Kinocut MCP helpers", "roots": [ref(r) for r in helpers],
                  **sizes(hprocs)})
    for s in sess:
        items.append({"id": f"session:{s['sid']}", "kind": "session", "group": None, **s})
    # what stays: VS Code, the runner's family, the kept list; anything else above 50 MB is "unknown" (left running, named in the morning)
    kept: dict[str, list[dict]] = {}
    unknown = []
    bot_pids = set()
    for it in items:
        if it["kind"] == "bot" and it["supervisor"]:
            bot_pids |= {it["supervisor"]["pid"]} | set(descendants(it["supervisor"]["pid"], kids))
    for bot in BOTS.values():
        for r in bot_browsers(bot, snap):
            bot_pids |= {r["pid"]} | set(descendants(r["pid"], kids))
    covered = closing | bot_pids | {q["pid"] for q in hprocs} | protected
    for s in sess:
        covered |= {s["pid"]} | set(descendants(s["pid"], kids))
    for p in snap.values():
        if p["pid"] in covered:
            continue
        if p["pid"] in vscode:
            kept.setdefault("VS Code", []).append(p)
            continue
        why = next((w for w, test in KEEP if test(p)), None)
        if why:
            kept.setdefault(why, []).append(p)
        elif lc(p, "exe").startswith(("c:\\windows\\", "c:\\programdata\\microsoft\\windows defender\\")) or not p.get("exe") \
                or lc(p, "name") in ("memcompression", "registry", "system", "secure system"):
            kept.setdefault("Windows", []).append(p)
        elif p.get("ws", 0) >= 50 * 2 ** 20:
            unknown.append({**ref(p), "exe": p.get("exe"), **sizes([p])})
    counted = [it for it in items if it["kind"] in ("bot", "app", "helpers")] + [s for s in sess if s["verdict"] == "idle"]
    est_ws = sum(it.get("ws_gb", 0) for it in counted)
    est_priv = sum(it.get("priv_gb", 0) for it in counted)
    return {"schema": SCHEMA, "state": "planned", "planned": datetime.now().isoformat(timespec="seconds"), "runner": mine,
            "memory_before": memory(), "estimate": {"ws_gb": round(est_ws, 2), "priv_gb": round(est_priv, 2)}, "items": items,
            "kept": {k: {"count": len(v), **sizes(v)} for k, v in sorted(kept.items())}, "unknown": unknown}


def print_plan(m: dict) -> None:
    print(f"room plan {m['planned']}: free {m['memory_before']['avail_gb']} GB, commit headroom {m['memory_before']['commit_headroom_gb']} GB;"
          f" closing would free about {m['estimate']['ws_gb']} GB in use ({m['estimate']['priv_gb']} GB committed)")
    print("\nJOB BOTS (stopped between applications, restarted through their own tasks after the picture):")
    for it in m["items"]:
        if it["kind"] == "bot":
            sup = it["supervisor"]
            print(f"  {it['bot']:10s} task {it['task']} ({it['task_was']}); {it['state']}: {it['why']}"
                  + (f"; supervisor {sup['pid']}, {it['ws_gb']} GB" if sup else ""))
    print("\nAPPS:")
    for it in m["items"]:
        if it["kind"] == "app":
            what = ("close, reopen when you're back" if it["reopen"] else "close, not reopened") if it["running"] and not it["why"] else \
                (it["why"] or "not running")
            print(f"  {it['name']:28s} {what}" + (f"; {len(it['roots'])} root(s) {[r['pid'] for r in it['roots']]}, {it['ws_gb']} GB in use,"
                                                   f" {it['priv_gb']} GB committed" if it["roots"] else "")
                  + (f"; {it['windows']} window(s)" if it["app"] == "edge" else ""))
        elif it["kind"] == "task":
            print(f"  task {it['task']:24s} ({it['task_was']}): held, back on when opencode reopens")
        elif it["kind"] == "helpers":
            print(f"  {it['name']:28s} close: {[r['pid'] for r in it['roots']]}, {it['ws_gb']} GB")
    print("\nCLAUDE CODE TABS:")
    for it in m["items"]:
        if it["kind"] == "session":
            print(f"  {it['pid']:6d} {it['sid'][:8]} {'KEEP ' if it['verdict'] == 'active' else 'CLOSE'} idle {it['idle_min']} min,"
                  f" {it['ws_gb']} GB; {'; '.join(it['reasons']) or 'idle: nothing running, no timer, nothing in the last hour'}")
    print("\nKEPT:")
    for k, v in m["kept"].items():
        print(f"  {k:42s} {v['count']:3d} processes, {v['ws_gb']} GB in use")
    print("\nUNKNOWN (left running, named in the morning page):")
    for u in m["unknown"] or [{"name": "none", "pid": 0, "ws_gb": 0}]:
        print(f"  {u['name']} {u['pid']} {u['ws_gb']} GB")


# ------------------------------------------------------------------------------------------------------------------ the claim
def claim_path() -> Path:
    return home() / "claim.json"


def claim() -> None:
    """The night's claim on the machine's memory: Gemini waves (tools/wave.py) hold off while it names a live process."""
    save(claim_path(), {**me(), "since": datetime.now().isoformat(timespec="seconds")})


def release_claim() -> None:
    c = load(claim_path())
    if c and c.get("pid") == os.getpid():
        claim_path().unlink(missing_ok=True)


def claimed() -> bool:
    c = load(claim_path()) if claim_path().exists() else None
    return bool(c) and alive(c.get("pid"), c.get("ctime"))


# ------------------------------------------------------------------------------------------------------------------ the waits
def wait_until_away(deadline: datetime, say=print) -> bool:
    said = 0.0
    while datetime.now() < deadline:
        ok, why = away()
        if ok:
            say(f"room: you are away ({why})")
            return True
        if time.time() - said > 1800:
            say(f"room: waiting for you to be away ({why}); until {deadline:%H:%M}")
            said = time.time()
        time.sleep(30)
    say(f"room: you were not away by {deadline:%H:%M}; nothing closed, no picture tonight")
    return False


def facecard_runs(snap: dict | None = None) -> list[dict]:
    snap = snap or snapshot()
    return [p for p in snap.values() if lc(p, "name") in ("python.exe", "pythonw.exe") and "facecard.py" in lc(p, "cmd")]


def wait_for_facecard_runs(max_s: float, say=print) -> None:
    """A logged-in Gemini run is never killed (it holds the newest cookie): the room waits for it."""
    t0 = time.time()
    runs = facecard_runs()
    if runs:
        say(f"room: waiting for {len(runs)} Gemini picture run(s) to end (max {max_s / 60:.0f} min)")
    while runs and time.time() - t0 < max_s:
        time.sleep(60)
        runs = facecard_runs()
    if runs:
        say(f"room: {len(runs)} Gemini run(s) still going after {max_s / 60:.0f} min; left running")


# ------------------------------------------------------------------------------------------------------------------ making room
def _check_back() -> None:
    if idle_s() < BACK_S:
        raise UserBack()


def _item(m: dict, item_id: str) -> dict | None:
    return next((it for it in m["items"] if it["id"] == item_id), None)


def make_room(keep_sessions=(), say=print, bot_budget_s: float = BOT_BUDGET_S) -> dict:
    """Close everything the user's rule allows, recording each step in room.json first. Raises UserBack if he returns meanwhile (the
    caller puts everything back). Returns the manifest."""
    m = plan(keep_sessions)
    m["state"] = "making"
    save(manifest_path(), m)
    say(f"room: making room; free {m['memory_before']['avail_gb']} GB; about {m['estimate']['ws_gb']} GB in use to close")
    # 1. hold the tasks that would restart things during the night
    for it in m["items"]:
        if it["kind"] in ("bot", "task") and it.get("task_was") not in (None, "Disabled"):
            _check_back()
            it["held"] = task_set(it["task"], False)
            save(manifest_path(), m)
            say(f"room: task {it['task']} {'switched off' if it['held'] else 'could NOT be switched off'}")
    # 2. the bots, each between applications, one shared budget
    t0 = time.time()
    pending = [it for it in m["items"] if it["kind"] == "bot" and it["supervisor"]]
    while pending:
        _check_back()
        snap = snapshot()
        kids = children(snap)
        for it in list(pending):
            state, sup, why = bot_state(it["bot"], snap, kids)
            if state == "absent":
                it.update(status="already stopped", why=why)
                pending.remove(it)
            elif state == "safe":
                res = kill_tree(tree(sup, snap, kids))
                for r in bot_browsers(BOTS[it["bot"]], snapshot()):
                    s2 = snapshot()
                    res["ended"] += kill_tree(tree(r, s2, children(s2)))["ended"]
                it.update(status="stopped", why=why, closed=res)
                say(f"room: bot {it['bot']} stopped ({why}); ended {len(res['ended'])}, left {res['left']}")
                pending.remove(it)
            else:
                it["why"] = why
            save(manifest_path(), m)
        if pending and time.time() - t0 > bot_budget_s:
            for it in pending:
                it["status"] = "left running"
                say(f"room: bot {it['bot']} still busy after {bot_budget_s / 60:.0f} min ({it['why']}); left running")
            break
        if pending:
            time.sleep(60)
    # 3. the apps, from a fresh look at what runs now; herdr before opencode (an `opencode attach` pane has no timeout)
    snap = snapshot()
    kids = children(snap)
    fresh = plan(keep_sessions, snap)
    for app_id in APPS:
        _check_back()
        it, now_it = _item(m, f"app:{app_id}"), _item(fresh, f"app:{app_id}")
        it.update({k: now_it[k] for k in ("running", "reopen", "roots", "why", "ws_gb", "priv_gb", "group") if k in now_it})
        if app_id == "edge":
            it.update(windows=now_it.get("windows"), exe=now_it.get("exe"))
        if not now_it["running"] or now_it["why"]:
            continue
        res = {"ended": [], "left": []}
        for r in now_it["roots"]:
            p = snap.get(r["pid"])
            if p and p["ctime"] == r["ctime"]:
                part = kill_tree(tree(p, snap, kids))
                res["ended"] += part["ended"]
                res["left"] += part["left"]
        it.update(status="closed", closed=res)
        save(manifest_path(), m)
        say(f"room: closed {it['name']} (ended {len(res['ended'])}" + (f", left {res['left']}" if res["left"] else "") + ")")
    if _item(m, "app:opencode").get("status") == "closed":
        time.sleep(3)
        still = listening(OPENCODE_PORTS)
        if still:
            say(f"room: something still listens on {sorted(still)} after closing opencode")
    # 4. the unused MCP helpers, then the idle Claude Code tabs (each re-checked right before)
    _check_back()
    snap = snapshot()
    kids = children(snap)
    fresh = plan(keep_sessions, snap)
    hit = _item(fresh, "helpers")
    res = {"ended": [], "left": []}
    for r in hit["roots"]:
        p = snap.get(r["pid"])
        if p and p["ctime"] == r["ctime"]:
            part = kill_tree(tree(p, snap, kids))
            res["ended"] += part["ended"]
            res["left"] += part["left"]
    _item(m, "helpers").update(roots=hit["roots"], status="closed", closed=res)
    save(manifest_path(), m)
    for s in [it for it in fresh["items"] if it["kind"] == "session"]:
        it = _item(m, f"session:{s['sid']}")
        if it is None:
            m["items"].append(s)
            it = s
        it.update({k: s[k] for k in ("verdict", "reasons", "idle_min", "mcp")})
        if s["verdict"] != "idle":
            continue
        _check_back()
        snap = snapshot()
        kids = children(snap)
        again = next((x for x in sessions(snap, kids, keep_ids=set(keep_sessions), protected=protected_pids(snap, kids))
                      if x["sid"] == s["sid"]), None)
        if not again or again["verdict"] != "idle":
            it.update(verdict="active", reasons=(again or {}).get("reasons", ["gone"]))
            continue
        for h in again["mcp"]:
            p = snap.get(h["pid"])
            if p and p["ctime"] == h["ctime"]:
                kill_tree(tree(p, snap, kids))
        ok = terminate_exact(again["pid"], again["ctime"], EXIT_QUIET)
        it.update(status="closed" if ok else "could not close")
        save(manifest_path(), m)
        say(f"room: {'closed' if ok else 'could NOT close'} idle Claude Code tab {again['pid']} ({again['sid'][:8]}, idle {again['idle_min']} min)")
    time.sleep(5)
    m["memory_after"] = memory()
    m["state"] = "made"
    m["made"] = datetime.now().isoformat(timespec="seconds")
    save(manifest_path(), m)
    say(f"room: made; free {m['memory_after']['avail_gb']} GB (was {m['memory_before']['avail_gb']} GB)")
    return m


def listening(ports) -> set[int]:
    import psutil
    try:
        return {c.laddr.port for c in psutil.net_connections(kind="tcp") if c.status == psutil.CONN_LISTEN and c.laddr and c.laddr.port in ports}
    except Exception:
        return set()


# ------------------------------------------------------------------------------------------------------------- putting it back
def clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k != "ELECTRON_RUN_AS_NODE" and not k.startswith(("VSCODE_", "CLAUDE"))}


def explorer_open(target: str) -> None:
    """Explorer starts it: the app inherits Explorer's environment, not ours, and is outside the night task's job."""
    subprocess.Popen(["explorer.exe", target], env=clean_env(), creationflags=CREATE_NO_WINDOW, close_fds=True)


def ensure_edge_shortcut(edge_exe: str | None) -> Path | None:
    lnk = edge_shortcut()
    if lnk.exists():
        return lnk
    exe = edge_exe or r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ps = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); $s.TargetPath = '{exe}';"
          " $s.Arguments = '--restore-last-session'; $s.Save()")
    _run("powershell", "-NoProfile", "-NonInteractive", "-Command", ps, timeout=300)
    return lnk if lnk.exists() else None


def _wait_for(test, seconds: float) -> bool:
    t0 = time.time()
    while time.time() - t0 < seconds:
        if test():
            return True
        time.sleep(5)
    return test()


def _running(pred) -> bool:
    snap = snapshot()
    return any(pred(p, snap) for p in snap.values())


def restore_bot(it: dict, say=print) -> str:
    """Back on through its own task, exactly one supervisor: enable, let a missed trigger start it, run it only if nothing did."""
    bot = BOTS[it["bot"]]
    if it.get("held"):
        task_set(bot["task"], True)
    if it.get("task_was") in (None, "Disabled") or it.get("status") in (None, "left running"):
        return "task back on" if it.get("held") else "nothing to do"
    for _ in range(2):
        time.sleep(60)
        if supervisors(bot, snapshot()):
            return "running"
        task_run(bot["task"])
    time.sleep(60)
    return "running" if supervisors(bot, snapshot()) else "NOT running"


def restore_app(m: dict, it: dict, say=print) -> str:
    if it["app"] == "opencode":
        for name in OPENCODE_TASKS:
            t = _item(m, f"task:{name}")
            if t and t.get("held"):
                task_set(name, True)
                t["restored"] = datetime.now().isoformat(timespec="seconds")
        for name in OPENCODE_TASKS:
            task_run(name)
        ok = _wait_for(lambda: listening(OPENCODE_PORTS) == set(OPENCODE_PORTS), 420)
        return "running on 4599 and 4600" if ok else f"listening only on {sorted(listening(OPENCODE_PORTS))}"
    if it["app"] == "wispr":
        explorer_open(str(STARTUP / "Wispr Flow.lnk"))
        return "running" if _wait_for(lambda: _running(APPS["wispr"][0]), 90) else "NOT running"
    if it["app"] == "edge":
        lnk = ensure_edge_shortcut(it.get("exe"))
        explorer_open(str(lnk) if lnk else "shell:AppsFolder\\MSEdge")
        return "running" if _wait_for(lambda: _running(APPS["edge"][0]), 90) else "NOT running"
    return "not reopened"


_RESTORING = threading.Lock()     # the return watcher and the end of the night may put things back at the same moment
RESTORE_ORDER = {"app:wispr": 0, "app:edge": 1, "app:opencode": 2}   # what he uses first; opencode waits minutes for its servers; bots last


def restore(m: dict | None = None, groups=("bots", "apps"), say=print) -> dict | None:
    """Put back what the room changed, for the groups asked. Idempotent: each item once, at most 3 tries, then reported."""
    with _RESTORING:
        return _restore(groups, say)


def _restore(groups, say) -> dict | None:
    m = load()                    # always the record on disk: another thread may have put something back meanwhile
    if not m:
        return None
    m["state"] = "restoring"
    save(manifest_path(), m)
    for it in sorted(m["items"], key=lambda it: RESTORE_ORDER.get(it["id"], 3 if it["kind"] == "bot" else 4)):
        group = it.get("group")
        if it["kind"] == "task":
            continue                                                    # restored with its app (opencode)
        if group not in groups or it.get("restored") or it.get("restore_tries", 0) >= 3:
            continue
        if it["kind"] == "app" and (it.get("status") != "closed" or not it.get("reopen")):
            continue
        it["restore_tries"] = it.get("restore_tries", 0) + 1
        try:
            res = restore_bot(it, say) if it["kind"] == "bot" else restore_app(m, it, say)
        except Exception as e:
            res = f"FAILED ({type(e).__name__}: {e})"
        ok = not res.startswith(("NOT", "FAILED", "listening only"))
        it["restored"] = datetime.now().isoformat(timespec="seconds") if ok else None
        it["restore_result"] = res
        save(manifest_path(), m)
        say(f"room: {it.get('name') or it['id']}: {res}")
    # opencode's tasks switched off while no opencode was running: back on with the apps
    if "apps" in groups and _item(m, "app:opencode").get("status") != "closed":
        for it in m["items"]:
            if it["kind"] == "task" and it.get("held") and not it.get("restored"):
                task_set(it["task"], True)
                it["restored"] = datetime.now().isoformat(timespec="seconds")
    pending = [it for it in m["items"] if needs_restore(it)]
    m["state"] = "restored" if not pending else "restoring"
    save(manifest_path(), m)
    if not pending:
        archive(m)
    return m


def needs_restore(it: dict) -> bool:
    if it.get("restored") or it.get("restore_tries", 0) >= 3:
        return False
    if it["kind"] == "bot":
        return bool(it.get("held") or it.get("status") == "stopped")
    if it["kind"] == "app":
        return it.get("status") == "closed" and bool(it.get("reopen"))
    if it["kind"] == "task":
        return bool(it.get("held"))
    return False


def archive(m: dict) -> None:
    stamp = (m.get("planned") or datetime.now().isoformat()).replace(":", "").replace("-", "")[:15]
    try:
        os.replace(manifest_path(), home() / f"room_{stamp}.json")
    except OSError:
        pass


def morning(made: str | None) -> datetime:
    """From when an input means he is back: 06:00 after a night room (made 18:00-06:00); right away for a room made in the day."""
    t = datetime.fromisoformat(made) if made else datetime.now()
    six = t.replace(hour=RETURN_HOUR, minute=0, second=0, microsecond=0)
    if t.hour < RETURN_HOUR:
        return six
    if t.hour >= RETURN_UNTIL_HOUR:
        return six + timedelta(days=1)
    return t


def back_after_morning(m: dict) -> bool:
    """He is back: his last keyboard or mouse input is after that time."""
    return last_input() >= morning(m.get("made") or m.get("planned"))


class ReturnWatcher(threading.Thread):
    """Reopens Wispr Flow, opencode and Edge (those that were open and got closed) on his first input after 06:00."""

    def __init__(self, say=print):
        super().__init__(daemon=True)
        self.say, self.done, self.fired = say, threading.Event(), False

    def run(self):
        while not self.done.wait(15):
            m = load()
            if not m or not any(needs_restore(it) for it in m["items"] if it.get("group") == "apps"):
                return
            if back_after_morning(m):
                self.say("room: you are back; reopening what was open")
                restore(groups=("apps",), say=self.say)
                self.fired = True
                return


def apps_pending(m: dict | None = None) -> bool:
    m = m or load()
    return bool(m) and any(needs_restore(it) for it in m["items"] if it.get("group") == "apps")


def own_room() -> dict | None:
    """The room on disk if this process made it (also one it was still making when something failed)."""
    m = load()
    return m if m and (m.get("runner") or {}).get("pid") == os.getpid() and m.get("state") != "restored" else None


def restore_if_stale(say=print) -> str | None:
    """A room whose night is gone (a crash, a reboot): the bots come back now; the apps when he is back after 06:00 (or now, if the night
    never got that far)."""
    m = load()
    if not m or m.get("state") == "restored":
        return None
    r = m.get("runner") or {}
    if alive(r.get("pid"), r.get("ctime")):
        return None
    groups = ["bots"] + (["apps"] if back_after_morning(m) else [])
    restore(groups=tuple(groups), say=say)
    return f"room left by a night that is gone: restored {', '.join(groups)}" + ("; apps wait for you" if "apps" not in groups else "")
