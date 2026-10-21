# nano-banana-facecard

Photos of one man (the user) made through the Gemini app (`gemini_webapi`, cookies from the DPAPI vault in `session.py`): his face, hair,
beard and slim build, in the scene, pose, outfit and light of a goal picture (usually a Pinterest pin of another man).

## READ FIRST: generation is on hold, and the rules after the 2026-10-17 retrospective

> The user, 2026-10-17: "all the recent generations have been going downhill. Do not generate any more images. Keep the to-dos on hold ...
> find out why and fix it." The findings, with every number, are in `RETROSPECTIVE_2026-10-17.md`.

- **The hold:** while `.cache/GENERATION_HOLD` exists, `facecard.py gen / replicate / run`, `runner.run` and `tools/wave.py` refuse (exit 6) and auto-continue
  decides "hold"; the tasks `facecard-autocontinue` and `facecard-local-overnight` are disabled. Only the user lifts it (their words in chat).
  For one run the user approved: `FACECARD_HOLD_PASS="<recipe ref>::<their words>"` set on that one `facecard.py run` process lets exactly that
  recipe through `facecard.py` and `runner.run`; the hold file stays (first used 2026-10-19 for pin 8 v8, the teeth test).
- **Why it went downhill (measured):** every picture of the user's best set (`D:\Downloads\AI me`) took one pass, or one pass plus one small fix;
  from 2026-10-11 pictures became chains of edits on edits (pin 14: six), each pass adding damage; each failed checklist item became one more edit;
  the goals moved to shirtless pumped bodies on other men (which one pass cannot do, known since 2026-09-27); generated pictures were fed back in.
- **The rules from now on:**
  1. One coherent picture per attempt: the user's own photo -> replicate; another man's photo -> one whole route G render from real photos of
     the user. A render that is wrong on the user gets a new whole render; the person in a render is never edited.
  2. At most one small fix, on objects only (a prop, lettering, a background figure, a sparkle), on a render the user has seen; no head pasted from
     another render, no body reshaping, no fix of a fix. `runner.py` refuses a recipe whose pictures would have more than two passes
     (`tools/edit_depth.py`, exit 7; a lineage it cannot read is refused too) unless the user asked for that exact edit
     (`FACECARD_DEEP_EDIT_OK` / a wave job's `"deep_edit_ok"`).
  3. The user's eye decides first: 2 to 4 whole renders per goal beside the nearest best-set picture; the checklist names defects for the user, it
     is never the reason for another pass. Items 19, 26, 28, 31 and 32 (the current look) are pointed out, never rejecting (the user, 2026-10-17).
  4. Real photos of the user as references, except the body of a shirtless picture: the pumped physique, always (the user, 2026-10-17,
     confirming 10-10). Any other generated picture (E2 smile, head-angle cell) only where the user asks for it for that goal.
  5. Nothing runs on its own: a wave runs only for a goal plan the user approved; no spare-credit backlog runs (the user, 2026-10-17, in place
     of their 10-13 spare-credit rule).
- **Next, once the user lifts the hold (their order, 2026-10-17):** the shirtless pins first, each in one whole render with the pumped physique;
  a body that misses gets a new whole render, never a body edit. **Smiles with teeth are a major open item:** "none of the generated images till
  now have good teeth showing images" (diagnosis: `.cache/smile_diagnosis_2026-10-17/REPORT.md`, FAILURE_LOG F72: nothing asks for teeth, the
  closed-lip default sits in five places; goal faces are too small, a median 55 px between the eyes against 246 in IMG_6875; the teeth came out
  right only with the real IMG_6875 crop on a large face, as in E2). The user's answers, 2026-10-18: only E2 has the right teeth; teeth only for
  smiling goals or when they ask; the real IMG_6875 + IMG_3884 are the teeth references (never the generated E2, never "whiter"); the first
  teeth test goes straight to a shirtless pin. The user's photos are sufficient: never ask for new or better ones ("dont keep blaiming the photos").
  **Teeth mode** (built 2026-10-18): `facecard.py recipe new ... --teeth "<why: the goal's man smiles, or the user's words>"` sends HIS TEETH,
  FRONT and HIS TEETH, TURNED (the two real crops in `D:\FacecardData\approved_refs\teeth`, facecard.json `teeth_refs`) after the inventory's
  own references, and refuses an inventory or route text that never says how his mouth is, or that asks for closed lips or whiter teeth;
  checklist item 38 judges the teeth beside those photos. For his own photos the E2 method (`IMG_6858@v7`: `--zone expression`, the real
  IMG_6875 crop as `--expression-ref`, `--rank smile`). None of the eight shirtless pins shows its man smiling (measured 2026-10-18);
  the user chose pin 8 for the first teeth test: `pin_783485666539777118@v8` is frozen and waits for the hold to lift.
- **How to ask the user** (2026-10-18/19): every decision goes in the AskUserQuestion box, the recommended option first with its reason
  ("use the 'ask user question' tool to prompt me for the decision to take"). When it depends on any picture, the links must reach the user
  first, and text in the same turn as a box never shows: start a 5-second background wait, END the turn with one bullet per picture (a short
  label and its clickable link, the format they called "perfect"), then ask in the box first thing in the next turn, the pictures named in
  words only.
