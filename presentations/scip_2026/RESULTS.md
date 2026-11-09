# SCiP 2026 poster: LLM-generated feature norms vs. human norms

Full pipeline, code and data: [`llm_feature_norms/`](../../llm_feature_norms/README.md). Figures: [`figures/`](figures/) (PNG 300 dpi and editable SVG).

## What we did
- 60 test cues (12 per concreteness fifth) from the reprocessed FLT norms; none used for examples or calibration.
- Two local models (Llama 3.1 8B, Qwen 2.5 1.5B), each as zero-shot and few-shot (8 real human lists), 20 runs per cue = 20 virtual participants. 4,800 test runs.
- Same cleaning pipeline as the human answers, including step 12 that merges inflected forms into the base word (`gambling → gamble`, `feeling → feel`; spelling correction skipped; 93.4% identical on 3,000 human answers, differences are spelling).
- Score: share of the human top-10 features recovered by the model (found in at least 1 run, or in at least 10% of runs). Ceiling: what 20 random people recover.

## Main result (mean % of human top-10 features recovered, 60 cues)
| Method | ≥1 run | ≥10% of runs |
|---|---|---|
| Llama 3.1 few-shot | 83.8 | 75.5 |
| Llama 3.1 zero-shot | 81.7 | 72.0 |
| Qwen 2.5 1.5B few-shot | 76.0 | 69.1 |
| Qwen 2.5 1.5B zero-shot | 76.9 | 66.1 |
| 20 people (ceiling) | 88.7 | 77.0 |

- Llama few-shot comes close to the 20-person ceiling; it is within about 5 points on ≥1 run and roughly equal on ≥10%.
- Few-shot helps little (Llama +2 to +3 points); the model matters more (Qwen about 7 points lower, p < .001).
- Coverage rises with concreteness (+3.4 points per SD, p = .018) and word frequency (+3.9, p = .011); word length is not reliable (+1.1, p = .50). Mixed model, random intercept for cue.
- Fifths, abstract to concrete, Llama few-shot: 80.5, 79.3, 82.7, 89.9, 86.5 (people: 84.0, 87.1, 90.5, 90.3, 91.6). The gap to people is largest for abstract cues.

## Caveats (say these on the poster)
- Models write about 26-29 words per run versus about 5 per person, and many more distinct features (about 150-180 per cue at 20 runs vs 61 for people). `coverage_any` is generous for that reason; the ≥10% column is the fairer one.
- Temperature calibration: all tested values (0.7, 0.9, 1.1) over-produced distinct features; we used the lowest, 0.7. Lower values were not tested.
- Models were not audited for exposure to the original norms or other feature-norm data.
- 60 of 200 test cues so far; no LoRA, Strudel arm, or memorization probe yet.
- Feature-level correlation (`r_percent`) is low (0.2-0.3): the models find the same features but not in the same proportions.
