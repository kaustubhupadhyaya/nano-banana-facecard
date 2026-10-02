---
name: facecard-session
description: >-
  Run a working session on the nano-banana-facecard model (the user's "my version of any photo" pipeline): session-start cleanup (keep only the
  best pictures, their metadata and the user's reviews, delete the rest), applying the image creation to photos in a resumable batch, run reports,
  the angle-reference library, and the end-of-session review loop (numbered pictures with complete file paths, scores -2..+2 with defect tags and
  "keep", recorded into facecard.json, FEEDBACK_LOG.md and FEEDBACK_MATRIX.xlsx). Use at the start and end of any facecard session, and when the
  user says "apply our image creation", "run it on these photos", "open the images generated this round", "give complete file locations",
  reviews pictures, or asks what is waiting for review.
---

# facecard session

Repo `C:\Users\Admin\GitHub\nano-banana-facecard`, Python `.venv\Scripts\python.exe` (run everything from the repo root). The pipeline itself (how
`replicate` edits a head crop, its gates and measured limits) is documented in the `gemini-identity-gen` skill; this skill is the session routine.

## 0. The best-picture checklist (the user's rule, 2026-09-26; applies to every step below)

- **No picture is called best until it passes [`BEST_CHECKLIST.md`](../../BEST_CHECKLIST.md)** (repo root). That is 30 numbered checks, from the user's own complaints, done by eye:
  - open the picture next to its source, head zoomed in, whole picture seen;
  - record the result with `tools\best_check.py "<picture>" --source "<source>" --fail <n,...> --na <n,...> --note "..."`.
- **One failed item means NOT BEST, and so does one item that can't be verified.** Never present such a picture as best, and don't copy it to `D:\Downloads\AI me`. Rework it in a `/loop` with `/think-again`: name the failed item, find its cause, fix that, make the next version, and never repeat a fix on the DO NOT RETRY lists in `FEEDBACK_LOG.md`.
- The pipeline's `best.jpg` / `best.png` (and `facecard.py gen`'s `best.jpg`) is only a candidate until the checklist passes.
- **Posture and position (items 12, 14, 29, 30) are measured before they are judged** (the user, 2026-09-27: these mistakes kept getting past a by-eye check; root causes in FEEDBACK_LOG section 12).
  - Run: `D:\VisionModels\yolo\.venv\Scripts\python.exe tools\pose_compare.py "<goal>" <renders>` (`gen --goal` runs it automatically).
  - Its limits are fixed. A FAIL is a FAIL; never call its numbers "guides", and never loosen a limit without the user.
  - Judge these items on its overlay `<render>_pose.jpg`, limb by limb (legs and feet too) against the goal, never against the previous version.
- **Never write a POSE from my own reading alone.** Save the goal's measurement first (`pose_compare.py "<goal>" --save-goal`). The POSE text must agree with its facts (stance, knee angles, torso lean, hand heights), and `--pose-points` adds them to the prompt.

- **Loop until perfect (the user, 2026-10-01):** a goal is not finished until a picture passes all 30 items or the user accepts one. After every wave run
  `tools\goal_status.py --open`, read the goal's section of `FEEDBACK_LEDGER.md`, change only the request section that controls the failed item, and start the
  next wave (all open goals in parallel, sized to `tools\quota.py`, scheduled after the credit reset when the window is empty). Never stop at a failed attempt;
  details in the gemini-identity-gen skill, section "Loop until perfect".

## 0b. Route G: the user's role-based single prompt (the default for a goal picture, 2026-09-26)

