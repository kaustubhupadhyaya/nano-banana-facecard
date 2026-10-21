# Feedback ledger

One entry for EVERY generated picture, passed or not (written by `tools/export_results.py`, the end hook of the gemini-identity-gen skill). Only passed pictures are copied to the results folder; everything that failed is recorded here, with what was wrong and what went right, so the lesson outlives the file in `outputs\` (the session-start prune deletes those). Entries are never removed. Add the human notes with `tools\best_check.py <picture> --fail ... --note "what was wrong" --right "what went right"`.

Updated 2026-10-22 02:43. 657 pictures.

## misc_back-wrist-send

2 pictures, 0 passed.

- **attempt 1** `20261010_182109_goal-back-wrist-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, back_wrist_send@v1, request 2ae2efb883fb)
  - wrong: pose gate failed: person found no person in render
- **attempt 2** `20261010_182109_goal-back-wrist-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, back_wrist_send@v1, request 2ae2efb883fb)
  - right: pose gate passed every measured item

## misc_beach

1 pictures, 0 passed.

- **attempt 1** `20261001_063602_replicate_beach/not_passing_closest.jpg`: **NOT CHECKED YET**

## misc_body-grey-send

16 pictures, 0 passed.

- **attempt 1** `20261010_132103_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v1, request 0f952533a14e)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.043 (goal x0.52 y0.49, render x0.51 y0.45)
- **attempt 2** `20261010_132103_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v1, request 0f952533a14e)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.040 (goal x0.52 y0.49, render x0.51 y0.45)
- **attempt 3** `20261010_164007_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v2, request 8e270df02e3e)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.054 (goal x0.52 y0.49, render x0.52 y0.44)
- **attempt 4** `20261010_164007_goal-body-grey-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, body_grey_send@v2, request 8e270df02e3e)
- **attempt 5** `20261010_164007_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v2, request 8e270df02e3e)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.044 (goal x0.52 y0.49, render x0.51 y0.45)
- **attempt 6** `20261010_164007_goal-body-grey-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, body_grey_send@v2, request 8e270df02e3e)
- **attempt 7** `20261010_165103_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v3, request 5d392038a7e4)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.082 (goal x0.51 y0.49, render x0.50 y0.40); his right hand position shift 0.100 (goal x0.16 y0.96, render x0.16 y0.86); his left hand position shift 0.103 (goal x0.83 y0.95, render x0.86 y0.85)
- **attempt 8** `20261010_165103_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v3, request 5d392038a7e4)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.041 (goal x0.51 y0.49, render x0.51 y0.44)
- **attempt 9** `20261010_170647_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v4, request 6a6a625e8a8d)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.111 (goal x0.51 y0.51, render x0.51 y0.40); his right hand position shift 0.099 (goal x0.17 y0.96, render x0.16 y0.86); his left hand position shift 0.097 (goal x0.84 y0.94, render x0.88 y0.85)
- **attempt 10** `20261010_170647_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v4, request 6a6a625e8a8d)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.070 (goal x0.51 y0.51, render x0.50 y0.44); size in the frame (torso) x1.17
- **attempt 11** `20261010_174108_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v5, request 82864cf90f12)
  - wrong: pose gate failed: size in the frame (torso) x1.09; his left forearm direction 18 deg off
- **attempt 12** `20261010_174108_goal-body-grey-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, body_grey_send@v5, request 82864cf90f12)
- **attempt 13** `20261010_174108_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v5, request 82864cf90f12)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.049 (goal x0.54 y0.44, render x0.57 y0.40)
- **attempt 14** `20261010_174108_goal-body-grey-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, body_grey_send@v5, request 82864cf90f12)
- **attempt 15** `20261010_184945_goal-body-grey-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v6, request 438b5c718cef)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.044 (goal x0.47 y0.31, render x0.50 y0.34); head position shift 0.232 (goal x0.48 y0.08, render x0.59 y0.28)
- **attempt 16** `20261010_184945_goal-body-grey-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, body_grey_send@v6, request 438b5c718cef)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.047 (goal x0.47 y0.31, render x0.50 y0.35)

## misc_casual-send

4 pictures, 0 passed.

- **attempt 1** `20261010_180824_goal-casual-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, casual_send@v1, request 50740f79e51c)
  - right: pose gate passed every measured item
- **attempt 2** `20261010_180824_goal-casual-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, casual_send@v1, request 50740f79e51c)
  - right: pose gate passed every measured item
- **attempt 3** `20261010_182611_goal-casual-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, casual_send@v2, request 2b13e9da1fac)
  - right: pose gate passed every measured item
- **attempt 4** `20261010_182611_goal-casual-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, casual_send@v2, request 2b13e9da1fac)
  - right: pose gate passed every measured item

## misc_dsc07985-original

5 pictures, 0 passed.

- **attempt 1** `20261010_090126_goal-dsc07985-original/v1_0.png`: **NOT CHECKED YET**, identity 0.55 (Flash, DSC07985_Original@v1, request 3a74e12b6682)
  - right: identity 0.55 (accept band)
- **attempt 2** `20261010_090126_goal-dsc07985-original/v2_0.png`: **NOT CHECKED YET**, identity 0.65 (Flash, DSC07985_Original@v1, request 3a74e12b6682)
  - right: identity 0.65 (accept band)
- **attempt 3** `20261010_090126_goal-dsc07985-original/v3_0.png`: **NOT CHECKED YET**, identity 0.64 (Flash, DSC07985_Original@v1, request 3a74e12b6682)
  - right: identity 0.64 (accept band)
- **attempt 4** `20261010_090126_goal-dsc07985-original/v4_0.png`: **NOT CHECKED YET**, identity 0.73 (Flash, DSC07985_Original@v1, request 3a74e12b6682)
  - right: identity 0.73 (accept band)
- **attempt 5** `20261010_090126_goal-dsc07985-original/v5_0.png`: **NOT CHECKED YET**, identity 0.69 (Flash, DSC07985_Original@v1, request 3a74e12b6682)
  - right: identity 0.69 (accept band)

## misc_g2a-cell1-send

2 pictures, 0 passed.

- **attempt 1** `20261014_084658_goal-g2a-cell1-send/v1_0.jpg`: **FAIL (checklist)** (Flash, g2a_cell1_send@v2, request 648e51aad7b3)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | 12/14/29 are the render's gate against the SOURCE CROP (pin 5, headpose -17.4 / -41.0, roll 12.4): the picture reads -24.3 / -32.5 / roll 20.2 (the bow is 8.5 degrees shallower than the crop, the roll 8 degrees larger), so the gate FAILS; it is not the cell test. 21: identity is not measurable on a bowed face (06_measure: none); by eye the nose, brows, ear, beard and skin read as his but this needs the user's eye. The pitch passes the cell with only 0.5 degrees to spare.
  - right: Cell (a) test passes by the numbers: headpose on the picture -24.3 / -32.5 against the cell -20 / -40 (4.3 and 7.5 degrees, limit 8); neutral closed lips, no smile leaked from the E2 reference; colour photograph; cigarette gone; one ear, no ghost outline; hair, beard and chain are his current look. | 22 of 36 checklist items passed, 10 not applicable
- **attempt 2** `20261014_084658_goal-g2a-cell1-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, g2a_cell1_send@v2, request 648e51aad7b3)
  - wrong: pose gate failed: head position shift 0.107 (goal x0.52 y0.48, render x0.60 y0.56); head bow (nose below eye line / eye distance) goal +0.56, render +0.82 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.11; neck/head direction 56 deg off

## misc_g2b3-cell2-send

2 pictures, 0 passed.

- **attempt 1** `20261014_120201_goal-g2b3-cell2-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, g2b3_cell2_send@v1, request 3a3147f7745a)
  - right: pose gate passed every measured item
- **attempt 2** `20261014_120201_goal-g2b3-cell2-send/v2_0.jpg`: **FAIL (checklist)** (Flash, g2b3_cell2_send@v1, request 3a3147f7745a)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | 12 is the render gate against the SOURCE CROP (-5.2 / -25.6): the bow is 5 degrees deeper, not the cell test. 21: the bowed face is not measurable (06_measure none); by eye it reads as his but needs the user's eye. Defects: grey glare patches at the hair's top left carried over from the source's lighting; the warm-orange cast of the 2023 room stays on the skin (item 9 judged against the source, which has it); Gemini's star at the bottom right (about x 822, y 987) must be removed before it becomes a reference. v1 reads -19.2 / -24.3 (yaw 19 degrees off): fails the cell.
  - right: Cell (b) test passes: headpose on the picture -2.7 / -30.7 against the cell 0 / -25 (2.7 and 5.7 degrees, limit 8). Neutral closed lips, chain visible, current beard, one head and the ear pair as in the source, natural skin colour. | 24 of 36 checklist items passed, 10 not applicable

## misc_g2c-cell3-send

2 pictures, 0 passed.

- **attempt 1** `20261014_114657_goal-g2c-cell3-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, g2c_cell3_send@v1, request 47a3735b9c6e)
  - wrong: pose gate failed: head position shift 0.118 (goal x0.52 y0.62, render x0.47 y0.52); head bow (nose below eye line / eye distance) goal +0.46, render +0.79 (bowed lower)
- **attempt 2** `20261014_114657_goal-g2c-cell3-send/v2_0.jpg`: **FAIL (checklist)** (Flash, g2c_cell3_send@v1, request 47a3735b9c6e)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | Cell (c) FAILS the pose test: headpose on the picture +28.2 / -22.4 (v2) and +34.4 / -17.0 (v1) against +25 / -35: the bow was lifted by 22 and 27 degrees (the crop read -44.1, the render came back 12.6 and 18 degrees too shallow), so the pitch is outside the 8-degree limit on both returns. Not a candidate. 21: not measurable on a bowed face.
  - right: Yaw is on target (+28.2 against +25). | 24 of 36 checklist items passed, 10 not applicable

## misc_g2d-cell4-send

2 pictures, 0 passed.

- **attempt 1** `20261014_115204_goal-g2d-cell4-send/v1_0.jpg`: **FAIL (checklist)** (Flash, g2d_cell4_send@v1, request 83e0882b17da)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | 12 is the render gate against the SOURCE CROP (pin 7, -39.5 / -2.3): the turn is 5.6 degrees deeper than the crop, which is the wanted change toward -45, so it is not the cell test. 21: the face is a three-quarter view, identity is not measurable (06_measure none); by eye the nose, brows, ear, beard and skin read as his beside IMG_6861 but it needs the user's eye. Gemini's star sits at the bottom right of the picture (about x 1087, y 760): it must be removed before the picture becomes a reference. v2 was compared by eye: the same quality but turned 6 degrees too far (-51.1).
  - right: Cell (d) test passes: headpose on the picture -45.1 / +2.8 against the cell -45 / 0 (0.1 and 2.8 degrees, limit 8); the second return reads -51.1 / -6.7 (6.1 and 6.7, passes narrowly). Neutral closed lips (no smile from E2), natural skin colour, one ear, phone and hand removed cleanly, current look. | 24 of 36 checklist items passed, 10 not applicable
- **attempt 2** `20261014_115204_goal-g2d-cell4-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, g2d_cell4_send@v1, request 83e0882b17da)
  - wrong: pose gate failed: head position shift 0.075 (goal x0.51 y0.43, render x0.58 y0.47); head bow (nose below eye line / eye distance) goal +0.57, render +0.72 (bowed lower)

## misc_g2e-cell5-send

2 pictures, 0 passed.

- **attempt 1** `20261014_123335_goal-g2e-cell5-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, g2e_cell5_send@v1, request bde733ab3cde)
  - right: pose gate passed every measured item
- **attempt 2** `20261014_123335_goal-g2e-cell5-send/v2_0.jpg`: **FAIL (checklist)** (Flash, g2e_cell5_send@v1, request bde733ab3cde)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive) | Cell (e) FAILS its pose proxy on both returns. The source crop is a rear three-quarter view (headpose -27.2 / -12.7, the ear at about 65 percent of the head from the back of the curls to the nose tip). v2 reads -77.8 / -17.3 / roll 26.0 and v1 -80.3 / -45.3 / roll 57.2, and the ear sits at 45 percent (v2) and 49 percent (v1): the render turned the head 50 degrees toward the camera into a profile, the same move pin 13s smile edit made, so it is not a looking-back-over-the-shoulder cell. 12/14: the render gate and the proxy agree here. 21: identity is not measurable on a profile (06_measure none). Smile match against IMG_6875 was not run (no credits; it also cannot judge a profile). Gemini star at the bottom right.
  - right: A clean right-profile smile with his own beard, curls, ear and chain; natural skin; the smile is broad with teeth. | pose gate passed every measured item | 23 of 36 checklist items passed, 10 not applicable

## misc_g2f-cell6-send

2 pictures, 0 passed.

- **attempt 1** `20261014_155947_goal-g2f-cell6-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, g2f_cell6_send@v1, request bf966ec0f2ad)
  - right: pose gate passed every measured item
- **attempt 2** `20261014_155947_goal-g2f-cell6-send/v2_0.jpg`: **FAIL (checklist)** (Flash, g2f_cell6_send@v1, request bf966ec0f2ad)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | 21: the three-quarter face is not measurable by identity (06_measure none); by eye it reads as his beside IMG_6861 but needs the user's eye. The AI part-by-part smile comparison with IMG_6875 returned no usable answer (the Gemini text calls timed out twice), so 'every part same' is NOT confirmed; the landmark numbers against IMG_6875 are eye_open +22 percent on both (his eyes are rendered wider than in the real smile, which squints more), mouth_open +11 percent (v1 +16), mouth width +4 percent (v1 +2), lift +2 percent (v1 0), brow +4 percent (v1 +6): v2 is closer on four of five. His teeth look even and slightly brighter than in IMG_6875 (check by eye). The face size against the source crop was not measured (the render gate passes). Gemini star at the bottom right to be removed before it becomes a reference.
  - right: Cell (f) test passes: headpose on the picture -29.2 / +0.5 against the cell -30 / 0 (0.8 and 0.5 degrees, limit 8); v1 reads -29.8 / +2.2. The render's own pose gate passes both. A natural broad smile with teeth, smile lines and raised cheeks like IMG_6875; his own beard, curls and chain; natural colour. | pose gate passed every measured item | 25 of 36 checklist items passed, 10 not applicable

## misc_g2f2-cell6p-send

2 pictures, 0 passed.

- **attempt 1** `20261014_174705_goal-g2f2-cell6p-send/v1_0.jpg`: **FAIL (checklist)** (Flash, g2f2_cell6p_send@v1, request e9ff5e5f006d)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | 21: identity is not measurable on a three-quarter face (06_measure none); by eye it reads as his beside IMG_6868 but needs the user's eye. The AI comparison for v1 said eyes = stronger (the outer-corner crinkles and narrowing of the eyes are stronger than in IMG_6875) and match False because of that one part; the landmark eye opening reads +37 percent (v2 +38) so the eye shape differs from the real smile in both directions of measure; mouth_open -2 percent (v2 +13), mouth width +3 (v2 +4), lift +2 (v2 +1), brow +3 (v2 +1). v2 had no usable AI answer (Gemini timed out). Gemini star at the bottom right to be removed before it becomes a reference.
  - right: Cell (f) +30 side test passes: headpose on the picture +33.1 / -1.3 against the cell +30 / 0 (3.1 and 1.3 degrees, limit 8); v2 reads +31.5 / +0.1. No pull toward profile (the +54 neighbour IMG_6862 did not turn the head). AI part-by-part against IMG_6875: cheeks, smile lines, brows, mouth and teeth the same. A natural broad smile, his own beard, curls and chain. | pose gate passed every measured item | 25 of 36 checklist items passed, 10 not applicable
- **attempt 2** `20261014_174705_goal-g2f2-cell6p-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, g2f2_cell6p_send@v1, request e9ff5e5f006d)
  - right: pose gate passed every measured item

## misc_google-2-img-4446

9 pictures, 0 passed.

- **attempt 1** `20261014_085205_goal-google-2-img-4446/v1_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.56 (accept band)
- **attempt 2** `20261014_085205_goal-google-2-img-4446/v2_0.png`: **NOT CHECKED YET**, identity 0.60 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.60 (accept band)
- **attempt 3** `20261014_085205_goal-google-2-img-4446/v3_0.png`: **NOT CHECKED YET**, identity 0.53 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.53 (accept band)
- **attempt 4** `20261014_085205_goal-google-2-img-4446/v4_0.png`: **NOT CHECKED YET**, identity 0.55 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.55 (accept band)
- **attempt 5** `20261014_085205_goal-google-2-img-4446/v5_0.png`: **NOT CHECKED YET**, identity 0.61 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.61 (accept band)
- **attempt 6** `20261014_085205_goal-google-2-img-4446/v6_0.png`: **NOT CHECKED YET**, identity 0.57 (Flash, google-2__IMG_4446@v1, request 1fb416eab1f0)
  - right: identity 0.57 (accept band)
- **attempt 7** `20261014_111701_goal-google-2-img-4446/v1_0.png`: **NOT CHECKED YET**, identity 0.70 (Flash, google-2__IMG_4446@v2, request 1a68dd1f2f71)
  - right: identity 0.70 (accept band)
- **attempt 8** `20261014_111701_goal-google-2-img-4446/v2_0.png`: **NOT CHECKED YET**, identity 0.57 (Flash, google-2__IMG_4446@v2, request 1a68dd1f2f71)
  - right: identity 0.57 (accept band)
- **attempt 9** `20261014_111701_goal-google-2-img-4446/v3_0.png`: **NOT CHECKED YET**, identity 0.66 (Flash, google-2__IMG_4446@v2, request 1a68dd1f2f71)
  - right: identity 0.66 (accept band)

## misc_img-3884

7 pictures, 0 passed.

- **attempt 1** `20261010_123707_goal-img-3884/v1_0.png`: **NOT CHECKED YET**, identity 0.68 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.68 (accept band)
- **attempt 2** `20261010_123707_goal-img-3884/v3_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.56 (accept band)
- **attempt 3** `20261010_123707_goal-img-3884/v4_0.png`: **NOT CHECKED YET**, identity 0.55 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.55 (accept band)
- **attempt 4** `20261010_130644_goal-img-3884/v1_0.png`: **NOT CHECKED YET**, identity 0.62 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.62 (accept band)
- **attempt 5** `20261010_130644_goal-img-3884/v2_0.png`: **NOT CHECKED YET**, identity 0.59 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.59 (accept band)
- **attempt 6** `20261010_130644_goal-img-3884/v3_0.png`: **NOT CHECKED YET**, identity 0.66 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.66 (accept band)
- **attempt 7** `20261010_130644_goal-img-3884/v4_0.png`: **NOT CHECKED YET**, identity 0.63 (Flash, IMG_3884@v1, request f1cdcd631cec)
  - right: identity 0.63 (accept band)

## misc_img-3884-original

6 pictures, 0 passed.

- **attempt 1** `20261010_085046_goal-img-3884-original/v1_0.png`: **NOT CHECKED YET**, identity 0.61 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.61 (accept band)
- **attempt 2** `20261010_085046_goal-img-3884-original/v2_0.png`: **NOT CHECKED YET**, identity 0.75 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.75 (accept band)
- **attempt 3** `20261010_085046_goal-img-3884-original/v3_0.png`: **NOT CHECKED YET**, identity 0.72 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.72 (accept band)
- **attempt 4** `20261010_085046_goal-img-3884-original/v4_0.png`: **NOT CHECKED YET**, identity 0.59 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.59 (accept band)
- **attempt 5** `20261010_085046_goal-img-3884-original/v5_0.png`: **NOT CHECKED YET**, identity 0.60 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.60 (accept band)
- **attempt 6** `20261010_085046_goal-img-3884-original/v6_0.png`: **NOT CHECKED YET**, identity 0.63 (Flash, IMG_3884_Original@v1, request 2363db54a25f)
  - right: identity 0.63 (accept band)

## misc_img-3929-half

5 pictures, 0 passed.

- **attempt 1** `20261010_114904_goal-img-3929-half/v1_0.png`: **NOT CHECKED YET**, identity 0.54 (Flash, IMG_3929_half@v1, request f4a01b383df6)
  - right: identity 0.54 (accept band)
- **attempt 2** `20261010_114904_goal-img-3929-half/v2_0.png`: **NOT CHECKED YET**, identity 0.54 (Flash, IMG_3929_half@v1, request f4a01b383df6)
  - right: identity 0.54 (accept band)
- **attempt 3** `20261010_114904_goal-img-3929-half/v3_0.png`: **NOT CHECKED YET**, identity 0.54 (Flash, IMG_3929_half@v1, request f4a01b383df6)
  - right: identity 0.54 (accept band)
- **attempt 4** `20261010_114904_goal-img-3929-half/v4_0.png`: **NOT CHECKED YET**, identity 0.50 (Flash, IMG_3929_half@v1, request f4a01b383df6)
  - right: identity 0.50 (gray zone, needs a human eye)
- **attempt 5** `20261010_114904_goal-img-3929-half/v5_0.png`: **NOT CHECKED YET**, identity 0.48 (Flash, IMG_3929_half@v1, request f4a01b383df6)
  - right: identity 0.48 (gray zone, needs a human eye)

## misc_img-3929-original

5 pictures, 0 passed.

- **attempt 1** `20261010_091508_goal-img-3929-original/v2_0.png`: **NOT CHECKED YET**, identity 0.63 (Flash, IMG_3929_Original@v1, request d6f8515bc6f8)
  - right: identity 0.63 (accept band)
- **attempt 2** `20261010_091508_goal-img-3929-original/v3_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, IMG_3929_Original@v1, request d6f8515bc6f8)
  - right: identity 0.56 (accept band)
- **attempt 3** `20261010_091508_goal-img-3929-original/v4_0.png`: **NOT CHECKED YET**, identity 0.58 (Flash, IMG_3929_Original@v1, request d6f8515bc6f8)
  - right: identity 0.58 (accept band)
- **attempt 4** `20261010_091508_goal-img-3929-original/v5_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, IMG_3929_Original@v1, request d6f8515bc6f8)
  - right: identity 0.56 (accept band)
- **attempt 5** `20261010_091508_goal-img-3929-original/v6_0.png`: **NOT CHECKED YET**, identity 0.58 (Flash, IMG_3929_Original@v1, request d6f8515bc6f8)
  - right: identity 0.58 (accept band)

## misc_img-3931-half

4 pictures, 0 passed.

- **attempt 1** `20261010_120509_goal-img-3931-half/v1_0.png`: **NOT CHECKED YET**, identity 0.65 (Flash, IMG_3931_half@v1, request f93c11b08498)
  - right: identity 0.65 (accept band)
- **attempt 2** `20261010_120509_goal-img-3931-half/v2_0.png`: **NOT CHECKED YET**, identity 0.63 (Flash, IMG_3931_half@v1, request f93c11b08498)
  - right: identity 0.63 (accept band)
- **attempt 3** `20261010_124559_goal-img-3931-half/v2_0.png`: **NOT CHECKED YET**, identity 0.60 (Flash, IMG_3931_half@v2, request e6c6c773c181)
  - right: identity 0.60 (accept band)
- **attempt 4** `20261010_124559_goal-img-3931-half/v3_0.png`: **NOT CHECKED YET**, identity 0.67 (Flash, IMG_3931_half@v2, request e6c6c773c181)
  - right: identity 0.67 (accept band)

## misc_img-6858

16 pictures, 0 passed.

- **attempt 1** `20261010_045920_goal-img-6858/v1_0.png`: **NOT CHECKED YET**, identity 0.79 (Flash, IMG_6858@v4, request 787fea373178)
  - right: identity 0.79 (accept band)
- **attempt 2** `20261010_045920_goal-img-6858/v2_0.png`: **NOT CHECKED YET**, identity 0.80 (Flash, IMG_6858@v4, request 787fea373178)
  - right: identity 0.80 (accept band)
- **attempt 3** `20261010_045920_goal-img-6858/v3_0.png`: **NOT CHECKED YET**, identity 0.80 (Flash, IMG_6858@v4, request 787fea373178)
  - right: identity 0.80 (accept band)
- **attempt 4** `20261010_092648_goal-img-6858/v1_0.png`: **NOT CHECKED YET**, identity 0.81 (Flash, IMG_6858@v5, request 7ce63b2e2ab6)
  - right: identity 0.81 (accept band)
- **attempt 5** `20261010_092648_goal-img-6858/v2_0.png`: **NOT CHECKED YET**, identity 0.81 (Flash, IMG_6858@v5, request 7ce63b2e2ab6)
  - right: identity 0.81 (accept band)
- **attempt 6** `20261010_092648_goal-img-6858/v3_0.png`: **NOT CHECKED YET**, identity 0.81 (Flash, IMG_6858@v5, request 7ce63b2e2ab6)
  - right: identity 0.81 (accept band)
- **attempt 7** `20261010_092648_goal-img-6858/v4_0.png`: **NOT CHECKED YET**, identity 0.78 (Flash, IMG_6858@v5, request 7ce63b2e2ab6)
  - right: identity 0.78 (accept band)
- **attempt 8** `20261010_123208_goal-img-6858/v1_0.png`: **NOT CHECKED YET**, identity 0.89 (Flash, IMG_6858@v6, request b64f99ec2b1d)
  - right: identity 0.89 (accept band)
- **attempt 9** `20261010_123208_goal-img-6858/v2_0.png`: **NOT CHECKED YET**, identity 0.88 (Flash, IMG_6858@v6, request b64f99ec2b1d)
  - right: identity 0.88 (accept band)
- **attempt 10** `20261010_123208_goal-img-6858/v4_0.png`: **NOT CHECKED YET**, identity 0.88 (Flash, IMG_6858@v6, request b64f99ec2b1d)
  - right: identity 0.88 (accept band)
- **attempt 11** `20261010_123208_goal-img-6858/v5_0.png`: **NOT CHECKED YET**, identity 0.88 (Flash, IMG_6858@v6, request b64f99ec2b1d)
  - right: identity 0.88 (accept band)
- **attempt 12** `20261010_125108_goal-img-6858/v1_0.png`: **NOT CHECKED YET**, identity 0.90 (Flash, IMG_6858@v7, request 98567b5523fb)
  - right: identity 0.90 (accept band)
- **attempt 13** `20261010_125108_goal-img-6858/v2_0.png`: **NOT CHECKED YET**, identity 0.90 (Flash, IMG_6858@v7, request 98567b5523fb)
  - right: identity 0.90 (accept band)
- **attempt 14** `20261010_125108_goal-img-6858/v3_0.png`: **NOT CHECKED YET**, identity 0.90 (Flash, IMG_6858@v7, request 98567b5523fb)
  - right: identity 0.90 (accept band)
- **attempt 15** `20261010_125108_goal-img-6858/v5_0.png`: **NOT CHECKED YET**, identity 0.89 (Flash, IMG_6858@v7, request 98567b5523fb)
  - right: identity 0.89 (accept band)
- **attempt 16** `20261010_125108_goal-img-6858/v6_0.png`: **NOT CHECKED YET**, identity 0.89 (Flash, IMG_6858@v7, request 98567b5523fb)
  - right: identity 0.89 (accept band)

## misc_pin12d-send

6 pictures, 0 passed.

- **attempt 1** `20261014_104657_goal-pin12d-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)
  - right: pose gate passed every measured item
- **attempt 2** `20261014_104657_goal-pin12d-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)
- **attempt 3** `20261014_104657_goal-pin12d-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)
  - right: pose gate passed every measured item
- **attempt 4** `20261014_104657_goal-pin12d-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)
- **attempt 5** `20261014_104657_goal-pin12d-send/v3_0.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)
  - right: pose gate passed every measured item
- **attempt 6** `20261014_104657_goal-pin12d-send/v3_0r.jpg`: **NOT CHECKED YET** (Flash, pin12d_send@v1, request ae1ec5a8d19b)

## misc_pin14janeu-send

2 pictures, 0 passed.

- **attempt 1** `20261011_110209_goal-pin14janeu-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14janeu_send@v1, request 86e43402438c)
  - right: pose gate passed every measured item
- **attempt 2** `20261011_110209_goal-pin14janeu-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14janeu_send@v1, request 86e43402438c)
  - right: pose gate passed every measured item

## misc_pin16fix-face

10 pictures, 0 passed.

- **attempt 1** `20261011_013208_goal-pin16fix-face/v1_0.png`: **NOT CHECKED YET**, identity 0.63 (Flash, pin16fix_face@v1, request e502727ad619)
  - right: identity 0.63 (accept band)
- **attempt 2** `20261011_013208_goal-pin16fix-face/v2_0.png`: **NOT CHECKED YET**, identity 0.58 (Flash, pin16fix_face@v1, request e502727ad619)
  - right: identity 0.58 (accept band)
- **attempt 3** `20261011_013208_goal-pin16fix-face/v3_0.png`: **NOT CHECKED YET**, identity 0.71 (Flash, pin16fix_face@v1, request e502727ad619)
  - right: identity 0.71 (accept band)
- **attempt 4** `20261011_013208_goal-pin16fix-face/v4_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, pin16fix_face@v1, request e502727ad619)
  - right: identity 0.56 (accept band)
- **attempt 5** `20261012_033211_goal-pin16fix-face/v1_0.png`: **FAIL (checklist)**, identity 0.58 (Flash, pin16fix_face@v2, request f2263022a778)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN) | 21: not verifiable as more accurate than the base the user called 'almost there but still not accurate': identity fell 0.684 -> 0.584 and the face changed little; 31: the cheeks read a little fuller and the skin smoother than his photos (cheek_iod 2.41 against his 2.29-2.36, cjwr 1.15 against 1.09-1.13; the scene reading asked for 'smooth and clean skin'). Gates all pass: size 1.038, light dE 3.5, neck gap 7.0
  - right: zone face on the Route G picture with his daylight faces: the size (1.038) and the light (dE 3.5) both inside their gates for the first time on pin 16 | identity 0.58 (accept band) | 29 of 36 checklist items passed, 5 not applicable
- **attempt 6** `20261012_033211_goal-pin16fix-face/v2_0.png`: **NOT CHECKED YET**, identity 0.73 (Flash, pin16fix_face@v2, request f2263022a778)
  - right: identity 0.73 (accept band)
- **attempt 7** `20261012_033211_goal-pin16fix-face/v3_0.png`: **NOT CHECKED YET**, identity 0.50 (Flash, pin16fix_face@v2, request f2263022a778)
  - right: identity 0.50 (gray zone, needs a human eye)
- **attempt 8** `20261012_040156_goal-pin16fix-face/v1_0.png`: **FAIL (checklist)**, identity 0.54 (Flash, pin16fix_face@v3, request 637440654cea)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN) | 21: nearly the same face as the base the user called 'almost there but still not accurate' and as v2 he did not choose ('Neither yet'); identity 0.543 (base 0.684). 31: cheeks a little wide (cheek_iod 2.42 against his 2.29-2.36), jaw 2.15 against 2.04-2.13. Gates pass: size 1.00, light dE 5.5, neck gap 6.0
  - right: identity 0.54 (accept band) | 29 of 36 checklist items passed, 5 not applicable
- **attempt 9** `20261012_040156_goal-pin16fix-face/v2_0.png`: **NOT CHECKED YET**, identity 0.61 (Flash, pin16fix_face@v3, request 637440654cea)
  - right: identity 0.61 (accept band)
- **attempt 10** `20261012_040156_goal-pin16fix-face/v3_0.png`: **NOT CHECKED YET**, identity 0.48 (Flash, pin16fix_face@v3, request 637440654cea)
  - right: identity 0.48 (gray zone, needs a human eye)

## misc_pin16fix-marks-send

2 pictures, 0 passed.

- **attempt 1** `20261011_013419_goal-pin16fix-marks-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin16fix_marks_send@v1, request 76c66dc7351b)
  - right: pose gate passed every measured item
- **attempt 2** `20261011_013419_goal-pin16fix-marks-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin16fix_marks_send@v1, request 76c66dc7351b)
  - right: pose gate passed every measured item

## misc_pin5-stage1

1 pictures, 0 passed.

- **attempt 1** `20261001_221714_replicate_pin5_stage1/not_passing_closest.jpg`: **NOT CHECKED YET**

## misc_pin9build2-send

4 pictures, 0 passed.

