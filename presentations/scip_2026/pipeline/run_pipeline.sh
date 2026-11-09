#!/usr/bin/env bash
# Runs the whole pipeline after calibration generation has finished.
# Needs: ollama serve (OLLAMA_NUM_PARALLEL=6), models llama3.1 and qwen2.5:1.5b pulled,
# and the flt-nlp conda environment (spaCy, pandas, statsmodels, num2words, nltk).
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
$PY 01_select_cues.py
while pgrep -f "02_generate.py.*--split calibration" > /dev/null; do sleep 20; done
$PY 04_calibrate.py
T=$($PY -c "import json;print(json.load(open('../results/temperature.json'))['temperature'])")
for model in llama3.1 qwen2.5:1.5b; do
  for cond in zero few; do
    $PY 02_generate.py --model "$model" --condition "$cond" --split test --wave 1 --temps "$T"
  done
done
$PY 05_score.py
