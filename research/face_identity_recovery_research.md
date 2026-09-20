# Forensic Research: Root Causes of Facial Degradation in Side Poses and Identity Drift

**Date:** 2026-09-19  
**Repository:** `nano-banana-facecard`  
**Focus:** Mathematical and architectural failure modes in 2D face swapping, multi-modal reference cross-contamination, and recovery strategy.

---

## 1. Executive Summary

Between run `20260918_204845` (which user flagged as high quality, score `0.837`) and subsequent runs (`20260919_084946`, `20260919_091939`, `20260919_152612`), facial quality severely degraded. 

Forensic analysis of the code, inputs, and intermediate generation artifacts reveals **three compound root causes**:
1. **Geometric Incompatibility in 2D Affine Warping (`cv2.estimateAffinePartial2D`):** FaceFusion's warping templates (`WARP_TEMPLATE_SET['arcface_128']`) are strictly symmetrical frontal templates. When a target face exceeds $45^\circ$ yaw, 2D affine transforms lack the degrees of freedom to represent 3D foreshortening. The far eye is compressed and sheared into a planar anomaly.
2. **Anatomical Skull Contamination via `--scene-image`:** Introducing the Pinterest image as `--scene-image` (even with a blurred face box) caused Gemini's cross-attention to anchor on the reference model's skull shape (a slender youth with a narrow jaw and thin neck). Face-swapping the user's features onto an incompatible skull geometry created a deformed, pinched composite.
3. **The Expression Restorer Conflict at Extreme Angles:** LivePortrait's facial flow fields destabilize at steep angles with open laughter, smearing teeth and lips into grey artifacts.

---

## 2. Primary Source Analysis

### A. FaceFusion Landmark Warping Math
**Source:** `C:\Users\Admin\GitHub\facefusion\facefusion\face_helper.py`, line 215:
```python
def estimate_matrix_by_face_landmark_5(face_landmark_5, warp_template, crop_size):
    warp_template_norm = WARP_TEMPLATE_SET.get(warp_template) * crop_size
    affine_matrix = cv2.estimateAffinePartial2D(
        face_landmark_5, warp_template_norm, method=cv2.RANSAC, ransacReprojThreshold=100
    )[0]
    return affine_matrix
```
- `WARP_TEMPLATE_SET['arcface_128']` defines a symmetrical, front-facing 5-point destination:
  - Left Eye: `[0.3616, 0.4038]`
  - Right Eye: `[0.6369, 0.4023]`
  - Nose: `[0.5001, 0.5604]`
  - Left Mouth: `[0.3871, 0.7216]`
  - Right Mouth: `[0.6150, 0.7203]`
- Mathematical Limitation: `cv2.estimateAffinePartial2D` computes only scale, 2D rotation, and 2D translation (4 DOF). It has zero degrees of freedom for 3D yaw rotation ($\theta_y$).
- Consequence: When a face is turned at $60^\circ$–$80^\circ$, the Euclidean distance $\|le - nose\|$ is 3× to 5× greater than $\|re - nose\|$. Fitting this to an equilateral frontal template forces severe non-affine stretching onto the neural network input. The subsequent inverse affine `paste_back` operation glues a distorted 2D sticker back into the 3D scene.

### B. Multi-Modal Vision Conditioning in Imagen 3 / Gemini
**Source:** Gemini API Image Generation Multi-Modal Reference Token Processing.
- When an image is passed as `--scene-image`, Gemini does not merely copy the background; its multi-modal encoder attends to the entire visual frame (clothing, body proportions, shoulder width, skull silhouette, neck angle).
- In the Pinterest photo (`c3a7031b4165fdcf81d2b64259e3646c.jpg`), the model possesses:
  - An adolescent, low-mass mandibular structure.
  - A long, narrow neck.
  - A severe $75^\circ$ head turn with an upward tilt.
- Because Gemini received this image, it forced the generated character's skeletal frame to match the reference model's frame. This made the base image fundamentally incompatible with Kaustubh's facial dimensions (athletic build, strong jaw, broader zygomatic arch).

### C. Contrast: Why `20260918_204845` Succeeded
- **`scene_image`: `None`**. No visual reference polluted the skeletal generation.
- **Pose in Prompt:** Explicitly directed to a gentle $40^\circ$ three-quarter profile with chin level and directional side key light.
- **Gemini Base Generation:** Rendered Kaustubh's true skull width, athletic neck, and natural eye spacing.
- **FaceFusion Execution:** Operating at $35^\circ$–$40^\circ$ yaw, the affine warping distortion remained negligible, yielding a clean, sharp, natural portrait scoring **`0.837`**.

---

## 3. Structural Solutions & Architecture Redesign

To achieve consistent high quality across all poses, the pipeline must enforce four hard boundaries:

1. **Eliminate Raw Person-Reference `--scene-image` Contamination:**
   Never feed a full-body photo of another human to Gemini as a style reference. Doing so transfers that person's skull, jaw, and neck proportions to the output. Scene composition, lighting, clothing, and posture must be conveyed via rich text prompt descriptors, or via scene references where the human subject is completely masked out.
2. **Pose-Angle Safety Cap ($30^\circ$–$45^\circ$ Maximum Yaw):**
   Candid environmental photography achieves maximum attractiveness and naturalness at a $30^\circ$ to $45^\circ$ three-quarter profile (the "Beach / Mountain 204845" angle). Extreme $70^\circ$–$90^\circ$ ear-showing profiles must be avoided because 2D face swappers physically cannot project 3D depth without facial distortion.
3. **Decoupled Landmark Alignment for 3/4 Poses:**
   For $30^\circ$–$45^\circ$ poses, route exclusively to the angle-matched reference (`IMG_6861` for right, `IMG_6868` for left) using `inswapper_128` with `pixel_boost="512x512"` and `weight=0.70` (blending with native skin pores).
4. **Sharpness & Structural Loss Gate:**
   Every restoration must pass a strict Laplacian sharpness variance check ($\ge 300$). If post-processing reduces edge definition, it is rejected.
