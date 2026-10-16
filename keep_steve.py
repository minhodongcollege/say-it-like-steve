# Phase 1, step 3: keep only Steve's sentences.
# How: make a "voiceprint" of Steve from audio where only he talks, then compare every sentence's voice to it.
# Run: uv run --with speechbrain --with torch --with torchaudio --with soundfile python -I keep_steve.py [talk names]
# Writes data/steve/<talk>.json (every sentence + score + steve yes/no) and <talk>.txt (Steve's lines only).
import glob, json, os, subprocess, sys
import numpy as np, torch
from speechbrain.inference.speaker import EncoderClassifier

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# CPU like the first run (2026-10-15: newer speechbrain picks the Mac GPU by default and .numpy() fails)
enc = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir=os.path.expanduser("~/.cache/ecapa"), run_opts={"device": "cpu"})
SR = 16000

def load(talk):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"data/audio/{talk}.m4a", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)

def embed(wav, start, end):
    clip = wav[int(start * SR):int(end * SR)]
    if len(clip) < SR * 0.8: return None                     # too short to recognize a voice
    with torch.no_grad():
        e = enc.encode_batch(torch.from_numpy(clip.copy())[None]).squeeze()
    return (e / e.norm()).numpy()

def sentences(talk):
    return json.load(open(f"data/transcripts/{talk}.json"))["sentences"]

# Voiceprints from audio where only Steve talks, at three ages (1983, 2005, 2007).
REFS = [("1983-06_idca-aspen-talk", 30, 900), ("2005-06-12_stanford", 25, 880), ("2007-01-09_iphone", 60, 600)]
refs = []
for talk, a, b in REFS:
    wav = load(talk)
    es = [e for s in sentences(talk) if a <= s["start"] and s["end"] <= b and (e := embed(wav, s["start"], s["end"])) is not None]
    m = np.mean(es, 0); refs.append(m / np.linalg.norm(m))

THRESHOLD = 0.45   # ponytail: one fixed cutoff, tuned by reading results; per-talk tuning if some talks come out wrong

os.makedirs("data/steve", exist_ok=True)
talks = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob("data/transcripts/*.json"))
for talk in talks:
    wav, S = load(talk), sentences(talk)
    E = [embed(wav, s["start"], s["end"]) for s in S]
    score = [max(float(e @ r) for r in refs) if e is not None else None for e in E]
    # Second pass: a voiceprint of Steve from THIS talk (same mic, same age), built from the sentences we're surest about.
    sure = [e for e, sc in zip(E, score) if sc is not None and sc >= 0.6]
    if len(sure) >= 10:
        own = np.mean(sure, 0); own /= np.linalg.norm(own)
        score = [max(sc, float(e @ own)) if e is not None else None for e, sc in zip(E, score)]
    # Short lines ("Yeah.") have no score: they take the label of the sentences around them.
    steve = []
    for i, sc in enumerate(score):
        if sc is None:
            near = [x for x in score[max(0, i - 2):i + 3] if x is not None]
            sc = float(np.mean(near)) if near else 0
        steve.append(sc >= THRESHOLD)
    out = [dict(s, score=None if sc is None else round(sc, 3), steve=st) for s, sc, st in zip(S, score, steve)]
    json.dump(out, open(f"data/steve/{talk}.json", "w"), indent=1)
    open(f"data/steve/{talk}.txt", "w").write("\n".join(s["text"].strip() for s in out if s["steve"]) + "\n")
    kept = sum(len(s["text"].split()) for s in out if s["steve"]); total = sum(len(s["text"].split()) for s in out)
    print(f"{talk:36} kept {kept:6} of {total:6} words ({100 * kept / total:4.1f}%)")
