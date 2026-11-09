# SCiP 2026 poster: LLM-generated feature norms vs. human norms

Full pipeline, code and data: [`llm_feature_norms/`](../../llm_feature_norms/README.md). Figures: [`figures/`](figures/) (PNG 300 dpi and editable SVG).

## What we did
- 200 test cues (40 per concreteness fifth, run in three waves) from the reprocessed FLT norms; none used for examples or calibration.
- Two local models (Llama 3.1 8B, Qwen 2.5 1.5B), each as zero-shot and few-shot (8 real human lists), 20 runs per cue = 20 virtual participants. 16,000 test runs.
- Same cleaning pipeline as the human answers, including step 12 that merges related words into one lemma (`gambling → gamble`, `lucky → luck`; spelling correction skipped; 93.4% identical on 3,000 human answers, differences are spelling).
- Score: share of the human top-10 features recovered by the model (found in at least 1 run, or in at least 4 of 20 runs). Ceiling: what 20 random people recover.

## Main result (mean % of human top-10 features recovered, 200 test cues)
A feature counts as found if it appears in at least 1 of the 20 runs, or in at least 4 of 20 (16%, the McRae et al. cutoff of 5 of 30 people; the same rule is applied to the 20 people). `fig6_threshold` shows every cutoff from 1 to 10 runs. Human and model words are both merged into one lemma first (FLT step 12).

| Method | ≥1 run | ≥4 runs (16%) | first 5 words, ≥1 run | first 5 words, ≥4 runs |
|---|---|---|---|---|
| Llama 3.1 few-shot | 85.7 | 71.5 | 60.6 | 41.9 |
| Llama 3.1 zero-shot | 82.9 | 67.4 | 55.3 | 36.1 |
| Qwen 2.5 1.5B few-shot | 78.8 | 63.1 | 57.9 | 37.5 |
| Qwen 2.5 1.5B zero-shot | 77.8 | 61.2 | 53.4 | 34.3 |
| 20 people (ceiling) | 89.1 | 56.0 | 89.1 | 56.0 |

- At ≥1 run, Llama few-shot is about 3 points below the 20-person ceiling.
- At ≥4 runs all four methods are above the 20 people (56.0%). People write about 5 words each, so few features reach 4 of 20 people, while a model run lists about 27 words and repeats its favourites. The people ceiling falls faster with the cutoff (`fig6_threshold`: 89% at 1 run, 19% at 10 runs; Llama few-shot 86% to 55%).
- **Length check:** counting only each model run's first 5 words (about what a person writes), the models fall to 53-61% at ≥1 run and 34-42% at ≥4 runs, below the 89% and 56% for people. So the ≥4 result above is a length effect, not evidence that models beat people. Caveat: a model's first 5 words may be its most generic ones, so this is only an approximation of equal length.
- Few-shot helps little (Llama +3 points, Qwen +1); the model matters more (Qwen about 7-8 points lower, p < .001).
- Cue predictors of coverage (≥1 run, mixed model, random intercept for cue): concreteness +3.5 points per SD (p < .001); word frequency -0.3 (p = .76); word length -0.6 (p = .51). With 60 cues, frequency looked like +3.5 (p = .022); it did not hold with 200 cues. With only the first 5 words, none of the three predicts coverage (concreteness +0.6, p = .60). Fifths of concreteness, abstract to concrete, Llama few-shot: 79.5, 86.1, 84.8, 88.9, 89.3 (people: 84.4, 87.9, 89.5, 91.5, 92.4).
- Correlation of model and human feature percentages (per cue, then averaged): about 0.3 over all features. With the McRae 16% cutoff on both lists it is 0.1-0.2 (Llama few-shot 0.2), and slightly negative (-0.1 to -0.2) with first-5 words. The cutoff leaves about 5 human features per cue but many more model features, because model runs repeat the same words, so this number mostly reflects that repetition.

## Caveats (say these on the poster)
- Models write about 26-29 words per run versus about 5 per person, and many more distinct features (about 130-160 per cue at 20 runs vs about 60 for people). `coverage_any` is generous for that reason; the ≥4 runs column is the stricter one.
- Temperature: test runs used 0.7. Calibration on 10 cues (Llama zero-shot) tested 0.3-1.1: counting all words, 0.3 matches the number of distinct features best (all values still produce about 2x as many as people); counting only the first 5 words, 1.1 matches best. The two criteria disagree, so the temperature was not changed (`results/temperature_candidate.json`).
- Models were not audited for exposure to the original norms or other feature-norm data.
- No LoRA, Strudel arm, or memorization probe yet.
- Feature-level correlation is low (about 0.1-0.4): the models find many of the same features but not in the same proportions.
