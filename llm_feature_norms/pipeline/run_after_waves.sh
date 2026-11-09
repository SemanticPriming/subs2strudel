#!/usr/bin/env bash
# Follow-up to run_waves.sh (waits for it, so it can be started at the same time):
#   1. calibration at lower temperatures (0.3, 0.5) with Llama zero-shot on the 20 calibration cues,
#      then 04_calibrate.py (writes temperature_candidate.json; temperature.json is not touched)
#   2. scoring on the first 5 words of each run (05_score.py --first 5) next to the full-length scoring
# Look at results/calibration.csv and summary_by_method_first5.csv, then decide about step 3 (README, "Open follow-ups").
#   caffeinate -i nohup ./run_after_waves.sh > ../results/after_waves.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python}
while pgrep -f "run_waves.sh" > /dev/null; do sleep 60; done
echo "=== waves finished $(date)"
$PY 05_score.py --first 5
$PY 02_generate.py --model llama3.1 --condition zero --split calibration --temps 0.3 0.5
$PY 04_calibrate.py
echo "=== done $(date)"
