# Design playbook

Detail for SKILL.md phase 4 (STRUCTURE → SKIN). Storytelling authority: [bilateral-visual-storytelling.md](bilateral-visual-storytelling.md).

## 5b. Research and evidence-led visuals

The creator can supply only a talking-head recording. Own the supporting research, asset creation and visual direction; do not require them to supply screen recordings or finished graphics.

- Dispatch bounded research subagents for claims, chart data and relevant source material while the lead agent plans the edit. Review their evidence before using it; keep heavy local media jobs sequential.
- Use available browser/computer tools to inspect primary sources and capture relevant charts, pages or application views. Save source URLs, publication/data dates, captured originals and underlying data when available in the project, with a `SOURCES.md` mapping each visual to its spoken claim and timeline cue.
- Either use a readable source capture or rebuild it as an animated HyperFrames chart. Preserve values, units, axis scales, time ranges, legends and qualifications. Verify extracted numbers against the original; never invent missing values or imply more precision than the source supports. Flag an unsupported spoken claim rather than illustrating it as established fact.
- Make motion explain the narration: reveal the relevant series, trace the trend, highlight the comparison, zoom into the referenced region, or introduce annotations on the corresponding words. Keep labels readable and preserve context during crops and zooms. Show a compact source credit and retain full provenance in `SOURCES.md`.
- Generated images may illustrate a concept or supply a decorative layer. Render factual chart geometry and labels deterministically from verified data; do not rely on image generation to preserve numbers, axes or source text. Label conceptual illustrations when they could be mistaken for evidence.

## 5c. Spoken references are cues: the reference sweep

**Why this exists.** In one recording the presenter said, on camera, "here's a picture of <person>, and here's their full name right there" and "here's a picture of <another person>… and a couple of screenshots of <their product>." Both times the images were not visible in the recording, and the first build ignored both. The creator had to catch it twice. **A spoken reference is an instruction to the editor, whoever the presenter says it to.** If they tell an on-screen AI agent "go find a picture of <person>", the final video still needs that picture.

**Run this sweep on the final edited-voice transcript, before designing any cards.** Read every sentence and flag:
- **Show-and-tell phrases:** "here's a picture/photo/logo/screenshot of…", "look at this", "check this out", "you can see", "I'll show you", "as you can see", "this is X" (about a person, product or place).
- **Introductions:** any named person, product, company, tool, repo or place that the presenter explains ("it's from X", "created by X", "if you don't know what X is", "he's the guy who…").
- **Things the presenter asks an on-screen agent to find or make** that the recording doesn't clearly show.

**For each flag, do all of this (no asking first; the presenter asking for the visual is permission to download it):**
1. **Find a real asset online**, in this order: Wikipedia/Wikimedia Commons infobox image (CC license) for people, places and products → the project's own official repo or press kit (for open-source tools use the MIT/Apache-licensed repo assets such as theme previews or README screenshots) → other clearly licensed sources. Do NOT use images from an "all rights reserved" site when a licensed alternative exists. Never generate a real person's likeness.
2. **Check the license and the facts.** Record license, author/credit, source URL, date, and file size. Verify the spelling of the name and the claim being illustrated (Wikipedia is the minimum check). Note what the footage never verifies.
3. **Download it into `assets/images/`** (state the filename, source and size in the report) and **look at the image** before using it. Make a web-sized copy.
4. **Show it, anchored to the spoken words.** Name plate with the full name and role; a short credit line on screen for any CC BY (or similar) license; keep the credit legible. In cam sections use a card clear of the face and mic (top-right works). In screen sections use an opaque panel over the screen area (not a see-through one). When there is a gap before the images arrive, fill it with a title card, not empty space.
5. **Log it** in `SOURCES.md` (spoken line, file, source, license, caveats) and put the credit lines in every description.

**Gate before render:** write a short `REFERENCES.md` table (timestamp, spoken phrase, asset, source, license, status). Every row must be "placed" or explicitly "could not find, creator informed". Never skip a reference silently. If nothing suitable exists, say so in chat and offer an alternative (a titled card).

