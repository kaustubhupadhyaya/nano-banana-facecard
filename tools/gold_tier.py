"""The gold tier: the user's five gold pictures, kept apart from everything else and checked for consistency (the user, 2026-10-09).

The user, 2026-10-09: "remember these five image goals in a separate tier of images. ALWAYS"; "these gold references consistently need to be
consistent". gold.json lists them (the user's original file, a read-only copy in D:\\FacecardGold, the blob in the blob store, the goal, the run
that made each one, and its 32-item checklist as recorded). Nothing here re-renders, moves or deletes a gold picture.

    .venv\\Scripts\\python.exe tools\\gold_tier.py list               # the tier, each picture's checklist verdict, and whether every copy is intact
    .venv\\Scripts\\python.exe tools\\gold_tier.py check              # the five side by side with the character's photos, measures, similarity
    .venv\\Scripts\\python.exe tools\\gold_tier.py compare <picture>  # a new picture beside the gold tier and the character's photos, same scale

check and compare write into the review folder (D:\\FacecardReview\\gold-<date>\\). The yardstick for his face and build stays the character's
photos (BEST_CHECKLIST items 31, 32): every gold tile is labelled with its checklist verdict and failed items, so a failed trait is never copied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GOLD_JSON = ROOT / "gold.json"


def load() -> dict:
    return json.loads(GOLD_JSON.read_text(encoding="utf-8"))


def sha_of(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def status(p: dict) -> str:
    q = p.get("qc") or {}
    failed = q.get("failed") or []
    return f"{q.get('verdict', 'unchecked')}" + (f" (fails {','.join(map(str, failed))})" if failed else "")


def intact(p: dict) -> dict:
    import provenance as P
    return {"original": sha_of(Path(p["original"])) == p["sha256"], "copy": sha_of(Path(p["copy"])) == p["sha256"], "blob": P.verify(p["sha256"])}


def cmd_list() -> int:
    reg = load()
    bad = 0
    print(f"gold tier ({len(reg['pictures'])} pictures, added {reg['added']}; copies in {reg['gold_dir']})")
    for p in reg["pictures"]:
        ok = intact(p)
        bad += not all(ok.values())
        miss = [k for k, v in ok.items() if not v]
        print(f"  {p['key']:9s} {status(p):40s} {p['file']:13s} {'intact' if not miss else 'MISSING/CHANGED: ' + ', '.join(miss)}")
        print(f"            goal: {p['goal'] or p['goal_is']}")
    return 1 if bad else 0


def _character():
    import characters
    ch, _ = characters.load("me")
    return ch, [(r["name"], characters.ref_path(r["name"])) for r in ch["references"] if characters.ref_path(r["name"])]


def sheet(items: list[tuple[str, Path, list[str]]], out: Path) -> Path | None:
    """Row 1 the faces (aligned on the eyes at one interocular distance), row 2 the torsos (one shoulder width), each tile labelled."""
    import cv2
    import numpy as np
    import character
    allm = character.measure_all([str(p) for _, p, _ in items], say=lambda *a: None)
    faces, torsos = [], []
    for name, p, lines in items:
        sha = (allm.get(str(p)) or character.measure(p))["sha256"]
        f = character.face_tile(p, sha, [name] + lines)
        t = character.torso_tile(p, sha, [name] + lines)
        if f is not None:
            faces.append(f)
        if t is not None:
            torsos.append(t)
    rows = [character._row(r) for r in (faces, torsos) if r]
    if not rows:
        return None
    w = max(r.shape[1] for r in rows)
    rows = [cv2.copyMakeBorder(r, 0, 10, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(235, 235, 235)) for r in rows]
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])
    return out


def similarity(named: list[tuple[str, Path]]) -> dict:
    """ArcFace similarity of every pair (head crop, 2dfan4 alignment). Small or hidden faces score low whoever they are: report, never gate."""
    from scorer import ArcFaceScorer
    sc = ArcFaceScorer()
    emb = {}
    for k, p in named:
        try:
            emb[k] = sc.embed_head(str(p))
        except Exception:
            emb[k] = None
    keys = [k for k, e in emb.items() if e is not None]
    return {a: {b: round(sc.similarity(emb[a], emb[b]), 3) for b in keys} for a in keys}


def out_dir() -> Path:
    import paths
    return paths.review_dir() / f"gold-{datetime.now():%Y-%m-%d}"


def cmd_check() -> int:
    import character
    reg = load()
    ch, refs = _character()
    od = out_dir()
    gold = [(p["key"], Path(p["copy"]), [status(p)]) for p in reg["pictures"]]
    made = sheet(gold + [(f"his {n[:16]}", q, ["character photo"]) for n, q in refs], od / "gold_consistency.jpg")
    summary = {"date": datetime.now().isoformat(timespec="seconds"), "character": f"{ch['name']}@v{ch['version']}", "pictures": {}}
    for key, p, _ in gold:
        m = character.measure(p)
        summary["pictures"][key] = {"face_usable": m["face"].get("usable"), "face_reason": m["face"].get("reason"),
                                    "body_usable": m["body"].get("usable"), "body_reason": m["body"].get("reason"),
                                    "vs_band": character.compare(m, ch["band"]) if ch.get("band") else {}}
    summary["similarity"] = similarity([(k, p) for k, p, _ in gold] + [(f"his {n}", q) for n, q in refs])
    (od / "gold_check.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet: {made}\nmeasures and similarity: {od / 'gold_check.json'}")
    for key, v in summary["pictures"].items():
        outside = [f"{sec}.{n} {c['value']:.2f}" for sec in ("face", "body") for n, c in (v["vs_band"].get(sec) or {}).items() if not c["inside"]]
        print(f"  {key:9s} face {'measured' if v['face_usable'] else 'not measurable'}, body {'measured' if v['body_usable'] else 'not measurable'}"
              + (f"; outside his band: {', '.join(outside)}" if outside else ""))
    return cmd_list()


def cmd_compare(picture: str) -> int:
    reg = load()
    _, refs = _character()
    pic = Path(picture)
    od = out_dir()
    items = [("THIS PICTURE", pic, [pic.name[:30]])] + [(p["key"], Path(p["copy"]), [status(p)]) for p in reg["pictures"]] \
        + [(f"his {n[:16]}", q, ["character photo"]) for n, q in refs]
    made = sheet(items, od / f"compare_{pic.stem[:40]}.jpg")
    sim = similarity([("THIS PICTURE", pic)] + [(p["key"], Path(p["copy"])) for p in reg["pictures"]])
    print(f"sheet: {made}")
    for k, v in (sim.get("THIS PICTURE") or {}).items():
        if k != "THIS PICTURE":
            print(f"  similarity to {k}: {v}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("check")
    c = sub.add_parser("compare")
    c.add_argument("picture")
    a = ap.parse_args()
    return {"list": cmd_list, "check": cmd_check}.get(a.cmd, lambda: cmd_compare(a.picture))()


if __name__ == "__main__":
    sys.exit(main())
