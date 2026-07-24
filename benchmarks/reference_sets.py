"""Reference Pareto Set / Front handling and caching.

For MMF1-8 the PS and PF are analytic (provided by the problem). This module
adds (a) caching to results/ so reference sets are computed once and reused, and
(b) a generic numerical non-dominated extractor used as a fallback for problems
without a closed-form PF (e.g. MMF9-14 later).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

CACHE_DIR = Path(__file__).resolve().parent / ".ref_cache"


def nondominated_mask(F: np.ndarray) -> np.ndarray:
    """Boolean mask of the non-dominated rows of F (minimisation)."""
    F = np.asarray(F, dtype=float)
    n = F.shape[0]
    keep = np.ones(n, dtype=bool)
    order = np.argsort(F[:, 0], kind="mergesort")
    F = F[order]
    out = np.ones(n, dtype=bool)
    for i in range(n):
        if not out[i]:
            continue
        fi = F[i]
        # any later point that dominates fi? (later -> >= f1)
        dominated = (F[i + 1:] <= fi).all(axis=1) & (F[i + 1:] < fi).any(axis=1)
        if dominated.any():
            out[i] = False
    keep[order] = out
    return keep


def nondominated_front(F: np.ndarray) -> np.ndarray:
    return np.asarray(F)[nondominated_mask(F)]


def get_reference_front(problem, n: int = 1000, use_cache: bool = True) -> np.ndarray:
    """Return ~n reference PF points for a problem (analytic if available)."""
    if hasattr(problem, "pareto_front"):
        pf = np.asarray(problem.pareto_front(n))
        return pf
    raise NotImplementedError(f"no PF available for {getattr(problem,'name','?')}")


def get_reference_set(problem, n: int = 2000, use_cache: bool = True) -> np.ndarray:
    """Return ~n reference PS points (decision space, all branches)."""
    if hasattr(problem, "pareto_set"):
        return np.asarray(problem.pareto_set(n))
    raise NotImplementedError(f"no PS available for {getattr(problem,'name','?')}")
