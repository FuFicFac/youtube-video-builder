"""Assemble assets/edit/fg.webm (presenter cut-out, alpha) on the edited timeline from the
hybrid mattes in assets/hybrid/. Frame-exact: each hybrid file's frame 0 is source frame
ceil(start*F); EDL segments are split wherever they cross a hybrid-chunk boundary.
Read segments are transparent (the reading scene uses its own cam matte).
"""
import json, math, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
edl = json.load(open("edl.json"))
F = 24000 / 1001
FPS = "24000/1001"
CH = [("th_000", 0.0), ("th_120", 120.0), ("th_240", 240.0)]
src = []
for name, start in CH:
    meta = json.load(open(f"../assets/hybrid/{name}.webm.json"))
    a = math.ceil(start * F - 1e-6)
    src.append((f"../assets/hybrid/{name}.webm", a, a + meta["frames"]))

inputs = []
for p, _, _ in src:
    inputs += ["-c:v", "libvpx-vp9", "-i", p]
parts, labels = [], []


def add(part):
    labels.append(f"[v{len(parts)}]")
    parts.append(part + f"[v{len(parts)}]")


for s in edl["segments"]:
    fa, fb = round(s["src_in"] * F), round(s["src_out"] * F)
    if s["section"] == "read":
        add(f"color=c=black@0.0:s=1920x1080:r={FPS},trim=end_frame={fb - fa},format=yuva420p")
        continue
    cur = fa
    while cur < fb:
        hit = next(((i, lo, hi) for i, (p, lo, hi) in enumerate(src) if lo <= cur < hi), None)
        if hit is None:  # 1-frame rounding gap between chunks: repeat the previous chunk's last matte frame
            prev = next(((i, lo, hi) for i, (p, lo, hi) in enumerate(src) if hi == cur), None)
            if prev is None:
                raise SystemExit(f"no hybrid matte covers source frame {cur} ({cur / F:.2f}s)")
            i, lo, hi = prev
            add(f"[{i}:v]trim=start_frame={hi - 1 - lo}:end_frame={hi - lo},setpts=PTS-STARTPTS,format=yuva420p")
            cur += 1
            continue
        i, lo, hi = hit
        end = min(fb, hi)
        add(f"[{i}:v]trim=start_frame={cur - lo}:end_frame={end - lo},setpts=PTS-STARTPTS,format=yuva420p")
        cur = end
g = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[out]"
os.makedirs("graphs", exist_ok=True)
open("graphs/fg.ffgraph", "w").write(g)
out = "../assets/edit/fg.webm"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-/filter_complex", "graphs/fg.ffgraph", "-map", "[out]",
                "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "30", "-row-mt", "1",
                "-deadline", "good", "-cpu-used", "5", "-auto-alt-ref", "0", out], check=True)
n = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                    "stream=nb_read_packets", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
exp = sum(round(s["src_out"] * F) - round(s["src_in"] * F) for s in edl["segments"])
print(f"wrote {out}: {n} frames (expected {exp})", "OK" if int(n) == exp else "MISMATCH")
