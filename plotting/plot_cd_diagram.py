"""Critical-difference (CD) diagram (Demsar 2006) for a metric across problems.

Computes per-problem ranks, average ranks, and the Nemenyi critical difference, then
draws the standard CD diagram (algorithms on a rank axis; groups within CD connected).

Usage:
  python plotting/plot_cd_diagram.py --experiment benchmark --metric IGDX
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from scipy.stats import rankdata

from metrics.indicators import DIRECTION
from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR, RAW_DIR

# Nemenyi q_alpha (alpha=0.05) for k = 2..10
_Q05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949,
        8: 3.031, 9: 3.102, 10: 3.164}


def _per_problem_means(experiment, metric):
    data = defaultdict(lambda: defaultdict(list))
    for jf in (RAW_DIR / experiment).glob("*/*/run_*.json"):
        r = json.loads(jf.read_text())
        if metric in r["metrics"]:
            data[r["problem"]][r["algorithm"]].append(r["metrics"][metric])
    problems = sorted(data)
    algos = sorted({a for p in data.values() for a in p})
    M = np.full((len(problems), len(algos)), np.nan)
    for i, p in enumerate(problems):
        for j, a in enumerate(algos):
            if data[p][a]:
                M[i, j] = np.mean(data[p][a])
    return M, problems, algos


def plot(experiment="benchmark", metric="IGDX", out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    M, problems, algos = _per_problem_means(experiment, metric)
    lower = DIRECTION.get(metric, "min") == "min"
    ranks = np.array([rankdata(row if lower else -row) for row in M])
    avg = ranks.mean(0)
    k = len(algos); N = len(problems)
    cd = _Q05.get(k, 3.2) * np.sqrt(k * (k + 1) / (6.0 * N))

    order = np.argsort(avg)
    names = [algos[i] for i in order]; rk = avg[order]
    lo, hi = 1, k
    fig, ax = plt.subplots(figsize=(9, 3.2)); ax.set_xlim(lo - 0.5, hi + 0.5); ax.set_ylim(0, 5)
    ax.axis("off")
    ax.plot([lo, hi], [4, 4], "k", lw=1.2)
    for r in range(lo, hi + 1):
        ax.plot([r, r], [4, 4.15], "k", lw=1.0); ax.text(r, 4.35, str(r), ha="center", fontsize=9)
    # place labels left/right by rank
    half = (k + 1) / 2
    for idx, (nm, r) in enumerate(zip(names, rk)):
        if r <= half:
            yy = 3.5 - idx * 0.45
            ax.plot([r, r], [4, yy], "k", lw=0.8); ax.plot([r, lo - 0.4], [yy, yy], "k", lw=0.8)
            ax.text(lo - 0.5, yy, f"{nm} ({r:.2f})", ha="right", va="center", fontsize=8.5)
        else:
            yy = 3.5 - (k - 1 - idx) * 0.45
            ax.plot([r, r], [4, yy], "k", lw=0.8); ax.plot([r, hi + 0.4], [yy, yy], "k", lw=0.8)
            ax.text(hi + 0.5, yy, f"{nm} ({r:.2f})", ha="left", va="center", fontsize=8.5)
    # CD bar
    ax.plot([lo, lo + cd], [4.7, 4.7], "k", lw=2.5)
    ax.text(lo + cd / 2, 4.85, f"CD = {cd:.2f}", ha="center", fontsize=9)
    # connect groups within CD
    yb = 3.75
    for i in range(k):
        for j in range(i + 1, k):
            if rk[j] - rk[i] <= cd:
                ax.plot([rk[i], rk[j]], [yb, yb], "k", lw=3, solid_capstyle="round")
                yb -= 0.12
                break
    ax.set_title(f"Critical-difference diagram -- {experiment} / {metric} "
                 f"(N={N} problems, alpha=0.05)", fontsize=11)
    out_stem = out_stem or (FIG_DIR / f"cd_{experiment}_{metric}")
    save(fig, out_stem); plt.close(fig); print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="benchmark")
    ap.add_argument("--metric", default="IGDX")
    args = ap.parse_args()
    plot(args.experiment, args.metric)
