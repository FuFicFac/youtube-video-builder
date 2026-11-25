"""Generate the vertical shorts (1080x1920) as separate HyperFrames projects.

Each short pulls ranges from the edited main timeline (pre-bumper edit time),
reuses the edited voice + presenter cut-out, and adds kinetic word-by-word subtitles.
"""
import html, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WORDS = json.load(open(os.path.join(HERE, "edit_words.json")))
EDL = json.load(open(os.path.join(HERE, "edl.json")))
SEG = EDL["segments"]
READ_START = 1e9  # no reading scene
FPS = 24000 / 1001


def norm(w):
    return re.sub(r"[^a-z0-9$]", "", w.lower())


def _find(phrase, near, span=9):
    toks = [norm(t) for t in phrase.split() if norm(t)]
    best = None
    for i in range(len(WORDS) - len(toks) + 1):
        if all(norm(WORDS[i + k][0]) == toks[k] for k in range(len(toks))):
            d = abs(WORDS[i][1] - near)
            if d <= span and (best is None or d < best[0]):
                best = (d, i)
    if best is None:
        raise SystemExit(f"anchor not found: {phrase!r} near {near}")
    return best[1], len(toks)


def at(p, n):
    i, _ = _find(p, n)
    return WORDS[i][1]


def end(p, n):
    i, k = _find(p, n)
    return WORDS[i + k - 1][2]


def snap(t):
    return round(round(t * FPS) / FPS, 4)


SHORTS = [
    {
        "slug": "short-1-how-many-ideas-did-you-lose",
        "hook": ["HOW MANY IDEAS", "*DID YOU LOSE?*"],
        "ranges": [(at("How many good ideas", 5.5) - 0.08, end("called Sorter.", 47.5) + 0.5)],
        "behind": [(at("couldn't find again", 11.0), "!COULDN'T FIND! IT"), (at("It's still sitting", 31.9), "*STILL THERE*"),
                   (at("what was valuable", 34.5), "*WHAT MATTERED*"), (at("a notes system", 41.0), "*NOTES SYSTEM*"),
                   (at("called Sorter", 47.2), "MEET *SORTER*")],
    },
    {
        "slug": "short-2-books-to-the-desk",
        "hook": ["HOW I'D WIRE", "*MY NOTES SYSTEM*"],
        "ranges": [(at("First, our software", 421.2) - 0.08, end("on every request.", 472.0) + 0.35)],
        "behind": [(at("breaks it into useful", 423.5), "*SECTIONS*"), (at("search finds existing", 427.0), "*SEARCH*"),
                   (at("Sorter gets a manageable", 431.0), "SORTER *COMPARES*"), (at("need a new page", 449.0), "*NEW PAGE*?"),
                   (at("bringing books to the desk", 462.5), "BOOKS → *DESK*")],
    },
    {
        "slug": "short-3-what-if-is-not-a-decision",
        "hook": ["“WHAT IF…”", "IS *NOT A DECISION*"],
        "ranges": [(at("There's another decision", 511.5) - 0.08, end("flag those cases.", 552.0) + 0.4)],
        "behind": [(at("What if we tried", 517.5), "“WHAT *IF*…”"), (at("I'm exploring", 520.5), "*EXPLORING*"),
                   (at("distinguish a possibility", 534.0), "*POSSIBILITY*"), (at("surface that disagreement", 546.0), "*SURFACE IT*"),
                   (at("Sorter could help flag", 552.0), "*FLAG IT*")],
    },
    {
        "slug": "short-4-a-million-tokens-for-4-cents",
        "hook": ["A MILLION TOKENS", "FOR *4.2¢*"],
        "ranges": [(at("The part that I love", 630.7) - 0.08, end("the cheap part.", 634.0) + 0.3),
                   (at("At the published direct", 641.5) - 0.08, end("my notes system", 682.5) + 0.35)],
        "behind": [(at("four point two cents per million", 643.5), "*4.2¢*"), (at("little pieces of text", 652.5), "*TOKENS*"),
                   (at("a thousand requests", 661.5), "*1,000* × *1,000*"), (at("one million tokens", 667.0), "*1M* TOKENS"),
                   (at("Sorter portion would be", 669.5), "= *4.2¢*"), (at("example calculation", 675.0), "!EXAMPLE! MATH")],
    },
]

PARAS = [   # EXAMPLE passage for a reading short: replace with the text actually read on screen
    "The morning ferry left the island at six, and by the time it cleared the breakwater the fog had already started to lift off the water.",
    "“Rope,” the captain said.",
    "She coiled it without looking. The engine settled into its usual rattle. Behind them the harbour lights went out one by one, and ahead the mainland showed as a thin grey line under a pale sky.",
]


