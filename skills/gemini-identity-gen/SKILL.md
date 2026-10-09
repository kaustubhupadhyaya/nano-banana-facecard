---
name: gemini-identity-gen
description: Redo the user's own photo with their face without changing anything else in it (replicate), or generate identity-consistent images of them from scratch, including a scene copied from someone else's photo or a Pinterest pin (scene-prompt-writer, then a recipe run), via their Google AI Pro Gemini web session (no billed API). Use for "generate a photo of me", "replicate this photo with my face", "facecard", "nano banana [pro]", "face restore", or anything mentioning __Secure-1PSID/__Secure-1PSIDTS cookies. For writing scene prompt text for from-scratch generation, use the scene-prompt-writer skill.
---

# gemini-identity-gen

Device-wide skill. It ships inside the repo it drives, `C:\Users\Admin\GitHub\nano-banana-facecard`,
at `skills/gemini-identity-gen/`; the copies under `~\.agents\skills` and `~\.claude\skills` are
junctions to that folder, so edit it in the repo. Any agent on this machine (Claude Code, Pi,
OpenCode) should use this skill rather than re-deriving the approach or creating new vault entries.

Run `facecard.py check` first: it reports whether FaceFusion, the reference photos and the vault
all resolve, and prints the exact fix for anything missing (paths are set in `paths.py`).

## Which command

| You have | Use | Why |
|---|---|---|
| The subject's own photo to redo with his own face | **a `replicate/1` recipe**: `facecard.py recipe new --method replicate --goal <photo> --character me@v1 --because "..."`, then `facecard.py run <goal>@vN` | Edits a crop of the full-resolution original and pastes it back. Background, clothes, body and framing cannot drift. Route G refuses his own photo (stage 01, exit 2): on 2026-10-07 it redrew the whole kayak photo at ~1 MP with a ~77 px face. An OLDER photo of his redone in his current look takes two passes (the user, 2026-10-08: "body and hair rework needed since the current physique and face has changed"): `--zone build --current-look` (his body), then `--from-picture <pass-A picture> --current-look` (his head: current cut, lean face, size up to 1.10 for the beard). |
| Someone else's photo, a Pinterest/Instagram pin or a screenshot, as a style to copy | **scene-prompt-writer** (reference mode), an element inventory, then a **recipe**: `facecard.py recipe new ... --character me@v1 --because "..."` and `facecard.py run <goal>@vN` | His head on another man's photo keeps that man's body (silhouette within 2%), about 15% of results were acceptable, and it is catfishing. The skill turns the pin into a structured scene with his own traits; the recipe freezes the method so every run sends the same request. |
| No source photo, a scene described in words or a style template | scene-prompt-writer (template mode), then `gen --subject <name>` | Draws a new image. Everything is regenerated, so expect drift outside the face. |

`gen --scene-image` now just runs `replicate`; the prompt text is ignored, because the photo is the scene. Leave it off for
someone else's photo. The subject's own photo is always redone with `replicate`: describing it in words and regenerating
redrew the whole frame, changed the pose, clothes, background and physique, and dropped glasses (measured 2026-09-19/20).
For someone else's photo, scene-prompt-writer's spec and its drift-five check exist to close exactly those gaps.

## Consistency: recipes and staged runs (the user, 2026-10-07)

Every goal picture is made from a **recipe** version (the frozen method: inputs + a locked request) through the **8 fixed stages** of
`facecard.py run`, each leaving its evidence in the run folder and on one report page in `D:\FacecardReview`. The rules, the stages, the
commands and where things live are in the repo's `AGENTS.md`: read it before generating. In short: change the method only with
`recipe bump --because "<the user's words / the failed item>"`, prove a version with `run --dry-run`, debug with `facecard.py diff <runA> <runB>`.
`gen --goal ...` still works for exploration (it runs as an ad-hoc recipe through the same stages); adopt a good run with `recipe import-run`.

**The same man in every picture (the user, 2026-10-08):** every new recipe takes `--character me@vN` (`characters/me/`): the same face and body photos for every goal and a description read from them (AGENTS.md, "The same man in every picture"). Before it, 79 runs used 11 face sets, a January arms photo with fuller arms beside the slim September body photo, and a text that called his face leaner than his photos show. Stage 06 records his face-fullness and build measures against the character's band (record-only); checklist items 31 and 32 are judged on the stage-07 character sheet.

## Loop until perfect (the user, 2026-10-01: "when you already know exactly which one is failing, then why did you stop?")

**Never stop at a failed attempt. A goal is finished only when a picture of it passes all 35 items of BEST_CHECKLIST.md (or the user accepts one with
`best_check.py --user-approved`).** Knowing which items fail is the start of the next attempt, not a reason to report and wait. The loop, per goal and
for all open goals at once (parallel processes, one per goal; `tools\goal_status.py --open` lists them and exits 1 while any is open):

0. **Ask what is wrong, in the user's own words, before optimising any number** (when a picture of the goal was rejected). Pin 5 cost about 10 attempts and 3,000
   credits chasing the identity score when the complaint was lighting ("face seems lasso-ed in"); the best-ArcFace sample (0.73) was the rejected one. Record the
   words in the ledger (`best_check.py --note`). `tools\goal_status.py --open --next` then shows, per open goal, the lint of its newest inventory, the model that
   really passed the pose gate most and the canary command.
