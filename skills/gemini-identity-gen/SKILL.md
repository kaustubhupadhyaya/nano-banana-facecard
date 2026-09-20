---
name: gemini-identity-gen
description: Put the user's face into a source photo (their own or someone else's) without changing anything else in it, or generate identity-consistent images of the user from scratch, via their Google AI Pro Gemini web session (no billed API). Use for "generate a photo of me", "replicate this photo with my face", "facecard", "nano banana [pro]", "face restore", or anything mentioning __Secure-1PSID/__Secure-1PSIDTS cookies. For writing scene prompt text for from-scratch generation, use the scene-prompt-writer skill.
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
| A source photo (theirs or a Pinterest/Instagram image) to reproduce with the user's face | **`replicate`** | Edits a crop and pastes it back into the untouched original. Background, clothes, body and framing cannot drift. |
| No source photo, a scene described in words | `gen` | Draws a new image. Everything is regenerated, so expect drift outside the face. |

`gen --scene-image` now just runs `replicate`; the prompt text is ignored, because the photo is the scene.
**Never describe a source photo in words and ask for a new photo of it.** That is what redrew the whole frame,
changed the pose, clothes, background and physique, and dropped glasses (measured 2026-09-19/20).

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

## Scorer and pool (identity.py, scorer.py, landmarks.py, calibrate.py)

- Pool = every photo of the user (FaceCard_Originals + `.cache/super_favs`), derived files (mirrored, headless) excluded,
  near-duplicates of the photo being scored excluded (leave-one-out). Never add a mirrored copy: faces are not symmetric.
- Score = mean of the 3 most similar pool photos (was: max over all, which one lucky photo could decide).
- Embedding = ArcFace `w600k_r50` on an upscaled head crop aligned with FaceFusion's 2dfan4 68 landmarks.
- Pose = landmark SHAPE distance. Yaw from a generic 3D model was measured unreliable (a frontal photo read +132 degrees).
- `python calibrate.py` reprints all of the above from real photos and known-good/bad outputs. Re-run it after any
  change to the pool or scorer.

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

`facecard.py models` lists what the account can use (2026-09-20: 3.1 Pro `e6fa609c3fa255c0` pinned in
`facecard.json`, 3.8 Flash, 3.5 Flash-Lite). Run it if a run fails with an unknown-model error.

## Ground rules

- **Source photo -> `replicate`. Never redraw it from a text description.**
- **NEVER judge identity by eye.** Read and report the numbers, and show the compare sheets.
- **NEVER feed generated images back into the reference set,** and never add a mirrored photo to it.
- **Never change a threshold quietly.** Thresholds live in `facecard.json`; changing one needs the user's approval.
- Candidness is the goal for from-scratch scenes: asymmetrical posture, natural ground contact, mid-moment expressions.
- Attractiveness levers belong in the scene prompt (lighting, posture, fit, framing), never in the identity lock.
- Do not put "athletic/muscular/lean build" in any prompt that has the user's own body in the frame: it replaces the
  user's real physique with a generic one.