**Also:** include these assets in the shorts when the clip contains the reference.

## 6. Design

- **Editorial energy and retention:** a visual style specifies typography, palette and geometry; keep the lively explanatory rhythm of the approved edits. Build frequent useful visual moments from what the presenter actually says: comparisons, examples, step reveals, qualifications and concise diagrams. Fill the available negative space with larger, bold, readable material while protecting the presenter's face/head, gestures and meaningful source content; keep the presenter visibly engaged in the explanation. Time motion, emphasis and transitions to the speech. A sparse layout, long inert panel or long passage with no illustration needs an editorial reason. When the creator asks for mostly white panels with black lettering against a black filmed background, use that direction coherently. User-requested purposeful motion takes precedence over an adapted web template's instant-only animation restrictions. Keep claims source-faithful; no filler graphics merely to increase scene count.
- **Channel style, designed per explanation:** take research facts and cautions into the edit, then design the scenes around the presenter's actual words. The reference edits show cut-out slides, rounded presenter cards, highlighter blocks, large numbers and readable foreground callouts. Preserve that purposeful timing and variety when adapting another visual style; avoid imposing another agent's research-slide layout on the finished edit.
- **Protect the presenter's face through motion:** position text-over-footage from the union of face boxes across the whole window, allowing for punch-ins, leaning and chin/beard. Stack chips below the chin on the roomier side; see `face_box()` in `reference/talking-head/build.py` and the Apple Vision `facetrack.swift` helper. On other platforms use available tracking or manually verify the full movement range. Inspect actual MP4 frames from every overlay window.
- **Small repairs after rendering:** `reference/talking-head/patch_window.py` can make a video-only, time-shifted composition for a bounded re-render. Adapt its FPS, check patch alignment against the original (PSNR peak at offset 0), splice on exact frame boundaries while retaining the original audio, and verify the saved repaired MP4. Use `--keep-fg` when the window includes words behind the presenter.

- **Balanced presenter treatments:** keep content-driven full camera, source stages and original-footage cards. Masking is selective, never dominant. Its dynamic possibilities are still welcome, particularly compositions that move the presenter to the side and leave generous space for large, readable supporting graphics. Give the edit a balanced mix of masked cut-outs, purposeful slides/swishes and repositioning, full-frame talking head, and rounded rectangular head-and-shoulders cards. Do not let masking dominate, and do not reduce this preference to a ban on masking or a rigid equal-time quota. Choose the treatment to support each spoken beat; avoid repetitive effects or constant movement while the viewer needs to read.
- **Foreground graphics:** text boxes and graphics may appear **in front of the presenter**, directly over the original footage; no subject mask is needed. Use animated text cards, lower thirds, keyword boxes, quote panels, arrows and callouts as part of the visual mix. Time their entrances, emphasis and exits to the explanation, keep text readable, and position them clear of the presenter's face and any screen detail being discussed. Foreground overlays, side panels and presenter repositioning are deliberate design choices alongside masking, not emergency fallbacks. Choose these treatments autonomously without asking the creator what should replace a behind-the-head effect.
- **Screen-share and chart framing:** prefer a vertical rounded-corner presenter box beside the material when the presenter explains what they see. Keep their whole head and shoulders visible, with comfortable headroom, and keep the referenced screen detail readable and unobstructed. An original-footage PiP can provide variety when appropriate; use a masked presenter only when explicitly requested. Adapt historical crop coordinates to the actual footage and inspect leaning, gestures and transitions in the rendered video.

- **Brand and style variation:** locate and read the channel's own `DESIGN.md` if one exists. The blue/green palette, fixed hex values and bundled HTML are example defaults, not a requirement that every video look the same. Leave room for different palettes, typography, HTML and layout styles. Select a coherent project direction from approved references or the requested style and record it in `BRIEF.md`; adapt colors, fonts and components together while retaining readable contrast, source fidelity, purposeful motion and balanced presenter treatments. Read relevant local design/style references when available. If no other direction is selected, use these historical defaults:
  - colors: navy `#0a1424`, set green `#39d98a`, set blue `#3b7bff`, paper `#f2ecdf`, warning red `#ff5d4f`
  - fonts: League Gothic for display, Space Mono for labels, Newsreader serif for reading pages