1. **Freeze, prove, canary, production.**
   - `tools\inventory_lint.py <inventory or recipe>` (free): errors on a missing photo to edit or more than 10 files; warns on a cropped goal with no FRAMING keep
     line, a keep line saying "exactly as in the PHOTO TO EDIT" about the head or arms of the goal's own photo, a build item with no measure, a steeply bowed head
     with no "deeper than the goal" line.
   - **Freeze** the method: `facecard.py recipe new --goal ... --prompt ... --inventory ... --replace-subject --character me@v1 --samples 2 --because "..."` (or
     `recipe bump <goal>@vN --<what changes> --because "..."`); **prove** it free with `facecard.py run <goal>@vN --dry-run` (stage 03: request = lock).
   - **Canary = 2 samples on the production model** (`facecard.py run <goal>@vN --samples 2`), only for a NEW version. The pose gate passes about 25-35% of
     samples, so one sample fails a good recipe about 70% of the time, and a Flash canary does not predict Pro (pin 6: Flash returned the pin man, Pro replaced
     him). Scale up only after at least one pose pass.
   - **Production** = more runs of the SAME version: `tools\wave.py <spec.json>` with `{"recipe": "<goal>@vN", "samples": 2, "repeat": N}` jobs (`--dry-run`
     first; `--after-reset` or `--at HH:MM` to wait). `--face-refs @clean_studio` (or `@clean_profile_right`) in a bump selects a named reference set from
     `facecard.json` for one goal; it is an A/B judged by the user's eye, never a global change, and the ArcFace pool (`refs`) is not touched.
2. **Audit every picture that passed the pose gate** against all 35 items at full zoom (`tools\audit_views.py`, `body_sheet.py`, the pose json numbers);
   record it with `tools\best_check.py ... --fail ... --note "what was wrong" --right "what went right"`. A pass is exported automatically.
3. **Diagnose** with `tools\goal_status.py`: it prints the items that failed most, what was already tried (model and inventory variant) and the fix the
   ledger's lessons attach to each failed item. Read the goal's section of `FEEDBACK_LEDGER.md` first: **never repeat a fix that already failed**.
4. **Change only the request section that controls the failed item**, as a new recipe version: a new inventory variant `..._vN.json`, then
   `recipe bump <goal>@vN --inventory <it> --because "<failed item + the user's words>"` (it prints exactly what changed in the request). Switch model when two
   versions on one model failed the same item, and go back to 1. Several versions of one goal run in parallel; `facecard.py diff` compares their runs.
5. **Pace by credits, never by giving up.** The credit guard (`credit_guard.py`, stage 04 of every run) does the sizing: before a run spends anything it reads a FRESH meter
   (the cached reading lags: it once said 1,141 left when 96 were), subtracts what the other runs in flight have reserved (`.cache\inflight\<pid>.json`; 120 per Flash
   image, 150 per Pro image (260 until 2026-10-08: both chat models now hand the picture to the same image tool), `credit_guard` in `facecard.json`) and waits until the images fit with a margin of 150. At most 4 generations run at once (a burst of 6
   returned no image for 5 of them and was charged ~160 credits anyway). `--wait-max SECONDS` (default 21600) bounds the wait, `--no-wait` exits with code 3 and
   generates nothing, `--no-guard` skips the check (use it only when the user said to). When the window is empty, `tools\wave.py <spec> --after-reset` waits for the
   reset and starts all open goals in parallel (arm a Monitor on `.cache\wave_<tag>.done`); keep auditing in the meantime. Credits run out; the loop does not end.
   A run's own credit total is exact only for a run that was alone: overlapping runs share the account-wide meter.

**The only reasons to stop:** every goal is DONE; the user says stop; or a blocker only the user can clear (Gemini cookies expired: give the YOUR TURN
vault block; a request Gemini refuses on every sample; a checklist item the user must rule on, such as identity in the 0.20-0.52 gray zone after at
least three Pro samples at different seeds, shown with the compare sheet). In all three cases keep every OTHER goal running.

**Lessons that finished the hard goals (2026-10-01, FEEDBACK_LEDGER.md has the evidence; try these before inventing a new fix):**
- **Head bow / turn below the goal's number:** renders land about 0.12 short of the bow the request asks for. Ask for MORE than the goal (pin 9: nose 1.1 eye-distances below the eye line when the goal is 0.87) and state it first and last in the keep list. A reference of him at the same pose (`.cache\synthetic_refs`) did nothing.
- **The pin man's build keeps coming back:** a build sentence alone is ignored on goals where his arms fill the frame. What works: the VISIBLE CONSEQUENCE of a slim body (gaping armholes, loose sleeves, collarbone and ribs showing), and for the hardest cases a TWO-STAGE route: stage 1 = a render that already has the right head, posture and size; stage 2 = `gen --replace-subject --body-only` with the inventory's `photo_to_edit` set to that render and the slimming written with EXPLICIT AMOUNTS (arms a third thinner, shoulders a fifth narrower, loose polo). Without amounts the edit changes nothing.
- **Never write 'exactly as in the PHOTO TO EDIT' about the head or arms of the goal's own photo** (it hands the pin man back) and never add a FRAMING sentence that says 'never closer' on a close crop (same result). In a stage-2 edit of HIS OWN render it is correct.
- **Hidden or bowed faces cannot be scored** (ArcFace 0.0-0.3 on a face that is his): judge hair, beard, jaw, nose against his references at zoom, report the number, pass item 21 only by eye, and flag it for the user to confirm.
- **Parallel runs of the same goal** are safe now (unique run folders, atomic mkdir); give each run its own log tag.

