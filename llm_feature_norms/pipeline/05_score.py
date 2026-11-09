"""
Step 5: score the model norms against the human norms.

For every model x prompt condition x test cue:
  * the model's runs are processed like human answers (process_text.py) and
    counted: frequency_feature = runs that produced the word, n = runs
  * coverage = top-10 feature-mass coverage: take the human top-10 features
    (largest percent of people first) and report the share of their summed
    percentages that the model also produced
      coverage_any   the model produced the word in at least 1 run
      coverage_4runs the model produced it in at least 4 of 20 runs (16%, the McRae et al. cutoff of 5 of 30 people)
      coverage_phrase the pilot's rule on the raw model phrases (substring)
  * ceiling = the same score for 20 randomly chosen people against the top-10
    of the remaining people (100 draws), i.e. how well a human sample of the
    same size as the model's runs does
  * r = correlation between model and human percentages over the features
    either of them produced (r_percent); and r_percent_16 with the McRae 16% cutoff on both lists (a feature below
    16% counts as 0 in that list; features absent from both are dropped)
Then a mixed model of coverage on the cue predictors.
"""
import numpy as np
import pandas as pd
import process_text as p
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"
ROOT = Path(__file__).resolve().parents[2]
rng = np.random.default_rng(2026)

cues = pd.read_csv(RESULTS / "cues.csv", keep_default_na=False)
test = cues[cues.split == "test"]
gens = pd.read_csv(RESULTS / "generations.csv", keep_default_na=False)
temp = __import__("json").loads((RESULTS / "temperature.json").read_text())["temperature"]
gens = gens[gens.cue.isin(set(test.cue)) & (gens.temperature.astype(float) == temp)]
print(f"{len(gens):,} test runs at temperature {temp}", flush=True)

# 1. process the model output like the human answers
feature_rows, phrase_rows = [], {}
for (model, cond, cue), g in gens.groupby(["model", "condition", "cue"]):
    n_runs = len(g)
    counts = {}
    for text in g.text:
        for _, w, _, _ in p.process_answer(cue, text):
            counts[w] = counts.get(w, 0) + 1
    for w, c in counts.items():
        feature_rows.append((model, cond, cue, w, c, n_runs, 100 * c / n_runs))
    phrase_rows[(model, cond, cue)] = {f.strip().lower() for t in g.text for f in t.split(",") if f.strip()}
feats = pd.DataFrame(feature_rows, columns=["model", "condition", "cue", "feature", "frequency_feature", "n", "normalized_feature"])
feats.round(3).to_csv(RESULTS / "model_features.csv", index=False)

# 2. human norms
done = set(feats.cue)                                   # test cues that have model runs so far
test = test[test.cue.isin(done)]
flt = pd.read_csv(ROOT / "data/human/english_flt.csv", usecols=["cue", "lemma", "normalized_lemma"], keep_default_na=False)
flt = flt.drop_duplicates(["cue", "lemma"]).rename(columns={"lemma": "feature", "normalized_lemma": "normalized_feature"})
flt = flt[flt.cue.isin(done)]
people = pd.read_csv(RESULTS / "inputs/human_person_lists.csv", dtype=str, keep_default_na=False)
people = people[people.cue.isin(done)]


def top10(series):
    s = series.sort_values(ascending=False, kind="stable")
    return s.head(10)


def coverage(top, produced):
    total = top.sum()
    return 100 * top[[f in produced for f in top.index]].sum() / total if total else np.nan


human_pct = {c: g.set_index("feature")["normalized_feature"].astype(float) for c, g in flt.groupby("cue")}
human_top = {c: top10(s) for c, s in human_pct.items()}

