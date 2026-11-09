#!/usr/bin/env bash
# Runs the remaining test cues in waves, scoring after each wave so there are usable results at every stage.
#   wave 2: 8 more cues per concreteness fifth (40 cues, 100 in total)
#   wave 3: the rest (100 cues, 200 in total)
# Generation resumes where it stopped, so this can be stopped and started again safely.
# Needs: ollama serve (OLLAMA_NUM_PARALLEL=6), llama3.1 and qwen2.5:1.5b pulled, results/temperature.json
# (from 04_calibrate.py). Wave 1 (60 cues) is already done.
#   caffeinate -i nohup ./run_waves.sh > ../results/waves_run.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
T=$($PY -c "import json;print(json.load(open('../results/temperature.json'))['temperature'])")
for wave in 2 3; do
  echo "=== wave $wave started $(date)"
  for model in llama3.1 qwen2.5:1.5b; do
    for cond in zero few; do
      $PY 02_generate.py --model "$model" --condition "$cond" --split test --wave "$wave" --temps "$T"
    done
  done
  echo "=== wave $wave generated $(date); scoring"
  $PY 05_score.py
  $PY 06_figures.py
  echo "=== wave $wave done $(date)"
done
