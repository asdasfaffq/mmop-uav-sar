"""Shared scaffolding for baseline MOEAs (kept minimal and faithful).

Provides vectorised SBX + polynomial mutation, binary tournament selection, and a
generic NSGA-II environmental selection parameterised by a *diversity function* --
this is what cleanly separates DN-NSGA-II (decision-space crowding) from
Omni-optimizer (combined crowding) without duplicating the NSGA-II core.

These helpers reuse the project's verified Pareto primitives
(`algorithms.equivalence_fitness`) so all algorithms share identical
non-dominated sorting and crowding semantics.
"""
from __future__ import annotations

import numpy as np

from algorithms.equivalence_fitness import (crowding_distance,
                                            fast_nondominated_sort)


# --------------------------------------------------------------------------
# Variation
# --------------------------------------------------------------------------
def sbx_crossover(P: np.ndarray, rng, eta: float, pc: float, xl, xu) -> np.ndarray:
    """Simulated binary crossover over a mating pool P (returns same-size offspring)."""
    P = P.copy()
    n, d = P.shape
    xl = np.asarray(xl); xu = np.asarray(xu)
    perm = rng.permutation(n)
    Q = P.copy()
    for k in range(0, n - 1, 2):
        i, j = perm[k], perm[k + 1]
        p1, p2 = P[i].copy(), P[j].copy()
        if rng.random() > pc:
            Q[i], Q[j] = p1, p2
            continue
        u = rng.random(d)
        beta = np.where(u <= 0.5, (2 * u) ** (1 / (eta + 1)),
                        (1 / (2 * (1 - u))) ** (1 / (eta + 1)))
        # per-gene swap mask (SBX applies to each var with prob 0.5)
        swap = rng.random(d) <= 0.5
        c1 = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2)
        c2 = 0.5 * ((1 - beta) * p1 + (1 + beta) * p2)
        Q[i] = np.where(swap, c1, p1)
        Q[j] = np.where(swap, c2, p2)
    return np.clip(Q, xl, xu)


def polynomial_mutation(P: np.ndarray, rng, eta: float, pm: float, xl, xu) -> np.ndarray:
    P = P.copy()
    n, d = P.shape
    xl = np.asarray(xl, dtype=float); xu = np.asarray(xu, dtype=float)
    span = xu - xl
    span[span < 1e-12] = 1e-12
    do = rng.random((n, d)) < pm
    u = rng.random((n, d))
    d1 = (P - xl) / span
    d2 = (xu - P) / span
    b1 = np.maximum(2 * u + (1 - 2 * u) * (1 - d1) ** (eta + 1), 0.0)
    b2 = np.maximum(2 * (1 - u) + 2 * (u - 0.5) * (1 - d2) ** (eta + 1), 0.0)
    dq = np.where(u <= 0.5, b1 ** (1 / (eta + 1)) - 1, 1 - b2 ** (1 / (eta + 1)))
    P = np.where(do, P + dq * span, P)
    return np.clip(P, xl, xu)


def de_offspring(P: np.ndarray, rng, F: float, CR: float, xl, xu) -> np.ndarray:
    """DE/rand/1/bin offspring for the whole population."""
    n, d = P.shape
    Q = P.copy()
    for i in range(n):
        idxs = rng.choice([k for k in range(n) if k != i], size=3, replace=False)
        a, b, c = P[idxs]
        mutant = a + F * (b - c)
        mask = rng.random(d) < CR
        mask[rng.integers(d)] = True
        Q[i] = np.where(mask, mutant, P[i])
    return np.clip(Q, np.asarray(xl), np.asarray(xu))


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------
def ranks_and_div(F, X, CV, diversity_fn):
    """Return per-individual (rank, diversity) using the given diversity_fn."""
    fronts = fast_nondominated_sort(F, CV)
    rank = np.empty(len(F), dtype=int)
    div = np.zeros(len(F))
    for r, fr in enumerate(fronts):
        rank[fr] = r
        if len(fr):
            div[fr] = diversity_fn(F[fr], X[fr])
    return rank, div, fronts


def binary_tournament(rank, div, rng, n_out):
    n = len(rank)
    out = np.empty(n_out, dtype=int)
    for k in range(n_out):
        a, b = rng.integers(0, n, size=2)
        if rank[a] < rank[b] or (rank[a] == rank[b] and div[a] > div[b]):
            out[k] = a
        else:
            out[k] = b
    return out


def nsga2_environmental(X, F, CV, n_select, diversity_fn):
    """Generic NSGA-II environmental selection with a pluggable diversity_fn."""
    fronts = fast_nondominated_sort(F, CV)
    chosen: list[int] = []
    for fr in fronts:
        if len(chosen) + len(fr) <= n_select:
            chosen.extend(fr.tolist()); continue
        need = n_select - len(chosen)
        div = diversity_fn(F[fr], X[fr])
        keep = fr[np.argsort(-div)[:need]]
        chosen.extend(keep.tolist())
        break
    return np.asarray(chosen, dtype=int)


# diversity functions ------------------------------------------------------
def div_objective(F, X):
    return crowding_distance(F)


def div_decision(F, X):
    return crowding_distance(X)


def div_omni(F, X):
    """Omni-optimizer style: crowding in BOTH spaces; a point keeps the larger of
    its two crowding values when it is above the mean in either space, else the
    smaller -- rewarding spread in objective OR decision space (Deb & Tiwari 2008)."""
    cf = crowding_distance(F)
    cx = crowding_distance(X)
    mf = cf[np.isfinite(cf)].mean() if np.isfinite(cf).any() else 0.0
    mx = cx[np.isfinite(cx)].mean() if np.isfinite(cx).any() else 0.0
    out = np.where((cf > mf) | (cx > mx), np.maximum(cf, cx), np.minimum(cf, cx))
    return out
