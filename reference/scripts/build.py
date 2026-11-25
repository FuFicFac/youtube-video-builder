"""Reference edit — generate index.html (adapt every cue, path and label before running).

Intro take: room plate + hybrid cut-out, splash, words-behind, CTA panels, bumper.
Demo take: the screen share becomes a stage; the presenter lives in a moving cam window
(circle PiP <-> rounded card), with zooms, a "what Opus built" tracker and rebuilt
kinetic panels. Every cue is anchored to a phrase the presenter says (edit_words.json).
The cue phrases and labels below are examples from that edit; replace them with your own narration.
"""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EDL = json.load(open(os.path.join(HERE, "edl.json")))
WORDS = json.load(open(os.path.join(HERE, "edit_words.json")))  # [w, start, end]
_m = []
for w in WORDS:  # QA transcript writes "All right." where the script has "Alright,"
    if _m and _m[-1][0].lower() == "all" and w[0].lower().startswith("right"):
        _m[-1] = ["Alright" + w[0][5:], _m[-1][1], w[2]]
    else:
        _m.append(list(w))
WORDS = []
for w in _m:  # split hyphenated tokens so "AI-generated" == "AI generated"
    parts = [p for p in w[0].split("-") if p]
    for p in parts or [w[0]]:
        WORDS.append([p, w[1], w[2]])
FPS = 24000 / 1001
SEG = EDL["segments"]
AROLL_DUR = EDL["duration"]
I_LEN = next(s["edit_in"] for s in SEG if s["src"] == "demo")


ALIAS = {"pros": "prose", "saul": "sol", "sal": "sol", "saw": "sol", "gonna": "going",
         "mockup": "mock"}   # ASR spelling -> script spelling, per recording


def norm(w):
    n = re.sub(r"[^a-z0-9$]", "", w.lower())
    return ALIAS.get(n, n)


def _find(phrase, near, span):
    toks = [norm(t) for t in phrase.replace("-", " ").split() if norm(t)]
    best = None
    for i in range(len(WORDS) - len(toks) + 1):
        if all(norm(WORDS[i + k][0]) == toks[k] for k in range(len(toks))):
            d = abs(WORDS[i][1] - near)
            if d <= span and (best is None or d < best[0]):
                best = (d, i)
    if best is None:
        raise SystemExit(f"anchor not found: {phrase!r} near {near}")
    return best[1], len(toks)


def at(phrase, near, span=22):
    i, _ = _find(phrase, near, span)
    return WORDS[i][1]


def end(phrase, near, span=22):
    i, n = _find(phrase, near, span)
    return WORDS[i + n - 1][2]


C = at("If you are possibly", 31.0) - 0.06   # bumper after the handoff cue ("This is CHANNEL NAME.")
B = 3.4
TAIL = 2.2


def T(t):
    return round(t + B if t >= C else t, 3)


TOTAL = round(AROLL_DUR + B + TAIL, 3)
NAVY, PAPER, GREEN, RED, BLUE = "#0a1424", "#f2ecdf", "#39d98a", "#ff5d4f", "#3b7bff"
el_html, js = [], []

# shared building blocks (words-behind, studio panels) from an earlier edit
exec(open(os.path.join(HERE, "base_parts.py.txt")).read())
_orig_panel = panel


def panel(side, t0, t1, pages, demo=False):
    if demo:
        PANELS.append((side, t0, t1, pages))
    else:
        _orig_panel(side, t0, t1, pages)


# =====================================================================
#                          INTRO CUES
# =====================================================================
SPLASH_IN = at("welcome", 2.0) - 0.35
SPLASH_OUT = end("channel name,", 4.0) + 0.9   # last words of the spoken channel name
behind("CHANNEL TAGLINE GOES HERE IN ONE LINE",
       [(at("first half of the tagline", 8.0), "CHANNEL TAGLINE"),
        (at("second half of the tagline", 10.0), "GOES *HERE*")],
       at("Alright, what are we", 11.5))
behind("WHAT ARE WE DOING TODAY?",
       [(at("Opus 5.5, and all", 14.5), "*OPUS 5.5*"),
        (at("incredible things", 17.5), "INCREDIBLE THINGS *I'VE BUILT*")],
       at("And also the one thing", 21.5))
