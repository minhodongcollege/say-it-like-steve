# Human blind read (2026-10-15): 6 items, my model vs Claude few-shot, A/B hidden. The AI judges disagree, so Minho decides.
# Run: python3 -I make_blind.py data/eval/model_v3.jsonl   → "Blind Read.md" (for him) + data/eval/blind_read_key.json (hidden)
import json, os, random, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
model_path = sys.argv[1]
I = {json.loads(l)["eid"]: json.loads(l) for l in open("data/eval/inputs.jsonl")}
out = {"model": {json.loads(l)["eid"]: json.loads(l)["output"] for l in open(model_path)},
       "claude": {json.loads(l)["eid"]: json.loads(l)["output"] for l in open("data/eval/baseline.jsonl")}}
rng = random.Random(15)
mine = [e for e in I if e.startswith("mine") and e != "mine-research-ai-intro"]   # one personal text left out
test = [e for e in I if e.startswith("test")]
items = rng.sample(mine, 3) + rng.sample(test, 3)   # random, not hand-picked
rng.shuffle(items)

md = ["# Blind read: which one sounds more like Steve Jobs?",
      f"One of **A** / **B** is my trained model ({os.path.basename(model_path)[:-6]}), the other is Claude with 8 real Steve examples. Random order.",
      "Write **A** or **B** after **Pick:**. Judge only: does it sound like Steve *talking* (word choice, sentence shape, how he explains)? Not which is better writing.", ""]
key = {}
for n, e in enumerate(items, 1):
    a, b = rng.sample(["model", "claude"], 2)
    key[n] = {"eid": e, "A": a, "B": b}
    md += [f"## {n}", f"> [!note]- {'My original text' if e.startswith('mine') else 'Plain input'} (click to open)",
           *[f"> {line}" for line in I[e]["input"].splitlines() if line.strip()], ""]
    if I[e].get("steve"):
        md += ["> [!quote]- What Steve really said (to compare)", *[f"> {line}" for line in I[e]["steve"].splitlines() if line.strip()], ""]
    md += [f"**A:** {out[a][e]}", "", f"**B:** {out[b][e]}", "", "**Pick:** ", "", "---", ""]
open("Blind Read.md", "w").write("\n".join(md))
json.dump(key, open("data/eval/blind_read_key.json", "w"), indent=1)
print("items:", items)