- **Command:** `.venv\Scripts\python.exe facecard.py gen --subject me --goal "<goal>" --prompt "<sections.txt>" --count 4`
- **References by role:**
  - images 1-4 are FACE references (studio photos chosen by the goal's head pose);
  - image 5 is the BODY reference (`IMG_6923 Copy.JPG`);
  - image 6 is the SHOULDER AND ARM reference (`IMG_0440_Original.jpg`);
  - plus the ORIGINAL PHOTO when the goal is his own photo (ArcFace decides; `--goal-as-image yes|no` overrides).
- **Prompt:** the identity sentence, then FACE and BUILD (`facecard.json` `subject_profiles.me.face_text` / `build_text`), then the sections file, then the style line (`prompts\role_template.txt`).
- **The sections file** holds POSE / WARDROBE / SCENE / LIGHT / CAMERA, written from the goal with the scene-prompt-writer skill. The goal picture of another man is never sent: sent photos leak their model's skull, jaw and neck, and public figures are refused.
- **Each render:** `tools\review_sheet.py --goal "<goal>" <renders>`, then the 30 items (`tools\best_check.py`).
- **Inventory first** (the user, 2026-09-28: "make them all go right at the first go"): before the first render of a goal, write `.cache\inventories\<goal>.json`. Every visible element is HIS / GOAL / REMOVE, and each HIS item says what the goal shows and what replaces it, with a reference cut from his own photos (`tools\ref_sheet.py`).
  - Run `gen --replace-subject --inventory <json>`.
  - Check with `tools\inventory_check.py` at full zoom.
  - Fix a leftover object with an objects-mode inventory plus `tools\region_edit.py` on a crop with no head in it.
- **Controls built into the request** (2026-09-27; the checklist is designed in, not only checked after):
  - `--pose-points`: the goal's measured joints in Gemini's `[y, x]` 0-1000 format, plus the computed facts;
  - `--layout-image`, with `--pose-image`: the goal's boxes and skeleton as a sketch;
  - `--goal-as-image goal`: the goal itself sent as the GOAL IMAGE, its man explicitly excluded (the user asked to try this);
  - `--replace-subject`: the goal sent as the PHOTO TO EDIT, its man replaced by him from the references;
  - `--prop PATH::LABEL`: his own objects, such as his CB350 (`.cache\props\`).
- **On a fail:** change only the section that controls the failed item.
- **Fallbacks,** only after 3 rounds that cannot pass an item: the replicate edit, FaceFusion swap, or the free-GPU head swap (see the plan).

## 1. Start of the session (always, before anything else)

1. `tools\session_prune.py` (dry run: prints what would be kept and deleted), then `tools\session_prune.py --apply`. The user's standing rule
   (2026-09-23): at session start keep only each run's picture (`best.*` or `not_passing_closest.jpg`), its `run.json` / `run.log`, and every file
   the user reviewed or the records name; delete the rest (candidates, raw returns, sent crops, compare sheets). It never touches runs written in
   the last 15 minutes, the best versions in `D:\Downloads\AI me`, `.cache\synthetic_refs`, `.cache\ref_poses.json`, source photos or patches. It
   also marks the session start, which `pending_review.py` and `run_report.py` use.
2. `tools\match_best_versions.py --record`: picks up pictures the user copied into `D:\Downloads\AI me` by hand (matched to their run by pixel
   content, recorded with md5 in `facecard.json` `best_versions`; such a photo is returned unchanged by `replicate` unless `--force`).
3. Status in three lines: `git status --short` (uncommitted pipeline changes are experiments waiting for the user's approval), `tools\quota.py`
   (credits left in the 5-hour window, reset time; `--watch` keeps a live line and `.cache\quota.json`), and `tools\pending_review.py --all` (unreviewed pictures from earlier sessions: ask for
   their reviews first).

## 2. Applying the image creation

- "Apply our image creation" means: the default pipeline on every photo given, no modes or flags, no extra diagnostic reruns; show the pictures
  and plain numbers, then end the turn.
- `tools\batch_run.py "<photo1>" "<photo2>" ...` (run it in the background). Resumable (state in `.cache\batch_state.json`, `--state` for a
  separate list), waits for the quota reset and repeats the photo, stops when the cookies fail. Full output of each run: `.cache\batch_logs\`.
- Cookies expired ("Authentication failed" / "Missing cookies"): the user refreshes them in the vault popup, never in chat:
  `python C:\Users\Admin\.agents\skills\secure-vault\vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account"` (the exact
  hints are in `session.py` `REFRESH_COMMAND`). Give it as a YOUR TURN block.
- Angle library: `angle_refs.py --dry-run` lists which head poses (turn -90..90 x level / looking down / looking up) have no reference of him;
  `angle_refs.py` renders them from his studio photos and keeps a render only if identity >= 0.60 and the AI-read pose is within 15 degrees.
  If it stops on the quota (exit 3), run it again after the reset; kept renders stay cached in `.cache\synthetic_refs\`.

## 3. Reports

- `tools\run_report.py` (this session's runs), `--last N`, or run folders by name: every attempt's identity (and the source's), similarity to
  the source, size, movement, light, neck gap, sharpness, clothes SSIM, the judge's flags, placements, the references sent, and the result path.
- When the user asks to "open" or "read" pictures: use the Read tool on each file and give every complete absolute path. The picture of a run is
  `outputs\<run>\best.jpg`, or `not_passing_closest.jpg` when nothing passed; never present a head crop (`raw\c*_head_raw.jpg`) as a result.
- **Results folder (end hook, 2026-10-01):** only PASSED pictures (checklist BEST, or accepted by the user) are copied, flat, to
  `D:\FacecardResults\<collection>_<NN>_<title>_v<N>.jpg` by `tools\export_results.py` (called by `best_check.py` each time it records a checklist or an approval, and at the end of every
  gen / replicate run; see the gemini-identity-gen skill). When the user accepts a picture the checklist failed ("pencil in mouth pass v1 - sufficient"), run
  `tools\best_check.py "<picture>" --user-approved "<their words>"`. Name a new goal in `results_names.json` before its first run, and give the user the
  results-folder paths for passed pictures.

## 4. End of the session: reviews

1. `tools\pending_review.py`: the new pictures, numbered, with complete paths and key numbers (queue saved to `.cache\review_queue.json`).
   Open each with the Read tool, then list the paths for the user in a YOUR TURN block.
2. Ask for reviews in the user's format (chosen 2026-09-23), one line per picture:
   ```
   <n> a<-2..+2> i<-2..+2> [keep] [tags] [other:"..."] ["note"]      e.g.  1 a+2 i+1 keep
   <n> skip                                                                2 a-1 i0 hair light
   ```
   a = attractiveness, i = identity, both against the source photo (-2 much worse, 0 the same, +2 much better). Tags: `hair light size angle
   expression pasted blur glasses clothes`. `keep` = it becomes the user's best version of that photo.
3. Write the user's reply to `.cache\review_input.txt` and run `tools\record_review.py --file .cache\review_input.txt`: records each review in
   `facecard.json` `reviews`, appends to `FEEDBACK_LOG.md` (section Reviews), and for `keep` copies the picture into `D:\Downloads\AI me` and
   records it as a best version. If the user answers in free words instead, translate them into this format, show the lines, and record them.
4. Rebuild the workbook: `research\feedback_matrix\build_feedback_matrix.py` (optional `FM_CACHE=<file>` to cache the image measurements) ->
   `FEEDBACK_MATRIX.xlsx`; reviews become rows automatically (`fm_rows4.py`).

## 5. Before changing the pipeline

- Save a checkpoint first: `git diff > .cache\patches\<name>_UNCOMMITTED.patch` and a copy of `replicate.py`. Changes stay uncommitted until the
  user approves the pictures they make; commit and push only when the user asks.
- A threshold changes only with the user's approval; say which gate changed and why. Before any live run, replay a new gate or rule on the saved
  runs: it must keep every best version and reviewed "perfect" picture (the sharpness gate was restricted to far faces because a perfect kayak
  picture measures 8.3x).
- Real end-to-end runs only (no unit tests, no stubs). Never commit photos: `outputs\`, `.cache\`, `models\` are ignored and the repo is public.

## Where things are

`outputs\<stamp>_replicate_<photo>\` runs; `.cache\feedback\` older evidence; `D:\Downloads\AI me\` the user's best versions (`facecard.json`
`best_versions`); `.cache\synthetic_refs\` rendered angle references; `.cache\ref_poses.json` the AI's pose reading of every reference;
`FEEDBACK_LOG.md` every verdict and what it taught; `FEEDBACK_MATRIX.xlsx` everything ranked with paths; `.cache\patches\` rollback points.
