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


# --------------------------------------------------------------------------
# Transferability probe: the within-front sparsity term as a portable add-on
# --------------------------------------------------------------------------
def decision_sparsity(X, k: int = 3):
    """Normalised decision-space kNN sparsity S in [0, 1] (1 = sparsest).

    Identical definition to the one used inside `algorithms.selection.hybrid_diversity`
    so the term transferred onto a foreign backbone is *the same signal*, not a
    re-derived approximation.
    """
    X = np.asarray(X, float)
    n = len(X)
    if n <= 2:
        return np.zeros(n)
    lo = X.min(0); span = X.max(0) - lo; span[span < 1e-12] = 1.0
    Xn = (X - lo) / span
    D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    kk = min(k, n - 1)
    knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)
    smin, smax = knn.min(), knn.max()
    return (knn - smin) / (smax - smin) if smax > smin else np.zeros(n)


def with_within_front_sparsity(div_fn, beta: float = 0.5, k: int = 3):
    """Wrap a backbone's diversity function with the within-front sparsity bonus.

    Returns ``div_fn(F, X) * (1 + beta * S)``, i.e. the sparsity signal acts only
    *inside* an already-formed front (the backbone's dominance sort is untouched),
    exactly as in EARS-MMOEA's hybrid key. Infinite (boundary) diversity values are
    preserved so the backbone's boundary-retention behaviour is unchanged.

    This is the transferability probe: if the *placement* of the signal -- not the
    surrounding framework -- is what carries the effect, wrapping a foreign backbone
    should reproduce the benefit.
    """
    def wrapped(F, X):
        base = np.asarray(div_fn(F, X), float)
        n = len(X)
        if n <= 2:
            return base
        sp = decision_sparsity(X, k)
        out = base.copy()
        finite = np.isfinite(base)
        out[finite] = base[finite] * (1.0 + beta * sp[finite])
        return out

    wrapped.__name__ = f"wf_sparsity[{getattr(div_fn, '__name__', 'div')}]"
    return wrapped


def insort_environmental(X, F, CV, n_select, beta: float = 0.5, k: int = 3):
    """In-sort counterfactual for the transferability probe.

    Mirrors `algorithms.selection`'s `in_sort_pure_s` exactly: the SAME sparsity
    signal S is fused with a continuous convergence scalar into a single global key
    ``score = -conv + beta * S``, which then decides survival ACROSS front
    boundaries (the dominance sort no longer has precedence). Holding the signal and
    the backbone fixed and moving S from within-front to in-sort isolates the effect
    of PLACEMENT alone -- now on a foreign backbone rather than inside EARS.
    """
    X = np.asarray(X, float); F = np.asarray(F, float)
    CV = np.zeros(len(X)) if CV is None else np.asarray(CV, float)
    n_select = min(int(n_select), len(X))
    feasible = CV <= 0
    if not feasible.any():
        return np.argsort(CV)[:n_select]      # least-violating, as in EARS's variant
    score = np.full(len(X), -np.inf)
    fidx = np.where(feasible)[0]
    Ff = F[fidx]
    lo = Ff.min(0); span = Ff.max(0) - lo; span[span < 1e-12] = 1.0
    Fn = (Ff - lo) / span
    conv = np.linalg.norm(Fn - Fn.min(0), axis=1)
    conv = conv / conv.max() if conv.max() > 0 else conv          # 0..1
    sp = decision_sparsity(X[fidx], k) if len(fidx) > 2 else np.ones(len(fidx))
    score[fidx] = -conv + beta * sp
    return np.argsort(-score)[:n_select]


def resolve_div_fn(base_div, params):
    """Return the backbone's own diversity function, or the within-front-sparsity
    wrapped version when the transferability probe is switched on.

    Off by default, so every previously reported baseline result is bit-for-bit
    unaffected.
    """
    p = params or {}
    if not p.get("wf_sparsity", False):
        return base_div
    return with_within_front_sparsity(base_div, beta=float(p.get("wf_beta", 0.5)),
                                      k=int(p.get("wf_k", 3)))
