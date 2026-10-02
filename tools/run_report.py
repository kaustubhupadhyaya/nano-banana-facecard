"""The report of a run: every attempt with its numbers and why it failed, the references it was sent, and the picture it produced (full path).

    .venv\\Scripts\\python.exe tools\\run_report.py                      # the runs of this session (since tools\\session_prune.py --apply)
    .venv\\Scripts\\python.exe tools\\run_report.py <run folder> [...]   # given runs (name or path)
    .venv\\Scripts\\python.exe tools\\run_report.py --last 3             # the three newest runs
Columns: identity (source identity), similarity to the source face, head size / source, moved, light dE, neck gap, sharpness x source, SSIM of the
clothes and background, the AI judge's flags, placement of which attempt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fc_common import OUTPUTS, SESSION_MARK, attempt_table, picture_of, run_dirs  # noqa: E402


def fmt(v, spec="") -> str:
    return "-" if v is None else format(v, spec)


def report(d: Path) -> None:
    j = json.loads((d / "run.json").read_text(encoding="utf-8")) if (d / "run.json").exists() else {}
    pic = picture_of(d)
    print(f"\n=== {d.name}")
    print(f"source {j.get('scene')} | {j.get('source_kind')} photo, expression {j.get('expression_policy')}, status {j.get('status')}"
          + (" | far face" if j.get("far_face") else ""))
    refs = j.get("identity_refs_pose") or [{"name": n} for n in (j.get("identity_refs") or [])]
    print("references: " + ", ".join(f"{r['name']}" + (f" ({r['kind']}, turn {r['pose'][0]:+.0f} chin {r['pose'][1]:+.0f})" if r.get("pose") else "") for r in refs))
    if j.get("source_pose"):
        sp = j["source_pose"]
        print(f"source pose (AI): turn {sp.get('turn')} chin {sp.get('chin')} camera {sp.get('camera')}")
    print(f"{'att':>3} {'verdict':10} {'identity':>15} {'gt':>6} {'size':>6} {'moved':>6} {'dE':>5} {'neck':>6} {'sharp':>6} {'ssim':>6}  judge / placement / problems")
    for r in attempt_table(d):
        idt = f"{fmt(r['identity'])} ({fmt(r['source_identity'])})"
        print(f"{r['attempt']:>3} {str(r['verdict']):10} {idt:>15} {fmt(r['gt_sim']):>6} {fmt(r['size']):>6} {fmt(r['shift']):>6} {fmt(r['light_dE']):>5} "
              f"{fmt(r['neck']):>6} {fmt(r['sharp']):>6} {fmt(r['ssim']):>6}  {r['judge']}"
              + (f" / placement of {r['placement_of']}" if r["placement_of"] else "")
              + (" / " + "; ".join(p.split(" (")[0] for p in r["problems"]) if r["problems"] else ""))
    best = (j.get("best") or {}).get("candidate")
    closest = (j.get("not_passing_closest") or {}).get("candidate")
    print(f"result: {'best = attempt ' + str(best) if best else ('nothing passed; closest = attempt ' + str(closest) if closest else 'no picture')}"
          + (f" -> {pic}" if pic else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--last", type=int)
    args = ap.parse_args()
    if args.runs:
        dirs = [Path(r) if Path(r).is_dir() else OUTPUTS / r for r in args.runs]
    elif args.last:
        dirs = run_dirs(OUTPUTS)[-args.last:]
    else:
        since = json.loads(SESSION_MARK.read_text(encoding="utf-8")).get("session_start", "") if SESSION_MARK.exists() else ""
        dirs = [d for d in run_dirs(OUTPUTS) if d.name[:15] >= since]
    for d in dirs:
        if (d / "run.json").exists():
            report(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
