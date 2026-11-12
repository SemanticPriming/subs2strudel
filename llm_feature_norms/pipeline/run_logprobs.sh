#!/usr/bin/env bash
# Step 7: regenerate wave 1 (60 test cues x 20 runs) with token logprobs, then score.
# Needs ollama serve (OLLAMA_NUM_PARALLEL=6) and the flt-nlp environment.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
for model in qwen2.5:1.5b llama3.1; do
  for cond in zero few; do
    $PY 07_logprob_generate.py --model "$model" --condition "$cond" --wave 1
  done
done
$PY 07_logprob_score.py
$PY 07_logprob_score.py --first 5

# Step 7c (optional): 100 short runs per cue, only the first phrase of each (no earlier list items to condition on)
#   for model in qwen2.5:1.5b llama3.1; do for cond in zero few; do
#     $PY 07_logprob_generate.py --model "$model" --condition "$cond" --wave 1 --runs 100 --max-tokens 24 --out ../results/logprobs_phrase1.csv
#   done; done
#   $PY 07_logprob_score.py --phrase1 --input ../results/logprobs_phrase1.csv --tag _p1long
