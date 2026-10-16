# Phase 3, step 9: run my trained model on every test input in data/eval/inputs.jsonl.
# Run: uv run --with mlx-lm python -I run_eval.py <adapter|none> [out.jsonl] [temperature] [model]   → data/eval/model.jsonl
import json, os, re, sys
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler, make_logits_processors

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SYSTEM = "Rewrite the user's text the way Steve Jobs would say it. Keep the same facts and meaning."  # same as training
adapter = None if sys.argv[1] == "none" else sys.argv[1]   # "none" = plain Gemma, shown 8 real Steve examples instead (fair check)
out_path = sys.argv[2] if len(sys.argv) > 2 else "data/eval/model.jsonl"
BASE = sys.argv[4] if len(sys.argv) > 4 else "mlx-community/gemma-4-12B-it-qat-4bit"
model, tok = load(BASE, adapter_path=adapter)
EXAMPLES = open("data/eval/baseline_examples.md").read() if adapter is None else ""
# Google's recommended Gemma sampling + a repetition penalty: without it the model sometimes looped
# ("And it's why I'm not happy with this." ~50 times, 2026-10-13 test).
TEMP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4   # 1.0 (Google's default) made it incoherent, 0.7 without penalty looped
sampler = make_sampler(temp=TEMP, top_p=0.95, top_k=64)
procs = make_logits_processors(repetition_penalty=1.1, repetition_context_size=64)
with open(out_path, "w") as out:
    for l in open("data/eval/inputs.jsonl"):
        r = json.loads(l)
        if adapter:   # same format as training
            prompt = tok.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": r["input"]}],
                                             add_generation_prompt=True, tokenize=False)
        else:         # untrained: same examples Claude got, thinking off so it answers directly
            prompt = tok.apply_chat_template([{"role": "system", "content": SYSTEM + " Output only the rewritten text.\n\nHere is how he really talked:\n\n" + EXAMPLES},
                                              {"role": "user", "content": r["input"]}], add_generation_prompt=True, tokenize=False, enable_thinking=False)
        text = generate(model, tok, prompt, max_tokens=600, sampler=sampler, logits_processors=procs)
        text = re.sub(r"<\|channel>.*?(<channel\|>|$)", "", text, flags=re.S).strip()
        out.write(json.dumps({"eid": r["eid"], "output": text}) + "\n"); out.flush()
        print(r["eid"], len(text.split()), "words", flush=True)
