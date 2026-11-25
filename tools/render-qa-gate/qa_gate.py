#!/usr/bin/env python3
"""Render QA gate: measured pass/fail checks on a finished video render.

Run it on every render before it is shown to the creator. Exit code 0 = pass (maybe with
warnings), 1 = fail, 2 = could not run. A failing render goes back for a fix and
through the gate again; that loop is the point.

What it measures (ffmpeg detectors + local Whisper, nothing leaves the machine):
  format     resolution, audio stream present, duration
  loudness   near-silent or clipping audio
  dead air   stretches of silence in the edited voice (default -42 dB, >= 1.0 s)
  black      black video (dropped/missing clips)
  frozen     frozen video (warning only: slides and screen demos freeze legitimately)
  script     with --script: every intended word is still audible in the render
             (catches clipped intros, dropped clauses, trimmed word tails)

What it does NOT measure: caption presence/sync, framing, legibility, taste.
For those it extracts review frames (every flagged moment + an even spread) and
lists them in the report for a vision pass by the agent.

Usage:
  qa_gate.py render.mp4
  qa_gate.py short.mp4 --short --script short-script.txt
  qa_gate.py render.mp4 --script TRANSCRIPT.md --allow 170-183   # known, wanted silence
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

WATCH_SCRIPTS = Path(os.environ.get("WATCH_SKILL_SCRIPTS") or Path.home() / ".claude/skills/watch/scripts")


# ------------------------------------------------------------------ helpers
def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def ts(sec: float) -> str:
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m):02d}:{s:04.1f}"


def probe(video: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(video)])
    if r.returncode != 0:
        raise SystemExit(f"ffprobe failed: {r.stderr.strip()}")
    data = json.loads(r.stdout)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    return {
        "duration": float(data["format"].get("duration", 0)),
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "has_video": v is not None,
        "has_audio": a is not None,
    }


def detect(video: Path, info: dict, silence_db: float, min_silence: float,
           freeze_min: float) -> dict:
    """One decode pass for every detector."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video)]
    if info["has_video"]:
        cmd += ["-vf", f"scale=320:-2,blackdetect=d=0.3:pix_th=0.10,"
                       f"freezedetect=n=0.003:d={freeze_min}"]
    else:
        cmd += ["-vn"]
    if info["has_audio"]:
        cmd += ["-af", f"silencedetect=noise={silence_db}dB:d={min_silence},volumedetect"]
    else:
        cmd += ["-an"]
    cmd += ["-f", "null", "-"]
    err = run(cmd).stderr or ""

    def spans(start_re: str, end_re: str) -> list[dict]:
        starts = [max(0.0, float(x)) for x in re.findall(start_re, err)]
        ends = [float(x) for x in re.findall(end_re, err)]
        out = []
        for i, s in enumerate(starts):
            e = ends[i] if i < len(ends) else info["duration"]
            out.append({"start": round(s, 2), "end": round(e, 2), "dur": round(e - s, 2)})
        return out

    black = [{"start": round(float(a), 2), "end": round(float(b), 2),
              "dur": round(float(b) - float(a), 2)}
             for a, b in re.findall(r"black_start:([\d.]+)\s+black_end:([\d.]+)", err)]
    mean = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", err)
    peak = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", err)
    return {
        "silence": spans(r"silence_start:\s*(-?[\d.]+)", r"silence_end:\s*([\d.]+)"),
        "frozen": spans(r"freeze_start:\s*([\d.]+)", r"freeze_end:\s*([\d.]+)"),
        "black": black,
        "mean_db": float(mean.group(1)) if mean and mean.group(1) != "-inf" else None,
        "peak_db": float(peak.group(1)) if peak and peak.group(1) != "-inf" else None,
    }


def allowed(span: dict, allow: list[tuple[float, float]]) -> bool:
    return any(span["start"] >= a - 0.25 and span["end"] <= b + 0.25 for a, b in allow)


# ------------------------------------------------------------------ script match
_NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
        "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten"}
_EQUIV = {"gonna": "going to", "wanna": "want to", "gotta": "got to", "alright": "all right",
          "ok": "okay", "cuz": "because", "cause": "because", "'em": "them"}


