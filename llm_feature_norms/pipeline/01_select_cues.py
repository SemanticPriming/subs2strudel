"""
Step 1: choose the cues.

Eligible cues: in the reprocessed FLT norms with at least 30 people (n), a
Brysbaert concreteness rating, a single word, and not a stop/filler word.
They are split by concreteness quintile into
  test         40 per quintile (200): scored, never used for prompts or tuning
  calibration   4 per quintile (20):   used to pick the temperature
  train        everything else:        source of the human examples in the few-shot prompt
Also writes the pool of human answers (cleaned, from train cues) that the
few-shot prompt draws from.
"""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # repo root
OUT = HERE.parent / "results"
SEED = 2026

flt = pd.read_csv(ROOT / "data/human/english_flt.csv", keep_default_na=False)
ratings = pd.read_csv(ROOT / "data/human/cue_ratings.csv", keep_default_na=False)
exempt = set(pd.read_csv(OUT / "inputs/exempt_cues.csv")["cue"])

cues = flt.groupby("cue").agg(n=("n", "first"), n_answered=("n_answered", "first")).reset_index()
cues = cues.merge(ratings[["cue", "concreteness", "concreteness_sd", "frequency_subtlex"]], on="cue", how="left")
for col in ["concreteness", "concreteness_sd", "frequency_subtlex"]:
    cues[col] = pd.to_numeric(cues[col], errors="coerce")

ok = (cues["n"] >= 30) & cues["concreteness"].notna() & cues["cue"].str.fullmatch(r"[a-z]+") & ~cues["cue"].isin(exempt)
elig = cues[ok].copy()
elig["length"] = elig["cue"].str.len()
elig["log_frequency"] = np.log10(elig["frequency_subtlex"].clip(lower=1))
elig["quintile"] = pd.qcut(elig["concreteness"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
print(f"{len(cues):,} FLT cues -> {len(elig):,} eligible")

rng = np.random.default_rng(SEED)
elig["split"] = "train"
for q, g in elig.groupby("quintile"):
    pick = rng.permutation(g.index.values)
    elig.loc[pick[:40], "split"] = "test"
    elig.loc[pick[40:44], "split"] = "calibration"
elig = elig.sort_values(["split", "quintile", "cue"])
elig.to_csv(OUT / "cues.csv", index=False)
print(elig["split"].value_counts().to_dict())
print(elig[elig.split == "test"].groupby("quintile")[["concreteness", "log_frequency", "length", "n"]].mean().round(2))

# ---- the pool of human answers for the few-shot prompt (train cues only) ----
# Needs FLT-Projects' processed/01_filtered.csv (cleaned human answers); pass its folder as the first argument.
import sys
FLT = Path(sys.argv[1] if len(sys.argv) > 1 else "/Users/erinbuchanan/GitHub/Research/4_done/FLT-Projects/processed")
answers = pd.read_csv(FLT / "01_filtered.csv", usecols=["row_id", "cue", "answer_clean"], dtype=str, keep_default_na=False)
answers = answers[answers.cue.isin(set(elig[elig.split == "train"].cue))]
text = answers.answer_clean.str.replace(r"\s+", " ", regex=True).str.strip()
good = text.str.count(",").between(3, 12) & text.str.len().between(40, 170) & ~text.str.contains(r"\d|http|\(|\)|;|:")
pool = answers[good].assign(answer=text[good]).drop(columns="answer_clean").sample(min(int(good.sum()), 3000), random_state=SEED)
pool.to_csv(OUT / "inputs/fewshot_pool.csv", index=False)
print(f"few-shot pool: {len(pool):,} answers from {pool.cue.nunique():,} train cues")
