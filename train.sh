#!/bin/zsh
# Phase 2, step 8: fine-tune Gemma 4 12B with LoRA on data/train/ (my/flat text → Steve).
# Saves the adapter (the small add-on file) to adapters/<run name>/, with a checkpoint every 50 steps.
# Run: ./train.sh [run name] [model] [steps] [data dir]     Log: adapters/<run name>/train.log
#   v1 (2026-10-13): Gemma 4 12B, 600 steps → best at step 200, overfit in epoch 2. v2: Gemma 4 31B, 300 steps (1 epoch).
#   --mask-prompt     only Steve's side counts in the loss: it learns to WRITE Steve, not to copy my input
#   --batch-size 4    4 pairs per step; 1,219 pairs ≈ 305 steps per epoch, so 600 steps ≈ 2 epochs
#   --grad-checkpoint saves memory (needed for the 31B on 48 GB), a bit slower
#   --steps-per-eval  check the validation loss (practice quiz) every 50 steps; keep the checkpoint where it's lowest
cd "${0:A:h}"
RUN=${1:-gemma4-12b-v1}
MODEL=${2:-mlx-community/gemma-4-12B-it-qat-4bit}
ITERS=${3:-600}
DATA=${4:-data/train}   # v3: data/train_v3
mkdir -p adapters/$RUN
uvx --from mlx-lm mlx_lm.lora \
  --model $MODEL \
  --train --data $DATA --fine-tune-type lora --mask-prompt \
  --batch-size 4 --iters $ITERS --grad-checkpoint --learning-rate 1e-5 --num-layers 16 --max-seq-length 1024 \
  --steps-per-report 10 --steps-per-eval 50 --val-batches -1 --save-every 50 \
  --adapter-path adapters/$RUN --seed 0 2>&1 | tee adapters/$RUN/train.log
