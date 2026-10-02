"""Make a video with the Gemini web session (the Create-video tool, Gemini Omni): a real call, nothing mocked. Same Pro login as the images.

    .venv\\Scripts\\python.exe tools\\video_probe.py "a paper boat drifting across a puddle at dawn, no people"
    .venv\\Scripts\\python.exe tools\\video_probe.py "he turns toward the camera and smiles" --photo "D:\\FacecardResults\\x.jpg" --aspect portrait

Writes the clip and a record <stem>.json (credits before/after, the first reply, how long it took, whether the request was rewritten) into
.cache\\video_probe\\ (--out to change). The record is the evidence when no video comes back: Gemini's own words are in "text".
The credit meter is account-wide: run it with no other facecard job going if the cost matters.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / ".cache" / "video_probe"


async def run(a) -> dict:
    from session import authenticated_client
    from video import generate_video
    async with authenticated_client(verbose=False) as client:
        return await generate_video(client, a.prompt, Path(a.out), photos=a.photo, aspect=a.aspect, model=a.model, wait_s=a.wait,
                                    temporary=a.temporary, delete_chat=a.delete_chat)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt")
    ap.add_argument("--photo", action="append", default=[], help="a photo to seed the video (repeat the flag; the web page takes up to 5)")
    ap.add_argument("--aspect", choices=["landscape", "portrait"], default="landscape")
    ap.add_argument("--wait", type=float, default=900.0, help="seconds to wait for the clip after the request")
    ap.add_argument("--model", default=None, help="a model name or id from `facecard.py models`; default: the account's default (no model header)")
    ap.add_argument("--temporary", action="store_true", help="send as a temporary chat (may not be readable back; measured by this tool)")
    ap.add_argument("--delete-chat", action="store_true", help="delete the chat from the Gemini history after the clip is saved")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    from loguru import logger
    import session  # noqa: F401
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    rec = asyncio.run(run(a))
    print(f"record: {rec.get('record')}")
    return 0 if rec.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
