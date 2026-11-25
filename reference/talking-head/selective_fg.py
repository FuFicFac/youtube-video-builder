"""Selective presenter cut-outs: one alpha webm per behind-text window (edit time), Apple Vision .accurate
person mask on exactly the source frames that window shows. Frame-exact: edit frame -> source frame via the
same rounding cut.py uses. Output assets/edit/fgw{i}.webm (i = window index in fg_windows.json)."""
import json, math, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
os.environ["TMPDIR"] = os.path.join(HERE, "tmp")
F = 24000 / 1001
PM = os.environ.get("PERSON_MASK_BIN")
if not PM or not os.path.isfile(PM) or not os.access(PM, os.X_OK):
    raise RuntimeError("Set PERSON_MASK_BIN to a verified executable")
edl = json.load(open("edl.json"))["segments"]
wins = [{"name": f"fgw{i}", "a": a, "b": b} for i, (a, b) in enumerate(json.load(open("fg_windows.json")))]
if os.path.exists("shorts_windows.json"):
    wins += json.load(open("shorts_windows.json"))   # [{name, a, b}] edit-time ranges used by the shorts
# edit frame table
table, e = [], 0
for s in edl:
    fa, fb = round(s["src_in"] * F), round(s["src_out"] * F)
    table.append((e, e + fb - fa, fa)); e += fb - fa


def src_runs(ea, eb):
    runs = []
    for lo, hi, fa in table:
        a, b = max(ea, lo), min(eb, hi)
        if a < b:
            runs.append((fa + a - lo, b - a))
    return runs


def enc(args, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "4", *args, "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                    "-b:v", "0", "-crf", "28", "-row-mt", "1", "-deadline", "good", "-cpu-used", "5", "-auto-alt-ref", "0", out], check=True)


for wdef in wins:
    name, a, b = wdef["name"], wdef["a"], wdef["b"]
    i = name
    out = f"../assets/edit/{name}.webm"
    if os.path.exists(out + ".ok"):
        continue
    ea, eb = round(a * F), round(b * F)
    parts = []
    for k, (sf, n) in enumerate(src_runs(ea, eb)):
        start = (sf - 0.25) / F           # ceil(start*F) == sf
        dur = (n + 2) / F
        raw = f"tmp/m{name}_{k}.gray"
        subprocess.run([PM, "src.mp4", f"{start:.6f}", f"{dur:.6f}", raw, "accurate"], check=True, stderr=subprocess.DEVNULL)
        m = json.load(open(raw + ".json"))
        g = ("[0:v]setpts=PTS-STARTPTS,format=rgb24[v];"
             "[1:v]lut=y='clip((val-90)*1.8,0,255)',scale=1920:1080:flags=lanczos,format=gray[a];"
             "[2:v]format=gray[mic];[a][mic]blend=all_mode=lighten:shortest=0:repeatlast=1[am];"
             "[v][am]alphamerge,format=yuva420p[out]")
        p = f"tmp/{name}_{k}.webm"
        enc(["-ss", f"{start:.6f}", "-t", f"{dur:.6f}", "-i", "src.mp4", "-f", "rawvideo", "-pix_fmt", "gray",
             "-video_size", f"{m['mask_width']}x{m['mask_height']}", "-framerate", "24000/1001", "-i", raw,
             "-loop", "1", "-framerate", "24000/1001", "-i", "mic_mask.png",
             "-filter_complex", g, "-map", "[out]", "-frames:v", str(n)], p)
        os.remove(raw); os.remove(raw + ".json")
        parts.append(p)
    ins = sum([["-c:v", "libvpx-vp9", "-i", p] for p in parts], [])
    g = "".join(f"[{k}:v]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0,format=yuva420p[o]"
    enc([*ins, "-filter_complex", g, "-map", "[o]", "-r", "24000/1001"], out)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                        "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    if int(n) != eb - ea:
        raise RuntimeError(f"{name}: {n} frames; expected {eb - ea}; no success marker written")
    print(f"{name}: {n} frames (expected {eb - ea}) OK", flush=True)
    for p in parts:
        os.remove(p)
    open(out + ".ok", "w").write(n)
print("FG DONE", flush=True)
