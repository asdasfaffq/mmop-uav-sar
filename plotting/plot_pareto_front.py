"""Pareto-front comparison plot: reference PF + each algorithm's obtained front.

Reads final-population objectives from results/raw/<exp>/<problem>/<algo>/run_000.npz
(or a chosen run) and overlays them on the analytical PF. Used in Phase 7/12.

Usage:
  python plotting/plot_pareto_front.py --experiment benchmark --problem MMF1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from benchmarks import mmf
from plotting._style import algo_style, apply_style, save
from utils.io_utils import FIG_DIR, RAW_DIR


def _load_front(exp, problem, algo, run=0):
    npz = RAW_DIR / exp / problem / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None
    with np.load(npz) as d:
        return d["objectives"]


def plot(experiment, problem, algorithms, run=0, out_stem=None):
    apply_style()
    import matplotlib.pyplot as plt
    p = mmf.make(problem)
    pf = p.pareto_front(500)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(pf[:, 0], pf[:, 1], "-", color="0.5", lw=1.5, label="True PF", zorder=1)
    for a in algorithms:
        F = _load_front(experiment, problem, a, run)
        if F is None:
            continue
        st = algo_style(a)
        ax.scatter(F[:, 0], F[:, 1], s=14, alpha=0.8, label=a,
                   color=st["color"], marker=st["marker"], zorder=2)
    ax.set_xlabel(r"$f_1$"); ax.set_ylabel(r"$f_2$")
    ax.set_title(f"Pareto front comparison -- {problem}")
    ax.legend(loc="best", framealpha=0.9)
    out_stem = out_stem or (FIG_DIR / f"pareto_front_{problem}")
    save(fig, out_stem)
    plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="benchmark")
    ap.add_argument("--problem", default="MMF1")
    ap.add_argument("--run", type=int, default=0)
    ap.add_argument("--algorithms", nargs="*", default=None)
    args = ap.parse_args()
    from baselines.baseline_registry import ALL_ALGORITHMS
    plot(args.experiment, args.problem, args.algorithms or list(ALL_ALGORITHMS), args.run)
