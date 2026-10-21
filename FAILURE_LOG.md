# Failure log

The user, 2026-10-10 evening: "multiple rounds of failures seem to be happening back to back. Keep a record of why each of those is happening."

Every failure gets an entry here: a run, a wave, a refusal, a picture that failed its gates or the user's eye, a tool that broke, and my own
mistakes. Each entry says what failed, the evidence, the cause (or "unknown" and the assumption it rests on), what it cost, the fix, and
whether it is closed. Newest first. The patterns at the top say which failures share a cause; the decision under them says what gets rewired.

## Patterns (what keeps causing the failures)

| # | Pattern | Entries | Where it lives |
|---|---|---|---|
| P1 | **The orchestration around the runs is blind.** A wave keeps starting runs after a failure every run will share (sign-in), counts "running" from log growth instead of live processes, and has no stop command, so stopping one means hunting PIDs by hand and missing children. | F1, F2, F3, F4 | `tools/wave.py`, `runner.py` |
| P2 | **One fragile Gemini session.** A single rejected sign-in ends a run; nothing checks the session before a wave starts or retries a short rejection. | F2 | `session.py`, `tools/wave.py` |
| P3 | **The machine is short of memory.** 16 GB with the overnight Qwen render, Edge, VS Code and the job bots: runs wait or page out, and my own measuring jobs ran past their time limit. | F4, F9, E1 | the whole box |
| P4 | **Gemini's own habits, caught by the gates.** It re-frames or zooms, draws the person larger (4 of 4 pictures on the evening of 2026-10-10: x1.13-1.21), takes the pose of a reference photo, keeps the photo's body, and shrinks arms in a grey-out. The gates caught every one; each catch costs a picture (95-173 credits on Flash, measured tonight). | F5, F7, F11, E2-E9 | the prompts and references |
| P5 | **My own mistakes.** Claims I did not verify, wrong reads of a picture, a wrong estimate. | F1, F7, F8, F10, E10-E12 | my process |
| P6 | **Work waits on the user.** A question at the end of a turn, or a to-do held behind one, stops everything through whole credit windows: three idle hours on 2026-10-10, five on 2026-10-11. | F31 | my process, `tools/autocontinue.py` |

## Rework done (2026-10-10 22:10, after wave pins1417b ended)

| Item | Where | Tested for real (free: waves of recipe dry runs) |
|---|---|---|
| Sign-in check before every start; a refusal waits 2 and 5 minutes; a lasting one halts the wave | `tools/session_check.py`, `tools/wave.py` | the check signs in (AVAILABLE, 2,008 credits); every test run started after one. **The refusal path is not tested**: it needs a real refusal (no fake sessions); it shows in the wave log as "session: ... waits N min" |
| Halt on exit 5 (sign-in) and 3 (credit guard) | `runner.py` `SIGN_IN_FAILED`, `tools/wave.py` | not tested (needs a real failure) |
| Runs tracked by process (PID + start time, launcher and child) in `.cache/wave_<tag>.runs.json`; other waves count only live processes | `tools/wave.py` | another wave saw a running test run as live; ended runs and killed processes were not counted |
| `tools/wave.py --stop <tag>` (graceful) and `--now` (ends runs not yet signed in, checks none is left) | `tools/wave.py` | `--stop`: 2 queued runs not started, the running one finished; `--now`: a run in stage 01 ended with its children, 0 processes left |
| Every run without an accepted picture, and every halt, writes a line to `.cache/failures.jsonl` | `runner.record_failure`, `tools/wave.py` | halts: written (the two test lines were removed); runs: first real run will show it |
| The exit line shows the pose gate ("pose gate 1 pass / 1 fail") | `tools/wave.py` | not shown by dry runs (no stage 06) |

F1, F3 and F4 are closed by these; F2's cause is still unknown, but a repeat now waits and halts instead of failing every queued run.

## Rework decision (2026-10-10 20:55)

The generation core (frozen recipes, locks, gates, the 36-item checklist) did its job: no bad picture was passed. The layer around it (P1, P2)
is wired wrong, and it is what turned single problems into repeated ones and cost 346 credits tonight. It is reworked after the running wave
(pins1417b) ends, without stopping that wave:
- **Session preflight before every run of a wave**: a cheap sign-in check. A short rejection is retried after 2 and 5 minutes; a lasting one
  halts the wave and is written here, instead of failing run after run.
- **Halt on failures every run would share**: the sign-in failure gets its own exit code, and the wave stops starting runs when it sees it.
- **Runs tracked by process, not by log growth**: each wave records its runs' PIDs with their start times, so other waves and my checks see
  what is really running.
- **`tools/wave.py --stop <tag>`**: no new runs start and the running ones finish (the default); `--now` stops the whole process tree as it is
  at that moment and then checks that nothing of that wave is left.
- **Failures recorded by the system**: every run that ends without a picture writes its reason to `.cache/failures.jsonl`; I copy each one
  here with its cause.
- **Credit planning from measured cost**: 95-173 credits per Flash picture tonight, not the 100 I planned with.
- ~~A first picture that fails the pose gate stops a new recipe's run~~ **dropped (21:50)**: pin 16's second run (F13) failed its first
  picture and passed its second, the only near-pass of the evening; stopping after one fail would have lost it. The stop stays at 2 fails.
- **P4 gets a method change, not new words** (the do-not-retry rule): pin 14 in two stages (him with the restore, then the background);
  pin 16's BODY references cropped to the torso so their hanging arms cannot set his pose.

## Entries

### F78. Pin 15 v8 stood upright: the pin man's lean was never written into the inventory (the user's verdict, 2026-10-22)
- **The user, 2026-10-22 (question box), of pin 15 v8:** "yes, we need a new render, and I want you to understand that the person in the Google Pinterest image is
  pushing their hips forward and leaning their back backwards towards the camera. That is, the back is relatively closer to the camera than the hips. This creates
  the back to look more triangular, that is, shoulders wider and waist narrower. Implement that pose exactly as it is."
- **Cause, from the inventory (v17) the render was built from:** its posture item said "standing with his back to the mirror, his torso turned slightly ..." and no item
  named the lean, the forward hips or the perspective it makes (shoulders near the camera and large, waist far and small), so the render stood him upright with the camera
  at a distance. That the lean is the pin's pose is the user's reading of the pin; the pose gate (shoulders 0.167 and 0.179 low) did not name it.
- **Fix, v9** (`.cache/inventories/pin_783485666540141726_v18.json`): the posture item opens with the lean and a new CHANGE item "the lean and the triangle of the back" carries it
  (hips pushed forward toward the mirror, upper back leaning back toward the camera, shoulders, rear deltoids and lats near and large, waist and waistband far and small,
  the back a triangle, never an upright rectangle). The rest of v8 (the two BODY references, no size cap) is unchanged, so the lean is the one new variable. Open until the
  render is seen. Queued with pin 13 v9 for 03:33:25 IST (the window held 154 of 2,400 credits at 02:45, the user's own use).
- **Same round, pin 13 v8 "Neither, new render":** v9 sends the pin's three overhead screens as reference crops (the garbled menu line is the defect I can name); the size item
  is unchanged because wording has not moved it in five renders (v7 x1.31; v8 x1.69 and x1.32): if the size matters more than the head turn, the turn is what to reduce.

### F77. The 22:33 chain and pin 15 v8 (2026-10-21 22:33-23:25): pins 6, 14 and 13 ran at the refill, pin 15's back is thicker for the first time
- **The chain** (armed 19:03, ran 22:33:37-22:47:08, three whole renders, 931 credits, window 2,400 -> 1,469: it reconciles to the credit, nobody else spent
  in that stretch): **pin 6 v5** (Flash, the sharp-face item and his real profile IMG_6863): the face is sharp (jaw, chin, nose crisp); pose gate FAIL (head bow
  +0.90 and +0.81 against +0.61, size x1.15 and x1.09, head and shoulders 0.12 off); render 1's hand points at the drawing. **Pin 14 v5** (Flash, the same
  sharp-face change): sharp, lean faces; gate FAIL (size x1.15 and x1.07, forearm and hand off), the janeu hangs straight down in both. **Pin 13 v8** (Pro): the
  jeans sit at the waist (the v7 flaw is fixed); size x1.69 and x1.32, hands 0.22-0.36 off, the screens' lettering garbled. All six NOT BEST; the sparkle stays on
  all six (busy corners, texture 14-52).
- **Pin 15 v8** (run `20261021_231703`, Flash, 274 credits -> 1,195): the approved pumped back crop, mirrored, plus his real flexed IMG_7420 frame as the two BODY
  references, no size cap, and the outline item's "no larger" removed. Pose gate: only item 14 fails (shoulders 0.167 and 0.179 low); the head items pass for the
  first time. By eye the back is broader and thicker than v6's (`07_review/back_mass_compare_v8.jpg`). Three changes at once (the pumped crop added, the cap
  sentences removed, "no larger" removed): which one carried it is not isolated. Recipe v7 was frozen with a typo (`referencess` in four inventory items) and never run.
- **The janeu direction of the references (found while building v8):** `pumped_back_torso.jpg` is a direct view of his back, its thread runs upper picture-left to
  lower picture-right (his left shoulder to his right hip seen from behind). The mirror pin needs upper picture-right to lower picture-left, as the real IMG_7420
  frame has it. That is why v4, which sent the torso alone, drew the thread the wrong way. For a mirror picture send `pumped_back_torso_mirrored.jpg` (physique
  `pumped-back-flexed`).

