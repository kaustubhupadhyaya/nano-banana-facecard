"""One-off calibration: does ArcFace separate the user's good/bad identity verdicts?
Run once, read the numbers, decide. Not part of the regular CLI."""

from pathlib import Path

import paths
from scorer import ArcFaceScorer

ROOT = Path(__file__).parent
REFS_DIR = paths.refs_dir()
REFS = ["IMG_6858.jpg", "IMG_6859.jpg", "IMG_6862.jpg", "IMG_6863.jpg",
        "IMG_6864.jpg", "IMG_6873.jpg", "IMG_6875.jpg", "IMG_6923 Copy.JPG"]

GOOD = {
    "beach": "outputs/20260917_144731_sitting-on-a-sandy-beach-at-golden-hour/v1_0.jpg",
    "sweater-orig-face": "outputs/20260917_145008_standing-outdoors-at-night-near-a-buildi/v1_0.jpg",
    "kurta": "outputs/20260917_144849_sitting-at-an-outdoor-evening-event-venu/v1_0.jpg",
}
BAD = {
    "garden-orig": "outputs/20260917_144808_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg",
    "car-orig": "outputs/20260917_144926_sitting-in-the-driver-s-seat-of-a-conver/v1_0.jpg",
    "sweater-regen-v1": "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v1_0.jpg",
    "sweater-regen-v2": "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v2_0.jpg",
    "sweater-regen-v3": "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v3_0.jpg",
    "garden-regen-v1": "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg",
    "garden-regen-v2": "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v2_0.jpg",
    "garden-regen-v3": "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v3_0.jpg",
    "car-regen-v1": "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v1_0.jpg",
    "car-regen-v2": "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v2_0.jpg",
    "car-regen-v3": "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v3_0.jpg",
}


def main():
    scorer = ArcFaceScorer()
    ref_embeds = scorer.embed_many([REFS_DIR / r for r in REFS])
    valid_refs = [e for e in ref_embeds.values() if e is not None]
    print(f"\n{len(valid_refs)}/{len(REFS)} refs got a face embedding.\n")

    def score(path: str) -> float | None:
        try:
            emb = scorer.embed(ROOT / path)
        except Exception as e:
            print(f"  [skip] {path}: {e}")
            return None
        return max(scorer.similarity(emb, r) for r in valid_refs)

    print("=== GOOD (user-confirmed) ===")
    good_scores = {}
    for label, path in GOOD.items():
        s = score(path)
        good_scores[label] = s
        print(f"  {label:<20} max_ref_sim={s:.3f}" if s is not None else f"  {label:<20} FACE NOT DETECTED")

    print("\n=== BAD (user-confirmed) ===")
    bad_scores = {}
    for label, path in BAD.items():
        s = score(path)
        bad_scores[label] = s
        print(f"  {label:<20} max_ref_sim={s:.3f}" if s is not None else f"  {label:<20} FACE NOT DETECTED")

    good_vals = [v for v in good_scores.values() if v is not None]
    bad_vals = [v for v in bad_scores.values() if v is not None]
    print(f"\nGood: min={min(good_vals):.3f} max={max(good_vals):.3f}")
    print(f"Bad:  min={min(bad_vals):.3f} max={max(bad_vals):.3f}")
    if min(good_vals) > max(bad_vals):
        gap = min(good_vals) - max(bad_vals)
        print(f"\nSEPARATES CLEANLY. Gap={gap:.3f}. Suggested threshold={ (min(good_vals)+max(bad_vals))/2 :.3f}")
    else:
        overlap_bad = [l for l, v in bad_scores.items() if v is not None and v >= min(good_vals)]
        print(f"\nDOES NOT SEPARATE. Bad entries scoring >= worst good ({min(good_vals):.3f}): {overlap_bad}")


if __name__ == "__main__":
    main()