behind("AND ALSO THE ONE THING I WILL NOT EVEN TOUCH",
       [(at("the one thing", 22.0), "THE ONE THING"),
        (at("not even touch", 24.5), "I !WON'T TOUCH!")],
       at("So let's jump", 27.5))
panel("L", C + 0.01, at("Today we are literally", 63.0), [
    (C + 0.01, "LEARN WHAT I BUILD", [
        (at("lot of workflows", 36.5), "chip", "WORKFLOWS"),
        (at("GitHub repos", 38.5), "chip", "GITHUB *REPOS*"),
        (at("programs that I've built", 40.5), "chip", "PROGRAMS"),
        (at("lot of students", 44.0), "chip", "*STUDENTS* I'VE TAUGHT")]),
    (at("my school name", 46.5), "", [
        (at("my school name", 46.5), "note", "MY SCHOOL"),
        (at("school name here.", 47.0), "hero", "SCHOOL *NAME*"),
        (at("links in the description", 49.0), "link", "LINK IN THE DESCRIPTION")]),
    (at("And if you are interested in prose", 51.0), "", [
        (at("without writing slop", 56.0), "note", "WRITE WITH AI — *WITHOUT THE SLOP*"),
        (at("my course name", 58.5), "hero", "COURSE *NAME*"),
        (at("a link to that too", 61.0), "link", "LINK IN THE DESCRIPTION")])])
behind("TODAY WE ARE LITERALLY GOING TO GO",
       [(at("all the way", 66.5), "ALL *THE WAY*"),
        (at("talking about Opus 5.5 and what", 71.0), "*OPUS 5.5*"),
        (at("amazing, amazing program", 77.0), "AMAZING. *AMAZING.*")],
       at("Alright, let's jump into", 82.0))
panel("R", at("Alright, let's jump into", 82.0), I_LEN + 0.2, [
    (at("Alright, let's jump into", 82.0), "THE BEST MODEL", [
        (at("building story", 88.0), "ok", "FOR BUILDING *STORY*"),
        (at("all kinds of things around story", 89.0), "ok", "EVERYTHING *AROUND* STORY"),
        (at("Not necessarily writing", 91.0), "stamp", "NOT NECESSARILY WRITING", "red")])])

# =====================================================================
#                          DEMO: layout engine
# =====================================================================
FACE = (280, 380)                                   # head+shoulders centre inside the 560x860 cam window
CIRCLE = "inset(7% 0% 18.6% 0% round 50%)"          # PIP_HEAD_SHOULDERS (creator note: not a tight face crop)
CARD = "inset(0% 0% 0% 0% round 6%)"
LAYOUT = {  # vp: x, y, scale, opacity | cw: x, y, scale, clip
    "STAGE_R": dict(vp=(70, 150, 1.0, 1), cw=(1720 - FACE[0] * .42, 880 - FACE[1] * .42, .42, CIRCLE)),
    "STAGE_L": dict(vp=(70, 150, 1.0, 1), cw=(200 - FACE[0] * .42, 880 - FACE[1] * .42, .42, CIRCLE)),
    "SIDE_L": dict(vp=(660, 262, .7, 1), cw=(70, 110, 1.0, CARD)),
    "SIDE_R": dict(vp=(36, 262, .7, 1), cw=(1290, 110, 1.0, CARD)),
    "PANEL_L": dict(vp=(660, 262, .7, 0), cw=(150, 110, 1.0, CARD)),
    "PANEL_R": dict(vp=(36, 262, .7, 0), cw=(1210, 110, 1.0, CARD)),
}
MODES = []   # (t, layout, zoom=(scale, fx%, fy%))
TRACK = []   # (t, label)


def mode(t, layout, zoom=(1.0, 50, 50)):
    MODES.append((t, layout, zoom))


def track(t, label):
    TRACK.append((t, label))


D0 = I_LEN
mode(D0, "STAGE_R")
track(at("This is the sketch that I put", 114.0), "BUILT BY OPUS 5.5 · IN HYPERFRAMES")
mode(at("It builds my worlds", 156.0), "STAGE_L", (1.12, 50, 45))
mode(at("Alright, so that's basically it", 171.0), "PANEL_L")
panel("L", at("Alright, so that's basically it", 171.0), at("let me show you another", 193.0), [
    (at("Alright, so that's basically it", 171.0), "", [
        (at("that entire video", 173.0), "note", "THAT ENTIRE VIDEO?"),
        (at("built by Opus", 178.0), "hero", "BUILT BY *OPUS 5.5*"),
        (at("inside of Hyperframes", 186.0), "chip", "INSIDE *HYPERFRAMES*"),
        (at("Lickety split", 190.0), "chip", "LICKETY *SPLIT*")])], demo=True)
