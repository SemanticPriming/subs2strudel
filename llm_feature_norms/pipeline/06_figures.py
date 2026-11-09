"""
Step 6: poster figures for SCiP 2026.

Reads llm_feature_norms/results/ (written by 05_score.py) and writes PNG (300 dpi) and
SVG files to presentations/scip_2026/figures/. Sized and lettered for a poster: large
type, direct labels, one idea per figure.

  fig1_overview.png        how the study works (with a real example run through the processing)
  fig2_coverage.png        how much of the human top-10 each method recovers, against 20 people
  fig3_concreteness.png    the same, by how concrete the cue is
  fig4_predictors.png      what predicts coverage (concreteness, frequency, length)
  fig5_examples.png        one concrete and one abstract cue, human vs model features
  fig6_threshold.png       coverage as the bar rises: found in at least 1, 2, ... 10 of 20 runs

  python 06_figures.py [--results DIR] [--out DIR]
"""
import argparse
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpecFromSubplotSpec  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ---- design: one hue per model, condition by tint, humans in neutral ink ----
INK, SUB, MUTED, GRID = "#1c1b1a", "#52514e", "#8a8984", "#e7e6e2"
BLUE, ORANGE = "#2a78d6", "#eb6834"                      # categorical slots 1 and 2 (validated)
HUMAN = "#52514e"
MODEL_COLOR = {"llama3.1": BLUE, "qwen2.5:1.5b": ORANGE}
MODEL_NAME = {"llama3.1": "Llama 3.1 (8B)", "qwen2.5:1.5b": "Qwen 2.5 (1.5B)"}
COND_NAME = {"zero": "zero-shot", "few": "few-shot"}

plt.rcParams.update({
    "font.family": ["Arial", "Helvetica Neue", "DejaVu Sans"],
    "font.size": 18, "axes.titlesize": 21, "axes.labelsize": 18,
    "xtick.labelsize": 16, "ytick.labelsize": 17,
    "text.color": INK, "axes.labelcolor": SUB, "xtick.color": SUB, "ytick.color": INK,
    "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 1.2, "figure.facecolor": "white", "axes.facecolor": "white",
    "svg.fonttype": "none",
})


def tint(hex_color, share):
    """Mix a colour with white (share = amount of white)."""
    c = np.array(mpl.colors.to_rgb(hex_color))
    return tuple(c + (1 - c) * share)


def color_for(model, cond):
    base = MODEL_COLOR[model]
    return base if cond == "few" else tint(base, 0.5)


def label_for(model, cond):
    return f"{MODEL_NAME[model]}\n{COND_NAME[cond]}"


def spread(values, gap):
    """Nudge label positions apart so they never overlap."""
    v = np.asarray(values, float)
    order = np.argsort(v)
    s = v[order].copy()
    for i in range(1, len(s)):
        s[i] = max(s[i], s[i - 1] + gap)
    s += v[order].mean() - s.mean()
    out = np.empty_like(v)
    out[order] = s
    return out


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def methods_present(cov):
    return [(m, c) for m in MODEL_COLOR for c in ["zero", "few"] if ((cov.model == m) & (cov.condition == c)).any()]


# ------------------------------------------------------------------ figure 2
def fig_coverage(cov, out):
    methods = methods_present(cov)
    panels = [("coverage_any", "ceiling_any", "Found in at least 1 of 20 runs"),
              ("coverage_4runs", "ceiling_4runs", "Found in at least 4 of 20 runs (16%)")]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8), sharey=True)
    ypos = np.arange(len(methods))[::-1]
    for ax, (col, ceil_col, title) in zip(axes, panels):
        for y, (m, c) in zip(ypos, methods):
            v = cov[(cov.model == m) & (cov.condition == c)][col].dropna()
            mean, ci = v.mean(), 1.96 * v.std(ddof=1) / np.sqrt(len(v))
            ax.barh(y, mean, height=0.5, color=color_for(m, c), zorder=3)
            ax.plot([mean - ci, mean + ci], [y, y], color=INK, lw=2.4, zorder=4, solid_capstyle="butt")
            ax.vlines([mean - ci, mean + ci], y - 0.13, y + 0.13, color=INK, lw=2.4, zorder=4)
            ax.text(mean - ci - 1.6, y, f"{mean:.0f}%", va="center", ha="right", fontsize=20, fontweight="bold",
                    color="white" if c == "few" else INK, zorder=5)
        ceiling = cov.drop_duplicates("cue")[ceil_col].mean()
        ax.axvline(ceiling, color=HUMAN, lw=2.6, ls=(0, (5, 3)), zorder=2)
        ax.text(ceiling, 1.015, f"20 people: {ceiling:.0f}%", ha="center", va="bottom", fontsize=17, color=HUMAN,
                fontweight="bold", transform=ax.get_xaxis_transform())
        ax.set_xlim(0, 108)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.xaxis.grid(True, color=GRID, lw=1, zorder=0)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.set_title(title, loc="left", color=INK, pad=46)
        ax.set_xlabel("Share of the human top-10 features recovered (%)")
    fig.text(0.5, -0.04, "Whiskers: 95% confidence interval across cues. Dashed line: what 20 randomly chosen people recover.",
             ha="center", fontsize=14, color=SUB)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([label_for(m, c) for m, c in methods])
    fig.tight_layout(w_pad=2.5)
    save(fig, out, "fig2_coverage")