- **attempt 1** `20261014_110205_goal-pin9build2-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin9build2_send@v1, request de97954ccde7)
  - wrong: pose gate failed: person found no person in goal
- **attempt 2** `20261014_110205_goal-pin9build2-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin9build2_send@v1, request de97954ccde7)
- **attempt 3** `20261014_110205_goal-pin9build2-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin9build2_send@v1, request de97954ccde7)
  - wrong: pose gate failed: person found no person in goal
- **attempt 4** `20261014_110205_goal-pin9build2-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin9build2_send@v1, request de97954ccde7)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Stage 1 body only again: the head is still the pin man (19, 21, 28, 31 cannot pass). 26/32 FAIL on the measure: ATR bare-arm thickness per torso length, near arm upper 0.272 / forearm 0.165 (v1: 0.286 / 0.172; base 0.273 / 0.181; pin man 0.301 / 0.211) against the target 0.19 / 0.135 and his own 0.169-0.179 / 0.122-0.127: the forearm moved 9 percent, the upper arm not at all, which is above the TODO limit (0.23 / 0.16) for a failed method. The far arm now reads 0.205 / 0.200 (base 0.228 / 0.187). Note the pin man leans toward the camera, so the near upper arm is foreshortened and nearer than the torso; the standing-photo target may not transfer 1:1 (written in F66).
  - right: Both returns pasted back clean (ECC 0.998 and 0.976); head, girl, shelves, calendar and desk untouched; the arms are visibly leaner and longer than the base, the hand lies flat on the folder; the near forearm measures 0.165 (base 0.181). | 24 of 36 checklist items passed, 6 not applicable

## misc_r3-forearm-send

2 pictures, 0 passed.

- **attempt 1** `20261010_173503_goal-r3-forearm-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, r3_forearm_send@v1, request b92a2475e7ae)
  - wrong: pose gate failed: person found no person in goal
- **attempt 2** `20261010_173503_goal-r3-forearm-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, r3_forearm_send@v1, request b92a2475e7ae)
  - wrong: pose gate failed: person found no person in goal

## motorcycle-outfit-men_01_motorcycle-maroon-tee-helmet

1 pictures, 1 passed.

- **attempt 1** `D:\FacecardArchive\outputs_2026-09-29\20260928_pin_final/pin_v1_engine_v1_0.jpg`: **PASS (all 30 items)**
  - right: Inventory run v22 v1_0 + objects-only engine region edit (frame slider, HONDA engine cover, 0 pixels changed outside the crop). Pose gate PASS incl. head bow; every inventory item checked at full zoom: his wheels, road tyres, plain disc, chrome mudguard, round black mirrors, black handguards, fog lamp, frame slider, HONDA engine cover, H'ness badge, brown seat, tank stripe pattern, his helmet (clear visor), his round watch; no watermark. Open detail for the user: the tank's HONDA letters read flatter and whiter than his polished chrome ones. 21 judged from visible features (sunglasses).

## motorcycle-outfit-men_02_porch-reading-smoking-grey-tee

4 pictures, 1 passed.

- **attempt 1** `20260930_234015_goal-pin-783485666539775327/v1_0.jpg`: **FAIL (checklist)**, identity 0.56 (Flash, pin_783485666539775327.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal) | re-audit 2026-10-01 at full zoom: head pitch not as the goal (eyes straight to the camera, chin level; the goal's chin is lowered and the eyes look up at the camera); everything else passes; hands, hair, beard, identity 0.557 checked
  - right: pose gate 11 of 11; hands, book, cigarette, smoke, water bottle, hillside and grey tee faithful to the pin; ASL watermark gone; his curly hair and full beard | pose gate passed every measured item | identity 0.56 (accept band) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 2** `20260930_234015_goal-pin-783485666539775327/v2_0.jpg`: **PASS (all 30 items)**, identity 0.60 (Flash, pin_783485666539775327.json)
  - right: chin lowered and eyes up at the camera as in the pin; both hands clean at zoom; hair, beard and scene faithful; slim forearm; this is the picture that passes | pose gate passed every measured item | identity 0.60 (accept band) | 24 of 30 checklist items passed, 6 not applicable
- **attempt 3** `20260930_234015_goal-pin-783485666539775327/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.50 (Flash, pin_783485666539775327.json)
  - wrong: pose gate failed: size in the frame (torso) x1.10; his right forearm direction 25 deg off; his right hand position shift 0.224 (goal x0.67 y0.70, render x0.46 y0.76)
  - right: identity 0.50 (gray zone, needs a human eye)
- **attempt 4** `20260930_234015_goal-pin-783485666539775327/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity -0.00 (Flash, pin_783485666539775327.json)
  - wrong: pose gate failed: his right hand position shift 0.064 (goal x0.67 y0.70, render x0.62 y0.73)
  - right: identity -0.00 (rejected band, not meaningful when the face is hidden, bowed or in profile)

## motorcycle-outfit-men_03_stairs-white-tank-black-trousers-bag

26 pictures, 1 passed.

- **attempt 1** `20260930_234349_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.06 (Flash, pin_783485666539775340.json)
  - wrong: pose gate failed: his left hand position shift 0.264 (goal x0.32 y0.54, render x0.58 y0.60)
  - right: identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 2** `20260930_234349_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity -0.01 (Flash, pin_783485666539775340.json)
  - wrong: pose gate failed: his left hand position shift 0.321 (goal x0.32 y0.54, render x0.63 y0.61)
  - right: identity -0.01 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 3** `20260930_235828_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (checklist)**, identity 0.06 (Flash, pin_783485666539775340.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | re-audit: the goal's face is completely hidden (crown of the head seen from above, hand over the mouth) but the render shows eyes, nose and mouth (head not bowed enough), and a dark band over the eyes reads as sunglasses the goal does not have
  - right: framing now exact (man at the far left, cut by the edge) after the FRAMING line was added; slim arms; bag, hoodie, red sneaker, stairs, wall and slipper faithful; hands clean | pose gate passed every measured item | identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 20 of 30 checklist items passed, 8 not applicable
- **attempt 4** `20260930_235828_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (checklist)**, identity 0.03 (Flash, pin_783485666539775340.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal) | re-audit: the goal's face is completely hidden but the render shows the eyes, nose and beard: head not bowed enough
  - right: framing exact; bag, hoodie, watch on the wrist, stairs and wall faithful; hands clean | pose gate passed every measured item | identity 0.03 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 5** `20260930_235828_goal-pin-783485666539775340/v3_0.jpg`: **NOT CHECKED YET**, identity 0.05 (Flash, pin_783485666539775340.json)
  - right: pose gate passed every measured item | identity 0.05 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 6** `20260930_235828_goal-pin-783485666539775340/v4_0.jpg`: **FAIL (checklist)**, identity 0.03 (Flash, pin_783485666539775340.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 3 re-run v4: pose gate PASS, framing right, but the arm and shoulder keep the goal man's muscular build (seen on the review sheet)
  - right: framing exact; pose gate passed; scene faithful | pose gate passed every measured item | identity 0.03 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 7** `20261001_041045_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539775340_v2.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | regeneration 1: pose gate PASS and the framing is right (man at the left, bag, stairs), slim arms, hands fine; but a dark band across the eyes reads as sunglasses the goal does not have (face hidden in the goal), despite the no-glasses wording
  - right: pose gate passed; framing exact; slim arms, bag, stairs faithful; hands clean | pose gate passed every measured item | 21 of 30 checklist items passed, 8 not applicable
- **attempt 8** `20261001_041045_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.08 (Flash, pin_783485666539775340_v2.json)
  - wrong: pose gate failed: his left hand position shift 0.283 (goal x0.32 y0.54, render x0.60 y0.59)
  - right: identity 0.08 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 9** `20261001_041045_goal-pin-783485666539775340/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.04 (Flash, pin_783485666539775340_v2.json)
  - wrong: pose gate failed: his left hand position shift 0.063 (goal x0.32 y0.54, render x0.37 y0.58)
  - right: identity 0.04 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 10** `20261001_041558_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (checklist)**, identity 0.08 (Flash, pin_783485666539775340_v3.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | borderline: the eye region under the curls is a deep dark band; at 2.6x zoom it reads as shadow (no frame or nose pads seen) but cannot be proven not to be sunglasses, which the goal does not have; nose and mouth are visible where the goal's hand hides them
  - right: best of this goal so far: pose gate passed; framing exact (man at the far left, cut by the edge); head bowed with the curls leading; slim arms; both hands clean; bag, hoodie, red sneaker, stairs, wall and slipper faithful | pose gate passed every measured item | identity 0.08 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 11** `20261001_041558_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (checklist)**, identity 0.01 (Flash, pin_783485666539775340_v3.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | clear dark sunglasses over the eyes although the prompt said no glasses (the goal's dark face area gets read as sunglasses)
  - right: pose gate passed; framing exact; slim arms; hands clean; scene faithful | pose gate passed every measured item | identity 0.01 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 12** `20261001_041558_goal-pin-783485666539775340/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.00 (Flash, pin_783485666539775340_v3.json)
  - wrong: pose gate failed: his left hand position shift 0.305 (goal x0.32 y0.54, render x0.59 y0.68)
  - right: identity 0.00 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 13** `20261001_041558_goal-pin-783485666539775340/v4_0.jpg`: **FAIL (checklist)**, identity 0.07 (Flash, pin_783485666539775340_v3.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | dark sunglasses over the eyes again
  - right: pose gate passed; framing exact; scene faithful; hands clean | pose gate passed every measured item | identity 0.07 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 14** `20261001_043444_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539775340_v4.json)
  - wrong: pose gate failed: his left hand position shift 0.292 (goal x0.32 y0.54, render x0.59 y0.65)
- **attempt 15** `20261001_043444_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.10 (Flash, pin_783485666539775340_v4.json)
  - wrong: pose gate failed: his left hand position shift 0.095 (goal x0.32 y0.54, render x0.40 y0.59)
  - right: identity 0.10 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 16** `20261001_063344_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (checklist)**, identity -0.06 (Flash, pin_783485666539775340_v4.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | the shoulders and upper arms are still the goal man's heavy, rounded muscle (thicker than his arm photos IMG_0440 / IMG_6923)
  - right: the eyes-open-under-the-curls wording fixed the sunglasses: no glasses, eyes in the shadow of his curls; framing and pose exact (pose gate passed); cigarette hand, bag, hoodie, red sneaker, earring, stairs and wall faithful | pose gate passed every measured item | identity -0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 8 not applicable
- **attempt 17** `20261001_063344_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.06 (Flash, pin_783485666539775340_v4.json)
  - wrong: pose gate failed: his left hand position shift 0.275 (goal x0.32 y0.54, render x0.59 y0.60)
  - right: identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 18** `20261001_063344_goal-pin-783485666539775340/v3_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539775340_v4.json)
  - wrong: pose gate failed: his left hand position shift 0.063 (goal x0.32 y0.54, render x0.38 y0.57)
- **attempt 19** `20261001_064643_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.11 (Flash, pin_783485666539775340_v5.json)
  - wrong: pose gate failed: his left hand position shift 0.072 (goal x0.32 y0.54, render x0.38 y0.58)
  - right: identity 0.11 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 20** `20261001_064643_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.04 (Flash, pin_783485666539775340_v5.json)
  - wrong: pose gate failed: his left hand position shift 0.129 (goal x0.32 y0.54, render x0.45 y0.57)
  - right: identity 0.04 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 21** `20261001_065356_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539775340_v5.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | Pro still draws the goal man's thick rounded deltoids and biceps; the eyes sit in a dark shadow band under the curls (no frame visible, but close to the sunglasses look)
  - right: pose gate passed; framing, cigarette hand, bag, hoodie, red sneaker, stairs and wall faithful; his curls | pose gate passed every measured item | 21 of 30 checklist items passed, 8 not applicable
- **attempt 22** `20261001_065356_goal-pin-783485666539775340/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.08 (Pro, pin_783485666539775340_v5.json)
  - wrong: pose gate failed: his left hand position shift 0.080 (goal x0.32 y0.54, render x0.37 y0.60)
  - right: identity 0.08 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 23** `20261001_065356_goal-pin-783485666539775340/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.01 (Pro, pin_783485666539775340_v5.json)
  - wrong: pose gate failed: his left hand position shift 0.075 (goal x0.32 y0.54, render x0.40 y0.54)
  - right: identity 0.01 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 24** `20261001_071557_goal-pin-783485666539775340/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.07 (Flash, pin_783485666539775340_v6.json)
  - wrong: pose gate failed: his left hand position shift 0.117 (goal x0.32 y0.54, render x0.43 y0.58)
  - right: identity 0.07 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 25** `20261001_071557_goal-pin-783485666539775340/v2_0.jpg`: **PASS (all 30 items)**, identity 0.10 (Flash, pin_783485666539775340_v6.json)
  - right: the slim-build line with its VISIBLE CONSEQUENCE (tank-top armholes gape around thin arms, straps wide of narrow shoulders) finally gave his build: thin arms, narrow shoulders; pose gate passed; framing exact; cigarette hand, bag, hoodie, red sneaker, chain, stairs and wall faithful; first pin 3 picture to pass every item | pose gate passed every measured item | identity 0.10 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 8 not applicable
- **attempt 26** `20261001_071557_goal-pin-783485666539775340/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.12 (Flash, pin_783485666539775340_v6.json)
  - wrong: pose gate failed: his left hand position shift 0.094 (goal x0.32 y0.54, render x0.41 y0.58)
  - right: identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile)

## motorcycle-outfit-men_04_mirror-camera-selfie-shirtless

30 pictures, 5 passed.

- **attempt 1** `20260930_234557_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050.json)
  - wrong: pose gate failed: size in the frame (shoulders-to-nose x2.2) x1.20
- **attempt 2** `20260930_234557_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777050.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | re-audit: the raised arm and chest keep the goal man's deep muscle separation and striations, more than his arm photo IMG_0440 and his body photo IMG_6923 show; scene, camera, strap, hair and beard pass
  - right: the very close crop is exact: blurred raised hand, camera, leather strap, dark band, panel; his curls at the top and his dark beard under the camera | pose gate passed every measured item | 20 of 30 checklist items passed, 9 not applicable
- **attempt 3** `20260930_234557_goal-pin-783485666539777050/v3_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.047 (goal x0.38 y0.70, render x0.42 y0.71)
- **attempt 4** `20260930_234557_goal-pin-783485666539777050/v4_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777050.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | re-audit: the raised arm and chest keep the goal man's deep muscle separation and striations, more than his arm photo IMG_0440 and his body photo IMG_6923 show; scene, camera, strap, hair and beard pass
  - right: same exact crop, strap and camera; his curls and beard; hands clean | pose gate passed every measured item | 20 of 30 checklist items passed, 9 not applicable
- **attempt 5** `20261001_041045_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v2.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.084 (goal x0.38 y0.70, render x0.46 y0.71); head position shift 0.054 (goal x0.45 y0.54, render x0.50 y0.55); head bow (nose below eye line / eye distance) goal +0.45, render +0.32 (more level, chin up); neck/head direction 15 deg off; his left upper arm direction 15 deg off
- **attempt 6** `20261001_041045_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v2.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.060 (goal x0.38 y0.70, render x0.43 y0.73); head bow (nose below eye line / eye distance) goal +0.45, render +0.35 (more level, chin up); size in the frame (shoulders-to-nose x2.2) x1.13
- **attempt 7** `20261001_041422_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v3.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.048 (goal x0.38 y0.70, render x0.39 y0.75); size in the frame (shoulders-to-nose x2.2) x1.15
- **attempt 8** `20261001_041422_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v3.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.048 (goal x0.38 y0.70, render x0.39 y0.75); size in the frame (shoulders-to-nose x2.2) x1.25
- **attempt 9** `20261001_041846_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v4.json)
  - wrong: pose gate failed: head position shift 0.046 (goal x0.45 y0.54, render x0.48 y0.56); size in the frame (shoulders-to-nose x2.2) x1.08
- **attempt 10** `20261001_041846_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v4.json)
  - wrong: pose gate failed: size in the frame (shoulders-to-nose x2.2) x1.10
- **attempt 11** `20261001_063340_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v5.json)
  - wrong: pose gate failed: size in the frame (shoulders-to-nose x2.2) x0.88
- **attempt 12** `20261001_063340_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050_v5.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.060 (goal x0.38 y0.70, render x0.43 y0.73); head position shift 0.046 (goal x0.45 y0.54, render x0.49 y0.56); his left upper arm direction 16 deg off
- **attempt 13** `20261001_063344_goal-pin-783485666539777050/v1_0.jpg`: **SUPERSEDED by v1_0s.jpg** (Pro, pin_783485666539777050_v5.json)
  - right: Pro model with the measured FRAMING line (nose at 54 percent, shoulder line at 70 percent) and the slim-arm wording: pose gate passed for the first time on this pin; close crop, blurred raised hand, camera, leather strap, dark band and panel exact; his curls and dark beard | pose gate passed every measured item | 21 of 30 checklist items passed, 9 not applicable
- **attempt 14** `20261001_063344_goal-pin-783485666539777050/v1_0s.jpg`: **PASS (accepted by the user)** (Pro, pin_783485666539777050_v5.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 36 (His janeu and chain) | v1_0.jpg of 2026-10-01 with only Gemini's sparkle mark filled from the wall around it (2,970 px, 0.3% of the frame; every other pixel byte-identical). The pose gate today: PASS (head 0.013, shoulders 0.028, x1.06). 21: the camera hides his face as in the pin; 36: no janeu (the picture predates the janeu rule); 19/26/28/31/32: the old slim build and the 10-01 references, not compared at the same scale (unverified) | the user accepted it anyway: the user, 2026-10-20/21: 'an exception could be made' (to the goal-likeness rule) and, of this sparkle-free copy, 'Replace it (Recommended)'
  - right: the user's exception: 'it still shows my personality better than the rest' | 35 of 38 checklist items passed, 1 not applicable
- **attempt 15** `20261001_063344_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777050_v5.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.087 (goal x0.38 y0.70, render x0.44 y0.76); size in the frame (shoulders-to-nose x2.2) x1.14
- **attempt 16** `20261013_230157_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050@v1, request 6c0dbd393122)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.118 (goal x0.38 y0.70, render x0.46 y0.62); head position shift 0.119 (goal x0.45 y0.54, render x0.49 y0.42); size in the frame (shoulders-to-nose x2.2) x1.18; his left hand position shift 0.169 (goal x0.63 y0.48, render x0.77 y0.38)
- **attempt 17** `20261013_230157_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777050@v1, request 6c0dbd393122)
  - wrong: pose gate failed: size in the frame (shoulders-to-nose x2.2) x1.12
- **attempt 18** `20261013_230157_goal-pin-783485666539777050/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777050@v1, request 6c0dbd393122)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 34 (Text in the picture); 36 (His janeu and chain) | 29: the pose gate's only fail: size x1.12 (limit 1.07); everything else passes (body 0.014, head 0.006, arms 2-3 deg, hand 0.021); 34: the camera's lettering reads FUJIFILM the normal way round where the pin's is mirror-reversed; 36: the janeu is one thin line from the picture-left shoulder (right side) but slants more than his reference and crosses the chain's left arm; 32: the chest reads leaner and flatter than pumped_front.jpg in the dim light (by eye, no scale measurement); 21/31 not compared at one scale. A Pro run is queued (pin4pro)
  - right: 25 of 36 checklist items passed, 5 not applicable
- **attempt 19** `20261014_024122_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (checklist)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture); 35 (Candid capture look); 36 (His janeu and chain) | Pro v1_0: the pose gate fails only head bow (nose below the eye line +0.54, the pin +0.45, tolerance 0.08); the restore REFUSED it (re-framed, shift 0.049 of the frame), so the pin's own room, camera plate and sparkle are not restored; Gemini's sparkle star shows bottom right; by eye: his curls, beard, silver chain with pendant, a thin thread down the chest, the camera and arms close to the pin; none of 19-36 compared at one scale on an unrestored picture (unverified = fail); a second Pro run (pin4pro2, 4 samples) is queued
  - right: 20 of 36 checklist items passed, 5 not applicable
- **attempt 20** `20261014_024122_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.074 (goal x0.38 y0.70, render x0.45 y0.67); head position shift 0.106 (goal x0.45 y0.54, render x0.52 y0.46); head bow (nose below eye line / eye distance) goal +0.45, render +0.54 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.23; his left upper arm direction 17 deg off; his left hand position shift 0.112 (goal x0.63 y0.48, render x0.73 y0.42)
- **attempt 21** `20261014_073157_goal-pin-783485666539777050/v1_0.jpg`: **FAIL (pose gate, not checked)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.45, render +0.56 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.08
- **attempt 22** `20261014_073157_goal-pin-783485666539777050/v1_0r.jpg`: **NOT CHECKED YET** (pro, pin_783485666539777050@v2, request 678af7c7f026)
- **attempt 23** `20261014_073157_goal-pin-783485666539777050/v2_0.jpg`: **FAIL (pose gate, not checked)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.083 (goal x0.38 y0.70, render x0.45 y0.67); head position shift 0.109 (goal x0.45 y0.54, render x0.51 y0.45); size in the frame (shoulders-to-nose x2.2) x1.23; his left upper arm direction 30 deg off; his left hand position shift 0.100 (goal x0.63 y0.48, render x0.72 y0.43)
- **attempt 24** `20261014_073157_goal-pin-783485666539777050/v3_0.jpg`: **FAIL (pose gate, not checked)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: pose gate failed: size in the frame (shoulders-to-nose x2.2) x1.09
- **attempt 25** `20261014_073157_goal-pin-783485666539777050/v3_0r.jpg`: **FAIL (checklist)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 34 (Text in the picture) | 29: size in the frame x1.09 (limit 0.93-1.07), measured, not explained away. 21: the camera hides eyes and nose as in the goal; no face is found, so there is no identity score and hair, beard, jaw, ear and skin match by eye only: needs the user's eye. 34: the lettering on the camera's plate is mirror-reversed FUJIFILM in the goal (mirror shot); in the render the 8 glyphs are soft and not in the same orientation, so it is unverifiable (camera_plate_zoom2.jpg); the leather strap carries no text. Also seen at 4x (left_edge.jpg): along the left edge below the raised arm the render shows a 12 px sliver of light wall where the pin's arm reaches the edge (the arm outline is about 12 px narrower than the pin's there); the pose gate arm angles pass.
  - right: Pose gate: every limb, head position (0.010), bow (+0.45 vs +0.46), neck direction, forearm and hand within the limits; only the size in the frame misses (x1.09 against 0.93-1.07). Background restored; Gemini sparkle absent; face light 1.27 and face/neck 1.27 measured OK; body reads pumped with the biceps vein; janeu and chain there. | 27 of 36 checklist items passed, 6 not applicable
