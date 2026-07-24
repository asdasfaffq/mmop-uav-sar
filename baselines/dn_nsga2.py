"""DN-NSGA-II -- Decision-space Niching NSGA-II (Liang, Yue, Qu, IEEE CEC 2016).

Faithful structure: standard NSGA-II (binary-tournament mating, SBX+PM, R=P+Q,
non-dominated sort, last-front truncation) but with the **crowding distance
computed in DECISION space** so decision-space diversity (multiple equivalent
Pareto sets) is preserved. Both the mating tournament and the environmental
truncation use the decision-space crowding.

Reimplemented in Python from the paper; uses the project's shared NSGA-II core.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from baselines import _common as C
from baselines.baseline_registry import register


@register("DN_NSGAII")
class DNNSGAII(Algorithm):
    name = "DN_NSGAII"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        eta_c = self.params.get("sbx_eta", 20); pc = self.params.get("sbx_prob", 0.9)
        eta_m = self.params.get("pm_eta", 20); pm = self.params.get("pm_prob", 1.0 / prob.n_var)

        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]
        div_fn = C.div_decision

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
