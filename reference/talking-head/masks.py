"""Person mattes for the whole source: Apple Vision .accurate person mask (contrast curve)
UNION a static hand-drawn mic matte (camera + mic never move; Vision and u2net both drop the mic).
Frame 0 of each chunk = source frame ceil(start*24000/1001). Raw masks deleted per chunk.
"""
import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.environ["TMPDIR"] = os.path.join(HERE, "tmp")
F = 24000 / 1001
SRC = "src.mp4"
PM = os.environ.get("PERSON_MASK_BIN")
if not PM or not os.path.isfile(PM) or not os.access(PM, os.X_OK):
    raise RuntimeError("Set PERSON_MASK_BIN to a verified executable")
CHUNKS = [("th_000", 0.0, 120.0), ("th_120", 120.0, 120.0), ("th_240", 240.0, 89.6)]


def f0(t):
    return math.ceil(t * F - 1e-6)


def run(name, start, dur):
    out = f"../assets/hybrid/{name}.webm"
    if os.path.exists(out + ".json"):
        print(f"{name}: exists, skipping", flush=True)
        return
    raw = f"tmp/{name}.gray"
    subprocess.run([PM, SRC, str(start), str(dur), raw, "accurate"], check=True, stderr=subprocess.DEVNULL)
    meta = json.load(open(raw + ".json"))
    n, mw, mh = meta["frames"], meta["mask_width"], meta["mask_height"]
    g = ("[0:v]setpts=PTS-STARTPTS,format=rgb24[v];"
         "[1:v]lut=y='clip((val-90)*1.8,0,255)',scale=1920:1080:flags=lanczos,format=gray[vm];"
         "[2:v]format=gray[mic];"
         "[vm][mic]blend=all_mode=lighten:shortest=0:repeatlast=1[a];"
         "[v][a]alphamerge,format=yuva420p[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "4", "-ss", str(start), "-t", str(dur), "-i", SRC,
                    "-f", "rawvideo", "-pix_fmt", "gray", "-video_size", f"{mw}x{mh}", "-framerate", "24000/1001", "-i", raw,
                    "-loop", "1", "-framerate", "24000/1001", "-i", "mic_mask.png",
                    "-filter_complex", g, "-map", "[out]", "-frames:v", str(n), "-an",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-row-mt", "1",
                    "-deadline", "good", "-cpu-used", "5", "-auto-alt-ref", "0", out], check=True)
    meta.update({"first_source_frame": f0(start)})
    json.dump(meta, open(out + ".json", "w"), indent=1)
    os.remove(raw)
    os.remove(raw + ".json")
    print(f"{name}: {n} frames, vision {meta.get('elapsed_seconds', 0):.0f}s", flush=True)


if __name__ == "__main__":
    want = set(sys.argv[1:])
    for c in CHUNKS:
        if not want or c[0] in want:
            run(*c)
    print("MASKS DONE", flush=True)
