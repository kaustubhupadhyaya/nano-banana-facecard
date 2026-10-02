"""Gemini web-app video ("Create video", Gemini Omni) through the cookie session: no billed API, same Pro credits as images.

How the web page asks for a video (captured 2026-10-01 from gemini.google.com with the Create-video tool on; measurements in skills\\gemini-identity-gen\\SKILL.md, "Video through this session").
The StreamGenerate request is the plain chat request with four differences, which `video_tool` applies to the one request the library sends:
  - the message content (slot 0) gets a tool element at index 9: [null x6, [[null, null, null, ASPECT]]]   ASPECT 1 = landscape 16:9, 2 = portrait 9:16
  - slot 49 = 11 (a plain chat has 0; deep research 1), slot 54 = [], slot 55 = [[16]] without a photo / [[17]] with one (what 17 means is
    measured in `tools\\video_probe.py` runs, not assumed here)
  - the model header's capability list carries 16: [4,5,6,8] -> [4,5,6,8,16,4,5,6,8,16], as the web page sends it
The reply comes back at once as text ("I'm generating your video. This could take a few minutes..."); the clip is attached to that chat turn
later. `generate_video` therefore sends, then polls `read_chat(cid)` until the turn carries a video, then saves it.
"""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from gemini_webapi.constants import MODEL_HEADER_KEY, Endpoint

from session import credits_left, describe_usage, usage_of

ASPECT = {"landscape": 1, "portrait": 2}
CAPABILITIES = [4, 5, 6, 8, 16, 4, 5, 6, 8, 16]
SLOT_TOOL_MSG, SLOT_MODE, SLOT_55 = 9, 49, 55
MODE_VIDEO = 11


def rewrite_form(data: dict, aspect: str, has_photo: bool) -> dict:
    """The StreamGenerate form body with the Create-video tool switched on. `at` (the session token) is passed through untouched."""
    outer = json.loads(data["f.req"])
    inner = json.loads(outer[1])
    msg = list(inner[0])
    msg += [None] * (SLOT_TOOL_MSG + 1 - len(msg))
    msg[SLOT_TOOL_MSG] = [None] * 6 + [[[None, None, None, ASPECT[aspect]]]]
    inner[0] = msg
    inner[SLOT_MODE] = MODE_VIDEO
    inner[54] = []
    inner[SLOT_55] = [[17 if has_photo else 16]]
    outer[1] = json.dumps(inner, separators=(",", ":"))
    return {**data, "f.req": json.dumps(outer, separators=(",", ":"))}


def rewrite_headers(headers: dict) -> dict:
    h = dict(headers)
    raw = h.get(MODEL_HEADER_KEY)
    if raw:
        parts = json.loads(raw)
        if len(parts) > 8 and isinstance(parts[8], list):
            parts[8] = list(CAPABILITIES)
        h[MODEL_HEADER_KEY] = json.dumps(parts, separators=(",", ":"))
    return h


@contextmanager
def video_tool(client, aspect: str = "landscape", has_photo: bool = False):
    """While active, the client's chat requests are sent with the Create-video tool on. Yields a dict whose 'sent' counts the requests changed:
    0 afterwards means the library used a different HTTP session than the one patched (e.g. it re-logged in), and the answer was plain chat."""
    if aspect not in ASPECT:
        raise ValueError(f"aspect must be one of {sorted(ASPECT)}")
    sess = client._live_client
    original = sess.stream
    state = {"sent": 0}

    def patched(method, url, **kw):
        if str(url) == str(Endpoint.GENERATE) and isinstance(kw.get("data"), dict) and "f.req" in kw["data"]:
            kw["data"] = rewrite_form(kw["data"], aspect, has_photo)
            if "headers" in kw:
                kw["headers"] = rewrite_headers(kw["headers"])
            state["sent"] += 1
        return original(method, url, **kw)

    sess.stream = patched
    try:
        yield state
    finally:
        try:
            del sess.stream
        except AttributeError:
            sess.stream = original


