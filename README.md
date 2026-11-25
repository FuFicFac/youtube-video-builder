# YouTube Video Builder

An agent skill that turns a talking-head or screen-demo recording into a finished YouTube edit, built entirely as
[HyperFrames](https://github.com/heygen-com/hyperframes) compositions (HTML rendered to video). You talk to camera, the
agent cuts and builds, you review and edit in the HyperFrames desktop app, then it exports the main video and a set of
captioned vertical shorts.

It works with any agent that loads `SKILL.md` skills (Claude Code, Codex, the HyperFrames app's own chat).

## What it does

- **Cut:** transcribes the recording, removes flubs, restarts and dead air, and places every seam from the measured
  waveform so no word is clipped. Every content cut is logged for your veto.
- **Structure:** plans what the viewer sees sentence by sentence. Numbers, names, comparisons and references get shown;
  opinion and story stay on the presenter.
- **Skin:** applies one chosen palette and type system across the whole video.
- **Build:** writes an app-editable HyperFrames project (clip pairs on the frame grid, one sub-composition per beat) and
  opens it in the desktop app for review.
- **Review loop:** reads your comments from the app, fixes each one, and sweeps the whole video for the same class of
  problem.
- **Export and verify:** renders, then checks the actual file: duration, loudness, dead air, black or frozen frames,
  and whether every intended word is still audible.
- **Shorts:** 3–4 vertical shorts with word-by-word burned captions.

Signature modules included: the **Read-Along Page** (the presenter cut out beside a paper page with word-by-word
highlighting), **words behind the presenter**, **side-swish studio panels**, a single **channel splash** on a handoff
cue, and **fast-cut mode** for Shorts-style pacing on a 16:9 main.

## Prerequisites

The reference setup is an Apple-silicon Mac running macOS 15. Most of the pipeline is portable; the parts marked
*macOS* are not.

### Required

| Tool | Used for | Notes |
|---|---|---|
| An agent that loads skills | running the workflow | Claude Code, Codex, or the HyperFrames app chat |
| [HyperFrames](https://github.com/heygen-com/hyperframes) CLI | build, check, snapshot, render | run through `npx hyperframes`; `catch-up` needs CLI 0.8.138 or newer |
| HyperFrames desktop app | reviewing, commenting on and editing the project | `npx hyperframes open <project>` |
| HyperFrames agent skills | composition rules the agent must follow | `hyperframes`, `hyperframes-core`, `hyperframes-studio`, `hyperframes-cli`, `general-video`, `media-use`, from the HyperFrames project |
| Node.js 22+ | HyperFrames | |
| ffmpeg and ffprobe | all prep: layers, crops, audio, loudness, verification | |
| Python 3.11+ | the reference scripts and the QA gate | `numpy` for some checks |
| [uv](https://docs.astral.sh/uv/) | running Parakeet and Demucs without installing them (`uvx`) | |
| Parakeet MLX | word-level transcription (`uvx --from parakeet-mlx parakeet-mlx`) | *macOS, Apple silicon.* Elsewhere, swap in any ASR that returns word timestamps |

### Required for the render QA gate (`tools/render-qa-gate/`)

| Tool | Used for |
|---|---|
| whisper.cpp with a local model | re-transcribing the finished render |
| The `watch` skill from [claude-cuts-video](https://github.com/FuFicFac/claude-cuts-video) | the local-Whisper wrapper the gate imports |

The gate looks for the `watch` skill's scripts at `~/.claude/skills/watch/scripts`. If yours live elsewhere, set
`WATCH_SKILL_SCRIPTS` to that folder. Usage and thresholds are in `tools/render-qa-gate/README.md`.

### Optional, by feature

| Tool | Needed for |
|---|---|
| Demucs 4 (`uvx … demucs`) | pulling voice away from music on a span |
| Xcode Command Line Tools (`swiftc`) | *macOS.* building the Apple Vision person-mask and face-track helpers for cut-outs |
| HyperFrames `remove-background` (u2net) | cut-out mattes; the fallback is a rounded original-footage card |
| [Open Design](https://github.com/nexu-io/open-design) app | the style gallery at intake (`scripts/build_style_gallery.py`); without it, pick a palette by hand |
| A sound-effects library and manifest | SFX; the `media-use` skill can supply one |

### Optional companion skills (not included)

`motion-prompt` (named motion moves), `cut-the-curve` (seam techniques), `master-video-workflow` and `finale-studio`
(deck-driven "how I made it" episodes), `sfx-library`. The skill mentions them where they apply and works without them.

### Machine notes

- Renders, mask passes, Demucs and full-length transcodes are heavy. Run them one at a time and keep caches on a volume
  with free space (`VIDEO_CACHE_ROOT`, `TMPDIR`, `XDG_CACHE_HOME`). The reference machine had 16 GB of memory, and two
  heavy jobs at once could crash it.
- Budget tens of GB of free disk for a long edit.

## Install

Clone this repo into the folder your agent loads skills from, keeping the folder name `youtube-video-builder`:

```bash
git clone https://github.com/FuFicFac/youtube-video-builder.git ~/.claude/skills/youtube-video-builder
```

For Codex or another agent, use that agent's skills folder instead. Then ask the agent to build a YouTube edit from a
recording; it reads `SKILL.md` first.

## Set it up for your channel

The skill ships with placeholders where a channel's identity goes. Before your first edit, tell the agent (or write
into your project's `BRIEF.md`):

- your on-screen name and channel name (replace `HOST NAME` and `CHANNEL NAME`)
- where video projects should live (`<projects-root>`)
- your handoff cue for the channel splash, if you use one, and your splash design
- your default palette and fonts
- where your real headshots live, if you want your face in thumbnails or cards

The skill never generates the presenter's likeness or voice. Faces come only from your footage or photos you supply.

## What's in the repo

| Path | What it is |
|---|---|
| `SKILL.md` | the workflow the agent follows |
| `reference/*.md` | the method in detail: cut and audio, visual storytelling, design playbook, app workflow, render and verify, fast-cut mode |
| `reference/scripts/`, `reference/templates/` | example generators, checks and job files from a screen-demo edit |
| `reference/talking-head/` | example pipeline for a locked-camera talking-head edit |
| `reference/read-along/` | the Read-Along Page module |
| `scripts/build_style_gallery.py` | builds the local style gallery from an Open Design install |
| `tools/render-qa-gate/` | measured pass/fail checks for a finished render |

**The reference code is a set of examples, not a library.** Each file came from one real edit and still carries that
edit's timings, crops and cue lists, with names and paths replaced by placeholders. Copy what you need into your
project's `work/` folder and adapt it before running. `reference/README.md` lists the environment variables the job
files expect.

## License

MIT. See [LICENSE](LICENSE). HyperFrames, Parakeet, Demucs, Whisper, Open Design and the other tools named here belong
to their own projects and carry their own licenses.