**The user's verdict on pin 5 and pin 6 (2026-10-01) and what it changed in the audit:** both pictures passed 30/30 by my eye and the user called both wrong. Cause, measured: (1) the hair and beard were the pin man's (long loose curls, patchy stubble) instead of his references' (tight curls, SHORT FADED SIDES with ear and scalp visible, a FULL DENSE beard); (2) pin 5's face was lit 1.7x brighter than the pin's (103 vs 61: in the pin the hair shades the whole upper face). A profile or bowed face cannot be scored by ArcFace, so these were passed by eye, loosely. From now on every audit runs `tools\audit_views.py <label> <goal> <render> <run folder>`: it puts the render's head beside ALL his reference heads (black and white when the goal is), and prints FACE LIGHT (render vs goal, limit 0.77-1.30) and FACE vs NECK (face brightness over neck brightness against the goal's, tolerance 0.12: the old pin 5 picture read 1.20 against the pin's 0.82, the "lasso-ed in" signature; `gen` computes the same numbers into `run.json` as `light` and ranks the pose-gate passers with the light in range first, never rejecting on it): judge items 19 and 28 on that head row, hair and beard separately, and never pass them from the whole-picture view. Write his haircut and beard into every inventory as explicit geometry (tight curls ~6-8 cm on top, sides short and faded, ear and scalp visible; full dense beard from the sideburns along the whole jaw, neat edges), and for a goal whose face is shaded, name the shade as a keep line (the hair falls forward over the brow, the face is not brighter than the white tee).

**What the loop may never do to finish faster:** loosen a gate, a limit or a checklist item; call a picture best that failed an item; count a picture the
pose gate passed only because the pin's own man came back unchanged (diff to the goal under about 10, face still the pin man's) as a result; skip the
audit because a number looks good. A fixed limit that a picture misses by a hair (size 1.08 against 1.07) is a FAIL: regenerate.

**Progress report each time something passes or a wave ends, in two lines per goal** (what passed or what still fails and what the next wave changes);
never a closing summary that offers to continue: the next wave is already running or scheduled.

## End hook: results export (the user, 2026-10-01; only passed pictures, one flat folder)

Pictures that PASS are copied out of the repo's `outputs\<run>\` into one flat results folder outside it. Nothing else is copied, and there are no
subfolders: the file name alone says what a picture is.

```
D:\FacecardResults\                  paths.results_dir(): FACECARD_RESULTS_DIR env var, results_dir in facecard.json, or this default
    motorcycle-outfit-men_02_porch-reading-smoking-grey-tee_v1.jpg        <collection>_<NN>_<title>_v<N>.jpg
    motorcycle-outfit-men_02_porch-reading-smoking-grey-tee_v2.jpg
    motorcycle-outfit-men_06_shirtless-pencil-in-mouth-bw_v1.jpg
```

- **PASSED** = the picture's checklist (`tools\best_check.py`, BEST_CHECKLIST.md) says BEST, or **the user accepted it**. When the user says a picture is
  good enough ("pencil in mouth pass v1 - sufficient"), record their words with
  `tools\best_check.py "<picture>" --user-approved "<their words>"`: the failed items stay on record, the verdict becomes `BEST (user-approved)`, and the
  picture is exported. Anything else (failed items, no checklist yet, pose-gate failures) is never copied; a picture whose checklist is re-recorded with
  failed items is withdrawn (its copy is deleted).
- **When it runs:** `tools\export_results.py` is called by `best_check.py` each time it records a checklist or an approval (this is what brings a
  picture over), and at the end of every `facecard.py gen` / `replicate` run. Nothing needs to be run by hand;
  `tools\export_results.py [<run> ...] [--dry-run]` does it manually and is idempotent.
- **`vN`** counts the passed versions of one goal in the order they were generated (v1, v2, ...). A number is never reused or renumbered. Which run and
  candidate a file came from is in the hidden `.export_index.json` in that folder; the names do not need it.
