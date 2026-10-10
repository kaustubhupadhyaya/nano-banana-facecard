"""One local picture with Qwen-Image-2.1 on this laptop's CPU (stable-diffusion.cpp), fully recorded. Separate from the Gemini system.

The user, 2026-10-09: "Prepare a system where the current Gemini system is intact, but a parallel system of dedicated overnight runs with
multiple image generations is created using the Qwen local image model." This module makes ONE picture from a frozen recipe:
- the recipe lock's images, staged byte-identical from the blob store, the photo to edit FIRST (in Qwen-Image-2.1 image 1 is the image
  being edited and sets the canvas);
- the lock prompt renumbered for that order and written with the model's own reference tokens <image1>..<imageN> (stable-diffusion.cpp
  labels each reference "<imageN><|vision_start|>...", src/conditioning/conditioner.hpp); every change to the prompt is a recorded transform;
- `sd-cli` run hidden, at below-normal priority, inside a job object (it dies with this process), its step progress read from its output
  and its memory sampled every 2 s;
- local_run.json: the command, seed, sizes, threads, every sha256 (inputs, models, program), time per phase, seconds per step, memory peaks.

    .venv\\Scripts\\python.exe local_gen.py pin_783485666539777055@v2 --dry-run
    .venv\\Scripts\\python.exe local_gen.py pin_783485666539777055@v2 -W 512 -H 640 --steps 2 --refs-cap 262144 --seed 1 -t 4

tools/overnight.py runs it from a queue at night. Never used here: .cache\\inflight (the Gemini credit guard; the cookie keep-alive skips its
renewal while that folder has entries), outputs\\ (the Gemini tools scan it), a file named run.json (tools/best_check.py would export the
picture to the results folder), any post-processing of the picture.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import paths  # noqa: E402
import provenance as P  # noqa: E402
import recipe as R  # noqa: E402

SCHEMA = "facecard.local_run/1"
SDCPP_RELEASE = "master-948-228c707"
SDCPP_ZIP = {"name": "sd-master-228c707-bin-win-cpu-x64.zip",
             "url": "https://github.com/leejet/stable-diffusion.cpp/releases/download/master-948-228c707/sd-master-228c707-bin-win-cpu-x64.zip"}
# role -> (file under paths.localgen_models_dir(), sha256 published by its source). The diffusion model is the user's exact file.
MODEL_FILES = {
    "diffusion": ("qwen-image-2.1-UC-Q4_K_M.gguf", "e79c8a009f2ecbdb6c70fd663d9aea9ee304a0d91f347e4169a756b8ad141b41"),
    "vae": ("vae/qwen_image_2.1_vae_bf16.safetensors", "bb21f7473051e1ac368515dd3f2e15cd44d7a11748ee8823e1ddca3e4876b7c9"),
    "llm": ("Qwen3VL-8B-Instruct-Q4_K_M.gguf", "67d1659bfe71b89d50b45a4ad1a9e5b997e5bb16ce5da66a6a6167abd569e9e2"),
    "llm_vision": ("mmproj-Qwen3VL-8B-Instruct-F16.gguf", "ca524100ebf825c9a870db1c580d03879e0da0ab2541697e2458e64891cf9d38"),
    # the int8 ConvRot text encoder, downloaded ONLY from the user's repo abenzerps/Qwen-Image-2.1-Uncensored-GGUF (the user, 2026-10-10);
    # the sha256 is the one that repo's API publishes for text_encoders/qwen3vl_8b_int8_convrot.safetensors; vision tower included
    "llm_int8": ("text_encoders/qwen3vl_8b_int8_convrot.safetensors", "8bfd0f6e12abf2d2d697ecc888e5e90b0d6741d6708f05799f53afa560452e8f"),
}
# which files each text-encoder choice loads: "int8" = the model's own companion (no compromise, the user 2026-10-10); "q4" = the 4-bit GGUF
TE_SETS = {"int8": ("diffusion", "vae", "llm_int8"), "q4": ("diffusion", "vae", "llm", "llm_vision")}
QWEN_ROLE_ORDER = ("photo_to_edit", "face", "body")      # then any other role, in the lock's order
GB = 1024 ** 3

# ----------------------------------------------------------------------------------------------------------------------- Windows calls
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
CREATE_NO_WINDOW = 0x08000000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9
ProcessPowerThrottling = 4


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                  "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wt.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t), ("PrivateUsage", ctypes.c_size_t)]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", wt.DWORD), ("BatteryFullLifeTime", wt.DWORD)]


class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [("Version", wt.ULONG), ("ControlMask", wt.ULONG), ("StateMask", wt.ULONG)]


k32.CreateJobObjectW.restype = wt.HANDLE
k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
k32.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
k32.QueryInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.c_void_p]
k32.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
k32.TerminateJobObject.argtypes = [wt.HANDLE, wt.UINT]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.c_void_p, wt.DWORD]
k32.GlobalMemoryStatusEx.argtypes = [ctypes.c_void_p]
k32.GetSystemPowerStatus.argtypes = [ctypes.c_void_p]
k32.SetProcessInformation.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]


def memory_status() -> dict:
    """Available RAM and commit headroom of the machine, in GB."""
    m = MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    k32.GlobalMemoryStatusEx(ctypes.byref(m))
    return {"total_gb": round(m.ullTotalPhys / GB, 2), "avail_gb": round(m.ullAvailPhys / GB, 2),
            "commit_limit_gb": round(m.ullTotalPageFile / GB, 2), "commit_headroom_gb": round(m.ullAvailPageFile / GB, 2)}


def on_ac_power() -> bool | None:
    s = SYSTEM_POWER_STATUS()
    if not k32.GetSystemPowerStatus(ctypes.byref(s)):
        return None
    return {0: False, 1: True}.get(s.ACLineStatus)


class Job:
    """A Windows job object: its process dies when this handle closes (also when this Python process dies), and it reports peak memory."""

    def __init__(self):
        self.h = k32.CreateJobObjectW(None, None)
        if not self.h:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(self.h, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")

    def assign(self, proc: subprocess.Popen) -> bool:
        return bool(k32.AssignProcessToJobObject(self.h, int(proc._handle)))

    def peak_gb(self) -> float | None:
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        if not k32.QueryInformationJobObject(self.h, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info), None):
            return None
        return round(info.PeakProcessMemoryUsed / GB, 3)

    def terminate(self) -> None:
        k32.TerminateJobObject(self.h, 1)

    def close(self) -> None:
        if self.h:
            k32.CloseHandle(self.h)
            self.h = None


def process_memory(proc: subprocess.Popen) -> dict | None:
    pmc = PROCESS_MEMORY_COUNTERS_EX()
    pmc.cb = ctypes.sizeof(pmc)
    if not k32.K32GetProcessMemoryInfo(int(proc._handle), ctypes.byref(pmc), pmc.cb):
        return None
    return {"ws_gb": pmc.WorkingSetSize / GB, "peak_ws_gb": pmc.PeakWorkingSetSize / GB, "commit_gb": pmc.PrivateUsage / GB,
            "peak_commit_gb": pmc.PeakPagefileUsage / GB}


def top_memory_users(n: int = 8) -> list[tuple[str, float]]:
    """(program, GB of private memory summed over its processes), largest first. ctypes only: tasklist timed out under memory pressure."""
    k32.K32EnumProcesses.argtypes = [ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]
    k32.OpenProcess.restype = wt.HANDLE
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    arr = (wt.DWORD * 4096)()
    got = wt.DWORD()
    if not k32.K32EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(got)):
        return []
    agg: dict[str, float] = {}
    for pid in arr[: got.value // ctypes.sizeof(wt.DWORD)]:
        h = k32.OpenProcess(0x1000, False, pid)                          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            continue
        try:
            buf, size = ctypes.create_unicode_buffer(520), wt.DWORD(520)
            name = Path(buf.value).name if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else f"pid {pid}"
            pmc = PROCESS_MEMORY_COUNTERS_EX()
            pmc.cb = ctypes.sizeof(pmc)
            if k32.K32GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
                agg[name] = agg.get(name, 0.0) + pmc.PrivateUsage / GB
        finally:
            k32.CloseHandle(h)
    return sorted(((k, round(v, 2)) for k, v in agg.items()), key=lambda kv: -kv[1])[:n]


def no_power_throttling(proc: subprocess.Popen) -> bool:
    """Opt the child out of EcoQoS (Windows slows background processes down to save power)."""
    st = PROCESS_POWER_THROTTLING_STATE(1, 0x1, 0x0)
    return bool(k32.SetProcessInformation(int(proc._handle), ProcessPowerThrottling, ctypes.byref(st), ctypes.sizeof(st)))


# --------------------------------------------------------------------------------------------------------------------------- the files
ENGINES = {"cpu": SDCPP_RELEASE, "vulkan": SDCPP_RELEASE + "-vulkan"}   # the Vulkan build runs on the Intel UHD iGPU (shared memory)


def sd_cli(engine: str = "cpu") -> Path:
    d = paths.sdcpp_dir() / ENGINES[engine]
    for name in ("sd-cli.exe", "sd.exe"):
        if (d / name).is_file():
            return d / name
    raise SystemExit(f"stable-diffusion.cpp {ENGINES[engine]} is not installed in {d} (see AGENTS.md, Overnight local runs)")


def engine_record(engine: str = "cpu") -> dict:
    exe = sd_cli(engine)
    return {"engine": engine, "release": SDCPP_RELEASE, "folder": ENGINES[engine], "exe": str(exe), "exe_sha256": P.sha256_file_cached(exe),
            "dll_sha256": {p.name: P.sha256_file_cached(p) for p in sorted(exe.parent.glob("*.dll"))}}


def model_paths(verify: bool = True, te: str = "q4") -> dict[str, Path]:
    """The model files of a text-encoder choice; with verify, each sha256 must equal the one its source published (hashed once, then cached
    by size and time). The int8 text encoder is returned under the role "llm"."""
    d = paths.localgen_models_dir()
    out, bad = {}, []
    for role in TE_SETS[te]:
        name, sha = MODEL_FILES[role]
        role = "llm" if role == "llm_int8" else role
        p = d / name
        if not p.is_file():
            bad.append(f"{role}: {p} is missing")
            continue
        if verify and P.sha256_file_cached(p) != sha:
            bad.append(f"{role}: {p.name} sha256 differs from the published {sha[:12]}")
        out[role] = p
    if bad:
        raise SystemExit("local model files not ready:\n  " + "\n  ".join(bad))
    return out


# -------------------------------------------------------------------------------------------------------------------------- the prompt
IMG_REF = re.compile(r"\b([Ii]mages?) (\d+)(?:-(\d+))?")


def qwen_order(lock: dict) -> list[dict]:
    """The lock's files with the photo to edit first, then faces, then the body, then anything else (each group in the lock's order)."""
    rank = {r: i for i, r in enumerate(QWEN_ROLE_ORDER)}
    files = sorted(lock["files"], key=lambda f: (rank.get(f["role"], len(rank)), f["n"]))
    if not files or files[0]["role"] != "photo_to_edit":
        raise SystemExit("this recipe has no photo to edit: the local system only runs edit recipes (Route G) for now")
    return [{**f, "old_n": f["n"], "new_n": i + 1} for i, f in enumerate(files)]


def renumber(prompt: str, mapping: dict[int, int]) -> str:
    """'Image N' / 'images A-B' in the lock prompt become the model's reference tokens for the new order: 'image 5' -> '<image1>',
    'images 1-3' -> '<image2>, <image3> and <image4>'. Then the ROLES lines are sorted by their first image, so the photo to edit is listed first."""
    found = IMG_REF.findall(prompt)

    def fn(m: re.Match) -> str:
        a, b = int(m.group(2)), m.group(3)
        if b is None:
            return f"<image{mapping[a]}>"
        new = [mapping[k] for k in range(a, int(b) + 1)]
        if new != list(range(new[0], new[0] + len(new))):
            raise ValueError(f"'{m.group(0)}' would not stay a contiguous range in the new order ({new})")
        toks = [f"<image{k}>" for k in new]
        return toks[0] if len(toks) == 1 else ", ".join(toks[:-1]) + " and " + toks[-1]

    out = IMG_REF.sub(fn, prompt)
    if IMG_REF.findall(out) or out.count("<image") < len(found):
        raise ValueError("renumbering left an 'image N' reference behind")
    head = "REFERENCE IMAGES BY ROLE:\n"
    if head in out:
        start = out.index(head) + len(head)
        end = out.index("\n\n", start)
        lines = out[start:end].split("\n")
        lines.sort(key=lambda l: int(re.search(r"<image(\d+)>", l).group(1)) if re.search(r"<image(\d+)>", l) else 999)
        out = out[:start] + "\n".join(lines) + out[end:]
        if not lines[0].startswith("<image1> is the PHOTO TO EDIT"):
            raise ValueError(f"the first ROLES line is not the photo to edit: {lines[0]!r}")
    return out


def qwen_prompt(lock: dict, order: list[dict]) -> tuple[str, list[str]]:
    """The lock prompt for this model and order, and the list of transforms applied to it (recorded in local_run.json). It reaches sd-cli as
    a UTF-8 file (--prompt-file), so its text needs no other change: a command-line prompt would pass through the ANSI code page."""
    mapping = {f["old_n"]: f["new_n"] for f in order}
    text = renumber(lock["prompt"], mapping)
    transforms = [f"image numbers renumbered for Qwen order {json.dumps({str(k): v for k, v in sorted(mapping.items())})} and written as "
                  "the model's reference tokens <imageN>"]
    return text, transforms


# ---------------------------------------------------------------------------------------------------------------------------- running
STEP_RE = re.compile(r"(\d+)/(\d+)\s*-\s*([\d.]+)\s*(s/it|it/s)")


def build_argv(exe: Path, models: dict, inputs: list[Path], prompt_file: Path, out_tmp: Path, preview: Path, o: dict) -> list[str]:
    argv = [str(exe), "--diffusion-model", str(models["diffusion"]), "--vae", str(models["vae"]), "--llm", str(models["llm"])]
    if models.get("llm_vision"):             # a GGUF text encoder needs its separate vision tower; the int8 one carries its own
        argv += ["--llm_vision", str(models["llm_vision"])]
    for p in inputs:
        argv += ["-r", str(p)]
    argv += ["--prompt-file", str(prompt_file), "-W", str(o["W"]), "-H", str(o["H"]), "--steps", str(o["steps"]), "--cfg-scale", str(o["cfg"]),
             "--sampling-method", o["sampler"], "-t", str(o["threads"]), "-s", str(o["seed"]), "--fa", "--vae-tiling", "--mmap"]
    if o.get("refs_cap"):                    # 0 = the model's own default (1 MP per reference); a cap shrinks the references
        argv += ["--ref-image-args", f"vae_input_max_pixels={o['refs_cap']}"]
    if o.get("backend"):                     # e.g. "vulkan0" (everything on the iGPU) or "te=cpu,diffusion=vulkan0"
        argv += ["--backend", o["backend"]]
    argv += ["--model-args", f"qwen_image_2_1_prefix_cache_type={o['cache_type']}",
             "--preview", "proj", "--preview-path", str(preview), "-v", "-o", str(out_tmp)]
    return argv + list(o.get("extra_args") or [])


# sd-cli's own log lines that start each phase, in order (read from a real run, 2026-10-09). A phase only moves forward.
PHASE_MARKERS = (("ref_encode", "preprocess ref["),                  # the reference images through the VAE
                 ("condition", "encode_first_stage completed"),      # the text encoder over the prompt and the reference images
                 ("sample", "generating image:"),                    # the diffusion steps; the first one also builds the reference cache
                 ("decode", "sampling completed"),                   # the VAE decodes the picture
                 ("save", "decode_first_stage completed"))
PHASE_ORDER = ("load",) + tuple(p for p, _ in PHASE_MARKERS)
# sd-cli's own timings: "<what> completed, taking 387.01s"
OWN_TIMING = re.compile(r"(encode_first_stage|get_learned_condition|sampling|decode_first_stage) completed, taking ([\d.]+)\s*s\b")
OWN_NAMES = {"encode_first_stage": "ref_encode", "get_learned_condition": "condition", "sampling": "sample", "decode_first_stage": "decode"}



def save_json(path: Path, data, tries: int = 1, say=None) -> bool:
    """atomic_write_json that never stops a picture. Windows refuses to replace a file another process has open (a watcher reading
    progress.json, Defender scanning it): on 2026-10-10 that PermissionError escaped the loop and killed a run at step 5 of 40 (the job
    object then ended sd-cli). A progress file gets one attempt (P retries ~3 s itself); the run record gets `tries` attempts."""
    for i in range(tries):
        try:
            P.atomic_write_json(path, data)
            return True
        except OSError as e:
            if i == tries - 1:
                if say:
                    say(f"[local] could not save {Path(path).name} ({type(e).__name__}); the picture continues")
                return False
            time.sleep(2 * (i + 1))
    return False

class Progress:
    """What sd-cli is doing, read from its output. Progress means a change of (phase, counter, completed sub-step): the user's standing rule
    is that a monitor measures progress, never mere liveness."""

    def __init__(self, steps: int):
        self.steps = steps
        self.t0 = time.time()
        self.phase = "load"
        self.phase_start = {"load": self.t0}
        self.counter = None
        self.last_change = self.t0
        self.step_times: list[tuple[int, float]] = []
        self.own: dict[str, float] = {}
        self.lines = 0
        self.lock = threading.Lock()

    def _phase(self, name: str) -> None:
        if PHASE_ORDER.index(name) > PHASE_ORDER.index(self.phase):
            self.phase = name
            self.phase_start[name] = time.time()
            self.last_change = time.time()
            if name == "sample":
                self.step_times = [(0, time.time())]

    def feed(self, line: str) -> None:
        with self.lock:
            self.lines += 1
            for name, marker in PHASE_MARKERS:
                if marker in line:
                    self._phase(name)
            t = OWN_TIMING.search(line)
            if t:
                self.own[OWN_NAMES[t.group(1)]] = float(t.group(2))
            if "computing vae encode graph completed" in line:          # one reference image encoded: progress inside ref_encode
                self.last_change = time.time()
            m = STEP_RE.search(line)
            if m:
                cur, tot = int(m.group(1)), int(m.group(2))
                if (self.phase, cur, tot) != self.counter:
                    self.counter = (self.phase, cur, tot)
                    self.last_change = time.time()
                    if self.phase == "sample" and tot == self.steps and cur > self.step_times[-1][0]:
                        self.step_times.append((cur, time.time()))

    def snapshot(self) -> dict:
        with self.lock:
            st = self.step_times
            secs = [round(b[1] - a[1], 1) for a, b in zip(st, st[1:])]
            return {"phase": self.phase, "counter": self.counter, "step": st[-1][0] if st else 0, "steps": self.steps,
                    "first_step_s": secs[0] if secs else None, "step_secs": secs[1:], "own_timings_s": dict(self.own),
                    "elapsed_s": round(time.time() - self.t0, 1), "since_progress_s": round(time.time() - self.last_change, 1),
                    "phase_start": {k: round(v - self.t0, 1) for k, v in self.phase_start.items()}}


# Before a phase has been measured on this machine: generous ceilings (seconds without progress), from the first trial (2026-10-09:
# references 6.5 min, text encoder 24.5 min at 512 px with five 512 px references under memory pressure).
UNMEASURED_LIMIT_S = {"load": 1800, "ref_encode": 3600, "condition": 3 * 3600, "sample_first": 3 * 3600, "sample": 3 * 3600,
                      "decode": 3600, "save": 600}


def default_stall_limit(snap: dict, measured: dict | None = None) -> float:
    """Seconds without progress before the child is stopped: max(3 x the measured time, 15 min) for a phase measured on this machine at
    this shape, else the unmeasured ceiling above."""
    measured = measured or {}
    ph = snap["phase"]
    if ph == "sample":
        if snap["step_secs"]:
            return max(3 * max(snap["step_secs"]), 900)
        if snap["first_step_s"] is None:                                # still inside the first step (it also builds the reference cache)
            return max(3 * measured["first_step_s"], 900) if measured.get("first_step_s") else UNMEASURED_LIMIT_S["sample_first"]
        return max(3 * measured["s_per_step"], 900) if measured.get("s_per_step") else UNMEASURED_LIMIT_S["sample"]
    if measured.get(f"{ph}_s"):
        return max(3 * measured[f"{ph}_s"], 900)
    return UNMEASURED_LIMIT_S.get(ph, 3600)


PRIORITY = {"below_normal": BELOW_NORMAL_PRIORITY_CLASS, "normal": 0x00000020}


def run_sd(argv: list[str], log_path: Path, progress_path: Path, steps: int, stall_limit=default_stall_limit, measured: dict | None = None,
           stop: threading.Event | None = None, priority: str = "below_normal", say=print) -> dict:
    """Run sd-cli to the end (or until the watchdog or `stop` ends it). Returns the attempt record. Below-normal priority by default (the
    night: the job bots and the user's programs come first); "normal" for a daytime trial, which otherwise starves (2026-10-09: 0.3 cores)."""
    started = datetime.now().isoformat(timespec="seconds")
    prog = Progress(steps)
    job = Job()
    mem = {"peak_ws_gb": 0.0, "peak_commit_gb": 0.0, "min_avail_gb": None, "min_commit_headroom_gb": None}
    killed_by = None
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0,
                            creationflags=CREATE_NO_WINDOW | PRIORITY[priority])
    in_job = job.assign(proc)
    throttling_off = no_power_throttling(proc)

    def reader():
        buf = b""
        with open(log_path, "ab") as log:
            while True:
                chunk = proc.stdout.read(65536)
                if not chunk:
                    break
                log.write(chunk)
                log.flush()
                buf += chunk
                parts = re.split(rb"[\r\n]", buf)
                buf = parts.pop()
                for part in parts:
                    if part.strip():
                        prog.feed(part.decode("utf-8", "replace"))
            if buf.strip():
                prog.feed(buf.decode("utf-8", "replace"))

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    last_write = 0.0
    said = None
    try:
        while proc.poll() is None:
            pm = process_memory(proc)
            ms = memory_status()
            if pm:
                mem["peak_ws_gb"] = max(mem["peak_ws_gb"], pm["peak_ws_gb"])
                mem["peak_commit_gb"] = max(mem["peak_commit_gb"], pm["peak_commit_gb"])
            mem["min_avail_gb"] = ms["avail_gb"] if mem["min_avail_gb"] is None else min(mem["min_avail_gb"], ms["avail_gb"])
            mem["min_commit_headroom_gb"] = ms["commit_headroom_gb"] if mem["min_commit_headroom_gb"] is None \
                else min(mem["min_commit_headroom_gb"], ms["commit_headroom_gb"])
            snap = prog.snapshot()
            if (snap["phase"], snap["step"]) != said:     # one log line per phase change and per finished step: a watcher reads only the
                said = (snap["phase"], snap["step"])      # log, never progress.json (a reader holding it open crashed a run, 2026-10-10)
                took = (snap["step_secs"] or [snap["first_step_s"]])[-1] if snap["step"] else None
                say(f"[local] {snap['phase']}" + (f" step {snap['step']}/{snap['steps']}" if snap["phase"] == "sample" else "")
                    + (f" ({took:.0f} s)" if took is not None else "") + f"; free {ms['avail_gb']} GB")
            limit = stall_limit(snap, measured) if stall_limit else None
            if limit and snap["since_progress_s"] > limit:
                killed_by = f"watchdog: no progress for {snap['since_progress_s']:.0f} s in phase {snap['phase']} (limit {limit:.0f} s)"
            elif stop is not None and stop.is_set():
                killed_by = getattr(stop, "reason", None) or "stopped"
            if killed_by:
                say(f"[local] stopping sd-cli: {killed_by}")
                job.terminate()
                break
            if time.time() - last_write > 5:
                save_json(progress_path, {**snap, "memory": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in mem.items()},
                                                    "pid": proc.pid, "updated": datetime.now().isoformat(timespec="seconds")})
                last_write = time.time()
            time.sleep(2)
        try:
            proc.wait(timeout=600)       # a process stuck in page-ins can take minutes to die after the job is terminated (2026-10-10)
        except subprocess.TimeoutExpired:
            say("[local] sd-cli did not exit within 10 min of being stopped; recording the attempt anyway")
    finally:
        t.join(timeout=30)
        job_peak = job.peak_gb()
        job.close()
    snap = prog.snapshot()
    ends = dict(snap["phase_start"])
    total = snap["elapsed_s"]
    order = sorted(ends.items(), key=lambda kv: kv[1])
    phases = {name: round((order[i + 1][1] if i + 1 < len(order) else total) - start, 1) for i, (name, start) in enumerate(order)}
    secs = snap["step_secs"]
    rec = {"started": started, "ended": datetime.now().isoformat(timespec="seconds"), "exit_code": proc.returncode, "killed_by": killed_by,
           "priority": priority, "in_job_object": in_job, "eco_qos_off": throttling_off, "elapsed_s": total, "phases_s": phases,
           "own_timings_s": snap["own_timings_s"], "steps_done": snap["step"], "first_step_s": snap["first_step_s"], "step_secs": secs,
           "s_per_step_median": sorted(secs)[len(secs) // 2] if secs else None, "output_lines": prog.lines,
           "peak_working_set_gb": round(mem["peak_ws_gb"], 2), "peak_commit_gb": round(mem["peak_commit_gb"], 2), "job_peak_gb": job_peak,
           "min_avail_gb": mem["min_avail_gb"], "min_commit_headroom_gb": mem["min_commit_headroom_gb"]}
    save_json(progress_path, {**snap, "finished": rec["ended"], "exit_code": rec["exit_code"], "killed_by": killed_by}, tries=5)
    return rec


# ------------------------------------------------------------------------------------------------------------------------- the run
def run_folder(goal_key: str, tag: str = "") -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", goal_key.lower()).strip("-")
    d = paths.local_dir() / "runs" / f"{datetime.now():%Y%m%d_%H%M%S}_qwen21-local_{slug}{tag}"
    (d / "inputs").mkdir(parents=True, exist_ok=False)
    return d


def generate(recipe_ref: str, seed: int = 1, W: int = 768, H: int = 960, steps: int = 25, threads: int = 4, refs_cap: int = 589824,
             cache_type: str = "q8_0", cfg: float = 1.0, sampler: str = "euler", dry_run: bool = False, extra_args: list[str] | None = None,
             measured: dict | None = None, stop: threading.Event | None = None, retries: int = 0, priority: str = "below_normal",
             engine: str = "cpu", backend: str | None = None, te: str = "int8", say=print) -> Path:
    """Make one picture (v1_0.png) of a recipe in a new run folder under D:\\FacecardLocal\\runs; returns the folder."""
    if W % 32 or H % 32:
        raise SystemExit(f"width and height must be divisible by 32 (got {W}x{H})")
    rec, rec_path = R.load(recipe_ref)
    problems = R.check_integrity(rec)
    if problems:
        raise SystemExit("recipe integrity:\n  " + "\n  ".join(problems))
    lock = rec["lock"]
    order = qwen_order(lock)
    prompt, transforms = qwen_prompt(lock, order)
    goal_key = rec["goal"].get("key") or R.goal_key_of(rec["goal"]["path"])
    run = run_folder(goal_key, "_dry" if dry_run else "")
    inputs = [P.stage(f["sha256"], run / "inputs", f"{f['new_n']}_{f['role']}{Path(f['upload_name']).suffix.lower() or '.jpg'}") for f in order]
    (run / "recipe_copy.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    P.write_text_lf(run / "prompt_lock.txt", lock["prompt"])
    P.write_text_lf(run / "prompt_qwen.txt", prompt)
    opts = {"seed": seed, "W": W, "H": H, "steps": steps, "threads": threads, "refs_cap": refs_cap, "cache_type": cache_type, "cfg": cfg,
            "sampler": sampler, "engine": engine, "backend": backend, "te": te, "extra_args": extra_args or []}
    roles = {("llm" if r == "llm_int8" else r): r for r in TE_SETS[te]}      # role in the command -> MODEL_FILES key
    models = model_paths(verify=True, te=te) if not dry_run else {k: paths.localgen_models_dir() / MODEL_FILES[v][0] for k, v in roles.items()}
    exe = sd_cli(engine) if not dry_run else paths.sdcpp_dir() / ENGINES[engine] / "sd-cli.exe"
    out_tmp, out = run / "v1_0.tmp.png", run / "v1_0.png"
    argv = build_argv(exe, models, inputs, run / "prompt_qwen.txt", out_tmp, run / "preview.png", opts)
    record = {
        "schema": SCHEMA, "created": datetime.now().isoformat(timespec="seconds"), "dry_run": dry_run, "job": opts,
        "recipe": {"ref": recipe_ref, "file": str(rec_path), "file_sha256": P.sha256_file(rec_path), "goal_key": goal_key,
                   "request_sha256": lock.get("request_sha256"), "prompt_sha256": lock.get("prompt_sha256")},
        "prompt": {"qwen_sha256": P.sha256_text(prompt), "chars": len(prompt), "transforms": transforms},
        "inputs": [{"n": f["new_n"], "was_n": f["old_n"], "role": f["role"], "name": f["upload_name"], "sha256": f["sha256"], "px": f.get("px")}
                   for f in order],
        "models": {k: {"file": str(models[k]), "sha256": MODEL_FILES[roles[k]][1], "bytes": models[k].stat().st_size if models[k].exists() else None}
                   for k in models},
        "engine": engine_record(engine) if not dry_run else {"engine": engine, "release": SDCPP_RELEASE, "exe": str(exe)},
        "machine": {**memory_status(), "ac_power": on_ac_power()},
        "argv": argv,
        "images": [],
    }
    staged = [P.sha256_file(p) for p in inputs]
    if staged != [f["sha256"] for f in order]:
        raise SystemExit("a staged input differs from its blob")
    save_json(run / "local_run.json", record, tries=10, say=say)
    if dry_run:
        say(f"[local] dry run: {run}\n[local] order: " + ", ".join(f"<image{f['new_n']}> {f['role']} {f['upload_name']}" for f in order))
        say("[local] transforms: " + "; ".join(transforms))
        say("[local] command: " + " ".join(f'"{a}"' if " " in a else a for a in record["argv"]))
        return run
    image = {"k": 1, "seed": seed, "attempts": []}
    record["images"].append(image)
    for attempt in range(1 + retries):
        say(f"[local] sd-cli ({engine}{', backend ' + backend if backend else ''}) {W}x{H}, {steps} steps, cfg {cfg}, seed {seed}, {threads} threads,"
            f" refs cap {refs_cap or 'model default'}, cache {cache_type} -> {run}")
        a = run_sd(argv, run / f"sdcli_{attempt + 1}.log", run / "progress.json", steps, measured=measured, stop=stop, priority=priority, say=say)
        a["log"] = f"sdcli_{attempt + 1}.log"
        image["attempts"].append(a)
        save_json(run / "local_run.json", record, tries=10, say=say)
        if a["exit_code"] == 0 and out_tmp.is_file():
            from PIL import Image
            with Image.open(out_tmp) as im:
                im.load()
                image["px"] = list(im.size)
            out_tmp.replace(out)
            image["output"] = out.name
            image["output_sha256"] = P.sha256_file(out)
            break
        if stop is not None and stop.is_set():
            break
    save_json(run / "local_run.json", record, tries=10, say=say)
    last = image["attempts"][-1]
    say(f"[local] {'DONE ' + str(out) if image.get('output') else 'NO PICTURE'}: exit {last['exit_code']}"
        + (f", stopped ({last['killed_by']})" if last["killed_by"] else "")
        + f", {last['elapsed_s'] / 60:.1f} min, phases {last['phases_s']}, s/step {last['s_per_step_median']},"
          f" peak working set {last['peak_working_set_gb']} GB, peak commit {last['peak_commit_gb']} GB")
    return run


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recipe", help="a recipe ref, e.g. pin_783485666539777055@v2")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("-W", type=int, default=768)
    ap.add_argument("-H", type=int, default=960)
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("-t", "--threads", type=int, default=4)
    ap.add_argument("--refs-cap", type=int, default=0, help="largest reference size in pixels; 0 = the model's default (no shrinking)")
    ap.add_argument("--cfg", type=float, default=1.0, help="guidance scale (1.0 = the official default for Qwen-Image-2.1)")
    ap.add_argument("--engine", choices=sorted(ENGINES), default="cpu", help="cpu, or vulkan (the Intel UHD iGPU)")
    ap.add_argument("--backend", default=None, help="sd-cli --backend, e.g. vulkan0 or te=cpu,diffusion=vulkan0")
    ap.add_argument("--te", choices=sorted(TE_SETS), default="int8", help="text encoder: int8 = the model's own companion, q4 = 4-bit GGUF")
    ap.add_argument("--cache-type", default="q8_0", help="the reference-image prefix cache type (f16, q8_0, q4_0)")
    ap.add_argument("--priority", choices=sorted(PRIORITY), default="below_normal", help="sd-cli's CPU priority (normal for a daytime trial)")
    ap.add_argument("--min-free-gb", type=float, default=0, help="wait until this much RAM is free before starting")
    ap.add_argument("--min-commit-gb", type=float, default=0, help="wait until Windows can commit this much more memory before starting")
    ap.add_argument("--wait-max-min", type=float, default=120, help="give up waiting for memory after this many minutes")
    ap.add_argument("--extra", nargs=argparse.REMAINDER, default=[], help="more sd-cli arguments, recorded as they are")
    ap.add_argument("--dry-run", action="store_true", help="stage the inputs and write the prompt and the command; run nothing")
    a = ap.parse_args()
    if not a.dry_run and (a.min_free_gb or a.min_commit_gb):
        t0 = time.time()
        while True:
            ms = memory_status()
            if ms["avail_gb"] >= a.min_free_gb and ms["commit_headroom_gb"] >= a.min_commit_gb:
                print(f"[local] memory ok: {ms}", flush=True)
                break
            if time.time() - t0 > a.wait_max_min * 60:
                print(f"[local] gave up after {a.wait_max_min:.0f} min: {ms}; top: {top_memory_users(6)}", flush=True)
                return 3
            print(f"[local] waiting for memory: free {ms['avail_gb']} GB (need {a.min_free_gb}), commit headroom {ms['commit_headroom_gb']} GB"
                  f" (need {a.min_commit_gb}); top: {top_memory_users(5)}", flush=True)
            time.sleep(60)
    run = generate(a.recipe, a.seed, a.W, a.H, a.steps, a.threads, a.refs_cap, a.cache_type, cfg=a.cfg, dry_run=a.dry_run, extra_args=a.extra,
                   priority=a.priority, engine=a.engine, backend=a.backend, te=a.te)
    rec = json.loads((run / "local_run.json").read_text(encoding="utf-8"))
    return 0 if a.dry_run or (rec["images"] and rec["images"][-1].get("output")) else 1


if __name__ == "__main__":
    sys.exit(main())
