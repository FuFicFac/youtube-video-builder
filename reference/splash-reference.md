# Channel splash reference — a worked example

This records the splash and bumper of one approved reference edit, as an example of the timing and motion a channel
splash needs. Swap in your own logo, palette, tagline and sounds; keep the discipline of anchoring every event to a
measured time.

## Evidence and scope

Measured media of the reference edit: 1920×1080, 24000/1001 nominal fps, 834.125750 seconds.
Visual design reviewed from frames extracted from the actual MP4 (opening 0–75s, splash 2–7s, bumper 32–37s, last 30s). Exact easing, event times, font names, colors and audio cue names below come from the matching local HyperFrames composition, not estimates from screenshots. Sound cues are source-code evidence; this review does not claim an independent listening assessment.
Generator examples in this repo: `scripts/base_logo.py.txt`, `templates/template.html`, `scripts/base_sfx.py.txt` and `scripts/build.py`.

## Opening splash — 00:02.610–00:06.180

Full-frame dark navy (#0a1424) takeover, opening vertically from a thin horizontal center strip over 0.35s (`expo.out`). Soft green and blue light beams sweep in opposite directions. Large condensed League Gothic three-word logo: a blue first word (#3b7bff) and a green second word (#39d98a) on the top row, the warm off-white third word (#f2ecdf) below. Small widely tracked green Space Mono tagline (the channel's own line).

- 2.610: navy reveal begins.
- 2.710 / 2.810: opposing light sweeps begin (1.4s / 1.6s).
- 2.860: first-word letters drop/flip into place with 0.08s stagger, 0.45s duration, `back.out(1.8)`.
- 4.060: the second word scales down from 2.6× to 1× over 0.35s, `expo.out`.
- 4.510: the third word reveals left-to-right over 0.4s, `power4.out`.
- 4.560: subtle whole-logo push from 1× to 1.06× over 1.2s.
- 4.760: tagline rises 20px and fades in over 0.35s.
- 5.830: logo shrinks to 0.6×, blurs 12px and fades over 0.3s; background/tagline fade from 5.880. Return to camera by 6.180.

Source sound cues: whoosh at 2.560 (gain .45), sparkle at 4.160 (.18), bass impact 1 at 4.510 (.5). Preserve the relationship to word entrances while mixing appropriately against new speech.

## Post-hook bumper — 00:32.580–00:35.980 (3.4 seconds)

Same stacked logo and navy palette. Circular background reveal (0.5s), staggered rising first-word letters, rotating/scaling second-word pop-in, the third word settling from a wide horizontal scale, expanding/fading green rings, and an episode-specific subtitle. The subtitle names the episode (TOPIC · ANGLE); replace it for each new episode.

Relative to bumper start: first word +0.35s; second word and rings +0.70s; third word +0.85s; tagline +1.30s. Three rings expand from .2× to 3.2×, fading over 1.6s with .3s stagger. Logo gently pushes to 1.08×. At +2.95s logo/tag/rings move upward and fade; at +3.00s navy wipes upward over .4s.

Source sound cues: riser starts .6s before bumper (last 1.3s of riser asset); short whoosh at +.3s; bass impact 2 at +.7s; exit whoosh at +2.95s.

## Apply to the next video

**One full splash per video.** The reference edit had both an opening splash and a post-hook bumper; the standing rule is now only one. Use the post-hook bumper treatment at the deliberate handoff cue ("…on <channel name>"). The opening splash timings above are reference for that one splash's motion vocabulary, or for where it goes when no handoff cue exists. See [cues-bumper-ending.md](cues-bumper-ending.md).

Recreate these treatments in HyperFrames using the existing logo/template/SFX references. Match typography, stacked composition, colors, motion order, light sweeps/rings and sound punctuation. Re-anchor the opening word entrances to the new edited voice saying the channel name; the old absolute timestamps are evidence, not new-video cues. Insert the 3.4s bumper at the appropriate post-hook beat. Avoid adding an unrelated new splash design.

This reference governs the brand splash and bumper. The outro rules in [cues-bumper-ending.md](cues-bumper-ending.md) still govern the recommendation ending: original full-screen presenter and pointing gesture, large lower-third recommended-video title, and clear thumbnail placement areas. Do not copy the old ending's presenter-card layout over that instruction.