- **A picture that already qualified elsewhere** (an archived run, the user's `D:\Downloads\AI me`) is brought in with
  `tools\export_results.py --import "<picture>" --goal-key <goal stem>`; it needs its BEST / user-approved checklist next to it, like any other.
  The user wants every goal of a board represented by its best picture (2026-10-01: "populate them if they are already present elsewhere").
- **An approval can be withdrawn:** when the user rejects a picture they accepted before, record the checklist again without `--user-approved`,
  with their words in `--note` and the items they named in `--fail`; the hook deletes its copy from the results folder.
- **Name every new goal in `results_names.json` before its first run** (goal picture stem -> `collection`, `number`, `title`, in the user's words).
  A goal that is not listed is named `misc_<stem>_vN`.
- The copies are COPIES: `outputs\` keeps its run folders (the session-start prune may later delete candidates there).
- This is not the user's best-versions folder: `D:\Downloads\AI me` is still only for pictures the user marks `keep`, and nothing reads the results folder back.
- **When you hand pictures to the user, give the paths in the results folder** for the passed ones, and the `outputs\` path only for work in progress.
- **Feedback ledger (the user, 2026-10-01): pictures that fail are not kept, so their lessons are.** The same hook writes `FEEDBACK_LEDGER.md` /
  `feedback_ledger.json` (repo root, text only): ONE ENTRY FOR EVERY GENERATED PICTURE, passed or not, with its result, identity score, pose-gate detail,
  **what was wrong** and **what went right**. Entries are never removed, so they outlive the files in `outputs\` (the session-start prune deletes those).
  Every `best_check.py` call must therefore say both: `--note "what was wrong"` and `--right "what went right"` (a lesson learned is written into the
  prompt of the next attempt, not only into the ledger). Pictures that failed the pose gate and were never checked get an automatic entry from `run.json`.
  Before regenerating a goal, read that goal's section of the ledger so a fix that already failed is not tried again.

## replicate (the default workflow)

**Principle (round 3, 2026-09-20): the AI does all the visual work and all the scene reading; code only copies pixels that
must not change, measures, and retries. Nothing Gemini renders is altered by a heuristic.** Round 2 layered a face-shaped
mask, a relight, grain, softening and a landmark warp on top of Gemini's crop, and results got worse (the kayak photo fell
from 0.58 to 0.23) because those steps understood the picture less well than Gemini did. They were removed, not tuned.

```powershell
python facecard.py replicate --scene "C:\path\photo.jpg"                # auto: own photo -> face, someone else -> head
python facecard.py replicate --scene photo.jpg --force --count 1        # own photo (benchmark: the output should stay you)
python facecard.py replicate --scene photo.jpg --zone head+build        # opt-in body edit, see limits below
```

Options: `--zone auto|face|head|head+build`, `--source auto|own|foreign`, `--glasses same|yes|no` (default `same`
= keep what the photo shows), `--look any|curly|short`, `--expression auto|none|"text"` (`none` skips the AI scene reading),
`--count N` (candidates that must PASS, default 2), `--max-attempts N` (ceiling on Gemini image calls, default 6), `--force`.

How it works:
1. Scores the source face against the user's photo pool to decide own vs foreign (a score in 0.20-0.50 is a gray zone: a
   small or turned face scores low even when it is the user, so the log says to pass `--source own|foreign`).
2. Cuts a crop from the FULL-RESOLUTION source around the head, tightened so the face keeps its own pixels inside the
   1024 px sent. Any other copy of the face in the frame (a window reflection) is included in the SAME crop.
3. **Gemini reads the crop** (text call, no image quota, model `vision_model` in `facecard.json`): head turn and tilt,
   gaze, glasses, hair, light, how bright the face is, reflection present. It reads the source expression too but that is NOT
   copied into the prompt (copying it produced "lips slightly parted" and an open laugh, both reviewed as bad).
4. **Gemini edits the crop** with 3 to 4 head crops of the user (nearest in head shape, never the source itself). Two frontal
   anchor references are added only when Gemini read the head as turned less than 65 degrees. The prompt asks for the
   **attractiveness policy** (`attractiveness_note` in `facecard.json`: at his best, calm confident eyes, relaxed closed-lip smile or
   calm focused look, never tense or awkward; `--expression same` copies the source instead), the head **including the hair exactly
   the size of the source's, never larger**, a jaw and neck as clean as the source (no extra fold), and exactly the exposure, colour
   and grain of the photo. A window reflection stays in the SAME crop and the SAME call.
5. The returned crop is pasted back with a wide soft border at the crop edge. Never pasted: Gemini's sparkle watermark and any pixels
   an alignment warp had to invent. Pixels outside the crop are asserted identical to the source.
6. **Gemini judges** source vs output crop (text call). Code measures identity score, head size and position (of the face the
   pipeline is editing, not of a reflection in the same crop), drift outside the heads, and the light on the face.
7. A candidate that fails a hard gate is retried, with what went wrong fed into the next prompt. If several candidates pass, **Gemini
   picks the better expression pair by pair, each pair in both orders**. The order that chooses `best.png` is: the AI's expression
   wins, then the identity band (accept > uncertain) only as a tiebreak, then the identity number. (The band used to come first; in
   stained-glass run 151934 that let an almost untouched candidate, similarity 0.96 to the source, beat the one the AI and the user
   both preferred. Below 0.52 the score cannot tell good from bad, so it must not outrank the AI's comparison.) If none pass, the
   candidate with the fewest problems is saved as `not_passing_closest.jpg` for the user's eye.

Gates — a candidate that fails any is `invalid` and retried, never quietly accepted:

| Gate | Limit | Source |
|---|---|---|
| pixels changed outside the crop | 0 | asserted on the saved PNG |
| returned crop lines up with the source (ECC on the outer ring) | ecc >= 0.80, scale within 20%, shift <= 30% | good returns ecc 0.99+, scale 1.000, shift < 0.003; a wrongly framed return 0.53 / 1.05 / 0.30; re-framed returns of 6-12% still register at ecc 0.94-0.99 and are warped. Widening further was tested and gains nothing: two table-tennis returns at scale 0.799 (ecc 1.000) still fail the size gate once aligned (head 1.19x and 1.36x the source) |
| returned aspect ratio | within 3% of the crop | Gemini sometimes returns another framing |
| drift inside the crop away from the heads (clothes, background) | mean diff <= 10, SSIM >= 0.80 | good 1.3-3.7 / 0.95-0.996; a wrong return 54.5 / 0.35 |
| head size and position vs source (face box) | own photos 0.85-1.15, foreign photos 0.95-1.04 (PROVISIONAL, from one review: a head at 1.054 was "too big"); shift <= 0.12 head widths | Gemini returns heads at 0.87-1.21 of the source |
| face light vs the source face (own photos only) | LAB colour distance dE <= 14 | PROVISIONAL: outputs the user called fine 12.2 and 5.5, the one he called worse 16.5 |
| AI judge, hard | same head angle, glasses present in both or in neither (frame-shape differences do NOT count: that wording rejected good candidates twice), no ghost or overlapping face, no seam, lighting consistent, nothing else changed | Gemini looking at both crops. The ghost question caught the flagged Pinterest output twice and raised 0 false alarms on 4 outputs he called perfect; it MISSED the flagged kayak "three faces" one (recall is partial) |

Warnings only (never fail a candidate): judge says the expression differs, the judge gave no usable answer.

Reading a run (`run.log` / `run.json`): `score` = mean of the user's 3 most similar pool photos. `gt_sim` = similarity to
the source face itself, meaningful only for own photos. `shape_dist` (head shape vs source, landmark based) is a
measurement in the log, not a gate. Verdicts: `accept` / `uncertain` / `reject` / `invalid`. The limits are in
`facecard.json` and were **approved by the user on 2026-09-20** ("yes go ahead", shown these exact numbers):
`identity_thresholds` (hard reject < 0.20, accept >= 0.52, own photo if the pool score is >= 0.40) and `gates`
(`light_de_max` 14, own photos only; `size_own` 0.85-1.15; `size_foreign` 0.95-1.04). `light_de_max` rests on two of his
judgements and `size_foreign` on one, so those two stay **provisional**: re-check them against his next reviews before
trusting them. A missing key falls back to the built-in default in `replicate.py`.

## Do not rebuild (measured worse, 2026-09-20)

`composite.py` still contains `relight`, `match_grain`, `match_sharpness`, `match_exposure` and the landmark warp in
`replicate.py` history. They are unused on purpose. Each made the face darker, softer or noisier than Gemini's own
render and produced the "sticker" look the user complained about. So did cutting the face out along a BiSeNet/ATR
mask: the mask cannot see thin glasses, mislabels dark curly hair, and the seam along the jaw is what looked pasted.
Also unreliable as gates: 2dfan4 landmarks (failed on 3 of 5 photos; heatmap confidence is not a reliability measure and
YuNet's 5 points fail on profiles), which is why angle, expression and light are read by Gemini, not derived from them.
If a result looks wrong, retry the generation or read the AI judge's note; do not post-process Gemini's pixels.

## What the AI judge can and cannot see (measured 2026-09-20 against the user's own verdicts)

- **Rating one image's expression does not work:** the user's "awkward" kayak and his "perfect emotion" kayak both got 6/10 with the same
  generic sentence. **Comparing two images does:** the AI picked the one he preferred 4 of 4 times (both orders, 2 repetitions). So expression is
  used for choosing between candidates, never as an absolute gate.
- **Head size cannot be judged by the AI:** asked for head width as a percentage of shoulder width it read his "too big" Pinterest head as smaller
  (43 vs 45), and asked which head is larger it just noticed the hair differed. Head size is therefore a geometric gate on the face box, and the
  gate is provisional.
- **A "double chin" the user reported was in his own photo:** `c1_head_send.png` is the crop SENT to Gemini, byte-identical to the source
  (mean difference 0.0). The jaw check is a warning, not a gate, and is unvalidated.
- Two of the user's flagged outputs (round 2, before this pipeline) could not be re-judged because their runs did not record a crop.

## Measured limits (2026-09-20). Do not claim more than this.

- **The identity score is decisive only at the extremes.** The user's own photos score 0.26-0.88 against each other,
  outputs the user confirmed good 0.53-0.68, drifted outputs 0.23-0.58, a different man 0.11. Between 0.20 and 0.52
  it cannot tell "him, poorly rendered" from "someone similar". Report the number, show the compare sheet, and let the
  user judge the gray zone. Never call an image "holds identity" from a score alone.
- **Gemini re-renders the face, it does not copy it.** Even in the best case the output face matches the source face at
  gt_sim ~0.66-0.69 (real same-session frames are 0.85-0.93), and expression can soften.
- **The AI is not infallible either.** On the kayak photo the scene reading called an open-mouth smile a closed-mouth
  smile, and the judge (a second call) caught the drift as a warning. Two readings are more reliable than one, not
  perfect. The user's eye is the final judge.
- **Physique of other people's photos is NOT reshaped.** `head+build` re-renders the torso but the silhouette stays
  within 2 percent of the source, even with `--build strong`, and it can drop clothing details such as an undershirt
  collar. That is why `head` is the default for foreign photos. On the user's own photos the body is never touched.
- **Gemini answers with text when its image quota is spent** ("I can create more images as soon as your limit resets");
  that is detected and stops the batch rather than retrying. The judge occasionally answers "I seem to be encountering
  an error"; it is retried once.

## Quota meter (2026-10-01): see it before the wall, not at it

The web app charges compute credits, not requests: **2,400 per 5-hour window and 48,384 per week** on this Pro account, about 64-86 credits per
image, 1-2 per text call (FEEDBACK_LOG section 13). The numbers are Gemini's own Settings -> Usage Limits page, read through one text RPC that costs
no image credits. `usage_percentage` is percent USED (measured: 114 credits left = 95% used).

- **Live:** `.venv\Scripts\python.exe tools\quota.py --watch` (every 60 s, `--every 30` for faster) prints one line,
  `tier PRO: 5h 114 left (95% used), resets 06:31 in 0h09m | week 32,876 left (32% used)`, and writes `.cache\quota.json` for any other tool.
  It keeps one login open and never rotates the cookies, so it can run next to a real run; if its session dies it logs in again from the vault,
  and if the cookies are really gone it stops and prints the refresh step. Without `--watch` it takes one reading.
- **Every `replicate` run** prints `[Credits] window left at start: ...; up to N image calls may cost about ...` (a warning, never a block: it
  does not change `--count` or `--max-attempts`), then `[Credits] <tag>: window dropped N during this call, ...` after each image call, and a
  settled `[Credits] run total ...` at the end. **The meter is account-wide**: a parallel run (or the Gemini app) on the same account is counted
  in these deltas. Measured 2026-10-01: one capped `replicate` showed 567 credits for 2 images while another `gen --count 4` ran at the same time;
  the watcher's 20-second timeline showed drops of 173, 127 and 77 at moments when nothing of this run was calling Gemini. Per-image figures are
  only clean when nothing else uses the account (check with the watcher first). The same block is saved in `run.json` as `credits`; `tools\credit_report.py` lists it. `batch_run.py`
  shows the first and last of these lines per photo. `gen` (route G) already logged credits the same way.
- Code: `session.py` (`credits_left`, `describe_usage`, `CreditMeter`, `CREDITS_PER_IMAGE = 85`).

## Video through this session (2026-10-01): WORKS, from text or from the user's photo

The Pro web session makes video with the app's "Create video" tool (Gemini Omni), no billed API. Library path, verified end to end with real calls:

```powershell
.venv\Scripts\python.exe tools\video_probe.py "<prompt>" [--photo "D:\Downloads\AI me\nightout.jpg"] [--aspect portrait] [--delete-chat]
```
Code: `video.py` (`generate_video`, `video_tool`). Clips and a record `<stem>.json` (credits, first reply, seconds, `request_rewritten`) go to `.cache\video_probe\`.

- **Why a plain prompt failed:** "Create a video: ..." through `generate_content` got text ("I cannot directly generate or render video files"), 0 videos, 3
  credits. The tool is switched on in the request, not by wording. Captured from the web page (browser profile `google-1` over CDP, signed in as Pro,
  nothing typed): a video request is the chat request plus (1) slot 0 index 9 = `[null x6, [[null,null,null,ASPECT]]]` (ASPECT 1 landscape, 2 portrait),
  (2) slot 49 = 11 (chat 0, deep research 1), slot 54 = `[]`, slot 55 = `[[16]]` text-only or `[[17]]` with a photo, (3) capability `16` added to the model
  header list (`[4,5,6,8]` -> `[4,5,6,8,16,4,5,6,8,16]`). `video_tool` rewrites those on the one request the library sends; the library's own parser,
  recovery polling and `GeneratedVideo.save()` do the rest. `gemini_webapi` 2.1.1 is untouched in site-packages (a library upgrade can break the slot
  numbers: re-capture the web request if `request_rewritten` is 1 but the reply is plain text).
- **What comes back:** 10.0 s, H.264 + AAC audio (it makes sound), 24 fps, 1280x720 landscape or 720x1280 portrait, about 3 MB, plus a thumbnail. The
  Gemini sparkle watermark is in the bottom-right corner of every frame. `generate_content` blocks 70-78 s and returns "Your video is ready!" with the clip
  attached (the library polls the chat itself); the first reply is "I'm generating your video..." and the clip is attached to the turn later.
- **Cost, measured with nothing else running:** 525 (text-only landscape) and 520 (portrait + photo) credits per clip, about 22 percent of the 2,400 window,
  against about 85 for an image. A browser-made clip showed no drop at the first reading and the meter was unchanged afterwards, so read the cost from a
  quiet account. About 4 clips per window; the weekly 48,384 is not the limit.
- **From the user's own photo:** `--photo` is sent as the first reference. Test: `D:\Downloads\AI me\nightout.jpg` (frontal, 768x1376) + portrait, prompt "turns his
  head toward the camera, calm slight smile". Result: frame 0 is the photo, same scene, outfit and lights; the camera drifts in, the face turns and smiles.
  `facecard.py score` on frames at 0 / 2.5 / 5 / 7.5 / 9.8 s: max reference similarity 0.80 / 0.75 / 0.78 / 0.79 / 0.79 (the photo itself 0.855; mean over
  references 0.45-0.48 against 0.52). Same person by the scorer, about 0.06-0.10 below the source; the user's eye is the judge. A browser test with a
  non-frontal photo (bent over a desk) was accepted too: no face refusal.
- **Open:** whether slot 55 `[[17]]` means "has a photo" or "portrait" (text-only portrait and photo-seeded landscape were not run: 520 credits each);
  the "Put yourself into any scene / create an avatar" feature in the video composer was not explored; up to 5 photos and one video can be attached in the
  app (only one photo tried here); clip length and resolution have no control in the composer (aspect only).
- The video chats stay in the Gemini history unless `--delete-chat` is given (video from a temporary chat was not tried).

## User review of rounds 1-3 (2026-09-20) and what changed for round 4

The user reviewed 14 outputs. Recorded in `facecard.json` under `approved_outputs`, so later work keeps what was good.

| Verdict | Output | Consequence |
|---|---|---|
| perfect | rocky `034849`, `061004`; stained glass `060631/c1_head_raw.jpg` (face AND reflection in one pass); table tennis `061432/c1_head_raw.jpg` (nailed a hard angle) | keep behaving like this. Two of these had been REJECTED by my own gates (face_shift measured on the reflection; alignment gate too tight), which is what round 4 fixed |
| perfect emotion, light off | kayak `060329` (calm closed-lip smile, light dE 16.5) | the expression target |
| awkward expression | kayak `064200` (light dE 7.1, good) | same prompt family, different sample: Gemini's expression varies run to run. Fix = attractiveness policy in the prompt + AI pairwise choice among passing candidates |
| head too big | Pinterest `064235` (face box 1.054x) | foreign-photo size gate 0.95-1.04, "hair the same size, never larger" in the prompt |
| separate reflection pass "does not mirror me" | stained glass `063313/c1_copy1_raw.jpg` | removed; the reflection goes in the same call |
| bad (round-2 pipeline) | kayak `053307` ("three faces", not him), Pinterest `054417` (overlapping faces), rocky `053504` | gone with the round-2 mask and warp; the ghost check is kept as a gate |
| "double chin" | stained glass `064633/c1_head_send.png` | not generated: it is the unedited source crop |

## Round-4 benchmark (2026-09-20, 15:09-15:50 IST, `--count 3 --max-attempts 6`, 21 image calls in total)

Every number is in the run's `run.log` / `run.json`. "Pick" = the candidate written to `best.png`. The user's eye is the judge; these rows say what the pipeline measured.

| Photo | Passed / attempts | Pick | What the pick measured | Run folder |
|---|---|---|---|---|
| kayak (own) | 3 / 6 | attempt 6 (AI expression wins 2, then attempt 2 with 1) | identity 0.598, similarity to his real face 0.682, face light dE 7.7, drift SSIM 0.966. The user called **attempt 2** "good" (0.592 / 0.746 / dE 4.0); when asked to compare it with 6, the user called it "perfect" without choosing one, so both are kept | `20260920_150905_replicate_google-1__IMG_5549` |
| stained glass (own, with reflection) | 3 / 3 | attempt 1 after the selection-order fix (it was attempt 3 before) | identity 0.447 (profile faces score low), similarity 0.641, dE 2.1, drift SSIM 0.972. The user called attempt 1 "very promising". Judge warns the reflection does not clearly match the re-rendered face | `20260920_151934_replicate_google-4__IMG_5850_Original` |
| Pinterest (foreign) | 3 / 3 | attempt 1 | identity 0.587, head size 0.968 of the source, no judge flags. **User verdict 2026-09-20: accepted except the hair: only the front was the user, the sides and back were still the source model. Cause found in the prompt (the source hair was listed as must-stay); fixed in Round 5 below.** Light dE 15-21 (another man's skin, not gated) | `20260920_152548_replicate_pinterest_target` |
| table tennis (own, 109 px face looking down) | 2 / 6 | attempt 1 | subtle edit: dE 2.4, head size 1.066, drift SSIM 0.995. Identity 0.436 and similarity about 0 are NOT meaningful on a face this small. Attempts 2 and 4 dropped the glasses (caught); 3 and 6 were re-framed to 0.799 and fail the size gate anyway | `20260920_153036_replicate_google-2__IMG_3943` |
| rocky (own, regression) | 3 / 3 | attempt 3 (wins 2) over attempt 1 (wins 1) | identity 0.556, dE 9.9 (a brighter face than the dim source; attempt 1 is dE 1.1 with less change), drift SSIM 0.997. User verdict 2026-09-20: "perfect", no preference between attempts 3 and 1, both kept | `20260920_153829_replicate_google-1__IMG_4861_SnapseedCop` |

Judge tally over the batch: in the kayak run the AI judge fired 7 hard flags: 2 right, 3 wrong (two of them the glasses wording, since fixed), 2 unverifiable. After the fix,
the other four runs (15 attempts) raised hard flags only on table-tennis attempts 2 and 4 (glasses missing); attempt 2 verified on the sheet (glasses gone, head zoomed, clothes redrawn).
A second confirming judge call was considered and NOT added: one wording problem, not general noise. Re-tally if a good candidate is lost to the judge again.

Two limits the batch showed: the number of attempts needed varies a lot (kayak 6, table tennis 6, others 3), and a candidate that passes every gate can still differ in taste (kayak 2 vs 6, rocky 1 vs 3), which is why the AI compares them pairwise and the user makes the final call.

## Round 5 (2026-09-20, Pinterest): the hair on another man's photo

The user rejected the round-4 Pinterest output (`20260920_152548`): only the front hair was his, the middle, back and sides were still the reference model's. Cause, read from the prompt: for a foreign photo `scene_block` listed the AI's description of the SOURCE hair under "must stay exactly as they are", while `edit_prompt` asked for his hair "with the outline, length and volume of the last image". The hair mask of that output matched the source's outline to within 2 px. Fix (`replicate.py`, zone head only, own-photo prompts byte-identical before and after): the source hair is no longer described, and the prompt says all of his hair is his (front, top, crown, temples and sides, around the ears, back to the nape). The sentence "the head, including the hair, exactly the same size, never larger" stays.

Result (run `20260920_165702_replicate_pinterest_target`, 4 attempts): the hair is fully his in all four. No attempt passed the gates (head size 0.942 / 1.128 / 0.949 / 1.032, face moved 0.193 and 0.151 on two). The user's verdict on attempt 3 (`cand3.png`: it missed the size limit by 0.001; its hair top and left edge sit within 5 px of the source's): face size, lighting and hair are all right and it is an improvement; the face position and the expression do not match the reference. Measured: the head is 7 degrees more level than the source (pitch +9.3 in the source, +2.2 in the output; the round-4 run was 8.5 to 11 degrees off, so the hair fix did not cause it), and the expression is a calm closed mouth where the reference has a subtle smile. Both are still open.

## Round 6 (2026-09-20 night to 2026-09-21): reference leakage, then the five-scene test

**Cause found for the pasted look and the levelled head on another man's photo.** The identity references leak into the render. The prompt said "skin tone exactly as in the reference photos", two of the four references are bright portraits (face lightness L 61 and 60 against the photo's 37), and their head pitch is 0.6 to 2.5 degrees against the source's 9.3. Renders came back 20 lightness units brighter (neck included, so the neck read as pasted) and about 3 degrees level. The AI judge said "same angle" for all of them, so it cannot see this; a head-pose gate measured better numbers and the user still called the result worse, so it was rolled back.

**Shipped for another man's photo (zone head):** the prompt names the references as the source of identity only ("natural complexion and beard as in the reference photos ... ignore their lighting, exposure, colour cast and head angle; those come from the last image"); the expression defaults to the reference's own ("same") instead of the attractiveness policy, and a judge `same_expression: false` is a hard failure; a light gate of 20 (`gates.light_de_max_foreign`, provisional: cand3 accepted at 18.4, the rejected renders 31 to 35); the size floor is 0.94 (cand3, whose size was approved, measured 0.949). Own-photo prompts are byte-identical to before.

**Result:** Pinterest run `20260921_000411`, attempt 3: the user said perfect. Face L 43.3 / neck L 31.3 (photo 36.7 / 31.2), pose within 2 degrees, hair outline within 5 px, light dE 14.2, judge clear. One good sample of four, so reliability is unproven.

**Five-scene test** (`D:\Downloads\AI me`: night out, nerd, mountain, beach, car2; these already look like the user, pool similarity 0.85 / 0.80 / 0.62 / 0.68 / 0.66). Foreign mode: nerd, mountain, beach and car2 passed, night out failed 0 of 4 (the model re-posed the tilted head: size +13 to 18 percent, moved 0.25). Default mode (`--force` only, all five classified as own): every scene passed 2 of 2. The user's verdicts: nerd, beach, night out "as it is" every time; mountain worse than the source; car2 face lighting and size bad; night-out `c1_head_raw.jpg` (foreign attempt 1) was better in attractiveness and identity than anything accepted, and the gates had rejected it.

**Why the results repeated (measured):** on a photo the pipeline classifies as already the user (similarity 0.4 or more) it is built to return the picture: the prompt says keep everything, the gates reject any change of size, position, angle or drift, and the pick for own photos ends in `gt_sim`, the similarity to the SOURCE face, so the candidate closest to the source wins and a better face is never rewarded. `gt_sim` of what the user approved is 0.23 to 0.75; of what he called "as it is" 0.93 to 0.99. Car2's gates missed the problem: its face is 12.5 lightness units brighter than the source but the light distance (10.5) is under the own limit 14, and the face-minus-neck gap is +17.7 against +4.0 in the source.

**Known bug:** the sparkle-watermark exclusion hole is not moved with the ECC warp, so a re-aligned return leaks the star into the paste (seen in the night-out `not_passing_closest.jpg`).

## Round 8 (2026-09-21): tried and rolled back; the record is in research/round8_attempt.md

The user rolled the code back to round 7 (commit `7fd3ebc`): attractiveness and identity were right, the one mistake was that the good renders existed only as head crops. What round 8 measured before the rollback, so it is not tried twice: whole-photo references were WORSE (Pinterest pick dE 15.8 against the ideal's 5.7; stained glass 1 of 6); the face-only AI comparison against the source agreed with the user's eye in 1 of 3 cases, so it is never a veto; the AI same-man check for gray-zone classification was right 3 of 3; and a face-box registration can merge a re-framed return into the complete picture (0 changed px outside the crop). The beach `c1` raw the user liked was Gemini re-rendering the kayak reference photo, not the beach crop. The patch is `research/round8_attempt.patch`.

The rule that follows from the review: a rendered head is never a result; it is always merged into the complete picture, and only a complete picture that passes the gates can be `best`.

## Scorer and pool (identity.py, scorer.py, landmarks.py)

- Pool = every photo of the user (FaceCard_Originals + `.cache/super_favs`), derived files (mirrored, headless) excluded,
  near-duplicates of the photo being scored excluded (leave-one-out). Never add a mirrored copy: faces are not symmetric.
- Score = mean of the 3 most similar pool photos (was: max over all, which one lucky photo could decide).
- Embedding = ArcFace `w600k_r50` on an upscaled head crop aligned with FaceFusion's 2dfan4 68 landmarks.
- Pose = landmark SHAPE distance. Yaw from a generic 3D model was measured unreliable (a frontal photo read +132 degrees).
- `calibrate.py`, which reprinted these numbers from known-good/bad outputs, was archived on 2026-10-07 (its 22 run paths had gone stale):
  `D:\FacecardArchive\cleanup-2026-10-07\calibrate.py`, or git history. Every staged run now records the identity rule and the gate limits it
  applied (`01_method/env.json`), and `facecard.py run <recipe> --remeasure <run>` re-measures saved pictures for free.

## gen (from scratch) and restore

```powershell
python facecard.py gen --prompt prompts/beach_headshot.txt --count 2
python facecard.py restore outputs/some_run/v1_0.jpg
python facecard.py score outputs/some_run/best.jpg
```

`gen` draws everything, so there is no guarantee outside the face. It then scores and, on frontal/mild poses, runs the
FaceFusion swap; steep profiles (over 45 degrees) are locked out of the 2D swapper because its frontal template warp
collapses the far eye. Its old profile gate (0.50 on a max-over-refs score) was inflated and is superseded by the
numbers above; treat `gen` scores as legacy.

## Session cookies (DPAPI vault)

Two cookies identify the session in the DPAPI vault (`C:\Users\Admin\.secrets\vault.dpapi`):

| Cookie | Vault entry | Field | Value shape |
|---|---|---|---|
| `__Secure-1PSID` | `gemini-cookies-psid` | `password` | ~150 chars, starts `g.a000` |
| `__Secure-1PSIDTS` | `gemini-cookies` | `password` | ~78 chars, starts `sidts-` |

Refresh command (run from `C:\Users\Admin\.agents\skills\secure-vault`):
```powershell
python vault.py gui --request "gemini-cookies-psid:account,gemini-cookies:account" `
  --hint "gemini-cookies-psid=Password = FRESH value of __Secure-1PSID (starts g.a000)" `
  --hint "gemini-cookies=Password = FRESH value of __Secure-1PSIDTS (starts sidts-)"
```
**Important:** DevTools (F12) → Application → Cookies → `https://gemini.google.com`. **Double-click
the Value cell** before copying (the table clips long strings). Always capture BOTH cookies fresh,
back-to-back, from a freshly reloaded tab.

## Models

`facecard.py models` lists what the account can use (2026-10-08: 3.1 Pro `e6fa609c3fa255c0`, 3.8 Flash `56fdd199312815e2` = `facecard.json`
`model`, 3.5 Flash-Lite). The chat model is all the library chooses; the image model is the app's (Nano Banana 2.1 for AI Pro since 2026-10-06, per
Google; `tools\model_probe.py` finds the same `imagen_default` tool behind Flash and Pro). Flash is the default for new recipes and finals. Run it if a run fails with an unknown-model error.

## Ground rules

- **The subject's own photo -> a `replicate/1` recipe (`recipe new --method replicate`). Anyone else's photo -> scene-prompt-writer, an inventory, then a Route G recipe (`recipe new --character me@v1` + `run`).**
- **NEVER judge identity by eye.** Read and report the numbers, and show the compare sheets.
- **NEVER feed generated images back into the reference set,** and never add a mirrored photo to it. The one exception is the user's own
  request of 2026-10-10 (an approved ideal smile, head-angle references and a next-cut physique), under the guards in AGENTS.md "The
  reference-set upgrade": nothing generated is a reference until the user approves it, and the real photos stay the identity pool and band.
- **Never change a threshold quietly.** Thresholds live in `facecard.json`; changing one needs the user's approval.
- From-scratch scenes follow scene-prompt-writer: the reference decides pose, light and expression; attractiveness levers
  fill only what the reference leaves open.
- Attractiveness levers belong in the scene prompt (lighting, posture, fit, framing), never in the identity lock.
- Do not put "athletic/muscular/lean build" in any prompt that has the user's own body in the frame: it replaces the
  user's real physique with a generic one.
