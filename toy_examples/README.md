# Toy examples: LLM routes to concept-feature norms

Two small pilots that replace Strudel's hand-built pattern grammar with an open-source LLM (llama3.1, run locally with Ollama). Everything the scripts need is in this folder, and they can be run from any directory.

## What is here

| File | What it does |
|---|---|
| `elicit_norms.py` | **Approach 1.** The LLM acts as a "virtual participant" doing the feature listing task (20 runs per concept), scored like the human norms |
| `extract_corpus_sentences.py` | **Approach 2.** The LLM reads real subtitle sentences containing a concept and says whether they name a property |
| `clean_corpus_norms.py` | **Approach 2 (earlier version).** The LLM filters the corpus co-occurrence counts for a concept down to real properties |
| `fetch_corpus_sample.sh` | Downloads a ~8 MB slice of the OPUS OpenSubtitles v2024 English corpus into `data/subs/` (git-ignored; we have no rights to redistribute it) |
| `compare_to_human.py` | Scores each method's output against the human norms (top-10 feature-mass coverage, phrase and lemma versions) and writes `output/coverage_vs_human.csv`. Needs `pip install spacy nltk` and `python -m spacy download en_core_web_sm` for the lemma score |
| `toy_comparison.html` | The pilot memo comparing the outputs to human norms. **Static page**: its human numbers came from the old 2019 norms file |
| `output/` | The three result files, in the same format as the human norms |

## Data in `data/`

| File | Used by | Notes |
|---|---|---|
| `english_backward.csv` | `clean_corpus_norms.py` | Dependency-parsed subtitle counts (concept, dependent word, frequency). A copy of `archive/example/english_backward.csv` |
| `human/english_mcrae_toy.csv`, `human/english_vinson_toy.csv` | `compare_to_human.py` | McRae and Vinson norms for the toy concepts they cover. `dog` is only in these two; the old pilot's "Buchanan" `dog` numbers came from them |
| `human/english_flt_toy.csv` | for comparing | Human norms (reprocessed feature listing data, no frequency cutoff) for the toy concepts `apple`, `art`, `band`, `chair`, `concert`, `happiness`, `radio`. A subset of `../data/human/english_flt.csv`; same columns as `output/*.csv` plus a few extras. `dog` is not a cue in the feature listing task, so it has no human norms |
| `subs/` | `extract_corpus_sentences.py` | Created by `fetch_corpus_sample.sh`; not in git |

## Running

You need Python 3 (standard library only) and [Ollama](https://ollama.com) running locally with `ollama pull llama3.1`.

```bash
cd toy_examples
./fetch_corpus_sample.sh                      # once, for approach 2 (sentences)
python elicit_norms.py                        # dog, chair, apple, happiness
python extract_corpus_sentences.py            # dog, chair, apple, happiness
python clean_corpus_norms.py                  # art, band, concert, radio
```

Pass `--concepts word1 word2 ...` to change the concepts; each script has `--help`. Results go to `output/`. The scripts' default paths no longer depend on where you run them from.

## Results against the human norms

`output/coverage_vs_human.csv` (rerun `python compare_to_human.py`). Phrase score, the pilot's rule; the lemma score is in the file.

| Method | Concept | vs FLT | vs McRae | vs Vinson |
|---|---|---|---|---|
| virtual participants | dog | - | 93.7 | 100.0 |
| virtual participants | chair | 93.6 | 100.0 | 93.0 |
| virtual participants | apple | 91.4 | 100.0 | 85.4 |
| virtual participants | happiness | 78.1 | - | - |
| corpus sentences | dog | - | 26.6 | 30.3 |
| corpus sentences | chair | 42.8 | 45.8 | 35.2 |
| corpus sentences | apple | 31.6 | 25.6 | 37.1 |
| corpus sentences | happiness | 0.0 | - | - |
| corpus cleaned | art, band, concert | 0.0 | - | - |
| corpus cleaned | radio | 11.3 | 0.0 | - |

For comparison, two random halves of the FLT people agree at 86.9% on average (`data/human/split_half_ceiling.csv`). The score counts a human feature as recovered when the method produced it at all, so it rewards long feature lists and is not a like-for-like match to the split-half number; treat the comparison as rough.

## Output format

`cue, feature, frequency_feature, n, normalized_feature`, where `normalized_feature = frequency_feature / n * 100`. This is the same scoring as `data/human/english_flt_toy.csv`, so the files can be compared by joining on `cue` and `feature`.
