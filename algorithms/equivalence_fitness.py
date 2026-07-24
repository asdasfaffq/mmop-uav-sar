"""Module 1 -- Dual-Space Equivalence-Aware Fitness.

Core idea of MMOP: many decision-space solutions map to the same (or near-equal)
Pareto front. Standard MOEAs only reward objective-space spread and therefore
collapse all solutions onto one Pareto set. EARS-MMOEA instead scores every
individual in BOTH spaces and rewards *equivalence diversity*: solutions that are
objective-good AND decision-space-novel relative to existing modes.

This module also hosts the low-level Pareto primitives (constraint-aware
non-dominated sorting, crowding distances) used across the algorithm.

The composite selection key per individual is:
    (rank,  -equivalence_diversity)
where lower rank is better and higher diversity is better. `equivalence_diversity`
fuses:
  * objective-space crowding (spread on the front),
  * decision-space crowding (spread of equivalent solutions),
  * Special Crowding Distance (SCD, Yue et al. 2018) combining the two,
  * niche rarity (modes with fewer members are boosted) -- the equivalence-aware term.
Setting `use_equivalence=False` reduces it to plain objective crowding (ablation A3).
"""
from __future__ import annotations

import numpy as np


# --------------------------------------------------------------------------
# Pareto primitives (constraint-aware)
# --------------------------------------------------------------------------
def constrained_dominates(fi, cvi, fj, cvj) -> bool:
    """Deb's constraint-domination: feasible beats infeasible; among feasible
    use Pareto dominance; among infeasible smaller CV wins."""
    if cvi <= 0 and cvj > 0:
        return True
    if cvi > 0 and cvj <= 0:
        return False
    if cvi > 0 and cvj > 0:
        return cvi < cvj
    # both feasible -> Pareto
    return np.all(fi <= fj) and np.any(fi < fj)


def domination_matrix(F: np.ndarray, CV: np.ndarray | None = None) -> np.ndarray:
    """Boolean (n,n) matrix: D[i,j] == True iff i constraint-dominates j.

    Vectorised Deb constraint-domination (feasible > infeasible; among feasible
    Pareto; among infeasible smaller CV wins).
    """
    F = np.asarray(F, dtype=float)
    n = F.shape[0]
    if CV is None:
        CV = np.zeros(n)
    CV = np.asarray(CV, dtype=float)

    le = (F[:, None, :] <= F[None, :, :]).all(axis=2)
    lt = (F[:, None, :] < F[None, :, :]).any(axis=2)
    pareto = le & lt
    feas = CV <= 0
    both_feas = feas[:, None] & feas[None, :]
    i_feas_j_inf = feas[:, None] & (~feas[None, :])
    both_inf = (~feas[:, None]) & (~feas[None, :])
    cv_less = CV[:, None] < CV[None, :]
    D = (both_feas & pareto) | i_feas_j_inf | (both_inf & cv_less)
    np.fill_diagonal(D, False)
    return D


def fast_nondominated_sort(F: np.ndarray, CV: np.ndarray | None = None) -> list[np.ndarray]:
    """Return a list of fronts (each an array of indices), constraint-aware."""
    F = np.asarray(F, dtype=float)
    n = F.shape[0]
    if n == 0:
        return [np.empty(0, dtype=int)]
    D = domination_matrix(F, CV)
    ndom = D.sum(axis=0)                 # how many dominate j
    fronts: list[np.ndarray] = []
    cur = np.where(ndom == 0)[0]
    remaining = ndom.copy()
    while cur.size:
        fronts.append(cur)
        remaining[cur] = -1              # mark assigned
        # decrement domination counts of everything the current front dominates
        dominated_counts = D[cur].sum(axis=0)
        remaining = remaining - dominated_counts
        cur = np.where(remaining == 0)[0]
    return fronts


def _normalize(A: np.ndarray) -> np.ndarray:
    lo = A.min(axis=0)
    rng = A.max(axis=0) - lo
    rng[rng < 1e-12] = 1.0
    return (A - lo) / rng


