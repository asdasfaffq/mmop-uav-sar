"""Average-rank bar chart per metric from results/statistics/<exp>_ranks.csv.

A compact, honest visual of which algorithm ranks best on each metric (lower rank
= better). Used in Phase 7/12 alongside the Friedman/Wilcoxon tables.

Usage:
  python plotting/plot_rank_tables.py --experiment benchmark
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from plotting._style import algo_style, apply_style, save
from utils.io_utils import FIG_DIR, STATS_DIR


def plot(experiment="benchmark", out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    ranks_csv = STATS_DIR / f"{experiment}_ranks.csv"
    df = pd.read_csv(ranks_csv, index_col=0)  # rows=metrics, cols=algorithms
    metrics = list(df.index); algos = list(df.columns)

    x = np.arange(len(metrics)); w = 0.8 / len(algos)
    fig, ax = plt.subplots(figsize=(1.6 * len(metrics) + 2, 5))
    for j, a in enumerate(algos):
        st = algo_style(a)
        ax.bar(x + j * w, df[a].values, width=w, label=a, color=st["color"],
               edgecolor="white", linewidth=0.4)
    ax.set_xticks(x + 0.4 - w / 2); ax.set_xticklabels(metrics, rotation=20, ha="right")
    ax.set_ylabel("average rank (lower is better)")
    ax.set_title(f"Average rank by metric -- {experiment}")
    ax.legend(ncol=min(len(algos), 3), loc="upper center",
              bbox_to_anchor=(0.5, -0.18), framealpha=0.9)
    out_stem = out_stem or (FIG_DIR / f"{experiment}_average_rank")
    save(fig, out_stem)
    plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="benchmark")
    args = ap.parse_args()
    plot(args.experiment)