- **attempt 26** `20261014_073157_goal-pin-783485666539777050/v4_0.jpg`: **FAIL (pose gate, not checked)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.060 (goal x0.38 y0.70, render x0.44 y0.68); head position shift 0.086 (goal x0.45 y0.54, render x0.50 y0.47); size in the frame (shoulders-to-nose x2.2) x1.32; his left forearm direction 17 deg off; his left hand position shift 0.124 (goal x0.63 y0.48, render x0.75 y0.44)
- **attempt 27** `20261019_154219_goal-pin-783485666539777050/v1_0.jpg`: **PASS (accepted by the user)** (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | 12/14/29/30: the pose gate: shoulders 0.124 and head 0.109 higher than the pin's, neck 15 deg, left upper arm 21 deg, left hand 0.148 off; 37: Gemini re-framed the picture (the background copy refused it: re-framed / no person mask), so the background is Gemini's and the sparkle mark stays; 21: the camera hides his face as in the pin (no identity score to rely on); 34: the camera's lettering is garbled; 19/26/28/31/32 not compared at the same scale (unverified) | the user accepted it anyway: the user, 2026-10-20 (question box): 'keep both but try again to frame it properly only after first debugging why it happened'
  - right: one whole render on Pro: his curls and beard, the pumped torso, the janeu and the chain, the camera pose of the pin | 30 of 38 checklist items passed, 1 not applicable
- **attempt 28** `20261019_154219_goal-pin-783485666539777050/v2_0.jpg`: **PASS (accepted by the user)**, identity 0.43 (pro, pin_783485666539777050@v2, request 678af7c7f026)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | 12/14/29/30: the pose gate: shoulders 0.152 and head 0.165 higher, drawn x1.27 larger, the left hand 0.246 off (a wave instead of the pin's hand on the wall); 37: Gemini re-framed the picture (the background copy refused it: re-framed / no person mask), so the background is Gemini's and the sparkle mark stays; 21: the camera hides his face as in the pin (no identity score to rely on); 34: the camera's lettering is garbled; 19/26/28/31/32 not compared at the same scale (unverified) | the user accepted it anyway: the user, 2026-10-20 (question box): 'keep both but try again to frame it properly only after first debugging why it happened'
  - right: one whole render on Pro: his curls and beard, the pumped torso, the janeu and the chain, the camera pose of the pin | identity 0.43 (gray zone, needs a human eye) | 30 of 38 checklist items passed, 1 not applicable
- **attempt 29** `20261020_192346_goal-pin-783485666539777050/v1_0.jpg`: **PASS (accepted by the user)** (pro, pin_783485666539777050@v3, request 3e007aacbdbb)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | 12/14/29/30 (the pose gate): head 0.067 higher, shoulders 0.058 right, nose-to-shoulders x1.34, the camera hand 0.101 higher: his head upright above the camera where the pin's man ducks behind it; 37: re-framed, so the background copy refused it (ECC under 0.8) and Gemini's sparkle mark stays; 21: the camera hides his face as in the pin; 34: the camera's lettering is garbled; 19/26/28/31/32 not compared at the same scale (unverified) | the user accepted it anyway: the user, 2026-10-21 (question box): 'Keep both' (the v3 fix renders, an exception to the exact-pose rule: 'almost seem perfect')
  - right: recipe v3 (FAILURE_LOG F74): the shoulder line back at the pin's height (0.68-0.71 against 0.70) once the build wording named only what the frame shows | 30 of 38 checklist items passed, 1 not applicable
- **attempt 30** `20261020_192346_goal-pin-783485666539777050/v2_0.jpg`: **PASS (accepted by the user)** (pro, pin_783485666539777050@v3, request 3e007aacbdbb)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | 12/14/29/30 (the pose gate): head 0.089 higher, shoulders 0.067 right, nose-to-shoulders x1.29, the camera hand 0.131 higher: his head upright above the camera where the pin's man ducks behind it; 37: re-framed, so the background copy refused it (ECC under 0.8) and Gemini's sparkle mark stays; 21: the camera hides his face as in the pin; 34: the camera's lettering is garbled; 19/26/28/31/32 not compared at the same scale (unverified) | the user accepted it anyway: the user, 2026-10-21 (question box): 'Keep both' (the v3 fix renders, an exception to the exact-pose rule: 'almost seem perfect')
  - right: recipe v3 (FAILURE_LOG F74): the shoulder line back at the pin's height (0.68-0.71 against 0.70) once the build wording named only what the frame shows | 30 of 38 checklist items passed, 1 not applicable

## motorcycle-outfit-men_05_poolside-reading-bw

37 pictures, 2 passed.

- **attempt 1** `20260930_234859_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.21 (Flash, pin_783485666539777054.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | pin 5 poolside reader B&W: pose gate PASS; tattoos removed, sunglasses/phone/lighter/ring kept; identity score 0.21/0.18/0.14 (v1/v3/v4) is in the gray zone (bowed head, black and white), hair and beard match by eye at zoom but the number cannot confirm it: needs the user's eye; Gemini sparkle on the paper bottom-right left as produced
  - right: head bow 0.50 = the pin's 0.50; black-and-white grade kept; forearm tattoos gone; ring, sunglasses, phone, lighter and cigarette kept; hair and beard look like his | pose gate passed every measured item | identity 0.21 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 2** `20260930_234859_goal-pin-783485666539777054/v3_0.jpg`: **FAIL (checklist)**, identity 0.16 (Flash, pin_783485666539777054.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | pin 5 poolside reader B&W: pose gate PASS; tattoos removed, sunglasses/phone/lighter/ring kept; identity score 0.21/0.18/0.14 (v1/v3/v4) is in the gray zone (bowed head, black and white), hair and beard match by eye at zoom but the number cannot confirm it: needs the user's eye; Gemini sparkle on the paper bottom-right left as produced
  - right: head bow 0.50 = the pin's; black-and-white grade, tattoos gone, objects kept; fullest curls of the three | pose gate passed every measured item | identity 0.16 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 3** `20260930_234859_goal-pin-783485666539777054/v4_0.jpg`: **FAIL (checklist)**, identity 0.13 (Flash, pin_783485666539777054.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | pin 5 poolside reader B&W: pose gate PASS; tattoos removed, sunglasses/phone/lighter/ring kept; identity score 0.21/0.18/0.14 (v1/v3/v4) is in the gray zone (bowed head, black and white), hair and beard match by eye at zoom but the number cannot confirm it: needs the user's eye; Gemini sparkle on the paper bottom-right left as produced
  - right: head bow 0.49 = the pin's; hair falls over the forehead like the pin's; tattoos gone | pose gate passed every measured item | identity 0.13 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 4** `20261001_041044_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.49 (Pro, pin_783485666539777054_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.495 is in the gray zone (best of all pin 5 samples, still below the 0.52 accept line, needs a human eye); the ring on his finger in the pin is missing
  - right: Pro model: best face of the pin 5 samples (clear lean face, full dark beard and curls like his); pose gate passed; head bow matches the pin; black-and-white grade, tattoos gone, sunglasses, phone, lighter, cigarette and pack kept; hands clean | pose gate passed every measured item | identity 0.49 (gray zone, needs a human eye) | 21 of 30 checklist items passed, 7 not applicable
- **attempt 5** `20261001_041044_goal-pin-783485666539777054/v2_0.jpg`: **NOT CHECKED YET**, identity 0.35 (Pro, pin_783485666539777054_v2.json)
  - right: pose gate passed every measured item | identity 0.35 (gray zone, needs a human eye)
- **attempt 6** `20261001_041044_goal-pin-783485666539777054/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.10 (Pro, pin_783485666539777054_v2.json)
  - wrong: pose gate failed: his left forearm direction 108 deg off; his left hand position shift 0.245 (goal x0.49 y0.79, render x0.68 y0.63)
  - right: identity 0.10 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 7** `20261001_041044_goal-pin-783485666539777054/v4_0.jpg`: **NOT CHECKED YET**, identity 0.25 (Pro, pin_783485666539777054_v2.json)
  - right: pose gate passed every measured item | identity 0.25 (gray zone, needs a human eye)
- **attempt 8** `20261001_043444_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.34 (Pro, pin_783485666539777054_v3.json)
  - wrong: pose gate failed: neck/head direction 16 deg off
  - right: identity 0.34 (gray zone, needs a human eye)
- **attempt 9** `20261001_043444_goal-pin-783485666539777054/v2_0.jpg`: **FAIL (checklist)**, identity 0.19 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity 0.193 (rejected band; the Pro face this time is not him)
  - right: pose gate passed; ring kept after naming it; black-and-white scene and objects faithful | pose gate passed every measured item | identity 0.19 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 10** `20261001_063341_goal-pin-783485666539777054/v3_0.jpg`: **FAIL (checklist)**, identity 0.39 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity 0.392 is in the gray zone (needs a human eye); Pro returned only one of three pictures in this run
  - right: pose gate passed; black-and-white scene and objects faithful | pose gate passed every measured item | identity 0.39 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 11** `20261001_064639_goal-pin-783485666539777054/v1_0.jpg`: **NOT CHECKED YET**, identity 0.03 (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item | identity 0.03 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 12** `20261001_064639_goal-pin-783485666539777054/v2_0.jpg`: **FAIL (checklist)**, identity 0.40 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity 0.403, gray zone (needs a human eye)
  - right: pose gate passed; black-and-white scene and objects faithful (Pro) | pose gate passed every measured item | identity 0.40 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 13** `20261001_113317_goal-pin-783485666539777054/v1_0.jpg`: **NOT CHECKED YET**, identity 0.18 (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item | identity 0.18 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 14** `20261001_113317_goal-pin-783485666539777054/v2_0.jpg`: **FAIL (checklist)**, identity 0.36 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity 0.365 is in the 0.20-0.52 gray zone; the checklist counts what I cannot verify as a fail. By eye at zoom: his curly hair, full dark beard, jaw and nose look like his references, the silver ring is back on the finger (named in the request), tattoos gone, cigarette, sunglasses, phone, lighter, pack and scene faithful. THE USER'S EYE DECIDES THIS ONE after 5 Pro samples (0.495, 0.403, 0.365, 0.194, 0.184)
  - right: pose gate passed, head bow 0.50 = the pin; ring present; every object and the black-and-white grade faithful; the only open item is identity in the gray zone | pose gate passed every measured item | identity 0.36 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 15** `20261001_113317_goal-pin-783485666539777054/v3_0.jpg`: **NOT CHECKED YET** (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item
- **attempt 16** `20261001_113317_goal-pin-783485666539777054/v4_0.jpg`: **NOT CHECKED YET**, identity 0.19 (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item | identity 0.19 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 17** `20261001_114851_goal-pin-783485666539777054/v1_0.jpg`: **NOT CHECKED YET**, identity 0.52 (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item | identity 0.52 (gray zone, needs a human eye)
- **attempt 18** `20261001_114851_goal-pin-783485666539777054/v2_0.jpg`: **NOT CHECKED YET**, identity 0.06 (Pro, pin_783485666539777054_v3.json)
  - right: pose gate passed every measured item | identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 19** `20261001_114851_goal-pin-783485666539777054/v3_0.jpg`: **FAIL (checklist)**, identity 0.73 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 19 (All of the hair is his own); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | THE USER, 2026-10-01: the poolside reading picture is wrong. My diagnosis against the pin and his references: (1) item 9/10 light: the face is lit about 1.7x brighter than the pin's (face-region mean 103 vs 61 of 255): in the pin the hair falls forward and shades the whole upper face, the render shows a clean, evenly lit, beauty-bright face; (2) items 19/28 hair: the render's curls are a bushy cap with long sides covering the ears' top, his references show tight curls with SHORT FADED sides (scalp visible above the ear) and longer curls only at the back; (3) skin is smooth/clean, the pin man is textured with stubble
  - right: pose gate, objects, ring, B&W grade and overall tonal range (mean 132 vs 131, std 63 vs 66) match the pin | pose gate passed every measured item | identity 0.73 (accept band) | 19 of 30 checklist items passed, 7 not applicable
- **attempt 20** `20261001_203506_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.23 (Pro, pin_783485666539777054_v4.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | THE USER, 2026-10-01: none of the three look like him, negative progress in identity retention compared with the previous versions. My earlier pass of item 21 'by eye' was wrong, and so was dismissing the low ArcFace scores (0.23-0.31 on pin 5 against 0.733 for the earlier picture of the same pose) as unusable: the number was a real warning. Suspected cause: I replaced the references-driven wording ('exactly as in the FACE references: same length, density and shape') with my own geometric description of his hair and beard, and added a face-shade line, so the model leaned on my words instead of his photos; the face drawn is leaner and more angular with a heavier, darker beard than his references.
  - right: pose gate passed every measured item | identity 0.23 (gray zone, needs a human eye) | 21 of 30 checklist items passed, 7 not applicable
- **attempt 21** `20261001_213357_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.31 (Pro, pin_783485666539777054_v4.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | THE USER, 2026-10-01: none of the three look like him, negative progress in identity retention compared with the previous versions. My earlier pass of item 21 'by eye' was wrong, and so was dismissing the low ArcFace scores (0.23-0.31 on pin 5 against 0.733 for the earlier picture of the same pose) as unusable: the number was a real warning. Suspected cause: I replaced the references-driven wording ('exactly as in the FACE references: same length, density and shape') with my own geometric description of his hair and beard, and added a face-shade line, so the model leaned on my words instead of his photos; the face drawn is leaner and more angular with a heavier, darker beard than his references.
  - right: pose gate passed every measured item | identity 0.31 (gray zone, needs a human eye) | 21 of 30 checklist items passed, 7 not applicable
- **attempt 22** `20261001_213357_goal-pin-783485666539777054/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.27 (Pro, pin_783485666539777054_v4.json)
  - wrong: pose gate failed: where he stands along the table goal 0.29, render 0.37 of its length from picture-left
  - right: identity 0.27 (gray zone, needs a human eye)
- **attempt 23** `20261001_213357_goal-pin-783485666539777054/v3_0.jpg`: **NOT CHECKED YET** (Pro, pin_783485666539777054_v4.json)
  - right: pose gate passed every measured item
- **attempt 24** `20261001_214525_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777054_v5.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity: the face is hidden under the hair and the shade line, ArcFace finds no face; the six-photo run with the shade/face wording did not retain identity
  - right: pose gate passed | pose gate passed every measured item | 21 of 30 checklist items passed, 7 not applicable
- **attempt 25** `20261001_214537_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.08 (Pro, pin_783485666539777054_v5.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity ArcFace 0.083, the shaded face does not look like him; the 'face exactly as in the references' wording did not help
  - right: pose gate passed | pose gate passed every measured item | identity 0.08 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 26** `20261001_214939_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.01 (Pro, pin_783485666539777054_v3.json)
  - wrong: pose gate failed: neck/head direction 19 deg off
  - right: identity 0.01 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 27** `20261001_214944_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity not retained: the original wording with SIX face photos (instead of four) gave ArcFace 0.01 / none / 0.12 on pin 5 (baseline Pro n=11 mean 0.31): more reference photos did NOT help and may dilute the likeness
  - right: pose gate passed | pose gate passed every measured item | 22 of 30 checklist items passed, 7 not applicable
- **attempt 28** `20261001_214949_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.12 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | identity not retained: the original wording with SIX face photos (instead of four) gave ArcFace 0.01 / none / 0.12 on pin 5 (baseline Pro n=11 mean 0.31): more reference photos did NOT help and may dilute the likeness
  - right: pose gate passed | pose gate passed every measured item | identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 29** `20261002_023554_goal-pin-783485666539777054_3/v1_0.jpg`: **FAIL (checklist)**, identity 0.41 (Pro, pin_783485666539777054_v6.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | overnight experiment 2026-10-02: face about a quarter brighter than the pin's (face light ratio 1.12-1.23, within the limit), original hair/beard wording, default four face photos, Pro. Pipeline identity 0.34-0.41 (gray zone, below 0.52) and the sheet's ArcFace 0.18-0.23 against 0.36 for the old pin 5 v1 (0.733 in the pipeline's own score): a moderately brighter face did NOT recover identity; the old picture with the 1.6x brighter face stays the closest to his references. Awaiting the user's choice by eye.
  - right: pose gate passed; face light within the limit; scene and objects faithful | pose gate passed every measured item | identity 0.41 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 30** `20261002_023554_goal-pin-783485666539777054_2/v1_0.jpg`: **FAIL (checklist)**, identity 0.34 (Pro, pin_783485666539777054_v6.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | overnight experiment 2026-10-02: face about a quarter brighter than the pin's (face light ratio 1.12-1.23, within the limit), original hair/beard wording, default four face photos, Pro. Pipeline identity 0.34-0.41 (gray zone, below 0.52) and the sheet's ArcFace 0.18-0.23 against 0.36 for the old pin 5 v1 (0.733 in the pipeline's own score): a moderately brighter face did NOT recover identity; the old picture with the 1.6x brighter face stays the closest to his references. Awaiting the user's choice by eye.
  - right: pose gate passed; face light within the limit; scene and objects faithful | pose gate passed every measured item | identity 0.34 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 31** `20261002_023554_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.38 (Pro, pin_783485666539777054_v6.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | overnight experiment 2026-10-02: face about a quarter brighter than the pin's (face light ratio 1.12-1.23, within the limit), original hair/beard wording, default four face photos, Pro. Pipeline identity 0.34-0.41 (gray zone, below 0.52) and the sheet's ArcFace 0.18-0.23 against 0.36 for the old pin 5 v1 (0.733 in the pipeline's own score): a moderately brighter face did NOT recover identity; the old picture with the 1.6x brighter face stays the closest to his references. Awaiting the user's choice by eye.
  - right: pose gate passed; face light within the limit; scene and objects faithful | pose gate passed every measured item | identity 0.38 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 32** `20261002_041740_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.26 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | think-again test 2026-10-02: ONLY clean studio photos as face references (IMG_6868, 6858, 6873, 6862; no _fav photos): identity 0.26 / 0.04, baseline 0.31 (n=11): the contaminated _fav reference was NOT the cause
  - right: pose gate passed | pose gate passed every measured item | identity 0.26 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 33** `20261002_041749_goal-pin-783485666539777054/v1_0.jpg`: **FAIL (checklist)**, identity 0.04 (Pro, pin_783485666539777054_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | think-again test 2026-10-02: ONLY clean studio photos as face references (IMG_6868, 6858, 6873, 6862; no _fav photos): identity 0.26 / 0.04, baseline 0.31 (n=11): the contaminated _fav reference was NOT the cause
  - right: pose gate passed | pose gate passed every measured item | identity 0.04 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 7 not applicable
- **attempt 34** `20261002_171750_goal-pin-783485666539777054/v1_0.jpg`: **PASS (accepted by the user)**, identity 0.24 (Pro, pin_783485666539777054_v6.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | 21: bowed face, ArcFace cannot score it (v1_0 0.25, v2_0 0.39); at full zoom the tight curls, full dense beard, nose and brows match his references, but identity is not verifiable by the agent. 26: scene and clothes as in the pin; the physique is mostly hidden by the tee and the table, so his slimmer build is not verifiable by the agent. | the user accepted it anyway: the user, 2026-10-07: both renders great ('the image you generated now was great'; answered Both)
  - right: Light matches the pin (face 1.07x / 1.25x of the pin's, face/neck 0.85 / 0.75 vs the pin's 0.82), so the earlier 'lasso-ed in' complaint is gone; pose gate PASS on all 13 checks; his curls and full beard; cigarette in mouth and hand on the book as in the pin. Method: inventory pin_783485666539777054_v6, Pro e6fa609c3fa255c0, FACE refs three-quarter-left (IMG_6862, IMG_6863, IMG_5850_fav_34left head crop, IMG_6868), BODY IMG_6923 Copy, ARMS IMG_0440_Original. | pose gate passed every measured item | identity 0.24 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 5 not applicable
- **attempt 35** `20261002_171750_goal-pin-783485666539777054/v2_0.jpg`: **PASS (accepted by the user)**, identity 0.39 (Pro, pin_783485666539777054_v6.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | 21: bowed face, ArcFace cannot score it (v1_0 0.25, v2_0 0.39); at full zoom the tight curls, full dense beard, nose and brows match his references, but identity is not verifiable by the agent. 26: scene and clothes as in the pin; the physique is mostly hidden by the tee and the table, so his slimmer build is not verifiable by the agent. | the user accepted it anyway: the user, 2026-10-07: both renders great ('the image you generated now was great'; answered Both)
  - right: Light matches the pin (face 1.07x / 1.25x of the pin's, face/neck 0.85 / 0.75 vs the pin's 0.82), so the earlier 'lasso-ed in' complaint is gone; pose gate PASS on all 13 checks; his curls and full beard; cigarette in mouth and hand on the book as in the pin. Method: inventory pin_783485666539777054_v6, Pro e6fa609c3fa255c0, FACE refs three-quarter-left (IMG_6862, IMG_6863, IMG_5850_fav_34left head crop, IMG_6868), BODY IMG_6923 Copy, ARMS IMG_0440_Original. | pose gate passed every measured item | identity 0.39 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 5 not applicable
- **attempt 36** `20261007_012738_goal-pin-783485666539777054/v1_0.jpg`: **NOT CHECKED YET**, identity 0.37 (Pro, pin_783485666539777054@v1, request 325809ba02e3)
  - right: pose gate passed every measured item | identity 0.37 (gray zone, needs a human eye)
- **attempt 37** `20261007_012738_goal-pin-783485666539777054/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Pro, pin_783485666539777054@v1, request 325809ba02e3)
  - wrong: pose gate failed: neck/head direction 19 deg off
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)

## motorcycle-outfit-men_06_shirtless-pencil-in-mouth-bw

68 pictures, 3 passed.

- **attempt 1** `20260930_235140_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055.json)
  - wrong: failed checklist items: 5 (The head fits the body); 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal) | THE USER, 2026-10-01 (withdrawing the earlier 'sufficient'): the pencil is not in my mouth at all, it is held by my chin in a physically impossible way; my head seems weirdly placed on top of the body; my body has not been changed, the physique is of a different person; not acceptable by our generation rules
  - right: scene, palette, jar of brushes, bracelet and the folded arm match the pin; his curls and beard in profile | 15 of 30 checklist items passed, 7 not applicable
- **attempt 2** `20260930_235140_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal) | pin 6: head bow +0.70 vs +0.61, head shift 0.042, size x1.14; the arm reaches out to the bottom-right where the goal's hand rests clasped at the lower left (item 30 by eye); identity unverified (profile, no face found)
  - right: scene and objects match the pin; his curls and beard in profile | 18 of 30 checklist items passed, 7 not applicable
- **attempt 3** `20260930_235828_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v2.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | pin 6 re-run v1: returned the goal photo almost unchanged (mean abs diff 5.3): still the goal man's face and hair, not him; 'exactly as in the PHOTO TO EDIT' wording made Gemini keep the man. Not a result | LESSON: the wording 'exactly as in the PHOTO TO EDIT' about his head and arms makes Gemini hand back the pin's own man nearly unchanged (mean abs diff to the pin 5.3); the pose gate cannot see this
  - right: pose gate passed every measured item | 19 of 30 checklist items passed, 7 not applicable
- **attempt 4** `20260930_235828_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v2.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | pin 6 re-run: pose gate FAIL head bowed lower (+0.83/+0.75 vs +0.61), size x1.21/x1.23, head shifted; identity unverified (profile)
  - right: 19 of 30 checklist items passed, 7 not applicable
- **attempt 5** `20260930_235828_goal-pin-783485666539777055/v3_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v2.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | pin 6 re-run: pose gate FAIL head bowed lower (+0.83/+0.75 vs +0.61), size x1.21/x1.23, head shifted; identity unverified (profile)
  - right: 19 of 30 checklist items passed, 7 not applicable
- **attempt 6** `20261001_000531_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | pin 6 third attempt: pose gate PASS but the picture is the goal photo nearly unchanged (mean abs diff 6.5): the face and hair are the goal man's, not him | LESSON: same as the earlier pin 6 re-run: the photo is handed back with the pin's own man (mean abs diff 6.5)
  - right: pose gate passed every measured item | 20 of 30 checklist items passed, 7 not applicable
- **attempt 7** `20261001_000531_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v3.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when); 30 (Body posture and action exactly as in the goal) | pin 6 third attempt v2: pose gate PASS, but the face still reads as the goal man's face (identity cannot be scored, profile) and the arm differs from the goal's
  - right: pose gate passed every measured item | 20 of 30 checklist items passed, 7 not applicable
- **attempt 8** `20261001_000531_goal-pin-783485666539777055/v3_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v3.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.075 (goal x0.27 y0.21, render x0.29 y0.28); size in the frame (shoulders-to-nose x2.2) x0.86; neck/head direction 22 deg off
- **attempt 9** `20261001_000531_goal-pin-783485666539777055/v4_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v3.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.054 (goal x0.27 y0.21, render x0.27 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.73 (bowed lower)
- **attempt 10** `20261001_043443_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.087 (goal x0.27 y0.21, render x0.29 y0.29); head position shift 0.100 (goal x0.52 y0.22, render x0.60 y0.28); head bow (nose below eye line / eye distance) goal +0.61, render +1.13 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.17
- **attempt 11** `20261001_043443_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.049 (goal x0.27 y0.21, render x0.25 y0.26); head position shift 0.052 (goal x0.52 y0.22, render x0.56 y0.26); size in the frame (shoulders-to-nose x2.2) x1.13
- **attempt 12** `20261001_063342_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.065 (goal x0.27 y0.21, render x0.27 y0.27); head position shift 0.078 (goal x0.52 y0.22, render x0.59 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.92 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.23
- **attempt 13** `20261001_063342_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: head position shift 0.051 (goal x0.52 y0.22, render x0.56 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.70 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.13
- **attempt 14** `20261001_063344_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.108 (goal x0.27 y0.21, render x0.30 y0.31); head position shift 0.134 (goal x0.52 y0.22, render x0.63 y0.30); head bow (nose below eye line / eye distance) goal +0.61, render +1.20 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.28; neck/head direction 16 deg off
- **attempt 15** `20261001_063344_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v4.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.061 (goal x0.27 y0.21, render x0.27 y0.27); neck/head direction 18 deg off
- **attempt 16** `20261001_064638_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.17 (Pro, pin_783485666539777055_v5.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.612 (goal x0.27 y0.21, render x0.86 y0.34); head position shift 0.240 (goal x0.52 y0.22, render x0.75 y0.29); neck/head direction 156 deg off
  - right: identity 0.17 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 17** `20261001_064638_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v5.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal) | pose gate: size in the frame x1.15 (limit 1.07, head bowed a little lower and closer); the shoulders and arm are still broad and muscular, not his slim build
  - right: fixes two of the user's complaints: the brush is clamped between his lips in his mouth (not against the chin) and the head joins the neck naturally; framing, objects, bracelet and the black-and-white grade match the pin; his curls and beard (Pro, measured FRAMING line) | 21 of 30 checklist items passed, 7 not applicable
- **attempt 18** `20261001_065356_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v6.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.053 (goal x0.27 y0.21, render x0.27 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.69 (bowed lower)
- **attempt 19** `20261001_065356_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v6.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the pose gate passed only because Gemini handed back the pin's own man (mean abs diff to the pin 3.2 for v2, 9.6 for v3): his face, hair and heavy build are the goal man's. LESSON: the wave-4 FRAMING line ('the camera is as close as in the PHOTO TO EDIT ... nose tip only 9 percent below the shoulder line') made Pro keep the whole photo
  - right: nothing new beyond the pin itself | pose gate passed every measured item | 18 of 30 checklist items passed, 7 not applicable
- **attempt 20** `20261001_065356_goal-pin-783485666539777055/v3_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v6.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the pose gate passed only because Gemini handed back the pin's own man (mean abs diff to the pin 3.2 for v2, 9.6 for v3): his face, hair and heavy build are the goal man's. LESSON: the wave-4 FRAMING line ('the camera is as close as in the PHOTO TO EDIT ... nose tip only 9 percent below the shoulder line') made Pro keep the whole photo
  - right: nothing new beyond the pin itself | pose gate passed every measured item | 18 of 30 checklist items passed, 7 not applicable
- **attempt 21** `20261001_071557_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v7.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the pose gate passed because Gemini handed the pin back almost unchanged (mean abs diff to the pin 6.9 / 6.3): the pin man's face, hair and heavy build. LESSON (pin 6, 3 times now): any 'FRAMING exactly ... never closer' line on this goal makes it return the photo; the only real replacements came from the inventory WITHOUT a framing line (size then 1.14-1.15x)
  - right: nothing beyond the pin | pose gate passed every measured item | 18 of 30 checklist items passed, 7 not applicable
- **attempt 22** `20261001_071557_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v7.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the pose gate passed because Gemini handed the pin back almost unchanged (mean abs diff to the pin 6.9 / 6.3): the pin man's face, hair and heavy build. LESSON (pin 6, 3 times now): any 'FRAMING exactly ... never closer' line on this goal makes it return the photo; the only real replacements came from the inventory WITHOUT a framing line (size then 1.14-1.15x)
  - right: nothing beyond the pin | pose gate passed every measured item | 18 of 30 checklist items passed, 7 not applicable
- **attempt 23** `20261001_113317_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.058 (goal x0.27 y0.21, render x0.28 y0.27); head position shift 0.072 (goal x0.52 y0.22, render x0.58 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.74 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.14
- **attempt 24** `20261001_113317_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v8.json)
  - wrong: failed checklist items: 6 (The head and face are his true size); 19 (All of the hair is his own); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | THE USER, 2026-10-01: the shirtless pencil-in-mouth picture is wrong. My diagnosis against the pin and his references: (1) items 19/28 hair: long loose curls hang over the ear and temple like the pin man's, his references show tight curls with short faded sides and the ear and scalp visible; (2) item 28 beard: patchy short stubble on the cheeks with a goatee, like the pin man's, his references show a FULL DENSE dark beard along the whole jaw and cheeks with neat edges; (3) the profile face cannot be scored, so identity was judged by eye and this is what the eye missed
  - right: brush clamped in the mouth, head joined to the neck, lean build, framing and objects, tonal range (mean 76 vs 72) | pose gate passed every measured item | 20 of 30 checklist items passed, 7 not applicable
- **attempt 25** `20261001_113317_goal-pin-783485666539777055/v3_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: head position shift 0.071 (goal x0.52 y0.22, render x0.59 y0.25); head bow (nose below eye line / eye distance) goal +0.61, render +0.89 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.27
- **attempt 26** `20261001_113317_goal-pin-783485666539777055/v4_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.050 (goal x0.27 y0.21, render x0.23 y0.24); size in the frame (shoulders-to-nose x2.2) x1.12
- **attempt 27** `20261001_113318_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.049 (goal x0.27 y0.21, render x0.28 y0.26); head position shift 0.094 (goal x0.52 y0.22, render x0.61 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.76 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.22
- **attempt 28** `20261001_113318_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.102 (goal x0.27 y0.21, render x0.34 y0.28); head position shift 0.064 (goal x0.52 y0.22, render x0.58 y0.25); head bow (nose below eye line / eye distance) goal +0.61, render +0.85 (bowed lower); neck/head direction 18 deg off
- **attempt 29** `20261001_203454_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v9.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.057 (goal x0.27 y0.21, render x0.29 y0.26); head position shift 0.110 (goal x0.52 y0.22, render x0.61 y0.29); head bow (nose below eye line / eye distance) goal +0.61, render +0.80 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.26
- **attempt 30** `20261001_203500_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v9.json)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 29 (The distance from the camera is the same as in the goal) | pose gate failed (head bow / position / size) and the face is lit 1.44x the pin's (108 vs 75)
  - right: THE HAIR AND BEARD FIX WORKED: tight curls with short faded sides and the ear plainly visible, a full dense beard along the jaw, as in his references; brush clamped in his mouth; lean build | 18 of 30 checklist items passed, 7 not applicable
- **attempt 31** `20261001_203500_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v9.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 23 (There is a visible change); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the pin handed back almost unchanged (mean abs diff 5.4): the pin man's face, hair and beard; the pose gate passes it by construction
  - right: nothing beyond the pin | pose gate passed every measured item | 19 of 30 checklist items passed, 7 not applicable
- **attempt 32** `20261001_203945_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v9.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.049 (goal x0.27 y0.21, render x0.28 y0.26); size in the frame (shoulders-to-nose x2.2) x0.93
- **attempt 33** `20261001_203949_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v9.json)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 29 (The distance from the camera is the same as in the goal) | closest so far: pose gate failed only on size (x1.11 vs limit 1.07) and the face is lit 1.35x the pin's (101 vs 75, limit 1.30); the pin's face is shaded
  - right: hair is his (tight curls, short sides, ear visible), beard full and dense along the jaw, brush clamped between the lips, head bow, framing and objects match; real replacement (diff to the pin 20) | 20 of 30 checklist items passed, 7 not applicable
- **attempt 34** `20261001_203954_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v9.json)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 29 (The distance from the camera is the same as in the goal) | pose gate failed (head position, bow, size) and the face is lit 1.44x the pin's
  - right: hair and beard fix visible | 18 of 30 checklist items passed, 7 not applicable
- **attempt 35** `20261001_213326_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v10.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the beard is patchy and sparse (visible skin on the cheeks, like the pin man's), not his full dense beard: item 28; pose gate and face light pass (bow 0.58, size 1.01, face 75 vs 75)
  - right: best measured match to the pin (size 1.01, face brightness identical) and a real replacement; hair on top and the ear are right | pose gate passed every measured item | 21 of 30 checklist items passed, 7 not applicable
- **attempt 36** `20261001_213331_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055_v10.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | THE USER, 2026-10-01: none of the three look like him, negative progress in identity retention compared with the previous versions. My earlier pass of item 21 'by eye' was wrong, and so was dismissing the low ArcFace scores (0.23-0.31 on pin 5 against 0.733 for the earlier picture of the same pose) as unusable: the number was a real warning. Suspected cause: I replaced the references-driven wording ('exactly as in the FACE references: same length, density and shape') with my own geometric description of his hair and beard, and added a face-shade line, so the model leaned on my words instead of his photos; the face drawn is leaner and more angular with a heavier, darker beard than his references.
  - right: pose gate passed every measured item | 21 of 30 checklist items passed, 7 not applicable
- **attempt 37** `20261001_213335_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v10.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.045 (goal x0.27 y0.21, render x0.25 y0.25); head bow (nose below eye line / eye distance) goal +0.61, render +0.80 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.12
- **attempt 38** `20261001_213339_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v11.json)
  - wrong: pose gate failed: head position shift 0.056 (goal x0.52 y0.22, render x0.54 y0.28)
- **attempt 39** `20261001_213343_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v11.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.045 (goal x0.27 y0.21, render x0.29 y0.25); size in the frame (shoulders-to-nose x2.2) x0.90
- **attempt 40** `20261001_213347_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539777055_v11.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.085 (goal x0.27 y0.21, render x0.29 y0.29); head position shift 0.106 (goal x0.52 y0.22, render x0.61 y0.28); head bow (nose below eye line / eye distance) goal +0.61, render +1.06 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.22; neck/head direction 15 deg off
- **attempt 41** `20261001_213352_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.61, render +0.73 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.18
- **attempt 42** `20261001_213352_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v10.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.083 (goal x0.27 y0.21, render x0.24 y0.29); head position shift 0.086 (goal x0.52 y0.22, render x0.58 y0.28); head bow (nose below eye line / eye distance) goal +0.61, render +0.90 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.10
- **attempt 43** `20261001_214539_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v12.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | not confirmed as him (profile, no ArcFace); same references-driven wording as pin 5 which failed identity
  - right: pose gate passed | pose gate passed every measured item | 22 of 30 checklist items passed, 7 not applicable
- **attempt 44** `20261001_214555_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v12.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.078 (goal x0.27 y0.21, render x0.31 y0.27); head position shift 0.069 (goal x0.52 y0.22, render x0.59 y0.24); head bow (nose below eye line / eye distance) goal +0.61, render +0.81 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.08; neck/head direction 18 deg off
- **attempt 45** `20261001_214954_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.054 (goal x0.27 y0.21, render x0.27 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.70 (bowed lower)
- **attempt 46** `20261001_214957_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.073 (goal x0.27 y0.21, render x0.29 y0.28); head position shift 0.075 (goal x0.52 y0.22, render x0.58 y0.27); head bow (nose below eye line / eye distance) goal +0.61, render +1.00 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.12
- **attempt 47** `20261002_023555_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v8.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | overnight sample 2026-10-02 with the ORIGINAL wording (v8), four face photos, Pro: failed the fixed pose gate; identity cannot be scored on a bowed profile, the user chooses by eye
  - right: scene and objects faithful | 20 of 30 checklist items passed, 7 not applicable
- **attempt 48** `20261002_023555_goal-pin-783485666539777055_2/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v8.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | overnight sample 2026-10-02 with the ORIGINAL wording (v8), four face photos, Pro: failed the fixed pose gate; identity cannot be scored on a bowed profile, the user chooses by eye
  - right: scene and objects faithful | 20 of 30 checklist items passed, 7 not applicable
- **attempt 49** `20261002_023555_goal-pin-783485666539777055_2/v2_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055_v8.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | overnight sample 2026-10-02 with the ORIGINAL wording (v8), four face photos, Pro: failed the fixed pose gate; identity cannot be scored on a bowed profile, the user chooses by eye
  - right: scene and objects faithful | 20 of 30 checklist items passed, 7 not applicable
- **attempt 50** `20261002_041757_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.61, render +0.74 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.18
- **attempt 51** `20261002_041802_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: head position shift 0.049 (goal x0.52 y0.22, render x0.56 y0.26); head bow (nose below eye line / eye distance) goal +0.61, render +0.71 (bowed lower); size in the frame (shoulders-to-nose x2.2) x1.11
- **attempt 52** `20261002_042928_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539777055_v8.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.072 (goal x0.27 y0.21, render x0.27 y0.28); neck/head direction 18 deg off
- **attempt 53** `20261007_032810_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055@v1, request 3c69af775481)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | pose gate FAIL 12/14/29: the camera moved back and he is re-centred (grey diff 42 to the pin); face light x1.44 (limit 1.30); identity not scorable on the bowed face
  - right: the pencil is held in his mouth this time; his curls and beard from the current references | 20 of 30 checklist items passed, 5 not applicable
- **attempt 54** `20261007_032810_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Pro, pin_783485666539777055@v1, request 3c69af775481)
  - wrong: failed checklist items: 4 (The face is not lasso-ed and edited in); 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal) | pose gate FAIL 12/14/29 (camera further back, position); face light x1.36; face/neck 1.03 vs the pin's 0.89 reads pasted in; identity not scorable
  - right: the pencil in his mouth; his hair and beard | 18 of 30 checklist items passed, 5 not applicable
- **attempt 55** `20261009_010141_goal-pin-783485666539777055/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055@v2, request f1ec7822cd35)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 06 v2 (character me@v2, Flash): pose gate items 12, 12/14, 14, 29 (the framing and the head moved); grey diff to goal 26.8. Items not looked at closely are listed as failed (unverifiable).
  - right: 17 of 32 checklist items passed, 6 not applicable
- **attempt 56** `20261009_010141_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055@v2, request f1ec7822cd35)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 06 v2 (character me@v2, Flash): pose gate items 12, 12/14, 14, 29; grey diff to goal 22.6. Items not looked at closely are listed as failed (unverifiable).
  - right: 17 of 32 checklist items passed, 6 not applicable
- **attempt 57** `20261013_193206_goal-pin-783485666539777055/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666539777055@v3, request 67f9def36b6e)
  - right: pose gate passed every measured item
- **attempt 58** `20261013_193206_goal-pin-783485666539777055/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055@v3, request 67f9def36b6e)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | stage 1 of 2 by design: body only, the head is still the pin man's (19, 21, 28, 31 cannot pass); the pumped build and the silver chain are in, the pose gate passes, light x1.03; 26/32/36 not yet compared at one scale (the back view needs his_back.jpg beside it); stage 2 (his head by region edit) queued as pin6head
  - right: 24 of 36 checklist items passed, 5 not applicable
- **attempt 59** `20261013_193206_goal-pin-783485666539777055/v4_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055@v3, request 67f9def36b6e)
  - wrong: failed checklist items: 2 (No ghost outline, doubled edge, second hairline, second ear or second collar); 11 (Neck and above do not look copy-pasted); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | whole-picture pose gate FAIL: shoulder midpoint 0.054 (limit 0.04), bow +0.74 against +0.61, size x1.10 (the 10-01 head's own readings: 0.051, +0.75, x1.13); 2/11: a pale halo follows the head outline on the wall, the neck skin is lighter than the shoulder; 26: the pencil crosses the beard below the lower lip instead of sitting between the lips (the very thing the user withdrew his 2026-10-01 approval over: 'pencil held by the chin'); 21/31 identity not scorable in this bowed profile, not compared at one scale; 32/36 the back view not compared beside his_back.jpg
  - right: 21 of 36 checklist items passed, 5 not applicable
- **attempt 60** `20261013_224703_goal-pin6head-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin6head_send@v1, request 75a7d4fa103e)
  - wrong: pose gate failed: person found no person in goal
- **attempt 61** `20261013_224703_goal-pin6head-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin6head_send@v1, request 75a7d4fa103e)
  - wrong: pose gate failed: person found no person in goal
- **attempt 62** `20261013_224703_goal-pin6head-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin6head_send@v1, request 75a7d4fa103e)
  - wrong: failed checklist items: 5 (The head fits the body); 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | whole-picture pose gate FAIL (shoulder midpoint 0.063, head 0.048, size x1.10, head direction 22 deg off); two pencils; a pale wall patch with a hard edge; a seam on the shoulder at x 290; the ear 45 px right and 15 px down from the pin's (FAILURE_LOG F48); the face reads as him; v2 head method queued next
  - right: 21 of 36 checklist items passed, 5 not applicable
- **attempt 63** `20261014_033207_goal-pin6head2-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin6head2_send@v1, request f09a288c1f72)
  - wrong: pose gate failed: person found no person in goal
- **attempt 64** `20261014_033207_goal-pin6head2-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin6head2_send@v1, request f09a288c1f72)
  - wrong: pose gate failed: person found no person in goal
- **attempt 65** `20261021_032452_goal-pin-783485666539777055/v1_0.jpg`: **PASS (accepted by the user)** (Flash, pin_783485666539777055@v4, request e64358a640d4)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 35 (Candid capture look) | run 20261021_032452 (pin 6 v4, one whole render, frame-aware pumped-side-chest wording): pose gate FAIL: head bowed lower than the pin's (+0.86 against +0.61), head 0.055 and shoulders 0.074 off, nose-to-shoulders x1.15, neck 15 deg off; 35: crisper and cleaner than the pin's soft film grain; 21: his face is in shadow and half hidden, identity not measurable: unverified; 19/26/28/31/32 not compared at the same scale (unverified); the sparkle mark stays (busy corner: knife and jar under it) | the user accepted it anyway: the user, 2026-10-21 (question box), of this render: 'this is the better one out of the two renders, but it still does not match the given goal. Somehow, it slightly differs ... (the clarity, the blur, the angle or the sharpness of the face: the chin and nose) ... this still is a very good render regardless. Great improvement from all past renders.'
  - right: his curls, beard, the brush in his mouth, the silver chain and the janeu, the pumped shoulder and arm, the marble floor and the objects as in the pin | 32 of 38 checklist items passed, 1 not applicable
- **attempt 66** `20261021_032452_goal-pin-783485666539777055/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777055@v4, request e64358a640d4)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 35 (Candid capture look) | run 20261021_032452 (pin 6 v4): pose gate FAIL: head 0.103 and shoulders 0.103 lower than the pin's, nose-to-shoulders x1.21; he leans less far forward than the pin's man; 35: crisper and cleaner than the pin's film grain; 21: identity not measurable: unverified; 19/26/28/31/32 not compared (unverified); the sparkle mark stays (busy corner)
  - right: his curls, beard, the brush in his mouth, the chain and the janeu, the pumped arm, the objects on the floor | 32 of 38 checklist items passed, 1 not applicable
- **attempt 67** `20261021_223340_goal-pin-783485666539777055/v1_0.jpg`: **PASS (accepted by the user)** (Flash, pin_783485666539777055@v5, request faf352753ef8)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 35 (Candid capture look) | run 20261021_223340 (pin 6 v5, Flash, one whole render, the sharp-face item and his real profile IMG_6863): pose gate FAIL: head bowed lower than the pin's (+0.90 against +0.61), head 0.126 and shoulders 0.127 off, nose-to-shoulders x1.15, neck 17 deg off; the face is sharp now (jaw, chin and nose crisp, 07_review/face_sharpness_compare.jpg); 35: crisper and cleaner than the pin's soft film grain; 21: his bowed face is not found by the scorer (faces 0), identity not measurable: unverified; 27: the head bow and size misses of v4 are back; 26/32 NOTE: a bowed side pose not compared at the same scale beside the pumped standard (unverified); 30: his hand points a finger at the drawing where the pin's hand rests closed; the sparkle stays (busy corner: knife, plate and cup under it, texture 22.3). | the user accepted it anyway: the user, 2026-10-22 (question box): 'Keep both' for pin 6 v5 (render 1 and render 2)
  - right: the sharp face with the jaw, chin and nose crisp, his curls and beard, the brush in his mouth, the silver chain and the janeu, the pumped shoulder and arm, the marble floor and the objects as in the pin | 26 of 38 checklist items passed, 5 not applicable
- **attempt 68** `20261021_223340_goal-pin-783485666539777055/v2_0.jpg`: **PASS (accepted by the user)** (Flash, pin_783485666539777055@v5, request faf352753ef8)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 35 (Candid capture look) | run 20261021_223340 (pin 6 v5, Flash, one whole render, the sharp-face item and his real profile IMG_6863): pose gate FAIL: head bowed lower than the pin's (+0.81 against +0.61), head 0.124 and shoulders 0.120 off, nose-to-shoulders x1.09 (limit 1.07); the face is sharp now (jaw, chin and nose crisp, 07_review/face_sharpness_compare.jpg); 35: crisper and cleaner than the pin's soft film grain; 21: his bowed face is not found by the scorer (faces 0), identity not measurable: unverified; 27: the head bow and size misses of v4 are back; 26/32 NOTE: a bowed side pose not compared at the same scale beside the pumped standard (unverified); the sparkle stays (busy corner: knife, plate and cup under it, texture 20.1). | the user accepted it anyway: the user, 2026-10-22 (question box): 'Keep both' for pin 6 v5 (render 1 and render 2)
  - right: the sharp face with the jaw, chin and nose crisp, his curls and beard, the brush in his mouth, the silver chain and the janeu, the pumped shoulder and arm, the marble floor and the objects as in the pin | 27 of 38 checklist items passed, 5 not applicable

## motorcycle-outfit-men_07_mirror-selfie-cat-grey-tee-sweatpants

11 pictures, 1 passed.

- **attempt 1** `20260930_235318_goal-pin-783485666539777115/v1_0.jpg`: **FAIL (checklist)**, identity 0.19 (Flash, pin_783485666539777115.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 7 mirror selfie with cat: pose gate PASS, watermark gone; identity 0.188 (looks like a different man), physique still the goal man's huge arms
  - right: watermark gone; mirror, cat, phone and room faithful | pose gate passed every measured item | identity 0.19 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 2** `20260930_235318_goal-pin-783485666539777115/v2_0.jpg`: **FAIL (checklist)**, identity 0.44 (Flash, pin_783485666539777115.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 7: pose gate PASS; identity 0.442 gray zone (needs the user's eye); slimmer arms than the goal but the sweatpants came out blue-grey where the goal's are light grey
  - right: slimmer arms than the pin; identity 0.44 is the best of the round; cat, phone, room faithful | pose gate passed every measured item | identity 0.44 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 3** `20260930_235318_goal-pin-783485666539777115/v3_0.jpg`: **FAIL (checklist)**, identity 0.11 (Flash, pin_783485666539777115.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 7: pose gate PASS; identity 0.106 (not him); goal man's huge arms
  - right: pose and scene faithful | pose gate passed every measured item | identity 0.11 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 4** `20260930_235318_goal-pin-783485666539777115/v4_0.jpg`: **FAIL (checklist)**, identity 0.45 (Flash, pin_783485666539777115.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 7: pose gate PASS; best face of the four, identity 0.454 gray zone (needs the user's eye); physique is still the goal man's thick arms and forearms, not his slim build
  - right: best face of this round (identity 0.454); light-grey sweatpants and the scene faithful | pose gate passed every measured item | identity 0.45 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 5** `20260930_235828_goal-pin-783485666539777115/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.12 (Flash, pin_783485666539777115_v2.json)
  - wrong: pose gate failed: size in the frame (torso) x1.10
  - right: identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 6** `20260930_235828_goal-pin-783485666539777115/v2_0.jpg`: **FAIL (checklist)**, identity 0.12 (Flash, pin_783485666539777115_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 7 re-run: identity 0.089, arms still heavy
  - right: slim-build wording worked on the arms; scene faithful | pose gate passed every measured item | identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 7** `20260930_235828_goal-pin-783485666539777115/v3_0.jpg`: **FAIL (checklist)**, identity 0.14 (Flash, pin_783485666539777115_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | pin 7 re-run: identity 0.150 (not him)
  - right: light-grey sweatpants kept after naming the colour; scene faithful | pose gate passed every measured item | identity 0.14 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 8** `20260930_235828_goal-pin-783485666539777115/v4_0.jpg`: **FAIL (checklist)**, identity 0.59 (Flash, pin_783485666539777115_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | THE USER, 2026-10-01: can work with more clarity in the face; it is very smoothened, hence negative points on identity
  - right: the user: it can work; slim arms, light-grey sweatpants, cat, phone, mirror and room faithful; head bow 0.24 = the pin | pose gate passed every measured item | identity 0.59 (accept band) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 9** `20261001_043443_goal-pin-783485666539777115/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.07 (Flash, pin_783485666539777115_v3.json)
  - wrong: pose gate failed: his right forearm direction 15 deg off
  - right: identity 0.07 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 10** `20261001_043443_goal-pin-783485666539777115/v2_0.jpg`: **NOT CHECKED YET**, identity 0.29 (Flash, pin_783485666539777115_v3.json)
  - right: pose gate passed every measured item | identity 0.29 (gray zone, needs a human eye)
- **attempt 11** `20261001_043443_goal-pin-783485666539777115/v3_0.jpg`: **PASS (all 30 items)**, identity 0.71 (Flash, pin_783485666539777115_v3.json)
  - right: face sharp with real skin texture and individual beard hairs after the sharp-face line was added; identity 0.709 (accept band); pose gate passed; phone hand and cat clean; light-grey sweatpants, mirror, room and dim light as the pin; watermark gone | pose gate passed every measured item | identity 0.71 (accept band) | 24 of 30 checklist items passed, 6 not applicable

## motorcycle-outfit-men_08_mirror-selfie-cat-shirtless

35 pictures, 1 passed.

- **attempt 1** `20260930_235607_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (checklist)**, identity 0.75 (Flash, pin_783485666539777118.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 8 shirtless with cat: pose gate PASS, identity 0.752; physique is still heavily muscular like the goal (big pecs, arms), not his slim build
  - right: highest identity of the project for a foreign pin (0.752); cat, phone, watch, chain, sweatpants and the blue edge light faithful | pose gate passed every measured item | identity 0.75 (accept band) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 2** `20260930_235607_goal-pin-783485666539777118/v2_0.jpg`: **FAIL (checklist)**, identity 0.68 (Flash, pin_783485666539777118.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 8: pose gate PASS, identity 0.680; physique moderately muscular, still broader than his
  - right: identity 0.680; scene, cat, watch and chain faithful | pose gate passed every measured item | identity 0.68 (accept band) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 3** `20260930_235607_goal-pin-783485666539777118/v3_0.jpg`: **FAIL (checklist)**, identity 0.66 (Flash, pin_783485666539777118.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | re-audit: on the body sheet at the same torso scale the chest, shoulders and visible abs are clearly more muscular than his body photo IMG_6923 (flat chest, no abs); face, hands, cat, watch and scene pass, identity 0.659
  - right: identity 0.659; face, hands, cat and scene faithful (only the body was too muscular) | pose gate passed every measured item | identity 0.66 (accept band) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 4** `20260930_235607_goal-pin-783485666539777118/v4_0.jpg`: **FAIL (checklist)**, identity 0.45 (Flash, pin_783485666539777118.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | pin 8: pose gate PASS, identity 0.451 gray zone (needs the user's eye); slimmest body
  - right: slimmest body of the four; scene faithful | pose gate passed every measured item | identity 0.45 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 5** `20261001_041044_goal-pin-783485666539777118/v1_0.jpg`: **NOT CHECKED YET**, identity 0.43 (Flash, pin_783485666539777118_v2.json)
  - right: pose gate passed every measured item | identity 0.43 (gray zone, needs a human eye)
- **attempt 6** `20261001_041044_goal-pin-783485666539777118/v2_0.jpg`: **FAIL (checklist)**, identity 0.63 (Flash, pin_783485666539777118_v2.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 08 v2 under the 32 items (character sheet beside IMG_6923 / IMG_6858 at the same scale): fuller cheeks than his lean face (cheek width +1.1 band widths) (31); the pin man's broad muscular chest and shoulders, upper arms 1.69 eye-distances against his 1.30-1.48 (26, 32). The user, 2026-10-08, on the new same-man checks (31, 32): 'rework them too'. Its 10-01 approval ('the mirror selfie cat s...') is superseded by this.
  - right: pose gate passed every measured item | identity 0.63 (accept band) | 23 of 32 checklist items passed, 6 not applicable
- **attempt 7** `20261001_041044_goal-pin-783485666539777118/v3_0.jpg`: **NOT CHECKED YET**, identity 0.43 (Flash, pin_783485666539777118_v2.json)
  - right: pose gate passed every measured item | identity 0.43 (gray zone, needs a human eye)
- **attempt 8** `20261001_041044_goal-pin-783485666539777118/v4_0.jpg`: **NOT CHECKED YET**, identity 0.39 (Flash, pin_783485666539777118_v2.json)
  - right: pose gate passed every measured item | identity 0.39 (gray zone, needs a human eye)
- **attempt 9** `20261008_231611_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (checklist)**, identity 0.65 (Flash, pin_783485666539777118@v4, request 149af921d340)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 32 (His build, the same in every picture of him) | pin 8 v4 (character me@v1, Flash) sample 1: pose gate items 12/14; the pin man's broad, muscular shoulders and thick arms (arm width 1.62 vs his band 1.30-1.48) (26, 32).
  - right: his face, beard and current tapered curly hair; no six-pack | identity 0.65 (accept band) | 22 of 32 checklist items passed, 6 not applicable
- **attempt 10** `20261008_231611_goal-pin-783485666539777118/v2_0.jpg`: **FAIL (checklist)**, identity 0.73 (Flash, pin_783485666539777118@v4, request 149af921d340)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 32 (His build, the same in every picture of him) | pin 8 v4 sample 2: re-framed closer (grey diff to goal 42), pose gate 14/30, camera distance (29); a softer, heavier chest and thick arms, not his build (arm width 1.65) (26, 32).
  - right: his face and hair | identity 0.73 (accept band) | 21 of 32 checklist items passed, 6 not applicable
- **attempt 11** `20261008_231611_goal-pin-783485666539777118/v3_0.jpg`: **FAIL (checklist)**, identity 0.78 (Flash, pin_783485666539777118@v4, request 149af921d340)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 32 (His build, the same in every picture of him) | pin 8 v4 sample 3: re-framed closer (grey diff 40), pose gate 14/30 (29); heavier chest and thick arms (arm width 1.67) (26, 32).
  - right: his face and hair | identity 0.78 (accept band) | 21 of 32 checklist items passed, 6 not applicable
- **attempt 12** `20261008_231611_goal-pin-783485666539777118/v4_0.jpg`: **FAIL (checklist)**, identity 0.66 (Flash, pin_783485666539777118@v4, request 149af921d340)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 32 (His build, the same in every picture of him) | pin 8 v4 sample 4: pose gate PASS, but shoulders and arms still fuller than his body photo IMG_6923 (arm width 1.67 vs his 1.30-1.48): the build follows the pin's man (26, 32).
  - right: pose gate pass, identity 0.662; his face, beard, current hair; stomach soft like his, no abs: closer to him than every earlier pin 8 render | pose gate passed every measured item | identity 0.66 (accept band) | 24 of 32 checklist items passed, 6 not applicable
- **attempt 13** `20261008_233602_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (checklist)**, identity 0.66 (Flash, pin_783485666539777118@v5, request 7b14921e63ab)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 32 (His build, the same in every picture of him) | pin 8 v5 (body-only pass on v4 sample 4) sample 1: slimmer than v4, but the shoulders stay broad and capped and the upper arms fuller than his body photo IMG_6923 (arm width 1.60 vs his 1.30-1.48) (26, 32).
  - right: pose gate pass, identity 0.664, his face and current hair kept from v4; arms and shoulders visibly slimmer than before; soft stomach like his | pose gate passed every measured item | identity 0.66 (accept band) | 24 of 32 checklist items passed, 6 not applicable
- **attempt 14** `20261008_233602_goal-pin-783485666539777118/v2_0.jpg`: **FAIL (checklist)**, identity 0.64 (Flash, pin_783485666539777118@v5, request 7b14921e63ab)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 32 (His build, the same in every picture of him) | pin 8 v5 sample 2: as sample 1 (arm width 1.60) (26, 32).
  - right: pose gate pass, identity 0.637, slimmer than v4 | pose gate passed every measured item | identity 0.64 (accept band) | 24 of 32 checklist items passed, 6 not applicable
- **attempt 15** `20261009_010222_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (checklist)**, identity 0.64 (Flash, pin_783485666539777118@v6, request c50fa3fe00ca)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 08 v6 (second body pass, character me@v2): pose gate items 14, 29, 30 (the body pass moved the camera distance). Items not looked at closely are listed as failed (unverifiable).
  - right: identity 0.64 (accept band) | 17 of 32 checklist items passed, 6 not applicable
- **attempt 16** `20261009_010222_goal-pin-783485666539777118/v2_0.jpg`: **FAIL (checklist)**, identity 0.66 (Flash, pin_783485666539777118@v6, request c50fa3fe00ca)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 08 v6 (second body pass, character me@v2): pose gate item 29 (camera distance). Items not looked at closely are listed as failed (unverifiable).
  - right: identity 0.66 (accept band) | 19 of 32 checklist items passed, 6 not applicable
- **attempt 17** `20261013_190541_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Flash, pin_783485666539777118@v7, request 13c4a251a9bc)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.079 (goal x0.48 y0.33, render x0.50 y0.41); head position shift 0.043 (goal x0.50 y0.25, render x0.51 y0.29); size in the frame (torso) x1.08; his right forearm direction 57 deg off; his left forearm direction 19 deg off; his left hand position shift 0.188 (goal x0.63 y0.40, render x0.78 y0.52)
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 18** `20261013_190541_goal-pin-783485666539777118/v2_0.jpg`: **NOT CHECKED YET**, identity 0.71 (Flash, pin_783485666539777118@v7, request 13c4a251a9bc)
  - right: pose gate passed every measured item | identity 0.71 (accept band)
- **attempt 19** `20261013_190541_goal-pin-783485666539777118/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777118@v7, request 13c4a251a9bc)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | 19/28: the head came back with the pin man's straight swept hair and bangs, not his tight curls (the approved 2026-10-01 version has them); 21: face and beard are his (identity 0.71) but the hair reads as another man; 36: the janeu hangs nearly vertical down the picture-right side of the stomach instead of one diagonal from the picture-left shoulder (F33/F37/F39 habit); 26/31/32 not yet compared at one scale beside the standards (an intermediate picture: the hair and janeu region edits run first). Pose gate PASS
  - right: 24 of 36 checklist items passed, 5 not applicable
- **attempt 20** `20261013_222656_goal-pin8head-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin8head_send@v1, request 6743f6258467)
  - wrong: pose gate failed: head position shift 0.078 (goal x0.47 y0.77, render x0.54 y0.79); head bow (nose below eye line / eye distance) goal +0.67, render +0.53 (more level, chin up)
- **attempt 21** `20261013_222656_goal-pin8head-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin8head_send@v1, request 6743f6258467)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.67, render +0.58 (more level, chin up)
- **attempt 22** `20261013_223205_goal-pin8janeu-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin8janeu_send@v1, request 76b0e635aae1)
  - right: pose gate passed every measured item
- **attempt 23** `20261013_223205_goal-pin8janeu-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin8janeu_send@v1, request 76b0e635aae1)
  - wrong: failed checklist items: 2 (No ghost outline, doubled edge, second hairline, second ear or second collar); 4 (The face is not lasso-ed and edited in); 11 (Neck and above do not look copy-pasted); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | 2/4/11: a ghost second brow and a light band across the forehead where the redrawn curls meet the old bangs (seen on hair_check.jpg beside the 10-01 best.jpg); the curls are crisper than the soft face; 26/32: by eye bulkier than pumped_front.jpg in the upper arms and chest at one scale (bideltoid_iod 7.24 vs 7.00, +3%); 21/31 not compared at one scale. Pose gate PASS
  - right: 24 of 36 checklist items passed, 5 not applicable
- **attempt 24** `20261013_223205_goal-pin8janeu-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin8janeu_send@v1, request 76b0e635aae1)
  - right: pose gate passed every measured item
- **attempt 25** `20261013_223205_goal-pin8janeu-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin8janeu_send@v1, request 76b0e635aae1)
- **attempt 26** `20261013_223205_goal-pin8janeu-send/v3_0r.jpg`: **FAIL (checklist)** (Flash, pin8janeu_send@v1, request 76b0e635aae1)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | 26/32: the arms and shoulders are far bulkier than pumped_front.jpg at one scale (body_check.jpg: the upper arms are as thick as the pin man's, the deltoids rounder and larger than his standard; bideltoid +3% but the arm mass is the pin man's): the pin man's build leaking through the kept outline. The head (the user-approved 10-01 head), the janeu, the chain, the cat and the room are right; pose gate PASS
  - right: 29 of 36 checklist items passed, 5 not applicable
- **attempt 27** `20261014_071718_goal-pin8build-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin8build_send@v1, request ac1ec1ee826c)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.044 (goal x0.57 y0.25, render x0.56 y0.20)
- **attempt 28** `20261014_071718_goal-pin8build-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin8build_send@v1, request ac1ec1ee826c)
- **attempt 29** `20261014_071718_goal-pin8build-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin8build_send@v1, request ac1ec1ee826c)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.054 (goal x0.57 y0.25, render x0.56 y0.19)
- **attempt 30** `20261014_071718_goal-pin8build-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin8build_send@v1, request ac1ec1ee826c)
- **attempt 31** `20261019_053523_goal-pin-783485666539777118/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.71 (Flash, pin_783485666539777118@v8, request 557ffdac3f53)
  - wrong: pose gate failed: head position shift 0.054 (goal x0.50 y0.25, render x0.53 y0.21)
  - right: identity 0.71 (accept band)
- **attempt 32** `20261019_053523_goal-pin-783485666539777118/v1_0r.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666539777118@v8, request 557ffdac3f53)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal) | 12/14: the pose gate reads his head 0.054 off the pin's (limit 0.04), a little higher; 19/26/28/31/32 were not compared at the same scale this time (unverified, pointed out only) | the user rejected it: the user, 2026-10-19: 'although the teeth here were perfect, the hair is not' (the background restore pasted the pin man's hair, FAILURE_LOG F73); replaced by their choice v1_0s.jpg: 'I like this one' (earlier accepted: the user, 2026-10-19 (dialog): teeth 'The first picture's do'; overall 'Keep the first')
  - right: teeth mode, first test: his open smile with his own teeth from the real IMG_6875 crop, in one whole render with the pumped torso | 36 of 38 checklist items passed, 0 not applicable
- **attempt 33** `20261019_053523_goal-pin-783485666539777118/v1_0s.jpg`: **PASS (accepted by the user)** (Flash, pin_783485666539777118@v8, request 557ffdac3f53)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | 12/14: the pose gate reads his head 0.054 off the pin's (limit 0.04), a little higher; 37: the background is Gemini's redraw of the pin's room (SSIM 0.83 against it), chosen by the user over the copied-back background with its halo; only the sparkle is the pin's; 19/26/28/31/32 not compared at the same scale (unverified, pointed out only) | the user accepted it anyway: the user, 2026-10-19: 'I like this one, as the other one has distortion around the halo that you tried to add' (v1_0_sparkle_only.jpg)
  - right: Gemini's render as drawn: his curls, his teeth (teeth mode, the real IMG_6875 crop), the pumped torso; only the sparkle watermark replaced by the pin's pixels | 35 of 38 checklist items passed, 0 not applicable
- **attempt 34** `20261019_053523_goal-pin-783485666539777118/v2_0.jpg`: **NOT CHECKED YET**, identity 0.62 (Flash, pin_783485666539777118@v8, request 557ffdac3f53)
  - right: pose gate passed every measured item | identity 0.62 (accept band)
- **attempt 35** `20261019_053523_goal-pin-783485666539777118/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539777118@v8, request 557ffdac3f53)
  - wrong: failed checklist items: 36 (His janeu and chain); 38 (His teeth, when they show, are his own) | 36: the janeu starts mid-chest instead of at his shoulder; 38: a smoother, more even row of teeth, and the user chose only the first picture's teeth as his (dialog 2026-10-19); not kept by the user; 19/26/28/31/32 not compared at the same scale (unverified)
  - right: 36 of 38 checklist items passed, 0 not applicable

## motorcycle-outfit-men_09_black-polo-leaning-over-desk-office

92 pictures, 1 passed.

- **attempt 1** `20260930_235828_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)**, identity 0.07 (Flash, pin_783485666539779317.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal) | pin 9 classroom: pose gate FAIL head bow +0.67 vs goal +0.87 (chin up, more level), size x1.14; identity 0.074 (not him); arms still the goal man's
  - right: scene and the foreground person unchanged; polo, trousers, plant, shelf, notice board faithful | identity 0.07 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 20 of 30 checklist items passed, 6 not applicable
- **attempt 2** `20260930_235828_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.39 (Flash, pin_783485666539779317.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 9: pose gate FAIL head bow +0.75 vs +0.87 (more level); identity 0.387 gray zone; arms and shoulders still the goal man's heavy build
  - right: head bow passed the pose gate after the steep-bow wording; scene faithful; curly hair and dark beard | identity 0.39 (gray zone, needs a human eye) | 21 of 30 checklist items passed, 6 not applicable
- **attempt 3** `20261001_000237_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 9 classroom re-run (steep head bow + slim-build wording): pose gate PASS now (head bow matches the goal); scene and the foreground person unchanged; curly black hair and dark beard; identity score 0.13-0.16 (bowed head, gray zone, needs the user's eye); upper arms and biceps still heavy under the polo sleeves, the goal man's build; sparkle bottom-right left as produced
  - right: steep head bow passed the pose gate; scene faithful | pose gate passed every measured item | 22 of 30 checklist items passed, 6 not applicable
- **attempt 4** `20261001_000237_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.16 (Flash, pin_783485666539779317_v2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | pin 9 classroom re-run (steep head bow + slim-build wording): pose gate PASS now (head bow matches the goal); scene and the foreground person unchanged; curly black hair and dark beard; identity score 0.13-0.16 (bowed head, gray zone, needs the user's eye); upper arms and biceps still heavy under the polo sleeves, the goal man's build; sparkle bottom-right left as produced
  - right: steep head bow passed the pose gate; scene faithful | pose gate passed every measured item | identity 0.16 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 5** `20261001_000237_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (checklist)**, identity 0.13 (Flash, pin_783485666539779317_v2.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 29 (The distance from the camera is the same as in the goal) | pin 9 re-run v3: head bow +0.71 vs +0.87, size x1.09
  - right: identity 0.13 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 20 of 30 checklist items passed, 6 not applicable
- **attempt 6** `20261001_002901_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.13 (Flash, pin_783485666539779317_v3.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.72 (more level, chin up)
  - right: identity 0.13 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 7** `20261001_041045_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.13 (Pro, pin_783485666539779317_v3.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.69 (more level, chin up)
  - right: identity 0.13 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 8** `20261001_041045_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.21 (Pro, pin_783485666539779317_v3.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.047 (goal x0.45 y0.48, render x0.50 y0.46); head position shift 0.040 (goal x0.33 y0.47, render x0.36 y0.45); head bow (nose below eye line / eye distance) goal +0.87, render +0.55 (more level, chin up); size in the frame (torso) x1.08
  - right: identity 0.21 (gray zone, needs a human eye)
- **attempt 9** `20261001_041443_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.25 (Flash, pin_783485666539779317_v3.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.73 (more level, chin up); size in the frame (torso) x1.08
  - right: identity 0.25 (gray zone, needs a human eye)
- **attempt 10** `20261001_041443_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.45 (Flash, pin_783485666539779317_v3.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.71 (more level, chin up)
  - right: identity 0.45 (gray zone, needs a human eye)
- **attempt 11** `20261001_041846_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317_v4.json)
  - wrong: failed checklist items: 6 (The head and face are his true size); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | the curls are an oversized ball, bigger than his head should be (head too big, unreal); arms and shoulders are still the goal man's heavy build
  - right: pose gate passed after the steep-bow wording (head bow matches the pin); scene and the foreground person unchanged; polo, trousers and props faithful | pose gate passed every measured item | 22 of 30 checklist items passed, 6 not applicable
- **attempt 12** `20261001_041846_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317_v4.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.63 (more level, chin up)
- **attempt 13** `20261001_041846_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (checklist)**, identity 0.32 (Flash, pin_783485666539779317_v4.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.317 is in the gray zone (needs a human eye); upper arms, forearms and shoulders are still the goal man's heavy muscular build under tight polo sleeves although the wording asked for thin arms
  - right: pose gate passed (steep head bow matches the pin); his curly hair and dark beard look right; scene, foreground person, polo and trousers faithful; best face of the pin 9 samples | pose gate passed every measured item | identity 0.32 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 14** `20261001_041846_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (checklist)**, identity 0.05 (Flash, pin_783485666539779317_v4.json)
  - wrong: failed checklist items: 19 (All of the hair is his own); 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | the face and the straight dark hair are the goal man's, not his curls (identity 0.054); the man was not replaced
  - right: pose gate passed; scene faithful | pose gate passed every measured item | identity 0.05 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 21 of 30 checklist items passed, 6 not applicable
- **attempt 15** `20261001_063341_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.06 (Flash, pin_783485666539779317_v5.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.73 (more level, chin up); size in the frame (torso) x1.08
  - right: identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 16** `20261001_063341_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.14 (Flash, pin_783485666539779317_v5.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.63 (more level, chin up)
  - right: identity 0.14 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 17** `20261001_063341_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.12 (Flash, pin_783485666539779317_v5.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.66 (more level, chin up); size in the frame (torso) x1.10
  - right: identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 18** `20261001_063341_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.31 (Flash, pin_783485666539779317_v5.json)
  - wrong: pose gate failed: size in the frame (torso) x1.08
  - right: identity 0.31 (gray zone, needs a human eye)
- **attempt 19** `20261001_064734_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.12 (Flash, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: size in the frame (torso) x1.12
  - right: identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 20** `20261001_064734_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.03 (Flash, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.102 (goal x0.45 y0.48, render x0.55 y0.47); head position shift 0.117 (goal x0.33 y0.47, render x0.44 y0.49); size in the frame (torso) x0.92; his right forearm direction 18 deg off; his right hand position shift 0.141 (goal x0.34 y0.87, render x0.48 y0.84); his left hand position shift 0.192 (goal x0.45 y0.87, render x0.64 y0.84)
  - right: identity 0.03 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 21** `20261001_064734_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: size in the frame (torso) x1.09
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 22** `20261001_064734_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Flash, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.78 (more level, chin up); size in the frame (torso) x1.11
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 23** `20261001_065418_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.40 (Pro, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.62 (more level, chin up)
  - right: identity 0.40 (gray zone, needs a human eye)
- **attempt 24** `20261001_065418_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.24 (Pro, pin_783485666539779317_v6.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.71 (more level, chin up)
  - right: identity 0.24 (gray zone, needs a human eye)
- **attempt 25** `20261001_071557_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.09 (Flash, pin_783485666539779317_v7.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.65 (more level, chin up)
  - right: identity 0.09 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 26** `20261001_071557_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.36 (Flash, pin_783485666539779317_v7.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.364 is in the gray zone (needs a human eye; bowed head); the upper arms, forearms and shoulders are still the pin man's heavy build under tight polo sleeves (the tank-top 'visible consequence' wording has not been tried on this goal's polo yet)
  - right: first pin 9 picture that passes the pose gate with the right head bow AND the right size (both measured), with the numeric framing lines; his curls and dark beard; scene and the foreground person unchanged; hands and desk faithful; best face of the pin 9 samples | pose gate passed every measured item | identity 0.36 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 27** `20261001_071557_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.14 (Flash, pin_783485666539779317_v7.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.76 (more level, chin up)
  - right: identity 0.14 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 28** `20261001_113317_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.23 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.67 (more level, chin up)
  - right: identity 0.23 (gray zone, needs a human eye)
- **attempt 29** `20261001_113317_goal-pin-783485666539779317/v1_0.png`: **NOT CHECKED YET** (Flash, pin_783485666539779317_v8.json)
- **attempt 30** `20261001_113317_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.72 (more level, chin up)
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 31** `20261001_113317_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.34 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: size in the frame (torso) x1.07
  - right: identity 0.34 (gray zone, needs a human eye)
- **attempt 32** `20261001_113317_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.67 (more level, chin up); size in the frame (torso) x1.09
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 33** `20261001_114849_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.11 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head position shift 0.055 (goal x0.33 y0.47, render x0.35 y0.42); head bow (nose below eye line / eye distance) goal +0.87, render +0.77 (more level, chin up); neck/head direction 16 deg off
  - right: identity 0.11 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 34** `20261001_114849_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.08 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.75 (more level, chin up); size in the frame (torso) x1.09
  - right: identity 0.08 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 35** `20261001_114849_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.20 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.78 (more level, chin up)
  - right: identity 0.20 (gray zone, needs a human eye)
- **attempt 36** `20261001_114849_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.25 (Flash, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.53 (more level, chin up); his left hand position shift 0.123 (goal x0.45 y0.87, render x0.57 y0.84)
  - right: identity 0.25 (gray zone, needs a human eye)
- **attempt 37** `20261001_114851_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.27 (Pro, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.59 (more level, chin up)
  - right: identity 0.27 (gray zone, needs a human eye)
- **attempt 38** `20261001_114851_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539779317_v8.json)
  - wrong: pose gate failed: size in the frame (torso) x1.11
- **attempt 39** `20261001_115319_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.29 (Flash, pin_783485666539779317_v9.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.75 (more level, chin up)
  - right: identity 0.29 (gray zone, needs a human eye)
- **attempt 40** `20261001_115319_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_v9.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.73 (more level, chin up)
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 41** `20261001_115319_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.22 (Flash, pin_783485666539779317_v9.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.73 (more level, chin up)
  - right: identity 0.22 (gray zone, needs a human eye)
- **attempt 42** `20261001_115625_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.28 (Flash, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.66 (more level, chin up)
  - right: identity 0.28 (gray zone, needs a human eye)
- **attempt 43** `20261001_115625_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.32 (Flash, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.69 (more level, chin up)
  - right: identity 0.32 (gray zone, needs a human eye)
- **attempt 44** `20261001_115625_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (checklist)**, identity 0.31 (Flash, pin_783485666539779317_v10.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.312 is in the gray zone (needs a human eye; bowed head); the upper arms, forearms and shoulders are still the pin man's heavy muscular build in tight polo sleeves (on the body sheet they are far thicker than his body photo IMG_6923)
  - right: FIRST pin 9 picture that passes the whole pose gate: head bow 0.85 vs 0.87, torso size x1.04, body shift 0.011, head shift 0.002, every limb within 4 degrees, both hand positions within 0.03; the fix was asking for a bow MORE STEEP than the pin (nose 1.1 eye distances below the eye line) because renders land about 0.12 short of the asked bow; scene, foreground person, polo, trousers, desk and hands faithful; his curls and dark beard | pose gate passed every measured item | identity 0.31 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 45** `20261001_115625_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.25 (Flash, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.72 (more level, chin up)
  - right: identity 0.25 (gray zone, needs a human eye)
- **attempt 46** `20261001_115629_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.22 (Pro, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.113 (goal x0.45 y0.48, render x0.55 y0.42); head position shift 0.162 (goal x0.33 y0.47, render x0.48 y0.42); head bow (nose below eye line / eye distance) goal +0.87, render +0.57 (more level, chin up); size in the frame (torso) x1.11; torso direction 21 deg off; his left forearm direction 17 deg off; his right hand position shift 0.065 (goal x0.34 y0.87, render x0.41 y0.85); his left hand position shift 0.214 (goal x0.45 y0.87, render x0.66 y0.84)
  - right: identity 0.22 (gray zone, needs a human eye)
- **attempt 47** `20261001_115629_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Pro, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.069 (goal x0.45 y0.48, render x0.52 y0.47); head position shift 0.108 (goal x0.33 y0.47, render x0.43 y0.49); head bow (nose below eye line / eye distance) goal +0.87, render +0.63 (more level, chin up); size in the frame (torso) x0.91; neck/head direction 22 deg off
- **attempt 48** `20261001_120058_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.61 (more level, chin up)
- **attempt 49** `20261001_120058_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.06 (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: head position shift 0.133 (goal x0.33 y0.47, render x0.45 y0.44); head bow (nose below eye line / eye distance) goal +0.87, render +0.54 (more level, chin up); torso direction 34 deg off; his right upper arm direction 18 deg off; his right forearm direction 20 deg off; his left forearm direction 21 deg off; his right hand position shift 0.070 (goal x0.34 y0.87, render x0.28 y0.84); his left hand position shift 0.244 (goal x0.45 y0.87, render x0.69 y0.92)
  - right: identity 0.06 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 50** `20261001_120058_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.043 (goal x0.45 y0.48, render x0.48 y0.44); head position shift 0.097 (goal x0.33 y0.47, render x0.39 y0.40); head bow (nose below eye line / eye distance) goal +0.87, render +0.77 (more level, chin up); size in the frame (torso) x1.18; torso direction 15 deg off; neck/head direction 27 deg off
- **attempt 51** `20261001_163323_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)**, identity 0.38 (Flash, pin_783485666539779317_v10.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal) | pose gate failed (head too level or size) so not audited further
  - right: scene faithful | identity 0.38 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 52** `20261001_163323_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.30 (Flash, pin_783485666539779317_v10.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal) | pose gate failed (head too level or size) so not audited further
  - right: scene faithful | identity 0.30 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 53** `20261001_163323_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (checklist)**, identity 0.37 (Flash, pin_783485666539779317_v10.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.369 gray zone; on the body sheet the upper arms and forearms are slimmer than the pin man's but still far heavier than his body photo IMG_6923 (build not his)
  - right: the overshoot-bow wording reproduced: head bow 0.85 vs 0.87, torso size x1.06, whole pose gate passed again (2nd time in 2 batches, ~1 in 4 samples); his curls and dark beard; scene, foreground person, desk and hands faithful | pose gate passed every measured item | identity 0.37 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 54** `20261001_163323_goal-pin-783485666539779317/v4_0.jpg`: **FAIL (checklist)**, identity 0.24 (Flash, pin_783485666539779317_v10.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal) | pose gate failed (head too level or size) so not audited further
  - right: scene faithful | identity 0.24 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 6 not applicable
- **attempt 55** `20261001_163326_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.32 (Pro, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.68 (more level, chin up)
  - right: identity 0.32 (gray zone, needs a human eye)
- **attempt 56** `20261001_163326_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.12 (Pro, pin_783485666539779317_v10.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.63 (more level, chin up); size in the frame (torso) x1.10
  - right: identity 0.12 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 57** `20261001_163330_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.24 (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.70 (more level, chin up); size in the frame (torso) x1.08
  - right: identity 0.24 (gray zone, needs a human eye)
- **attempt 58** `20261001_163330_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.23 (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.70 (more level, chin up)
  - right: identity 0.23 (gray zone, needs a human eye)
- **attempt 59** `20261001_163330_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.31 (Flash, pin_783485666539779317_v11.json)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.052 (goal x0.45 y0.48, render x0.50 y0.46); head position shift 0.051 (goal x0.33 y0.47, render x0.37 y0.45); head bow (nose below eye line / eye distance) goal +0.87, render +0.68 (more level, chin up)
  - right: identity 0.31 (gray zone, needs a human eye)
- **attempt 60** `20261001_165831_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)**, identity 0.35 (Flash, pin_783485666539779317_v12.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.346 gray zone; arms and forearms still the pin man's heavy muscle (body sheet vs IMG_6923)
  - right: pose gate fully passed: bow 0.83 vs 0.87, torso x1.03, body shift 0.010; scene, hands, polo and his curls and beard faithful | pose gate passed every measured item | identity 0.35 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 61** `20261001_165831_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.36 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.75 (more level, chin up)
  - right: identity 0.36 (gray zone, needs a human eye)
- **attempt 62** `20261001_165831_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.68 (more level, chin up); size in the frame (torso) x1.09
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 63** `20261001_165837_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.20 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.73 (more level, chin up)
  - right: identity 0.20 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 64** `20261001_165837_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.11 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.66 (more level, chin up)
  - right: identity 0.11 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 65** `20261001_165837_goal-pin-783485666539779317/v3_0.jpg`: **NOT CHECKED YET**, identity 0.10 (Flash, pin_783485666539779317_v12.json)
  - right: pose gate passed every measured item | identity 0.10 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 66** `20261001_165843_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.71 (more level, chin up)
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 67** `20261001_165843_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317_v12.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity not scorable here; arms and forearms still the pin man's heavy muscle
  - right: pose gate fully passed: bow 0.92 vs 0.87 (deeper, within 0.08), torso x1.02, body shift 0.007; scene faithful | pose gate passed every measured item | 22 of 30 checklist items passed, 6 not applicable
- **attempt 68** `20261001_165843_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.34 (Flash, pin_783485666539779317_v12.json)
  - wrong: pose gate failed: head position shift 0.042 (goal x0.33 y0.47, render x0.35 y0.44); head bow (nose below eye line / eye distance) goal +0.87, render +0.72 (more level, chin up)
  - right: identity 0.34 (gray zone, needs a human eye)
- **attempt 69** `20261001_170359_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317_stage2.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.79 (more level, chin up)
- **attempt 70** `20261001_170359_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.32 (Flash, pin_783485666539779317_stage2.json)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | identity 0.317 gray zone; arms: the body-only slimming edit barely changed them (arm crop vs the source render and the pin man looks the same: bulging biceps and thick forearm under the sleeve); the polo is still tight
  - right: body-only edit kept the head, bow (0.83), size (1.04) and framing: the pose gate passes on an edited render, so a body-only chain is viable for this goal; his curls and beard; scene faithful | pose gate passed every measured item | identity 0.32 (gray zone, needs a human eye) | 22 of 30 checklist items passed, 6 not applicable
- **attempt 71** `20261001_170359_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.27 (Flash, pin_783485666539779317_stage2.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.79 (more level, chin up); size in the frame (torso) x1.07
  - right: identity 0.27 (gray zone, needs a human eye)
- **attempt 72** `20261001_170403_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.26 (Flash, pin_783485666539779317_stage2.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.78 (more level, chin up); size in the frame (torso) x1.07
  - right: identity 0.26 (gray zone, needs a human eye)
- **attempt 73** `20261001_170403_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317_stage2.json)
  - wrong: pose gate failed: size in the frame (torso) x1.08
- **attempt 74** `20261001_170403_goal-pin-783485666539779317/v3_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_stage2.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.77 (more level, chin up)
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 75** `20261001_170832_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317_stage3.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | stage 3a render: pose gate failed on size (torso x1.09 / x1.07 > 1.07); v1 also grew glasses the pin does not have
  - right: arms visibly slimmer with the explicit magnitudes | 21 of 30 checklist items passed, 6 not applicable
- **attempt 76** `20261001_170832_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.31 (Flash, pin_783485666539779317_stage3.json)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | stage 3a render: pose gate failed on size (torso x1.09 / x1.07 > 1.07); v1 also grew glasses the pin does not have
  - right: arms visibly slimmer with the explicit magnitudes | identity 0.31 (gray zone, needs a human eye) | 21 of 30 checklist items passed, 6 not applicable
- **attempt 77** `20261001_170837_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)**, identity 0.32 (Flash, pin_783485666539779317_stage3b.json)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | pin 09 v1 under the 32 items: heavily muscled forearms and upper arms and broad shoulders, the pin man's build, beside IMG_6923 at the same scale (26, 32). N/A 31: his face is bowed and mostly hidden. The user, 2026-10-08, on the new same-man checks (31, 32): 'rework them too'.
  - right: pose gate passed every measured item | identity 0.32 (gray zone, needs a human eye) | 23 of 32 checklist items passed, 7 not applicable
- **attempt 78** `20261001_170837_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666539779317_stage3b.json)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.78 (more level, chin up)
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 79** `20261007_032816_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317@v1, request 8d030c3c2943)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | pose gate FAIL 12: his head is bowed less than the pin's, as in every single-stage attempt of this pin; face/neck 1.50 vs 2.11; identity not scorable on the bowed face
  - right: his curls and beard; the office scene kept (grey diff 6.5) | 23 of 30 checklist items passed, 5 not applicable
- **attempt 80** `20261007_032816_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.25 (Flash, pin_783485666539779317@v1, request 8d030c3c2943)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | pose gate FAIL 12: head bowed less than the pin's; face/neck 1.53 vs 2.11; identity 0.25 on the bowed face, not verifiable
  - right: his curls and beard; the office scene kept (grey diff 6.0) | identity 0.25 (gray zone, needs a human eye) | 23 of 30 checklist items passed, 5 not applicable
- **attempt 81** `20261009_010202_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (checklist)**, identity 0.31 (Flash, pin_783485666539779317@v2, request aab27307cc18)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 09 v2 (character me@v2, Flash) sample 1: pose gate PASS and his curls and beard, but the body is the pin man's: heavily muscled upper arms and forearms (arm width 3.09 vs his 1.30-1.48) beside IMG_6923 (26, 32); the bowed face cannot be judged for identity or fullness (21, 31, unverifiable).
  - right: pose gate passed every measured item | identity 0.31 (gray zone, needs a human eye) | 22 of 32 checklist items passed, 6 not applicable
- **attempt 82** `20261009_010202_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (checklist)**, identity 0.42 (Flash, pin_783485666539779317@v2, request aab27307cc18)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | pin 09 v2 sample 2: pose gate item 12; the pin man's muscled arms (26, 32). Items not looked at closely are listed as failed (unverifiable).
  - right: identity 0.42 (gray zone, needs a human eye) | 19 of 32 checklist items passed, 6 not applicable
- **attempt 83** `20261014_030859_goal-pin-783485666539779317/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666539779317@v3, request 08a18fa1568f)
  - right: pose gate passed every measured item
- **attempt 84** `20261014_030859_goal-pin-783485666539779317/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666539779317@v3, request 08a18fa1568f)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | stage 1 of 2 by design: body only, the head is the pin man's (19, 21, 28, 31 cannot pass yet). 26/32: the arms are as heavy as the pin man's (the casual yardstick: never thinner than his own photo, but not the pin man's 3.09 arm widths against his 1.30-1.48): the kept outline again (F46, F52); pose gate PASS; v2_0 fails item 12 only. A face seems to carry glasses in the raw v1 render crop but the restored picture shows the pin man's head
  - right: 24 of 36 checklist items passed, 6 not applicable
- **attempt 85** `20261014_030859_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317@v3, request 08a18fa1568f)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.74 (more level, chin up)
- **attempt 86** `20261014_030859_goal-pin-783485666539779317/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin_783485666539779317@v3, request 08a18fa1568f)
- **attempt 87** `20261014_074709_goal-pin9build-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin9build_send@v1, request 83288686fff3)
  - wrong: pose gate failed: person found no person in goal
- **attempt 88** `20261014_074709_goal-pin9build-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin9build_send@v1, request 83288686fff3)
  - wrong: pose gate failed: person found no person in goal
- **attempt 89** `20261014_074709_goal-pin9build-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin9build_send@v1, request 83288686fff3)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Stage 1 of 2 by design: body only, the head is still the pin man's (19, 21, 28, 31 cannot pass). 26/32: the arms are still heavier than his casual standard: bare-arm thickness per torso length by ATR (pin9build_measures.json): near arm upper 0.273 and forearm 0.181 (base 0.275 / 0.191, pin man 0.301 / 0.211) against the target 0.19 / 0.135 and his own 0.169-0.179 / 0.122-0.127; the far arm 0.228 / 0.187 (base 0.188 / 0.181) did not shrink. The build wave moved the near forearm 5 percent, not the 30 percent needed. v1 was refused by the paste (re-framed: ECC 0.945, scale 0.82 / 0.78). Pose gate on the raw returns FAIL 14/29/30 on both (the crop's frame), the pasted v2_0r keeps the base pose.
  - right: Pose: v2 pasted back clean (ECC 0.999, shift 0); the near forearm is slimmer than the base by eye (arms_goal_base_new.jpg); polo, trousers, girl, calendar, shelves untouched (head rows 0.00%). | 24 of 36 checklist items passed, 6 not applicable
- **attempt 90** `20261021_033704_goal-pin-783485666539779317/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.18 (Flash, pin_783485666539779317@v4, request ba9553e41497)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.049 (goal x0.45 y0.48, render x0.49 y0.44); head bow (nose below eye line / eye distance) goal +0.87, render +0.74 (more level, chin up)
  - right: identity 0.18 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 91** `20261021_033704_goal-pin-783485666539779317/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666539779317@v4, request ba9553e41497)
  - wrong: pose gate failed: head bow (nose below eye line / eye distance) goal +0.87, render +0.74 (more level, chin up)
- **attempt 92** `20261021_033704_goal-pin-783485666539779317/v2_0r.jpg`: **PASS (accepted by the user)** (Flash, pin_783485666539779317@v4, request ba9553e41497)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | run 20261021_033704 (pin 9 v4, one whole render, casual-front-arms wording, restore with heads kept): the pose gate passes every measured item except the head bow: goal +0.87 (nose below the eye line over the eye distance), render +0.74, a little more level (limit 0.08 apart); 21: his face is bowed in 3/4, identity not measurable: unverified; 19/26/28/31/32 not compared at the same scale (unverified); the restore left his head untouched (0.3% of head pixels differ from the raw render) | the user accepted it anyway: the user, 2026-10-21 (question box): 'Keep it (Recommended)' (the restored pin 9 render; it fails only the head bow, 0.74 against 0.87)
  - right: the closest of the round: the classroom exactly as in the pin, his curls and beard, the silver chain, the relaxed arms in the black polo, the posture bent over the desk, nothing else changed | 34 of 38 checklist items passed, 2 not applicable

## motorcycle-outfit-men_10_gym-mirror-back-shirtless-bw-side-face

16 pictures, 0 passed.

- **attempt 1** `20261009_155526_goal-pin-783485666540141734/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v1, request 7d078f80e233)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate PASS. 12 FAILS: the user asked for his side face only VERY slightly more visible than the pin (which shows none); the head is turned so far that the cheek, closed eye, nose and mouth show in a 3/4 profile. 21, 31, 32 not judged (a bowed 3/4 face has no landmarks; the body is seen from behind with no back reference): listed failed (unverifiable). Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: pose gate passed every measured item | 20 of 32 checklist items passed, 8 not applicable
- **attempt 2** `20261009_155526_goal-pin-783485666540141734/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v1, request 7d078f80e233)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate PASS. 12 FAILS: closer than v1_0 but still far more than 'very slightly': the cheek, the closed eye, the brow and the nose tip show (a 3/4 profile, about 35 degrees more than the pin). 21, 31, 32 not judged (no landmarks on a bowed profile; body seen from behind): listed failed (unverifiable). Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: pose gate passed every measured item | 20 of 32 checklist items passed, 8 not applicable
- **attempt 3** `20261009_164019_goal-pin-783485666540141734/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v2, request a03303251fd8)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL 30 (his left forearm 19 degrees off the pin's, his right hand 0.100 of the frame off). 12 FAILS again: the head is a lowered profile with the cheek, closed eye and nose visible, not 'very slightly' more than the pin. 21, 31, 32 not judged (no landmarks on a bowed profile; body seen from behind). Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: 19 of 32 checklist items passed, 8 not applicable
- **attempt 4** `20261009_164019_goal-pin-783485666540141734/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v2, request a03303251fd8)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL 30 (his left forearm 15 degrees off, at the limit). 12 FAILS again: a lowered profile with cheek, closed eye, brow and nose visible. 21, 31, 32 not judged. Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: 19 of 32 checklist items passed, 8 not applicable
- **attempt 5** `20261009_203844_goal-pin-783485666540141734/v1_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v3, request 39088e91b697)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture) | Obsolete recipe v3 (the pin's own head pose, 'lats slimmer and smoother, no deep grooves'), started at 20:38 by the old wave c that had survived the crash; superseded by v5/v6. 32: the back is smoother than his real one: exactly the definition the user said was being removed (v3's own wording caused it). 33/34 unverifiable: no background restore, the people and the mirrored sign are Gemini's redraw.
  - right: pose gate passed every measured item | 27 of 35 checklist items passed, 5 not applicable
- **attempt 6** `20261009_203844_goal-pin-783485666540141734/v2_0.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v3, request 39088e91b697)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture) | Obsolete recipe v3 (the pin's own head pose, 'lats slimmer and smoother, no deep grooves'), started at 20:38 by the old wave c that had survived the crash; superseded by v5/v6. 32: the back is smoother than his real one: exactly the definition the user said was being removed (v3's own wording caused it). 33/34 unverifiable: no background restore, the people and the mirrored sign are Gemini's redraw.
  - right: pose gate passed every measured item | 27 of 35 checklist items passed, 5 not applicable
- **attempt 7** `20261009_204003_goal-pin-783485666540141734/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666540141734@v5, request 20a5c7ade3b8)
  - right: pose gate passed every measured item
- **attempt 8** `20261009_204003_goal-pin-783485666540141734/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v5, request 20a5c7ade3b8)
  - wrong: failed checklist items: 36 (His janeu and chain) | 36: his back is bare and his janeu is not there (the user, 2026-10-10: 'It is the holy thread that Brahmins wear, called jenu', in every bare-torso picture). 32 now passes (re-check above). Next: a region edit adding the janeu across his back, with the rebuilt his_back.jpg as the reference, then export.
  - right: Back definition now his (the v3 'smoother, no grooves' line removed); curls over the brow hide the eye; restore made the people and the STENU/KEY sign identical to the pin. | 30 of 36 checklist items passed, 5 not applicable
- **attempt 9** `20261009_204003_goal-pin-783485666540141734/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666540141734@v5, request 20a5c7ade3b8)
  - wrong: pose gate failed: his left forearm direction 15 deg off
- **attempt 10** `20261009_204003_goal-pin-783485666540141734/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v5, request 20a5c7ade3b8)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 26 (Scenery, background and clothes are unchanged from the source photo); 30 (Body posture and action exactly as in the goal); 32 (His build, the same in every picture of him) | Recipe v5. 30: pose gate FAIL (body posture). 12: the face is turned toward the camera more than in v1_0, about as much as the reviewed sample 155526 v2_0 (eye, nose and cheek in a lowered profile), so not hidden more as the user asked. 26: a neck chain the pin does not have, and a black towel drawn hanging from the upper bar beside his head (inside the silhouette band, so Gemini's pixels). 32: prominent forearm veins like the pin man's; his own forearms are slim and smooth (IMG_6923, his video). Background, people and lettering outside him are the pin's (restore ECC 0.980).
  - right: Back definition his, as in v1_0. | 26 of 35 checklist items passed, 5 not applicable
- **attempt 11** `20261010_091126_goal-pin-783485666540141734/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666540141734@v6, request 45ff20ae567f)
  - wrong: pose gate failed: his left forearm direction 19 deg off
- **attempt 12** `20261010_091126_goal-pin-783485666540141734/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666540141734@v6, request 45ff20ae567f)
  - right: pose gate passed every measured item
- **attempt 13** `20261011_040302_goal-pin-783485666540141734/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666540141734@v7, request af6208604306)
  - right: pose gate passed every measured item
- **attempt 14** `20261011_040302_goal-pin-783485666540141734/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v7, request af6208604306)
  - wrong: failed checklist items: 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in); 12 (Head and face pose match the goal) | 12: his head turned into profile (beard and nose show) where the pin's face is hidden; the user asked on this pin to 'hide the face a little more' (v4). 8: Gemini's sparkle watermark stayed on the floor near his trouser leg (inside the restore's band around him).
  - right: pose gate passed; janeu direction right for a back view; full arms with veins; restore kept people and lettering | 30 of 36 checklist items passed, 4 not applicable
- **attempt 15** `20261011_040302_goal-pin-783485666540141734/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin_783485666540141734@v7, request af6208604306)
  - right: pose gate passed every measured item
- **attempt 16** `20261011_040302_goal-pin-783485666540141734/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141734@v7, request af6208604306)
  - wrong: failed checklist items: 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in); 12 (Head and face pose match the goal) | 12: his head turned into profile where the pin's face is hidden (the user, v4: 'hide the face a little more'). 8: Gemini's sparkle watermark stayed near his trouser leg.
  - right: pose gate passed; janeu direction right; full arms with veins | 30 of 36 checklist items passed, 4 not applicable

## motorcycle-outfit-men_11_pizza-table-head-on-hand-navy-zip-sweater

19 pictures, 3 passed.

- **attempt 1** `20261009_155531_goal-pin-783485666540141628/v1_0.jpg`: **FAIL (checklist)**, identity 0.57 (Flash, pin_783485666540141628@v1, request 3220d9047176)
  - wrong: failed checklist items: 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's) | Pose gate PASS (body 0.006, head 0.007, bow +0.41 vs +0.42); identity 0.574 accepted; face light 124 vs the goal's 122. The tool's FACE vs NECK FAIL (12.4 vs 13.5) is an artifact: both necks read about 10 (the navy collar and the beard's shadow), so the ratio compares two near-black patches; judged by eye (4/10/11 pass: face, hair and neck read as one head, no seam). 28 FAILS: his beard in IMG_6858/6861/6868 is a full, dense, black beard hanging below the jaw with a full moustache; the render's is a short, light stubble beard with skin showing through on the jaw and chin and a thin moustache (lower-face crops at the same scale).
  - right: Near-exact edit of the pin: the same restaurant, plate, bottle, sign, sweater, hands and pose, his curls and his lean face (cheek_iod/jaw_iod at the lean end), his round watch in place of the pin's, the pin's '1/7' marker gone. | pose gate passed every measured item | identity 0.57 (accept band) | 24 of 32 checklist items passed, 7 not applicable
- **attempt 2** `20261009_155531_goal-pin-783485666540141628/v2_0.jpg`: **FAIL (checklist)**, identity 0.16 (Flash, pin_783485666540141628@v1, request 3220d9047176)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL (12, 12/14, 14, 29, 30); identity 0.156 rejected: a different-looking man; the restaurant was redrawn (a street with a brick building, a different sideboard, the plate cut by the bottom edge) and his hand moved to the temple. Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: identity 0.16 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 15 of 32 checklist items passed, 7 not applicable
- **attempt 3** `20261009_203544_goal-pin-783485666540141628/v1_0.jpg`: **FAIL (checklist)**, identity 0.56 (Flash, pin_783485666540141628@v2, request a3f5c39b63bd)
  - wrong: failed checklist items: 34 (Text in the picture) | Obsolete recipe v2 (beard close-up, the pin's own expression), started at 20:35 by the old wave c that had survived the session crash; superseded by v3 (light smirk) and v4 (candid smile). The beard is now full and dense (v1's item 28 fixed) and the pose gate passes. 34 fails as unverifiable: v2 has no background restore, so every lettering is Gemini's redraw; the sign, L10 card, bottle and glass letters look the same at 100%, but the accent of SANCHEZ on the plate cannot be confirmed letter for letter.
  - right: pose gate passed every measured item | identity 0.56 (accept band) | 28 of 35 checklist items passed, 6 not applicable
- **attempt 4** `20261009_203544_goal-pin-783485666540141628/v2_0.jpg`: **FAIL (checklist)**, identity 0.56 (Flash, pin_783485666540141628@v2, request a3f5c39b63bd)
  - wrong: failed checklist items: 34 (Text in the picture) | Obsolete recipe v2 (beard close-up, the pin's own expression), started at 20:35 by the old wave c that had survived the session crash; superseded by v3 (light smirk) and v4 (candid smile). The beard is now full and dense (v1's item 28 fixed) and the pose gate passes. 34 fails as unverifiable: v2 has no background restore, so every lettering is Gemini's redraw; the sign, L10 card, bottle and glass letters look the same at 100%, but the accent of SANCHEZ on the plate cannot be confirmed letter for letter.
  - right: pose gate passed every measured item | identity 0.56 (accept band) | 28 of 35 checklist items passed, 6 not applicable
- **attempt 5** `20261009_204403_goal-pin-783485666540141628/v1_0.jpg`: **NOT CHECKED YET**, identity 0.60 (Flash, pin_783485666540141628@v3, request de29ec1c41d8)
  - right: pose gate passed every measured item | identity 0.60 (accept band)
- **attempt 6** `20261009_204403_goal-pin-783485666540141628/v1_0r.jpg`: **PASS (all 35 items)** (Flash, pin_783485666540141628@v3, request de29ec1c41d8)
  - right: Full dense beard from the HIS BEARD crop; his round black watch; every lettering identical to the pin's (restored); light smirk without tension. | 28 of 35 checklist items passed, 7 not applicable
- **attempt 7** `20261009_204403_goal-pin-783485666540141628/v2_0.jpg`: **NOT CHECKED YET**, identity 0.50 (Flash, pin_783485666540141628@v3, request de29ec1c41d8)
  - right: pose gate passed every measured item | identity 0.50 (gray zone, needs a human eye)
- **attempt 8** `20261009_204403_goal-pin-783485666540141628/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141628@v3, request de29ec1c41d8)
  - wrong: failed checklist items: 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's) | 28: the user, 2026-10-10: 'V2 just has a little more beard than what I would expect. Let's try to fix that'. Measured beside his_beard.jpg (IMG_6858's lower face): the cheek beard is denser and grows higher than his (his upper cheeks are sparse with skin showing, the cheek line low) and the moustache is fuller. 21 now passes by the user's eye. Base for the beard fix.
  - right: The user: 'the rest of everything in V2 is perfect' (eyes, smirk, hair, hand, light). Clear very light smirk; full dense beard; lettering identical to the pin. | 27 of 35 checklist items passed, 7 not applicable
- **attempt 9** `20261009_204806_goal-pin-783485666540141628/v1_0.jpg`: **NOT CHECKED YET**, identity 0.55 (Flash, pin_783485666540141628@v4, request 1fafd58de0d0)
  - right: pose gate passed every measured item | identity 0.55 (accept band)
- **attempt 10** `20261009_204806_goal-pin-783485666540141628/v1_0r.jpg`: **PASS (all 35 items)** (Flash, pin_783485666540141628@v4, request 1fafd58de0d0)
  - right: Candid smile caught mid-reaction; full dense beard; his round black watch; every lettering identical to the pin's (restored). | 28 of 35 checklist items passed, 7 not applicable
- **attempt 11** `20261009_204806_goal-pin-783485666540141628/v2_0.jpg`: **FAIL (checklist)**, identity 0.69 (Flash, pin_783485666540141628@v4, request 1fafd58de0d0)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture) | Recipe v4. The sample came back re-framed (aspect 0.747 against the pin's 0.813; grey diff to the pin 27.7), so the background restore refused it: 26 and 29 fail (scene and framing redrawn), 30 pose gate FAIL, 34 the lettering is Gemini's redraw, not copied and not verified letter for letter. The smile and identity (0.685) are good.
  - right: identity 0.69 (accept band) | 24 of 35 checklist items passed, 7 not applicable
- **attempt 12** `20261010_032927_goal-v1-eyeband-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, v1_eyeband_send@v1, request f9fa4426004a)
  - right: pose gate passed every measured item
- **attempt 13** `20261010_032927_goal-v1-eyeband-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, v1_eyeband_send@v1, request f9fa4426004a)
  - wrong: failed checklist items: 27 (None of the flaws recorded for earlier versions of this photo is back) | Alternative eye edit (same recipe). 27 fails: the flaw the user named on _v1 (its eyes) is only half fixed: the lids stay almost as open as _v1's and the irises read a little lighter, so it does not have v2_0r's light-smirk narrowing; the composite v2_0r beside it does. Pasted back cleanly (ECC 0.995).
  - right: 27 of 35 checklist items passed, 7 not applicable
- **attempt 14** `20261010_032927_goal-v1-eyeband-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, v1_eyeband_send@v1, request f9fa4426004a)
  - right: pose gate passed every measured item
- **attempt 15** `20261010_032927_goal-v1-eyeband-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, v1_eyeband_send@v1, request f9fa4426004a)
  - wrong: failed checklist items: 16 (No awkward, tense, forced or smirking reaction, unless the user asked for that expression (2026-10-09) | 16: the user, 2026-10-10: 'v3 is not getting the eyes from v2, and idk where it is getting from it has made it even worse and drunk looking'. The region edit did not carry v2_0r's eyes over: the lids came back heavier and half closed. Rejected; the user now prefers v2_0r itself (perfect except a little more beard).
  - right: Eyes from v2_0r (the user's choice) on _v1's face, which the user called perfect; identity 0.618. | 27 of 35 checklist items passed, 7 not applicable
- **attempt 16** `20261010_114204_goal-v2-beard-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, v2_beard_send@v5, request 98f0af689f90)
  - wrong: pose gate failed: head position shift 0.057 (goal x0.52 y0.49, render x0.47 y0.51)
- **attempt 17** `20261010_114204_goal-v2-beard-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, v2_beard_send@v5, request 98f0af689f90)
- **attempt 18** `20261010_114204_goal-v2-beard-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, v2_beard_send@v5, request 98f0af689f90)
  - wrong: pose gate failed: head position shift 0.056 (goal x0.52 y0.49, render x0.47 y0.51)
- **attempt 19** `20261010_114204_goal-v2-beard-send/v2_0r.jpg`: **PASS (accepted by the user)** (Flash, v2_beard_send@v5, request 98f0af689f90)
  - wrong: failed checklist items: 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in) | 8: Gemini's sparkle watermark (a faint four-pointed star, about 47 px across) on the back of his right hand at x 0.87, y 0.89; it comes from the base render of 2026-10-09 (run 20261009_204403 v2_0r, before the restore replaced the sparkle disc), and that picture's check on 2026-10-10 missed it | the user accepted it anyway: AskUserQuestion 2026-10-12 00:0x: 'Pin 11 pizza' approved; 'D:\Downloads\AI me\date simulate.jpg this already is best for me'
  - right: the user's favourite of pin 11 (saved by him on 2026-10-10 as D:\Downloads\AI me\date simulate.jpg): the beard fix on the picture he called perfect | 27 of 36 checklist items passed, 8 not applicable

## motorcycle-outfit-men_12_red-flags-print-tee-tote-front-print

20 pictures, 1 passed.

- **attempt 1** `20261009_155539_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.78 (Flash, pin_783485666540141702@v1, request 0c30fbc73e15)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | The user asked for the print on the FRONT, so the pin's back view became a front view: items 12, 14 and 30 compare with a back-view goal and are N/A (the pose gate says FAIL 14, 30 for that reason; 29 passes). 26 FAILS: the pin's print is a wide round geometric sans-serif in bright crimson with 'I'M A BULL' in a regular solid weight; the render has a condensed typeface in dark maroon and the last line OUTLINED (hollow letters). Face measures all inside his band (cjwr 1.138, par 2.217, jaw_iod 2.029, cheek_iod 2.308). 19 and 32 not confirmed (side curls over the ear tops; the oversized tee hides the body, the measures read bideltoid 4.95 against 5.91-6.72): listed failed (unverifiable).
  - right: identity 0.78 (accept band) | 18 of 32 checklist items passed, 11 not applicable
- **attempt 2** `20261009_155539_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (checklist)**, identity 0.77 (Flash, pin_783485666540141702@v1, request 0c30fbc73e15)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | Front view by the user's request (12, 14, 30 N/A; the gate FAILs 12/14, 14, 30 for that reason, 29 passes). 26 FAILS: the same print error as v1_0 (condensed typeface, dark maroon, last line OUTLINED). Face measures inside his band (cjwr 1.141, jaw_iod 2.009, cheek_iod 2.292; par 2.239 a hair over). 19 and 32 not confirmed: listed failed (unverifiable).
  - right: identity 0.77 (accept band) | 18 of 32 checklist items passed, 11 not applicable
- **attempt 3** `20261009_164243_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.78 (Flash, pin_783485666540141702@v2, request c02de5bf2e43)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him) | The only failed item is 32. The user asked for the print on the FRONT, so the pin's back view became a front view: 12, 14 and 30 are N/A (the pose gate says FAIL 14, 30 for that reason; 29 passes). The recipe v2 fixed v1's wrong lettering: 26 now passes. Every trusted face measure is inside his band (cjwr 1.119, par 2.184, jaw_iod 2.029, cheek_iod 2.272); pool score 0.777. 32 cannot be verified: the oversized tee covers his shoulders and upper arms (the arm measures read 'not arm skin', the body measure failed for lack of memory), only the neck and forearms show, and they look lean. The user can accept it with their words.
  - right: Print, tote, watch and mall as the pin's; his curls (ears and temples showing), full dense beard and lean face: every trusted face measure inside his band. | identity 0.78 (accept band) | 21 of 32 checklist items passed, 10 not applicable
- **attempt 4** `20261009_164243_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (checklist)**, identity 0.76 (Flash, pin_783485666540141702@v2, request c02de5bf2e43)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him) | The only failed item is 32 (see v1_0): the oversized tee hides his build; the arm measures read 'not arm skin'; the shoulder and waist measures are outside his band but unreliable under a drop-shoulder tee (bideltoid_iod 5.09 vs 5.91-6.72, shoulder_iod 5.03 vs 4.23-4.81). Front view by the user's request: 12, 14, 30 N/A (the gate FAILs 12/14, 14, 30 for that reason; 29 passes). Face measures inside his band (cjwr 1.120, par 2.198, jaw_iod 2.017, cheek_iod 2.260); pool score 0.760.
  - right: identity 0.76 (accept band) | 21 of 32 checklist items passed, 10 not applicable
- **attempt 5** `20261009_203601_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.71 (Flash, pin_783485666540141702@v3, request 777829a4002a)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture); 35 (Candid capture look) | Recipe v3 (candid rush, text mode). 34: a glowing shop name with half-legible letters (TA..NGE) behind the glass at picture-left and a second lit sign at picture-right: a text-mode picture may carry only the asked-for print. 33: a white-clad figure inside the shop at picture-left (person or mannequin, cannot be told: unverifiable). 35: the free hand and the bag are sharp, the face tack-sharp, no motion blur: it reads as a posed walking portrait, not a rushed snapshot. 32: the oversized tee hides chest and waist (unverifiable, as in v2). 12/14/30 N/A: the user asked for the front view (pose gate FAIL 14/30 for that reason). Cause: 'shopping-mall viewing gallery' brings shops with signs and mannequins whatever the paragraph says about glow.
  - right: Print exact (four crimson lines, wide round geometric sans, I'M A BULL in the regular weight, solid); identity 0.708; face, curls and full beard his; slight tilt and bag strap cut by the left edge. | identity 0.71 (accept band) | 21 of 35 checklist items passed, 10 not applicable
- **attempt 6** `20261009_203601_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (checklist)**, identity 0.74 (Flash, pin_783485666540141702@v3, request 777829a4002a)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture) | Recipe v3 (candid rush, text mode). 34: readable lit shop signs behind the glass (SOUL... at picture-left, ..Shop over the shop behind his head) and red sale boards: a text-mode picture may carry only the asked-for print. 33: headless mannequins in the shop windows and a person-like dark-haired figure at the far left inside the shop (unverifiable): a text-mode picture has no one but him. 32: the oversized tee hides chest and waist (unverifiable, as in v2). 12/14/30 N/A: the user asked for the front view. Cause: 'shopping-mall viewing gallery' brings shops with signs and mannequins whatever the paragraph says about glow.
  - right: Print exact; identity 0.743; mid-stride with the free hand motion-blurred, slight tilt, off-centre, bag cut by the left edge: the candid look the user asked for. | identity 0.74 (accept band) | 22 of 35 checklist items passed, 10 not applicable
- **attempt 7** `20261009_205525_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.75 (Flash, pin_783485666540141702@v4, request fb6b637d6305)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 35 (Candid capture look) | Recipe v4 (empty-bokeh mall walkway). 34 now passes: every sign behind him is soft unreadable glow (v3 had readable shop names). 33 still fails: a blurred dark-haired figure behind the counter at picture-left and a second blurred figure in the corridor at picture-right; the paragraph's 'He is the only person in the frame' does not keep a mall empty. 35: the free hand and the bag are sharp (no motion blur), it reads half-posed. 32: the oversized tee hides chest and waist (unverifiable, as in v2/v3). 12/14/30 N/A: the user asked for the front view.
  - right: Print exact; identity 0.754; signs all soft glow; creamy shallow depth of field. | identity 0.75 (accept band) | 22 of 35 checklist items passed, 10 not applicable
- **attempt 8** `20261009_205525_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (checklist)**, identity 0.71 (Flash, pin_783485666540141702@v4, request fb6b637d6305)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 35 (Candid capture look) | Recipe v4 (empty-bokeh mall walkway). 34 now passes: every sign behind him is soft unreadable glow (v3 had readable shop names). 33 still fails: small blurred shoppers in the atrium below at picture-left and one in the corridor at picture-right; the paragraph's 'He is the only person in the frame' does not keep a mall empty. 35: the free hand and the bag are sharp (no motion blur), it reads half-posed. 32: the oversized tee hides chest and waist (unverifiable, as in v2/v3). 12/14/30 N/A: the user asked for the front view.
  - right: Print exact; identity 0.710; signs all soft glow; creamy shallow depth of field. | identity 0.71 (accept band) | 22 of 35 checklist items passed, 10 not applicable
- **attempt 9** `20261014_065449_goal-pin12fix-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - right: pose gate passed every measured item
- **attempt 10** `20261014_065449_goal-pin12fix-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 35 (Candid capture look) | 33: the right patch still holds a faint red-brown vertical figure at about x 750, y 480-600 and the dark head-shaped blob on the shoulder at about x 675, y 520 (3x crop right_zoom_3x.jpg), so a passer-by still reads there; the grey-out removed only the red column's top. 32: the oversized tee hides chest and waist; the visible forearm and upper arm are lean with faint veins but cannot be measured against casual_front (unverifiable, as in v2-v4). 35: the free hand and the bag are clean and unblurred, it reads half-posed (as the base). Gemini sparkle of the base still at the floor bottom right (about 727, 1143).
  - right: v1: left background patch clean (the dark head-like spot is gone, soft bokeh), red column mostly faded. Print exact (pixel diff to base max 11); head, tee and tote untouched; only the grey background patches changed. | 22 of 36 checklist items passed, 11 not applicable
- **attempt 11** `20261014_065449_goal-pin12fix-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - right: pose gate passed every measured item
- **attempt 12** `20261014_065449_goal-pin12fix-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - wrong: failed checklist items: 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in); 11 (Neck and above do not look copy-pasted); 32 (His build, the same in every picture of him); 33 (Background people); 35 (Candid capture look) | 8/11/33: the grey patches came back as flat rectangles: a pink block on the left (x 80-140, y 480-570), a new bright red rectangle on the right (about x 745-775, y 560-640) and a hard dark rim along his right shoulder (x 640-700, y 500-600); worse than the base. 32 and 35 as v1.
  - right: v2: red column and the smudge are gone from the right patch wall. Print exact (pixel diff to base max 11); head, tee and tote untouched; only the grey background patches changed. | 20 of 36 checklist items passed, 11 not applicable
- **attempt 13** `20261014_065449_goal-pin12fix-send/v3_0.jpg`: **NOT CHECKED YET** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - right: pose gate passed every measured item
- **attempt 14** `20261014_065449_goal-pin12fix-send/v3_0r.jpg`: **FAIL (checklist)** (Flash, pin12fix_send@v1, request 01a424e8288a)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 35 (Candid capture look) | 33: a thin red vertical streak from the ceiling light down to about y 640 at x 755 and the dark head-shaped blob at the shoulder remain on the right (3x crop right_zoom_3x.jpg), so it still reads as a passer-by in red; left patch keeps a faint dark spot. 32 and 35 as v1.
  - right: v3: left patch softened, only a faint remnant. Print exact (pixel diff to base max 11); head, tee and tote untouched; only the grey background patches changed. | 22 of 36 checklist items passed, 11 not applicable
- **attempt 15** `20261014_080200_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.71 (Flash, pin_783485666540141702@v5, request 2db351177cb6)
  - wrong: failed checklist items: 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture) | 33: blurred shoppers remain: a pink-bodied figure left of the glass at about x 150, y 620 and a red/orange blob at the left edge (x 0-10, y 600-650), and pale figure shapes in the shop at the right (x 750-790, y 690-740) (bg_left_3x.jpg, bg_right_3x.jpg); pin12b v1 only had a faint figure at the right shoulder, so v5 is worse on 33. 34: the apostrophe in DON'T and I'M is the typographic curly one (print_compare.jpg); the pin print and pin12b have the straight tick: not letter for letter. 32: the oversized tee hides chest and waist (unverifiable, as in every pin 12 version). The Gemini sparkle sits ON the hand's knuckles (about x 727, y 1143) and would have to be removed before any export.
  - right: v5 keeps his face, hair and beard (identity 0.707); the free hand now has motion blur (v4 and the pin12b base were sharp); the ceiling and rail setting works. | identity 0.71 (accept band) | 23 of 36 checklist items passed, 10 not applicable
- **attempt 16** `20261014_080200_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (checklist)**, identity 0.72 (Flash, pin_783485666540141702@v5, request 2db351177cb6)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 32 (His build, the same in every picture of him); 33 (Background people); 34 (Text in the picture) | 19: a longer curl lock hangs down the picture-right side of the head past the ear (x 575-600, y 340-460), the current cut has the sides tapered short. 33: a dark head and dark red top at the left edge (x 0-30, y 570-620), a standing dark figure in the shop at the left (x 280-330, y 580-640) and a pink figure far right (x 800-840, y 560-620) (bg_left_3x.jpg). 34: curly apostrophes as v1. 32: the tee hides chest and waist. A faint sparkle on the floor at the wrist (about x 727, y 1140).
  - right: v2: identity 0.720; the right-side background is the cleanest of the two; motion blur on the hand. | identity 0.72 (accept band) | 22 of 36 checklist items passed, 10 not applicable
- **attempt 17** `20261021_034550_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (rejected by the user)**, identity 0.73 (Pro, pin_783485666540141702@v6, request b0daf4e8a848)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 30 (Body posture and action exactly as in the goal); 33 (Background people) | run 20261021_034550 (pin 12 v6 = v5's request on PRO, the only change): the user asked for the print on the FRONT, so this is a front view from text where the pin is a back view: the pose gate compares it with the back view anyway and FAILS (shoulders 0.069, left upper arm 24 deg); 33: a dark figure-like shape in the shop window at the picture-right edge (about x 790, y 690) that may be a passer-by: unverified; 19/26/28/31/32 not compared at the same scale (unverified); the sparkle mark stays (pale on a pale floor, a fill missed it) | the user rejected it: the user, 2026-10-21 (question box), of both pin 12 v6 renders: 'the smile is horrible, total garbage ... the subject is too close to the camera ... the background blur has to be reduced ... imitate it perfectly, even when it comes to texture, background'
  - right: Pro: the print exact in the pin's typeface and colour on the front, his curls and beard, the cream oversized tee, the white tote, the black watch, a mall corridor with no readable signs and no clear people | identity 0.73 (accept band) | 32 of 38 checklist items passed, 2 not applicable
- **attempt 18** `20261021_034550_goal-pin-783485666540141702/v2_0.jpg`: **FAIL (rejected by the user)**, identity 0.71 (Pro, pin_783485666540141702@v6, request b0daf4e8a848)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 30 (Body posture and action exactly as in the goal); 33 (Background people) | run 20261021_034550 (pin 12 v6, Pro): front view from text against a back-view pin: the pose gate FAILS (shoulders 0.100, left upper arm 26 deg); 33: not checked at 100% on every background shape: unverified; 19/26/28/31/32 not compared (unverified); sparkle stays | the user rejected it: the user, 2026-10-21 (question box), of both pin 12 v6 renders: 'the smile is horrible, total garbage ... the subject is too close to the camera ... the background blur has to be reduced ... imitate it perfectly, even when it comes to texture, background'
  - right: Pro: the print on the front, his curls and beard, the cream tee, the tote | identity 0.71 (accept band) | 32 of 38 checklist items passed, 2 not applicable
- **attempt 19** `20261021_173953_goal-pin-783485666540141702/v1_0.jpg`: **FAIL (checklist)**, identity 0.64 (Pro, pin_783485666540141702@v7, request 8b9146c76f4a)
  - wrong: failed checklist items: 34 (Text in the picture) | run 20261021_173953 (pin 12 v7, Pro, teeth mode, route text v6): a front view from text against a back-view pin, so items 12, 14 and 30 are N/A (the user changed the view: the print on the front, AGENTS.md pins 10-13 lessons); the pose gate measured it anyway and its numbers are not applicable. 34 FAIL: the pin's small 'Untld' mark below the print is not in the picture (the print design crop carries the four lines only); every shop sign is soft unreadable glow at x4-x6, one grey sign in the right corridor shows letter-like shapes and no word. 19 NOTE: the curls are fuller down the sides than his tapered cut and cover the picture-left ear. 26/32 NOTE: the oversized tee hides chest and waist; only forearms and upper arms show. The sparkle stays: the corner is busy (the hand and floor joints, texture above 9.0), so tools/sparkle_fill.py refused. Eyes 76-77 px apart: the subject is as large in the frame as in v6 (76 and 81 px); the background is in focus now (sharpness 267 and 393 against 6 and 17 in v6).
  - right: his natural open smile with his own teeth showing (lips apart 0.179 of the eye distance; IMG_6875 0.198, the cat selfie 0.175), the background in ordinary phone focus, the print exact on the front, his curls and beard, the tote and the black watch | identity 0.64 (accept band) | 29 of 38 checklist items passed, 8 not applicable
- **attempt 20** `20261021_173953_goal-pin-783485666540141702/v2_0.jpg`: **PASS (accepted by the user)**, identity 0.68 (Pro, pin_783485666540141702@v7, request 8b9146c76f4a)
  - wrong: failed checklist items: 33 (Background people); 34 (Text in the picture) | run 20261021_173953 (pin 12 v7, Pro, teeth mode, route text v6): a front view from text against a back-view pin, so items 12, 14 and 30 are N/A (the user changed the view: the print on the front, AGENTS.md pins 10-13 lessons); the pose gate measured it anyway and its numbers are not applicable. 34 FAIL: the pin's small 'Untld' mark below the print is not in the picture (the print design crop carries the four lines only); every shop sign is soft unreadable glow at x4-x6, one grey sign in the right corridor shows letter-like shapes and no word. 19 NOTE: the curls are fuller down the sides than his tapered cut and cover the picture-left ear. 26/32 NOTE: the oversized tee hides chest and waist; only forearms and upper arms show. The sparkle stays: the corner is busy (the hand and floor joints, texture above 9.0), so tools/sparkle_fill.py refused. Eyes 76-77 px apart: the subject is as large in the frame as in v6 (76 and 81 px); the background is in focus now (sharpness 267 and 393 against 6 and 17 in v6). 33 FAIL: two figure-shaped forms inside the left shop front (a white-topped one and a dark one, about 25 px tall): a mannequin and a customer cannot be told apart at that size. | the user accepted it anyway: the user, 2026-10-21 (question box): 'Render 2 (Recommended)' for pin 12 v7 (its smile matches his teeth best; the missing Untld mark and the two shop-window figure-shaped forms stay on record)
  - right: the widest, most natural open smile of the two with his own teeth (wide row of upper teeth, uneven edges, the thin line between the front teeth; lips apart 0.141 of the eye distance), the atrium sharp in ordinary phone focus, the print exact, his curls and lean face, the tote and the black watch | identity 0.68 (accept band) | 28 of 38 checklist items passed, 8 not applicable

## motorcycle-outfit-men_13_bowling-alley-red-ball-looking-right-smiling

17 pictures, 0 passed.

- **attempt 1** `20261009_155544_goal-pin-783485666540141619/v1_0.jpg`: **FAIL (checklist)**, identity 0.53 (Flash, pin_783485666540141619@v1, request fddd7edacaac)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL (14: body 0.063 right of the pin's place; 29: torso x1.26 the pin's size; 30: both hands off by 0.12 and 0.085). The shoulders also turned toward the camera. The head is a near full profile (yaw -70), more than the user's 'slight side profile'. Identity 0.525. Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: identity 0.53 (accept band) | 15 of 32 checklist items passed, 8 not applicable
- **attempt 2** `20261009_155544_goal-pin-783485666540141619/v2_0.jpg`: **FAIL (checklist)**, identity 0.44 (Flash, pin_783485666540141619@v1, request fddd7edacaac)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL (12/14 head 0.169 off; 14 body 0.124 off; 29 torso x1.23; 30 hands off by 0.148 and 0.118). Identity 0.440. Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: identity 0.44 (gray zone, needs a human eye) | 14 of 32 checklist items passed, 8 not applicable
- **attempt 3** `20261009_164540_goal-pin-783485666540141619/v1_0.jpg`: **FAIL (checklist)**, identity 0.47 (Flash, pin_783485666540141619@v3, request 657cd5086f78)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL even with the layout sketch and skeleton: 14 body 0.216 of the frame right of the pin's place, 12/14 head 0.264 off, 29 torso x1.24, 30 hands off by 0.23 and 0.21, stance 0.59 of the pin's. The sketch was ignored. Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: identity 0.47 (gray zone, needs a human eye) | 14 of 32 checklist items passed, 8 not applicable
- **attempt 4** `20261009_164540_goal-pin-783485666540141619/v2_0.jpg`: **FAIL (checklist)**, identity 0.48 (Flash, pin_783485666540141619@v3, request 657cd5086f78)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | Pose gate FAIL 14, 29, 30 (the same size and place errors as v1_0). Items not looked at closely are listed as failed (unverifiable): the picture is superseded.
  - right: identity 0.48 (gray zone, needs a human eye) | 15 of 32 checklist items passed, 8 not applicable
- **attempt 5** `20261009_205207_goal-pin-783485666540141619/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.09 (Flash, pin_783485666540141619@v5, request 9953901eb220)
  - wrong: pose gate failed: head position shift 0.050 (goal x0.26 y0.24, render x0.31 y0.24)
  - right: identity 0.09 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 6** `20261009_205207_goal-pin-783485666540141619/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141619@v5, request 9953901eb220)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN) | STAGE 1 of the two-stage plan (recipe v5: replace him in place, head still away): the intermediate base for the head-turn edit, not a result. Pose gate: body position shift 0.005, torso size x1.05, torso and all four arm segments 1-5 degrees off, all PASS (the v1/v3 samples were x1.23-1.26 and shifted right); only the head position fails, shift 0.050 against 0.04, because the head already turns slightly toward picture-right (a sliver of beard shows), which is the user's own direction for stage 2. 21 and 31 cannot be judged with the face turned away. Screens, the left-edge person and the lanes are the pin's own pixels (restore ECC 0.999, 76.8% copied).
  - right: First render that keeps the pin man's place and size; restore makes the screens' names and the scrolling line identical to the pin. | 24 of 35 checklist items passed, 7 not applicable
- **attempt 7** `20261009_205207_goal-pin-783485666540141619/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.05 (Flash, pin_783485666540141619@v5, request 9953901eb220)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.250 (goal x0.25 y0.32, render x0.50 y0.32); head position shift 0.287 (goal x0.26 y0.24, render x0.55 y0.23); size in the frame (torso) x1.16; his left forearm direction 19 deg off; his right hand position shift 0.281 (goal x0.35 y0.53, render x0.63 y0.56); his left hand position shift 0.198 (goal x0.16 y0.50, render x0.36 y0.53); feet apart (stance) x0.69 (goal 0.35, render 0.24 torso lengths)
  - right: identity 0.05 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 8** `20261009_205207_goal-pin-783485666540141619/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141619@v5, request 9953901eb220)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN) | STAGE 1 (recipe v5), not a result: pose gate FAIL 12/14, 14, 29, 30 (head and body position, size, posture); the face is turned away so 21 and 31 cannot be judged. Restore ECC 0.973.
  - right: 22 of 35 checklist items passed, 7 not applicable
- **attempt 9** `20261014_035627_goal-pin13head-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin13head_send@v1, request eb91da4f9e32)
  - right: pose gate passed every measured item
- **attempt 10** `20261014_035627_goal-pin13head-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin13head_send@v1, request eb91da4f9e32)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | 12/14: the whole-picture pose gate fails only head position (shift 0.056, limit 0.04): his head turned from the rear profile toward the camera to show the smile, the pose change the user asked for ('looking right, smiling, slight side profile'): recorded as a fail; 21/31/32 not compared at one scale beside the character sheet (the face is in a 3/4 profile; the body is the stage-1 base, shirt covering it) and left for the user's eye. The other three returns were refused by the paste (re-framed, ECC 0.50/0.64, shift 12 px); v1 pasted with --max-shift 0.03 (shift 4.7 px, ECC 0.909)
  - right: 25 of 36 checklist items passed, 6 not applicable
- **attempt 11** `20261014_035627_goal-pin13head-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin13head_send@v1, request eb91da4f9e32)
  - right: pose gate passed every measured item
- **attempt 12** `20261014_035627_goal-pin13head-send/v3_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin13head_send@v1, request eb91da4f9e32)
  - wrong: pose gate failed: head position shift 0.049 (goal x0.55 y0.50, render x0.59 y0.53)
- **attempt 13** `20261014_035627_goal-pin13head-send/v4_0.jpg`: **NOT CHECKED YET** (Flash, pin13head_send@v1, request eb91da4f9e32)
  - right: pose gate passed every measured item
- **attempt 14** `20261021_034227_goal-pin-783485666540141619/v1_0.jpg`: **FAIL (rejected by the user)**, identity 0.50 (Pro, pin_783485666540141619@v7, request ad05cc3324bd)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 38 (His teeth, when they show, are his own) | run 20261021_034227 (pin 13 v7 = v3's request on PRO, the only change): pose gate FAIL: shoulders 0.151 right of the pin's, torso x1.31 larger, right hand 0.210 and left hand 0.123 off, left forearm 17 deg off (items 14, 29, 30; the same failure as every Flash run); the head turn and smile are the user's request; 21: identity 0.50, the gray zone just under the 0.52 accept band, the picture reads as him by eye: unverified; 34: the screens' lettering is garbled (the menu line reads 'Simply eean the atar to view our menu'); 38: his teeth show at about 3 px, not verifiable at that size; 19/26/28/31/32 not compared at the same scale (unverified); the sparkle mark stays (busy corner) | the user rejected it: the user, 2026-10-21 (question box), of pin 13 v7: 'The pants are below the buttocks, hanging on the hamstring or the knee ... unlike the given goal ... baggy but properly worn around the waist itself'
  - right: Pro: his curls and beard, the smile in a slight side profile, looking back over his right shoulder as asked, the grey tee, the wristbands, the red ball, the alley, the star decals | identity 0.50 (gray zone, needs a human eye) | 31 of 38 checklist items passed, 1 not applicable
- **attempt 15** `20261021_034227_goal-pin-783485666540141619/v2_0.jpg`: **FAIL (rejected by the user)**, identity 0.51 (Pro, pin_783485666540141619@v7, request ad05cc3324bd)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 38 (His teeth, when they show, are his own) | run 20261021_034227 (pin 13 v7, Pro): pose gate FAIL: shoulders 0.163 right of the pin's, torso x1.32, hands 0.207 / 0.127 off, left forearm 16 deg off; 21: identity 0.51, gray zone; 34: the screens' lettering is slightly garbled ('Simply scan tha star'); 38: teeth about 3 px, not verifiable; 19/26/28/31/32 not compared (unverified); sparkle stays (busy corner) | the user rejected it: the user, 2026-10-21 (question box), of pin 13 v7: 'The pants are below the buttocks, hanging on the hamstring or the knee ... unlike the given goal ... baggy but properly worn around the waist itself'
  - right: Pro: the smile in a slight side profile over the right shoulder as asked, his curls and beard, the grey tee and wristbands, the red ball, the alley | identity 0.51 (gray zone, needs a human eye) | 31 of 38 checklist items passed, 1 not applicable
- **attempt 16** `20261021_224339_goal-pin-783485666540141619/v1_0.jpg`: **FAIL (rejected by the user)**, identity 0.50 (Pro, pin_783485666540141619@v8, request af1c1e7d7799)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 38 (His teeth, when they show, are his own) | run 20261021_224339 (pin 13 v8, Pro, the jeans worn at the waist): pose gate FAIL: shoulders 0.204 off, torso x1.69 larger, right hand 0.355 and left hand 0.222 off, left forearm 16 deg off; the jeans sit at his waist as the user asked (the v7 flaw is fixed); 34: the screens' lettering is garbled (the menu line reads 'Simply acan the star to view our menu, ordo' and the scores are garbled); 38: his teeth show on a face only 98 px (render 1) wide, not verifiable beside his smile photos at that size; 21: identity 0.50, the gray zone under the 0.52 accept band, a 3/4 profile, the picture reads as him by eye: unverified; 27: the torso size and the hand positions of v7 are back; the head turn and smile are the user's request; 26/32 NOTE: the tee hides the body (only the arms show), not compared at the same scale (unverified); the sparkle stays (busy corner, texture 14.3). | the user rejected it: the user, 2026-10-22 (question box): 'Neither, new render' for pin 13 v8 (both renders)
  - right: the jeans worn at the waist with a belt line and straight baggy legs, the grey tee, the wristbands, the red ball, the lane and its star decals, his curls and beard, the smile in a 3/4 profile looking along the lane | identity 0.50 (gray zone, needs a human eye) | 26 of 38 checklist items passed, 5 not applicable
- **attempt 17** `20261021_224339_goal-pin-783485666540141619/v2_0.jpg`: **FAIL (rejected by the user)**, identity 0.46 (Pro, pin_783485666540141619@v8, request af1c1e7d7799)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 34 (Text in the picture); 38 (His teeth, when they show, are his own) | run 20261021_224339 (pin 13 v8, Pro, the jeans worn at the waist): pose gate FAIL: shoulders 0.244 off, torso x1.32 larger, right hand 0.277 and left hand 0.219 off, feet apart x0.71 (limit 0.75); the jeans sit at his waist as the user asked (the v7 flaw is fixed); 34: the screens' lettering is garbled (the menu line reads 'Sinply scan the star to view our menu, ordo' and the scores are garbled); 38: his teeth show on a face only 80 px (render 2) wide, not verifiable beside his smile photos at that size; 21: identity 0.46, the gray zone under the 0.52 accept band, a 3/4 profile, the picture reads as him by eye: unverified; 27: the torso size and the hand positions of v7 are back; the head turn and smile are the user's request; 26/32 NOTE: the tee hides the body (only the arms show), not compared at the same scale (unverified); the sparkle stays (busy corner, texture 15.4). | the user rejected it: the user, 2026-10-22 (question box): 'Neither, new render' for pin 13 v8 (both renders)
  - right: the jeans worn at the waist with a belt line and straight baggy legs, the grey tee, the wristbands, the red ball, the lane and its star decals, his curls and beard, the smile in a 3/4 profile looking along the lane | identity 0.46 (gray zone, needs a human eye) | 26 of 38 checklist items passed, 5 not applicable

## motorcycle-outfit-men_14_gokarna-clifftop-shirtless-cap-looking-down

43 pictures, 3 passed.

- **attempt 1** `20261010_205035_goal-pin-783485666540168309/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.30 (Flash, pin_783485666540168309@v1, request 2008e9569cbc)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.086 (goal x0.44 y0.62, render x0.46 y0.54); head position shift 0.097 (goal x0.52 y0.52, render x0.57 y0.44); size in the frame (torso) x1.16; his left hand position shift 0.096 (goal x0.54 y0.84, render x0.62 y0.77)
  - right: identity 0.30 (gray zone, needs a human eye)
- **attempt 2** `20261010_205035_goal-pin-783485666540168309/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.41 (Flash, pin_783485666540168309@v1, request 2008e9569cbc)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.060 (goal x0.44 y0.62, render x0.47 y0.57); head position shift 0.079 (goal x0.52 y0.52, render x0.59 y0.48); size in the frame (torso) x1.13; his left forearm direction 23 deg off; his left hand position shift 0.096 (goal x0.54 y0.84, render x0.62 y0.78)
  - right: identity 0.41 (gray zone, needs a human eye)
- **attempt 3** `20261011_033245_goal-pin-783485666540168309/v1_0.jpg`: **NOT CHECKED YET**, identity 0.25 (Flash, pin_783485666540168309@v2, request 4b6f628d9ddb)
  - right: pose gate passed every measured item | identity 0.25 (gray zone, needs a human eye)
- **attempt 4** `20261011_033245_goal-pin-783485666540168309/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168309@v2, request 4b6f628d9ddb)
  - wrong: failed checklist items: 11 (Neck and above do not look copy-pasted); 36 (His janeu and chain) | stage 1 base: the framing holds (pose gate passed in full). 11: a pale halo in the sky around his head and cap where the restored pin sky meets Gemini's lighter sky (stage 2 redraws the sky). 36: the janeu runs nearly straight down the picture-right side instead of crossing to his right hip at picture-left; chain and pendant correct.
  - right: two stages hold the frame; backward cap, chain with pendant, no tattoos or bangle, pumped torso | 29 of 36 checklist items passed, 5 not applicable
- **attempt 5** `20261011_033245_goal-pin-783485666540168309/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.33 (Flash, pin_783485666540168309@v2, request 4b6f628d9ddb)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.067 (goal x0.44 y0.62, render x0.45 y0.55); head position shift 0.079 (goal x0.52 y0.52, render x0.58 y0.47); size in the frame (torso) x1.16; his left forearm direction 20 deg off; his right hand position shift 0.087 (goal x0.38 y0.85, render x0.30 y0.83); his left hand position shift 0.070 (goal x0.54 y0.84, render x0.60 y0.79)
  - right: identity 0.33 (gray zone, needs a human eye)
- **attempt 6** `20261011_033245_goal-pin-783485666540168309/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168309@v2, request 4b6f628d9ddb)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal) | drawn larger again: torso x1.16, shoulders 0.067 and head 0.079 off, hands 0.07-0.09 off (pose gate)
  - right: 27 of 36 checklist items passed, 5 not applicable
- **attempt 7** `20261011_103210_goal-pin14s2-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14s2_send@v1, request 773a41573551)
  - right: pose gate passed every measured item
- **attempt 8** `20261011_103210_goal-pin14s2-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin14s2_send@v1, request 773a41573551)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | the user, 2026-10-11: 'something looks off. It is not replicating the ref goal images as it is. Both V1 and V2. Also, the physique that it is giving me is not looking like mine, and the face looks off. In terms of leanness and body fat percentage, the face still looks a lot leaner than the body.' My checklist had passed both (FAILURE_LOG F28).
  - right: 27 of 36 checklist items passed, 5 not applicable
- **attempt 9** `20261011_103210_goal-pin14s2-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14s2_send@v1, request 773a41573551)
  - right: pose gate passed every measured item
- **attempt 10** `20261011_103210_goal-pin14s2-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin14s2_send@v1, request 773a41573551)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | the user, 2026-10-11: 'something looks off. It is not replicating the ref goal images as it is. Both V1 and V2. Also, the physique that it is giving me is not looking like mine, and the face looks off. In terms of leanness and body fat percentage, the face still looks a lot leaner than the body.' My checklist had passed both (FAILURE_LOG F28).
  - right: 27 of 36 checklist items passed, 5 not applicable
- **attempt 11** `20261011_234656_goal-pin-783485666540168309/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity -0.02 (Flash, pin_783485666540168309@v3, request 82fd652e6bc6)
  - wrong: pose gate failed: his left hand position shift 0.081 (goal x0.54 y0.84, render x0.63 y0.83)
  - right: identity -0.02 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 12** `20261011_234656_goal-pin-783485666540168309/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity -0.04 (Flash, pin_783485666540168309@v3, request 82fd652e6bc6)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.115 (goal x0.44 y0.62, render x0.43 y0.51); head position shift 0.113 (goal x0.52 y0.52, render x0.59 y0.43); size in the frame (torso) x1.32; his left forearm direction 25 deg off; his right hand position shift 0.130 (goal x0.38 y0.85, render x0.26 y0.81); his left hand position shift 0.102 (goal x0.54 y0.84, render x0.63 y0.79)
  - right: identity -0.04 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 13** `20261012_020337_goal-pin14v4-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin14v4_send@v1, request 8454b7d9bb9b)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.055 (goal x0.53 y0.19, render x0.59 y0.20); head position shift 0.138 (goal x0.55 y0.08, render x0.69 y0.07)
- **attempt 14** `20261012_020337_goal-pin14v4-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin14v4_send@v1, request 8454b7d9bb9b)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.058 (goal x0.53 y0.19, render x0.58 y0.23); head position shift 0.093 (goal x0.55 y0.08, render x0.64 y0.08)
- **attempt 15** `20261012_031630_goal-pin14janeu2-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14janeu2_send@v1, request 21834342744a)
  - right: pose gate passed every measured item
- **attempt 16** `20261012_031630_goal-pin14janeu2-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14janeu2_send@v1, request 21834342744a)
  - right: pose gate passed every measured item
- **attempt 17** `20261012_061458_goal-pin14janeu3-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin14janeu3_send@v1, request 0457b7da9b29)
  - wrong: pose gate failed: his left hand position shift 0.095 (goal x0.93 y0.82, render x0.86 y0.76)
- **attempt 18** `20261012_061458_goal-pin14janeu3-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14janeu3_send@v1, request 0457b7da9b29)
  - right: pose gate passed every measured item
- **attempt 19** `20261012_163848_goal-pin14ghost-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14ghost_send@v1, request ab36c9b0751e)
  - right: pose gate passed every measured item
