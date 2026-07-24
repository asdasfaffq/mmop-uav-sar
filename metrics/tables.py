"""CSV + LaTeX export of summary, rank, and win/tie/loss tables."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from metrics.statistics import (average_rank, per_problem_means, wilcoxon_holm)


def mean_std_frame(per_run, problems, algorithms) -> pd.DataFrame:
    rows = {}
    for p in problems:
        rows[p] = {}
        for a in algorithms:
            v = np.asarray(per_run.get(p, {}).get(a, []), dtype=float)
            rows[p][a] = (np.mean(v), np.std(v)) if len(v) else (np.nan, np.nan)
    return pd.DataFrame(rows).T  # rows=problems, cols=algorithms, cells=(mean,std)


def summary_table(per_run, problems, algorithms, reference, lower_better,
                  alpha=0.05) -> pd.DataFrame:
    """Per-problem 'mean(std)' strings; best in bold-marker '*'; significance vs
    reference marked with +/-/= (reference is better/worse/tie after Holm)."""
    means = per_problem_means(per_run, problems, algorithms)
    cmp = wilcoxon_holm(per_run, problems, algorithms, reference, lower_better, alpha)
    verdict = {(pv.problem, pv.algorithm): pv.verdict for pv in cmp.pairs}

    out = pd.DataFrame(index=problems, columns=algorithms, dtype=object)
    for i, p in enumerate(problems):
        row = means[i]
        if np.all(np.isnan(row)):
            best_j = -1
        else:
            best_j = int(np.nanargmin(row) if lower_better else np.nanargmax(row))
        for j, a in enumerate(algorithms):
            v = np.asarray(per_run.get(p, {}).get(a, []), dtype=float)
            if not len(v):
                out.loc[p, a] = "--"; continue
            cell = f"{np.mean(v):.4e}({np.std(v):.1e})"
            if j == best_j:
                cell = "*" + cell  # best
            if a != reference:
                vd = verdict.get((p, a), "tie")
                cell += {"win": " +", "loss": " -", "tie": " ="}[vd]
            out.loc[p, a] = cell
    return out


def rank_frame(per_run, problems, algorithms, lower_better) -> pd.DataFrame:
    _, mean_rank = average_rank(per_run, problems, algorithms, lower_better)
    return pd.DataFrame({"algorithm": algorithms, "avg_rank": mean_rank}) \
        .sort_values("avg_rank").reset_index(drop=True)


def wtl_frame(per_run, problems, algorithms, reference, lower_better, alpha=0.05):
    cmp = wilcoxon_holm(per_run, problems, algorithms, reference, lower_better, alpha)
    rows = [{"vs": a, "win": w, "tie": t, "loss": l} for a, (w, t, l) in cmp.wtl.items()]
    return pd.DataFrame(rows)


def save_csv(df: pd.DataFrame, path) -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return path


def save_latex(df: pd.DataFrame, path, caption="", label="") -> Path:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    body = df.to_latex(escape=True, na_rep="--")
    if caption or label:
        body = ("\\begin{table}[t]\n\\centering\n"
                + (f"\\caption{{{caption}}}\n" if caption else "")
                + (f"\\label{{{label}}}\n" if label else "")
                + body + "\\end{table}\n")
    path.write_text(body, encoding="utf-8")
    return path