mode(at("let me show you another", 193.0), "STAGE_L")
track(at("for a potential client", 209.0), "CLIENT MOCK-UP · CLIENT NAME")
mode(at("So here's that video", 219.0), "STAGE_R", (1.08, 50, 50))
mode(at("I can even before I even", 238.0), "SIDE_L")
track(at("I bet that I could", 242.0), "LIVE · A HORIZONTAL VERSION, ON THE FLY")
mode(at("could you make a horizontal", 250.0), "STAGE_R", (1.35, 30, 40))
mode(at("but it's not just that", 264.0), "PANEL_R")
panel("R", at("but it's not just that", 264.0), at("And this is the sketch, what", 310.0), [
    (at("but it's not just that", 264.0), "IT ALSO…", [
        (at("one hand sketch", 267.0), "step", "HAND SKETCH → *BLENDER MODEL*", "01"),
        (at("entire fly through", 276.0), "step", "→ A FULL *FLY-THROUGH*", "02"),
        (at("story engine built", 279.0), "step", "A *STORY ENGINE* FROM MY NOTES", "03"),
        (at("Three different board games", 286.0), "step", "THREE *BOARD GAMES*", "04"),
        (at("My thumbnail brand was measured", 289.0), "step", "MY THUMBNAIL BRAND, *MEASURED*", "05"),
        (at("it doesn't write for me", 307.0), "stamp", "IT DOESN'T WRITE FOR ME", "red")])], demo=True)
mode(at("And this is the sketch, what", 310.0), "STAGE_L", (1.0, 50, 50))
track(at("And this is the sketch, what", 310.0), "HAND SKETCH → 3D MODEL")
mode(at("it's such a basic sketch", 316.0), "STAGE_L", (1.6, 22, 70))
mode(at("into something that is tangible", 335.5), "STAGE_R", (1.0, 50, 50))
mode(at("rendered a real blender render", 342.0), "STAGE_R", (1.45, 45, 65))
mode(at("this is the AI generated picture", 376.0), "SIDE_L")
mode(at("at this fly through", 393.0), "STAGE_R", (1.0, 50, 50))
track(at("at this fly through", 393.0), "AI FLY-THROUGH")
mode(at("does not lift up", 402.0), "STAGE_R", (1.3, 50, 55))
mode(at("I love the fact that", 413.0), "STAGE_L", (1.0, 50, 50))
mode(at("this was on C Dance", 425.0), "SIDE_R")
track(at("this was on C Dance", 425.0), "FLY-THROUGH · SEEDANCE")
mode(at("It also worked on the", 450.0), "PANEL_L")
panel("L", at("It also worked on the", 450.0), at("Then I turned those into", 505.0), [
    (at("It also worked on the", 450.0), "MY NOTES", [
        (at("think deeply about the plot", 456.0), "note", "THINK DEEPLY *BEFORE* YOU PITCH"),
        (at("it read everything", 465.0), "hero", "IT READ *EVERYTHING*"),
        (at("the sample project", 468.0), "chip", "THE SAMPLE PROJECT"),
        (at("the 15 creatures", 470.0), "chip", "THE *15 CREATURES*")]),
    (at("found clues", 476.0), "CLUES I PLANTED", [
        (at("A boulder that", 480.0), "ok", "A BOULDER THAT *MOVED AFTER A RAIN*"),
        (at("a mound that got", 483.0), "ok", "A MOUND WITH A *CONTOUR LINE*"),
        (at("would never realize", 492.0), "note", "…WITHOUT EVEN *REALIZING IT*")]),
    (at("figured out storylines", 496.0), "", [
        (at("six different storylines", 499.0), "hero", "*6* STORYLINES"),
        (at("episodic now", 504.0), "stamp", "EPISODIC", "green")])], demo=True)
