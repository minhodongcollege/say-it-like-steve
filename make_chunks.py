# Phase 1, step 4: cut Steve's text into chunks of ~100-250 words, one idea each. Each chunk = one training example.
# Run: python3 -I make_chunks.py
# Reads data/steve/*.json. Writes data/chunks.jsonl (for training), data/demo_dropped.jsonl (left out, to review)
# and data/chunks.md (easy to read in Obsidian). Needs data/demo_labels.json.
import glob, json, os, re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
MIN, MAX = 100, 250
UNSCRIPTED = ["idca", "next-team", "mit-sloan", "svha", "smithsonian", "lost-interview", "fireside", "d1-", "d3-", "d5-", "d8-",
              "interview", "talk"]   # v4 talks (2026-10-15) all have one of these in their name
JUNK = re.compile(r"^(thank you( so much| very much| all)?|thanks|music|applause|\W*)[.!]*$", re.I)
FIXES = [(r"\bWaz\b", "Woz"), (r"\bScully\b", "Sculley"), (r"\bXerox Park\b", "Xerox PARC"),
         (r"\bNextS(tep)?\b", "NeXTSTEP"), (r"(?<=[a-z,] )Next\b", "NeXT")]
# Keynote demo narration (Steve operating a computer on stage, not explaining) is left out. Which chunks are demos was
# decided by an AI reading every keynote chunk (2026-10-13), saved as [talk, start second] in data/demo_labels.json.
DEMO = {tuple(x) for x in json.load(open("data/demo_labels.json"))}

def words(s): return len(s["text"].split())

def fix(t):
    for a, b in FIXES: t = re.sub(a, b, t)
    return t

def blocks(S):
    """Uninterrupted stretches of Steve: cut where someone else says 3+ words or there's 15+ s of silence."""
    out, cur = [], []
    for s in S:
        if not s["steve"]:
            if words(s) >= 3 and cur: out.append(cur); cur = []
            continue
        if JUNK.match(s["text"].strip()): continue
        if cur and s["start"] - cur[-1]["end"] > 15: out.append(cur); cur = []
        cur.append(s)
    return out + ([cur] if cur else [])

def split(block):
    """Cut a long block at sentence ends, choosing the longest pause that keeps both sides 100-250 words."""
    chunks, i = [], 0
    while i < len(block):
        rest = sum(words(s) for s in block[i:])
        if rest <= MAX: chunks.append(block[i:]); break
        best, n = None, 0
        for j in range(i, len(block) - 1):
            n += words(block[j])
            if n > MAX: break
            if n >= MIN and rest - n >= MIN:
                pause = block[j + 1]["start"] - block[j]["end"]
                if best is None or pause > best[0]: best = (pause, j)
        if best is None:  # no clean cut: take as much as fits
            n, j = 0, i
            while j < len(block) and n + words(block[j]) <= MAX: n += words(block[j]); j += 1
            best = (0, max(j - 1, i))
        chunks.append(block[i:best[1] + 1]); i = best[1] + 1
    return [c for c in chunks if sum(words(s) for s in c) >= MIN]

kept, demo = [], []
for f in sorted(glob.glob("data/steve/*.json")):
    talk = os.path.basename(f)[:-5]
    kind = "unscripted" if any(k in talk for k in UNSCRIPTED) else "scripted"
    for block in blocks(json.load(open(f))):
        for c in split(block):
            text = fix(" ".join(s["text"].strip() for s in c))
            w = len(text.split())
            row = dict(talk=talk, kind=kind, start=round(c[0]["start"]), end=round(c[-1]["end"]), words=w, text=text)
            is_demo = (talk, row["start"]) in DEMO
            (demo if is_demo else kept).append(row)

# IDs stay the same when talks are added (v4, 2026-10-15): cleaned text and pairs are saved by ID, so a chunk keeps its old ID
# and new chunks get the next free numbers.
old = {(r["talk"], r["start"]): r for r in map(json.loads, open("data/chunks.jsonl"))} if os.path.exists("data/chunks.jsonl") else {}
nxt = max((int(r["id"][1:]) + 1 for r in old.values()), default=0)
for r in kept:
    o = old.get((r["talk"], r["start"]))
    if o:
        assert o["text"] == r["text"], f"chunk {o['id']} changed: chunking rules changed, so old pairs no longer match"
        r["id"] = o["id"]
    else:
        r["id"] = f"c{nxt:04d}"; nxt += 1
with open("data/chunks.jsonl", "w") as o:
    for r in kept: o.write(json.dumps(r) + "\n")
with open("data/demo_dropped.jsonl", "w") as o:
    for r in demo: o.write(json.dumps(r) + "\n")
with open("data/chunks.md", "w") as o:
    o.write(f"# Steve chunks\n{len(kept)} chunks made by `make_chunks.py`. Each one becomes one training example.\n\n")
    for r in kept:
        o.write(f"### {r['id']} · {r['talk']} · {r['start'] // 60}:{r['start'] % 60:02d} · {r['words']} words\n{r['text']}\n\n")

for k in ["unscripted", "scripted"]:
    rs = [r for r in kept if r["kind"] == k]
    print(f"{k:10} {len(rs):4} chunks, {sum(r['words'] for r in rs):6} words")
print(f"demo narration left out: {len(demo)} chunks, {sum(r['words'] for r in demo)} words")
