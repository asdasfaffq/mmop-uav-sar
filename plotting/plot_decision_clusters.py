"""Decision-space clustering plot: obtained solutions coloured by detected mode,
overlaid on the analytical Pareto set (the equivalent decision-space branches).

Visualises the MMOP goal -- multiple Pareto-equivalent decision-space sets. For
n_var>2 a 2-D projection (first two variables) is used. Phase 7/10/12.

Usage:
  python plotting/plot_decision_clusters.py --experiment benchmark --problem MMF5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from algorithms.niching import adaptive_niching
from benchmarks import mmf
from plotting._style import apply_style, save, PALETTE
from utils.io_utils import FIG_DIR, RAW_DIR


def _load_decisions(exp, problem, algo, run=0):
    npz = RAW_DIR / exp / problem / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None
    with np.load(npz) as d:
        return d["decisions"]


def plot(experiment, problem, algo="EARS_MMOEA", run=0, out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    p = mmf.make(problem)
    X = _load_decisions(experiment, problem, algo, run)
    fig, ax = plt.subplots(figsize=(6, 5))
    ps = p.pareto_set(2000)
    ax.scatter(ps[:, 0], ps[:, 1], s=4, color="0.7", label="True PS", zorder=1)
    if X is not None:
        info = adaptive_niching(X, p.xl, p.xu, rng=np.random.default_rng(0))
        for m in range(info.n_modes):
            sel = info.labels == m
            ax.scatter(X[sel, 0], X[sel, 1], s=18,
                       color=PALETTE[m % len(PALETTE)],
                       label=f"mode {m+1}", zorder=2, edgecolor="white", linewidth=0.3)
        ax.set_title(f"Decision-space modes -- {problem} / {algo} "
                     f"({info.n_modes} modes)")
    else:
        ax.set_title(f"Decision-space PS -- {problem}")
    ax.set_xlabel(r"$x_1$"); ax.set_ylabel(r"$x_2$")
    # legend OUTSIDE the axes (right) so the many mode entries never cover the curves
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0,
              framealpha=0.95, markerscale=1.4, fontsize=8, ncol=1)
    fig.tight_layout()
    out_stem = out_stem or (FIG_DIR / f"decision_clusters_{problem}")
    save(fig, out_stem)
    plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="benchmark")
    ap.add_argument("--problem", default="MMF5")
    ap.add_argument("--algorithm", default="EARS_MMOEA")
    ap.add_argument("--run", type=int, default=0)
    args = ap.parse_args()
    plot(args.experiment, args.problem, args.algorithm, args.run)
