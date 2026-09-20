# nano-banana-facecard

Generate identity-consistent images of yourself via the actual Gemini web app
(gemini.google.com), reusing your Google AI Pro subscription's quota instead of
a billed API key. Built on [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API),
which authenticates as you using your browser session cookies.

**Heads up:** this drives gemini.google.com outside Google's official developer API.
It's not illegal, but it's unofficial/unsupported — Google could rate-limit or flag
heavy automated use, and the library can break when Google changes the site.

**Skills:** the full workflow is documented as two skills any agent on this machine can use.
- `skills/gemini-identity-gen/SKILL.md` — vault cookies, troubleshooting, running this tool. It
  ships **in this repo**, because it drives this repo's venv, prompts and reference photos. Edit
  it here. `~\.agents\skills\gemini-identity-gen` and `~\.claude\skills\gemini-identity-gen` are
  junctions pointing at this folder, so every agent picks up the change.
- `~\.agents\skills\scene-prompt-writer\SKILL.md` — writing the scene prompt text, including from
  a reference image. It stays global because it works with any identity-reference pipeline, not
  only this one (junctioned into `~\.claude\skills\scene-prompt-writer`).

On a new machine, recreate the junctions after cloning:

```
New-Item -ItemType Junction -Path "$HOME\.agents\skills\gemini-identity-gen" -Target "<repo>\skills\gemini-identity-gen"
New-Item -ItemType Junction -Path "$HOME\.claude\skills\gemini-identity-gen" -Target "<repo>\skills\gemini-identity-gen"
```

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
- `--scene-image`: now runs `replicate` on that photo (the prompt text is ignored).
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

## Reproduce a source photo with your face: `replicate`

Use this whenever there is a photo to reproduce (yours, or someone else's from Pinterest). It never redraws the photo.
The principle: **the AI does all the visual work and all the scene reading; code only copies pixels that must not change,
measures, and retries.** Nothing Gemini renders is altered by a heuristic.

```
.venv\Scripts\python.exe facecard.py replicate --scene "C:\path\photo.jpg"                 # auto zone
.venv\Scripts\python.exe facecard.py replicate --scene photo.jpg --force --count 1         # your own photo (benchmark)
.venv\Scripts\python.exe facecard.py replicate --scene photo.jpg --zone head+build         # opt-in body edit
```

What happens: a crop around the head (and any reflection of it) is cut from the full-resolution original; Gemini describes
the crop (head angle, expression, glasses, light) in a text call; Gemini edits the crop with that description in the
prompt; the **whole returned crop** is pasted back with a soft border at the crop edge, so face, hair, neck and light stay
consistent with each other; Gemini then judges source vs output (angle, glasses, seam, lighting, anything else changed).
Everything outside the crop is asserted identical to the source. The prompt asks for a flattering, relaxed expression rather than a copy of the source's (`attractiveness_note` in `facecard.json`, `--expression same` to copy it), a head the same size as the source's, and a window reflection stays in the same crop and the same call. When several candidates pass, Gemini chooses the better expression pair by pair (each pair in both orders, which matched the user's own verdict 4 of 4 times). A candidate that fails a check is retried, up to
`--max-attempts` (default 6) image calls, and what went wrong (the judge's own note, plus a sentence per failed check such as
"the face came out brighter than the photo") is written into the next prompt. Other copies of your face in the frame, such as a
window reflection, get their own tight crop and their own edit.

Each run writes `cand<N>.png` (lossless), `best.png` / `best.jpg` (or `not_passing_closest.jpg` when nothing passed),
`compare_head_<N>.jpg` (source | output | difference | crop border), `compare_full_<N>.jpg`, `run.json` and `run.log` to
`outputs/<timestamp>_replicate_<name>/`. The AI judge's answer is in both logs.

Code: `replicate.py` (the command), `composite.py` (crop paste, alignment check, drift measure), `identity.py` (photo
pool and scoring), `calibrate.py` (prints the numbers behind the thresholds). `segment.py` and `landmarks.py` remain for
measurement only; the paste no longer uses them.

Limits measured on 2026-09-20 (full detail in `skills/gemini-identity-gen/SKILL.md`): Gemini re-renders the face, so it
is close to but not pixel-exact with your real face; the identity score only separates clear matches from clear misses;
other people's bodies are not reshaped (the silhouette stays within 2 percent); and an earlier design that post-processed
Gemini's face (relight, grain, blur, mask cut-out) made results worse and was removed.

## Face restoration + scoring (optional)

`restore.py` runs generated images through [FaceFusion](https://github.com/facefusion/facefusion)
to pull the real face back over Gemini's drifted one, and `scorer.py` gives an objective ArcFace
identity-match score rather than judging by eye. It swaps with `inswapper_128`, restores expression
with LivePortrait on frontal poses, and runs no face enhancer by default (enhancers wipe out skin
texture). Each target's pose is detected first, and reference photos are picked from the matching
`pose_bins` set in `facecard.json`.

**Requires a separate local clone of FaceFusion.** It is upstream third-party code
(`facefusion/facefusion`, OpenRAIL-AS licensed), deliberately not bundled here: bundling would end
upstream updates and pull its licence over this repo. It also needs its own Python 3.12 venv, which
cannot share this repo's 3.14 venv because the two pin conflicting OpenCV builds.

Every location outside this repo is resolved in `paths.py`, in this order: an environment
variable, then a key in `facecard.json`, then a default.

| Location | Env var | `facecard.json` key | Default |
|---|---|---|---|
| FaceFusion clone | `FACEFUSION_DIR` | `facefusion_dir` | `../facefusion`, a sibling of this repo |
| Reference photos | `FACECARD_REFS_DIR` | `refs_dir` | `D:\Downloads\FaceCard_Originals` |
| secure-vault skill | `SECURE_VAULT_DIR` | `vault_dir` | `~/.agents/skills/secure-vault` |

Check that everything resolves, and get the exact clone command if FaceFusion is missing:

```
.venv\Scripts\python.exe facecard.py check     # paths, then Gemini authentication
.venv\Scripts\python.exe paths.py              # paths only, no network
```

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

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache License, Version 2.0](LICENSE-APACHE) at
your option.
