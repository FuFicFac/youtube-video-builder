# Read-Along Page: the signature reading scene

**Call it with:** "do the read-along", "read-along page", "reading scene", "do the thing where I'm reading",
"switch me side to side while I read", or automatically whenever the presenter reads prose, a chapter, a script, a doc
or a post on screen.

Creator note, after the first edit that used it: *"I love the way you dealt with me reading… you would switch me
back and forth as if I was still looking at the text, but you kept it very dynamic."* Never drop this or water it
down.

## What the viewer sees

1. The screen share (or the camera) gives way to a **warm paper page** opening with a circular reveal and a whoosh;
   header chips name the work and chapter.
2. The passage, **typed verbatim from the recording's frames** (ground truth; presenters misread words), is split into 3–4
   pages by paragraph. Pages with fewer words get bigger type.
3. **Word-by-word highlight**: unread words are dimmed ink; each lights to full ink with a green marker on its spoken
   time, and the marker moves on with the next word. Read text stays dark, so the viewer sees progress.
4. **The presenter as a cut-out in a bottom corner, alternating sides every page.** On the right they are
   **mirrored** so they face left toward the text; on the left they are unmirrored. The text column (and header) moves
   to the opposite side. On each page change the cut-out **drops out, flips while hidden, and pops back up**
   (`back.out`). Never flip while it is visible.
5. A quick whoosh back to the room when the reading ends.

**This scene is a cut-out by default.** It's the standing exception to "masking is selective": the effect depends on
the presenter standing in the page. Use a rounded original-footage card only when the matte genuinely can't be made clean.

## Build it (four steps)

1. **Find the span and the text.** Locate the reading in the edited transcript (start a beat before the first word,
   end after the last). Pull full-res frames of the text being read and type every paragraph exactly.
2. **Make the cut-out matte** (heavy job: ask the creator first, run alone): adapt and launch
   [prep_cam_read.command](prep_cam_read.command) via `open -a Terminal`.
   - Crop a **vertical head-and-shoulders strip** measured from this footage (OBS cam strip, or a ~608×1080 strip
     around the face for full-frame takes). Leave room for leaning.
   - `hyperframes remove-background` (u2net) mattes it; the optional choke tightens soft edges.
   - **Locked camera?** Draw one garbage-matte PNG from a strip frame (PIL polygon, 1.5 px blur) to hold out the
     wall patch beside the mic that both u2net and Vision keep. Look at a composited frame before running the full
     pass.
   - Cleaner edges/mic: the Apple Vision hybrid ([person-mask.swift](person-mask.swift), build with
     `swiftc -O person-mask.swift -o person-mask`, set `PERSON_MASK_FPS` to the source rate) plus a static mic
     polygon. See `../talking-head/masks.py` and `selective_fg.py`.
   - Matte the **source window**, not the cut edit; the generator maps the EDL's cuts onto it.
3. **Generate the scene:** copy [example_config.json](example_config.json), fill it in, and run
   `python3 read_along.py config.json`. It writes `compositions/<id>.html` (an app-editable sub-composition) and
   prints the host `<div>` for `index.html`, including `data-words-pin` so the app re-times it when the creator cuts words.
   Several readings in one video get one config and `id` each. Use the video's chosen palette (`palette` block) and
   its font faces; the paper/ink/green defaults are the original look.
   It reports page-word matching: under 80% matched means a wrong span, words file or typed text. Fix it, don't ship.
4. **Check it:** `hyperframes check` (must pass; the unread-ink default of 52% is chosen to pass contrast), then
   `hyperframes snapshot --at <page1+6>,<flip-0.3>,<page2+5>,…` and look: the presenter faces the text on both sides, the header
   is never under them, there's no fringe beside the mic, and their head and shoulders are fully in frame on every page.
   In the app, scrub every page flip.

## Shorts

When a short contains the reading, the Read-Along page counts as its captions (each word lights as it is read).
Re-run the generator at 1080×1920 geometry only after checking the layout: text on top, the presenter bottom-anchored,
alternating corners.

## Provenance

Ported from the reading scene of a real edit (its generator, its `.readscene`/`.rpage`/`#camwrap`/`#camflip`
template rules and its matte script). Verified against that project's real data: 4 pages R/L/R/L, 194/199 words
exact-matched to speech, all 199 highlights within 21 ms of the original, `check` passed. `person-mask.swift` is
FPS-parameterized and compiles with the stock Xcode command-line tools on macOS.
