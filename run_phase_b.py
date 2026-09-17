"""Phase B benchmark: restore face on rejected images and measure ArcFace identity shift."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from restore import restore_face
from scorer import ArcFaceScorer

ROOT = Path(__file__).parent

TARGETS = [
    # Original round bad labels
    ("garden-orig", "outputs/20260917_144808_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg"),
    ("car-orig", "outputs/20260917_144926_sitting-in-the-driver-s-seat-of-a-conver/v1_0.jpg"),
    # Regen round 1 bad labels (sweater)
    ("sweater-r1-v1", "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v1_0.jpg"),
    ("sweater-r1-v2", "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v2_0.jpg"),
    ("sweater-r1-v3", "outputs/20260917_152246_standing-outdoors-at-night-near-a-buildi/v3_0.jpg"),
    # Regen round 1 bad labels (garden)
    ("garden-r1-v1", "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v1_0.jpg"),
    ("garden-r1-v2", "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v2_0.jpg"),
    ("garden-r1-v3", "outputs/20260917_152424_standing-outdoors-at-night-in-a-garden-s/v3_0.jpg"),
    # Regen round 1 bad labels (car)
    ("car-r1-v1", "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v1_0.jpg"),
    ("car-r1-v2", "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v2_0.jpg"),
    ("car-r1-v3", "outputs/20260917_152634_sitting-in-the-driver-s-seat-of-a-pale-c/v3_0.jpg"),
    # Regen round 2 (unmodified latest round rejected by user)
    ("sweater-r2-v1", "outputs/20260917_162711_standing-outdoors-at-night-near-a-buildi/v1_0.jpg"),
    ("garden-r2-v3", "outputs/20260917_162853_standing-outdoors-at-night-in-a-garden-s/v3_0.jpg"),
    ("car-r2-v1", "outputs/20260917_163039_sitting-in-the-driver-s-seat-of-a-pale-c/v1_0.jpg"),
]


def main():
    scorer = ArcFaceScorer()

    with open(ROOT / "facecard.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    refs_dir = Path(cfg["refs_dir"])
    restore_refs = [refs_dir / name for name in cfg.get("restore_refs", ["IMG_6858.jpg", "IMG_6859.jpg", "IMG_6875.jpg"])]
    all_refs = [refs_dir / name for name in cfg["refs"]]

    # Pre-embed refs
    ref_embeds = {}
    for r in all_refs:
        try:
            ref_embeds[r.name] = scorer.embed(r)
        except Exception as e:
            print(f"  Ref {r.name} skipped: {e}")

    valid_ref_embeds = list(ref_embeds.values())
    centroid = ArcFaceScorer.centroid(valid_ref_embeds)

    results = []
    print(f"\nProcessing {len(TARGETS)} targets with FaceFusion CPU...\n")

    for label, rel_path in TARGETS:
        target_path = ROOT / rel_path
        if not target_path.exists():
            print(f"Skipping {label}: {target_path} not found")
            continue

        # Score before
        try:
            emb_before = scorer.embed(target_path)
            max_before = max(scorer.similarity(emb_before, r) for r in valid_ref_embeds)
            cent_before = scorer.similarity(emb_before, centroid)
        except Exception as e:
            max_before = cent_before = None

        # Restore
        res = restore_face(
            target_path=target_path,
            source_paths=restore_refs,
            swapper_model="inswapper_128",
            enhancer_model="gfpgan_1.4",
            mask_types=["box", "occlusion"],
        )

        if not res["success"]:
            print(f"[{label}] FAILED: {res.get('error')}")
            continue

        restored_path = Path(res["output"])

        # Score after
        try:
            emb_after = scorer.embed(restored_path)
            max_after = max(scorer.similarity(emb_after, r) for r in valid_ref_embeds)
            cent_after = scorer.similarity(emb_after, centroid)
        except Exception as e:
            max_after = cent_after = None

        row = {
            "label": label,
            "target": str(target_path.relative_to(ROOT)),
            "restored": str(restored_path.relative_to(ROOT)),
            "time_sec": res["elapsed_sec"],
            "max_before": max_before,
            "max_after": max_after,
            "delta_max": (max_after - max_before) if (max_after and max_before) else None,
            "cent_before": cent_before,
            "cent_after": cent_after,
            "delta_cent": (cent_after - cent_before) if (cent_after and cent_before) else None,
        }
        results.append(row)
        print(f"[{label:<14}] done in {row['time_sec']:>5.1f}s | max_ref: {row['max_before']:.3f} -> {row['max_after']:.3f} (+{row['delta_max']:+.3f}) | centroid: {row['cent_before']:.3f} -> {row['cent_after']:.3f}")

    # Output full summary table
    print("\n" + "=" * 90)
    print(f"{'Label':<15} {'Time(s)':<8} {'Max Before':<12} {'Max After':<12} {'Delta':<10} {'Centroid After':<15}")
    print("-" * 90)
    for r in results:
        delta_str = f"{r['delta_max']:+.3f}" if r['delta_max'] else "N/A"
        cent_str = f"{r['cent_after']:.3f}" if r['cent_after'] else "N/A"
        print(f"{r['label']:<15} {r['time_sec']:<8.1f} {r['max_before']:<12.3f} {r['max_after']:<12.3f} {delta_str:<10} {cent_str:<15}")

    avg_time = np.mean([r["time_sec"] for r in results])
    avg_max_after = np.mean([r["max_after"] for r in results if r["max_after"]])
    print("-" * 90)
    print(f"Average CPU time per image: {avg_time:.1f}s | Average ArcFace max score after restore: {avg_max_after:.3f}")
    print("=" * 90)

    # Save results to JSON
    with open(ROOT / "outputs" / "phase_b_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
