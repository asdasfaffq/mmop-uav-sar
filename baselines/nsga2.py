"""NSGA-II (Deb, Pratap, Agarwal, Meyarivan, IEEE TEVC 6(2):182-197, 2002).

The non-multimodal control. This is the standard algorithm with objective-space crowding
distance -- no decision-space machinery of any kind. It exists to answer the question a
reviewer should ask of every MMOP paper: is the multimodal apparatus needed at all, or
would a plain Pareto-based optimizer already return usable alternatives?

Structurally identical to the DN-NSGA-II port except for the diversity function
(`div_objective` instead of `div_decision`), so any difference between the two isolates
the space in which crowding is measured.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from baselines import _common as C
from baselines.baseline_registry import register


@register("NSGAII")
class NSGAII(Algorithm):
    name = "NSGAII"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        eta_c = self.params.get("sbx_eta", 20); pc = self.params.get("sbx_prob", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]
        div_fn = C.resolve_div_fn(C.div_objective, self.params)

        while self.budget_left >= N:
            rank, div, _ = C.ranks_and_div(F, X, CV, div_fn)
            pool = C.binary_tournament(rank, div, rng, N)
            Q = C.sbx_crossover(X[pool], rng, eta_c, pc, prob.xl, prob.xu)
            Q = C.polynomial_mutation(Q, rng, eta_m, pm, prob.xl, prob.xu)
            qo = self._evaluate(Q)
            RX = np.vstack([X, Q]); RF = np.vstack([F, qo["F"]])
            RCV = np.concatenate([CV, qo["CV"]])
            idx = C.nsga2_environmental(RX, RF, RCV, N, div_fn)
            X, F, CV = RX[idx], RF[idx], RCV[idx]

        return Result(X=X, F=F, CV=CV, n_evaluations=self.evaluations_used)
