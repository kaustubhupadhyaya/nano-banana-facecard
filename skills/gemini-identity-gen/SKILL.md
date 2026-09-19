---
name: gemini-identity-gen
description: Generate identity-consistent images of the user via their Google AI Pro Gemini web session (no billed API) with automatic FaceFusion face restoration and ArcFace objective scoring. For writing the actual scene prompt text, use the scene-prompt-writer skill. Use for "generate a photo of me", "facecard", "nano banana [pro]", "face restore", or anything mentioning __Secure-1PSID/__Secure-1PSIDTS cookies.
---

# gemini-identity-gen

Device-wide skill. It ships inside the repo it drives, `C:\Users\Admin\GitHub\nano-banana-facecard`,
at `skills/gemini-identity-gen/`; the copies under `~\.agents\skills` and `~\.claude\skills` are
junctions to that folder, so edit it in the repo. Any agent on this machine (Claude Code, Pi,
OpenCode) should use this skill rather than re-deriving the approach or creating new vault entries.

Run `facecard.py check` first: it reports whether FaceFusion, the reference photos and the vault
all resolve, and prints the exact fix for anything missing (paths are set in `paths.py`).

## How it works

1. **Generation:** Generates base images via `gemini_webapi` (HanaokaYuzu/Gemini-API), authenticated
   with the user's Google AI Pro session cookies from the DPAPI vault (no billed API).
   Includes angle-matched references (e.g. `IMG_6862_mirrored.jpg` for right-facing profiles) so
   Gemini's 3D multi-modal cross-attention renders authentic facial silhouettes natively.
2. **Intelligent Pose & Sharpness Gating:**
   - **Profile Lockout (>35° yaw):** 2D face swappers (`inswapper_128`) fail mathematically at steep angles,
     causing melted/black far-eye sockets, blurred teeth, and waxy midface patches. For profile and steep candid
     poses, **FaceFusion is strictly locked out**. Gemini's native generation is preserved in 100% native quality.
   - **Sharpness Gatekeeper:** On frontal/mild poses where restoration runs, FaceFusion uses `--face-swapper-weight 0.6`
     (partial blend preserving pores). If restored facial sharpness drops below 65% of the raw image's Laplacian
     variance, the restoration is automatically rejected to prevent low-res degradation.
   - **Native Acceptance:** If raw generation already meets threshold (e.g. `beach.jpg`), it is accepted directly
     with zero post-processing.
3. **Objective Verification (ArcFace & Pose Calibration):** Scores candidate images using ArcFace (`w600k_r50.onnx`).
   Detects yaw ratio and pose angle; profile poses use angle-calibrated thresholds against profile references.
   **Never judge identity by human or agent eye** ("looks good" is unreliable and led to past drift crises).
4. **Best Selection:** Candidates scoring above threshold and marked `ACCEPTED` are promoted to `best.jpg`.

## 1. Session cookies (DPAPI vault)

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

## 2. CLI commands

Run with the project venv Python:
`C:\Users\Admin\GitHub\nano-banana-facecard\.venv\Scripts\python.exe facecard.py <cmd>`

- **Generate (End-to-End: Gen + Restore + Score + Best):**
  ```powershell
  python facecard.py gen --prompt prompts/beach_headshot.txt --count 2
  ```
  Generates 2 candidates, runs FaceFusion restoration on each, scores raw vs restored with ArcFace,
  and saves the highest-scoring candidate meeting threshold (>= 0.60) to `best.jpg`.
  Use `--no-restore` only if raw generation without face swap is explicitly requested.

- **Restore Existing Images:**
  ```powershell
  python facecard.py restore outputs/some_run/v1_0.jpg outputs/some_run/v2_0.jpg
  ```
  Restores face on any image using `restore_refs` (`IMG_6858.jpg`, `IMG_6862.jpg`, `IMG_6873.jpg`, `IMG_6875.jpg`, `IMG_6923 Copy.JPG`),
  prints ArcFace scores before/after, and saves `<name>_restored.jpg`.

- **Score Images Objectively:**
  ```powershell
  python facecard.py score outputs/some_run/best.jpg
  ```
  Reports max cosine similarity to references, mean similarity, and centroid similarity.

- **Search Pose / Attractiveness References:**
  ```powershell
  python facecard.py pose-refs --query "men street style full body 35mm candid" --count 4
  ```
  Searches Pinterest, fashion editorial archives, Openverse, Wikimedia, and Pexels. Downloads high-res
  reference photos into `pose_refs/<slug>/` and compiles a single `contact_sheet.jpg` grid for quick
  composition, shot distance, and styling inspiration.

- **Check / Models:**
  ```powershell
  python facecard.py check
  python facecard.py models
  ```

## 3. Reference photos & Configuration (`facecard.json`)

- `refs_dir`: `C:\Users\Admin\Downloads\FaceCard_Originals`
- `refs`: Master reference photo set attached to Gemini prompts.
- `restore_refs`: Curated sharp, distortion-free reference set (`IMG_6858.jpg`, `IMG_6862.jpg`, `IMG_6873.jpg`, `IMG_6875.jpg`,
  `IMG_6923 Copy.JPG`) capturing both frontal and authentic 3/4 profile jaw contours and athletic posture.
- `identity_threshold`: `0.60`. Restored unobstructed portraits score ~0.81–0.86; complex occlusions
  (sunglasses/turned heads/laughter) score ~0.75–0.83. Raw drifting generations score < 0.55.

## 4. Ground Rules

- **Candidness is the common goal across all generations:** Images must look unposed, spontaneous, and authentic — never stiff, rigid, or staged like commercial stock photos. Use asymmetrical body posture, natural ground contact, slight cervical head tilts, and spontaneous mid-emotion/mid-conversation facial expressions.
- **Scene reference replication via blurred `--scene-image`:** When replicating a specific reference photo's posture/scene, run `blur_face(image_path)` and pass the result as `--scene-image`. Gemini will lock onto the exact limb positions, ground contact points, and environmental scale without contaminating facial identity.
- **NEVER judge identity by eye.** Always read and report ArcFace scores.
- **NEVER feed generated images back into the reference set.** Always use the original photos.
- **Attractiveness levers belong in the scene prompt (lighting, posture, fit, framing) and pose references**,
  NEVER by distorting facial structure in the identity lock.
