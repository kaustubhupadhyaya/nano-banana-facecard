"""The user's verdicts of 2026-09-23 on the eleven hard-rule pictures, and their best versions (D:/Downloads/AI me). Applied on top of fm_rows and
fm_rows2 (the dicts are updated in place when this module is imported). Data only."""
from fm_rows import CLASSES, ROWS
from fm_rows2 import ROWS2

B_USER3 = "the user's own codes (2026-09-23 verdicts)"
B_WORDS3 = "derived from the user's words (2026-09-23)"
BV = r"D:\Downloads\AI me"
CLASSES["BEST_VERSION"] = (95, "01b BEST VERSION - the user keeps this picture as the best version of the photo (D:/Downloads/AI me)")

UPDATES = {
    "L-01": dict(cls="BEST_VERSION", verdict="major improvement a,i-p (kept as the best version nightout.jpg)", a="P", i="P", basis=B_USER3,
                 extra_paths=["best.png", BV + r"\nightout.jpg"]),
    "L-02": dict(cls="NO_CHANGE", verdict="nochanges", a="O", i="O", basis=B_WORDS3),
    "L-03": dict(cls="IMPROVEMENT", verdict="improvement ,but it was already perfect and was being used as reference hence wasnt requirred to change again",
                 a="P", i="P", basis=B_WORDS3,
                 use="A photo that is already one of the user's best versions is not to be changed: the pipeline now returns such a source unchanged (C8)."),
    "L-04": dict(cls="MIXED", verdict="not the same as the reference image at all, do you even have the correct reference image? a,i-p but not amtching reference",
                 a="P", i="P", basis=B_USER3,
                 notfine="The source's broad open-mouth laugh became a calm closed-mouth smile. The source file was the right one (all four car2 runs used the same crop). The user's best car2 (car.png, row C-02) kept the laugh.",
                 use="A laugh in his own photo must stay a laugh: the pipeline now keeps the source's expression when Gemini reads a broad or open-mouth smile (C4)."),
    "L-05": dict(cls="REJECTED", verdict="no improvement a,i -n", a="N", i="N", basis=B_USER3),
    "L-06": dict(cls="REJECTED", verdict="worst version till now. worst.", a="", i="", basis="empty: 'worst' does not separate a and i"),
    "L-11": dict(cls="REJECTED", verdict="worst", a="", i="", basis="empty: 'worst' does not separate a and i"),
    "L-07": dict(cls="BEST_VERSION", verdict="ok, slight improvement a,i -p (kept as the best version kayak.jpg)", a="P", i="P", basis=B_USER3,
                 extra_paths=["best.png", BV + r"\kayak.jpg"]),
    "L-08": dict(cls="BEST_VERSION", verdict="no major improvements was allready good , a-p, i-n (kept as the best version mt1.jpg)", a="P", i="N", basis=B_USER3,
                 extra_paths=["best.png", BV + r"\mt1.jpg"]),
    "L-09": dict(cls="MIXED", verdict="a-o, i-n", a="O", i="N", basis=B_USER3),
    "L-10": dict(cls="REJECTED", verdict="worst version till now", a="", i="", basis="empty: 'worst' does not separate a and i"),
    "C-02": dict(cls="BEST_VERSION", verdict="kept by the user as the best version car.png (the head crop of this attempt was rated a P, i P)", basis=B_USER3,
                 fine="The laugh of the source is kept; face lit like the photo (dE 1.8), size 1.0, neck gap 2.1, clothes untouched (SSIM 0.997).",
                 notfine="Rejected in its run only by the AI 'not better than the source' veto, which the hard rule turned into a ranking tiebreak.",
                 extra_paths=[BV + r"\car.png"]),
    "P-01": dict(cls="BEST_VERSION", verdict="everything, perfect (the reflection included) - kept as the best version mirror.jpg",
                 extra_paths=["best.png", BV + r"\mirror.jpg"]),
    "I-01": dict(extra_paths=["best.png", BV + r"\mt2.jpg"]),
}
for r in ROWS + ROWS2:
    if r["id"] in UPDATES:
        r.update(UPDATES[r["id"]])

READ = "Assistant's read of the numbers: "
ROWS3 = [
    dict(id="B-01", group="Pinterest", rnd="R8", run="20260921_171345_replicate_pinterest_target", file="cand1.png", kind="composite", cls="BEST_VERSION",
         covers=["not_passing_closest.jpg"],
         verdict="kept by the user as a best version (cand1.png); no words given on it", a="", i="", basis="none: kept, not coded",
         fine=READ + "face lit like the photo (dE 13.8, within the limit 20 for another man's photo), head a little small (0.91), clothes untouched (SSIM 0.965), the user's face and curls (identity 0.55).",
         notfine="Rejected by the gates of its run: head size 0.91 (floor 0.94) and the AI judge's 'expression differs from the source' (hard for another man's photo). A round-8 run (code rolled back).",
         use="The user accepts a head at 0.91 of the source and an expression that differs from the reference here; the floor was not lowered because the ideal (I-01) came from re-placing a 0.923 face.",
         extra_paths=[BV + r"\cand1.png"]),
]

WORSE = "all are worse looking than ever (2026-09-23, on the five pictures of the think-again round)"
for _id, _grp, _run, _file in (("W-01", "Pinterest", "20260923_040017_replicate_pinterest_target", "not_passing_closest.jpg"),
                               ("W-02", "stained glass", "20260923_033637_replicate_google-4__IMG_5850_Original", "best.jpg"),
                               ("W-03", "kayak", "20260923_034524_replicate_google-1__IMG_5549", "best.jpg"),
                               ("W-04", "rocky", "20260923_035023_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg"),
                               ("W-05", "table tennis", "20260923_032918_replicate_google-2__IMG_3943", "not_passing_closest.jpg")):
    ROWS3.append(dict(id=_id, group=_grp, rnd="R9", run=_run, file=_file, kind="composite", cls="REJECTED", verdict=WORSE, a="N", i="",
                      basis="derived from the user's words (2026-09-23): 'worse looking' is attractiveness", fine="-",
                      notfine="Made by the think-again round's code (head-crop classification, identity-drop gate, too-bright placement rule, dimmer references for another man's photo); that code was rolled back.",
                      use="Do not repeat the think-again round's changes (patch kept in .cache/patches/best_versions_round_2026-09-23_UNCOMMITTED.patch).",
                      extra_paths=[]))
