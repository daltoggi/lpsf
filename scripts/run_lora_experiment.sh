#!/usr/bin/env bash
# Drive the full LoRA-from-experience memory experiment end to end.
# Uses the MLX venv. Logs every stage. Safe to re-run.
#
#   bash scripts/run_lora_experiment.sh
#
set -uo pipefail
cd "$(dirname "$0")/.."

PY="$HOME/.lpsf-ml-venv/bin/python"
MODEL="mlx-community/Qwen2.5-0.5B-Instruct-4bit"
DATA="data/lora_fact"
ADAPTER="$DATA/adapter"

echo "=== [1/5] generate data ==="
$PY scripts/lora_data_gen.py || exit 1

echo "=== [2/5] probe BASE model (empty ctx should miss; RAG should hit) ==="
$PY scripts/lora_memory_experiment.py --stage base || exit 1

echo "=== [3/5] train LoRA (teach the fictional fact) ==="
# Small model, tiny dataset: all layers, modest iters. ~minutes on Apple Silicon.
$PY -m mlx_lm lora \
  --model "$MODEL" \
  --train \
  --data "$DATA" \
  --fine-tune-type lora \
  --num-layers -1 \
  --batch-size 2 \
  --iters 200 \
  --learning-rate 1e-4 \
  --adapter-path "$ADAPTER" \
  --max-seq-length 256 \
  --steps-per-report 50 \
  --steps-per-eval 100 || exit 1

echo "=== [4/5] probe LoRA model (empty ctx should now HIT) ==="
$PY scripts/lora_memory_experiment.py --stage lora || exit 1

echo "=== [5/5] render report ==="
$PY scripts/lora_memory_experiment.py --stage report || exit 1

echo "=== DONE ==="
