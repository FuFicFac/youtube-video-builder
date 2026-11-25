"""Edit decision list for the reference edit: an intro take + a demo take.

The phrases in REMOVE are that edit's real flubs, kept as examples of the pattern. Replace them with your own.

Cuts are anchored on Parakeet word starts; long silences are tightened.
Output edl.json: kept segments [{src, src_in, src_out, edit_in, edit_out}] + edited word list.
"""
import json, re

FPS = 24000 / 1001
W = {"intro": json.load(open("intro_words.json")), "demo": json.load(open("demo_words.json"))}
SIL = {"intro": json.load(open("intro_sil.json")), "demo": json.load(open("demo_sil.json"))}
RANGE = {"intro": (1.45, None), "demo": (1.18, None)}


def norm(w):
    return re.sub(r"[^a-z0-9$]", "", w.lower())


def find(src, phrase, near, span=6):
    toks = [norm(t) for t in phrase.split() if norm(t)]
    ws, best = W[src], None
    for i in range(len(ws) - len(toks) + 1):
        if all(norm(ws[i + k][0]) == toks[k] for k in range(len(toks))):
            d = abs(ws[i][1] - near)
            if d <= span and (best is None or d < best[0]):
                best = (d, i)
    if best is None:
        raise SystemExit(f"{src}: not found {phrase!r} near {near}")
    return best[1]


def cut(src, first, near, keep, keep_near):
    """remove from the first word of `first` up to (not incl.) the first word of `keep`."""
    i, j = find(src, first, near), find(src, keep, keep_near, 9)
    ws = W[src]
    a = ws[i][1] - 0.06
    b = ws[j][1] - 0.05
    return (src, a, b, " ".join(w[0] for w in ws[i:j]))


def raw(src, a, b, why):
    return (src, a, b, why)


def end_of(src, phrase, near):
    i = find(src, phrase, near)
    k = len([t for t in phrase.split() if norm(t)])
    return W[src][i + k - 1][2]


LAST = {"intro": 2679, "demo": 21814}  # real frame counts (ffprobe -count_packets)
RANGE["intro"] = (1.45, min(end_of("intro", "not necessarily writing though", 105) + 0.35, (LAST["intro"] - 1) / FPS))
RANGE["demo"] = (1.18, min(end_of("demo", "see you in the next video", 902) + 0.4, (LAST["demo"] - 1) / FPS))

REMOVE = [
    # ---- intro
    cut("intro", "Opus 5 and all excuse", 15.8, "Opus 5.5, and all of those", 19.0),
    cut("intro", "Again, welcome to", 39.3, "If you are possibly", 42.3),
    cut("intro", "try out AI.", 69.1, "Try out my course", 71.5),
    cut("intro", "best, the", 99.2, "best model", 100.0),
    # ---- demo
    cut("demo", "is actually supposed to include", 4.2, "it's supposed to include the", 8.5),
    cut("demo", "but but", 16.1, "but I'm going", 16.4),
    cut("demo", "uh image generation", 40.5, "image generation", 41.4),
    cut("demo", "And this is and", 86.2, "and that entire video", 87.4),
    cut("demo", "that I came across", 110.3, "that I built with", 114.2),
    cut("demo", "for my client", 124.1, "a mock-up for", 131.6),
    cut("demo", "and uh I also", 135.0, "I also hope", 135.8),
    raw("demo", 166.0, 185.85, "[client video playback trimmed to a 16s highlight] + and I was able and you know"),
    cut("demo", "I bet I could get a real", 190.1, "I bet that I could", 194.7),
    cut("demo", "vertical a", 199.1, "horizontal version of this video watch", 200.3),
    cut("demo", "and uh I can't", 213.7, "I can't wait", 214.2),
    cut("demo", "right in right", 222.2, "right for me", 222.8),
    cut("demo", "two-story engine,", 240.8, "story engine built", 247.5),
    cut("demo", "uh I hand", 273.0, "I hand it over", 273.8),
    cut("demo", "and it what what", 283.3, "what gets me", 284.7),
    cut("demo", "you if you look", 286.4, "if you look right", 286.7),
    cut("demo", "It doesn't", 292.9, "kind of the background", 300.5),
    cut("demo", "a real a real", 326.8, "a real blender", 330.2),
    cut("demo", "write a uh build", 355.8, "draw a", 358.6),
    cut("demo", "a artist a better", 359.2, "a better", 361.4),
    cut("demo", "uh version of this", 362.4, "version of this", 362.8),
    cut("demo", "where how far", 378.2, "how far it had", 378.6),
    cut("demo", "and so it this is how", 380.6, "this is how far I really", 382.7),
    cut("demo", "um a aggregator", 428.2, "a aggregator", 428.8),
    cut("demo", "and I am it it it", 447.1, "it did an exceptional", 449.0),
    cut("demo", "in my fur", 463.0, "in my first universe", 463.9),
    cut("demo", "And really has a uh", 533.1, "has different aspects", 537.0),
    cut("demo", "a a simulation", 573.3, "a simulation", 574.2),
    cut("demo", "Four expressions that I had,", 594.6, "full expressions", 597.5),
    cut("demo", "it was completely so yeah", 626.0, "it first generated", 638.0),
    cut("demo", "effectively", 676.4, "everything you uh just", 711.2) if False else
    raw("demo", end_of("demo", "effectively", 676.3) + 0.25, 711.16, "[33s dead air] + everything uh"),
    cut("demo", "uh just saw", 712.2, "just saw is opus", 712.6),
    cut("demo", "And you st", 749.7, "and it's still in there", 750.3),
    cut("demo", "that people should uh", 767.4, "I don't think people need", 769.0),
    cut("demo", "on my uh", 774.4, "I feel like anthropic", 775.4),
    cut("demo", "It's just it's", 784.3, "it's just wrong", 785.4),
    cut("demo", "to do that to", 811.3, "to do that myself", 812.3),
    cut("demo", "Uh to with bootstrap?", 834.2, "I didn't give it that", 836.5),
    cut("demo", "I have a uh", 838.5, "Have a complete thing", 840.2),
    cut("demo", "It's got it", 857.0, "it did 10 things", 858.8),
]
# fix the entry above that used an inline conditional (keep file readable for vetoes)
REMOVE = [r for r in REMOVE if r]

