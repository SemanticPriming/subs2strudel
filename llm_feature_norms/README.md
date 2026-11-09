# LLM-generated feature norms, compared with human norms

Can a language model, given the same instructions as the human participants, produce concept-feature norms that match the human ones? This folder is the full pipeline. The summary for the SCiP 2026 poster is in `presentations/scip_2026/`.

The design follows `no_sync/` proposal v2 (feature norms only). Human benchmark: the reprocessed feature listing norms in `data/human/` (from [doomlab/FLT-Projects](https://github.com/doomlab/FLT-Projects)).

## What is run

| Script (`pipeline/`) | What it does |
|---|---|
| `01_select_cues.py` | Picks the cues: 2,719 eligible FLT cues (30+ people, a concreteness rating, one word, not a stop word) split by concreteness quintile into test, calibration and train. Also builds the pool of human answers for the few-shot prompt |
| `02_generate.py` | Each model run is one virtual participant: one independent sample of a comma-separated list, with the Buchanan et al. (2019) instructions and worked examples. **zero** = instructions only; **few** = plus 8 real human lists from train cues. Models run through Ollama; output is appended to `results/generations.csv` and the script resumes where it stopped |
| `process_text.py` | Processes model output the way the human answers were processed (clean, contractions, abbreviations, spaCy lemmas, numbers, stop words, cue word removed, one word per row). The rules are copied from the FLT-Projects notebooks; spelling is skipped. `validate_processing.py` checks it against the human pipeline (93.4% of 3,000 answers identical, differences are spelling) |
| `04_calibrate.py` | Chooses the sampling temperature: the one where 20 runs give a number of different features closest to 20 people, on the calibration cues |
| `05_score.py` | Scores the test cues: top-10 feature-mass coverage against the human norms, the human ceiling (20 random people against the rest), feature-level correlation, and a mixed model of coverage on concreteness, frequency and length |
| `run_pipeline.sh` | Runs calibration, test generation for each model and condition, and scoring |

Requirements: Ollama (`OLLAMA_NUM_PARALLEL=6 ollama serve`) with `llama3.1` and `qwen2.5:1.5b` pulled, and the `flt-nlp` conda environment from FLT-Projects plus `statsmodels`. Run `01_select_cues.py` first, then `run_pipeline.sh`.

## Metrics

- **Coverage** (top-10 feature-mass coverage): take the human top-10 features for a cue (largest percent of people first) and report the share of their summed percentages that the model also produced. `coverage_any` counts a feature if one or more runs produced it, `coverage_4runs` if at least 4 of the 20 runs (16%, the McRae et al. cutoff of 5 of 30 people) did, `coverage_phrase` is the pilot's substring rule on the raw model phrases.
- **Ceiling:** the same score for 20 random people against the top-10 of the remaining people, i.e. how well a human sample the size of the model's 20 runs does.

## Not included (planned, see the proposal)

- Models whose training data can be audited (Comma v0.1, OLMo 3) and the exposure audit for the published norms. The models here have **not** been audited and have probably seen the McRae and Buchanan norm files.
- LoRA fine-tuning (only few-shot prompting is used) and the Strudel corpus arm.
- Only part of the 200 test cues have been run.

Model lists are much longer than people's (about 20 features per run against about 5 words per person), so `coverage_any` is generous; read it together with `coverage_4runs` and the ceiling.
