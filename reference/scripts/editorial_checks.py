#!/usr/bin/env python3
"""Local editorial evidence checks. No cut choices, downloads, or media mutation."""
import argparse, difflib, hashlib, json, math, re, sys
from fractions import Fraction
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def emit(args, report, errors):
    report['errors'] = errors
    report['pass'] = not errors
    report['limit'] = 'Evidence check; subjective listening, semantic judgment and visual usefulness require separate review.'
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'command': args.command, 'pass': report['pass'], 'errors': errors, 'report': str(target)}))
    return 0 if not errors else 1

def spans(edl):
    rate = float(Fraction(edl['fps']))
    return [(s['source_start_frame'] / rate, s['source_end_frame'] / rate) for s in edl['segments']]

def retained(edl, lo, hi):
    return sum(max(0.0, min(b, hi) - max(a, lo)) for a, b in spans(edl))

def edl_check(a):
    old, new = read(a.before), read(a.after)
    errors, windows = [], []
    rate = float(Fraction(new['fps']))
    last_source, last_timeline, total = -1, 0, 0
    bumper = new.get('bumper', {})
    bumper_frames = int(bumper.get('duration_frames', round(bumper.get('duration', 0) * rate)))
    bumper_start = int(bumper.get('start_frame', round(bumper.get('start', 0) * rate)))
    timeline_intervals = []
    if bumper_frames:
        timeline_intervals.append((bumper_start, bumper_start + bumper_frames, 'bumper'))
    for i, s in enumerate(new['segments']):
        lo, hi = s['source_start_frame'], s['source_end_frame']
        duration, start = s['duration_frames'], s['timeline_start_frame']
        if hi <= lo or duration != hi - lo:
            errors.append(f'Segment {i}: inconsistent source frames')
        if lo < last_source or start < last_timeline:
            errors.append(f'Segment {i}: overlapping/reversed source or timeline')
        if min(lo, start) < 0:
            errors.append(f'Segment {i}: negative frame')
        timeline_intervals.append((start, start + duration, f'segment {i}'))
        last_source, last_timeline = hi, start + duration
        total += duration
    cursor = 0
    for start, end, label in sorted(timeline_intervals):
        if start != cursor:
            errors.append(f'{label}: timeline gap or overlap at frame {cursor}')
        cursor = end
    if total + bumper_frames != new['frames'] or cursor != new['frames']:
        errors.append('Total source/timeline/inserted bumper frame counts disagree')
    if abs(new['duration'] - new['frames'] / rate) > 0.5 / rate:
        errors.append('Duration does not match rational frame count')
    for raw in a.pause_window:
        lo, hi, label = raw.split(':', 2)
        lo, hi = float(lo), float(hi)
        before, after = retained(old, lo, hi), retained(new, lo, hi)
        windows.append({'label': label, 'source_start': lo, 'source_end': hi, 'before_retained_seconds': before, 'after_retained_seconds': after, 'removed_seconds': before - after})
        if after >= before - 1e-6:
            errors.append(f'{label}: reviewed quiet span was not tightened')
    return emit(a, {'fps': new['fps'], 'frames': new['frames'], 'duration': new['duration'], 'segments': len(new['segments']), 'pause_windows': windows}, errors)

def word_objects(data):
    if isinstance(data, list):
        return data
    if 'words' in data:
        return data['words']
    if 'sentences' in data:
        words = []
        for sentence in data['sentences']:
            for t in sentence.get('tokens', []):
                text = t.get('text', '')
                if not re.search(r'\w', text):
                    continue  # Punctuation must not inflate a word's acoustic end.
                if not words or text.startswith(' '):
                    words.append(dict(text=text.strip(), start=t.get('start'), end=t.get('end')))
                else:
                    words[-1]['text'] += text
                    words[-1]['end'] = t.get('end')
        return words
    raise ValueError('Expected a word list, {words}, or Parakeet {sentences}')

def tokens(data, aliases):
    values = []
    for w in word_objects(data):
        text = w.get('text', w.get('word', '')) if isinstance(w, dict) else str(w)
        for token in re.findall(r"\d+(?:\.\d+)*|[^\W\d_]+(?:['’][^\W\d_]+)*", text.lower()):
            values.append(aliases.get(token.replace('’', "'"), token.replace('’', "'")))
    return values