track(at("It also worked on the", 450.0), "A STORY ENGINE FROM MY NOTES")
mode(at("Then I turned those into", 505.0), "STAGE_R", (1.0, 50, 50))
track(at("Then I turned those into", 505.0), "THREE BOARD GAMES")
mode(at("this is sort of the first universe", 528.0), "STAGE_R", (1.55, 22, 58))
mode(at("second universe", 533.0), "STAGE_R", (1.55, 52, 58))
mode(at("third universe", 538.0), "STAGE_L", (1.55, 80, 58))
mode(at("these aren't just pretty pictures", 547.0), "SIDE_L")
mode(at("Then I pointed it at my", 564.0), "STAGE_R", (1.0, 50, 50))
track(at("Then I pointed it at my", 564.0), "MY THUMBNAIL BRAND, MEASURED")
mode(at("the exact green", 572.0), "PANEL_L")
panel("L", at("the exact green", 572.0), at("just saw is opus", 641.0), [
    (at("the exact green", 572.0), "MY BRAND, MEASURED", [
        (at("the exact green", 572.0), "swatch", "THE EXACT GREEN", GREEN),
        (at("the exact blue", 574.0), "swatch", "THE EXACT BLUE", BLUE),
        (at("full expressions", 577.0), "note", "EVERY EXPRESSION, TIED TO THE CLAIM:")]),
    (at("shock for launches", 582.0), "EXPRESSION = CLAIM", [
        (at("shock for launches", 582.0), "step", "SHOCK → *LAUNCHES*", "01"),
        (at("laughing for", 584.0), "step", "LAUGHING → *WINS*", "02"),
        (at("side eye", 587.0), "step", "SIDE-EYE → *SKEPTICAL*", "03"),
        (at("pointing for tutorials", 590.0), "step", "POINTING → *TUTORIALS*", "04")]),
    (at("it found a real bug", 593.0), "IT FOUND A BUG", [
        (at("four of my thumbnails", 595.0), "note", "IN 4 OF MY THUMBNAILS…"),
        (at("covering the payoff word", 600.0), "stamp", "TIMESTAMP COVERED THE PAYOFF", "red")]),
    (at("tried to generate like my faces", 604.0), "", [
        (at("AI generated faces", 607.0), "no", "AI-GENERATED FACES"),
        (at("real headshot", 614.0), "ok", "MY *REAL HEADSHOTS*"),
        (at("more info for agents", 636.0), "hero", "A SYSTEM *FOR AGENTS*")])], demo=True)
mode(at("just saw is opus", 641.0), "SIDE_L")
track(at("just saw is opus", 641.0), "EVERYTHING ABOVE = OPUS THINKING")
mode(at("what I did not let it", 649.0), "PANEL_R")
panel("R", at("what I did not let it", 649.0), at("Remember the story engine", 745.0), [
    (at("what I did not let it", 649.0), "WHAT I DIDN'T LET IT DO", [
        (at("write my prose", 651.0), "stamp", "WRITE MY PROSE", "red"),
        (at("Not the chapters", 653.0), "no", "NOT THE CHAPTERS"),
        (at("not the scenes", 655.0), "no", "NOT THE SCENES")]),
    (at("Here's why", 658.0), "HERE'S WHY", [
        (at("invisible watermark", 662.0), "hero", "AN *INVISIBLE* WATERMARK"),
        (at("help page", 668.0), "note", "THEIR OWN HELP PAGE NAMES *OPUS 5.5*"),
        (at("You can't see it", 670.0), "ok", "YOU CAN'T SEE IT"),
        (at("It survives copy", 672.0), "ok", "IT SURVIVES *COPY*"),
        (at("It survives pasting", 673.5), "ok", "IT SURVIVES *PASTING*"),
        (at("some of the editing", 675.0), "ok", "EVEN SOME *EDITING*")]),
    (at("There's no switching it", 679.0), "", [
        (at("There's no switching it", 679.0), "no", "NO OFF SWITCH"),
        (at("regulators", 684.0), "chip", "REGULATORS"),
        (at("the media", 685.0), "chip", "THE MEDIA"),
        (at("fact checkers", 686.0), "chip", "FACT CHECKERS"),
        (at("schools", 687.5), "chip", "SCHOOLS"),
        (at("run a detector", 689.0), "stamp", "DETECTORS RUN *NOW*", "red")]),
    (at("putting my name on a book", 711.0), "", [
        (at("putting my name on a book", 711.0), "note", "I'M NOT PUTTING MY NAME ON A BOOK…"),
        (at("fingerprint", 706.0), "hero", "…WITH SOMEBODY ELSE'S *FINGERPRINT*"),
        (at("could change the quality", 717.5), "note", "AND IT COULD CHANGE *THE PROSE*")]),
    (at("it is my right", 722.0), "MY RIGHT", [
        (at("in any way, shape, or form", 724.0), "note", "TO WRITE *ANY WAY I WANT*"),
        (at("not putting out slop", 735.0), "no", "AS LONG AS IT'S NOT SLOP"),
        (at("If it's a good story", 741.0), "hero", "A GOOD STORY IS *A GOOD STORY*")])], demo=True)
