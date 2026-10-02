"""Build FEEDBACK_MATRIX.xlsx: every image the user reviewed (directly or by batch) and every new image of 2026-09-21, ranked, with the user's
verdict, measured scores, non-crop divergence and the complete file location, so that any agent can see what is fine and what is not.

Run (needs openpyxl; the project venv has it after `pip install openpyxl`):
    .venv\\Scripts\\python.exe research\\feedback_matrix\\build_feedback_matrix.py [output.xlsx]
Data: fm_rows.py, fm_rows2.py (the user's verdicts, curated); numbers come from .cache/feedback/*/run.json and from the image files.
"""
import datetime
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fm_assemble import FB, GATES, OUTS, assemble, flags, load_json, recorded, round_of, ai_wins, closest_of, save_cache  # noqa: E402
from fm_measure import Measurer, ROOT, scene_path  # noqa: E402
from fm_rows import BATCH_R1, BATCH_R2, BATCH_TEXT, CLASSES, CODE_STATE, NO_VERDICT_RUNS  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "FEEDBACK_MATRIX.xlsx"

# ------------------------------------------------------------------------------------------------ styles
FONT = "Calibri"
F_BASE = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_TITLE = Font(name=FONT, size=16, bold=True, color="1F3864")
F_LINK = Font(name=FONT, size=10, color="0563C1", underline="single")
F_RED = Font(name=FONT, size=10, bold=True, color="C00000")
F_AMBER = Font(name=FONT, size=10, bold=True, color="B45F06")
F_GREEN = Font(name=FONT, size=10, bold=True, color="2E7D32")
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
CENTER_TOP = Alignment(horizontal="center", vertical="top", wrap_text=True)
THIN = Side(style="thin", color="D0D0D0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BANDS = {"ROW": "305496", "WHERE": "548235", "THE USER'S VERDICT": "BF8F00", "MEASURED (limits in the header)": "7030A0",
         "NON-CROP DIVERGENCE": "C55A11", "PIPELINE / AI": "44546A", "READING": "2E75B6"}
CLASS_FILL = {"IDEAL": "63BE7B", "BEST_VERSION": "7BC67E", "PERFECT": "A9D08E", "IMPROVEMENT": "C6E0B4", "PENDING_FACE_GOOD_PASS": "BDD7EE", "PENDING_FACE_GOOD_FAIL": "FFE699",
              "HEAD_PERFECT": "FFF2CC", "HEAD_GOOD": "FFF2CC", "HEAD_PROMISING": "FFF2CC", "PENDING_PASS": "DDEBF7", "MIXED": "FCE4D6",
              "PENDING_FAIL": "EDEDED", "PENDING_UNCHANGED": "D9D9D9", "NO_CHANGE": "F8CBAD", "BATCH_REJECTED": "F4B084", "REJECTED": "F4B6B6",
              "NOT_A_RESULT": "BFBFBF"}


def fill(hex_: str) -> PatternFill:
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def uri(path: str) -> str:
    return Path(path).as_uri()


def set_link(cell, path: str):
    if path:
        cell.value = path
        cell.hyperlink = uri(path)
        cell.font = F_LINK


# ------------------------------------------------------------------------------------------------ the ranking sheet
# (header, key, width, number format, band)
COLS = [
    ("Rank", "rank", 6, "0", "ROW"),
    ("Row ID", "id", 7, None, "ROW"),
    ("Photo", "group", 16, None, "ROW"),
    ("Class (how the rank was decided)", "class_label", 36, None, "ROW"),
    ("Points", "points", 7, "0", "ROW"),
    ("Valid result? (complete picture, source size, 0 px changed outside the crop)", "valid", 26, None, "ROW"),
    ("Rank among valid pictures", "rank_valid", 9, "0", "ROW"),
    ("Review round", "rnd", 8, None, "ROW"),
    ("Code state that made it", "code_state", 34, None, "ROW"),
    ("Image kind", "kind_label", 26, None, "ROW"),
    ("Source photo: own or another man's", "source_kind", 10, None, "ROW"),
    ("COMPLETE IMAGE FILE LOCATION", "path", 70, None, "WHERE"),
    ("Other copies of this image", "other", 55, None, "WHERE"),
    ("Source photo (the original that was edited)", "source_photo", 50, None, "WHERE"),
    ("Run folder", "run", 44, None, "WHERE"),
    ("Run record (run.json)", "runjson", 55, None, "WHERE"),
    ("User verdict (their words)", "verdict", 55, None, "THE USER'S VERDICT"),
    ("Attractiveness a (P improved / N degraded / O no change)", "a", 12, None, "THE USER'S VERDICT"),
    ("a score (+1 / 0 / -1)", "a_pts", 8, "+0;-0;0", "THE USER'S VERDICT"),
    ("Identity i (P / N / O)", "i", 9, None, "THE USER'S VERDICT"),
    ("i score (+1 / 0 / -1)", "i_pts", 8, "+0;-0;0", "THE USER'S VERDICT"),
    ("Basis of the a / i codes", "basis", 32, None, "THE USER'S VERDICT"),
    ("Identity: likeness to the user's own photos (pool score; >= 0.52 accept, < 0.20 reject)", "identity", 18, "0.000", "MEASURED (limits in the header)"),
    ("Similarity to the SOURCE face (> 0.90 = returned unchanged; approved outputs 0.23-0.75)", "gt_sim", 18, "0.000", "MEASURED (limits in the header)"),
    ("Head size / source head (allowed 0.94-1.04)", "size", 15, "0.000", "MEASURED (limits in the header)"),
    ("Head moved, in face widths (allowed <= 0.12)", "shift", 15, "0.000", "MEASURED (limits in the header)"),
    ("Face light distance dE (own <= 14, another man's photo <= 20)", "dE", 16, "0.0", "MEASURED (limits in the header)"),
    ("Neck gap vs source (face brighter than neck by more than in the source; <= +10)", "neck", 17, "+0.0;-0.0;0.0", "MEASURED (limits in the header)"),
    ("Redrawn clothes / background inside the crop: SSIM (>= 0.80)", "ssim", 17, "0.000", "MEASURED (limits in the header)"),
    ("Redrawn clothes / background inside the crop: mean abs diff (<= 10)", "mad", 17, "0.00", "MEASURED (limits in the header)"),
    ("Pixels changed OUTSIDE the crop, recorded by the run (0 = untouched)", "outside_rec", 18, "#,##0", "NON-CROP DIVERGENCE"),
    ("Pixels changed OUTSIDE the crop, recomputed from THIS FILE against the source", "outside_px", 20, "#,##0", "NON-CROP DIVERGENCE"),
    ("Share of the area outside the crop that changed (%)", "outside_pct", 16, "0.0000", "NON-CROP DIVERGENCE"),
    ("Share of the crop that changed (%)", "inside_pct", 14, "0.0", "NON-CROP DIVERGENCE"),
    ("AI judge: what it flagged", "judge", 32, None, "PIPELINE / AI"),
    ("AI comparison with the source face", "vs_src", 12, None, "PIPELINE / AI"),
    ("AI face ranking inside its run (win share of the attempts compared)", "ai_rank", 18, None, "PIPELINE / AI"),
    ("Pipeline verdict", "pverdict", 11, None, "PIPELINE / AI"),
    ("Gates failed / problems the run recorded", "problems", 60, None, "PIPELINE / AI"),
    ("Where the numbers come from", "measured_by", 34, None, "PIPELINE / AI"),
    ("WHAT IS FINE", "fine", 62, None, "READING"),
    ("WHAT IS NOT FINE", "notfine", 62, None, "READING"),
    ("Use it for / lesson for the next agent", "use", 52, None, "READING"),
]


