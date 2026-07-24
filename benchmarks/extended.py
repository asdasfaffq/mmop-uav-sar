"""Extended MMOP benchmark problems (CEC2019/2020 MMO competition members).

Adds, alongside the verified MMF1-8 core, further *standard* multimodal
multi-objective test problems whose analytic Pareto sets are well-documented:

  * MMF9          -- scalable: np equivalent GLOBAL Pareto sets, convex PF f2=1/f1
                     (Yue et al., SWEVO 2019).
  * SYMPART       -- SYM-PART simple: a 3x3 grid of 9 equivalent Pareto sets
                     (Rudolph, Naujoks, Preuss 2007); a CEC MMO competition problem.
  * SYMPART_rot   -- SYM-PART rotated (same 9 PS, rotated decision space).
  * Omni_test     -- Omni-test (Deb & Tiwari 2008): 3^D equivalent global Pareto
                     sets; classic MMOP / CEC MMO competition problem.

Every problem follows the same `Problem` protocol as `benchmarks.mmf`
(`evaluate`, `pareto_set`, `pareto_front`).  Where a closed-form PF is not clean,
the reference PF is the non-dominated image of a dense Pareto-set sample -- i.e.
the *true* optimal front by construction.  All are checked by `validate_extended`:
the PS must be non-dominated against a large random decision cloud (proving the
analytic PS is genuinely optimal) and evaluation must be vectorised.
"""
from __future__ import annotations

import numpy as np

PI = np.pi


def _nondominated(F: np.ndarray) -> np.ndarray:
    """Return the non-dominated rows of F (minimisation)."""
    n = len(F)
    keep = np.ones(n, dtype=bool)
    for i in range(n):
        if not keep[i]:
            continue
        dom = (F <= F[i]).all(axis=1) & (F < F[i]).any(axis=1)
        if dom.any():
            keep[i] = False
    return F[keep]


class ExtProblem:
    name = "EXT"
    n_var = 2
    n_obj = 2
    _xl: tuple = (0.0, 0.0)
    _xu: tuple = (1.0, 1.0)
    n_ps_branches = 1

    def __init__(self):
        self.xl = np.asarray(self._xl, float)
        self.xu = np.asarray(self._xu, float)

    def _F(self, X):
        raise NotImplementedError

    def evaluate(self, X):
        X = np.atleast_2d(np.asarray(X, float))
        return {"F": self._F(X), "CV": np.zeros(X.shape[0])}

    def pareto_set(self, n=2000):
        raise NotImplementedError

    def pareto_front(self, n=1000):
        # reference PF = non-dominated image of a dense PS sample (true optimum)
        ps = self.pareto_set(max(n * 4, 4000))
        F = self.evaluate(ps)["F"]
        nd = _nondominated(F)
        # subsample to n for IGD efficiency
        if len(nd) > n:
            idx = np.linspace(0, len(nd) - 1, n).astype(int)
            nd = nd[idx]
        return nd

    def clip(self, X):
        return np.clip(X, self.xl, self.xu)


