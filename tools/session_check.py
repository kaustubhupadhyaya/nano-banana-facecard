"""Is the Gemini session signed in right now? tools/wave.py asks before every run (2026-10-10: at 20:20 every sign-in was refused for about ten
minutes, and the wave would have started run after run into the same refusal).

    .venv\\Scripts\\python.exe tools\\session_check.py        -> exit 0 and the credit window when signed in, exit 5 when not

It signs in the way a run does (session.authenticated_client: the vault's cookie pairs, then the signed-in google-1 browser profile), with no
renewal and no image call. Only the account status and the credit window are printed, never a cookie.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SIGN_IN_FAILED = 5      # runner.SIGN_IN_FAILED


async def check() -> int:
    import session as S
    try:
        async with S.authenticated_client() as client:
            usage = ""
            try:
                usage = S.describe_usage(S.usage_of(client))
            except Exception as e:
                usage = f"credit window not read ({type(e).__name__})"
            print(f"signed in: {client.account_status.name}; {usage}", flush=True)
            return 0
    except Exception as e:
        print(f"not signed in: {type(e).__name__}: {str(e).splitlines()[0][:200]}", flush=True)
        return SIGN_IN_FAILED


if __name__ == "__main__":
    sys.exit(asyncio.run(check()))
