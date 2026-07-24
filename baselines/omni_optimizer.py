"""Omni-optimizer (Deb & Tiwari, EJOR 185(3):1062-1087, 2008).

NSGA-II framework with the Omni crowding distance that fuses objective-space and
decision-space crowding: a solution above the mean crowding in EITHER space keeps
the larger of its two crowding values, otherwise the smaller (`div_omni`). This
preserves diversity in both spaces and lets the algorithm maintain multiple
equivalent decision-space regions. Restricted/ε duplicate handling from the
original is approximated by the standard NSGA-II elitist replacement.

Reimplemented in Python from the paper; uses the shared NSGA-II core.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from baselines import _common as C
from baselines.baseline_registry import register


@register("OmniOptimizer")
class OmniOptimizer(Algorithm):
    name = "OmniOptimizer"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        eta_c = self.params.get("sbx_eta", 20); pc = self.params.get("sbx_prob", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]
        div_fn = C.div_omni

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
