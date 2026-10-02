# Best-picture checklist

No picture is called **best** until the agent has checked it against every item below by eye. The agent opens the picture next to its source photo (the reference, for another man's photo), with the head zoomed in and the whole picture seen. The user set this rule on 2026-09-26.

**Scoring rules:**
- Every item is PASS, FAIL or N/A (the condition does not apply).
- An item that cannot be verified counts as FAIL: Gemini's and the agent's own vision have missed defects the user saw.
- **If even one item fails, the picture is not best and is not called best.** It goes back into the loop (`/loop`) with `/think-again`: name the failed item, find why it happened, fix that cause, and make the next version. Never retry a fix already on the DO NOT RETRY lists in `FEEDBACK_LOG.md`.
- The pipeline's own `best.jpg` / `best.png` is only a candidate until this checklist passes. Record the result with `tools\best_check.py`.
- **Nothing is shown to the user as progress or as a candidate until this checklist is recorded for it** (the user, 2026-09-27: three pin versions were shown after only the pose gate and an identity score, and they had regressed 10 versions of progress).
  - Before showing, compare the picture item by item with the current best version of the same photo.
  - An item that passed there and fails here is a regression, and the picture is not shown as progress.
  - Never pick a candidate or an edit base by the identity score: ArcFace rates a level, camera-facing studio face highest, so picking by it chose the regression.
- **Before the first render of any goal: an element inventory** (`.cache\inventories\<goal>.json`, the user, 2026-09-28).
  - Every visible element of the goal gets a source: HIS (from his references), GOAL (kept as is) or REMOVE (e.g. a watermark, inpainted before sending).
  - Every HIS item is named in the prompt as "the photo shows X; make it Y (image N)", and `gen --inventory` compiles it.
  - An edit keeps every goal pixel the prompt does not name: "the motorcycle becomes his" left the Ducati's wheels, tyres and disc.
  - After the render, `tools\inventory_check.py` puts the render's parts beside his references. Judge each part at full zoom, not from a thumbnail.
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
| 16 | No awkward, tense, forced or smirking reaction | |
| 17 | A laugh in his own photo is kept as a laugh, not closed into a smile | the source shows no laugh |
| 18 | No fold, double chin or bulge under the chin that the source does not have | |
| 19 | All of the hair is his own: front, top, sides and back | |
| 20 | A reflection mirrors him: the same face and the same reaction | no reflection of him |
| 21 | It is unmistakably him, not just attractive: identity checked against his reference photos. With the eyes hidden (sunglasses in the goal): hair, beard, jaw, nose, ears and skin all clearly match his references, compared zoomed, and the identity score is reported (the user, 2026-09-26) | |
| 22 | The face is better than or equal to the source face, never worse | another man's photo |
| 23 | There is a visible change: not the source returned as it is | the source is one of his best versions (item 25) |
| 24 | No better attempt of the same run was thrown out by the checks: all attempts were compared by eye before choosing | |
| 25 | The source was not already perfect; if it is one of his best versions or he called it perfect, it is returned unchanged | |
| 26 | Scenery, background and clothes are unchanged from the source photo, and so is the physique. For another man's photo: the scene and clothes as in the reference, the physique always his own from his body reference (the user, 2026-09-26) | |
| 27 | None of the flaws recorded for earlier versions of this photo is back: the same mistake is not repeated | first version of a new photo |
| 28 | His face, hair, beard and moustache come from his FACE REFERENCE photos, never from the goal's face, even when the goal is his own photo: the same beard length and density, the same moustache, the same hair as the references (the user, 2026-09-26: table tennis v5 got a bigger beard and moustache than his references have) | |
| 29 | The distance from the camera is the same as in the goal: the same shot size, his size in the frame, and the perspective (telephoto flat or close wide) as the goal photo (the user, 2026-09-26: pin v5 was shot closer than the pin) | |
| 30 | Body posture and action exactly as in the goal: the stance and lean, where his weight is, each arm and hand, what he is doing with them, and his feet (the user, 2026-09-26: table tennis v5 stood upright with both arms hanging; the goal leans over the table corner with both hands low at waist height, the paddle held out over the table - v6 then raised the paddle to chest height, also wrong) | |

Record a check:

    .venv\Scripts\python.exe tools\best_check.py "<picture>" --source "<source photo>" --fail 4,26 --na 3,17,20 --note "..."

This writes `<picture>.checklist.json` next to the picture and prints BEST or NOT BEST. Items not listed as fail or N/A count as pass, so list every failed or unverifiable item.
