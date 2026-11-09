"""
Step 4: pick the sampling temperature.

For the calibration cues, compare how many different features appear in 20
model runs with how many appear in 20 randomly chosen people (the
vocabulary-growth idea from the method papers, at one sample size). The
temperature whose number of different features is closest (in ratio) to the
human number is used for the test cues. Model output is processed like the
human answers first (process_text.py).
"""
import json
import numpy as np
import pandas as pd
import process_text as p
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"
MODEL, CONDITION = "llama3.1", "zero"
rng = np.random.default_rng(2026)

gens = pd.read_csv(RESULTS / "generations.csv", keep_default_na=False)
gens = gens[(gens.model == MODEL) & (gens.condition == CONDITION)]
cal = set(pd.read_csv(RESULTS / "cues.csv", keep_default_na=False).query("split == 'calibration'").cue)
gens = gens[gens.cue.isin(cal)]

rows = []
for (temp, cue), g in gens.groupby(["temperature", "cue"]):
    lists = [[w for _, w, _, _ in p.process_answer(cue, t)] for t in g.text]
    rows.append({"temperature": temp, "cue": cue, "runs": len(lists),
                 "distinct_features": len(set(w for l in lists for w in l)),
                 "words_per_run": np.mean([len(l) for l in lists])})
model = pd.DataFrame(rows)

people = pd.read_csv(RESULTS / "inputs/human_person_lists.csv", dtype=str, keep_default_na=False)
human = []
for cue, g in people[people.cue.isin(cal)].groupby("cue"):
    per_person = g.groupby("subject_id")["word"].apply(list)
    draws = [rng.choice(len(per_person), 20, replace=False) for _ in range(300)]
    distinct = [len(set(w for i in d for w in per_person.iloc[i])) for d in draws]
    human.append({"cue": cue, "human_distinct_20": np.mean(distinct), "human_words_per_person": per_person.map(len).mean()})
human = pd.DataFrame(human)

both = model.merge(human, on="cue")
both["log_ratio_distinct"] = np.log(both.distinct_features / both.human_distinct_20)
both["log_ratio_length"] = np.log(both.words_per_run / both.human_words_per_person)
summary = both.groupby("temperature").agg(
    cues=("cue", "size"), distinct_features=("distinct_features", "mean"), human_distinct_20=("human_distinct_20", "mean"),
    words_per_run=("words_per_run", "mean"), human_words_per_person=("human_words_per_person", "mean"),
    mean_log_ratio_distinct=("log_ratio_distinct", "mean"), mean_abs_log_ratio_distinct=("log_ratio_distinct", lambda s: s.abs().mean()),
).round(3).reset_index()
summary.to_csv(RESULTS / "calibration.csv", index=False)
best = float(summary.loc[summary.mean_abs_log_ratio_distinct.idxmin(), "temperature"])
(RESULTS / "temperature.json").write_text(json.dumps({"temperature": best, "model": MODEL, "condition": CONDITION}))
print(summary.to_string(index=False))
print("chosen temperature:", best)
