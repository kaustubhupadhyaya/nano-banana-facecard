"""The Gemini session cookies from the signed-in google-1 Chrome profile (the user, 2026-10-09, asked how a dead session should be restarted:
"From your browser").

Why: the session lives on two Google cookies. __Secure-1PSID is long-lived; __Secure-1PSIDTS is renewed. Until 2026-10-08 each run renewed it
and saved the newest value to the vault (session.py), so no one had to paste cookies. That night several long-waiting runs renewed the same
session in parallel, Google rate-limited the renewals (HTTP 429), a stale value was saved over a good one, and the session died. This module
restarts it without the user: it opens the persistent automation profile (%USERPROFILE%\\.secrets\\profiles\\google-1, signed in to Google)
over Chrome's debugging port, off-screen, loads gemini.google.com so Google refreshes the session, and reads the two cookies IN-PROCESS.
Values are returned to the caller only: never printed, logged, passed on a command line or written to the vault's password fields.
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import paths

NAMES = ("__Secure-1PSID", "__Secure-1PSIDTS")


def _bs():
    sys.path.insert(0, str(paths.vault_dir()))
    import browser_session
    return browser_session


def _http(url: str, method: str = "GET", timeout: float = 5.0) -> dict | list | None:
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _cdp(ws_url: str, method: str, params: dict | None = None, timeout: float = 20.0) -> dict:
    from curl_cffi.requests import Session
    s = Session()
    ws = s.ws_connect(ws_url)
    try:
        ws.send_json({"id": 1, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = ws.recv_json()
            if msg.get("id") == 1:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method}: {msg['error'].get('message')}")
                return msg.get("result") or {}
        raise TimeoutError(f"CDP {method}: no answer")
    finally:
        with contextlib.suppress(Exception):
            ws.close()


def from_browser(label: str = "google-1", url: str = "https://gemini.google.com/app", settle: float = 10.0, say=print) -> dict | None:
    """{'__Secure-1PSID': ..., '__Secure-1PSIDTS': ...} from the profile, or None (signed out, no browser, no answer). Reuses the profile's
    browser when its debugging port is already up (another tool may be using it); otherwise starts it off-screen and closes it afterwards."""
    bs = _bs()
    port = bs.port_for(label)
    started = None
    if not bs._cdp_alive(port):
        args = [str(bs.browser_exe()), f"--remote-debugging-port={port}", f"--user-data-dir={bs.profile_dir(label)}", "--no-first-run",
                "--no-default-browser-check", "--disable-session-crashed-bubble", "--hide-crash-restore-bubble",
                "--window-position=-32000,-32000", "--window-size=1200,800", "about:blank"]
        started = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 40
        while time.time() < deadline and not bs._cdp_alive(port):
            time.sleep(0.5)
        if not bs._cdp_alive(port):
            say(f"[session] the {label} browser profile did not open its debugging port")
            _stop(started)
            return None
    target = None
    try:
        target = _http(f"http://127.0.0.1:{port}/json/new?{url}", method="PUT")
        time.sleep(settle)            # Google's own page refreshes the session cookies on load
        ws_url = (_http(f"http://127.0.0.1:{port}/json/version") or {}).get("webSocketDebuggerUrl")
        if not ws_url:
            return None
        cookies = _cdp(ws_url, "Storage.getCookies").get("cookies") or []
        found = {}
        for c in cookies:
            if c.get("name") in NAMES and str(c.get("domain", "")).lstrip(".") == "google.com":
                found[c["name"]] = c.get("value")
        if all(found.get(n) for n in NAMES):
            say(f"[session] Gemini session cookies read from the {label} browser profile")
            return found
        say(f"[session] the {label} browser profile has no Google session cookies (signed out?)")
        return None
    except Exception as e:
        say(f"[session] reading the {label} browser profile failed: {type(e).__name__}")
        return None
    finally:
        if target and target.get("id"):
            with contextlib.suppress(Exception):
                _http(f"http://127.0.0.1:{port}/json/close/{target['id']}")
        if started is not None:
            _stop(started, port)


def _stop(proc, port: int | None = None) -> None:
    """Close the browser this module started GRACEFULLY first (Browser.close flushes the profile's cookie store, so the session Google just
    refreshed is kept on disk), and force it only if it does not exit."""
    if port is not None:
        with contextlib.suppress(Exception):
            ws_url = (_http(f"http://127.0.0.1:{port}/json/version") or {}).get("webSocketDebuggerUrl")
            if ws_url:
                _cdp(ws_url, "Browser.close", timeout=5)
        with contextlib.suppress(Exception):
            proc.wait(timeout=15)
    if proc.poll() is None:
        with contextlib.suppress(Exception):
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, timeout=15)
