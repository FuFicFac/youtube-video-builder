"""Hybrid person mattes: Apple Vision person segmentation (tight edges, no set-light halo)
everywhere, except a fixed box around the mic stand where the earlier u2net matte is kept
(Vision treats the mic as background). Frame registration: every file's frame 0 is source
frame ceil(start * 24000/1001), matching ffmpeg's accurate -ss and the person-mask tool.

Runs chunk by chunk; raw masks are deleted as soon as each chunk is encoded.
usage: hybrid_masks.py [chunk-name ...]
"""
import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.environ["TMPDIR"] = os.path.join(HERE, "tmp")
os.makedirs("tmp", exist_ok=True)
os.makedirs("../assets/hybrid", exist_ok=True)
F = 24000 / 1001
SRC = "../assets/src/source.mp4"
PM = os.environ.get("PERSON_MASK_BIN")
if not PM or not os.path.isfile(PM) or not os.access(PM, os.X_OK):
    raise RuntimeError("Set PERSON_MASK_BIN to a verified person-mask executable")


def f0(t):
    return math.ceil(t * F - 1e-6)


# name, start, duration, old-matte file, old-matte start, crop (w,h,x,y) or None, mic box (x,y,w,h)
FULL_BOX = (840, 560, 470, 520)
CAM_BOX = (160, 420, 220, 332)
CHUNKS = [
    ("th_000", 0.0, 120.0, "../assets/alpha/th_a.webm", 0.0, None, FULL_BOX),
    ("th_120", 120.0, 40.0, "../assets/alpha/th_a.webm", 0.0, None, FULL_BOX),
    ("th_160", 160.0, 13.9, "../assets/alpha/th_a2.webm", 158.0, None, FULL_BOX),
    ("th_286", 286.0, 120.0, "../assets/alpha/th_b.webm", 286.0, None, FULL_BOX),
    ("th_406", 406.0, 120.0, "../assets/alpha/th_b.webm", 286.0, None, FULL_BOX),
    ("th_526", 526.0, 100.0, "../assets/alpha/th_b.webm", 286.0, None, FULL_BOX),
    ("cam_158", 158.0, 137.9, "../assets/alpha/cam_read.webm", 158.0, (428, 752, 0, 165), CAM_BOX),
]


def run(name, start, dur, old, old_start, crop, box):
    out = f"../assets/hybrid/{name}.webm"
    if os.path.exists(out) and os.path.exists(out + ".json"):
        print(f"{name}: exists, skipping", flush=True)
        return
    raw = f"tmp/{name}.gray"
    subprocess.run([PM, SRC, str(start), str(dur), raw, "accurate"], check=True, stderr=subprocess.DEVNULL)
    meta = json.load(open(raw + ".json"))
    n, mw, mh = meta["frames"], meta["mask_width"], meta["mask_height"]
    w, h = (crop[0], crop[1]) if crop else (1920, 1080)
    crop_f = f",crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}" if crop else ""
    skip = f0(start) - f0(old_start)
    bx, by, bw, bh = box
    g = (f"[0:v]setpts=PTS-STARTPTS,format=rgb24{crop_f}[v];"
         f"[1:v]lut=y='clip((val-90)*1.8,0,255)',scale=1920:1080:flags=lanczos,format=gray{crop_f}[vm];"
         f"[2:v]trim=start_frame={skip},setpts=PTS-STARTPTS,alphaextract,format=gray,lut=y='if(gt(val,170),255,0)',gblur=sigma=1.2[um];"
         f"color=c=black:s={w}x{h}:r=24000/1001,format=gray,drawbox=x={bx}:y={by}:w={bw}:h={bh}:color=white:t=fill[box];"
         f"[um][box]blend=all_mode=multiply:shortest=1[umb];"
         f"[vm][umb]blend=all_mode=lighten:shortest=1[a];"
         f"[v][a]alphamerge,format=yuva420p[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", SRC,
                    "-f", "rawvideo", "-pix_fmt", "gray", "-video_size", f"{mw}x{mh}", "-framerate", "24000/1001", "-i", raw,
                    "-c:v", "libvpx-vp9", "-i", old,
                    "-filter_complex", g, "-map", "[out]", "-frames:v", str(n), "-an",
                    "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-row-mt", "1",
                    "-deadline", "good", "-cpu-used", "5", "-auto-alt-ref", "0", out], check=True)
    meta.update({"first_source_frame": f0(start), "old_matte": old, "mic_box": box, "crop": crop})
    json.dump(meta, open(out + ".json", "w"), indent=1)
    os.remove(raw)
    os.remove(raw + ".json")
    print(f"{name}: {n} frames, vision {meta['elapsed_seconds']:.0f}s", flush=True)


if __name__ == "__main__":
    want = set(sys.argv[1:])
    for c in CHUNKS:
        if not want or c[0] in want:
            run(*c)
    print("HYBRID MASKS DONE", flush=True)