def cell_value(r: dict, key: str):
    m = r["m"]
    if key in ("identity", "gt_sim", "size", "shift", "dE", "neck", "ssim", "mad", "outside_rec", "outside_px", "outside_pct", "inside_pct", "judge", "vs_src"):
        return m.get(key)
    if key == "pverdict":
        return m.get("verdict") or ""
    if key == "problems":
        if r["kind"] == "head_raw" and (m.get("comp_verdict") or m.get("comp_problems")):
            return "Composite of this attempt: " + str(m.get("comp_verdict") or "?") + (" - " + m["comp_problems"] if m.get("comp_problems") else "")
        return "; ".join(p for p in [m.get("problems"), m.get("warnings")] if p)
    if key == "size" and r["kind"] == "head_raw":
        return m.get("size")
    return r.get(key)


def metric_font(r: dict, key: str, v):
    """Red / amber / green only where the number is a gate for this kind of row."""
    if v is None or r["kind"] in ("gen", "head_send"):
        return None
    head = r["kind"] == "head_raw"
    if key == "identity":
        return F_RED if v < GATES["hard_reject"] else (F_AMBER if v < GATES["accept"] else F_GREEN)
    if head:
        return None                               # a raw return's size and shift are its own framing, not gates
    own = (r["source_kind"] != "foreign")
    if key == "gt_sim":
        return F_RED if v > GATES["unchanged"] else None
    if key == "size":
        return F_RED if not (GATES["size"][0] <= v <= GATES["size"][1]) else None
    if key == "shift":
        return F_RED if v > GATES["shift"] else None
    if key == "dE":
        return F_RED if v > (GATES["dE_own"] if own else GATES["dE_foreign"]) else None
    if key == "neck":
        return F_RED if v > GATES["neck"] else None
    if key == "ssim":
        return F_RED if v < GATES["ssim"] else None
    if key == "mad":
        return F_RED if v > GATES["mad"] else None
    if key in ("outside_px", "outside_rec"):
        return F_RED if v not in (0,) else None
    return None


