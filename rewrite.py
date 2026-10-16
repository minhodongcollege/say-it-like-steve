# Step 12, the tool: rewrite text the way Steve Jobs would say it.
#   ./steve                     rewrite what's on the clipboard with Claude + 8 real Steve examples; result is copied back
#   ./steve "my text..."        or pipe text in
#   ./steve --local             my fine-tuned model instead (free, offline, ~15 s)
#   ./steve --local --adapter none   plain Gemma, no training (for comparison)
# Default = Claude since 2026-10-16: in my blind read I picked Claude 5 of 6 times over my v3 model.
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SYSTEM = "Rewrite the user's text the way Steve Jobs would say it. Keep the same facts and meaning."  # same as in training
ADAPTER = "adapters/gemma4-12b-v3-best"   # best so far (2026-10-14); switch to v4 if it wins
p = argparse.ArgumentParser()
p.add_argument("text", nargs="?")
p.add_argument("--local", action="store_true")
p.add_argument("--adapter", default=ADAPTER)
p.add_argument("--temp", type=float, default=0.4)  # tested: 1.0 incoherent, 0.6-0.7 loops more
a = p.parse_args()
UTF8 = {**os.environ, "LANG": "en_US.UTF-8"}   # else the clipboard garbles dashes and curly quotes
text = a.text or (sys.stdin.read() if not sys.stdin.isatty() else subprocess.run(["pbpaste"], capture_output=True, text=True, env=UTF8).stdout)
if not text.strip(): sys.exit("Nothing to rewrite: copy some text first, or pass it in quotes.")

if not a.local:
    if not shutil.which("claude"): sys.exit("This mode needs Claude Code installed and logged in (https://claude.com/claude-code). Or train your own model and use --local.")
    examples = open(os.path.join(HERE, "data/eval/baseline_examples.md")).read()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE_CODE_", "CLAUDE_AGENT_SDK"))}  # works from inside Claude sessions too
    r = subprocess.run(["claude", "-p", "--tools", "", "--system-prompt",
                        SYSTEM + " Output only the rewritten text.\n\nHere is how he really talked:\n\n" + examples],
                       input="Rewrite this:\n\n" + text, capture_output=True, text=True, env=env, cwd="/tmp")
    if r.returncode: sys.exit(r.stderr or r.stdout)
    out = r.stdout.strip()
else:
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler, make_logits_processors
    adapter = None if a.adapter == "none" else os.path.join(HERE, a.adapter)
    if adapter and not os.path.isdir(adapter): sys.exit(f"No trained model at {a.adapter}. Train one first (see README), or run without --local.")
    model, tok = load("mlx-community/gemma-4-12B-it-qat-4bit", adapter_path=adapter)
    # Same prompt format as training (mlx-lm's default for Gemma 4, with its "thinking" switch on); the trained model answers directly.
    prompt = tok.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
                                     add_generation_prompt=True, tokenize=False)
    # Google's recommended Gemma sampling + a repetition penalty (without it the model sometimes looped)
    out = generate(model, tok, prompt, max_tokens=800, sampler=make_sampler(temp=a.temp, top_p=0.95, top_k=64),
                   logits_processors=make_logits_processors(repetition_penalty=1.1, repetition_context_size=64))
    out = re.sub(r"<\|channel>.*?(<channel\|>|$)", "", out, flags=re.S).strip()  # safety net: drop any "thinking" text

print(out)
subprocess.run(["pbcopy"], input=out, text=True, env=UTF8)  # ready to paste
