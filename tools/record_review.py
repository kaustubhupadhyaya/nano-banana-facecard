"""Record the user's reviews of the pictures listed by pending_review.py (review format chosen by the user, 2026-09-23).

One line per picture:
    <n> a<-2..+2> i<-2..+2> [keep] [tags...] [other:"..."] ["free note"]
    <n> skip
a = attractiveness, i = identity, both compared with the source photo: -2 much worse, 0 the same, +2 much better.
tags: hair light size angle expression pasted blur glasses clothes (what is wrong); keep = this becomes the best version of that photo.

For each line: facecard.json "reviews" gets the record; FEEDBACK_LOG.md section "Reviews" gets a row; "keep" copies the picture into
D:\\Downloads\\AI me (named <source>_<run stamp>) and records it in facecard.json "best_versions" (md5, run, attempt), so later runs return it
unchanged. Rebuild the workbook afterwards (research\\feedback_matrix\\build_feedback_matrix.py).

    .venv\\Scripts\\python.exe tools\\record_review.py --file reviews.txt
    .venv\\Scripts\\python.exe tools\\record_review.py --text "1 a+2 i+1 keep"
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import BEST_DIR, REVIEW_QUEUE, ROOT, TAGS, load_config, md5, save_config  # noqa: E402

LINE_RE = re.compile(r"^\s*(\d+)[.):]?\s+(.*)$")


def parse(line: str) -> dict | None:
    m = LINE_RE.match(line)
    if not m:
        return None
    n, rest = int(m.group(1)), m.group(2)
    rec = {"n": n, "raw": line.strip(), "a": None, "i": None, "keep": False, "skip": False, "tags": [], "note": ""}
    notes = re.findall(r'other:"([^"]*)"', rest) + re.findall(r'(?<!other:)"([^"]*)"', rest)
    rest = re.sub(r'other:"[^"]*"|"[^"]*"', " ", rest)
    for tok in rest.replace(",", " ").split():
        t = tok.lower()
        if re.fullmatch(r"a[+-]?[0-2]", t):
            rec["a"] = int(t[1:])
        elif re.fullmatch(r"i[+-]?[0-2]", t):
            rec["i"] = int(t[1:])
        elif t == "keep":
            rec["keep"] = True
        elif t == "skip":
            rec["skip"] = True
        elif t in TAGS:
            rec["tags"].append(t)
        else:
            notes.append(tok)
    rec["note"] = " ".join(x for x in notes if x).strip()
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", help="a text file with one review per line")
    ap.add_argument("--text", help="the reviews as one string (lines separated by newlines or ';')")
    args = ap.parse_args()
    if not REVIEW_QUEUE.exists():
        print("No review queue: run tools\\pending_review.py first.")
        return 1
    queue = {q["n"]: q for q in json.loads(REVIEW_QUEUE.read_text(encoding="utf-8"))}
    text = Path(args.file).read_text(encoding="utf-8") if args.file else (args.text or "")
    # a ';' separates reviews only outside a quoted note (2026-09-24: a note with a ';' was cut in half)
    lines = [ln for ln in re.split(r'\n|;(?=(?:[^"]*"[^"]*")*[^"]*$)', text) if ln.strip()]
    cfg = load_config()
    reviews = cfg.setdefault("reviews", {})
    best = cfg.setdefault("best_versions", {})
    today = date.today().isoformat()
    log_rows = []
    for ln in lines:
        rec = parse(ln)
        if rec is None or rec["n"] not in queue:
            print(f"  not understood or no such picture: {ln!r}")
            continue
        q = queue[rec["n"]]
        key = f"{q['run']}/{q['file']}"
        if rec["skip"]:
            print(f"  {rec['n']}: skipped")
            continue
        entry = {"a": rec["a"], "i": rec["i"], "keep": rec["keep"], "tags": rec["tags"], "note": rec["note"], "date": today,
                 "source": q["source"], "path": q["path"], "attempt": q["attempt"], "raw": rec["raw"]}
        reviews[key] = entry
        kept_to = ""
        if rec["keep"]:
            BEST_DIR.mkdir(parents=True, exist_ok=True)
            src_pic = Path(q["path"])
            dest = BEST_DIR / f"{Path(q['source']).stem}_{q['run'][:15]}{src_pic.suffix}"
            shutil.copy2(src_pic, dest)
            best[str(dest).replace("\\", "/")] = {"md5": md5(dest), "run": q["run"], "which": f"attempt {q['attempt']}",
                                                  "what": f"kept by the user {today}: a {rec['a']:+d} i {rec['i']:+d}" if rec["a"] is not None and rec["i"] is not None
                                                  else f"kept by the user {today}"}
            kept_to = str(dest)
        fmt = lambda v: "" if v is None else f"{v:+d}"
        log_rows.append(f"| {today} | `{q['run']}/{q['file']}` | {fmt(rec['a'])} | {fmt(rec['i'])} | {'yes: ' + kept_to if kept_to else ''} | "
                        f"{' '.join(rec['tags'])} | {rec['note']} |")
        print(f"  {rec['n']}: recorded a {fmt(rec['a'])} i {fmt(rec['i'])}{' keep -> ' + kept_to if kept_to else ''} {' '.join(rec['tags'])}")
    save_config(cfg)
    if log_rows:
        fl = ROOT / "FEEDBACK_LOG.md"
        raw = fl.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        header = "## Reviews (scores -2..+2 against the source, defect tags, keep = best version)"
        lines_ = raw.split(nl)
        if header not in raw:
            lines_ = [ln for ln in lines_]
            while lines_ and not lines_[-1].strip():
                lines_.pop()
            lines_ += ["", header, "", "| Date | Picture | a | i | Kept as best version | Tags | Note |", "|---|---|---|---|---|---|---|"] + log_rows + [""]
        else:
            # insert after the last row of the reviews table, wherever the section is
            k = lines_.index(header) + 1
            while k < len(lines_) and not lines_[k].startswith("|"):
                k += 1
            while k < len(lines_) and lines_[k].startswith("|"):
                k += 1
            lines_[k:k] = log_rows
        fl.write_bytes(nl.join(lines_).encode("utf-8"))
    print(f"{len(log_rows)} review(s) recorded in facecard.json and FEEDBACK_LOG.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
