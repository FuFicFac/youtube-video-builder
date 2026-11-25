#!/usr/bin/env python3
"""Read-Along Page generator: the presenter reads text on screen and the page follows word by word.

Writes one HyperFrames sub-composition (compositions/<id>.html) with:
  * a warm paper page that opens with a circular reveal, header chips,
  * the passage paginated, each page sliding in ~0.45 s before its first spoken word,
  * word-by-word highlight (dim ink -> full ink + green marker that clears on the next word),
  * the presenter's cut-out (transparent matte video) in a bottom corner, alternating sides every page and
    mirrored on the right so they always face the text; the cut-out drops out, flips while hidden, pops back.

Ported from the "READ scene" of an earlier edit's generator + template.
Standard library only. Usage:  python3 read_along.py CONFIG.json
Prints the host <div> to paste into index.html (with data-words-pin so the app re-times it on cuts).

CONFIG.json (times are FINAL-TIMELINE seconds unless named source_*):
{
  "project": "/abs/project/root",
  "id": "read-along",                       # composition id + filename (one per reading passage)
  "start": 158.4, "end": 291.0,             # read span on the final timeline (host data-start/end)
  "track_index": 6,
  "header": ["BOOK TITLE", "CHAPTER 1 · CHAPTER NAME"],   # first = filled chip, rest = labels
  "paragraphs": ["verbatim text typed from the recording's frames", "..."],
  "pages": [[[0,1],"R"], [[2],"L"]],        # optional: paragraph indices + presenter's side; auto if omitted
  "font_sizes": [66, 56],                   # optional, per page; auto from word count if omitted
  "words": "work/edit_words.json",          # final-timeline words: [[text,start,end],...] or [{text,start,end}]
  "cam": {
    "src": "assets/alpha/cam_read.webm",    # transparent matte of the cam strip (prep_cam_read.sh)
    "source_start": 158.0,                  # source second where the matte file begins
    "segments": [[158.4, 158.0, 40.2], [198.6, 199.9, 92.4]],  # [timeline_start, source_start, duration]: the EDL
    "width": 640, "video_height": 1126, "bottom": -46        # card geometry (historical defaults)
  },
  "pin_src": "assets/src/source.mp4",     # optional: recording the reading comes from, for data-words-pin
  "pin_source_from": 158.0, "pin_source_to": 296.3,
  "palette": {"paper": "#f2ecdf", "ink": "#191713", "marker": "rgba(57,217,138,0.5)",
              "glow": "rgba(57,217,138,0.16)", "chip_bg": "#191713", "chip_fg": "#39d98a",
              "serif": "Newsreader", "mono": "Space Mono"},
  "font_faces": "@font-face { ... }",       # optional CSS, e.g. the project's Newsreader/Space Mono faces
  "fps": 30
}
"""
import html
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

W, H = 1920, 1080
PAL = {"paper": "#f2ecdf", "ink": "#191713", "marker": "rgba(57,217,138,0.5)",
       "glow": "rgba(57,217,138,0.16)", "chip_bg": "#191713", "chip_fg": "#39d98a",
       "serif": "Newsreader", "mono": "Space Mono"}


def norm(w):
    return re.sub(r"[^a-z0-9$]", "", w.lower())


def load_words(path):
    raw = json.loads(Path(path).read_text())
    out = []
    for w in raw:
        if isinstance(w, dict):
            out.append((w.get("text") or w.get("word"), float(w["start"]), float(w.get("end", w["start"]))))
        else:
            out.append((w[0], float(w[1]), float(w[2] if len(w) > 2 else w[1])))
    return out


def auto_pages(paras, target=85):
    """Group paragraphs into pages of ~target words; sides alternate R, L, R, ..."""
    pages, cur, n = [], [], 0
    for i, p in enumerate(paras):
        c = len(p.split())
        if cur and n + c > target:
            pages.append(cur)
            cur, n = [], 0
        cur.append(i)
        n += c
    if cur:
        pages.append(cur)
    return [(pl, "R" if k % 2 == 0 else "L") for k, pl in enumerate(pages)]