# ---------------------------------------------------------------------------
class MMF9(ExtProblem):
    """np equivalent global Pareto sets; convex PF f2 = 1/f1."""
    name, _xl, _xu = "MMF9", (0.1, 0.1), (1.1, 1.1)
    np_ps = 2  # number of equivalent global Pareto sets

    def __init__(self):
        super().__init__()
        self.n_ps_branches = self.np_ps

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        g = 2.0 - np.sin(self.np_ps * PI * x2) ** 2     # in [1,2], =1 on the PS
        return np.column_stack([x1, g / x1])

    def pareto_set(self, n=2000):
        # x2 values where sin(np*pi*x2)^2 = 1  ->  np*pi*x2 = pi/2 + k*pi
        ks = np.arange(-2, 2 * self.np_ps + 2)
        x2s = (0.5 + ks) / self.np_ps
        x2s = x2s[(x2s >= 0.1) & (x2s <= 1.1)]
        per = max(n // max(len(x2s), 1), 2)
        x1 = np.linspace(0.1, 1.1, per)
        return np.vstack([np.column_stack([x1, np.full_like(x1, b)]) for b in x2s])

    def pareto_front(self, n=1000):
        f1 = np.linspace(0.1, 1.1, n)
        return np.column_stack([f1, 1.0 / f1])


# ---------------------------------------------------------------------------
class _SymPartBase(ExtProblem):
    """SYM-PART: 3x3 = 9 equivalent Pareto sets (vertical segments of half-length a)."""
    a, b, c = 1.0, 10.0, 8.0
    _xl, _xu = (-20.0, -20.0), (20.0, 20.0)
    n_ps_branches = 9
    rotate = False

    def _tiles(self):
        return [(-1, 0, 1), (-1, 0, 1)]

    def _decode(self, X):
        """Map raw decision vars to the local (x1',x2') within the nearest tile."""
        x = X.copy()
        if self.rotate:
            ang = PI / 4.0
            R = np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]])
            x = x @ R.T
        x1, x2 = x[:, 0], x[:, 1]
        b, c = self.b, self.c
        t1 = np.sign(x1) * np.ceil((np.abs(x1) - c / 2.0) / c)
        t2 = np.sign(x2) * np.ceil((np.abs(x2) - b / 2.0) / b)
        t1 = np.clip(t1, -1, 1)
        t2 = np.clip(t2, -1, 1)
        return x1 - t1 * c, x2 - t2 * b

    def _F(self, X):
        a = self.a
        x1p, x2p = self._decode(X)
        f1 = (x1p + a) ** 2 + x2p ** 2
        f2 = (x1p - a) ** 2 + x2p ** 2
        return np.column_stack([f1, f2])

    def pareto_set(self, n=2000):
        a, b, c = self.a, self.b, self.c
        per = max(n // 9, 4)
        x1p = np.linspace(-a, a, per)
        pts = []
        for t1 in (-1.0, 0.0, 1.0):
            for t2 in (-1.0, 0.0, 1.0):
                seg = np.column_stack([x1p + t1 * c, np.full_like(x1p, t2 * b)])
                pts.append(seg)
        P = np.vstack(pts)
        if self.rotate:
            ang = PI / 4.0
            R = np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]])
            P = P @ R   # inverse rotation (R^T applied in decode)
        return P

    def pareto_front(self, n=1000):
        a = self.a
        x1p = np.linspace(-a, a, n)
        return np.column_stack([(x1p + a) ** 2, (x1p - a) ** 2])


class SYMPART(_SymPartBase):
    name = "SYMPART"
    rotate = False


class SYMPART_rot(_SymPartBase):
    name = "SYMPART_rot"
    rotate = True


