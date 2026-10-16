# v3 (2026-10-14): light cleanup of Steve's side (the training targets). Spoken transcripts are full of false starts
# ("there's something sort of, I think that that, there's going to be"), and v1 learned to write that garble.
# Qwen 30B (local) removes only speech errors; a check then makes sure it only DELETED words (nearly no new words),
# otherwise the original is kept. Also drops a leading "And"/"But"/"Yeah" (chunks often start mid-answer → v1 began 17/27 outputs with "And").
# Run: uv run --with mlx-lm python -I clean_steve.py [how many]   → data/chunks_clean.jsonl (same rows, cleaned "text", "raw" = original)
import difflib, json, os, re, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
PROMPT = """Below is a transcript of Steve Jobs speaking. Clean up speech errors only, so it reads the way he meant to say it.

Rules:
- Remove false starts and abandoned half-sentences (keep the version he finished), stutters, accidentally repeated words, "um" and "uh".
- Keep everything else exactly: his words, word order, sentence structure, informal grammar, "you know", "I mean", "sort of", repetition for effect, questions to the audience, jokes.
- Do not add words. Do not reword, polish or summarize.
- Output only the cleaned transcript.

Examples of what to remove:
- "And there's something sort of, I think that that, there's going to be a little slice" → "And there's going to be a little slice"
- "How many people, how many of you are 36 years, older than 36 years old?" → "How many of you are older than 36 years old?"
- "brought, shared this w the horsepower" → "shared the horsepower"

Transcript:
"""
LEAD = re.compile(r"^(?:(?:And|But|Yeah|Okay|Oh|Um|Uh)\b[,.]?\s+)+", re.I)

def words(t): return re.findall(r"[a-z0-9']+", t.lower())

def only_deleted(raw, clean):
    """Share of the cleaned words that are new (not kept from the original, in order). Near 0 = it only deleted."""
    a, b = words(raw), words(clean)
    kept = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    return (len(b) - kept) / max(len(b), 1), len(b) / max(len(a), 1)

def strip_lead(t):
    t = LEAD.sub("", t)
    return t[:1].upper() + t[1:]

def accept(raw, clean):
    new, kept = only_deleted(raw, clean)
    return new <= 0.03 and kept >= 0.75

if __name__ == "__main__":
    assert strip_lead("And so, yeah. And it works.") == "So, yeah. And it works."
    assert strip_lead("Yeah, and then we did it.") == "Then we did it."
    assert accept("The computer's 36 years old. And I think that that, there's going to be a little slice in the timeline of history as we look back.",
                  "The computer's 36 years old. And there's going to be a little slice in the timeline of history as we look back.")
    assert not accept("I think it's great", "I believe it is truly a wonderful thing")
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    out_path = "data/chunks_clean.jsonl"
    done = {json.loads(l)["id"] for l in open(out_path)} if os.path.exists(out_path) else set()
    todo = [json.loads(l) for l in open("data/chunks.jsonl")]
    todo = [c for c in todo if c["id"] not in done][: int(sys.argv[1]) if len(sys.argv) > 1 else None]
    model, tok = load("mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit")
    with open(out_path, "a") as out:
        for i, c in enumerate(todo):
            p = tok.apply_chat_template([{"role": "user", "content": PROMPT + c["text"]}], add_generation_prompt=True, tokenize=False)
            clean = generate(model, tok, p, max_tokens=600, sampler=make_sampler(temp=0.0)).strip()
            ok = accept(c["text"], clean)
            text = strip_lead(clean if ok else c["text"])
            out.write(json.dumps({**c, "raw": c["text"], "text": text, "words": len(text.split()), "cleaned": ok}) + "\n"); out.flush()
            print(f"{i + 1}/{len(todo)} {c['id']} {'cleaned' if ok else 'KEPT RAW'} {c['words']} -> {len(text.split())}", flush=True)
