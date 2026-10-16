#!/bin/zsh
# Phase 1, step 2: transcribe every talk in data/audio/ with NVIDIA Parakeet v2 (free, runs on this Mac).
# Writes data/transcripts/<talk>.json (sentences with timestamps, used by later steps) and .txt (one sentence per line).
# Safe to re-run: talks already transcribed are skipped.
# Why Parakeet, not Whisper turbo (2026-10-13): same accuracy in the test, but on long talks Whisper got stuck in loops,
# and the loop fix made it drop punctuation (61% of the Lost Interview). Parakeet always punctuates and never looped.
cd "${0:A:h}"
mkdir -p data/transcripts
for f in data/audio/*.m4a; do
  name=${f:t:r}
  [[ -f data/transcripts/$name.json ]] && continue
  echo "$(date +%H:%M) $name"
  uvx parakeet-mlx "$f" --model mlx-community/parakeet-tdt-0.6b-v2 --output-format json \
    --output-dir data/transcripts --output-template "$name" >/dev/null || echo "FAILED $name"
done
python3 -I - <<'PY'
import glob, json
for f in sorted(glob.glob("data/transcripts/*.json")):
    S = json.load(open(f))["sentences"]
    open(f[:-5] + ".txt", "w").write("\n".join(s["text"].strip() for s in S) + "\n")
    # Loop check: flag any sentence repeated 3+ times in a row.
    segs = [s["text"].strip().lower() for s in S]
    run = best = 1
    for a, b in zip(segs, segs[1:]):
        run = run + 1 if a == b and a else 1
        best = max(best, run)
    print(("LOOP?  " if best >= 3 else "ok     ") + f.split("/")[-1], f"(longest repeat: {best})")
PY
