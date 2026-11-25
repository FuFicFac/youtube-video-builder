# Reference docs and code

## Method and workflow docs (read from SKILL.md)

| File | Covers |
|---|---|
| `editorial-method.md` | CUT → STRUCTURE → SKIN, the editing method this skill follows |
| `hyperframes-app.md` | Desktop app as editing surface: project location, app-editable layout, word pins, review loop, export |
| `cut-and-audio.md` | Transcription, EDL, calibrated pauses, gap sweep, audio cleanup, frame-exact layers, cut-out recipes |
| `bilateral-visual-storytelling.md` | Narration-driven illustration, both sides of frame, full-screen takeovers, effect sync, QR |
| `design-playbook.md` | Research visuals, reference sweep, design rules, Read-Along Page, assets, shorts |
| `cues-bumper-ending.md` | The single splash at the handoff cue, the ending fade, QR persistence |
| `splash-reference.md` | Example splash motion/SFX timing from the reference edit |
| `open-design-styles.md` | Palette/style gallery at intake (optional, needs Open Design) |
| `fast-cut-mode.md` | Fast-cut long-form pacing layer (change-biased, bump in/out, re-hooks, illustration look-lock) + `scripts/pacing_check.py` |
| `read-along/` | Signature Read-Along Page module: matte prep, generator, example config, Vision helper |
| `render-and-verify.md` | Durable jobs, CLI version policy, render flags, watchdog, recovery, final QA |

**Skill location.** Install this folder once, in the folder your agent loads skills from, and symlink it from any
other agent's skills folder so there is a single copy to edit. Resolve the dependency skills (`hyperframes`,
`media-use` and the optional companions named in SKILL.md) from that agent's own catalog, and report anything missing
rather than claiming capability.

# Reference code (from the reference edit)

These files were built for one real screen-demo edit. Copy them into the new project's `work/` folder and adapt the paths, crops, anchors and cue lists. They are working references, not a library.

## scripts/

| File | Does |
|---|---|
| `edl.py` | Word-anchored cuts + protected silence trims → `edl.json` |
| `cut.py` | Frame-exact layer cuts (audio, intro, cam/screen crops) |
| `hybrid_intro.py`, `hybrid_masks.py`, `fg_build.py` | Vision + u2net hybrid cut-out mattes, cut to the edit |
| `build.py` | Main composition generator (intro, demo layouts, panels, tracker, splash/bumper, SFX) |
| `base_parts.py.txt` | Words-behind builder + studio panel builder |
| `base_logo.py.txt` | Lower third, splash, bumper, outro |
| `base_sfx.py.txt` | Sound effects |
| `shorts_build.py` | Vertical shorts generator |

## templates/

| File | Does |
|---|---|
| `template.html`, `short_template.html` | Page shells and CSS |
| `render.command` | Bounded render example: historical 0.8.81 settings, verify installed version, 2 workers, 150-frame segments, browser recycle |
| `transcribe.command`, `qa.command` | Chunked Parakeet runs |
| `separate.command` | Demucs voice/music split, CPU, caches external |

## Change for the PiP bubble

Creator note: the bubble must show the presenter's head and shoulders. In `build.py`, change `CIRCLE` to `inset(7% 0% 18.6% 0% round 50%)`, lower the STAGE cam scale from 0.62 to about 0.42, and recompute the bubble centre as `(280, 380)` in window coordinates.

## Agent-neutral adaptation

These files remain examples from one
specific edit, including source filenames, 23.976 fps, fixed transcription spans,
EDL decisions, cue text, crop rectangles, matte chunks and rendering flags. Read
and adapt them before execution. Do not run them directly in this installed skill
folder. Copy selected resources into the new project's `work/` and explicitly check
all outputs stay inside that project. Adapt transcription ranges to the measured
source duration; preserve the final partial chunk and merge timestamp offsets.

Set these in the adapted job file (GUI Terminal launches may not inherit variables):

- `VIDEO_PROJECT_DIR`: absolute root of the new project, with a `work/` directory.
- `VIDEO_CACHE_ROOT`: absolute cache directory on a verified volume with capacity.
- `HYPERFRAMES_CLI`: optional absolute installed HyperFrames CLI file; defaults to
  `node_modules/hyperframes/bin/hyperframes.mjs` inside the project. Verify the
  version and flags; 0.8.81 is the historical version, not a hashed npm cache path.
- `PERSON_MASK_BIN`: executable Apple Vision helper when using hybrid matting.
  This binary is not bundled; build it from `read-along/person-mask.swift`, or
  choose the footage-card fallback if unavailable.
- `MEDIA_SFX_MANIFEST`: manifest from the available `media-use` skill. Copy the
  corresponding audio assets to the project before building.

The `.py.txt` files are composition fragments injected by the example generator,
not standalone executable Python. In particular `base_sfx.py.txt` ends at the
opening of a loop; inspect how `build.py` uses the fragment before adapting it.
The standalone `.py` files parse but still require project-specific inputs and
installed dependencies. Shell templates require macOS bash/zsh, ffmpeg/ffprobe,
Node/HyperFrames, and where relevant uv/Parakeet MLX/Demucs. Syntax validation
alone does not establish successful transcription, matting or rendering.

The creative defaults in SKILL.md take precedence over historical example values,
including the head-and-shoulders PiP change above. Check the current source rather
than assuming the old OBS crop or page-reading camera orientation still applies.

## Locked-camera talking-head variant

Read [talking-head/README.md](talking-head/README.md) for the newer composition
examples: face-aware callouts, alternating presenter treatments, selective foreground
windows, captioned shorts, diagnostic denoising, bounded repairs, segment-join recovery,
final loudness correction and a scoped resource watchdog. The README explains the
selective build order and distinguishes the earlier whole-layer matte prep. These examples have the same adapt-before-running requirement.

- [bilateral-visual-storytelling.md](bilateral-visual-storytelling.md): whole-narration causal illustrations, bilateral geometry, selected full-screen passages, limited hybrid raster scenes, word/beat and perceptual effect sync, QR and actual encoded-frame QA. Executable evidence gate: `scripts/bilateral_checks.py`.
