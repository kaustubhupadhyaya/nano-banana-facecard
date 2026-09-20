"""Calibrate identity thresholds from real photos. Prints numbers; writes nothing.

1. Genuine: every photo of the user scored leave-one-out against the rest of the pool (near-duplicates of itself
   excluded). Score = mean of the 3 most similar pool photos.
2. Outputs judged good / bad / a different man, scored the same way and listed together, so overlap is visible.
3. Method check: the old scorer (full frame, YuNet 5-point alignment) vs a head crop vs 2dfan4 alignment.

The limits in facecard.json (identity_thresholds, gates) were approved by the user on 2026-09-20; a re-calibration only PROPOSES new ones
and they go into facecard.json only after the user approves them.

Usage:  .venv\\Scripts\\python.exe calibrate.py
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

import identity
from scorer import ArcFaceScorer, NoFaceError

ROOT = Path(__file__).parent

# Outputs the user judged good / bad on 2026-09-17 (see the previous calibrate.py), plus the 2026-09-19 night runs.
GOOD = {
    "beach": "outputs/20260917_144731_sitting-on-a-sandy-beach-at-golden-hour/v1_0.jpg",
    "sweater-orig-face": "outputs/20260917_145008_standing-outdoors-at-night-near-a-buildi/v1_0.jpg",
    "kurta": "outputs/20260917_144849_sitting-at-an-outdoor-evening-event-venu/v1_0.jpg",
}
BAD = {
    "garden-orig": "outputs/20260917_144808_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg",
    "car-orig": "outputs/20260917_144926_sitting-in-the-driver-s-seat-of-a-conver/v1_0.jpg",
    "sweater-regen-v1": "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v1_0.jpg",
    "garden-regen-v1": "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg",
    "car-regen-v1": "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v1_0.jpg",
    # 2026-09-19 night runs: the source photos were the user's own, the outputs drifted (see the diagnosis)
    "fav1-rocky-out": "outputs/20260919_223448_candid-environmental-full-body-photograp/v1_0.jpg",
    "fav2-kayak-out": "outputs/20260919_223621_candid-environmental-lifestyle-photograp/v1_0.jpg",
    "fav3-pingpong-out": "outputs/20260919_223730_candid-indoor-athletic-action-photograph/v1_0.jpg",
    "fav5-glass-out": "outputs/20260919_224409_candid-indoor-lifestyle-photograph-a-man/v1_0.jpg",
}
STRANGER = {
    # unambiguously a different man (European face in a wooded hillside), from the 2026-09-19 22:38 run
    "fav4-hillside-stranger": "outputs/20260919_223835_candid-outdoor-medium-portrait-with-natu/v1_0.jpg",
}
# 2026-09-20 review round: verdicts the user gave on rounds 1-3. The score does NOT capture expression quality
# (kayak 060329 scores 0.642 and was "perfect emotion"; 064200 scores 0.573 and was "awkward"), which is why the AI judge asks
# expression_natural instead of the score deciding it.
REVIEWED_GOOD = {
    "rocky r3 (perfect)": "outputs/20260920_061004_replicate_google-1__IMG_4861_SnapseedCop/best.jpg",
    "rocky r2 (perfect)": "outputs/20260920_034849_replicate_google-1__IMG_4861_SnapseedCop/best.jpg",
    "kayak 060329 (perfect emotion, light off)": "outputs/20260920_060329_replicate_google-1__IMG_5549/best.jpg",
}
REVIEWED_BAD = {
    "kayak 064200 (awkward expression)": "outputs/20260920_064200_replicate_google-1__IMG_5549/best.jpg",
    "kayak 053307 (r2, not him, ghosts)": "outputs/20260920_053307_replicate_google-1__IMG_5549/best.jpg",
    "rocky 053504 (r2, bad)": "outputs/20260920_053504_replicate_google-1__IMG_4861_SnapseedCop/best.jpg",
    "pinterest 064235 (head too big)": "outputs/20260920_064235_replicate_pinterest_target/best.jpg",
    "pinterest 054417 (r2, overlapping faces)": "outputs/20260920_054417_replicate_pinterest_target/best.jpg",
}
UNCONFIRMED = {
    "pinterest-alpine-out (old gate: 0.528, accepted)": "outputs/20260919_222952_authentic-candid-environmental-photograp/best.jpg",
}


def main() -> None:
    config = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
    scorer = ArcFaceScorer()
    print("Building pool (cached after the first run)...")
    pool = identity.build_pool(config, scorer)
    print(f"\nPool: {len(pool)} photos of the user (yaw is a coarse estimate and unreliable on some photos)\n")
    print(f"{'photo':<38}{'face_w':>7}{'yaw':>7}   nearest by head shape")
    for e in sorted(pool, key=lambda e: e.name):
        nn = identity.nearest_by_shape(e.shape, pool, n=2, exclude_names={e.name})
        print(f"{e.name:<38}{e.face_w:>7}{e.yaw:>+7.0f}   " + ", ".join(f"{x.name} ({d:.2f})" for x, d in nn))

    print("\n=== GENUINE + METHOD CHECK: leave-one-out score (mean of top 3) under three embedding methods ===")
    print("  plain = full frame, YuNet 5-point alignment (the old scorer)")
    print("  crop  = upscaled head crop, YuNet 5-point alignment")
    print("  fan   = upscaled head crop, 2dfan4 68-landmark alignment (the new scorer)")
    print(f"{'photo':<38}{'plain':>7}{'crop':>7}{'fan':>7}   fan top matches")
    yun: dict[str, dict[str, np.ndarray]] = {"plain": {}, "crop": {}}
    for e in pool:
        img = cv2.imread(str(e.path))
        try:
            yun["plain"][e.name] = scorer.embed_array(img)
        except NoFaceError:
            pass
        try:
            yun["crop"][e.name] = scorer.embed_head(img, align="yunet")
        except NoFaceError:
            pass
    genuine: dict[str, float] = {}
    for e in pool:
        excl = {e.name} | identity.duplicates_of(e.emb, pool)
        row = {}
        for m in ("plain", "crop"):
            q = yun[m].get(e.name)
            alt = [identity.PoolEntry(x.name, x.path, yun[m][x.name], x.shape, x.yaw, x.pitch, x.face_w) for x in pool if x.name in yun[m]]
            row[m] = identity.score_against_pool(q, alt, exclude_names=excl)["score"] if q is not None else float("nan")
        r = identity.score_against_pool(e.emb, pool, exclude_names=excl)
        genuine[e.name] = r["score"]
        tops = ", ".join(f"{n}:{s}" for n, s in r["top"])
        print(f"{e.name:<38}{row['plain']:>7.3f}{row['crop']:>7.3f}{r['score']:>7.3f}   {tops}")

    print("\n=== OUTPUTS scored with the fan method, all together (sorted by score) ===")
    rows = []
    for label_kind, group in (("GOOD", GOOD), ("bad", BAD), ("STRANGER", STRANGER), ("?", UNCONFIRMED)):
        for label, rel in group.items():
            p = ROOT / rel
            if not p.exists():
                print(f"  (missing) {label}")
                continue
            r = identity.score_image(p, pool, scorer)
            if not r.get("detected"):
                print(f"  (no face) {label}")
                continue
            rows.append((r["score"], label_kind, label, r["face_w"], r["pose_conf"]))
    print(f"{'score':>7}  {'user verdict':<10}{'face_w':>7}  output")
    for score, kind, label, fw, conf in sorted(rows, reverse=True):
        print(f"{score:>7.3f}  {kind:<10}{fw:>7}  {label}")

    gen = list(genuine.values())
    good = [s for s, k, *_ in rows if k == "GOOD"]
    bad = [s for s, k, *_ in rows if k == "bad"]
    stranger = [s for s, k, *_ in rows if k == "STRANGER"]
    print("\n=== SUMMARY (proposals are not written anywhere) ===")
    print(f"genuine leave-one-out: min {min(gen):.3f}  median {float(np.median(gen)):.3f}  max {max(gen):.3f}")
    print(f"user-confirmed good outputs: min {min(good):.3f}  max {max(good):.3f}")
    print(f"user-judged bad outputs:     min {min(bad):.3f}  max {max(bad):.3f}")
    print(f"different man:               max {max(stranger):.3f}")
    if min(gen) > max(stranger):
        print(f"hard-reject line (clearly not him): midpoint of different-man max and genuine min = {(max(stranger) + min(gen)) / 2:.3f}")
    else:
        print(f"hard-reject line: genuine min {min(gen):.3f} <= different-man max {max(stranger):.3f}; no clean line")
    print(f"bad outputs at or above the lowest good output ({min(good):.3f}): "
          f"{sum(1 for s in bad if s >= min(good))} of {len(bad)}")


if __name__ == "__main__":
    main()
