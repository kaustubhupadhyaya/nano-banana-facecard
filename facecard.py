"""
facecard: generate identity-consistent images of yourself via the Gemini web app,
reusing your Google AI Pro session (see session.py) instead of a billed API key.

Usage:
    .venv\\Scripts\\python.exe facecard.py check
    .venv\\Scripts\\python.exe facecard.py models
    .venv\\Scripts\\python.exe facecard.py gen --prompt prompts/studio_test.txt --count 1
    .venv\\Scripts\\python.exe facecard.py gen --prompt "wearing a red jacket, city street at night" --scene-image path\\to\\scene.jpg --count 2
    .venv\\Scripts\\python.exe facecard.py restore outputs/some_run/v1_0.jpg
    .venv\\Scripts\\python.exe facecard.py score outputs/some_run/v1_0.jpg
    .venv\\Scripts\\python.exe facecard.py pose-refs --query "man in convertible smiling" --count 6
"""

import argparse
import asyncio
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from gemini_webapi.exceptions import GeminiError, ImageGenerationError, UsageLimitExceededError
from session import AuthError, authenticated_client

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "facecard.json"
IDENTITY_LOCK_PATH = ROOT / "prompts" / "identity_lock.txt"
SCENE_REF_NOTE = "\n\nThe last attached image is a scene/style reference (not the identity reference) — match its pose, outfit, framing, lighting, and setting."


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def get_refs_dir(config: dict) -> Path:
    refs_dir = Path(config.get("refs_dir", ""))
    if not refs_dir.exists() or not any(refs_dir.glob("*.jpg")):
        fallback = ROOT / config.get("cache_dir", ".cache/refs")
        if fallback.exists():
            return fallback
    return refs_dir


def prepare_ref(src: Path, cache_dir: Path, max_dim: int = 2048) -> Path:
    """EXIF-transpose + downscale a reference image, cached by source mtime."""
    if not src.exists():
        fallback = cache_dir / src.name
        if fallback.exists():
            src = fallback
        else:
            raise FileNotFoundError(f"Reference image not found: {src}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / (src.stem + ".jpg")
    if cached.is_file() and cached.stat().st_mtime >= src.stat().st_mtime:
        return cached

    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
        img.save(cached, "JPEG", quality=95)
    return cached


def fix_extension(path: Path) -> Path:
    """gemini_webapi keeps the given filename even when Google serves JPEG, so match the real format."""
    with Image.open(path) as img:
        real_ext = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(img.format, path.suffix)
    if real_ext == path.suffix:
        return path
    return path.rename(path.with_suffix(real_ext))


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len] or "gen").rstrip("-")


def cmd_score(args) -> int:
    import scorer

    config = load_config()
    refs_dir = get_refs_dir(config)
    ref_paths = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    scorer.score_images([Path(p) for p in args.images], ref_paths)
    return 0


def cmd_refs_matrix(args) -> int:
    import scorer

    config = load_config()
    refs_dir = get_refs_dir(config)
    ref_paths = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    scorer.refs_matrix(ref_paths)
    return 0


