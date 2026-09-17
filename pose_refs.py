"""Pose and model reference search and contact-sheet generation.

Searches Openverse (free, no key) or Pexels (if pexels-api key present in vault/env)
for model/pose photos. Downloads results, builds a contact sheet grid, and provides
face-blurring for scene reference usage.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent
POSE_REFS_DIR = ROOT / "pose_refs"


def get_pexels_api_key() -> Optional[str]:
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        return key.strip()
    try:
        sys.path.insert(0, r"C:\Users\Admin\.agents\skills\secure-vault")
        import vault
        if vault.has_secret("pexels-api", "password"):
            val = vault.get_secret("pexels-api", "password")
            if val:
                return val.strip()
    except Exception:
        pass
    return None


def search_openverse(query: str, count: int = 6) -> List[dict]:
    params = {
        "q": query,
        "page_size": count,
        "license_type": "commercial,modification",
    }
    url = f"https://api.openverse.org/v1/images/?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "nano-banana-facecard/1.0"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("results", [])[:count]:
                img_url = item.get("url")
                if img_url:
                    results.append({
                        "source": "openverse",
                        "title": item.get("title", "Untitled"),
                        "creator": item.get("creator", "Unknown"),
                        "license": item.get("license", "CC"),
                        "url": img_url,
                        "thumbnail": item.get("thumbnail") or img_url,
                    })
    except Exception as e:
        print(f"Openverse search failed: {e}")
    return results


def search_wikimedia(query: str, count: int = 6) -> List[dict]:
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": "1024",
        "format": "json",
    }
    url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "nano-banana-facecard/1.0 (kaustubh)"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for pid, p in pages.items():
                infos = p.get("imageinfo", [])
                if infos:
                    info = infos[0]
                    img_url = info.get("thumburl") or info.get("url")
                    if img_url:
                        results.append({
                            "source": "wikimedia",
                            "title": p.get("title", "Wikimedia Image").replace("File:", ""),
                            "creator": "Wikimedia Commons contributor",
                            "license": "CC / Public Domain",
                            "url": img_url,
                            "thumbnail": info.get("thumburl") or img_url,
                        })
                if len(results) >= count:
                    break
    except Exception as e:
        print(f"Wikimedia search failed: {e}")
    return results


def search_pinterest_editorial(query: str, count: int = 6) -> List[dict]:
    import html
    search_q = f"{query} site:pinterest.com"
    url = "https://www.bing.com/images/search?q=" + urllib.parse.quote(search_q) + "&form=HDRSC2"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    })
    results = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
        raw_matches = re.findall(r"m=\"(\{[^\"]+\})\"", page)
        for m in raw_matches:
            clean = html.unescape(m)
            try:
                d = json.loads(clean)
                murl = d.get("murl")
                if murl and (murl.startswith("http://") or murl.startswith("https://")):
                    results.append({
                        "source": "pinterest",
                        "title": d.get("t", "Pinterest Ref"),
                        "creator": "Pinterest contributor",
                        "license": "Editorial / Reference",
                        "url": murl,
                        "thumbnail": d.get("turl") or murl,
                    })
                if len(results) >= count:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"Pinterest search failed: {e}")
    return results


def search_pexels(query: str, api_key: str, count: int = 6) -> List[dict]:
    params = {
        "query": query,
        "per_page": count,
        "orientation": "portrait",
    }
    url = f"https://api.pexels.com/v1/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "nano-banana-facecard/1.0"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for photo in data.get("photos", [])[:count]:
                src = photo.get("src", {})
                img_url = src.get("large2x") or src.get("large") or src.get("original")
                if img_url:
                    results.append({
                        "source": "pexels",
                        "title": photo.get("alt", "Pexels Photo"),
                        "creator": photo.get("photographer", "Unknown"),
                        "license": "Pexels License (free to use)",
                        "url": img_url,
                        "thumbnail": src.get("medium") or img_url,
                    })
    except Exception as e:
        print(f"Pexels search failed: {e}")
    return results


def download_image(url: str, dest: Path, timeout: int = 20) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "nano-banana-facecard/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
        dest.write_bytes(content)
        # Verify valid image via PIL
        with Image.open(dest) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        if dest.exists():
            dest.unlink(missing_ok=True)
        return False


def build_contact_sheet(
    image_paths: List[Path],
    output_path: Path,
    labels: Optional[List[str]] = None,
    tile_size: tuple[int, int] = (400, 500),
    cols: int = 3,
) -> Path:
    if not image_paths:
        raise ValueError("No images to build contact sheet.")

    n = len(image_paths)
    rows = (n + cols - 1) // cols
    w, h = tile_size
    padding = 10
    label_h = 30

    sheet_w = cols * w + (cols + 1) * padding
    sheet_h = rows * (h + label_h) + (rows + 1) * padding

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(30, 30, 30))
    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(image_paths):
        r = i // cols
        c = i % cols
        x = padding + c * (w + padding)
        y = padding + r * (h + label_h + padding)

        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.thumbnail((w, h), Image.LANCZOS)
                # Center on tile
                pad_x = x + (w - img.width) // 2
                pad_y = y + (h - img.height) // 2
                sheet.paste(img, (pad_x, pad_y))
        except Exception as e:
            print(f"Failed to load image for sheet {path}: {e}")

        lbl = labels[i] if labels and i < len(labels) else f"#{i+1}: {path.name}"
        draw.text((x + 5, y + h + 5), lbl[:40], fill=(220, 220, 220))

    sheet.save(output_path, "JPEG", quality=90)
    return output_path


def blur_face(image_path: str | Path, output_path: Optional[str | Path] = None) -> Path:
    """Detects face via YuNet and applies heavy Gaussian blur to the face box."""
    from scorer import DETECTOR_PATH

    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    h, w = img.shape[:2]
    detector = cv2.FaceDetectorYN.create(str(DETECTOR_PATH), "", (w, h), score_threshold=0.6)
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)

    if faces is not None and len(faces) > 0:
        for face in faces:
            fx, fy, fw, fh = map(int, face[:4])
            fx = max(0, fx)
            fy = max(0, fy)
            fw = min(w - fx, fw)
            fh = min(h - fy, fh)
            if fw > 0 and fh > 0:
                roi = img[fy:fy+fh, fx:fx+fw]
                # Heavy blur
                ksize = (max(31, (fw // 4) * 2 + 1), max(31, (fh // 4) * 2 + 1))
                blurred_roi = cv2.GaussianBlur(roi, ksize, 30)
                img[fy:fy+fh, fx:fx+fw] = blurred_roi

    out_p = Path(output_path) if output_path else Path(image_path).parent / f"{Path(image_path).stem}_blurred.jpg"
    cv2.imwrite(str(out_p), img)
    return out_p


def fetch_pose_refs(query: str, count: int = 6) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:40] or "pose"
    dest_dir = POSE_REFS_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    pexels_key = get_pexels_api_key()
    if pexels_key:
        print(f"Searching Pexels for: '{query}'...")
        items = search_pexels(query, pexels_key, count=count)
    else:
        print(f"Searching Openverse (free) for: '{query}'...")
        items = search_openverse(query, count=count)

    if not items and pexels_key:
        print("Pexels returned 0, falling back to Openverse...")
        items = search_openverse(query, count=count)

    if not items:
        print("Falling back to Pinterest / Editorial search...")
        items = search_pinterest_editorial(query, count=count)

    if not items:
        print("Falling back to Wikimedia Commons search...")
        items = search_wikimedia(query, count=count)

    downloaded = []
    credits_list = []
    for i, item in enumerate(items):
        ext = ".jpg"
        file_name = f"ref_{i+1:02d}{ext}"
        target_file = dest_dir / file_name
        print(f"  Downloading [{i+1}/{len(items)}]: {item['title'][:40]}...", end=" ", flush=True)
        if download_image(item["url"], target_file):
            print("OK")
            downloaded.append(target_file)
            credits_list.append({
                "file": file_name,
                "title": item["title"],
                "creator": item["creator"],
                "license": item["license"],
                "url": item["url"],
                "source": item["source"],
            })
        else:
            print("FAILED")

    with open(dest_dir / "credits.json", "w", encoding="utf-8") as f:
        json.dump(credits_list, f, indent=2)

    if downloaded:
        sheet_path = dest_dir / "contact_sheet.jpg"
        labels = [f"#{i+1}: {c['creator']}" for i, c in enumerate(credits_list)]
        build_contact_sheet(downloaded, sheet_path, labels=labels)
        print(f"\nContact sheet generated: {sheet_path}")
        return sheet_path
    else:
        print("No images were downloaded.")
        return dest_dir
