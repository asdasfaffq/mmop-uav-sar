"""MMF multimodal multi-objective test suite (Yue, Qu, Liang et al.).

Objective formulas and analytical Pareto Sets (PS) / Pareto Fronts (PF) for
MMF1-MMF8 are transcribed verbatim from the canonical PlatEMO implementations
(`Problems/.../MMF*.m`, including their analytical `GetOptimum`). These 8
problems all share the property that *on the Pareto set the deviation term y is
exactly 0*, so the PF reduces to a clean closed form (`_pf_f2`) -- which we use
both to generate reference fronts and to self-validate (`benchmark_validation.py`).

Each problem:
* is bi-objective (minimisation), unconstrained (CV == 0);
* exposes `evaluate(X) -> {'F', 'CV'}` (vectorised, the `Problem` protocol);
* exposes `pareto_set(n)` -- reference PS across ALL equivalent decision-space
  branches -- and `pareto_front(n)` -- analytic reference PF.

References
----------
Yue, Qu, Liang, IEEE TEVC 22(5), 2018; Yue et al., Swarm Evol. Comput. 48, 2019.
PlatEMO: Tian et al. (BIMK/PlatEMO).
"""
from __future__ import annotations

import numpy as np

PI = np.pi


class MMFProblem:
    """Base class. Subclasses set name/_xl/_xu/n_ps_branches and implement
    `_F`, `pareto_set`, and `_pf_f2` (analytic PF as f2 = g(f1))."""

    name: str = "MMF"
    n_var: int = 2
    n_obj: int = 2
    _xl: tuple = (0.0, 0.0)
    _xu: tuple = (1.0, 1.0)
    n_ps_branches: int = 1
    _f1_range: tuple = (0.0, 1.0)  # PF support along f1

    def __init__(self):
        self.xl = np.asarray(self._xl, dtype=float)
        self.xu = np.asarray(self._xu, dtype=float)

    # -- objective evaluation -------------------------------------------------
    def _F(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def evaluate(self, X: np.ndarray) -> dict[str, np.ndarray]:
        X = np.atleast_2d(np.asarray(X, dtype=float))
        return {"F": self._F(X), "CV": np.zeros(X.shape[0])}

    # -- reference sets -------------------------------------------------------
    def pareto_set(self, n: int = 2000) -> np.ndarray:
        raise NotImplementedError

    def _pf_f2(self, f1: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def pareto_front(self, n: int = 1000) -> np.ndarray:
        f1 = np.linspace(self._f1_range[0], self._f1_range[1], n)
        return np.column_stack([f1, self._pf_f2(f1)])

    def clip(self, X: np.ndarray) -> np.ndarray:
        return np.clip(X, self.xl, self.xu)


def _grid(lo: float, hi: float, n: int) -> np.ndarray:
    return np.linspace(lo, hi, max(int(n), 2))


# ---------------------------------------------------------------------------
class MMF1(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF1", (1.0, -1.0), (3.0, 1.0), 1

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1 - 2.0)
        f2 = 1.0 - np.sqrt(f1) + 2.0 * (x2 - np.sin(6 * PI * f1 + PI)) ** 2
        return np.column_stack([f1, f2])

    def pareto_set(self, n=2000):
        x1 = _grid(1.0, 3.0, n)
        return np.column_stack([x1, np.sin(6 * PI * np.abs(x1 - 2.0) + PI)])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF2(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF2", (0.0, 0.0), (1.0, 2.0), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        y = np.where(x2 <= 1.0, x2 - np.sqrt(x1), x2 - 1.0 - np.sqrt(x1))
        g = 4.0 * y ** 2 - 2.0 * np.cos(20.0 * y * PI / np.sqrt(2.0)) + 2.0
        return np.column_stack([x1, 1.0 - np.sqrt(x1) + 2.0 * g])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(0.0, 1.0, per)
        a = np.column_stack([x1, np.sqrt(x1)])
        b = np.column_stack([x1, np.sqrt(x1) + 1.0])
        return np.vstack([a, b])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF3(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF3", (0.0, 0.0), (1.0, 1.5), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        temp = (x2 <= 0.5) | ((x2 < 1.0) & (x1 > 0.25))
        y = np.where(temp, x2 - np.sqrt(x1), x2 - 0.5 - np.sqrt(x1))
        g = 4.0 * y ** 2 - 2.0 * np.cos(20.0 * y * PI / np.sqrt(2.0)) + 2.0
        return np.column_stack([x1, 1.0 - np.sqrt(x1) + 2.0 * g])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(0.0, 1.0, per)
        a = np.column_stack([x1, np.sqrt(x1)])
        b = np.column_stack([x1, np.sqrt(x1) + 0.5])
        return np.vstack([a, b])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF4(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF4", (-1.0, 0.0), (1.0, 2.0), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        s = np.sin(PI * np.abs(x1))
        y = np.where(x2 < 1.0, x2 - s, x2 - 1.0 - s)
        return np.column_stack([np.abs(x1), 1.0 - x1 ** 2 + 2.0 * y ** 2])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(-1.0, 1.0, per)
        s = np.sin(PI * np.abs(x1))
        return np.vstack([np.column_stack([x1, s]), np.column_stack([x1, s + 1.0])])

    def _pf_f2(self, f1):
        return 1.0 - f1 ** 2


class MMF5(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF5", (1.0, -1.0), (3.0, 3.0), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        s = np.sin(6 * PI * np.abs(x1 - 2.0) + PI)
        y = np.where(x2 <= 1.0, x2 - s, x2 - 2.0 - s)
        f1 = np.abs(x1 - 2.0)
        return np.column_stack([f1, 1.0 - np.sqrt(f1) + 2.0 * y ** 2])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(1.0, 3.0, per)
        s = np.sin(6 * PI * np.abs(x1 - 2.0) + PI)
        return np.vstack([np.column_stack([x1, s]), np.column_stack([x1, s + 2.0])])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF6(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF6", (1.0, -1.0), (3.0, 2.0), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        band = (
            (x1 <= 7.0 / 6.0)
            | ((8.0 / 6.0 < x1) & (x1 <= 9.0 / 6.0))
            | ((10.0 / 6.0 < x1) & (x1 <= 11.0 / 6.0))
            | ((13.0 / 6.0 < x1) & (x1 <= 14.0 / 6.0))
            | ((15.0 / 6.0 < x1) & (x1 <= 16.0 / 6.0))
            | (17.0 / 6.0 < x1)
        )
        temp = (x2 <= 0.0) | ((x2 <= 1.0) & band)
        s = np.sin(6 * PI * np.abs(x1 - 2.0) + PI)
        y = np.where(temp, x2 - s, x2 - 1.0 - s)
        f1 = np.abs(x1 - 2.0)
        return np.column_stack([f1, 1.0 - np.sqrt(f1) + 2.0 * y ** 2])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(1.0, 3.0, per)
        s = np.sin(6 * PI * np.abs(x1 - 2.0) + PI)
        return np.vstack([np.column_stack([x1, s]), np.column_stack([x1, s + 1.0])])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF7(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF7", (1.0, -1.0), (3.0, 1.0), 1

    @staticmethod
    def _ps_x2(x1):
        f1 = np.abs(x1 - 2.0)
        return (0.3 * f1 ** 2 * np.cos(24 * PI * f1 + 4 * PI) + 0.6 * f1) \
            * np.sin(6 * PI * f1 + PI)

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        f1 = np.abs(x1 - 2.0)
        return np.column_stack([f1, 1.0 - np.sqrt(f1) + (x2 - self._ps_x2(x1)) ** 2])

    def pareto_set(self, n=2000):
        x1 = _grid(1.0, 3.0, n)
        return np.column_stack([x1, self._ps_x2(x1)])

    def _pf_f2(self, f1):
        return 1.0 - np.sqrt(f1)


class MMF8(MMFProblem):
    name, _xl, _xu, n_ps_branches = "MMF8", (-PI, 0.0), (PI, 9.0), 2

    def _F(self, X):
        x1, x2 = X[:, 0], X[:, 1]
        s = np.sin(np.abs(x1)) + np.abs(x1)
        y = np.where(x2 <= 4.0, x2 - s, x2 - 4.0 - s)
        f1 = np.sin(np.abs(x1))
        f2 = np.sqrt(np.maximum(1.0 - f1 ** 2, 0.0)) + 2.0 * y ** 2
        return np.column_stack([f1, f2])

    def pareto_set(self, n=2000):
        per = max(n // 2, 2)
        x1 = _grid(-PI, PI, per)
        s = np.sin(np.abs(x1)) + np.abs(x1)
        return np.vstack([np.column_stack([x1, s]), np.column_stack([x1, s + 4.0])])

    def _pf_f2(self, f1):
        return np.sqrt(np.maximum(1.0 - f1 ** 2, 0.0))


# ---------------------------------------------------------------------------
_MMF_CLASSES = {c.__name__: c for c in
                [MMF1, MMF2, MMF3, MMF4, MMF5, MMF6, MMF7, MMF8]}
MMF_NAMES = tuple(_MMF_CLASSES.keys())


def make(name: str) -> MMFProblem:
    if name not in _MMF_CLASSES:
        raise KeyError(f"unknown MMF problem '{name}'. Known: {MMF_NAMES}")
    return _MMF_CLASSES[name]()


def all_problems() -> list[MMFProblem]:
    return [make(n) for n in MMF_NAMES]
