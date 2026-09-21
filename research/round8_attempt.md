# Round 8 (2026-09-21): what was tried, what it measured, why it was rolled back

The code in `round8_attempt.patch` was applied on top of commit `7fd3ebc` (round 7), run live on three photos, and then rolled back by the user
to `7fd3ebc`: round 7 keeps attractiveness and identity right, and its one mistake is that the good renders existed only as head crops. Only
that mistake is being fixed after this. Everything below is kept so that nothing here is tried twice by accident.

## What the patch changed

- A. A returned crop whose alignment failed was still scored; a good face (pool identity >= 0.52) became a rescue source.
- B. The rescue reference became a head crop of the raw return (3x face box, 768 px), named by image number in the prompt; up to 3 rescues.
- C. The AI "not better than the source" comparison stopped rejecting candidates (ranking only).
- D. Two-sided neck checks: face-minus-neck gap within +-10 of the source, neck lightness within +-10 of the source neck.
- E. Own-photo size upper limit back to the approved 1.04.
- F. `refs_mode: all_whole`: every reference in `facecard.json` sent as a whole photo, the way `beach.jpg` (a `gen` output) was made.
- G. Gray-zone classification (pool score 0.20-0.40) asked of the AI ("same man?") instead of the number.

## What the probes measured (text calls only, real saved crops)

| Probe | Result |
|---|---|
| Face-only pairwise question, raw return vs source crop, both orders, on the three returns the user rated a P / i P | agreed with the user in 1 of 3 (night out c2: return; beach c1: SOURCE; car2 c1: tie). So it must never be a veto. |
| General pairwise question on the same | night out SOURCE, beach SOURCE, car2 tie (car2 composite: SOURCE); table tennis and stained glass: candidate |
| AI same-man check (G) | 3 of 3 right: table tennis (the user, 109 px face, score 0.399) True; Pinterest (another man, 0.106) False; night out (0.853) True |

## What the live runs measured

| Run | Setup | Result |
|---|---|---|
| Pinterest `165147` | all_whole references (3 left-turned profiles for a right-turned head; the dark kayak/rocky photos are not config refs) | pick attempt 4, light dE 15.8, identity 0.477; 5 of 6 attempts dE 25-36. The ideal (`064221`) measured dE 5.7 / 0.506. Worse. |
| Stained glass `170107` | all_whole | 1 of 6 passed (round 7: 2 of 4); sizes 0.89-1.10; face sharpness 0.16-0.34 of the source. Worse. |
| Pinterest `171345` | nearest_heads (the round-7 references) | 0 of 6 passed; attempt 3 lost to an HTTP 429 download error; the same setup had passed 1 of 6 in the morning: outcomes vary a lot run to run |
| Stained glass `172446` | nearest_heads | 2 of 2 passed, pick attempt 1 |
| Night out `173615` | nearest_heads | 0 of 3 (quota): attempts 1-2 identity 0.86 / 0.81 but re-posed (size 0.86-0.89, moved 0.15-0.17) and never tagged for rescue because a lighting or neck gate also fired |

Conclusion on F: whole-photo references are worse and stay opt-in. D and G were not evaluated on enough photos to keep.

## The registration-merge probe (the basis of the "always merge" rule that follows)

Face-box registration (one scale and one translation of the returned face onto the source face, then the existing soft paste with the validity
mask) on three saved raw returns, complete pictures with 0 changed pixels outside the crop:

| Raw return | identity | size | shift | drift SSIM | note |
|---|---|---|---|---|---|
| night out c2 (user: P/P) | 0.785 | 1.000 | 0.011 | 0.655 | fails drift: the return re-posed the shoulders |
| table tennis c1 (user: i P) | 0.581 | 0.981 | 0.025 | 0.937 | passes drift |
| beach c1 (user: P/P) | 0.551 | 0.991 | 0.014 | 0.532 | fails drift, correctly: this return is Gemini's re-render of the kayak reference photo it was sent (glasses, life vest, reeds), not an edit of the beach crop; that is why its ring alignment failed by 26 percent |

The beach finding matters: the face the user rated "wins in all" is a free re-render of one of their real reference photos, the same thing that
made `D:\Downloads\AI me\beach.jpg` (a from-scratch `gen` output) an ideal.
