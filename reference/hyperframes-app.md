# HyperFrames desktop app: the editing surface

The HyperFrames desktop app (`/Applications/HyperFrames.app`, bundle `dev.hyperframes.desktop`) is the
**primary editing surface** for these edits. The agent builds the first cut; the creator watches, scrubs, comments and
edits in the app; the agent answers those notes in the project files; the main renders from the app's Export.

Evidence: the app bundle (`Contents/Resources/app.asar`, `main/*.mjs`), its docs at
https://hyperframes.heygen.com/studio-app/ and a first app-built edit (10:42 main, exported in 21 min on the bundled
CLI 0.8.137, no crash). Facts were true for app 0.1.0 / CLI 0.8.137–0.8.139; the app self-updates, so re-check anything surprising.

## 1. Where the project lives

- **Build in your own projects folder, never inside `~/.hyperframes-studio`.** The app's own projects live on the
  boot disk, and its media import **copies** the file in: a first project put a 1.2 GB recording inside
  `~/.hyperframes-studio/`. Create the project in its own folder (`<projects-root>/<date>-<slug>/`, on an external
  volume with free space when the boot disk is small) and keep footage there or reference it relatively.
- **Hand it to the app with `npx hyperframes open <project-dir>`.** On macOS this runs `open -b dev.hyperframes.desktop`,
  links the folder into Home in place (no copy), and writes `.hyperframes/agent-handoff.json` so the app's chat shows
  that it picked up from Claude/Codex. Do this as soon as the first preview-worthy build exists, not at the end.
- **If the creator attaches media inside the app**, it is already copied. Leave it there for that edit, but report
  the boot-disk cost (`du -sh`) and prefer referencing the original in the projects folder next time.
- The app writes and owns: `.hyperframes/` (agent-runs, comments, history, requests, transcripts), `.thumbnails/`,
  `.waveform-cache/`, `renders/`, `project.json`, `CLAUDE.md`/`AGENTS.md`, `.claude/skills/`. Don't hand-edit or
  delete them. Keep the skill's own working files in `work/`.

## 2. Lay out the composition so the app can edit it

The app shows exactly what the HTML declares. A pre-flattened MP4 is one unusable block on its timeline. Build the main
so each editorial decision is its own timeline element.

- **Root `index.html`** = full HTML document, `data-composition-id`, `data-width`/`data-height`, timed hosts only.
- **A-roll as cut clips of one prepared source.** Prepare full-length, source-aligned layers once
  (`assets/edit/aroll.mp4` picture and `assets/edit/voice.wav`/`.m4a` cleaned voice, both the same length as the
  recording; screen/cam crops likewise). Then express the EDL as clip pairs:
  `<video class="clip" muted src="assets/edit/aroll.mp4" data-start data-duration data-media-start data-track-index="0">`
  plus a matching `<audio>` on its own track with identical start/duration/media-start. Snap every value to the project's
  rational frame grid. The cuts then show up as razor cuts the creator can trim, nudge or undo. Per-clip seeks have no
  cumulative drift; the old frame-exact pre-cut layers (`cut.py`) are a fallback for footage that won't seek cleanly.
- **One sub-composition per scene/beat:** `<div class="clip" data-composition-src="compositions/<beat>.html"
  data-start data-duration data-track-index>`. Name beats by content (`opening.html`, `models-talk.html`,
  `channel-bumper.html`, `wrap-up.html`) so the layer list reads like the edit.
- **Track discipline** (from `hyperframes-studio`): one kind of element per `data-track-index`; A-roll, voice, music,
  SFX, graphics and (shorts only) captions each get their own tracks; exactly one captions host marked
  `data-track-kind="captions"` when captions exist. Keep content inside 90% action-safe / 80% title-safe areas. No guide
  or ruler elements in the HTML.
- **Word pins keep graphics married to speech.** An element with `data-words-pin="<media src> <from> <to>"` (seconds
  of that recording) is re-timed by the app when the creator cuts in the words lane, and removed when all its words are cut.
  Pin every word-anchored beat host (callouts, panels, reference cards, the bumper, QR) to its anchor words in source
  seconds, in addition to its computed `data-start`.
  **Never pin a host whose word range also plays somewhere else in the edit** (a cold open or callback that reuses
  source audio): the app re-times a pinned host to the FIRST place its words appear. In one edit a read-along
  (pinned 145–543 s) and an in-place scene jumped to 0:00 because the cold open reused 161–168 s, and the
  page covered the first half of the video in the app while the CLI snapshots (taken before the app re-timed) looked
  fine. Drop the pin for those hosts, and after `hyperframes open` re-read `index.html` to confirm no host moved.
- **Transcripts for the words lane are the app's job.** It transcribes each media file itself into
  `.hyperframes/transcripts/<sha256>.json`. Don't hand-write that store. The skill's own Parakeet/whisper words stay in
  `work/` and remain the authority for cut decisions and QA.