- **Splash reference:** match the opening splash and post-hook bumper described in [splash-reference.md](splash-reference.md), which records the observed visuals and source-backed animation/SFX timing of the reference edit. Preserve that timing and motion while anchoring cues to the new narration. If the creator selects a palette/style for the whole video, adapt splash colors and typography coherently to that choice; record any retained brand-specific treatment in `BRIEF.md`. This does not override the newer full-screen outro/thumbnail instructions.
- **Opening:**
  - lower third "HOST NAME · HOST · CHANNEL NAME" (names from `BRIEF.md`)
  - no full splash here when a handoff cue exists: the video gets **one** splash, at the deliberate handoff ([cues-bumper-ending.md](cues-bumper-ending.md))
- **Captions: shorts only.** The 16:9 main gets no burned-in caption track (creator note: "I don't understand why we have captions under the entire thing"). Kinetic keywords and callouts are graphics, not captions. Add main-video captions only when the creator asks for them; then run them full-width across the bottom, never in a small corner box.
- **Cards never cover the presenter's face.** Side cards and pills next to the presenter are big and **vertical rectangles** (taller than wide), sized to the free side of the frame, never wide horizontal bars that reach into the face/head envelope. Check each card against the union face box for its whole window, including leaning.
- **Words behind the presenter, a selective masking beat** (room plate → scrim → text → cut-out):
  - use sparingly for major emphasis; prefer other layouts for routine explanations
  - split each phrase into **left and right halves around the presenter's head**
  - bold size and readable, never hidden
  - slide in from the frame edges toward the presenter, drift slightly inward
  - the full sentence stays as a small kicker line on top
- **Studio panels:** the presenter on one side, and a panel of steps, chips, stamps, hero words or ✓/✕ rows on the other, each item appearing on the word they say.
- **Panel typography beside a boxed presenter:** give explanation, chart and diagram text enough of the panel to be comfortably readable at reduced playback size. Prefer larger, heavier lettering with a strong hierarchy; let the explanation occupy the available space. Trim, split or reflow text instead of shrinking it into small, light type. Keep source credits visually secondary but legible. Check the composed frame at thumbnail/reduced playback size as well as full resolution; choose sizes for the actual layout rather than imposing a universal font-size minimum.
- **Calls to action:**
  - the channel's own offers (course, community, newsletter), named exactly as the presenter says them
  - "LINK IN THE DESCRIPTION" pill with bouncing chevrons at every link mention
- **Presenter crop and placement:** when the presenter is reduced beside a chart, source page or screen share, prefer a **vertical rectangular card**, optionally with rounded corners, on the appropriate side. Keep their **whole head and shoulders** visible with comfortable headroom; never turn a small presenter view into a tight face crop. Size and position the supporting material so its relevant detail stays readable. Masking and PiP remain options when they help the scene, not the default. Inspect the crop at multiple moments, including leaning and gestures, and in the actual rendered transitions. Historical crop coordinates below must be adapted to the new footage.
- **Screen demos and researched visuals:** the material becomes a rounded **stage**, and the presenter moves between these presets (reference `LAYOUT` in `build.py`); prefer the vertical side-card treatment above when explaining something visible:
  - `STAGE_L`/`STAGE_R`: screen big, the presenter in a PiP bubble in the corner
  - `SIDE_L`/`SIDE_R`: the presenter in a big rounded card, screen smaller
  - `PANEL_L`/`PANEL_R`: presenter card plus a rebuilt kinetic panel, screen hidden
  - **PiP bubble = head and shoulders, never a tight face crop** (creator note). Preset `PIP_HEAD_SHOULDERS`: cam window clip `inset(7% 0% 18.6% 0% round 50%)`, window scale about 0.42. That's an oval showing the whole head and shoulders, not a circle on the face.
