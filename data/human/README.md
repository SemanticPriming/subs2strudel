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

## Other files in this folder

| File | What it is |
|---|---|
| `english_mcrae.csv` | McRae et al. (2005) norms: 541 cues, n = 30 per cue |
| `english_vinson.csv` | Vinson and Vigliocco (2008) norms: 392 cues, n = 20 per cue |
| `cue_ratings.csv` | One row per cue in any of the three norm files (4,436 cues), with which files it is in (`in_flt`, `in_mcrae`, `in_vinson`) and the Brysbaert et al. (2014) concreteness mean and SD, proportion who knew the word, and SUBTLEX frequency. 4,188 cues have a rating (3,524 of the 3,722 FLT cues) |
| `split_half_ceiling.csv` | How well two random halves of the people agree for each FLT cue (top-10 feature-mass coverage, 100 random splits; mean 86.9%). It is the ceiling for any method scored this way. Higher for cues with more people. From `11_split_half_ceiling.ipynb` in FLT-Projects |

`english_mcrae.csv` and `english_vinson.csv` have the same columns as `english_flt.csv` (`cue`, `feature`, `frequency_feature`, `n`, `normalized_feature`) plus `pos`. They come from the 2019 Word-Norms-2 processing (`final words 2017.csv`, features reduced to their root form there), **not** from the newer pipeline: only counts per cue exist for these studies, not per-person lists, so the stop word and lemma steps could not be rerun. The three sets overlap on few cues (FLT and McRae 62, FLT and Vinson 69), and they were collected and processed differently, so keep them separate rather than pooling them.

