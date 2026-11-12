"""
Step 7b: correlate the human percent with the model's word probability.

Instead of comparing the human percent with the model's percent of 20 runs, take
the probability the model gave each word when it wrote it (the inverse of
surprisal) and compare that with the human percent.

For every run (07_logprob_generate.py):
  * the first line of the response is split at commas into phrases, each phrase is
    processed like a human answer (process_text.py, the same rules as step 5; a
    repeated word is kept once, in its first place)
  * each processed word is traced back to the raw word it came from, and the
    probability is exp(sum of the logprobs) of the tokens that spell that raw word,
    given everything before it. Only those tokens count, not the frame around the
    word ("has a" in "has a beak"). A word split into several tokens (leg+s) gets
    the product of their probabilities. A word that cannot be traced back (a
    contraction that was expanded, say) has no probability and is left out of the
    average (the share is printed).
Per model x condition x cue x word:
  * pct         the share of runs that produced the word (the usual model percent)
  * mean_prob   the probability averaged over the runs that produced the word
  * expected    the sum of the probabilities over all runs / number of runs, so a
                word not produced in a run counts as 0 there (a word produced once at
                0.4 gets 0.02 with 20 runs)
Correlated with the human percent (normalized_lemma), per cue, then averaged:
  * on the words the model produced ("model words"; a word no person listed has 0)
  * on all words either the model or people produced ("union"; 0 where absent)
Pearson r and Spearman rho; log_prob = Pearson r on log(mean_prob).

  python 07_logprob_score.py [--first 5] [--input results/logprobs.csv]
Run with the flt-nlp environment.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import process_text as p

ap = argparse.ArgumentParser()
ap.add_argument("--first", type=int, default=0, help="only the first N processed words of each run; outputs get a _firstN suffix")
ap.add_argument("--phrase1", action="store_true", help="only the words of the first phrase of each run (nothing earlier in the list to condition on); outputs get a _phrase1 suffix")
ap.add_argument("--input", default=None)
ap.add_argument("--tag", default="", help="suffix for the output files (pilots)")
a = ap.parse_args()
FIRST = a.first
PHRASE1 = a.phrase1
SUF = a.tag + (f"_first{FIRST}" if FIRST else "") + ("_phrase1" if PHRASE1 else "")

RESULTS = Path(__file__).resolve().parent.parent / "results"
ROOT = Path(__file__).resolve().parents[2]
inp = Path(a.input) if a.input else RESULTS / "logprobs.csv"


def spans(tokens):
    """Character span of each token's visible part (leading spaces excluded) in the joined text."""
    out, pos = [], 0
    for tok, _ in tokens:
        start = pos + len(tok) - len(tok.lstrip())
        pos += len(tok)
        out.append((start, pos))
    return out


def run_words(cue, tokens):
    """-> list of (position, word, prob, first_token_prob, n_tokens, phrase_index); prob is NaN if the word cannot be traced to tokens."""
    text = "".join(t for t, _ in tokens)
    tok_spans = spans(tokens)
    lines = [(m.start(), m.end()) for m in re.finditer(r"[^\n]+", text) if m.group().strip()]
    if not lines:
        return []
    ls, le = lines[0]
    rows, seen, cursor = [], set(), ls
    for k, m in enumerate(re.finditer(r"[^,]+", text[ls:le])):
        ps, pe = ls + m.start(), ls + m.end()
        raw, low = text[ps:pe], text[ps:pe].lower()
        cursor = 0
        for _, w, orig, _tag in p.process_answer(cue, raw):
            if w in seen:
                continue
            seen.add(w)
            hit = re.compile(r"(?<![a-z0-9])" + re.escape(orig.lower()) + r"(?![a-z0-9])").search(low, cursor)
            prob = first = np.nan
            n_tok = 0
            if hit:
                s, e = ps + hit.start(), ps + hit.end()
                cursor = hit.start()          # a later piece of the same raw word (numbers) may reuse it
                idx = [i for i, (cs, ce) in enumerate(tok_spans) if cs < e and ce > s and ce > cs]
                if idx:
                    prob = float(np.exp(sum(tokens[i][1] for i in idx)))
                    first = float(np.exp(tokens[idx[0]][1]))
                    n_tok = len(idx)
            rows.append((len(seen), w, prob, first, n_tok, k))
    return rows


# 1. every word of every run
runs = pd.read_csv(inp, keep_default_na=False)
word_rows = []
for r in runs.itertuples():
    for pos, w, prob, first, n_tok, k in run_words(r.cue, json.loads(r.tokens)):
        word_rows.append((r.model, r.condition, r.cue, r.run, pos, w, prob, first, n_tok, k))