- **Also on screen demos:**
  - zoom into the diagram region the presenter is talking about, with a slow drift on static slides
  - a tracker chip, "<SUBJECT> → <topic>" or similar
  - rebuild long static slides as kinetic panels
- **Reading pages:** use the **Read-Along Page** (section 6b).
- **Anchoring:** every cue is anchored to a phrase from the **final edited-voice transcript**. Normalize ASR variants: split hyphens, merge "All right" into "Alright", alias known mishearings (for example pros→prose), and use about a 20-second search window. Then print each cue with its words to confirm it landed.

## 6b. Signature trick: the Read-Along Page

**Use the module: [read-along/README.md](read-along/README.md).** It holds the exact recipe, the matte prep
(`prep_cam_read.command`) and the generator (`read_along.py`), which reproduces the original reading scene within
one frame. **The presenter is a cut-out by default here:** alternating corners, mirrored on the right to face the text,
drop out, flip while hidden, pop back. This is the standing exception to selective masking.

## 6c. Pictures and AI video clips: own asset production

When a beat would land harder with an image (a concept, a scene the presenter describes, a metaphor, a chapter mood), generate the asset with an available image tool within the task's authorization. Use available video tools for suitable illustrative clips. Do not routinely hand production back to the creator. If a capability is unavailable, report it and build an appropriate HyperFrames illustration where feasible. Record reusable prompts and asset slots in `IMAGE-PROMPTS.md`.

- Put them in `IMAGE-PROMPTS.md` at the project root. One entry per image:
  - **slot name**, which is the filename: `assets/images/<slot>.png`
  - **timestamp** and the **line the presenter says** there
  - **aspect and size:** 16:9 1920×1080 for full-frame beats, 1:1 or 4:5 for panel cards, 9:16 for shorts
  - **the prompt itself**, detailed: subject, composition and where empty space must stay free for text or the presenter's cut-out, camera and lens, lighting, the selected project palette from `BRIEF.md` (use historical green/blue/navy only when that look is chosen), style, mood, and what to avoid (text, logos, watermarks, extra hands)
  - one line on **how it's used**: Ken Burns drift, behind-presenter plate, panel card, or split-screen
- **Never ask for the presenter's face or likeness.** Their face only ever comes from their footage or headshots they supply. Images illustrate ideas; they don't depict the presenter.
- During assembly, a designed **placeholder** may identify a pending asset slot. Replace it with the finished asset or a deliberate HyperFrames alternative before final delivery; a placeholder build is a preview, not a completed video. Save images in their matching `assets/images/` slots and rebuild.
- **AI video is allowed** in these YouTube builds: fly-throughs, B-roll, scene illustrations (e.g. Seedance via Higgsfield). Write video prompts the same way, with slot, duration (5–10 s), aspect, motion/camera move, start and end frame and safe zones, and drop them into `assets/video/<slot>.mp4`. If the creator keeps a no-AI-video rule for another kind of film (real-footage documentaries, for example), it does not apply here unless they say so.

## 7. Shorts (3–4, 30–60 s)

Reference: `reference/scripts/shorts_build.py`, `short_template.html`.

- 1080×1920 layout:
  - hook title up top
  - middle: the screen share zoomed, or a big kinetic keyword
  - bottom: the presenter in a rounded cam window
  - word-by-word captions over their chest, with the active word green
  - progress bar across the top
  - end card: CHANNEL NAME, "FULL REVIEW ON THE CHANNEL"
- Choose self-contained arguments: a hook, a reason and a payoff. Fix ASR spellings in captions.

- **Captions are mandatory on every short.** Word-by-word burned-in captions; the Read-Along page counts only because each word lights as it is read.
- **Talking-head shorts, optional cut-out recipe** (full-frame cut-out, `reference/talking-head/short_template.html`): scale the presenter's cut-out to about 1.2× (`.fgv` 2304×1296 at left −588, top 640). The behind-words band then sits full-width at y 470 above their head, and captions sit at y 1490 on their chest. At 1.55× the head hid short words like "FAST".