def crowding_distance(A: np.ndarray) -> np.ndarray:
    """Standard crowding distance over rows of A (objective OR decision space)."""
    A = np.asarray(A, dtype=float)
    n, m = A.shape
    if n <= 2:
        return np.full(n, np.inf)
    An = _normalize(A)
    dist = np.zeros(n)
    for k in range(m):
        order = np.argsort(An[:, k])
        dist[order[0]] = dist[order[-1]] = np.inf
        span = An[order[-1], k] - An[order[0], k]
        if span < 1e-12:
            continue
        dist[order[1:-1]] += (An[order[2:], k] - An[order[:-2], k]) / span
    return dist


def special_crowding_distance(F: np.ndarray, X: np.ndarray) -> np.ndarray:
    """SCD (Yue et al. 2018): per individual combine objective-space and
    decision-space crowding so that being spread out in EITHER space is rewarded.
    """
    cd_f = crowding_distance(F)
    cd_x = crowding_distance(X)
    # infinities (boundary points) -> keep as max priority
    finite_f = cd_f[np.isfinite(cd_f)]
    finite_x = cd_x[np.isfinite(cd_x)]
    mean_f = finite_f.mean() if finite_f.size else 0.0
    mean_x = finite_x.mean() if finite_x.size else 0.0
    scd = np.empty(len(F))
    for i in range(len(F)):
        if cd_f[i] > mean_f or cd_x[i] > mean_x:
            scd[i] = max(cd_f[i], cd_x[i])
        else:
            scd[i] = min(cd_f[i], cd_x[i])
    return scd


# --------------------------------------------------------------------------
# Equivalence-aware diversity (the dual-space fitness term)
# --------------------------------------------------------------------------
def equivalence_diversity(F: np.ndarray, X: np.ndarray,
                          mode_labels: np.ndarray | None = None,
                          use_equivalence: bool = True,
                          niche_boost: float = 0.5) -> np.ndarray:
    """Per-individual diversity score fusing SCD with niche rarity.

    Parameters
    ----------
    mode_labels : decision-space cluster id per individual (from niching), or None.
    use_equivalence : if False, returns plain objective crowding (ablation A3).
    niche_boost : weight of the rarity boost (rarer modes scored higher).
    """
    if not use_equivalence:
        return crowding_distance(F)

    scd = special_crowding_distance(F, X)
    if mode_labels is None:
        return scd

    labels = np.asarray(mode_labels)
    # rarity = inverse occupancy of the individual's mode, normalised to [0,1]
    rarity = np.zeros(len(F))
    uniq, counts = np.unique(labels[labels >= 0], return_counts=True)
    if counts.size:
        occ = dict(zip(uniq.tolist(), counts.tolist()))
        max_c = counts.max()
        for i, lb in enumerate(labels):
            c = occ.get(int(lb), max_c)
            rarity[i] = 1.0 - (c - 1) / max(max_c, 1)
    # boost SCD by rarity; keep boundary infinities dominant
    finite = np.isfinite(scd)
    out = scd.copy()
    out[finite] = scd[finite] * (1.0 + niche_boost * rarity[finite])
    return out


def selection_keys(F, X, CV=None, mode_labels=None, use_equivalence=True,
                   niche_boost=0.5):
    """Return (rank, diversity) arrays for environmental selection.

    Sorting ascending by rank then descending by diversity gives the EARS order.
    """
    fronts = fast_nondominated_sort(F, CV)
    rank = np.empty(len(F), dtype=int)
    for r, fr in enumerate(fronts):
        rank[fr] = r
    div = np.zeros(len(F))
    for fr in fronts:
        if len(fr) == 0:
            continue
        div[fr] = equivalence_diversity(
            F[fr], X[fr],
            None if mode_labels is None else np.asarray(mode_labels)[fr],
            use_equivalence=use_equivalence, niche_boost=niche_boost)
    return rank, div, fronts
