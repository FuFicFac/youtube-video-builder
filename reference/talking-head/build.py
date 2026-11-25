"""Generate index.html (main 16:9 edit, an example talking-head video) from the locked EDL + final-edit word timings.

Every cue is anchored to a phrase the presenter actually says (found in edit_words.json, the
Parakeet transcript of the final edited voice), so graphics land on the spoken words.

EXAMPLE DATA: every cue phrase, panel line, name and number below is neutral stand-in copy that shows
the shape of a real edit. Replace all of it (and HOST NAME / CHANNEL NAME / the wordmark) for your video.
"""
import html, json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EDL = json.load(open(os.path.join(HERE, "edl.json")))
WORDS = json.load(open(os.path.join(HERE, "edit_words.json")))  # [w, start, end] in edit time

FPS = 24000 / 1001
SEG = EDL["segments"]
READ_START = READ_END = 1e9  # no reading scene in this video
AROLL_DUR = EDL["duration"]


def norm(w):
    return re.sub(r"[^a-z0-9$]", "", w.lower())


def _find(phrase, near, span):
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


def at(phrase, near, span=9):
    i, _ = _find(phrase, near, span)
    return WORDS[i][1]


def end(phrase, near, span=9):
    i, n = _find(phrase, near, span)
    return WORDS[i + n - 1][2]


# ---- bumper insert -------------------------------------------------------
C = at("I have a course", 75.0) - 0.06   # bumper: after the "...this is <channel name>" handoff, before the first CTA
B = 3.4                                          # bumper length
TAIL = 0.0   # end on the original full-screen shot (end-screen thumbnails go over it)


def T(t):
    return round(t + B if t >= C else t, 3)


TOTAL = round(AROLL_DUR + B + TAIL, 3)

# ---- colours / helpers ---------------------------------------------------
NAVY, PAPER, GREEN, RED, BLUE = "#0a1424", "#f2ecdf", "#39d98a", "#ff5d4f", "#3b7bff"
el_html, js = [], []
uid = [0]


def nid(p):
    uid[0] += 1
    return f"{p}{uid[0]}"


def mark(text):
    """*green* and !red! inline accents -> spans."""
    t = html.escape(text)
    t = re.sub(r"\*(.+?)\*", r'<span class="g">\1</span>', t)
    t = re.sub(r"!(.+?)!", r'<span class="r">\1</span>', t)
    return t


def plain(text):
    return re.sub(r"[*!]", "", text)


ICON = {
    "ok": '<svg class="ic" viewBox="0 0 48 48"><circle cx="24" cy="24" r="21" fill="none" stroke="#39d98a" stroke-width="4"/><path d="M14 25l7 7 13-15" fill="none" stroke="#39d98a" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "ar": '<svg class="ic" viewBox="0 0 48 48"><circle cx="24" cy="24" r="21" fill="none" stroke="#3b7bff" stroke-width="4"/><path d="M13 24h20M26 16l8 8-8 8" fill="none" stroke="#3b7bff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "no": '<svg class="ic" viewBox="0 0 48 48"><circle cx="24" cy="24" r="21" fill="none" stroke="#ff5d4f" stroke-width="4"/><path d="M16 16l16 16M32 16L16 32" stroke="#ff5d4f" stroke-width="5" stroke-linecap="round"/></svg>',
}

# ---- camera track (room vs studio, punch-ins) ----------------------------
STUDIO = []   # (t0, t1, side) side 'L' => presenter on left, panel right


def studio(t0, t1, side, mode):
    STUDIO.append((t0, t1, side, mode))


# ---- BEHIND cues (text between room plate and the presenter) --------------------------
BEHIND = []
ENTR = ["slam", "rise", "wipe", "skew"]


def behind(kicker, beats, t_end):
    BEHIND.append((kicker, beats, t_end))


def split_words(text):
    """'NO !SPYING!' -> [('NO',''),('SPYING','r')] keeping *green* / !red! accents per word."""
    out = []
    for m in re.finditer(r"\*(.+?)\*|!(.+?)!|([^*!]+)", text):
        g, r, p = m.groups()
        cls, seg = ("g", g) if g else (("r", r) if r else ("", p))
        for i, w in enumerate(seg.split()):
            if out and (not re.search(r"[A-Za-z0-9$]", w) or (i == 0 and not seg[:1].isspace() and m.start() > 0
                                                               and not text[m.start() - 1].isspace())):
                out[-1] = (out[-1][0] + w, out[-1][1])
            else:
                out.append((w, cls))
    return out


def halves(words, side_hint):
    """Split a word list into (left, right) balanced by characters; single words take one side."""
    if len(words) == 1:
        return (words, []) if side_hint == 0 else ([], words)
    best = None
    tot = sum(len(w) for w, _ in words)
    for k in range(1, len(words)):
        l = sum(len(w) for w, _ in words[:k])
        d = abs(tot - 2 * l) + (4 if words[k - 1][1] and words[k - 1][1] == words[k][1] else 0)
        if best is None or d < best[0]:
            best = (d, k)
    k = best[1]
    return words[:k], words[k:]


def rows_for(words):
    chars = sum(len(w) for w, _ in words) + len(words) - 1
    if chars <= 20 or len(words) < 3:
        return [words]
    # two rows, balanced by characters
    best = None
    tot = sum(len(w) for w, _ in words)
    for k in range(1, len(words)):
        l = sum(len(w) for w, _ in words[:k])
        d = abs(tot - 2 * l)
        if best is None or d < best[0]:
            best = (d, k)
    return [words[:best[1]], words[best[1]:]]


def span_words(ws):
    return " ".join(f'<span class="{c}">{html.escape(w)}</span>' if c else html.escape(w) for w, c in ws)


def build_behind():
    beat_no = 0
    for n, (kicker, beats, t_end) in enumerate(BEHIND):
        t0 = beats[0][0] - 0.12
        t0s, t1s = T(t0), T(t_end)
        cid = f"bh{n}"
        inner = [f'<div class="kicker" id="{cid}k" data-layout-allow-overlap><span class="kdot"></span>{html.escape(kicker)}</div>']
        beat_parts = []
        for b, (bt, text) in enumerate(beats):
            words = split_words(text)
            rows = rows_for(words)
            nrow = len(rows)
            parts = []
            for r, rw in enumerate(rows):
                L, R = halves(rw, (beat_no + r) % 2)
                grp = f"{cid}b{b}r{r}"
                for side, ws in (("l", L), ("r", R)):
                    if not ws:
                        continue
                    pid = f"{grp}{side}"
                    parts.append((pid, side, r))
                    inner.append(f'<div class="bh bh-{side} rows{nrow} row{r}" id="{pid}" data-fitgroup="{grp}" '
                                 f'data-fit="{html.escape(" ".join(w for w, _ in ws))}" data-fitw="655" data-layout-allow-overlap>{span_words(ws)}</div>')
            beat_parts.append(parts)
            beat_no += 1
        el_html.append(
            f'<div class="clip behind" id="{cid}" data-start="{t0s}" data-duration="{round(t1s - t0s, 3)}" data-track-index="3">'
            + "".join(inner) + "</div>")
        js.append(f'tl.fromTo("#{cid}k",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:.35,ease:"power3.out"}},{t0s});')
        for b, (bt, text) in enumerate(beats):
            s = T(bt) - 0.05
            e = T(beats[b + 1][0]) - 0.05 if b + 1 < len(beats) else t1s
            rise = (n + b) % 3 == 2
            for pid, side, r in beat_parts[b]:
                sel = f"#{pid}"
                sign = -1 if side == "l" else 1
                d = r * 0.08
                if rise:
                    # rises up from behind the shoulders
                    js.append(f'tl.fromTo("{sel}",{{opacity:0,yPercent:70,x:{-sign * 30}}},{{opacity:1,yPercent:0,x:0,duration:.55,ease:"back.out(1.5)"}},{s + d:.3f});')
                else:
                    # slides in from the frame edge toward the presenter
                    js.append(f'tl.fromTo("{sel}",{{opacity:0,x:{sign * 760},skewX:{sign * -14},filter:"blur(10px)"}},'
                              f'{{opacity:1,x:0,skewX:0,filter:"blur(0px)",duration:.55,ease:"expo.out"}},{s + d:.3f});')
                # keeps drifting inward, tucking behind him
                hold = max(.3, e - s - .8)
                js.append(f'tl.to("{sel}",{{x:{-sign * 18},duration:{hold:.2f},ease:"none"}},{s + .55 + d:.3f});')
                js.append(f'tl.to("{sel}",{{opacity:0,x:{-sign * 120},duration:.22,ease:"power2.in"}},{e - .22:.3f});')
        js.append(f'tl.to("#{cid}k",{{opacity:0,duration:.2}},{t1s - .22:.3f});')
        js.append(f'tl.to("#scrim",{{opacity:.6,duration:.3,ease:"power2.out"}},{t0s:.3f});')
        js.append(f'tl.to("#scrim",{{opacity:0,duration:.3,ease:"power2.in"}},{t1s - .3:.3f});')


