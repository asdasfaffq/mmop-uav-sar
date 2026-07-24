"""CPDEA -- Convergence-Penalized Density-based Evolutionary Algorithm
(Liu, Ishibuchi, Yen, Nojima, Masuyama, IEEE TEVC 24(3):551-565, 2020).

Mechanism: DE reproduction + environmental selection driven by a
**convergence-penalized decision-space density**. Each solution's decision-space
distances are penalised by how poorly it (or its neighbour) converges, so that
poorly-converged solutions appear denser and are removed first, while
well-converged solutions are retained to maximise decision-space diversity --
directly handling the convergence/diversity imbalance in decision space.

Implementation note (honest): this is a faithful-in-spirit Python reimplementation
of the paper's convergence-penalised density principle (official MATLAB:
`yiping0liu/CPDEA`). It uses a front-structured, one-shot penalised-density
truncation rather than the original's fully-iterative global truncation, for
tractability at the project's population size; fidelity is checked at the Phase 7
validation gate against published IGDX/PSP, and any gap is reported, not hidden.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from algorithms.equivalence_fitness import fast_nondominated_sort
from baselines import _common as C
from baselines.baseline_registry import register


def _norm(A):
    lo = A.min(0); rng = A.max(0) - lo; rng[rng < 1e-12] = 1.0
    return (A - lo) / rng


def _convergence(F):
    """Normalised objective-space distance to the ideal point (lower=better)."""
    Fn = _norm(F)
    return np.linalg.norm(Fn - Fn.min(0), axis=1)


def cpdea_environmental(X, F, CV, n_select, k=3, lam=2.0):
    fronts = fast_nondominated_sort(F, CV)
    chosen: list[int] = []
    for fr in fronts:
        if len(chosen) + len(fr) <= n_select:
            chosen.extend(fr.tolist()); continue
        need = n_select - len(chosen)
        sub_idx = fr
        Xs, Fs = X[sub_idx], F[sub_idx]
        Xn = _norm(Xs)
        D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
        conv = _convergence(Fs)
        # convergence penalty: shrink distances involving poorly-converged points
        pen = 1.0 + lam * (conv[:, None] + conv[None, :])
        pd = D / pen
        np.fill_diagonal(pd, np.inf)
        kk = min(k, len(sub_idx) - 1)
        if kk < 1:
            keep = sub_idx[:need]
        else:
            knn = np.sort(pd, axis=1)[:, :kk].sum(axis=1)  # larger = sparser=better
            keep = sub_idx[np.argsort(-knn)[:need]]
        chosen.extend(np.asarray(keep).tolist())
        break
    return np.asarray(chosen, dtype=int)


@register("CPDEA")
class CPDEA(Algorithm):
    name = "CPDEA"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        Fde = self.params.get("de_F", 0.5); CR = self.params.get("de_CR", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)
        lam = self.params.get("cpdea_lambda", 2.0)

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]

        while self.budget_left >= N:
            Q = C.de_offspring(X, rng, Fde, CR, prob.xl, prob.xu)
            Q = C.polynomial_mutation(Q, rng, eta_m, pm, prob.xl, prob.xu)
            qo = self._evaluate(Q)
            RX = np.vstack([X, Q]); RF = np.vstack([F, qo["F"]])
            RCV = np.concatenate([CV, qo["CV"]])
            idx = cpdea_environmental(RX, RF, RCV, N, lam=lam)
            X, F, CV = RX[idx], RF[idx], RCV[idx]

        return Result(X=X, F=F, CV=CV, n_evaluations=self.evaluations_used)
