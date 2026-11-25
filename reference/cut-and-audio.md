# Cut and audio: transcription, EDL, sound, layers

Detail for SKILL.md phases 2–3. Method authority: [editorial-method.md](editorial-method.md).

## 2. Transcribe: chunked and safe

`reference/templates/transcribe.command` runs Parakeet (`uvx --from parakeet-mlx parakeet-mlx`) in 120-second chunks, sequentially, through the selected durable runner. Keep long transcriptions sequential; concurrent runs were associated with prior crashes, without proving causation. Merge the chunks with offsets into `*_words.json`.

Parakeet sometimes silently **drops a whole sentence inside a chunk** (not only at edges). Check every gap over 1.5 s between words against `silencedetect`: if the gap isn't silent, re-run Parakeet on a short window around it and splice the words in.

## 3. Edit decision list

Reference: `reference/scripts/edl.py`. For a locked-camera talking-head take, read `reference/talking-head/README.md` and its matching variant scripts.

- **Content anchors and acoustic seams:** the transcript identifies the intended removal; the measured source waveform determines the actual seam in quiet air. Protect complete acoustic tails and soft onsets on both sides, recovering missing recognition in short windows. Historical 50–60 ms ASR-start pads are examples, not universal safe boundaries.
- **What to cut:**
  - flubs, false starts, stutters and "uh"/"um"
  - repeated takes and intros, keeping the intended clean take, and "I know I stumbled" asides
  - long dead air, misspeaks and self-corrections, keeping the corrected version without changing the meaning; flag an uncorrected substantive misspeak rather than inventing replacement speech
  - log every cut in `CUT-NOTES.md` so the creator can veto
