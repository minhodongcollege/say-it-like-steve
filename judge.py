# Phase 3, step 10: blind A/B judging of two sets of outputs.
# Each item appears twice with A/B swapped, so a judge that always prefers "A" (or "B") can't tip the score.
#   python3 -I judge.py build <tag> <x.jsonl> <y.jsonl>     → data/eval/judge/<tag>_tasks.json (+ hidden _key.json)
#   uv run --with mlx-lm python -I judge.py qwen <tag>       → Qwen3 30B (local) judges   → <tag>_qwen.jsonl
#   (a Claude helper can write <tag>_claude.jsonl from the same tasks file, without seeing the key)
#   python3 -I judge.py score <tag>
import json, os, random, sys
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
D = "data/eval/judge"
cmd, tag = sys.argv[1], sys.argv[2]

def build(x_path, y_path):
    I = {json.loads(l)["eid"]: json.loads(l) for l in open("data/eval/inputs.jsonl")}
    out = {name: {json.loads(l)["eid"]: json.loads(l)["output"] for l in open(p)}
           for name, p in [(os.path.basename(x_path)[:-6], x_path), (os.path.basename(y_path)[:-6], y_path)]}
    (xn, X), (yn, Y) = out.items()
    # 3 style references from training talks, not the ones the few-shot baselines were shown
    used = open("data/eval/baseline_examples.md").read()
    train_talks = {json.loads(l)["talk"] for l in open("data/train/train.jsonl")}
    pool = [json.loads(l) for l in open("data/chunks.jsonl")]
    random.seed(21)
    refs = random.sample([c["text"] for c in pool if c["talk"] in train_talks and c["text"][:80] not in used and 110 <= c["words"] <= 170], 3)
    tasks, key, n = [], {}, 0
    for e in I:
        for a, b in ((xn, yn), (yn, xn)):
            n += 1; tid = f"t{n:02d}"
            tasks.append({"tid": tid, "A": out[a][e], "B": out[b][e], "real_steve": I[e].get("steve")})
            key[tid] = {"eid": e, "A": a, "B": b}
    random.seed(22); random.shuffle(tasks)
    os.makedirs(D, exist_ok=True)
    json.dump({"style_examples": refs, "tasks": tasks}, open(f"{D}/{tag}_tasks.json", "w"), indent=1)
    json.dump(key, open(f"{D}/{tag}_key.json", "w"), indent=1)
    print(f"{len(tasks)} tasks: {xn} vs {yn}")

def prompt(J, t):
    ex = "\n\n".join(f"Example {i + 1}:\n{x}" for i, x in enumerate(J["style_examples"]))
    ref = (f"\n\nHere is what Steve Jobs actually said in this case:\n{t['real_steve']}\n\nWhich text, A or B, is closer to how he actually said it?"
           if t["real_steve"] else "\n\nWhich text, A or B, sounds more like Steve Jobs speaking?")
    return (f"Here are real transcripts of Steve Jobs speaking:\n\n{ex}\n\nText A:\n{t['A']}\n\nText B:\n{t['B']}{ref} "
            "Judge only the way of speaking (word choice, sentence structure, how ideas are explained), not which is better writing. "
            "Answer with one letter only: A or B.")

def qwen():
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    J = json.load(open(f"{D}/{tag}_tasks.json"))
    model, tok = load("mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit")
    with open(f"{D}/{tag}_qwen.jsonl", "w") as out:
        for t in J["tasks"]:
            p = tok.apply_chat_template([{"role": "user", "content": prompt(J, t)}], add_generation_prompt=True, tokenize=False)
            a = generate(model, tok, p, max_tokens=5, sampler=make_sampler(temp=0.0)).strip()[:1].upper()
            out.write(json.dumps({"tid": t["tid"], "pick": a}) + "\n")

def score():
    key = json.load(open(f"{D}/{tag}_key.json"))
    names = sorted({k["A"] for k in key.values()})
    for judge in ["qwen", "claude"]:
        path = f"{D}/{tag}_{judge}.jsonl"
        if not os.path.exists(path): continue
        wins = Counter()
        for l in open(path):
            j = json.loads(l); k = key[j["tid"]]
            if j["pick"] in ("A", "B"):
                wins[("test talks (vs real Steve)" if k["eid"].startswith("test") else "my writings", k[j["pick"]])] += 1
        print(f"\n{judge} judge:")
        for g in ["my writings", "test talks (vs real Steve)"]:
            a, b = wins[(g, names[0])], wins[(g, names[1])]
            print(f"  {g:28} {names[0]} {a:2} | {names[1]} {b:2}  → {names[0]} wins {100 * a / max(a + b, 1):.0f}%")

if cmd == "build": build(sys.argv[3], sys.argv[4])
elif cmd == "qwen": qwen(); score()
elif cmd == "score": score()