# ------------------------------------------------------------------ figure 3
def fig_concreteness(cov, out):
    methods = methods_present(cov)
    q = cov.groupby("quintile")["concreteness"].mean()
    panels = [("coverage_any", "ceiling_any", "Found in at least 1 of 20 runs"),
              ("coverage_4runs", "ceiling_4runs", "Found in at least 4 of 20 runs (16%)")]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), sharey=True)
    for ax, (col, ceil_col, title) in zip(axes, panels):
        ends = {}
        for m, c in methods:
            g = cov[(cov.model == m) & (cov.condition == c)].groupby("quintile")[col]
            mean, se = g.mean(), g.sem()
            ax.fill_between(mean.index, mean - 1.96 * se, mean + 1.96 * se, color=color_for(m, c), alpha=0.16, lw=0, zorder=2)
            ax.plot(mean.index, mean, color=color_for(m, c), lw=4, marker="o", ms=10, mec="white", mew=2, zorder=4,
                    ls="-" if c == "few" else (0, (1.2, 1.6)))
            ends[(m, c)] = mean.iloc[-1]
        cg = cov.drop_duplicates("cue").groupby("quintile")[ceil_col].mean()
        ax.plot(cg.index, cg, color=HUMAN, lw=3, ls=(0, (5, 3)), zorder=3)
        ends["human"] = cg.iloc[-1]
        keys = list(ends)
        ys = spread([ends[k] for k in keys], 5.5)
        for k, y in zip(keys, ys):
            if k == "human":
                ax.text(5.18, y, "20 people", color=HUMAN, va="center", fontsize=16, fontweight="bold")
            else:
                ax.text(5.18, y, f"{MODEL_NAME[k[0]].split(' (')[0]}, {COND_NAME[k[1]]}", color=INK, va="center", fontsize=15)
        ax.set_xlim(0.8, 6.6)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels([f"{q.loc[i]:.1f}" for i in [1, 2, 3, 4, 5]])
        ax.yaxis.grid(True, color=GRID, lw=1, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title(title, loc="left", pad=14)
        ax.set_xlabel("Cue concreteness (mean rating of each fifth of the cues)\nabstract  →  concrete")
    axes[0].set_ylabel("Share of the human top-10\nfeatures recovered (%)")
    axes[0].set_ylim(0, 105)
    fig.text(0.5, -0.07, "Solid lines: few-shot.  Dotted lines: zero-shot.  Dashed grey line: 20 randomly chosen people.  Bands: 95% confidence interval.",
             ha="center", fontsize=14, color=SUB)
    fig.tight_layout(w_pad=2.5)
    save(fig, out, "fig3_concreteness")


# ------------------------------------------------------------------ figure 4
def fig_predictors(mm, out):
    names = {"concreteness_z": "Concreteness", "log_frequency_z": "Word frequency (log)", "length_z": "Word length"}
    rows = mm.loc[[k for k in names if k in mm.index]]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ypos = np.arange(len(rows))[::-1]
    for y, (k, r) in zip(ypos, rows.iterrows()):
        lo, hi = r["estimate"] - 1.96 * r["se"], r["estimate"] + 1.96 * r["se"]
        sig = r["p"] < 0.05
        col = BLUE if sig else MUTED
        ax.plot([lo, hi], [y, y], color=col, lw=4, solid_capstyle="round", zorder=3)
        ax.plot(r["estimate"], y, "o", ms=17, color=col, mec="white", mew=2.5, zorder=4)
        ax.text(hi + 0.35, y, f"{r['estimate']:+.1f}", va="center", fontsize=19, fontweight="bold", color=INK)
    ax.axvline(0, color=SUB, lw=1.8, zorder=2)
    ax.set_yticks(ypos)
    ax.set_yticklabels([names[k] for k in rows.index])
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color=GRID, lw=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Change in coverage (percentage points) per 1 SD of the predictor\nblue = reliably different from zero; grey = not")
    ax.set_title("What predicts how well a model matches people?", loc="left", pad=14)
    save(fig, out, "fig4_predictors")


# ------------------------------------------------------------------ figure 5
def fig_examples(cov, mf, human, out):
    pick = ("llama3.1", "few") if ((cov.model == "llama3.1") & (cov.condition == "few")).any() else methods_present(cov)[-1]
    m, c = pick
    cues = cov[(cov.model == m) & (cov.condition == c)].drop_duplicates("cue").sort_values("concreteness")
    chosen = [("Most abstract cue", cues.iloc[0].cue), ("Most concrete cue", cues.iloc[-1].cue)]
    fig = plt.figure(figsize=(17, 7.4))
    outer = fig.add_gridspec(1, 2, wspace=0.16)
    for k, (title, cue) in enumerate(chosen):
        h = human[human.cue == cue].set_index("feature")["normalized_feature"].sort_values(ascending=False)
        mod = mf[(mf.model == m) & (mf.condition == c) & (mf.cue == cue)].set_index("feature")["normalized_feature"].sort_values(ascending=False)
        feats = list(h.index[:8]) + [f for f in mod.index[:4] if f not in h.index[:8]]
        hv = np.array([h.get(f, 0) for f in feats])
        mv = np.array([mod.get(f, 0) for f in feats])
        inner = GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[k], width_ratios=[1, 0.62, 1], wspace=0.04)
        axl, axm, axr = (fig.add_subplot(inner[i]) for i in range(3))
        y = np.arange(len(feats))[::-1]
        axl.barh(y, hv, height=0.62, color=HUMAN, zorder=3)
        axr.barh(y, mv, height=0.62, color=MODEL_COLOR[m], zorder=3)
        for ax in (axl, axr):
            ax.set_ylim(-0.7, len(feats) - 0.3)
            ax.set_yticks([])
            ax.set_xticks([0, 50, 100])
            ax.xaxis.grid(True, color=GRID, lw=1, zorder=0)
            ax.set_axisbelow(True)
            ax.spines["left"].set_visible(False)
            ax.tick_params(axis="x", labelsize=14)
        axl.set_xlim(100, 0)
        axr.set_xlim(0, 100)
        axm.set_xlim(0, 1)
        axm.set_ylim(-0.7, len(feats) - 0.3)
        axm.axis("off")
        for yy, f, hval, mval in zip(y, feats, hv, mv):
            in_h = f in h.index[:8]
            axm.text(0.5, yy, f, ha="center", va="center", fontsize=17, color=INK if in_h else MODEL_COLOR[m],
                     fontweight="bold" if in_h else "normal", style="normal" if in_h else "italic")
        axl.set_title("People (%)", loc="right", fontsize=18, color=HUMAN, pad=8, fontweight="bold")
        axr.set_title(f"{MODEL_NAME[m].split(' (')[0]} (%)", loc="left", fontsize=17, color=MODEL_COLOR[m], pad=8, fontweight="bold")
        ctr = cues[cues.cue == cue].iloc[0]
        fig.text(0.5 * (axl.get_position().x0 + axr.get_position().x1), axl.get_position().y1 + 0.145,
                 f"{title}: \u201c{cue}\u201d", ha="center", fontsize=23, fontweight="bold", color=INK)
        fig.text(0.5 * (axl.get_position().x0 + axr.get_position().x1), axl.get_position().y1 + 0.095,
                 f"mean concreteness rating {ctr.concreteness:.1f} of 5", ha="center", fontsize=17, color=SUB)
    fig.text(0.5, -0.02, "Features in blue italics: produced by the model, not in the human top 8", ha="center", fontsize=15, color=SUB)
    save(fig, out, "fig5_examples")


