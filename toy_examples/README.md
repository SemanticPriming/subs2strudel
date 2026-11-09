# Toy examples: LLM routes to concept-feature norms

Two small pilots that replace Strudel's hand-built pattern grammar with an open-source LLM (llama3.1, run locally with Ollama). Everything the scripts need is in this folder, and they can be run from any directory.

## What is here

| File | What it does |
|---|---|
| `elicit_norms.py` | **Approach 1.** The LLM acts as a "virtual participant" doing the feature listing task (20 runs per concept), scored like the human norms |
| `extract_corpus_sentences.py` | **Approach 2.** The LLM reads real subtitle sentences containing a concept and says whether they name a property |
| `clean_corpus_norms.py` | **Approach 2 (earlier version).** The LLM filters the corpus co-occurrence counts for a concept down to real properties |
| `fetch_corpus_sample.sh` | Downloads a ~8 MB slice of the OPUS OpenSubtitles v2024 English corpus into `data/subs/` (git-ignored; we have no rights to redistribute it) |
| `toy_comparison.html` | The pilot memo comparing the outputs to human norms. **Static page**: its human numbers came from the old 2019 norms file |
| `output/` | The three result files, in the same format as the human norms |

## Data in `data/`

| File | Used by | Notes |
|---|---|---|
| `english_backward.csv` | `clean_corpus_norms.py` | Dependency-parsed subtitle counts (concept, dependent word, frequency). A copy of `archive/example/english_backward.csv` |
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

## Output format

`cue, feature, frequency_feature, n, normalized_feature`, where `normalized_feature = frequency_feature / n * 100`. This is the same scoring as `data/human/english_flt_toy.csv`, so the files can be compared by joining on `cue` and `feature`.
