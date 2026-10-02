"""The labelled pictures any new "eye" must be judged on (2026-09-24).

Why: Gemini's own vision, asked as a judge, passed pictures the user called "absolutely horrible", "unreal and monsterish" and "worst"
(FEEDBACK_LOG sections 9-10). The user asked for external, free eyes that see faces and pasted-in faces the way they do ("my face alone has
been lasso-ed and edited in"). An eye is useful only if it agrees with these verdicts.

label  flag = the user saw a pasted, overlapping, out-of-proportion or unnatural head; an eye must flag it
       pass = the user called it perfect / ideal / kept it as the best version; an eye must pass it
       info = mixed or unrelated verdicts; reported, not scored
picture = a file in the run folder, or an absolute path (the user's best versions in D:\\Downloads\\AI me)
Verdicts are the user's own words (FEEDBACK_LOG sections 3, 6, 7, 10 and facecard.json reviews).
"""

AIME = r"D:\Downloads\AI me"

CASES = [
    # ---- flag: pasted, overlapping, out of proportion, unnatural
    ("F01", "flag", "20260920_032241_replicate_google-2__IMG_3943", "best.jpg", "wrong face overlapping done here"),
    ("F02", "flag", "20260920_032650_replicate_google-4__IMG_5850_Original", "best.jpg", "lighting unnatural, reflection not handled"),
    ("F03", "flag", "20260920_032923_replicate_pinterest_target", "best.jpg", "face overlap looking unnatural"),
    ("F04", "flag", "20260920_033645_replicate_pinterest_target", "best.jpg", "same, unnatural"),
    ("F05", "flag", "20260920_064235_replicate_pinterest_target", "best.jpg", "head too big"),
    ("F06", "flag", "20260920_054417_replicate_pinterest_target", "best.jpg", "head bad and also looks like 2 faces are overlapping"),
    ("F07", "flag", "20260920_053307_replicate_google-1__IMG_5549", "best.jpg", "has three faces (basically 2 reflections)"),
    ("F08", "flag", "20260920_173847_replicate_pinterest_target", "cand1.png",
     "the head tilt angle is off and throws off the whole picture, the neck-above part looks copy-pasted, lighting mismatched"),
    ("F09", "flag", "20260920_173847_replicate_pinterest_target", "cand6.png", "same verdict as cand1 of this run (copy-pasted)"),
    ("F10", "flag", "20260921_004110_replicate_car2", "best.jpg", "face size and lighting not proportional to the rest of the body and scene"),
    ("F11", "flag", "20260921_020055_replicate_car2", "best.jpg", "face lighting and size bad"),
    ("F12", "flag", "20260923_183350_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg",
     "absolutely horrible: looks like my face alone has been lasso-ed and edited in"),
    ("F13", "flag", "20260923_161146_replicate_google-4__IMG_0862", "not_passing_closest.jpg", "unreal, monsterish (two heads fused)"),
    ("F14", "flag", "20260923_160011_replicate_google-2__IMG_3943", "not_passing_closest.jpg", "unreal, monsterish (head too big for the body)"),
    ("F15", "flag", "20260921_223507_replicate_pinterest_target", "not_passing_closest.jpg", "worst version till now. worst."),
    ("F16", "flag", "20260922_023359_replicate_pinterest_target", "not_passing_closest.jpg", "worst"),
    ("F17", "flag", "20260922_025509_replicate_google-2__IMG_3943", "not_passing_closest.jpg", "worst version till now"),
    # ---- pass: perfect, ideal, kept as the best version
    ("P01", "pass", "20260920_034849_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg", "perfect"),
    ("P02", "pass", "20260920_061004_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg", "perfect"),
    ("P03", "pass", "20260920_150905_replicate_google-1__IMG_5549", "best.jpg", "perfect"),
    ("P04", "pass", "20260920_153829_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg", "perfect"),
    ("P05", "pass", "20260921_000411_replicate_pinterest_target", "best.png", "perfect"),
    ("P06", "pass", "20260921_064221_replicate_pinterest_target", AIME + r"\mt2.jpg", "more than perfect, the ideal (best version mt2)"),
    ("P07", "pass", "20260921_070221_replicate_google-4__IMG_5850_Original", AIME + r"\mirror.jpg", "perfect (best version mirror)"),
    ("P08", "pass", "20260921_213349_replicate_night out", AIME + r"\nightout.jpg", "major improvement (best version nightout)"),
    ("P09", "pass", "20260922_024138_replicate_google-1__IMG_5549", AIME + r"\kayak.jpg", "slight improvement (best version kayak)"),
    ("P10", "pass", "20260922_024632_replicate_google-1__IMG_4861_SnapseedCop", AIME + r"\mt1.jpg", "was already good (best version mt1)"),
    ("P11", "pass", "20260921_171345_replicate_pinterest_target", AIME + r"\cand1.png", "best version cand1"),
    ("P12", "pass", "20260921_043841_replicate_car2", AIME + r"\car.png", "best version car"),
    ("P13", "pass", "20260923_201520_replicate_google-4__IMG_0862", "not_passing_closest.jpg", "perfect (kept as the best version)"),
    ("P14", "pass", "20260920_165702_replicate_pinterest_target", "cand3.png",
     "face size, lighting, hair everything alright (position and expression did not match the reference)"),
    # ---- info: mixed or unrelated
    ("I01", "info", "20260923_201520_replicate_google-4__IMG_0862", "cand2.png", "meh, a +2 i -2"),
    ("I02", "info", "20260923_040017_replicate_pinterest_target", "not_passing_closest.jpg", "all are worse looking than ever"),
    ("I03", "info", "20260923_033637_replicate_google-4__IMG_5850_Original", "best.jpg", "all are worse looking than ever"),
    ("I04", "info", "20260923_034524_replicate_google-1__IMG_5549", "best.jpg", "all are worse looking than ever"),
    ("I05", "info", "20260923_035023_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg", "all are worse looking than ever"),
    ("I06", "info", "20260923_032918_replicate_google-2__IMG_3943", "not_passing_closest.jpg", "all are worse looking than ever"),
    ("I07", "info", "20260920_060329_replicate_google-1__IMG_5549", "best.jpg", "perfect face emotion but lighting is off"),
    ("I08", "info", "20260920_053504_replicate_google-1__IMG_4861_SnapseedCop", "best.jpg", "bad (round-2 heuristic output)"),
    ("I09", "info", "20260921_042928_replicate_nerd", "best.png", "a N, i P: head-and-neck lighting degrades attractiveness"),
]