# ------------------------------------------------------------------ figure 1
def fig_overview(out):
    fig, ax = plt.subplots(figsize=(18, 7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 44)
    ax.axis("off")
    boxes = [
        ("The task", ["Same instructions", "people were given:", "\u201clist the properties", "of the word\u201d", "(zero-shot, or plus", "8 human lists)"], MUTED),
        ("20 virtual\nparticipants", ["The model answers", "20 times, each run", "a different random", "seed (= 20 people)"], BLUE),
        ("Processed like\nhuman answers", ["Same cleaning as", "the human data:", "lemmas, stop words", "out, one word each"], BLUE),
        ("Feature norms", ["% of runs that gave", "each feature,", "for each of the", "60 test cues"], BLUE),
        ("Compared with\nreal people", ["Share of the human", "top-10 features the", "model recovers, vs.", "20 real people"], HUMAN),
    ]
    w, gap = 17.6, 2.55
    for k, (head, lines, col) in enumerate(boxes):
        x = 1.0 + k * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 9), w, 32, boxstyle="round,pad=0.15,rounding_size=1.6", fc="white", ec=col, lw=3.4))
        ax.add_patch(plt.Circle((x + 2.3, 38.0), 1.75, color=col, zorder=3))
        ax.text(x + 2.3, 38.0, str(k + 1), ha="center", va="center", color="white", fontsize=17, fontweight="bold", zorder=4)
        ax.text(x + w / 2 + 1.2, 35.0, head, ha="center", va="center", fontsize=17, fontweight="bold", color=INK, linespacing=1.15)
        for n, ln in enumerate(lines):
            ax.text(x + w / 2, 27.2 - 3.35 * n, ln, ha="center", va="center", fontsize=14.5, color=SUB)
        if k < len(boxes) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.35, 25), (x + w + gap - 0.35, 25), arrowstyle="-|>", mutation_scale=26, color=SUB, lw=3))
    ax.text(50, 3.8, "Example, one model run for \u201cchair\u201d:  \u201chas four legs, used for sitting, made of wood\u201d   \u2192   four \u00b7 leg \u00b7 sit \u00b7 wood",
            ha="center", va="center", fontsize=17, color=INK)
    save(fig, out, "fig1_overview")