def words_check(a):
    aliases = read(a.aliases) if a.aliases else {}
    expected, actual = tokens(read(a.expected), aliases), tokens(read(a.actual), aliases)
    errors, groups = [], []
    for op, x, y, u, v in difflib.SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
        if op != 'equal':
            groups.append({'id': str(len(groups)), 'operation': op, 'expected_range': [x, y], 'actual_range': [u, v], 'expected': expected[x:y], 'actual': actual[u:v]})
    hashes = {'expected_sha256': sha(a.expected), 'actual_sha256': sha(a.actual)}
    reviews = read(a.reviews) if a.reviews else {}
    if reviews and any(reviews.get(k) != v for k, v in hashes.items()):
        errors.append('ASR reviews do not match the current full-word input hashes')
    base = Path(a.reviews).parent if a.reviews else Path('.')
    for g in groups:
        r = reviews.get('reviews', {}).get(g['id'], {})
        evidence = [Path(x) if Path(x).is_absolute() else base / x for x in r.get('evidence', [])]
        okay = r.get('status') == 'verified_asr_variation' and bool(r.get('notes')) and bool(evidence) and all(x.is_file() for x in evidence)
        g['review'] = r if okay else None
        if not okay:
            errors.append(f'Unresolved full-audio word difference {g["id"]}')
    return emit(a, {**hashes, 'expected_tokens': len(expected), 'actual_tokens': len(actual), 'differences': groups, 'normalization_aliases': aliases}, errors)

def cues_check(a):
    rate = float(Fraction(a.fps))
    gap = a.bumper_frame / rate - a.cue_end
    fade_gap = a.fade_frame / rate - a.signoff_end
    errors = []
    if gap < -1e-6 or gap > 3 / rate + 1e-6:
        errors.append('Bumper does not follow completed cue within 0–3 frames')
    if fade_gap < -1e-6 or fade_gap > 1 / rate + 1e-6:
        errors.append('Fade is not the next frame after the completed signoff')
    if a.fade_end_frame <= a.fade_frame:
        errors.append('Fade must have positive duration')
    return emit(a, {'fps': a.fps, 'cue_end': a.cue_end, 'bumper_frame': a.bumper_frame, 'bumper_start': a.bumper_frame / rate, 'post_cue_ms': gap * 1000, 'signoff_end': a.signoff_end, 'fade_frame': a.fade_frame, 'fade_start': a.fade_frame / rate, 'post_signoff_ms': fade_gap * 1000, 'fade_duration': (a.fade_end_frame - a.fade_frame) / rate}, errors)

def shorts_check(a):
    baseline = read(a.baseline)
    files = [x for x in baseline['files'] if x.get('width') == 1080 and x.get('height') == 1920]
    errors, checks = [], []
    if len(files) != a.count:
        errors.append(f'Expected {a.count} vertical baseline files, found {len(files)}')
    for entry in files:
        path = Path(entry['file'])
        same = path.is_file() and sha(path) == entry.get('sha256')
        checks.append({'file': str(path), 'unchanged': same, 'prior_machine_checks_pass': entry.get('machine_checks_pass', False)})
        if not same or not entry.get('machine_checks_pass'):
            errors.append(f'{path.name}: changed/unverified; fresh affected-Short QA required')
    return emit(a, {'files': checks, 'reuse': 'Previous complete machine QA applies only to byte-identical files; verify shared editable dependencies separately.'}, errors)