### F76. The evening round of 2026-10-21: pin 12 v7 and pin 15 v6 ran; the Gemini window was emptied by a consumer that is not this pipeline
- **Pin 12 v7** (run `20261021_173953`, Pro, `--teeth`, route text v6): the smile shows his own teeth now (lips apart 0.179 and 0.141 of the eye
  distance; IMG_6875 0.198, the cat selfie 0.175; identity 0.64 and 0.68). The background is in focus (sharpness 267 and 393 against 6 and 17 in v6).
  **The camera did not move back:** eyes 76 and 77 px apart against 76 and 81 in v6, although the route text asked for two and a half metres with
  the head a sixth of the frame (it measures about a quarter); wording alone does not change his size in the frame. Checklist (items 12/14/30 N/A: the
  user's change of view): both NOT BEST on 34, the pin's small "Untld" mark under the print is not in the render (the earlier pin 12 records passed 34
  without naming it); v2_0 also on 33, two figure-shaped forms in the left shop front (mannequin or customer cannot be told apart at 25 px). The sparkle
  stays on both (busy corner, texture 11.7 and 12.9 against the 9.0 limit).
- **Pin 15 v6** (run `20261021_174638`, Flash, his real flexed IMG_7420 frame, unflipped, as the body): one picture (the second call returned nothing:
  the session turned unauthenticated at 17:51). The janeu runs the right way and the sparkle is filled (`v1_0s.jpg`). Shoulders 0.177 and head 0.243 off
  the pin's (he sits lower and smaller in the frame). In the side-by-side sheet at one height (`07_review/back_mass_compare.jpg`) the back is not more
  massive than v5's and is less massive than the pin man's and than his real frame. The assumption behind v6, that a real flexed frame carries his back
  mass into a mirror-selfie composition, did not hold in this render; cause beyond that: unknown. Open, waiting for the user's verdict.
- **The Gemini window (account-wide meter), the complete record from the run logs and `.cache/failures.jsonl`:** windows in which this pipeline ran
  alone reconcile to the credit: 02:33-07:33, six runs spent 1,550 (2,400 -> 850); 07:33-12:33, pin 15 v5 spent 272 (-> 2,128). Window 12:33-17:33: the
  pipeline made no call (no run folder between 11:52 and 15:48; the 15:48 run stopped at the credit guard) and the meter read 0 of 2,400 at 15:49:09, so
  2,400 credits went to a consumer outside this pipeline. Window 17:33-22:33: 1,600 left at 17:40:24 (800 used before this pipeline's first call; its
  17:35 run died at sign-in before it generated); pin 12 v7 spent 272 (-> 1,328); pin 15 v6's one call read 641 on the meter against 123-141 for every
  other picture (the excess is not this pipeline's); 0 left at 17:53:48; the pin 6 v5 run waited 912 s at the guard and stopped (exit 3). Weekly left:
  29,642 (17:40), 29,370 (17:47), 27,864 (18:11). Excluded as the consumer: this pipeline's other runs (none exist), `SecondBrain-Gemini-HourlySync`
  (reads chats only), the keep-alive (no generation); the account's chat list holds no chat dated 10-20 or 10-21. **Answered by the user (question box, 2026-10-21 about 23:00): "It was me"**: the drain of those windows was their own Gemini use; the Activity page was not read.

### F75. The one-render round of 2026-10-21: six pins, every pose gate failed again, the pictures look like the user (pins 15, 6, 14, 9, 13, 12)
- **The user, 2026-10-21:** "dont wait until user approves just move on to next pin going forward". Each pin: one whole render (2 pictures), no
  edits, `FACECARD_HOLD_PASS` for that recipe only, credits 247-285 a run (the window went 2,400 -> 850).
- **Results (pose gate, then my checklist; all NOT BEST, nothing exported, nothing marked approved for the user):**
  pin 15 v4 (Flash, back-torso photo): shoulders 0.16-0.17 off, he sits lower, render 1 on a 3:4 canvas (0.747 against the pin's 0.881), the
  janeu runs the wrong way for a mirror picture; pin 6 v4 (Flash): head bowed lower than the pin's (+0.86 against +0.61), x1.15-1.21 larger;
  pin 14 v4 (Flash, Gokarna in words): x1.21-1.29 larger, hands 0.07-0.11 off, the janeu runs straight down; **pin 9 v4 (Flash, restore with
  heads kept): passes every measured item except the head bow (0.74 against 0.87), the closest result of the round**; pin 13 v7 (PRO, v3's
  request unchanged): x1.31 larger and 0.15 right of the pin's, garbled screen text; pin 12 v6 (PRO, v5's request): a front view from text
  against a back-view pin (the pose gate cannot apply), identity 0.73/0.71, print exact.
- **Pro against Flash, corrected:** I first wrote that Pro raised pin 13's identity (0.50/0.51 against 0.13-0.35 on Flash). The ledger says
  Flash's whole renders of pin 13 scored 0.53, 0.44, 0.47, 0.48 (only the head-away stage-1 renders scored 0.05-0.09), and pin 12's Flash
  runs 0.71/0.72 against Pro's 0.73/0.71: no identity gain from Pro on these two, and the pose failures were the same. Not a fix.
- **The F74 rule, tested:** pin 4's v3 (chest-only wording) fixed the shoulder line (0.68-0.71 against 0.70) but not the head; pin 15's torso
  photo and cropped wording did not stop it drawing him lower; so the build wording is one cause among others (the pin man's much bigger body
  and the camera distance drive the re-composition).
- **Tools made on the way:** `tools/sparkle_fill.py` (fills only the sparkle's own pixels from the wall; refuses a corner with objects under the
  star, texture above 9, or one where the star is pale on pale; `--max-busy` to override); `best_check.py --superseded-by`; the head ellipses in
  `tools/background_restore.py`; physiques `pumped-front-chest`, `pumped-back-torso`, `pumped-side-chest`, `casual-front-arms`.

### F74. Pin 4 re-framed in 10 of 10 renders since 10-13: the build wording asked for body parts the pin does not show (2026-10-20)
- **The user, 2026-10-20,** of run `20261019_154219` (both renders re-framed): "keep both but try again to frame it properly only after first
  debugging why it happened." Both kept (`_04_..._v4.jpg`, `_v5.jpg`, sparkle mark left: the background copy refused both).
- **Measured:** every pin 4 render since 10-13 (Flash and Pro, 10 pictures, recipe v1/v2 with physique `pumped-front-torso`) failed the pose
  gate: his head 0.10-0.17 higher than the pin's, shoulders-to-nose x1.05-1.32 (the pin's man ducks his head behind the camera: 16% of the
  frame between nose and shoulder line), more torso showing. The 10-01 render that passed (`20261001_063344` `v1_0.jpg`, Pro, the same pin and
  framing words) passes today's pose gate too (head 0.013, size x1.06).
- **Cause (the one difference in the words):** the physique's build text, put in BUILD and in the CHANGE list, said "the lean torso with his
  upper abs and obliques showing, the tight narrow waist", and its label "cropped at the chin and the waistband"; the pin is cut just below
  his chest, so the abs and the waist can only show if Gemini stands him upright and raises him. The 10-01 request said "a slim, lean build:
  ... a flat chest and stomach" with his real full-length body photos. Not separable without renders: the torso photo itself.
- **Fix to test (one change):** physique `pumped-front-chest`: the same photo, worded for what the frame shows ("but only as much of it as the
  PHOTO TO EDIT shows: the firm chest, the round shoulder caps and his full upper arms ... The picture stays cut where the PHOTO TO EDIT is
  cut"); recipe `pin_783485666539777050@v3`. Rule for every recipe: the build text names only body parts the goal's frame shows.

### F73. The background restore pasted the pin man's hair over his (pin 8, 2026-10-19)
- **The user, 2026-10-19,** of the kept pin 8 picture (`_08_..._v3.jpg` = run `20261019_053523` `v1_0r.jpg`): "although the teeth here were
  perfect, the hair is not."
- **Cause (code, not Gemini):** Gemini's raw render `v1_0.jpg` has his curls. `tools/background_restore.py` keeps Gemini's pixels only inside
  YOLO's person mask plus where the render differs strongly from the pin; YOLO's mask stopped at the shoulders in the render and in the pin (a
  dark head on a dark wall, the phone over the face), and dark curls over the pin man's dark straight hair differ too little, so the pin man's
  hair was copied over his curls while his face survived (`07_review/restore_head_check.jpg`).
- **Fixed:** `head_mask()`: an ellipse over every human head (YuNet faces at a score of 0.8 or more; the kitten he holds scored 0.63, the men
  0.91) is always Gemini's, in the render and in the pin. Limit seen: a lighter oval of Gemini's ceiling above his head on a dark wall. New
  `--only-sparkle` (single mode): everything Gemini's except the sparkle watermark, for a pin with no background people or text.
- **Audit of all 37 restored pictures:** the head changed in 7; exported among them: pin 8 v3 (this one) and the pizza `_11_..._v2.jpg` (the
  top of the curls trimmed, 6% of the head).

### F72. No goal picture shows good teeth (the user, 2026-10-17; diagnosis `.cache/smile_diagnosis_2026-10-17/REPORT.md`)
- **The user, 2026-10-17:** "smile is a major project item to be corrected since none of the generated images till now have good teeth showing images".
- **Measured** (586 pictures, local landmarks, no Gemini call): teeth show in 57 (14%), 50 of them from the 10-10 smile tests on the user's own
  photos; in goal pictures (route G) in 5 of 271 (1.8%). None of the 10 exports shows teeth; of the 17 best-set pictures only car and mt2 do, a few px tall.
- **Causes:** (1) nothing asks for teeth: the closed-lip smile is the default in `facecard.json` `attractiveness_note`, in `replicate.py`
  (`DEFAULT_ATTRACTIVENESS`, `FACE_PAIR_PROMPT`, `scene_block`) and in the scene-prompt-writer policy; the pair judge prefers closed lips, the
  checklist has no teeth item, the character's four faces have closed lips; 14 of 137 recipes asked for teeth (first on 10-09), 28 for closed
  lips; no word of the user asked for closed lips. (2) At goal size a picture cannot carry teeth: every return is a ~1 MP preview
  (`full_size: false`), and route G faces sit a median 55 px between the eyes (IMG_6875: 246); teeth show in 1.5% of pictures under 100 px and 84%
  at 200 px or more. (3) Without the real IMG_6875 crop the teeth come out pale, even and blunt ("a shade whiter" made it worse). (4) Likely: the
  generated E2 as the teeth reference on small heads smooths the rows.
- **What worked:** E2 (`outputs/20261010_125108_goal-img-6858/v1_0.png`): the real IMG_6875 crop as the reference and the head at 62% of a ~1009 px
  crop. The user, of a route B redo of IMG_3884 on 10-10: "Teeth shape, size, my lips, everything is perfect".
- **The user's answers (2026-10-18):** only E2 has the right teeth (not the IMG_3884 redo); teeth only for smiling goals or when asked; the real
  IMG_6875 + IMG_3884 as the teeth references (never E2, never "whiter"); the first teeth test goes straight to a shirtless pin once the hold is
  lifted. No new photos: "dont keep blaiming the photos" (the existing ones are sufficient).
- **First test, 2026-10-19:** pin 8 v8 (one whole render, `--teeth`, the two real crops): the user, of the first picture: teeth "The first
  picture's do", "Keep the first" (exported `_08_..._v3.jpg`). The opening matched his (lips 0.18 of the eye distance, his 0.20) with the eyes
  only 61 px apart; the second picture's teeth came out as an even row.

### F71. The downward spiral since 2026-10-11: edits stacked on edits (retrospective of 2026-10-17, `RETROSPECTIVE_2026-10-17.md`)
- **The user, 2026-10-17:** "all the recent generations have been going downhill ... even with multiple checks, modular processing, and step-by-step
  processing ... we still have been going into a downward spiral ... find out why and fix it." Nothing in the user's best set (`D:\Downloads\AI me`, 17
  pictures) is newer than 2026-10-11 01:53.
- **Measured:** every best-set picture took one pass or one pass plus one small fix. Of the 428 pictures since 10-07, 58 (11 runs, all from 10-11)
  were edits of edits: pin 14 up to six passes, pin 16's eye fixes were edits of surf.jpg itself (one of the best set), pins 8, 9, 12, 15 at three. Before 10-07
  no request sent a generated picture as a reference; from 10-10, 66 of 91 did. Whole-render prompts grew from 4,935 to 12,843 characters (median),
  Pro fell from 68 of 107 runs to 2 of 24, and four of the five gold pictures fail my checklist.
- **Causes:** (1) chains of partial edits, each adding damage; (2) goals moved to shirtless pumped bodies on other men, which one pass cannot do
  (FEEDBACK_LOG 16, 2026-09-27), so the chains looked necessary; (3) every failed checklist item became one more edit instead of a fresh render;
  (4) my own outputs fed back as references and bases; (5) volume (135 runs in eight days) with fewer of the user's reviews.
- **Fixed:** generation on hold (`.cache/GENERATION_HOLD`, both hidden tasks disabled); `tools/edit_depth.py` + a guard in `runner.py` refuse a
  recipe whose pictures would have more than two passes, or whose lineage it cannot read (exit 7), unless the user asked for that exact edit
  (12 of the 137 frozen recipes, all chains from 10-11 on); `runner.run` checks the hold too; the operating rules at the top of `AGENTS.md`.
  The user's decisions (10-17): the pumped physique always, shirtless pins first, the current-look items as notes, spare credits only for plans
  they approve; an A/B against the code of commit `42296f2` (2026-10-02) is proposed for when they lift the hold.
- **More evidence, the same day:** the user called two exported pictures "bad" that they had approved in dialogs (pin 15 v2 on 10-12, pin 14 v3
  on 10-13, both before the 10-14 rule that a question about pictures is never a dialog). They are chains of 3 and 5 passes. Recorded with the new
  `tools/best_check.py --user-rejected` (the approvals stay under "history"); the results folder withdrew both, the originals stay in `outputs/`.

### F64. G2 cell (b) retry, `google-2__IMG_4446` v2 with `--loose-crop` (TODO 105, 2026-10-14 09:47-10:00): the AI head-box reading stalled twice, and `recipe new` then saved a recipe that did not apply the loose crop
- **What I ran:** `recipe bump` refuses a replicate/1 recipe whose inputs change ("it reads the photo again"), so v2 was frozen the way v1 was:
  `recipe new --method replicate --goal D:/FacecardData/head_angles/originals/google-2__IMG_4446.jpg --character me@v2 --zone face --current-look
  --expression same --loose-crop --samples 2 --max-attempts 3 --because "..."`. Try 1 (09:47, window 57 credits left): head box Flash
  `TimeoutError` (150 s), Pro "I seem to be encountering an error"; try 2 (09:53, 54 left): both models timed out. The scene reading answered both
  times.
- **Evidence:** both saved recipes have `readings.head_box.box = null` and `inputs.crop = [846, 436, 1024, 1024]` (the same as v1) although
  `method.args.loose_crop = true`: `replicate_recipe.freeze` applies the loose crop only `if ... and head is not None`, and it carries on without a
  head box instead of refusing. Such a v2 would have run v1's framing again for 450 credits. Both files were moved (not deleted) to
  `.cache/replicate_freeze/20261014_094735_google-2__IMG_4446/rejected_v2_no_head_box.json` and `.../20261014_095343_google-2__IMG_4446/`;
  `recipes/misc/google-2-img-4446/` holds only v1, so the next freeze is v2 again. Nothing was queued.
- **The crop it should give (computed offline from v1's frozen head box 1146,463,1581,1114 with `replicate.expression_crop`, no Gemini):**
  [846, 436, 1024, 1024] becomes [838, 337, 1050, 1050]: the head share goes 63.6% -> 62.0% (hardly changed) and the hair top goes from 2.6% to
  12.0% below the crop's top edge (the head gets headroom; the crop is 2.5% wider). In v1's six returns the framing was kept (ECC 0.985-0.995,
  scale 1.000) and only the head came back smaller, so whether headroom is the cause is a hypothesis, not a measurement.
- **Cause:** the head-box call stalled on Gemini's side (v1's freeze at 08:31, with a full window, answered); both tries were at 97% of the window
  (54-57 of 2,400 left), so a quota-near-empty stall is the working assumption, unproven. Second problem, in code: `--loose-crop` with a missing head
  box should refuse the freeze (as `--head-region` refuses a missing face), not save a recipe that says loose and is not. Not changed here.
- **Cost:** about 3 credits per try (57 -> 54), both from the window that ends at 10:33. A fresh freeze also re-reads the scene, so its wording
  differs a little from v1's (v1: "a very slight sideways tilt toward his left shoulder"; try 1: "a slight tilt to the right of the picture").
- **Resolved (10:36, after the refill to 2,400 credits):** the third freeze read the head box (1141, 468, 1585, 1118) and wrote
  [v2.json](nano-banana-facecard/recipes/misc/google-2-img-4446/v2.json): crop [839, 342, 1049, 1049] (v1 [846, 436, 1024, 1024]), head share 62.0%,
  hair top 12.0% below the top edge, `max_attempts` 3, `loose_crop` true; references, zone, current look, gates, character, hair and face notes
  identical to v1. Dry run: `request 1a68dd1f2f71bb0d = the lock`. Queued as wave `g2b` (450 credits, behind pin12d and pin9build2), review
  TODO 106. The stall points to the near-empty window (a freeze at 97% used failed twice, at a full window it answered at once); still unproven.
  Not exactly "framing only": the scene reading was redone on the new crop, so the prompt's "what the photo shows" lines are worded differently
  (head turned 20-25 instead of 25-30 degrees, chin, gaze, hair, light and face-brightness wording); the pose v1 returned (-4.5 / -28.2) came
  from the old wording, so g2b's pose is measured again, not assumed. The `because` text quotes the offline crop (838, 337, 1050) from v1's head
  box; the frozen crop is the one above (the AI box moved by 5 px).

### F70. G2 cell (f) -30 side (wave `g2f2`, run 20261014_155947, 2 pictures, 133 credits per call): pose in range, the AI smile comparison could not run, and the background agent for the +30 side hit the account's session limit (2026-10-14 16:3x)
- **Result:** v1 reads -29.8 / +2.2 and v2 -29.2 / +0.5 against the cell -30 / 0 (limit 8): both in range, the render gate passes both. Smile landmarks against IMG_6875
  (`g2f_review_smile.jpg`): eye_open +22% on both (his eyes are rendered wider than in the real smile), mouth_open +16 / +11, mouth width +2 / +4, lift 0 / +2, brow +6 / +4: v2 is closer on four of five.
  Checklist v2_0: NOT BEST on 21 only (identity not measurable on a three-quarter face).
- **Not obtained:** `smile_match.py --ai` ('every part same') returned no usable answer twice (both Gemini text calls timed out), so the part-by-part claim is unverified; retry it when the text service answers.
- **Background agent failure:** the agent preparing backlog 9 (the +30 side) stopped at 16:2x with an API 429: 'You've hit your session limit, resets 5:30pm'. That limit belongs to the Claude account, not the
  Gemini credits: six agents ran in parallel with this session today. Backlog 9 stays claimed with whatever the agent saved; no more background agents until the limit resets at 17:30.

### F69. G2 smiling cells, wave `g2ef` (2026-10-14 12:33-14:34, 2 pictures + 1 run lost, 272 + 0 credits): cell (e) turned into a profile, and cell (f) lost its sign-in while waiting for credits (2026-10-14 14:5x)
- **Cell (e), looking back over the shoulder with E2 (`g2e_cell5_send@v1`, run 20261014_123335):** both returns fail the pose proxy. The source crop is a rear three-quarter view (-27.2 / -12.7,
  the ear about 65% of the head from the back of the curls to the nose tip); v1 reads -80.3 / -45.3 / roll 57.2 with the ear at 49%, v2 -77.8 / -17.3 / roll 26.0 with the ear at 45%: the render turned the
  head about 50 degrees toward the camera into a right profile, the same move pin 13's smile edit made. Both show a clean broad smile with his own beard, curls and chain, but neither is a
  looking-back cell. Checklist v2_0: NOT BEST (12, 14, 21). Nothing for approval.
- **Cell (f), -30 / 0 with E2 (`g2f_cell6_send@v1`, run 20261014_124117): no picture.** The wave was queued with 600 credits at a window of 632; cell (e) took 272 of them and about 236 more went elsewhere
  between 12:25 and 12:41 (window 124 at the start of the second run). The second run started anyway, passed its own sign-in and then sat 113 minutes at its credit guard ('window 124 - reserved 0 <
  need 240 + margin 150'); its Gemini session expired while it waited and it exited 5 (sign-in failed) at 14:34. The window also hit 0.
- **Cause:** the wave started a run without checking the window for that run, and a run that waits at its own guard stays signed in (runs never renew the cookie, memory note facecard-gemini-session).
- **Fix (code, `tools/wave.py`):** a run now starts only when the window holds `--min-credits` (default 390: the guard's rule for a 2-sample run, 240 + 150); until then the wave waits BEFORE the sign-in and logs
  `credits: <run> waits (the window holds N credits < 390; it resets at HH:MM)` (tools/quota.py refreshes the meter when older than 10 minutes or past its reset; an unreadable meter never blocks).
  Checked against the real meter: 'the window holds 0 credits < 390; it resets at 15:33'.
- **Next:** cell (f) is queued again as wave `g2f2` (330 credits, same recipe and lock) for after the 15:33 reset; for cell (e) a real photo of him looking back over the shoulder, smiling, is the better source.

### F68. G2 cells (b), (c), (d) by the head-edit method (waves `g2b3` and `g2cd`, 2026-10-14 11:46-12:05, 6 pictures, about 810 credits): (b) and (d) land in range, (c) lifts the bow (2026-10-14 12:3x)
- **Method (the cell (a) one):** a Route G objects-mode head edit of a head-and-shoulders crop, the crop itself is the cell, nothing pasted back.
- **Measured (headpose.py on the returned picture; source crop in brackets):**
  - (d) -45 / 0 from pin 7 (crop -39.5 / -2.3): v1 -45.1 / +2.8 (0.1 and 2.8 off the cell: PASS), v2 -51.1 / -6.7 (6.1 and 6.7: passes narrowly).
  - (b) 0 / -25 from the 2023 selfie crop (-5.2 / -25.6): v1 -19.2 / -24.3 (yaw 19 off: FAIL), v2 -2.7 / -30.7 (2.7 and 5.7: PASS).
  - (c) +25 / -35 from IMG_7004 (+25.1 / -44.1): v1 +34.4 / -17.0, v2 +28.2 / -22.4: the bow was LIFTED by 22-27 degrees, pitch 12.6 and 18 degrees off the cell: FAIL both. As predicted, the
    render does not keep a deep bow; cell (a) came back 8.5 degrees shallower, (d) went the other way (+5), (c) 22 shallower: the shift is not a constant.
- **Checklist:** (d) v1, (b) v2 and (c) v2 are NOT BEST on 12 (the render gate against the SOURCE crop, not the cell test) and 21 (identity not measurable on a bowed or three-quarter
  face; needs the user's eye); everything else passes (24 passed, 10 n/a). Defects to fix before either becomes a reference: Gemini's star at the bottom right of both pictures; the
  2023 crop's grey glare patches at the hair's top left and its warm-orange room cast carried over in (b) v2.
- **Credits:** g2cd 540, g2b3 270: 135 per Route G picture as budgeted (the replicate runs cost 137-277 per attempt, F63).
- **Next:** (b) v2 and (d) v1 go to the user for approval (plain-text questions in chat). Cell (c) has no source in the cell: filed as a [user] to-do for one new real photo of him at about
  +25 yaw / -35 pitch.

### F67. G2 cell (b) retry with `--loose-crop` (`google-2__IMG_4446@v2`, run 20261014_111701, 3 attempts, 437 credits): worse, the head came back 21% smaller (2026-10-14 11:3x)
- **Result:** 0 of 3 pass the gates. Size ratio 0.792 / ?(v2 0.792) / 0.784 against 0.94-1.10 (v1 of the recipe was 0.82-0.87): the looser crop made the redrawn head SMALLER, not the
  same size. v1 and v3 also moved the head (face shift 0.197 and 0.188 against 0.12) and the AI judge saw the head angle change on v3. Identity 0.70 / 0.568 / 0.658 (fine).
- **Poses (headpose.py, whole picture):** v1 -32.9 / -20.1 / roll 23.0, v2 -10.6 / -26.6 / roll 13.5, v3 -29.0 / -22.2 / roll 23.0, against the cell 0 / -25: only v2's pitch is in
  range, its yaw is 10.6 degrees off (limit 8), v1 and v3 are 29-33 degrees off. So the loose crop also let Gemini turn the head; the v1 recipe's returns (-4.5 to -4.8 yaw) were better on pose.
- **Cause (the hypothesis in F64 failed):** headroom was not the cause. Inside the 1024 px crop the head is a smaller share when the crop is looser, and the replicate prompt asks Gemini to
  keep the head the same size, but it draws it at roughly 80% of the source head either way; with the face only 339 px wide in a full-body photo the gate cannot be met by crop framing.
- **Do not retry:** replicate/1 on this photo with or without `--loose-crop` (9 attempts, 9 invalid, 1,271 credits).
- **Next:** the method that worked for cell (a) (F63): a Route G objects-mode head edit of a head-and-shoulders crop of the real photo at about 2.5x with E2 and his nearest current
  photos as references, so the head size is the crop's by construction and the paste-back resizes it. Filed as a [claude] item.

### F66. Pin 9 second arm build (`pin9build2`, run 20261014_110205, 2 pictures, 259 credits): the whole-arm repaint made the arms leaner and longer, but the upper arm did not move (2026-10-14 11:3x)
- **Result:** both returns pasted back clean (ECC 0.998 / 0.976); the changes are the two grey arm shapes plus the polo's sleeve and body edge where the arm moved
  (polo region 7-15% of its pixels, arms box 36-37%); head, neck, girl (0.02), calendar and shelves (0.06) and the desk are unchanged. The arms look leaner and the near
  hand lies flat on the folder with the arm straighter (`pin9b2_review/arms_goal_base_v1_v2.jpg`).
- **Measured (ATR bare arm per torso length, `pin9build2_measures.json`):** near arm upper / forearm: v1 0.286 / 0.172, v2 0.272 / 0.165, base 0.273 / 0.181, pin man 0.301 / 0.211, target
  0.19 / 0.135, his own 0.169-0.179 / 0.122-0.127. The forearm moved 9% (v2), the upper arm 0%. The TODO's limit for a failed method was 0.23 / 0.16: **failed again** on the
  upper arm and just above on the forearm. The far arm improved (0.205 / 0.200 against 0.228 / 0.187).
- **Possible cause:** the pin man leans toward the camera, so the near upper arm is foreshortened and closer to the lens than the torso; the per-torso-length target comes from his
  frontal standing photos and may not transfer one to one. The measure counts the bare arm skin from the sleeve hem to the fingertips, and the sleeve hem's own position moves with the pose.
- **No credits spent on a third try:** the written fallback is a lighter-grey guide tube of the target width on the old centre line inside the grey (inventory `pin9build2.json`, field
  written for this case); it needs the user's answer to TODO 85 (arm size: real size / a little fuller / like the pin man) because the target itself is in question. Checklist
  v2_0r: NOT BEST, 6 failed (19, 21, 26, 28, 31, 32; stage 1 is body only); the star at x 870, y 940 remains.

### F65. Pin 12 second grey-out pass (`pin12d`, run 20261014_104657, 3 pictures): the background worked; a dark rim along the shoulder came from the paste, not from Gemini (2026-10-14 11:3x)
- **Result:** all three returns pasted back over pin12b v1_0r (ECC 0.955 / 0.965 / 0.978, pose gate 3 pass): the red-brown figure at x 750, the head-shaped blob
  at x 675 and the red column are gone in all three (plain bokeh with a cyan light and a brown column; v2 has two cyan blobs, v3 a dark grey patch at the strip's
  top left). The difference to the base: 4.3% of the picture, 0.025% (about 270 px) outside the strip and the hand box; the face rows change 0.00%.
- **Defect found at 3x:** a thin DARK RIM along the shirt edge on all three (`pin12d_review/right_bg_3x.jpg`). Cause: the paste keeps the base's own pixels outside the grey
  mask, and the 2 px clear band beside the shirt is the OLD dark background, so the new bright bokeh sits behind a dark line. (pin12b had the same rim and I missed it
  there, because the old dark bokeh hid it.)
- **Fix, three tries (`scratchpad pin12d_seam.py`):** (1) a rim mask from a brightness-built shirt silhouette ate the red letter E of the print (the shirt mask also took the
  bright bokeh as shirt: wrong); (2) a hole-filled silhouette still missed the rim (the same wrong silhouette); (3) the rim taken from the grey mask's own boundary
  (up to 4 px outside it, darker than 150, inside the strip box) and healed with cv2.inpaint (Telea, radius 3): rim gone, print and tee untouched.
  Gemini's star at the floor (727, 1143) is covered with the picture's own floor pixels 75 px lower, feathered (`v1_0r_seam_nostar.jpg`).
- **Checklist v1_0r_seam_nostar: NOT BEST, 1 failed (32: the oversized tee hides chest and waist), 10 n/a, 25 passed** (33 passes now; 35 and 34 pass).
  Leftovers: an 8 x 10 px beige notch at the strip's top-left corner (x 617-625, y 458-470) and a few pale fringe pixels at the sleeve's lower edge (x 740-760, y 650-700).
- **Lesson:** after any grey-out paste against a shirt or body edge, check the edge at 3x for the old background's dark band; heal it from the grey mask boundary, never from a
  colour-built silhouette. **Status:** held as the candidate; question TODO 107 asks for the export.

### F63. G2 cells, wave `g2a` (2026-10-14 08:46-09:21): cell (a) reads in range; cell (b) made 6 pictures and none passes the size gate; the window went from 1,163 to 58 credits
- **Cell (a), yaw -20 / pitch -40 (`g2a_cell1_send@v2`, run 20261014_084658, 2 pictures, 271 credits):** v1 reads -24.3 / -32.5 / roll 20.2 and v2
  -27.7 / -32.1 / roll 24.0 on the picture itself (headpose.py), the pin 5 source crop read -17.4 / -41.0 / roll 12.4. Against the cell v1 is 4.3 and
  7.5 degrees off (limit 8, the pitch passes by 0.5), v2 7.7 and 7.9 (passes by 0.1). The render's own pose gate FAILS 12, 12/14, 29 on both because
  it compares with the source crop (the bow is 8.5 degrees shallower and the roll 8 degrees larger than the crop's): that is not the cell test.
  Neutral closed lips (E2's smile did not leak), colour photograph, cigarette gone, one ear, tapered sides, full beard and chain. Checklist v1_0:
  NOT BEST 12, 14, 21 (identity not measurable on a bowed face), 29; the user's eye decides. v1 is the pick (closer on both axes).
- **Cell (b), yaw 0 / pitch -25 (`google-2__IMG_4446@v1`, run 20261014_085205, 6 attempts, 834 credits):** poses v2 -4.5 / -28.2, v3 -4.6 / -30.2,
  v4 -4.8 / -31.5 are within 8 degrees of the cell; identity 0.599 / 0.534 / 0.547 passes 0.52; but the head size gate fails all six
  (size ratio 0.82-0.87 against 0.94-1.10: Gemini redraws the head 13-18% smaller than the 2023 photo's head inside the 1024 px crop; the
  picture is a full-body mirror selfie where the head is 339 px of 2268). v1 reads -9.7 yaw, v5 and v6 -26 / -27.7 (out). **No picture passes; nothing to show.**
- **Credits:** the wave was queued at 500 and spent 1,105 (271 + 834): a replicate run with `max_attempts 6` costs 137-277 credits per attempt (edit plus
  two judge calls, some timed out and re-tried), not the 94 a picture costs in a Route G wave. Queue replicate jobs at 150 per attempt times
  `max_attempts`, and prefer `max_attempts 3` for a size problem that repeats the same on every attempt (all six failed the same way).
- **Cause (b):** the head is small in the frame, so the redone head inside the square crop comes back smaller; the same cause as the head-size
  limits in the replicate section of AGENTS.md. **Next:** the same photo with `--loose-crop` and `max_attempts 3`, queued for the next window.

### F62. Pin 9 build wave (`pin9build`, run 20261014_074709, 2 pictures, 257 credits): the arms barely shrank (2026-10-14 08:4x)
- **Result:** v1 refused by the paste (re-framed: ECC 0.945, scale 0.82 / 0.78); v2 pasted back clean (ECC 0.999, shift 0 px), head rows 0.00%
  changed, girl 1.2% (only at the arm edge), calendar, shelves, trousers untouched. The near forearm looks slimmer by eye
  (`pin9_review/arms_goal_base_new.jpg`).
- **Measured (ATR bare arm per torso length, `pin9build_measures.json`):** near arm upper 0.273 / forearm 0.181 (base 0.275 / 0.191, pin man 0.301 /
  0.211) against the target 0.19 / 0.135 and his own photos 0.169-0.179 / 0.122-0.127; far arm 0.228 / 0.187 (base 0.188 / 0.181): it grew.
  So the wave moved the near forearm 5%, not the 30% needed: items 26 and 32 stay FAIL; stage 1 is body only by design, so 19, 21, 28, 31 fail
  too (checklist v2_0r: NOT BEST, 6 failed). Gemini's star is still at about x 870, y 940.
- **Cause:** the same as F52 for pin 8's first wave: the kept outline of the pin man's arm leads the render, and the grey bands of this wave
  left most of the sleeve and the upper arm outside the repaint (they are cloth in the pin, so the ATR bare-arm band is hand and forearm only).
- **Next (a changed method, not the same words):** a second build with the repaint covering the whole arm outline (sleeve to wrist, both arms)
  and his casual-front reference as the only arm reference; then stage 2 (his approved 10-01 head) on the result. Filed as a [claude] item.

### F61. Pin 12 recipe v5 (`pin12c`, run 20261014_080200, 2 pictures, 282 credits): worse than the grey-out fix on background people and the print (2026-10-14 08:3x)
- **Run:** the wave stopped after 2 pictures because both failed the pose gate on items 14 and 30, which are N/A here (the pin is a back view, the
  picture is the front the user asked for). Identity 0.707 / 0.720 (accept band).
- **Worked:** the free hand and the bag smear with motion blur (item 35 passes; the base and v4 were sharp).
- **Failed:** 33 on both: blurred shoppers are back (v1: a pink-bodied figure left of the glass and a red blob at the left edge, pale figures in the
  right shop; v2: a dark head and red top at the left edge, a standing figure in the left shop, a pink figure at the far right); the paragraph's
  empty walkway and the tipped-up camera did not stop a mall from filling itself (as F51/v4). 34 on both: the print's apostrophes are the typographic
  curly ones, the pin's and pin12b's are straight (`pin12c_review/print_compare.jpg`). v2 also 19 (a long curl lock down the picture-right side).
  32 as in every pin 12 version (the tee hides chest and waist). v1 has Gemini's star ON the knuckles.
- **Cause:** a full re-render of a mall setting invents background people again; only region edits keep the background the user's earlier
  picture had. The apostrophe is a typeface choice Gemini makes when it re-draws the print; the grey-out edits keep the print pixels.
- **Decision:** v5 is dropped (do not retry). The best pin 12 candidate stays `pin12fix v1_0r` (fails 32, 33 faint, 35). Question TODO 97 asks the
  user (second grey-out pass / export as is / drop); its recommended step is filed as a [claude] item.

### F60. Pin 8 build wave (`pin8build`, run 20261014_071718): the arms are at his standard, one gate misses by 0.003, and Gemini put a light block beside the arm (2026-10-14 07:5x)
- **Result:** both returns pasted back with `--affine` (ECC 0.883 / 0.999); the head, phone, hand, cat, sweatpants, janeu and chain are the base
  pixels (region differences max 3-8, head rows 0.00%); only the arm and shoulder bands changed (1.2% of the picture), so the head was not pasted
  again (it is the approved 10-01 head already in the base). The near arm measures 0.186 / 0.192 of the torso against the standard's 0.189 (the
  base 0.211). The shoulder-width measure is unusable here (1.14 on v1, 0.60 on v2: the phone hand and the cat break the shoulder band).
- **Gemini's own pose gate on the raw returns:** FAIL 14 on both (the crop's frame); on the whole pasted picture v2 FAILS only item 29
  (torso x0.927, limit 0.93), v1 fails 14 (0.050), 29 (x0.87) and 30 (right forearm 15 deg).
- **New defect:** where the arm narrowed, the strip at the left edge (x 28-79, y 634-735) came back as a light grey block (v1 bigger, with a rounded
  tail below the strip; v2 smaller): the strip was dark grey in the pin. Repaired by copying the picture's own strip colour row by row from x 6-26
  (`scratchpad pin8_strip.py`; first two attempts ate the arm's underside rim and left a halo, so the mask now takes only pixels lighter than the
  strip's own colour, never warm skin, and below the strip only near-white leftovers). Result `v2_0r_strip.jpg`: clean at 4x except a faint
  12 px pale line under the strip beside the elbow (the strip's own lower edge).
- **Checklist v2_0r_strip: NOT BEST, 1 failed (29), 5 n/a, 30 passed.** The far arm (the one holding the cat) cannot be measured (the cat covers its
  inner edge); judged by eye on its outer contour and recorded as such in items 26 and 32.
- **Cause of the size miss:** the narrower shoulders sit about 3% lower (render y 0.36 against the pin's 0.33), which shortens the shoulder-to-hip
  line the gate calls "torso"; the base passed at the pin's size with the pin man's shoulders. Not fixed by code (the render is not rescaled).
- **Status:** held as the candidate; question TODO 95 asked in chat (export / hold / fix); nothing exported.

### F59. Pin 4 on Pro (`pin4pro2`, run 20261014_073157, 4 samples, 303 credits): none passes the pose gate; v3 misses only the size by 0.02 (2026-10-14 07:5x)
- **Pose gate:** v1 FAIL 12 (head bow +0.56 against the pin's +0.45) and 29 (x1.08); v2 and v4 FAIL 12/14, 14, 29, 30 (the man stands elsewhere,
  head yaw -7 and -41; their background restore was refused, so no `r` file); **v3 FAIL 29 only (size x1.09 against 0.93-1.07)**: head position 0.010,
  bow +0.46 against +0.45, neck 3 deg, forearm 2 deg, hand 0.020, body 0.014, all within the limits. Face light x1.27 and face/neck 1.27 OK on v3;
  v1 x1.43 and 1.12 and v2 x1.66 and 0.53 read as pasted in.
- **Checklist v3_0r (restored, no sparkle): NOT BEST, 3 failed (21, 29, 34), 6 n/a.**
  - 29: measured, not explained away.
  - 21: the camera hides eyes and nose as in the pin, so no face is found and there is no identity score; hair, beard, jaw, ear and skin
    match IMG_6858 by eye only.
  - 34: the pin's camera plate reads mirrored FUJIFILM (a mirror shot); the render's 8 glyphs are soft and not in the same orientation
    (`pin4_review/camera_plate_zoom2.jpg`).
  - Seen at 4x and written in the note: a 12 px light wall sliver at the left edge beside the raised arm (the pin's arm reaches the edge;
    the render's outline is about 12 px narrower there), while the arm angles pass the gate.
  - Passed with evidence: 19, 26, 28, 31, 32 (waist and hips are out of frame: named), 33, 35, 36 (janeu from the picture-left shoulder,
    chain on the sternum, beside pumped_front).
- **Cause of the size miss:** Pro frames the man 9% larger than the pin (`size = shoulders-to-nose x2.2`); the same pose in v1 gives x1.08.
  A re-frame is not available to the restore (it keeps the pin's pixels, not the render's scale).
- **Status:** held as the candidate; question TODO 93 asks the user (export / hold / fix); nothing exported.

### F58. Pin 12 grey-out fix (`pin12b`, run 20261014_065449): the right-hand passer-by is not gone, no picture is best (2026-10-14 07:3x)
- **What came back:** three returns, all pose-gate PASS, all pasted back over the base `v1_0.jpg` (ECC 0.999 / 0.954 / 0.993, shift 0 px); the
  pixel difference to the base is only the three grey patches (0.95 / 1.88 / 1.06 % of the picture) plus JPEG noise on the print (max 11).
- **v1 (best):** the left patch is clean (the dark head-like spot is gone) and the red column faded, but a faint red-brown vertical figure at
  about x 750, y 480-600 and a dark head-shaped blob on the right shoulder (x 675, y 520) still read as a passer-by: item 33 FAIL.
- **v2:** worse than the base: a flat pink block on the left, a new bright red rectangle on the right and a hard dark rim along the shoulder
  (items 8, 11, 33). **v3:** a thin red streak from the ceiling light down to y 640 stays (33).
- **32 and 35 fail as in the base** (the oversized tee hides chest and waist; the free hand and the bag are clean and unblurred), so a fixed
  background alone would not have made it best.
- **Cause:** the grey-out repainted only the red column's top and the left spot; the figure's lower part and the head-shaped blob sat
  outside the grey bands (the diff components: x 645-802, y 406-663 on the right), so Gemini kept them as existing lines.
- **Next:** recipe v5 (frozen 10-09, dry run = the lock today) queued as `pin12c`: a camera tipped up so only ceiling lights and the rail are
  behind him, an empty walkway, and motion blur on the bag and hand, which answers 33 and 35 together. Nothing exported. The sparkle at
  the base's floor (727, 1143) is removed with the picture's own floor pixels only on an export.

### F57. A wave "running" for an hour with nothing rendering: the ping read the memory gate as busy (2026-10-14 05:47-06:45, pin12b)
- **What happened:** the 05:47 tick started `pin12b` with 2,400 credits; its driver stayed alive, but every 5 s the log said
  `memory: pin12_next1 waits (free memory 0.7 GB < 1.5 GB)`. The ping printed `NOOP: busy: wave(s) running` at 06:01, 06:12, 06:25 and
  06:42, so nothing rendered for 55 minutes and I answered "no change" twice (liveness, not progress: the exact case in the standing rule).
- **Cause:** `decide()` treated "a wave driver is alive" as busy, with no look at its log; the machine sits near 0.7 GB available, while the
  gate (set after a run starved at 0.37 GB free) needs 1.5 GB for 60 s.
- **Fix:** `memory_blocked()` in `tools/autocontinue.py` reads each running wave's log; a run of memory-wait lines older than MEM_WAIT_MIN
  (10 min) makes the ping a WORK ORDER ("FREE MEMORY") instead of NOOP, and STALLED/toast rules then apply as for any other stall. The
  order's text: close only what the user allowed as idle (Claude Code tabs idle over an hour with no timer or background job, never this
  tab), check an app's children and CPU first, never the job bots, his Edge or VS Code; the gate itself stays at 1.5 GB.
- **Done by hand at 06:45:** four Claude Code tabs closed (github-68 idle 8.5 h, github-5d 16.9 h, github-bd 2.8 h, github-db 1.6 h; ~830 MB
  with their helpers; their history stays and typing in one resumes it). The opencode server was NOT closed: a research session was running
  in it (13 yt-dlp searches at 05:41). Left alone: his Edge (3 GB, 25 tabs), the bots' browsers, Pylance (870 MB).

### F56. Pin 6, the approved 10-01 head reused on the pumped body: close, not good enough (2026-10-14 04:2x, `v4_0r`, no credits)
- **Result:** one ear, one pencil at the pin's angle (44.4-45.8 against 44.5), B&W kept, only the head zone changed (max 3 outside). His face reads
  as him. Whole-picture pose gate FAIL: shoulder midpoint 0.054, bow +0.74 against +0.61, size x1.10 (the 10-01 picture's own readings: 0.051,
  +0.75, x1.13). At 100%: a pale halo follows the head outline on the wall (the 10-01 wall is about 10 levels lighter), the neck skin is lighter
  than the shoulder, and the pencil crosses the beard below the lower lip instead of sitting between the lips.
- **Note:** the user withdrew his 2026-10-01 "sufficient" for exactly this head (pencil held by the chin, head placed oddly on the body, wrong
  body): the body is fixed, the head's pencil and bow are not.
- **Three head routes failed on pin 6** (F48, F55, this). The picture is shown to the user as the best so far, for his decision; no fourth
  method is started without his answer.

### F55. Pin 6 head v2 (grey face and pencil, ear kept): re-composed returns, a second ear, the pencil at the wrong angle (2026-10-14 03:32)
- **Result:** neither return could be pasted (re-framed: ECC 0.508 / 0.625 and 0.640 / 0.767). Forced pastes read: the pin's ear kept (max diff 1) but
  his redrawn ear sits lower and larger beside it (double ear); the head roll 47-50 degrees against the pin's 38.8; bow +0.79 / +0.84 against
  +0.61; size x1.17-1.19; one pencil now but at 27-29 degrees against the pin's 44, its far end elsewhere; a pale wall patch inside the grey;
  marble invented at the bottom; whole-picture pose gate FAIL (12, 12/14, 14, 29). The face reads as him.
- **Cause:** a strongly bowed, tilted profile (roll 39 degrees) with a pencil: Gemini re-composes the whole crop to a more upright head with a
  bigger skull than the pin man's, whatever the grey pins.
- **Two methods failed** (v1: head crop with the pencil band kept; v2: grey face and pencil, ear kept). Do not retry a third grey variant.
- **Next:** the only approved pin 6 picture came from the 2026-10-01 run; its head is user-approved material (as on pin 8): reuse it, aligned,
  pasted with a wide feather and the pencil's whole path, on the stage-1 body. No credits.

### F54. Pin 9 v3 (body only, casual-front): the arms keep the pin man's mass (2026-10-14 03:08, `pin9b` run 20261014_030859)
- **Result:** v1_0r passes the pose gate and the restore (v2_0r fails item 12 only); NOT BEST as stage 1: the arms are as heavy as the pin man's (26/32).
  The head is Gemini's, with glasses the pin man does not wear (stage 2 replaces it).
- **Measured** (ATR bare-arm thickness across the arm's axis per torso length, upper-arm half / forearm half; `forearm_atr9.py`, scratch `pins91213`):
  the pin man's near arm 0.301 / 0.211, v1_0r 0.275 / 0.191 (97 / 67 px), the 10-09 v1_0 0.279 / 0.201, the 10-01 best 0.248 / 0.176; the far forearm
  about 0.22 by skin colour. His arms: casual_front 0.179 / 0.122 and 0.169 / 0.125, IMG_6923 Copy 0.169 / 0.127, pumped_front 0.183 / 0.125,
  his side-lit photos 0.185-0.22 / 0.10-0.16. So the render is 1.5-1.6x his relaxed arm. (The silhouette run through the arm's axis merged
  with the dark polo and was useless here: only the bare-arm labels separate the arm.)
- **Cause:** the kept outline again (F46, F52). **Fix queued:** `pin9build` (grey-out of both arm edges, targets 0.19 / 0.135, shaves 30 / 19 px near,
  12 / 28 px far); stage 2 (the head) after it, the 10-01 head or a region edit. **Open.**

### F53. Pin 4 on Pro: both pictures miss the pose gate, v1 narrowly (2026-10-14 02:41, `pin_783485666539777050@v2`, 188 credits)
- **Result:** v1_0 fails only item 12, head bow (nose below the eye line +0.54, the pin +0.45, tolerance 0.08); v2_0 re-framed (items 12, 12/14,
  14, 29, 30). The restore refused v1_0 (re-framed, shift 0.049 of the frame), so the room, the camera plate and Gemini's sparkle star are not
  restored. By eye v1_0 is the closest pin 4 so far: his curls and beard, a silver chain with pendant, a thin thread down the chest, the
  pin's raised arm and camera hold. A Pro picture costs about 94 credits, so the stop-after-2-fails rule saves little here.
- **Next:** pin4pro2, the same recipe with 4 samples and no early stop; the pictures that pass the gate or narrowly miss it are reviewed and
  the restore checked for each.

### F52. Pin 8 v3: the arm holding the cat keeps the pin man's mass (2026-10-14 03:00, `v3_0r`)
- **Result:** the head (the user-approved 10-01 head pasted with a 16 px feather), janeu, chain, cat, room and the pose gate are right. At one
  scale beside `pumped_front.jpg` the arms looked far bulkier than his standard (items 26/32).
- **Measured (per torso length):** the shoulder line is already his (0.909 against 0.89-0.91 in his photos); the cat-holding upper arm is
  about 0.26 against 0.19-0.22 (about 36% over); my first reading of the whole body as "bulkier" was partly the side-by-side's scale (the head
  here is 13% small against the torso, so eye-distance scaling inflated everything).
- **Cause:** the kept outline (the pin man's arm); Gemini keeps an outline it is given.
- **Fix queued:** `pin8build`: the band along each upper arm's outer edge and the shoulder tops painted grey and repainted as wall (28 / 11 / 8 px).

### F50. Pin 8: redrawn hair left a ghost second brow and a light band on the forehead (2026-10-14 02:30)
- **Result:** the hair edit on pin 8's v2_0r put his curls in, but where the new hair met the pin's old bangs a second brow and a light band
  remained (plain paste added a pale ceiling halo and a doubled brow as well; a custom mask fixed the halo).
- **Fix:** the head of the version the user approved on 2026-10-01 (his face with curls, the same pin) was aligned (landmark similarity,
  median residual 0.5 px) and pasted with a 16 px feather: `v3_0r`, no ghost, no band.

### F51. Pin 12 v5 and pin 13 v6 were queued for 2026-10-10 08:20 and never ran; pin 13's base was read as "a sliver of beard" (2026-10-14 02:2x, found by the backlog 5 review)
- **What happened:** the memory note said the morning wave `pins1013e` held pin 12 v5, pin 10 v6 and pin 13 v6. `.cache/wave_pins1013e.json` was
  overwritten at 02:51 on 10-10 by the pizza and smile jobs (the tag was reused), so pin 12 v5 and pin 13 v6 were never started; pin 10 v6 ran in
  `pins1013g`. Pin 13 v6 had also stopped once at stage 04 on 10-09 20:58 ("the Gemini session expired while this run waited for credits"; the
  window held 158 credits and the session was fine: the false alarm of the memory note). Both recipes were frozen and then forgotten for four days.
- **Also found:** pin 13's stage-1 base (v5 v1_0r) was recorded as "the head already turns slightly toward picture-right, a sliver of beard shows".
  At 4x it is a rear profile: ear, a strip of cheek, the beard and the nose tip show, the head turned about 100 degrees from the camera; only the
  smile is missing. v6 (a whole-frame edit turning the head "about 50 degrees") was written for a head facing away and would have overshot.
- **Cause:** my process: a wave spec file reused under an old tag, no check that a queued recipe has a run folder, and a base judged at thumbnail size.
- **Fix:** pins 9, 12 and 13 queued under new tags (pin9b, pin13b, pin12b) with the F39-F47 methods; v5 and v6 stay frozen, unqueued (v5 is pin 12's
  fallback; v6 is obsolete). Rule: a new wave gets a new tag, and `tools/autocontinue.py status` is the only list of what is queued; look at a
  base head at 4x before writing a head edit.
- **Open:** whether the three queued versions pass (pin9b, pin13b, pin12b).

### F49. The auto-continue state file collided under four agents (2026-10-14 02:3x)
- **What happened:** `autocontinue.py reviewed pin4` died with `PermissionError: WinError 32` while replacing `.cache/autocontinue.json`
  (the temp file was open in another process), so pin 4 stayed "to review". Several agents ran `todo`, `start-todo` and `add` at the same time;
  each command read the file, changed it and wrote it back, so two commands could also overwrite each other's change.
- **Fix:** every command now runs under a lock file (`.cache/autocontinue.lock`, O_EXCL, waits up to 150 s, a lock older than 10 minutes is
  taken over) and saves through a per-process temp file. The failed command was re-run. Closed.

### F48. Pin 6 stage 2 (his head by region edit on the pumped body-only picture): pose gate fail, two pencils (2026-10-13 22:47, `pin6head_send@v1`)
- **Result:** v1_0 refused at the paste (ECC 0.922, scale 1.013 / 0.863: the head came back re-composed and upright, pitch -25 against the pin's
  -37). v2_0r pasted (ECC 0.971; only the head and neck changed; the pencil's own pixels untouched; B&W kept, max channel difference 8) but the
  whole-picture pose gate FAILS: shoulder midpoint 0.063 (limit 0.04), head position 0.048 (0.04), size x1.10 (0.93-1.07), head direction 22 deg
  off (15); roll 50.5 against the pin's 38.8. At 100%: two pencils (the pin's kept one across his beard plus one Gemini drew in the mouth), a
  pale wall patch with a hard curved edge, a dark smudge, a vertical seam on the shoulder at the crop's edge (x 290), and the ear 45 px right
  and 15 px down from the pin's. The face reads as him (curls, full beard).
- **Cause:** the pin's strongly tilted bowed profile (roll 39 degrees) is normalised by Gemini when it redraws the head; the pencil kept by the
  mask meets a second one drawn in the mouth; the crop edge cuts through the shoulder.
- **Next:** the pencil is greyed with the face so Gemini draws one pencil in the mouth and the paste carries that pencil; the ear's pixels stay
  the pin's (it fixes the skull's position and roll); the crop edge moves to smooth background, with a wide feather.

### F47. Auto-continue sat idle for 10 hours with 2,240 of 2,400 credits unused (2026-10-13 04:30-18:13)
- **The user (18:0x):** "Make the auto continue look into the fire [5-hour] window and the credits left as well. Since so much credit is left,
  why are you not processing anything? ... It is ideally just hitting periodically without processing anything. If there is any process, any
  to-do item, only then use auto continue. If you are using auto continue, then at least do the to-do work."
- **Evidence:** from 14:40 every tick read "idle: nothing queued, nothing to review, no [claude] to-do" while the results folder lacked pins 6, 8,
  9, 12 and 13 and pin 14's Gokarna place was open; the 17:33-19:33 window ran down with 2,240 credits (the previous window ended the same
  way at 2,277).
- **Causes:** (1) `decide()` read only the queue and my own to-do list: the remaining goals were never to-do items, so "no work" meant "no
  filed work", and the credits and the reset time were not looked at; (2) three identical timer jobs (one per restart, never removed) fired the
  long prompt up to three times per half hour, each answered "no change"; (3) the prompt carried the whole procedure, so every quiet tick
  cost a long prompt and the real work lived in prose, not in the tool.
- **Fix (`tools/autocontinue.py`):** a standing `backlog` of the user's remaining goals (`backlog add|done|list`); `decide()` shows the credit
  window with the time to the reset and, when the window still holds at least 600 credits after the queued waves, nothing is queued and fewer
  than 2 waves run, it makes the backlog's first goal the work (`work: spare credits (...): take backlog N`); `ping` prints `NOOP: <decision>`
  when there is nothing to do and otherwise a work order that lists the tasks themselves (waves to review, ready to-dos, questions to ask,
  the spare-credit goal) with the rules. One timer job now runs `ping` every half hour.
- **Seeded backlog:** pin 14 Gokarna place; pins 8, 6 and 4 redone by the pumped yardstick with the janeu (the approved 2026-10-01
  pictures of 6 and 8 predate it and are not in the results folder); pins 9, 12, 13 reviewed and advanced; G2 head-angle cells.
- **Also found:** pin 15 (user-approved) was missing from `D:\FacecardResults`; the cause is unknown; re-exported 2026-10-13.

### F46. Pin 14 v5 (head region edit on the ghost-fixed body): the head is right, the body is narrower than his (2026-10-13 04:02, `pin14head3_send@v1`, 125 credits)
- **Result:** 2 returns pasted back (ECC 0.90). On the whole pin v2_0r passes the pose gate (body shift 0.006, head 0.021); v1_0r fails only
  the left forearm (19 deg). The head keeps the pin's cap, place, bow and gaze and reads as his: curls under the cap, full beard, his ear.
  Only the head and neck changed (max 4 below y 0.65).
- **Failed (checklist, NOT BEST):** 26 and 32: the shoulders and arms are narrower and thinner than `pumped_front.jpg` and than IMG_7008
  at one scale (`body_check.jpg`); 21 and 31 await the user's eye (a clear profile under a beard cannot be measured).
- **Cause:** pin 14 v4 stage A pasted back only the pin man's outline grown 10 px (`pin14v4_mask.png`), and Gemini kept that outline too, so a
  build wider than the pin man's could not be drawn: the user's "the physique ... is not looking like mine" (F28) was only half fixed (the
  skin tone, the tattoos and the janeu are, the width is not).
- **Next:** a body edit whose mask also covers the band around the arms and shoulders where his build is wider, the background there
  redrawn from the hillside; his shoulder width and arm size from the pumped standard, the torso size inside the pose gate (0.93-1.07);
  then the head again on that body.
- **Closed 2026-10-13:** `pin14body2_send@v1` v3_0r (shoulders +6%, 0.739 of torso length against about 0.89 for the standard; whole-pin
  pose gate PASS; edges clean at 3x/4x): the user, asked "Does this look like you?": "Yes, export it". Exported as
  `motorcycle-outfit-men_14_..._v3.jpg` (BEST user-approved; items 21, 26, 31, 32 on record). The background is still the pin's own coast:
  the Gokarna place (stage C) waits for the Togedr photo (TODO 42), else the text place.

### F45. Pin 14 stage B, head swap (replicate, zone head): 0 of 6 usable (2026-10-12 17:05, `pin14head@v2`)
- **Result:** all invalid: head size x1.04-1.47 (limit 0.94-1.04), the head moved (face shift 0.13-0.30, limit 0.12), v3 also 37.7 lighter
  than the photo and a changed head angle. The head region held (the crop was on his head, F43 fixed).
- **Cause:** the far face again (55 px, turned about 80 degrees away): a whole-head redraw from his references comes back large, as on pin 16
  (F34, F36). Most of his face is hidden in this pin anyway: what shows is the hair under the cap, the beard edge, the ear and the skin.
- **Next (method):** a Route G region edit of the head crop (objects mode) that keeps the head's size, angle and place and changes only what
  shows: the pin man's hair to his curls, the clean cheek edge to his beard, the ear and neck to his skin, with his real profile photos facing
  the same way as the reference. Region edits keep what is drawn (the habit that hurt the janeu helps here).

### F44. Pin 16 eyes-only region edit: Gemini kept the far eye's gaze (2026-10-12 16:52, `pin16eyes_send@v2`, 4 samples)
- **Result:** all four pasted back cleanly (ECC 0.987-0.998; only the eye ellipses changed, max 7 outside). Openness inside his band in all;
  eye agreement -0.01 / -0.03 / -0.02 / -0.09 (base -0.07; his band -0.34..-0.18): none better than the base, three slightly worse.
- **Cause:** the same habit as the janeu (F33, F37, F39): an edit keeps what is already drawn; words and his eyes as a reference did not move
  the iris. Gemini also sharpened the crop in v2-v4.
- **Next (method):** the grey-out that moved the janeu: grey the far eye (sclera and iris inside the lids) so Gemini must draw it, with his
  eyes at the same turn as the reference; the eye gate measures each pasted return and only one inside his band counts.

### F43. Pin 14 stage B: replicate's face detector took his torso for the face (2026-10-12, `pin14head@v1`, never run)
- **The ghost fix passed first:** ghost-fix v1_0r reads 5.6 / 5.9 along the old cord's path (bare skin about 6; before 8.0 / 13.5), the
  new thread unchanged (27.7 against 29.2).
- **What happened:** freezing the head swap, the face detector picked a "face" on his bare torso (box 246,602, 138x214) over the real,
  small head (357,487, 61x86), threw out the correct AI head box as implausible, and built the crop [0,242,729,729] around the chest.
  The recipe is frozen but is never queued.
- **Cause:** a small, turned-away head above a large, lit bare torso; the detector's largest-face choice has no sense of where a head can be.
- **Fix:** an opt-in head region for `recipe new --method replicate` (the box the face is searched in), recorded in the recipe; old recipes
  compile unchanged.

### F42. Pin 16's eyes look in two directions: the cause of his "eye condition" instinct (2026-10-12, measured)
- **The user:** "less open ... something more than just spacing ... one eye is looking 75° to the left and another ... 80° or 85° ... it
  looks like an eye condition, which I actually don't have".
- **Measured** (`eye_measure.py`: 2dfan4 eye outlines, a dark-iris locator, headpose; stable to 0.04 when his photos are shrunk to the
  renders' 32-46 px eye distance): eye agreement (the picture-left iris's place between its corners minus the right one's) is -0.32 to
  -0.20 on his photos at 27-31 degrees and -0.32 on the pin's own real face; the base and every redraw read -0.07 to -0.14: the far eye's
  iris sits mid-eye, too near the nose. Openness and the eye-to-nose distances are inside his bands.
- **Cause:** the Route G render drew the far eye's gaze wrong, and zone face keeps the base's eyes, so every redraw inherited it (all six
  zone-face returns fail the new gate).
- **Decision:** `pin16fix_face@v4` (zone face + `--eye-gate`) removed from the queue before it ran (it could only select among returns that
  keep the same eyes). Next: a region edit of the eyes only, with his real eyes at the same turn as the reference, the eye gate choosing
  among returns, pasted back over the eyes alone.

### F41. Pin 14 janeu by grey-out: the new thread is right, a faint ghost of the old cord is left (2026-10-12 06:14, `pin14janeu3_send@v1`)
- **Result:** v1 pasted back (ECC 0.992; only the bands changed, max 6 outside, no grey left): one thin diagonal from beside his neck at
  picture-right to the top of his hand at picture-left. v2 re-framed (976x1091) and was refused by both fits.
- **Failed:** a faint ghost of the old cord runs beside the new thread from the lower chest to the waistband (thread detector 10-22 along
  the old path, bare skin 3-12, the old cord 43-69): two threads at 2x, faintly at 100%.
- **Cause:** the grey band over the old cord was narrower than its soft edge and shadow, so a trace of the old cord survived around the grey.
- **Next:** a second, smaller grey-out on this result: a band over the ghost only (lower chest to waistband, wider than the ghost's soft edge),
  his skin there; the new thread's pixels stay; paste back that band only.

### F40. Pin 16 zone face with a mixed set: the gates pass, the face stays the base's (2026-10-12 04:01, `pin16fix_face@v3`)
- **Result:** v1_0 ACCEPT (size 1.00, light dE 5.5, neck gap 6.0, identity 0.543); v2_0 invalid (size 1.127, head angle); v3_0 uncertain.
- **Seen:** the base, v2 and v3 are nearly one face side by side: replicate's zone face on his own generated head keeps that head's face, so
  the references change little; the user called the base "almost there but still not accurate" and chose "Neither yet" for v2.
- **Lesson:** more face-only tries on this base are cosmetic variations (do-not-retry). The next version needs to know what he sees as off.
- **Status:** pin 16 waits for his answer (question "Pin 16 off").

### F39. Pin 14's janeu fix left the cord where it was (2026-10-12 03:16, `pin14janeu2_send@v1`)
- **Result:** both returns differ from the crop sent by a grey difference of only 4.4-4.9: the thread still hangs from beside his neck down
  the picture-right side of his chest and curves across the lower stomach (the old J shape), not IMG_7002's single diagonal. The band
  paste changed nothing that matters (and pin 15's detector, on this sunlit crop, also caught his rim-lit outlines: bands of 31-34%).
- **Cause:** Gemini keeps a line that is already in the photo; words asking for another path do not move it (F33, F37, now F39).
- **Next (method):** take the old cord out of the photo first and give the thread no existing line to follow: grey out a band along the old
  cord and a band along the target diagonal (the grey-out method of the physique work), so Gemini must draw skin over the old path and
  the thread along the new one; paste back only those bands.

### F38. Pin 16 zone face with the daylight faces: every gate passes, the likeness is not better (2026-10-12 03:32, `pin16fix_face@v2`)
- **Result:** v1_0 ACCEPT (size 1.038, light dE 3.5, neck gap 7.0, identity 0.584); v2_0 invalid (size 1.127, head angle, expression);
  v3_0 uncertain (identity 0.501). The size and the light are inside their gates together for the first time on pin 16.
- **Failed (checklist, NOT BEST):** 21: not verifiably more accurate than the base the user called "almost there but still not accurate"
  (identity 0.684 -> 0.584, the face changed little); 31: cheeks a little fuller and skin smoother than his photos (cheek_iod 2.41 against
  2.29-2.36; the freeze's scene reading asked for "smooth and clean skin").
- **Cause (assumption):** me-day's three faces are all frontal; the pin's head is turned about 27 degrees, so Gemini has no real photo of him
  at that turn and fills the shape in.
- **Next:** the user's eye on base vs redraw (question), and a mixed face set: his daylight front photos plus me@v2's real three-quarter photo
  on the pin's side of the turn.

### F37. Pin 14 v4 stage A (torso and arms region edit at 2x): the pose holds, the janeu hangs straight down again (2026-10-12 02:03)
- **Result:** v1 pasted back with `--affine` (ECC 0.946, scale 1.000); v2 refused (no clean fit, ECC 0.843). v1_0r passes the pose gate in
  full against the pin (body shift 0.003, head 0.002, size x0.97, every limb inside its limit); the tattoos, bracelet and rings are gone, the
  chain is silver with its pendant, the skin warmer than v3's.
- **Failed:** the janeu is drawn as a cord hanging straight down from his neck to the waistband, the second time (F33), although the item said
  "one diagonal ... never hanging straight down": Gemini's habit (P4), so the words are not repeated.
- **Next (method):** a narrow-band janeu fix on v1_0r, as on pin 15 (F30): a region edit of the chest with his real photo of the janeu
  across his chest as the reference, pasted back only along the old cord and the new thread; then stage B (his head).

### F36. Pin 16's placement pass kept the head too big (2026-10-12 02:17, `pin16s2_head@v3`, about 140 credits)
- **Result:** 4 of 4 invalid on size (x1.111-1.139, limit 0.94-1.04); the light stays fixed (dE 11.4-12.1, neck gap 0.1-0.8); v1 and v3
  also changed the expression.
- **Cause:** the head sent back as the placement reference (test v2_0, ranked best by the AI's expression comparison) was itself x1.139, so
  the pass held a head that was already too big; the pass that worked in September placed a head that was too SMALL (0.923 -> 0.981).
- **Lesson:** a placement head is chosen by its measured size, never by the expression rank alone. Do not repeat the pass with another
  oversized head (every test head was x1.08-1.18).
- **Next:** a structurally different route for the far face: zone face on pin 16's own Route G v2_0r (his head is already there at the right
  size; F16's attempts there came back only 5-6% larger, and failed mostly on the light, which the daylight faces now fix).

### F35. The Togedr photo through his Edge: the Playwright extension does not connect (2026-10-12 02:2x-02:5x)
- **What happened:** Playwright MCP 0.0.83 (`--extension --browser msedge --profile-dir-name Default`), driven from a small stdio client
  (`scratchpad/pw_client.py`; the session's own MCP tools load only after a restart). Try 1 (no token) opened the post in a new tab, then
  the page read hung 120 s and the script ended without closing that tab. Try 2 waited 300 s for the connect step. With the extension's
  token (stored in the vault as `playwright-ext:token`, he pasted it in chat), tries 3-6 failed: "Playwright extension did not connect
  within 30s after opening the connect page. Make sure the extension is installed in the Chrome profile "Default" and
  PLAYWRIGHT_MCP_EXTENSION_TOKEN matches its token." My reads of "no tab found" in tries 3-5 were that error, not his tabs.
- **Cost:** no photo; each try may have left a Playwright connect page open in his browser (he is told to close them).
- **Cause (unknown):** the assumption is that the extension sits in a different browser or profile than Edge's `Default` ("Profile 1"),
  or that the token no longer matches. Stopped after six tries; the next step is his (question "Edge connect").

### F34. Pin 16's daylight face test: the light is fixed, the head is still too big (2026-10-11 23:33, `pin16s2_head@v2`, 136 credits)
- **Result:** with the test character `me-day@v1` (his real outdoor photos IMG_6844/6846/6845, all frontal), the face light came back at
  dE 10.1-13.4 (v1 with me@v2's indoor faces: 33-35, limit 20) and the face-to-neck gap 1-8 (v1: 14-27, limit 10): F27's cause was the
  references, and daylight references fix it. Identity 0.50-0.61 (v1 0.76-0.79; only frontal faces in the set).
- **Still failing:** head size x1.08-1.18 in all 4 (limit 0.94-1.04); attempts 3 and 4 also changed the expression. The probe's cause: a far
  face (about 70 px) comes back large (the 2026-09-23 survey: 142-227 px faces 0.98-1.03, a 109 px face 1.19), and the visible forehead
  and his full beard widen the face box over the pin man's fringe and clean jaw.
- **Next:** the placement pass (the best first-pass head fed back with "exactly this position and size") fixed size on another man's
  photo before (0.923 -> 0.981), but it sends a generated face, which needs his OK (question).

### F33. Pin 14 v3 stage A, body only on the whole pin: both pictures fail the pose gate (2026-10-11 23:46, 140 credits)
- **v1_0r:** the pin man's head kept, but the arms moved (item 30); the skin came out light peach, not his warm brown; the janeu drawn as a
  cord hanging straight down from the neck to the waistband instead of diagonally from his left shoulder (picture-right) to his right hip.
- **v2_0r:** re-framed and zoomed in, the head bowed and turned (items 12, 14, 29, 30): P4.
- **Cause:** on this pin the head is small and the torso large, so a whole-frame edit leaves Gemini the whole picture to redraw; body only held
  the posture on pins 15 and 16, where the head is big in the frame. The janeu wording was right; Gemini drew its own idea of a thread.
- **Next (method change):** a region edit of the torso and arms only, sent at 2x (the torso was 365 px in the whole-frame return, the reason
  it read smooth), pasted back inside his outline, so the head, the background and the frame keep the pin's pixels.

### F32. Pin 10 stopped by the user: it misrepresents his height (2026-10-12 01:3x)
- **The user,** on v7's two sparkle-fixed pictures: "stop working on this image it misrepresents my height, i am taller than this as seen
  from full body reference image."
- **What my checks missed:** no item measures his height or proportions (head size against his whole height, leg length against the
  torso) beside his full-body reference. The pose gate measures the torso against the goal's (x0.93-1.07), item 29 the shot size and item
  32 the build, so a figure kept inside the pin man's outline passes with the pin man's proportions.
- **Status:** pin 10 closed, no further versions. Candidate check: his proportions beside his full-body reference (IMG_6923 Copy,
  `pumped_front.jpg`) at one scale wherever his legs show; record-only until the user approves it as a gate.

### F31. Auto-continue sat idle for five hours with three [claude] to-dos open (2026-10-11 17:18-22:30)
- **The user (22:2x):** "why is the decision idle and nothing is queued when you already know there are so many to-do items in the list? The
  auto-continue system seems faulty."
- **Evidence:** `.cache/autocontinue.log` says "idle: nothing queued" every 15 minutes from 12:45 to 22:15, with one wave in between
  (pin15stub, 16:46); nothing advanced after 17:18. The 17:33-22:33 window ended with 2,277 of its 2,400 credits unused (`.cache/quota.json`).
  I answered the loop "auto-continue: no change" at least four times.
- **Causes:**
  1. `decide()` looked only at the queue: with it empty it returned "idle" before reading the to-do list or the credits, so a list full of
     work read the same as no work.
  2. Only my loop turns a to-do into a queued wave, and I held every remaining step behind a question to the user: TODO 17 behind 18 (daylight
     face references), TODO 20 behind 19 (what "ref goal images" means), and pin 17 v2 (TODO 2) filed as the user's. That broke the rule of the
     same morning (memory `facecard-autocontinue`: queue the recommended default, ask only what is the user's call).
  3. The loop prompt let me reply "no change" whenever nothing had changed, and nothing measured progress, so the stall raised no alarm.
  4. Smaller: the log's hourly de-duplication compared the wrong part of the line (`split(" ", 2)`), and the credits were read only for a
     queued wave, so the reading stayed at 21:20.
- **Fix (`tools/autocontinue.py`, 22:35):**
  - The decision is `work` while a wave waits for review or a [claude] to-do is ready, and `STALLED` after 60 minutes without progress (a
    wave queued, started, ended or reviewed, a to-do done); the tick then sends the user one Windows toast per stall.
  - A [user] item is only an approval or the user's own choice. A question takes `--default`, which files the recommended step as a [claude]
    item done at once; `--after <tag>` marks the only [claude] items that may wait (for a wave).
  - The loop prompt (cron `5bbd5fdc`) may answer "no change" only on idle, busy, waiting or ready.
  - Questions 18 and 19 withdrawn, their defaults put into TODO 17 and 20; TODO 2 is mine.
- **Status:** fixed; `status` reads "work: 3 [claude] to-do(s) ready". The STALLED path has not fired for real yet; the toast call was run
  once by hand (22:33).

### F30. Pin 15's exported picture "visibly shows erase and drag tool usage" (2026-10-11 16:25)
- **Cause, measured** (difference map against v3 v1_0r): the janeu fix pasted Gemini's redraw over 41% of his back. That redraw is softer than
  the phone photo, so the patch reads as airbrushed; it carries a smeared highlight beside the new thread near the shoulder blade; and a short
  stub of thread was left below the new thread's end (top-hat strength there: 59 in Gemini's return, 13 in the original, so Gemini drew it).
- **My mistake:** I passed the picture without a difference map; the patch was visible at full size.
- **Fix:** withdrawn from the results folder; the same return re-pasted only along narrow bands over the old and the new thread (3.6% of the
  crop, `v2_0r_band2.jpg`: his skin elsewhere is the original again); the stub and the janeu's short end go to a small targeted edit
  (`pin15stub_send@v1`) pasted along bands only.
- **Rule:** a fix of a thin detail (a thread, a ring, a mark) is pasted only along a narrow band around it, and every pasted picture is checked
  with a difference map against its base before it is called done.
- **Result (17:20):** the stub fix (`pin15stub_send@v1`, 2 returns, ECC 0.978 / 0.974) removed the stub and continued the janeu; the
  difference map against v3 v1_0r shows only the two thread paths changed. `outputs/20261011_164737_goal-pin15stub-send/v1_0r.jpg` passes 32
  items, fails only 14 (shoulders), and waits for the user's approval (his earlier one was for the patched version). Closed as a defect.

### F29. A fix recipe was written into its parent pin's recipe folder (2026-10-11 16:09)
- **What happened:** `pin15janeu_send` v2 was saved as `v4.json` inside pin 15's folder: once a fix is filed under its pin's name in
  `results_names.json` (for the export), `recipe_dir` points at the pin's folder, `next_version` counted the pin's versions, and `load` of plain
  `pin_783485666540141726` would then have returned the fix. The dry run showed it: it loaded pin 15's v2 instead of the new recipe.
- **Fix:** `recipe.py` `recipe_files` / `home_dir`: a key finds only files whose recipe id is that key (its results-name folder and
  `recipes/misc/<key>`), and a new version goes beside its own earlier versions, never into another recipe's folder. The misplaced file moved
  to `recipes/misc/pin15janeu-send/v2.json` (never run). Every reference resolves to its own id. Closed.

### F28. Pin 14: the user rejects both Gokarna pictures my checklist passed (2026-10-11 16:10)
- **The user:** "something looks off. It is not replicating the ref goal images as it is. Both V1 and V2. Also, the physique that it is giving
  me is not looking like mine, and the face looks off. In terms of leanness and body fat percentage, the face still looks a lot leaner than the
  body."
- **What my check missed:** items 21 (the face), 31 (the face against the body: the user's pin 10 complaint again, "face looks a lot smoother
  compared to body"), 32 (his physique) and 26 (the references not replicated). I passed them on the pose gate, the edges and the body standard
  beside it, not on whether the body and face read as his together. Both pictures were withdrawn from the results folder.
- **Open question for the user:** "ref goal images": the pin's own pose and framing, or the Gokarna location photos (the Facebook one was never
  readable and the Instagram one was not sent)?
- **Status:** open.

### F27. Pin 16 head swap: the best identity yet, but every head too bright and too big (2026-10-11 12:32, `pin16s2_head@v1`)
- **Evidence:** `outputs/20261011_123206_goal-pin16s2-head/run.log`: identity 0.76-0.79 (the pin's best so far), but all 4 attempts gate-invalid:
  head x1.13-1.19 (limit 1.04), the face 32-33 lighter than the photo (light dE 33-35, limit 20) and 14-27 brighter than his neck (limit 10);
  the AI judge saw seams and a lighting mismatch.
- **Cause:** the same as F16, now on the foreign-photo path too: his four character face photos are bright indoor shots, and their light comes
  through on every head redraw in outdoor shade, even with "ignore their lighting" in the prompt. Words did not fix it, so the fix is the
  references: face photos of him in daylight for daylight scenes (a [user] question and a [claude] design item in the queue).
- **Status:** open.

### F26. Pin 16 v3, body only: the arm stays on the fin (2026-10-11 12:02, `pin_783485666540168242@v3`, 71 credits)
- **Result:** both pictures pass the pose gate (v1/v2 dropped the arm in 7 of 8); restore ECC 0.997. The head is still the pin man's, as asked,
  so stage 2 swaps it: `pin16s2_head@v1` (replicate, zone head, source foreign, his curls and current cut; the foreign path tells Gemini to
  ignore the references' light, the cause of F16).
- **What it shows:** for pins whose posture Gemini keeps changing (an arm on an object, a bowed head), editing the body and the head in two
  steps keeps the posture; the same held the frame on pin 15 (F25).
- **Status:** stage 2 queued.

### F25. Pin 15 v3, body only: the frame holds; the shoulders sit lower (2026-10-11 10:47, `pin_783485666540141726@v3`, 66 credits)
- **v1_0r:** Gemini redrew the head as his anyway (curls, beard; "do not redraw his head" was not kept) and held the pin's frame (restore ECC
  0.899): the closest pin 15 picture so far. Fails item 14, shoulder midpoint 0.076 off (limit 0.04; the head position passed), most likely
  the pin man's massive trapezius lifting his shoulder line; and item 36, the janeu slanting as on his back seen directly where this mirror
  picture needs it mirrored (fix queued: `pin15janeu_send@v1`).
- **v2_0r:** the head stayed the pin man's, as asked; shoulders 0.166 off.
- **What it shows:** keeping the head still pins the frame (F12's re-framing is gone in v1); the shoulder measure is the user's call.
- **Status:** open (item 14 for the user).

### F24. My error: pin 14's item 36 failed against a wrong picture of the rule (2026-10-11 10:50, corrected 11:30)
- I failed both Gokarna pictures on item 36 because the janeu did not cross "diagonally to his right hip". Item 36 says "as in his photos";
  beside his own front photo the thread hangs nearly straight down the front, exactly as in the pictures. Re-recorded: both pass all 36 and
  are exported. The janeu-fix run (`pin14janeu_send@v1`, about 100 credits) was not needed.
- **Rule:** item 36 is judged beside his photo at 100%, never against a description of the path.

### F23. Pin 14 stage 2: the Gokarna background works; one item left (2026-10-11 10:32, `pin14s2_send@v1`, about 100 credits)
- **Result:** both returns redrew only the scene behind him as the Gokarna beach trek (red laterite slopes, the footpath, a palm-lined bay);
  pasted outside his outline they pass 30 items with clean edges, and stage 1's sky halo is gone. The paste needed `--affine`: the whole-frame
  fit refused them (ECC 0.68), since 84% of the frame changes on purpose; aligned on his unchanged figure they sit at ECC 0.976 / 0.987.
- **Left:** item 36, the janeu path from stage 1 (straight down the picture-right side). A chest-only fix (`pin14janeu_send@v1`) is queued; his
  figure is the same pixels in both pictures, so one fix serves both.

### F22. Pin 16 v2 (torso-only BODY references): the arm still hangs (2026-10-11 10:18, `pin_783485666540168242@v2`, 81 credits)
- **Evidence:** both pictures: left forearm 73 / 70 degrees off, hand 0.20 / 0.18 off (v1 also torso x1.12); identity 0.67 / 0.63.
- **The hypothesis of F19 is rejected:** with no hanging forearm or hand shown in any reference, Gemini still drops the arm. 7 of 8 pictures
  of this pin now; the cause is the edit itself, not the references. Next: the body-only method being tested on pin 15 (it keeps the pin's
  posture and hands, and swaps the head after), if it holds there.
- **Status:** open.

### F21. Pin 10 v7 (gym back, pumped): both pictures fail by small margins (2026-10-11 04:03, `pin_783485666540141734@v7`, 70 credits)
- **Held:** the pose gate passed for both; pumped back with its definition, full arms with veins, the janeu from the picture-left shoulder to
  the picture-right hip, the chain, the earbud, people and lettering (restored).
- **Failed:** item 12, his head turned into profile (beard and nose show) where the pin hides the face; the user asked on this pin to "hide
  the face a little more" (v4); and item 8, Gemini's sparkle watermark stayed on the floor next to his trouser leg, inside the restore's band
  around him, so it was not replaced by the pin's pixels.
- **Fix candidates:** the sparkle: the pin's own pixels copied into that small disc (it is floor in both); the head: for the user's eye first
  (on pin 17 he liked a visible face "in the right amount").
- **Status:** closed 2026-10-12: the sparkle was removed with the pin's own floor pixels (`v1_0r_sparkle.jpg`, `v2_0r_sparkle.jpg`); he chose
  "Show the profile", then stopped the pin: it misrepresents his height (F32).

### F20. Pin 14 stage 1: the two-stage method holds the frame in 1 of 2 (2026-10-11 03:32, `pin_783485666540168309@v2`, 72 credits)
- **v1_0r:** passes the pose gate in full (the re-framing of F11 is gone); fails item 11 (a pale halo in the sky around his head, where the
  restored pin sky meets Gemini's lighter sky; stage 2 redraws that sky) and item 36 (the janeu runs straight down the picture-right side
  instead of crossing to his right hip at picture-left).
- **v2_0r:** drawn larger again (torso x1.16), fails 12, 14, 29, 30.
- **Next:** stage 2 on v1_0r: only the background redrawn as the Gokarna beach trek, pasted back outside his outline (the restore's own mask);
  the janeu path is a separate small fix.
- **Status:** open.

### F19. Pin 16, third run: the arm hangs again in both pictures (2026-10-11 03:05, `pin_783485666540168242@v1`, 117 credits)
- **Evidence:** `outputs/20261011_030505_goal-pin-783485666540168242`: his left forearm 75 / 69 degrees off and the hand 0.18-0.19 off (it
  hangs at his side, the board floats unheld); v2 also torso x1.08; identity 0.56 / 0.59, lower than run 2's 0.68. The pin man's calf tattoo
  is back at the frame's bottom edge on the restored copies: the restore copies the pin's pixels where the person mask misses the lower leg.
- **The pattern:** this recipe held the arm in 1 of 6 pictures (F5, F13, F19). The keep list already names the hand on the fin, so the next
  version changes the method: the BODY references (`pumped-side`, both standing with their arms hanging) cropped to the torso, so no hanging
  forearm or hand is shown to copy.
- **Status:** open.

### F18. The work sat idle for three hours, through two credit refills (2026-10-10 22:15 to 2026-10-11 01:26)
- **What happened:** I ended a turn on a question ("Want me to run both, one, or neither?") and nothing ran until the user's "continue";
  the window refilled at 21:33 and again at 02:33 while queued-able work waited. The user: "did you not autoresume when credits got
  refreshed? create a system to auto-continue for claude code when gemini image credits refresh".
- **Cause:** my process, and no mechanism that continues without a reply: waves wait for credits on their own, but only once someone starts
  them.
- **Fix (02:58):** `tools/autocontinue.py`: a queue of ready waves and a to-do list; the hidden task `facecard-autocontinue` runs `tick`
  every 15 minutes and starts the next wave when the window holds its credits (tested: its first real tick started `pin16r3`); in an open
  session a CronCreate job re-runs the review loop every 30 minutes; sessions start with `autocontinue.py status`; a recommended,
  non-risky next step is queued instead of asked about. Closed.

### F17. The test: pin 15 with his old body photo re-framed too (2026-10-11 01:41, `pin_783485666540141726@v2`, 1 picture)
- **Result:** with IMG_6923 Copy instead of the pumped back (nothing else changed), the picture still failed the pose gate, and the restore
  refused it: its shape was 0.747 where the pin is 0.881. So the pumped photo is not what re-frames pin 15 (one picture; F12's hypothesis
  is not supported there).
- **What the shapes show:** every reference photo is 3:4 (0.750). Two of the evening's returns came back in a shape other than their pin's:
  this one (0.747, close to the references) and pin 17 v1_0 (0.806 for a square pin); pins 14 and 16 are 3:4 themselves, and their re-framing
  was him drawn larger in the right shape. Two forms of re-framing, then: the canvas shape drifting toward the references' on pins that are
  not 3:4, and him drawn 13-21% larger.
- **Status:** open: causes narrowed, not fixed.

### F16. Pin 16 face fix (replicate on v2_0r): 0 of 4 attempts usable (2026-10-11 01:32, `pin16fix_face@v1`, 161 credits)
- **Evidence:** `outputs/20261011_013208_goal-pin16fix-face/run.log`: attempts 2 and 4 came back unchanged (95% the same face); attempts 1
  and 3 changed the face (identity 0.63 / 0.71) but drew the head 5-6% larger (limit 4%) and much brighter than the photo and his neck (light
  difference 24, limit 14; face +17-19 over the neck, limit 10). By eye the whole crop came back lighter, the trees included, and his skin
  lighter.
- **Cause (known from round 6, 2026-09-20):** the light of the face references leaks: me@v2's faces are bright indoor photos, this face sits
  in outdoor shade. Repeating the same request is on the do-not-retry list.
- **Status:** open. The marks fix of the same picture worked (F15).

### F15. A region-edit paste kept the old pixels along the frame's edge (2026-10-11 01:40, pin 16 marks fix)
- **What happened:** the marks fix removed the pin man's ring, forearm mark and calf tattoo, but the lowest part of the tattoo stayed: the crop
  ended at the picture's bottom edge, and the paste always kept a 14 px border of the old picture (meant to hide seams inside the picture).
- **Fix:** `tools/region_edit.py` keeps that border only on sides inside the picture. Re-pasted: the calf is clean to the edge. Closed.

### F14. Pin 17 (balcony back): one picture re-framed, one fails by small margins (2026-10-10 21:08 run, `pin_783485666540141762@v1`, 392 credits)
- **v1_0:** shoulders 0.205 off, hands 0.13-0.14 off; the restore refused it (aspect ratio 0.806, the pin's 1.000).
- **v2_0r** (restored, ECC 0.995, the reflections excluded and drawn as his plain arm): fails item 14 by 0.002 (shoulders 0.042, limit 0.04;
  limits are never loosened), item 12 (his head turned into profile, beard and nose showing, where the pin shows only the ear and cheek edge)
  and item 36 (the chain reads gold, his is silver; the janeu runs the right way). Checklist: NOT BEST, 3 failed.
- **Status:** closed 2026-10-12: v2 = v2_0r's head pasted on the pin man's neck at its own proportions, body only (pose gate pass on
  both), then the chain fixed alone with his real chain (IMG_7002) as the reference and pasted along the chain only: `pin17chain_send`
  v2_0r, BEST 33/36, exported (`motorcycle-outfit-men_17_..._v1.jpg`).

### F13. Pin 16 (surfboard), second run: one picture holds the pose but keeps the pin man's tattoo and ring (2026-10-10 21:03 run, 392 credits)
- **v1_0:** the arm hangs again (left forearm 71 degrees off, hand 0.178 off), as in F5.
- **v2_0r** (restored, ECC 0.995): passes the pose gate in full and 30 checklist items; identity 0.684. Fails item 32: the pin man's calf
  tattoo is on his calf and the pin man's silver ring on the finger holding the fin, though the inventory asked for both to go. The pin's
  light smirk came out neutral.
- **The user (22:15):** "face almost there but still not accurate, needs fixing": item 21 fails by his eye too (identity 0.684 did not
  catch it).
- **Cause:** Gemini keeps small marks of the man it replaces when they sit away from the head (the calf at the frame's bottom edge, a ring).
- **Fix candidate:** a region edit of the calf and the hand (cheap, the rest of the picture stays).
- **Status:** open.

### F12. Pin 15 (mirror back): both pictures re-framed; the restore refused both (2026-10-10 20:57 run, `pin_783485666540141726@v1`, 185 credits)
- **Evidence:** `outputs/20261010_205703_goal-pin-783485666540141726`: shoulders 0.148 / 0.146 and head 0.154 / 0.217 off (limit 0.04); the
  background restore refused both as re-framed (background ECC 0.729 and 0.568, needs 0.80); identity 0.172 and 0.315 (his face is mostly
  hidden here, so the score is weak evidence).
- **The pattern:** 6 of 6 pictures this evening re-framed (pins 14, 15, 16), while yesterday's Route G pins (10, 11, 13) mostly held the frame.
  The last two runs broke it: 2 of 4 held the frame (F13, F14), so the evening ends at 6 of 10 re-framed.
  What is new tonight: the `--physique` BODY photos (pumped_front / pumped_back) in place of IMG_6923 Copy, and the subagent-written
  inventories. **Cause unknown.** A cheap test after the wave: the same recipe with the character's own body photo, one picture, to see whether
  the physique reference is what moves the frame.
- **Diagnosis (2026-10-11 03:25, `v1_0_pose.jpg`):** he is drawn smaller and lower than the pin man: his neck base at about 30% of the frame
  height where the pin's is at 18% (the inventory's keep line already gave 18%), and the camera moved a little (the door frame ghosts in the
  blend). The pin man's massive back fills the frame; Gemini re-composed around his narrower one. Words already said it, so the next pin 15
  version changes the method (for example the grey-out target outline used for his physique, or a layout image), not the wording.
- **Status:** open.

### F11. Pin 14 (Gokarna): both pictures re-framed, him drawn larger (2026-10-10 20:50 run, `pin_783485666540168309@v1`, 190 credits)
- **Evidence:** `outputs/20261010_205035_goal-pin-783485666540168309/v1_0_pose.jpg`: torso x1.16 and x1.13 the pin's size (limit 0.93-1.07),
  shoulders moved 0.086 / 0.060 and the head 0.097 / 0.079 up the frame (limit 0.04), the hand at picture-left 0.096 off; the horizon moved
  from about half the frame height to near the top, and his face turned further toward the camera than the pin's. Otherwise close: the
  Gokarna cliff, the backward cap, his chain and pendant, the janeu and the pumped torso are there.
- **Cause (hypothesis):** with the whole background in the CHANGE list (20 items, no restore) Gemini recomposed the shot; the same drawn-larger
  habit as F5 and E2 (4 of 4 pictures tonight 13-21% larger).
- **Fix candidate, after the wave:** two stages, as the prep agent proposed: him first with `--restore-background` (the pin's own framing is
  copied back), then only the background of a passing render.
- **Status:** open.

### F1. Pin 16 ran on its own after I stopped the wave, and spent 346 credits (2026-10-10 20:29-20:44)
- **What happened:** I stopped wave `pins1417` at about 20:29 by killing a list of PIDs taken a minute earlier. The wave had started pin 16 at
  20:29:11, after that list was taken. My check afterwards searched only for the wave and pin 15, so I said "nothing is left running". Pin 16
  ran to the end: 2 pictures, 346 credits, both failed the pose gate (F5).
- **Cause:** my process: a stale PID list and an after-check that did not cover every job of the wave. The same kind of leftover spent credits
  on 2026-10-09 (a crashed session's driver).
- **Fix:** `tools/wave.py --stop <tag> [--now]` (22:10, tested): runs tracked by process; `--now` ends a run with every child it has at that
  moment and checks none is left. Waves are never stopped by a PID list again.
- **Status:** closed.

### F2. Every Gemini sign-in was rejected for 10 minutes (2026-10-10 20:20)
- **What happened:** wave `pins1417`, pin 14: all four vault cookie pairs and the cookies read from the google-1 browser profile came back
  `UNAUTHENTICATED` (RPC `GPRiHf` denied). No picture, no credits. At 20:30 the same vault pair (the browser-read PSID) was `AVAILABLE`, with
  1,191 credits and a clean abuse status. The keep-alive had renewed at 15:51, the 18:49 run and my 19:41 quota read worked.
- **Cause:** unknown. Assumption: a short rejection on Google's side; nothing in the logs shows a cookie change between 20:20 and 20:30 (the
  vault file was written at 20:26, but other tools use it too).
- **Fix:** a sign-in check before every start, retried after 2 and 5 minutes, then a halt (22:10); sign-in failures exit 5.
- **Status:** cause unknown; a repeat is now contained.

### F3. The wave logged a run that made no picture as "exit 0 (rendered)" (2026-10-10 20:27)
- **Cause:** `runner.py`: the sign-in failure is raised outside the stage blocks, so the run's exit code stayed 0.
- **Fix:** `runner.run()` keeps the code of any stage failure (exit 1, "no render"). 20:33.
- **Status:** closed.

### F4. The second wave waited 15 minutes for two runs that were not really its business (2026-10-10 20:35-20:50)
- **What happened:** `pins1417b` counted "2 runs already going": pin 16 of the stopped wave (truly running, F1, until 20:44) and pin 15 (stopped
  at 20:28, counted until its log was 20 minutes old).
- **Again at 20:55:** pin 15 was held for the same orphan pin 16, which had ended at 20:44 but would have counted until 21:04, because the
  stopped wave never wrote its exit line. At 20:57 I appended the two true end lines to `.cache/wave_pins1417.log` (marked as written by hand);
  the running wave was not touched.
- **Cause:** P1, runs counted from log growth.
- **Fix:** runs tracked by process in `.cache/wave_<tag>.runs.json` (22:10, tested).
- **Status:** closed.

### F5. Pin 16 (surfboard, side view): both pictures failed the pose gate (2026-10-10 20:29 run, `pin_783485666540168242@v1`)
- **Evidence:** `outputs/20261010_202925_goal-pin-783485666540168242/v1_0_pose.jpg`: torso x1.21 the pin's size (limit 0.93-1.07), head moved
  0.041 (limit 0.04), his left forearm 72 degrees off and his hand moved 0.19 of the frame: his arm hangs at his side instead of holding the fin,
  and the board floats unheld. Identity 0.626 and 0.589.
- **Cause (hypothesis, to test):** `--physique pumped-side` sends his front and his back, both standing with his arms hanging down; Gemini took
  that arm pose from them. The same recipe runs once more in `pins1417b` (queued before this was known; the wave is left to finish).
- **Fix candidates, after the wave:** BODY references cropped to the torso (no hands), or the hand on the fin named in the CHANGE list.
- **Status:** open.

### F6. Pin 14 could not be frozen: the gate took the pin for his own photo (2026-10-10 20:13)
- **Cause:** the pin man's face, turned about 80 degrees away, scored 0.461 against his photo pool; own photo starts at 0.40. Turned faces
  score anywhere in 0.20-0.50.
- **Fix:** `results_names.json` `"source": "foreign"` for that pin; `recipe.own_photo_of` reads it. The 0.40 threshold is unchanged.
- **Status:** closed.

### F7. Back round 4 (his video frame) failed (2026-10-10 18:49 run, `body_grey_send@v6`)
- **(a) The paste refused both returns as re-framed (ECC 0.76-0.77).** They were not re-framed: on the background they fit at scale 1.00 and
  3 px (ECC 0.97); his body, half the crop, differs on purpose. I first told the user they were zoomed out: wrong. Fixed with
  `region_edit.py --affine` (fit on the background only). Closed.
- **(b) The pictures fail:** arms thinner (v2 measured -33.7%, both thinner by eye; the user's rule is never thinner), love handles -10.8% /
  -13.5% (target -4 to -8), faint ghost edges beside the arms. The approved round 1 back stays the standard. Cause open: the grey-out target
  outline or Gemini's habit of slimming arms (round 1 also shrank them).

### F8. My credit estimate was wrong (2026-10-10 evening)
- I planned the four pins at about 100 credits a picture; the measured cost tonight is 173 on Flash (pin 16: 346 for 2).
- **Fix:** plan from `credits.json` of the last runs. Closed as a rule.

### F9. The round 4 measure printed nothing (2026-10-10 19:45)
- **Cause:** my 400-second limit stopped it before it printed; its output was buffered because it was piped. Measuring runs 7+ minutes on this
  box (P3).
- **Fix:** long measures run in the background, unbuffered, with their own log. Closed.

### F10. Fetch problems for the evening pins (2026-10-10 19:05)
- `read_board.py` returns 0 pins for single pin links (it reads boards); yesterday's pin reader (scratchpad `read_pins.py`) worked.
- The Facebook location photo needs a login and no browser was connected; Instagram shows publicly one photo of the post.
- My Bash heredocs halved backslashes twice (a known quirk): scripts are written with the Write tool.

### Earlier on 2026-10-10 (from the day's work, short)
- **E1.** 03:41: a run beside the overnight Qwen render was paged out and made no progress. Fixed: the memory gate in `tools/wave.py`.
- **E2.** Smile route A: the tight crop came back zoomed out 10 of 10; on the loose crop a big smile made the face 5-16% larger. Changed to
  the loose crop; the size gate stays.
- **E3.** The laugh looking down: 0 of 12; Gemini lifts a bowed head. Dropped by the user.
- **E4.** Route B (his older smiles redrawn to today's look) changed his nose and wrinkles. Dropped by the user.
- **E5.** Physique round 1: waist +1%, arms -2%, veins and janeu lost. Round 3: a shifted return pasted a second waistband (the shift refusal
  was added). Gemini filled the grey with his old outline (a target outline was added).
- **E6.** The pizza third picture: "drunk looking" eyes; Gemini's sparkle pasted onto the sweater (now never pasted).
- **E7.** DSC07985 kept his glasses under `--glasses no` (the check was skipped instead of asked). Fixed.
- **E8.** The back wrist fix showed a seam (a soft ramp fixed it); the shoulder warp widened his triceps (the user: not what was approved).
- **E9.** The back target outline: a straight grey top, a target cleared by the neck cut, no face found on the video frame. Fixed in
  `tools/physique_greyout.py`.
- **E10.** My prompt called his janeu an earphone wire and removed it twice. Fixed everywhere (checklist item 36).
- **E11.** I failed pin 10 gym v5 on item 32 for veins that are his own. Corrected.
- **E12.** I recommended "a shade whiter" teeth; they looked fake. Removed.
- **E13.** (2026-10-12 04:1x) On pin 16 I read cheek_iod 2.41-2.42 and jaw_iod 2.15 as "the eyes sit too close" and told the user so after
  his "space between eyes". Measured properly (eye distance corrected for the head turn, against eye-to-mouth and eye-to-nose): every
  version is inside his band (his real photos 0.95-1.18 and 1.41-1.68; v2/v3 at his median). Those ratios rise with the turn: his own
  photos at 16-19 degrees read 2.40-2.45. Rule: compare face measures only at the same head turn.

