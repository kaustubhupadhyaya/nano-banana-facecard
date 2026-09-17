"""
Authenticated GeminiClient factory, reading cookies from the local DPAPI vault.

Vault layout:
    gemini-cookies-psid.password   __Secure-1PSID    (user-entered only, via vault GUI)
    gemini-cookies.password        __Secure-1PSIDTS   (user-entered only, via vault GUI)
    gemini-cookies.rotated         latest rotated __Secure-1PSIDTS (written by this module)

gemini_webapi persists cookies to a plaintext JSON cache file under its cookie-cache
directory (keyed by the raw __Secure-1PSID value) whenever it rotates the session or
closes the client. That directory is redirected per-run to an isolated temp folder via
GEMINI_COOKIE_PATH and deleted afterwards, so no plaintext cookie file is left on disk.
"""

import shutil
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, r"C:\Users\Admin\.agents\skills\secure-vault")
import vault

from gemini_webapi import GeminiClient
from gemini_webapi.constants import AccountStatus

PSID_LABEL = "gemini-cookies-psid"
PSIDTS_LABEL = "gemini-cookies"
REFRESH_COMMAND = (
    'python vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account" '
    '--hint "gemini-cookies-psid=Password = value of the __Secure-1PSID cookie (starts with g.a000)" '
    '--hint "gemini-cookies=Password = value of the __Secure-1PSIDTS cookie (starts with sidts-)"'
)


class AuthError(RuntimeError):
    pass


def _psidts_candidates() -> list[str]:
    candidates = []
    for value in (vault.get_secret(PSIDTS_LABEL, "rotated"), vault.get_secret(PSIDTS_LABEL, "password")):
        if value and value not in candidates:
            candidates.append(value)
    return candidates


@asynccontextmanager
async def authenticated_client(verbose: bool = False):
    """Yield an authenticated GeminiClient, or raise AuthError with no secret in the message."""
    secure_1psid = vault.get_secret(PSID_LABEL, "password")
    psidts_candidates = _psidts_candidates()

    if not secure_1psid or not psidts_candidates:
        raise AuthError(
            "Missing cookies in vault. Need gemini-cookies-psid.password (__Secure-1PSID) "
            "and gemini-cookies.password (__Secure-1PSIDTS). From the secure-vault folder run:\n"
            f"  {REFRESH_COMMAND}"
        )

    cookie_tmp_dir = Path(tempfile.mkdtemp(prefix="gemini_webapi_cookies_"))
    client: GeminiClient | None = None
    try:
        import os

        os.environ["GEMINI_COOKIE_PATH"] = str(cookie_tmp_dir)

        last_error: Exception | None = None
        for secure_1psidts in psidts_candidates:
            candidate = GeminiClient(secure_1psid, secure_1psidts)
            try:
                await candidate.init(timeout=120, verbose=verbose)
            except Exception as e:
                last_error = e
                continue

            if candidate.account_status == AccountStatus.AVAILABLE:
                client = candidate
                break
            else:
                await candidate.close()
                last_error = AuthError(f"account_status={candidate.account_status.name}")

        if client is None:
            raise AuthError(
                "Authentication failed with all known cookies (session likely expired). "
                f"Underlying: {type(last_error).__name__ if last_error else 'unknown'}\n"
                f"Refresh from the secure-vault folder: {REFRESH_COMMAND}"
            )

        yield client

    finally:
        if client is not None:
            try:
                fresh_psidts = None
                for cookie in client.cookies.jar:
                    if cookie.name == "__Secure-1PSIDTS":
                        fresh_psidts = cookie.value
                        break
                await client.close()
                if fresh_psidts and fresh_psidts not in psidts_candidates:
                    vault.set_value(PSIDTS_LABEL, "rotated", fresh_psidts)
            except Exception:
                pass

        shutil.rmtree(cookie_tmp_dir, ignore_errors=True)
