---
name: youtube-video-builder
description: >-
  Build YouTube edits from talking-head and screen-demo footage with HyperFrames,
  using the HyperFrames desktop app as the editing surface: tight clean cuts,
  narration-driven graphics, one channel splash, read-along pages, a full-frame
  pointing outro, and captioned vertical shorts. Use for a full YouTube edit, for
  answering the creator's notes/comments on an edit open in the HyperFrames app, or
  for a channel's video-building workflow. Also the home of the signature moves:
  "do the read-along" / "reading scene" builds the masked Read-Along Page (cut-out
  switching sides, mirrored to face the text). Agent-neutral (Claude Code, Codex,
  the app's own chat). "Fast-cut mode" / "fast-cut it" turns on the fast-cut
  long-form pacing layer (reference/fast-cut-mode.md).
---

# YouTube Video Builder

The presenter talks to camera; the agent builds the video; the creator reviews and edits it in the **HyperFrames
desktop app**; the main exports from the app. ("The presenter" is the person on camera and "the creator" is the person
giving notes. They are usually the same person.)

**Read before working:** [reference/editorial-method.md](reference/editorial-method.md) (the editing method) and
[reference/hyperframes-app.md](reference/hyperframes-app.md) (how projects live in the app). Load the `hyperframes`
skill (it routes to `hyperframes-core`, `hyperframes-studio`, `general-video`) and `media-use` for SFX. Reference code in
`reference/` is a set of adapt-before-running examples from real edits ([reference/README.md](reference/README.md)),
not a library.

## 0. Non-negotiables

1. **HyperFrames only.** The picture is always a HyperFrames composition; ffmpeg is prep only (layers, mattes, audio).
   No Remotion, no hand-built Resolve XML for these edits.
2. **The file the creator attaches is the source.** Never substitute another recording by transcript-matching. If their
   wording implies another file, ask in one line.
3. **Never copy the presenter's name from a transcript.** ASR misspells names. Take the name, the channel name and
   their spellings from `BRIEF.md`, and correct them in every caption, lower third and transcript.
4. **Never generate the presenter's likeness or voice.** Their face only comes from their footage or from headshots
   they supply; never alter real people's pixels (composite only). The app's **Fix words** voice clone is a synthetic
   voice: don't use or offer it unless the creator asks.
5. **Ask before heavy jobs** (renders, exports, mask passes, transcodes, Demucs). The creator may have other jobs
   running, and two at once can crash a memory-limited machine (the reference setup was a 16 GB Apple-silicon Mac). Run
   heavy work one at a time with caches on an external volume with free space (`VIDEO_CACHE_ROOT`, `TMPDIR`,
   `XDG_CACHE_HOME`, HF/torch/npm caches; check `df -h` and `memory_pressure` first).
6. **Notes are fixes; musing is not a command.** Act on comments and direct requests. Thinking out loud
   ("maybe we could…") gets discussed, not executed.
7. **Every spoken reference gets shown** ("here's a picture of…", named people/products). Run the reference sweep in
   [design-playbook.md](reference/design-playbook.md) §5c before designing.
8. **Say "rendering" until the MP4 is verified.** When the creator reports something from their machine, their
   evidence beats your theory.

## 1. Intake (one short exchange)

- Establish: project folder `<projects-root>/<YYYY-MM-DD>-<slug>/` (**never** build inside
  `~/.hyperframes-studio`), source path, measured FPS (`ffprobe`; don't assume 23.976), music under voice?, CLI version,
  and the presenter's name and channel name exactly as they should appear on screen.
- **Ask palette/style** and, when Open Design is installed, show its gallery
  ([open-design-styles.md](reference/open-design-styles.md)), unless the creator already chose a style for this video.
  Shorts default yes (3–4 × 30–60 s), built **after** the main is approved. No storyboard unless the creator asks for
  one.
- `npx hyperframes init`, then write `BRIEF.md`: source, FPS, style, CLI version, presenter and channel names, shorts
  plan, splash cue choice.

## 2. CUT: what stays, and where seams land

Detail: [cut-and-audio.md](reference/cut-and-audio.md). Transcript picks *what* to cut; the measured waveform picks
*where*.

- Transcribe in sequential chunks (Parakeet MLX, `transcribe.command`); check every >1.5 s ASR gap against the audio and
  re-transcribe non-silent gaps.
- Cut by meaning: flubs, false starts, restarts, retakes, "I know I stumbled" asides, editor instructions, dead air.
  Cut at complete thoughts. Keep jokes and intentional rhythm. Log every content cut in `CUT-NOTES.md` for veto.
- **Measure this recording's gate** (no copied −45 dB; a copied gate once clipped a quiet word). Then **sweep the whole
  video for gaps** before the creator sees anything: the default taste is tight. Every edited-voice gap over ~0.6 s is
  tightened or justified in `CUT-NOTES.md`, and no seam clips a word tail (creator note: "You cut off the word
  folder").
- Audio: diagnose noise before denoising (up to ~80% perceptual reduction, voice natural); two-pass loudnorm −16 LUFS /
  −1.5 dBTP; compensate denoiser latency. Voice over music → Demucs on that span only.
- Prepare **full-length, source-aligned** layers (`assets/edit/aroll.mp4`, `assets/edit/voice.wav`, crops) and an
  `edl.json` snapped to the rational frame grid. Re-transcribe the edited voice and diff it against the intended words.

## 3. STRUCTURE: what the viewer sees, moment by moment

Detail: [bilateral-visual-storytelling.md](reference/bilateral-visual-storytelling.md),
[design-playbook.md](reference/design-playbook.md).

- Read the edited transcript sentence by sentence: **SHOW** numbers, names, comparisons, processes and references;
  **SAY** opinion, story and emotion on the presenter. Plan object → spoken action → consequence; use both sides of the
  frame; occasional full-screen illustrative takeovers while the voice continues. Any graphic-free stretch over ~15 s
  needs a specific reason. Write the plan as `VISUAL-BEATS.json` / `STORYTELLING-AUDIT.json`.
- Research claims with bounded subagents; real licensed assets logged in `SOURCES.md` / `REFERENCES.md`; charts rebuilt
  from verified data. Generated stills/clips are allowed for concepts (`IMAGE-PROMPTS.md`), never for the presenter.
- **Presenter treatments:** a balanced mix of full frame, big rounded head-and-shoulders cards (vertical when beside
  material), source stages with a head-and-shoulders PiP, foreground callouts, and swishes/repositioning.
  **Masking is selective, never dominant:** cut-outs and words-behind-the-presenter for big emphasis beats only; a
  chunky matte gets swapped for a rounded original-footage card. **Exception: the Read-Along Page is a cut-out by
  default** (§3a).
- **Cards never cover the presenter's face**: big, vertical-rectangle side cards clear of the union face box for the
  whole window.
- **Fixed beats:** lower third "HOST NAME · HOST · CHANNEL NAME" at the open; **one** channel splash at the
  deliberate handoff cue (for example "…let's talk about it on <channel name>"), first frame 0–3 frames after the
  measured release; CTA pills ("LINK IN THE DESCRIPTION") on link mentions; Read-Along Page whenever the presenter
  reads text (§3a); full-frame original-shot outro for the pointing gesture at the end-screen recommendations;
  next-video title box low; QR held from its mention to the end; fade tight to the last word while holding the last
  shot. Cue rules: [cues-bumper-ending.md](reference/cues-bumper-ending.md).
- **No burned captions on the 16:9 main** unless the creator asks. Captions belong to the shorts.

## 3a. Signature moves: call them by name

The favorite treatments are reusable modules, so they survive between videos. When the creator names one, or the
footage calls for it, use the module, not a from-scratch approximation.

- **Read-Along Page**: "do the read-along", "reading scene", "switch me side to side while I read", or any time the
  presenter reads text on screen. Paper page, word-by-word green highlight, the presenter **masked out** in a bottom
  corner, alternating sides each page and mirrored to face the text, dropping out and popping back on every flip.
  Module: [reference/read-along/](reference/read-along/README.md): `prep_cam_read.command` makes the matte,
  `read_along.py` writes the app-editable sub-composition.
- **Words behind the presenter**: the phrase split left/right around their head on a scrim, their cut-out in front.
  For major emphasis ([design-playbook.md](reference/design-playbook.md) §6).
- **Side-swish studio panels**: the presenter slides to one side as a cut-out or rounded card, and big bold
  steps/chips/✓✕ rows fill the other side on their words ([design-playbook.md](reference/design-playbook.md) §6,
  `talking-head/build.py`).
- **The splash**: one channel splash on the handoff cue ([cues-bumper-ending.md](reference/cues-bumper-ending.md)).
- **Master Video Workflow** (optional companion skill, not included): when the footage is a riff recorded against a
  Finale Studio deck ("how I made it" episodes), load `master-video-workflow` first if it is installed. Its deck
  becomes this skill's STRUCTURE, its tangents get visuals from its source menu, and everything else (cut, skin, build,
  review, export, shorts) runs here as normal.
- **Fast-cut mode**: "fast-cut mode", "fast-cut it", "keep it moving", or Shorts-style energy on a 16:9 main. Pacing
  follows the subject with a bias toward change: 3–6 s is the normal rhythm, longer holds need a written reason,
  bump-in/bump-out punch-ins, re-hooks, one locked illustration look. Read
  [reference/fast-cut-mode.md](reference/fast-cut-mode.md) before planning; check with
  `reference/scripts/pacing_check.py`. Everything else in this skill still applies.
- **Motion Prompt moves** (optional companion skill, not included): when the creator names a move by number or name
  ("mask reveal on the title", "#005", "whip pan into the demo") or says "open the library", load the `motion-prompt`
  skill if it is installed: `pick --local` for the gallery, `get`/`kit` for the spec. Port with its
  `references/hyperframes.md` (GSAP easing map). Its timings drive the move; this skill's look (type, palette,
  cut-outs) and `cut-the-curve` seams still win. List the #IDs used in §8's report. Not a license to sprinkle moves:
  one named move per beat, only where the narration calls for it.

## 4. SKIN: apply the chosen style

The style sets type, palette and geometry. It never thins the storytelling or slows the cadence ("Brutalist" is a
look, not permission to go sparse). Big, bold, phone-readable type, especially in side panels. Adapt the splash colors
to the chosen palette while keeping its motion and SFX timing ([splash-reference.md](reference/splash-reference.md)).
Example defaults when nothing else is chosen: navy `#0a1424`, green `#39d98a`, blue `#3b7bff`, paper `#f2ecdf`;
League Gothic / Space Mono / Newsreader.

## 5. BUILD for the app, then hand it over

Detail: [hyperframes-app.md](reference/hyperframes-app.md) §2–3.

- **App-editable layout:** the EDL becomes clip pairs, `<video muted class="clip">` on `aroll.mp4` plus matching
  `<audio>` on `voice.wav`, each with `data-start`/`data-duration`/`data-media-start` on the frame grid; one
  sub-composition per beat (`compositions/<beat>.html`); one element kind per track; word-anchored hosts carry
  `data-words-pin="<src> <from> <to>"` so they follow the creator's cuts in the words lane.
- Build with an adapted generator in `work/` (examples: `reference/talking-head/build.py`) **once**. After the creator
  has touched the project in the app, edit files in place, keeping every `data-hf-id`, and wrap your turn in
  `hyperframes history begin` / `end` so they can undo it as one step.
- `npx hyperframes check` must pass; look at snapshot contact sheets; render a bounded **preview of the splash
  transition and the ending** and verify the timing on real encoded frames and audio.
- `npx hyperframes open <project>` and tell the creator what to look at. They scrub, comment and edit in the app.

## 6. REVIEW LOOP: answer the creator's notes

- Catch up first, every turn: MCP `comments.list` (open) when the app's MCP is connected, else
  `npx hyperframes@latest catch-up <dir> --json` plus `.hyperframes/comments.jsonl`.
- Fix each note **and sweep the whole video for the same class of problem** (one silence comment means sweep all
  gaps; one card over the face means check every card). Verify with `preview.frame` or snapshots, resolve the
  comment, re-run `check`.
- If the creator reverses an instruction ("disregard the last instruction… change everything back"), use
  `history undo` / `restore` for that turn, then apply what they kept.

## 7. EXPORT and verify

Detail: [render-and-verify.md](reference/render-and-verify.md), [hyperframes-app.md](reference/hyperframes-app.md) §6.

- **Gate before export:** `REFERENCES.md` complete; splash and ending cue records pass; gap sweep clean; `check` passes;
  editorial checks (`reference/scripts/editorial_checks.py`, `bilateral_checks.py`) run on the real EDL and beats.
- **With the creator's go**, export the main from the app (or the CLI render path for long/matte-heavy mains). Copy the
  MP4 from `renders/` into the project's deliverables folder next to the source; the `~/Downloads` clone is not the
  deliverable.
- **Verify the actual file:** ffprobe duration/frames vs plan, `media_clock.py` cadence, full decode with 0 errors,
  encoded loudness −16 LUFS / ≤−1.5 dBTP (each file separately), frames sampled around every beat, the splash
  boundary and the fade; re-transcribe the final audio and diff it.
- **QA gate, required on every rendered MP4 (main and each short) before the creator sees it:**
  `python3 <skill-root>/tools/render-qa-gate/qa_gate.py <render.mp4> --script <intended words>`
  (`--expect 1920x1080` for the main, `--short` for shorts; `--allow START-END` for a deliberate silence such as the
  splash). The script is the intended words from the cut plan, never a transcript made from the render itself. Exit 1 =
  fix and run it again; do not hand over a failing file. Then read every frame in its `review-frames/`: captions,
  framing and graphics alignment are not measured. The main is a full decode plus Whisper, so it is a heavy job and
  runs under the creator's go. Limits and thresholds: the tool's `README.md`.
- **Then shorts** (3–4, 1080×1920, word-by-word burned captions mandatory, hook/reason/payoff, own loudness check);
  design detail in [design-playbook.md](reference/design-playbook.md) §7.
- Deliver `TRANSCRIPT.md` (corrected names, final timestamps incl. the splash) and the renders folder path.

## 8. Report in

Hand the creator the actual saved paths and state exactly what was verified and what wasn't (listening limits
included). If they keep project notes somewhere, write a short note there only when asked (verified outputs,
remaining work, pipeline observations).

## Next evolution

Teleprompter-backed talk-to-camera takes with the prompter script as transcript ground truth: keep the full frame
as the room plate; cards and PiP for panels; selective masking as above.