def mark(text):
    t = html.escape(text)
    t = re.sub(r"\*(.+?)\*", r'<span class="g">\1</span>', t)
    t = re.sub(r"!(.+?)!", r'<span class="r">\1</span>', t)
    return t


END_CARD = 2.6
# caption spelling fixes: ASR token (lower case) -> correct spelling. EXAMPLE entries: replace with your own
# (always include the presenter's name and product names the ASR gets wrong).
FIX = {"sorta": "Sorter", "codec": "Codex", "hostname": "Host Name", "edition": "addition", "pros": "prose", "chat": "Chat", "6.": "6"}


def fix(w):
    m = re.match(r"^(\W*)(.*?)(\W*)$", w)
    core = FIX.get(m.group(2).lower(), m.group(2))
    tail = m.group(3)
    if core.isdigit() and tail == ".":
        tail = ""
    return m.group(1) + core + tail


_FT = []
for line in open(os.path.join(HERE, "face", "track.txt")):
    p = line.split()
    if len(p) == 5:
        _FT.append(((int(p[0][:5]) - 1) / 2.0, float(p[1])))


def _to_edit(ts):
    for sg in SEG:
        if sg["src_in"] <= ts < sg["src_out"]:
            return sg["edit_in"] + ts - sg["src_in"]


FACE = [(e, cx) for e, cx in ((_to_edit(t), cx) for t, cx in _FT) if e is not None]
VW = 2304 * 1.03   # cut-out width in the short (1.2x, plus the 1.03 border crop)
SW = []


