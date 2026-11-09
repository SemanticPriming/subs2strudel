"""
Compare the toy outputs with the human feature norms.

Score = top-10 feature-mass coverage: take the human top-10 features for a
concept (largest normalized_feature first) and report the share of their
summed percentages that the method also produced.

Two ways of deciding that the method "produced" a human feature:
  phrase - the human feature is a substring of one of the method's feature
           phrases (the pilot's rule, e.g. "tail" is found in "wags_its_tail")
  lemma  - the method's phrases are reduced to content-word lemmas (spaCy,
           NLTK stop words removed), as the human answers were processed, and
           the human feature must be one of them

Needs spaCy (with en_core_web_sm) and NLTK stopwords for the lemma score:
    pip install spacy nltk && python -m spacy download en_core_web_sm
Without them only the phrase score is written.

Human sources (data/human/): english_flt_toy.csv (reprocessed Buchanan feature
listing data), english_mcrae_toy.csv, english_vinson_toy.csv. Each concept is
scored against every source that has it.
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

HUMAN = {
    "flt": HERE / "data" / "human" / "english_flt_toy.csv",
    "mcrae": HERE / "data" / "human" / "english_mcrae_toy.csv",
    "vinson": HERE / "data" / "human" / "english_vinson_toy.csv",
}
METHODS = {
    "elicited (virtual participants)": HERE / "output" / "llm_elicited_norms.csv",
    "corpus sentences": HERE / "output" / "llm_corpus_sentences_norms.csv",
    "corpus cleaned": HERE / "output" / "llm_corpus_cleaned_norms.csv",
}


def read_norms(path):
    norms = defaultdict(dict)
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            norms[row["cue"]][row["feature"].lower()] = float(row["normalized_feature"])
    return norms


def top10(features):
    return sorted(features.items(), key=lambda kv: (-kv[1], kv[0]))[:10]


def coverage(top, produced):
    total = sum(p for _, p in top)
    return 100 * sum(p for f, p in top if produced(f)) / total if total else float("nan")


def load_lemmatizer():
    try:
        import spacy
        from nltk.corpus import stopwords
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        stop = set(stopwords.words("english"))
    except Exception as err:
        print(f"(lemma score skipped: {err})")
        return None

    def lemmas(phrase):
        doc = nlp(phrase.replace("_", " ").lower())
        return {t.lemma_.lower() for t in doc if t.is_alpha and t.lemma_.lower() not in stop}

    return lemmas


def main():
    human = {name: read_norms(p) for name, p in HUMAN.items() if p.exists()}
    lemmatize = load_lemmatizer()
    rows = []
    for method, path in METHODS.items():
        model = read_norms(path)
        for cue, feats in model.items():
            phrases = [f.lower().replace("_", " ") for f in feats]
            lemma_set = set().union(*(lemmatize(f) for f in feats)) if lemmatize else None
            for source, norms in human.items():
                if cue not in norms:
                    continue
                top = top10(norms[cue])
                rows.append({
                    "method": method, "cue": cue, "human_source": source,
                    "coverage_phrase": round(coverage(top, lambda f: any(f in p for p in phrases)), 1),
                    "coverage_lemma": round(coverage(top, lambda f: f in lemma_set), 1) if lemma_set is not None else "",
                    "human_top10": " ".join(f for f, _ in top),
                })
    out = HERE / "output" / "coverage_vs_human.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(f"{r['method']:34s} {r['cue']:10s} vs {r['human_source']:7s} phrase {r['coverage_phrase']:5.1f}  lemma {r['coverage_lemma']}")
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