def words(text: str) -> list[str]:
    text = re.sub(r"\*\*\[[^\]]*\]\*\*", " ", text)      # **[0:14.4]** stamps
    text = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", text)      # [music], (laughs)
    text = text.lower().replace("’", "'")
    out = []
    for w in re.findall(r"[a-z0-9']+", text):
        w = w.strip("'")
        if not w:
            continue
        w = _EQUIV.get(w, _NUM.get(w, w))
        # Expand contractions so "they're" and "they are" compare equal.
        w = re.sub(r"n't$", " not", w)
        w = re.sub(r"'re$", " are", w)
        w = re.sub(r"'m$", " am", w)
        w = re.sub(r"'ll$", " will", w)
        w = re.sub(r"'ve$", " have", w)
        w = re.sub(r"'s$", "", w)   # "that's"/"that is" and possessives: drop, ambiguous
        out.extend(w.replace("'", "").split())
    return out


def script_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8").splitlines()
    # video-short's transcript_clean.md: spoken text only on "[0.16-5.28] ..." lines.
    timed = [ln for ln in raw if re.match(r"\s*\[\d+(\.\d+)?-\d+(\.\d+)?\]", ln)]
    if timed:
        return "\n".join(timed)
    lines = []
    for line in raw:
        s = line.strip()
        if s.startswith("#") or (s.startswith("*") and s.endswith("*") and not s.startswith("**[")):
            continue  # headings and italic editor notes are not spoken
        lines.append(line)
    return "\n".join(lines)


def transcribe(video: Path, work: Path, model: str | None) -> list[dict]:
    sys.path.insert(0, str(WATCH_SCRIPTS.resolve()))
    try:
        import transcribe as wt  # the watch skill's local-whisper wrapper
    except ImportError as e:
        raise RuntimeError(f"watch skill scripts not found at {WATCH_SCRIPTS}: {e}")
    work.mkdir(parents=True, exist_ok=True)
    wav = work / "audio.wav"
    if not wav.exists():
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
                 "-vn", "-ar", "16000", "-ac", "1", str(wav)])
        if r.returncode != 0:
            raise RuntimeError(f"audio extraction failed: {r.stderr.strip()}")
    if model is None:
        # The watch skill takes the first ggml file it finds, even a dangling
        # symlink. Pick the largest model that really exists instead.
        real = [m for m in wt.cached_models()["whisper.cpp"] if Path(m).is_file()]
        if real:
            model = max(real, key=lambda m: Path(m).stat().st_size)
    print(f"[qa-gate] whisper model: {model or 'watch-skill default'}", file=sys.stderr)
    return wt.local_whisper(str(wav), model)