def auto_size(nwords):
    # Historical sizes: 66/56/52/70 px for ~45/75/80/40-word pages. Fewer words -> bigger type.
    return int(max(50, min(74, 74 - (nwords - 35) * 0.45)))


def main(cfg_path):
    cfg = json.loads(Path(cfg_path).read_text())
    root = Path(cfg["project"])
    cid = cfg.get("id", "read-along")
    pal = {**PAL, **cfg.get("palette", {})}
    fps = float(cfg.get("fps", 30))
    snap = lambda t: round(round(t * fps) / fps, 3)  # noqa: E731
    rs, re_ = snap(float(cfg["start"])), snap(float(cfg["end"]))
    dur = round(re_ - rs, 3)
    L = lambda t: max(0.0, snap(t - rs))  # noqa: E731  timeline -> scene-local

    paras = cfg["paragraphs"]
    pages = [(list(p), s) for p, s in cfg["pages"]] if cfg.get("pages") else auto_pages(paras)
    toks = [(p, w) for p, txt in enumerate(paras) for w in txt.split()]

    # --- align page words to spoken words (difflib equal+replace, interpolate the rest) ---
    words_path = Path(cfg["words"])
    words = load_words(words_path if words_path.is_absolute() else root / words_path)
    spoken = [w for w in words if rs - 0.2 <= w[1] < re_]
    a, b = [norm(w) for _, w in toks], [norm(w[0]) for w in spoken]
    times = [None] * len(toks)
    matched = 0
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("equal", "replace"):
            for k in range(i2 - i1):
                times[i1 + k] = spoken[j1 + min(k, j2 - j1 - 1)][1]
                matched += op == "equal"
    known = [i for i, t in enumerate(times) if t is not None]
    for i in range(len(times)):
        if times[i] is None:
            prev = max((k for k in known if k < i), default=None)
            nxt = min((k for k in known if k > i), default=None)
            if prev is not None and nxt is not None:
                times[i] = times[prev] + (times[nxt] - times[prev]) * (i - prev) / (nxt - prev)
            else:
                times[i] = times[prev] + 0.25 if prev is not None else rs + 1
    for i in range(1, len(times)):
        times[i] = max(times[i], times[i - 1] + 0.05)

    # --- page markup ---
    sizes = cfg.get("font_sizes") or [auto_size(sum(len(paras[p].split()) for p in pl)) for pl, _ in pages]
    page_html, first_word = [], []
    for pg, (plist, side) in enumerate(pages):
        col = "colL" if side == "R" else "colR"
        ps_html, first = [], None
        for p in plist:
            spans = []
            for i, (pp, w) in enumerate(toks):
                if pp == p:
                    spans.append(f'<span class="w" id="{cid}-w{i}">{html.escape(w)}</span>')
                    first = i if first is None else first
            ps_html.append(f'<p>{" ".join(spans)}</p>')
        first_word.append(first)
        page_html.append(f'<div class="rpage {col}" id="{cid}-pg{pg}" style="font-size:{sizes[pg]}px">{"".join(ps_html)}</div>')

    hdr = cfg.get("header", [])
    head_html = "".join(
        f'<span class="chipg">{html.escape(t)}</span>' if k == 0 else f"<span>{html.escape(t)}</span>"
        for k, t in enumerate(hdr))

    # --- cam: one clip per EDL segment inside the span, all inside the flip wrapper ---
    cam = cfg["cam"]
    cw, vh, vb = cam.get("width", 640), cam.get("video_height", 1126), cam.get("bottom", -46)
    vids = []
    for n, (ts, ss, d) in enumerate(cam["segments"]):
        a0, a1 = max(ts, rs), min(ts + d, re_)
        if a1 - a0 <= 1 / fps:
            continue
        media = ss + (a0 - ts) - cam["source_start"]
        vids.append(f'<video class="clip" id="{cid}-cam{n}" src="{cam["src"]}" muted playsinline '
                    f'data-start="{L(a0)}" data-duration="{snap(a1 - a0)}" data-media-start="{snap(media)}" '
                    f'data-track-index="1"></video>')
    if not vids:
        sys.exit("cam.segments do not overlap the read span")

    # --- timeline (scene-local seconds) ---
    js = [f'tl.fromTo("#{cid}-paper",{{clipPath:"circle(0% at 50% 50%)"}},{{clipPath:"circle(150% at 50% 50%)",duration:.7,ease:"power3.inOut"}},0);',
          f'tl.fromTo("#{cid}-head",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:.5,ease:"power3.out"}},0.4);']
    for pg, (plist, side) in enumerate(pages):
        ps = 0.35 if pg == 0 else L(times[first_word[pg]] - 0.45)
        pe = L(times[first_word[pg + 1]] - 0.45) if pg + 1 < len(pages) else dur
        js.append(f'tl.fromTo("#{cid}-pg{pg}",{{opacity:0,y:70}},{{opacity:1,y:0,duration:.5,ease:"power3.out"}},{ps:.3f});')
        if pg + 1 < len(pages):
            js.append(f'tl.to("#{cid}-pg{pg}",{{opacity:0,y:-70,duration:.35,ease:"power2.in"}},{max(0, pe - .35):.3f});')
        camx = 0 if side == "R" else -(W - cw)
        headx = 0 if side == "R" else cw - 50  # header rides with the text column, never under the presenter
        flip = -1 if side == "R" else 1  # mirrored on the right so he faces left, toward the text
        if pg == 0:
            js.append(f'tl.set("#{cid}-flip",{{scaleX:{flip}}},0);')
            js.append(f'tl.set("#{cid}-head",{{x:{headx}}},0);')
            js.append(f'tl.fromTo("#{cid}-camwrap",{{x:{camx},yPercent:100}},{{x:{camx},yPercent:0,duration:.7,ease:"power3.out"}},0.3);')
        else:  # drop out, flip while hidden, pop back up. Never flip while visible.
            js.append(f'tl.to("#{cid}-camwrap",{{yPercent:100,duration:.35,ease:"power3.in"}},{max(0, ps - .5):.3f});')
            js.append(f'tl.set("#{cid}-camwrap",{{x:{camx}}},{max(0, ps - .14):.3f});')
            js.append(f'tl.set("#{cid}-flip",{{scaleX:{flip}}},{max(0, ps - .14):.3f});')
            js.append(f'tl.to("#{cid}-head",{{x:{headx},duration:.4,ease:"power3.inOut"}},{max(0, ps - .5):.3f});')
            js.append(f'tl.to("#{cid}-camwrap",{{yPercent:0,duration:.55,ease:"back.out(1.2)"}},{max(0, ps - .12):.3f});')
    for i in range(len(toks)):
        js.append(f'tl.set("#{cid}-w{i}",{{color:"{pal["ink"]}",backgroundColor:"{pal["marker"]}"}},{L(times[i]):.3f});')
        if i + 1 < len(toks):
            js.append(f'tl.set("#{cid}-w{i}",{{backgroundColor:"rgba(0,0,0,0)"}},{L(times[i + 1]):.3f});')
    js.append(f'tl.to("#{cid}-camwrap",{{yPercent:100,duration:.35,ease:"power3.in"}},{max(0, dur - .45):.3f});')

    # Unread words: dimmed ink. 52% keeps the read/unread progress obvious and passes `check` (WCAG AA large, 3:1).
    # The original used 32%, which `check` fails as contrast_aa_failure.
    ink_dim = cfg.get("unread_ink") or ("rgba(25,23,19,0.52)" if pal["ink"].lower() == "#191713"
                                        else "color-mix(in srgb, " + pal["ink"] + " 52%, transparent)")
    css = f"""{cfg.get("font_faces", "")}
#{cid}-root {{ position:absolute; inset:0; overflow:hidden; }}
#{cid}-paper {{ position:absolute; inset:0; background:{pal["paper"]}; }}
#{cid}-glow {{ position:absolute; width:1600px; height:1600px; left:-300px; top:-700px; border-radius:50%;
  background:radial-gradient(circle, {pal["glow"]} 0%, rgba(0,0,0,0) 60%); }}
#{cid}-head {{ position:absolute; left:110px; top:46px; display:flex; gap:26px; align-items:center; font-family:"{pal["mono"]}", monospace;
  font-weight:700; font-size:30px; letter-spacing:.1em; color:{pal["ink"]}; }}
#{cid}-root .chipg {{ background:{pal["chip_bg"]}; color:{pal["chip_fg"]}; padding:6px 16px; border-radius:8px; }}
#{cid}-root .rpage {{ position:absolute; top:140px; bottom:60px; display:flex; flex-direction:column; justify-content:center; opacity:0; }}
#{cid}-root .rpage.colL {{ left:110px; width:{W - cw - 130}px; }}
#{cid}-root .rpage.colR {{ left:{cw + 60}px; width:{W - cw - 160}px; }}
#{cid}-root .rpage p {{ font-family:"{pal["serif"]}", Georgia, serif; font-weight:450; font-size:1em; line-height:1.42; margin:0 0 30px; color:{pal["ink"]}; }}
#{cid}-root .w {{ color:{ink_dim}; border-radius:6px; }}
#{cid}-camwrap {{ position:absolute; left:{W - cw}px; top:0; width:{cw}px; height:{H}px; overflow:hidden;
  filter:drop-shadow(0 18px 40px rgba(25,23,19,.45)); }}
#{cid}-flip {{ position:absolute; inset:0; transform-origin:50% 50%; }}
#{cid}-flip video {{ position:absolute; left:0; bottom:{vb}px; width:{cw}px; height:{vh}px; }}"""

    doc = f"""<!DOCTYPE html>
<html>
  <head><meta charset="UTF-8"><title>{cid}</title></head>
  <body>
    <template>
      <style>{css}
      </style>
      <div id="{cid}-root" data-composition-id="{cid}" data-width="{W}" data-height="{H}">
        <div id="{cid}-paper"></div><div id="{cid}-glow"></div>
        <div id="{cid}-head">{head_html}</div>
        {"".join(page_html)}
        <div id="{cid}-camwrap"><div id="{cid}-flip">{"".join(vids)}</div></div>
      </div>
      <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
        {chr(10).join("        " + j for j in js).lstrip()}
        window.__timelines["{cid}"] = tl;
      </script>
    </template>
  </body>
</html>
"""
    out = root / "compositions" / f"{cid}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc)

    pin = ""
    if cfg.get("pin_src"):
        pin = f' data-words-pin="{cfg["pin_src"]} {cfg["pin_source_from"]} {cfg["pin_source_to"]}"'
    host = (f'<div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" '
            f'data-start="{snap(rs)}" data-duration="{dur}" data-track-index="{cfg.get("track_index", 6)}" '
            f'data-track-kind="graphics" data-width="{W}" data-height="{H}"{pin}></div>')
    print(f"wrote {out}")
    print(f"pages: {len(pages)}  words: {len(toks)}  exact-matched to speech: {matched}/{len(toks)}"
          f"  cam clips: {len(vids)}  sides: {' '.join(s for _, s in pages)}")
    if matched < 0.8 * len(toks):
        print("WARNING: under 80% of page words matched the transcript. Check the span, the words file and the typed text.")
    print("host for index.html (if this is a rebuild, keep the existing data-hf-id):")
    print(host)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