- **attempt 20** `20261012_163848_goal-pin14ghost-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14ghost_send@v1, request ab36c9b0751e)
  - right: pose gate passed every measured item
- **attempt 21** `20261012_170539_goal-pin14head/v1_0.png`: **NOT CHECKED YET**, identity 0.27 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.27 (gray zone, needs a human eye)
- **attempt 22** `20261012_170539_goal-pin14head/v2_0.png`: **NOT CHECKED YET**, identity 0.26 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.26 (gray zone, needs a human eye)
- **attempt 23** `20261012_170539_goal-pin14head/v3_0.png`: **NOT CHECKED YET**, identity 0.35 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.35 (gray zone, needs a human eye)
- **attempt 24** `20261012_170539_goal-pin14head/v4_0.png`: **NOT CHECKED YET**, identity 0.45 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.45 (gray zone, needs a human eye)
- **attempt 25** `20261012_170539_goal-pin14head/v5_0.png`: **NOT CHECKED YET**, identity 0.37 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.37 (gray zone, needs a human eye)
- **attempt 26** `20261012_170539_goal-pin14head/v6_0.png`: **NOT CHECKED YET**, identity 0.40 (Flash, pin14head@v2, request 1f6e2f98b3b2)
  - right: identity 0.40 (gray zone, needs a human eye)
- **attempt 27** `20261013_040232_goal-pin14head3-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin14head3_send@v1, request c4b852c15f33)
  - wrong: pose gate failed: head position shift 0.378 (goal x0.25 y0.52, render x0.63 y0.51)
