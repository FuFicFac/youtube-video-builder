# Fast-cut mode: fast-cut long-form

Trigger: the creator says "fast-cut mode", "fast-cut it", "keep it moving", or asks for Shorts-style energy on a 16:9 main.
It is a pacing layer on top of this skill, not a separate pipeline: intake, cut, skin, app build, review, export and
shorts all run as in `SKILL.md`. What changes is how often the picture changes and how the edit holds attention.

Origin: the editorial principles of vertical-Shorts editing (hook fast, change the picture often, keep the speaker
present), rewritten from first principles for horizontal long-form. Shorts-only build pipelines are **not** used:
they render a throwaway project with a pre-mixed track, which the HyperFrames app cannot edit. Everything here
builds the app-native project described in [hyperframes-app.md](hyperframes-app.md).

## 1. The pacing rule

**Pacing follows the subject, and the default is change.** When the subject calls for a change (a new idea, a name,
a number, a reaction, a punchline, a shift in tone), the picture changes. 3–6 s between changes is the normal rhythm,
not a cap and not a quota. A demo, an emotional beat or a line that needs to land may hold longer, but only for that
reason, written next to the scene in the plan. A static stretch with no reason fails review. Never add filler to
raise the count: every change shows or emphasizes something the subject just did.

In this mode the general rules "no motion quota" ([bilateral-visual-storytelling.md](bilateral-visual-storytelling.md))
and the 15 s hold trigger ([editorial-method.md](editorial-method.md)) are tightened, not removed: the review trigger
is 6 s, and the burden of proof sits on the hold, not on the change.

## 2. What counts as a change (16:9 vocabulary)

- **Bump in / bump out.** A punch-in or pull-back on the presenter timed to an emphasis word. Cap the scale by source resolution
  (1080p source ≤ ~1.2×, 4K source up to ~2×); never tighter than head and shoulders. Author bumps as
  keyframes on the A-roll host (`hyperframes-keyframes`), not as extra clips, so a 15-minute timeline doesn't fill
  with hundreds of elements. A cut back to full frame is a bump out.
- **Layout switch.** Full frame → side-swish panel → stage with head-and-shoulders PiP → full takeover, per
  [design-playbook.md](design-playbook.md) §6. Switch on a spoken turn, not mid-phrase.
- **Card in/out, row added, number counting up.** A list adds a row per spoken item on its word; a stated figure
  counts up on the word. One idea per card.
- **Screen zoom.** On any page, zoom into the one field or line the presenter is talking about, on the word.
- **B-roll** for what the words name. Each clip once; hold its last frame rather than loop; end a graphic on the next
  clip's first frame so the cut disappears.
- **Read-Along beats.** Highlight progression alone is not a change; a page flip, a side switch, a pull-quote
  takeover or a cut to the presenter's reaction is.
- **Illustrated takeover** (§6) for the one or two moments that deserve an illustrated world.

## 3. Structure for retention

- **Hook, first ~30 s at Shorts speed.** Open on the strongest line or visual (a verdict, a surprising result), not on
  setup. First change within ~1–2 s, on the first strong word. Plant one question the video answers later. The
  channel lower third and splash still follow [cues-bumper-ending.md](cues-bumper-ending.md); a cold-open tease
  before them is allowed when it's the presenter's real line.
- **Re-hooks.** Every ~60–120 s, depending on the subject, give the viewer a reason to stay: tease what's next,
  open a loop ("we'll see if it holds up on price"), or pay one off. Mark them `rehook` in the plan. Chapters line up
  with them.
- **Close full circle.** Bring the hook's question or visual back at the verdict.

## 4. Footage-specific rules

- **Screen-demo spans** (OBS face strip + screen share): never leave the raw composite on screen. Recapture each page
  clean at 1920 wide (or crop the share when it's readable), lift the presenter into a head-and-shoulders PiP from the strip, and
  zoom to what they name. Map screen spans by keyframe luma before cutting.
- **Reading spans:** Read-Along Page ([read-along/README.md](read-along/README.md)). Text ground truth comes from the creator's
  file or the document, never ASR or OCR; word timing comes from the transcript. Cut retakes, keep the last clean
  read of each line, and still change the picture on the story's turns.
- **Spoken numbers:** show them only after checking the audio; never invent or round a figure the presenter didn't say.

## 5. B-roll order

The creator's own footage first (including the screen parts of the recording), then official demos and launch media,
then license-checked Wikimedia Commons (never use a file whose license needs a decision without the creator's OK),
then generated stills for concepts only (`IMAGE-PROMPTS.md`, never the presenter's likeness). Logos only from official files. Log everything in
`SOURCES.md`.

## 6. Illustration style library: one look, drawn on deliberately

If you keep a library of illustration styles (canvas-scene looks, a style atlas), it is a resource, not a grab bag.
None is bundled with this skill.

- **Look-lock at intake.** Pick one primary style and at most one accent for the video, with a one-line reason tied
  to the subject; show the creator 2–3 candidates with preview links and wait for their pick. Record it in `BRIEF.md`.
- **Carry the look through.** Pull the chosen style's palette and type into the cards and panels, so DOM graphics and
  canvas scenes read as one system (the channel skin still wins on the splash and lower third).
- **Takeovers only, a handful per video.** Canvas is for illustrated worlds DOM can't draw; the presenter, type and cards stay
  in DOM. Guide every scene with real reference pictures of the subject: a style paints, it doesn't make pictures.
- Seek-safe only (seeded randomness, no rAF loops, full repaint per frame). Check the terms of use of any
  third-party style library before anything publishes.

## 7. Cutting in this mode

Fast pacing comes from the picture, not from shaving the presenter's speech. Fixed 0.1 s word handles borrowed from
Shorts editing clipped words in practice: use the measured gate and handles from [cut-and-audio.md](cut-and-audio.md), end kept ranges on
real audio (ASR inflates the last word before a pause), and cut dead air, retakes and tangents. Log content cuts in
`CUT-NOTES.md`.

**Waveform-check every cut edge (hard rule).** Never trust transcript word times alone for an edge:
ASR clips trailing consonants and misses soft starts ("But", "And"). Every kept range must start and end in measured
silence: look at the energy in the 60 ms before each start and the 80 ms after each end, and if the voice is still up,
move the edge out to where it decays (short of any dropped neighbour word). For app-native timelines apply that test to each
A-roll clip's in/out on the source audio. Re-check after every recut. A clipped word is a failed edit even if the
captions read right.

**Voice sits on top of the music.** The voice stays clearly in front: start music beds around 26 dB under the voice
for talk-driven pieces, not 18, and only raise the bed for a beat where the music is the point.

## 8. Plan, check, review

- **Plan in chat before building:** one line per scene (time, layout, what's on screen, words spoken, `hold:` reason
  if > 6 s), the re-hooks, the B-roll sources with links and license tier, the illustration look, anything to generate. Wait
  for the creator's go. Save the same plan as `PACING.json`:
  `{"duration": s, "changes": [{"t": s, "kind": "...", "what": "..."}], "holds": [{"start": s, "end": s, "reason": "..."}], "rehooks": [s, ...]}`
  in edited-timeline seconds.
- **Check:** `python3 reference/scripts/pacing_check.py PACING.json --report work/pacing-report.json`. It flags
  unexplained gaps over 6 s, a late first change, and stretches with no re-hook. Re-run after every build pass.
- **Review in the app only** (comments), per `SKILL.md` §6.
- **No burned captions on the main**; keyword callouts only. Shorts stay captioned.
