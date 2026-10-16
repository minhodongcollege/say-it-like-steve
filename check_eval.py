# Phase 3, step 10: automatic checks on test outputs.
# Run: python3 -I check_eval.py data/eval/model.jsonl data/eval/baseline.jsonl
# For each output:
#   copied  = longest word-for-word stretch copied from Steve's TRAINING transcripts (memorization)
#   apple   = Apple words that weren't in the input (shortcut: it learned "talk about Apple", not "talk like Steve")
#   missing = numbers from the input that disappeared (facts lost)
#   repeats = 4-word phrases used 2+ times in the same output (rambling)
import glob, json, re, sys

def words(t): return re.findall(r"[a-z0-9']+", t.lower())

train_talks = {json.loads(l)["talk"] for f in glob.glob("data/train*/train.jsonl") for l in open(f)}  # v1 + v3 + v4 (new talks)
N = 8
train_grams = set()
for l in open("data/chunks.jsonl"):
    c = json.loads(l)
    if c["talk"] in train_talks:
        w = words(c["text"]); train_grams.update(tuple(w[i:i + N]) for i in range(len(w) - N + 1))

APPLE = re.compile(r"\b(apple|mac|macs|macintosh|ipod|iphone|ipad|itunes|pixar|woz|wozniak)\b", re.I)
def apple_words(t): return {m.lower() for m in APPLE.findall(t)} | ({"NeXT"} if "NeXT" in t else set())  # NeXT only with its capitals, "next" is a normal word
def numbers(t): return set(re.findall(r"\d[\d.]*\d|\d", t.replace(",", "")))

def longest_copy(t):
    w = words(t); best = run = 0
    for i in range(len(w) - N + 1):
        run = run + 1 if tuple(w[i:i + N]) in train_grams else 0
        best = max(best, run)
    return best + N - 1 if best else 0

def repeats(t):
    w = words(t); g = [tuple(w[i:i + 4]) for i in range(len(w) - 3)]
    return sum(1 for x in set(g) if g.count(x) >= 2)

inputs = {json.loads(l)["eid"]: json.loads(l) for l in open("data/eval/inputs.jsonl")}
for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path)]
    print(f"\n== {path}  ({len(rows)} outputs)")
    tot = dict(copied=0, apple=0, missing=0, repeats=0)
    for r in rows:
        inp = inputs[r["eid"]]["input"]; out = r["output"]
        c, a = longest_copy(out), apple_words(out) - apple_words(inp)
        m, rp = numbers(inp) - numbers(out), repeats(out)
        tot["copied"] += c >= 12; tot["apple"] += bool(a) and r["eid"].startswith("mine"); tot["missing"] += bool(m); tot["repeats"] += rp
        flags = [f"copied {c} words" if c >= 12 else "", f"Apple words {sorted(a)}" if a else "", f"lost numbers {sorted(m)}" if m else "", f"{rp} repeated phrases" if rp >= 3 else ""]
        flags = [f for f in flags if f]
        if flags: print(f"  {r['eid']:28} " + "; ".join(flags))
    print(f"  TOTAL: copies of 12+ words: {tot['copied']} | my writings with new Apple words: {tot['apple']}/7 | lost numbers: {tot['missing']} | repeated phrases: {tot['repeats']}")