- **attempt 28** `20261013_040232_goal-pin14head3-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin14head3_send@v1, request c4b852c15f33)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 30 (Body posture and action exactly as in the goal); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | 30: left forearm 19 deg off (limit 15) on the whole pin; 26/32 as v2_0r; a stray curl pokes above the cap rim at picture-right
  - right: 26 of 36 checklist items passed, 5 not applicable
- **attempt 29** `20261013_040232_goal-pin14head3-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin14head3_send@v1, request c4b852c15f33)
  - wrong: pose gate failed: head position shift 0.388 (goal x0.25 y0.52, render x0.64 y0.51)
- **attempt 30** `20261013_040232_goal-pin14head3-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin14head3_send@v1, request c4b852c15f33)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | 26/32: the body is narrower than his: shoulders and arms thinner than pumped_front.jpg and than IMG_7008 at one scale (body_check.jpg beside the picture); the paste mask was the pin man's outline grown 10 px, so a build wider than his could not be drawn (the user: 'the physique that it is giving me is not looking like mine', twice). 21/31: awaiting the user's eye (the face is in clear profile under a beard, not measurable). Pose gate on the whole pin: PASS (body shift 0.006, head 0.021)
  - right: head swapped by a region edit that kept the pin man's cap, head place, bow and down-right gaze; janeu thin and diagonal, ghost gone; the head reads as his (curls, full beard, ear); only the head and neck changed (max 4 below y 0.65) | 27 of 36 checklist items passed, 5 not applicable
- **attempt 31** `20261013_044047_goal-pin14body2-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
  - right: pose gate passed every measured item