def write_ranking(wb: Workbook, rows: list[dict]):
    ws = wb.create_sheet("Ranking")
    ncol = len(COLS)
    # band row + header row
    prev = None
    start = 1
    for c, (_, _, _, _, band) in enumerate(COLS, 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = fill(BANDS[band])
        if band != prev:
            cell.value = band
            cell.font = F_HEAD
            if prev is not None:
                pass
            prev = band
    for c, (head, key, width, fmt, band) in enumerate(COLS, 1):
        h = ws.cell(row=2, column=c, value=head)
        h.font, h.fill, h.alignment, h.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = width
    ws.row_dimensions[2].height = 118
    ws.row_dimensions[1].height = 18
    for i, r in enumerate(rows, 3):
        for c, (head, key, width, fmt, band) in enumerate(COLS, 1):
            v = cell_value(r, key)
            cell = ws.cell(row=i, column=c)
            cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
            if key == "path":
                set_link(cell, r["path"])
            elif key in ("runjson", "source_photo") and v and Path(str(v)).exists():
                set_link(cell, str(v))
            else:
                cell.value = v if v not in ("",) else None
            if fmt and isinstance(v, (int, float)):
                cell.number_format = fmt
            if key in ("rank", "id", "points", "a", "i", "a_pts", "i_pts", "rank_valid", "rnd", "pverdict", "vs_src", "source_kind"):
                cell.alignment = CENTER_TOP
            f = metric_font(r, key, v) if isinstance(v, (int, float)) else None
            if f is not None:
                cell.font = f
        ws.cell(row=i, column=4).fill = fill(CLASS_FILL[r["cls"]])
        v6 = ws.cell(row=i, column=6)
        v6.fill = fill("C6E0B4" if r["valid"].startswith("YES") else "F4B6B6")
    ws.freeze_panes = "D3"
    ws.auto_filter.ref = f"A2:{get_column_letter(ncol)}{len(rows) + 2}"
    ws.sheet_view.zoomScale = 90
    return ws


# ------------------------------------------------------------------------------------------------ README
README = [
    ("TITLE", "FEEDBACK MATRIX: every reviewed and every new image of the nano-banana-facecard model, ranked"),
    ("", "Written 2026-09-22 from the evidence in .cache/feedback (runs up to 20260922_025509; the user's verdicts and best versions of 2026-09-23 included). Companions: FEEDBACK_LOG.md (the narrative), facecard.json (approved_outputs, gates), skills/gemini-identity-gen/SKILL.md."),
    ("H", "What the model must deliver"),
    ("The goal", "replicate returns the USER'S VERSION of any given photo: the complete photo with their face, perfect identity retention and the maximum attractiveness that keeps it natural, with nothing else changed (background, clothes, physique, pose, glasses, bandana). Identity and naturalness come before attractiveness."),
    ("What the user counts as attractive", "Calm confident eyes, a defined jawline, a relaxed closed-lip smile or a slight smile with soft eyes (on another man's photo: the reference photo's own expression at the same strength), full natural curly hair, the face and neck lit like the photo and the body, head and face in proportion with the body, one real photograph rather than a paste. NEVER tense, awkward, forced, smirking or caught mid-motion; never a pasted-looking head, a second face or ghost outline, hair that is not entirely the user's."),
    ("THE HARD RULE (the user, 2026-09-21)", "A rendered head is never a result. Every completed head creation is merged into the complete picture first, and only that picture can be chosen as 'best', if it meets the rules for best (the gates on the 'Limits & gates' sheet). A VALID RESULT = a complete picture with the source's dimensions and 0 pixels changed outside the crop. Head crops (c*_head_raw.jpg) are intermediates, however good the face is."),
    ("The user's best versions (2026-09-23)", "The folder D:\\Downloads\\AI me holds the user's best version of each photo: beach.jpg (gen 20260917_144731), nightout.jpg (213349 attempt 2), kayak.jpg (024138 attempt 1), mt1.jpg (rocky 024632 attempt 3), mirror.jpg (stained glass 070221 attempt 4), mt2.jpg (Pinterest 064221 attempt 4, the ideal), cand1.png (Pinterest 171345 attempt 1) and car.png (car2 043841 attempt 1), matched by pixel content; class 01b BEST VERSION in the ranking. What they share: face lit like the photo (dE 1.0-13.8), head size 0.91-1.03, the face really re-rendered, identity drop at most 0.171, a laugh kept. No best version exists for nerd, mountain, table tennis or IMG_0862."),
    ("H", "How to read this workbook"),
    ("Sheets", "Ranking = every image, best first (the main table). Verdict matrix (R7) = the user's nine-row matrix of 2026-09-21 next to what the hard rule did on the same photos. New live run (RULE) = the eleven runs made 2026-09-21 21:33 to 2026-09-22 03:01. Runs summary = one row per run folder. Candidates = every attempt of every run with all its numbers. Limits & gates = the numbers a picture must meet and how far each is approved. Concerns checklist = what the user complained about, per photo. Preserve vs fix = what must not be touched and what is open."),
    ("Rank and class", "Rank orders by CLASS points (the class is decided by the USER'S verdict where they gave one), then valid pictures before head crops, then identity, then row id. Classes: IDEAL 100 > PERFECT 90 > IMPROVEMENT 75 > complete picture from a P/P face that passes every gate 70 > good face as a head crop only 62-67 > NOT REVIEWED but passes the gates of its own version 55 (provisional) > complete picture from a P/P face that fails a gate 48 > MIXED 45 > NOT REVIEWED and failed a gate 35 > unchanged look-alike 27 > NO CHANGE 25 > old batch that the user judged worse 12 > REJECTED 10 > not a result 5. Points are only an ordering key. Rows the user has not reviewed are ranked by their measured gates and say so in 'Class'."),
    ("The user's codes", "a = attractiveness, i = identity, judged against the SOURCE photo: P improved, N degraded, O no change. The user gave these codes explicitly only for the nine-row matrix of 2026-09-21; for other rows the assistant derived them from the user's words ('perfect' = P and P, 'nailed attractiveness but not looking like me' = a P, i N) and the column 'Basis of the a / i codes' says which. Where the words do not separate a and i the codes are empty. a score / i score are the same codes as +1 / 0 / -1."),
    ("Attractiveness has no automatic score", "The pipeline cannot measure attractiveness. The only ground truth is the user's verdict (columns a and the verdict text). The 'AI face ranking' column is the Gemini pairwise comparison of the attempts inside one run (relative, only in runs made since round 7) and never overrides the user."),
    ("Identity", "Pool score = ArcFace similarity of the face to the user's own reference photos (0-1). >= 0.52 accepted, < 0.20 rejected, in between 'uncertain' (a profile or turned face scores low: the approved ideals measure 0.49-0.51). 'Similarity to the SOURCE face' shows whether the face really changed: everything the user approved measures 0.23-0.75, everything they called 'as it is' 0.93-0.99, so > 0.90 = the source came back unchanged."),
    ("Non-crop divergence", "Two columns of numbers: what the run recorded and what was recomputed from the very file in column 'COMPLETE IMAGE FILE LOCATION' against the source photo (PNG: exact; JPEG: a tolerance of 24/255 because a JPEG re-encode alone differs by up to 16). Valid pictures show 0. Head crops and crops sent to Gemini are not pictures, so they show nothing. Generated-from-scratch pictures have no source, so no divergence is defined (the whole picture is new). 'Share of the crop that changed' says how much of the edited region was actually re-rendered."),
    ("Colours", "Numbers are red where they break the current gate for that kind of row (size outside 0.94-1.04, moved > 0.12, light dE above the limit, neck gap > +10, SSIM < 0.80, similarity to the source > 0.90, any pixel changed outside the crop). Identity is red < 0.20, amber 0.20-0.52, green >= 0.52. Head crops are coloured for identity only: their size and shift are the raw return's own framing, not gates."),
    ("Numbers from", "Rows made by the pipeline show what the run recorded in run.json at the time (older versions recorded fewer numbers; empty = not measured then). Head crops, offline merges, generated pictures and rows without a record were measured now with the pipeline's own functions on the file (column 'Where the numbers come from'). The user's words are quoted from FEEDBACK_LOG.md and facecard.json. Problem strings recorded by older runs quote the limits of THEIR time (for example a size limit of 1.03, later corrected to the approved 1.04)."),
    ("User verdict vs the assistant's read", "'User verdict' is always the user's own words. In 'WHAT IS FINE / NOT FINE' the rows made this round (ids C-, O-, L-) are the ASSISTANT'S READ of the picture plus numbers, marked as such: the user has not reviewed them."),
    ("H", "Where things are"),
    ("Images", "Every path is absolute. Evidence store (kept, gitignored, shows the user's face): C:\\Users\\Admin\\GitHub\\nano-banana-facecard\\.cache\\feedback\\<run folder>\\ ; working folder (may be cleared): ...\\nano-banana-facecard\\outputs\\<run folder>\\ ; the two ideals also in .cache\\feedback\\ideal\\ ; offline merges in .cache\\feedback\\rule_check_offline\\ ; source photos in D:\\Downloads\\AI me\\ (five), .cache\\super_favs\\ (five), .cache\\pinterest_target.jpg. Raw returns of new runs are in <run folder>\\raw\\. None of these images is in git."),
    ("Regenerate", "Scripts: research\\feedback_matrix\\build_feedback_matrix.py (+ fm_rows.py, fm_rows2.py = the curated verdict rows, fm_assemble.py, fm_measure.py). Add the user's new verdicts to fm_rows*.py and rerun; needs openpyxl."),
    ("H", "State of the code at the time of writing"),
    ("Commit and working tree", "HEAD = origin/main = 779267f (round-7 pipeline plus the record of the rolled-back round 8). UNCOMMITTED on top: replicate.py and facecard.json = the hard merge rule (face-box registration of every return, raw returns kept in raw/, best asserted to be a complete picture, AI 'not better than the source' comparison demoted to a tiebreak, placement of a good face from its head crop, own size upper limit back to the approved 1.04, rescue attempts 3). Nothing of it is committed until the user approves the live pictures."),
    ("What the hard rule did live", "Default pipeline, no flags, one batch in two halves: 2026-09-21 21:33-22:42 and, after the quota reset, 2026-09-22 02:33-03:01 (rows L-01..L-11). NIGHT OUT: attempt 1 rendered a face with identity 0.884 that failed size and moved (0.896 / 0.158); its placement (attempt 2) became a complete picture that passes every gate = the rule works end to end on one photo (placements 3 and 4 failed at size 0.89). BEACH: best = attempt 5, a normal attempt (the 3 placements of attempt 1's face failed: clothes redrawn, seam, glasses). CAR2: best = attempt 5, a normal attempt (one placement passed with identity only 0.367, two failed the neck gap and a redrawn crop). MOUNTAIN: both attempts passed, best = attempt 2. NERD: unchanged (0.945) or judged 'head angle / clothes changed'; nothing promoted; its 3 placements failed. PINTEREST: the ideal was not reproduced in 9 completed attempts over two runs (face lit dE 30-34 against a limit of 20; all 3 placements of a 0.62 face came back as bright). KAYAK and ROCKY (regression checks on photos the user had called perfect): both pass every gate (kayak identity 0.597 = the approved 0.598; rocky 0.494, by a placement that repaired a too-bright attempt). STAINED GLASS: the best has identity 0.223 (the approved picture 0.488) and its reflection appears not to match the new curls: a regression. TABLE TENNIS: nothing passed in 6 attempts, every render's head 13-25 percent too big. Of 20 completed placements, 4 passed every gate (night out, car2, kayak, rocky). A DEFECT FOUND WHILE WRITING THIS WORKBOOK: the code that recognises a good face never excludes a return that is the source unchanged (the approved plan says it must: 'not the source returned unchanged, gt_sim <= 0.90'), so beach's 3 placements and nerd's first placement used a face that WAS the source (raw similarity 0.944 and 0.902), and nerd's other two used a near-unchanged face (0.893); those 6 placements could not have improved anything (the second half of the batch was not affected: the faces placed there measured 0.758, 0.478, 0.135 and -0.071). The earlier offline check never tested that path. The code is unchanged since the live runs (see 'Preserve vs fix'). None of the eleven pictures has been reviewed by the user."),
    ("Image quota", "Gemini image window: ~84 credits per image, 2,400 per 5-hour window (observed resets 21:31 and 02:31 IST); the first half of the batch ended with 0 credits at 22:42, the second half ran 02:33-03:01 without hitting the limit."),
]


def write_readme(wb: Workbook, rows: list[dict]):
    ws = wb.active
    ws.title = "READ ME"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 150
    r = 1
    for a, b in README:
        if a == "TITLE":
            ws.cell(row=r, column=1, value=b).font = F_TITLE
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
            ws.row_dimensions[r].height = 26
        elif a == "H":
            c = ws.cell(row=r, column=1, value=b)
            c.font, c.fill = F_HEAD, fill("305496")
            ws.cell(row=r, column=2).fill = fill("305496")
        elif a == "":
            c = ws.cell(row=r, column=1, value=b)
            c.font, c.alignment = F_BASE, WRAP_TOP
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
            ws.row_dimensions[r].height = 32
        else:
            ws.cell(row=r, column=1, value=a).font = F_BOLD
            ws.cell(row=r, column=1).alignment = WRAP_TOP
            c = ws.cell(row=r, column=2, value=b)
            c.font, c.alignment = F_BASE, WRAP_TOP
        r += 1
    # class legend with counts
    r += 1
    ws.cell(row=r, column=1, value="Classes used in Ranking").font, ws.cell(row=r, column=1).fill = F_HEAD, fill("305496")
    ws.cell(row=r, column=2, value="Points | rows in this workbook").font, ws.cell(row=r, column=2).fill = F_HEAD, fill("305496")
    r += 1
    counts = {}
    for x in rows:
        counts[x["cls"]] = counts.get(x["cls"], 0) + 1
    for k, (pts, label) in sorted(CLASSES.items(), key=lambda kv: -kv[1][0]):
        a = ws.cell(row=r, column=1, value=label)
        a.fill, a.font, a.alignment = fill(CLASS_FILL[k]), F_BASE, WRAP_TOP
        n_rows = counts.get(k, 0)
        b = ws.cell(row=r, column=2, value=f"{pts} points | {n_rows} row" + ("" if n_rows == 1 else "s"))
        b.font = F_BASE
        r += 1
    r += 1
    ws.cell(row=r, column=1, value=f"Total rows in Ranking: {len(rows)}; valid complete pictures: {sum(1 for x in rows if x['valid'].startswith('YES'))}").font = F_BOLD
    ws.sheet_view.zoomScale = 100


# ------------------------------------------------------------------------------------------------ the verdict matrix of 2026-09-21
MATRIX = [
    # (#, row id, what it actually is, complete picture?, measured (from the log), what it teaches, live run of the rule, row id of the live run)
    ("1", "H-04", "raw return of attempt 2, own mode", "no, headshot; rejected: size 0.935, moved 0.134, judge angle changed; 2 rescues failed (one unchanged, one copied the reference's pose)",
     "pool identity 0.784", "the best face was found on attempt 2 and never made it into the photo",
     "Offline: merged into the picture by the ring it fails size and moved (O-01). LIVE: attempt 1 rendered a face of identity 0.884, its placement became a complete picture that passes every gate (identity 0.84, size 0.994, shift 0.003, dE 2.6): the rule works on this photo.", "L-01"),
    ("2", "R-15", "pasted composite, attempt 1", "yes", "face L 52.9 vs source 43.7; neck L 43.8 vs source 16.9 (+27); yaw 9 degrees off; light dE 8.9 and neck gap -18.5 passed",
     "identity is there; the head-and-neck lighting degrades attractiveness and no gate saw it",
     "LIVE: the face came back unchanged (gt_sim 0.945) or the AI judge flagged the head angle / clothes as changed; nothing promoted; all three placements failed the same judge, but they placed a face that was the source unchanged or nearly (0.902 / 0.893: recognition defect, see Preserve vs fix).", "L-02"),
    ("3", "H-05", "raw return of attempt 1, re-framed by Gemini (scale 0.74, shift 0.26): a re-render of the KAYAK reference photo, not an edit of the beach crop", "no, headshot; alignment failed so it was never measured or kept",
     "pool identity 0.557 (measured afterwards)", "'wins in all: attraction, identity, pose'; discarded before anyone looked at the face",
     "Offline: merged by the face box it redraws the clothes (drift SSIM 0.53) and is rejected (O-02). LIVE: a best picture passes every gate (attempt 5: identity 0.508, small change from a source that is already the user's ideal); its 3 placements used a face that was the source unchanged (0.944: recognition defect).", "L-03"),
    ("4", "H-06", "raw return of attempt 1, aligned fine", "no; the composite was rejected by the AI 'not better than the source' comparison", "pool identity 0.561, size 1.0, neck gap 2.1",
     "the general AI comparison was wrong against the user's eye; it must not reject",
     "Offline: merged it is a clean picture that passes every gate (O-03). LIVE: attempt 5 passes every gate (identity 0.593, dE 1.0, neck +2.1) but the source's broad laugh became a calm closed-mouth smile.", "L-04"),
    ("5", "N-07", "the crop SENT to Gemini, byte-identical to the source (the run died on the quota)", "-", "-", "the user rated the source crop; 'no change' is exactly right",
     "LIVE: both attempts passed at once (identity 0.439 / 0.485); best = attempt 2, near-identical to the source (gt_sim 0.837).", "L-05"),
    ("6 / 9", "I-01", "composite, foreign mode, a RESCUE of attempt 3", "yes: 'more than perfect', the ideal",
     "identity 0.506, size 0.981, shift 0.115, light dE 5.7, neck gap 4.9, pose within 2.4 degrees, expression same", "face first, then the same face re-rendered in the right frame",
     "LIVE: not reproduced under the rule: 0 of 3 completed attempts (L-06; the closest, attempt 3: head moved 0.188, face too bright dE 25.8; the quota ran out on attempt 4) and 0 of 6 in a second run (L-11: face lit dE 30-34 against a limit of 20; the 3 placements of a 0.62 face came back as bright).", "L-06"),
    ("7", "X-03", "raw return of attempt 1, re-framed (scale 1.31, shift 0.36), never measured", "no, headshot", "pool identity 0.595 vs source crop 0.488; classified as another man's photo (109 px face), hair and expression replaced",
     "classification by the number misfires on a tiny face", "Offline: merged by the face box it passes the gates but a ghost of the old head shows (O-04). LIVE (2026-09-22 02:55): nothing passed in 6 attempts, every head 13-25 percent too big (closest attempt 3: size 1.194, moved 0.146); no ghost seen at picture size (L-10).", "L-10"),
    ("8", "P-01", "composite, own mode, normal path", "yes, perfect", "identity 0.488, gt_sim 0.762, size 1.009, light dE 1.0", "the own path with the attractiveness policy works on a real photo",
     "LIVE (2026-09-22 02:51): best = attempt 2 of 2, identity 0.223 against the approved 0.488, drift SSIM 0.921; the reflection appears not to match the new curls (L-09): a regression. Round-8 runs of the same photo (rolled back) had identity 0.407 / 0.46.", "L-09"),
    ("9", "I-02", "gen output 20260917_144731 v1_0.jpg (md5 match to D:\\Downloads\\AI me\\beach.jpg): from scratch, raw, no restore", "yes, ideal", "not a replicate run",
     "9 whole references, identity-lock text, scene text with pose, expression, light direction and lens", "n/a (not a paste-back)", ""),
]


def write_matrix(wb: Workbook, rows: list[dict]):
    by = {r["id"]: r for r in rows}
    ws = wb.create_sheet("Verdict matrix (R7)")
    heads = ["#", "Row ID", "Photo", "COMPLETE IMAGE FILE LOCATION", "What it actually is", "a (user)", "i (user)", "Complete picture?", "Measured then", "What it teaches",
             "Identity now (pool)", "Similarity to source", "Size", "Moved", "What the HARD RULE did on this photo (live run 2026-09-21 21:33-22:42 unless it says offline)", "Live row ID", "Live picture location"]
    widths = [6, 8, 15, 70, 44, 8, 8, 38, 40, 40, 10, 10, 8, 8, 70, 8, 70]
    ws.cell(row=1, column=1, value="The user's verdict matrix of 2026-09-21 (a = attractiveness, i = identity; P improved, N degraded, O no change) next to what the hard rule did").font = F_TITLE
    for c, (h, w) in enumerate(zip(heads, widths), 1):
        cell = ws.cell(row=2, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[2].height = 60
    for i, (num, rid, what, comp, meas, teach, live, live_id) in enumerate(MATRIX, 3):
        r = by[rid]
        lv = by.get(live_id)
        vals = [num, rid, r["group"], r["path"], what, r["a"], r["i"], comp, meas, teach, r["m"].get("identity"), r["m"].get("gt_sim"), r["m"].get("size"), r["m"].get("shift"),
                live, live_id, lv["path"] if lv else ""]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=i, column=c)
            cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
            if c in (4, 17) and v:
                set_link(cell, v)
            else:
                cell.value = v if v != "" else None
            if c in (11, 12, 13, 14) and isinstance(v, (int, float)):
                cell.number_format = "0.000"
    ws.freeze_panes = "D3"


# ------------------------------------------------------------------------------------------------ the new live run
def write_live(wb: Workbook, rows: list[dict]):
    ws = wb.create_sheet("New live run (RULE)")
    ws.cell(row=1, column=1, value="The eleven live runs of the hard rule (default pipeline, no flags): 2026-09-21 21:33-22:42 and, after the quota reset, 2026-09-22 02:33-03:01. None of the pictures is reviewed by the user yet.").font = F_TITLE
    heads = ["Photo", "Run folder", "Result", "Attempts made", "Passing attempts", "Good faces found (attempt: identity)", "Placements (attempt <- face of attempt)", "How each attempt ended",
             "Result picture (COMPLETE IMAGE FILE LOCATION)", "Row ID", "Identity", "Similarity to source", "Size", "Moved", "dE", "Neck gap", "SSIM", "Changed px outside the crop", "AI face ranking", "Run log"]
    widths = [14, 40, 30, 9, 9, 26, 26, 90, 70, 7, 9, 10, 8, 8, 7, 8, 8, 12, 18, 55]
    for c, (h, w) in enumerate(zip(heads, widths), 1):
        cell = ws.cell(row=2, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[2].height = 48
    live = [r for r in rows if r["id"].startswith("L-")]
    live.sort(key=lambda r: r["run"])
    for i, r in enumerate(live, 3):
        d = load_json(FB / r["run"] / "run.json") or {}
        cands = d.get("candidates", [])
        passing = [c["index"] for c in cands if c.get("verdict") in ("accept", "uncertain")]
        good = [f"{c['index']}: {c['good_face']['score']}" for c in cands if c.get("good_face")]
        place = [f"{c['index']} <- {c['placement_of_attempt']}" for c in cands if c.get("placement_of_attempt")]
        ends = []
        for c in cands:
            m = c.get("metrics") or {}
            if "score" not in m:
                ends.append(f"{c['index']}: no picture (image quota ran out)" if d.get("status") == "usage_limit" else f"{c['index']}: no picture")
            else:
                why = "PASSED (" + (c.get("verdict") or "") + ")" if c.get("verdict") in ("accept", "uncertain") else "; ".join(p.split(" (")[0] for p in c.get("problems", []))
                ends.append(f"{c['index']}: {why}")
        res = "best: attempt " + str((d.get("best") or {}).get("candidate")) + " (" + str((d.get("best") or {}).get("verdict")) + ")" if d.get("best") else \
            "nothing promoted; closest = attempt " + str(closest_of(FB / r["run"], d))
        vals = [r["group"], r["run"], res, d.get("attempts"), ", ".join(map(str, passing)) or "none", ", ".join(good) or "none", ", ".join(place) or "none", "\n".join(ends), r["path"], r["id"],
                r["m"].get("identity"), r["m"].get("gt_sim"), r["m"].get("size"), r["m"].get("shift"), r["m"].get("dE"), r["m"].get("neck"), r["m"].get("ssim"), r["m"].get("outside_px"),
                r["ai_rank"], str(FB / r["run"] / "run.log")]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=i, column=c)
            cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
            if c in (9, 20) and v:
                set_link(cell, v)
            else:
                cell.value = v if v not in ("", None) else None
            if c in (11, 12, 13, 14, 17) and isinstance(v, (int, float)):
                cell.number_format = "0.000"
    ws.freeze_panes = "C3"


# ------------------------------------------------------------------------------------------------ runs summary and candidates
def all_replicate_runs():
    fb = {p.name for p in FB.iterdir()}
    return sorted([p for p in FB.iterdir() if p.is_dir() and "_replicate_" in p.name]
                  + [p for p in OUTS.iterdir() if p.is_dir() and "_replicate_" in p.name and p.name not in fb], key=lambda p: p.name)


def write_runs(wb: Workbook, rows: list[dict]):
    ws = wb.create_sheet("Runs summary")
    heads = ["Run folder", "Started", "Review round", "Code state", "Source photo (short)", "Source photo location", "Source: own or another man's", "Expression policy", "Attempts made",
             "Status", "Result", "Result picture (COMPLETE IMAGE FILE LOCATION)", "Attempts that passed", "Good faces found (attempt: identity)", "Placements (attempt <- face of attempt)",
             "AI face ranking", "Feedback from the user", "Ranking row(s)", "Evidence folder", "Working folder (outputs; may be cleared)"]
    widths = [44, 17, 8, 34, 24, 50, 10, 16, 9, 12, 34, 70, 12, 26, 24, 22, 60, 12, 60, 60]
    for c, (h, w) in enumerate(zip(heads, widths), 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 48
    rows_by_run: dict[str, list[dict]] = {}
    for r in rows:
        rows_by_run.setdefault(r["run"], []).append(r)
    i = 2
    fb = {p.name for p in FB.iterdir()}
    all_dirs = sorted([p for p in FB.iterdir() if p.is_dir() and p.name not in ("ideal", "rule_check_offline")]
                      + [p for p in OUTS.iterdir() if p.is_dir() and p.name[:8].isdigit() and p.name not in fb and "_angle_refs" not in p.name], key=lambda p: p.name)
    for d in all_dirs:
        j = load_json(d / "run.json") or {}
        rep = "_replicate_" in d.name
        ts = d.name[:15]
        started = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
        rnd = "gen" if not rep else round_of(d.name)
        cands = j.get("candidates", []) if rep else []
        if rep:
            best = j.get("best")
            if best:
                res = f"best: attempt {best.get('candidate')} ({best.get('verdict')})"
                pic = next((str(d / f) for f in ("best.png", "best.jpg") if (d / f).exists()), "")
            elif (d / "not_passing_closest.jpg").exists():
                res = f"nothing promoted; closest: attempt {closest_of(d, j)}"
                pic = str(d / "not_passing_closest.jpg")
            else:
                res, pic = "no picture" + (" (image quota ran out)" if j.get("status") == "usage_limit" else ""), ""
            passing = ", ".join(str(c["index"]) for c in cands if c.get("verdict") in ("accept", "uncertain")) or "none"
            good = ", ".join(f"{c['index']}: {c['good_face']['score']}" for c in cands if c.get("good_face")) or ""
            place = ", ".join(f"{c['index']} <- {c['placement_of_attempt']}" for c in cands if c.get("placement_of_attempt")) or ""
            sp = scene_path(j)
            short = re.sub(r"^\d{8}_\d{6}_replicate_", "", d.name)
        else:
            f = next((x for x in ("best.jpg", "v1_0_restored.jpg", "v1_0.jpg") if (d / x).exists()), None)
            res, pic, passing, good, place, sp = ("generated picture" if f else "no picture kept"), (str(d / f) if f else ""), "", "", "", None
            short = re.sub(r"^\d{8}_\d{6}_", "", d.name).replace("-", " ")
        mine = rows_by_run.get(d.name, [])
        direct = [x for x in mine if x["cls"] not in ("BATCH_REJECTED",) and not x["id"].startswith(("A-", "L-", "O-", "C-"))]
        if direct:
            fb = "; ".join(f"{x['id']}: " + (x["verdict"][:120]) + (f" (a {x['a']}, i {x['i']})" if x["a"] or x["i"] else "") for x in direct)
        elif d.name in BATCH_R1:
            fb = BATCH_TEXT["R1"]
        elif d.name in BATCH_R2:
            fb = BATCH_TEXT["R2"]
        elif not rep:
            fb = BATCH_TEXT["gen"]
        elif d.name in NO_VERDICT_RUNS:
            fb = "no verdict given"
        else:
            fb = "none yet" if rnd in ("R8", "RULE") else "none given"
        vals = [d.name, started, rnd, CODE_STATE.get(rnd, rnd), short, (str(sp) if sp.exists() else "(deleted by the user since) " + str(sp)) if sp else "", j.get("source_kind") or "", j.get("expression_policy") or "", j.get("attempts") if rep else None,
                j.get("status") or "", res, pic, passing, good, place, ", ".join(f"{k}: {v:g}" for k, v in ai_wins(d).items()), fb, ", ".join(x["id"] for x in mine), str(d),
                str(OUTS / d.name) if (OUTS / d.name).exists() else ""]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=i, column=c)
            cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
            if c in (6, 12, 19, 20) and v and Path(str(v)).exists():
                set_link(cell, str(v))
            else:
                cell.value = v if v not in ("", None) else None
        i += 1
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{i - 1}"


def write_candidates(wb: Workbook):
    ws = wb.create_sheet("Candidates")
    heads = ["Run folder", "Review round", "Attempt", "Pipeline verdict", "Identity (pool)", "Similarity to source face", "Head size / source", "Head moved (face widths)", "Face light dE", "dL (+ brighter)",
             "Neck gap", "SSIM outside the head", "Mean abs diff outside the head", "Pixels changed outside the crop", "AI judge flagged", "AI comparison with source", "Gates failed / problems", "Warnings",
             "Merged by", "Ring match (ECC)", "Placement of the face of attempt", "Good face found (identity)", "Picked as best", "Closest (nothing passed)", "COMPLETE PICTURE of this attempt", "Head crop returned by Gemini"]
    widths = [44, 8, 8, 10, 10, 11, 10, 10, 9, 9, 9, 10, 11, 12, 32, 12, 70, 40, 26, 9, 12, 11, 8, 9, 70, 60]
    for c, (h, w) in enumerate(zip(heads, widths), 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 60
    i = 2
    for d in all_replicate_runs():
        j = load_json(d / "run.json") or {}
        best = (j.get("best") or {}).get("candidate")
        closest = closest_of(d, j) if not j.get("best") else None
        for c in j.get("candidates", []):
            n = c.get("index")
            m = c.get("metrics") or {}
            st = (c.get("stages") or [{}])[-1] if c.get("stages") else {}
            pic = d / f"cand{n}.png"
            raw = next((p for p in (d / "raw" / f"c{n}_head_raw.jpg", d / f"c{n}_head_raw.jpg") if p.exists()), None)
            vals = [d.name, round_of(d.name), n, c.get("verdict") or ("no picture" if "score" not in m else ""), m.get("score"), m.get("gt_sim"), m.get("size_ratio"), m.get("face_shift_frac"),
                    (m.get("light") or {}).get("dE"), (m.get("light") or {}).get("dL"), m.get("neck_gap"), (m.get("drift") or {}).get("ssim"), (m.get("drift") or {}).get("mean_abs_diff"),
                    (c.get("outside_check") or {}).get("changed_outside"), flags(c.get("judge")), (c.get("face_vs_source") or {}).get("winner") or "", "; ".join(c.get("problems", [])),
                    "; ".join(c.get("warnings", [])), st.get("aligned_by") or "", st.get("ecc"), c.get("placement_of_attempt"), (c.get("good_face") or {}).get("score"),
                    "yes" if n == best else "", "yes" if n == closest else "", str(pic) if pic.exists() else "", str(raw) if raw else ""]
            for k, v in enumerate(vals, 1):
                cell = ws.cell(row=i, column=k)
                cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
                if k in (25, 26) and v:
                    set_link(cell, v)
                else:
                    cell.value = v if v not in ("", None) else None
                if k in (5, 6, 7, 8, 12) and isinstance(v, (int, float)):
                    cell.number_format = "0.000"
            i += 1
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{i - 1}"


# ------------------------------------------------------------------------------------------------ limits, concerns, preserve / fix
LIMITS = [
    ("Identity: accept", ">= 0.52", "pool score of any output face", "APPROVED 2026-09-20", "calibrate.py: genuine photos of the user score 0.26-0.88 against each other, outputs he called good 0.53-0.68, drifted ones 0.23-0.58, a different man 0.11. Only the extremes are decidable; the user's eye decides the middle. The approved ideals measure 0.49-0.51 (turned faces score low).", "facecard.json identity_thresholds"),
    ("Identity: hard reject", "< 0.20", "pool score", "APPROVED 2026-09-20", "same calibration", "facecard.json identity_thresholds"),
    ("Source classification", "own if the source face's pool score >= 0.40, else another man's", "chooses zone (face / head), expression policy (auto / same) and limits", "APPROVED 2026-09-20", "Misfires on a tiny face: the table-tennis photo of the user (109 px face) scored 0.40 and was treated as another man's.", "facecard.json identity_thresholds.own_min"),
    ("Head size, own photos", "0.94 - 1.04 of the source head", "output head width / source head width", "APPROVED (2026-09-21 plan); 1.03 was a slip and is fixed", "Every output the user approved measures 0.959-1.018; car2 at 1.04 with a brighter face was called out of proportion; 1.03 rejected car2 attempts 5 and 6, complete pictures with no other problem. NOTE: the user-approved rocky 034849 measures 1.058.", "facecard.json gates.size_own; replicate.py SIZE_MIN/SIZE_MAX"),
    ("Head size, another man's photo", "0.94 - 1.04", "same", "PROVISIONAL", "The user called 1.054 'too big' (run 064235); the floor was 0.95 until the approved cand3 measured 0.949. No evidence for 'too small'.", "facecard.json gates.size_foreign"),
    ("Head moved", "<= 0.12 face widths", "distance between the source and output face centres", "PROVISIONAL", "Approved complete pictures measure 0.028-0.115 (the ideal I-01 is 0.115).", "replicate.py SHIFT_MAX"),
    ("Face light, own photos", "dE <= 14", "Lab distance of the output face from the source face", "PROVISIONAL (two judgements)", "Fine: 12.2 and 5.5; worse: 16.5. A brighter face than the dim photo is accepted up to about 9.9 (rocky).", "facecard.json gates.light_de_max"),
    ("Face light, another man's photo", "dE <= 20", "same", "PROVISIONAL (one review)", "Approved cand3 measured 18.4; renders called pasted or mismatched measured 31-35.", "facecard.json gates.light_de_max_foreign"),
    ("Neck gap", "<= +10 (face brighter than its neck by more than in the source)", "face L minus neck L, output minus source", "PROVISIONAL", "Approved outputs within +6.5; car2 (called out of proportion) +13.7. The one-sided form missed the nerd picture (neck L +27); a two-sided check was a round-8 idea and is not in the code.", "facecard.json gates.neck_gap_max"),
    ("Unchanged", "similarity to the SOURCE face > 0.90 = rejected", "own photos", "PROVISIONAL", "Approved outputs 0.23-0.75; everything the user called 'as it is' 0.93-0.99.", "facecard.json gates.unchanged_gt_sim"),
    ("Redrawn clothes / background", "SSIM >= 0.80 and mean abs diff <= 10 outside the head, inside the crop", "compared with the source crop", "measured 2026-09-20", "Good returns 1.3-3.7 / SSIM 0.95-0.996; a wrongly framed return 54.5 / 0.35.", "replicate.py DRIFT_MAD_MAX, DRIFT_SSIM_MIN"),
    ("Outside the crop", "0 pixels changed", "every output (asserted before best.png / best.jpg / not_passing_closest.jpg are written)", "HARD RULE", "The whole crop is pasted back with a soft border; everything else is the source's own pixels.", "composite.verify_outside; replicate.py complete_picture()"),
    ("Alignment of the returned crop", "ring match ECC >= 0.80, scale within +-0.20, shift <= 0.30; otherwise the return is REFUSED (not merged) and the next attempt asks for the exact framing", "before pasting", "measured 2026-09-20; face-box merge removed 2026-09-23", "The face-box merge (2026-09-21 to 09-23) laid a head drawn at another scale over the real one: IMG_0862 got a second hairline, a second ear and a smeared collar (user: unreal, monsterish). None of the 8 face-box merges ever passed; every best version had a matching ring (ECC >= 0.90, scale <= 1.048, shift <= 0.092).", "replicate.py align_to_ring, edit_stage"),
    ("Gemini's sparkle watermark", "never pasted (hole of radius ~52 px at 120 px in from the bottom-right corner of the return)", "every paste", "measured 2026-09-20", "The star at the bottom right of some source photos is IN the source (night out, car2, beach, nerd): not a pipeline defect.", "replicate.py SPARKLE_OFFSET / SPARKLE_RADIUS"),
    ("Attempts", "up to 6 Gemini image calls per run, stops after 2 passing; 3 of them may be placements of a good face", "per run", "RESCUE_ATTEMPTS = 3 (the hard rule)", "A placement sends the head crop of the good face as the last reference and asks for it at the position, size, turn and tilt of the source.", "replicate.py RESCUE_ATTEMPTS, --max-attempts"),
    ("AI judge", "HARD (the attempt is retried): head angle changed, glasses not preserved, double image / ghost, seam visible, lighting inconsistent, clothes / body / hands / background changed; 'expression differs' is hard only when the expression must match (another man's photo). SOFT (warning only): a fold under the chin, reflection mismatch, 'expression differs' on the user's own photo (by design)", "text call to Gemini on source crop vs output crop", "measured", "The general question 'is it better than the source' is NOT a gate any more (it agreed with the user's eye in 1 of 3 cases): it only ranks.", "replicate.py JUDGE_PROMPT, judge_failures"),
    ("Image quota", "~84 credits per image, 2,400 per 5-hour window", "Gemini web account", "observed", "Exhausted at 22:42 on 2026-09-21; reset at 02:31 IST, after which the batch finished all its photos by 03:01. The batch script waits for the reset and stops on an authentication failure.", "gemini_webapi UsageLimitExceededError"),
]

CONCERNS_SOURCES = [
    ("kayak", ".cache\\super_favs\\google-1__IMG_5549.jpg", "three faces / ghost outlines from the reflections; attractive but not looking like the user; awkward tense mouth instead of the user's own calm reaction; face lighting off (dE 16.5)", "calm closed-lip smile with soft eyes, lit like the photo (060329 emotion, 150905 attempts 2 and 6)"),
    ("rocky", ".cache\\super_favs\\google-1__IMG_4861_SnapseedCopy.jpg", "the round-2 heuristic output (053504)", "034849, 061004, 153829 (a face brighter than the dim photo is acceptable up to dE 9.9)"),
    ("stained glass (with reflection)", ".cache\\super_favs\\google-4__IMG_5850_Original.jpg", "unnatural lighting; reflection not handled or mirroring a different reaction; a double chin (it is in the SOURCE, not generated)", "face and reflection rendered in the same pass (060631); 151934 very promising; 070221 everything perfect"),
    ("table tennis", ".cache\\super_favs\\google-2__IMG_3943.jpg", "wrong overlapping face; needs a more attractive expression; the round-7 return was called N on attractiveness", "the hard head angle nailed (061432)"),
    ("IMG_0862", ".cache\\super_favs\\google-4__IMG_0862.jpg", "none given per output (batch verdicts only)", "-"),
    ("Pinterest (another man's photo)", ".cache\\pinterest_target.jpg", "face overlap; two faces; head too big; hair only partly the user's; face position and expression not matching the reference; head cut-pasted, neck pasted, tilt off, lighting mismatched", "000411 best; 064221 best = THE IDEAL: face and neck lit like the photo, pose within 2 degrees, the reference's smile, the user's own hair, size right"),
    ("night out", "(deleted by the user since) D:\\Downloads\\AI me\\night out.jpg", "returned as it is, three times; the better face (002751 c1_head_raw, 042258 c2_head_raw) was thrown out by the gates", "fuller curly hair, defined face, calm slight smile, clearly the user"),
    ("nerd", "(deleted by the user since) D:\\Downloads\\AI me\\nerd.jpg", "before and after the same, twice; a N / i P on the round-7 picture (neck +27 lighter)", "-"),
    ("mountain", "(deleted by the user since) D:\\Downloads\\AI me\\mountain.jpg", "face replication worse than the source", "the source crop rated a O / i P"),
    ("beach", "D:\\Downloads\\AI me\\beach.jpg", "no change at all, twice. NOTE: this photo is itself the user's second ideal (a from-scratch generation)", "the source is already ideal"),
    ("car2", "(deleted by the user since) D:\\Downloads\\AI me\\car2.jpg", "face size and lighting not proportional to the body and scene, twice", "the head crop c1 of run 043841 (a P / i P)"),
]
CONCERNS_GENERAL = [
    "Face overlapping, ghost outline or a duplicate face (032241, 032923, 054417, 053307).",
    "Face lighting unnatural, or the face and neck brighter than the photo and the body: the cut-and-paste look (032650, 060329, 173847, car2).",
    "Head or face too big or out of proportion with the body (064235, car2).",
    "Head angle, tilt or position not matching the source or reference (round 1 in general, 165702, 173847).",
    "Expression awkward or tense (064200); expression not matching the reference (165702); a laugh or teeth the reference does not have (054417, 173847).",
    "Hair not entirely the user's (152548).",
    "A reflection that is not the user or has a different reaction (063313).",
    "The output only looks like the user and the face is not replaced: a look-alike returned unchanged (nerd, beach, night out).",
    "Face replication worse than the source (mountain).",
    "Attractive but not the user (053307).",
    "Changing the scenery, background, clothes or physique (the very first message; the gen runs).",
    "A fold or double chin that the source does not have (the one the user reported was in the source).",
    "NEW (2026-09-21): a good face that exists only as a head crop, or a head crop reported as the result (the hard rule).",
]

PRESERVE = [
    ("PRESERVE", "Paste-back with zero change outside the crop", "Every replicate output has 0 changed pixels outside the crop (asserted, and recomputed in this workbook); the whole crop is pasted with a soft border.", "I-01, P-01, every 'YES' row"),
    ("PRESERVE", "The path that made the ideal for another man's photo", "References sent as identity only, the reference photo's own expression, the light limit of 20, the size band, and the RESCUE (a good face re-rendered in the source's framing).", "I-01, P-02"),
    ("PRESERVE", "The path that made the perfect own-photo picture", "Own path with the attractiveness policy (auto expression), zone face. Under the rule it still passes on kayak (identity 0.597 = the approved 0.598) and rocky (0.494 against 0.534 / 0.556), but NOT on stained glass (0.223 against 0.488).", "P-01, L-07, L-08, L-09"),
    ("PRESERVE", "The unchanged gate", "similarity to the source face > 0.90 = as it is = not a result; it is exactly what the user called 'as it is'.", "N-01..N-06, L-02"),
    ("PRESERVE", "Pairwise AI face comparison in both orders, as a RANKING", "It ranks the attempts of a run; it never vetoes (the general 'better than the source' question agreed with the user in 1 of 3 cases).", "L-03, H-06"),
    ("PRESERVE", "The identity floor as a floor only", "0.52 accept / 0.20 reject; turned or profile faces score low, so identity below 0.52 is 'uncertain', not a failure by itself.", "I-01 (0.506), P-01 (0.488)"),
    ("PRESERVE", "Face and reflection in one pass", "A separate reflection pass does not mirror the real face.", "H-02, X-04"),
    ("PRESERVE", "Identity references are head crops (3x the face box, 768 px)", "And a placement sends the head crop of the good face, never the whole raw return.", "L-01"),
    ("PRESERVE", "The expression to aim for", "Calm closed-lip smile with soft eyes, or the reference's own expression on another man's photo.", "X-01, P-06, H-01, I-01"),
    ("FIXED", "A rendered head is never a result", "Merged into the complete picture first (ring, else face box); raw returns in raw/; best.* and not_passing_closest.jpg asserted complete. LIVE-PROVEN on night out (identity 0.884 face became a picture that passes every gate). Uncommitted until the user approves the pictures.", "L-01, O-01..O-04, H-04"),
    ("FIXED", "Own-photo size upper limit", "1.03 was a slip; the approved value is 1.04 (rejected car2 attempts 5 and 6 wrongly).", "H-06"),
    ("OPEN - DEFECT", "Face recognition for placement does not exclude a return that is the source unchanged", "replicate.py good_face_in() (line 640) accepts any raw return with pool identity >= 0.52 (and a matching expression under the same-expression policy); its docstring and the approved plan (R4: 'not the source returned unchanged, own photos gt_sim <= 0.90') say it must also reject an unchanged face, but the check is missing and its `own` argument is unused. Live effect: beach's 3 placements and nerd's first placement placed a face that WAS the source (raw similarity 0.944 and 0.902), nerd's other two a near-unchanged one (0.893): 6 of the 20 completed placements (all in the first half of the batch) were wasted. Not fixed: the code is uncommitted and awaits the user's review; the fix is one condition using the source embedding and gates.unchanged_gt_sim. The earlier offline check judged the 'as it is' runs by the gate on the composite and never ran this function on them.", "L-02, L-03"),
    ("OPEN", "Placement (rescue) reliability", "Live: 20 completed placements, 4 passed every gate: night out attempt 2 (identity 0.84), car2 attempt 2 (identity only 0.367, 'uncertain'), kayak attempt 2 (0.473, 'uncertain') and rocky attempt 3 (0.494; it repaired the light and neck gap its source attempt had failed). Of the 16 failures, 6 placed an unchanged or near-unchanged face (beach 3, nerd 3: the defect above) and 10 placed a genuinely changed face: night out 2 and car2 2 (size 0.89 / angle changed; face brighter than the neck; crop redrawn), Pinterest 3 (all as bright as their source, dE 30.9-33.2) and table tennis 3 (head 13-17 percent too big). A placement repairs light only when the fault was in that one attempt's exposure (rocky), not when the model keeps making the same kind of render.", "L-01..L-04, L-07, L-08, L-10, L-11"),
    ("OPEN", "The ideal for another man's photo is not reproducible on demand", "Pinterest passed 1 of 4 (000411), 1 of 6 (064221), 1 of 6 (165147, R8 code), 0 of 6 (171345, R8 code), 0 of 3 completed attempts (223507, RULE code) and 0 of 6 (20260922_023359, RULE code).", "I-01, L-06, L-11"),
    ("OPEN", "Selection can pick a low-identity 'uncertain' candidate", "Stained glass: the run stopped after 2 attempts because both passed as 'uncertain' (identity 0.38 and 0.223), and the AI face ranking (1.0 against 0.0) picked the 0.223 one, just above the 0.20 hard-reject line; the user-approved picture of the same photo measured 0.488. Identity is only a floor in the selection key and the AI ranking outranks it.", "L-09, P-01"),
    ("OPEN", "Table tennis: every render's head is 13-25 percent too big", "6 of 6 attempts and 3 of 3 placements failed the size gate (1.136-1.252): the photo is classified as another man's (109 px face, below own_min 0.40), so the render is a foreign-mode edit with a larger head.", "L-10, X-03"),
    ("OPEN", "The nerd photo still comes back unchanged", "Rendered faces change the head angle or the clothes; placements did not repair it. The user called the picture 'as it is' twice (003247, 015354) and, on the round-7b picture, a N / i P (neck lighting).", "L-02, R-15"),
    ("OPEN", "A ghost of the replaced head after a merge", "Faint grey dome behind the new hair passes every number.", "O-04"),
    ("OPEN", "Expression change on the user's own photos (car2)", "The source's broad laugh became a calm closed-mouth smile in the live run; the user rated the laughing head crop P/P.", "L-04, H-06"),
    ("OPEN", "Two-sided face-and-neck lightness check", "Only 'face brighter than neck' is gated; the nerd picture's neck was 27 lightness units lighter than the source and passed. A round-8 idea, not in the code.", "R-15"),
    ("OPEN", "A whole-photo re-render of a reference cannot be pasted", "Beach c1 was Gemini re-rendering the kayak reference, not an edit of the beach crop.", "H-05, O-02"),
    ("DONE", "The user's verdicts on the eleven live pictures (2026-09-23)", "night out major improvement (a P i P, kept); kayak slight improvement (P P, kept); rocky a P i N (kept); car2 a P i P but not matching the source (its laugh was closed); beach an improvement that was not needed (already a best version); nerd no change; stained glass a O i N; mountain a N i N; Pinterest twice and table tennis 'worst'. The four offline merges were not reviewed.", "L-01..L-11"),
    ("FIXED (uncommitted, 2026-09-23)", "Changes made from the best versions and the verdicts", "C1 own / another man's decided on a head crop of the source (table tennis becomes own; no other photo changes class). C2 a face that is the source returned unchanged is never placed. C3 on another man's photo a face that failed the light or neck check is not placed. C4 a laugh or broad open smile in his own photo is kept (the source's own expression). C5 his own photo may not lose more than 0.20 of identity against the source (provisional). C7 the closest not-passing picture prefers one lit like the photo. C8 a source that is one of the user's best versions (same file content) is returned unchanged unless --force. Checkpoint of the state that made the best versions: .cache/patches/rule_state_of_best_versions_2026-09-23.patch.", "L-01..L-11, B-01, C-02"),
    ("DO NOT RETRY", "Whole-photo references for the crop pipeline (refs_mode all_whole)", "Measured worse: Pinterest pick dE 15.8, stained glass 1 of 6 passed (round 8, rolled back).", "R8 rows A-*"),
    ("DO NOT RETRY", "The pose gate / expression experiment", "Produced a pasted-looking head and neck (face L 58 / neck L 62 against 37 / 31): references leak exposure into the render; rolled back at the user's request.", "R-10, R-11"),
    ("DO NOT RETRY", "The face-only AI comparison as a veto", "Agreed with the user's eye in 1 of 3 cases.", "H-06"),
    ("DO NOT RETRY", "Heuristic post-processing (relight, grain, blur, landmark warp, mask cut-out)", "'Images are getting worse; non-AI processing is making it all worse.'", "R2 batch rows"),
    ("DO NOT RETRY", "A separate reflection pass", "Does not mirror the real face.", "X-04"),
    ("DO NOT RETRY", "From-scratch generation for a photo that must keep its scene", "Changes scenery, clothes, physique (the very first message); the one exception is the ideal I-02, made with whole references and explicit pose/light text.", "gen rows G-*, I-02"),
]


def write_simple(wb: Workbook, title: str, heads: list[str], widths: list[int], data: list[tuple], link_cols=(), band_col=None, colors=None, tall=False):
    ws = wb.create_sheet(title)
    for c, (h, w) in enumerate(zip(heads, widths), 1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, fill("1F3864"), Alignment(wrap_text=True, vertical="center", horizontal="center"), BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 34
    for i, rowvals in enumerate(data, 2):
        for c, v in enumerate(rowvals, 1):
            cell = ws.cell(row=i, column=c, value=v)
            cell.font, cell.alignment, cell.border = F_BASE, WRAP_TOP, BORDER
        if colors and band_col is not None:
            col = colors.get(rowvals[band_col])
            if col:
                ws.cell(row=i, column=band_col + 1).fill = fill(col)
    ws.freeze_panes = "A2"
    return ws


def main():
    print("measuring...")
    meas = Measurer()
    rows = assemble(meas)
    save_cache()
    wb = Workbook()
    write_readme(wb, rows)
    write_ranking(wb, rows)
    write_matrix(wb, rows)
    write_live(wb, rows)
    write_runs(wb, rows)
    write_candidates(wb)
    write_simple(wb, "Limits & gates", ["Rule", "Value", "Applies to", "Status", "Evidence / why", "Where it lives"], [28, 44, 36, 26, 90, 40], LIMITS)
    src_rows = [(a, b, c, d) for a, b, c, d in CONCERNS_SOURCES]
    ws = write_simple(wb, "Concerns checklist", ["Source photo", "Where it is", "Concerns the user raised (a new output must have none of them)", "What the user counted as good"], [26, 52, 90, 70], src_rows)
    r0 = len(src_rows) + 3
    ws.cell(row=r0, column=1, value="Concerns that apply to any output").font = F_BOLD
    for k, t in enumerate(CONCERNS_GENERAL, 1):
        c = ws.cell(row=r0 + k, column=1, value=k)
        c.font, c.alignment = F_BASE, CENTER_TOP
        c2 = ws.cell(row=r0 + k, column=2, value=t)
        c2.font, c2.alignment = F_BASE, WRAP_TOP
        ws.merge_cells(start_row=r0 + k, start_column=2, end_row=r0 + k, end_column=4)
    write_simple(wb, "Preserve vs fix", ["Status", "Topic", "What / why", "Evidence rows"], [14, 52, 120, 40], PRESERVE, band_col=0,
                 colors={"PRESERVE": "C6E0B4", "FIXED": "BDD7EE", "FIXED (uncommitted, 2026-09-23)": "BDD7EE", "DONE": "E2EFDA", "OPEN": "FFE699", "OPEN - DEFECT": "F4B084", "DO NOT RETRY": "F4B6B6"})
    wb.move_sheet("Preserve vs fix", offset=-(len(wb.sheetnames) - 3))
    wb.properties.title = "nano-banana-facecard feedback matrix"
    wb.properties.creator = "Claude (assistant), from the user's verdicts"
    wb.save(OUT)
    print("saved", OUT, "rows", len(rows))
    return rows


if __name__ == "__main__":
    main()
