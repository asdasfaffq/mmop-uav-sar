"""Statistical comparison layer for the benchmark study.

Inputs are organised as `per_run[problem][algorithm] -> 1-D array of the metric
over the (paired) independent runs`. Runs are paired across algorithms by index
(same seed protocol), so the paired Wilcoxon signed-rank test is appropriate.

Provides:
  * average_rank      -- mean rank per algorithm across problems (1 = best);
  * friedman_test     -- omnibus test across algorithms over problems;
  * wilcoxon_holm     -- pairwise reference-vs-others with Holm correction and
                         per-problem win/tie/loss verdicts;
  * win_tie_loss      -- aggregated W/T/L counts per algorithm vs the reference.

`lower_better` selects the metric direction (True for IGD/IGDX/..., False for HV/PSP).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats


# --------------------------------------------------------------------------
def per_problem_means(per_run, problems, algorithms) -> np.ndarray:
    """Matrix (n_problems, n_algorithms) of mean metric values."""
    M = np.full((len(problems), len(algorithms)), np.nan)
    for i, p in enumerate(problems):
        for j, a in enumerate(algorithms):
            vals = per_run.get(p, {}).get(a)
            if vals is not None and len(vals):
                M[i, j] = np.mean(vals)
    return M


def average_rank(per_run, problems, algorithms, lower_better: bool):
    """Return (ranks_matrix, mean_rank_per_algorithm). Rank 1 = best per problem."""
    M = per_problem_means(per_run, problems, algorithms)
    ranks = np.full_like(M, np.nan, dtype=float)
    for i in range(M.shape[0]):
        row = M[i]
        valid = ~np.isnan(row)
        vals = row[valid] if lower_better else -row[valid]
        # average ranks for ties
        r = stats.rankdata(vals, method="average")
        ranks[i, valid] = r
    mean_rank = np.nanmean(ranks, axis=0)
    return ranks, mean_rank


def friedman_test(per_run, problems, algorithms, lower_better: bool):
    """Friedman omnibus over problems (blocks) x algorithms (groups)."""
    M = per_problem_means(per_run, problems, algorithms)
    M = M[~np.isnan(M).any(axis=1)]  # complete cases only
    if M.shape[0] < 2 or M.shape[1] < 3:
        return {"statistic": np.nan, "pvalue": np.nan, "n_problems": int(M.shape[0])}
    cols = [M[:, j] for j in range(M.shape[1])]
    stat, p = stats.friedmanchisquare(*cols)
    return {"statistic": float(stat), "pvalue": float(p), "n_problems": int(M.shape[0])}


@dataclass
class PairVerdict:
    problem: str
    algorithm: str
    pvalue: float
    pvalue_holm: float
    median_ref: float
    median_other: float
    verdict: str          # 'win' / 'tie' / 'loss'  (reference vs other)


@dataclass
class ComparisonResult:
    reference: str
    alpha: float
    pairs: list[PairVerdict] = field(default_factory=list)
    wtl: dict[str, tuple[int, int, int]] = field(default_factory=dict)  # algo -> (W,T,L)


def _holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni step-down correction; returns adjusted p-values (same order)."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    prev = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        prev = max(prev, val)
        adj[idx] = min(prev, 1.0)
    return adj.tolist()


def wilcoxon_holm(per_run, problems, algorithms, reference: str,
                  lower_better: bool, alpha: float = 0.05) -> ComparisonResult:
    others = [a for a in algorithms if a != reference]
    raw_pairs = []
    pvals = []
    for p in problems:
        ref_vals = np.asarray(per_run.get(p, {}).get(reference, []), dtype=float)
        for a in others:
            ov = np.asarray(per_run.get(p, {}).get(a, []), dtype=float)
            if len(ref_vals) == 0 or len(ov) == 0 or len(ref_vals) != len(ov):
                pval, mref, moth = np.nan, np.nan, np.nan
            else:
                diff = ref_vals - ov
                if np.allclose(diff, 0.0):
                    pval = 1.0
                else:
                    try:
                        pval = stats.wilcoxon(ref_vals, ov, zero_method="wilcox").pvalue
                    except ValueError:
                        pval = 1.0
                mref, moth = float(np.median(ref_vals)), float(np.median(ov))
            raw_pairs.append((p, a, pval, mref, moth))
            pvals.append(1.0 if np.isnan(pval) else pval)
    adj = _holm(pvals)

    res = ComparisonResult(reference=reference, alpha=alpha)
    wtl = {a: [0, 0, 0] for a in others}  # W,T,L of reference vs a
    for (p, a, pval, mref, moth), pa in zip(raw_pairs, adj):
        if np.isnan(pval) or pa > alpha:
            verdict = "tie"
        else:
            better = (mref < moth) if lower_better else (mref > moth)
            verdict = "win" if better else "loss"
        res.pairs.append(PairVerdict(p, a, float(pval), float(pa), mref, moth, verdict))
        wtl[a][0 if verdict == "win" else 1 if verdict == "tie" else 2] += 1
    res.wtl = {a: tuple(v) for a, v in wtl.items()}
    return res
