"""Scalable-dimension MMOP for the high-dimensional stress test.

Motivation: the standard MMF suite is fixed at a two-dimensional decision space,
so it cannot probe whether the kNN sparsity estimate and the silhouette k-means
niching degrade as the decision dimension grows (a known concern for distance-based
methods in high dimensions). We therefore build a scalable family with a fully
ANALYTIC, verifiable Pareto set.

Construction (ScalableMMF2, dimension d >= 2): take the two-equivalent-set MMF2 in
its first two variables and embed it in d dimensions by appending (d-2) spherical
"distance" variables x_3..x_d that vanish on the Pareto set:

    f1 = x1
    y  = x2 - sqrt(x1)         (x2 <= 1)   or   x2 - 1 - sqrt(x1)   (x2 > 1)
    g  = 4 y^2 - 2 cos(20 pi y / sqrt 2) + 2          (g = 0 at y = 0)
    h  = sum_{i=3}^{d} (x_i - 1/2)^2                  (h = 0 at x_i = 1/2)
    f2 = 1 - sqrt(x1) + 2 g + h

The Pareto set is exactly TWO equivalent branches, x2 = sqrt(x1) and x2 = 1 + sqrt(x1),
with x_3..x_d = 1/2, for x1 in [0,1]; the Pareto front is f2 = 1 - sqrt(f1) for any d.
Thus the number of equivalent global Pareto sets stays fixed at two while the decision
dimension scales, isolating the effect of dimension on the diversity machinery. The
appended variables are genuine nuisance dimensions that the search must converge while
keeping the two modes separated, which is precisely what stresses kNN / k-means.
"""
from __future__ import annotations

import numpy as np

PI = np.pi


def _nondominated(F: np.ndarray) -> np.ndarray:
    keep = np.ones(len(F), bool)
    for i in range(len(F)):
        if not keep[i]:
            continue
        dom = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        dom[i] = False
        keep[dom] = False
    return F[keep]


class ScalableMMF2:
    """MMF2 embedded in d dimensions with (d-2) spherical distance variables."""
    n_obj = 2
    n_ps_branches = 2

    def __init__(self, d: int):
        if d < 2:
            raise ValueError("d must be >= 2")
        self.d = int(d)
        self.n_var = self.d
        self.name = f"ScalMMF2_d{self.d}"
        # x1 in [0,1], x2 in [0,2], distance vars in [0,1]
        self.xl = np.array([0.0, 0.0] + [0.0] * (self.d - 2), float)
        self.xu = np.array([1.0, 2.0] + [1.0] * (self.d - 2), float)

    def _F(self, X: np.ndarray) -> np.ndarray:
        x1, x2 = X[:, 0], X[:, 1]
        # two equivalent valleys at x2 = sqrt(x1) and x2 = 1 + sqrt(x1); assign each
        # point to the nearer valley by folding the raw offset at the 0.5 ridge (this
        # avoids the piecewise seam at x2 = 1 that would mis-score the x1 = 0 boundary).
        y = x2 - np.sqrt(x1)
        y = y - (y > 0.5).astype(float)
        g = 4.0 * y ** 2 - 2.0 * np.cos(20.0 * y * PI / np.sqrt(2.0)) + 2.0
        if self.d > 2:
            h = np.sum((X[:, 2:] - 0.5) ** 2, axis=1)
        else:
            h = np.zeros_like(x1)
        return np.column_stack([x1, 1.0 - np.sqrt(x1) + 2.0 * g + h])

    def evaluate(self, X):
        X = np.atleast_2d(np.asarray(X, float))
        return {"F": self._F(X), "CV": np.zeros(X.shape[0])}

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = np.linspace(0.0, 1.0, per)
        tail = np.full((per, self.d - 2), 0.5) if self.d > 2 else np.empty((per, 0))
        a = np.column_stack([x1, np.sqrt(x1), tail])             # branch a: x2 = sqrt(x1)
        b = np.column_stack([x1, np.sqrt(x1) + 1.0, tail])       # branch b: x2 = 1+sqrt(x1)
        return np.vstack([a, b])

    def pareto_front(self, n=1000):
        f1 = np.linspace(0.0, 1.0, n)
        return np.column_stack([f1, 1.0 - np.sqrt(f1)])

    def clip(self, X):
        return np.clip(X, self.xl, self.xu)


