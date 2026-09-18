# nano-banana-facecard

Generate identity-consistent images of yourself via the actual Gemini web app
(gemini.google.com), reusing your Google AI Pro subscription's quota instead of
a billed API key. Built on [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API),
which authenticates as you using your browser session cookies.

**Heads up:** this drives gemini.google.com outside Google's official developer API.
It's not illegal, but it's unofficial/unsupported — Google could rate-limit or flag
heavy automated use, and the library can break when Google changes the site.

**Device-wide skills:** the full workflow is documented as two skills any agent on this machine can
use — update these files, not a copy in this repo, when the workflow changes:
- `C:\Users\Admin\.agents\skills\gemini-identity-gen\SKILL.md` — vault cookies, troubleshooting,
  running this tool (junctioned into `~\.claude\skills\gemini-identity-gen`)
- `C:\Users\Admin\.agents\skills\scene-prompt-writer\SKILL.md` — writing the scene prompt text,
  including from a reference image (junctioned into `~\.claude\skills\scene-prompt-writer`)

## One-time setup: session cookies in the vault

Two cookies identify your Gemini session: `__Secure-1PSID` and `__Secure-1PSIDTS`.
Both go into the local DPAPI vault (`C:\Users\Admin\.agents\skills\secure-vault`),
never into a plaintext file, never through chat.

1. Open the browser profile that's logged into your Google AI Pro account, go to
   https://gemini.google.com, confirm you're signed in.
2. DevTools (F12) → **Application** → **Storage → Cookies** → `https://gemini.google.com`.
3. For each cookie, **double-click its Value cell** (this reveals the full string —
   the table view visually clips long values) and copy it.
4. Run the VS Code task **"Facecard: re-enter cookies"**, or from
   `C:\Users\Admin\.agents\skills\secure-vault`:
   ```
   python vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account"
   ```
5. In the popup:
   - `gemini-cookies-psid` entry → paste `__Secure-1PSID` into **Password**
   - `gemini-cookies` entry → paste `__Secure-1PSIDTS` into **Password**
   - Save each.

`session.py` reads these two fields in-process at run time (`vault.get_secret(...)`) —
values are never printed, logged, or written to disk in plaintext. When the library
rotates your session, the new `__Secure-1PSIDTS` is written to `gemini-cookies.rotated`
automatically (not to `password`, which stays yours to set only via the popup).

`__Secure-1PSIDTS` rotates periodically. If `facecard.py check` reports auth failure,
repeat steps 1-5 to refresh both entries.

## Usage

```
.venv\Scripts\python.exe facecard.py check                                    # verify session
.venv\Scripts\python.exe facecard.py models                                   # list available models
.venv\Scripts\python.exe facecard.py gen --prompt prompts/studio_test.txt --count 1
```

Or from VS Code: **Terminal → Run Task** → "Facecard: generate" / "Facecard: check session" /
"Facecard: re-enter cookies".

- `--prompt`: scene text, or a path to a `.txt` file (see `prompts/identity_lock.txt` for the
  identity-lock preamble that's automatically prepended — only write the scene description
  after it, and keep it positive-only: describe pose/outfit/setting/lighting, never the face).
- `--scene-image`: optional path to a photo/screenshot whose pose, outfit, and framing should
  be matched (identity still comes from the pinned refs, not this image).
- `--count`: how many variations to generate (each is an independent request against the same
  pinned refs — outputs are never fed back in as new references).
- `--model`: override the model id from `facecard.json` for one run.

Reference photos are pinned in `facecard.json` (`refs`, under `refs_dir`) — currently 6 sharp,
varied-angle shots from `FaceCard_Originals`. Edit that list to change them.

Outputs land in `outputs/<timestamp>_<slug>/v<n>_<i>.jpg` (the extension follows the real format
Google serves, usually JPEG), with a `run.json` recording the exact prompt, ref filenames, model,
and any errors (no cookies). Images come back at the Gemini app's native size (about 1 MP, e.g.
768×1376 for 9:16) with the app's visible Gemini sparkle mark, same as downloading from the app.

`facecard.json` pins `"model": "e6fa609c3fa255c0"` (the app's "3.1 Pro", which renders images with
Nano Banana Pro). Model ids can change when Google updates the app; if `gen` fails with an unknown
model error, run `facecard.py models` and update the id.

Prompt files included: `prompts/studio_test.txt` (plain studio portrait) and
`prompts/mountain_tank_top.txt` (alpine trail scene).

## Face restoration + scoring (optional)

`restore.py` runs generated images through [FaceFusion](https://github.com/facefusion/facefusion)
(inswapper_128 + gfpgan_1.4) to pull the real face back over Gemini's drifted one, and `scorer.py`
gives an objective ArcFace identity-match score rather than judging by eye.

**Requires a separate local clone of FaceFusion** — `restore.py` expects it at
`C:\Users\Admin\GitHub\facefusion` (`FACEFUSION_DIR`, top of the file). This is upstream
third-party code (`facefusion/facefusion` on GitHub), not bundled in this repo — clone it
yourself and install its own requirements before using `restore.py`.

## Notes

- Which underlying image model actually serves the request is decided by Google's app;
  run `facecard.py models` to see what's available on this account and pin one in
  `facecard.json` if you want to force it.
- Quota is whatever your Gemini app account gets under your Pro subscription — same daily
  limits as using the app by hand.
- If a generation drifts on identity, don't feed the drifted output back in as a new
  reference — regenerate from `facecard.json`'s pinned refs again.
- `session.py` redirects `gemini_webapi`'s cookie cache (which it otherwise writes as
  plaintext JSON to `%TEMP%\gemini_webapi\`) to a per-run temp directory that's deleted after
  every command, so no plaintext session file is left on disk.