mode(at("Remember the story engine", 745.0), "SIDE_R")
track(at("Remember the story engine", 745.0), "WHAT IT NEVER TOUCHED")
mode(at("complete thing on GPT", 757.0), "PANEL_L")
panel("L", at("complete thing on GPT", 757.0), at("it did 10 things", 770.0), [
    (at("complete thing on GPT", 757.0), "WRITING?", [
        (at("GPT 6", 759.0), "hero", "*GPT-6 SOL*"),
        (at("different it is at writing", 762.0), "note", "FULL REVIEW ON THE CHANNEL")])], demo=True)
mode(at("it did 10 things", 770.0), "STAGE_R", (1.0, 50, 50))
track(at("it did 10 things", 770.0), "TEN JOBS · ZERO CHAPTERS")
mode(at("so much fun", 781.0), "STAGE_R", (1.5, 40, 75))
mode(at("Alright, my", 801.0), "PANEL_L")
panel("L", at("Alright, my", 801.0), AROLL_DUR + 0.6, [
    (at("Alright, my", 801.0), "HOST NAME", [
        (at("all of my schools", 796.0), "note", "ALL MY STUFF · ALL MY SCHOOLS"),
        (at("links in the description", 799.0), "link", "LINK IN THE DESCRIPTION")]),
    (at("this is a video that they want", 802.0), "", [
        (at("this is a video that they want", 802.0), "slot", "GPT-6 *SOL*", "HOW GOOD IT WRITES",
         at("GPT-6", 808.0))])], demo=True)

DS = T(D0)
# ---- intro camera + panels ------------------------------------------------------
build_behind()
build_panels()
STUDIO.sort()
intro_cuts = [s["edit_in"] for i, s in enumerate(SEG) if i and s["src"] == "intro"]
TR = 0.5
merged = []
for a, b, side in STUDIO:
    if merged and merged[-1][2] == side and a - merged[-1][1] < 0.4:
        merged[-1] = (merged[-1][0], b, side)
    else:
        merged.append((a, b, side))


def in_studio(t):
    return next((s for a, b, s in merged if a <= t < b), None)


zi = 0
for t in intro_cuts:
    if t < SPLASH_OUT or any(abs(t - x) < TR + .1 for a, b, _ in merged for x in (a, b)):
        continue
    zi += 1
    z = 1.1 if zi % 2 else 1.0
    if in_studio(t):
        js.append(f'tl.set("#icv",{{scale:{1.08 if z > 1 else 1.0}}},{T(t):.3f});')
    else:
        js.append(f'tl.set(["#platecam","#fgcam"],{{scale:{z}}},{T(t):.3f});')
# studio beats in the intro: the presenter in a rounded card (no hard cut-out; cleaner around the mic)
for a, b, side in merged:
    cx = 110 if side == "L" else 1110
    js.append(f'tl.set("#icard",{{x:{cx}}},{T(a) - .1:.3f});')
    js.append(f'tl.to(["#platecam","#fgcam"],{{opacity:0,duration:{TR},ease:"power2.inOut"}},{T(a) - .05:.3f});')
    js.append(f'tl.fromTo("#icard",{{opacity:0,xPercent:{-60 if side == "L" else 60},scale:.92}},'
              f'{{opacity:1,xPercent:0,scale:1,duration:{TR + .2},ease:"power3.out"}},{T(a) - .05:.3f});')
    if b < I_LEN - 0.3:
        js.append(f'tl.to(["#platecam","#fgcam"],{{opacity:1,duration:{TR},ease:"power2.inOut"}},{T(b) - .1:.3f});')
        js.append(f'tl.to("#icard",{{opacity:0,scale:1.08,duration:{TR},ease:"power2.inOut"}},{T(b) - .1:.3f});')
    else:
        js.append(f'tl.to("#icard",{{opacity:0,duration:.4,ease:"power2.in"}},{DS - .1:.3f});')

