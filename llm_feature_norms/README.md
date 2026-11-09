# LLM-generated feature norms, compared with human norms

Can a language model, given the same instructions as the human participants, produce concept-feature norms that match the human ones? This folder is the full pipeline. The summary for the SCiP 2026 poster is in `presentations/scip_2026/`.

The design follows `no_sync/` proposal v2 (feature norms only). Human benchmark: the reprocessed feature listing norms in `data/human/` (from [doomlab/FLT-Projects](https://github.com/doomlab/FLT-Projects)).

## What is run

| Script (`pipeline/`) | What it does |
|---|---|
| `01_select_cues.py` | Picks the cues: 2,719 eligible FLT cues (30+ people, a concreteness rating, one word, not a stop word) split by concreteness quintile into test, calibration and train. Also builds the pool of human answers for the few-shot prompt |
| `02_generate.py` | Each model run is one virtual participant: one independent sample of a comma-separated list, with the Buchanan et al. (2019) instructions and worked examples. **zero** = instructions only; **few** = plus 8 real human lists from train cues. Models run through Ollama; output is appended to `results/generations.csv` and the script resumes where it stopped |
| `process_text.py` | Processes model output the way the human answers were processed (clean, contractions, abbreviations, spaCy lemmas, numbers, stop words, cue word removed, one word per row, then related words merged into one lemma by `merge_lemmas.py`). The rules are copied from the FLT-Projects notebooks (step 12 for the merge); spelling is skipped. `validate_processing.py` checks it against the human pipeline (93.4% of 3,000 answers identical, differences are spelling) |
| `04_calibrate.py` | Chooses the sampling temperature: the one where 20 runs give a number of different features closest to 20 people, on the calibration cues |
| `05_score.py` | Scores the test cues: top-10 feature-mass coverage against the human norms, the human ceiling (20 random people against the rest), feature-level correlation (all features, and with the 16% cutoff on both lists), coverage at every cutoff from 1 to 10 runs (`coverage_by_threshold.csv`), and a mixed model of coverage on concreteness, frequency and length |
| `06_figures.py` | Draws the poster figures (PNG and SVG) into `presentations/scip_2026/figures/` from the files `05_score.py` wrote |
| `merge_lemmas.py` | Merges related words into one lemma: the 2019 translation dictionary without its odd pairs, plus affix rules checked against WordNet. Same file as in FLT-Projects (step 12); its dictionaries are in `results/inputs/` (`translation_2019.csv`, `lemma_keep_separate.csv`, `lemma_force_merge.csv`, ...) |
| `run_waves.sh`, `run_after_waves.sh` | Overnight runs: test waves 2 and 3 (the other 140 test cues) with scoring after each wave, then the lower-temperature calibration and the first-5-words scoring |
| `run_pipeline.sh` | Runs calibration, test generation for each model and condition, and scoring |

Requirements: Ollama (`OLLAMA_NUM_PARALLEL=6 ollama serve`) with `llama3.1` and `qwen2.5:1.5b` pulled, and the `flt-nlp` conda environment from FLT-Projects plus `statsmodels`. Run `01_select_cues.py` first, then `run_pipeline.sh`.

## Results

See `presentations/scip_2026/RESULTS.md` (60 test cues): Llama 3.1 few-shot recovers about 86% of the human top-10 features when a feature found in any run counts, against about 90% for 20 people; with a stricter bar of 4 of 20 runs the models are above 20 people because they repeat words. Re-run `05_score.py` and `06_figures.py` after changing the merge rules.

## Metrics

- **Coverage** (top-10 feature-mass coverage): take the human top-10 features for a cue (largest percent of people first) and report the share of their summed percentages that the model also produced. `coverage_any` counts a feature if one or more runs produced it, `coverage_4runs` if at least 4 of the 20 runs (16%, the McRae et al. cutoff of 5 of 30 people) did, `coverage_phrase` is the pilot's substring rule on the raw model phrases.
- **Ceiling:** the same score for 20 random people against the top-10 of the remaining people, i.e. how well a human sample the size of the model's 20 runs does.

## Open follow-ups (read this before the next run)

**Length mismatch.** A model run lists about 27 words, a person about 5, so "found in any run" is generous and 20 runs give far more distinct features than 20 people (about 160 vs 60). On the first 60 cues, scoring only the **first 5 words of each run** drops coverage to 54-59% (vs 90% for 20 people; `summary_by_method_first5.csv`), so the length-matched comparison favours people. Plan, in order:

1. **Lower temperatures.** The calibration winner (0.7) was the lowest value tried. `run_after_waves.sh` adds 0.3 and 0.5 to the calibration (Llama zero-shot, 20 calibration cues) and writes `results/calibration.csv` and `temperature_candidate.json`. It does **not** change `temperature.json`, so the 200 test cues stay at 0.7. Expect little change: most of the gap is length, not randomness. Only if a lower temperature clearly wins on both the all-words and the first-5-words column, regenerate the test cues at that temperature.
2. **Score both ways.** Every score exists at full length and on the first 5 words (`05_score.py` and `05_score.py --first 5`; files with a `_first5` suffix). Compare them for all 200 cues.
3. **If the first-5 gap holds: ask for shorter lists** (add "about 5 properties" to the prompt) as an extra prompt condition. This changes the instructions relative to the people, so report it as its own condition, not a replacement. Not started.

## Not included (planned, see the proposal)

- Models whose training data can be audited (Comma v0.1, OLMo 3) and the exposure audit for the published norms. The models here have **not** been audited and have probably seen the McRae and Buchanan norm files.
- LoRA fine-tuning (only few-shot prompting is used) and the Strudel corpus arm.
- Only part of the 200 test cues have been run.

Model lists are much longer than people's (about 20 features per run against about 5 words per person), so `coverage_any` is generous; read it together with `coverage_4runs` and the ceiling.
