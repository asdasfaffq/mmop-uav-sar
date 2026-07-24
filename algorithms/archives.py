"""Module 2 -- Three-Archive System.

Archive 1 (ParetoObjectiveArchive): high-quality feasible non-dominated solutions
    -> guards objective-space convergence & quality.
Archive 2 (DecisionModeArchive): representatives of distinct decision-space modes
    -> prevents collapse onto a single Pareto set (the MMOP failure mode).
Archive 3 (RouteFamilyArchive): UAV-specific, lives in route_family_archive.py and
    is only instantiated for the application (Phase 10).

The two benchmark archives cooperate: the Pareto archive enforces convergence,
while the decision-mode archive enforces equivalence coverage. Truncation uses
*objective* crowding for Archive 1 and *decision-space* crowding for Archive 2,
so each preserves diversity in the space it is responsible for.
"""
from __future__ import annotations

import numpy as np

from algorithms.equivalence_fitness import (crowding_distance,
                                            fast_nondominated_sort)


class ParetoObjectiveArchive:
    """Bounded archive of feasible non-dominated solutions (objective quality)."""

    def __init__(self, capacity: int):
        self.capacity = int(capacity)
        self.X = np.empty((0, 0))
        self.F = np.empty((0, 0))

    def update(self, X: np.ndarray, F: np.ndarray, CV: np.ndarray | None = None):
        X = np.atleast_2d(X); F = np.atleast_2d(F)
        if CV is None:
            CV = np.zeros(len(X))
        feas = CV <= 0
        if not feas.any():
            return
        X, F = X[feas], F[feas]
        if self.X.shape[0] == 0:
            allX, allF = X, F
        else:
            allX = np.vstack([self.X, X])
            allF = np.vstack([self.F, F])
        # keep first front only
        fronts = fast_nondominated_sort(allF)
        nd = fronts[0]
        allX, allF = allX[nd], allF[nd]
        # dedup
        allX, allF = _dedup(allX, allF)
        if len(allX) > self.capacity:
            allX, allF = _truncate_by_crowding(allX, allF, allF, self.capacity)
        self.X, self.F = allX, allF

    def __len__(self):
        return self.X.shape[0]


class EpsilonBandDiversityArchive:
    """Convergence-gated decision-diversity archive (the redesigned MMOP core).

    Resolves the convergence/diversity trade-off that single-population MMOEAs face:
      1. ADMIT only solutions whose objective vector lies within an epsilon band of
         the running non-dominated front (in NORMALISED objective space) -- i.e. only
         *already-converged* solutions enter. This decouples convergence from
         diversity, so maximising decision spread here cannot hurt IGD.
      2. TRUNCATE by decision-space kNN density (keep the sparsest) -- so the archive
         maximises decision-space (Pareto-set) coverage among converged solutions.

    The archive accumulates such solutions across the whole run, then is reported
    (truncated to N) as the final solution set: converged AND decision-diverse.
    """

    def __init__(self, capacity: int, epsilon: float = 0.02, k: int = 3,
                 feature_fn=None):
        self.capacity = int(capacity)
        self.epsilon = float(epsilon)
        self.k = int(k)
        # optional topology feature map: when given, the decision-spread truncation
        # operates in FEATURE space (route-family structure) instead of raw decision
        # space -- this is what maintains route-family diversity on the UAV problem.
        self.feature_fn = feature_fn
        self.X = np.empty((0, 0))
        self.F = np.empty((0, 0))
        self._ideal = None
        self._nadir = None

    def _update_bounds(self, F):
        lo = F.min(0); hi = F.max(0)
        self._ideal = lo if self._ideal is None else np.minimum(self._ideal, lo)
        self._nadir = hi if self._nadir is None else np.maximum(self._nadir, hi)

    def _norm(self, F):
        rng = self._nadir - self._ideal
        rng = np.where(rng < 1e-12, 1.0, rng)
        return (F - self._ideal) / rng

    def update(self, X, F, CV=None):
        X = np.atleast_2d(np.asarray(X, float)); F = np.atleast_2d(np.asarray(F, float))
        if CV is None:
            CV = np.zeros(len(X))
        feas = np.asarray(CV) <= 0
        if not feas.any():
            return
        X, F = X[feas], F[feas]
        self._update_bounds(F)
        # combine with existing archive, then gate against the GLOBAL best front so
        # stale members dominated by later solutions are pruned (protects IGD).
        if self.X.shape[0]:
            allX = np.vstack([self.X, X]); allF = np.vstack([self.F, F])
        else:
            allX, allF = X, F
        allX, allF = _dedup(allX, allF)
        nd = fast_nondominated_sort(allF)[0]
        Fn = self._norm(allF); frontN = Fn[nd]
        diff = np.maximum(Fn[:, None, :] - frontN[None, :, :], 0.0)   # IGD+ to front
        dpf = np.linalg.norm(diff, axis=2).min(axis=1)
        near = dpf <= self.epsilon                                    # converged band
        allX, allF = allX[near], allF[near]
        if len(allX) > self.capacity:
            allX, allF = self._truncate_by_density(allX, allF, self.capacity)
        self.X, self.F = allX, allF

    def _truncate_by_density(self, X, F, cap):
        """One-shot O(n^2) decision-space density truncation: keep the `cap` points
        with the largest kNN distance (sparsest), with the two extreme (boundary)
        points always retained so the PS span is covered."""
        n = len(X)
        if n <= cap:
            return X, F
        rep = self.feature_fn(X) if self.feature_fn is not None else X
        Xn = _norm01(rep)
        D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
        np.fill_diagonal(D, np.inf)
        kk = min(self.k, n - 1)
        knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)   # larger = sparser = keep
        # guarantee the per-dimension extreme points survive (PS span coverage)
        keep_force = set(np.argmin(Xn, axis=0).tolist()) | set(np.argmax(Xn, axis=0).tolist())
        knn_adj = knn.copy()
        knn_adj[list(keep_force)] = np.inf
        sel = np.argsort(-knn_adj)[:cap]
        return X[sel], F[sel]

    def report(self, n):
        """Return up to n archive members, spread by decision-space density."""
        if len(self.X) <= n:
            return self.X, self.F
        return self._truncate_by_density(self.X, self.F, n)

    def __len__(self):
        return self.X.shape[0]


