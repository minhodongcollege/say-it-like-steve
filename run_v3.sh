#!/bin/zsh
# v3 overnight run (2026-10-14): clean Steve's side → order-keeping pairs → split → train 12B 1 pass → test → Qwen judge.
# Every step is safe to re-run (finished chunks/pairs are skipped). Log: data/run_v3.log
set -e
cd "${0:A:h}"
PY=(uv run --with mlx-lm python -I)
step() { echo "\n=== $(date '+%H:%M') $1"; }

step "1/7 clean Steve's side";       $PY clean_steve.py
step "2/7 plain pairs (same order)"; $PY make_pairs.py plain
step "3/7 my-style pairs";           $PY make_pairs.py mine
step "4/7 check + split"
python3 -I check_pairs.py data/pairs_v3.jsonl
python3 -I check_pairs.py data/pairs_mine_v3.jsonl
python3 -I split_data.py
step "5/7 train Gemma 4 12B, 300 steps"
./train.sh gemma4-12b-v3 mlx-community/gemma-4-12B-it-qat-4bit 300 data/train_v3
# keep the checkpoint with the lowest validation loss
BEST=$(sed 's/\x1b\[[0-9;]*m//g' adapters/gemma4-12b-v3/train.log | awk '$2=="val" && $1>1 {print $3, $1}' | sort -n | head -1 | awk '{printf "%07d", $2}')
echo "best checkpoint: step $BEST"
mkdir -p adapters/gemma4-12b-v3-best
cp adapters/gemma4-12b-v3/${BEST}_adapters.safetensors adapters/gemma4-12b-v3-best/adapters.safetensors
cp adapters/gemma4-12b-v3/adapter_config.json adapters/gemma4-12b-v3-best/
step "6/7 run the 27 test inputs";   $PY run_eval.py adapters/gemma4-12b-v3-best data/eval/model_v3.jsonl 0.4
python3 -I check_eval.py data/eval/model_v3.jsonl data/eval/model_t0.4.jsonl
step "7/7 Qwen judge: v3 vs v1, v3 vs Claude baseline"
python3 -I judge.py build v3-vs-v1 data/eval/model_v3.jsonl data/eval/model_t0.4.jsonl
python3 -I judge.py build v3-vs-claude data/eval/model_v3.jsonl data/eval/baseline.jsonl
$PY judge.py qwen v3-vs-v1
$PY judge.py qwen v3-vs-claude
step "done"
