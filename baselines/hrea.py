"""HREA -- Hierarchy Ranking based Evolutionary Algorithm for multimodal
multi-objective optimization (Li, Xiang, Yang, Cao, Liu, Yang, IEEE TEVC 27(1):
98-110, 2023).

Mechanism: HREA's distinguishing feature is a *hierarchy ranking* that handles both
GLOBAL and LOCAL Pareto fronts. The population is partitioned into decision-space
peaks (niches); within each peak a local non-dominated sort gives a local Pareto
rank, and the environmental selection combines the global Pareto rank with the local
structure so that locally non-dominated solutions (local Pareto sets) are retained --
gated by a parameter p that controls how much local structure to keep. This lets HREA
preserve several equivalent/locally-optimal decision-space sets rather than collapsing
to the single global one.

Implementation note (honest): this is a faithful-in-spirit Python reimplementation of
the hierarchy-ranking principle (official code: gengfengli/HREA). It uses a k-means
peak partition with a within-peak non-dominated sort and a p-gated local-front
retention, plus special-crowding-distance tie-breaks, rather than the original's exact
peak-detection routine, for tractability at the project's population size; fidelity is
checked on MMF (it must recover multiple equivalent Pareto sets and reach IGDX
competitive with the other baselines), and any gap is reported, not hidden.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from algorithms.equivalence_fitness import fast_nondominated_sort, special_crowding_distance
from baselines import _common as C
from baselines.baseline_registry import register


def _norm(A):
    lo = A.min(0); rng = A.max(0) - lo; rng[rng < 1e-12] = 1.0
    return (A - lo) / rng


def _front_rank(F, CV):
    """Per-individual non-dominated front index (0 = global Pareto front)."""
    fronts = fast_nondominated_sort(F, CV)
    rank = np.empty(len(F), dtype=int)
    for lvl, fr in enumerate(fronts):
        rank[fr] = lvl
    return rank


def _peaks(X, n_peaks, rng):
    """Decision-space peak partition (k-means); falls back to a single peak."""
    from sklearn.cluster import KMeans
    n = len(X)
    k = int(max(1, min(n_peaks, n)))
    if k <= 1:
        return np.zeros(n, dtype=int)
    seed = int(rng.integers(0, 2**31 - 1))
    lab = KMeans(n_clusters=k, n_init=3, random_state=seed).fit_predict(_norm(X))
    return lab


def hrea_environmental(X, F, CV, n_select, n_peaks, p_local, rng):
    """Hierarchy-ranking environmental selection.

    Hierarchy key = global front rank + p_local * local (within-peak) front rank.
    Solutions that are locally non-dominated (local rank 0) are thus only mildly
    penalised, so local Pareto sets in distinct decision-space peaks are retained;
    p_local interpolates between pure global selection (p=large) and strong local
    retention (p small). Ties are broken by special crowding distance (objective +
    decision space), keeping spread-out solutions.
    """
    n = len(X)
    g = _front_rank(F, CV).astype(float)
    lab = _peaks(X, n_peaks, rng)
    local = np.zeros(n)
    for c in np.unique(lab):
        idx = np.where(lab == c)[0]
        if len(idx) == 1:
            local[idx] = 0.0
            continue
        lr = _front_rank(F[idx], None if CV is None else CV[idx]).astype(float)
        local[idx] = lr
    key = g + p_local * local                     # hierarchy rank (lower = better)
    scd = special_crowding_distance(F, X)          # tie-break (higher = better)
    # sort by hierarchy key asc, then SCD desc
    order = np.lexsort((-scd, key))
    return order[:n_select]


@register("HREA")
class HREA(Algorithm):
    name = "HREA"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        Fde = self.params.get("de_F", 0.5); CR = self.params.get("de_CR", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)
        # HREA hyper-parameters
        n_peaks = int(self.params.get("hrea_peaks", max(2, int(round(np.sqrt(N / 2.0))))))
        p_local = float(self.params.get("hrea_p", 0.5))

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]

        while self.budget_left >= N:
            # GA reproduction (SBX + PM), standard for HREA-family
            P = C.sbx_crossover(X, rng, self.params.get("sbx_eta", 15),
                                self.params.get("sbx_prob", 0.9), prob.xl, prob.xu)
            Q = C.polynomial_mutation(P, rng, eta_m, pm, prob.xl, prob.xu)
            qo = self._evaluate(Q)
            RX = np.vstack([X, Q]); RF = np.vstack([F, qo["F"]])
            RCV = np.concatenate([CV, qo["CV"]])
            idx = hrea_environmental(RX, RF, RCV, N, n_peaks, p_local, rng)
            X, F, CV = RX[idx], RF[idx], RCV[idx]

        return Result(X=X, F=F, CV=CV, n_evaluations=self.evaluations_used)
