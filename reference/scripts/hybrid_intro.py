"""Hybrid matte for the intro talking head (same recipe as an earlier edit):
Apple Vision (.accurate) + contrast curve everywhere, thresholded u2net inside a fixed mic box.
Then cut to the edit (frame-exact) -> ../assets/edit/fg_intro.webm"""
import json, math, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
F = 24000 / 1001
PM = os.environ.get("PERSON_MASK_BIN")
if not PM or not os.path.isfile(PM) or not os.access(PM, os.X_OK):
    raise RuntimeError("Set PERSON_MASK_BIN to a verified person-mask executable")
SRC = "../assets/src/intro.mp4"
DUR = 111.6
BOX = (840, 560, 470, 520)
os.makedirs("../assets/hybrid", exist_ok=True)
raw = "tmp/intro.gray"
if not os.path.exists("../assets/hybrid/intro.webm"):
    subprocess.run([PM, SRC, "0", str(DUR), raw, "accurate"], check=True, stderr=subprocess.DEVNULL)
    m = json.load(open(raw + ".json"))
    bx, by, bw, bh = BOX
    g = ("[0:v]setpts=PTS-STARTPTS,format=rgb24[v];"
         "[1:v]lut=y='clip((val-90)*1.8,0,255)',scale=1920:1080:flags=lanczos,format=gray[vm];"
         "[2:v]setpts=PTS-STARTPTS,alphaextract,format=gray,lut=y='if(gt(val,170),255,0)',gblur=sigma=1.2[um];"
         f"color=c=black:s=1920x1080:r=24000/1001,format=gray,drawbox=x={bx}:y={by}:w={bw}:h={bh}:color=white:t=fill[box];"
         "[um][box]blend=all_mode=multiply:shortest=1[umb];[vm][umb]blend=all_mode=lighten:shortest=1[a];"
         "[v][a]alphamerge,format=yuva420p[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "4", "-t", str(DUR), "-i", SRC,
                    "-f", "rawvideo", "-pix_fmt", "gray", "-video_size", f"{m['mask_width']}x{m['mask_height']}",
                    "-framerate", "24000/1001", "-i", raw, "-c:v", "libvpx-vp9", "-i", "../assets/alpha/intro_u2.webm",
                    "-filter_complex", g, "-map", "[out]", "-frames:v", str(m["frames"]), "-an",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-row-mt", "1",
                    "-threads", "4", "-deadline", "good", "-cpu-used", "5", "-auto-alt-ref", "0",
                    "../assets/hybrid/intro.webm"], check=True)
    json.dump(m, open("../assets/hybrid/intro.webm.json", "w"), indent=1)
    os.remove(raw); os.remove(raw + ".json")
# cut to edit
edl = json.load(open("edl.json"))
parts, labels = [], []
for i, s in enumerate([s for s in edl["segments"] if s["src"] == "intro"]):
    parts.append(f"[0:v]trim=start_frame={round(s['src_in'] * F)}:end_frame={round(s['src_out'] * F)},setpts=PTS-STARTPTS,format=yuva420p[v{i}]")
    labels.append(f"[v{i}]")
EXP = sum(round(s['src_out'] * F) - round(s['src_in'] * F) for s in edl["segments"] if s["src"] == "intro")
open("graphs/fg_intro.ffgraph", "w").write(";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0,tpad=stop_mode=clone:stop=6[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-c:v", "libvpx-vp9", "-i", "../assets/hybrid/intro.webm",
                "-/filter_complex", "graphs/fg_intro.ffgraph", "-map", "[out]", "-frames:v", str(EXP), "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                "-b:v", "0", "-crf", "30", "-row-mt", "1", "-threads", "4", "-deadline", "good", "-cpu-used", "5",
                "-auto-alt-ref", "0", "../assets/edit/fg_intro.webm"], check=True)
print("fg_intro done")
