"""
Check that process_text.py reproduces the human pipeline: run 3,000 real human
answers (from FLT-Projects' processed/01_filtered.csv) through it and compare
the words with processed/08_words.csv for the same answers. Differences are
expected only where the human pipeline corrected spelling.
"""
import sys
import numpy as np
import pandas as pd
import process_text as p

FLT = sys.argv[1] if len(sys.argv) > 1 else "/Users/erinbuchanan/GitHub/Research/4_done/FLT-Projects/processed"
f = pd.read_csv(f"{FLT}/01_filtered.csv", usecols=["row_id", "cue", "answer_raw"], dtype=str, keep_default_na=False)
w = pd.read_csv(f"{FLT}/08_words.csv", usecols=["row_id", "word"], dtype=str, keep_default_na=False)
human = w.groupby("row_id")["word"].apply(list).to_dict()

sample = f.sample(3000, random_state=1)
exact = jacc = 0
rows = []
for rid, cue, text in zip(sample.row_id, sample.cue, sample.answer_raw):
    mine = [x[1] for x in p.process_answer(cue, text)]
    theirs = human.get(rid, [])
    a, b = set(mine), set(theirs)
    j = len(a & b) / len(a | b) if (a | b) else 1.0
    exact += mine == theirs
    jacc += j
    rows.append((rid, cue, text[:80], " ".join(mine), " ".join(theirs), j))
n = len(sample)
print(f"identical word lists: {exact / n:.1%};  mean word overlap (Jaccard): {jacc / n:.3f}")
bad = pd.DataFrame(rows, columns=["row_id", "cue", "answer", "mine", "human_pipeline", "jaccard"]).sort_values("jaccard")
print(bad[bad.jaccard < 1].head(8).to_string(index=False))
