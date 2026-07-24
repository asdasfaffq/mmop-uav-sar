"""Module 5 -- Constraint-Aware Multimodal Selection support.

On the standard MMF benchmark every solution is feasible (CV == 0), so this is a
pass-through there. For the UAV application it provides:
  * an epsilon-relaxation schedule so near-boundary infeasible solutions survive
    early (they often seed new route families), tightening to feasible-first late;
  * effective-CV transformation used by the constraint-aware non-dominated sort.

`boundary_near_mask` flags slightly-infeasible solutions worth preserving for
their decision-space novelty even after epsilon has tightened.
"""
from __future__ import annotations

import numpy as np


class EpsilonController:
    """Geometric epsilon decay: eps_t = eps_0 * decay**t, used to relax CV."""

    def __init__(self, eps0: float = 0.1, decay: float = 0.95):
        self.eps0 = float(eps0)
        self.decay = float(decay)
        self.t = 0
        self.eps = float(eps0)

    def step(self):
        self.t += 1
        self.eps = self.eps0 * (self.decay ** self.t)
        return self.eps

    def effective_cv(self, CV: np.ndarray) -> np.ndarray:
        """Treat violations below the current epsilon as feasible."""
        CV = np.asarray(CV, dtype=float)
        return np.maximum(0.0, CV - self.eps)


def boundary_near_mask(CV: np.ndarray, band: float = 0.05) -> np.ndarray:
    """Solutions that are infeasible but only slightly (0 < CV <= band)."""
    CV = np.asarray(CV, dtype=float)
    return (CV > 0) & (CV <= band)
