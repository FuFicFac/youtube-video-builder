# Narration becomes an illustration

Distilled from a creator's review of one real edit. This is the reusable method, not a claim that every prior render used it. User-selected house style overrides historical palette examples. Preserve CUT → STRUCTURE → SKIN.

## Plan the entire narration

Before expensive capture, audit the whole final transcript, including jokes, demos, surprises, useful revelations, emotional turns and the ending. Assign every interval a purposeful illustration, real source demo, presenter hold, brand cue or closing treatment. Quiet presenter passages need a content-specific reason. Engagement has no motion quota or arbitrary card cadence. (Fast-cut mode tightens this: see fast-cut-mode.md §1.) “Brutalist” describes visual skin; it never means sparse storytelling or cutting meaningful dialogue.

Find causal opportunities: establish an object; the spoken verb changes its state; the next clause reveals the consequence. Keep that same illustration alive through the sentence instead of substituting a string of text cards. A passing concern can become a returning speech ribbon and then an unchecked task; scattered session slips can compile into a summary and enter an inbox. Label schematic, hypothetical, recollected and unverified outcomes accurately. Preserve meaningful response waits and reaction timing.

## Use the available space

Inspect actual footage for head, shoulders, leaning, hands, mic and gesture envelopes across each scene and transition. Record presenter exclusion and left/right graphic regions. Use both sides as a coordinated sentence when space permits: input or problem on one side, response or payoff on the other. One side leads while the other holds context. Size pictures and labels for the actual playback surface. Do not reuse a small fixed left card as the whole visual grammar.

When full-camera footage cannot safely support bilateral explanation, contain the complete original frame in a centered card, preserving gestures. For native OBS strips, retain their original unmasked geometry. Clip each side canvas so moving graphics cannot cross the presenter exclusion. Preserve true screen evidence when the presenter refers to a visible document, thumbnail or history. No invented screenshot or presenter likeness, and no faces of people who haven't agreed to appear.

Occasional full-screen illustrative takeovers are explicitly allowed: the presenter temporarily disappears while their voice continues, the illustration performs a strong narrated idea, and the edit returns naturally to them or the real demo. Use these selected moments for genuine explanatory or comedic benefit, without a duration quota. Return to the real face for important reactions and vulnerable delivery. A full-screen takeover supersedes the presenter-visible exclusion requirement for that interval; preserve the original voice and document the return reason.

## Word and beat timing

Anchor each meaningful object/action/consequence to retained words from complete edited-voice ASR. Resolve merged numerals and proper-name variants deliberately. Log the exact retained phrase, actual word start, rounded rational frame, physical state change and purpose. Verify uncertain soft starts with measured waveform and short-window ASR; graphics move to the voice, never shift speech to fit an effect. Apply motion-doctrine to real authored seams, preserve its direction/current and run the numerical seam gate. Use finite information-driven actions; no idle ambient wobble or endless cute loops.

Reference videos can inspire attention, causal continuity and spoken-word precision. Do not copy another creator’s character designs, illustrations, compositions, choreography or signature scenes. Distinguish user-reported quality from your own representative-frame or listening evidence.

## A limited raster experiment

An original raster may serve one especially useful narrative scene when authorized. Generate ahead of time; retain the prompt, hash, source path, symbolic label, exact scene and generation budget. HyperFrames supplies narration-driven motion and supporting authored paths/footsteps/text. A generic dog is a symbolic illustration, never a fabricated portrait of the creator's own pet, an invented exterior recording or evidence of a real condition. Honor an explicit one-image budget. The rest may remain authored vector illustrations. Preserve transparency and never generate the presenter’s likeness.

## Effects align to motion

Asset start is not perceptual onset. Measure each reused effect’s onset and energy peak, especially swishes with quiet lead-in. Identify the visible sweep center, impact or physical arrival frame. Trim leading quiet when justified, preserve the original effect’s tone, and place its peak on the intended visual beat or slight documented lead. Log asset trim, onset, peak, timeline start, gain and frame error. Do not blanket-shift dialogue. Keep gains quiet, avoid comedy effects on vulnerable moments, and measure final encoded loudness separately for each affected output. Audit all effect-bearing transitions; listen when possible and state limitations when it is not.

## Ending QR and validation

Use a user-supplied or verified exact destination. Preserve QR modules and quiet zone, square aspect and stationary placement. Respect the requested safe area; for TV playback, bottom LEFT worked in the reference edit, with 15–20 seconds of hold inside the existing ending. Keep face, signoff and end-screen gesture areas safe. Decode the QR from actual final encoded frames at multiple times, including reduced playback scale; decoding the source PNG alone is insufficient. No unrequested tail or publication.

Run `scripts/bilateral_checks.py PROJECT --phase authoring --report qa/bilateral-authoring.json` before capture. Use `STORYTELLING-AUDIT.json` as the evidence contract: continuous section coverage, purposeful beats, actual geometry, retained-word actions, cue and effect ledgers, generated-asset budget/hash and return reasons. After encoding, add actual finished-frame paths and independent final gates, then run phase `final`. The helper validates declared evidence, not artistic quality or listening.

Inspect actual finished frames for every authored world, material action, transition and long hold, plus bumper and ending. Validate full decode, actual decoded frame count, rational packet cadence, source-to-edited PCM integrity excluding only documented seam treatments, complete encoded ASR differences, final loudness and QR decode. Self-correlation cannot establish retained-source integrity. Preserve a reviewed export and offer prior comparison during a revision. Reuse unaffected Shorts’ QA only after byte hashes and shared dependency identities remain unchanged. Refresh transcript, chapter timings and promises from the final encoded audio.
