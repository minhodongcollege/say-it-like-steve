# Phase 1, step 5: make the "plain" side of each pair (back-translation).
# A free open model (Qwen3 30B, runs on this Mac) rewrites each Steve chunk with the same facts but without his style.
# Two kinds of plain side:
#   plain  → data/pairs.jsonl       flat, ordinary memo-style paragraph
#   mine   → data/pairs_mine.jsonl  the flat version rewritten the way I (Minho) write (samples: data/minho_writing.json),
#                                   so the model learns exactly the job I'll give it: my writing → Steve's way of saying it
# Run: uv run --with mlx-lm python -I make_pairs.py plain|mine [how many]   (safe to re-run: chunks already done are skipped)
# v3 (2026-10-14): PLAIN now keeps the speaker's order of ideas. v1 said "main point first, then the details", so the
#   plain side was reshuffled and the model learned to scramble stories. Made from the cleaned chunks (clean_steve.py).
#   v1 files: data/pairs.jsonl, data/pairs_mine.jsonl (from data/chunks.jsonl).
import json, os, random, re, sys
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

os.chdir(os.path.dirname(os.path.abspath(__file__)))
MODEL = "mlx-community/Qwen3-30B-A3B-Instruct-2507-4bit"
KEEP = """- Keep EVERY fact, number, name, example, story event and claim, with exactly the same meaning. Do not add anything that is not in the passage.
- Keep the same point of view (I, we, you).
- Use different words and sentence structure from the original. Never copy a phrase of 4 or more words, except names, numbers and technical terms.
- Output only the rewritten text."""
PLAIN = f"""Below is a passage of someone speaking. Rewrite it as a plain, flat written paragraph, the way an ordinary person would write it down in a memo or in notes.

Rules:
{KEEP}
- Keep the ideas in EXACTLY the same order as the speaker. Go through the passage from start to end and write one plain sentence or two for each thing he says, in the order he says it. Do not move the main point to the front, do not group or reorder anything.
- Keep side comments and small details too (as plain statements), unless they are only filler like "you know" or "yeah".
- If the speaker uses a comparison or analogy, keep it, but state it in one short, flat sentence.
- Remove all style: no questions to the audience, no repetition for effect, no build-ups or reveals, no lists of three for rhythm, no short punchy sentences, no exclamations, no jokes, no "you know".
- Use medium-length, ordinary sentences.

Passage:
"""
MINE = """Here are real examples of how Minho writes. This is his own unedited writing (English is his second language):

{examples}

What his writing is like: simple everyday words (kinda, a lot of, stuff, things, pretty, really, super); he sometimes starts with "I think", "I feel like", "So", "And", "But", "Let's say", "for example"; he joins ideas with "and" and "so" into longer sentences; he sometimes drops "the" or "a", uses a wrong verb form or a slightly off word; few commas; he explains in a straightforward order without drama.

Below is a short plain text. Rewrite EVERY sentence the way Minho would write it himself, as a draft he typed to explain this same content. It must clearly sound like Minho, not like the plain text: change the words and the way sentences are joined. Use normal capitalization.

Rules:
- Keep every fact, number, name and claim with exactly the same meaning. Do not add anything new: no new examples, no new opinions, no conclusions that are not in the text.
- Do not add questions to the reader, jokes, or dramatic lines.
- Keep the same point of view (I, we, you).
- Keep the ideas in exactly the same order as the plain text.
- Write it as an explanation in paragraph form, not as instructions or a chat message.
- Output only the rewritten text.

Plain text:
"""

mode = sys.argv[1]
V = "_v3"
out_path = {"plain": f"data/pairs{V}.jsonl", "mine": f"data/pairs_mine{V}.jsonl"}[mode]
samples = json.load(open("data/minho_writing.json"))

def examples(chunk_id):
    rng = random.Random(chunk_id)  # same examples every time for the same chunk
    pick = [rng.choice([s for s in samples if s["source"] == "LinkedIn draft"]),
            rng.choice([s for s in samples if s["source"] == "college essay"])]
    pick += rng.sample([s for s in samples if s["source"] == "chat message"], 4)
    return "\n\n".join(f"Example {i + 1}:\n" + " ".join(s["text"].split()[:150]) for i, s in enumerate(pick))

flat = {json.loads(l)["id"]: json.loads(l)["plain"] for l in open(f"data/pairs{V}.jsonl")} if mode == "mine" else {}

def prompt_for(c):
    if mode == "plain": return PLAIN + c["text"]
    # Built from the flat version, not from Steve, so none of his style can leak into "my" side.
    return MINE.format(examples=examples(c["id"])) + flat[c["id"]]

def fix_case(text, ref):
    """The model tends to write all lowercase. Restore capitals: sentence starts, "I", and names from the flat version."""
    names = {w.lower(): w for w in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][\w'’-]+", ref)}  # 2+ letters: "S" in "U.S." broke "that's"
    text = re.sub(r"[A-Za-z][\w'’-]*", lambda m: names.get(m.group().lower(), m.group()), text)
    text = re.sub(r"\bi\b", "I", text)
    text = re.sub(r"\bi('m|'ve|'ll|'d)\b", lambda m: "I" + m.group(1), text)
    return re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)

chunks = [json.loads(l) for l in open("data/chunks_clean.jsonl")]  # v3: Steve's side after clean_steve.py
done = {json.loads(l)["id"] for l in open(out_path)} if os.path.exists(out_path) else set()
todo = [c for c in chunks if c["id"] not in done and (mode == "plain" or c["id"] in flat)][: int(sys.argv[2]) if len(sys.argv) > 2 else None]
model, tok = load(MODEL)
sampler = make_sampler(temp=0.5 if mode == "plain" else 0.8)
with open(out_path, "a") as out:
    for i, c in enumerate(todo):
        prompt = tok.apply_chat_template([{"role": "user", "content": prompt_for(c)}], add_generation_prompt=True, tokenize=False)
        plain = generate(model, tok, prompt, max_tokens=700, sampler=sampler).strip()
        if mode == "mine": plain = fix_case(plain, flat[c["id"]])
        out.write(json.dumps({"id": c["id"], "plain": plain}) + "\n"); out.flush()
        print(f"{i + 1}/{len(todo)} {c['id']} {c['words']} -> {len(plain.split())} words", flush=True)
