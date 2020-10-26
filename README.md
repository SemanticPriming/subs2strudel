# subs2strudel

Creating semantic concept-feature norms using STRUDEL

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
