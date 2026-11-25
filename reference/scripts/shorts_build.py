"""Vertical shorts (1080x1920) for the reference edit (hooks, ranges and keywords are examples: replace them).

Layout: hook title (top) · screen share OR big kinetic keyword (middle) · presenter cam window
(bottom, rounded) · word-by-word captions over the chest · progress bar · end card.
Ranges are in edit time of the main cut (pre-bumper) and come from demo segments only.
"""
import html, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WORDS = json.load(open(os.path.join(HERE, "edit_words.json")))
EDL = json.load(open(os.path.join(HERE, "edl.json")))
I_LEN = next(s["edit_in"] for s in EDL["segments"] if s["src"] == "demo")
FPS = 24000 / 1001
ALIAS = {"pros": "prose", "saul": "sol", "gonna": "going"}


def norm(w):
    n = re.sub(r"[^a-z0-9$]", "", w.lower())
    return ALIAS.get(n, n)


_W = []
for w in WORDS:
    if _W and _W[-1][0].lower() == "all" and w[0].lower().startswith("right"):
        _W[-1] = ["Alright" + w[0][5:], _W[-1][1], w[2]]
    else:
        _W.append(list(w))
WORDS = _W


def _find(p, near, span=25):
    toks = [norm(t) for t in p.replace("-", " ").split() if norm(t)]
    best = None
    for i in range(len(WORDS) - len(toks) + 1):
        if all(norm(WORDS[i + k][0]) == toks[k] for k in range(len(toks))):
            d = abs(WORDS[i][1] - near)
            if d <= span and (best is None or d < best[0]):
                best = (d, i)
    if best is None:
        raise SystemExit(f"anchor not found: {p!r} near {near}")
    return best[1], len(toks)


def at(p, n):
    return WORDS[_find(p, n)[0]][1]


def end(p, n):
    i, k = _find(p, n)
    return WORDS[i + k - 1][2]


def snap(t):
    return round(round(t * FPS) / FPS, 4)


FIX = {"saul": "Sol", "pros": "prose", "hostnaim": "Hostname"}   # ASR misspelling -> caption spelling (add the presenter's name)


def fix(w):
    m = re.match(r"^(\W*)(.*?)(\W*)$", w)
    return m.group(1) + FIX.get(m.group(2).lower(), m.group(2)) + m.group(3)


SHORTS = [
    {"slug": "short-1-why-i-wont-write-with-opus",
     "hook": ["WHY I WON'T", "WRITE WITH *OPUS 5.5*"],
     "range": (at("Here's why", 666.0) - 0.06, end("it's just wrong", 717.0) + 0.3),
     "words": [(at("invisible watermark", 670.0), "*INVISIBLE* WATERMARK"), (at("It survives copy", 680.0), "SURVIVES *COPY*"),
               (at("It survives pasting", 682.0), "SURVIVES *PASTE*"), (at("no switching it", 688.0), "!NO OFF SWITCH!"),
               (at("run a detector", 698.0), "!DETECTORS! NOW"), (at("fingerprint", 714.0), "NOT MY *NAME*")]},
    {"slug": "short-2-it-found-clues-i-planted",
     "hook": ["OPUS 5.5 FOUND CLUES", "*I DIDN'T KNOW* I PLANTED"],
     "range": (at("I asked it to think", 460.0) - 0.06, end("make it episodic now", 507.0) + 0.3),
     "words": [(at("read everything", 470.0), "IT READ *EVERYTHING*"), (at("the 15 creatures", 474.0), "*15* CREATURES"),
               (at("A boulder that", 484.0), "A BOULDER THAT *MOVED*"), (at("a mound that got", 488.0), "A *CONTOUR LINE*"),
               (at("six different storylines", 502.0), "*6* STORYLINES")]},
    {"slug": "short-3-it-measured-my-brand",
     "hook": ["AI MEASURED", "*MY THUMBNAILS*"],
     "range": (at("Then I pointed it at my", 572.0) - 0.06, end("wasn't gonna work", 622.0) + 0.3),
     "screen": True},
    {"slug": "short-4-sketch-to-blender",
     "hook": ["A HAND SKETCH →", "*A REAL 3D MODEL*"],
     "range": (at("And this is the sketch, what", 314.0) - 0.06, end("I can now build from", 366.0) + 0.3),
     "screen": True},
]
END_CARD = 2.6
TEMPLATE = open(os.path.join(HERE, "short_template.html")).read()