KS = range(1, 11)
sweep_rows = []
rows = []
for (model, cond, cue), g in feats.groupby(["model", "condition", "cue"]):
    n_runs = g.n.iloc[0]
    top = human_top[cue]
    any_set = set(g.feature)
    pct_set = set(g.feature[g.frequency_feature >= 4])
    for k in KS:
        sweep_rows.append({"model": model, "condition": cond, "cue": cue, "min_runs": k,
                           "coverage": coverage(top, set(g.feature[g.frequency_feature >= k]))})
    phr = phrase_rows[(model, cond, cue)]
    covered_phrase = {f for f in top.index if any(f in ph for ph in phr)}
    union = human_pct[cue].index.union(g.feature)
    hp = human_pct[cue].reindex(union).fillna(0)
    mp = g.set_index("feature")["normalized_feature"].reindex(union).fillna(0)
    # McRae cutoff on both lists: a feature below 16% of people (or of runs) counts as absent (0);
    # compared over the features that pass in at least one source
    hf, mf_ = hp.where(hp >= 16, 0), mp.where(mp >= 16, 0)
    keep = (hf > 0) | (mf_ > 0)
    r16 = np.corrcoef(hf[keep], mf_[keep])[0, 1] if keep.sum() >= 3 and hf[keep].std() > 0 and mf_[keep].std() > 0 else np.nan
    rows.append({"model": model, "condition": cond, "cue": cue, "n_runs": n_runs, "n_features": len(any_set),
                 "r_percent_16": r16,
                 "words_per_run": g.frequency_feature.sum() / n_runs,
                 "coverage_any": coverage(top, any_set), "coverage_4runs": coverage(top, pct_set),
                 "coverage_phrase": coverage(top, covered_phrase), "r_percent": np.corrcoef(hp, mp)[0, 1]})
cov = pd.DataFrame(rows)

# 3. human ceiling: 20 random people against the rest
ceil, ceil_sweep = [], []
for cue, g in people.groupby("cue"):
    per_person = g.groupby("subject_id")["word"].apply(set)
    ids = np.arange(len(per_person))
    a_any, a_10 = [], []
    a_k = {k: [] for k in KS}
    for _ in range(100):
        pick = rng.permutation(ids)
        a, rest = pick[:20], pick[20:]
        share = pd.Series([w for i in rest for w in per_person.iloc[i]]).value_counts() / len(rest) * 100
        top = top10(share)
        counts_a = pd.Series([w for i in a for w in per_person.iloc[i]]).value_counts()
        a_any.append(coverage(top, set(counts_a.index)))
        a_10.append(coverage(top, set(counts_a.index[counts_a >= 4])))
        for k in KS:
            a_k[k].append(coverage(top, set(counts_a.index[counts_a >= k])))
    ceil.append({"cue": cue, "ceiling_any": np.mean(a_any), "ceiling_4runs": np.mean(a_10)})
    ceil_sweep.extend({"cue": cue, "min_runs": k, "ceiling": np.mean(v)} for k, v in a_k.items())
ceil = pd.DataFrame(ceil)

sweep = pd.DataFrame(sweep_rows).merge(pd.DataFrame(ceil_sweep), on=["cue", "min_runs"])
sweep.round(3).to_csv(RESULTS / "coverage_by_threshold.csv", index=False)
out = cov.merge(ceil, on="cue").merge(test[["cue", "quintile", "concreteness", "log_frequency", "length", "n"]], on="cue")
out.round(3).to_csv(RESULTS / "coverage_by_cue.csv", index=False)

# 4. summaries
out["method"] = out.model + " / " + out.condition
tab = out.groupby("method")[["coverage_any", "coverage_4runs", "coverage_phrase", "ceiling_any", "ceiling_4runs", "r_percent", "r_percent_16", "n_features", "words_per_run"]].mean().round(1)
tab.to_csv(RESULTS / "summary_by_method.csv")
byq = out.pivot_table(index="quintile", columns="method", values="coverage_any", aggfunc="mean").round(1)
byq["human ceiling (20 people)"] = out.groupby("quintile")["ceiling_any"].mean().round(1)
byq.to_csv(RESULTS / "summary_by_concreteness.csv")
print(tab.to_string()); print(); print(byq.to_string())

# 5. what predicts coverage?
import statsmodels.formula.api as smf
for col in ["concreteness", "log_frequency", "length"]:
    out[col + "_z"] = (out[col] - out[col].mean()) / out[col].std()
fit = smf.mixedlm("coverage_any ~ concreteness_z + log_frequency_z + length_z + C(method)", out, groups=out["cue"]).fit()
coefs = pd.DataFrame({"estimate": fit.params, "se": fit.bse, "z": fit.tvalues, "p": fit.pvalues}).round(3)
coefs.to_csv(RESULTS / "mixed_model.csv")
print(); print(coefs.to_string())