class ScalableDMP:
    """Scalable distance-minimization MMOP (a second, structurally different family).

    A distance-minimization problem in R^d with two equivalent global Pareto sets.
    Two well-separated groups sit at centres c1=(-c,0,..), c2=(+c,0,..); each group
    g has a target pair A_g = c_g+(0,r,0,..), B_g = c_g-(0,r,0,..). A point is
    assigned to its nearest centre g*, and the objectives are the distances to that
    group's targets:
        f1(x) = ||x - A_{g*}||,   f2(x) = ||x - B_{g*}||.
    The Pareto set of two-point distance minimisation is the segment between the two
    targets, so the global PS is the union of TWO equivalent segments (x1=-c and
    x1=+c, x2 in [-r,r], x_3..x_d = 0); both map to the linear front f1+f2 = 2r.
    Distance minimisation is a standard MMOP problem class~\\cite{tanabe2020review};
    here it is cast as a scalable, analytically verifiable instance. The nuisance
    dimensions x_3..x_d (optimum 0) scale the decision dimension exactly as in
    ScalableMMF2, but the landscape (piecewise distance, linear PF) is different.
    """
    n_obj = 2
    n_ps_branches = 2

    def __init__(self, d: int, c: float = 5.0, r: float = 1.0):
        if d < 2:
            raise ValueError("d must be >= 2")
        self.d = int(d); self.c = float(c); self.r = float(r)
        self.n_var = self.d
        self.name = f"ScalDMP_d{self.d}"
        self.xl = np.array([-2.0 * c] + [-3.0] * (self.d - 1), float)
        self.xu = np.array([2.0 * c] + [3.0] * (self.d - 1), float)
        # group centres and targets in R^d
        self._C = np.zeros((2, self.d)); self._C[0, 0] = -c; self._C[1, 0] = c
        off = np.zeros(self.d); off[1] = r
        self._A = self._C + off          # (2,d)
        self._B = self._C - off

    def _F(self, X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, float))
        g = (np.abs(X[:, 0] - (-self.c)) > np.abs(X[:, 0] - self.c)).astype(int)  # nearest centre by x1
        A = self._A[g]; B = self._B[g]
        f1 = np.linalg.norm(X - A, axis=1)
        f2 = np.linalg.norm(X - B, axis=1)
        return np.column_stack([f1, f2])

    def evaluate(self, X):
        X = np.atleast_2d(np.asarray(X, float))
        return {"F": self._F(X), "CV": np.zeros(X.shape[0])}

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        t = np.linspace(-self.r, self.r, per)                 # along x2
        tail = np.zeros((per, self.d - 2)) if self.d > 2 else np.empty((per, 0))
        a = np.column_stack([np.full(per, -self.c), t, tail])  # branch at x1=-c
        b = np.column_stack([np.full(per, self.c), t, tail])   # branch at x1=+c
        return np.vstack([a, b])

    def pareto_front(self, n=1000):
        f1 = np.linspace(0.0, 2.0 * self.r, n)
        return np.column_stack([f1, 2.0 * self.r - f1])        # linear front f1+f2=2r

    def clip(self, X):
        return np.clip(X, self.xl, self.xu)


def make(d: int) -> ScalableMMF2:
    return ScalableMMF2(d)


def make_dmp(d: int) -> ScalableDMP:
    return ScalableDMP(d)


# Dimensions used in the high-dimensional study.
DIMS = (5, 10, 30, 50, 100)