def CAMLEFT(spec):
    xs = sorted(cx for e, cx in FACE if any(a <= e <= b for a, b in spec["ranges"])) or [0.5]
    cx = (xs[len(xs) // 10] + xs[-len(xs) // 10 - 1]) / 2       # middle of the presenter's lean range
    return max(1080 - VW, min(0, 540 - cx * VW))


def build(spec):
    out = os.path.join(PROJ, "shorts", spec["slug"])
    if not os.path.exists(os.path.join(out, "hyperframes.json")):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["npx", "-y", "hyperframes@0.8.81", "init", out, "--non-interactive", "--example=blank"],
                       check=True, capture_output=True)
    a = os.path.join(out, "assets")
    os.makedirs(os.path.join(a, "sfx"), exist_ok=True)
    for f in ["edit/voice.wav"] + [f"sfx/{n}.mp3" for n in
                                                                         ["whoosh", "whoosh-short", "pop", "impact-bass-1"]]:
        dst = os.path.join(a, os.path.basename(f) if f.startswith("edit") else f)
        if os.path.exists(dst):
            os.remove(dst)
        os.link(os.path.join(PROJ, "assets", f), dst)
    shutil.copy(os.path.join(PROJ, "assets", "fonts", "Newsreader.ttf"), os.path.join(a, "Newsreader.ttf"))

    rngs = [(snap(x), snap(y)) for x, y in spec["ranges"]]
    tmap, t = [], 0.0
    for x, y in rngs:
        tmap.append((x, y, t))
        t += y - x
    speech = t
    total = round(speech + END_CARD, 3)

    def S(et):  # edit time -> short time
        for x, y, o in tmap:
            if x - 0.02 <= et <= y + 0.02:
                return round(o + et - x, 3)
        return None

    media, els, js = [], [], []
    for i, (x, y, o) in enumerate(tmap):
        d = round(y - x, 4)
        media.append(f'<audio id="v{i}" src="assets/voice.wav" data-start="{o:.4f}" data-duration="{d}" data-media-start="{x}" data-track-index="20" data-volume="1"></audio>')
        if spec.get("read"):
            media.append(f'<video id="c{i}" class="camv" src="assets/cam_read.webm" data-start="{o:.4f}" data-duration="{d}" '
                         f'data-media-start="{round(x - READ_START, 4)}" data-track-index="2" muted playsinline></video>')
        else:
            nm = f"fgs_{spec['slug'][:7]}_{i}"
            src_f = os.path.join(PROJ, "assets", "edit", nm + ".webm")
            dst_f = os.path.join(a, nm + ".webm")
            if os.path.exists(src_f):
                if os.path.exists(dst_f):
                    os.remove(dst_f)
                os.link(src_f, dst_f)
            SW.append({"name": nm, "a": x, "b": y})
            media.append(f'<video id="f{i}" class="fgv" src="assets/{nm}.webm" data-start="{o:.4f}" data-duration="{d}" '
                         f'data-media-start="0" data-track-index="2" muted playsinline style="left:{CAMLEFT(spec):.0f}px"></video>')

    # punch-ins at internal cuts (edit segment boundaries inside the ranges) + range joins
    if not spec.get("read"):
        bounds = sorted({S(s["edit_in"]) for s in SEG for x, y, o in tmap if x + 0.3 < s["edit_in"] < y - 0.3}
                        | {o for x, y, o in tmap[1:]})
        for k, b in enumerate(bounds):
            if b is None:
                continue
            js.append(f'tl.set("#ejcam",{{scale:{1.1 if k % 2 == 0 else 1.0}}},{b:.3f});')

    # captions: groups of up to 3 words, break on punctuation / pauses
    ws = []
    for w, s0, e0 in WORDS:
        st = S(s0 + 0.01)
        if st is None or S(max(s0 + 0.02, e0 - 0.02)) is None:
            continue
        ws.append([w, st, S(max(s0 + 0.02, e0 - 0.02))])
    if not spec.get("read"):
        groups, cur = [], []
        for i, w in enumerate(ws):
            cur.append(w)
            brk = (len(cur) >= 3 or re.search(r"[.,?!]$", w[0]) or
                   (i + 1 < len(ws) and ws[i + 1][1] - w[2] > 0.35))
            if brk:
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        # caption words that get the accent colour. EXAMPLE list: replace with the key nouns/numbers of your video
        EMPH = {"sorter", "ideas", "idea", "lost", "search", "desk", "books", "library", "decision", "possibility",
                "exploring", "disagreement", "flag", "cheap", "cents", "tokens", "million", "thousand", "conversation", "agents",
                "fast", "free", "build", "write", "ai", "data", "everything", "model", "style", "edit",
                "cannot", "can't", "writing", "combined", "exact"}
        for g, grp in enumerate(groups):
            gs = grp[0][1] - 0.04
            ge = groups[g + 1][0][1] - 0.04 if g + 1 < len(groups) else min(grp[-1][2] + 0.5, speech)
            spans = []
            for k, (w, s0, e0) in enumerate(grp):
                cls = "cw em" if norm(w) in EMPH or any(norm(w).startswith(x) for x in ("5", "6")) else "cw"
                spans.append(f'<span class="{cls}" id="g{g}w{k}">{html.escape(fix(w).upper())}</span>')
            els.append(f'<div class="clip cap" id="g{g}" data-start="{gs:.3f}" data-duration="{max(0.2, ge - gs):.3f}" data-track-index="6">'
                       f'<div class="capin" id="g{g}i" data-fit="{html.escape(" ".join(fix(x[0]).upper() for x in grp))}">{" ".join(spans)}</div></div>')
            js.append(f'tl.fromTo("#g{g}i",{{scale:.72,y:30,opacity:0}},{{scale:1,y:0,opacity:1,duration:.16,ease:"back.out(2.6)"}},{gs:.3f});')
            for k, (w, s0, e0) in enumerate(grp):
                js.append(f'tl.set("#g{g}w{k}",{{color:"#39d98a",scale:1.12}},{s0:.3f});')
                if k + 1 < len(grp):
                    js.append(f'tl.set("#g{g}w{k}",{{color:"#f2ecdf",scale:1}},{grp[k + 1][1]:.3f});')
        for b, (bt, text) in enumerate(spec.get("behind", [])):
            s0 = S(bt)
            if s0 is None:
                continue
            nxt = [S(x[0]) for x in spec["behind"][b + 1:] if S(x[0])]
            e0 = min(s0 + 3.2, (nxt[0] - 0.1) if nxt else speech)
            els.append(f'<div class="clip bword" id="bw{b}" data-start="{s0 - 0.05:.3f}" data-duration="{e0 - s0 + 0.05:.3f}" data-track-index="1">'
                       f'<div class="bwin" id="bw{b}i" data-fit="{html.escape(re.sub(r"[*!]", "", text))}" data-fitw="1010">{mark(text)}</div></div>')
            js.append(f'tl.fromTo("#bw{b}i",{{scale:1.4,opacity:0,filter:"blur(12px)"}},{{scale:1,opacity:1,filter:"blur(0px)",duration:.35,ease:"expo.out"}},{s0 - 0.05:.3f});')
            js.append(f'tl.to("#bw{b}i",{{opacity:0,y:-40,duration:.2}},{e0 - 0.2:.3f});')
            media.append(f'<audio id="sw{b}" src="assets/sfx/whoosh-short.mp3" data-start="{s0 - 0.1:.3f}" data-duration="0.57" data-track-index="{30 + b}" data-volume="0.22"></audio>')
    else:
        # manuscript karaoke
        import difflib
        toks = [(p, w) for p, txt in enumerate(PARAS) for w in txt.split()]
        A = [norm(w) for _, w in toks]
        Bn = [norm(w[0]) for w in ws]
        times = [None] * len(toks)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, Bn, autojunk=False).get_opcodes():
            if op in ("equal", "replace"):
                for k in range(i2 - i1):
                    times[i1 + k] = ws[j1 + min(k, j2 - j1 - 1)][1]
        known = [i for i, x in enumerate(times) if x is not None]
        for i in range(len(times)):
            if times[i] is None:
                p = max([k for k in known if k < i], default=None)
                n = min([k for k in known if k > i], default=None)
                times[i] = (times[p] + (times[n] - times[p]) * (i - p) / (n - p)) if p is not None and n is not None else (times[p] + .25 if p is not None else 0.2)
        paras_html = []
        for p in range(len(PARAS)):
            sp = " ".join(f'<span class="w" id="rw{i}" data-layout-allow-occlusion>{html.escape(w)}</span>' for i, (pp, w) in enumerate(toks) if pp == p)
            paras_html.append(f'<p id="rp{p}">{sp}</p>')
        els.append(f'<div class="clip mpage" id="mpage" data-start="0" data-duration="{speech:.3f}" data-track-index="1"><div class="mscroll" id="mscroll">{"".join(paras_html)}</div></div>')
        for i in range(len(toks)):
            js.append(f'tl.set("#rw{i}",{{color:"#191713",backgroundColor:"rgba(57,217,138,0.5)"}},{times[i]:.3f});')
            if i + 1 < len(toks):
                js.append(f'tl.set("#rw{i}",{{backgroundColor:"rgba(57,217,138,0)"}},{times[i + 1]:.3f});')
        # scroll paragraph 3 up when it starts
        p3 = next(i for i, (p, w) in enumerate(toks) if p == 2)
        js.append(f'tl.to("#mscroll",{{y:-560,duration:.8,ease:"power3.inOut"}},{times[p3] - .6:.3f});')
        js.append('tl.fromTo("#mscroll",{opacity:0},{opacity:1,duration:.4,ease:"power2.out"},1.75);')

    hook = "".join(f'<div class="hl" id="h{i}">{mark(l)}</div>' for i, l in enumerate(spec["hook"]))
    js.insert(0, 'tl.fromTo("#hook",{scale:1.1,y:120},{scale:1,y:0,duration:.55,ease:"expo.out"},1.6);')
    js.insert(0, 'tl.fromTo(".hl",{opacity:0,yPercent:80},{opacity:1,yPercent:0,duration:.4,stagger:.12,ease:"back.out(1.8)"},0);')
    js.insert(0, f'tl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{total},ease:"none"}},0);')
    js.append(f'tl.fromTo("#endbg",{{clipPath:"circle(0% at 50% 60%)"}},{{clipPath:"circle(130% at 50% 60%)",duration:.5,ease:"power3.inOut"}},{speech:.3f});')
    js.append(f'tl.fromTo("#endin > *",{{opacity:0,y:60}},{{opacity:1,y:0,duration:.4,stagger:.12,ease:"back.out(1.6)"}},{speech + .3:.3f});')
    media.append(f'<audio id="swend" src="assets/sfx/whoosh.mp3" data-start="{speech - 0.05:.3f}" data-duration="0.57" data-track-index="50" data-volume="0.4"></audio>')
    media.append(f'<audio id="swhit" src="assets/sfx/impact-bass-1.mp3" data-start="{speech + 0.35:.3f}" data-duration="2.12" data-track-index="51" data-volume="0.35"></audio>')
    media.append('<audio id="swhook" src="assets/sfx/pop.mp3" data-start="0.05" data-duration="0.72" data-track-index="52" data-volume="0.35"></audio>')

    read = bool(spec.get("read"))
    bg = ('<div id="bgp"></div>' if read else
          '<div id="bg"><div class="grid"></div><div class="glow1"></div><div class="glow2"></div></div>')
    person = ('<div id="camcam">' if read else '<div id="ejcam">') + "".join(m for m in media if "<video" in m) + "</div>"
    rep = {"TOTAL": f"{total}", "SPEECH": f"{speech:.3f}", "ENDDUR": f"{END_CARD}", "BG": bg, "PERSON": person, "HOOK": hook,
           "ELEMENTS": "\n".join(els), "AUDIO": "\n".join(m for m in media if "<audio" in m),
           "TIMELINE": "\n".join(js), "READCLS": "read" if read else ""}
    page = TEMPLATE
    for k, v in rep.items():
        page = page.replace("{{" + k + "}}", v)
    open(os.path.join(out, "index.html"), "w").write(page)
    print(f"{spec['slug']}: {total:.1f}s ({speech:.1f}s speech)")


TEMPLATE = open(os.path.join(HERE, "short_template.html")).read()
if __name__ == "__main__":
    import sys
    for s in SHORTS:
        if len(sys.argv) < 2 or sys.argv[1] in s["slug"]:
            build(s)
    json.dump(SW, open(os.path.join(HERE, "shorts_windows.json"), "w"), indent=1)
