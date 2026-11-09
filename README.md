# subs2strudel

Creating semantic concept-feature norms using STRUDEL

## What is in this repository

| Folder | What it holds |
|---|---|
| `data/human/` | Human concept-feature norms (reprocessed feature listing task, McRae, Vinson), concreteness and frequency ratings, and the split-half ceiling. See `data/human/README.md` |
| `llm_feature_norms/` | The pipeline that asks language models to write feature lists, processes them like the human answers and scores them against the human norms. Start with `llm_feature_norms/README.md` |
| `presentations/scip_2026/` | The SCiP 2026 poster: results summary (`RESULTS.md`), figures (`figures/`, PNG and SVG), and a starter PowerPoint at 48 x 36 in (`poster_scip_2026.pptx`, built by `build_poster.py`). `presentations/scip_2020/` is the 2020 STRUDEL talk |
| `toy_examples/` | The small LLM and corpus pilots with their data, outputs and run instructions; see `toy_examples/README.md` |
| `materials/`, `archive/` | Instructions and older material |
| `no_sync/` | Git-ignored working documents (proposals) |

## Human feature norms

`data/human/english_flt.csv` holds the human concept-feature norms used as the comparison. They come from the reprocessed feature listing data in [doomlab/FLT-Projects](https://github.com/doomlab/FLT-Projects) (no frequency cutoff), not from the published 2019 file. Each row has the processed word (`feature`) and the word it is merged into (`lemma`, e.g. `gambling` and `gamble`), with the number of people for each. See `data/human/README.md` for the columns.

## LLM-generated feature norms (SCiP 2026)

Two open models (Llama 3.1 8B, Qwen 2.5 1.5B), zero-shot and with 8 real human examples, each write 20 feature lists per word (one run = one virtual participant). The lists are cleaned with the same rules as the human answers, including merging related words into one lemma, and compared with the human norms for 60 test words: the share of the human top-10 features the model also lists, against what 20 randomly chosen people achieve. Results and caveats are in `presentations/scip_2026/RESULTS.md`; run instructions are in `llm_feature_norms/README.md`.

## Toy examples

`toy_examples/` holds the small LLM pilots (LLM-elicited and corpus-derived norms) with their data, outputs and run instructions; see `toy_examples/README.md`.

# Collecting the Data

Below is the process you need to run in order to contribute a language to the collection.

1. Open up `process_strudels.Rmd` in the root (`~/`) folder.
   It is the same folder that contains this `README.md`.
2. Select a language not currently completed.
   See `~/data/udpipe_languages.csv`'s `Completed` column.
3. Select a number of sub processes.
   Each sub process takes one core and ~2GB of RAM.
4. Run, NOT KNIT, everything.
   This will:
   * Download a new language file into the `~/data` folder.
   * Download a new language _udpipe_ control file into the `~/` folder.
   * Splits the langage file into smaller files for parallel processing.
     This makes more files in the `~/data` folder.
   * Runs each smaller file in its own process.
     This generates files in the `~/concept-feature` folder.
   * Combines the files into a single file.
5. Upload the combined file to the [releases](https://github.com/SemanticPriming/subs2strudel/releases) in GitHub.
6. Update the releases and `~/data/udpipe_languages.csv` noting the progress.
