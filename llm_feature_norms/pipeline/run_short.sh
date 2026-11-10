#!/usr/bin/env bash
# Extra prompt condition: ask for "about 5 properties" (zero5, few5), all 200 test cues, same temperature as the main runs.
# The instructions differ from the ones the people had, so this is reported as its own condition (scored with --short; the main results are untouched).
# Generation resumes where it stopped, so this can be stopped and started again safely.
#   caffeinate -i nohup ./run_short.sh > ../results/short_run.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-/opt/miniconda3/envs/flt-nlp/bin/python}
T=$($PY -c "import json;print(json.load(open('../results/temperature.json'))['temperature'])")
echo "=== short started $(date)"
for model in llama3.1 qwen2.5:1.5b; do
  for cond in zero5 few5; do
    $PY 02_generate.py --model "$model" --condition "$cond" --split test --temps "$T"
  done
done
echo "=== short generated $(date); scoring"
$PY 05_score.py --short
$PY 05_score.py --short --first 5
echo "=== short done $(date)"