- **The shirtless pins run one after another without waiting for approval** (the user, 2026-10-21: "dont wait until user approves just move on to
  next pin going forward"): pins 15, 6, 14 in that order, one whole render each (2 pictures), each run with `FACECARD_HOLD_PASS` for that recipe
  quoting these words; the hold file stays for everything else. Checklists are recorded honestly (never `--user-approved` on the user's behalf),
  only what truly passes is exported, and the user gets a roundup with links when a batch is done.
- **The pose shapes his body** (the user, 2026-10-21): with an arm raised or the lats spread his back opens into a V whatever his pump, shown by
  his non-pumped videos (`D:\FacecardData\body_refs\2026-10-21_videos`: IMG_7419 back/side/front poses, IMG_7420 back with the arm raised,
  IMG_7249 legs). For such a pose give a pose-matched real frame as an extra body reference (inventory `refs`, "take only the SHAPE") beside
  the pumped standard, and never word the back or shoulders as narrower or less massive than the pin man's.
- **The body wording names only what the goal's frame shows** (FAILURE_LOG F74, 2026-10-20): "upper abs and obliques showing, the tight
  narrow waist" on a pin cut below the chest made Gemini stand him up and re-frame pin 4 in 10 of 10 renders; pick or add a physique variant
  whose build text fits the crop (`pumped-front-chest` for a chest-up frame).
- **Camera distance is measured, never trusted to wording** (FAILURE_LOG F76, 2026-10-21): pin 12 v7's route text asked for two and a half metres with the head a sixth of the frame, and the eyes stayed 76-77 px apart (v6: 76 and 81). Read the eyes-apart px of the render before and after a distance request, and say plainly when it did not move. The smile needs eyes about 100 px apart or more for the teeth to read; 76 px showed them.
- **Text the goal has is carried or named as missing** (item 34, F76): a small mark such as the pin 12 tee's "Untld" under the print is a text the goal has; leave it in the print design crop or record 34 as failed. Shop signs in a mall view stay soft glow; figure-shaped forms in a shop window that cannot be told from people at 25 px fail 33.
- **The credit window can be emptied by something that is not this pipeline** (F76, 2026-10-21): reconcile a window from `.cache/failures.jsonl` before blaming or excusing anyone; the consumer of 10-21's windows was the user's own Gemini use (their answer, "It was me"). Read `tools/quota.py` before a chain and start credit-hungry runs the minute a window resets, `--wait-max 900` (the 22:33 chain did, and spent 931 credits undisturbed).
- **Pin 15's pose is a lean** (the user, 2026-10-22, F78): hips pushed forward, upper back leaning back toward the camera, so the back is nearer the camera than the hips and reads as a triangle (shoulders wide, waist narrow). It has to be written into the posture item and a CHANGE item (v9); a render built without it stands upright.
- **A mirror picture needs mirror-direction threads** (F77): `pumped_back_torso.jpg` is a direct back view, its janeu runs upper picture-left to lower picture-right; the mirror pins (15) need upper picture-right to lower picture-left, as the real IMG_7420 frame has it. Use `pumped_back_torso_mirrored.jpg` (physique `pumped-back-flexed`, pin 15 v8: the first back with only item 14 of the pose gate failing) and never send a reference whose thread runs the wrong way.
- The sections below are the history of how the pipeline was built; where they conflict with these rules, these rules win.

## Consistency is the rule (the user, 2026-10-07)

> "Even if the generation is faulty, it is still consistent: the method used to generate the image is followed consistently each time, so
> that each step of the image generation is very pronounced and visible, which can help us debug this later easily."

Gemini cannot be seeded (`gemini_webapi` has no seed; nor does any tool for Nano Banana). So consistency means: **one recipe version always
sends one locked request, and every run goes through the same eight stages, recorded and reported.**

- A **recipe** is the frozen method of one goal: `recipes/<collection>/<NN>-<title>/v<N>.json`, holding `inputs` (every reference by role,
  with its sha256 and why it was chosen; the inventory; the flags) and a `lock` (the exact prompt, the files in send order with sha256 and
  upload name, the model, `request_sha256`). Versions are immutable.
- A **run** sends the lock byte for byte; the bytes come from the **blob store** (`D:\FacecardData\blobs`), never from `.cache`.
- **METHOD DRIFT** in a run means today's code would compile the recipe differently. The run still sends the lock; a deliberate change
  becomes a new version (`recipe bump`).
- Gates and limits (pose gate, light, identity) change only with the user's approval.

## The same man in every picture (the user, 2026-10-08)

> "If I am making you generate 10 images of the same character using the same reference images, all should look the same." Body fat (visible
> in the face too) and body type (muscle, fat, proportions) must be identical every time.

- **One character, frozen**: `characters/me/v<N>.json` (`characters.py`, `facecard.py character new|show`) holds the ONLY photos of him that
  are sent (face: front `IMG_6858`, three-quarter left `IMG_6868`, three-quarter right `IMG_6861`, profile `IMG_6863`; body `IMG_6923 Copy`,
  all from 2026-09-08/15), the description of his face, hair, beard, skin and build read from those photos, and his band of measures.
  Every new recipe takes `--character me@vN`: Route G sends 3 faces + the body photo (4 images of him), replicate the 4 faces as head crops.
  The character's description replaces `face_text` / `build_text` / the identity bible in those recipes. A change is a new character version.
- **Why** (survey of 2026-10-08): the January arms photo `IMG_0440` (fuller arms, short hair, shot from below) went beside the slim
  September body photo in 76 of 79 runs; the face set changed with every goal (11 sets); old `_fav` crops (short hair, glasses) were in the
  most-used sets; the text said "lean face ... hollow cheeks" while his photos show fuller cheeks; and every pin's man was described as
  "broader and far more muscular" whatever he looked like. Edits also keep the edited photo's body.
- **Where the pictures differed** (`tools/character_audit.py`, all 251 ledger pictures, `D:\FacecardReview\character_audit_2026-10-08.html`):
  the body follows the GOAL picture. The goal explains 84% of the spread of upper-arm width (`arm_iod`) and 28% of `arm_shoulder`; the face
  reference set, the model, the route and the 2.1 switch explain about 1% each once the goal is fixed. Pin 9's renders all sit above his band,
  pin 8's sit 43% of the way from him to the pin's man, pin 5's inside his band. Face fullness could be measured on only 4 pictures (faces must
  be turned 25 degrees or less), so face fat is judged by eye on the character sheet; the face measures may partly read the beard outline.
  The validation numbers (KEEP: cjwr, par, jaw_iod, cheek_iod, arm_shoulder; arm_iod promising, needs a second measurable heavy goal man)
  are in the audit page; nothing about them is a gate.
- **Measured, record-only**: `character.py` measures face fullness (cheek-to-jaw width, width-to-height, perimeter-to-area: the facial
  adiposity measures of Coetzee et al. 2009/2010) and build (shoulder, upper-arm and waist widths); stage 06 records each picture against the
  character's band, stage 07 draws the character sheet; checklist items 31 (face fullness) and 32 (build) are judged on it. The measures
  become gates only after the user approves them. `tools/character_audit.py` measures every picture made so far.
- **Current look (the user, 2026-10-08)**: every picture shows him as he looks TODAY, his face (lean: "if it's the leanness, stick to
  the leaner look"; only his beard may widen the head, up to 1.10), his current haircut, his beard AND his current physique, even when the
  goal is an older photo of his. An older own photo is redone in two frozen `replicate/1` passes: pass A `--zone build --current-look` (his
  body crop from the goal's keypoints, the character's body photos, a frozen two-order AI build reading, background drift outside his
  silhouette, an AI body judge), then pass B `--from-picture <pass-A picture> --current-look` (the head: current cut, lean face, size gate
  0.94-1.10). `tools/best_check.py` forces items 26/32 to FAIL when a current-look own photo kept its old body, and refuses any PASS of 19,
  21, 26, 28, 31, 32 without an `--evidence` line naming the reference compared at the same scale. Character `me@v2` carries the lean wording.
- **His own photo is never sent through Route G**: stage 01, `recipe new` and `gen --goal` refuse it (exit 2). His own photo is a
  `replicate/1` recipe (`recipe new --method replicate --goal <photo> --character me@v1`): the head crop of the full-resolution original is
  edited and pasted back; the crop, the AI head-box and scene readings and the references are frozen, and every attempt sends the identical
  request. (2026-10-07 the own-photo pictures went downhill exactly there: Route G redrew the whole photo at ~1 MP with a ~77 px face.)
- **Placement pass, opt-in (2026-10-12, FAILURE_LOG F34):** `recipe bump <goal>@vN --place-from <run>/vK_0.png` (a copy of that version,
  nothing read again) or `recipe new --method replicate ... --place-from <picture>` adds ONE reference just before the photo to edit: the
  head of that picture (cut from its raw return `05_generate/raw/vK_raw.*` when the run kept it), with the old rescue sentence "keep the
  head at exactly the position, size, turn and tilt it has in the last image". It is how the only ideal on another man's photo was made
  (Pinterest 064221: 0.923 to 0.981); on another man's photo it never fixed a too-bright face. The head is a generated image: a recipe with
  it runs only after the user's yes. Versions without it compile unchanged (dry runs: request = lock). Test character `me-day@v1`
  (his real daylight faces IMG_6844/6846/6845, 2026-09-08, `.cache/refs`) beside `me@v2`, which stays the default.
- **Head region, opt-in (2026-10-12, pin 14, FAILURE_LOG F43):** `recipe new --method replicate ... --head-region x0,y0,x1,y1` (fractions of
  the frame, 0-1): only faces whose box centre lies inside count as his head, for the main face (and so the AI head-box check), any copy, and
  the run's own face reading; recorded as `inputs.head_region` and `method.args.head_region`. Pin 14's torso read as a face larger than the
  turned-away head (v1 froze on it); v2 with `0.36,0.42,0.66,0.62` froze on the real head (55 px, far face, crop [48, 288, 683, 683]).
  Without it the largest face is the subject exactly as before (dry runs of pin16s2_head@v1, pin16fix_face@v3, IMG_6858@v7,
  google-1__IMG_5549@v9: no drift, request = lock). `recipe bump` refuses it: the face is chosen when the photo is read.
- **Eye gate, opt-in (2026-10-12, pin 16; the user: "one eye is looking 75 deg to the left and another 80 or 85 ... an eye condition"):**
  `recipe bump <goal>@vN --eye-gate "yaw=24:34,vergence=-0.34:-0.18"` (or on `recipe new --method replicate`) measures his eyes on every raw
  return with `eye_measure.py` (2dfan4 eye outlines, a dark-iris locator, headpose yaw) and fails a return whose turn or eye agreement is
  outside the bands from his real photos at the same turn. It selects only: not in the prompt, so the request stays the lock. Bands and
  reliability are in `eye_measure.py`'s docstring; the same-scale check sheet is `outputs/20261012_040156_goal-pin16fix-face/07_review/eyes_gaze_check.jpg`.
- **`"no_face_words": true` in a body-only inventory (2026-10-11, FAILURE_LOG F28/F33):** the BUILD sentence says "his body is" instead
  of "how lean or full his face and body are", so a body-only edit carries no face-leanness words (they made pin 14's face leaner than his).
  Inventories without the key compile as before (pin 15 v3: request = lock).

## The gold tier (the user, 2026-10-09)

> "Remember these five image goals in a separate tier of images. ALWAYS." "These gold references consistently need to be consistent."

- `gold.json` lists the five: kayak, beach, Pin_Best (pin 1), TT and tt2 (the table-tennis photo). Each entry has the user's file in
  `D:\Downloads\AI me`, a read-only copy in `D:\FacecardGold`, its blob, its goal, the run that made it and its 32-item checklist as recorded.
  A gold picture is never deleted, moved, overwritten or re-rendered in place, and a newer picture of the same goal never replaces it: only
  the user adds to or changes the tier.
- For these goals the gold picture is "the current best version of the same photo" that a new picture is compared with, item by item,
  before it is shown (`BEST_CHECKLIST.md`).
- Consistency: `tools/gold_tier.py check` puts the five beside the character's photos at one scale (faces, torsos) with measures and
  similarity; `tools/gold_tier.py compare <picture>` adds a new picture to that sheet. Run `check` after any change to the character or a
  method. The yardstick for face and build stays the character's photos: each gold tile carries its verdict and failed items, so a failed
  trait is never copied from it.
- Checklist 2026-10-09 (`D:\FacecardReview\gold-qc-2026-10-09`): only Pin_Best passes all 32 items. Kayak fails 19, 26, 27, 28, 31, 32 (the
  old photo's cut, beard, fuller face and body); beach 19, 26, 28, 32 (fuller hair at the sides; the build hidden by the sweater, so
  unverifiable); TT 12, 26, 32 (face turned about 15 degrees more toward the camera; the older photo's body); tt2 12, 24, 26, 27, 28, 32.
  The user decides any rework; a reworked picture joins the tier only when the user says so.

## The reference-set upgrade: ideal smile, head angles, next-cut physique (the user, 2026-10-10; plan approved)

> "smile always is turning out bad ... my smile reference image itself is bad i agree since i dont have a photogenic smile, but when captured in
> candid it can look different" (13 smile photos sent); "create an ideal smile image that you can refer to all the time and post-approve", then
> every other head profile from that front, and a back/front physique about 5 points leaner with 2-3 kg more muscle.

- **The override:** the skill rule "never feed generated images back into the reference set" gives way here, and only with these guards: the real
  front photo is always sent, at most one generated face goes in a request, the identity pool and the band stay real photos only, every generated
  reference carries the user's approval, and `me@v2` stays (old recipes keep their version). Nothing generated is a reference until the user approves it.
- **Smiles:** the open smile with teeth is the problem (the closed-lip smile keeps today's references, the user's words). Study:
  `tools\character_study.py smiles` (pose, identity, one-scale face and lower-face crops, `D:\FacecardData\smile_study`; never in the identity pool)
  and `exemplar E2 IMG_3884,DSC07985,IMG_6637 --trim-top 0.12` (`.cache\inventories\pin_refs\his_smile_E2.jpg`). Teeth: his own, as they are
  (the user, 2026-10-10: "There is no need to change the color of the teeth or anything"; "a shade whiter" made them uniform and fake).
- **His full originals:** the 13 smile photos in `D:\Downloads` are crops (DSC07985 was 478 px wide); the camera originals are in the Takeout
  copies under `D:\PersonalArchive-backup\GooglePhotos\google-1|google-2\photos\Takeout` (read-only), converted to
  `D:\FacecardData\smile_study\originals\` (`ffmpeg -i X.HEIC -frames:v 1 -q:v 2 X.jpg`). YuNet misses faces over about 800 px at full size
  (IMG_3931, DC8F5024): those are used at half size (`*_half.jpg`).
- **"Until it matches" (the user, 2026-10-10):** a generated smile must match his REAL smile in the same pose. `tools\smile_match.py <real> <pics>
  --ai` measures it: five landmark ratios (eye opening, mouth width and opening, corner lift, brows) and an AI comparison part by part (eyes,
  cheeks, smile lines, brows, mouth, teeth: same / weaker / stronger). The AI comparison matched the user's verdict on IMG_3884 route B ("mouth
  same, teeth same; eyes, cheeks, smile lines, brows weaker") where the landmarks read within 7%; matched = every part "same". The cause of
  "weaker": the `--expression same` wording ("...at the same strength, but natural and relaxed on his face, never tense or forced") plus a face
  drawn from four neutral photos. Fix, kept out of older recipes: `--expression "<his expression part by part>"` and his own face crop as an
  `--expression-ref` with `--expression-ref-intro "a close crop of his face in the last image itself: this very smile."`; for the front photo the
  target is IMG_6875 (his real smile, same tank-top session) as the expression reference.
- **replicate/1 flags for it:** `--zone expression --expression "<words>" --expression-ref PATH::LABEL` edits his own photo's expression only (the crops
  go after his face photos, the photo to edit stays last); `--rank smile` ranks passing pictures with `SMILE_PAIR_PROMPT` (FACE_PAIR_PROMPT calls any
  smirk a fault, so open smiles always lost). Gate exceptions the user approved with the plan: under `zone expression` the "returned unchanged" gate
  is replaced by the judge's "expression changed" check; under `--glasses no|yes` the glasses check asks for the change (skipping it, as first
  built, let both DSC07985 pictures pass with his glasses still on). `--loose-crop` gives a face edit the expression framing (a big close face
  otherwise fills 84% of its crop and comes back re-composed). Older recipes compile unchanged (dry runs: request = lock).
- **Expression crop (measured 2026-10-10):** `IMG_6858@v2`'s crop held his whole head at 84% of its height and Gemini zoomed out in all its returns
  (scale 0.76, not mergeable, or aligned with the head 4-5% too big): 0 passed. `--zone expression` now frames the crop the way Gemini's own
  re-framed returns did (`replicate.expression_crop`: the whole head at `EXPR_HEAD_SHARE` 0.62 of the side, the hair top at 0.12); the size gate
  is unchanged. Route A on that crop: `IMG_6858@v4`, its control `@v5`.
- **Memory:** a Gemini run beside the overnight Qwen render (`sd-cli.exe`) is paged out and stops progressing (03:41, 0.37 GB free). `tools\wave.py`
  starts a run only while no `sd-cli.exe` runs and `--min-free-gb` (1.5) has been free for 60 s, and logs why it waits.
- **Recipes (2026-10-10):** route A `IMG_6858@v2` (his front photo + the E2 crops), control `IMG_6858@v3` (no crops), route B `IMG_3884_Original@v1`,
  `DSC07985_Original@v1` (his real smiles brought to his current look), E3 `IMG_3929_Original@v1` (laughing, looking down); pizza third picture
  `v1_eyeband_send@v1` (objects mode: `_v1`'s eye band with `v2_0r`'s eyes, pasted back by `tools\region_edit.py`; the user rejected it: "made
  it even worse and drunk looking"). The "until it matches" versions: `IMG_6858@v6` (IMG_6875 as the expression reference), `IMG_3884@v1` and
  `IMG_3931_half@v2` (full originals, own face crop, expression spelled out); E3 again `IMG_3929_half@v1` (failed, above).
- **Do not retry:** the laugh looking down (IMG_3929, pitch -39) brought to his current look: 0 of 6 on the tight crop (re-composed), 0 of 6 from the
  original on the loose crop (Gemini lifts the bowed head: moved 0.21-0.29, angle changed). Adding a big smile to his neutral front photo makes
  Gemini draw the face 5-16% larger (face box and eye distance alike), so the size gate is right there.
- **Region edits of his own finished picture** (`tools\region_edit.py`; inventory `"mode": "objects", "region_edit": true` lets Route G take his own
  picture, because only the crop returns): a crop's `.json` may carry `"below"` (paste only under a line, e.g. under his eyes), and Gemini's
  sparkle is never pasted. The pizza beard fix (`v2_beard_send@v5`): fix 2 lowered the cheek beard 26->20% dark, the moustache 20->13%.
- Order the user set (2026-10-10 afternoon): the next-cut physique first (G3), then the smile task (G1), then the head-angle cells (G2, pose from
  real pixels, never "turn N degrees"); then character `me@v3` and an A/B against `me@v2` before it becomes the default.
- **G1 closed (2026-10-10):** the open smile E2 is `D:\FacecardData\approved_refs\his_smile_E2_open_front_v1.png` (run 20261010_125108 v1_0, recipe
  `IMG_6858@v7`; the user: "it is this image that I am saying is a good reference because this does not look like you did any touch-ups"); its
  `.json` holds the evidence. The laugh (E3) and route B (his older smiles redrawn to his current look: "the nose likely got changed, and the facial
  wrinkles") are dropped. Angled smiles come later in G2, generated and held to IMG_6875 with `tools\smile_match.py --ai`.

## His body references (the user, 2026-10-10)

> "Here are more photos I have attached for complete physique reference. Use them and understand my body structure in more detail. Keep them
> stored forever for future references."

- `D:\FacecardData\body_refs\2026-10-10\`: `originals\` (10 files byte-identical, sha256 in `manifest.json`, also in the blob store), `clean\`
  (IMG_6929.HEIC as JPG; screen bars cut off). `manifest.json` says what each shows. Side window light in the room of IMG_6923 shows what its
  flat light hides: the abs and obliques, the lean waist, his real arm size, the biceps vein and forearm veins. IMG_6929 is his full-length back
  (the same grey joggers as the front IMG_6923 Copy: the front/back pair). Screens IMG_7002/7003/7005/7007 carry the Photos "Crop" button and
  IMG_6997 a recording dot at the top: crops sent to Gemini leave them out.
- **His janeu:** the thin white thread from his left shoulder diagonally across his chest (or back) to his right hip is his janeu, the sacred
  thread he always wears, not an earphone wire (the user, 2026-10-10: "It is the holy thread that Brahmins wear, called jenu"). It is in every
  bare-torso picture, with his silver neck chain: `facecard.json` traits `always_worn`, checklist item 36 (evidence needed), `his_back.jpg` keeps it.
  In a mirror picture it is drawn mirrored: from his left shoulder at picture-right (the user, 2026-10-11, on pin 15: "I had forgotten that
  this was a mirror image. The genu is perfectly positioned"). Item 36 is judged beside his own photo at 100%, never against a description of
  the path (FAILURE_LOG F24); his photo shows it hanging nearly straight down the front.
- **Veins are his:** visible biceps vein and forearm veins with a faint green tint (the user). The pin 10 gym back v5 `v1_0r` that I failed on item
  32 for "prominent veins where his are smooth (IMG_6923)" passes 32 beside IMG_7005/7006; it now waits only for its janeu (item 36).
- **Physique test (G3), method A, full grey-out** (`tools\physique_greyout.py make|measure [--ai <crop json>]`; the user chose it over the 10-09
  rejection): round 1 `body_grey_send@v1` kept the waist (+1%), shrank the arms (-2%), lost both veins and the janeu; the AI part-by-part
  comparison (`BODY_MATCH_PROMPT`) agreed on all of that. Round 2 `@v2` adds three side-lit crops (IMG_7008, 7006, 7005) as references.
- **The yardstick (the user, 2026-10-10 evening):** "any shirtless picture will get the fully pumped version of mine, and casual outdoor
  dressed versions will get the casual in-between version of my body". Casual arms: "the size of the arm shouldn't reduce from the actual photo
  that I had sent, but the vascularity should lie between the real photo that I shared and the pumped photo". The approved files, byte-identical
  copies under plain names, are in `D:\FacecardData\physique\standard\`: `pumped_front.jpg` (round 3 + forearm fix), `pumped_back.jpg`
  (back round 1 + wrist fix, without the shoulder warp, which widened the triceps: "what I approved was slightly increasing the shoulder width
  and not arm size"), `casual_front.jpg` (the in-between: "still not as casual as I wanted it to be ... but it's fine").
- **Recipes take it with `--physique pumped-front | pumped-back | pumped-side | casual-front`** (`facecard.json`
  `subject_profiles.me.physique`): the standard's photo replaces the character's body photo (IMG_6923 Copy, the relaxed body before the cut),
  and its build text replaces the character's build text and an inventory's "build" item. `pumped-side` sends front and back. Without the flag a
  recipe compiles exactly as before (all Route G recipes but pin 8 v2-v4, whose drift is older, recompile to their locks).
- **Two steps when Gemini keeps changing the pin's posture or frame (2026-10-11, FAILURE_LOG F25/F26):** first `--body-only` (the pin's
  head stays and pins the frame; his body by `--physique`), then swap the head with `recipe new --method replicate --zone head --source foreign
  --look curly --current-hair` on the picture that holds. Pin 16 held the arm on the fin in 2 of 2 (one-step: 1 of 8); pin 15 held its frame.
  A background change goes the same way: him first with `--restore-background` in the pin's own framing, then only the background as a region
  edit pasted outside his outline (pin 14: one step re-framed both pictures, two steps passed all 36 items).
- **A region edit of a thin detail is pasted only along a narrow band** (the user, 2026-10-11, on pin 15: "visibly shows erase and drag tool
  usage" after a janeu fix pasted Gemini's softer redraw over 41% of his back): mask the detail's old and new path, dilated a little, never the
  whole body; check every pasted picture with a difference map against its base before calling it done (FAILURE_LOG F30).
- `tools\region_edit.py paste --affine`: the alignment is fitted on the background outside the grey area only. Back round 4's returns were
  refused by the whole-crop fit (ECC 0.76) although on the background they sit at scale 1.00 and 3 px (ECC 0.97).

## Overnight local runs: Qwen-Image-2.1 on this laptop (the user, 2026-10-09)

> "Prepare a system where the current Gemini system is intact, but a parallel system of dedicated overnight runs with multiple image
> generations is created using the Qwen local image model."

**What it is:**
- A second, separate system. `local_gen.py` makes one picture from a frozen recipe; `tools/overnight.py` runs a queue of them at night.
- The engine is stable-diffusion.cpp (MIT, an outside program): `paths.sdcpp_dir()` = `C:\LocalGen\sd.cpp\<release>\sd-cli.exe`.
- The models are in `paths.localgen_models_dir()` = `C:\LocalGen\models\qwen-image-2.1`, on the NVMe because the engine reads weights
  from disk when RAM is short. They are the user's exact `qwen-image-2.1-UC-Q4_K_M.gguf`, the 2.1 VAE, and the Qwen3-VL-8B text encoder as
  GGUF Q4_K_M (the 9.35 GB int8 one does not fit in 15.6 GB of RAM) with its mmproj. Their sha256 values are in `local_gen.MODEL_FILES`.
- Everything the system writes goes to `paths.local_dir()` = `D:\FacecardLocal`: `runs\<stamp>_qwen21-local_<goal>\` (with `local_run.json`
  and `v1_0.png`), `queue.json`, `state.json`, `overnight.log` and `summary\<date>.html`.

**How a recipe becomes a local picture:**
- The lock's images are staged byte-identical from the blob store, with the photo to edit FIRST: in Qwen-Image-2.1 image 1 is the image
  being edited and sets the canvas.
- The lock prompt is renumbered for that order and written with the model's reference tokens `<image1>`..`<imageN>`.
  stable-diffusion.cpp labels each reference that way, and ComfyUI's 2.1 guide addresses images as `<image1>`.
- The prompt reaches sd-cli as a UTF-8 file (`--prompt-file`), never on the command line, which would pass through the ANSI code page.
  Every transform is recorded in `local_run.json`.
- Settings: cfg 1.0 (above 1 doubles the time), euler, sizes divisible by 32, the reference-image cache as q8_0.
- `--mmap`: the model files are memory-mapped, so their pages do not count against Windows' commit limit and can be dropped and
  re-read under pressure. On 2026-10-09 the daytime machine had 0.4 GB of RAM free and 2.4 GB of commit left.
- The same program, models, arguments AND thread count give the same picture; all of them are recorded.

**The night (`tools/overnight.py run`, task `facecard-local-overnight` daily 04:00 through runhidden):**
- The user, 2026-10-11: "lets set it from 4am ist to 11am or beyond". The window in `queue.json` is start 04:00, no start after 06:00,
  hard stop 11:00; `finish_started` lets a started picture run past 11:00. The 23:30 start made room at 00:02 while he was still up
  (10 idle minutes counted as away), so the night was cancelled and everything was put back.
- One picture at a time, only on AC power, no new picture after `last_start`, and none whose predicted time would pass `hard_stop`.
- It keeps the PC awake. The lid on the charger was set to "do nothing" on 2026-10-09, with the user's approval; on battery the lid
  still sleeps it. The user must stay signed in (locking the screen is fine).
- Memory, in this order (the user, 2026-10-09: "Pause llama-router during Qwen runs"; "make space on your own by smartly tracking what
  processes the ongoing claudecode tasks require and eliminating others"):
  - It pauses the `llama-router` task: the task is disabled, ended, and every llama-server is stopped. The task restarts itself on
    failure, so a plain stop came back 63 s later. At the end of the night it is enabled and started again, and the start is checked.
    A marker file (`llama_router_paused.json`) makes `run` and `status` undo a pause whose process died.
  - It needs commit headroom of 1.15 x the measured peak commit (6 GB unmeasured): running out of commit crashes Claude Code
    (0xC0000409).
  - Since 2026-10-10 it first makes room (below), then waits up to 30 min for the picture's measured peak + 1.5 GB to be free, then
    starts with whatever is free if that is at least 3.5 GB. With `--mmap`, the model's pages come from its file, so a short machine
    pages instead of failing.
  - It uses `schtasks`, ctypes and psutil, never PowerShell, because under memory pressure PowerShell took over 2 minutes just to start.
- Its watchdog measures progress: the (phase, step) value must change within max(3 x the measured time, 15 min), or the run is stopped,
  retried once, then skipped. The phases come from sd-cli's own log lines (`local_gen.PHASE_MARKERS`).
- `status` shows the live progress (`progress.json`), and the morning page lists each picture with its time and memory.

**Measured on this laptop (2026-10-09, pin 6, 5 references capped at 512x512, normal priority, about 2.4 cores):**

| Phase | 512x640, 2 steps |
|---|---|
| encode the references (VAE) | 353 s (~70 s a reference) |
| text encoder (prompt + 5 images, about 4.5k tokens) | 937 s |
| first step (it also builds the reference cache) | 1,960 s |
| each later step | 429 s |
| decode (VAE, tiled) | 529 s |
| total | 70 min; peak working set 6.7 GB, peak commit 5.4 GB |

- With llama-router holding 7.5 GB, the same run starved at 0.3 cores, and at below-normal priority it got leftovers. So a daytime
  trial uses `--priority normal`, and nights stay below normal.
- The 2-step picture already had the pin's composition, with the brush clamped between his teeth.

**No compromises on quality (the user, 2026-10-10):**

> "just because my own machine is not capable of generating quickly doesn't mean you start making compromises on image quality or our
> goal ... do not make any compromises and generate a perfect system's output itself."

On 2026-10-09 I shrank the night picture to 640x800 and the references to 512x512 so it would fit a night. That run was stopped and is
marked abandoned. A slow machine gets more time and faster hardware; it never gets a smaller, shorter or lower-precision picture.

Full quality means Alibaba's own defaults and the system's standard:
- The edit at the photo's own size: 1200x1500 becomes 1152x1440, the closest exact 4:5 with both sides divisible by 32.
- References at the model's default size (`--refs-cap 0`).
- 40 steps (Alibaba's example), cfg 1.0, euler.
- The model's own int8 text encoder, which carries its vision tower (`--te int8`).
- The reference cache stays q8_0, "about bf16 accuracy" per ComfyUI's 2.1 guide.

**Speed comes from hardware:**
- The Vulkan build on the Intel UHD iGPU (`--engine vulkan --backend vulkan0`) made the same picture for the same seed with no
  artefacts, 3.3x faster: 21.5 min instead of 70.4 for the trial shape. References took 196 s, the text encoder 282 s, the first step
  about 608 s, each later step 112 s, and the decode 79 s.
- At full quality that is about 13-14 min a step and about 10 h a picture (about 40 h on the CPU).
- stable-diffusion.cpp cannot save a half-made picture, so a started picture runs to the end: `window.finish_started` (default true)
  disables the hard stop for it, and the night task's time limit is 23 h.

**Full quality does not fit this laptop's memory (measured 2026-10-10, run `20261010_021500`, marked abandoned):**
- With no cap, sd-cli sizes every reference to the output area: about 1.65 MP each.
- The text encoder then reads 16,120 image tokens (1,706 s). The diffusion prefix grows to about 50k tokens, and its q8_0 cache needs
  about 13 GB.
- The iGPU's budget is about 6.4 GB: "insufficient memory for prefix caching". Even without the cache, block 0 needed 6.3 GB, and
  sampling failed.
- The no-compromise fix is hardware. The two 8 GB DDR4-3200 SO-DIMMs can be replaced with 2x32 GB (the i3-1115G4 takes 64 GB), which
  gives the iGPU about 32 GB.
- The user's decision, 2026-10-10: "Test picture now, then decide". One TEST picture: 1152x1440, 40 steps, the int8 encoder,
  references capped at 512x512, which judges whether Qwen is worth the RAM. It is never a final or gold result.
- The user on bit-width, 2026-10-10: "it doesn't mean that the 4-bit quantized model cannot produce that. There is no necessity for an
  8-bit quantization model". Full quality is about the picture: its size, its steps and its reference detail, not the files' bit-width.

**The test picture did not finish (2026-10-10, both runs marked abandoned):**
- `20261010_033943`: references 53 s, text encoder 581 s, first step 1,129 s, later steps 303-963 s. It died at step 5 of 40 when
  `os.replace` onto `progress.json` raised PermissionError; `save_json` is best-effort since.
- `20261010_050604`: references 70 s, text encoder 521 s, then no step finished in 3 h. On the iGPU the image model's weights are
  streamed from disk every step ("params disk"), and with 0.01 GB of RAM free the reads fell to 0 MB/s. The watchdog stopped it at
  08:16; the supervisor then crashed on `proc.wait(timeout=60)` (now 10 min, and it records the attempt either way).
- With no picture running (08:45), 4.1 GB of RAM was free and 28.5 GB was committed. The test picture needs about 7.5 GB plus room to
  keep the 4.6 GB model cached, so on 16 GB it runs only with the rest of the machine closed.

**Making room (`tools/room.py`; the user, 2026-10-10):**

> "Apart from VS Code, which has multiple tabs of Claude Code running, everything else can be closed. Even inside VS Code, ideal Claude
> Code tabs can be closed as well, and only active, running ones can be kept to make up space for our local Qwen run."

What comes back, in his answers: "only wispr flow, opencode, and edge that too reopen only if they were open at night and got closed for
ram", when he is back (his first keyboard or mouse use after 06:00); the job bots restart after the picture.

- The night waits until he is away: 10 min without keyboard or mouse, or 45 min while something keeps the screen on. It also waits for
  any Gemini picture run to end; a logged-in run is never killed. If he touches the keyboard or mouse while room is being made, it puts
  everything back and waits again (until `last_start`).
- `C:\LocalGen\room\room.json` records each change before it is made, so a crash can always be undone. The `facecard-local-restore` task
  (every 30 min and at sign-in, also on battery) puts back a room whose night is gone. To run it by hand: `schtasks /Run /TN
  facecard-local-restore`.
- **Closed:**
  - The job bots, only between applications: Naukri when its log's last line is the cooldown's "Next search cycle starts at" at least
    2 min ahead, Instahyre when its state says `InCycle: false`, LinkedIn while resting. They share one 90-min budget; a bot still busy
    after it is left running. Their tasks are switched off first, because the supervisors restart the bots.
  - herdr (with Pi in it) before opencode, then both opencode servers (their two tasks switched off first), Claude Desktop (kept if it
    hosts a Claude Code session), Teams, Wispr Flow, his own Edge (the one without the bots' `--user-data-dir`), and the DaVinci/Kinocut
    helpers.
  - Idle Claude Code tabs, each re-checked just before. A tab stays if it is the watching tab (`queue.json` `room.keep_sessions`), is busy
    or waiting, has a child other than conhost and its MCP helpers, has a ScheduleWakeup or CronCreate pending since its process started,
    or did anything in the last hour.
- **Left running:** VS Code and everything under it, Google Drive (the G: second brain), memory-guard, Gemini runs and waves, Blip
  (forcing it closed breaks it), OneDrive, QuickLook, the Ungate and Antigravity proxies, small utilities. Anything else is "unknown" and
  is named on the morning page. `overnight.py room-plan` prints all of it, and changes nothing.
- **Coming back:** the bots through their own tasks after the picture, one at a time: enable, wait 60 s, run only if no supervisor
  started (two supervisors started together both quit). Wispr Flow, opencode and Edge (with `--restore-last-session`) come back when he
  is back. If the picture is already done, the night waits for him until 18:00. Teams, Claude Desktop, herdr and Pi stay closed. A
  closed tab keeps its history; typing in it resumes it.
- **Rules learned here:**
  - A process is (pid, creation time): pids are reused. The lock, markers and claim store both.
  - Never `taskkill /T`: it follows stale parent pids (memory-guard's runhidden has a dead parent). Never `/IM`: the bots share msedge.exe
    and python.exe.
  - A Claude Code tab is `~/.claude/sessions/<pid>.json` plus the extension's own `native-binary\claude.exe` with a matching start time.
    Claude Desktop is also named claude.exe. An idle tab ends with exit code 0xFFFFFFFF, which shows no error line in VS Code (drill,
    2026-10-10: the "NotebookLM" tab ended with exactly that code and did not respawn). Never read `sessions\*.key`.
  - Apps reopen through Explorer, with `ELECTRON_RUN_AS_NODE`, `VSCODE_*` and `CLAUDE*` removed, so Electron apps start normally and sit
    outside the task's job.
- `tools/wave.py` holds Gemini waves off while the night's claim (`C:\LocalGen\room\claim.json`) names a live process, not only while
  sd-cli runs.
- `local_gen.py` writes one line per phase change and per finished step to `overnight.log`. A watcher reads only that log, never
  `progress.json`: a reader holding that file open crashed a run.

**Kept apart from Gemini:**
- Never write or list `.cache\inflight`: the cookie keep-alive skips renewal while it has entries.
- Never write under `outputs\`, never create a file named `run.json`, and never create `01_method\recipe.json` in a local run: those
  make `best_check.py` export, or make a folder look like a Gemini run.
- QC of a local picture uses the Gemini system's own tools without changing them:
  - `facecard.py run <recipe> --remeasure <local run folder>` gives the pose gate, identity, character sheet and a report. It makes no
    network call. Its report shows the Gemini prompt order; the local `prompt_qwen.txt` is the real prompt.
  - `tools/best_check.py` is recorded in the local folder, never on the remeasure copy.
- Licence: the Qwen Research License allows only non-commercial use (research or evaluation). The paid app would need Alibaba's
  commercial licence. Users found the "uncensored" file's tensors bit-identical to the base model.

## The loop for a goal

1. **Ask the user what looks wrong, in their own words.** Done when their words are the `--because` of the next version.
2. **Freeze the method**: `facecard.py recipe new --goal ... --prompt ... --inventory ... --replace-subject --character me@vN --because "..."`
   (another man's photo), or `facecard.py recipe new --method replicate --goal <his photo> --character me@vN --because "..."` (his own photo),
   or `facecard.py recipe bump <goal>@vN --<what changes> --because "..."`. Done when the version file is written and its lock diff printed.
3. **Prove it**: `facecard.py run <goal>@vN --dry-run` (free). Done when stage 03 says the request equals the lock.
4. **Run it**: `facecard.py run <goal>@vN --samples 2` (the credit guard paces it; `tools\wave.py` runs several recipes). Done when the run
   reaches stage 08 or names the stage that failed. A wave checks the Gemini sign-in before every start (`tools\session_check.py`), halts on
   a refusal that lasts 7 minutes or a credit-guard refusal, tracks its runs by process in `.cache\wave_<tag>.runs.json`, and is stopped only
   with `tools\wave.py --stop <tag>` (`--now`: also its runs not yet signed in), never by killing PIDs by hand (FAILURE_LOG.md F1). Exit codes:
   0 pictures, 1 no picture, 2 method refused, 3 credit guard, 4 a later stage failed, 5 sign-in failed. A run without an accepted picture
   writes a line to `.cache\failures.jsonl`; its cause goes into `FAILURE_LOG.md`.
5. **Review**: open the run's report in `D:\FacecardReview` (`index.html` lists every run), judge all 35 items of `BEST_CHECKLIST.md` by eye,
   record each picture with `tools\best_check.py`. Done when every picture has a checklist; a pass exports itself to `D:\FacecardResults`.
6. **Debug from records**: `facecard.py diff <runA> <runB>` (request, code, outcomes) and the reports. Report run folders and stage numbers.

`facecard.py gen --goal ...` is for exploration; adopt a good exploratory run with `facecard.py recipe import-run <run> --because "..."`
(it refuses unless today's code reproduces the run's prompt from files that predate the run).

## The eight stages (each writes `NN_<name>/` in the run folder, beside `manifest.json`, `run.log`, `run.json` and `report.html`)

| # | stage | evidence it leaves |
|---|---|---|
| 01 | method | recipe copy, integrity, drift (`drift.diff`), `env.json` (argv, git state, packages, models, gate limits), preflight, the own-photo check (Route G refuses his own photo), the character check |
| 02 | inputs | pinned goal + its keypoints, `references.jpg` ("Image N - ROLE - name - why"); replicate: `crop_on_original.jpg` |
| 03 | request | `prompt.txt`, `request.json` (`request_sha256`), the exact files sent, the inventory lint |
| 04 | credits | account, the model's listed name (MODEL CHANGED when Google swapped the model behind the id), the credit guard's decision |
| 05 | generate | one `call_N.json` per Gemini call: outcome, reply, ids, picture size, full size or preview, library log, credits; replicate: each attempt's merge, gates and AI judge |
| 06 | measure | pose gate, identity (gen's rule), light (replicate: its own gates); record-only: faces found, face size, grey diff to the goal, pool identity, head pose, C2PA, character measures against the band |
| 07 | review | audit sheets per picture (head row beside his references, hands), the character sheet (items 31, 32), checklist status |
| 08 | result | ranking with every sort key, `best.jpg` (never a pose-gate fail; replicate: `best.png`), export and ledger lines |

Exit codes: 0 done, 1 no picture or authentication, 2 the method stage refused (before any credit), 3 credit guard refused, 4 a later stage failed.
`--remeasure <run>` re-runs 06-08 on a run's pictures with no Gemini call.

## Character consistency options (research 2026-10-07: how AI influencers stay consistent)

Studios keep a face constant by fixing it as an asset (a 3D head composited onto real photos: Imma, Shudu, Lil Miquela; a trained model;
or one face swapped onto every post: Emily Pellegrini), then curating by eye. Training, seeds and 3D heads do not exist in the Gemini app, so
three request-level techniques are implemented as recipe options (off unless a recipe sets them; older recipes compile unchanged):
- `--build-sheet` with `--face-count 3`: at most 4 images of him (Google documents Nano Banana 2 at up to 4 character images; Route G sent 6).
  His body and arm photos go as one side-by-side image of his real photos.
- `--head-swap`: the replace-subject edit worded as a whole-head swap (face, hair, beard, ears), because face-only wording keeps the target's hair.
- `--identity-bible`: `prompts/identity_bible.txt` (his traits read from the current studio photos), frozen into the recipe, stated first and repeated last.
Deferred: one refine turn in the same chat with the face photos re-attached (about 75 credits more per picture), and a 2x2 face sheet
(expected to lose detail). Each option is judged as an A/B against the version without it (same goal, same window), confirmed by a second
wave before it becomes a default.

## Models: Nano Banana 2.1 and Flash (2026-10-08)

- `gemini_webapi` (2.1.1, the newest release) chooses only the CHAT model by header id (Flash `56fdd199312815e2` = "3.8 Flash", Pro
  `e6fa609c3fa255c0` = "3.1 Pro"); the app chooses the image model. `tools/model_probe.py` found the same image tool id (`imagen_default`) in
  the raw reply of both, no model version, and Google's C2PA manifest names none either. Google: Nano Banana 2.1 has been the default
  image model for AI Pro accounts since its rollout began on 2026-10-06 ("Redo with Pro" for Nano Banana Pro is an app button the library
  cannot press). So every run already uses whatever 2.1 rollout the account has; runs before 2026-10-06 used the older model.
- A recipe's model id does not pin the model: Google swapped the model behind the flash id. Stage 04 records the listed name and shows
  MODEL CHANGED when it differs from the recipe's (`method.model.display`) or the last run's (`.cache/models_seen.json`).
- Flash is the default for new recipes and finals. Pro only by `recipe bump --model pro --because "<failed item>"` after Flash failed twice,
  or when an A/B on the same request shows Pro better. Solo probe cost: Flash 33, Pro 38 credits per picture; the guard reserves 120 / 150.

## Where things live

| place | holds |
|---|---|
| repo root | flat modules (`facecard.py` CLI, `runner.py`, `recipe.py`, `provenance.py`, `report.py`, `replicate.py`, ...), `recipes/`, `prompts/`, `tools/`, `skills/`, and the records the tools read: `facecard.json`, `results_names.json`, `BEST_CHECKLIST.md`, `FEEDBACK_LOG.md`, `FEEDBACK_LEDGER.md` + `feedback_ledger.json`, `FEEDBACK_MATRIX.xlsx` |
| `.cache/` | state and caches (gitignored): prepared references, goal copies, inventories, poses, the credit guard's registry |
| `outputs/` | run folders (gitignored) |
| `D:\FacecardData\blobs` | exact bytes of every file a recipe sends (content-addressed, read-only) |
| `D:\FacecardReview` | every run's report + `index.html` |
| `D:\FacecardResults` | passed pictures only, flat names `<collection>_<NN>_<title>_v<N>.jpg` |
| `D:\FacecardGold` | the gold tier: read-only copies of the user's five gold pictures (`gold.json`, `tools/gold_tier.py`) |
| `C:\LocalGen` | the local system's engine (`sd.cpp\<release>`) and Qwen-Image-2.1 models (`models\qwen-image-2.1`), outside the repo |
| `D:\FacecardLocal` | the local system's runs, queue, state, night log and morning summaries (`local_gen.py`, `tools/overnight.py`) |
| `D:\FacecardArchive` | archived runs, scratch and checkpoints (with a `MANIFEST.tsv` per move) |

## Standing rules

- **Auto-continue (the user, 2026-10-11: "create a system to auto-continue for claude code when gemini image credits refresh"):** work
  never waits for a reply or for a refill. A ready wave goes into the queue (`tools\autocontinue.py add <spec>`); the hidden task
  `facecard-autocontinue` (every 15 min, `tick`) starts the next one when the window holds its credits, no wave runs and the overnight
  render holds no claim. Every session starts with `tools\autocontinue.py status`: it reviews the waves listed TO REVIEW (36 items, then
  `reviewed <tag>`) and works every [claude] to-do marked READY without asking. A recommended next step that is not risky is queued, not
  asked about (2026-10-10: three idle hours after a question, through a full refill).
  - **A [user] item never holds up a [claude] item** (2026-10-11: five idle hours and a whole credit window unused while three [claude]
    to-dos waited behind questions, FAILURE_LOG F31). [user] items are only the user's approvals and own choices. A question that has a
    sensible answer is filed with `todo "<question>" --who user --default "<step>"`: the default becomes a [claude] item, done at once, and
    the user can redirect it. Only `--after <tag>` (waiting for a wave) lets a [claude] item wait.
  - The decision reads `work` while Claude has work and `STALLED` after 60 minutes without progress (the tick then sends the user one
    toast). Answer the loop "no change" only on idle, busy, waiting or ready.
  - **Spare credits are work** (the user, 2026-10-13: "since so much credit is left, why are you not processing anything?", FAILURE_LOG
    F47): the decision always shows the 5-hour window (credits left, reset time, hours to it). When the window still holds 600 credits or more
    after the queued waves, nothing is queued and fewer than 2 waves run, the first goal of the standing `backlog` (`autocontinue.py backlog
    add|done|list`) is the work: prepare it, queue it, `backlog done <n>`. Credits unused at the reset are lost. Keep the backlog filled with the
    goals the user has asked for; an empty backlog with spare credits is itself reported.
  - **The periodic timer calls `autocontinue.py ping`**: `NOOP` when nothing needs doing (reply "auto-continue: no change"), otherwise a work
    order that lists the tasks; do them. One timer job only (check `CronList` after every restart; duplicates fire the prompt several times).
  - **A claim is not idle either** (2026-10-14: three open claims answered "idle: no [claude] to-do"): the ping lists claimed items as
    "busy: claimed work in progress", and after 60 minutes with no progress it hands out a CLAIMED WORK task (finish it, read the agent, or release
    the claim). Close every claim with `done-todo` / `backlog done` when its job ends.
  - **A wave stuck on the memory gate is not "busy"** (FAILURE_LOG F57, 2026-10-14: pin12b waited 55 min at 0.7 GB free): after 10 minutes of
    `memory: ... waits` lines in its log the ping hands out a FREE MEMORY task. The 1.5 GB gate stays. Close only what is idle (Claude Code
    tabs idle over an hour with no timer or background job, windowless background apps), never this tab, the bots' browsers, his Edge or an app
    with live children; if the wave still waits after a few minutes, tell him which choice is left (restart Pylance, pause the appliers).
  - **Questions are asked at once and never wait** (the user, 2026-10-11 23:0x: "immediately ask using ask-user-question tool and on top
    of that still not be blocked by it and just choose the recommended option to keep working on until i answer"): start the recommended
    option's step, file the question (`autocontinue.py ask ... --default ...`), hand long preparations to background agents, then ask
    with AskUserQuestion from the session itself (`autocontinue.py questions --mark-asked`; subagents cannot use AskUserQuestion). Record
    the reply with `autocontinue.py answer <n> "<label>"`, which files a redirect item when he chose otherwise.
  - **Exception, 2026-10-14: a question about pictures is never a dialog** (a dialog hides the chat text above it and shows no clickable
    links; the hook `~/.claude/hooks/link-format.mjs` denies it). End the turn with a normal message that holds the picture links
    (`[name](nano-banana-facecard/outputs/<run>/<file>)`, `[name](FacecardResults/<file>)`) and put the question in plain text under them;
    record his chat reply with `autocontinue.py answer <n> "<label>" --note "<his words>"`.
- **Every failure gets an entry in `FAILURE_LOG.md`** (the user, 2026-10-10: "Keep a record of why each of those is happening"): what failed,
  the evidence, the cause or "unknown" with its assumption, the cost, the fix, open or closed; failures that share a cause go under its
  patterns. A running wave is never stopped abruptly to fix the system: rework waits until it ends (the user, same day).
- Secrets come from the DPAPI vault inside the process (`session.py`); run logs redact cookie values.
- The Gemini session runs itself (2026-10-09): runs never renew the cookie (`auto_refresh` off); `tools/gemini_keepalive.py` (task
  `facecard-gemini-keepalive`, every 6 h, hidden) is the only renewer, under `.cache/gemini_session.lock`; a run saves a changed cookie only
  if no other process saved one since it started; dead vault cookies are read from the signed-in google-1 browser profile
  (`gemini_cookies.py`, the user's choice). Never force-kill a logged-in run: it holds the newest cookie.
- Pins 10-13 lessons (2026-10-09): a Route G Flash image costs about 160 credits metered (not the 33 of a solo probe), so a 2,400 window holds about 14 pictures; start recipes 3 minutes
  apart (`.cache/launch_wave_*.sh`), because stage 06 ran out of memory with four at once (YOLO "not enough memory" on 4 of 8 pictures; `facecard.py run --remeasure <run>` redoes it).
  A view the user asks to change (the print on the FRONT of a back-view pin) is a text-mode recipe (the goal is not sent) and makes checklist items 12/14/30 N/A: say so. Garment
  lettering and his beard go in as reference crops (`--prop PATH::LABEL`, or inventory `refs`): text alone drew the wrong typeface with an outlined last line twice, and his beard as stubble.
  `--layout-image` sends a sketch only when `.cache/layouts/<goal>.json` exists, so run `tools/goal_layout.py <goal>` BEFORE the bump (and it was ignored on pin 13). "Turn his head N
  degrees" overshoots (8, 12 and 60 degrees all gave profiles): for a hidden-face pin ask for the pin's own head pose, and for a changed head do it as a second edit of a render that already passed the pose gate.
- Verification is real runs: dry runs, re-measures, a paid run. Unit tests, mocks and stubs have no place here.
- The AI renders; code copies and measures. Gemini's pixels are never post-processed, and exported pictures stay byte-identical (each sample
  carries Google's signed C2PA manifest). **One exception, the user's decision of 2026-10-09:** an edit-mode pin whose recipe sets `restore_background`
  gets the pin's OWN background pixels copied back around him (`tools/background_restore.py`: only the union of the two person silhouettes comes from Gemini;
  the raw `vN_0.jpg` is never touched, the copy is `vN_0r.jpg` and carries its own checklist; its C2PA no longer validates). Copying pixels that must not change is
  still "code copies"; nothing Gemini drew is altered. Details measured on pins 10, 11 and 13: where the sample differs from the pin by more than 28 grey levels within 6% of the
  longer side of a silhouette, Gemini's pixels are kept too (the pin man's hair bun outside the YOLO mask came back above the new head without it); a sample that re-framed
  the picture is refused (ECC < 0.80, scale outside 0.97-1.03, shift over 3%, background SSIM < 0.45); Gemini's sparkle watermark becomes the pin's pixels unless a
  silhouette reaches it (then the whole star stays as produced, never half of it); overlays of the pin (Pinterest's "1/7") are excluded by `.cache/restore_exclude/<goal key>.json`.
  `tools/wave.py` does it after each run of a job with `"restore": true`.
- **Three standing rules (the user, 2026-10-09: "rules you are forgetting, when not given a reference or when given as well"), checklist items 33-35:**
  no background people are added (the goal's own stay as they are; a text-mode setting is written empty); no text is added (the goal's own stays letter for letter,
  asked-for lettering is sent as a reference crop, shop signs and screens are unreadable glow); and a picture with no reference to follow reads as a quick
  handheld phone shot caught in a rush (slight motion blur, tilt, off-centre, grain). They live in `BEST_CHECKLIST.md`, the scene-prompt-writer skill
  (`capture: candid`, empty setting, text rules), `tools/inventory_lint.py` (inventory keep lines, `--scene <paragraph>`), and `tools/best_check.py` (evidence needed).
- **His back (the user, 2026-10-09):** `D:\Downloads\B9F9CBB0-9336-4E0A-83BF-F6E6BF72BA79.MP4` shows his current back from behind; frames in `D:\FacecardData\back_video`,
  the reference image `his_back.jpg` (inventory ref for back-view goals) and the record-only back measures in `D:\FacecardData\back_video\back_measures.json`.
  `tools\back_reference.py build` cuts frames 54 and 74 (1.80 s and 2.47 s) out of the video by exact frame index and keeps his janeu, the thin white sacred thread
  across his back (2026-10-09 I took it for an earphone wire and painted it out; the user, 2026-10-10: "It is the holy thread that Brahmins wear, called jenu";
  `--remove-thread` still exists, only on request; the old file is `his_back_2026-10-09_thread_removed.jpg`), and writes `.cache\inventories\pin_refs\his_back.jpg` +
  `his_back.json` (video sha256, frames, crop);
  `measure <image>...` records sw_px, hw_px, torso_px, sw_hw, sw_torso and silhouette widths in one unit for his frames, the pin man and a result (his four frames: sw_torso 0.55-0.63,
  sw_hw 1.44-1.47). Item 32 on a back view is judged by eye beside the frames. A back view with the face hidden keeps the face as lean and defined as the back, never smoother.
- The GitHub repo is public: images, blobs and run folders stay out of git. Commit or push only when the user asks.

## Pointers

- `skills/gemini-identity-gen/SKILL.md`: how the pipeline works, its measured limits, the loop-until-perfect lessons. Read before a bump.
- `skills/facecard-session/SKILL.md`: session start and end, reviews, the prune.
- `FEEDBACK_LEDGER.md`: every picture's result with what was wrong and right; read the goal's section before a bump.
- `docs/image-gen-process.html`: the process, written for people.

## Prior art (open source, surveyed 2026-10-07)

Patterns adopted, implemented in our own code (no code copied):
- [DVC](https://github.com/iterative/dvc) (Apache-2.0): `dvc.lock` hashes every input and output of a stage -> the recipe lock and the manifest.
- [Hydra](https://github.com/facebookresearch/hydra) (MIT): each run keeps its resolved config -> `01_method` (recipe copy, `env.json`).
- [FaceFusion](https://github.com/facefusion/facefusion) (OpenRAIL-AS): per-step job records -> `manifest.json`. Also used as-is, in its own
  venv, by `restore.py`.
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) / [InvokeAI](https://github.com/invoke-ai/InvokeAI) /
  [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui): the workflow is stored with each output -> run records and the
  ledger, kept beside the JPEG (Google's C2PA signature covers the file's bytes).
- [FaceChain](https://github.com/modelscope/facechain) (Apache-2.0) `post_process_fn`: one face, minimum face size, a ranked list -> the
  record-only measures of stage 06.
- Google's [consistent imagery notebook](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/use-cases/media-generation/consistent_imagery_generation.ipynb)
  (Apache-2.0) and the Nano Banana prompting guides: inputs named by number and role ("Image 1 is ...").

Modules used as-is, after a fit check (2026-10-07), record-only (they never decide or reject anything):
- [yakhyo/head-pose-estimation](https://github.com/yakhyo/head-pose-estimation) (MIT): `HeadPoseONNX` + its `SCRFD` face detector, vendored
  verbatim in `vendor/head_pose/` (source commit and file hashes in `SOURCE.md`; weights in `models/head_pose/`), driven by `headpose.py`.
  SCRFD finds the bowed faces of pins 5 and 6 that YuNet misses; where both detectors work the readings agree within about 1 degree.
  Yaw > 0 = face turned toward picture-left. It writes the goal's measured head turn into a recipe's face-choice evidence (with a warning
  when it contradicts the chosen bin) and each picture's head pose into `06_measure`. Its keypoint-crop mode flipped the yaw sign on 2 of 5
  goals, so faces are always cropped by SCRFD.
- [c2pa-python](https://github.com/contentauth/c2pa-python) (MIT/Apache-2.0): reads the C2PA manifest Google signs into every picture;
  `06_measure` records it (`Valid` = the bytes are exactly Google's output; the "untrusted certificate" note only means no trust list is set).
- Not adopted yet: [rtmlib](https://github.com/Tau-J/rtmlib) `Wholebody` (Apache-2.0, ONNX) for hand and mouth keypoints (pin 6's pencil);
  needs `--no-deps` because of an OpenCV variant clash.

Character measures (2026-10-08):
- Facial adiposity measures: Coetzee, Perrett & Stephen 2009 ("Facial adiposity: a cue to health?") and Coetzee et al. 2010 ("Deciphering
  faces: quantifiable visual cues to weight"): cheek-to-jaw width ratio, width-to-height ratio and perimeter-to-area ratio track BMI in men.
  Computed in `character.py` from the 68 landmarks of FaceFusion's 2dfan4 model already on disk.
- Body measures from `yolo11m-pose` keypoints and the `yolo11m-seg` person mask (both already in the YOLO venv).
- Design reference only (non-commercial licences, GPU, SMPL model files): [SHAPY](https://github.com/muelea/shapy) (height, weight,
  chest/waist/hip from one photo), [SMPLify-X](https://github.com/vchoutas/smplify-x).

Design reference only:
- GPU-only identity generators: [InstantID](https://github.com/instantX-research/InstantID), [PhotoMaker](https://github.com/TencentARC/PhotoMaker),
  [PuLID](https://github.com/ToTheBeginning/PuLID), [InfiniteYou](https://github.com/bytedance/InfiniteYou),
  [IP-Adapter FaceID](https://github.com/tencent-ailab/IP-Adapter), UniPortrait, ConsistentID, StoryDiffusion, [ConsiStory](https://github.com/NVlabs/consistory).
- GPL / AGPL code stays out of this MIT/Apache repo: [Fooocus](https://github.com/lllyasviel/Fooocus), ComfyUI, roop, ReActor;
  [gemini_webapi](https://github.com/HanaokaYuzu/Gemini-API) (AGPL) is used as a dependency.
- No fit here: pyiqa (non-commercial licence, heavy dependencies), deepface (TensorFlow), MediaPipe (no Python 3.14 wheels),
  imagehash and colour-science (no calibrated use yet).

Open hypotheses, each a candidate `recipe bump` (test one at a time, judged by the user):
- Pin 5's face references were chosen for a head turned toward picture-left (the route text said "25 degrees toward picture-left"), but the
  goal's measured head turn is 18 degrees toward picture-right (yaw -18, pitch -47). The user still called recipe v1's renders great.
- Nano Banana Pro takes up to 5 character images; Route G recipes sent 6 photos of him (4 face, body, arms). Character recipes send 4.
- Upload names such as `IMG_5850_fav_34left_head768_...jpg` reach the model with the files (replicate/1 sends neutral names: `face_front.jpg`).
- An edit keeps the edited photo's body (the audit: the body follows the goal). Measured 2026-10-09: replicate/1 pass A (`--zone build`,
  the character's build text + a frozen reading "shoulders and upper arms clearly slimmer") returned the kayak and mirror bodies UNCHANGED
  (AI judge "the same", silhouette widths 1.00, by eye identical); a Route G body-only pass with a percent magnitude moved pin 8's arm width
  only 1.67 -> 1.60, and a second one moved the camera (pose gate 29). DO NOT RETRY wording variants of "change his body, keep everything
  else". Also measured 2026-10-09: prompt version 2 (the clothes may change, only his head, pose and scene kept, the user's idea) returned
  the body unchanged in 8 of 8 attempts (kayak v9, mirror v7: judge "the same", widths 1.00): an edit of the photo keeps the body outline. Candidates still untested: the body region greyed out in the photo to edit (inpaint, so the body must be redrawn from his body
  photo), or the goal's pose and clothes as text with no photo to edit for the body.
- The goal is re-encoded before it is sent (the board file, then the `.cache` copy, then the prepared copy).
- The full-size download is attempted but returns no URL, so every picture is the preview (about 1 megapixel); `call_N.json` records it.

## Time: IST only, on this whole computer (mandatory)

The user, 2026-10-21: "dont use UTC timing anywhere on this computer ... apply 1 common rule to use IST only."

- Every time you say, write, log, store, schedule, compare or show is IST (India Standard Time, UTC+05:30, this PC's own clock). Never UTC, GMT or a "Z" time.
- A day is an IST calendar day, midnight to midnight. When a service resets at another time of day, give that time in IST ("LinkedIn's count resets at 05:30 IST"), never as "00:00 UTC".
- A time you meet in UTC (a site's reset time, a cloud tool's log, an API field) is converted to IST before you use, show or store it. A time the user quotes is IST.
- Code written or edited here uses local time (`datetime.now()`, `Get-Date`) or `ZoneInfo("Asia/Kolkata")`. No `utcnow()`, `gmtime`, `-AsUTC`, `ToUniversalTime()`, `date -u`, `TZ=UTC`, and no `Z`-suffixed timestamps in logs, files, databases, dashboards, file names, schedules or messages.
- Only a third-party protocol that forces UTC (HTTP headers, JWT or cookie expiry, a GitHub Actions cron) may touch UTC, and only at that edge: convert on the way in, never store or show it.