def _norm01(A):
    lo = A.min(0); rng = A.max(0) - lo; rng = np.where(rng < 1e-12, 1.0, rng)
    return (A - lo) / rng


class DecisionModeArchive:
    """Bounded archive preserving distinct decision-space modes.

    Accepts solutions that are non-dominated (loosely) and, when full, removes the
    one most crowded in *decision* space -- so it retains the widest spread of
    equivalent decision-space solutions.
    """

    def __init__(self, capacity: int):
        self.capacity = int(capacity)
        self.X = np.empty((0, 0))
        self.F = np.empty((0, 0))

    def update(self, X: np.ndarray, F: np.ndarray, CV: np.ndarray | None = None):
        X = np.atleast_2d(X); F = np.atleast_2d(F)
        if CV is None:
            CV = np.zeros(len(X))
        feas = CV <= 0
        if not feas.any():
            return
        X, F = X[feas], F[feas]
        if self.X.shape[0] == 0:
            allX, allF = X, F
        else:
            allX = np.vstack([self.X, X])
            allF = np.vstack([self.F, F])
        # restrict to (near) non-dominated set to keep quality, but keep more
        # fronts than Archive 1 so decision diversity is not over-pruned.
        # (Phase-8 note: a front-0-only variant was tested; it did not yield a
        # validation-confirmed IGDX gain because the final reported union is
        # already non-dominated-filtered, so it was reverted to keep the design
        # identical to the validated Phase-7 algorithm.)
        fronts = fast_nondominated_sort(allF)
        keep = np.concatenate(fronts[:2]) if len(fronts) > 1 else fronts[0]
        allX, allF = allX[keep], allF[keep]
        allX, allF = _dedup(allX, allF)
        if len(allX) > self.capacity:
            # truncate by DECISION-space crowding (preserve decision diversity)
            allX, allF = _truncate_by_crowding(allX, allF, allX, self.capacity)
        self.X, self.F = allX, allF

    def __len__(self):
        return self.X.shape[0]


# --------------------------------------------------------------------------
def _dedup(X, F, tol=1e-9):
    if len(X) == 0:
        return X, F
    _, idx = np.unique(np.round(X / tol).astype(np.int64), axis=0, return_index=True)
    idx = np.sort(idx)
    return X[idx], F[idx]


def _truncate_by_crowding(X, F, space_for_crowding, capacity):
    """Iteratively drop the most-crowded point (in the given space) until <= cap."""
    X, F, S = X.copy(), F.copy(), space_for_crowding.copy()
    while len(X) > capacity:
        cd = crowding_distance(S)
        drop = int(np.argmin(cd))  # most crowded (smallest distance)
        X = np.delete(X, drop, axis=0)
        F = np.delete(F, drop, axis=0)
        S = np.delete(S, drop, axis=0)
    return X, F