# ---- STUDIO panels -----------------------------------------------------------
PANELS = []


def panel(side, t0, t1, pages, mode=None):
    """pages: list of (t_page, title, items); items: (t, kind, text[, extra])"""
    if mode is None:   # alternate: presenter cut-out sliding aside <-> rounded head-and-shoulders card
        mode = "cut" if len(PANELS) % 2 == 0 else "card"
    studio(t0, t1, side, mode)
    PANELS.append((side, t0, t1, pages))


def build_panels():
    for n, (side, t0, t1, pages) in enumerate(PANELS):
        pid = f"pn{n}"
        t0s, t1s = T(t0), T(t1)
        cls = "right" if side == "L" else "left"
        parts = []
        for p, (tp, title, items) in enumerate(pages):
            pg = f"{pid}p{p}"
            rows = []
            for i, it in enumerate(items):
                ti, kind, text = it[0], it[1], it[2]
                iid = f"{pg}i{i}"
                if kind in ("ok", "no", "row2"):
                    ic = ICON["ar" if kind == "row2" else kind]
                    rows.append(f'<div class="row {kind}" id="{iid}">{ic}<span>{mark(text)}</span></div>')
                elif kind == "chip":
                    rows.append(f'<div class="chip" id="{iid}">{mark(text)}</div>')
                elif kind == "note":
                    rows.append(f'<div class="note" id="{iid}">{mark(text)}</div>')
                elif kind == "stamp":
                    col = it[3] if len(it) > 3 else "red"
                    rows.append(f'<div class="stamp {col}" id="{iid}">{mark(text)}</div>')
                elif kind == "hero":
                    rows.append(f'<div class="hero" id="{iid}" data-fit="{html.escape(plain(text))}" data-fitw="1010">{mark(text)}</div>')
                elif kind == "step":
                    rows.append(f'<div class="step" id="{iid}"><b>{html.escape(it[3])}</b><span>{mark(text)}</span></div>')
                elif kind == "link":
                    rows.append(f'<div class="linkcta" id="{iid}"><div class="pill">{mark(text)}</div>'
                                '<div class="chev"><i></i><i></i><i></i></div></div>')
                elif kind == "meter":
                    rows.append(f'<div class="meter" id="{iid}"><div class="mlabel">{mark(text)}</div>'
                                f'<div class="mtrack"><div class="mfill" id="{iid}f"></div></div></div>')
                elif kind == "ba":
                    rows.append(f'<div class="ba" id="{iid}"><div class="bcard" id="{iid}a"><small>BEFORE</small>'
                                f'<span>{mark(text)}</span></div><div class="barrow" id="{iid}x">→</div>'

                                f'<div class="bcard after" id="{iid}b"><small>AFTER</small><span>{mark(it[3])}</span></div></div>')
                elif kind == "slot":
                    rows.append(f'<div class="slot" id="{iid}"><small>WATCH NEXT</small><div class="slotbig">{mark(text)}</div>'
                                f'<div class="slotsub" id="{iid}s">{mark(it[3])}</div></div>')
                elif kind == "big":
                    rows.append(f'<div class="big" id="{iid}"><b id="{iid}n">{html.escape(it[3])}</b><span>{mark(text)}</span></div>')
                elif kind == "bars":
                    rows.append(f'<div class="bar" id="{iid}"><div class="blabel">{mark(text)}</div><div class="btrack"><div class="bfill" id="{iid}f" style="width:{it[3]}%"></div></div>'
                                f'<div class="bpct" id="{iid}p">{it[3]}%</div></div>')
                elif kind == "shot":
                    rows.append(f'<div class="shot" id="{iid}"><div class="shotin" id="{iid}z"><img src="assets/research/{text}" alt=""></div></div>'
                                f'<div class="srcl" id="{iid}c">{html.escape(it[4])}</div>')
                elif kind == "out3":
                    rows.append(f'<div class="o3" id="{iid}"><b>{html.escape(text)}</b><i>→</i><span>{mark(it[3])}</span></div>')
                elif kind == "quote":
                    rows.append(f'<div class="quote" id="{iid}"><div class="qt">{mark(text)}</div><div class="qdest {it[4]}" id="{iid}d">→ {mark(it[3])}</div></div>')
                elif kind == "side":
                    rows.append(f'<div class="ba" id="{iid}"><div class="bcard" id="{iid}a"><small>SOURCE CONVERSATION</small>'
                                f'<span>{mark(text)}</span></div><div class="barrow" id="{iid}x">⇄</div>'
                                f'<div class="bcard after" id="{iid}b"><small>SUGGESTION</small><span>{mark(it[3])}</span></div></div>')
                elif kind == "src":
                    rows.append(f'<div class="srcl" id="{iid}">{html.escape(text)}</div>')
                elif kind == "folders":
                    tiles = "".join(f'<div class="ftile" id="{iid}t{k}"><div class="ftab"></div><span>{html.escape(fn)}</span></div>' for k, fn in enumerate(it[3]))
                    rows.append(f'<div class="fold" id="{iid}"><div class="fnote" id="{iid}n"><small>NOTE</small>{mark(text)}</div><div class="frow">{tiles}</div></div>')
            title_html = f'<div class="ptitle" id="{pg}t" data-fit="{html.escape(plain(title))}" data-fitw="1010">{mark(title)}</div>' if title else ""
            parts.append(f'<div class="page" id="{pg}"><div class="prule" id="{pg}r"></div>{title_html}<div class="rows">{"".join(rows)}</div></div>')
        el_html.append(f'<div class="clip panel {cls}" id="{pid}" data-start="{t0s}" data-duration="{round(t1s - t0s, 3)}" data-track-index="5">{"".join(parts)}</div>')

        for p, (tp, title, items) in enumerate(pages):
            pg = f"{pid}p{p}"
            ps = max(T(tp) - 0.1, t0s + 0.25) if p == 0 else T(tp) - 0.1
            pe = T(pages[p + 1][0]) - 0.1 if p + 1 < len(pages) else t1s
            dx = 60 if side == "L" else -60
            js.append(f'tl.fromTo("#{pg}",{{opacity:0,x:{dx}}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{ps:.3f});')
            js.append(f'tl.fromTo("#{pg}r",{{scaleX:0}},{{scaleX:1,duration:.6,ease:"expo.out"}},{ps + .05:.3f});')
            if title:
                js.append(f'tl.fromTo("#{pg}t",{{opacity:0,yPercent:60}},{{opacity:1,yPercent:0,duration:.5,ease:"back.out(1.4)"}},{ps + .08:.3f});')
            for i, it in enumerate(items):
                ti, kind = T(it[0]) - 0.06, it[1]
                ti = max(ti, ps + 0.15)
                iid = f"#{pg}i{i}"
                if kind == "stamp":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,scale:2.2,rotation:-14}},{{opacity:1,scale:1,rotation:-4,duration:.32,ease:"back.out(2.2)"}},{ti:.3f});')
                elif kind == "hero":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,scale:1.25,filter:"blur(10px)"}},{{opacity:1,scale:1,filter:"blur(0px)",duration:.45,ease:"expo.out"}},{ti:.3f});')
                elif kind == "chip":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,scale:.6,y:30}},{{opacity:1,scale:1,y:0,duration:.38,ease:"back.out(2)"}},{ti:.3f});')
                elif kind == "link":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,y:80,scale:.8}},{{opacity:1,y:0,scale:1,duration:.5,ease:"back.out(1.8)"}},{ti:.3f});')
                    dur = pe - ti - 0.6
                    reps = max(0, int(dur / 0.7) - 1)
                    js.append(f'tl.fromTo("{iid} .chev",{{y:0}},{{y:34,duration:.35,ease:"power2.in",yoyo:true,repeat:{reps * 2 + 1}}},{ti + .5:.3f});')
                    js.append(f'tl.fromTo("{iid} .pill",{{scale:1}},{{scale:1.06,duration:.35,ease:"sine.inOut",yoyo:true,repeat:{reps * 2 + 1}}},{ti + .5:.3f});')
                elif kind == "meter":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,x:40}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}f",{{scaleX:0}},{{scaleX:.92,duration:1.6,ease:"power4.out"}},{ti + .25:.3f});')
                elif kind == "ba":
                    js.append(f'tl.fromTo("{iid}a",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}x",{{opacity:0,scale:.3}},{{opacity:1,scale:1,duration:.35,ease:"back.out(2)"}},{ti + .6:.3f});')
                    js.append(f'tl.fromTo("{iid}b",{{opacity:0,x:40}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{T(it[4]) - .06 if len(it) > 4 else ti + 1.1:.3f});')
                elif kind == "slot":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,scale:.85}},{{opacity:1,scale:1,duration:.5,ease:"back.out(1.6)"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}s",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.4,ease:"power3.out"}},{T(it[4]) - .06:.3f});')
                elif kind == "big":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,x:{dx}}},{{opacity:1,x:0,duration:.35,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}n",{{scale:1.8,filter:"blur(8px)"}},{{scale:1,filter:"blur(0px)",duration:.45,ease:"expo.out"}},{ti:.3f});')
                elif kind == "bars":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,x:40}},{{opacity:1,x:0,duration:.35,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}f",{{scaleX:0}},{{scaleX:1,duration:1.1,ease:"power4.out"}},{ti + .15:.3f});')
                    js.append(f'tl.fromTo("{iid}p",{{opacity:0}},{{opacity:1,duration:.3}},{ti + .6:.3f});')
                elif kind == "shot":
                    rx, ry, rw, rh = it[3]
                    k = 1000 / 1600
                    Z = min(1000 / (rw * k), 560 / (rh * k))
                    zx = -rx * k * Z + (1000 - rw * k * Z) / 2
                    zy = -ry * k * Z + (560 - rh * k * Z) / 2
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,y:40,scale:.94}},{{opacity:1,y:0,scale:1,duration:.5,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}c",{{opacity:0}},{{opacity:1,duration:.4}},{ti + .3:.3f});')
                    js.append(f'tl.fromTo("{iid}z",{{x:0,y:0,scale:1}},{{x:{zx:.1f},y:{zy:.1f},scale:{Z:.3f},duration:1.4,ease:"power3.inOut"}},{ti + .9:.3f});')
                elif kind == "quote":
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,x:{dx},rotation:-1.5}},{{opacity:1,x:0,rotation:0,duration:.45,ease:"back.out(1.6)"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}d",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.35,ease:"power3.out"}},{T(it[5]) - .06:.3f});')
                elif kind == "side":
                    js.append(f'tl.fromTo("{iid}a",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{ti:.3f});')
                    js.append(f'tl.fromTo("{iid}x",{{opacity:0,scale:.3}},{{opacity:1,scale:1,duration:.35,ease:"back.out(2)"}},{ti + .5:.3f});')
                    js.append(f'tl.fromTo("{iid}b",{{opacity:0,x:40}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{T(it[4]) - .06 if len(it) > 4 else ti + 0.9:.3f});')
                elif kind == "folders":
                    tf, tm, tgt = T(it[4]) - .06, T(it[5]) - .06, it[6]
                    js.append(f'tl.fromTo("{iid}n",{{opacity:0,y:-40,rotation:-3}},{{opacity:1,y:0,rotation:0,duration:.5,ease:"back.out(1.6)"}},{ti:.3f});')
                    js.append(f'tl.fromTo("#{pg} .ftile",{{opacity:0,y:50}},{{opacity:1,y:0,duration:.4,stagger:.12,ease:"back.out(1.8)"}},{tf:.3f});')
                    js.append(f'tl.to("{iid}n",{{x:{(tgt - 1) * 330},y:330,scale:.34,opacity:.0,duration:.8,ease:"power3.inOut"}},{tm:.3f});')
                    js.append(f'tl.to("{iid}t{tgt}",{{borderColor:"#39d98a",backgroundColor:"rgba(57,217,138,0.22)",scale:1.08,duration:.35,ease:"back.out(2)"}},{tm + .6:.3f});')
                    for k2 in range(len(it[3])):
                        if k2 != tgt:
                            js.append(f'tl.to("{iid}t{k2}",{{opacity:.3,duration:.4}},{tm + .6:.3f});')
                else:
                    js.append(f'tl.fromTo("{iid}",{{opacity:0,x:{dx}}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{ti:.3f});')
            if p + 1 < len(pages):
                js.append(f'tl.to("#{pg}",{{opacity:0,x:{-dx},duration:.25,ease:"power2.in"}},{pe - .25:.3f});')
        js.append(f'tl.to("#{pid} .page",{{opacity:0,duration:.25,ease:"power2.in"}},{t1s - .28:.3f});')

# =====================================================================
#                               CUES
# =====================================================================
# face track (Apple Vision, 2 fps on source) -> edit-time face centre, for card crops + callout sides
_FT = []
for line in open(os.path.join(HERE, "face", "track.txt")):
    p = line.split()
    if len(p) == 5:
        _FT.append(((int(p[0][:5]) - 1) / 2.0, float(p[1])))
_FB = {}   # face box per sample: (cx, cy, w, h) normalised
for line in open(os.path.join(HERE, "face", "track.txt")):
    p = line.split()
    if len(p) == 5:
        _FB[(int(p[0][:5]) - 1) / 2.0] = tuple(map(float, p[1:]))


def _to_edit(ts):
    for sg in SEG:
        if sg["src_in"] <= ts < sg["src_out"]:
            return sg["edit_in"] + ts - sg["src_in"]


FACE = sorted((e, cx) for e, cx in ((_to_edit(t), cx) for t, cx in _FT) if e is not None)


def face_box(t0, t1):
    """union of his face boxes over [t0,t1] edit time, in screen px (1.03 crop zoom + worst-case 1.08 punch-in about 50%/30%)."""
    bx = [_FB[t] for t in _FB if (lambda e: e is not None and t0 - 0.5 <= e <= t1 + 0.5)(_to_edit(t))] or [(0.5, 0.35, 0.2, 0.35)]
    def scr(x, y):
        X, Y = x * 1920 * ZOOM, y * 1080 * ZOOM
        return 960 + (X - 960) * 1.08, 324 + (Y - 324) * 1.08
    l = min(scr(cx - w / 2, cy)[0] for cx, cy, w, h in bx); r = max(scr(cx + w / 2, cy)[0] for cx, cy, w, h in bx)
    bot = max(scr(cx, cy + h / 2 * 1.25)[1] for cx, cy, w, h in bx)   # +25%: chin/beard below the detector box
    return l, r, bot


def face_span(t0, t1):
    xs = [cx for e, cx in FACE if t0 <= e <= t1] or [0.5]
    return min(xs), max(xs), sorted(xs)[len(xs) // 2]


ZOOM = 1.03  # plate is scaled 1.03 from top-left to hide the source's black right/bottom border

# ---- foreground callouts (over the original footage, no mask) ----
CALLOUTS = []


def callout(t0, t1, items, style="stack", side=None):
    """items: [(t, text)]. style: stack (chips on the free side), lower (big lower-third box), chapter, quote."""
    CALLOUTS.append((t0, t1, items, style, side))


def build_callouts():
    for n, (t0, t1, items, style, side) in enumerate(CALLOUTS):
        cid = f"co{n}"
        l, r, bot = face_box(t0, t1)
        if side is None:
            side = "R" if (1920 - r) > l else "L"
        extra = ""
        if style == "stack":
            # chips live BELOW his chin, on the roomier side, sized to fit (never over his face)
            avail_h = 1080 - 60 - (bot + 30)
            fs = int(max(64, min(110, avail_h / (len(items) * 1.32))))
            extra = f' style="--fs:{fs}px;padding-bottom:60px"'
        rows = []
        for i, (t, text) in enumerate(items):
            fit = f' data-fit="{html.escape(plain(text))}" data-fitw="1100"' if style == "stack" else ""
            rows.append(f'<div class="cchip" id="{cid}i{i}"{fit}>{mark(text)}</div>')
        el_html.append(f'<div class="clip callout {style} side{side}" id="{cid}" data-start="{T(t0):.3f}" data-duration="{T(t1) - T(t0):.3f}" '
                       f'data-track-index="6"{extra}>{"".join(rows)}</div>')
        CO_META.append({"id": cid, "style": style, "side": side, "t0": T(t0), "t1": T(t1), "face": [round(l), round(r), round(bot)]})
        dx = -80 if side == "L" else 80
        for i, (t, text) in enumerate(items):
            ti = max(T(t) - 0.06, T(t0) + 0.02)
            if style in ("lower", "chapter", "quote"):
                js.append(f'tl.fromTo("#{cid}i{i}",{{opacity:0,y:60,clipPath:"inset(0% 100% 0% 0%)"}},{{opacity:1,y:0,clipPath:"inset(0% 0% 0% 0%)",duration:.55,ease:"expo.out"}},{ti:.3f});')
            else:
                js.append(f'tl.fromTo("#{cid}i{i}",{{opacity:0,x:{dx},scale:.8}},{{opacity:1,x:0,scale:1,duration:.4,ease:"back.out(1.8)"}},{ti:.3f});')
        js.append(f'tl.to("#{cid} .cchip",{{opacity:0,y:-20,duration:.25,stagger:.04,ease:"power2.in"}},{T(t1) - .3:.3f});')


CO_META = []


T_WELCOME = at("welcome", 2.5)
# the splash wordmark lands on the spoken channel name: anchor each part to its word
SPLASH_IN, SPLASH_OUT = T_WELCOME - 0.35, end("Channel.", 4.0) + 0.9
T_LOGO_B, T_LOGO_C = at("TV Channel.", 3.2), at("Channel.", 4.0)
LOGO = ("YOUR", "TV", "CHANNEL")   # PLACEHOLDER three-part wordmark: replace with your channel name
EXAMPLE = "ILLUSTRATIVE EXAMPLE · NOT A LIVE TEST"
PROPOSED = "PROPOSED WORKFLOW · AN EXPERIMENT"

# ---- cold open / hook ----
behind("HOW MANY GOOD IDEAS HAVE YOU ALREADY HAD WITH AI…",
       [(at("good ideas", 6.5), "GOOD *IDEAS*"),
        (at("couldn't find again", 11.0), "!COULDN'T FIND! AGAIN")],
       at("How many?", 15.7))
callout(at("I'm talking about", 16.8), at("You didn't lose", 30.1),
        [(at("a story problem", 21.0), "A *STORY* PROBLEM"), (at("a business idea that", 22.0), "A *BUSINESS* IDEA"),
         (at("the little change", 25.4), "THE *LITTLE CHANGE* THAT MADE IT WORK")])
behind("YOU DIDN'T LOSE THE CONVERSATION",
       [(at("It's still sitting", 31.9), "IT'S *STILL THERE*"),
        (at("what was valuable", 34.5), "*WHAT WAS VALUABLE*")],
       at("I've been building", 39.9))
callout(at("I've been building", 39.9), at("Now I've found", 45.1),
        [(at("a notes system", 41.0), "BUILDING A *NOTES SYSTEM*")], style="lower")
behind("NOW I'VE FOUND SOMETHING CALLED…",
       [(at("called Sorter", 46.0), "*SORTER*")],
       at("What if a small", 52.3))
panel("R", at("What if a small", 52.3), at("That is the biggest", 65.8), [
    (at("What if a small", 52.3), "A DIFFERENT QUESTION", [
        (at("What if a small", 52.3), "note", "WHAT IF AN INEXPENSIVE, *FOCUSED* AI HELPED DECIDE…"),
        (at("already has a home", 58.0), "ok", "WHICH IDEAS *HAVE A HOME*"),
        (at("worth leaving behind", 63.0), "no", "WHICH ARE WORTH LEAVING")])])

# ---- bumper, then CTA ----
panel("L", C + 0.01, at("Alright. I want to make", 97.6), [
    (C + 0.01, "", [
        (at("I have a course", 75.0), "note", "MY COURSE"),
        (at("the course name", 76.5), "hero", "COURSE *NAME*"),
        (at("links in the description", 79.0), "link", "LINK IN THE DESCRIPTION")]),
    (at("Second, if you", 86.7), "", [
        (at("new here", 88.0), "note", "A SECOND OFFER · *ONE LINE*"),
        (at("second offer name", 95.0), "hero", "SECOND *OFFER*"),
        (at("link in the description", 96.0), "link", "LINK IN THE DESCRIPTION")])])

# ---- what this video is ----
callout(at("I want to make Sorter", 98.8), at("That's kind of the whole", 103.2),
        [(at("I want to make Sorter", 98.8), "MAKE *SORTER* UNDERSTANDABLE")], style="lower")
panel("R", at("And in this video", 114.8), at("So let's get into it", 133.8), [
    (at("And in this video", 114.8), "IN THIS VIDEO", [
        (at("what Sorter actually does", 116.0), "step", "WHAT SORTER *ACTUALLY DOES*", "01"),
        (at("help organize the ideas", 118.5), "step", "ORGANIZE *BURIED IDEAS*", "02"),
        (at("how to test whether", 123.5), "step", "HOW TO *TEST* ITS DECISIONS", "03"),
        (at("need to be a programmer", 130.5), "stamp", "NO CODING NEEDED", "green")])])
callout(at("Let's talk about my notes", 135.6), at("Alright, let's start", 141.1),
        [(at("Let's talk about my notes", 135.6), "PART 1 · *MY NOTES ON SORTER*")], style="chapter")

# ---- B1 folders (illustrative) ----
panel("L", at("Alright, let's start", 141.1), at("That's the kind of job", 181.5), [
    (at("Alright, let's start", 141.1), "READ A NOTE. *PICK A FOLDER.*", [
        (at("a note that says", 153.5), "folders", "“Next time I record a tutorial, turn the best explanations into a *short*.”",
         ["STORY IDEAS", "VIDEO PRODUCTION", "TRAVEL PLANS"], at("three folders", 164.0), at("put that note in video production", 171.5), 1),
        (at("a note that says", 153.5), "src", EXAMPLE)])])

# ---- B2 how Sorter works + three output types ----
panel("L", at("That's the kind of job", 181.5), at("they're not even infallible", 214.8), [
    (at("That's the kind of job", 181.5), "WHAT SORTER IS *BUILT FOR*", [
        (at("give it some text", 186.5), "step", "SOME *TEXT*", "01"),
        (at("explain the decision", 188.0), "step", "THE *DECISION* WE NEED", "02"),
        (at("define the possible answers", 191.0), "step", "THE *POSSIBLE ANSWERS*", "03"),
        (at("it returns a decision", 196.2), "hero", "→ A DECISION + *NUMBERS*")]),
    (at("It can choose a category", 203.0), "THREE KINDS OF *ANSWERS*", [
        (at("choose a category", 204.0), "out3", "CHOICE", "PICKS A *CATEGORY*"),
        (at("judge whether a statement", 206.0), "out3", "LIKELIHOOD", "HOW LIKELY IT'S *TRUE*"),
        (at("score something against", 209.5), "out3", "SCORE", "A POSITION ON *YOUR SCALE*"),
        (at("choose a category", 204.0), "src", "SOURCE · docs.example.com · Choice / Likelihood / Score")])])

# ---- B3 uncertainty bars (official doc example) ----
panel("R", at("they're not even infallible", 214.8), at("Here's where I initially", 241.0), [
    (at("they're not even infallible", 214.8), "NOT *INFALLIBLE*", [
        (at("they're not even infallible", 215.0), "big", "RETURNS", "61%"),
        (at("because this is information", 216.5), "big", "BILLING", "35%"),
        (at("getting parsed", 217.8), "big", "SHIPPING", "4%"),
        (at("They're information our", 219.2), "note", "CONFIDENCE *0.42* = HOW SPREAD OUT THE ANSWER IS"),
        (at("They're information our", 219.2), "src", "VENDOR DOCUMENTATION EXAMPLE · SUPPORT TICKET · NOT A LIVE TEST")]),
    (at("to decide whether to accept", 224.0), "SOFTWARE DECIDES", [
        (at("accept an answer", 226.0), "ok", "CLEAR? *ACCEPT IT*"),
        (at("ask somebody to look", 227.5), "row2", "UNSURE? *ASK A PERSON*"),
        (at("smart model for certain", 238.0), "hero", "SMART FOR *CERTAIN THINGS*")])])

# ---- tangled up ----
callout(at("Here's where I initially", 241.0), at("Well, for that folder", 254.3),
        [(at("Here's where I initially", 241.0), "WHERE I GOT *TANGLED UP*"),
         (at("ask another AI model", 248.5), "DOES ANOTHER MODEL *DO THE THINKING*?")])
behind("FOR THAT FOLDER DECISION…",
       [(at("makes the judgment itself", 259.0), "SORTER MAKES *THE CALL*")],
       at("But picking a folder", 261.8))

# ---- B4 division of labour ----
panel("R", at("But picking a folder", 261.8), at("One clarification matters", 288.2), [
    (at("But picking a folder", 261.8), "TWO DIFFERENT *JOBS*", [
        (at("So Sorter can help", 269.0), "out3", "SORTER", "PICKS *THE FOLDER*"),
        (at("a writing model is gonna", 271.0), "out3", "WRITING MODEL", "WRITES *THE PAGE*"),
        (at("the regular software", 278.0), "out3", "SOFTWARE", "OPENS · LINKS · *SAVES*")])])

# ---- B4b clarification: zoom into an official doc capture ----
panel("L", at("One clarification matters", 288.2), at("my ideas, they don't", 319.9), [
    (at("One clarification matters", 288.2), "ONE *CLARIFICATION*", [
        (at("the vendor describes a training", 297.5), "shot", "primer-capture.png", (416, 360, 776, 330),
         "SOURCE · docs.example.com · primer page — one-line description of the capture")]),
    (at("The useful distinction", 309.0), "WHAT IT *RETURNS*", [
        (at("choices and scores", 314.0), "ok", "*CHOICES* & *SCORES*"),
        (at("newly written paragraph", 316.5), "no", "A NEWLY WRITTEN PARAGRAPH")])])

# ---- where ideas live ----
callout(at("my ideas, they don't", 319.9), at("that means collecting", 342.3),
        [(at("Claude sessions", 325.0), "*CLAUDE*"), (at("codec sessions", 327.0), "*CODEX*"),
         (at("another agent", 331.5), "*AGENTS*"), (at("in Grok", 332.5), "*GROK*"), (at("even OpenClaw", 334.5), "*OPENCLAW*"),
         (at("Some are notes", 336.9), "NOTES · *THE ARCHIVE*")], style="stackside")
panel("R", at("that means collecting", 342.3), at("Take the discussion", 363.3), [
    (at("that means collecting", 342.3), "COLLECTING IS *ONLY PART*", [
        (at("already captured", 349.5), "ok", "WHAT'S *ALREADY CAPTURED*"),
        (at("what's in my notes", 353.0), "ok", "WHAT'S *IN MY NOTES*"),
        (at("What's changed", 355.0), "ok", "WHAT'S *CHANGED*"),
        (at("still sitting in a conversation", 357.0), "row2", "WHAT'S STILL *IN A CONVERSATION*")])])
panel("L", at("Take the discussion", 363.3), at("That's the gap", 400.1), [
    (at("Take the discussion", 363.3), "EXAMPLE: *YOUTUBE TITLES*", [
        (at("played off of the thumbnail", 372.5), "note", "TITLES THAT *PLAY OFF THE THUMBNAIL*"),
        (at("finding that conversation", 379.0), "ok", "FOUND THE CONVERSATION"),
        (at("Did that decision ever", 384.1), "hero", "DID IT REACH *MY AGENTS*?"),
        (at("agents.md file", 393.0), "step", "AGENTS.MD → *SKILL FOLDER*", "↳")])])
behind("THAT'S THE GAP I'M INTERESTED IN",
       [(at("a good decision", 405.0), "A GOOD *DECISION*"),
        (at("Without that decision", 407.5), "!NOT IN! THE SYSTEM")],
       at("Alright. Here is how", 415.1))

# ---- B5 proposed workflow ----
panel("R", at("Here is how I would", 416.3), at("I mean, what's going on", 454.3), [
    (at("Here is how I would", 416.3), "PUTTING IT *TOGETHER*", [
        (at("reads a new conversation", 421.5), "step", "READ A *NEW CONVERSATION*", "01"),
        (at("breaks it into useful", 423.5), "step", "BREAK IT INTO *SECTIONS*", "02"),
        (at("search finds existing", 427.0), "step", "SEARCH FINDS *RELATED NOTES*", "03"),
        (at("Sorter gets a manageable", 431.0), "step", "SORTER *COMPARES* THEM", "04"),
        (at("Here is how I would", 416.3), "src", PROPOSED)]),
    (at("We ask", 441.0), "SORTER ASKS", [
        (at("already covered", 442.0), "chip", "ALREADY *COVERED*?"),
        (at("add something to an existing", 444.5), "chip", "ADDS TO *A PAGE*?"),
        (at("need a new page", 449.0), "chip", "NEEDS *A NEW PAGE*?"),
        (at("particularly unclear", 451.5), "chip", "*UNCLEAR*?")])])
panel("L", at("Think of the search", 460.5), at("If the new note belongs", 474.4), [
    (at("Think of the search", 460.5), "BOOKS TO *THE DESK*", [
        (at("bringing books to the desk", 462.5), "ok", "SEARCH *BRINGS THE BOOKS*"),
        (at("Sorter helps compare", 465.5), "ok", "SORTER *COMPARES THE DESK*"),
        (at("entire library", 471.0), "no", "THE WHOLE LIBRARY"),
        (at("Think of the search", 460.5), "src", PROPOSED)])])
panel("R", at("If the new note belongs", 474.4), at("I want to see what", 501.9), [
    (at("If the new note belongs", 474.4), "THEN…", [
        (at("propose that connection", 480.0), "step", "PROPOSE *THE CONNECTION*", "01"),
        (at("prepare those drafts", 487.5), "step", "WRITING MODEL *DRAFTS*", "02"),
        (at("review the suggestion", 491.5), "step", "I *REVIEW* IT", "03"),
        (at("follow the link back", 493.5), "step", "LINK BACK TO *THE SOURCE*", "04"),
        (at("That source link matters", 497.4), "stamp", "SOURCE LINK MATTERS", "green")])])
callout(at("I want to see what", 501.9), at("There's another decision", 511.5),
        [(at("I want to see what", 501.9), "WHAT I *ACTUALLY SAID*"),
         (at("not just what a model", 505.0), "NOT WHAT A MODEL *THOUGHT I MEANT*")], style="quote")

# ---- B6 possibility vs decision ----
panel("L", at("There's another decision", 511.5), at("we still have to test", 556.8), [
    (at("There's another decision", 511.5), "POSSIBILITY OR *DECISION*?", [
        (at("What if we tried", 517.5), "quote", "“What if we tried this?”", "IDEAS", "g", at("I'm exploring", 520.5)),
        (at("haven't changed the rules", 529.0), "quote", "A NEW RULE FOR *EVERY PROJECT*", "REVIEW FIRST", "b", at("distinguish a possibility", 534.0)),
        (at("There's another decision", 511.5), "src", "ILLUSTRATIVE WORDING")]),
    (at("And if two notes disagree", 539.3), "TWO NOTES *DISAGREE*", [
        (at("surface that disagreement", 546.0), "hero", "*SURFACE IT*"),
        (at("not quickly pick", 548.0), "no", "PICK THE MORE CONFIDENT ONE"),
        (at("Sorter could help flag", 552.0), "stamp", "FLAG IT", "green")])])

# ---- B7 review list ----
panel("R", at("we still have to test", 556.8), at("Let me show you what", 593.3), [
    (at("we still have to test", 556.8), "A FIRST VERSION", [
        (at("we still have to test", 556.8), "note", "STILL TO TEST: *USEFUL ON THIS MATERIAL?*"),
        (at("already captured, suggested", 566.0), "chip", "ALREADY *CAPTURED*"),
        (at("suggested edition", 567.5), "chip", "SUGGESTED *ADDITION*"),
        (at("possible new page", 569.0), "chip", "POSSIBLE *NEW PAGE*"),
        (at("needs a closer look.", 571.0), "chip", "NEEDS A *CLOSER LOOK*")]),
    (at("That's enough to test", 579.6), "", [
        (at("without turning every passing", 582.0), "note", "NOT EVERY PASSING THOUGHT → *A PERMANENT RULE*"),
        (at("do it cheap", 591.0), "stamp", "AND DO IT CHEAP", "green")])])

# ---- B7b evaluate one conversation ----
panel("L", at("Let me show you what", 593.3), at("And this model really", 628.3), [
    (at("Let me show you what", 593.3), "ONE CONVERSATION · *THREE THINGS*", [
        (at("already knows about", 600.5), "ok", "WHAT IT *ALREADY KNOWS*"),
        (at("genuinely missed", 603.0), "ok", "WHAT WE *GENUINELY MISSED*"),
        (at("where it gets confused", 605.0), "row2", "WHERE IT *GETS CONFUSED*")]),
    (at("I want to keep a source", 606.0), "JUDGE IT, *DON'T ADMIRE IT*", [
        (at("keep a source conversation", 607.5), "side", "WHAT I *SAID*", "WHAT IT *SUGGESTS*", at("beside the suggestions", 609.5)),
        (at("tangible evidence", 621.0), "note", "*TANGIBLE EVIDENCE*, FAST"),
        (at("I want to keep a source", 606.0), "src", "REVIEW STATES: CAPTURED · ADDITION · NEW PAGE · NEEDS REVIEW")])])

# ---- B8 cost ----
callout(at("The part that I love", 630.7), at("At the published direct", 641.5),
        [(at("the cheap part", 634.0), "THE *CHEAP* PART")], style="lower")
behind("PUBLISHED DIRECT RATE · docs.example.com/models · CHECKED <DATE>",
       [(at("four point two cents per million", 643.5), "*4.2¢* / MILLION"),
        (at("input tokens are the little", 651.5), "TOKENS = *TEXT*"),
        (at("partly a language model", 657.0), "PARTLY *AN LLM*")],
       at("for a simple example", 660.0))
panel("R", at("for a simple example", 660.0), at("the result I care about", 700.5), [
    (at("for a simple example", 660.0), "THE MATH", [
        (at("a thousand requests", 661.5), "note", "1,000 REQUESTS × *1,000* INPUT TOKENS"),
        (at("one million tokens", 667.0), "note", "= *1,000,000* INPUT TOKENS"),
        (at("Sorter portion would be", 669.5), "hero", "SORTER: *4.2¢*"),
        (at("for a simple example", 660.0), "src", "ILLUSTRATIVE SORTER-ONLY CALCULATION · NOT MY MEASURED COST")]),
    (at("longer notes repeated", 679.0), "WHAT *ADDS UP*", [
        (at("longer notes", 679.0), "chip", "LONGER *NOTES*"),
        (at("repeated checks", 680.0), "chip", "REPEATED *CHECKS*"),
        (at("search your transcriptions", 689.0), "chip", "SEARCH · *TRANSCRIPTION*"),
        (at("your storage", 690.5), "chip", "*STORAGE*"),
        (at("any writing model", 693.0), "chip", "ANY *WRITING MODEL*")])])

# ---- the result ----
behind("THE RESULT I CARE ABOUT IS PRETTY SIMPLE",
       [(at("less time managing", 704.0), "LESS *MANAGING*"),
        (at("more time using", 706.5), "MORE *USING*")],
       at("Finding something I forgot", 714.0))
callout(at("Finding something I forgot", 714.0), at("I mean, these are", 733.0),
        [(at("Finding something I forgot", 714.0), "FIND *WHAT I FORGOT*"),
         (at("Catching a decision", 720.5), "CATCH *A MISSED DECISION*"),
         (at("Knowing where to leave", 726.5), "KNOW WHAT *TO LEAVE ALONE*")])

# ---- try it ----
panel("L", at("I want you to start", 739.5), at("If you're building systems", 758.5), [
    (at("I want you to start", 739.5), "TRY IT *YOURSELF*", [
        (at("start with one conversation", 740.5), "step", "START WITH *ONE CONVERSATION*", "01"),
        (at("check the suggestions", 742.5), "step", "CHECK *THE SUGGESTIONS*", "02"),
        (at("see what it missed", 744.0), "step", "SEE *WHAT IT MISSED*", "03"),
        (at("then decide whether", 745.5), "step", "THEN DECIDE: *A BIGGER JOB?*", "04"),
        (at("the next one", 751.0), "note", "NEXT TOPIC — *VIDEO SOON*")])])

# ---- CTA ----
panel("R", at("If you're building systems", 758.5), at("do me a favor", 796.0), [
    (at("If you're building systems", 758.5), "COME *JOIN ME*", [
        (at("come join me", 761.0), "hero", "COURSE *NAME*"),
        (at("The link is in the", 766.0), "link", "LINK IN THE DESCRIPTION")]),
    (at("Multiple levels", 773.5), "MULTIPLE *LEVELS*", [
        (at("a few dollars a month", 781.5), "hero", "*$X* / MONTH"),
        (at("supports the channel", 782.5), "note", "SUPPORTS *THE CHANNEL*"),
        (at("like I said, is in", 792.5), "link", "LINK IN THE DESCRIPTION")])])
callout(at("do me a favor", 796.0), at("Alright here is a video", 813.5),
        [(at("in the comments", 797.0), "COMMENT: *YOUR BEST LOST IDEA*")], style="lower")

# ---- outro: original full-screen shot, title box bottom-left under his pointing hand ----
T_OUT = at("Alright here is a video", 813.5)
T_TITLE = at("right here is a video", 818.5)
NEXT_TITLE = "Title Of Your Next Video. It Goes Here."

build_behind()
build_panels()
build_callouts()

# ---- camera: full frame (punch-ins at cuts) <-> rounded head-and-shoulders card beside panels ----
STUDIO.sort()
CARD_W, CARD_TOP, CARD_S, CARD_M = 780, 30, 0.84, 70     # card crop (plate px), scale, screen margin
CARD_H = 1080 - CARD_TOP


def in_studio(t):
    for a, b, side, mode in STUDIO:
        if a - 0.6 <= t < b + 0.6:
            return side
    return None


merged = []
for a, b, side, mode in STUDIO:
    if merged and merged[-1][2] == side and merged[-1][3] == mode and a - merged[-1][1] < 1.2:
        merged[-1] = (merged[-1][0], b, side, mode)
    else:
        merged.append((a, b, side, mode))
TR = 0.7
for a, b, side, mode in merged:
    if mode == "cut":
        # presenter cut-out slides aside over the navy studio; the room plate fades away
        x = -500 if side == "L" else 500
        clip = "inset(0% 30.5% 0% 0%)" if side == "L" else "inset(0% 0% 0% 0%)"   # left slides: drop the mic so it can't cross the panel
        js.append(f'tl.to("#platecard",{{opacity:0,duration:.18,ease:"power1.in"}},{T(a) - .08:.3f});')
        js.append(f'tl.set("#fgcam",{{clipPath:"{clip}"}},{T(a) + .1:.3f});')
        js.append(f'tl.fromTo("#fgcam",{{x:0,y:0,scale:1}},{{x:{x},y:76,scale:.9,duration:.6,ease:"power3.inOut",immediateRender:false}},{T(a) - .05:.3f});')
        js.append(f'tl.to("#fgcam",{{x:0,y:0,scale:1,duration:.6,ease:"power3.inOut"}},{T(b) - .1:.3f});')
        js.append(f'tl.set("#fgcam",{{clipPath:"inset(0% 0% 0% 0%)"}},{T(b) + .3:.3f});')
        js.append(f'tl.to("#platecard",{{opacity:1,duration:.15,ease:"power1.out"}},{T(b) + .48:.3f});')
        continue
    lo, hi, med = face_span(a, b)
    # centre the crop on his face; widen toward the lean range so the whole head stays in
    cx = (lo + hi) / 2 * 1920 * ZOOM
    L = max(0, min(1920 - CARD_W, cx - CARD_W / 2))
    sw, sh = CARD_W * CARD_S, CARD_H * CARD_S
    X = (CARD_M if side == "L" else 1920 - CARD_M - sw) - CARD_S * L
    Y = (1080 - sh) / 2 - CARD_S * CARD_TOP
    clip = f"inset({CARD_TOP / 10.8:.3f}% {(1920 - L - CARD_W) / 19.2:.3f}% 0% {L / 19.2:.3f}% round 40px)"
    ta, tb = T(a) - 0.1, T(b) - 0.15
    js.append(f'tl.fromTo("#platecard",{{clipPath:"inset(0% 0% 0% 0% round 0px)",x:0,y:0,scale:1}},'
              f'{{clipPath:"{clip}",x:{X:.1f},y:{Y:.1f},scale:{CARD_S},duration:{TR},ease:"power3.inOut",immediateRender:false}},{ta:.3f});')
    js.append(f'tl.fromTo("#cardring",{{opacity:0}},{{opacity:1,duration:.4}},{ta + TR - .2:.3f});')
    js.append(f'tl.set("#cardring",{{left:{X + CARD_S * L:.1f},top:{Y + CARD_S * CARD_TOP:.1f},width:{sw:.1f},height:{sh:.1f}}},{ta:.3f});')
    js.append(f'tl.to("#cardring",{{opacity:0,duration:.2}},{tb - .05:.3f});')
    js.append(f'tl.to("#platecard",{{clipPath:"inset(0% 0% 0% 0% round 0px)",x:0,y:0,scale:1,duration:{TR},ease:"power3.inOut"}},{tb:.3f});')

# punch-ins at internal cuts while full frame (plate + cut-out together)
cuts = [s["edit_in"] for i, s in enumerate(SEG) if i]
zoom_i = 0
for t in cuts:
    if in_studio(t) or t < SPLASH_OUT or t >= T_OUT - 0.5:
        continue
    zoom_i += 1
    z = 1.08 if zoom_i % 2 else 1.0
    js.append(f'tl.set(["#platecam","#fgcam"],{{scale:{z}}},{T(t):.3f});')
# reset punch-in when a card starts and at the outro
for a, b, side, mode in merged:
    js.append(f'tl.set(["#platecam","#fgcam"],{{scale:1}},{T(a) - 0.12:.3f});')
js.append(f'tl.set(["#platecam","#fgcam"],{{scale:1}},{T(T_OUT) - 0.05:.3f});')

# ---- lower third + splash + bumper -----------------------------------------------------
el_html.append(f'''<div class="clip lower3" id="l3" data-start="0.15" data-duration="{round(SPLASH_IN - 0.1, 3)}" data-track-index="5">
<div class="l3bar" id="l3bar"></div><div class="l3name" id="l3name">HOST NAME</div><div class="l3sub" id="l3sub">HOST · CHANNEL NAME</div></div>''')
js.append('tl.fromTo("#l3bar",{scaleX:0},{scaleX:1,duration:.5,ease:"expo.out"},0.2);')
js.append('tl.fromTo("#l3name",{opacity:0,x:-40},{opacity:1,x:0,duration:.45,ease:"power3.out"},0.3);')
js.append('tl.fromTo("#l3sub",{opacity:0,x:-30},{opacity:1,x:0,duration:.45,ease:"power3.out"},0.45);')
js.append(f'tl.to("#l3",{{opacity:0,duration:.2}},{SPLASH_IN - 0.3:.3f});')


def logo(prefix, big=True):
    return (f'<div class="logo {"lg" if big else "sm"}" id="{prefix}logo">'
            f'<div class="lw" id="{prefix}w" data-layout-allow-overlap>' + "".join(f"<span data-layout-allow-overlap>{c}</span>" for c in LOGO[0]) + '</div>'
            f'<div class="lai" id="{prefix}ai">{LOGO[1]}</div>'
            f'<div class="lm" id="{prefix}m" data-layout-allow-overlap>{LOGO[2]}</div></div>')


el_html.append(f'<div class="clip takeover" id="splash" data-start="{SPLASH_IN:.3f}" data-duration="{SPLASH_OUT - SPLASH_IN:.3f}" data-track-index="8">'
               '<div class="tobg" id="splbg"></div><div class="beam b1" id="splb1"></div><div class="beam b2" id="splb2"></div>'
               + logo("spl") + '<div class="tagline" id="spltag">YOUR TAGLINE HERE</div></div>')
S0 = SPLASH_IN
js += [
    f'tl.fromTo("#splbg",{{clipPath:"inset(50% 0% 50% 0%)"}},{{clipPath:"inset(0% 0% 0% 0%)",duration:.35,ease:"expo.out"}},{S0:.3f});',
    f'tl.fromTo("#splb1",{{xPercent:-120}},{{xPercent:120,duration:1.4,ease:"power2.inOut"}},{S0 + .1:.3f});',
    f'tl.fromTo("#splb2",{{xPercent:120}},{{xPercent:-120,duration:1.6,ease:"power2.inOut"}},{S0 + .2:.3f});',
    f'tl.fromTo("#splw span",{{opacity:0,yPercent:-90,rotationX:-80}},{{opacity:1,yPercent:0,rotationX:0,duration:.45,stagger:.08,ease:"back.out(1.8)"}},{S0 + .25:.3f});',
    f'tl.fromTo("#splai",{{opacity:0,scale:2.6}},{{opacity:1,scale:1,duration:.35,ease:"expo.out"}},{T_LOGO_B - .1:.3f});',
    f'tl.fromTo("#splm",{{opacity:0,clipPath:"inset(0% 100% 0% 0%)"}},{{opacity:1,clipPath:"inset(0% 0% 0% 0%)",duration:.4,ease:"power4.out"}},{T_LOGO_C - .05:.3f});',
    f'tl.fromTo("#spllogo",{{scale:1}},{{scale:1.06,duration:1.2,ease:"none"}},{T_LOGO_C:.3f});',
    f'tl.fromTo("#spltag",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.35,ease:"power3.out"}},{T_LOGO_C + .2:.3f});',
    f'tl.to("#spllogo",{{opacity:0,scale:.6,filter:"blur(12px)",duration:.3,ease:"power3.in"}},{SPLASH_OUT - .35:.3f});',
    f'tl.to(["#splbg","#spltag"],{{opacity:0,duration:.3,ease:"power2.in"}},{SPLASH_OUT - .3:.3f});',
]
el_html.append(f'<div class="clip takeover" id="bumper" data-start="{C:.3f}" data-duration="{B:.3f}" data-track-index="8">'
               '<div class="tobg" id="bmpbg"></div><div class="rings" id="bmprings"><i></i><i></i><i></i></div>'
               + logo("bmp") + '<div class="tagline" id="bmptag">EPISODE TITLE HERE</div></div>')
js += [
    f'tl.fromTo("#bmpbg",{{clipPath:"circle(0% at 50% 50%)"}},{{clipPath:"circle(120% at 50% 50%)",duration:.5,ease:"power3.inOut"}},{C:.3f});',
    f'tl.fromTo("#bmprings i",{{scale:.2,opacity:.9}},{{scale:3.2,opacity:0,duration:1.6,stagger:.3,ease:"power2.out"}},{C + .7:.3f});',
    f'tl.fromTo("#bmpw span",{{opacity:0,y:120}},{{opacity:1,y:0,duration:.4,stagger:.07,ease:"expo.out"}},{C + .35:.3f});',
    f'tl.fromTo("#bmpai",{{opacity:0,rotation:-25,scale:.3}},{{opacity:1,rotation:0,scale:1,duration:.45,ease:"back.out(2.4)"}},{C + .7:.3f});',
    f'tl.fromTo("#bmpm",{{opacity:0,scaleX:1.7}},{{opacity:1,scaleX:1,duration:.6,ease:"expo.out"}},{C + .85:.3f});',
    f'tl.fromTo("#bmptag",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.4,ease:"power3.out"}},{C + 1.3:.3f});',
    f'tl.to("#bmplogo",{{scale:1.08,duration:1.6,ease:"none"}},{C + 1.1:.3f});',
    f'tl.to(["#bmplogo","#bmptag","#bmprings"],{{opacity:0,y:-60,duration:.3,ease:"power3.in"}},{C + B - .45:.3f});',
    f'tl.to("#bmpbg",{{clipPath:"inset(0% 0% 100% 0%)",duration:.4,ease:"power3.inOut"}},{C + B - .4:.3f});',
]
# outro: original full-screen shot; next-video title in a big lower-left box, clear of face, pointing hand and thumbnail slots
el_html.append(f'<div class="clip nexttitle" id="nxt" data-start="{T(T_TITLE) - 0.1:.3f}" data-duration="{TOTAL - T(T_TITLE) + 0.1:.3f}" data-track-index="7">'
               f'<div class="nxk" id="nxk">NEXT ON CHANNEL NAME</div><div class="nxt" id="nxtt">{html.escape(NEXT_TITLE).replace(". It ", ".<br>It ")}</div></div>')
js += [f'tl.fromTo("#nxt",{{opacity:0,y:80}},{{opacity:1,y:0,duration:.6,ease:"expo.out"}},{T(T_TITLE) - 0.1:.3f});',
       f'tl.fromTo("#nxk",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.4,ease:"power3.out"}},{T(T_TITLE) + 0.3:.3f});']

# ---- media --------------------------------------------------------------------
def media_pair(tag, id_, src, extra=""):
    a = (f'<{tag} id="{id_}a" src="{src}" data-start="0" data-duration="{C:.3f}" data-media-start="0" {extra}></{tag}>')
    b = (f'<{tag} id="{id_}b" src="{src}" data-start="{C + B:.3f}" data-duration="{AROLL_DUR - C:.3f}" '
         f'data-media-start="{C:.3f}" {extra}></{tag}>')
    return a + b


plate = media_pair("video", "plate", "assets/edit/aroll.mp4", 'class="fill" data-track-index="1" muted playsinline')
# presenter cut-out only where something is behind him or he is moved (plate shows him identically elsewhere).
win = ([(beats[0][0] - 0.45, t_end + 0.35) for _, beats, t_end in BEHIND]      # words behind him
       + [(a - 0.45, b + 0.9) for a, b, side, mode in STUDIO if mode == "cut"])    # cut-out slides
win = sorted((max(0.0, a), min(AROLL_DUR, b)) for a, b in win)
mw = []
for a, b in win:
    if mw and a <= mw[-1][1] + 1.0:
        mw[-1] = (mw[-1][0], max(mw[-1][1], b))
    else:
        mw.append((a, b))
FG_WIN = []
for a, b in mw:
    FG_WIN += [(a, min(b, C)), (C, b)] if a < C < b else [(a, b)]
fg = "".join(
    f'<video id="fg{i}" src="assets/edit/fgw{i}.webm" class="fill" data-start="{T(round(a * FPS) / FPS):.4f}" '
    f'data-duration="{(round(b * FPS) - round(a * FPS)) / FPS:.4f}" '
    f'data-media-start="0" data-track-index="4" muted playsinline></video>'
    for i, (a, b) in enumerate(FG_WIN) if b - a > 0.05)
json.dump([[a, b] for a, b in FG_WIN], open(os.path.join(HERE, "fg_windows.json"), "w"))
print(f"fg windows: {len(FG_WIN)}, cut-out on screen {sum(b - a for a, b in FG_WIN):.0f}s of {AROLL_DUR:.0f}s")
voice = media_pair("audio", "voice", "assets/edit/voice.wav", 'data-track-index="20" data-volume="1"')

SFX = []


SFX_MANIFEST = os.environ.get("MEDIA_SFX_MANIFEST")
if not SFX_MANIFEST or not os.path.isfile(SFX_MANIFEST):
    raise RuntimeError("Set MEDIA_SFX_MANIFEST to the available media-use SFX manifest")
SFXDUR = {k: v["duration"] for k, v in json.load(open(SFX_MANIFEST)).items()}


def sfx(name, t, vol=0.35, media_start=0.0, dur=None):
    d = dur or (SFXDUR[name] - media_start)
    d = min(d, TOTAL - t - 0.05)
    SFX.append(f'<audio id="sfx{len(SFX)}" src="assets/sfx/{name}.mp3" data-start="{t:.3f}" data-media-start="{media_start:.3f}" data-duration="{d:.3f}" '
               f'data-track-index="{40 + len(SFX)}" data-volume="{vol}"></audio>')


sfx("whoosh", SPLASH_IN - 0.05, 0.45)
sfx("impact-bass-1", T_LOGO_C - 0.05, 0.5)
sfx("glitch-1", T(at("couldn't find again", 11.0)), 0.12, dur=0.9)
sfx("impact-bass-1", T(at("called Sorter", 46.0)) + 0.1, 0.4)
sfx("impact-bass-1", T(at("Sorter portion would be", 669.5)), 0.3)
for t0, t1, items, style, side in CALLOUTS:
    sfx("whoosh-short" if style != "stack" else "click-soft", T(items[0][0]) - 0.05, 0.14 if style == "stack" else 0.2)
sfx("sparkle", T_LOGO_B, 0.18)
sfx("riser", C - 0.6, 0.35, media_start=10.03 - 1.3, dur=1.3)
sfx("whoosh-short", C + 0.3, 0.4)
sfx("impact-bass-2", C + 0.7, 0.5)
sfx("whoosh", C + B - 0.45, 0.35)
for kicker, beats, t_end in BEHIND:
    sfx("whoosh-short", T(beats[0][0]) - 0.12, 0.16)
for side, t0, t1, pages in PANELS:
    for tp, title, items in pages:
        for it in items:
            if it[1] == "stamp":
                sfx("impact-bass-2", T(it[0]) - 0.02, 0.32)
            elif it[1] == "link":
                sfx("pop", T(it[0]), 0.35)
                sfx("chime", T(it[0]) + 0.3, 0.12)
            elif it[1] in ("chip",):
                sfx("click-soft", T(it[0]), 0.25)

# ---- page -----------------------------------------------------------------------
tpl = open(os.path.join(HERE, "template.html")).read()
out = (tpl.replace("{{DURATION}}", f"{TOTAL}")
       .replace("{{PLATE}}", plate).replace("{{FG}}", fg)
       .replace("{{ELEMENTS}}", "\n".join(el_html)).replace("{{CAM}}", "")
       .replace("{{AUDIO}}", voice + "\n" + "\n".join(SFX))
       .replace("{{TIMELINE}}", "\n".join(js)))
open(os.path.join(ROOT, "index.html"), "w").write(out)
json.dump({"C": C, "B": B, "total": TOTAL, "fg_windows": FG_WIN, "callouts": CO_META,
           "splash": [SPLASH_IN, SPLASH_OUT], "studio": STUDIO},
          open(os.path.join(HERE, "build_meta.json"), "w"), indent=1)
print(f"total={TOTAL}s C={C:.2f} behind={len(BEHIND)} panels={len(PANELS)} tweens={len(js)}")
