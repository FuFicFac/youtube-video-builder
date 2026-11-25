# Talking-head examples

These are project-specific examples from two real locked-camera edits, not runnable defaults. Read [../README.md](../README.md) for configuration and dependencies. Copy selected files into the new project's `work/`, adapt fixed filenames, phrase anchors, FPS, cue text, mic geometry and caption placement, and keep generated files in that project. The creative guidance in SKILL.md takes precedence over the examples' hardcoded palette and layouts.

## Current selective-foreground composition

`build.py` and its matching `template.html` include alternating cut-out slides and rounded cards, highlighter blocks, hero numbers, face-aware foreground callouts, and a full-screen original-footage outro. `shorts_build.py` and `short_template.html` add mandatory word-by-word captions and selective short mattes.

Prepare `edl.json`, final edited `edit_words.json`, `assets/edit/aroll.mp4`, cleaned `assets/edit/voice.wav`, fonts and SFX first. The builders also read `face/track.txt`: extract source JPGs at 2 fps with sequential five-digit filenames starting at 00001, compile/run `facetrack.swift` on macOS, and save its stdout to that file. Each valid line is `filename cx cy width height`, normalized with a top-left origin. If using another tracker or sample rate, adapt both builders' timestamp conversion. Manually checked framing is a fallback when tracking is unavailable.

1. Adapt/run `build.py` to write the main page and `fg_windows.json`.
2. Adapt/run `shorts_build.py` to write the shorts and `shorts_windows.json`.
3. Adapt/run `selective_fg.py` with a verified `PERSON_MASK_BIN`, source footage and static `mic_mask.png`. It maps each edit frame back through the same EDL and writes only needed cut-out windows. Validate source frame counts and each output's count. Invalidate old `.ok` markers when the EDL, windows, source or mic polygon changes.
4. Run `shorts_build.py` again to link newly created short matte files into the short projects, then check all media references before rendering.

Set `MEDIA_SFX_MANIFEST` for the available media-use manifest. The person-mask executable, compiled face tracker, fonts, SFX, face samples and project transcripts are not bundled. Generate/adapt a mic polygon from current footage; the old geometry is only an example.

## Optional audio and repair helpers

- `denoise.py`: measured HVAC example with latency compensation, matched A/B excerpts and noise/timing report. Its 48 kHz assumption, filter frequencies and fixed speech windows are historical; adapt them to actual noise and duration before running. Confirm exact sample count and listen to speech after cleanup.
- `patch_window.py NAME T0 T1 [--keep-fg]`: video-only composition window for a bounded repair. Adapt FPS, retain needed foreground, verify alignment before splicing, and check the repaired MP4.
- `manual_mux.py SEGMENT_DIRECTORY OUTPUT`: recover a failed final join from kept segments and composition audio cues. Run from the project root, adapt FPS and paths, verify all required segments and cue semantics, and validate the recovered result.
- `finalize.py`: final per-file loudness correction with video stream-copy and a QA report, run from `work/`. Adapt the file selection to intended deliverables, preserve pre-correction files when required, and verify the encoded ceiling, expected frames/duration and real MP4 picture independently. A report alone is not delivery approval.

## Earlier whole-layer matte prep

`prep.command`, `masks.py` and `fg_build.py` retain the earlier whole-layer pipeline. Use this variant only with a composition adapted to consume its full foreground layer; the newer builders expect selective `fgw*`/`fgs*` assets. `render.command` is reusable after project setup: it uses a scoped process-group watchdog, records failures, and never calls a stopped run done. Defaults are configurable with `VIDEO_MIN_BOOT_KB`, `VIDEO_MIN_MEM_PERCENT`, `VIDEO_RENDER_WORKERS` (1) and `VIDEO_BROWSER_TIMEOUT` (240). Verify installed CLI flags. Process success still requires final MP4 QA.