def script_check(script: list[str], segs: list[dict]) -> dict:
    heard, heard_t = [], []
    for seg in segs:
        for w in words(seg["text"]):
            heard.append(w)
            heard_t.append(seg["start"])
    sm = difflib.SequenceMatcher(a=script, b=heard, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    missing = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag not in ("delete", "replace"):
            continue
        n_missing, n_heard = i2 - i1, j2 - j1
        # A same-length swap is almost always ASR spelling, not a lost word.
        lost = n_missing - n_heard if tag == "replace" else n_missing
        t = heard_t[min(j1, len(heard_t) - 1)] if heard_t else 0.0
        missing.append({
            "at": round(t, 2), "script_index": i1, "lost_words": max(lost, 0),
            "span_words": n_missing,
            "expected": " ".join(script[i1:i2]),
            "heard": " ".join(heard[j1:j2]),
            "edge": "start" if i1 == 0 else ("end" if i2 == len(script) else ""),
        })
    # Coverage counts a word as lost only when nothing was heard in its place.
    # A word heard differently (ASR spelling, "ProductName" vs "Produktname") is not lost.
    lost_total = sum(d["lost_words"] for d in missing)
    n = len(script) or 1
    return {"coverage": 1.0 - lost_total / n, "exact_match": matched / n,
            "lost_words": lost_total, "script_words": len(script),
            "heard_words": len(heard), "diffs": missing}


# ------------------------------------------------------------------ review frames
def review_frames(video: Path, out: Path, times: list[tuple[float, str]]) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    frames = []
    for i, (t, why) in enumerate(sorted(times)):
        p = out / f"{i + 1:02d}_{ts(t).replace(':', 'm').replace('.', 's')}.jpg"
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}",
                 "-i", str(video), "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", str(p)])
        if r.returncode == 0 and p.exists():
            frames.append({"t": round(t, 2), "why": why, "path": str(p)})
    return frames


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="Measured QA gate for a video render.")
    ap.add_argument("video")
    ap.add_argument("--script", help="text/markdown of the words that must be audible")
    ap.add_argument("--short", action="store_true", help="expect 1080x1920 and <= 180 s")
    ap.add_argument("--expect", help="expected resolution, e.g. 1920x1080")
    ap.add_argument("--silence-db", type=float, default=-42.0)
    ap.add_argument("--min-silence", type=float, default=1.0)
    ap.add_argument("--max-dead-air", type=float, default=1.5,
                    help="silence longer than this fails; shorter only warns")
    ap.add_argument("--freeze-min", type=float, default=4.0)
    ap.add_argument("--allow", action="append", default=[], metavar="START-END",
                    help="seconds range where silence/black/freeze is intended (repeatable)")
    ap.add_argument("--min-coverage", type=float, default=0.93)
    ap.add_argument("--max-lost-run", type=int, default=4,
                    help="a run of more than this many lost script words fails")
    ap.add_argument("--spread", type=int, default=6, help="evenly spaced review frames")
    ap.add_argument("--whisper-model")
    ap.add_argument("--out-dir", help="default: '<render name> QA' beside the render")
    a = ap.parse_args()

    video = Path(a.video).expanduser().resolve()
    if not video.is_file():
        print(f"not a file: {video}", file=sys.stderr)
        return 2
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            print(f"{tool} not found", file=sys.stderr)
            return 2
    try:
        allow = [tuple(float(x) for x in r.split("-", 1)) for r in a.allow]
    except ValueError:
        print("--allow takes START-END in seconds, e.g. 170-183", file=sys.stderr)
        return 2

    out = Path(a.out_dir).expanduser() if a.out_dir else video.parent / f"{video.stem} QA"
    out.mkdir(parents=True, exist_ok=True)
    st = video.stat()
    work = out / "work" / f"{st.st_size}-{int(st.st_mtime)}"  # new render => new cache

    info = probe(video)
    det = detect(video, info, a.silence_db, a.min_silence, a.freeze_min)
    dur = info["duration"]
    fails: list[str] = []
    warns: list[str] = []
    flagged: list[tuple[float, str]] = []

    # format
    want = (1080, 1920) if a.short else (
        tuple(int(x) for x in a.expect.lower().split("x")) if a.expect else None)
    if not info["has_video"]:
        fails.append("no video stream")
    if not info["has_audio"]:
        fails.append("no audio stream")
    if want and (info["width"], info["height"]) != want:
        fails.append(f"resolution is {info['width']}x{info['height']}, expected {want[0]}x{want[1]}")
    if a.short and dur > 180:
        fails.append(f"short runs {dur:.0f} s, over the 180 s limit")

    # loudness
    if info["has_audio"]:
        if det["peak_db"] is None or det["peak_db"] < -30:
            fails.append(f"audio is effectively silent (peak {det['peak_db']} dB)")
        elif det["mean_db"] is not None and det["mean_db"] < -32:
            warns.append(f"audio is quiet (mean {det['mean_db']} dB)")
        if det["peak_db"] is not None and det["peak_db"] >= 0.0:
            warns.append("audio peaks at 0.0 dB (possible clipping)")

    # dead air
    for s in det["silence"]:
        if allowed(s, allow):
            continue
        where = f"{ts(s['start'])}–{ts(s['end'])} ({s['dur']:.1f} s)"
        if s["dur"] > a.max_dead_air:
            fails.append(f"dead air {where}")
            flagged.append((s["start"] + s["dur"] / 2, "dead air"))
        else:
            warns.append(f"pause {where}")

    # black / frozen
    for s in det["black"]:
        if allowed(s, allow):
            continue
        edge = s["start"] < 0.5 or s["end"] > dur - 0.5
        msg = f"black video {ts(s['start'])}–{ts(s['end'])} ({s['dur']:.1f} s)"
        (warns if edge and s["dur"] < 1.5 else fails).append(msg)
        flagged.append((s["start"] + s["dur"] / 2, "black video"))
    for s in det["frozen"]:
        if allowed(s, allow):
            continue
        warns.append(f"frozen video {ts(s['start'])}–{ts(s['end'])} ({s['dur']:.1f} s)")
        flagged.append((s["start"] + min(s["dur"] / 2, 2.0), "frozen video"))

    # script
    script_res = None
    if a.script:
        sp = Path(a.script).expanduser()
        if not sp.is_file():
            print(f"script not found: {sp}", file=sys.stderr)
            return 2
        try:
            segs = transcribe(video, work, a.whisper_model)
        except Exception as e:  # NoTranscript or setup problem: gate cannot vouch
            fails.append(f"script check could not run: {e}")
            segs = None
        if segs is not None:
            script_res = script_check(words(script_text(sp)), segs)
            cov = script_res["coverage"]
            if cov < a.min_coverage:
                fails.append(f"only {cov:.1%} of the script is audible "
                             f"(floor {a.min_coverage:.0%})")
            for d in script_res["diffs"]:
                lost = d["lost_words"]
                line = (f"at ~{ts(d['at'])} expected “{d['expected']}”, "
                        f"heard “{d['heard'] or '(nothing)'}”")
                if d["edge"] and lost >= 1:
                    fails.append(f"words lost at the {d['edge']} of the video: {line}")
                    flagged.append((d["at"], "lost words"))
                elif lost > a.max_lost_run:
                    fails.append(f"{lost} script words missing: {line}")
                    flagged.append((d["at"], "lost words"))
                elif lost >= 2:
                    warns.append(f"{lost} script words possibly missing: {line}")

    # review frames: flagged moments + even spread
    times = [(min(max(t, 0.0), max(dur - 0.1, 0.0)), why) for t, why in flagged[:24]]
    times += [(dur * (i + 0.5) / a.spread, "spread") for i in range(a.spread)] if dur else []
    frames = review_frames(video, out / "review-frames", times) if info["has_video"] else []

    verdict = "FAIL" if fails else "PASS"
    report = {
        "verdict": verdict, "video": str(video), "info": info,
        "loudness": {"mean_db": det["mean_db"], "peak_db": det["peak_db"]},
        "params": {"silence_db": a.silence_db, "min_silence": a.min_silence,
                   "max_dead_air": a.max_dead_air, "allow": a.allow,
                   "script": a.script, "min_coverage": a.min_coverage},
        "fails": fails, "warnings": warns,
        "silence": det["silence"], "black": det["black"], "frozen": det["frozen"],
        "script": script_res, "review_frames": frames,
    }
    (out / "qa-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [f"# QA gate: {verdict}", "", f"`{video.name}` · {info['width']}x{info['height']} · "
          f"{ts(dur)} · mean {det['mean_db']} dB / peak {det['peak_db']} dB", ""]
    md += ["## Fails (measured)"] + ([f"- {x}" for x in fails] or ["- none"]) + [""]
    md += ["## Warnings (measured)"] + ([f"- {x}" for x in warns] or ["- none"]) + [""]
    if script_res:
        md += ["## Script",
               f"- {script_res['coverage']:.1%} of {script_res['script_words']} script words "
               f"audible ({script_res['lost_words']} lost, {script_res['heard_words']} heard)",
               f"- {script_res['exact_match']:.1%} matched word for word "
               "(the rest were heard differently, usually ASR spelling)", ""]
    elif not a.script:
        md += ["## Script", "- not checked (no --script given)", ""]
    md += ["## Not measured: needs a vision pass",
           "Captions present and readable, framing, graphics alignment, on-screen spelling.",
           "Read these frames before calling the render done:", ""]
    md += [f"- `{f['path']}` (t={ts(f['t'])}, {f['why']})" for f in frames]
    text = "\n".join(md) + "\n"
    (out / "qa-report.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"report: {out / 'qa-report.md'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
