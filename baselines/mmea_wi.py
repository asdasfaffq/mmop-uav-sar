"""MMEA-WI -- Weighted Indicator-based EA for Multimodal Multiobjective
Optimization (Li, Zhang, Wang, Ishibuchi et al., IEEE TEVC 25(6):1064-1078, 2021).

Mechanism: an IBEA-style binary additive-epsilon indicator drives objective-space
convergence, but each solution's indicator fitness is **weighted by a
decision-space diversity term** so that solutions in sparse decision regions are
favoured -- letting the algorithm retain multiple equivalent Pareto sets while
still converging. Environmental selection iteratively removes the worst weighted
solution.

Implementation note (honest): faithful-in-spirit Python reimplementation of the
weighted-indicator principle (reference: PlatEMO / Wenhua-Li comparative repo).
The objective indicator is the standard IBEA additive-epsilon; the decision-space
weight is a normalised kNN-sparsity bonus. Fidelity is checked at the Phase 7
validation gate against published numbers; any gap is reported.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from baselines import _common as C
from baselines.baseline_registry import register


def _norm(A):
    lo = A.min(0); rng = A.max(0) - lo; rng[rng < 1e-12] = 1.0
    return (A - lo) / rng


def _epsilon_indicator_matrix(Fn):
    # I[i,j] = max_k (Fn[i,k] - Fn[j,k]) : additive epsilon (i over j)
    return (Fn[:, None, :] - Fn[None, :, :]).max(axis=2)


def _decision_sparsity(X, k=3):
    Xn = _norm(X)
    D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    kk = min(k, len(X) - 1)
    if kk < 1:
        return np.ones(len(X))
    s = np.sort(D, axis=1)[:, :kk].mean(axis=1)
    return _col01(s)  # 1 = sparse (far neighbours)


def _col01(v):
    lo, hi = v.min(), v.max()
    return (v - lo) / (hi - lo) if hi > lo else np.ones_like(v)


def mmea_wi_environmental(X, F, CV, n_select, kappa=0.05, gamma=0.5):
    # feasibility-first (fair constraint handling): if enough feasible solutions
    # exist, select among them by the weighted indicator; otherwise keep all
    # feasible and fill the rest by smallest constraint violation.
    if CV is not None:
        CV = np.asarray(CV, float)
        feas = np.where(CV <= 0)[0]
        if len(feas) >= n_select:
            sub = mmea_wi_environmental(X[feas], F[feas], None, n_select, kappa, gamma)
            return feas[sub]
        if len(feas) < len(X):
            infeas = np.where(CV > 0)[0]
            order = infeas[np.argsort(CV[infeas])]
            need = n_select - len(feas)
            return np.concatenate([feas, order[:need]])
    n = len(X)
    Fn = _norm(F)
    I = _epsilon_indicator_matrix(Fn)
    c = max(np.abs(I).max(), 1e-12)
    # IBEA fitness: higher is better
    fit = np.zeros(n)
    expmat = -np.exp(-I / (c * kappa))
    for i in range(n):
        fit[i] = expmat[:, i].sum() - expmat[i, i]
    spars = _decision_sparsity(X)
    alive = np.ones(n, dtype=bool)
    # weighted fitness: sparse-decision solutions get a survival bonus
    while alive.sum() > n_select:
        wfit = fit + gamma * spars
        wfit[~alive] = np.inf
        worst = int(np.argmin(wfit))
        alive[worst] = False
        # incremental IBEA fitness update
        fit += np.exp(-I[worst, :] / (c * kappa))
        fit[worst] = np.inf
    return np.where(alive)[0]


@register("MMEA_WI")
class MMEAWI(Algorithm):
    name = "MMEA_WI"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        eta_c = self.params.get("sbx_eta", 20); pc = self.params.get("sbx_prob", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)
        kappa = self.params.get("ibea_kappa", 0.05)
        gamma = self.params.get("mmeawi_gamma", 0.5)

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]

        while self.budget_left >= N:
            # mating: random pairs (indicator handles selection pressure)
            pool = rng.integers(0, N, size=N)
            Q = C.sbx_crossover(X[pool], rng, eta_c, pc, prob.xl, prob.xu)
            Q = C.polynomial_mutation(Q, rng, eta_m, pm, prob.xl, prob.xu)
            qo = self._evaluate(Q)
            RX = np.vstack([X, Q]); RF = np.vstack([F, qo["F"]])
            RCV = np.concatenate([CV, qo["CV"]])
            idx = mmea_wi_environmental(RX, RF, RCV, N, kappa=kappa, gamma=gamma)
            X, F, CV = RX[idx], RF[idx], RCV[idx]

        return Result(X=X, F=F, CV=CV, n_evaluations=self.evaluations_used)
