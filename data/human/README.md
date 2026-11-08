# Human feature norms (`english_flt.csv`)

Concept-feature norms from the feature listing task, reprocessed from the raw participant answers. They replace the published 2019 norms file (`english_Buchanan2019.csv`) that was here before.

Source: the processing pipeline in [doomlab/FLT-Projects](https://github.com/doomlab/FLT-Projects), file `processed/09_cue_feature_counts.csv` (README and `COMPARISON.md` there describe every step and how close these are to the 2019 norms). Answers flagged as dictionary or web text, answers from rejected MTurk assignments and other bad rows were left out before counting. **No frequency cutoff was applied**: every cue-feature pair is here, including features only one person listed.

| Column | Meaning |
|---|---|
| `cue` | the concept word |
| `feature` | the feature word (lemma, stop words removed) |
| `frequency_feature` | number of people who listed the feature for this cue |
| `n` | number of people with at least one feature for this cue |
| `normalized_feature` | `frequency_feature / n * 100` (same scoring as the LLM norms in `llm_norms/output/`) |
| `n_answered` | people who answered the cue before any exclusions |
| `pos` | most common part of speech for the feature under this cue |
| `mean_position` | average position in people's lists (1 = listed first) |
| `original_words` | the forms people actually typed, separated by `|` |

`cue`, `feature`, `frequency_feature`, `n` and `normalized_feature` match the column names of the LLM-elicited and corpus norms, so the files can be compared directly.

The participant instructions are in `materials/human/english_Buchanan2019.html`.
