#!/usr/bin/env python3
"""Fast-cut mode pacing check (reference/fast-cut-mode.md). Reads PACING.json; no media access.

Flags: gaps between picture changes over --hold-seconds without a covering hold reason, a first change later than
--first-change-seconds, and stretches longer than --rehook-seconds with no re-hook. Review triggers, not quotas."""
import argparse, json, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan')
    p.add_argument('--hold-seconds', type=float, default=6.0)
    p.add_argument('--first-change-seconds', type=float, default=2.0)
    p.add_argument('--rehook-seconds', type=float, default=120.0)
    p.add_argument('--report', required=True)
    a = p.parse_args()
    plan = json.loads(Path(a.plan).read_text())
    duration = float(plan['duration'])
    errors, warnings = [], []

    times = []
    for c in plan.get('changes', []):
        t = float(c['t'])
        if not 0 <= t <= duration:
            errors.append(f"change at {t:.2f}s is outside 0–{duration:.2f}s")
        if not c.get('kind') or not c.get('what'):
            errors.append(f"change at {t:.2f}s needs kind and what")
        times.append(t)
    times.sort()
    holds = plan.get('holds', [])
    for h in holds:
        if not str(h.get('reason', '')).strip():
            errors.append(f"hold {h.get('start')}–{h.get('end')}s has no reason")

    if not times or times[0] > a.first_change_seconds:
        first = times[0] if times else duration
        errors.append(f"first change at {first:.2f}s; hook wants one within {a.first_change_seconds:.1f}s")

    gaps, edges = [], [0.0] + times + [duration]
    for lo, hi in zip(edges, edges[1:]):
        if hi - lo <= a.hold_seconds:
            continue
        cover = next((h for h in holds if str(h.get('reason', '')).strip()
                      and float(h['start']) <= lo + 0.05 and float(h['end']) >= hi - 0.05), None)
        gaps.append({'start': lo, 'end': hi, 'duration': round(hi - lo, 3), 'hold_reason': cover and cover['reason']})
        if not cover:
            errors.append(f"unexplained hold {lo:.2f}–{hi:.2f}s ({hi - lo:.1f}s)")

    hooks = sorted(float(t) for t in plan.get('rehooks', []))
    for lo, hi in zip([0.0] + hooks, hooks + [duration]):
        if hi - lo > a.rehook_seconds:
            warnings.append(f"no re-hook for {hi - lo:.0f}s ({lo:.1f}–{hi:.1f}s); check the subject doesn't call for one")

    intervals = [hi - lo for lo, hi in zip(edges, edges[1:])]
    report = {'duration': duration, 'changes': len(times),
              'median_seconds_between_changes': sorted(intervals)[len(intervals) // 2] if intervals else None,
              'long_holds': gaps, 'rehooks': hooks, 'warnings': warnings, 'errors': errors, 'pass': not errors,
              'limit': 'Counts are review triggers; whether each change is useful needs eyes on encoded frames.'}
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'pass': report['pass'], 'errors': errors, 'warnings': warnings, 'report': a.report}))
    return 0 if not errors else 1

if __name__ == '__main__':
    sys.exit(main())
