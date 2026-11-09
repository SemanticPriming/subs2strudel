"""
Step 2: LLM feature lists, one "virtual participant" per run.

Each run is one independent sample (its own seed) of a comma-separated feature
list for a cue, with the task wording of Buchanan et al. (2019) and the same
worked examples the human participants saw. Two prompt conditions:

  zero  the instructions and the three worked examples only
  few   the same, plus 8 lists written by real participants for other (train)
        cues, as extra examples

Models are run with Ollama (http://localhost:11434). Output rows are appended
to results/generations.csv, and runs already there are skipped, so the script
can be stopped and restarted.

  python 02_generate.py --model llama3.1 --condition zero --split calibration --temps 0.7 0.9 1.1
  python 02_generate.py --model llama3.1 --condition few  --split test --wave 1
"""
import argparse
import csv
import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
OLLAMA_URL = "http://localhost:11434/api/generate"
BASE_SEED = 2026

INSTRUCTIONS = """This is a psychology feature-listing task. We need information on what people know about different things in the world.

For the word below, list as many properties of the concept as you can think of. Properties can be physical (internal/external parts, how it looks, sounds, smells, feels, or tastes), functional (what it is used for; where, when, or by whom it is used), categorical (what group or category it belongs to), or other facts (how it behaves, or where it comes from). Consider the word only as a noun.

Give your answer as a single comma-separated list, in the same style as these examples:

duck: is a bird, is an animal, waddles, flies, migrates, lays eggs, quacks, swims, has wings, has a beak, has webbed feet, has feathers, lives in ponds, lives in water, hunted by people, is edible
cucumber: is a vegetable, has green skin, has a white inside, has seeds, is cylindrical, is long, grows in gardens, grows on vines, is edible, is crunchy, used for making pickles, eaten in salads
stove: is an appliance, produces heat, inside has elements, inside has an oven, made of metal, is hot, is electrical, runs on wood, runs on gas, found in kitchens, used for baking, used for cooking food
"""
FEW_BLOCK = "\nHere are lists written by other participants for other words:\n\n{examples}\n"
ENDING = "\nNow give the comma-separated list of properties for this word. Output ONLY the comma-separated list, nothing else.\n\n{cue}:"


def fewshot_examples(n_total=8):
    path = RESULTS / "fewshot_examples.csv"
    if path.exists():
        return pd.read_csv(path)
    pool = pd.read_csv(RESULTS / "inputs/fewshot_pool.csv", keep_default_na=False)
    cues = pd.read_csv(RESULTS / "cues.csv", keep_default_na=False)
    pool = pool.merge(cues[["cue", "quintile"]], on="cue")
    rng = np.random.default_rng(BASE_SEED)
    picks = []
    for q, k in zip([1, 2, 3, 4, 5], [2, 2, 1, 1, 2]):
        g = pool[(pool.quintile == q) & pool.answer.str.count(",").between(4, 9)]
        g = g.drop_duplicates("cue")
        picks.append(g.iloc[rng.permutation(len(g))[:k]])
    ex = pd.concat(picks)[["cue", "quintile", "answer"]].reset_index(drop=True)
    ex.to_csv(path, index=False)
    return ex


def build_prompt(condition, cue):
    text = INSTRUCTIONS
    if condition == "few":
        ex = fewshot_examples()
        text += FEW_BLOCK.format(examples="\n".join(f"{c}: {a}" for c, a in zip(ex.cue, ex.answer)))
    return text + ENDING.format(cue=cue)


def call(model, prompt, temperature, seed):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": temperature, "seed": seed, "num_predict": 200}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())["response"]


def first_list(text):
    for line in text.strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--condition", choices=["zero", "few"], required=True)
    ap.add_argument("--split", choices=["calibration", "test"], required=True)
    ap.add_argument("--temps", nargs="+", type=float, default=[0.9])
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--wave", type=int, default=0, help="test cues: 1 = first 12 per concreteness quintile, 2 = next 8, 3 = remaining 20, 0 = all")
    ap.add_argument("--cal-cues", type=int, default=2, help="calibration cues per concreteness quintile")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=str(RESULTS / "generations.csv"))
    a = ap.parse_args()

    cues = pd.read_csv(RESULTS / "cues.csv", keep_default_na=False)
    cues = cues[cues.split == a.split].copy()
    cues["rank"] = cues.groupby("quintile").cumcount()
    if a.split == "calibration":
        cues = cues[cues["rank"] < a.cal_cues]
    elif a.wave:
        # wave 1: 12 cues per concreteness quintile (60), wave 2: the next 8 (100 in total), wave 3: the rest (200)
        cues = cues[{1: cues["rank"] < 12, 2: (cues["rank"] >= 12) & (cues["rank"] < 20), 3: cues["rank"] >= 20}[a.wave]]
    cue_list = cues["cue"].tolist()

    out = Path(a.out)
    done = set()
    if out.exists():
        old = pd.read_csv(out, keep_default_na=False)
        done = set(zip(old.model, old.condition, old.temperature.astype(float), old.cue, old.run.astype(int)))
    jobs = [(c, t, r) for t in a.temps for c in cue_list for r in range(a.runs)
            if (a.model, a.condition, float(t), c, r) not in done]
    print(f"{a.model} / {a.condition} / {a.split}: {len(cue_list)} cues, {len(jobs)} runs to do ({len(done)} already done)", flush=True)
    if not jobs:
        return

    new_file = not out.exists()
    lock = threading.Lock()
    f = open(out, "a", newline="")
    w = csv.writer(f)
    if new_file:
        w.writerow(["model", "condition", "temperature", "cue", "run", "text"])
    counter = {"n": 0}

    def work(job):
        cue, temp, run = job
        text = first_list(call(a.model, build_prompt(a.condition, cue), temp, BASE_SEED + run))
        with lock:
            w.writerow([a.model, a.condition, temp, cue, run, text])
            counter["n"] += 1
            if counter["n"] % 100 == 0:
                f.flush()
                print(f"  {counter['n']}/{len(jobs)}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    f.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
