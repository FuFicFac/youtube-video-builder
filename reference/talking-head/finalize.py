"""Per-file final loudness (-16 LUFS / -1.5 dBTP, audio-only, video stream-copied) + verification:
duration, frame count, full decode errors, EBU R128 after encode. Writes final_qa.json."""
import glob, json, os, re, subprocess
R = "../renders"


def run(a):
    return subprocess.run(a, capture_output=True, text=True, check=True)


def J(t):
    return json.loads(re.findall(r"\{[^{}]+\}", t)[-1])


out = []
for f in [p for p in glob.glob(f"{R}/*.mp4") + glob.glob(f"{R}/shorts/*.mp4") if not p.endswith(".tmp.mp4")]:
    m = J(run(["ffmpeg", "-hide_banner", "-threads", "4", "-i", f, "-vn", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]).stderr)
    if abs(float(m["input_i"]) + 16) > 0.3 or float(m["input_tp"]) > -1.5:
        af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
              f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
        tmp = f[:-4] + ".tmp.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-threads", "4", "-i", f, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", af,
             "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", tmp]).check_returncode()
        os.replace(tmp, f)
    fm = J(run(["ffmpeg", "-hide_banner", "-threads", "4", "-i", f, "-vn", "-af", "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-"]).stderr)
    dur = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).stdout.strip()
    fr = run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets,width,height", "-of", "csv=p=0", f]).stdout.strip()
    errs = len([l for l in run(["ffmpeg", "-v", "error", "-threads", "4", "-i", f, "-f", "null", "-"]).stderr.splitlines() if l.strip()])
    r = {"file": os.path.relpath(f, R), "duration": float(dur), "video": fr, "decode_errors": errs, "LUFS": fm["input_i"], "dBTP": fm["input_tp"],
         "before_LUFS": m["input_i"]}
    print(r, flush=True); out.append(r)
json.dump(out, open("final_qa.json", "w"), indent=1)