def cmd_restore(args) -> int:
    from restore import restore_face
    from scorer import ArcFaceScorer, analyze_face

    config = load_config()
    refs_dir = get_refs_dir(config)
    all_refs = [refs_dir / name for name in config["refs"] if (refs_dir / name).exists()]
    restore_refs = [refs_dir / name for name in config.get("restore_refs", ["IMG_6858.jpg", "IMG_6873.jpg", "IMG_6875.jpg", "IMG_6923 Copy.jpg"]) if (refs_dir / name).exists()]
    threshold = float(config.get("identity_threshold", 0.60))

    arc_scorer = ArcFaceScorer()
    ref_embeds = []
    for r in all_refs:
        try:
            emb = arc_scorer.embed(r)
            ref_embeds.append(emb)
        except Exception:
            pass

    for p in args.images:
        target = Path(p)
        if not target.exists():
            print(f"Target not found: {target}")
            continue

        face_info = analyze_face(target)
        raw_sharpness = face_info.get("sharpness", 0.0)
        is_profile = face_info.get("is_profile", False)
        yaw_ratio = face_info.get("yaw_ratio", 1.0)

        raw_score = None
        try:
            raw_emb = arc_scorer.embed(target)
            raw_score = max(arc_scorer.similarity(raw_emb, r) for r in ref_embeds)
        except Exception:
            pass

        print(f"Restoring {target.name} (raw score: {raw_score:.3f if raw_score else 'N/A'} | yaw={yaw_ratio:.2f} | profile={is_profile})...", flush=True)
        if is_profile:
            print("  [Profile Warning] Steep side angle detected. 2D face swapping may distort facial geometry.")

        res = restore_face(target, source_paths=restore_refs, swapper_weight=0.6)
        if not res["success"]:
            print(f"  FAILED: {res.get('error')}")
            continue

        restored_path = Path(res["output"])
        rest_info = analyze_face(restored_path)
        rest_sharpness = rest_info.get("sharpness", 0.0)

        rest_score = None
        try:
            rest_emb = arc_scorer.embed(restored_path)
            rest_score = max(arc_scorer.similarity(rest_emb, r) for r in ref_embeds)
        except Exception:
            pass

        status = "ACCEPTED" if (rest_score and rest_score >= threshold) else "REJECTED"
        score_str = f"{rest_score:.3f}" if rest_score else "N/A"
        print(f"  -> {restored_path.name} in {res['elapsed_sec']}s | score: {score_str} | sharp: {rest_sharpness:.1f} (raw: {raw_sharpness:.1f}) | [{status}]")
    return 0


def cmd_pose_refs(args) -> int:
    from pose_refs import fetch_pose_refs
    sheet = fetch_pose_refs(args.query, count=args.count)
    print(f"Pose references ready in: {sheet.parent if sheet.is_file() else sheet}")
    return 0


async def cmd_check(args) -> int:
    import paths

    paths_status = paths.report()
    print()
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            print(f"Authenticated. account_status={client.account_status.name}")
            return paths_status
    except AuthError as e:
        print(str(e))
        return 1


async def cmd_models(args) -> int:
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            models = client.list_models()
            if not models:
                print("No models returned.")
                return 1
            for m in models:
                print(f"{m.model_id}\t{m.display_name}\tavailable={m.is_available}")
            return 0
    except AuthError as e:
        print(str(e))
        return 1


