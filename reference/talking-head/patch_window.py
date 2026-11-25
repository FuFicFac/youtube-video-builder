"""Make a time-windowed copy of index.html (video only) so one stretch can be re-rendered and spliced into the
finished MP4. Timed elements are shifted by -T0; the GSAP timeline is scrubbed from T0 via tweenFromTo.
usage: patch_window.py NAME T0 T1   ->  ../patch_NAME.html"""
import re, sys
name, T0, T1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
F = 24000 / 1001
T0 = round(T0 * F) / F
D = round((T1 - T0) * F) / F
page = open("../index.html").read()
page = re.sub(r"<audio [^>]*></audio>", "", page)


def drop_video(m):
    tag = m.group(0)
    s_ = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
    d_ = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
    if 'id="fg' in tag and "--keep-fg" not in sys.argv:   # full-frame stretches: the cut-out is pixel-identical to the plate
        return ""
    return "" if (s_ + d_ - T0 <= 0 or s_ - T0 >= D) else tag


page = re.sub(r"<video [^>]*></video>", drop_video, page)


def fix(m):
    tag = m.group(0)
    s = float(re.search(r'data-start="([\d.]+)"', tag).group(1))
    d = float(re.search(r'data-duration="([\d.]+)"', tag).group(1))
    a, b = s - T0, s + d - T0
    if b <= 0 or a >= D:
        tag = re.sub(r'data-start="[\d.]+"', f'data-start="{D + 5:.3f}"', tag)
        tag = re.sub(r'data-duration="[\d.]+"', 'data-duration="0.05"', tag)
        return tag
    ns, ne = max(0.0, a), min(D, b)
    if tag.startswith("<video") and "data-media-start" in tag:
        ms = float(re.search(r'data-media-start="([\d.]+)"', tag).group(1)) + (ns - a)
        tag = re.sub(r'data-media-start="[\d.]+"', f'data-media-start="{ms:.4f}"', tag)
    tag = re.sub(r'data-start="[\d.]+"', f'data-start="{ns:.4f}"', tag)
    tag = re.sub(r'data-duration="[\d.]+"', f'data-duration="{ne - ns:.4f}"', tag)
    return tag


page = re.sub(r'<(?:div|video)[^>]*data-start="[\d.]+"[^>]*data-duration="[\d.]+"[^>]*>', fix, page)
page = re.sub(r'(id="root"[^>]*data-duration=")[\d.]+', lambda m: m.group(1) + f"{D:.4f}", page, count=1)
page = page.replace('window.__timelines["main"] = tl;',
                    f'window.__timelines["main"] = gsap.timeline({{ paused: true }}).add(tl.tweenFromTo({T0:.6f}, {T0 + D:.6f}, {{ ease: "none" }}), 0);')
page = page.replace("var D = ", f"var D0 = {D:.4f}; var D = ", 1)
open(f"../patch_{name}.html", "w").write(page)
print(f"patch_{name}.html  T0={T0:.4f} D={D:.4f} frames={round(D * F)}  start_frame={round(T0 * F)}")
