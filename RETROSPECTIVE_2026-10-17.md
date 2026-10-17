# Why the pictures went downhill, and what changes (retrospective, 2026-10-17)

Asked by the user on 2026-10-17: "all the recent generations have been going downhill. Do not generate any more images. Keep the to-dos on hold, and
perform a retrospective investigation into why things have been going downhill, in comparison to the images that occasionally were generated
perfectly previously ... find out why and fix it."

Generation is on hold (section 8). Every number below was measured on the saved runs; the scripts and their outputs are in
`.cache/retrospective_2026-10-17/` (git-ignored: the pictures show the user's face).

## 1. The short answer

The good pictures were made in **one pass**: one whole render (or, on the user's own photos, one face-only edit pasted into the untouched photo),
sometimes plus **one small local fix**. From 2026-10-11 the work turned into **chains of edits on edits**: a body pass, a janeu pass, a head pass,
a background pass, a seam heal, each one an edit of the previous result. Every pass leaves its own small damage (a rim, a halo, a ghost line,
eyes that no longer agree, a head that does not sit on the body), and the damage adds up. My checks did not stop this; they caused it: each failed
checklist item became one more edit, never a fresh render. Under that sit three things that made the chains necessary or more likely: the goals
moved to shirtless, pumped bodies on other men's photos (which Gemini cannot change in one pass: the project found that on 2026-09-27), my own
outputs started to be fed back in as references and bases, and the volume went up while the user's eye came in less often.

## 2. What the best set has in common

The user's best set is `D:\Downloads\AI me` (17 pictures; contact sheet `.cache/retrospective_2026-10-17/best_set.jpg`). Each was traced to the run
that made it by file content (`provenance.json`):

| Picture | Made | How | Passes |
|---|---|---|---|
| kayak, mirror, mt1, google-4 IMG_0862 | 09-21..09-23 | replicate on the user's own photo: face-only edit pasted into the untouched photo (full photo resolution) | 1 |
| nightout, car, cand1, mt2 | 09-21 | replicate (car and cand1 had been REJECTED by my gates; the user kept them) | 1 |
| beach | 09-17 | one `gen` from a scene text, 9 whole real reference photos | 1 |
| Instagram | 09-26 | route G, Pro, 4 real face photos | 1 |
| TT, tt2 | 09-27 | route G on the user's own photo, Flash, 4 pose-matched real face photos | 1 |
| pin2 | 09-26 | route G (pin v5 `v4_0`, copied into the folder by the user; its run file was pruned, so this one is traced by the review log) | 1 |
| Pin_Best | 09-28 | route G replace-subject, Pro, inventory; then one objects-only fix of the engine | 2 |
| date simulate (pizza) | 10-10 | route G recipe, then one small fix of the beard density | 2 |
| surf | 10-11 | route G recipe, then one small fix of the pin man's marks | 2 |

- 16 of 17 show the user **dressed**; surf is the one shirtless picture, and its body is lean.
- **None needed more than two passes**, and the second pass is always a small local fix.
- **Nothing in the set is newer than 2026-10-11 01:53.**
- My checklist would have rejected most of them: on 2026-10-09 four of the five gold pictures failed it (kayak 19/26/27/28/31/32, beach
  19/26/28/32, TT 12/26/32, tt2 12/24/26/27/28/32). Earlier my gates had rejected car, cand1 and IMG_0862 ("rejected by four gates": the user's
  verdict "perfect").

## 3. What changed, and when

| Period | Runs | How pictures were made | Real references only? | Whole-render prompt (median) | Pro share | Checklist items |
|---|---|---|---|---|---|---|
| 09-17..09-25 | 45 | replicate on the user's photos, one `gen` | yes (0 of 45 sent a generated picture) | - | - | - |
| 09-26..10-06 | 118 | route G, one pass (+ one fix on Pin_Best) | yes (0 of 118) | 4,935 chars | 68 of 107 | 27 -> 30 |
| 10-07..10-09 | 44 | recipes (frozen requests), still one pass | 40 of 44 | 7,476 chars | 0 of 23 | 32 -> 35 |
| 10-10..10-14 | 91 | 45 of 91 were region edits of earlier renders | **25 of 91** (66 sent a generated picture: the pumped physique, the E2 smile, or an earlier render as the base) | 12,843 chars | 2 of 24 | 36 |

Dates of the changes that matter (from `FEEDBACK_LOG.md`, `AGENTS.md`, the character files): 10-07 recipes; 10-08 character me@v1 (one fixed set
of face crops for every goal instead of four real photos chosen to match the goal's head angle); 10-09 me@v2 ("lean face, low facial fat"),
the gold tier, items 33-35; **10-10 the next-cut physique (generated), the yardstick "shirtless = fully pumped", item 36 (janeu and chain), the
grey-out body edits and the first region-edit chains**; 10-11 auto-continue, background agents, two-stage pins.

The last git commit is **2026-10-02 07:22 (`42296f2`)**, the code right after Pin_Best and the board pins; everything since (121 changed files) is
uncommitted.

## 4. Cause 1 (measured, the main one): edits stacked on edits

`tools/edit_depth.py` counts the generation passes behind a picture: a real photo or pin 0, a whole render 1, each edit of it one more.

- **All 428 pictures since 2026-10-07:** depth 1: 304, depth 2: 66, depth 3: 45, depth 4: 4, depth 5: 7, depth 6: 2.
- **Eleven runs (58 pictures) went past two passes, all from 10-11 on:** pin 14 (passes 3, 4, 5 and 6: janeu, ghost line, head, body, Gokarna
  place), pin 15 (the stub), pin 16 (two eye fixes), pin 8 (the build pass), pin 12 (the second grey-out), pin 9 (the second arm build).
- **Both recent best pictures sit at exactly two passes.** The clearest case is pin 16: `surf.jpg` is pass 2 (render + marks fix); my two eye
  fixes were pass 3 on top of surf itself, and the eye problem the user then saw ("it looks like an eye condition") was in those, not in surf.
  Sheet: `.cache/retrospective_2026-10-17/chains.jpg` (pin 14's six passes in a row, and pin 16's).
- The user said it at the time: the pizza third picture (a third pass) "made it even worse and drunk looking" (10-10); pin 14's two-stage version
  "something looks off ... the face still looks a lot leaner than the body" (10-11); pin 6 on 10-01: "my head seems weirdly placed on top of
  the body".
- Later on 2026-10-17 the user called two exported pictures "bad" that they had approved in dialogs on 10-12 and 10-13 (before the 10-14 rule
  that a question about pictures is never a dialog): pin 15 v2 (3 passes) and pin 14 v3 (5 passes). Both were withdrawn from the results folder.
- The project had already learned this on 2026-09-27 (`FEEDBACK_LOG.md` section 16): Gemini keeps the goal man's body in any edit, slims only
  when it re-renders the whole person, and code pasting between renders gives the pasted look. From 10-10 the work did both again: grey-out body
  edits, and heads pasted in from other renders by scratch scripts.

## 5. Cause 2: the goals moved to what one pass cannot do

From 10-10 almost every goal was a shirtless or bare-back picture of another man (pins 4, 6, 8, 10, 14, 15, 16, 17) with the pumped physique,
the janeu and the chain required. Gemini keeps the pin man's body, so the user's body could only be reached with body edits (cause 1). The best set is
the opposite: dressed, the user's own photos or simple pins, natural poses. Surf shows the pumped standard can work in one pass when the pin's body is
already close; most of the others were not.

## 6. Cause 3: my checks optimise the rules, not the user's eye

- The 36 items describe defects and the user's current look (19, 26, 28, 31, 32: current cut, current body, beard, lean face, build). They do not
  measure what made the best set good (one coherent photograph, attractive, natural), and the user's favourites fail them.
- Every failed item became another edit pass on the same picture (a faint background figure -> a second grey-out; a sparkle -> a patch; arms
  too thick -> a build pass; a janeu on the wrong side -> a janeu pass), never a fresh whole render.
- The pose gate stops a run after 2 failed pictures, so most recent runs made only 2 pictures to choose from.
- My own eye was wrong at times (E13 "eyes too close"; pins 5 and 6 passed 30/30 by me, rejected by the user on 10-01).

## 7. Cause 4 and 5: my outputs fed back in, and more volume with less of the user's eye

- Before 10-07 not one request sent a generated picture as a reference. From 10-10, 66 of 91 did: the generated pumped physique as the body
  reference, the generated E2 smile, or an earlier render as the photo to edit. A generated reference carries its own small errors into the next
  picture.
- 135 run folders and 428 pictures in eight days; auto-continue spent spare credits on backlog items, background agents prepared edits, and 14
  questions waited for the user while defaults ran. The decisions that made pictures worse were mine, made between the user's reviews.

**Not proven, to test (section 10):** Flash only since 10-09 (the gold Pin_Best, Instagram and beach were Pro; TT, tt2, pizza and surf were Flash);
prompts 2.6 times longer (surf's prompt was 13,600 characters and it is in the best set, so length alone is not the cause); the fixed face crops of
me@v1/v2 instead of pose-matched whole photos. Output size did not change (about 1 MP for route G throughout).

## 8. What is changed now (2026-10-17)

- **Nothing generates.** The hidden tasks `facecard-autocontinue` and `facecard-local-overnight` are disabled, the session ping is deleted, and the
  file `.cache/GENERATION_HOLD` makes `facecard.py gen / replicate / run` (exit 6), `tools/wave.py` (exit 6) and `autocontinue.py` (decision
  "hold") refuse. Checked: a real `facecard.py run` stopped before any Gemini call. Only the user lifts the hold.
- **The chain guard** (`tools/edit_depth.py`, called by `runner.py` before any credit is spent): a recipe whose pictures would have more than two
  passes (one render + one fix) is refused (exit 7) unless the user asked for that exact edit (`FACECARD_DEEP_EDIT_OK`, or a wave job's
  `"deep_edit_ok": "<their words>"`). Checked on the real recipes: pin 12's second grey-out and pin 9's second arm build are refused (3 passes);
  the surf marks fix (2) and whole renders (1) are allowed. Over the 428 pictures it would have stopped exactly the 11 chains above and none of the
  best set. It cannot see a head pasted in by a scratch script, so AGENTS.md forbids that. A recipe whose lineage it cannot read is refused too;
  of all 137 frozen recipes none is unreadable (107 come to one pass, 18 to two, and the 12 refused are the chain recipes above). `runner.run`
  also checks the hold itself, so a caller that bypasses `facecard.py` stops as well. Checked by calling it directly: pin 12's grey-out exit 7,
  a whole render exit 6, no run folder made.
- `AGENTS.md` starts with the new operating rules (section 9); `FAILURE_LOG.md` F71 records this retrospective.

## 9. The operating rules from now on

1. **One coherent picture per attempt.** The user's own photo: replicate (face only, pasted into the untouched photo). Another man's photo: one
   whole route G render from real photos of the user. When a render is wrong on the user (face, body, head, eyes), make a new whole render; never
   edit the person of a render.
2. **At most one small fix, on objects only** (a prop, lettering, a background figure, a sparkle, a mark), and only on a render the user has
   seen. No head pasted from another render, no body reshaping of a render, no fix of a fix.
3. **The user's eye decides first.** Show 2 to 4 whole renders per goal side by side with the nearest picture of the best set; the checklist
   becomes the list of defects I name for the user, not a reason for another pass.
4. **Real photos of the user as references.** The exception the user chose on 2026-10-17: the pumped physique is the body reference of every
   shirtless picture. Any other generated picture (the E2 smile, a head-angle cell) only where the user asks for it for that goal.
5. **Nothing runs on its own.** A wave runs only for a goal plan the user approved; auto-continue does not spend spare credits on backlog items.
   The user chose this on 2026-10-17, in place of their spare-credit rule of 2026-10-13 (spare credits took the next backlog goal).

## 10. What needs the user, and how the fix gets checked

The decisions that are the user's (their earlier rules point the other way):
- **The body yardstick:** keep "shirtless = the pumped physique" (a generated body as the reference), or use the user's real body photos for every goal?
- **Which goals first:** the shirtless pins (where one pass usually fails), or dressed and own-photo goals like the best set?
- **The current-look items** (19, 26, 28, 31, 32): the best set fails them; keep them as hard rules, or as notes?
- **Spare credits:** once the hold is lifted, back to the backlog runs of 2026-10-13, or only goal plans the user approved (rule 5)?

**The user's answers (2026-10-17):** the pumped physique always for shirtless pictures (their 10-10 rule stands); the shirtless pins first; the
current-look items pointed out, not rejecting (`tools/best_check.py` records them as NOTE; the scenery sentence of item 26 became item 37, which
still rejects); spare credits only for plans the user approves (rule 5 stands). One whole render now has to carry the pumped body: a render whose
body misses gets a new whole render, never a body edit, and the pins whose man is already closest to the pumped physique go first (my order).
Added the same day as a major item: "smile is a major project item to be corrected since none of the generated images till now have good teeth
showing images" (a diagnosis without generating: `.cache/smile_diagnosis_2026-10-17/`).

The check, once the user lifts the hold: three or four goals, each made by both the code of `42296f2` (the state that made Pin_Best, in a separate
git worktree, nothing overwritten) and today's code with the guard and the rules above, two renders each, shown to the user without labels.
About 135 credits a render: 8 to 16 renders, 1,100 to 2,200 credits.
