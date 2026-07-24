"""Generate the standard figure set from existing results.

After run_benchmark.py + run_statistics.py have produced raw results and the
ranks CSV, this regenerates: average-rank bars, per-problem Pareto-front
comparisons, and decision-space cluster plots. Safe to re-run; skips figures whose
inputs are missing.

Usage:
  python plotting/plot_all.py --experiment benchmark
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines.baseline_registry import ALL_ALGORITHMS
from benchmarks import mmf
from utils.io_utils import RAW_DIR, STATS_DIR
from plotting import (plot_pareto_front, plot_rank_tables, plot_decision_clusters,
                      plot_parameter_analysis)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default="benchmark")
    ap.add_argument("--results", default=None)  # accepted for CLI symmetry
    args = ap.parse_args(argv)
    exp = args.experiment

    made = []
    # 1. average-rank bars (needs ranks CSV)
    if (STATS_DIR / f"{exp}_ranks.csv").exists():
        plot_rank_tables.plot(exp); made.append("average_rank")

    # 2. parameter sensitivity (if analysis ran)
    try:
        plot_parameter_analysis.plot(); made.append("parameter_sensitivity")
    except Exception as e:
        print(f"[skip] parameter_sensitivity ({e})")

    # 3. per-problem Pareto fronts + decision clusters (where raw exists)
    exp_dir = RAW_DIR / exp
    if exp_dir.exists():
        problems = sorted([d.name for d in exp_dir.iterdir() if d.is_dir()
                           and d.name in mmf.MMF_NAMES])
        algos = list(ALL_ALGORITHMS)
        for prob in problems:
            try:
                plot_pareto_front.plot(exp, prob, algos, run=0)
                made.append(f"pareto_{prob}")
            except Exception as e:
                print(f"[skip] pareto {prob} ({e})")
            try:
                plot_decision_clusters.plot(exp, prob, "EARS_MMOEA", run=0)
                made.append(f"clusters_{prob}")
            except Exception as e:
                print(f"[skip] clusters {prob} ({e})")
    print(f"[ok] generated {len(made)} figures: {made}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