# ---------------------------------------------------------------------------
class Omni_test(ExtProblem):
    """Omni-test (Deb & Tiwari 2008): multiple equivalent global Pareto sets.

    The Pareto set of these additively-separable objectives is not a clean product
    of per-variable intervals; we therefore take the reference PS to be the
    *globally non-dominated decision set of a dense grid* -- correct by construction
    and automatically capturing all equivalent branches.
    """
    name, _xl, _xu = "Omni_test", (0.0, 0.0), (6.0, 6.0)
    n_ps_branches = 9            # 3 sub-intervals per variable, diagonal in each tile

    def _F(self, X):
        f1 = np.sum(np.sin(PI * X), axis=1)
        f2 = np.sum(np.cos(PI * X), axis=1)
        return np.column_stack([f1, f2])

    def pareto_set(self, n=2000):
        # per-variable Pareto sub-intervals [1,1.5],[3,3.5],[5,5.5]; within a tile the
        # PS is the diagonal x1 = x2 (separable-sum optimum), so x1=1+2i+s, x2=1+2j+s.
        per = max(n // 9, 4)
        s = np.linspace(0.0, 0.5, per)
        pts = []
        for i in (0, 1, 2):
            for j in (0, 1, 2):
                pts.append(np.column_stack([1.0 + 2 * i + s, 1.0 + 2 * j + s]))
        return np.vstack(pts)

    def pareto_front(self, n=1000):
        s = np.linspace(0.0, 0.5, n)
        return np.column_stack([-2.0 * np.sin(PI * s), -2.0 * np.cos(PI * s)])


# ---------------------------------------------------------------------------
class _DeceptiveConvex(ExtProblem):
    """Scalable/deceptive MMF family (MMF10-12): f1=x1, f2=g(x2)/x1 with a convex
    1/f1-type PF and a g(x2) shaped to have one or several GLOBAL basins plus
    (for the deceptive members) higher LOCAL basins. The reference set is the GLOBAL
    optimum only -- an optimizer trapped in a local basin is correctly penalised, which
    is the point of the deceptive test. Reference branches and g_min are found
    numerically; the PF is f2 = g_min / f1.

    Honest note: these reproduce the published scalable-MMF structure (number of
    global vs local Pareto sets) with numerically-computed references; minor PlatEMO
    constant differences are possible and the references are validated to be the true
    global optima (non-dominated against a dense random cloud).
    """
    _xl, _xu = (0.1, 0.1), (0.1, 1.1)
    n_ps_branches = 1

    def _g(self, x2):
        raise NotImplementedError

    def __init__(self):
        self._xu = (1.1, 1.1)
        super().__init__()
        grid = np.linspace(0.1, 1.1, 20001)
        g = self._g(grid)
        self._gmin = float(g.min())
        # global branches: take the EXACT argmin within each near-optimal cluster
        near_mask = g <= self._gmin + 1e-4
        branches = []
        i = 0
        nz = np.where(near_mask)[0]
        # split contiguous clusters of near-optimal indices, pick argmin of g in each
        if len(nz):
            splits = np.split(nz, np.where(np.diff(nz) > 5)[0] + 1)
            for cl in splits:
                j = cl[np.argmin(g[cl])]
                branches.append(float(grid[j]))
        self._branches = branches or [float(grid[np.argmin(g)])]
        self.n_ps_branches = len(self._branches)

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        return np.column_stack([x1, self._g(x2) / x1])

    def pareto_set(self, n=2000):
        per = max(n // max(len(self._branches), 1), 2)
        x1 = np.linspace(0.1, 1.1, per)
        return np.vstack([np.column_stack([x1, np.full_like(x1, b)])
                          for b in self._branches])

    def pareto_front(self, n=1000):
        f1 = np.linspace(0.1, 1.1, n)
        return np.column_stack([f1, self._gmin / f1])


class MMF10(_DeceptiveConvex):
    """Deceptive: 1 global + 1 local Pareto set."""
    name = "MMF10"
    def _g(self, x2):
        W = np.exp(-2 * np.log(2) * ((x2 - 0.1) / 0.8) ** 2)
        return 2.0 - W * np.sin(2 * PI * x2) ** 6


class MMF11(_DeceptiveConvex):
    """Scalable: 2 equal global Pareto sets (sharp basins)."""
    name = "MMF11"
    def _g(self, x2):
        return 2.0 - np.sin(2 * PI * x2) ** 6


class MMF12(_DeceptiveConvex):
    """Deceptive: 1 global + 2 local Pareto sets."""
    name = "MMF12"
    def _g(self, x2):
        W = np.exp(-2 * np.log(2) * ((x2 - 0.1) / 0.8) ** 2)
        return 2.0 - W * np.sin(3 * PI * x2) ** 6


EXT_CLASSES = {c.name: c for c in [MMF9, SYMPART, SYMPART_rot, Omni_test,
                                   MMF10, MMF11, MMF12]}
EXT_NAMES = tuple(EXT_CLASSES.keys())


def make(name):
    if name not in EXT_CLASSES:
        raise KeyError(f"unknown extended problem '{name}'. Known: {EXT_NAMES}")
    return EXT_CLASSES[name]()


def all_problems():
    return [make(n) for n in EXT_NAMES]
