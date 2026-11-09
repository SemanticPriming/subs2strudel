# SCiP 2026 poster: LLM-generated feature norms vs. human norms

Full pipeline, code and data: [`llm_feature_norms/`](../../llm_feature_norms/README.md). Figures: [`figures/`](figures/) (PNG 300 dpi and editable SVG).

## What we did
- 60 test cues (12 per concreteness fifth) from the reprocessed FLT norms; none used for examples or calibration.
- Two local models (Llama 3.1 8B, Qwen 2.5 1.5B), each as zero-shot and few-shot (8 real human lists), 20 runs per cue = 20 virtual participants. 4,800 test runs.
- Same cleaning pipeline as the human answers, including step 12 that merges related words into one lemma (`gambling → gamble`, `lucky → luck`; spelling correction skipped; 93.4% identical on 3,000 human answers, differences are spelling).
- Score: share of the human top-10 features recovered by the model (found in at least 1 run, or in at least 4 of 20 runs). Ceiling: what 20 random people recover.

## Main result (mean % of human top-10 features recovered, 60 cues)
A feature counts as found if it appears in at least 1 of the 20 runs, or in at least 4 of 20 (16%, the McRae et al. cutoff of 5 of 30 people; the same rule is applied to the 20 people). `fig6_threshold` shows every cutoff from 1 to 10 runs. Human and model words are both merged into one lemma first (FLT step 12: the 2019 translation dictionary minus its odd pairs, plus affix rules, so `luck`/`lucky`, `gamble`/`gambling` count as one feature).

| Method | ≥1 run | ≥4 runs (16%) |
|---|---|---|
| Llama 3.1 few-shot | 85.9 | 70.5 |
| Llama 3.1 zero-shot | 83.5 | 67.8 |
| Qwen 2.5 1.5B few-shot | 78.5 | 63.5 |
| Qwen 2.5 1.5B zero-shot | 78.6 | 61.6 |
| 20 people (ceiling) | 89.9 | 56.8 |

- At ≥1 run, Llama few-shot is about 4 points below the 20-person ceiling.
- At ≥4 runs the order flips: all four methods are above the 20 people (56.8%). People write about 5 words each, so few features reach 4 of 20 people, while a model run lists about 27 words and repeats its favourites. The people ceiling falls faster with the cutoff (`fig6_threshold`: 90% at 1 run, 19% at 10 runs; Llama few-shot 86% to 54%). This is a difference in how many words each source produces, not evidence that models match people better.
- Few-shot helps little (Llama +2 points, Qwen no difference); the model matters more (Qwen about 7 points lower, p < .001).
- Cue predictors of coverage (≥1 run, mixed model, random intercept for cue): concreteness +3.0 points per SD (p = .038), word frequency +3.5 (p = .022), word length +1.5 (p = .35). Fifths of concreteness, abstract to concrete, Llama few-shot: 82.3, 83.1, 85.7, 89.6, 88.6 (people: 86.0, 88.3, 91.5, 90.8, 92.7). These effects are modest and sensitive to how words are merged (they were p = .02 and .01 with no merge and weaker, p = .13 and .06, with the full unfiltered 2019 translation), so describe them as small.
- Correlation of model and human feature percentages (per cue, then averaged): 0.28-0.35 over all features. With the McRae 16% cutoff on both lists (a feature below 16% counts as 0 in that list, compared over features that pass in at least one) it is 0.07-0.16 (Llama few-shot 0.16). The cutoff leaves about 5 human features per cue (2019 norms: 5.8) but about 40 model features, because model runs repeat the same words, so this number mostly reflects that repetition.
- Merging: related words are merged into one lemma on both sides (FLT step 12): the 2019 translation without the pairs that join opposites or change meaning (`unhappy`/`happy`, `medicine`/`medic`), plus affix rules checked against WordNet.

## Caveats (say these on the poster)
- Models write about 26-29 words per run versus about 5 per person, and many more distinct features (about 130-160 per cue at 20 runs vs about 60 for people). `coverage_any` is generous for that reason; the ≥4 runs column is the stricter one.
- Temperature calibration: all tested values (0.7, 0.9, 1.1) over-produced distinct features; we used the lowest, 0.7. Lower values were not tested.
- Models were not audited for exposure to the original norms or other feature-norm data.
- 60 of 200 test cues so far; no LoRA, Strudel arm, or memorization probe yet.
- Feature-level correlation is low (0.08-0.36): the models find many of the same features but not in the same proportions.
