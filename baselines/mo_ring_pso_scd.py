"""MO_Ring_PSO_SCD (Yue, Qu, Liang, IEEE TEVC 22(5):805-817, 2018).

Multi-objective PSO with a **ring topology** (each particle's neighbourhood is
itself and its two ring neighbours) and the **Special Crowding Distance (SCD)**
that fuses objective- and decision-space crowding. The ring topology induces
stable niches so that multiple equivalent Pareto sets are tracked; an external
archive of non-dominated solutions is maintained and pruned by SCD.

This is the canonical MMOP baseline (CEC2019-MMO competition winner). Faithfully
reimplemented in Python from the paper + the MATLAB reference (FileExchange #68662).

Key settings (authors' recommended): constriction PSO with chi=0.7298,
c1=c2=2.05, velocity clamped to half the variable range.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from algorithms.equivalence_fitness import (constrained_dominates,
                                            fast_nondominated_sort,
                                            special_crowding_distance)
from baselines import _common as C
from baselines.baseline_registry import register


@register("MO_Ring_PSO_SCD")
class MORingPSOSCD(Algorithm):
    name = "MO_Ring_PSO_SCD"

    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        chi = 0.7298; c1 = c2 = 2.05
        d = prob.n_var
        xl, xu = prob.xl, prob.xu
        vmax = 0.5 * (xu - xl)

        # SCD, optionally wrapped with the within-front sparsity term for the
        # transferability probe (off by default -> identical to the reported runs).
        div = C.resolve_div_fn(special_crowding_distance, self.params)

        X = rng.uniform(xl, xu, size=(N, d))
        V = np.zeros((N, d))
        out = self._evaluate(X); F, CV = out["F"], out["CV"]
        pbestX, pbestF = X.copy(), F.copy()

        feas0 = CV <= 0
        if feas0.any():
            archX, archF = self._nd(X[feas0], F[feas0])
        else:
            archX, archF = X[:0].copy(), F[:0].copy()
        cap = N

        while self.budget_left >= N:
            # neighbourhood (ring) best per particle from neighbours' pbests
            nbest = self._ring_nbest(pbestX, pbestF, rng, div)
            r1 = rng.random((N, d)); r2 = rng.random((N, d))
            V = chi * (V + c1 * r1 * (pbestX - X) + c2 * r2 * (nbest - X))
            V = np.clip(V, -vmax, vmax)
            X = X + V
            # reflect at bounds, zero the velocity component
            below = X < xl; above = X > xu
            X = np.clip(X, xl, xu)
            V[below | above] = 0.0

            out = self._evaluate(X); F, CV = out["F"], out["CV"]
            # personal-best update
            for i in range(N):
                if constrained_dominates(F[i], CV[i], pbestF[i], 0.0):
                    pbestX[i], pbestF[i] = X[i], F[i]
                elif not constrained_dominates(pbestF[i], 0.0, F[i], CV[i]):
                    if rng.random() < 0.5:
                        pbestX[i], pbestF[i] = X[i], F[i]
            # archive update with SCD pruning
            archX, archF = self._update_archive(archX, archF, X, F, cap, CV=CV,
                                                div=div)

        # final output: external archive (feasible non-dominated, SCD-spread).
        # fallback to the least-violating particles if no feasible ever found.
        if len(archX) == 0:
            order = np.argsort(CV)[:N]
            archX, archF = X[order], F[order]
        return Result(X=archX, F=archF, CV=np.zeros(len(archX)),
                      n_evaluations=self.evaluations_used)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _nd(X, F):
        nd = fast_nondominated_sort(F)[0]
        return X[nd].copy(), F[nd].copy()

    def _ring_nbest(self, pbestX, pbestF, rng, div=special_crowding_distance):
        N = len(pbestX)
        nbest = np.empty_like(pbestX)
        for i in range(N):
            nb = [(i - 1) % N, i, (i + 1) % N]
            sub = pbestF[nb]
            fronts = fast_nondominated_sort(sub)
            cand = [nb[j] for j in fronts[0]]
            if len(cand) == 1:
                nbest[i] = pbestX[cand[0]]
            else:
                # pick the most diverse by SCD among the non-dominated neighbours
                scd = div(pbestF[cand], pbestX[cand])
                best = np.argwhere(scd == scd.max()).ravel()
                nbest[i] = pbestX[cand[int(rng.choice(best))]]
        return nbest

    def _update_archive(self, archX, archF, X, F, cap, CV=None,
                        div=special_crowding_distance):
        # fair constraint handling: only feasible solutions enter the archive
        if CV is not None:
            feas = np.asarray(CV) <= 0
            if feas.any():
                X, F = X[feas], F[feas]
            else:
                return archX, archF
        allX = np.vstack([archX, X]); allF = np.vstack([archF, F])
        nd = fast_nondominated_sort(allF)[0]
        allX, allF = allX[nd], allF[nd]
        # dedup
        _, uidx = np.unique(np.round(allX, 9), axis=0, return_index=True)
        allX, allF = allX[np.sort(uidx)], allF[np.sort(uidx)]
        if len(allX) > cap:
            scd = div(allF, allX)
            keep = np.argsort(-scd)[:cap]
            allX, allF = allX[keep], allF[keep]
        return allX, allF