KEEP_PAUSE = 0.32


def silence_trims(src):
    out = []
    lo, hi = RANGE[src]
    starts = [w[1] for w in W[src]]
    for s, e in SIL[src]:
        if e - s < 0.55 or e <= lo or s >= hi:
            continue
        a, b = s + KEEP_PAUSE / 2, e - KEEP_PAUSE / 2
        # never trim across a transcribed word (quiet words sit under the -45 dB gate)
        inside = [t for t in starts if a - 0.12 < t < b + 0.05]
        if inside:
            b = min(inside) - 0.12
            if b - a < 0.2:
                continue
        out.append((src, a, b, f"[silence {e - s:.2f}s]"))
    return out


def snap(t):
    return round(round(t * FPS) / FPS, 6)


segs = []
removed_all = []
for src in ("intro", "demo"):
    rem = sorted([r for r in REMOVE if r[0] == src] + silence_trims(src), key=lambda r: r[1])
    merged = []
    for s, a, b, why in rem:
        if merged and a <= merged[-1][2] + 0.02:
            merged[-1] = (s, merged[-1][1], max(merged[-1][2], b), merged[-1][3] + " + " + why)
        else:
            merged.append((s, a, b, why))
    removed_all += merged
    cur, hi = RANGE[src]
    for s, a, b, why in merged:
        if a > cur:
            segs.append([src, cur, a])
        cur = max(cur, b)
    segs.append([src, cur, hi])

out, t = [], 0.0
for src, a, b in segs:
    a, b = snap(a), snap(b)
    if b - a < 0.12:
        continue
    out.append({"src": src, "src_in": a, "src_out": b, "edit_in": round(t, 6)})
    t += b - a
    out[-1]["edit_out"] = round(t, 6)


def to_edit(src, ts):
    for s in out:
        if s["src"] == src and s["src_in"] <= ts < s["src_out"]:
            return s["edit_in"] + ts - s["src_in"]
    return None


words = []
for src in ("intro", "demo"):
    for w, a, b in W[src]:
        ea = to_edit(src, a + 0.01)
        if ea is not None:
            words.append({"w": w, "s": round(ea, 3), "src": src, "t": a})
json.dump({"duration": round(t, 6), "segments": out, "removed": removed_all, "words": words},
          open("edl.json", "w"), indent=1)
intro_len = next(s["edit_in"] for s in out if s["src"] == "demo")
print(f"segments={len(out)} intro={intro_len:.1f}s total={t:.1f}s (source {RANGE['intro'][1] - 1.45 + RANGE['demo'][1] - 1.18:.1f}s)")
for s, a, b, why in removed_all:
    if not why.startswith("[silence"):
        print(f"  {s:5} {a:7.2f}-{b:7.2f} {why[:70]}")