words = pd.DataFrame(word_rows, columns=["model", "condition", "cue", "run", "position", "feature", "prob", "first_token_prob", "n_tokens", "phrase"])
words.round(6).to_csv(RESULTS / f"logprob_words{SUF}.csv", index=False)
print(f"{len(runs):,} runs, {len(words):,} words; {words.prob.isna().mean():.1%} could not be traced to tokens", flush=True)
if FIRST:
    words = words[words.position <= FIRST]
if PHRASE1:
    words = words[words.phrase == 0]

# 2. per method x cue x word
n_runs = runs.groupby(["model", "condition", "cue"]).size().rename("n").reset_index()
feats = (words.groupby(["model", "condition", "cue", "feature"])
         .agg(runs_with_word=("run", "nunique"), mean_prob=("prob", "mean"), sum_prob=("prob", "sum"),
              mean_first_token_prob=("first_token_prob", "mean"), mean_position=("position", "mean"))
         .reset_index().merge(n_runs, on=["model", "condition", "cue"]))
feats["pct"] = 100 * feats.runs_with_word / feats.n
feats["expected"] = feats.sum_prob / feats.n

# 3. human norms
flt = pd.read_csv(ROOT / "data/human/english_flt.csv", usecols=["cue", "lemma", "normalized_lemma"], keep_default_na=False)
flt = flt.drop_duplicates(["cue", "lemma"]).rename(columns={"lemma": "feature", "normalized_lemma": "human_pct"})
flt["human_pct"] = flt.human_pct.astype(float)
feats = feats.merge(flt, on=["cue", "feature"], how="left")
feats["in_model"] = True
feats.round(6).to_csv(RESULTS / f"logprob_features{SUF}.csv", index=False)


def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return np.nan, np.nan
    return np.corrcoef(x, y)[0, 1], spearmanr(x, y)[0]


rows = []
for (model, cond, cue), g in feats.groupby(["model", "condition", "cue"]):
    h = flt[flt.cue == cue].set_index("feature")["human_pct"]
    gm = g.set_index("feature")
    mw = gm.assign(human_pct=h.reindex(gm.index).fillna(0))                     # words the model produced
    union = h.index.union(gm.index)
    u = pd.DataFrame({"human_pct": h.reindex(union).fillna(0)})
    for c in ["pct", "mean_prob", "expected"]:
        u[c] = gm[c].reindex(union)
    u["pct"] = u.pct.fillna(0)
    u["expected"] = u.expected.fillna(0)
    u["mean_prob0"] = u.mean_prob.fillna(0)                                    # a word never produced counts as 0
    row = {"model": model, "condition": cond, "cue": cue, "n_model_words": len(mw), "n_union": len(u)}
    row["mw_r_pct"], row["mw_rho_pct"] = corr(mw.human_pct, mw.pct)
    row["mw_r_prob"], row["mw_rho_prob"] = corr(mw.human_pct, mw.mean_prob)
    row["mw_r_logprob"], _ = corr(mw.human_pct, np.log(mw.mean_prob))
    row["mw_r_expected"], row["mw_rho_expected"] = corr(mw.human_pct, mw.expected)
    row["un_r_pct"], row["un_rho_pct"] = corr(u.human_pct, u.pct)
    row["un_r_prob"], row["un_rho_prob"] = corr(u.human_pct, u.mean_prob0)
    row["un_r_expected"], row["un_rho_expected"] = corr(u.human_pct, u.expected)
    rows.append(row)
by_cue = pd.DataFrame(rows)
by_cue.round(4).to_csv(RESULTS / f"logprob_by_cue{SUF}.csv", index=False)
by_cue["method"] = by_cue.model + " / " + by_cue.condition
summ = by_cue.groupby("method").mean(numeric_only=True).round(3)
summ.insert(0, "cues", by_cue.groupby("method").size())
summ.to_csv(RESULTS / f"logprob_summary{SUF}.csv")
pd.set_option("display.width", 250)
print("\nwords the model produced (human 0 if no person listed it):")
print(summ[["cues", "n_model_words", "mw_r_pct", "mw_r_prob", "mw_r_logprob", "mw_r_expected", "mw_rho_pct", "mw_rho_prob", "mw_rho_expected"]].to_string())
print("\nall words either side produced (0 where absent):")
print(summ[["n_union", "un_r_pct", "un_r_prob", "un_r_expected", "un_rho_pct", "un_rho_prob", "un_rho_expected"]].to_string())