# ---- demo layout tweens -------------------------------------------------------------
MODES.sort()
DS = T(D0)
first = True
for i, (t, lay, zoom) in enumerate(MODES):
    L = LAYOUT[lay]
    vx, vy, vs, vo = L["vp"]
    cx, cy, cs, clip = L["cw"]
    s = T(t) - 0.15
    if first:
        js.append(f'tl.set("#vp",{{x:{vx},y:{vy},scale:{vs},opacity:{vo}}},{DS:.3f});')
        js.append(f'tl.set("#cw",{{x:{cx:.1f},y:{cy:.1f},scale:{cs},clipPath:"{clip}"}},{DS:.3f});')
        js.append(f'tl.fromTo("#vp",{{yPercent:40,opacity:0}},{{yPercent:0,opacity:1,duration:.8,ease:"expo.out"}},{DS:.3f});')
        js.append(f'tl.fromTo("#cw",{{yPercent:60}},{{yPercent:0,duration:.8,ease:"back.out(1.4)"}},{DS + .2:.3f});')
        first = False
    else:
        js.append(f'tl.to("#vp",{{x:{vx},y:{vy},scale:{vs},opacity:{vo},duration:.8,ease:"power3.inOut"}},{s:.3f});')
        js.append(f'tl.to("#cw",{{x:{cx:.1f},y:{cy:.1f},scale:{cs},clipPath:"{clip}",duration:.8,ease:"power3.inOut"}},{s:.3f});')
    zs, fx, fy = zoom
    js.append(f'tl.set("#scrz",{{transformOrigin:"{fx}% {fy}%"}},{s:.3f});')
    js.append(f'tl.to("#scrz",{{scale:{zs},duration:1.1,ease:"power2.inOut"}},{s:.3f});')
    # slow drift while held (keeps static slides alive)
    nxt = T(MODES[i + 1][0]) - 0.2 if i + 1 < len(MODES) else T(AROLL_DUR)
    if nxt - s > 3:
        js.append(f'tl.to("#scrz",{{scale:{zs * 1.04:.3f},duration:{nxt - s - 1.2:.2f},ease:"none"}},{s + 1.1:.3f});')

# tracker chip
TRACK.sort()
for i, (t, label) in enumerate(TRACK):
    s = T(t)
    e = T(TRACK[i + 1][0]) - 0.1 if i + 1 < len(TRACK) else T(AROLL_DUR) - 0.2
    el_html.append(f'<div class="clip tracker" id="tk{i}" data-start="{s:.3f}" data-duration="{e - s:.3f}" data-track-index="7">'
                   f'<div class="tkin" id="tk{i}i"><span class="tkdot"></span><span class="tklab">OPUS 5.5 BUILT</span>'
                   f'<span class="tktxt">{html.escape(label)}</span></div></div>')
    js.append(f'tl.fromTo("#tk{i}i",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{s:.3f});')
    js.append(f'tl.to("#tk{i}i",{{opacity:0,duration:.2}},{e - .22:.3f});')

# ---- takeovers: lower third, splash, bumper, outro -------------------------------------
exec(open(os.path.join(HERE, "base_logo.py.txt")).read().replace("EPISODE TITLE · SUBTITLE", "OPUS 5.5 · WHAT I BUILT"))

# ---- media -------------------------------------------------------------------------------
plate = (f'<video id="platea" src="assets/edit/intro.mp4" class="fill" data-start="0" data-duration="{C:.4f}" data-media-start="0" data-track-index="1" muted playsinline></video>'
         f'<video id="plateb" src="assets/edit/intro.mp4" class="fill" data-start="{C + B:.4f}" data-duration="{I_LEN - C:.4f}" data-media-start="{C:.4f}" data-track-index="1" muted playsinline></video>')
win = [(beats[0][0] - 0.45, t_end + 0.35) for _, beats, t_end in BEHIND] + [(a - 0.45, b + 0.9) for a, b, _ in merged]
win = sorted((max(0.0, a), min(I_LEN, b)) for a, b in win)
mw = []
for a, b in win:
    if mw and a <= mw[-1][1] + 1.0:
        mw[-1] = (mw[-1][0], max(mw[-1][1], b))
    else:
        mw.append((a, b))
