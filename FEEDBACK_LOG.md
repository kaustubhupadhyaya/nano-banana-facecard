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

