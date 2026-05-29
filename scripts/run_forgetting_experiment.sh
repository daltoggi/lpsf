#!/usr/bin/env bash
# Catastrophic forgetting experiment.
# Assumes LoRA adapter already exists at data/lora_fact/adapter/.
# If not, run scripts/run_lora_experiment.sh first.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$HOME/.lpsf-ml-venv/bin/python"

echo "=== [1/3] probe BASE model (25 general-knowledge questions) ==="
$PY scripts/forgetting_experiment.py --stage base || exit 1

echo "=== [2/3] probe LORA model (same questions, adapter loaded) ==="
$PY scripts/forgetting_experiment.py --stage lora || exit 1

echo "=== [3/3] render report ==="
$PY scripts/forgetting_experiment.py --stage report || exit 1

echo "=== DONE ==="
