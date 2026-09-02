"""
Approach 2: LLM-cleaned corpus-derived concept-feature norms.

Rather than re-running Strudel's brittle POS pattern-grammar, or downloading
a fresh OpenSubtitles dump, this reuses the dependency-parsed OpenSubtitles-
derived corpus counts already produced in this project
(archive/example/english_backward.csv, concept -> dependent-word frequency
via UDPipe dependency parsing) and asks an open-source LLM to do what the
Strudel pattern-grammar / stopword lists tried to do by hand: separate real
semantic properties from noisy collocations (e.g. "martial" for "art", which
is just part of the fixed phrase "martial art", not a property of art).

Output is scored the same way as the human norms: normalized_feature =
share of the surviving corpus frequency mass.
"""

import argparse
import csv
import json
import urllib.request
from collections import defaultdict

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

PROMPT_TEMPLATE = """Below is a list of words that frequently co-occur with the concept "{concept}" in a large corpus of movie/TV subtitles. They were extracted automatically by dependency parsing, so many are just collocations or parts of fixed phrases (e.g. "martial" for "art", from "martial art"), not real semantic properties of {concept}.

Candidate words (with raw corpus frequency):
{candidates}

Task: like a psychology feature-listing study, keep ONLY the words that describe a genuine physical, functional, categorical, or associative property of {concept} as a noun (things it is used for, made of, related to, or how it behaves) - not fixed-phrase collocations, not unrelated modifiers, not the concept word itself. It's fine to keep only a handful if most candidates are noise.

Output ONLY a comma-separated list of the kept words, nothing else. Do not add new words that aren't in the candidate list.

Kept properties:"""


def load_candidates(path: str, concept: str, top_n: int) -> list[tuple[str, int]]:
    freq = defaultdict(int)
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["concept_lemma"] == concept:
                freq[row["feature_lemma"]] += int(row["freq"])
    return sorted(freq.items(), key=lambda x: -x[1])[:top_n]


def call_ollama(prompt: str, seed: int = 7) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 300, "seed": seed},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["response"]


def clean_concept(concept: str, candidates: list[tuple[str, int]]) -> list[dict]:
    cand_str = ", ".join(f"{w} ({c})" for w, c in candidates)
    prompt = PROMPT_TEMPLATE.format(concept=concept, candidates=cand_str)
    response = call_ollama(prompt)
    response = response.strip().split("\n")[0]
    if ":" in response:
        response = response.split(":", 1)[-1]
    kept = [w.strip().lower() for w in response.split(",") if w.strip()]

    freq_lookup = {w: c for w, c in candidates}
    kept_rows = [(w, freq_lookup[w]) for w in kept if w in freq_lookup]
    total = sum(c for _, c in kept_rows) or 1

    rows = []
    for feature, freq in sorted(kept_rows, key=lambda x: -x[1]):
        rows.append(
            {
                "cue": concept,
                "feature": feature,
                "raw_corpus_freq": freq,
                "normalized_feature": round(freq / total * 100, 4),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", nargs="+", default=["art", "band", "concert", "radio"])
    parser.add_argument("--corpus", default="archive/example/english_backward.csv")
    parser.add_argument("--top-n", type=int, default=40, help="candidate words considered per concept before filtering")
    parser.add_argument("--out", default="llm_norms/output/llm_corpus_cleaned_norms.csv")
    args = parser.parse_args()

    all_rows = []
    for concept in args.concepts:
        print(f"Cleaning corpus candidates for: {concept}")
        candidates = load_candidates(args.corpus, concept, args.top_n)
        print(f"  {len(candidates)} raw candidates, top 5: {candidates[:5]}")
        rows = clean_concept(concept, candidates)
        print(f"  kept {len(rows)} after LLM filtering")
        all_rows.extend(rows)

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cue", "feature", "raw_corpus_freq", "normalized_feature"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote {len(all_rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
