> **SUPERSEDED 2026-09-20.** This plan (headless scene masking, angle-routed references, profile lock-out) redrew the whole
> photo and could not keep the background, clothes, physique or face structure from drifting. It is replaced by `replicate`
> (edit a crop, paste it back into the untouched original). See README.md and skills/gemini-identity-gen/SKILL.md.

# Architectural Plan: E2E Full-Angle Replication & Identity Preservation Pipeline

**Date:** 2026-09-19  
**Goal:** Build a robust, end-to-end architecture capable of replicating any reference scene/pose at ALL facial angles (from 0° frontal up to 85° steep side profile) while maintaining true, uncompromised user facial identity without warped eyes, melted features, or waxy smoothing.

---

## 1. Executive Summary & Problem Diagnosis

### The Core Failure Mode:
In prior iterations, the pipeline faced an impossible choice:
1. **Visual Scene Conditioning Used:** Passing the reference photo as `--scene-image` (even with a blurred face box) caused Gemini's cross-attention to anchor on the reference model's skull, jaw, neck, and profile geometry. Post-processing with FaceFusion (`inswapper_128`) on steep side profiles (>45° yaw) resulted in catastrophic facial distortion because 2D affine partial warping (`cv2.estimateAffinePartial2D`) mathematically collapses when mapping 3D foreshortened profile landmarks into a symmetrical frontal template (`arcface_128`).
2. **Visual Scene Conditioning Omitted:** Dropping `--scene-image` caused Gemini to drift, completely losing the ground-level camera perspective, seated posture, leg folds, log contact, and background terrain.
3. **The Artificial Tier Constraint:** Rule 4 in `/scene-prompt-writer` locked perspectives into 3 rigid focal length/distance bundles (35mm full-body, 50mm cowboy, 85mm portrait), forcing prompts into artificial framing formulas that contradicted reference images.

---

## 2. The 5 Pillars of the New Architecture

### Pillar 1: Abolish Artificial Tiers in `scene-prompt-writer`
- Remove the 3-tier camera distance matrix.
- Decouple perspective into 4 independent axes:
  1. **Framing Distance:** Full environmental landscape, seated ground contact, cowboy, waist up, tight portrait.
  2. **Camera Elevation & Pitch:** Ground-level looking up, eye-level, low-angle, high-angle.
  3. **Focal Length & Compression:** 28–35mm spatial context, 50mm documentary, 85–135mm telephoto compression.
  4. **Depth of Field:** Crisp deep landscape focus (f/8) vs. shallow subject separation (f/1.8).
- **Mandatory Reference Override Rule:** When replicating a reference image, mirror its exact framing, camera pitch, and optical depth verbatim. Never force arbitrary focal lengths or bokeh into deep-focus daylight scenes.

### Pillar 2: Headless / Silhouette-Neutral Scene Conditioning (`--scene-image`)
- Replace simple face-box blurring with `mask_head_from_scene()` in `pose_refs.py`.
- Detects the face, hair, ears, jawline, and neck down to the collar line and neutralizes this entire region (seamless inpainting / soft background fill).
- Gemini receives 100% of the physical scene (camera elevation, seated posture, leg folding, arm draping, clothing textures, fallen log, grass, background ridges) with ZERO reference model skull or profile contamination.

### Pillar 3: Angle-Targeted Identity Conditioning for Gemini
- Replace the unstratified 13-photo attachment (which was 70% frontal and diluted profile attention) with dynamic angle-targeted reference routing:
  - **Right Profile (55°–85°):** `IMG_6862_mirrored.jpg` (master profile), `IMG_6869.jpg` (3/4 right), `IMG_6861.jpg` (3/4 right), and 1 frontal color/tone anchor (`IMG_6873.jpg`).
  - **Left Profile (55°–85°):** `IMG_6862.jpg` (master left profile), `IMG_6863.jpg`, `IMG_6868.jpg`, and 1 frontal anchor.
  - **Frontal / Mild (0°–45°):** Curated sharp frontal and 3/4 bins.
- Update `SCENE_REF_NOTE` to explicitly instruct Gemini that the scene reference has its head/neck masked out, and that all facial anatomy, skull proportions, and profile contours MUST come exclusively from the attached identity references.

### Pillar 4: Eliminating Frontal Swapper Corruption on Profiles
- On steep profile angles (>45° yaw / `is_profile == True`), **strictly lock out `inswapper_128`**.
- Because Gemini is conditioned on a headless scene reference and angle-matched profile references, it generates the user's authentic facial profile, nose bridge, and curly hairline natively at full resolution without 2D affine template warping.
- On frontal/mild poses (yaw $\le 45^\circ$), FaceFusion runs with `pixel_boost="512x512"` and pore-preserving weights (0.6–0.7), protected by the relative & absolute Laplacian sharpness gate.

### Pillar 5: Profile-Aware Scoring & Threshold Unification
- Update `scorer.py` to handle profile scoring without forcing a frontal landmark warp (`_align`) on profile targets.
- Unify yaw ratio and profile classification across `scorer.py` and `restore.py`.
- Fix config key naming (`restore_refs`) and casing (`IMG_6923 Copy.JPG`).
- Ensure `cmd_restore` respects angle routing rather than hardcoded frontal lists.

---

## 3. Implementation Checklist & Verification Targets

1. Update `C:\Users\Admin\.agents\skills\scene-prompt-writer\SKILL.md`.
2. Update `C:\Users\Admin\GitHub\nano-banana-facecard\pose_refs.py` with `mask_head_from_scene()`.
3. Update `C:\Users\Admin\GitHub\nano-banana-facecard\scorer.py`, `restore.py`, and `facecard.json`.
4. Update `C:\Users\Admin\GitHub\nano-banana-facecard\facecard.py`.
5. Sync device skills `skills/gemini-identity-gen/SKILL.md`.
6. Inspect and test on:
   - Primary target: Pinterest alpine pasture seated shot (`c3a7031b4165fdcf81d2b64259e3646c.jpg` / `pinterest_target.jpg`).
   - All targets in `C:\Users\Admin\Downloads\super favs`.
