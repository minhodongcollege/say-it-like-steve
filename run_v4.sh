#!/bin/zsh
# v4 run (2026-10-15): v3 recipe + 9 young unscripted talks (1980-1991, 118 new chunks). Only the new chunks get cleaned + paired.
# Every step is safe to re-run (finished chunks/pairs are skipped). Log: data/run_v4.log
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
python3 -I split_data.py data/train_v4
step "5/7 train Gemma 4 12B, 300 steps"
./train.sh gemma4-12b-v4 mlx-community/gemma-4-12B-it-qat-4bit 300 data/train_v4
# keep the checkpoint with the lowest validation loss
BEST=$(sed 's/\x1b\[[0-9;]*m//g' adapters/gemma4-12b-v4/train.log | awk '$2=="val" && $1>1 {print $3, $1}' | sort -n | head -1 | awk '{printf "%07d", $2}')
echo "best checkpoint: step $BEST"
mkdir -p adapters/gemma4-12b-v4-best
cp adapters/gemma4-12b-v4/${BEST}_adapters.safetensors adapters/gemma4-12b-v4-best/adapters.safetensors
cp adapters/gemma4-12b-v4/adapter_config.json adapters/gemma4-12b-v4-best/
step "6/7 run the 27 test inputs";   $PY run_eval.py adapters/gemma4-12b-v4-best data/eval/model_v4.jsonl 0.4
python3 -I check_eval.py data/eval/model_v4.jsonl data/eval/model_v3.jsonl
step "7/7 Qwen judge: v4 vs v3, v4 vs Claude baseline"
python3 -I judge.py build v4-vs-v3 data/eval/model_v4.jsonl data/eval/model_v3.jsonl
python3 -I judge.py build v4-vs-claude data/eval/model_v4.jsonl data/eval/baseline.jsonl
$PY judge.py qwen v4-vs-v3
$PY judge.py qwen v4-vs-claude
step "done"
