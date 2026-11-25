# Render QA gate

`qa_gate.py` runs measured pass/fail checks on a finished video render. Run it
before a render is shown to anyone. A failing render gets fixed and goes through the
gate again.

Everything runs locally (ffmpeg, ffprobe and a local Whisper transcriber; see the
top-level README for what to install). Nothing is uploaded.

## Usage

```bash
python3 qa_gate.py render.mp4
python3 qa_gate.py short.mp4 --short --script short-script.txt
python3 qa_gate.py render.mp4 --expect 1920x1080 --script TRANSCRIPT.md --allow 170-183
```

Exit codes: `0` pass (warnings allowed), `1` fail, `2` could not run (bad path,
missing tool, missing script file).

Output goes to `<render name> QA/` beside the render (override with `--out-dir`):
`qa-report.md`, `qa-report.json`, `review-frames/`, and `work/` (audio and
transcript cache, keyed by the render's size and modified time, so a re-render
is always transcribed fresh).

## What it checks

| Check | Fails when | Warns when |
|---|---|---|
| Format | no video or audio stream; resolution differs from `--short` (1080x1920) or `--expect`; a `--short` runs over 180 s | |
| Loudness | peak below -30 dB (silent audio) | mean below -32 dB; peak at 0.0 dB |
| Dead air | silence longer than `--max-dead-air` (1.5 s) at `--silence-db` (-42 dB) | silence of 1.0 to 1.5 s |
| Black video | any black span of 0.3 s or more | a black span under 1.5 s touching the first or last half second |
| Frozen video | never | any freeze of `--freeze-min` (4 s) or more |
| Script (`--script`) | words lost at the very start or end; a run of more than `--max-lost-run` (4) lost words; audible coverage below `--min-coverage` (93%) | a run of 2 to 4 lost words |

`--allow START-END` (seconds, repeatable) marks a span where silence, black or
a freeze is intended.

The script file is plain text or markdown. Headings, italic editor notes and
`**[0:14.4]**` timestamps are ignored. A word counts as lost only when nothing
was heard in its place; a word heard differently (a product name the model
spells its own way, for example) is
reported in the word-for-word figure but does not count against coverage.

A transcript whose lines look like `[0.16-5.28] words...` also works directly as
the script: only those lines are read.

## Where it is wired in

`SKILL.md` §7 and `reference/render-and-verify.md` require it on the main and on
every short. These are instructions the agent follows, not an automatic hook.

## What it does not check

Captions (present, readable, in sync), framing, graphics alignment, on-screen
spelling and taste are not measured. The gate saves review frames instead: one
at every flagged moment plus six spread evenly. Read those frames before calling
a render done. A PASS means the measured checks passed, nothing more.

Other limits:

- A single lost word mid-video is not reported, and a run of 2 to 4 only warns.
- Script matching is as good as the local Whisper model. Lost-word times are
  approximate (start of the transcript segment).
- Dead-air detection uses a fixed threshold. Music or app noise under the gap
  hides it, and a quiet recording may need a different `--silence-db`.
- It decodes the whole file once. On a long full edit that is a heavy job; ask
  first before running it while other renders or a video editor are busy.

## Test results

On a real 48 s short and a deliberately broken
copy (first 1.5 s cut, 3 s of black and silence inserted at 18.5 s):

| File | Script | Result | Audible | Word for word |
|---|---|---|---|---|
| good | its own transcript | PASS | 100.0% | 100.0% |
| good | hand-corrected | PASS | 99.2% | 94.3% |
| broken | its own transcript | FAIL: dead air, black video, words lost at start | 96.2% | 94.7% |
| broken | hand-corrected | FAIL: same three | 95.1% | 89.4% |

The first version of the coverage figure used word-for-word matching and failed
the good file against the hand-corrected script at 90.2%. That is why coverage
now counts only lost words.