- **attempt 32** `20261013_044047_goal-pin14body2-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
- **attempt 33** `20261013_044047_goal-pin14body2-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
  - right: pose gate passed every measured item
- **attempt 34** `20261013_044047_goal-pin14body2-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
- **attempt 35** `20261013_044047_goal-pin14body2-send/v3_0.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
  - right: pose gate passed every measured item
- **attempt 36** `20261013_044047_goal-pin14body2-send/v3_0r.jpg`: **FAIL (rejected by the user)** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | 26/32: still narrower than his pumped standard: shoulder line 0.739 of torso length against about 0.89 (turn-corrected) for pumped_front.jpg, 0.756 was the +6% cap taken to stay near the pin's outline; the near upper arm is as wide as his (0.244 vs 0.189-0.225). 21/31: awaiting the user's eye (a bearded profile cannot be scored). Pose gate on the whole pin PASS: body shift 0.006, torso x0.95, left forearm 10 deg | the user rejected it: the user, 2026-10-17, of the results copy motorcycle-outfit-men_14_gokarna-clifftop-shirtless-cap-looking-down_v3.jpg: 'these are bad' (earlier accepted: AskUserQuestion 2026-10-13 14:1x: 'Does this look like you?' -> 'Yes, export it')
  - right: his build in the pin's outline: broader deltoids, fuller chest and arms with veins, body hair; the janeu one thin diagonal with the ghost gone; the chain silver; the head (cap, curls, beard, ear) untouched; edges clean at 3x/4x; no colour step at the collar | 27 of 36 checklist items passed, 5 not applicable
