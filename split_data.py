# Phase 1, step 6: split the pairs into train / validation / test, by WHOLE TALK (Steve reused lines across talks,
# so a talk in both training and test would make the test too easy).
# Run: python3 -I split_data.py [out dir]   → data/train_v3/{train,valid,test}.jsonl (or out dir) in the chat format mlx-lm reads.
# v4 (2026-10-15): same v3 recipe + 9 young talks (they all land in train) → python3 -I split_data.py data/train_v4
# v3 (2026-10-14): cleaned Steve side (data/chunks_clean.jsonl) + order-keeping pairs (*_v3) → data/train_v3/. v1 = V="".
# Uses both kinds of pairs (flat → Steve and my style → Steve); leaves out pairs that copy more than 25% of Steve's phrases.
import json, os, random, re, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
TEST = {"2003-05_d1-interview", "1994_svha-interview", "2001-10-23_ipod"}      # final exam, opened once at the end
VALID = {"2005-05_d3-interview", "2011-06-06_wwdc-icloud"}                     # practice quiz, checked during training
SYSTEM = "Rewrite the user's text the way Steve Jobs would say it. Keep the same facts and meaning."

V = "_v3"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"data/train{V}"
chunks = {json.loads(l)["id"]: json.loads(l) for l in open("data/chunks_clean.jsonl" if V else "data/chunks.jsonl")}

def copy_too_much(flagged_file):
    out = set()
    for l in open(flagged_file):
        f = json.loads(l)
        for w in f["why"]:
            m = re.match(r"copies (\d+)%", w)
            if m and int(m.group(1)) > 25: out.add(f["id"])
    return out

rows = {"train": [], "valid": [], "test": []}
dropped = 0
for pairs, flagged, kind in [(f"data/pairs{V}.jsonl", f"data/pairs{V}_flagged.jsonl", "flat"),
                             (f"data/pairs_mine{V}.jsonl", f"data/pairs_mine{V}_flagged.jsonl", "mine")]:
    skip = copy_too_much(flagged)
    for l in open(pairs):
        p = json.loads(l)
        if p["id"] in skip: dropped += 1; continue
        c = chunks[p["id"]]
        split = "test" if c["talk"] in TEST else "valid" if c["talk"] in VALID else "train"
        rows[split].append({"messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": p["plain"]},
                                         {"role": "assistant", "content": c["text"]}],
                            "id": p["id"], "kind": kind, "talk": c["talk"]})

os.makedirs(OUT, exist_ok=True)
random.seed(0)
for split, rs in rows.items():
    random.shuffle(rs)  # mix talks and both pair kinds so training doesn't see one talk at a time
    with open(f"{OUT}/{split}.jsonl", "w") as o:
        for r in rs: o.write(json.dumps(r) + "\n")
    print(f"{split:5} {len(rs):5} pairs from {len({r['talk'] for r in rs})} talks")
print(f"left out for copying Steve: {dropped}")
assert not ({r["talk"] for r in rows["train"]} & {r["talk"] for r in rows["test"] + rows["valid"]})  # no talk leaks across splits
