"""Local vision-language eye: a vision model served by llama.cpp's llama-server on this laptop (Vulkan on the Intel iGPU), asked to compare the
original photo with the edited one. Free and offline: the user's photos never leave the machine.

    .venv\\Scripts\\python.exe research\\vision_eye\\bench.py qwen_local

The eye starts the server itself when it is not running, and restarts it once when it dies mid-benchmark. That happened 2026-09-24 after 19 pictures
with 4 slots and 8192 context, after Windows had filed a memory-leak report for it; now 1 slot and 4096 context.
EYE_MODEL / EYE_MMPROJ choose another model; EYE_SERVER another address.

Why side by side: the user's verdict "my face alone has been lasso-ed and edited in" is relative to the original. Both research surveys
(2026-09-24) found small vision models weak at spotting edits from one picture, and better with the original next to the result and short
yes/no questions. On another man's photo the face is replaced ON PURPOSE, so the eye is told so and "same man" is not asked.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

SERVER = os.environ.get("EYE_SERVER", "http://127.0.0.1:8093")
MODEL = os.environ.get("EYE_MODEL", r"D:\VisionModels\qwen3.5-4b\Qwen3.5-4B-Q4_K_M.gguf")
MMPROJ = os.environ.get("EYE_MMPROJ", r"D:\VisionModels\qwen3.5-4b\mmproj-F16.gguf")
EXE = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "WinGet" / "Packages" / "ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe" / "llama-server.exe"
LOG = Path(os.environ.get("TEMP", ".")) / "vision_eye_llama_server.log"
TIMEOUT = 900

ASPECTS = (
    "face_pasted: true if in {img} his face looks cut out and pasted onto his head, as if the face alone was lassoed and edited in: the face at "
    "a different angle or tilt than his hair, the top of his head, his ears or his neck, or a different size, sharpness, grain or light than "
    "the rest of the photo. false if the face and head look like one real photograph.\n"
    "head_fits_body: true if his head in {img} is the natural size and angle for his neck and shoulders.\n"
    "doubled: true if {img} shows any doubled or ghost outline, a second hairline, a second ear or a smeared collar.\n")
PAIR_OWN = (
    "Image 1 is an original phone photo of a man. Image 2 is the same photo after an AI edited his face. Look closely at image 2 the way the "
    "man himself would, comparing it with image 1. Answer ONLY with the JSON object.\n" + ASPECTS.format(img="image 2") +
    "same_man: true if image 2 shows the same man as image 1.\n"
    "reason: one short sentence on what looks wrong in image 2, or an empty string.")
PAIR_FOREIGN = (
    "Image 1 is a photo of a man. In image 2 an AI replaced his face and head with a different man's, on purpose; who he is does not matter. "
    "Look closely at image 2 and judge only whether the new head looks like it really belongs in this photo, comparing with image 1. Answer "
    "ONLY with the JSON object.\n" + ASPECTS.format(img="image 2") +
    "same_man: true.\n"
    "reason: one short sentence on what looks wrong in image 2, or an empty string.")
SINGLE = (
    "This is a phone photo of a man in which an AI edited his face. Look closely the way the man himself would. Answer ONLY with the JSON "
    "object.\n" + ASPECTS.format(img="the photo") +
    "same_man: true.\n"
    "reason: one short sentence on what looks wrong, or an empty string.")
SCHEMA = {
    "type": "object",
    "properties": {"face_pasted": {"type": "boolean"}, "head_fits_body": {"type": "boolean"}, "doubled": {"type": "boolean"},
                   "same_man": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["face_pasted", "head_fits_body", "doubled", "same_man", "reason"],
}


def _healthy() -> bool:
    try:
        with urllib.request.urlopen(SERVER + "/health", timeout=5) as r:
            return b'"ok"' in r.read()
    except Exception:
        return False


def ensure_server() -> None:
    """Start llama-server when nothing answers, and wait until the model is loaded (about 100 s on this laptop)."""
    if _healthy():
        return
    port = SERVER.rsplit(":", 1)[1]
    cmd = [str(EXE), "-m", MODEL, "--mmproj", MMPROJ, "--port", port, "-ngl", "99", "-np", "1", "-c", "4096", "--temp", "0",
           "--image-max-tokens", "1024", "--reasoning", "off"]
    log = open(LOG, "ab")
    subprocess.Popen(cmd, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0))
    for _ in range(120):
        time.sleep(5)
        if _healthy():
            return
    raise RuntimeError(f"llama-server did not become ready; see {LOG}")


def _data_url(path: str) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def ask(images: list[str], prompt: str) -> dict:
    content = [{"type": "image_url", "image_url": {"url": _data_url(p)}} for p in images] + [{"type": "text", "text": prompt}]
    body = {"messages": [{"role": "user", "content": content}], "temperature": 0, "max_tokens": 200,
            "response_format": {"type": "json_schema", "json_schema": {"name": "verdict", "schema": SCHEMA}}}
    for attempt in range(2):
        ensure_server()
        try:
            req = urllib.request.Request(SERVER + "/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                out = json.loads(r.read())
            return json.loads(out["choices"][0]["message"]["content"])
        except (ConnectionError, urllib.error.URLError):
            if attempt:
                raise
            time.sleep(5)   # the server died; ensure_server() starts it again
    raise RuntimeError("unreachable")


def judge(case: dict) -> dict:
    v = case.get("views", {})
    foreign = case.get("kind") == "foreign"
    if v.get("src_context") and v.get("context"):
        a = ask([v["src_context"], v["context"]], PAIR_FOREIGN if foreign else PAIR_OWN)
        mode = "pair-foreign" if foreign else "pair"
    elif v.get("context"):
        a = ask([v["context"]], SINGLE)
        mode = "single"
    else:
        return {"flag": None, "score": None, "why": "no view"}
    checks = [("face_pasted", False), ("head_fits_body", True), ("doubled", False)] + ([] if foreign or mode == "single" else [("same_man", True)])
    bad = [k for k, want in checks if a.get(k) is not want]
    return {"flag": bool(bad), "score": float(len(bad)), "why": f"[{mode}] {', '.join(bad) or 'clean'}: {a.get('reason', '')}", "answer": a}