- **attempt 37** `20261013_044047_goal-pin14body2-send/v4_0.jpg`: **NOT CHECKED YET** (Flash, pin14body2_send@v1, request 5fc0ebdee405)
  - right: pose gate passed every measured item
- **attempt 38** `20261013_184543_goal-pin14place-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin14place_send@v1, request 059ebfe2f6fa)
  - right: pose gate passed every measured item
- **attempt 39** `20261013_184543_goal-pin14place-send/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin14place_send@v1, request 059ebfe2f6fa)
  - wrong: failed checklist items: 30 (Body posture and action exactly as in the goal) | 30: the pose gate on the whole pin reads his left forearm 19 deg off (limit 15) and his left upper arm 10 deg; the same arm read 10 and 5 deg on the approved v3_0r; his pixels are unchanged apart from a 4 px edge ring and the hands did not move (0.026 -> 0.029), so this is the detector reading the arm against grass and red rock instead of a dark hillside, not a different pose; recorded as a fail, as the rule says
  - right: his picture the user approved (v3_0r) with the pin's land and sea replaced by a Gokarna coast: red laterite cliff, coconut palms, a curved sandy bay, turquoise surf; sky, horizon and him kept; the old ridge's ghost and a sky seam removed | 30 of 36 checklist items passed, 5 not applicable
- **attempt 40** `20261021_032954_goal-pin-783485666540168309/v1_0.jpg`: **PASS (accepted by the user)**, identity 0.45 (Flash, pin_783485666540168309@v4, request 1dfcaf5cedad)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 36 (His janeu and chain) | run 20261021_032954 (pin 14 v4, one whole render with the Gokarna place, front torso crop as the body photo): pose gate FAIL: torso drawn x1.29 larger, head 0.124 and shoulders 0.091 off, left forearm 25 deg off, left hand 0.090 off; 36: the janeu runs nearly straight down the picture-right side to the waistband, not across the chest to his right hip as in the references; 21: bowed profile, identity 0.45 not decisive: unverified; 37 not applicable: the place was changed on purpose (the user's Gokarna request); 19/26/28/31/32 not compared at the same scale (unverified); the sparkle mark stays (busy corner: grass and ground) | the user accepted it anyway: the user, 2026-10-21 (question box), of this render: 'captures the musculature perfectly, but it has softened or increased the fat percentage in my face. The face is not as sharp as the body looks here. Rest is the perfect image. Both the background and everything are perfect in this: body positioning, the subject, everything.'
  - right: the Gokarna coast as the user asked: red laterite cliff, the path, the bay with palms, turquoise sea; the maroon cap backwards, his curls and beard line, the silver chain with its black square pendant, the pumped chest and arms, black jeans with the white waistband | identity 0.45 (gray zone, needs a human eye) | 30 of 38 checklist items passed, 2 not applicable
- **attempt 41** `20261021_032954_goal-pin-783485666540168309/v2_0.jpg`: **FAIL (checklist)**, identity 0.19 (Flash, pin_783485666540168309@v4, request 1dfcaf5cedad)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 36 (His janeu and chain) | run 20261021_032954 (pin 14 v4): pose gate FAIL: torso x1.21 larger, head 0.078 and shoulders 0.094 off, left forearm 40 deg off, hands 0.071-0.111 off; 36: the janeu runs straight down the middle of the torso; 21: identity 0.19, bowed profile: unverified; 37 not applicable (place changed on purpose); 19/26/28/31/32 not compared (unverified); sparkle stays (busy corner)
  - right: the Gokarna coast with the path, palms, the bay and the surf; the cap, curls, beard, chain with pendant, pumped chest and arms | identity 0.19 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 30 of 38 checklist items passed, 2 not applicable
- **attempt 42** `20261021_223909_goal-pin-783485666540168309/v1_0.jpg`: **PASS (accepted by the user)**, identity 0.28 (Flash, pin_783485666540168309@v5, request 762443ceef1f)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 36 (His janeu and chain) | run 20261021_223909 (pin 14 v5, Flash, one whole render, Gokarna in words, the sharp-face item and his real profile IMG_6863): pose gate FAIL: torso x1.15 larger, shoulders 0.127 and head 0.080 off, left forearm 17 deg off, left hand 0.095 off; 36: the janeu hangs nearly straight down the picture-right side of the chest to the waistband, not across the chest to his right hip (07_review/torso_janeu_x1_5.jpg); 21: bowed profile, identity 0.28 below the 0.50 profile band: unverified, by eye the curls, beard, nose and jaw read as his; 37 not applicable: the place was changed on purpose (the user's Gokarna request); 27: the pose-gate misses and the straight janeu of v4 are back; the face is sharp now (07_review/face_sharpness_compare.jpg); 26/32 NOTE: not compared at the same scale beside the pumped standard (unverified); the sparkle stays (busy corner: soil and grass, texture 52.4). | the user accepted it anyway: the user, 2026-10-22 (question box): 'Keep both' for pin 14 v5 (render 1 and render 2)
  - right: the Gokarna coast as the user asked (red laterite cliff, the bay with palms, the sea), the maroon cap backwards, the sharp face with the jaw and nose crisp, his curls and beard, the silver chain with its pendant, the pumped chest and arms, black jeans with the white waistband | identity 0.28 (gray zone, needs a human eye) | 25 of 38 checklist items passed, 6 not applicable
- **attempt 43** `20261021_223909_goal-pin-783485666540168309/v2_0.jpg`: **PASS (accepted by the user)**, identity 0.35 (Flash, pin_783485666540168309@v5, request 762443ceef1f)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 36 (His janeu and chain) | run 20261021_223909 (pin 14 v5, Flash, one whole render, Gokarna in words, the sharp-face item and his real profile IMG_6863): pose gate FAIL: torso x1.07, shoulders 0.051 and head 0.054 off, left upper arm 22 deg and forearm 30 deg off, left hand 0.081 off; 36: the janeu hangs nearly straight down the picture-right side of the chest to the waistband, not across the chest to his right hip (07_review/torso_janeu_x1_5.jpg); 21: bowed profile, identity 0.35 below the 0.50 profile band: unverified, by eye the curls, beard, nose and jaw read as his; 37 not applicable: the place was changed on purpose (the user's Gokarna request); 27: the pose-gate misses and the straight janeu of v4 are back; the face is sharp now (07_review/face_sharpness_compare.jpg); 26/32 NOTE: not compared at the same scale beside the pumped standard (unverified); the sparkle stays (busy corner: soil and grass, texture 26.4). | the user accepted it anyway: the user, 2026-10-22 (question box): 'Keep both' for pin 14 v5 (render 1 and render 2)
  - right: the Gokarna coast as the user asked (red laterite cliff, the bay with palms, the sea), the maroon cap backwards, the sharp face with the jaw and nose crisp, his curls and beard, the silver chain with its pendant, the pumped chest and arms, black jeans with the white waistband | identity 0.35 (gray zone, needs a human eye) | 25 of 38 checklist items passed, 6 not applicable

## motorcycle-outfit-men_15_mirror-selfie-back-hand-behind-neck-shirtless

26 pictures, 0 passed.

- **attempt 1** `20261010_205703_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.17 (Flash, pin_783485666540141726@v1, request 9ec46c8bcd43)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.148 (goal x0.59 y0.22, render x0.57 y0.37); head position shift 0.154 (goal x0.59 y0.17, render x0.46 y0.25)
  - right: identity 0.17 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 2** `20261010_205703_goal-pin-783485666540141726/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.32 (Flash, pin_783485666540141726@v1, request 9ec46c8bcd43)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.146 (goal x0.59 y0.22, render x0.63 y0.36); head position shift 0.217 (goal x0.59 y0.17, render x0.40 y0.26)
  - right: identity 0.32 (gray zone, needs a human eye)
- **attempt 3** `20261011_014109_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.05 (Flash, pin_783485666540141726@v2, request df4b27ede9a2)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.149 (goal x0.59 y0.22, render x0.63 y0.36)
  - right: identity 0.05 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 4** `20261011_104706_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin_783485666540141726@v3, request a57010d1c5f7)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.076 (goal x0.59 y0.22, render x0.53 y0.27)
- **attempt 5** `20261011_104706_goal-pin-783485666540141726/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141726@v3, request a57010d1c5f7)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 36 (His janeu and chain) | Body only (v3): Gemini redrew the head as his anyway (curls, beard) and kept the pin's frame. 14: shoulder midpoint 0.076 off (render y 0.27, pin 0.22; limit 0.04), likely the pin man's massive trapezius lifting his shoulder line. 36: a mirror picture, so his left shoulder is at picture-right and the janeu must slant down to picture-left; it slants the other way, as on his real back unmirrored.
  - right: 31 of 36 checklist items passed, 3 not applicable
- **attempt 6** `20261011_104706_goal-pin-783485666540141726/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.02 (Flash, pin_783485666540141726@v3, request a57010d1c5f7)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.166 (goal x0.59 y0.22, render x0.50 y0.36)
  - right: identity 0.02 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 7** `20261011_104706_goal-pin-783485666540141726/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141726@v3, request a57010d1c5f7)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's) | Body only (v3): the head stayed the pin man's as asked (straight brown hair), so stage 2 (the head swap) would be needed; 14: shoulder midpoint 0.166 off. The janeu slants correctly for the mirror.
  - right: 29 of 36 checklist items passed, 3 not applicable
- **attempt 8** `20261011_113205_goal-pin15janeu-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin15janeu_send@v1, request f1c1db0b87b0)
  - right: pose gate passed every measured item
- **attempt 9** `20261011_113205_goal-pin15janeu-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin15janeu_send@v1, request f1c1db0b87b0)
  - right: pose gate passed every measured item
- **attempt 10** `20261011_113205_goal-pin15janeu-send/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin15janeu_send@v1, request f1c1db0b87b0)
  - wrong: failed checklist items: 8 (Nothing looks unreal or monsterish, at thumbnail size or zoomed in); 11 (Neck and above do not look copy-pasted); 14 (Face position and alignment in the frame match the goal) | the user, 2026-10-11 16:25: 'visibly shows erase and drag tool usage'. The janeu fix pasted Gemini's softer redraw over about 40% of his back (an airbrushed patch), a smeared highlight beside the new thread near the shoulder blade, and the old thread's lower end left as a broken stub (FAILURE_LOG F30). 14: shoulders 0.076 off.
  - right: 30 of 36 checklist items passed, 3 not applicable
- **attempt 11** `20261011_164737_goal-pin15stub-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin15stub_send@v1, request e4a6e7d7ddd1)
  - wrong: pose gate failed: person found no person in goal
- **attempt 12** `20261011_164737_goal-pin15stub-send/v1_0r.jpg`: **FAIL (rejected by the user)** (Flash, pin15stub_send@v1, request e4a6e7d7ddd1)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal) | pin 15 after F30: the janeu fix re-pasted along narrow bands only, then the stub removed and the thread continued by a band-only edit; his skin elsewhere is v3 v1_0r's own. 14: shoulders 0.076 off (limit 0.04). For the user's eye: his approval was for the earlier version. | the user rejected it: the user, 2026-10-17, of the results copy motorcycle-outfit-men_15_mirror-selfie-back-hand-behind-neck-shirtless_v2.jpg: 'these are bad' (earlier accepted: AskUserQuestion 2026-10-12 00:0x, 'Which of these do you approve as they are?': Pin 15 back (approve the cleaned back as it is))
  - right: 32 of 36 checklist items passed, 3 not applicable
- **attempt 13** `20261011_164737_goal-pin15stub-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin15stub_send@v1, request e4a6e7d7ddd1)
  - wrong: pose gate failed: person found no person in goal
- **attempt 14** `20261021_031826_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.13 (Flash, pin_783485666540141726@v4, request 9f3a108e5312)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.171 (goal x0.59 y0.22, render x0.62 y0.39); head position shift 0.170 (goal x0.59 y0.17, render x0.46 y0.28)
  - right: identity 0.13 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 15** `20261021_031826_goal-pin-783485666540141726/v1_0s.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666540141726@v4, request 9f3a108e5312)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 36 (His janeu and chain); 37 (Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17) | run 20261021_031826 (pin 15 v4, one whole render, body photo cropped to the frame): pose gate FAIL: shoulders 0.171 and head 0.170 off (he sits lower, camera pulled back), and the canvas came back 3:4 (0.747) where the pin is 0.881 (items 29/37); 36: the janeu starts at the picture-left shoulder and runs down to picture-right, wrong way for a mirror picture (it must slant down to picture-left); 21: identity 0.13, his head is turned away: unverified; 19/26/28/31/32 not compared at the same scale (unverified); sparkle mark filled with tools/sparkle_fill.py (v1_0s = v1_0 + that fill only) | the user rejected it: the user, 2026-10-21 (question box), of the two pin 15 renders: 'Neither is the correct answer' (the pose exaggerates the body's V shape, which these renders do not; see the three videos they added)
  - right: his curls, the beard line, the pumped back with the janeu, the silver chain, the phone and the bathroom as drawn | 31 of 38 checklist items passed, 1 not applicable
- **attempt 16** `20261021_031826_goal-pin-783485666540141726/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.35 (Flash, pin_783485666540141726@v4, request 9f3a108e5312)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.163 (goal x0.59 y0.22, render x0.49 y0.35)
  - right: identity 0.35 (gray zone, needs a human eye)
- **attempt 17** `20261021_031826_goal-pin-783485666540141726/v2_0s.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666540141726@v4, request 9f3a108e5312)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 36 (His janeu and chain) | run 20261021_031826 (pin 15 v4): pose gate FAIL: shoulders 0.163 off (he sits lower; y 0.35 against 0.22) in the pin's own canvas; 36: the janeu slants the wrong way for a mirror picture; 21: identity 0.35, his head shows more face in profile than the pin's bowed-away head: unverified; 19/26/28/31/32 not compared at the same scale (unverified); sparkle filled (v2_0s) | the user rejected it: the user, 2026-10-21 (question box), of the two pin 15 renders: 'Neither is the correct answer' (the pose exaggerates the body's V shape, which these renders do not; see the three videos they added)
  - right: kept the pin's canvas and the bathroom; his curls, beard, the pumped back, the silver chain, the phone | 33 of 38 checklist items passed, 1 not applicable
- **attempt 18** `20261021_115213_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.15 (Flash, pin_783485666540141726@v5, request 4c6e96262d1d)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.142 (goal x0.59 y0.22, render x0.57 y0.36); head position shift 0.160 (goal x0.59 y0.17, render x0.47 y0.27)
  - right: identity 0.15 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 19** `20261021_115213_goal-pin-783485666540141726/v1_0s.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666540141726@v5, request 4c6e96262d1d)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 36 (His janeu and chain) | run 20261021_115213 (pin 15 v5: a mirrored raised-arm frame of IMG_7420 as the pose-matched body reference, back wording no longer narrowing it): the pose gate FAILS: shoulders 0.142 and head 0.160 off (he still sits lower in the frame), but the back now has the wide V, the near shoulder blade and the lat edge as in the pin; 36: the janeu starts at the picture-left of the neck and runs down to picture-right, the wrong way for this mirror picture (the approved 10-11 version ran from the picture-right shoulder down to picture-left); 21: identity 0.15 with the face turned away: unverified; 19/26/28/31/32 not compared at the same scale (unverified); sparkle filled with tools/sparkle_fill.py (v1_0s = v1_0 + that fill only) | the user rejected it: the user, 2026-10-21 (question box), of pin 15 v5: 'The back musculature is still bad. It is underestimating my actual back musculature and flexed'
  - right: the V of the back as the pose gives it, the raised arm and hand behind the neck, the head bowed to picture-left, his curls and beard, the silver chain, the bathroom, the phone | 33 of 38 checklist items passed, 1 not applicable
- **attempt 20** `20261021_115213_goal-pin-783485666540141726/v2_0.jpg`: **FAIL (rejected by the user)**, identity 0.19 (Flash, pin_783485666540141726@v5, request 4c6e96262d1d)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 36 (His janeu and chain) | run 20261021_115213 (pin 15 v5): the pose gate FAILS: shoulders 0.154 and head 0.195 off (sits lower and to the right); the back has the wide V and the lat edge; 36: the janeu runs the wrong way for a mirror picture (picture-left neck down to picture-right); 21: identity 0.19, face turned away: unverified; 19/26/28/31/32 not compared (unverified); the sparkle stays (busy corner: the sweatpants) | the user rejected it: the user, 2026-10-21 (question box), of pin 15 v5: 'The back musculature is still bad. It is underestimating my actual back musculature and flexed'
  - right: the V of the back, the raised arm behind the neck, the bowed head, his curls and beard, the chain, the bathroom with its tiles | identity 0.19 (rejected band, not meaningful when the face is hidden, bowed or in profile) | 33 of 38 checklist items passed, 1 not applicable
- **attempt 21** `20261021_174638_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.01 (Flash, pin_783485666540141726@v6, request 0eac9050109e)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.177 (goal x0.59 y0.22, render x0.59 y0.40); head position shift 0.243 (goal x0.59 y0.17, render x0.39 y0.30)
  - right: identity 0.01 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 22** `20261021_174638_goal-pin-783485666540141726/v1_0s.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141726@v6, request 0eac9050109e)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back) | run 20261021_174638 (pin 15 v6, Flash, his real flexed IMG_7420 frame, unflipped, as the body; physique real-back-flexed): one picture from two calls (the second call returned nothing: the session turned unauthenticated at 17:51). The pose gate FAILS: shoulders 0.177 and head 0.243 off (he sits lower and smaller in the frame: head at x0.39 y0.30 against the pin's x0.59 y0.17). 27 FAIL: the head and shoulder position misses of v4 and v5 are back. 21: identity 0.0129, the face is turned down and 75% covered, so it cannot be compared at the references' scale; by eye the curls, beard and ear read as his. 26/32 NOTE: in the side-by-side sheet at one height (07_review/back_mass_compare.jpg) v6's back spans less of the frame than v5's and shows less mass than the pin man's and than his real flexed frame. The sparkle is filled (v1_0s.jpg: 1,649 star pixels only, every other pixel unchanged).
  - right: the janeu runs the right way (picture-right nape to picture-left hip), the hand behind the neck with the raised arm, the bowed head, his curls and beard, the silver chain, the bathroom with its tiles and door, the V of the back | 28 of 38 checklist items passed, 6 not applicable
- **attempt 23** `20261021_231703_goal-pin-783485666540141726/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.18 (Flash, pin_783485666540141726@v8, request 76de5545faf5)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.167 (goal x0.59 y0.22, render x0.51 y0.37)
  - right: identity 0.18 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 24** `20261021_231703_goal-pin-783485666540141726/v1_0s.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666540141726@v8, request 76de5545faf5)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back) | run 20261021_231703 (pin 15 v8, Flash, the approved pumped back crop mirrored plus his real flexed IMG_7420 frame as the two BODY references, no size cap): pose gate FAILS on item 14 only: shoulders 0.167 lower in the frame than the pin's (the head items pass now; v6 missed them by 0.243); 21: identity 0.18, the face is turned down and 58% covered, so it cannot be compared at the references' scale: unverified, by eye the curls, beard and ear read as his; 27: the shoulders sit lower than the pin's, as in v4 to v6; 26/32 NOTE: in the side-by-side sheet (07_review/back_mass_compare_v8.jpg) the back is broader and thicker than v6's (shoulders, trapezius, lats, the V) and still less massive than the pin man's; 19 NOTE: the curls above and behind the ear are as dense as on top where his sides are tapered; the sparkle is filled (1,652 star pixels only, every other pixel unchanged). | the user rejected it: the user, 2026-10-22 (question box), of pin 15 v8: 'yes, we need a new render, and I want you to understand that the person in the Google Pinterest image is pushing their hips forward and leaning their back backwards towards the camera. That is, the back is relatively closer to the camera than the hips. This creates the back to look more triangular, that is, shoulders wider and waist narrower. Implement that pose exactly as it is.'
  - right: the broad thick back with the wide lats and the V, the janeu running the mirror way from the nape to the left hip, the raised arm with the hand on the neck, the head items of the pose gate passing, the silver chain, the bathroom with its tile strip, door and handle, the phone in his hand | 29 of 38 checklist items passed, 6 not applicable
- **attempt 25** `20261021_231703_goal-pin-783485666540141726/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.22 (Flash, pin_783485666540141726@v8, request 76de5545faf5)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.179 (goal x0.59 y0.22, render x0.50 y0.38)
  - right: identity 0.22 (gray zone, needs a human eye)
- **attempt 26** `20261021_231703_goal-pin-783485666540141726/v2_0s.jpg`: **FAIL (rejected by the user)** (Flash, pin_783485666540141726@v8, request 76de5545faf5)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 21 (It is unmistakably him, not just attractive); 27 (None of the flaws recorded for earlier versions of this photo is back) | run 20261021_231703 (pin 15 v8, Flash, the approved pumped back crop mirrored plus his real flexed IMG_7420 frame as the two BODY references, no size cap): pose gate FAILS on item 14 only: shoulders 0.179 lower in the frame than the pin's (the head items pass now; v6 missed them by 0.243); 21: identity 0.22, the face is turned down and 81% covered, so it cannot be compared at the references' scale: unverified, by eye the curls, beard and ear read as his; 27: the shoulders sit lower than the pin's, as in v4 to v6; 26/32 NOTE: in the side-by-side sheet (07_review/back_mass_compare_v8.jpg) the back is broader and thicker than v6's (shoulders, trapezius, lats, the V) and still less massive than the pin man's; 19 NOTE: the curls above and behind the ear are as dense as on top where his sides are tapered; the sparkle is filled (1,693 star pixels only, every other pixel unchanged). | the user rejected it: the user, 2026-10-22 (question box), of pin 15 v8: 'yes, we need a new render ... the person in the Google Pinterest image is pushing their hips forward and leaning their back backwards towards the camera ... Implement that pose exactly as it is.'
  - right: the broad thick back with the wide lats and the V, the janeu running the mirror way from the nape to the left hip, the raised arm with the hand on the neck, the head items of the pose gate passing, the silver chain, the bathroom with its tile strip, door and handle, the phone in his hand | 29 of 38 checklist items passed, 6 not applicable

## motorcycle-outfit-men_16_surfboard-sandy-path-shirtless-looking-back

42 pictures, 1 passed.

- **attempt 1** `20261010_202925_goal-pin-783485666540168242/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.63 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: pose gate failed: head position shift 0.041 (goal x0.55 y0.39, render x0.54 y0.35); size in the frame (torso) x1.21; his left forearm direction 72 deg off; his left hand position shift 0.189 (goal x0.44 y0.62, render x0.54 y0.78)
  - right: identity 0.63 (accept band)
- **attempt 2** `20261010_202925_goal-pin-783485666540168242/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.59 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: pose gate failed: size in the frame (torso) x1.08; his left forearm direction 74 deg off; his left hand position shift 0.183 (goal x0.44 y0.62, render x0.56 y0.76)
  - right: identity 0.59 (accept band)
- **attempt 3** `20261010_210305_goal-pin-783485666540168242/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.63 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: pose gate failed: size in the frame (torso) x1.07; his left forearm direction 71 deg off; his left hand position shift 0.178 (goal x0.44 y0.62, render x0.54 y0.76)
  - right: identity 0.63 (accept band)
- **attempt 4** `20261010_210305_goal-pin-783485666540168242/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin_783485666540168242@v1, request 22dd03316f44)
- **attempt 5** `20261010_210305_goal-pin-783485666540168242/v2_0.jpg`: **NOT CHECKED YET**, identity 0.68 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - right: pose gate passed every measured item | identity 0.68 (accept band)
- **attempt 6** `20261010_210305_goal-pin-783485666540168242/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 32 (His build, the same in every picture of him) | The user, 2026-10-10: 'pin 16 - face almost there but still not accurate, needs fixing' (item 21). 32: the pin man's calf tattoo and his ring kept. Fix: his face redrawn from his references in a crop pasted back, then the calf and the hand.
  - right: pose gate passed in full; the hand holds the fin as in the pin; janeu and chain on the chest; restore ECC 0.995 | 29 of 36 checklist items passed, 5 not applicable
- **attempt 7** `20261011_030505_goal-pin-783485666540168242/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.56 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: pose gate failed: his left forearm direction 75 deg off; his left hand position shift 0.182 (goal x0.44 y0.62, render x0.55 y0.77)
  - right: identity 0.56 (accept band)
- **attempt 8** `20261011_030505_goal-pin-783485666540168242/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 30 (Body posture and action exactly as in the goal); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | 30: his arm hangs at his side and the board floats unheld (left forearm 69-75 degrees off, hand 0.18-0.19 off; FAILURE_LOG F5/F19); 32: the pin man's calf tattoo is back at the frame's bottom edge; 21: the same face as run 2's v2_0r, which the user called 'almost there but still not accurate', identity lower (0.56-0.59); 36: the janeu not verifiable at this scale; 29 (v2): torso x1.08
  - right: 27 of 36 checklist items passed, 5 not applicable
- **attempt 9** `20261011_030505_goal-pin-783485666540168242/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.59 (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: pose gate failed: size in the frame (torso) x1.08; his left forearm direction 69 deg off; his left hand position shift 0.190 (goal x0.44 y0.62, render x0.57 y0.76)
  - right: identity 0.59 (accept band)
- **attempt 10** `20261011_030505_goal-pin-783485666540168242/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v1, request 22dd03316f44)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal); 32 (His build, the same in every picture of him); 36 (His janeu and chain) | 30: his arm hangs at his side and the board floats unheld (left forearm 69-75 degrees off, hand 0.18-0.19 off; FAILURE_LOG F5/F19); 32: the pin man's calf tattoo is back at the frame's bottom edge; 21: the same face as run 2's v2_0r, which the user called 'almost there but still not accurate', identity lower (0.56-0.59); 36: the janeu not verifiable at this scale; 29 (v2): torso x1.08
  - right: 26 of 36 checklist items passed, 5 not applicable
- **attempt 11** `20261011_101820_goal-pin-783485666540168242/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.67 (Flash, pin_783485666540168242@v2, request ce1d43cb3b55)
  - wrong: pose gate failed: size in the frame (torso) x1.12; his left forearm direction 73 deg off; his left hand position shift 0.204 (goal x0.44 y0.62, render x0.56 y0.78)
  - right: identity 0.67 (accept band)
- **attempt 12** `20261011_101820_goal-pin-783485666540168242/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v2, request ce1d43cb3b55)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 29 (The distance from the camera is the same as in the goal); 30 (Body posture and action exactly as in the goal) | 30: the arm hangs again with the torso-only BODY references (left forearm 73 degrees off, hand 0.20 off); 29: torso x1.12. FAILURE_LOG F22.
  - right: 28 of 36 checklist items passed, 5 not applicable
- **attempt 13** `20261011_101820_goal-pin-783485666540168242/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.63 (Flash, pin_783485666540168242@v2, request ce1d43cb3b55)
  - wrong: pose gate failed: his left forearm direction 70 deg off; his left hand position shift 0.176 (goal x0.44 y0.62, render x0.54 y0.76)
  - right: identity 0.63 (accept band)
- **attempt 14** `20261011_101820_goal-pin-783485666540168242/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v2, request ce1d43cb3b55)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 30 (Body posture and action exactly as in the goal) | 30: the arm hangs again with the torso-only BODY references (left forearm 70 degrees off, hand 0.18 off). FAILURE_LOG F22.
  - right: 29 of 36 checklist items passed, 5 not applicable
