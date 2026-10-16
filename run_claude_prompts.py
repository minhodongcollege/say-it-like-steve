# Does the real Steve data matter, or is a plain prompt enough? (2026-10-16)
# Runs Claude (Claude Code CLI, same model for both) on every test input two ways:
#   zeroshot → only "Rewrite this the way Steve Jobs would say it"       → data/eval/claude_zeroshot.jsonl
#   fewshot  → the same + 8 real Steve excerpts (exactly what ./steve does) → data/eval/claude_fewshot.jsonl
# Run: python3 -I run_claude_prompts.py      then judge with judge.py (build / qwen / score)
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SYSTEM = "Rewrite the user's text the way Steve Jobs would say it. Keep the same facts and meaning. Output only the rewritten text."
EXAMPLES = open("data/eval/baseline_examples.md").read()
ENV = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDE_AGENT_SDK"))}
inputs = [json.loads(l) for l in open("data/eval/inputs.jsonl")]

def run(system, text):
    r = subprocess.run(["claude", "-p", "--tools", "", "--system-prompt", system], input="Rewrite this:\n\n" + text,
                       capture_output=True, text=True, env=ENV, cwd="/tmp")
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    return r.stdout.strip()

for name, system in [("zeroshot", SYSTEM), ("fewshot", SYSTEM + "\n\nHere is how he really talked:\n\n" + EXAMPLES)]:
    with ThreadPoolExecutor(4) as pool:
        outs = list(pool.map(lambda r: run(system, r["input"]), inputs))
    with open(f"data/eval/claude_{name}.jsonl", "w") as f:
        for r, o in zip(inputs, outs): f.write(json.dumps({"eid": r["eid"], "output": o}) + "\n")
    print(name, len(outs), "outputs")