## 3. Rebuilding without destroying the creator's edits

The app stamps every element with `data-hf-id="hf-xxxx"`, and its comments, history and undo point at those ids. The creator also
edits the HTML through the timeline.

- **After the creator has touched a project in the app, edit the HTML in place.** Do not regenerate `index.html` or a
  composition wholesale from `work/build.py`. If a generator rerun is unavoidable, first diff its output against the
  current file, carry over every `data-hf-id` and every timing/position the creator changed, and say what was regenerated.
- Wrap each agent turn that changes files in `npx hyperframes history begin --dir <project>` … `history end --dir <project>` (or the MCP
  `history.begin`/`end`), so the creator can undo the agent's change as one step in the app. Undo with `history undo`, never by
  hand-editing back.
- The app's file watcher hot-reloads the preview on every save. No restart is needed.

## 4. Reading the creator's notes

Before acting on anything in a project that has been open in the app, catch up:

1. **MCP, when connected** (`hyperframes-desktop` server at `http://127.0.0.1:<port>/mcp`; the creator connects it from the app's
   Connect panel, and the token is theirs):
   - `comments.list` (`status: "open"`): timestamped notes, often with a drawn region.
   - `preview.frame`: a 960 px still at any time, for checking without a render.
   - `ui.navigate`: put the creator's playhead on the moment you're discussing.
   - `comments.resolve` after a fix is in and verified.
2. **Without MCP:** `npx hyperframes@latest catch-up <dir> --json` (needs CLI ≥ 0.8.138; the app bundles 0.8.137) prints what the creator asked the app's agent, what it did and which
   files changed, including their hand edits, then marks them seen. Also read `.hyperframes/comments.jsonl` and
   `.hyperframes/agent-runs.jsonl`.
3. Re-run `npx hyperframes check` after any app-side change. The app's agent may have edited the composition.

Comments are the creator talking to the editor. Treat each as a required fix, and sweep for its siblings: "MORE UNNECESSARY
SILENCE" at one timestamp means sweep the whole video (a first app build drew four silence comments before the creator said
"Sweep the entire video for gaps").

## 5. The app's own chat agent

The app runs Claude Code (`claude --print`, permission mode bypass/auto, user setting sources) or Codex as "Framey".
**Personal skills are off per project until the creator enables them in that project's skill picker**, so a request
to "use the youtube video builder" in the in-app chat does nothing while it is off. When this skill runs inside the
app's chat, it follows the same rules; outside it, assume the creator may also be giving notes to Framey and catch up
first.

The app pauses its own writes while it detects an external agent session in the project. Don't fight it. Finish your
turn, then let the creator continue in the app.

## 6. Exporting from the app

- **Export panel / MCP `render.start`** run `hyperframes render <dir> --fps --quality --workers $HYPERFRAMES_RENDER_WORKERS`
  (default `auto`) with the app's bundled CLI. The process inherits the app's environment, so `HF_SEGMENTED_CAPTURE`,
  `HF_SEGMENT_FRAMES`, `HF_SEGMENT_BROWSER_RECYCLE` and `HYPERFRAMES_DOWNLOADS` work too, but only if they are set
  **when the app launches**. A Terminal `export` doesn't reach a running app.
- The finished file stays in the project's `renders/<Project>_<stamp>.mp4` with a `.meta.json`, and is cloned to
  `~/Downloads/<Project> <stamp>.mp4`. After export, **copy the MP4 into the project's deliverables folder next to the
  source media** and verify it there (`ffprobe`, full decode, loudness, frames). The Downloads clone is a convenience,
  not the deliverable.
- **Ask the creator before starting any export.** It is a heavy job like any render.
- Long or video-heavy mains (> ~15 min, many mattes): prefer the CLI render path in [render-and-verify.md](render-and-verify.md),
  or relaunch the app with the render environment in §6a.

### 6a. Launching the app with safe render settings (optional)

Only when the creator asks for it, and only while no other export or agent run is active (quitting stops them):

```bash
osascript -e 'quit app "HyperFrames"'
open -b dev.hyperframes.desktop --env HYPERFRAMES_RENDER_WORKERS=2 --env HF_SEGMENTED_CAPTURE=true --env HF_SEGMENT_FRAMES=150 --env HF_SEGMENT_BROWSER_RECYCLE=1
```

## 7. App features that need the creator's explicit request

- **Fix words** (`voiceFix`): speaks a new line in the presenter's *cloned* voice through HeyGen. That is a synthetic voice. Never
  use it, or offer it as a fix, unless the creator asks. Flag an uncorrected misspeak instead.
- **Remove background / Cut out** on a clip (u2net/SAM) swaps the clip's file for a derived matte. That is masking:
  follow the selective-masking rule in SKILL.md, and keep the original via the app's Restore original.
- Publishing or sharing from the app (`share`, HeyGen account) is outward-facing. Ask first.