FG_WIN = []
for a, b in mw:
    FG_WIN += [(a, min(b, C)), (C, b)] if a < C < b else [(a, b)]
fg = "".join(f'<video id="fg{i}" src="assets/edit/fg_intro.webm" class="fill" data-start="{T(a):.4f}" data-duration="{b - a:.4f}" '
             f'data-media-start="{a:.4f}" data-track-index="4" muted playsinline></video>'
             for i, (a, b) in enumerate(FG_WIN) if b - a > 0.05)
DD = AROLL_DUR - D0
icard = (f'<div id="icard"><div id="icv">'
         f'<video id="icarda" src="assets/edit/intro.mp4" data-start="0" data-duration="{C:.4f}" data-media-start="0" data-track-index="5" muted playsinline></video>'
         f'<video id="icardb" src="assets/edit/intro.mp4" data-start="{C + B:.4f}" data-duration="{I_LEN - C:.4f}" data-media-start="{C:.4f}" data-track-index="5" muted playsinline></video>'
         '</div></div>')
demo = icard + (f'<div id="vp"><div id="scrz"><video id="scr" src="assets/edit/screen.mp4" data-start="{DS:.4f}" data-duration="{DD:.4f}" '
        f'data-media-start="0" data-track-index="2" muted playsinline></video></div></div>'
        f'<div id="cw"><div id="cwin"><video id="cam" src="assets/edit/cam.mp4" data-start="{DS:.4f}" data-duration="{DD:.4f}" '
        f'data-media-start="0" data-track-index="3" muted playsinline></video></div></div>')
voice = (f'<audio id="voicea" src="assets/edit/voice.wav" data-start="0" data-duration="{C:.4f}" data-media-start="0" data-track-index="20" data-volume="1"></audio>'
         f'<audio id="voiceb" src="assets/edit/voice.wav" data-start="{C + B:.4f}" data-duration="{AROLL_DUR - C:.4f}" data-media-start="{C:.4f}" data-track-index="20" data-volume="1"></audio>')
el_html.insert(0, f'<div class="clip demobg" id="demobg" data-start="{DS - 0.4:.3f}" data-duration="{T(AROLL_DUR) - DS + 0.4:.3f}" data-track-index="0">'
                  '<div class="dglow1"></div><div class="dglow2"></div></div>')
js.append(f'tl.fromTo("#demobg",{{opacity:0}},{{opacity:1,duration:.4}},{DS - 0.4:.3f});')

# ---- sound ----------------------------------------------------------------------------------
exec(open(os.path.join(HERE, "base_sfx.py.txt")).read().split("sfx(\"whoosh-cinematic\"")[0])
sfx("whoosh-cinematic", DS - 0.5, 0.3, dur=2.2)
for kicker, beats, t_end in BEHIND:
    sfx("whoosh-short", T(beats[0][0]) - 0.12, 0.16)
for side, t0, t1, pages in PANELS:
    for tp, title, items in pages:
        for it in items:
            if it[1] == "stamp":
                sfx("impact-bass-2", T(it[0]) - 0.02, 0.3)
            elif it[1] == "link":
                sfx("pop", T(it[0]), 0.35)
                sfx("chime", T(it[0]) + 0.3, 0.12)
            elif it[1] == "chip":
                sfx("click-soft", T(it[0]), 0.22)
for t, lay, zoom in MODES[1:]:
    sfx("whoosh-short", T(t) - 0.18, 0.12)

tpl = open(os.path.join(HERE, "template.html")).read()
out = (tpl.replace("{{DURATION}}", f"{TOTAL}").replace("{{PLATE}}", plate).replace("{{FG}}", fg)
       .replace("{{ELEMENTS}}", "\n".join(el_html)).replace("{{CAM}}", demo)
       .replace("{{AUDIO}}", voice + "\n" + "\n".join(SFX)).replace("{{TIMELINE}}", "\n".join(js)))
open(os.path.join(ROOT, "index.html"), "w").write(out)
json.dump({"C": C, "B": B, "total": TOTAL, "demo_start": DS, "modes": len(MODES)}, open(os.path.join(HERE, "build_meta.json"), "w"))
print(f"total={TOTAL}s intro={I_LEN:.1f} C={C:.2f} behind={len(BEHIND)} panels={len(PANELS)} modes={len(MODES)} tweens={len(js)}")
