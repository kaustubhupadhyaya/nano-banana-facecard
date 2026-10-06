# nano-banana-facecard

Identity-consistent photos of one person through the actual Gemini web app (gemini.google.com), using a Google AI Pro subscription's
quota instead of a billed API key. Built on [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API), which authenticates with the
browser session's cookies.

**Heads up:** this drives gemini.google.com outside Google's official developer API. Google can rate-limit or flag heavy automated use,
and the library breaks when the site changes.

Agents working in this repo: read [`AGENTS.md`](AGENTS.md) first (the consistency rule, the stages, where things live).

## The method is a file: recipes and staged runs

Gemini's image model cannot be seeded, so the same request gives a new picture every time. What this repo keeps constant is the
**method**: a goal picture's request is frozen once as a **recipe** (`recipes/<collection>/<NN>-<title>/v<N>.json`: every reference photo by
role with its sha256 and the reason it was chosen, the inventory, and a lock holding the exact prompt, the files in order and the model).
A recipe version is never edited; a change is a new version that says why it exists.

```
.venv\Scripts\python.exe facecard.py recipe new --goal <goal.jpg> --prompt <route.txt> --inventory <inventory.json> --replace-subject \
                                                --model e6fa609c3fa255c0 --samples 2 --because "<why this version>"
.venv\Scripts\python.exe facecard.py run <goal>@v1 --dry-run        # free: proves the request is the recipe's, byte for byte
.venv\Scripts\python.exe facecard.py run <goal>@v1 --samples 2      # the real run
.venv\Scripts\python.exe facecard.py diff <runA> <runB>             # what differs: request, code, outcomes
.venv\Scripts\python.exe facecard.py recipe bump <goal>@v1 --inventory <new.json> --because "<what failed>"
.venv\Scripts\python.exe facecard.py recipe show <goal>             # versions, request hashes, track record
```

Every run goes through the same eight numbered stages, and each leaves its evidence in the run folder:
`01_method` (recipe copy, integrity, drift, environment), `02_inputs` (pinned goal, the references sheet), `03_request` (exact prompt and
files, request hash), `04_credits` (account, credit guard), `05_generate` (one record per Gemini call), `06_measure` (pose gate, identity,
light), `07_review` (audit sheets), `08_result` (ranking, export). A self-contained `report.html` shows all of it on one page and is also
published to the review folder. The exact bytes of every file a recipe sends live in a content-addressed store outside the repo.

`facecard.py gen --goal ...` takes the same flags for exploration (it runs as an ad-hoc recipe through the same stages); a good exploratory
run becomes a recipe version with `facecard.py recipe import-run <run> --because "..."`.

## Redo your own photo: `replicate`

For a photo of yourself, `replicate` edits a crop around the head and pastes it back into the untouched original, so background, clothes,
body and framing cannot drift. Gemini reads the crop, edits it with your reference photos, and judges source against output; code only copies
pixels, measures and retries (nothing Gemini renders is post-processed).

```
.venv\Scripts\python.exe facecard.py replicate --scene "C:\path\photo.jpg"
```

Details, measured limits and the review loop are in the two skills in [`skills/`](skills/) (`gemini-identity-gen`, `facecard-session`),
which every agent on the machine reads through junctions:

```
New-Item -ItemType Junction -Path "$HOME\.agents\skills\gemini-identity-gen" -Target "<repo>\skills\gemini-identity-gen"
New-Item -ItemType Junction -Path "$HOME\.claude\skills\gemini-identity-gen" -Target "<repo>\skills\gemini-identity-gen"
```

## One-time setup: session cookies in the vault

Two cookies identify the Gemini session, `__Secure-1PSID` and `__Secure-1PSIDTS`. Both go into the local DPAPI vault
(`C:\Users\Admin\.agents\skills\secure-vault`), never into a plaintext file and never through chat.

1. In the browser profile signed in to the Google AI Pro account, open https://gemini.google.com.
2. DevTools (F12) → Application → Storage → Cookies → `https://gemini.google.com`; double-click each Value cell (the table clips long values) and copy it.
3. Run the VS Code task **Facecard: re-enter cookies**, or from the secure-vault folder:
   `python vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account"`
4. Paste `__Secure-1PSID` into the `gemini-cookies-psid` entry's Password and `__Secure-1PSIDTS` into the `gemini-cookies` entry's Password.

`session.py` reads both in-process (`vault.get_secret`); values are never printed, logged or written to disk in plaintext (run logs redact
them). A rotated `__Secure-1PSIDTS` is written back to the vault automatically. If `facecard.py check` reports an auth failure, repeat the steps.

## Paths and checks

Every location outside the repo resolves in `paths.py`: an environment variable, then a key in `facecard.json`, then a default.

| Location | Env var | Default |
|---|---|---|
| Reference photos | `FACECARD_REFS_DIR` | `D:\Downloads\FaceCard_Originals` |
| Blob store (exact bytes of every recipe) | `FACECARD_BLOBS_DIR` | `D:\FacecardData\blobs` |
| Run reports | `FACECARD_REVIEW_DIR` | `D:\FacecardReview` |
| Passed pictures | `FACECARD_RESULTS_DIR` | `D:\FacecardResults` |
| YOLO pose gate interpreter | `FACECARD_YOLO_PYTHON` | `D:\VisionModels\yolo\.venv\Scripts\python.exe` |
| FaceFusion clone (optional face restore) | `FACEFUSION_DIR` | `../facefusion` |
| secure-vault skill | `SECURE_VAULT_DIR` | `~/.agents/skills/secure-vault` |

```
.venv\Scripts\python.exe facecard.py check      # paths, then Gemini authentication
.venv\Scripts\python.exe paths.py               # paths only
.venv\Scripts\python.exe facecard.py models     # the account's model ids
```

FaceFusion (used by `restore.py`) runs from its own clone and Python 3.12 venv and is not bundled (its licence and OpenCV build differ).

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache License, Version 2.0](LICENSE-APACHE) at your option.