- **attempt 15** `20261011_120200_goal-pin-783485666540168242/v1_0.jpg`: **NOT CHECKED YET**, identity -0.07 (Flash, pin_783485666540168242@v3, request 29a07fcd65d3)
  - right: pose gate passed every measured item | identity -0.07 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 16** `20261011_120200_goal-pin-783485666540168242/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v3, request 29a07fcd65d3)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN) | stage 1 of 2 (body only): the arm stays on the fin (pose gate passed); the head is still the pin man's by design; stage 2 swaps it (pin16s2_head@v1)
  - right: body only holds the arm on the fin where v1/v2 dropped it in 7 of 8 pictures | 27 of 36 checklist items passed, 5 not applicable
- **attempt 17** `20261011_120200_goal-pin-783485666540168242/v2_0.jpg`: **NOT CHECKED YET**, identity -0.02 (Flash, pin_783485666540168242@v3, request 29a07fcd65d3)
  - right: pose gate passed every measured item | identity -0.02 (rejected band, not meaningful when the face is hidden, bowed or in profile)
- **attempt 18** `20261011_120200_goal-pin-783485666540168242/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540168242@v3, request 29a07fcd65d3)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN) | stage 1 of 2 (body only): the arm stays on the fin (pose gate passed); the head is still the pin man's by design; stage 2 swaps it (pin16s2_head@v1)
  - right: body only holds the arm on the fin where v1/v2 dropped it in 7 of 8 pictures | 27 of 36 checklist items passed, 5 not applicable
- **attempt 19** `20261011_123206_goal-pin16s2-head/v1_0.png`: **FAIL (checklist)**, identity 0.78 (Flash, pin16s2_head@v1, request b0ae7ea654a9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 11 (Neck and above do not look copy-pasted) | head swap (replicate, zone head, foreign): gate-invalid: head x1.153 (limit 0.94-1.04), face light dE 33.8 (limit 20), face 18.0 brighter than the neck (limit 10), the judge saw a seam; the indoor face references' light carries over (FAILURE_LOG F27)
  - right: identity 0.78 (accept band) | 27 of 36 checklist items passed, 5 not applicable
- **attempt 20** `20261011_123206_goal-pin16s2-head/v2_0.png`: **FAIL (checklist)**, identity 0.76 (Flash, pin16s2_head@v1, request b0ae7ea654a9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 11 (Neck and above do not look copy-pasted) | head swap (replicate, zone head, foreign): gate-invalid: head x1.194 (limit 0.94-1.04), face light dE 32.6 (limit 20), face 18.8 brighter than the neck (limit 10), the judge saw a seam; the indoor face references' light carries over (FAILURE_LOG F27)
  - right: identity 0.76 (accept band) | 27 of 36 checklist items passed, 5 not applicable
- **attempt 21** `20261011_123206_goal-pin16s2-head/v3_0.png`: **FAIL (checklist)**, identity 0.76 (Flash, pin16s2_head@v1, request b0ae7ea654a9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 11 (Neck and above do not look copy-pasted) | head swap (replicate, zone head, foreign): gate-invalid: head x1.125 (limit 0.94-1.04), face light dE 33.3 (limit 20), face 14.5 brighter than the neck (limit 10), the judge saw a seam; the indoor face references' light carries over (FAILURE_LOG F27)
  - right: identity 0.76 (accept band) | 27 of 36 checklist items passed, 5 not applicable
- **attempt 22** `20261011_123206_goal-pin16s2-head/v4_0.png`: **FAIL (checklist)**, identity 0.79 (Flash, pin16s2_head@v1, request b0ae7ea654a9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 11 (Neck and above do not look copy-pasted) | head swap (replicate, zone head, foreign): gate-invalid: head x1.167 (limit 0.94-1.04), face light dE 35.0 (limit 20), face 27.4 brighter than the neck (limit 10), the judge saw a seam; the indoor face references' light carries over (FAILURE_LOG F27)
  - right: identity 0.79 (accept band) | 27 of 36 checklist items passed, 5 not applicable
- **attempt 23** `20261011_233349_goal-pin16s2-head/v1_0.png`: **NOT CHECKED YET**, identity 0.59 (Flash, pin16s2_head@v2, request 4a48e03cc59b)
  - right: identity 0.59 (accept band)
- **attempt 24** `20261011_233349_goal-pin16s2-head/v2_0.png`: **NOT CHECKED YET**, identity 0.61 (Flash, pin16s2_head@v2, request 4a48e03cc59b)
  - right: identity 0.61 (accept band)
- **attempt 25** `20261011_233349_goal-pin16s2-head/v3_0.png`: **NOT CHECKED YET**, identity 0.50 (Flash, pin16s2_head@v2, request 4a48e03cc59b)
  - right: identity 0.50 (gray zone, needs a human eye)
- **attempt 26** `20261011_233349_goal-pin16s2-head/v4_0.png`: **NOT CHECKED YET**, identity 0.57 (Flash, pin16s2_head@v2, request 4a48e03cc59b)
  - right: identity 0.57 (accept band)
- **attempt 27** `20261012_021718_goal-pin16s2-head/v1_0.png`: **NOT CHECKED YET**, identity 0.56 (Flash, pin16s2_head@v3, request f436abebeb9a)
  - right: identity 0.56 (accept band)
- **attempt 28** `20261012_021718_goal-pin16s2-head/v2_0.png`: **NOT CHECKED YET**, identity 0.57 (Flash, pin16s2_head@v3, request f436abebeb9a)
  - right: identity 0.57 (accept band)
- **attempt 29** `20261012_021718_goal-pin16s2-head/v3_0.png`: **NOT CHECKED YET**, identity 0.58 (Flash, pin16s2_head@v3, request f436abebeb9a)
  - right: identity 0.58 (accept band)
- **attempt 30** `20261012_021718_goal-pin16s2-head/v4_0.png`: **NOT CHECKED YET**, identity 0.59 (Flash, pin16s2_head@v3, request f436abebeb9a)
  - right: identity 0.59 (accept band)
- **attempt 31** `20261012_165252_goal-pin16eyes-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes_send@v2, request d0ee446dcec1)
  - right: pose gate passed every measured item
- **attempt 32** `20261012_165252_goal-pin16eyes-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes_send@v2, request d0ee446dcec1)
  - right: pose gate passed every measured item
- **attempt 33** `20261012_165252_goal-pin16eyes-send/v3_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes_send@v2, request d0ee446dcec1)
  - right: pose gate passed every measured item
- **attempt 34** `20261012_165252_goal-pin16eyes-send/v4_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes_send@v2, request d0ee446dcec1)
  - right: pose gate passed every measured item
- **attempt 35** `20261012_171655_goal-pin16eyes2-send/v1_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
  - right: pose gate passed every measured item
- **attempt 36** `20261012_171655_goal-pin16eyes2-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
- **attempt 37** `20261012_171655_goal-pin16eyes2-send/v2_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
  - right: pose gate passed every measured item
- **attempt 38** `20261012_171655_goal-pin16eyes2-send/v2_0r.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
- **attempt 39** `20261012_171655_goal-pin16eyes2-send/v3_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
  - right: pose gate passed every measured item
- **attempt 40** `20261012_171655_goal-pin16eyes2-send/v3_0r.jpg`: **PASS (accepted by the user)** (Flash, pin16eyes2_send@v1, request b10b193b3642)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | 21: awaiting the user's eye: his earlier verdict on the base was 'almost there but still not accurate' and 'space between eyes', traced to the far eye's gaze (FAILURE_LOG F42); this picture fixes exactly that eye and nothing else (59 px changed in the frame) | the user accepted it anyway: AskUserQuestion 2026-10-13: 'Is the eye problem gone?' -> 'Yes, export it'
  - right: the far eye redrawn by grey-out so both eyes look the same way: eye agreement -0.32 pasted / -0.25 at 4x (his band -0.34..-0.18; base -0.07), openness 0.277 / 0.370 inside his band, iris dark brown and the near eye's size, no seam (lids are the base's pixels) | 30 of 36 checklist items passed, 5 not applicable
- **attempt 41** `20261012_171655_goal-pin16eyes2-send/v4_0.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)
  - right: pose gate passed every measured item
- **attempt 42** `20261012_171655_goal-pin16eyes2-send/v4_0r.jpg`: **NOT CHECKED YET** (Flash, pin16eyes2_send@v1, request b10b193b3642)

## motorcycle-outfit-men_17_balcony-back-shirtless-cap-railing

11 pictures, 1 passed.

- **attempt 1** `20261010_210811_goal-pin-783485666540141762/v1_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.24 (Flash, pin_783485666540141762@v1, request 24a5487c0725)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.205 (goal x0.32 y0.34, render x0.53 y0.37); size in the frame (torso) x0.93; his right forearm direction 18 deg off; his left forearm direction 20 deg off; his right hand position shift 0.133 (goal x0.55 y0.60, render x0.68 y0.60); his left hand position shift 0.144 (goal x0.15 y0.61, render x0.30 y0.61)
  - right: identity 0.24 (gray zone, needs a human eye)
- **attempt 2** `20261010_210811_goal-pin-783485666540141762/v2_0.jpg`: **FAIL (pose gate, not checked)**, identity 0.25 (Flash, pin_783485666540141762@v1, request 24a5487c0725)
  - wrong: pose gate failed: body position (shoulder midpoint) shift 0.042 (goal x0.32 y0.34, render x0.36 y0.35)
  - right: identity 0.25 (gray zone, needs a human eye)
- **attempt 3** `20261010_210811_goal-pin-783485666540141762/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin_783485666540141762@v1, request 24a5487c0725)
  - wrong: failed checklist items: 14 (Face position and alignment in the frame match the goal); 36 (His janeu and chain) | The user, 2026-10-10: 'pin 17, not exactly the same pose, but plus points for making the face visible in the right amount' (item 12 accepted by the user: the face visible as here). 14: shoulder midpoint 0.042 off (pose gate limit 0.04), the pose not exactly the pin's. 36: the chain reads gold where his is silver; the janeu runs correctly.
  - right: the user: the face visible in the right amount (keep this head turn in the next version); restore with the reflections excluded; pumped back; janeu direction | 30 of 36 checklist items passed, 4 not applicable
- **attempt 4** `20261011_225040_goal-pin17v2-body/v1_0.jpg`: **NOT CHECKED YET**, identity 0.22 (Flash, pin17v2_body@v1, request 3be38d4cf722)
  - right: pose gate passed every measured item | identity 0.22 (gray zone, needs a human eye)
- **attempt 5** `20261011_225040_goal-pin17v2-body/v1_0r.jpg`: **FAIL (checklist)** (Flash, pin17v2_body@v1, request 3be38d4cf722)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 27 (None of the flaws recorded for earlier versions of this photo is back); 36 (His janeu and chain) | 26: a black underwear band shows above the sweatpants' waistband, which the pin does not have. 27 and 36: his neck chain drawn gold again (F14), his is silver
  - right: 30 of 36 checklist items passed, 3 not applicable
- **attempt 6** `20261011_225040_goal-pin17v2-body/v2_0.jpg`: **NOT CHECKED YET**, identity 0.26 (Flash, pin17v2_body@v1, request 3be38d4cf722)
  - right: pose gate passed every measured item | identity 0.26 (gray zone, needs a human eye)
- **attempt 7** `20261011_225040_goal-pin17v2-body/v2_0r.jpg`: **FAIL (checklist)** (Flash, pin17v2_body@v1, request 3be38d4cf722)
  - wrong: failed checklist items: 27 (None of the flaws recorded for earlier versions of this photo is back); 36 (His janeu and chain) | 12 N/A: the user on v1's v2_0r, 'plus points for making the face visible in the right amount' (this head keeps that turn, chin lowered toward the pin's). 27 and 36: F14's flaw is back: his neck chain is drawn gold where his is silver (pumped_back.jpg shows it silver), despite 'silver, never gold' in the prompt; the janeu is thin and in place (left shoulder at picture-left to the right hip at picture-right, into the waistband)
  - right: body only on the composite held the pin's exact posture (pose gate pass, shoulders now within 0.04) with his head turned so his face shows; the janeu came out thin; bracelet, tattoo and the pin man's reflections gone | 31 of 36 checklist items passed, 3 not applicable
- **attempt 8** `20261012_014900_goal-pin17chain-send/v1_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin17chain_send@v1, request 000e952f0e52)
  - wrong: pose gate failed: head position shift 0.362 (goal x0.53 y0.42, render x0.18 y0.33)
- **attempt 9** `20261012_014900_goal-pin17chain-send/v1_0r.jpg`: **NOT CHECKED YET** (Flash, pin17chain_send@v1, request 000e952f0e52)
- **attempt 10** `20261012_014900_goal-pin17chain-send/v2_0.jpg`: **FAIL (pose gate, not checked)** (Flash, pin17chain_send@v1, request 000e952f0e52)
  - wrong: pose gate failed: head position shift 0.373 (goal x0.53 y0.42, render x0.17 y0.33)
- **attempt 11** `20261012_014900_goal-pin17chain-send/v2_0r.jpg`: **PASS (all 36 items)** (Flash, pin17chain_send@v1, request 000e952f0e52)
  - right: pin 17 v2 = v1's liked head on the pin's exact body (composite + body only), then the chain fixed alone in a narrow band with his real chain as the reference | 33 of 36 checklist items passed, 3 not applicable

## own-photos_01_kayak-current-look

20 pictures, 0 passed.

- **attempt 1** `20261007_032800_goal-google-1-img-5549/v1_0.jpg`: **FAIL (checklist)**, identity 0.50 (Pro, google-1__IMG_5549@v1, request 4b57dca53b66)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 21: by eye the face stays close to his earlier face in the photo (identity 0.50), not clearly the current references' face; 28: medium curls without the short faded sides of the current references, and the beard only a little fuller than in the photo
  - right: pose gate PASS; light x0.98, face/neck 1.14 vs the photo's 1.12; glasses, smile, life jacket, kayak, sunset and framing kept; C2PA Valid | pose gate passed every measured item | identity 0.50 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 2** `20261007_032800_goal-google-1-img-5549/v2_0.jpg`: **FAIL (checklist)**, identity 0.33 (Pro, google-1__IMG_5549@v1, request 4b57dca53b66)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 21: the face is rounder and fuller than his lean current face (identity 0.33); 28: big loose curls all around instead of the tight curls with short faded sides of the references
  - right: pose gate PASS; light x0.98, face/neck 1.11 vs 1.12; scene, glasses and smile kept | pose gate passed every measured item | identity 0.33 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 3** `20261007_035216_goal-google-1-img-5549/v1_0.jpg`: **FAIL (checklist)**, identity 0.39 (Pro, google-1__IMG_5549@v2, request 9e60df6bed61)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 21: identity 0.39 and by eye still his earlier face; 28: curls without visible short faded sides, beard only a little fuller (the geometry wording did not take on this sample)
  - right: v2 (hair geometry): pose gate PASS; light x1.04, face/neck 1.08 vs 1.12; glasses and smile kept | pose gate passed every measured item | identity 0.39 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 4** `20261007_035216_goal-google-1-img-5549/v2_0.jpg`: **FAIL (checklist)**, identity 0.43 (Pro, google-1__IMG_5549@v2, request 9e60df6bed61)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 21: identity 0.43, very close to the photo's earlier face (grey diff to the photo only 8.3); 28: no short faded sides, beard close to the photo's
  - right: v2: pose gate PASS; light x1.00, face/neck 1.14 vs 1.12; scene unchanged | pose gate passed every measured item | identity 0.43 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 5** `20261007_035223_goal-google-1-img-5549/v1_0.jpg`: **FAIL (checklist)**, identity 0.44 (Pro, google-1__IMG_5549@v3, request 6ccd5badba8f)
  - wrong: failed checklist items: 10 (The face is not brighter than the neck and body); 21 (It is unmistakably him, not just attractive) | 10: face/neck 1.35 vs the photo's 1.12, the face reads brighter than his neck; 21: identity 0.44 (gray zone), by eye his current look, for the user to confirm
  - right: v3 (research options): tight curls with short faded sides, full beard, glasses and smile; pose gate PASS; scene unchanged | pose gate passed every measured item | identity 0.44 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 6** `20261007_035223_goal-google-1-img-5549/v2_0.jpg`: **FAIL (checklist)**, identity 0.63 (Pro, google-1__IMG_5549@v3, request 6ccd5badba8f)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body) | 9/10: the face is lit brighter than the backlit scene allows (face x1.33 of the photo's, limit 1.30; face/neck 1.25 vs 1.12)
  - right: v3: identity 0.63 (accepted) and by eye his current look: tight curls with faded sides, full beard; glasses, smile, kayak and sunset kept; pose gate PASS | pose gate passed every measured item | identity 0.63 (accept band) | 25 of 30 checklist items passed, 3 not applicable
- **attempt 7** `20261007_040448_goal-google-1-img-5549/v1_0.jpg`: **NOT CHECKED YET**, identity 0.52 (Pro, google-1__IMG_5549@v4, request cc4bbd1d8879)
  - right: pose gate passed every measured item | identity 0.52 (accept band)
- **attempt 8** `20261007_040448_goal-google-1-img-5549/v2_0.jpg`: **NOT CHECKED YET**, identity 0.37 (Pro, google-1__IMG_5549@v4, request cc4bbd1d8879)
  - right: pose gate passed every measured item | identity 0.37 (gray zone, needs a human eye)
- **attempt 9** `20261008_231632_goal-google-1-img-5549/v1_0.png`: **FAIL (checklist)**, identity 0.55 (Flash, google-1__IMG_5549@v5, request 306d01d43fd2)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 32 (His build, the same in every picture of him) | kayak v5 attempt 1: the old photo's haircut (full sides over the ears) (19, 28); the body is the old photo's (26, 32, forced). The user, 2026-10-08: 'body and hair rework needed since the current physique and face has been changed as can be seen in the reference images, hence can't be considered best'. FORCED: the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop (no body pass in its lineage).
  - right: identity 0.55 (accept band) | 24 of 32 checklist items passed, 4 not applicable
- **attempt 10** `20261008_231632_goal-google-1-img-5549/v2_0.png`: **FAIL (checklist)**, identity 0.60 (Flash, google-1__IMG_5549@v5, request 306d01d43fd2)
  - wrong: failed checklist items: 11 (Neck and above do not look copy-pasted); 19 (All of the hair is his own); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | kayak v5 attempt 2: a lighter, yellower rectangle of sky around his head where the crop was pasted back (the returned crop's sky is up to 3.8 levels lighter; the drift gate SSIM/mean diff does not catch a uniform shift) (11, 26); hair keeps the old photo's cut: full curly sides over the ears, where his references (character me@v1) have the sides tapered short with the ears and temples showing (items 19, 28). N/A: 3/20 no reflection of him; 15 his own photo; 17 the source shows an open smile, not a laugh (the attractiveness policy closed it, as in the kayak versions the user called perfect).
  - right: tight current curls on top, calm expression, identity 0.598 | identity 0.60 (accept band) | 24 of 32 checklist items passed, 4 not applicable
- **attempt 11** `20261008_231653_goal-google-1-img-5549/v1_0.png`: **FAIL (checklist)**, identity 0.66 (Pro, google-1__IMG_5549@v6, request 46a45a03e6d2)
  - wrong: failed checklist items: 11 (Neck and above do not look copy-pasted); 19 (All of the hair is his own); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | kayak v6 (Pro) attempt 1: a warmer, orange rectangle of sky around his head (11, 26); hair keeps the old photo's cut: full curly sides over the ears, where his references (character me@v1) have the sides tapered short with the ears and temples showing (items 19, 28). N/A: 3/20 no reflection of him; 15 his own photo; 17 the source shows an open smile, not a laugh (the attractiveness policy closed it, as in the kayak versions the user called perfect).
  - right: identity 0.661 (highest), head size 0.972, curls | identity 0.66 (accept band) | 24 of 32 checklist items passed, 4 not applicable
- **attempt 12** `20261008_231653_goal-google-1-img-5549/v2_0.png`: **FAIL (checklist)**, identity 0.62 (Pro, google-1__IMG_5549@v6, request 46a45a03e6d2)
  - wrong: failed checklist items: 11 (Neck and above do not look copy-pasted); 19 (All of the hair is his own); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | kayak v6 (Pro) attempt 2: a faint lighter rectangle of sky behind his head (11, 26); hair keeps the old photo's cut: full curly sides over the ears, where his references (character me@v1) have the sides tapered short with the ears and temples showing (items 19, 28). N/A: 3/20 no reflection of him; 15 his own photo; 17 the source shows an open smile, not a laugh (the attractiveness policy closed it, as in the kayak versions the user called perfect).
  - right: identity 0.621, more top volume like his current hair | identity 0.62 (accept band) | 24 of 32 checklist items passed, 4 not applicable
- **attempt 13** `20261008_233522_goal-google-1-img-5549/v1_0.png`: **FAIL (checklist)**, identity 0.61 (Flash, google-1__IMG_5549@v7, request 5c1cd798cbde)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | kayak v7 attempt 1: the body is the old photo's (26, 32, forced). The user, 2026-10-08: 'body and hair rework needed since the current physique and face has been changed as can be seen in the reference images, hence can't be considered best'. FORCED: the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop (no body pass in its lineage).
  - right: identity 0.61 (accept band) | 26 of 32 checklist items passed, 4 not applicable
- **attempt 14** `20261008_233522_goal-google-1-img-5549/v2_0.png`: **FAIL (checklist)**, identity 0.60 (Flash, google-1__IMG_5549@v7, request 5c1cd798cbde)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo); 32 (His build, the same in every picture of him) | kayak v7 attempt 2: the body is the old photo's (26, 32, forced). The user, 2026-10-08: 'body and hair rework needed since the current physique and face has been changed as can be seen in the reference images, hence can't be considered best'. FORCED: the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop (no body pass in its lineage).
  - right: identity 0.60 (accept band) | 26 of 32 checklist items passed, 4 not applicable
- **attempt 15** `20261009_010101_goal-google-1-img-5549/v1_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v8, request da8716fa9b4c)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak pass A (body pass, character me@v2): the body came back unchanged: the AI body judge says 'the same', silhouette widths 1.00 of the original, and by eye the arms and torso are the old photo's, fuller than IMG_6923 (26, 32). An intermediate picture: the head is the old photo's (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable
- **attempt 16** `20261009_010101_goal-google-1-img-5549/v2_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v8, request da8716fa9b4c)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak pass A (body pass, character me@v2): the body came back unchanged: the AI body judge says 'the same', silhouette widths 1.00 of the original, and by eye the arms and torso are the old photo's, fuller than IMG_6923 (26, 32). An intermediate picture: the head is the old photo's (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable
- **attempt 17** `20261009_034105_goal-google-1-img-5549/v1_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v9, request ee9c1eb49e81)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak v9 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable
- **attempt 18** `20261009_034105_goal-google-1-img-5549/v2_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v9, request ee9c1eb49e81)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak v9 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable
- **attempt 19** `20261009_034105_goal-google-1-img-5549/v3_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v9, request ee9c1eb49e81)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak v9 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable
- **attempt 20** `20261009_034105_goal-google-1-img-5549/v4_0.png`: **FAIL (checklist)** (Flash, google-1__IMG_5549@v9, request ee9c1eb49e81)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | kayak v9 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 22 of 32 checklist items passed, 4 not applicable

## own-photos_02_stained-glass-mirror-current-look

18 pictures, 0 passed.

- **attempt 1** `20261007_032805_goal-google-4-img-5850-original/v1_0.jpg`: **FAIL (checklist)**, identity 0.30 (Pro, google-4__IMG_5850_Original@v1, request 0998195128e0)
  - wrong: failed checklist items: 9 (The light on the face matches the photo); 10 (The face is not brighter than the neck and body); 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 9/10: the face is darker than the photo's face (light x0.73, limit 0.77-1.30); 21: profile face, identity 0.30, not verifiable by the agent; 28: curls all around instead of the short faded sides of the references
  - right: pose gate PASS; current curly hair, full beard and glasses on him AND in the window reflection; scene, colours, clothes and framing kept | pose gate passed every measured item | identity 0.30 (gray zone, needs a human eye) | 25 of 30 checklist items passed, 1 not applicable
- **attempt 2** `20261007_032805_goal-google-4-img-5850-original/v2_0.jpg`: **FAIL (checklist)**, identity 0.31 (Pro, google-4__IMG_5850_Original@v1, request 0998195128e0)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive); 28 (His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when) | 21: profile face, identity 0.31, not verifiable by the agent; 28: curls all around instead of the short faded sides of the references
  - right: pose gate PASS; light x0.92, face/neck 0.52 vs 0.54; the reflection mirrors the new curly hair, beard and glasses (2 faces found: him and the reflection); scene, colours, clothes and framing kept; C2PA Valid | pose gate passed every measured item | identity 0.31 (gray zone, needs a human eye) | 27 of 30 checklist items passed, 1 not applicable
- **attempt 3** `20261007_035228_goal-google-4-img-5850-original/v1_0.jpg`: **FAIL (checklist)**, identity 0.31 (Pro, google-4__IMG_5850_Original@v2, request 452817f41310)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | 21: profile face, identity 0.31, not verifiable by the agent: for the user to confirm
  - right: v2 (hair geometry): tight curls with short faded sides above the ear, full beard, glasses, the reflection updated too; pose gate PASS; light x1.04, face/neck 0.63 vs 0.54 | pose gate passed every measured item | identity 0.31 (gray zone, needs a human eye) | 28 of 30 checklist items passed, 1 not applicable
- **attempt 4** `20261007_035228_goal-google-4-img-5850-original/v2_0.jpg`: **FAIL (checklist)**, identity 0.34 (Pro, google-4__IMG_5850_Original@v2, request 452817f41310)
  - wrong: failed checklist items: 12 (Head and face pose match the goal); 21 (It is unmistakably him, not just attractive) | 12: pose gate FAIL (head bow); 21: profile face, identity 0.34, not verifiable by the agent
  - right: v2: faded sides and full beard; light x0.88 | identity 0.34 (gray zone, needs a human eye) | 27 of 30 checklist items passed, 1 not applicable
- **attempt 5** `20261007_035232_goal-google-4-img-5850-original/v1_0.jpg`: **FAIL (checklist)**, identity 0.38 (Pro, google-4__IMG_5850_Original@v3, request cee688a4fa65)
  - wrong: failed checklist items: 21 (It is unmistakably him, not just attractive) | 21: profile face, identity 0.38, not verifiable by the agent: for the user to confirm
  - right: v3 (research options): tight curls with faded sides, full beard, glasses, reflection updated; pose gate PASS; light x0.95, face/neck 0.55 vs 0.54 (matches the photo); scene unchanged | pose gate passed every measured item | identity 0.38 (gray zone, needs a human eye) | 28 of 30 checklist items passed, 1 not applicable
- **attempt 6** `20261007_035232_goal-google-4-img-5850-original/v2_0.jpg`: **FAIL (checklist)**, identity 0.64 (Pro, google-4__IMG_5850_Original@v3, request cee688a4fa65)
  - wrong: failed checklist items: 10 (The face is not brighter than the neck and body); 11 (Neck and above do not look copy-pasted) | 10/11: the face is cleaner and lighter than his yellow-lit neck (face/neck 0.77 vs the photo's 0.54): it reads pasted in
  - right: v3: identity 0.64 (accepted), current curls with faded sides and full beard; pose gate PASS; 2 faces found (him and the reflection) | pose gate passed every measured item | identity 0.64 (accept band) | 27 of 30 checklist items passed, 1 not applicable
- **attempt 7** `20261008_231713_goal-google-4-img-5850-original/v2_0.png`: **FAIL (checklist)**, identity 0.51 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 20 (A reflection mirrors him) | mirror v4 (replicate/1, Flash) attempt 2: head size 0.935 of the source (gate 0.94-1.04) (6); the reflection still shows the old short hair, not his curls (20). N/A: 15 his own photo; 17 no laugh.
  - right: his face, beard and current curly hair on the real head; light dE 11.2 | identity 0.51 (gray zone, needs a human eye) | 28 of 32 checklist items passed, 2 not applicable
- **attempt 8** `20261008_231713_goal-google-4-img-5850-original/v3_0.png`: **FAIL (checklist)**, identity 0.43 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | mirror v4 attempt 3: head size 0.935 (6); the reflection's yellow shirt turned pale blue (26). N/A: 15, 17.
  - right: his curls on the head AND in the reflection; light dE 4.8; natural, no visible patch | identity 0.43 (gray zone, needs a human eye) | 28 of 32 checklist items passed, 2 not applicable
- **attempt 9** `20261008_231713_goal-google-4-img-5850-original/v4_0.png`: **FAIL (checklist)**, identity 0.43 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 32 (His build, the same in every picture of him) | mirror v4 attempt 4: head 0.917 of the source (6); the hair keeps the old photo's outline, not his current tapered cut (19, 28); the body is the old photo's (26, 32, forced). The user, 2026-10-08: 'body and hair rework needed since the current physique and face has been changed as can be seen in the reference images, hence can't be considered best'. FORCED: the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop (no body pass in its lineage).
  - right: identity 0.43 (gray zone, needs a human eye) | 25 of 32 checklist items passed, 2 not applicable
- **attempt 10** `20261008_233542_goal-google-4-img-5850-original/v1_0.png`: **FAIL (checklist)**, identity 0.44 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 6 (The head and face are his true size); 9 (The light on the face matches the photo) | mirror v4 (second run of the same request) attempt 1: head 1.065 of the source (gate 0.94-1.04) (6); the face lit brighter than the photo, dE 15.9 (9). N/A: 15, 17.
  - right: his curls | identity 0.44 (gray zone, needs a human eye) | 28 of 32 checklist items passed, 2 not applicable
- **attempt 11** `20261008_233542_goal-google-4-img-5850-original/v2_0.png`: **FAIL (checklist)**, identity 0.44 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 26 (Scenery, background and clothes are unchanged from the source photo, and so is the physique) | mirror v4 (second run) attempt 2: the reflection's yellow shirt turned pale blue-white (26). N/A: 15, 17.
  - right: his curls on the head, light dE 3.2, head size 1.004 | identity 0.44 (gray zone, needs a human eye) | 29 of 32 checklist items passed, 2 not applicable
- **attempt 12** `20261008_233542_goal-google-4-img-5850-original/v3_0.png`: **FAIL (checklist)**, identity 0.47 (Flash, google-4__IMG_5850_Original@v4, request e0f4f804b2f9)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 32 (His build, the same in every picture of him) | mirror v4 (second run) attempt 3: the hair keeps the old photo's outline (curls down the sides, not his tapered sides) (19, 28); the body is the old photo's (26, 32, forced). The user, 2026-10-08: 'body and hair rework needed since the current physique and face has been changed as can be seen in the reference images, hence can't be considered best'. FORCED: the body is the old photo's: this goal is his current look, and the method kept every pixel below the head crop (no body pass in its lineage).
  - right: identity 0.47 (gray zone, needs a human eye) | 26 of 32 checklist items passed, 2 not applicable
- **attempt 13** `20261009_010121_goal-google-4-img-5850-original/v1_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v5, request 0eacac1accbe)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror pass A (body pass, character me@v2): the body came back unchanged: the AI body judge says 'the same', silhouette widths 1.00 of the original, and by eye the arms and torso are the old photo's, fuller than IMG_6923 (26, 32). An intermediate picture: the head is the old photo's (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
- **attempt 14** `20261009_010121_goal-google-4-img-5850-original/v2_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v5, request 0eacac1accbe)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror pass A (body pass, character me@v2): the body came back unchanged: the AI body judge says 'the same', silhouette widths 1.00 of the original, and by eye the arms and torso are the old photo's, fuller than IMG_6923 (26, 32). An intermediate picture: the head is the old photo's (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
- **attempt 15** `20261009_034130_goal-google-4-img-5850-original/v1_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v7, request 5993e3ce2634)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror v7 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
- **attempt 16** `20261009_034130_goal-google-4-img-5850-original/v2_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v7, request 5993e3ce2634)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror v7 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
- **attempt 17** `20261009_034130_goal-google-4-img-5850-original/v3_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v7, request 5993e3ce2634)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror v7 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
- **attempt 18** `20261009_034130_goal-google-4-img-5850-original/v4_0.png`: **FAIL (checklist)** (Flash, google-4__IMG_5850_Original@v7, request 5993e3ce2634)
  - wrong: failed checklist items: 19 (All of the hair is his own and his CURRENT cut, as in the character's photos); 21 (It is unmistakably him, not just attractive); 26 (Scenery, background and clothes are unchanged from the source photo); 28 (His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's); 31 (Face fullness is his, and LEAN); 32 (His build, the same in every picture of him) | mirror v7 (body pass, prompt version 2: the clothes may change, no keep-the-garments instruction): the body came back unchanged (AI body judge 'the same', silhouette widths 1.00, by eye the old body) (26, 32); an intermediate picture with the old head (19, 21, 28, 31). Items not looked at closely are listed as failed (unverifiable).
  - right: 24 of 32 checklist items passed, 2 not applicable
