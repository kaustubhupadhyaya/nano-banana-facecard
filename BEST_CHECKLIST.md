# Best-picture checklist

No picture is called **best** until the agent has checked it against every item below by eye. The agent opens the picture next to its source photo (the reference, for another man's photo), with the head zoomed in and the whole picture seen. The user set this rule on 2026-09-26.

**Scoring rules:**
- Every item is PASS, FAIL or N/A (the condition does not apply).
- An item that cannot be verified counts as FAIL: Gemini's and the agent's own vision have missed defects the user saw.
- **If even one item fails, the picture is not best and is not called best.** It goes back into the loop (`/loop`) with `/think-again`: name the failed item, find why it happened, fix that cause, and make the next version. Never retry a fix already on the DO NOT RETRY lists in `FEEDBACK_LOG.md`.
- **Since 2026-10-17** (the user, asked whether the current-look items should reject pictures: "No, just point them out"): items 19, 26 (the physique), 28, 31 and 32 are pointed out to the user and never make a picture not best (the scenery sentence of the old item 26 is item 37 and still rejects); `tools\best_check.py` records them as NOTE. The next version of a failed picture is a new whole render, never an edit of it, and comes after the user has seen it (`AGENTS.md`, READ FIRST).
- The pipeline's own `best.jpg` / `best.png` is only a candidate until this checklist passes. Record the result with `tools\best_check.py`.
- **Nothing is shown to the user as progress or as a candidate until this checklist is recorded for it** (the user, 2026-09-27: three pin versions were shown after only the pose gate and an identity score, and they had regressed 10 versions of progress).
  - Before showing, compare the picture item by item with the current best version of the same photo. For a goal in the gold tier
    (`gold.json`, the user, 2026-10-09) that is the gold picture; `tools\gold_tier.py compare <picture>` puts it beside the five at one scale.
  - An item that passed there and fails here is a regression, and the picture is not shown as progress.
  - Never pick a candidate or an edit base by the identity score: ArcFace rates a level, camera-facing studio face highest, so picking by it chose the regression.
- **Before the first render of any goal: an element inventory** (`.cache\inventories\<goal>.json`, the user, 2026-09-28).
  - Every visible element of the goal gets a source: HIS (from his references), GOAL (kept as is) or REMOVE (e.g. a watermark, inpainted before sending).
  - Every HIS item is named in the prompt as "the photo shows X; make it Y (image N)", and `gen --inventory` compiles it.
  - An edit keeps every goal pixel the prompt does not name: "the motorcycle becomes his" left the Ducati's wheels, tyres and disc.
  - After the render, `tools\inventory_check.py` puts the render's parts beside his references. Judge each part at full zoom, not from a thumbnail.
- **Current look (the user, 2026-10-08)**: every picture shows him as the character's photos show him today: his face (lean, no added cheek fat; his full beard may widen the jaw outline), his current haircut, his beard, and his current physique from the body reference. This holds even when the goal is an older photo of his: anything carried over from an older photo (the body, the haircut, the beard length) is pointed out (NOTE since 2026-10-17, not rejecting). `tools\best_check.py` forces 26 and 32 to NOTE for a current-look own photo whose method kept the old body, and refuses a PASS of 19, 21, 26, 28, 31, 32, 33, 34 or 35 without an `--evidence` line naming what was compared.
- **Items 33, 34 and 35 (the user, 2026-10-09: "rules you are forgetting, when not given a reference or when given as well")** hold for every picture, edit mode and text mode alike:
  - Background people are hard to handle and every added one makes the picture more complex: none are added, and the goal's own are kept as they are. A text-mode picture is written with the setting empty.
  - Text in AI pictures is hard for the same reason: none is added, the goal's own is kept letter for letter, and lettering the user asked for is exact. Shop signs and screens in a text-mode setting are soft unreadable glow.
  - A picture with no reference to follow reads as a quick handheld phone shot caught in a rush (slight motion blur, a few degrees of tilt, off-centre, grain), not a studio portrait.
  - Judge 33 and 34 at 100% on every person and every text, beside the goal; in an edit-mode pin the background copy (`tools\background_restore.py`) makes them identical by construction, and the check confirms the seams.
- **Items 31 and 32 (the user, 2026-10-08: the same man in every picture)** are judged on the character sheet in `07_review` (his face and torso beside the character's photos at the same scale); `06_measure` records the face-fullness and build measures against the character's band. The measures are record-only until the user approves them as gates.
- **Items 12, 14, 29 and 30 are measured first** (the user, 2026-09-27: posture and position mistakes kept passing a by-eye check).
  - `tools\pose_compare.py` runs on every render of `facecard.py gen --goal`, with fixed limits. Its FAIL is a FAIL, and is never explained away.
  - The eye check of these items uses its overlay (`<render>_pose.jpg`), limb by limb against the goal, never against the previous version.
  - Any POSE text in a prompt must agree with the goal's measured facts (`--pose-points`).

The items are the user's own complaints, from `FEEDBACK_LOG.md` and the reviews.

| # | Check (PASS only if true) | N/A when |
|---|---|---|
| 1 | One face only: no overlapping or second face | |
| 2 | No ghost outline, doubled edge, second hairline, second ear or second collar | |
| 3 | No extra faces: a reflection shows the same single head, not a third face | no reflection or glass in the picture |
| 4 | The face is not lasso-ed and edited in: face, hair, ears and neck read as one head, not a face patch under kept hair | |
| 5 | The head fits the body: same turn and tilt as the neck and shoulders, attached naturally | |
| 6 | The head and face are his true size: not bigger and not smaller than his real face, compared with the source and his references (the user, 2026-09-26: Instagram v4 face slightly smaller than his real one) | |
| 7 | Face size is in proportion to the body and the scene | |
| 8 | Nothing looks unreal or monsterish, at thumbnail size or zoomed in | |
| 9 | The light on the face matches the photo: direction, colour, exposure, grain | |
| 10 | The face is not brighter than the neck and body | |
| 11 | Neck and above do not look copy-pasted: no seam, halo, patch or colour step at the edge | |
| 12 | Head and face pose match the goal: the same turn (side and degrees), tilt (chin up or down), roll and gaze direction as in the goal photo, his own or another man's (widened by the user's question, 2026-09-26) | the user explicitly accepted a new pose for this photo |
| 13 | Face angle matches the head: the face points where the skull, hair and neck point | |
| 14 | Face position and alignment in the frame match the goal: where his head sits in the frame, how high, and which way it faces, for every goal, his own photo included (widened 2026-09-26) | |
| 15 | Expression matches the reference at the same strength (never caught mid-motion) | not another man's photo |
| 16 | No awkward, tense, forced or smirking reaction, unless the user asked for that expression (2026-10-09: a very light smirk, a candid smile) | |
| 17 | A laugh in his own photo is kept as a laugh, not closed into a smile | the source shows no laugh |
| 18 | No fold, double chin or bulge under the chin that the source does not have | |
| 19 | All of the hair is his own and his CURRENT cut, as in the character's photos: tight curls on top, the sides tapered short with the ears and temples showing, the curls longer at the back; compared at the same scale beside the character's photos. "Curly" alone is not a pass, and an older photo's cut is a fail (the user, 2026-10-08) | |
| 20 | A reflection mirrors him: the same face and the same reaction | no reflection of him |
| 21 | It is unmistakably him, not just attractive: identity checked against his reference photos. With the eyes hidden (sunglasses in the goal): hair, beard, jaw, nose, ears and skin all clearly match his references, compared zoomed, and the identity score is reported (the user, 2026-09-26) | |
| 22 | The face is better than or equal to the source face, never worse | another man's photo |
| 23 | There is a visible change: not the source returned as it is | the source is one of his best versions (item 25) |
| 24 | No better attempt of the same run was thrown out by the checks: all attempts were compared by eye before choosing | |
| 25 | The source was not already perfect; if it is one of his best versions or he called it perfect, it is returned unchanged | |
| 26 | The physique is always his CURRENT one from the character's body reference, for another man's photo AND for his own older photo: a body kept from an older photo of him is a fail (the user, 2026-10-08: "body rework needed since the current physique has changed, as can be seen in the reference images"). By the user's yardstick (2026-10-10: "any shirtless picture will get the fully pumped version of mine, and casual outdoor dressed versions will get the casual in-between version of my body"): a shirtless picture has the approved pumped physique (`D:\FacecardData\physique\standard\pumped_front.jpg`, `pumped_back.jpg`; recipe `--physique pumped-*`), a dressed casual outdoor one the in-between (`casual_front.jpg`: arms never thinner than his real photo, veins between relaxed and pumped) | |
| 27 | None of the flaws recorded for earlier versions of this photo is back: the same mistake is not repeated | first version of a new photo |
| 28 | His face, hair, beard and moustache come from the character's photos (his current look), never from the goal's face, even when the goal is his own older photo: the same beard length and density, the same moustache, the same current cut (the user, 2026-09-26: table tennis v5 got a bigger beard and moustache than his references have; 2026-10-08: the kayak and mirror pictures kept the old cut) | |
| 29 | The distance from the camera is the same as in the goal: the same shot size, his size in the frame, and the perspective (telephoto flat or close wide) as the goal photo (the user, 2026-09-26: pin v5 was shot closer than the pin) | |
| 30 | Body posture and action exactly as in the goal: the stance and lean, where his weight is, each arm and hand, what he is doing with them, and his feet (the user, 2026-09-26: table tennis v5 stood upright with both arms hanging; the goal leans over the table corner with both hands low at waist height, the paddle held out over the table - v6 then raised the paddle to chest height, also wrong) | |
| 31 | Face fullness is his, and LEAN: the cheeks, the jaw line under the beard, the chin and the neck as lean as in the character's photos (no added cheek fat); only his full beard may make the jaw outline wider. Judged on the character sheet at the same scale, for his own older photos too (the user, 2026-10-08: "body fat percentage that reflects in the face as well"; "if it's the leanness, stick to the leaner look") | his face is hidden |
| 32 | His build, the same in every picture of him: shoulder width, arms, chest, stomach and waist exactly as his current body reference and as his other passed pictures, judged on the character sheet at the same scale, for his own older photos too. A body that can be neither measured nor seen clearly is unverifiable, so FAIL (the user, 2026-10-08: "body type, which depends on muscle mass, body fat ... height ratios"; "if I make you generate 10 images of the same character using the same reference images, all should look the same"). For a back view, beside his back reference (`his_back.jpg`, cut from the user's back video of 2026-10-09; frames in `D:\FacecardData\back_video`) at the same scale: shoulder-blade edges, lat outline, spine groove and rear shoulders as clear as his. A shirtless picture is judged beside the pumped standard of item 26 (front or back), with his biceps vein and forearm veins; a dressed casual one beside the in-between | his body is not visible |
| 33 | Background people: no person the goal does not have; each person the goal has is there in the same number, place, size and pose, no sharper than in the goal, with no bent or missing limbs, doubled or melted faces, checked at 100% on every one. A text-mode picture has no one but him (the user, 2026-10-09: "humans in the background are hard to handle and adding more makes it more complex") | |
| 34 | Text in the picture: no text, sign, label, caption or logo the goal does not have (a text-mode picture has only the lettering the user asked for); every text the goal has is the same words, typeface and colour, letter for letter wherever the goal's is legible, and never garbled; where the goal's is unreadable the render's is too; lettering the user asked for (a garment print) is sharp and exact. Checked at 100% on every text (the user, 2026-10-09: "same goes for text in AI images"; pin 4's screen text came back garbled) | no text anywhere in the picture |
| 35 | Candid capture look: when the goal is a quick handheld snapshot, or the user asked for one, the picture reads as caught in a rush: the goal's own motion blur, grain, tilt and soft spots are kept; with no reference to follow they are added (slight motion blur on what moves, a few degrees of tilt, off-centre framing with an edge cutting something, phone grain, uneven light, focus not exactly on the face). Never studio-clean, symmetrical or over-sharp (the user, 2026-10-09: "make it more candid as if captured in a rush, use motion blurs etc.") | the goal is a deliberate studio or editorial picture, or the user asked for a polished look |
| 36 | His janeu and chain: with his chest or back bare, his janeu (the thin white sacred thread from his left shoulder diagonally across his chest, or his back, to his right hip) and his silver neck chain are there as in his photos, unbroken and in the right place; compared at 100% beside `D:\FacecardData\body_refs\2026-10-10` (the user, 2026-10-10: "It is the holy thread that Brahmins wear, called jenu"; he chose "Every bare-torso picture") | his chest and back are covered |
| 37 | Scenery, background and clothes are unchanged from the source photo (split out of item 26 on 2026-10-17: the physique part of 26 is pointed out, this part still rejects) | |
| 38 | His teeth, when they show, are his own: judged beside his real smile photos at the same scale (`D:\FacecardData\approved_refs\teeth`: IMG_6875 from the front, IMG_3884 turned): the uneven edges, the pointed canines, the thin line between the two front teeth, ivory with yellower sides, his lips parted as far as in his photos; never whiter, evener or straighter than his. E2 is the yardstick of right teeth (the user, 2026-10-17: "none of the generated images till now have good teeth showing images"; 2026-10-18: only E2 has the right teeth) | his teeth do not show |

Record a check:

    .venv\Scripts\python.exe tools\best_check.py "<picture>" --source "<source photo>" --fail 4,26 --na 3,17,20 --note "..."

This writes `<picture>.checklist.json` next to the picture and prints BEST or NOT BEST. Items not listed as fail or N/A count as pass, so list every failed or unverifiable item.