- **Calibrated pause tightening:** actually run a measured pause pass on the retained speech ranges. Select the detector/gate, minimum run and natural lead/tail handles from this recording’s noise floor, quiet speech, source scenes and cadence; record them and the evidence. Historical −45 dB/0.55 s/0.32 s settings must not be copied as defaults. Protect full word intervals (soft starts and tails), intentional rhythm and jokes. Review transient interruptions before joining wordless runs across them; uncertain sounds remain flagged. Log tightened and deliberately retained pauses.
- **Whole-video gap sweep, before the first preview.** The default taste is *tight*. A first app build drew four comments ("tons of silence right here", "MORE UNNECESSARY SILENCE", "Sweep the entire video for gaps"). After the pause pass, list every inter-word gap in the edited voice longer than about 0.6 s (calibrate to the presenter's cadence on this recording). Each one is either tightened or logged in `CUT-NOTES.md` with a specific reason (a joke beat, a reaction, a demo wait). "Pending review" is not a resting state; review every candidate before the creator sees a preview. Sweep again after every revision that moves audio.
- **Never clip a word to win a gap (creator note: "You cut off the word folder").** Tightening stops at the measured acoustic tail. Re-listen or re-transcribe a short window around every seam whose neighbor word ends in a soft consonant.
- **Clamp the last segment** to the real frame count from `ffprobe -count_packets`.
- **Bumper:** insert B = 3.4 s at the deliberate post-hook handoff to the channel name, before the call to action. Detect and verify that cue with §3a; use its measured speech completion as C. Split every media layer at C, then shift later cues with `T(t)`.


## 4. Audio

- **Voice over music:** run Demucs `htdemucs --two-stems vocals -d cpu -j 1 --segment 7` (reference: `separate.command`) on only the music span. Remix with vocals at 0 dB and music at −12 dB, then splice it back in.
  - Tell the creator it's the one spot to spot-check; fixing that span in their own editor is the fallback.
- Cut audio with sample-based `atrim` and 8 ms fades per segment.
- **Diagnose noise before choosing a denoiser:** inspect a pause spectrum and listen. In one office recording, most noise was low-frequency HVAC hum; high-pass/notch filters plus light denoising helped where afftdn alone did not. `reference/talking-head/denoise.py` preserves this measured example and latency compensation. Adapt its filter frequencies, sample rate, speech windows and paths to the current recording; do not apply those historical settings blindly. The example starts from a normalized A/B reference, then normalizes again after cleanup.
- **Background-noise cleanup:** reduce quiet-room incidental sounds, room tone and steady noise before loudness normalization. The target is up to roughly **80% perceptual noise reduction** while keeping the voice natural; this is a listening target, not a fixed filter setting or a measured reduction claim. Do not report a numerical reduction as achieved unless actually measured with a stated method. Back off processing if it causes pumping, watery/metallic artifacts, dull consonants or unnatural breathing. Treat isolated clicks separately where needed; do not remove speech transients as noise.
  - A/B the untreated and cleaned voice at matched listening loudness, including quiet phrases, consonants, breaths and pauses. Preserve the edited audio's exact sample count/duration and sync; compensate any denoiser latency without shifting word timing.
- After noise cleanup, normalize with two-pass loudnorm to **−16 LUFS / −1.5 dBTP**.
- **Final deliverable loudness:** independently measure each final main video and each short after SFX, mixing and AAC encoding. Normalize each to **−16 LUFS** with a **−1.5 dBTP ceiling**, then remeasure the encoded result. A normalized master does not guarantee a normalized excerpt, especially when a short selects emphatic speech. For an audio-only correction, preserve the HyperFrames-rendered picture with video stream-copy.
- **Verify:** re-transcribe the edited voice in chunks and diff it against the intended script. Check anything suspicious with a 20-second whisper window, since chunk edges drop words (an ASR artifact, not a bad cut).

## 5. Layers: frame-exact

**App-native default:** prepare each layer once at full source length (crops, cleaned voice) and express the cuts as clips with `data-media-start` on the frame grid ([hyperframes-app.md](hyperframes-app.md) §2), so the creator can trim them in the app. The frame-exact pre-cut layers below are the fallback for footage that doesn't seek cleanly, and remain the rule whenever ffmpeg itself cuts.

Reference: `reference/scripts/cut.py`.

- Use `trim=start_frame/end_frame`, never time trims; those drifted 5 frames over 9 minutes and slid the cut-out off the presenter. Verify each layer's frame count equals the EDL sum.
- **Screen-demo recordings:** first measure the current recording. The historical OBS layout put the cam strip at 428×752 (x0, y165) and the screen share at 1480×624 (x440, y134). Pre-crop each into its own file, since small frames render much cheaper than 1080p cropped twice.
- **Hybrid cut-out** (selective masking beats, where the presenter is full-frame and text goes behind them; see the masking rule in SKILL.md):
  - Apple Vision `.accurate` (set `PERSON_MASK_BIN` to a verified local `person-mask` executable; it is not bundled), with a contrast curve `clip((v−90)·1.8)`
  - Vision treats the **mic as background**, so inside a fixed mic box use a thresholded u2net matte (`hyperframes remove-background`)
  - **Pure talking-head takes (locked camera):** u2net drops the mic too. Draw a **static mic polygon** once from a full-res frame (PIL, 1.5 px blur) and `lighten`-blend it with the Vision matte. No second AI pass. Reference: `reference/talking-head/masks.py`
  - Chunk rounding can leave a **1-frame gap** between matte chunks (`ceil(120·F)` ≠ previous chunk's end). `fg_build.py` repeats the previous chunk's last matte frame; see `reference/talking-head/fg_build.py`
  - frame 0 of every matte = source frame `ceil(start·fps)` using the measured project frame rate (historical examples use `24000/1001`)
  - references: `hybrid_masks.py`, `hybrid_intro.py`, `fg_build.py`
- **Selective foreground (masking beats only):** the newer `reference/talking-head/build.py` writes `fg_windows.json` for behind-text and cut-out slide windows, and `shorts_build.py` writes `shorts_windows.json`. Use `selective_fg.py` to generate only those source-aligned mattes, keeping original footage elsewhere. Read `reference/talking-head/README.md` for the build order and required face-track inputs.
- If the cut-out looks chunky, use a **rounded card of the original footage** instead. Hard cut-outs aren't required.
