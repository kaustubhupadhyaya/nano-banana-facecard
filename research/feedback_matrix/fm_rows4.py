"""Rows from the user's reviews recorded by tools\\record_review.py (facecard.json "reviews": scores -2..+2 against the source, defect tags, keep).
Data only; the class follows the scores: keep = best version, a > 0 and i >= 0 = improvement, both 0 = no change, a + i <= -2 = rejected,
anything else = mixed."""
import json
from pathlib import Path

from fm_measure import ROOT

ROWS4 = []
_cfg = json.loads((ROOT / "facecard.json").read_text(encoding="utf-8"))
for _n, (_key, _r) in enumerate(sorted((_cfg.get("reviews") or {}).items()), 1):
    _run, _file = _key.split("/", 1)
    _a, _i = _r.get("a"), _r.get("i")
    _sign = lambda v: "" if v is None else ("P" if v > 0 else "N" if v < 0 else "O")
    _fmt = lambda v: "-" if v is None else f"{v:+d}"
    if _r.get("keep"):
        _cls = "BEST_VERSION"
    elif (_a or 0) > 0 and (_i or 0) >= 0:
        _cls = "IMPROVEMENT"
    elif _a == 0 and _i == 0:
        _cls = "NO_CHANGE"
    elif (_a or 0) + (_i or 0) <= -2:
        _cls = "REJECTED"
    else:
        _cls = "MIXED"
    ROWS4.append(dict(
        id=f"V-{_n:03d}", group=Path(str(_r.get("source", ""))).stem[:24], rnd=None, run=_run, file=_file, kind="composite", cls=_cls,
        verdict=f"a {_fmt(_a)}, i {_fmt(_i)}" + (" | keep" if _r.get("keep") else "") + (f" | {' '.join(_r.get('tags', []))}" if _r.get("tags") else "")
        + (f" | {_r['note']}" if _r.get("note") else "") + f" ({_r.get('date')}: {_r.get('raw')})",
        a=_sign(_a), i=_sign(_i), basis="the user's scores -2..+2 against the source (review format of 2026-09-23)",
        fine="-", notfine=("what the user marked wrong: " + ", ".join(_r["tags"])) if _r.get("tags") else "-",
        use="kept as the best version" if _r.get("keep") else "-", extra_paths=[]))