def mark(text):
    t = html.escape(text)
    t = re.sub(r"\*(.+?)\*", r'<span class="g">\1</span>', t)
    return re.sub(r"!(.+?)!", r'<span class="r">\1</span>', t)


def build(spec):
    out = os.path.join(PROJ, "shorts", spec["slug"])
    if not os.path.exists(os.path.join(out, "hyperframes.json")):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["npx", "hyperframes", "init", out, "--non-interactive", "--example=blank"], check=True, capture_output=True)
    a = os.path.join(out, "assets")
    os.makedirs(os.path.join(a, "sfx"), exist_ok=True)
    for f in ["edit/voice.wav", "edit/cam.mp4", "edit/screen.mp4"] + [f"sfx/{n}.mp3" for n in ["whoosh", "whoosh-short", "pop", "impact-bass-1"]]:
        dst = os.path.join(a, os.path.basename(f) if f.startswith("edit") else f)
        if os.path.exists(dst):
            os.remove(dst)
        os.link(os.path.join(PROJ, "assets", f), dst)
    x, y = snap(spec["range"][0]), snap(spec["range"][1])
    assert x >= I_LEN, "shorts use demo segments only"
    speech = round(y - x, 4)
    total = round(speech + END_CARD, 3)
    dm = round(x - I_LEN, 4)   # media offset inside cam/screen (demo-only files)
    S = lambda t: round(t - x, 3)
    media = [f'<audio id="v0" src="assets/voice.wav" data-start="0" data-duration="{speech}" data-media-start="{x}" data-track-index="20" data-volume="1"></audio>']
    vids = (f'<div id="camwin"><video id="cam" src="assets/cam.mp4" data-start="0" data-duration="{speech}" data-media-start="{dm}" data-track-index="2" muted playsinline></video></div>')
    if spec.get("screen"):
        vids += (f'<div id="scrwin"><video id="scr" src="assets/screen.mp4" data-start="0" data-duration="{speech}" data-media-start="{dm}" '
                 f'data-track-index="3" muted playsinline></video></div>')
    els, js = [], []
    ws = [[w, S(s0), S(e0)] for w, s0, e0 in WORDS if x <= s0 < y - 0.05]
    groups, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[.,?!]$", w[0]) or (i + 1 < len(ws) and ws[i + 1][1] - w[2] > 0.35):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    for g, grp in enumerate(groups):
        gs = grp[0][1] - 0.04
        ge = groups[g + 1][0][1] - 0.04 if g + 1 < len(groups) else min(grp[-1][2] + 0.5, speech)
        spans = " ".join(f'<span class="cw" id="g{g}w{k}">{html.escape(fix(w).upper())}</span>' for k, (w, s0, e0) in enumerate(grp))
        els.append(f'<div class="clip cap" id="g{g}" data-start="{max(0, gs):.3f}" data-duration="{max(0.2, ge - gs):.3f}" data-track-index="6">'
                   f'<div class="capin" id="g{g}i" data-fit="{html.escape(" ".join(fix(w[0]).upper() for w in grp))}">{spans}</div></div>')
        js.append(f'tl.fromTo("#g{g}i",{{scale:.72,y:30,opacity:0}},{{scale:1,y:0,opacity:1,duration:.16,ease:"back.out(2.6)"}},{max(0, gs):.3f});')
        for k, (w, s0, e0) in enumerate(grp):
            js.append(f'tl.set("#g{g}w{k}",{{color:"#39d98a",scale:1.12}},{s0:.3f});')
            if k + 1 < len(grp):
                js.append(f'tl.set("#g{g}w{k}",{{color:"#f2ecdf",scale:1}},{grp[k + 1][1]:.3f});')
    for b, (bt, text) in enumerate(spec.get("words", [])):
        s0 = S(bt)
        e0 = min(s0 + 4.0, S(spec["words"][b + 1][0]) - 0.1 if b + 1 < len(spec["words"]) else speech)
        els.append(f'<div class="clip bword" id="bw{b}" data-start="{s0 - 0.05:.3f}" data-duration="{e0 - s0 + 0.05:.3f}" data-track-index="1">'
                   f'<div class="bwin" id="bw{b}i" data-fit="{html.escape(re.sub(r"[*!]", "", text))}" data-fitw="980">{mark(text)}</div></div>')
        js.append(f'tl.fromTo("#bw{b}i",{{scale:1.4,opacity:0,filter:"blur(12px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:.35,ease:"expo.out"}},{s0 - 0.05:.3f});')
        js.append(f'tl.to("#bw{b}i",{{opacity:0,y:-40,duration:.2}},{e0 - 0.2:.3f});')
        media.append(f'<audio id="sw{b}" src="assets/sfx/whoosh-short.mp3" data-start="{max(0, s0 - 0.1):.3f}" data-duration="0.57" data-track-index="{30 + b}" data-volume="0.22"></audio>')
    if spec.get("screen"):
        js.append(f'tl.fromTo("#scr",{{scale:1}},{{scale:1.12,duration:{speech:.2f},ease:"none"}},0);')
    hook = "".join(f'<div class="hl" id="h{i}">{mark(l)}</div>' for i, l in enumerate(spec["hook"]))
    js.insert(0, 'tl.fromTo("#hook",{scale:1.1,y:120},{scale:1,y:0,duration:.55,ease:"expo.out"},1.6);')
    js.insert(0, 'tl.fromTo(".hl",{opacity:0,yPercent:80},{opacity:1,yPercent:0,duration:.4,stagger:.12,ease:"back.out(1.8)"},0);')
    js.insert(0, f'tl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{total},ease:"none"}},0);')
    js.append(f'tl.fromTo("#endbg",{{clipPath:"circle(0% at 50% 60%)"}},{{clipPath:"circle(130% at 50% 60%)",duration:.5,ease:"power3.inOut"}},{speech:.3f});')
    js.append(f'tl.fromTo("#endin > *",{{opacity:0,y:60}},{{opacity:1,y:0,duration:.4,stagger:.12,ease:"back.out(1.6)"}},{speech + .3:.3f});')
    media += [f'<audio id="swend" src="assets/sfx/whoosh.mp3" data-start="{speech - 0.05:.3f}" data-duration="0.57" data-track-index="50" data-volume="0.4"></audio>',
              f'<audio id="swhit" src="assets/sfx/impact-bass-1.mp3" data-start="{speech + 0.35:.3f}" data-duration="2.12" data-track-index="51" data-volume="0.35"></audio>',
              '<audio id="swhook" src="assets/sfx/pop.mp3" data-start="0.05" data-duration="0.72" data-track-index="52" data-volume="0.35"></audio>']
    bg = '<div id="bg"><div class="grid"></div><div class="glow1"></div><div class="glow2"></div></div>'
    rep = {"TOTAL": f"{total}", "SPEECH": f"{speech:.3f}", "ENDDUR": f"{END_CARD}", "BG": bg, "PERSON": vids, "HOOK": hook,
           "ELEMENTS": "\n".join(els), "AUDIO": "\n".join(media), "TIMELINE": "\n".join(js), "READCLS": ""}
    page = TEMPLATE
    for k, v in rep.items():
        page = page.replace("{{" + k + "}}", v)
    open(os.path.join(out, "index.html"), "w").write(page)
    print(f"{spec['slug']}: {total:.1f}s ({speech:.1f}s speech)")


if __name__ == "__main__":
    import sys
    for s in SHORTS:
        if len(sys.argv) < 2 or sys.argv[1] in s["slug"]:
            build(s)
