# Phase 1, step 5 checks: is each plain version OK to train on?
# Run: python3 -I check_pairs.py [data/pairs_mine.jsonl]   → prints a summary and writes <file>_flagged.jsonl
# Flags a pair when the plain version
#   - copies Steve: shares too many 4-word phrases with the original (model would learn to copy, not rewrite)
#   - drops numbers: a number Steve said is missing (model would learn to make things up)
#   - is too short or too long compared with the original
#   - is out of order: each plain sentence is matched to the Steve sentence it shares most words with; "order" = share of
#     neighbouring plain sentences whose matches go forward (1.0 = same order as Steve). Added for v3 (2026-10-14).
import json, re, sys

def grams(t, n=4):
    w = re.findall(r"[a-z0-9']+", t.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}

WORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORDS.update(thirty="30", forty="40", fifty="50", hundred="100", thousand="1000", million="1000000", billion="1000000000")

def digits(t):  # numbers Steve said, as digits ("$60", "1947"); spelled-out words like "one" are too ambiguous
    return set(re.findall(r"\d[\d.]*\d|\d", t.replace(",", "")))

def numbers(t):  # numbers in the plain version, digits or words
    t = re.sub(r"[a-z]+", lambda m: WORDS.get(m.group(), m.group()), t.lower().replace(",", ""))
    return set(re.findall(r"\d[\d.]*\d|\d", t))

STOP = set("the a an and or but so of to in on is it that this i you we they he was were be are for with as at have had do not".split())
def sents(t): return [set(re.findall(r"[a-z0-9']+", x.lower())) - STOP for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
def order(steve, plain):
    S = sents(steve)
    m = [max(range(len(S)), key=lambda i: len(p & S[i])) for p in sents(plain) if p]
    return sum(b >= a for a, b in zip(m, m[1:])) / max(len(m) - 1, 1)

PAIRS = sys.argv[1] if len(sys.argv) > 1 else "data/pairs.jsonl"
chunks = {json.loads(l)["id"]: json.loads(l) for l in open("data/chunks_clean.jsonl" if "_v3" in PAIRS else "data/chunks.jsonl")}
pairs = [json.loads(l) for l in open(PAIRS)]
flagged, orders = [], []
for p in pairs:
    steve, plain = chunks[p["id"]]["text"], p["plain"]
    g = grams(steve)
    copy = len(g & grams(plain)) / max(len(g), 1)
    missing = digits(steve) - numbers(plain)
    ratio = len(plain.split()) / len(steve.split())
    orders.append(order(steve, plain))
    why = [w for w, bad in [(f"copies {copy:.0%} of 4-word phrases", copy > 0.15),
                            (f"missing numbers {sorted(missing)}", bool(missing)),
                            (f"length {ratio:.0%} of original", not 0.35 <= ratio <= 1.3)] if bad]
    if why: flagged.append({"id": p["id"], "why": why})
with open(PAIRS.replace(".jsonl", "_flagged.jsonl"), "w") as o:
    for f in flagged: o.write(json.dumps(f) + "\n")
print(f"{len(pairs)} pairs, {len(flagged)} flagged ({100 * len(flagged) / max(len(pairs), 1):.0f}%)")
print(f"  order (1.0 = same order as Steve): average {sum(orders) / len(orders):.2f}, below 0.7: {sum(o < 0.7 for o in orders)}")
for kind in ["copies", "missing numbers", "length"]:
    print(f"  {kind}: {sum(any(w.startswith(kind) for w in f['why']) for f in flagged)}")
