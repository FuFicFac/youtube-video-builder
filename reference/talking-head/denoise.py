"""Voice cleanup (~80% perceptual noise reduction target). Noise here is HVAC rumble/hum (76% < 150 Hz, peaks 47-53 & 105-111 Hz).
Chain on the loudness-normalised cut voice: highpass 80 Hz, notches at 50/108 Hz, light afftdn, gentle expander in pauses.
afftdn latency (measured by cross-correlation) is trimmed so every word keeps its exact sample position.
Then two-pass loudnorm -16 LUFS / -1.5 dBTP, exact sample count. Writes A/B excerpts + denoise_report.json."""
import json, re, subprocess, wave, numpy as np
SRC, OUT = "tmp/voice_untreated_norm.wav", "../assets/edit/voice.wav"
FILT = ("highpass=f=80:poles=2,equalizer=f=50:t=q:w=4:g=-18,equalizer=f=108:t=q:w=6:g=-10,"
        "afftdn=nr=12:nf=-58:tn=1,agate=threshold=0.006:ratio=2:range=0.2:attack=8:release=250:knee=4")


def ff(*a):
    return subprocess.run(["ffmpeg", "-hide_banner", "-y", "-threads", "4", *map(str, a)], capture_output=True, text=True, check=True).stderr


def J(r):
    return json.loads(re.findall(r"\{[^{}]+\}", r)[-1])


def read(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels())[:, 0].astype(float) / 32768


ff("-i", SRC, "-af", FILT, "-ac", "1", "-c:a", "pcm_s16le", "tmp/den_nocomp.wav")
A, B = read(SRC), read("tmp/den_nocomp.wav")
N = len(A)
seg = slice(48000 * 300, 48000 * 306)
lag = int(np.argmax(np.correlate(B[seg.start:seg.stop + 4800], A[seg], "valid")))
ff("-i", "tmp/den_nocomp.wav", "-af", f"atrim=start_sample={lag},asetpts=PTS-STARTPTS,apad,atrim=end_sample={N}", "-c:a", "pcm_s16le", "tmp/den.wav")
m = J(ff("-i", "tmp/den.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"))
af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000,apad,atrim=end_sample={N}")
ff("-i", "tmp/den.wav", "-af", af, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", OUT)
C = read(OUT)
fm = J(ff("-i", OUT, "-af", "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-"))
w = json.load(open("edit_words.json"))
gaps = [(p[2] + 0.1, q[1] - 0.1) for p, q in zip(w, w[1:]) if q[1] - p[2] > 0.45]
def rms(x, s, e):
    v = x[int(s * 48000):int(e * 48000)]
    return 20 * np.log10(max(1e-9, np.sqrt(np.mean(v * v))))
red = [rms(A, s, e) - rms(C, s, e) for s, e in gaps]
# timing check: onset envelope alignment on 5 speech windows (lag should be ~0)
lags = []
for s in (40, 200, 400, 600, 780):
    a, c = np.abs(A[s * 48000:(s + 4) * 48000]), np.abs(C[s * 48000:(s + 4) * 48000])
    k = np.ones(480) / 480
    ea, ec = np.convolve(a, k, "same"), np.convolve(c, k, "same")
    x = np.correlate(ec[2400:-2400], ea, "valid"); lags.append(int(np.argmax(x)) - 2400)
for n, (s, e) in enumerate([(160, 175), (470, 485)]):
    ff("-ss", s, "-t", e - s, "-i", SRC, f"ab_{n}_before.wav")
    ff("-ss", s, "-t", e - s, "-i", OUT, f"ab_{n}_after.wav")
rep = {"filter": FILT, "latency_trimmed_samples": lag, "samples_in": N, "samples_out": len(C), "final_I": fm["input_i"], "final_TP": fm["input_tp"],
       "pause_windows": len(gaps), "pause_noise_reduction_db_median": round(float(np.median(red)), 2),
       "pause_noise_reduction_db_range": [round(float(min(red)), 2), round(float(max(red)), 2)],
       "timing_envelope_lag_samples": lags}
json.dump(rep, open("denoise_report.json", "w"), indent=1)
print(json.dumps(rep, indent=1))
