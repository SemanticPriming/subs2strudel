"""
Approach 2 (revised): LLM reads raw corpus sentences directly.

Strudel scans a window around a marked concept in the corpus and applies a
hand-written pattern-grammar to decide which nearby word is a property and
how it's connected (see archive/strudel_sups/strudel_report.pdf, Section 3).
This does the same job - concept in, candidate property out - but asks an
open-source LLM to make that judgment straight from the raw sentence,
instead of a regex-based connector-pattern grammar.

Corpus: a small local slice of OPUS-OpenSubtitles v2024 (English), see
fetch_corpus_sample.sh. Only ~8MB is pulled from the ~9.5GB file and it is
never committed (data/subs/ is gitignored) - this is a toy sample, not a
redistribution of the corpus.
"""

import argparse
import csv
import json
import random
import re
import urllib.request
from collections import Counter

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

PROMPT_TEMPLATE = """Here is one real sentence from a corpus of movie/TV subtitles. It contains the word "{concept}".

Sentence: {sentence}

Task: does this sentence, in context, indicate a genuine property of {concept} - something physical, functional, categorical, or behavioral about it (not about other things the sentence happens to mention)? If yes, output ONE short property as a word or short phrase (2-4 words), in the same style as a psychology feature-listing study, e.g. "has_legs", "made_of_wood", "used_for_sitting", "is_a_pet". If the sentence gives no real property of {concept} (e.g. it's just dialogue, a name, or unrelated), output exactly: none

Output ONLY the property phrase or the word "none", nothing else.

Property:"""

WORD_STRIP = re.compile(r"[^a-zA-Z ']")


def find_sentences(corpus_path: str, concept: str) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(concept)}s?\b", re.IGNORECASE)
    matches = []
    with open(corpus_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or len(line) > 200:
                continue
            if pattern.search(line):
                matches.append(line)
    return matches


def call_ollama(prompt: str, seed: int) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 20, "seed": seed},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["response"]


def extract_concept(concept: str, sentences: list[str], n_sentences: int, seed: int) -> tuple[list[dict], list[str]]:
    random.Random(seed).shuffle(sentences)
    sample = sentences[:n_sentences]

    counter = Counter()
    kept_examples = []
    for i, sentence in enumerate(sample):
        prompt = PROMPT_TEMPLATE.format(concept=concept, sentence=sentence)
        response = call_ollama(prompt, seed=2000 + i).strip().split("\n")[0]
        response = response.split(":")[-1].strip().strip('"').lower()
        if response and response != "none" and len(response) < 60:
            feature = response.replace(" ", "_")
            counter[feature] += 1
            if len(kept_examples) < 6:
                kept_examples.append(f"{sentence!r} -> {feature}")
        print(f"  [{concept}] {i + 1}/{len(sample)}: {sentence[:60]!r} -> {response}")

    n = len(sample)
    rows = []
    for feature, count in counter.most_common():
        rows.append(
            {
                "cue": concept,
                "feature": feature,
                "frequency_feature": count,
                "n_sentences": n,
                "normalized_feature": round(count / n * 100, 4),
            }
        )
    return rows, kept_examples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", nargs="+", default=["dog", "chair", "apple", "happiness"])
    parser.add_argument("--corpus", default="data/subs/opensubtitles_v2024_en_sample.txt")
    parser.add_argument("--n-sentences", type=int, default=25, help="sentences sampled per concept")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--out", default="llm_norms/output/llm_corpus_sentences_norms.csv")
    args = parser.parse_args()

    all_rows = []
    examples_log = []
    for concept in args.concepts:
        print(f"Finding sentences for: {concept}")
        sentences = find_sentences(args.corpus, concept)
        print(f"  {len(sentences)} candidate sentences found")
        rows, examples = extract_concept(concept, sentences, args.n_sentences, args.seed)
        all_rows.extend(rows)
        examples_log.append((concept, examples))

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cue", "feature", "frequency_feature", "n_sentences", "normalized_feature"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote {len(all_rows)} rows to {args.out}")

    print("\nExample sentence -> feature extractions:")
    for concept, examples in examples_log:
        print(f"  {concept}:")
        for ex in examples:
            print(f"    {ex}")


if __name__ == "__main__":
    main()
