#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
for model in qwen2.5:1.5b llama3.1; do
  for cond in zero few; do
    $PY 07_logprob_generate.py --model "$model" --condition "$cond" --wave 1 --runs 100 --max-tokens 24 --out ../results/logprobs_phrase1.csv
  done
done
$PY 07_logprob_score.py --phrase1 --input ../results/logprobs_phrase1.csv --tag _p1long
