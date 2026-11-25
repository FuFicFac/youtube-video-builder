"""Frame-exact cutting of the edit (edl.json) into layers.

usage:
  cut.py audio                         -> ../assets/edit/voice.wav (loudness-normalised later)
  cut.py video intro                   -> ../assets/edit/intro.mp4  (full frame, intro segments only)
  cut.py video demo CROP NAME          -> ../assets/edit/NAME.mp4   (crop w:h:x:y of the demo segments)
One ffmpeg at a time, 4 threads.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.makedirs("../assets/edit", exist_ok=True)
os.makedirs("graphs", exist_ok=True)
F = 24000 / 1001
edl = json.load(open("edl.json"))
SEG = edl["segments"]
SRC_V = {"intro": "../assets/src/intro.mp4", "demo": "../assets/src/demo.mp4"}
SRC_A = {"intro": "intro_audio.wav", "demo": "demo_audio.wav"}
mode = sys.argv[1]

if mode == "audio":
    parts, labels = [], []
    for i, s in enumerate(SEG):
        idx = 0 if s["src"] == "intro" else 1
        d = s["src_out"] - s["src_in"]
        parts.append(f"[{idx}:a]atrim={s['src_in']:.6f}:{s['src_out']:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.6f}:d=0.008[a{i}]")
        labels.append(f"[a{i}]")
    g = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
    open("graphs/audio.ffgraph", "w").write(g)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC_A["intro"], "-i", SRC_A["demo"],
                    "-/filter_complex", "graphs/audio.ffgraph", "-map", "[out]", "-ar", "48000", "-ac", "2",
                    "voice_raw.wav"], check=True)
    print("wrote voice_raw.wav")
else:
    src = sys.argv[2]
    crop = sys.argv[3] if len(sys.argv) > 3 else None
    name = sys.argv[4] if len(sys.argv) > 4 else src
    parts, labels = [], []
    for i, s in enumerate([s for s in SEG if s["src"] == src]):
        fa, fb = round(s["src_in"] * F), round(s["src_out"] * F)
        cf = f",crop={crop}" if crop else ""
        parts.append(f"[0:v]trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS{cf}[v{i}]")
        labels.append(f"[v{i}]")
    g = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[out]"
    gp = f"graphs/{name}.ffgraph"
    open(gp, "w").write(g)
    out = f"../assets/edit/{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "4", "-i", SRC_V[src], "-/filter_complex", gp,
                    "-map", "[out]", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-threads", "4",
                    "-pix_fmt", "yuv420p", "-g", "24", "-movflags", "+faststart", out], check=True)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    exp = sum(round(s["src_out"] * F) - round(s["src_in"] * F) for s in SEG if s["src"] == src)
    print(f"wrote {out}: {n} frames (expected {exp})", "OK" if int(n) == exp else "MISMATCH")
