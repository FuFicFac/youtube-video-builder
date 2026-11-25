"""Apply edl.json to a source (picture and/or audio) with ffmpeg trim+concat.

usage: cut.py video  SRC OUT [--offset S] [--section th|read|all] [--alpha]
       cut.py audio  SRC OUT
Segments outside --section become transparent (alpha) or are skipped.
"""
import json, subprocess, sys

edl = json.load(open("edl.json"))
FPS = "24000/1001"
mode, src, out = sys.argv[1:4]
args = sys.argv[4:]
offset = float(args[args.index("--offset") + 1]) if "--offset" in args else 0.0
section = args[args.index("--section") + 1] if "--section" in args else "all"
alpha = "--alpha" in args
compact = "--compact" in args


def want(s):
    if section == "all":
        return True
    if section == "th":
        return s["section"] in ("th_a", "th_b")
    return s["section"] == section


segs = edl["segments"]
parts, labels = [], []
if mode == "audio":
    for i, s in enumerate(segs):
        d = s["src_out"] - s["src_in"]
        parts.append(
            f"[0:a]atrim={s['src_in']:.6f}:{s['src_out']:.6f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.6f}:d=0.008[a{i}]")
        labels.append(f"[a{i}]")
    g = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-threads", "4", "-i", src, "-filter_complex", g, "-map", "[out]",
           "-ar", "48000", "-ac", "2", out]
else:
    # Only the covered span of this source gets trimmed; others are blank.
    run, cur = [], None
    for s in segs:
        ok = want(s)
        if compact and not ok:
            continue
        run.append((ok, s))
    fmt = "yuva420p" if alpha else "yuv420p"
    for i, (ok, s) in enumerate(run):
        d = s["src_out"] - s["src_in"]
        if ok:
            import math
            F = 24000 / 1001
            o = math.ceil(offset * F - 1e-6)
            fa, fb = round(s["src_in"] * F) - o, round(s["src_out"] * F) - o
            choke = ",lut=a='clip((val-70)*1.9,0,255)'" if alpha and "--choke" in args else ""
            parts.append(f"[0:v]trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS,format={fmt}{choke}[v{i}]")
        else:
            parts.append(f"color=c=black@0.0:s=WxH:r={FPS}:d={d:.6f},format={fmt}[v{i}]")
        labels.append(f"[v{i}]")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout.strip().split(",")
    g = (";".join(parts)).replace("WxH", f"{probe[0]}x{probe[1]}")
    g += ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[out]"
    if alpha:
        dec = ["-c:v", "libvpx-vp9"]
        enc = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28",
               "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0"]
    else:
        dec = []
        enc = ["-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-g", "24", "-movflags", "+faststart"]
    import os
    gp = os.path.join("graphs", os.path.basename(out) + ".ffgraph"); os.makedirs("graphs", exist_ok=True)
    open(gp, "w").write(g)
    cmd = ["ffmpeg", "-v", "error", "-y", "-threads", "4", *dec, "-i", src, "-/filter_complex", gp,
           "-map", "[out]", "-an", *enc, out]
print(" ".join(cmd[:8]), "...")
subprocess.run(cmd, check=True)
