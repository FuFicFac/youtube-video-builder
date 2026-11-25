"""EDL for an example talking-head video (single source, src.mp4).
EXAMPLE DATA: the flub phrases, timestamps and notes below are stand-ins from one edit; replace them all.
Cuts anchored on Parakeet word starts; silences tightened (never across a word start).
Output edl.json: segments [{src_in, src_out, edit_in, edit_out}] + removed + edited words.
"""
import json, re

FPS = 24000 / 1001
W = json.load(open("src_words.json"))
SIL = json.load(open("src_sil.json"))
LAST = 7903  # ffprobe -count_packets


def norm(w):
    return re.sub(r"[^a-z0-9$]", "", w.lower())


W = [w for i, w in enumerate(W) if not (i and w[1] - W[i - 1][1] < 0.1 and norm(w[0]) == norm(W[i - 1][0]))]  # ASR double tokens


def find(phrase, near, span=6):
    toks = [norm(t) for t in phrase.split() if norm(t)]
    best = None
    for i in range(len(W) - len(toks) + 1):
        if all(norm(W[i + k][0]) == toks[k] for k in range(len(toks))):
            d = abs(W[i][1] - near)
            if d <= span and (best is None or d < best[0]):
                best = (d, i)
    if best is None:
        raise SystemExit(f"not found {phrase!r} near {near}")
    return best[1]


def cut(first, near, keep, keep_near):
    i, j = find(first, near), find(keep, keep_near, 9)
    return (W[i][1] - 0.06, W[j][1] - 0.05, " ".join(w[0] for w in W[i:j]))


def end_of(phrase, near):
    i = find(phrase, near)
    return W[i + len([t for t in phrase.split() if norm(t)]) - 1][2]


RANGE = (1.1, min(end_of("the description bye", 324.1) + 0.45, (LAST - 1) / FPS))

REMOVE = [
    cut("personal actual personal", 15.6, "personal assistant that", 18.0),
    cut("version five uh no", 112.4, "version six of", 115.3),
    cut("keeping that friction and", 139.4, "keeping you friction", 141.4),
    cut("what they I think", 160.0, "I think it's spelled", 162.1),
    cut("Uh hopefully", 179.8, "hopefully I will", 180.0),
    cut("the model and or like", 226.2, "the lab to release", 227.9),
    cut("$500 level $500", 235.84, "$500 level subscription", 237.84),
    cut("uh actually using", 248.96, "actually using it", 249.44),
    cut("it really the only", 260.96, "the only thing", 261.92),
    cut("2500 uh 50", 266.8, "limit on their context", 276.6),
    cut("that right there honestly", 279.28, "that right there is", 282.32),
    cut("uh uh do me", 318.64, "do me a favor", 319.44),
]
KEEP_PAUSE = 0.32


def silence_trims():
    out, starts = [], [w[1] for w in W]
    for s, e in SIL:
        if e - s < 0.55 or e <= RANGE[0] or s >= RANGE[1]:
            continue
        a, b = s + KEEP_PAUSE / 2, e - KEEP_PAUSE / 2
        inside = [t for t in starts if a - 0.12 < t < b + 0.05]
        if inside:
            b = min(inside) - 0.12
            if b - a < 0.2:
                continue
        out.append((a, b, f"[silence {e - s:.2f}s]"))
    return out


def snap(t):
    return round(round(t * FPS) / FPS, 6)


rem = sorted(REMOVE + silence_trims())
merged = []
for a, b, why in rem:
    if merged and a <= merged[-1][1] + 0.02:
        merged[-1] = (merged[-1][0], max(merged[-1][1], b), merged[-1][2] + " + " + why)
    else:
        merged.append((a, b, why))
segs, cur = [], RANGE[0]
for a, b, why in merged:
    if a > cur:
        segs.append((cur, a))
    cur = max(cur, b)
segs.append((cur, RANGE[1]))
out, t = [], 0.0
for a, b in segs:
    a, b = snap(a), snap(b)
    if b - a < 0.12:
        continue
    out.append({"section": "th_a", "src_in": a, "src_out": b, "edit_in": round(t, 6)})
    t += b - a
    out[-1]["edit_out"] = round(t, 6)


def to_edit(ts):
    for s in out:
        if s["src_in"] <= ts < s["src_out"]:
            return s["edit_in"] + ts - s["src_in"]


words = []
for w, a, b in W:
    ea = to_edit(a + 0.01)
    if ea is not None:
        words.append([w, round(ea, 3), round(ea + (b - a), 3)])
json.dump({"duration": round(t, 6), "segments": out, "removed": merged, "words": words}, open("edl.json", "w"), indent=1)
json.dump(words, open("edit_words.json", "w"))
print(f"segments={len(out)} total={t:.1f}s (source span {RANGE[1] - RANGE[0]:.1f}s)")
with open("../CUT-NOTES.md", "w") as f:
    f.write("# Cut notes — <video title> (source: src.mp4)\n\n"
            f"Source {RANGE[1]-RANGE[0]:.1f}s → edited {t:.1f}s. Silences over 0.55s tightened to 0.32s.\n\n## Flubs removed (source time)\n\n")
    for a, b, why in merged:
        if not why.startswith("[silence"):
            f.write(f"- {int(a // 60)}:{a % 60:04.1f}–{int(b // 60)}:{b % 60:04.1f} — \"{why}\"\n")
    f.write("\n## Veto-able calls\n\n- Kept \"Alright, that's pretty much all I wanted to talk about…\" at 3:34 — it carries the next point, even though it sounds like an ending.\n"
            "- Dropped the stumbled context-limit number (\"2500… 50… 25000… 25000k\") → \"it only has a limit on their context\".\n"
            "- Captions spell product names as the vendor writes them, not as the ASR heard them (list each fix here).\n")
for a, b, why in merged:
    if not why.startswith("[silence"):
        print(f"  {a:7.2f}-{b:7.2f} {why[:70]}")