# ------------------------------------------------------------------ figure 6
def fig_threshold(sweep, out):
    sweep = sweep.assign(method=list(zip(sweep.model, sweep.condition)))
    fig, ax = plt.subplots(figsize=(13, 7))
    ends = {}
    for m, c in methods_present(sweep):
        g = sweep[(sweep.model == m) & (sweep.condition == c)].groupby("min_runs")["coverage"]
        mean, se = g.mean(), g.sem()
        ax.fill_between(mean.index, mean - 1.96 * se, mean + 1.96 * se, color=color_for(m, c), alpha=0.16, lw=0, zorder=2)
        ax.plot(mean.index, mean, color=color_for(m, c), lw=4, marker="o", ms=9, mec="white", mew=2, zorder=4,
                ls="-" if c == "few" else (0, (1.2, 1.6)))
        ends[(m, c)] = mean.iloc[-1]
    cg = sweep.drop_duplicates(["cue", "min_runs"]).groupby("min_runs")["ceiling"].mean()
    ax.plot(cg.index, cg, color=HUMAN, lw=3.5, ls=(0, (5, 3)), zorder=3)
    ends["human"] = cg.iloc[-1]
    keys = list(ends)
    ys = spread([ends[k] for k in keys], 5.2)
    for k, y in zip(keys, ys):
        if k == "human":
            ax.text(10.25, y, "20 people", color=HUMAN, va="center", fontsize=17, fontweight="bold")
        else:
            ax.text(10.25, y, f"{MODEL_NAME[k[0]].split(' (')[0]}, {COND_NAME[k[1]]}", color=INK, va="center", fontsize=15)
    for x, txt in [(1, "at least 1 run"), (4, "at least 4 runs\n(16%, McRae cutoff)")]:
        ax.axvline(x, color=MUTED, lw=1.4, ls=":", zorder=1)
        ax.text(x + 0.12, 3, txt, color=SUB, fontsize=14, va="bottom")
    ax.set_xlim(0.7, 12.6)
    ax.set_xticks(range(1, 11))
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, color=GRID, lw=1, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("A feature counts if it appears in at least this many of the 20 runs (or of the 20 people)")
    ax.set_ylabel("Share of the human top-10\nfeatures recovered (%)")
    ax.set_title("Coverage as the bar for counting a feature rises", loc="left", pad=14)
    fig.text(0.5, -0.03, "Solid lines: few-shot.  Dotted lines: zero-shot.  Dashed grey line: 20 randomly chosen people.  Bands: 95% confidence interval across cues.",
             ha="center", fontsize=13, color=SUB)
    save(fig, out, "fig6_threshold")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(HERE.parent / "results"))
    ap.add_argument("--out", default=str(ROOT / "presentations" / "scip_2026" / "figures"))
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    cov = pd.read_csv(res / "coverage_by_cue.csv")
    mm = pd.read_csv(res / "mixed_model.csv", index_col=0).rename(columns={"Unnamed: 0": "term"})
    mm = mm.rename(columns={"estimate": "estimate"})
    mf = pd.read_csv(res / "model_features.csv", keep_default_na=False)
    human = pd.read_csv(ROOT / "data/human/english_flt.csv", usecols=["cue", "lemma", "normalized_lemma"], keep_default_na=False)
    human = human.drop_duplicates(["cue", "lemma"]).rename(columns={"lemma": "feature", "normalized_lemma": "normalized_feature"})
    human = human[human.cue.isin(set(cov.cue))]

    fig_overview(out)
    fig_coverage(cov, out)
    fig_concreteness(cov, out)
    fig_predictors(mm, out)
    fig_examples(cov, mf, human, out)
    if (res / "coverage_by_threshold.csv").exists():
        fig_threshold(pd.read_csv(res / "coverage_by_threshold.csv"), out)


if __name__ == "__main__":
    main()