def visuals_check(a):
    plan = read(a.plan)
    base = Path(a.plan).parent
    errors, warnings, summary, ids = [], [], [], set()
    duration = plan['duration']
    video = Path(plan.get('evidence_video', ''))
    if not video.is_absolute():
        video = base / video
    if not video.is_file():
        errors.append('Actual encoded evidence video is missing')
    show_intervals = []
    for b in plan['beats']:
        ident = str(b['id'])
        if ident in ids:
            errors.append(f'Duplicate visual beat {ident}')
        ids.add(ident)
        if not 0 <= b['start'] < b['end'] <= duration + 1e-6:
            errors.append(f'{ident}: invalid beat bounds')
        if not b.get('phrase') or not b.get('purpose'):
            errors.append(f'{ident}: missing narration/purpose')
        if b.get('kind') not in ['SHOW', 'SAY', 'BRAND']:
            errors.append(f'{ident}: kind must be SHOW/SAY/BRAND')
        if b.get('kind') in ['SHOW', 'BRAND']:
            frames = [Path(x) if Path(x).is_absolute() else base / x for x in b.get('encoded_frames', [])]
            if not b.get('headline') or not frames or not all(x.is_file() for x in frames):
                errors.append(f'{ident}: missing headline or actual encoded-frame evidence')
            if b['end'] - b['start'] < 1.6:
                warnings.append(f'{ident}: dwell under ~1.6 seconds; review readability')
            show_intervals.append((b['start'], b['end']))
        summary.append({'id': ident, 'kind': b.get('kind'), 'start': b['start'], 'end': b['end'], 'phrase': b.get('phrase'), 'purpose': b.get('purpose')})
    merged = []
    for lo, hi in sorted(show_intervals):
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(hi, merged[-1][1])
        else:
            merged.append([lo, hi])
    # Review long stretches with no explanatory or brand graphic. This is a review
    # trigger, not a mandatory graphic cadence or a rule to decorate emotional speech.
    gaps, cursor = [], 0.0
    for lo, hi in merged:
        if lo > cursor:
            gaps.append({'start': cursor, 'end': lo, 'duration': lo - cursor})
        cursor = max(cursor, hi)
    if cursor < duration:
        gaps.append({'start': cursor, 'end': duration, 'duration': duration - cursor})
    for gap in gaps:
        if gap['duration'] < a.review_hold_seconds:
            continue
        accepted = None
        for review in plan.get('hold_reviews', []):
            if review.get('start', math.inf) > gap['start'] + 1e-6 or review.get('end', -math.inf) < gap['end'] - 1e-6:
                continue
            evidence = [Path(x) if Path(x).is_absolute() else base / x for x in review.get('evidence', [])]
            if review.get('reason') and evidence and all(x.is_file() for x in evidence):
                accepted = review
                break
        gap['editorial_review'] = accepted
        if not accepted:
            errors.append(f"Unreviewed graphic-free hold {gap['start']:.3f}–{gap['end']:.3f}s ({gap['duration']:.3f}s)")
    return emit(a, {'evidence_video': str(video), 'duration': duration, 'beats': summary, 'show_seconds': sum(hi-lo for lo, hi in merged), 'dwell_warnings': warnings, 'graphic_free_intervals': gaps, 'hold_review_trigger_seconds': a.review_hold_seconds, 'counts_are_not_retention_or_semantic_quality_targets': True}, errors)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    e = sub.add_parser('edl'); e.add_argument('--before', required=True); e.add_argument('--after', required=True); e.add_argument('--pause-window', action='append', default=[])
    w = sub.add_parser('words'); w.add_argument('--expected', required=True); w.add_argument('--actual', required=True); w.add_argument('--aliases'); w.add_argument('--reviews')
    c = sub.add_parser('cues'); c.add_argument('--fps', required=True)
    for name, typ in [('cue-end', float), ('bumper-frame', int), ('signoff-end', float), ('fade-frame', int), ('fade-end-frame', int)]:
        c.add_argument('--'+name, type=typ, required=True)
    s = sub.add_parser('shorts'); s.add_argument('--baseline', required=True); s.add_argument('--count', type=int, default=4)
    v = sub.add_parser('visuals'); v.add_argument('--plan', required=True); v.add_argument('--review-hold-seconds', type=float, default=15.0, help='Review trigger for unillustrated holds; does not mandate adding graphics')
    for parser in [e,w,c,s,v]:
        parser.add_argument('--report', required=True)
    a = p.parse_args()
    return {'edl': edl_check, 'words': words_check, 'cues': cues_check, 'shorts': shorts_check, 'visuals': visuals_check}[a.command](a)

if __name__ == '__main__':
    sys.exit(main())
