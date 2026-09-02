"""
Approach 1: LLM-elicited concept-feature norms.

Mimics the human feature-listing task (Buchanan et al., 2019 instructions,
see materials/human/english_Buchanan2019.html) by repeatedly prompting an
open-source LLM (llama3.1, via a local Ollama server) as if it were a
"virtual participant," then aggregating the produced features into
frequency-based norms the same way the human norming study does:
normalized_feature = (# virtual participants producing the feature) / N * 100
"""

import argparse
import csv
import json
import re
import urllib.request
from collections import Counter

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

# Condensed version of the original Buchanan et al. (2019) participant
# instructions (materials/human/english_Buchanan2019.html), including the
# same worked examples shown to human participants.
PROMPT_TEMPLATE = """This is a psychology feature-listing task. We need information on what people know about different things in the world.

For the word below, list as many properties of the concept as you can think of. Properties can be physical (internal/external parts, how it looks, sounds, smells, feels, or tastes), functional (what it is used for; where, when, or by whom it is used), categorical (what group or category it belongs to), or other facts (how it behaves, or where it comes from). Consider the word only as a noun.

Give your answer as a single comma-separated list, in the same style as these examples:

duck: is a bird, is an animal, waddles, flies, migrates, lays eggs, quacks, swims, has wings, has a beak, has webbed feet, has feathers, lives in ponds, lives in water, hunted by people, is edible
cucumber: is a vegetable, has green skin, has a white inside, has seeds, is cylindrical, is long, grows in gardens, grows on vines, is edible, is crunchy, used for making pickles, eaten in salads
stove: is an appliance, produces heat, inside has elements, inside has an oven, made of metal, is hot, is electrical, runs on wood, runs on gas, found in kitchens, used for baking, used for cooking food

Now give the comma-separated list of properties for this word. Output ONLY the comma-separated list, nothing else.

{concept}:"""

# Leading function-word patterns stripped to approximate the single/short
# lemma style used in the human norm spreadsheet (e.g. "has webbed feet" -> "webbed feet").
LEAD_STRIP = re.compile(
    r"^(is a |is an |is the |is |has a |has an |has |used for |used to |"
    r"made of |made from |found in |found on |lives in |lives on |runs on |"
    r"comes from |grows in |grows on |eaten in |eaten as |inside has |"
    r"inside has a |inside has an |a |an |the )+",
    re.IGNORECASE,
)


def normalize_feature(phrase: str) -> str:
    phrase = phrase.strip().lower()
    phrase = re.sub(r"[.\n]+$", "", phrase)
    prev = None
    while prev != phrase:
        prev = phrase
        phrase = LEAD_STRIP.sub("", phrase)
    phrase = phrase.strip().replace(" ", "_")
    return phrase


def call_ollama(concept: str, seed: int, temperature: float = 0.9) -> str:
    prompt = PROMPT_TEMPLATE.format(concept=concept)
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 150, "seed": seed},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["response"]


def elicit(concept: str, n_participants: int) -> list[dict]:
    raw_counter = Counter()
    norm_counter = Counter()
    for i in range(n_participants):
        response = call_ollama(concept, seed=1000 + i)
        # model sometimes echoes "concept:" or wraps in a sentence; take text after last colon if present
        response = response.split("\n")[0]
        if ":" in response:
            response = response.split(":", 1)[-1]
        phrases = [p.strip() for p in response.split(",") if p.strip()]
        seen_this_participant = set()
        for phrase in phrases:
            raw_counter[phrase.lower()] += 1
            norm = normalize_feature(phrase)
            if norm and norm not in seen_this_participant:
                norm_counter[norm] += 1
                seen_this_participant.add(norm)
        print(f"  [{concept}] participant {i + 1}/{n_participants}: {len(phrases)} features")

    rows = []
    for feature, count in norm_counter.most_common():
        rows.append(
            {
                "cue": concept,
                "feature": feature,
                "frequency_feature": count,
                "n": n_participants,
                "normalized_feature": round(count / n_participants * 100, 4),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", nargs="+", default=["dog", "chair", "apple", "happiness"])
    parser.add_argument("--n", type=int, default=20, help="number of virtual participants per concept")
    parser.add_argument("--out", default="llm_norms/output/llm_elicited_norms.csv")
    args = parser.parse_args()

    all_rows = []
    for concept in args.concepts:
        print(f"Eliciting features for: {concept}")
        all_rows.extend(elicit(concept, args.n))

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cue", "feature", "frequency_feature", "n", "normalized_feature"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Wrote {len(all_rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