async def _turn_with_video(client, cid: str):
    """(model text, [videos]) of the newest model turn of the chat, or (None, [])."""
    hist = await client.read_chat(cid)
    if not hist or not hist.turns:
        return None, []
    for turn in hist.turns:
        if turn.role == "model" and turn.model_output:
            return turn.model_output.text or "", list(turn.model_output.videos or []) + list(turn.model_output.media or [])
    return None, []


async def generate_video(client, prompt: str, out_dir: Path, *, photos: list[str] | None = None, aspect: str = "landscape",
                         model: str | None = None, wait_s: float = 900.0, poll_s: float = 15.0, temporary: bool = False,
                         delete_chat: bool = False, stem: str | None = None, say=print) -> dict:
    """Ask Gemini for a video, wait for it, save it. Returns a record {ok, path, cid, seconds, credits, text, ...}; never raises on a refusal
    (the refusal text is the record's 'text'). Raises UsageLimitExceededError when the window is spent."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = stem or f"video_{stamp}"
    rec: dict = {"stamp": stamp, "prompt": prompt, "photos": list(photos or []), "aspect": aspect, "ok": False,
                 "start": credits_left(client)}
    say(f"[Video] before: {describe_usage(usage_of(client))}")
    t0 = time.time()
    with video_tool(client, aspect, bool(photos)) as hook:
        out = await client.generate_content(prompt, files=list(photos) if photos else None, model=model, temporary=temporary)
    rec["request_rewritten"] = hook["sent"]
    cid = (out.metadata or [""])[0]
    rec.update({"cid": cid, "first_reply": out.text, "reply_seconds": round(time.time() - t0, 1), "videos_in_reply": len(out.videos)})
    say(f"[Video] reply after {rec['reply_seconds']} s (request rewritten: {hook['sent']}): {out.text[:160]!r}")
    if not hook["sent"]:
        rec["error"] = "the Create-video request was not sent (the library used another HTTP session); nothing was generated"
        return rec
    videos = list(out.videos or [])
    text = out.text
    while not videos and time.time() - t0 < wait_s and cid:
        await asyncio.sleep(poll_s)
        try:
            text, videos = await _turn_with_video(client, cid)
        except Exception as e:  # a poll can fail once while the turn is still being written
            say(f"[Video] poll failed ({type(e).__name__}); trying again")
            continue
        say(f"[Video] {int(time.time() - t0)} s: {'video ready' if videos else 'still generating'}")
        if text and not videos and "generating your video" not in text.lower() and "generat" not in text.lower()[:60]:
            rec["error"] = f"Gemini answered without a video: {text[:300]}"
            break
    rec["text"] = text
    rec["seconds"] = round(time.time() - t0, 1)
    if videos:
        saved = await videos[0].save(path=str(out_dir), filename=f"{stem}.mp4", verbose=False)   # a suffix keeps the library from prefixing a timestamp and hash
        rec["saved"] = saved
        rec["path"] = (saved or {}).get("video")
        rec["ok"] = bool(rec["path"]) and rec["path"] != "206"
    elif "error" not in rec:
        rec["error"] = f"no video after {int(wait_s)} s"
    await asyncio.sleep(3)
    try:
        await client._fetch_usage_info()
    except Exception:
        pass
    rec["end"] = credits_left(client)
    if rec["start"] is not None and rec["end"] is not None:
        rec["credits"] = rec["start"] - rec["end"]
    say(f"[Video] {'saved ' + str(rec.get('path')) if rec['ok'] else 'FAILED: ' + str(rec.get('error'))}; window dropped {rec.get('credits')} "
        f"(account-wide); {describe_usage(usage_of(client))}")
    if delete_chat and cid:
        try:
            await client.delete_chat(cid)
        except Exception as e:
            say(f"[Video] chat {cid} not deleted: {type(e).__name__}")
    rec["record"] = str(out_dir / f"{stem}.json")
    Path(rec["record"]).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return rec
