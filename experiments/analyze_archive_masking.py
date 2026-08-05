"""Statistics for the archive-masking causal test (`run_archive_masking.py`).

Reports, per metric, the paired within-front vs in-sort comparison in each reporting
regime, and the effect of removing the archives on each selection key. Because only the
reporting changes between the `_arch` and `_pop` arms of the same key, and seeds are
algorithm-independent, all comparisons are paired.

Usage: python experiments/analyze_archive_masking.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from experiments.run_statistics import load_per_run
from metrics.indicators import DIRECTION
from metrics.statistics import wilcoxon_holm
from utils.io_utils import STATS_DIR

METRICS = ["IGDX", "IGD", "PSP", "HV"]

# (reference, other, label) -- reference is the arm we ask "is it better?"
COMPARISONS = [
    ("WF_arch", "InSort8_arch", "within-front vs in-sort  [archives reported]"),
    ("WF_pop", "InSort8_pop", "within-front vs in-sort  [population only]"),
    ("WF_pop", "WF_arch", "within-front: population-only vs archives"),
    ("InSort8_pop", "InSort8_arch", "in-sort: population-only vs archives"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/raw")
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args(argv)

    per_run_all, problems, arms = load_per_run(Path(args.results), "archive_masking")
    if not problems:
        print("no results"); return 1

    print(f"Problems: {problems}\nArms: {arms}\n")
    print("Mean over all problems x runs:")
    means = []
    for a in ["WF_arch", "InSort8_arch", "NoS_arch", "WF_pop", "InSort8_pop", "NoS_pop"]:
        row = {"arm": a}
        for m in METRICS:
            vals = [v for p in problems for v in per_run_all.get(m, {}).get(p, {}).get(a, [])]
            row[m] = float(np.mean(vals)) if vals else np.nan
        means.append(row)
    mdf = pd.DataFrame(means)
    print(mdf.to_string(index=False, float_format=lambda x: f"{x:.5f}"))
    mdf.to_csv(STATS_DIR / "archive_masking_means.csv", index=False)

    rows = []
    print("\nPaired Wilcoxon, Holm-corrected over the 8 problems "
          f"(alpha={args.alpha}); W/T/L = first arm better.\n")
    for ref, other, label in COMPARISONS:
        cells = []
        for m in METRICS:
            per_run = per_run_all.get(m, {})
            lower = DIRECTION.get(m, "min") == "min"
            res = wilcoxon_holm(per_run, problems, [ref, other], reference=ref,
                                lower_better=lower, alpha=args.alpha)
            w, t, l = res.wtl[other]
            cells.append(f"{w}/{t}/{l}")
            rows.append({"comparison": label, "metric": m,
                         "win": w, "tie": t, "loss": l})
        print(f"  {label:44s}  " + "   ".join(f"{m}: {c}" for m, c in zip(METRICS, cells)))
    pd.DataFrame(rows).to_csv(STATS_DIR / "archive_masking_wtl.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
