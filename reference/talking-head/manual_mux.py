"""Finish a render whose segment concat failed (disk full): concat the captured segments (stream copy) and rebuild the
audio mix from the composition's own <audio> elements (src, data-start, data-media-start, data-duration, data-volume)."""
import html, json, re, subprocess, sys
D, OUT = sys.argv[1], sys.argv[2]
page = open("index.html").read()
segs = json.load(open(f"{D}/segments.json"))
n = segs["totalFrames"]
F = 24000 / 1001
total = n / F
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", sorted(__import__("glob").glob(f"{D}/concat-list-*.txt"))[0],
                "-c", "copy", "work/tmp/main_video.mp4"], check=True)
auds = re.findall(r"<audio ([^>]*)>", page)
ins, parts = [], []
for k, a in enumerate(auds):
    at = dict(re.findall(r'([\w-]+)="([^"]*)"', a))
    st, ms, du, vol = float(at["data-start"]), float(at.get("data-media-start", 0)), float(at["data-duration"]), float(at.get("data-volume", 1))
    ins += ["-i", at["src"]]
    parts.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={ms:.4f}:{ms + du:.4f},asetpts=PTS-STARTPTS,"
                 f"volume={vol},adelay={int(round(st * 1000))}:all=1[a{k}]")
g = ";".join(parts) + ";" + "".join(f"[a{k}]" for k in range(len(auds))) + f"amix=inputs={len(auds)}:normalize=0:dropout_transition=0,atrim=0:{total:.4f}[mix]"
open("work/tmp/mix.ffgraph", "w").write(g)
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-/filter_complex", "work/tmp/mix.ffgraph", "-map", "[mix]", "-ar", "48000", "-c:a", "pcm_s16le", "work/tmp/main_mix.wav"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/tmp/main_video.mp4", "-i", "work/tmp/main_mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("frames", n, "audio elements", len(auds), "->", OUT)
