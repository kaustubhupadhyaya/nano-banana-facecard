# FEEDBACK LOG: every output the user reviewed, and what each one taught

Written 2026-09-21 before the `outputs/` folder was cleared. Verdicts are the user's own words (paraphrase only where marked). Numbers are what the pipeline measured for that output: `gt_sim` = face similarity to the SOURCE face, `pool` = identity score against the user's reference photos, `size` = face width over the source's, `shift` = head movement in face widths, `dE` = face light distance to the source face, `ssim` = similarity outside the head. `-` = not measured by the pipeline version that made the output.

Evidence files (the named image, the compare sheet, `run.json`, `run.log`) are kept locally in `.cache/feedback/<run folder>/`, not in git (they show the user's face). Source photos: `.cache/super_favs/` (five), `.cache/pinterest_target.jpg`, and `D:\Downloads\AI me\` (five).

## 1. Source photos and every concern raised about them (the checklist a new output must clear)

| Source photo | Where it is | Concerns the user raised (a new output must have none of them) | What the user counted as good |
|---|---|---|---|
| kayak | `.cache/super_favs/google-1__IMG_5549.jpg` | three faces / ghost outlines from the reflections; attractive but not looking like the user; awkward tense mouth instead of the user's own calm reaction; face lighting off (dE 16.5) | calm closed-lip smile with soft eyes, lit like the photo (`060329` emotion, `150905` attempt 2 and 6) |
| rocky | `.cache/super_favs/google-1__IMG_4861_SnapseedCopy.jpg` | the round-2 heuristic output (`053504`) | `034849`, `061004`, `153829` (a face brighter than the dim photo is acceptable up to dE 9.9) |
| stained glass (with reflection) | `.cache/super_favs/google-4__IMG_5850_Original.jpg` | unnatural lighting; reflection not handled or mirroring a different reaction; a double chin (it is in the SOURCE, not generated) | face and reflection rendered in the same pass (`060631`); `151934` very promising |
| table tennis | `.cache/super_favs/google-2__IMG_3943.jpg` | wrong overlapping face; needs more attractive expression | the hard head angle nailed (`061432`) |
| IMG_0862 | `.cache/super_favs/google-4__IMG_0862.jpg` | none given per output (batch verdicts only) | - |
| Pinterest | `.cache/pinterest_target.jpg` | face overlap; two faces; head too big; hair only partly the user's; face position and expression not matching the reference; head cut-pasted, neck pasted, tilt off, lighting mismatched | `000411` best: face and neck lit like the photo, pose within 2 degrees, the reference's smile, the user's own hair, size right |
| night out | `D:\Downloads\AI me\night out.jpg` | returned as it is, three times; the better face (`002751` c1_head_raw) was thrown out by the gates | c1_head_raw: fuller curly hair, defined face, calm slight smile, clearly the user |
| nerd | `D:\Downloads\AI me\nerd.jpg` | before and after the same, twice | - |
| mountain | `D:\Downloads\AI me\mountain.jpg` | face replication worse than the source | - |
| beach | `D:\Downloads\AI me\beach.jpg` | no change at all, twice | - |
| car2 | `D:\Downloads\AI me\car2.jpg` | face size and lighting not proportional to the body and scene, twice | - |

## 2. Concerns that apply to any output (from all reviews)

- Face overlapping, ghost outline or a duplicate face (`032241`, `032923`, `054417`, `053307`).
- Face lighting unnatural, or the face and neck brighter than the photo and the body: the cut-and-paste look (`032650`, `060329`, `173847`, `004110`, `020055`).
- Head or face too big or out of proportion with the body (`064235`, car2).
- Head angle, tilt or position not matching the source or reference (round 1 in general, `165702`, `173847`).
- Expression awkward or tense (`064200`); expression not matching the reference (`165702`); a laugh or teeth the reference does not have (`054417`, `173847`).
- Hair not entirely the user's (`152548`).
- A reflection that is not the user or has a different reaction (`063313`).
- The output only looks like the user and the face is not replaced: a look-alike returned unchanged (nerd, beach, night out).
- Face replication worse than the source (mountain).
- Attractive but not the user (`053307`).
- Changing the scenery, background, clothes or physique (the very first message; the `gen` runs).
- A fold or double chin that the source does not have (the one the user reported was in the source).

**What the user counts as attractive** (from `060329`, `150905`, `000411` and the night-out `c1_head_raw`): calm confident eyes, a defined jawline, a relaxed closed-lip smile or a slight smile with soft eyes (on another man's photo, the reference's own expression at the same strength), full natural curly hair, skin lit like the neck and the scene, head and face in proportion with the body, one real photograph rather than a paste. Never tense, awkward, forced, smirking or caught mid-motion.

## 3. Every reviewed output

| Round | Source | Run folder | File | Verdict (the user) | gt_sim | pool | size | shift | dE | ssim |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | table tennis | `20260920_032241_replicate_google-2__IMG_3943` | `best.jpg` | wrong face overlapping done here | 0.01 | 0.595 | 1.101 | 0.038 | - | - |
| 1 | stained glass | `20260920_032650_replicate_google-4__IMG_5850_Original` | `best.jpg` | lighting unnatural, reflection not handled | 0.661 | 0.453 | 0.991 | 0.033 | - | - |
| 1 | Pinterest | `20260920_032923_replicate_pinterest_target` | `best.jpg` | face overlap looking unnatural | 0.16 | 0.575 | 0.935 | 0.142 | - | - |
| 1 | Pinterest | `20260920_033645_replicate_pinterest_target` | `best.jpg` | same, unnatural (the idea of editing a head and putting it in place is good; the execution goes wrong mostly in lighting, or a wrong assumption of the face angle) | 0.209 | 0.696 | 1.123 | 0.181 | - | - |
| 3 | Pinterest | `20260920_064235_replicate_pinterest_target` | `best.jpg` | head too big | 0.146 | 0.692 | 1.054 | 0.095 | 32.7 | 0.884 |
| 3 | Pinterest | `20260920_054417_replicate_pinterest_target` | `best.jpg` | head bad and also looks like 2 faces are overlapping | 0.159 | 0.526 | 0.904 | 0.015 | - | - |
| 3 | stained glass | `20260920_064633_replicate_google-4__IMG_5850_Original` | `c1_head_send.png` | you gave me a double chin I dont even have (this file is the crop SENT to Gemini, identical to the source: the fold is in the source photo) | - | - | - | - | - | - |
| 3 | kayak | `20260920_053307_replicate_google-1__IMG_5549` | `best.jpg` | has three faces (basically 2 reflections); nailed attractiveness but it is not looking like me | 0.353 | 0.227 | 0.991 | 0.02 | - | - |
| 3 | kayak | `20260920_064200_replicate_google-1__IMG_5549` | `best.jpg` | forgot attractiveness point, gave me an awkward facial reaction than what I even actually had | 0.619 | 0.573 | 1.033 | 0.004 | 7.0 | 0.996 |
| 3 | kayak | `20260920_060329_replicate_google-1__IMG_5549` | `best.jpg` | perfect face emotion but lighting is off | 0.686 | 0.642 | 0.995 | 0.022 | - | 0.996 |
| 3 | stained glass | `20260920_063313_replicate_google-4__IMG_5850_Original` | `c1_copy1_raw.jpg` | the mirror copy is perfect but its not mirroring me at all, both faces have different reaction | 0.96 | 0.535 | 1.038 | 0.007 | 2.6 | 0.989 |
| 3 | rocky | `20260920_053504_replicate_google-1__IMG_4861_SnapseedCop` | `best.jpg` | bad | 0.538 | 0.451 | 0.985 | 0.03 | - | - |
| 3 | stained glass | `20260920_060631_replicate_google-4__IMG_5850_Original` | `c1_head_raw.jpg` | perfect (face and reflection in one pass) | 0.494 | 0.436 | 0.995 | 0.66 | - | 0.982 |
| 3 | rocky | `20260920_034849_replicate_google-1__IMG_4861_SnapseedCop` | `best.jpg` | perfect | -0.008 | 0.501 | 1.058 | 0.029 | - | - |
| 3 | table tennis | `20260920_061432_replicate_google-2__IMG_3943` | `c1_head_raw.jpg` | perfectly nailed the weird head angle, only needs attractiveness improvement | - | - | - | - | - | - |
| 3 | rocky | `20260920_061004_replicate_google-1__IMG_4861_SnapseedCop` | `best.jpg` | perfect | 0.516 | 0.534 | 0.978 | 0.039 | - | 0.991 |
| 4 | kayak | `20260920_150905_replicate_google-1__IMG_5549` | `c2_head_raw.jpg` | this is good | 0.746 | 0.592 | 1.018 | 0.029 | 4.0 | 0.987 |
| 4 | kayak | `20260920_150905_replicate_google-1__IMG_5549` | `best.jpg` | perfect (the pipeline's pick, attempt 6; no preference between it and attempt 2) | 0.682 | 0.598 | 0.959 | 0.028 | 7.7 | 0.966 |
| 4 | stained glass | `20260920_151934_replicate_google-4__IMG_5850_Original` | `c1_head_raw.jpg` | this looks very promising | 0.641 | 0.447 | 0.987 | 0.026 | 2.1 | 0.972 |
| 4 | Pinterest | `20260920_152548_replicate_pinterest_target` | `best.jpg (named file missing, kept best.png)` | hair: only the front portion is mine, from the middle till behind including the sides looks like the reference model's still | 0.251 | 0.587 | 0.968 | 0.071 | 15.3 | 0.984 |
| 4 | rocky | `20260920_153829_replicate_google-1__IMG_4861_SnapseedCop` | `best.jpg` | perfect (the pipeline's pick, attempt 3; no preference between it and attempt 1) | 0.507 | 0.556 | 0.973 | 0.042 | 9.9 | 0.997 |
| 5 | Pinterest | `20260920_165702_replicate_pinterest_target` | `cand3.png` | face size, lighting, hair everything alright, but face position and expression isnt matching with the reference image; an improvement | 0.219 | 0.501 | 0.949 | 0.066 | 18.4 | 0.959 |
| 5 | Pinterest | `20260920_173847_replicate_pinterest_target` | `cand1.png` | expression match is closer, but the head tilt angle is off and throws off the whole picture, the neck-above part looks copy-pasted, lighting mismatched: roll it back | 0.203 | 0.509 | 0.897 | 0.069 | 32.4 | 0.957 |
| 5 | Pinterest | `20260920_173847_replicate_pinterest_target` | `cand6.png` | same verdict as cand1 of this run (rolled back) | 0.171 | 0.466 | 0.968 | 0.095 | 31.6 | 0.89 |
| 5 | Pinterest | `20260921_000411_replicate_pinterest_target` | `best.png` | perfect | 0.234 | 0.509 | 0.987 | 0.049 | 14.2 | 0.948 |
| 6 | night out | `20260921_002751_replicate_night out` | `c1_head_raw.jpg` | we already have seen better facial attractiveness and identity matchness (raw return of foreign-mode attempt 1, rejected by the gates) | 0.828 | 0.794 | 1.164 | 0.263 | 5.4 | 0.768 |
| 6 | nerd | `20260921_003247_replicate_nerd` | `best.png` | before and after are same | 0.993 | 0.805 | 1.0 | 0.007 | 1.6 | 0.993 |
| 6 | mountain | `20260921_003409_replicate_mountain` | `best.png` | face replication even worse than the source | 0.727 | 0.436 | 1.007 | 0.006 | 1.3 | 0.997 |
| 6 | beach | `20260921_003606_replicate_beach` | `best.png` | no changes made at all | 0.938 | 0.637 | 1.028 | 0.008 | 2.3 | 0.991 |
| 6 | car2 | `20260921_004110_replicate_car2` | `best.jpg` | face size and lighting not proportional to the rest of the body and scene | 0.751 | 0.692 | 0.969 | 0.021 | 10.2 | 0.993 |
| 6 | night out | `20260921_004741_replicate_night out` | `best.png` | stays same again (own mode, --force --expression same) | 0.976 | 0.846 | 0.994 | 0.006 | 1.3 | 0.995 |
| 7 | night out | `20260921_015113_replicate_night out` | `best.png` | as it is again (default rerun) | 0.947 | 0.833 | 0.974 | 0.068 | 2.2 | 0.973 |
| 7 | nerd | `20260921_015354_replicate_nerd` | `best.png` | as it is again (default rerun) | 0.928 | 0.709 | 1.0 | 0.015 | 0.4 | 0.987 |
| 7 | beach | `20260921_015829_replicate_beach` | `best.png` | as it is to the source again (default rerun) | 0.99 | 0.672 | 0.986 | 0.012 | 1.4 | 0.996 |
| 7 | car2 | `20260921_020055_replicate_car2` | `best.jpg` | face lighting and size bad (default rerun) | 0.758 | 0.74 | 1.04 | 0.039 | 10.5 | 0.997 |
| 7 | mountain | `20260921_015610_replicate_mountain` | `best.png` | (no verdict given on the default rerun) | 0.779 | 0.469 | 1.007 | 0.018 | 2.2 | 0.998 |

Rounds: 1 first `replicate` prototype; 3 the review of 14 outputs after the round-2 heuristics were removed; 4 the five-photo benchmark; 5 Pinterest position, expression and lighting; 6 the five-scene test in foreign mode; 7 the same five scenes with the default pipeline and `--force`.

## 4. Batches with indirect feedback (the user asked for improvements on the whole batch)

| Batch | What the user said | Runs (evidence: best image + `run.json`) |
|---|---|---|
| Round 1 (first prototype) | the idea of editing a head crop and putting it in place is good; the execution goes wrong mostly in lighting, or a wrong assumption of the face angle when generating a headshot only | `20260920_031638`, `20260920_032029`, `20260920_032110`, `20260920_032455` |
| Round 2 (heuristic post-processing: relight, grain, blur, landmark warp, mask cut-out) | getting further down the road, images are getting worse; non-AI processing is making it all worse | `20260920_034357`, `20260920_034643`, `20260920_035101`, `20260920_035302`, `20260920_035600`, `20260920_050330`, `20260920_050831`, `20260920_053643`, `20260920_054240`, `20260920_054329` |
| No verdict given | - | `20260920_061803`, `20260920_062241`, `20260920_153036` |
| `gen` runs (from-scratch generation plus FaceFusion restore), 2026-09-17..19, 38 folders | the very first message: the trial generations are screwing up the face and, where it was not needed, changing the scenery, background, clothes; the model cannot keep the physique and the face structure | `20260917_054613` to `20260919_224409` (one image and `run.json` each) |
| Default-run authentication failure, 2026-09-21 01:47-01:49 | no images were made | five folders `20260921_0147..0149`: deleted, nothing to keep |

## 5. The model that exists today, and what it still gets wrong

Code state: commit `20a62ef` (references named as identity only for another man's photo, the reference's own expression, a light limit of 20, size floor 0.94). Open problems from the reviews above: a better face is never rewarded and an unchanged look-alike is preferred (selection ends in `gt_sim`); a good face with wrong framing is rejected; the own-photo light and size gates miss a face brighter than its neck (car2); the sparkle watermark leaks when a return needed re-alignment. The plan that addresses them is in `SKILL.md` (Round 7) once applied.

## 6. Round 7 verdict matrix (2026-09-21): the reward-better-face pipeline on the ten feedback photos

a = attractiveness, i = identity; P = improved, N = degraded, O = no change (the user's own scale). Code: commit of round 7 (unchanged gate, neck gap, whole-face pairwise, rescue). Evidence in `.cache/feedback/<run>/`, the two ideals also in `.cache/feedback/ideal/`.

| # | File | What it actually is | a | i | Complete picture? | Measured | What it teaches |
|---|---|---|---|---|---|---|---|
| 1 | night out `c2_head_raw.jpg` (run 042258) | raw return of attempt 2, own mode | P | P | no, headshot; rejected: size 0.935, moved 0.134, judge angle changed; 2 rescues failed (one unchanged, one copied the reference's pose) | pool identity 0.784 | the best face was found on attempt 2 and never made it into the photo |
| 2 | nerd `best.png` (run 042928, attempt 1) | pasted composite | N | P | yes | face L 52.9 vs source 43.7; neck L 43.8 vs source 16.9 (+27); yaw 9 degrees off; light dE 8.9 and neck gap -18.5 passed | identity is there; the head-and-neck lighting degrades attractiveness and no gate saw it |
| 3 | beach `c1_head_raw.jpg` (run 043251) | raw return of attempt 1, re-framed by Gemini (scale 0.74, shift 0.26). CORRECTION (checked 2026-09-21 evening): this return is Gemini's re-render of the kayak reference photo it was sent (glasses, life vest, reeds, sunset water), not an edit of the beach crop; see `research/round8_attempt.md` | P | P | no, headshot; alignment failed so it was never measured or kept | pool identity 0.557 (measured afterwards) | 'wins in all: attraction, identity, pose'; discarded before anyone looked at the face |
| 4 | car2 `c1_head_raw.jpg` (run 043841) | raw return of attempt 1, aligned fine | P | P | no; the composite was rejected by the AI 'not better than the source' comparison | pool identity 0.561, size 1.0, neck gap 2.1 | the general AI comparison was wrong against the user's eye; it must not reject |
| 5 | mountain `c1_head_send.png` (run 044504) | the crop SENT to Gemini, byte-identical to the source (the run died on the quota) | O | P | - | - | the user rated the source crop; 'no change' is exactly right |
| 6 / 9 | Pinterest `best.jpg` (run 064221, attempt 4) | composite, foreign mode, a RESCUE of attempt 3 | P | P | yes: 'more than perfect', the ideal | identity 0.506, size 0.981, shift 0.115, light dE 5.7, neck gap 4.9, pose within 2.4 degrees, expression same | face first, then the same face re-rendered in the right frame |
| 7 | table tennis `c1_head_raw.jpg` (run 070955) | raw return of attempt 1, re-framed (scale 1.31, shift 0.36), never measured | N | P | no, headshot | pool identity 0.595 vs source crop 0.488; classified as another man's photo (109 px face), hair and expression replaced | classification by the number misfires on a tiny face |
| 8 | stained glass `best.jpg` (run 070221, attempt 4) | composite, own mode, normal path | P | P | yes, perfect | identity 0.488, gt_sim 0.762, size 1.009, light dE 1.0 | the own path with the attractiveness policy works on a real photo |
| 9 | `D:\Downloads\AI me\beach.jpg` | gen output `20260917_144731...` v1_0.jpg (md5 match): from scratch, raw, no restore | P | P | yes, ideal | not a replicate run | 9 whole references, identity-lock text, scene text with pose, expression, light direction and lens |

No verdict was given on kayak (064910), rocky (065438), mountain `best.png` (063352), or on the candidates rejected only for size (beach 1.059, car2 1.033, rocky 0.925-0.939).

**How the two ideals were made.** Pinterest 064221 attempt 4: attempt 3 rendered a good face at size 0.923; its raw return went back as one more reference with 'render that same face, keep the head at the position, size, turn and tilt of the last image'. beach.jpg: one `gen` call on 2026-09-17 with 9 whole reference photos (all angles), the identity-lock text and a scene text that states the pose, the expression, the light direction and the lens; nothing cropped, pasted or measured.

**Preserve:** the foreign path as it made 064221; the own path as it made 070221; whole-crop paste with zero change outside; the unchanged gate; pairwise in both orders; the identity floor as a floor only.

**Improve (round 8):** rescue from alignment failures too; the rescue reference is a head crop of the raw face; the AI vs-source comparison ranks but does not reject; two-sided neck lightness checks; references sent the way beach.jpg was made; gray-zone classification asked of the AI.


## 7. The hard-rule batch and the user's best versions (2026-09-23)

The eleven pictures of the hard-rule batch (default pipeline, 2026-09-21 21:33 to 2026-09-22 03:01), the user's verdicts verbatim:

| # | Photo | Picture | Verdict (the user) | Measured: identity (source), similarity to source, size, light dE |
|---|---|---|---|---|
| 1 | night out | `20260921_213349_replicate_night out/best.jpg` | major improvement a,i-p | 0.84 (0.846), 0.845, 0.994, 2.6 |
| 2 | nerd | `20260921_215338_replicate_nerd/not_passing_closest.jpg` | nochanges | 0.754 (0.803), 0.945, 1.0, 0.9 |
| 3 | beach | `20260921_220113_replicate_beach/best.jpg` | improvement, but it was already perfect and was being used as reference hence wasnt required to change again | 0.508 (0.677), 0.798, 1.014, 1.3 |
| 4 | car2 | `20260921_221426_replicate_car2/best.jpg` | not the same as the reference image at all, do you even have the correct reference image? a,i-p but not matching reference | 0.593 (0.66), 0.75, 1.013, 1.0; the source's broad laugh became a closed smile |
| 5 | mountain | `20260921_222419_replicate_mountain/best.jpg` | no improvement a,i -n | 0.485 (0.626), 0.837, 1.007, 1.2 |
| 6 | Pinterest | `20260921_223507_replicate_pinterest_target/not_passing_closest.jpg` | worst version till now. worst. | 0.562, 0.119, 0.994, 25.8 |
| 7 | Pinterest | `20260922_023359_replicate_pinterest_target/not_passing_closest.jpg` | worst | 0.64, 0.135, 0.974, 33.7 |
| 8 | kayak | `20260922_024138_replicate_google-1__IMG_5549/best.jpg` | ok, slight improvement a,i -p | 0.597 (0.632), 0.758, 1.032, 3.0 |
| 9 | rocky | `20260922_024632_replicate_google-1__IMG_4861_SnapseedCop/best.jpg` | no major improvements was already good, a-p, i-n | 0.494 (0.665), 0.554, 0.993, 1.0 |
| 10 | stained glass | `20260922_025116_replicate_google-4__IMG_5850_Original/best.jpg` | a-o, i-n | 0.223 (0.548), 0.228, 0.991, 3.3 |
| 11 | table tennis | `20260922_025509_replicate_google-2__IMG_3943/not_passing_closest.jpg` | worst version till now | 0.548, -0.071, 1.194, 5.4 |

**The user's best versions** (`D:\Downloads\AI me`, "this has best versions of all photos"), matched to their runs by pixel content (identical up to JPEG re-encoding):

| File | Run, attempt | How it was made | Identity (source) | Size | Light dE | Expression |
|---|---|---|---|---|---|---|
| `beach.jpg` | gen `20260917_144731` v1_0.jpg | from scratch: 9 whole references, identity-lock text, scene text with pose, expression, light, lens | 0.675 | - | - | stated in the scene text |
| `nightout.jpg` | `20260921_213349` night out, attempt 2 | hard rule: placement of attempt 1's face (0.884) | 0.84 (0.846) | 0.994 | 2.6 | the source's, kept |
| `kayak.jpg` | `20260922_024138` kayak, attempt 1 | hard rule, fresh attempt | 0.597 (0.632) | 1.032 | 3.0 | subtle smile made calm |
| `mt1.jpg` | `20260922_024632` rocky, attempt 3 | hard rule: placement of attempt 2's face, which re-lit it (18.7 to 1.0) | 0.494 (0.665) | 0.993 | 1.0 | neutral made a slight smile |
| `mirror.jpg` | `20260921_070221` stained glass, attempt 4 | round 7, fresh attempt | 0.488 (0.548) | 1.009 | 1.0 | neutral made calm |
| `mt2.jpg` | `20260921_064221` Pinterest, attempt 4 | round 7 rescue of attempt 3's well-lit face (dE 8.0, size 0.923) | 0.506 | 0.981 | 5.7 | the reference's, kept |
| `cand1.png` | `20260921_171345` Pinterest, attempt 1 | round 8 fresh attempt, REJECTED by the gates (size 0.91, judge: expression differs) | 0.55 | 0.91 | 13.8 | differs from the reference |
| `car.png` | `20260921_043841` car2, attempt 1 | round 7 fresh attempt, REJECTED only by the AI 'not better than the source' veto (removed by the hard rule) | 0.536 (0.66) | 1.0 | 1.8 | the laugh, kept |

No best version exists for nerd, mountain (the original), table tennis or IMG_0862. The user deleted the original `car2.jpg`, `nerd.jpg`, `mountain.jpg` and `night out.jpg` from that folder.

**What the best versions do right, measured:** the face is lit like the photo (light dE 1.0-5.7 in six, 13.8 in one; the two pictures the user called the worst measured 25.8 and 33.7); the head keeps its size and place (0.91-1.03, moved at most 0.115); the face is really re-rendered (similarity to the source 0.55-0.85 on his own photos; 'no changes' measured 0.945); it keeps looking like him (identity drop at most 0.171; the stained-glass picture rated identity-down dropped 0.325); a laugh in the source stays a laugh (`car.png`; the car2 picture that closed the mouth was 'not the same'). Three of them came from placing an already rendered face into the source's frame (night out, rocky, the Pinterest ideal); on his own photos a placement also re-lit the face, on another man's photo the three placements of a too-bright face stayed too bright.

**Changes made from this (uncommitted, 2026-09-23; checkpoint of the state that made the best versions at `.cache/patches/rule_state_of_best_versions_2026-09-23.patch`):** classification own / another man's on a head crop of the source (table tennis becomes his own photo, no other photo changes class); a face that is the source returned unchanged is never placed; on another man's photo a face that failed the light or neck check is not placed; a laugh or broad open smile in his own photo is kept (the source's own expression, judge-checked); his own photo may not lose more than 0.20 of identity against the source (provisional; catches the stained-glass 0.325 and kayak 'not me' 0.405, keeps every best version; mountain's 0.141 is not caught); the closest not-passing picture prefers one lit like the photo; a source that is one of the best versions (same file content) is returned unchanged unless `--force`. Considered and not made: lowering the head-size floor for another man's photo to 0.90 (the ideal's first render at 0.923 would have passed directly and the rescue that made the ideal might never have run).

**Live results of these changes (default pipeline, no flags, 2026-09-23 03:22-04:06; none reviewed by the user yet):**

| Photo | Run | Result | Identity (source) | Light dE | Size |
|---|---|---|---|---|---|
| beach | `20260923_032206_replicate_beach` | returned unchanged: it is a best version (no Gemini call) | - | - | - |
| Pinterest, old references | `20260923_032208_replicate_pinterest_target` | 0 of 6; five renders too bright (dE 26-35), the one lit right kept mostly the other man's face (identity 0.243) | - | - | - |
| Pinterest, references lit like the photo | `20260923_040017_replicate_pinterest_target` | 0 of 6, but all six lit like the photo (dE 5.3-12.6); closest = attempt 1, which fails only size | 0.542 | 8.2 | 1.071 |
| table tennis (now his own photo) | `20260923_032918_replicate_google-2__IMG_3943` | 0 of 6; every head measured 1.15-1.33 (attempt 1 looks the same size by eye: the detector boxes a blurry 109 px face smaller than a sharp one) | 0.524 | 3.4 | 1.33 |
| stained glass | `20260923_033637_replicate_google-4__IMG_5850_Original` | best = attempt 6 | 0.492 (0.548) | 12.1 | 0.965 |
| kayak | `20260923_034524_replicate_google-1__IMG_5549` | best = attempt 3, a placement of the already passing attempt 2 (identity 0.634) | 0.504 (0.632) | 11.3 | 1.009 |
| rocky | `20260923_035023_replicate_google-1__IMG_4861_SnapseedCop` | best = attempt 3; hair turned reddish-brown and the head turned toward the camera, which no gate caught; 3 attempts rejected by the identity-drop gate (0.225-0.245) | 0.474 (0.665) | 13.5 | 1.02 |

What this shows: the references' exposure is the cause of the too-bright faces on another man's photo (the same photo, the same code, only the references changed: five of six too bright against none of six). Still open: head size on Pinterest (1.07-1.17 with the dimmer references), table tennis size measured on a blurry face, a placement of an attempt that had already passed (kayak), hair colour and head-angle changes on rocky, and the source photo being sent as its own reference when the duplicate check misses it (table tennis, rocky; every rocky picture the user liked was made that way, so it is not changed).

## 8. Any angle, any distance (2026-09-23)

The user's verdict on the five pictures of the think-again round (Pinterest with dimmer references `20260923_040017`, stained glass `033637`, kayak `034524`, rocky `035023`, table tennis `032918`): **all are worse looking than ever.** The code went back to the state that made the best versions (checkpoint `.cache/patches/replicate_rule_state_2026-09-23.py`), keeping only: never place an unchanged face, keep a laugh, a best version returned unchanged.

Measured before the next change (read-only): head size by source face width over every saved run: faces 142-227 px have medians 0.98-1.03; the far face (table tennis, 109 px) 1.19, 4% inside the gate; blurred to the source's sharpness it is still 1.14-1.27, the hair+face silhouette 1.09-1.17 taller, so the model really draws the far head bigger; those faces are 7-17x sharper than the photo (best versions 0.17-4.6). The landmarks are unreliable on the looking-down and close photos (rocky, table tennis, IMG_0862), so the head-shape reference choice was blind there. The reference pool has no photo of him looking down or from above except rocky and table tennis themselves (IMG_6875 and IMG_6862 are level; their landmark pitch readings are wrong); IMG_6923's reference crop is a headless torso.

The plan (approved): references chosen by the pose the AI reads (cached per reference), the studio look preferred; a missing angle rendered from the studio photos and kept only if identity >= 0.60 and the read pose is within 15 degrees; a far face (< 130 px) sent with a wider crop (upscale <= 1.5x) and a prompt that keeps it small and soft; a sharpness gate (<= 6x the source). First test, only on the three originals the user chose: `C:\Users\Admin\Downloads\super favs\google-2__IMG_3943.HEIC`, `google-4__IMG_0862.HEIC`, `google-1__IMG_4861_SnapseedCopy.JPG` (the user decided not to add reference photos).

Results: table tennis `20260923_160011` and IMG_0862 `161146`, 0 of 6 each, both reviewed a -2 i 0, "unreal and monsterish" (Reviews below). Rocky `183350` passed on attempt 6 (identity 0.633, size 0.986, dE 3.1, no judge flag; waiting for review). The angle library is complete: all 21 poses (turn -90..90 x level / looking down / looking up) have a kept render in `.cache/synthetic_refs`.

## 9. Why they looked monsterish, and the fix (2026-09-23 evening)

The user asked why the two pictures look unreal and monsterish; the diagnosis, confirmed by the user as "perfect": **the head Gemini draws does not fit the real head and body it is pasted onto.**
- IMG_0862 (close face, camera above): the crop is capped at 1.8x the face, so the square cut his hair off. Asked for full curly hair, Gemini zoomed out and drew the whole head smaller; the ring no longer matched (ECC 0.00-0.73 in 4 of 6), and the face-box merge (added 2026-09-21) stretched the return 1.35x and slid it 30 percent onto his face: a second hairline, a second ear, a smeared collar, a head turned unlike its neck. None of the 8 face-box merges in all saved runs ever passed; every best version came from a return whose ring matched (ECC >= 0.90, scale <= 1.048, shift <= 0.092).
- Table tennis: the framing held, but the head was drawn 1.16-1.43x bigger than the body.

Changes (uncommitted; patch `.cache/patches/reframe_fix_2026-09-23_UNCOMMITTED.patch`, rollback `.cache/patches/replicate_before_reframe_fix_2026-09-23.py`):
- A re-framed return is refused, not merged; the next attempt asks for the exact framing (the face-box merge is removed). Gate change: the ring thresholds are unchanged (ECC >= 0.80, scale within 0.20, shift <= 0.30); what changed is that a return failing them no longer becomes a picture.
- A face that is not far gets its whole head, hair included, into the crop: the AI marks the head on a wide look around the face (text call, no image credits; 150 s limit per call), and a crop that cuts it grows until the head sits 8 percent inside every edge. Checked on six photos: the AI box was right on all six and repeatable (two readings within about 10 px); only IMG_0862's crop changes (1058 -> 1736 px); rocky, kayak, mirror, Pinterest and table tennis keep exactly the crop they had.

Live, IMG_0862 `20260923_201520`, default pipeline, 0 of 6 passed: no attempt was re-framed (ECC 0.93-1.00, scale 1.000), the judge flagged no double image and no seam, the pictures are one coherent head. What failed instead: the head drawn 5-17 percent bigger (all six), turned toward the camera and moved (4 of 6; references were two renders at turn +15 chin +15 and two frontal studio photos, which win on the 15-degree studio bonus), the face softer than the photo (sharpness 0.21-0.30 of the source, the cost of drawing the face smaller in the wider crop).

## 10. Think again: rocky, and a check that asks the user's question (2026-09-24)

Verdicts (Reviews below): rocky `183350` attempt 6, which passed every gate: "absolutely horrible"; a and i are irrelevant, because it is the same defect the diagnosis named. IMG_0862 `201520` attempt 1, the whole head redrawn facing the camera and rejected by four gates: "perfect", kept as the best version `D:\Downloads\AI me\google-4__IMG_0862_20260923_201520.jpg`. Attempt 2 (pose kept): "meh", a +2 i -2.

Autopsy:
- The reframe fix (section 9) never touched rocky. Its return kept the framing and its crop already held the head, and the rocky picture was made before the fix.
- In rocky, Gemini drew the face more upright and cleaner under the photo's own hair and skull, which is seen from above and looking down. The detector gives it the same face box as the source (width x1.014, height x1.006, within 3 px), so no size or position gate can see it.
- The references were four renders labelled chin +30. By eye they are almost level, and the AI read the source as chin +22 although he is looking down about twice that.
- The rocky pictures the user liked (`mt1`, P-04, P-05) all had rocky itself among their references. The source-vs-output judge said "same head angle" on all six rocky attempts.

The test (text calls only, no image credits; results in `.cache/patches/coherence_test_2026-09-24_results.json`):
- **What it asked:** Gemini looked at the picture alone, around the head, 1.5x the crop, twice per picture: "one natural head (face, hair, ears, neck turned the same way)? head in proportion to the body?"
- **Result:** it passed all 8 good pictures (the perfect IMG_0862 and seven best versions). But it also passed 5 of the 6 horrible or worst ones: rocky, table tennis `160011` and `025509`, Pinterest `223507` and `023359`. It caught only the IMG_0862 two-heads picture, through its hair patches.
- **So it was not used:**
  - it is not a gate;
  - the relaxation the user approved (pose, size, position and collar checks as warnings on his own photos when the check passes) was not applied, because it depended on a working check;
  - the "never show an incoherent picture" rule was not applied either.
- **Kept from this round:**
  - a 150 s limit on every Gemini text call, because a stalled answer stream otherwise waits forever;
  - `tools/record_review.py` now splits reviews on ';' only outside a quoted note.

```
DO NOT RETRY:
- face-box merge of a re-framed return: fused two heads (IMG_0862 161146); removed
- more crop geometry for rocky: its crop already held the head
- the AI's absolute pose numbers as the way to match references: rocky read chin +22 (really about twice), a near-level render read chin +30
- the source-vs-output judge question "same head angle": true on the horrible rocky picture
- asking Gemini whether the picture alone shows one natural head: passes 5 of 6 pictures the user called horrible or worst
- dimmer references, head-crop classification, identity-drop gate (the think-again round, "all worse")
```

## 11. The v1..v6 loop, the checklist, and route G (2026-09-26)

**The task (the user):**
- Three photos:
  - Pinterest pin 783485666539775315 (`.cache/pin_783485666539775315.jpg`: a paparazzi photo of a public figure beside a green scrambler);
  - table tennis `google-2__IMG_3943.HEIC`;
  - `instagram_DWrFDrIiWW8.jpg`.
- Make successive versions, each better, judged by my own eye, in a `/loop` with `/think-again`.
- Mid-loop the user turned their flagged defects into `BEST_CHECKLIST.md`:
  - 27 items, checked by eye with `tools/best_check.py`;
  - one fail, or an unverifiable item, means NOT BEST.
- Then the user supplied the prompt structure that had worked for them. It became **route G** (`facecard.py gen --goal`).

**Route G:**
- References by role:
  - 4 FACE references, chosen by pose;
  - BODY = `IMG_6923 Copy.JPG`;
  - SHOULDER AND ARM = `IMG_0440_Original.jpg`;
  - plus the original photo when it is his own.
- FACE and BUILD text from `subject_profiles.me`.
- The goal written as POSE / WARDROBE / SCENE / LIGHT / CAMERA with scene-prompt-writer.
- The goal of another man is never sent, so there is no leak and no public-figure refusal.

**Decisions (the user, 2026-09-26):**
- Sunglasses goals: identity is verified from the visible features.
- Item 26 for another man's photo: the scene and clothes as the goal, the physique his own.
- Public-figure photos: other tools, never a bypass.
- Kaggle first for any GPU route (Colab is excluded by its FAQ).
- Personal-use licences are fine.

| Photo | v1 | v2 | v3 | v4 (route G) | v5 | fix queued for v6 (02:32) |
|---|---|---|---|---|---|---|
| Pin | replicate: Gemini refused 5 of 6 (public figure); a lighter 1.13x head | gen from text: natural, but lettering garbled, wrong bike | gen, corrected scene: SCRAMBLER lettering right, composition close; checklist NOT BEST (12, 21, 26) | 25/27: 21 (aviators), 26 (twin-exhaust bike, utility SUV) | 26/27 (21 passes by the visible-feature rule): 26 (scene mirrored, other bike make, helmet in the other hand) | named Ducati Scrambler and Range Rover (builder, verbatim), orientation, the hands |
| Instagram | replicate passed (face-only edit) | replicate + source as reference: hardly different | not run (old route stopped) | **26/27** (`v3_0`): 26, the STUDDS helmet lettering garbled | worse: pout copied, tense brows, lettering still garbled | the word STUDDS named, lips at rest, his hair within the photo's outline |
| Table tennis | 0/6: curly mop, 1.24-1.36x, lifted chin, orange light | source as reference: short hair and bowed pose kept, 1.06-1.29x | replicate v3: one re-framed return refused, then the quota ran out | the original not sent (auto own-detection failed on the 108 px face): new composition, 26 and 21 fail | the original sent: scene, table, mural, pose all match; 25/27: 6 and 27 (fuller curls and a longer beard make the head silhouette 1.25x) | own photos: hair and beard within the photo's outline, volume and length (code) |

**The user's review of the three closest pictures (2026-09-26, late):**
- **Instagram v4 `v3_0`:** also fails because the face is slightly smaller than his real face. Item 6 is now two-sided.
- **Pin v5 `v4_0`:** the failure reasons were confirmed. It also fails the new item 29: the camera distance must match the goal. It was shot closer, with the bike angled instead of the pin's flat long-lens side-on view.
- **Table tennis v5 `v3_0`:** "impressive progress". My "head too big" was a misjudgment: the curls and beard make his head the right size.
  - The real failure is a bigger beard and moustache than his references have.
  - New item 28: face, hair, beard and moustache always come from the FACE references, never from the goal's face, even when the goal is his own photo.
  - The own-photo "keep the photo's hair and beard" rule I had added was replaced by this.
  - The FACE text now takes hair, beard and moustache from the references, and the original photo is labelled as scene only.

**More from the user the same night:**
- **Table tennis v5 `v3_0`:** the body posture and action were not kept. The goal leans over the table corner with both forearms raised and the paddle up; v3_0 stands upright with the paddle low. The cause was my own POSE transcription.
  - New item 30: posture and action as the goal.
  - `tabletennis_v6_sections.txt` transcribes the arms, hands, lean and feet again.
- **Asked whether face posture and alignment are covered:** only partly (item 12 = tilt; 14 only for another man's photo). Items 12 and 14 now cover the full head pose (turn, tilt, roll, gaze) and face position against the goal for every photo.
- **Re-scored:**
  - table tennis v5: fails 12, 14, 28, 30;
  - pin v5: fails 26, 29, 30;
  - Instagram v4: fails 6, 26.

**The user, 2026-09-27 (after v6):**
- **Instagram:** a huge success. v4 `v3_0` is kept as the best version by the user's decision, although the strict checklist still fails 6 and 26. The user had also copied it, and pin v5 `v4_0`, into `D:/Downloads/AI me` by hand.
- **Table tennis v6:** "a horrendous failure": the hair is not his, the face is blurrier than the source, and the pose again doesn't match.
  - Pose uniqueness is hard to put into words, so such goals get their own plan: an extra edit route that keeps his real body and pose (replicate, whole head from the references, his own photo no longer a reference).
  - Route G renders are about 1 MP (Gemini's native size), so a far face can only come out blurrier than a 12 MP original.
- **Pin:** much closer on body and head. The camera distance is the one compromise the user will not accept; the rest are acceptable.
- **Instead of a 3x3 grid:** Gemini's own detection format. `tools/goal_layout.py` reads the goal's boxes (normalized 0-1000) for his body, head and main objects.
  - Route G writes them into the prompt as a LAYOUT section.
  - The same tool reads a render's boxes, so framing and distance become numbers. Pin v6 `v2_0`: body height x0.91, head lower (from 16% of the frame instead of 4%).
- **Asked whether 30 items overfit:** I answered that it is not overfitting but a flat gate with equal weights and overlaps, and proposed two tiers. **The user chose to keep all 30 strict.**

**The user, 2026-09-27 (table tennis v6 `v4_0`):** "even though blurring, still face perfectly me": a perfect face implementation.
- The only failure is the body: item 30, the paddle raised to chest where the goal holds both hands low at waist height.
- My item 28 fail (short hair) was wrong, the user said at first, and the v7 curls line was reverted.
- Minutes later the user corrected it: "hair not from references" IS valid. Item 28 fail restored, curls line restored for v7.
- Lesson: on a far face, blur is acceptable when the identity is right.

**His Honda CB350 as the pin's motorcycle (the user asked, 2026-09-27):** found by eye on contact sheets of the Favorites (274 photos) and the shots around each hit.
- The second-brain vault holds no bike photo (Drive = text).
- Best reference, `.cache/props/cb350_side_IMG_7237.jpg`, from `_staging\google-2\...\Photos from 2024\IMG_7237.HEIC`: graduation day, the whole bike side-on facing picture-right like the pin's, his helmet visor down (no second face).
- Others:
  - `IMG_7234` / `IMG_7235`: the same side view, face visible;
  - `google-2__IMG_3510`: front three-quarter, green hoodie;
  - `google-1__IMG_5380`: from above, the Instagram-like set;
  - `google-2__IMG_4468`: sitting side-on, black jacket;
  - `google-3__20240706_073045_Original`: parked under a tree, far.
- Route G takes it as a labelled prop: `gen --prop PATH::LABEL` puts "Image 7 is HIS OWN MOTORCYCLE..." after the face, body and arm references.
- Pin v7cb = pin v7 with only the motorcycle sentence changed. It runs next to the Ducati pin v7, so the bike swap is judged on its own.
- On pin v7cb, item 26 reads "scene and clothes as the goal, the motorcycle his own CB350" (the user's request).
- The first search only covered the Favorites. The user asked why no photo showed the bike alone: a YOLO scan of every 2020+ Takeout photo (13,354 after de-duplication, screenshots skipped) found them. From 2023: `IMG_4123`/`4124`/`4125` (front three-quarter against a wall), `IMG_5014(1)` (rear three-quarter), `IMG_4564` (night), `IMG_5085` (side-on, far). All copied to `Downloads\CB350 bike photos\bike alone`.
  - The 2024 part added the best pin reference: `IMG_5857`/`IMG_5856` (google-2, 2024), a full side view in daylight, the bike alone, facing picture-right like the pin's.
    Saved as `.cache/props/cb350_side_alone_IMG_5857.jpg`, the prop for the next pin version.
  - Also: `IMG_5335` (side, dusk), `IMG_7603` (side, night), `IMG_5162`/`IMG_6141`/`IMG_6142` (front three-quarter), `IMG_6144` (rear), `IMG_3684` (delivery garland).
  - The plate KA 05 LX 1252 confirms it is his bike.
  - Scan finished (13,401 lines, nothing unreadable). The 2026 part added:
    - `IMG_5355`/`5356`/`5357` (google-1): side view in the Instagram-goal garage, facing picture-right, from slightly above;
    - `IMG_6540`/`6541`: side view beside a red SUV;
    - `IMG_5933`: rear three-quarter.
  - 2020-2022 held only other bikes. 24 photos in the Downloads folder in all.
  - Scan tools (scratchpad, not the repo): YOLO11n in `D:\VisionModels\yolo\.venv`; COCO motorcycle box at least 5% of the frame, no person covering it.

**v7 batch (2026-09-27 02:32), layout ratios from `goal_layout.py --compare`:**

| Photo | Best render | Result |
|---|---|---|
| Table tennis v7 | `20260927_024244.../v3_0` | Posture now matches (30). Person x1.06 (29 borderline). Head box x1.24 from hair volume. Beard to check against the references (28). The best table-tennis render so far. |
| Pin v7 (Ducati) | `v1_0` | Still framed too wide (29). The bike is reversed in 3 of 4. |
| Pin v7cb (his CB350) | `v4_0` | The bike is right in all 4. Person x0.83 (29 fails). |
| Instagram v6 | `v1_0` | Head tilted to picture-left (12). Not better than the kept v4 `v3_0`. |
| Table-tennis edit route | closest | Head turned toward the camera (12), x1.28 (6), reads pasted (4). |

- Boxes as text did not hold the pin's camera distance in three versions.
- Pin v8 adds one thing: `gen --layout-image`, which sends the goal's boxes as a flat coloured sketch labelled "LAYOUT SKETCH, not a photograph".
- **Pin v8 result:** the bike faces the right way in 4 of 4, and `v1_0` is the tightest pin framing yet (person x0.90), but the head is still low.
- `tools/frame_to_goal.py` crops a render to the goal's frame using the measured boxes. For a long-lens goal that equals moving the camera closer; it draws nothing.
  - `v1_0_framed.jpg`: framing close to the goal by eye. It still fails 12 (head bowed more steeply than the goal's).
- Measurement noise: Gemini's person box read x0.78 on that crop, which should read about x1.0. The layout numbers are ±10-15%: guides, not a gate.
- **Pin v9** (`20260927_032837...`): the prop is the rider-free side view `IMG_5857`, plus a lighter head bow toward picture-left. The quota ran out after 3 renders.
  - `v1_0`: a different man (ArcFace 0.06).
  - `v2_0`: the closest pin yet: him, person x0.94, head bowed toward picture-left, his bike. It fails 26: the SUV and hatchback are on swapped sides.
  - `v3_0`: the sketch's coloured rectangles were drawn into the photo. This is the first time seen, 1 of 7 sketch renders.
  - Next: name that artifact (now observed), and place the SUV and hatchback sides in the sketch or LAYOUT.

**What the loop taught:**
- Nothing pasted means none of the paste defects (items 1-2, 4-8, 10-11): route G renders are one photograph.
- Sending his own photo anchors the composition (table tennis v4 → v5).
- Gemini garbles small lettering even when told to copy it; naming the word is the next try.
- Gemini falls back on popular bike models unless the model is named.
- The FACE text's hair and beard override the photo's own cut on his photos; the fix keeps the photo's outline.
- Output resolution is about 896x1200 (lower than his phone photos).

## 12. Why posture and position mistakes kept getting past me, and the fix (2026-09-27 afternoon)

**The user, 2026-09-27:**
- Table tennis v7 `v3_0` does not match the goal's posture. I had called it "posture fixed".
- The pin renders put him in a different position from the goal's subject.
- "These mistakes have been happening repeatedly... find out how you are letting them bypass."
- Build the checklist into the generation and the prompts, not only into a check afterwards.
- Also try sending the goal image, labelled as the goal, with the subject taken only from the references.

**What the measurement shows** (`tools/pose_compare.py`: YOLO11 pose keypoints, goal vs render, fixed limits):
- **Table tennis v7 `v3_0`:** feet 2.73x as far apart as the goal's (0.53 vs 0.19 torso lengths): a walking lunge where the goal stands with the feet together. The torso leans 11° more. The arms, hands and head were close.
- **Pin, every render so far, including the user-kept v5 `v4_0`:**
  - shoulders about 0.09-0.11 of the frame too low; head 0.08-0.15 off;
  - hands at waist height where the goal lifts both to chest height (right forearm held out level to picture-left with the helmet);
  - forearm directions 65-170° off.

**How they got past me (root causes):**
1. **The same eyes wrote the posture and checked it.** The table tennis v7 POSE text I wrote says "leaning forward from the waist" and "his back foot behind him with the heel lifted, mid-step". Gemini drew exactly that, and my by-eye check shared the same misreading, so the error could not show. The pin text said "hands at waist height"; the goal has them at chest height.
2. **Holistic, relative judging.** I compared each version with the previous one ("closer than v6") instead of with the goal, limb by limb. The legs were never checked at all.
3. **Signals I had were explained away.** `goal_layout.py` reported the pin v9 `v2_0` head shift 0.1 and person shift 0.089. No limit existed, and after one noisy reading I called all the numbers "guides, not a gate". That dropped the gate in practice, which is the pattern the never-narrow rule forbids.
4. **Checks came only after generation.** The prompt carried no measured posture, only my prose.

**The fix (built 2026-09-27):**
- **Measured, fixed gate:** `tools/pose_compare.py` (runs in `D:\VisionModels\yolo\.venv`).
  - Limits:

    | Measure | Limit | Items |
    |---|---|---|
    | body position | ≤ 0.04 | 14 |
    | head position | ≤ 0.04 | 12/14 |
    | size in the frame | 0.93-1.07 | 29 |
    | torso direction | ≤ 10° | 30 |
    | each limb direction | ≤ 15° | 12/30 |
    | each hand position | ≤ 0.06 | 30 |
    | feet apart | 0.75-1.33 of the goal's | 30 |
    | position along the main object | ≤ 0.08 | 14 |

  - `facecard.py gen --goal` runs it on every render. A fail is never picked as best.jpg.
  - The overlay (`<render>_pose.jpg`: the goal's skeleton on the render, plus a 50/50 blend) is what I look at, not the bare render.
- **Checklist compiled into the request:**
  - `--pose-points`: the goal's measured joints in Gemini's `[y, x]` 0-1000 format, plus plain facts computed by code: stance, knee angles, torso lean, hand heights.
  - `--pose-image`: the goal's skeleton in the layout sketch.
  - `--goal-as-image goal`: the goal image sent as GOAL IMAGE; its man is explicitly not the subject.
  - `--replace-subject`: the goal is the PHOTO TO EDIT, and its man is replaced by him from the references, so posture and position come from its own pixels.
- **POSE text is never written from my reading alone again:** it has to agree with the measured facts (table tennis v8 and pin v11 rewritten from them).
- Round v11 (13:31) tests each control on the pin and table tennis.

## 13. What a run folder costs in Gemini credits, and how to cut it (2026-09-27)

**The user asked:** how many image tokens one output folder uses now, against the first runs, and whether the cost per image can come down.

**What we pay in:** the Gemini web app deducts compute credits, not tokens: 2,400 per 5-hour window and 48,384 per week, reduced together.
- Google publishes no per-image credit cost for the app. Since May 2026 limits are compute-based: prompt complexity, model and features, chat length.
- API scale, for reference: Nano Banana 2 costs 1,120 output tokens per 1K image. Input images cost a fixed 280/560/1,120 tokens by resolution level, not by pixels.

**Measured credits per image** (quota readings at login and `tools\quota.py`):

| Window | Route | Credits per image |
|---|---|---|
| 09-21 | replicate | ~86 |
| 09-26 afternoon | replicate + gen | ~80 |
| 09-26 21:31-23:14 | route G | 69 (1,655 for 24) |
| 09-26 23:14-23:23 | route G | 64 |
| 09-27 02:31-02:47 | route G | 75 |
| 09-27 round v11 | mixed | ~75 (≈1,276 for 17 images + 1 refusal) |

- A text call costs 1-2 credits.
- A refusal is nearly free.

**Per run folder:**

| Run type | Credits per run |
|---|---|
| First `gen` runs (09-17, 1-2 images) | ~70-160 |
| Replicate runs (6 edits + up to 3 synthetic refs + ~10 text calls) | ~500-840 |
| Route G runs (4 images) | ~260-300 |

**What drives the cost:** the number of generated images. Output is always about 1 MP, and the web app has no resolution setting.
- Input size doesn't: replicate sent 3.4 MP and paid 75-93 per image; route G sends 66 MP and paid 64-75.
- Prompt length shows at most a weak effect.

**Levers, in the order the plan tests them:**
1. **Per-call measurement.** `gen` records `credits` in `run.json` and prints `[Credits]`. `tools\credit_report.py` lists the runs. A hidden library re-send (`@running(retry=5)`, silent) shows as a call costing about twice the normal amount.
2. **Flash vs Pro chat model on the same request.** In the app both draw with Nano Banana 2, so Pro's extra cost would be its reasoning. Round v12 (14:00) tests this.
3. **Early stop:** `--stop-after-fails N` / `--stop-on-pass`. In round v11, 11 of 17 renders failed the gate; pin-B spent 4 renders on an answer known after 1-2.
4. **Replicate becomes a fallback** (500-840 per run). Replace-subject gives posture-true edits at ≤4 images.
5. **Trim what does nothing.** Drop the sketch and LAYOUT text when the goal image is sent. Fix `prepare_ref`: it uploads the full 12 MP cached copies because an up-to-date cache file is returned without checking its size.

**Round v12 (14:00, measured per call):**

| Run | Model | Credits | Per image | Pose gate |
|---|---|---|---|---|
| Table tennis W2 (same request both times) | Flash | 209 | **52.2** | **3/4 pass** |
| Table tennis W2 (same request both times) | Pro | 319 | 79.8 | 0/4 pass |
| Pin W2 (Pro) | Pro | 77 | 77 (1 image) | FAIL, right forearm 17° |

- **Flash, on table tennis:**
  - 35% cheaper per image, and better: posture as the goal, the gold glasses back, head bowed steeply.
  - v1's beard looks longer than his references.
  - v4 was a new close-up scene instead of an edit, and the gate caught it.
- **Pin W2:** 3 of 4 were refused as a public figure, and refusals cost about 0 credits.
- **Per-call readings lag by one call**, so run totals are the number to use.
- **Gate note, not changed:** feet-apart is a ratio of two small numbers when the goal's feet are close (0.19 torso lengths). Pro v1/v4 fail only on it. Proposed to the user: an absolute limit (|diff| ≤ 0.15 torso lengths).
- **Pending the user's review of the Flash renders:** Flash as the default generation model. The `prepare_ref` fix waits until then, so the comparison stays clean.

## 14. His own body in the pin (2026-09-27 evening)

**The user:** "yes all generation still improved further. but pinterest generations any versions are not using my body."

**Seen:** on a same-torso-scale sheet (`tools\body_sheet.py`), every pin render has the goal man's heavy build: broad thick shoulders, big arms, a big chest. His references (`IMG_6923 Copy`, `IMG_0440_Original`) show a slim, lean build.

**Causes:**
1. The edit and goal-image modes keep the goal body's pixels; Gemini swaps only the head.
2. The BUILD text ("broad shoulders, wide clavicle span, visible deltoid caps, defined biceps", from the user's sample prompt) described a more muscular body than his.
3. Nothing checked build.

**Done:**
- `facecard.json` `build_text` now matches his references: slim and lean, moderate shoulders, slim arms, flat chest, narrow waist. The old text is kept as `build_text_before_2026_09_27`.
- In goal and edit modes the prompt names the failure (now seen): never the goal man's broader, more muscular build. Edit mode now replaces "his whole body and head, not only his face".
- An automatic build measure (arm width and shoulders over torso length from YOLO masks) **failed validation**: it read the goal man as slimmer-armed than him. It was deleted and not used as a gate.
- `tools\body_sheet.py`: the fair visual check (head to hips, same torso length).
- Default model is Flash (user-approved). `prepare_ref` now downscales cached references (1536×2048 sent, not 12 MP).

**Round v13:**
- **Body-only edit of the pin-W v2_0 composite** (Flash, 19.5 credits per image): posture kept, build barely changed.
- **pin-W3** (whole-body wording, Flash, 42 credits per image):
  - 3 of 4 pass the pose gate, with no public-figure refusals on Flash (Pro refused 3 of 4).
  - `v3_0` has identity 0.864, the highest yet, but no sunglasses.
  - The body is still the goal's in all of them.

**Rounds v14-v16 (Flash, about 20-64 credits per image): an edit chain, each step one change:**
1. Replace-subject edit of the pin (pin-W3 `v3_0`: his face 0.864, the goal's body).
2. Slimming pass 1, with magnitudes: "upper arms about a third thinner, narrower shoulders, smaller flatter chest". Result `20260927_191818_goal-v3-0/v2_0`: visibly slimmer, 0.808.
3. Slimming pass 2: "clearly thinner, no bulging biceps". Results `20260927_192155_goal-v2-0/v1_0` (0.868) and `v2_0` (0.771): a lean build, much closer to his reference. Both pass the pose gate against the real pin goal.
4. Adding the goal's sunglasses back (round v16).

**Also found:**
- The angle-routed FACE references can be whole-scene favourite photos. `IMG_4861_fav_right` (his rocky boulder-and-dog photo) was edited *instead of* the PHOTO TO EDIT, and the pose gate caught it (half size, wrong place). `_fav` references now go as 768 px head-and-shoulders crops (`replicate.head_ref_crop`).
- On the sunglasses composite the slimming pass swapped the dark sunglasses for clear glasses in one render and dropped them in the other: "keep his eyewear" did not hold.
- Flash made no public-figure refusals on these edits (Pro refused 3 of 4 on the pin).

## 15. The pin chain regressed 10 versions, and the checklist was skipped (2026-09-27 night)

**The user:** the three pin versions (`20260927_192155_goal-v2-0/v1_0`, `20260927_192624_goal-v1-0/v1_0` and `/v2_0`) "regressed 10 version progress in a single go, do u even consider them best? what happened to our check lists?"

**What was wrong (seen at full size, and now measured):**
- The head is level with the eyes straight to the camera: head bow 0.40-0.42 against the goal's 0.52. The good pin versions read 0.46-0.58.
- It is a studio passport face on a candid body: the level-face mistake recorded before.
- Checklist: NOT BEST, 9-10 items failed each (4, 5, 12, 13, 14, 16, 24, 26, 27, and 10 or 21), recorded with `best_check.py`.

**How it got past me:**
1. **The checklist was never run.** I showed them after only the pose gate and ArcFace, as "progress" on the one complaint being fixed (the body). This is the same fix-one-thing tunnel as before.
2. **I picked the chain base by the highest identity score** (pin-W3 `v3_0`, 0.864). ArcFace scores a level, camera-facing studio face highest, so picking by it chose the regression.
3. **The pose gate had no head-bow or gaze measure**; the neck-line angle passes a level head.
4. **Body-only slimming passes went through replace-subject.** That mode sends his frontal studio face photos and asks for the whole head to be redrawn, so every "slim the body" pass also re-made the head as a level studio face.
5. **Each step was compared with its base, not with the goal and the earlier best versions.**

**Fixed:**
- `pose_compare.py`: new head-bow check (item 12, |Δ| ≤ 0.08, validated).
  - FAILS the 4 regressed renders.
  - PASSES pin-W `v2_0`, the approved table-tennis Flash renders and the kept Instagram version.
- `gen --body-only` (with `--replace-subject`): sends only the BODY and ARM references plus the photo to edit, and says not to redraw the head.
- BEST_CHECKLIST: nothing is shown as progress before the checklist is recorded and compared item by item with the current best of that photo. ArcFace never picks a candidate or base.
- Round v17: body-only slimming on pin-W `v2_0` (the base that passes every measured check).

## 16. His body under the right head in the pin: everything tried (2026-09-27 night)

**The target:** his lean build (his references) plus the goal's bowed head, sunglasses, posture and position. Base: pin-W `v2_0`, the one render that passes every measured check, with his face but the goal man's body.

| Try | What happened | Checklist |
|---|---|---|
| Body-only edit of pin-W `v2_0` (no face photos, "do not redraw his head") | Flash redrew the head anyway: level, eyes to camera, sunglasses dropped | 9 fails each |
| One pass: replace + slim + head-bow wording | Head bowed, but the goal man's build; lookalike faces (0.25/0.50) | 21, 24, 26 |
| User's "different way": edit HIS full-body photo into the pin (goal as reference only) | Goal man's muscular build again; lookalike faces | 14/21/26/29/30 |
| Option A1: Gemini edits only a body crop (no head), code pastes back | Gemini barely reshapes a crop: width change 1-3%, with either wording | - |
| Option A2: head transplant, pin-W head onto slim2 body (same frame, ECC 0.81) | Person-outline mask: the goal's neck floats beside the beard. Face-parser mask (BiSeNet): a dark seam under the beard, a smeared patch; reads pasted | fails 4/11 |

**What this shows:**
- Gemini keeps the goal man's body in any edit or reference of the goal.
- It slims only when it re-renders the whole person, and every such re-render re-levels the head to a camera stare.
- Code pasting between renders gives the pasted look.

**Not tried yet:** an instruction editor built to leave unedited regions untouched, such as FLUX Kontext on a free Hugging Face Space (fallback route H in the plan). It would slim the body in one pass while keeping the head's pixels.

**Tools kept:**
- `tools\body_crop_edit.py` and `tools\head_transplant.py`: option A, measured and failed.
- `gen --edit-photo`, `--body-only`.
- The face parser wiring: FaceFusion's `bisenet_resnet_34`, run from the YOLO venv with onnxruntime.

## 17. The pin at the first go: the element inventory (2026-09-28)

**The user**, on pin-W2 `v3_0` (`20260927_140839...`): "face and body language perfect, but bike tank pattern not mine, and many other unliked features still seeping in. Make them all go right at the first go." His choices: his own helmet, the bike's accessories and his watch; the watermark removed.

**Cause:** an edit keeps every goal pixel the prompt does not name. "The motorcycle becomes his CB350" named no parts, so the Ducati's wire-spoke wheels, knobby tyres, wavy disc and mirror survived, along with the goal man's helmet, watch and the watermark.

**Built:**
- `.cache\inventories\pin_783485666539775315.json`: every visible element is HIS, GOAL or REMOVE. Each HIS item reads "the photo shows X; make it Y (image N)".
- `tools\ref_sheet.py`, references cut from his own photos:
  - bike side `IMG_5857` and bike three-quarter `IMG_5162` (number plate blurred);
  - an items sheet: tank close-up, his helmet, his round smartwatch;
  - a clean photo to edit, with the watermark inpainted.
- `gen --inventory`: the references by role, the clean photo to edit, and CHANGE / KEEP lists. It refuses more than 10 files (the Gemini app's limit per prompt).
- `tools\inventory_check.py`: a parts sheet per render against his references, plus an optional Gemini yes/no second opinion.
- An objects-only inventory mode with `tools\region_edit.py`: a crop without a head, only the listed object changes, pasted back, a re-framed return refused.
- Rule added to BEST_CHECKLIST: an inventory before the first render of any goal.

**Round v22** (the v3_0 recipe: Pro, replace-subject, same face references, plus the inventory; 304 credits, 4 renders, no refusals):
- `v1_0` passes the pose gate, including the head bow.
- Right at the first go: his wheels and road tyres, plain disc, chrome mudguard, round black mirrors, black handguards, the fog lamp on the crash guard, his helmet (clear visor), his watch, no watermark. The tank is close: grey over-top stripes and bands, silver HONDA.
- Checklist: only 26 fails, for the frame slider missing and the engine-cover lettering garbled.
- I first recorded "handguards missing" from a small parts-sheet crop, and the Gemini second opinion also got it wrong. Parts must be judged at full zoom.
- Round v23: an objects-only region edit of the engine area (frame slider, HONDA engine cover).

## Reviews (scores -2..+2 against the source, defect tags, keep = best version)

| Date | Picture | a | i | Kept as best version | Tags | Note |
|---|---|---|---|---|---|---|
| 2026-09-23 | `20260923_160011_replicate_google-2__IMG_3943/not_passing_closest.jpg` | -2 | +0 |  | size pasted | unreal, monsterish: head too big for the body |
| 2026-09-23 | `20260923_161146_replicate_google-4__IMG_0862/not_passing_closest.jpg` | -2 | +0 |  | pasted angle hair | unreal, monsterish: re-framed return merged on the face box, second hairline and ear, smeared collar |
| 2026-09-24 | `20260923_201520_replicate_google-4__IMG_0862/not_passing_closest.jpg` | +2 | +2 | yes: D:\Downloads\AI me\google-4__IMG_0862_20260923_201520.jpg |  | perfect |
| 2026-09-24 | `20260923_201520_replicate_google-4__IMG_0862/cand2.png` | +2 | -2 |  |  | meh |
| 2026-09-24 | `20260923_183350_replicate_google-1__IMG_4861_SnapseedCop/best.jpg` |  |  |  | pasted angle | absolutely horrible: the same defect as diagnosed; face drawn level under hair and skull seen from above, looking down (a, i irrelevant) |
| 2026-09-27 | `20260926_213623_goal-instagram-dwrfdriiww8/v3_0.jpg` |  |  | yes: D:\Downloads\AI me\instagram_DWrFDrIiWW8_20260926_213623.jpg |  | huge success (the user, 2026-09-27); kept despite checklist items 6 (face slightly small) and 26 (helmet lettering) |
| 2026-09-29 | `20260928_pin_final/pin_v1_engine_v1_0.jpg` | +2 | +2 | yes: D:\Downloads\AI me\pin_783485666539775315_20260928_pin_fi.jpg |  | perfect version (the user, 2026-09-29): inventory run v22 v1_0 + engine region edit; passes all 30 items and the pose gate |
| 2026-09-29 | `20260927_140839_goal-pin-783485666539775315/v3_0.jpg` |  | +2 |  |  | bike tank pattern not his; the goal's Ducati parts, helmet, watch and watermark seeped in |
| 2026-09-29 | `20260927_192155_goal-v2-0/v1_0.jpg` | -2 |  |  | angle expression | regressed 10 versions of progress in one go (the user, 2026-09-27): level head, eyes to camera, passport face on a candid body; checklist was skipped |
| 2026-09-29 | `20260927_192624_goal-v1-0/v2_0.jpg` | -2 |  |  | angle expression | regressed 10 versions of progress in one go (the user, 2026-09-27): level head, eyes to camera |
| 2026-09-29 | `20260927_192624_goal-v1-0/v1_0.jpg` | -2 |  |  | angle expression | regressed 10 versions of progress in one go (the user, 2026-09-27): level head, eyes to camera, arms heavier |
| 2026-09-29 | `20260927_134902_goal-pin-783485666539775315/v2_0.jpg` |  |  |  |  | the goal man's heavy build, not his body |
| 2026-09-29 | `20260926_214359_goal-pin-783485666539775315/v4_0.jpg` |  |  |  | size | failure reasons identified correctly (the user, 2026-09-26); camera distance not kept as the goal; the user copied it to AI me by hand |
| 2026-09-29 | `20260927_024244_goal-google-2-img-3943/v3_0.jpg` |  |  |  |  | posture not as the goal |
| 2026-09-29 | `20260927_140053_goal-google-2-img-3943/v2_0.jpg` |  |  |  |  | all generations improved further (the user, 2026-09-27): posture, glasses, head bow right (Flash) |
| 2026-09-29 | `20260927_140053_goal-google-2-img-3943/v3_0.jpg` |  |  |  |  | all generations improved further (the user, 2026-09-27): posture, glasses, head bow right (Flash) |
| 2026-09-29 | `20260926_232006_goal-google-2-img-3943/v4_0.jpg` |  | +2 |  | hair blur | body posture not as the goal |
| 2026-09-29 | `20260926_215045_goal-google-2-img-3943/v3_0.jpg` |  |  |  | hair | posture not as the goal |

## 18. The motorcycle-outfit-men board, pins 2-9 (2026-09-30 night, round v25-v28)

**The user:** run gemini-identity-gen on eight pins of the Pinterest board (D:/PinterestBoards/motorcycle-outfit-men; the motorcycle pin was the goal of sections 11-17 and was excluded).

**Recipe used (the v22 recipe, Flash, no code change):** per pin `.cache/pin_<id>.jpg` (+ `_clean.jpg` with the watermark inpainted for the ASL and DreaminaAI pins), `pose_compare.py --save-goal`, an element inventory (`.cache/inventories/pin_<id>.json`: the man, hair, beard, skin, build as CHANGE items; posture, head, clothes, props, scene, light as KEEP items), then `facecard.py gen --subject me --goal ... --goal-as-image no --replace-subject --inventory ... --stop-after-fails 2`. Runs can be started as separate processes in parallel (the user asked for it; five at once worked, credits per call read high because the window counter is shared).

**Results (Gemini sparkle left in the bottom-right corner as produced):**
- Passes all 30 items: pin 2 v1/v2 (`20260930_234015`), pin 3 v1/v2 re-run (`20260930_235828_goal-pin-...5340`), pin 4 v2/v4 (`20260930_234557`), pin 7 v4 re-run (`20260930_235828_goal-pin-...7115`, identity 0.584, slim arms), pin 8 v3 (`20260930_235607`, identity 0.659).
- NOT BEST: pin 5 (identity 0.14-0.21: bowed head in black and white, gray zone, needs the user's eye), pin 6 (best = first run v1: head bowed lower than the goal, x1.13 size), pin 9 (head bow right after the re-run, but the goal man's heavy arms stay; identity 0.13-0.16).

**What this taught (do not repeat):**
1. **A goal that is cropped by the frame edge gets re-centred** (pin 3 v1/v2: man moved from the far left to the middle; pose gate failed only on hand position). Fix that worked first time: a FRAMING line first in the keep list (how much of the frame width he fills, head centre as a share of width and height, which edge cuts him). Pin 3 re-run passed 4 of 4.
2. **Saying "exactly as in the PHOTO TO EDIT" about his head or arms makes Gemini return the goal man unchanged** (pin 6 re-runs: mean abs diff to the goal 5-6.5, face and hair still the goal man's). The pose gate cannot see this (the pose matches the goal by construction), so check every pass with the eye and with the diff. Describe the pose in geometry (turn, bow, where the nose tip sits) without pointing back at the photo.
3. **Build:** naming the goal man's build as the failure AND giving concrete slim measures ("upper arms only a little thicker than his forearms ... sleeves hang loose") fixed pin 7 (from 3 of 4 heavy to a slim 4th), but not pin 9 (tight polo sleeves) and not the first pin 7 run (only a generic slim sentence).
4. **Named colours get lost:** pin 7 v2 turned the light-grey sweatpants blue-grey; stating "the exact same light warm grey, never blue" fixed it.
5. `--pose-points` is dropped when an inventory is given (the inventory replaces the scene text); the framing line carries the numbers instead.
6. `facecard.py gen` prints no identity score for a profile or hidden face; `facecard.py score <pictures>` still gives max_ref_sim (pin 7 v4: 0.584 while gen printed nothing).
7. **End hook (2026-10-01, corrected the same day):** only PASSED pictures (checklist BEST, or accepted by the user with `best_check.py --user-approved`) are copied by `tools/export_results.py` into one flat folder `D:/FacecardResults/`, named `<collection>_<NN>_<title>_v<N>.jpg` (no subfolders; names in `results_names.json`; hidden state `.export_index.json`). Called by best_check (copy on pass, withdraw on fail) and at the end of gen / replicate. Exported: pin 2 v1-v2, pin 3 v1-v2, pin 4 v1-v2, pin 6 v1 (user-approved), pin 7 v1, pin 8 v1.
8. **Feedback ledger (2026-10-01):** `FEEDBACK_LEDGER.md` / `feedback_ledger.json` hold one permanent entry for EVERY generated picture (what was wrong, what went right, identity, pose-gate detail); written by the end hook in `tools/export_results.py`; `best_check.py --right` adds the positives. Read a goal's section before regenerating it.
9. **The user's review of the results folder (2026-10-01):**
   - pin 6 pencil in mouth v1 (accepted the day before): now REJECTED. "The pencil is not in my mouth at all, it is held by my chin in a physically impossible way; my head seems weirdly placed on top of the body; my body has not been changed, the physique is of a different person." Approval withdrawn, failed 5, 8, 12, 14, 21, 26, 29, 30.
   - pin 7 mirror selfie cat grey tee: "can work with more clarity in the face; it is very smoothened, hence negative points on identity". A sharp-face line (real skin texture, pores, beard hairs, never smoothed) produced a clearer face at identity 0.709 (`20261001_043443.../v3_0.jpg`), now pin 7 v2 in the results folder.
   - pin 8 mirror selfie cat shirtless (regeneration v2): "quite good actually" (user-approved).
   - every goal of the board must be represented by its best picture: pin 1's perfect version was imported (`--import`).
   - Pin 6 lesson (Pro, 2026-10-01): with the slim-build and one-continuous-body lines the brush sits in his mouth, the head joins the neck and the build is his, but the model re-frames wider (pose gate 12/14/29 fail).
10. **The Pinterest board finished (2026-10-01):** all nine goals of motorcycle-outfit-men have a picture in `D:/FacecardResults` that passed the 30 items (`tools/goal_status.py`: 0 open). The hard ones: pin 3 (build: the visible-consequence wording), pin 6 (slim-build wording WITHOUT a framing line; framing lines return the pin man), pin 5 (Pro seed lottery: identity 0.19-0.73 over 9 samples), pin 9 (head bow: ask deeper than the goal; build: two-stage body-only edit with explicit magnitudes). Pin 9 v1 and pin 6 v2 were passed by eye on identity (bowed/profile face, ArcFace unusable) and on physique, flagged for the user to confirm. The loop-until-perfect rule is in the gemini-identity-gen skill.
11. **The user rejected pin 5 and pin 6 (2026-10-01), both passed 30/30 by my eye.** Measured causes: hair and beard were the pin man's (long loose curls, patchy stubble) instead of his references' (tight curls, short faded sides with the ear and scalp visible, a full dense beard); pin 5's face was lit 1.7x brighter than the pin's (103 vs 61). A profile or bowed face cannot be scored, so item 21 and the hair/beard items had been passed from a whole-picture view. Fix: haircut and beard written as geometry in the inventory (v4/v9 variants), the pin's face shade written as a keep line, and `tools/audit_views.py` (head row beside all his references in black and white, face-light ratio with limit 0.77-1.30). Result: pin 5 v2/v3 (face light 62-63 vs 65) and pin 6 v3 (face light 83 vs 75; ear and temple checked with the shadows lifted; one other pose-gate pass was rejected for a patchy beard). The old pin 5 v1 and pin 6 v2 stay in D:/FacecardResults, marked failed, until the user confirms the new ones (`best_check.py --keep-in-results`).

12. **Identity regression on pins 5 and 6 (2026-10-01 night):** the user said none of pin 5 v2/v3 and pin 6 v3 look like them, 'negative progress in identity retention'. Measured: pin 5 ArcFace by request variant (Pro): original wording n=11 mean 0.31 (0.03-0.73), my hair/beard geometry wording n=3 mean 0.27; so the wording was not the measurable cause, and the 0.733 picture was the luckiest of 11. I had dismissed the low scores as unusable for a bowed face, which was wrong (the same pose had scored 0.733). A face swap (restore) is locked out on a bowed head or smears the eyes. Lesson: the face-shade line and 'face exactly as in the references' wording made it worse (the face is hidden, 0.08); the old picture (pin 5 v1, brighter face) has the best identity. DO NOT TRY AGAIN: a face-shade keep line for goals whose man's face is shaded; my own geometric beard/hair description; the swap on bowed faces. Next: the old wording unchanged with only --face-count 6 (the two front-on photos IMG_6873 / IMG_6858 are dropped by the default cut of 4 for turned heads).
13. **Experiment 2026-10-01 night, one variable: six face photos instead of four (original wording, Pro):** pin 5 identity 0.01 / none (face hidden) / 0.12 (baseline n=11 mean 0.31), pin 6 no render passed the pose gate. Six photos did NOT improve identity; keep the default four. Cumulative DO NOT TRY AGAIN for identity on pins 5/6: face swap on a bowed head; my own geometric hair/beard description; a face-shade keep line; "face exactly as in the references"; more face photos. ~900 credits spent on these rounds without a gain: the ArcFace average of this route on a visible face is ~0.3 (accept line 0.52) and a single lucky sample (0.733) is what the old pin 5 v1 was. Open question to the user: what exactly is wrong with the OLD pin 5 v1 and pin 6 v2.
14. **Two-stage head redraw on pin 5 (replicate, Pro, 2026-10-01 22:17):** attempt 1 identity 0.31, similarity to its own source face 0.786, head size 1.068 (limit 1.04): the redraw copied the face it was given instead of making it more his; attempt 2 stopped at the quota. On pin 6 the redraw cannot run (no face detected on the bowed profile). Pattern across every judged picture: identity is high only when the face is VISIBLE and lit (pin 8 0.63, pin 7 0.71, pin 2 0.60, old pin 5 v1 0.56-0.73 with a face 1.6x brighter than the pin's) and collapses when the face is shaded or hidden the way the pin man's is (0.08-0.31). The pin shows the man's face in deep shade, so 'looks like the pin' and 'looks like him' pull apart: the user's old verdict on pin 5 v1 was 'doesn't look like me, too different from the pin, body or something else'. Experiment queued for after the 02:31 reset: pin 5 with the face about a quarter brighter than the pin's (inventory v6), Pro x3, measured by ArcFace; pin 6 samples with the original wording for the user to choose by eye.

15. **Overnight 2026-10-02 (credit window reset 02:31):** pin 5, face a quarter brighter than the pin's (ratio 1.12-1.23): pipeline identity 0.34-0.41, sheet ArcFace 0.18-0.23 vs the old pin 5 v1 0.733 / 0.36: moderate brightening did not recover identity; only the 1.6x brighter old picture stays closest to his references. Pin 6: none of three Pro samples passed the pose gate (one re-framed to a wide shot). The identity-gated redraw is impossible on pin 6. Sheets for the user: .cache/audit/sheet_pin5_overnight.jpg and sheet_pin6_overnight.jpg. No credits spent after this (1,926 left, resets 07:31); the decision (faithful shaded face vs recognisable lit face) is the user's.
16. **Think-again, 2026-10-02 (pins 5 and 6, identity):** DO NOT RETRY (all measured): own hair/beard wording, face-shade line, face swap on a bowed head, six face photos, 'face exactly as in the references' wording, head redraw (copies the given face; cannot run on pin 6), face a quarter brighter, and clean-photos-only references (this test: pin 5 0.26 / 0.04 vs baseline 0.31). Findings: (1) every render of 139 was sent one of only 3 reference sets, each with a _fav photo (glasses, short hair, purple/yellow double exposure); removing it changed nothing; (2) identity does NOT correlate with head bow (0.13), turn (0.13) or face size (-0.29) across 29 pin 5 renders: it is a likeness lottery (0.01-0.73 on identical inputs); (3) the highest-scoring sample (0.733 = old pin 5 v1) is the one the user rejected as 'doesn't look like me', so ArcFace does not match the user's eye on this goal. Next: ask the user which facial features look off and which accepted picture looks most like them.
17. **The user's own words on pins 5 and 6 (2026-10-02), after the think-again round:** pin 5: 'lighting off, face seems lasso-ed in'; pin 6: 'not me at all, body me, face structurally me but closely not me at all'; the accepted pictures (pins 2, 7, 8): 'all' look like him. So identity was the WRONG target for pin 5: the old picture's face is 27% brighter than its own neck (94 vs 74; the pin's face/neck ratio is 0.97), the pasted-in signature I never measured. tools/audit_views.py now prints FACE vs NECK (tolerance 0.12 around the goal's ratio) next to FACE LIGHT. Overnight pin 5 renders keep face and neck consistent (0.85-1.00). Pin 6: the body is right; fine facial detail is the open problem, no tool measures it, and the final pre-reset batch (4 Pro) did not pass the pose gate. Lesson: ask the user for THEIR words about what is wrong before optimising any number.

## 19. Pins 10-13, the second review and three standing rules (2026-10-09)

**The user, on the first samples of the four new pins:**
- gym back: "you are removing the back definition that I actually have, increase back definition a little more, also face and body fat percent are mismatching, face looks a lot smoother compared to body, hide the face a little more";
- pizza: "perfect already (text in the background could be given better attention), i would have liked the subject with a very light smirk instead although goal reference doesnt have it, another variation of candidly smiling";
- "most important among all three": no added background humans, no added text in AI images (with a reference or without), and a candid look as if captured in a rush, with motion blur.
- Decisions: his video `D:\Downloads\B9F9CBB0-...MP4` is the back reference; the pin's own background is copied back after the edit.

**What was built (all free to test, measured):**
1. Checklist items 33 (background people), 34 (text), 35 (candid capture look), item 16 allows an asked-for smirk; `best_check.py` wants an evidence line for 33-35; `inventory_lint.py` notes inventories without people or lettering keep lines (`--scene` for text-mode paragraphs); scene-prompt-writer got `capture: candid`, an empty setting and glow-only signs.
2. `tools/background_restore.py` (code copies, never edits Gemini's person pixels): on the pin 10, 11 and 13 samples the background ECC was 0.971-0.997 (scale 0.986-1.004, shift under 0.007 of the frame); the background outside both silhouettes differed from the pin by a mean 3.6-22 grey levels (SSIM 0.77-0.97; pin 13's samples had redrawn the lanes) and is now the pin's own pixels (43-61% of the frame copied). Two defects found on the first tests and fixed: the pin man's hair bun outside the YOLO mask came back above the new head (fix: Gemini's pixels are kept where the sample differs by more than 28 grey levels within 6% of the longer side of a silhouette), and Gemini's sparkle watermark (kept whole when a silhouette reaches it, replaced by the pin's pixels when not).
3. `tools/back_reference.py`: his back from frames 54 and 74 of the video, the thin line along his spine traced and replaced by skin: it is his janeu, not an earphone wire as I wrote (the user, 2026-10-10); since then it is kept (three automatic detectors, top-hat, local colour contrast and a Hessian ridge filter, all found the silhouette's edges instead), and record-only back measures: his four frames shoulder width / torso length 0.55-0.63, shoulder / hip width 1.44-1.47; the pin man's reading is unusable (shoulder confidence 0.42); the first gym samples read 0.42-0.47.
4. `tools/wave.py --parallel N --stagger S --not-before HH:MM` and per-job `"restore": true`; the wave runs from the hidden one-time task `facecard-wave-pins1013d` so a session crash cannot kill it again.

**Why the first samples failed him (measured):** the v3 gym line "a fifth narrower, lats slimmer and smoother, no deep carved grooves" is what removed the definition he really has (the samples' shoulder / torso ratio was 20-27% below his own frames); the visible face was a lowered 3/4 profile in 4 of 4 samples, so its softness showed against the lean body (hide it behind falling curls, ask for a hard jaw line); pin 13's samples came out bigger (torso x1.23-1.26) and further right than the pin man, so v5 is stage 1 only (replace in place, head still away) and the head turn becomes a second edit.

**Recipes of the wave:** pin 10 v5 (HIS BACK ref), pin 11 v3 (very light smirk) and v4 (candid smile) with the lettering named letter for letter, pin 12 v3 (text mode, mid-stride rush, motion blur, only the asked-for print as text), pin 13 v5 (stage 1). Results and the checklist verdicts follow below once the wave has run.

**Results of the 20:36 wave (2026-10-09, every picture checked on all 35 items with evidence):**
- Pizza (pin 11): PASSED twice. v3 (very light smirk) v1_0r and v4 (candid smile caught mid-reaction) v1_0r, exported as `motorcycle-outfit-men_11_..._v1.jpg` and `_v2.jpg`. The restore made the bar sign, the L10 card, SÁNCHEZ ROMERO, the bottle and the reversed glass letters the pin's own pixels; the beard is full and dense (the beard crop fixed item 28). v3 v2_0r shows the smirk most clearly but scores 0.50 (gray zone: the user's eye); v4 v2_0 came back re-framed (aspect 0.747 vs 0.813) and the restore refused it.
- Gym back (pin 10) v5 v1_0r passes 34 of 35: his back now has the definition of his video frames (shoulder-blade edges, spine groove, lat outline) and the curls over the brow hide the eye; only item 32 fails, both forearms carry the pin man's prominent veins where his are smooth (IMG_6923). v2_0r also turned the face toward the camera, added a neck chain and a towel, and failed the pose gate on 30.
- Print tee (pin 12): v3 "shopping-mall viewing gallery" drew readable shop signs (SOUL..., ...Shop), mannequins and a person-like figure (33, 34); v4 "atrium dissolved into portrait-mode bokeh" fixed the signs but still drew blurred people (33) and sharp hands (35). The print itself was exact in all four. DO NOT RETRY: describing a mall's shops as glow, or relying on "he is the only person in the frame" in a mall view.
- Bowling (pin 13) stage 1 (v5) v1_0r: the first render in the pin man's place and size (torso x1.05, every body check PASS; v1/v3 were x1.23-1.26); the head-position check missed (0.050 vs 0.04) because the head had begun to turn right. It is the base of stage 2.
- The old wave c had survived the session crash and ran two obsolete recipes at 20:35 and 20:38 (about 590 credits; 4 pictures, recorded NOT BEST); its driver was stopped one second before its third run.

**Queued for 2026-10-10 08:20** (task `facecard-wave-pins1013e`, after the Qwen overnight hard stop): pin 12 v5 (camera tipped up, only ceiling and lights behind him, an empty early-morning walkway, motion-blur smear on bag and hand), pin 10 v6 (smooth forearms, bare neck), pin 13 v6 (stage 2: an edit of the stage-1 base turning only his head and neck about 50 degrees right, smiling).

## 20. The ideal smile and the pizza third picture (2026-10-10)

**The user:**
- Smiles: "smile always is turning out bad ... my smile reference image itself is bad ... when captured in candid it can look different" (13 photos); the open smile with teeth is the problem; teeth first "mine, slightly whiter", then: "There is no need to change the color of the teeth or anything."
- Pizza third picture (`_v1` with v2_0r's eyes, region edit): "v3 is not getting the eyes from v2, and idk where it is getting from it has made it even worse and drunk looking". Then: "V2 is perfect. V2 just has a little more beard than what I would expect. Let's try to fix that ... It was a misdiagnosis from my end on the first read of V1 and V2. Hence, I want you to, in fact, push back a little on certain feedback of mine if you see that they are for sure wrong."
- On the two smile candidates (route B IMG_3884 v2_0, the front photo with smile words v1_0): "both are bad, unnatural. you have my natural smiling in the same poses what is the problem in them?" and "The smile itself is perfect. Teeth shape, size, my lips, everything is perfect, but it's the other facial expressions that are not matching with my real smile." For the front photo: use the smiling photo of the same tank-top session (IMG_6875) and "keep improving the Gemini generation" until it matches.
- The originals: "you can get it yourself from the Google Takeout".

**Measured:**
- Route A (front photo + smile crops): the tight crop (head 84%) zoomed out 10 of 10; on the loose crop 0 of 4 because the face comes back 5-16% larger with a big smile (face box and eye distance).
- `tools/smile_match.py --ai` on IMG_3884 route B v2_0: "mouth same, teeth same; eyes, cheeks, smile lines, brows weaker" (the user's verdict exactly); the five landmark ratios read within 7% (they do not see a squint). Cause: the `--expression same` wording ("but natural and relaxed ... never tense or forced") and a face drawn from four neutral photos.
- DSC07985 route B kept his glasses under `--glasses no` (the glasses check was skipped instead of asking for the change; fixed).
- The laugh looking down (IMG_3929): 0 of 12 over two crops; Gemini lifts the bowed head.
- Pizza beard fix (region edit below his eyes, his own beard as the reference): fix 2 cheek beard 26->20% dark, moustache 20->13%; fix 1 unchanged. Gemini's sparkle had been pasted onto the sweater (now never pasted).

## 21. The next-cut physique, the yardstick and pins 14-17 (2026-10-10 evening)

**The user:**
- Round 1 of the grey-out: "the fat around the waist even got increased further ... you shrank the arm size and have reduced my vascularity. I have a visible bicep vein and good forearm veins"; "The thing that you're calling an earphone wire is not an earphone wire. It is the holy thread that Brahmins wear, called jenu."
- Rounds 3 and 4: "round 3 actually has more improvement compared to round 4 in terms of waist tightening, but the arms look a little exaggerated, but it is acceptable"; then approved "Round 3" (with the forearm fix) and the back: "back approved, if you want to go for a 4th round - use the image that you extracted from the 6 sec video ... and yes very slightly increase shoulder breadth".
- The yardstick: "any shirtless picture will get the fully pumped version of mine, and casual outdoor dressed versions will get the casual in-between version of my body"; casual arms: "the size of the arm shouldn't reduce from the actual photo that I had sent, but the vascularity should lie between the real photo that I shared and the pumped photo that you have generated"; the in-between: "still not as casual as I wanted it to be ... but it's fine".
- The shoulder warp on the back: "basically increases the tricep size, and it looks very unnatural ... what I approved was slightly increasing the shoulder width and not arm size. These are still fine."
- Four pins in parallel: 783485666540168309 (pose, set in Gokarna from the bmcindia Instagram post and the Togedr Facebook photo, pumped front), 783485666540141726 (the back pin: "Start now with the approved back"), 783485666540168242 ("create a side body pose if required or utilise the back pose itself"), 783485666540141762 ("replicate").
- On the failures: "multiple rounds of failures seem to be happening back to back. Keep a record of why each of those is happening. Without stopping things that are going abruptly, you can also stop things once the current running wave gets completed if you think that the complete system is wired wrong" (FAILURE_LOG.md, the rework of 22:10).
- Pin 17 v2_0r: "not exactly the same pose, but plus points for making the face visible in the right amount" (the head turn of v2_0r is kept for the next version). Pin 16 v2_0r: "face almost there but still not accurate, needs fixing".
- 2026-10-11, pin 15 (body-only v3, janeu mirrored): "great picture, but the jenu is going in the wrong way. It should go from left shoulder to right oblique", then, after I said once that a mirror swaps the sides: "I had forgotten that this was a mirror image. The genu is perfectly positioned. Ignore my previous comments." Approved and exported. Rule: in a mirror picture the janeu is drawn mirrored (from his left shoulder at picture-right).
- 2026-10-11, pin 14 (two-stage Gokarna, v1 and v2): "something looks off. It is not replicating the ref goal images as it is. Both V1 and V2. Also, the physique that it is giving me is not looking like mine, and the face looks off. In terms of leanness and body fat percentage, the face still looks a lot leaner than the body." Withdrawn (FAILURE_LOG F28).

**Done and measured:**
- Approved physiques copied under plain names to `D:\FacecardData\physique\standard\` (pumped_front, pumped_back, casual_front; sha256 identical) and to `D:\FacecardResults` (physique_next-cut_front_pumped.jpg, physique_next-cut_back.jpg).
- `--physique` (recipes): me@v2 would have sent the relaxed IMG_6923 Copy with "arms of moderate size with light muscle tone ... never more muscular" on every shirtless pin; the standard's photo and build text now replace both. 48 Route G recipes recompile to their locks; pin 8 v2-v4 drift from the older character hair/beard wording.
- Back round 4 (video frame f_08, `body_grey_send@v6`): refused by the whole-crop paste fit (ECC 0.76-0.77) although aligned on the background (scale 1.00, 3 px, ECC 0.97): `region_edit.py --affine`. Measured: waist -8.6% (v2), love handles -10.8% / -13.5% (target -4..-8), arms -33.7% (v2); by eye both shrank his upper arms and forearms, with faint ghost edges beside the arms. Not passing; the round 1 back stays the standard.
- Gokarna: the Facebook photo needs a login (no browser connected); the Instagram post shows publicly one photo (ten trekkers in a palm grove), not sent: pin 14's background is written from the cliff path between Kudle and Om beach.
- Pin 14's turned-away face scored 0.461 against his photo pool (own photo from 0.40), so the recipe gate called the pin his own photo; `results_names.json` `"source": "foreign"` marks it as another man's (the threshold is unchanged). Pin 17's glass-door reflections are excluded from the restore (`.cache/restore_exclude/`).

## 22. Auto-continue fixed, and the questions asked at once (2026-10-11 night)

**The user:**
- "why is the decision idle and nothing is queued when you already know there are so many to-do items in the list? The auto-continue system seems faulty. Find out why this is happening and fix it." (FAILURE_LOG F31)
- "also edit your auto-resume to immediately ask using ask-user-question tool and on top of that still not be blocked by it and just choose the recommended option to keep working on until i answer. once that system is built ask me using it, whats blocking you right now?"
- His answers (AskUserQuestion, 2026-10-12 00:0x-01:3x):
  - Pin 14, "ref goal images": **Both** (the pin's pose, framing and look AND the real Gokarna place, each as it is).
  - The Gokarna photo: **"Open my Edge for it"** (I open his Edge profile once, read only the Togedr Facebook post, save the photo, close the browser).
  - Pin 16: **"Yes, test them"** (his real outdoor photos as face references, a test character; me@v2 unchanged).
  - Pin 10: **"Show the profile"**, then on the sparkle-fixed v7 pictures: "stop working on this image it misrepresents my height, i am taller than this as seen from full body reference image." (FAILURE_LOG F32; pin 10 is closed)
  - Approvals: **Pin 15 back** and **Pin 11 pizza**; on the pizza: "D:\Downloads\AI me\date simulate.jpg this already is best for me. wasnt this 'best' accrording to our checks?" That file is byte-identical to `outputs/20261010_114204_goal-v2-beard-send/v2_0r.jpg`; it had never been checked (no checklist record), so it waited two days for an approval instead of being checked and shown.

**Done and measured:**
- `tools/autocontinue.py`: `work` / `STALLED` decisions with a toast, `--after`, `--default`, `ask` / `questions` / `answer`. AskUserQuestion is not available to subagents ("No matching deferred tools found"), so the session asks itself after starting every default and handing long preparations to background agents; while his answers were pending, the queue ran pin16day and pin14v3a.
- Exported: pin 15 cleaned back (`_15_..._v2.jpg`, BEST user-approved, item 14 on record) and pin 11's beard-fixed v2 (`_11_..._v4.jpg`, BEST user-approved; item 8 on record: Gemini's sparkle on the back of his hand, missed by the base picture's check on 2026-10-10).
- Pin 14 (2026-10-13): after the head region edit and the widened body (shoulders +6%, measured 0.74 against about 0.89 for the standard), asked "Does this look like you?": "Yes, export it". Exported as BEST (user-approved; items 21, 26, 31, 32 on record). The Gokarna background (stage C) is still open.
- Pin 16 (2026-10-13): after the far eye was redrawn by grey-out (eye agreement -0.32, his band -0.34..-0.18; before -0.07), asked "Is the eye problem gone?": "Yes, export it". Exported as BEST (user-approved, item 21 on record).
- Pin 16's face (2026-10-12): "space between eyes"; shown that the spacing measures as his (my "too close" reading was wrong, FAILURE_LOG E13) and that the renders' eyes are less open: "Yes, it is less open, and it is something more than just spacing ... their relative spacing to the nose in between is likely off. Or it might be that one eye is looking 75° to the left and another is likely looking 80° or 85° to the left. Hence, it looks like an eye condition, which I actually don't have ... the instinct when a human eye is wrong is very visible for me." Next: measure eye openness and whether both eyes look the same way, against his real photos at the same turn (TODO 50).

## 23. The retrospective, the hold and the teeth (2026-10-17/18)

- 10-17: "all the recent generations have been going downhill. Do not generate any more images. Keep the to-dos on hold ... find out why and
  fix it." Generation is on hold (`.cache/GENERATION_HOLD`); why: `RETROSPECTIVE_2026-10-17.md`, FAILURE_LOG F71.
- 10-17, four decisions (dialog): the body reference of a shirtless picture is **the pumped physique, always**; **shirtless pins first**; the
  current-look items are **just pointed out** (`tools/best_check.py` NOTE; item 26's scenery sentence became item 37, which still rejects);
  spare credits go **only to plans the user approves**.
- 10-17: "smile is a major project item to be corrected since none of the generated images till now have good teeth showing images"
  (diagnosis: `.cache/smile_diagnosis_2026-10-17/REPORT.md`, FAILURE_LOG F72).
- 10-17, of two exported pictures they had approved in dialogs (pin 15 v2 on 10-12, pin 14 v3 on 10-13): "these are bad". Both withdrawn with
  `tools/best_check.py --user-rejected`; the approvals stay on record.
- 10-18: "do you want me to provide better photos of smile? previously when asked you said the ones you have are sufficient. dont keep blaiming
  the photos, i can recrop thm better and send again if you want." The photos are sufficient; no new or better photos are asked for.
- 10-18, the teeth (dialog): of the two pictures I had called exceptions, **only E2** (`outputs/20261010_125108_goal-img-6858/v1_0.png`) has
  the right teeth; the IMG_3884 redo (`outputs/20261010_085046_goal-img-3884-original/v2_0.png`) does not, which replaces the 10-10 words about
  it in section 20. Teeth **only for smiling goals or when the user asks** (closed lips elsewhere). The teeth references are the real
  **IMG_6875 + IMG_3884** (never the generated E2, never "whiter"). The first teeth test, once the hold is lifted, goes **straight to a
  shirtless pin**.
- 10-18, the teeth pin (dialog): **Pin 8** (none of the eight shirtless pins shows its man smiling; pin 8 has the largest face). Recipe
  `pin_783485666539777118@v8` = v7 plus his open smile with his own teeth (`--teeth`), frozen; its trial run (stages 01-03) matches the lock.
- 10-19 (dialog, "Lift the hold for this one run?"): **"Run pin 8 now (Recommended)"**. Run with `FACECARD_HOLD_PASS` for that one recipe;
  the hold file stays, so everything else is still held. It waited at the credit guard (need 2 x 120 + margin 150 = 390, window 307);
  the user chose "One render now", but the window fell to 16 by 03:52 (the user's own Gemini use: "Yes, that was me"), so both runs were
  stopped with nothing generated, and the user chose "Fresh start 05:35, 2 renders (Recommended)" (a fresh sign-in after the 05:33 reset).
- 10-19, the first teeth test (run `20261019_053523_goal-pin-783485666539777118`, 288 credits, background restored): teeth **"The first
  picture's do"**, overall **"Keep the first"** (`v1_0r.jpg`, exported as `motorcycle-outfit-men_08_mirror-selfie-cat-shirtless_v3.jpg`;
  on record: its head 0.054 higher than the pin's, pose gate limit 0.04). The second (`v2_0r.jpg`): not kept (an even row of teeth, the
  janeu starting mid-chest).
- 10-19, of the kept pin 8 picture: "although the teeth here were perfect, the hair is not." Cause: the background restore pasted the pin man's
  straight hair over the curls Gemini drew (FAILURE_LOG F73); Gemini's raw `v1_0.jpg` has his curls.
- 10-19, of the two fixes shown: "I like this one [v1_0_sparkle_only.jpg], as the other one has distortion around the halo that you tried to
  add." Kept as `v1_0s.jpg` (Gemini's render, only the sparkle replaced), exported as `motorcycle-outfit-men_08_mirror-selfie-cat-shirtless_v4.jpg`;
  the `_v3` export (the pin man's hair) is withdrawn and `v1_0r.jpg` recorded as rejected by the user.
- 10-19, the best pizza: "pizza best photo s under ai me actually" (`date simulate.jpg` = `_11_..._v4.jpg`; its base's head was untouched by
  the restore bug, 1.5% of head pixels differ). The older `_v2` export (curls trimmed) is left as it is.
- 10-19 (question box, after the links): "Next shirtless pin (Recommended)", then "Pin 4 now (Recommended)": recipe
  `pin_783485666539777050@v2` (Pro, 2 renders) run once with `FACECARD_HOLD_PASS`, then the head-safe background restore.
- 10-20 (box), of that run's two re-framed renders: "keep both but try again to frame it properly only after first debugging why it
  happened" (kept as `_04_..._v4.jpg`, `_v5.jpg`; the cause: FAILURE_LOG F74). Then, of the fix (recipe v3, physique `pumped-front-chest`):
  "Run it now (Recommended)".
- 10-20, of `_04_..._v3.jpg` (the 10-01 render, run `20261001_063344`, old slim build): "Both the recent versions look perfect to me. In
  fact, I prefer this version over the recent generations. Although it does break my rule of looking perfectly like the given goal Pinterest
  image, it still shows my personality better than the rest. That doesn't allow you to keep breaking the rule, but an exception could be
  made." And of the v3 fix renders (run `20261020_192346`, both failing the pose gate): "almost seem perfect. Could you help me understand
  what exactly you are claiming is wrong with them?"
- 10-21 (box), after the measured differences were explained (head upright and higher, more centered, the camera hand higher): the two fix
  renders "Keep both" (`_04_..._v6.jpg`, `_v7.jpg`, sparkle left: re-framed); the 10-01 picture's sparkle "Remove it (Recommended)", then of
  the fill (`tools/sparkle_fill.py`; the pin's-pixel patch showed a dark disc and was dropped) "Replace it (Recommended)": now `_v8.jpg`,
  `_v3.jpg` withdrawn as superseded (`best_check.py --superseded-by`).
- 10-21, the user: "dont wait until user approves just move on to next pin going forward". The pins then ran one after another, each ONE whole
  render under `FACECARD_HOLD_PASS` (2 pictures, no edits), checklists recorded honestly (nothing `--user-approved` for the user): pin 15 v4
  (run `20261021_031826`, Flash, back-torso photo + frame-aware words), pin 6 v4 (`20261021_032452`, Flash, whole render, pumped-side-chest),
  pin 14 v4 (`20261021_032954`, Flash, Gokarna in words, torso crop), pin 9 v4 (`20261021_033704`, Flash, casual-front-arms, restore with heads
  kept), then pin 13 v7 and pin 12 v6 on Pro (the model as the one new variable). Every pose gate failed again (15, 6, 14: head and shoulders
  lower or larger than the pin's; 9: only the head bow, 0.74 against 0.87); the pictures look like the user. Candidates await the user's eye.
  Full account: FAILURE_LOG F75 (which also corrects my first claim that Pro raised pin 13's identity: it did not).
- 10-21 (box, the round's results; pins 13 and 12 not asked yet): **Pin 9** restored render: "Keep it" (exported `_09_..._v2.jpg`). **Pin 6**
  render 1 (`v1_0.jpg`, exported `_06_..._v4.jpg`): "the better one out of the two renders, but it still does not match the given goal.
  Somehow, it slightly differs. Maybe it's the clarity of the photos, maybe this requires a little blurring, or it's the angle of the face or
  the sharpness in the face ... capturing the photo at the right angle to make sharp features of the face look exaggerated, for instance, the
  chin and nose ... this still is a very good render regardless. Great improvement from all past renders." **Pin 14** render 1 (`v1_0.jpg`,
  exported `_14_..._v4.jpg`): "captures the musculature perfectly, but it has softened or increased the fat percentage in my face. The face
  is not as sharp as the body looks here. Rest is the perfect image. Both the background and everything are perfect in this: body positioning,
  the subject, everything." **Pin 15**: "Neither is the correct answer, but ... the pose is hit in a way that the body's V shape gets exaggerated
  (regardless of whether the muscle mass is the same or not) ... adding non pumped video links to understand how poses can make huge
  differences" (IMG_7419, IMG_7420, IMG_7249; kept in `D:\FacecardData\body_refs\2026-10-21_videos`): memory `facecard-pose-shapes-the-body`;
  pin 15 v5 (a mirrored raised-arm frame of IMG_7420 as the pose-matched body reference, back wording that no longer narrows it) ran next.
  Both the pin 6 and the pin 14 notes say the same about the FACE: softer and fuller than the goal's sharp chin and nose and than the user's
  own sharp, lean face (checklist item 31).
- 10-21 (box, second set): **Pin 15 v5** (the video frame run): "The back musculature is still bad. It is underestimating my actual back
  musculature and flexed." **Pin 13 v7** (Pro): "The pants are below the buttocks, hanging on the hamstring or the knee in the photo that you
  rendered, unlike the given goal or reference, where they were actually just baggy but properly worn around the waist itself." **Pin 12 v6**
  (Pro), both renders: "the smile is horrible, total garbage, and the smile correction still needs to come up. Previously, we did nail it on the
  mirror selfie holding the cat. The same level of smile has to come here. Debug which exact step is failing. Moreover, the subject is too close to
  the camera and needs to be slightly back, or the background blur has to be reduced at the subjects. Refer to the Google image once again and
  imitate it perfectly, even when it comes to texture, background, everything, to mimic a natural photo." **What next:** "Fix both faces next
  (Recommended)" (pins 6 and 14). Recorded as not kept (`--user-rejected`).
  **The smile step that failed on pin 12** (found by comparing the two requests): the cat selfie's smile had his two real teeth photos as
  references and a CHANGE line "his own natural open smile ... as in HIS TEETH, FRONT"; pin 12's text-mode request had neither and asked for "a quick
  half-smile, one corner of the mouth lifted and the lips barely parted", so the smile was Gemini's stock smirk. Pin 12 v7 has teeth mode and the
  open-smile line, the camera 2.5 m away from the thighs up, the atrium behind in ordinary phone focus. Also in this round: pin 15 v6 (his real flexed
  IMG_7420 frame, unflipped, as the body), pin 6 v5 and pin 14 v5 (a sharp-face item and his real profile IMG_6863), pin 13 v8 (the jeans worn at the
  waist). The Gemini window was empty (0 of 2,400) from before 15:49 to 17:33 (not my runs: the last one ended at 12:02 with 2,128 left), so the five
  runs are queued for 17:35, one after another.
- 10-21 evening (run results; the user's verdicts follow): the credit window was empty from 15:49, refilled at 17:33 and was used up again by 17:53 by a
  consumer outside this pipeline (FAILURE_LOG F76). **Pin 12 v7** (`20261021_173953`, `--teeth`): his own teeth show (his IMG_6875 mouth is the yardstick),
  the background is in focus, the subject is as large in the frame as in v6 (eyes 76-77 px apart; the camera did not move back), the pin's small "Untld"
  mark is missing, v2_0 has two figure-shaped forms in a shop window; both NOT BEST. **Pin 15 v6** (`20261021_174638`): one picture, the janeu right,
  shoulders 0.177 and head 0.243 off the pin's, the back not more massive than v5's. Pins 6 v5, 14 v5 and 13 v8 are frozen and wait for the 22:33 refill.
- 10-21 night (the user's box answers, ~23:00): pin 12 v7 **"Render 2 (Recommended)"** (recorded user-approved, exported as `_12_..._v1.jpg`; its missing Untld mark and the
  two shop-window figure-shaped forms stay on record); pin 15 **"New render: pumped back + real frame (Recommended)"**: pin 15 v8 ran at 23:17 (F77); the credits
  question **"It was me"**: the drain of today's windows was the user's own Gemini use. The 22:33 chain ran pins 6 v5, 14 v5 and 13 v8 (F77): all NOT BEST by the checklist,
  the faces are sharp now, pin 13's jeans sit at the waist; pin 15 v8's back is thicker and only item 14 of the pose gate fails. Their verdicts follow.
- 10-22 (box, the night's results; recorded 01:10-02:40): pin 6 v5 **"Keep both"** (exported `_06_..._v5.jpg` and `_v6.jpg`); pin 14 v5 **"Keep both"** (exported `_14_..._v5.jpg` and
  `_v6.jpg`); pin 13 v8 **"Neither, new render"** (both withdrawn); pin 15 v8: "yes, we need a new render, and I want you to understand that the person in the Google Pinterest image is
  pushing their hips forward and leaning their back backwards towards the camera. That is, the back is relatively closer to the camera than the hips. This creates the back to look more
  triangular, that is, shoulders wider and waist narrower. Implement that pose exactly as it is." (both withdrawn; FAILURE_LOG F78). Pin 15 v9 (the lean) and pin 13 v9 (the scoreboard
  crops) are frozen, their dry runs pass, and they run at 03:33:25 IST after the refill.
- 10-18, a standing rule: "if you want any decision from my end, do not just write it in the chat. Use the Ask User Question tool to prompt
  that decision and get it from me."
