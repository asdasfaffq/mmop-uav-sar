"""Aggregate raw per-run metrics into summary, rank, and statistical-test tables.

Reads results/raw/<experiment>/<problem>/<algorithm>/run_XXX.json (each containing
a `metrics` dict), builds paired-run arrays per metric, and writes:
  results/statistics/<experiment>_<metric>_summary.csv
  results/statistics/<experiment>_<metric>_wtl.csv
  results/statistics/<experiment>_ranks.csv
  results/statistics/<experiment>_friedman.csv
  results/tables/<experiment>_<metric>_summary.tex

Usage:
  python experiments/run_statistics.py --results results/raw --experiment benchmark \
      --reference EARS_MMOEA
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from metrics.indicators import DIRECTION
from metrics.statistics import average_rank, friedman_test
from metrics import tables
from utils.io_utils import STATS_DIR, TABLE_DIR


def load_per_run(raw_dir: Path, experiment: str):
    """Return per_run[metric][problem][algorithm] = list aligned by run index."""
    exp_dir = raw_dir / experiment
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # metric->prob->algo->{run:val}
    problems, algorithms = set(), set()
    for jf in sorted(exp_dir.glob("*/*/run_*.json")):
        rec = json.loads(jf.read_text())
        prob, algo, ri = rec["problem"], rec["algorithm"], rec["run_index"]
        problems.add(prob); algorithms.add(algo)
        for m, v in rec["metrics"].items():
            data[m][prob][algo][ri] = v
    # convert run-dicts to arrays ordered by run index
    out = {}
    for m, pmap in data.items():
        out[m] = {}
        for prob, amap in pmap.items():
            out[m][prob] = {}
            for algo, rmap in amap.items():
                out[m][prob][algo] = np.array([rmap[k] for k in sorted(rmap)], float)
    return out, sorted(problems), sorted(algorithms)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/raw")
    ap.add_argument("--experiment", default="benchmark")
    ap.add_argument("--reference", default="EARS_MMOEA")
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args(argv)

    raw = Path(args.results)
    per_run_all, problems, algorithms = load_per_run(raw, args.experiment)
    if not problems:
        print(f"no results found under {raw/args.experiment}")
        return 1
    # order algorithms with reference first
    if args.reference in algorithms:
        algorithms = [args.reference] + [a for a in algorithms if a != args.reference]

    friedman_rows, rank_frames = [], {}
    for metric, per_run in per_run_all.items():
        lower = DIRECTION.get(metric, "min") == "min"
        # summary + wtl + latex
        summ = tables.summary_table(per_run, problems, algorithms, args.reference, lower, args.alpha)
        tables.save_csv(summ, STATS_DIR / f"{args.experiment}_{metric}_summary.csv")
        tables.save_latex(summ, TABLE_DIR / f"{args.experiment}_{metric}_summary.tex",
                          caption=f"{metric} mean(std) on {args.experiment} "
                                  f"(*=best; +/-/= = {args.reference} better/worse/tie, Holm).",
                          label=f"tab:{args.experiment}_{metric}")
        tables.save_csv(tables.wtl_frame(per_run, problems, algorithms, args.reference, lower, args.alpha),
                        STATS_DIR / f"{args.experiment}_{metric}_wtl.csv")
        # friedman + ranks
        fr = friedman_test(per_run, problems, algorithms, lower)
        fr.update({"metric": metric})
        friedman_rows.append(fr)
        _, mean_rank = average_rank(per_run, problems, algorithms, lower)
        rank_frames[metric] = dict(zip(algorithms, mean_rank))

    pd.DataFrame(friedman_rows).to_csv(STATS_DIR / f"{args.experiment}_friedman.csv", index=False)
    pd.DataFrame(rank_frames).T.to_csv(STATS_DIR / f"{args.experiment}_ranks.csv")
    print(f"[ok] statistics written to {STATS_DIR} and {TABLE_DIR} "
          f"({len(problems)} problems, {len(algorithms)} algorithms, "
          f"{len(per_run_all)} metrics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
