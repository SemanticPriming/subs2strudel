"""
Step 7a: the same virtual participants as step 2, but keeping the log probability
of every token the model wrote.

Ollama returns, for each generated token, the log probability the model gave it
given everything before it. These are taken from the model's own distribution
(checked: they barely change between temperature 0.7 and 1.5), so exp(logprob) is
the model's probability for the token and -logprob is its surprisal.

The runs are new samples (a seed does not reproduce the stored text in
generations.csv), so 07_logprob_score.py takes the percent of runs and the
probability from the same runs.

Output: results/logprobs.csv with one row per run; `tokens` is a JSON list of
[token, logprob]. Resumes where it stopped.

  python 07_logprob_generate.py --model llama3.1 --condition few --wave 1
"""
import argparse
import csv
import importlib.util
import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gen", HERE / "02_generate.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)
RESULTS = gen.RESULTS


def call(model, prompt, temperature, seed, max_tokens=200):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "logprobs": True,
                          "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens}}).encode()
    req = urllib.request.Request(gen.OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        d = json.loads(resp.read())
    return d["response"], [[t["token"], round(t["logprob"], 5)] for t in d["logprobs"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--condition", choices=["zero", "few", "zero5", "few5"], required=True)
    ap.add_argument("--temp", type=float, default=None, help="default: results/temperature.json")
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--wave", type=int, default=1, help="test cues: 1 = first 12 per concreteness quintile (60), 2 = next 8, 3 = remaining 20, 0 = all")
    ap.add_argument("--cues", nargs="+", help="only these cues (for a pilot)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-tokens", type=int, default=200, help="stop after this many tokens (24 is enough for the first phrase)")
    ap.add_argument("--out", default=str(RESULTS / "logprobs.csv"))
    a = ap.parse_args()
    temp = a.temp if a.temp is not None else json.loads((RESULTS / "temperature.json").read_text())["temperature"]

    cues = pd.read_csv(RESULTS / "cues.csv", keep_default_na=False)
    cues = cues[cues.split == "test"].copy()
    cues["rank"] = cues.groupby("quintile").cumcount()
    if a.wave:
        cues = cues[{1: cues["rank"] < 12, 2: (cues["rank"] >= 12) & (cues["rank"] < 20), 3: cues["rank"] >= 20}[a.wave]]
    cue_list = a.cues or cues["cue"].tolist()

    out = Path(a.out)
    done = set()
    if out.exists():
        old = pd.read_csv(out, keep_default_na=False, usecols=["model", "condition", "temperature", "cue", "run"])
        done = set(zip(old.model, old.condition, old.temperature.astype(float), old.cue, old.run.astype(int)))
    jobs = [(c, r) for c in cue_list for r in range(a.runs) if (a.model, a.condition, float(temp), c, r) not in done]
    print(f"{a.model} / {a.condition}: {len(cue_list)} cues, {len(jobs)} runs to do ({len(done)} already done)", flush=True)
    if not jobs:
        return

    new_file = not out.exists()
    lock = threading.Lock()
    f = open(out, "a", newline="")
    w = csv.writer(f)
    if new_file:
        w.writerow(["model", "condition", "temperature", "cue", "run", "response", "tokens"])
    counter = {"n": 0}

    def work(job):
        cue, run = job
        response, tokens = call(a.model, gen.build_prompt(a.condition, cue), temp, gen.BASE_SEED + run, a.max_tokens)
        with lock:
            w.writerow([a.model, a.condition, temp, cue, run, response, json.dumps(tokens)])
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