async def cmd_gen(args) -> int:
    config = load_config()
    refs_dir = get_refs_dir(config)
    cache_dir = ROOT / config.get("cache_dir", ".cache/refs")
    out_root = ROOT / config.get("out_dir", "outputs")
    model = args.model or config.get("model")
    threshold = float(config.get("identity_threshold", 0.60))
    restore_refs = [refs_dir / name for name in config.get("restore_refs", ["IMG_6858.jpg", "IMG_6873.jpg", "IMG_6875.jpg", "IMG_6923 Copy.jpg"]) if (refs_dir / name).exists() or (cache_dir / name).exists()]

    prompt_arg = Path(args.prompt)
    scene_text = prompt_arg.read_text(encoding="utf-8").strip() if prompt_arg.is_file() else args.prompt
    full_prompt = IDENTITY_LOCK_PATH.read_text(encoding="utf-8").strip() + "\n" + scene_text
    if args.scene_image:
        full_prompt += SCENE_REF_NOTE

    ref_paths = [prepare_ref(refs_dir / name, cache_dir) for name in config["refs"] if (refs_dir / name).exists() or (cache_dir / name).exists()]
    files = [str(p) for p in ref_paths]
    if args.scene_image:
        files.append(args.scene_image)

    print(f"Refs: {', '.join(p.name for p in ref_paths)}" + (" + scene image" if args.scene_image else ""))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_root / f"{timestamp}_{slugify(scene_text)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    run_log = {
        "timestamp": timestamp,
        "prompt": full_prompt,
        "refs": [p.name for p in ref_paths],
        "scene_image": args.scene_image,
        "model": model,
        "identity_threshold": threshold,
        "results": [],
    }

    # Lazy-load scorer
    from scorer import ArcFaceScorer, analyze_face
    arc_scorer = ArcFaceScorer()
    ref_embeds = []
    for r in ref_paths:
        try:
            emb = arc_scorer.embed(r)
            ref_embeds.append(emb)
        except Exception:
            pass

    from restore import restore_face

    candidates = []
    saved_count = 0
    try:
        async with authenticated_client(verbose=args.verbose) as client:
            print(f"Authenticated. account_status={client.account_status.name}")
            for i in range(args.count):
                print(f"\nGenerating candidate {i + 1}/{args.count}...")
                try:
                    output = await client.generate_content(
                        full_prompt, files=files, model=model, temporary=True
                    )
                except UsageLimitExceededError:
                    print("Usage limit hit on this account. Stopping batch.")
                    run_log["results"].append({"index": i, "error": "UsageLimitExceededError"})
                    break
                except (ImageGenerationError, GeminiError) as e:
                    print(f"Generation {i + 1} failed: {type(e).__name__}: {e}")
                    run_log["results"].append({"index": i, "error": f"{type(e).__name__}: {e}"})
                    continue

                candidate = output.candidates[output.chosen]
                images = candidate.generated_images
                if not images:
                    print(f"Generation {i + 1}: no image returned. Response text: {candidate.text}")
                    run_log["results"].append({"index": i, "error": "no_image", "text": candidate.text})
                    continue

                entry = {"index": i, "files": [], "evaluations": []}
                for j, img in enumerate(images):
                    saved_path = Path(await img.save(path=str(run_dir), filename=f"v{i + 1}_{j}.png", verbose=args.verbose))
                    saved_path = fix_extension(saved_path)
                    print(f"Saved raw image: {saved_path.name}")
                    entry["files"].append(saved_path.name)
                    saved_count += 1

                    cand_eval = {
                        "raw_file": saved_path.name,
                        "raw_score": None,
                        "restored_file": None,
                        "restored_score": None,
                        "status": "pending",
                    }

                    # Analyze face pose and sharpness
                    face_info = analyze_face(saved_path)
                    is_profile = face_info.get("is_profile", False)
                    yaw_ratio = face_info.get("yaw_ratio", 1.0)
                    raw_sharpness = face_info.get("sharpness", 0.0)

                    # Score raw image
                    try:
                        raw_emb = arc_scorer.embed(saved_path)
                        cand_eval["raw_score"] = float(max(arc_scorer.similarity(raw_emb, r) for r in ref_embeds))
                    except Exception:
                        pass

                    # Restore face unless --no-restore passed
                    final_path = saved_path
                    check_score = cand_eval["raw_score"]

                    if cand_eval["raw_score"] is not None and cand_eval["raw_score"] >= threshold and not is_profile:
                        cand_eval["restoration_skipped"] = "native_accepted"
                        cand_eval["status"] = "accepted"
                        print(f"  [Quality Gate] Native raw identity ({cand_eval['raw_score']:.3f} >= {threshold:.2f}) accepted natively.")
                    elif not args.no_restore:
                        print(f"  Restoring face on {saved_path.name} via angle-routed FaceFusion...", flush=True)
                        res = restore_face(saved_path)
                        if res["success"]:
                            restored_path = Path(res["output"])
                            rest_info = analyze_face(restored_path)
                            rest_sharpness = rest_info.get("sharpness", 0.0)
                            pose_desc = f"{res['pose']['bin']} ({res['pose']['direction']}, yaw={res['pose']['yaw_ratio']})"
                            print(f"  [Router] Pose: {pose_desc} -> Sources: {', '.join(res['sources'])}")

                            # Sharpness gatekeeper: reject blurry / melted artifacts
                            if raw_sharpness > 0 and rest_sharpness < 0.50 * raw_sharpness:
                                print(f"  [Sharpness Gate] Restoration lost excessive sharpness ({rest_sharpness:.1f} vs raw {raw_sharpness:.1f}). Discarding restoration.")
                                cand_eval["restoration_rejected"] = "sharpness_loss"
                                cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= 0.50) else "rejected"
                            else:
                                cand_eval["restored_file"] = restored_path.name
                                final_path = restored_path
                                try:
                                    rest_emb = arc_scorer.embed(restored_path)
                                    cand_eval["restored_score"] = float(max(arc_scorer.similarity(rest_emb, r) for r in ref_embeds))
                                    check_score = cand_eval["restored_score"]
                                except Exception:
                                    pass

                                if check_score is not None and check_score >= threshold:
                                    cand_eval["status"] = "accepted"
                                else:
                                    cand_eval["status"] = "rejected"
                        else:
                            print(f"  Restore failed: {res.get('error')}")
                            cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= threshold) else "rejected"
                    else:
                        cand_eval["status"] = "accepted" if (cand_eval["raw_score"] and cand_eval["raw_score"] >= threshold) else "rejected"

                    raw_s = f"{cand_eval['raw_score']:.3f}" if cand_eval['raw_score'] else "N/A"
                    rest_s = f"{cand_eval['restored_score']:.3f}" if cand_eval['restored_score'] else "N/A"
                    print(f"  [Score] raw: {raw_s} -> restored: {rest_s} | sharp: {raw_sharpness:.1f} | [{cand_eval['status'].upper()}]")

                    entry["evaluations"].append(cand_eval)
                    candidates.append((check_score or -1.0, final_path, cand_eval))

                run_log["results"].append(entry)
    except AuthError as e:
        print(str(e))
        return 1
    finally:
        # Pick best.jpg
        if candidates:
            # Sort by accepted status first, then by score
            candidates.sort(key=lambda x: (1 if x[2].get("status") == "accepted" else 0, x[0]), reverse=True)
            top_score, top_path, top_eval = candidates[0]
            is_accepted = top_eval.get("status") == "accepted" or top_score >= threshold
            if is_accepted:
                best_file = run_dir / "best.jpg"
                shutil.copy2(top_path, best_file)
                run_log["best"] = {
                    "file": "best.jpg",
                    "source": top_path.name,
                    "score": round(top_score, 3),
                    "status": "accepted",
                }
                print(f"\n[BEST] Selected {top_path.name} as best.jpg (identity score={top_score:.3f} | status=ACCEPTED)")
            else:
                print(f"\n[REJECTED] All candidates fell below threshold ({threshold:.2f}). Top score was {top_score:.3f}. No best.jpg created.")

        (run_dir / "run.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")

    return 0 if saved_count > 0 else 1


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description="Generate identity-consistent images via your Gemini web session",
                                     parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verify external paths (FaceFusion, reference photos, vault) and authentication", parents=[common])
    sub.add_parser("models", help="List available models for this account", parents=[common])

    score = sub.add_parser("score", help="Objective face-identity similarity of images against the pinned refs")
    score.add_argument("images", nargs="+", help="Image paths to score")

    sub.add_parser("refs-matrix", help="Pairwise identity similarity matrix among the pinned refs (find outliers)")

    restore_p = sub.add_parser("restore", help="Restore face on target image(s) using FaceFusion + verify")
    restore_p.add_argument("images", nargs="+", help="Image path(s) to restore")

    pose_p = sub.add_parser("pose-refs", help="Search and download pose/model references + build contact sheet")
    pose_p.add_argument("--query", required=True, help="Search query (e.g. 'man sitting in convertible laughing')")
    pose_p.add_argument("--count", type=int, default=6, help="Number of images to fetch (default 6)")

    gen = sub.add_parser("gen", help="Generate one or more images", parents=[common])
    gen.add_argument("--prompt", required=True, help="Scene text, or a path to a .txt file containing it")
    gen.add_argument("--scene-image", default=None, help="Optional path to a scene/style reference image")
    gen.add_argument("--count", type=int, default=1, help="How many variations to generate (default 1)")
    gen.add_argument("--model", default=None, help="Model id override (defaults to facecard.json's \"model\")")
    gen.add_argument("--no-restore", action="store_true", help="Skip FaceFusion restoration and keep raw output")

    args = parser.parse_args()
    args.verbose = getattr(args, "verbose", False)
    sync_handlers = {
        "score": cmd_score,
        "refs-matrix": cmd_refs_matrix,
        "restore": cmd_restore,
        "pose-refs": cmd_pose_refs,
    }
    if args.command in sync_handlers:
        return sync_handlers[args.command](args)
    async_handlers = {"check": cmd_check, "models": cmd_models, "gen": cmd_gen}
    return asyncio.run(async_handlers[args.command](args))


if __name__ == "__main__":
    sys.exit(main())
