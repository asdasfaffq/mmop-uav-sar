"""Paired analysis of the transferability probe (`run_transfer.py`).

For each foreign backbone, the two arms differ ONLY in whether the within-front
sparsity term is attached, and share the algorithm-independent per-run seed, so the
30 runs per problem are genuinely paired. We therefore use the same statistics as
the ablation: Wilcoxon signed-rank per problem, Holm-corrected over the 8 MMF
problems, reported per metric.

Reference arm = the +WFS variant, so "win" means the transferred term helped.

Writes:
  results/statistics/transfer_<metric>_pairs.csv
  results/statistics/transfer_summary.csv
  docs/transfer_report.md

Usage:
  python experiments/analyze_transfer.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from experiments.run_statistics import load_per_run
from experiments.run_transfer import PAIRS, PAIRS_INSORT, PAIRS_PLACEMENT
from metrics.indicators import DIRECTION
from metrics.statistics import wilcoxon_holm
from utils.io_utils import STATS_DIR

ROOT = Path(__file__).resolve().parent.parent

# a-priori primary metrics (decision-space quality) first, then the convergence
# cost metrics -- same reporting order as the benchmark section of the paper.
PRIMARY = ["IGDX", "PSP"]
SECONDARY = ["IGD", "HV"]


def analyse(per_run_all, problems, alpha=0.05, pairs=None):
    rows = []
    for base, treated in (pairs if pairs is not None else PAIRS):
        for metric in PRIMARY + SECONDARY:
            per_run = per_run_all.get(metric, {})
            lower = DIRECTION.get(metric, "min") == "min"
            res = wilcoxon_holm(per_run, problems, [treated, base], reference=treated,
                                lower_better=lower, alpha=alpha)
            w, t, l = res.wtl[base]
            # aggregate effect: mean over problems of the per-problem mean change
            deltas = []
            for p in problems:
                b = np.asarray(per_run.get(p, {}).get(base, []), float)
                a = np.asarray(per_run.get(p, {}).get(treated, []), float)
                if len(b) and len(a):
                    mb, ma = b.mean(), a.mean()
                    if mb != 0:
                        rel = (ma - mb) / abs(mb) * 100.0
                        deltas.append(-rel if lower else rel)  # positive = better
            rows.append({
                "backbone": base.replace("_base", "").replace("_INSORT", ""),
                "comparison": f"{treated} vs {base}",
                "metric": metric,
                "primary": metric in PRIMARY,
                "win": w, "tie": t, "loss": l,
                "mean_rel_improvement_%": float(np.mean(deltas)) if deltas else np.nan,
                "min_holm_p": float(min(pv.pvalue_holm for pv in res.pairs)),
            })
    return pd.DataFrame(rows), None


def per_problem_table(per_run_all, problems, metric, alpha=0.05):
    lower = DIRECTION.get(metric, "min") == "min"
    out = []
    for base, treated in PAIRS:
        per_run = per_run_all.get(metric, {})
        res = wilcoxon_holm(per_run, problems, [treated, base], reference=treated,
                            lower_better=lower, alpha=alpha)
        for pv in res.pairs:
            out.append({
                "backbone": base.replace("_base", ""),
                "problem": pv.problem,
                "median_base": pv.median_other,
                "median_wfs": pv.median_ref,
                "p_raw": pv.pvalue,
                "p_holm": pv.pvalue_holm,
                "verdict": pv.verdict,      # win = WFS better
            })
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/raw")
    ap.add_argument("--experiment", default="transfer")
    ap.add_argument("--alpha", type=float, default=0.05)
    args = ap.parse_args(argv)

    per_run_all, problems, algorithms = load_per_run(Path(args.results), args.experiment)
    if not problems:
        print(f"no results under {args.results}/{args.experiment}")
        return 1
    missing = [a for pair in PAIRS for a in pair if a not in algorithms]
    if missing:
        print(f"WARNING: missing arms {missing}")

    STATS_DIR.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 160)
    print(f"\nProblems: {problems}\nArms: {algorithms}")

    blocks = [
        ("A. within-front (+WFS) vs untouched backbone", PAIRS, "transfer_summary.csv"),
        ("B. in-sort (same S, front precedence overridden) vs untouched backbone",
         PAIRS_INSORT, "transfer_insort_summary.csv"),
        ("C. head-to-head: within-front vs in-sort placement", PAIRS_PLACEMENT,
         "transfer_placement_summary.csv"),
    ]
    for title, pairs, fname in blocks:
        avail = [(b, t) for b, t in pairs if b in algorithms and t in algorithms]
        if not avail:
            print(f"\n{title}\n  (arms not present yet -- skipped)")
            continue
        df, _ = analyse(per_run_all, problems, args.alpha, pairs=avail)
        df.to_csv(STATS_DIR / fname, index=False)
        print(f"\n{title}")
        print(f"  W/T/L = first arm better, Holm-corrected over {len(problems)} problems "
              f"(alpha={args.alpha}); positive improvement % = first arm better.")
        print(df.to_string(index=False))

    for metric in PRIMARY + SECONDARY:
        per_problem_table(per_run_all, problems, metric, args.alpha).to_csv(
            STATS_DIR / f"transfer_{metric}_pairs.csv", index=False)

    # D. in-sort weight sweep: does ANY in-sort weight recover the within-front result?
    sweep_rows = []
    for bb, wfs in [("DN_NSGAII", "DN_NSGAII_WFS"), ("Omni", "Omni_WFS")]:
        arms = [a for a in algorithms if a.startswith(f"{bb}_INSORT")]
        for arm in sorted(arms):
            lam = arm.split("lam")[-1] if "lam" in arm else "0.5"
            row = {"backbone": bb, "insort_lambda": float(lam)}
            for metric in ["IGDX", "IGD"]:
                per_run = per_run_all.get(metric, {})
                vals_a, vals_w = [], []
                for p in problems:
                    a_v = per_run.get(p, {}).get(arm)
                    w_v = per_run.get(p, {}).get(wfs)
                    if a_v is not None and w_v is not None:
                        vals_a.append(np.median(a_v)); vals_w.append(np.median(w_v))
                row[f"{metric}_insort_med"] = float(np.mean(vals_a)) if vals_a else np.nan
                row[f"{metric}_wf_med"] = float(np.mean(vals_w)) if vals_w else np.nan
            res = wilcoxon_holm(per_run_all.get("IGDX", {}), problems, [wfs, arm],
                                reference=wfs, lower_better=True, alpha=args.alpha)
            w, t, l = res.wtl[arm]
            row.update({"IGDX_WF_wins": w, "ties": t, "IGDX_WF_losses": l})
            sweep_rows.append(row)
    if sweep_rows:
        sweep = pd.DataFrame(sweep_rows).sort_values(["backbone", "insort_lambda"])
        sweep.to_csv(STATS_DIR / "transfer_insort_sweep.csv", index=False)
        print("\nD. in-sort weight sweep -- does any weight recover the within-front result?")
        print("  (medians averaged over the 8 problems; W/T/L = within-front vs that in-sort weight)")
        print(sweep.to_string(index=False, float_format=lambda x: f"{x:.5g}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
