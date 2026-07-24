"""Module 7 -- Environmental Selection.

Selects the next population of size N from the combined parent+offspring pool by:
  1. constraint-aware non-dominated sorting (objective convergence + feasibility);
  2. filling fronts whole while they fit;
  3. on the splitting front, keeping the individuals with the highest
     equivalence-aware diversity (objective + decision crowding via SCD, boosted
     by niche rarity) -- this is what preserves multiple Pareto-equivalent sets.

`use_equivalence=False` reduces step 3 to plain objective crowding (ablation A3);
`mode_labels=None` disables the niche-rarity boost (ablation A4).
"""
from __future__ import annotations

import numpy as np

from algorithms.equivalence_fitness import (equivalence_diversity,
                                            fast_nondominated_sort)


def _norm(A):
    lo = A.min(0); rng = A.max(0) - lo; rng[rng < 1e-12] = 1.0
    return (A - lo) / rng


def penalized_decision_density(F, X, mode_labels=None, niche_boost=0.5,
                               k=3, lam=2.0):
    """Phase-8 diversity key: convergence-penalised decision-space sparsity.

    For each solution: key = (decision-space kNN distance; larger = sparser = keep)
    / (1 + lam * convergence), so poorly-converged solutions are demoted while
    decision-diverse, well-converged ones are kept -- the mechanism by which CPDEA
    wins IGDX. A niche-rarity boost (rare modes scored higher) is layered on top.
    Maximise this key (keep the highest).
    """
    n = len(X)
    if n <= 2:
        return np.full(n, np.inf)
    Xn = _norm(np.asarray(X, float)); Fn = _norm(np.asarray(F, float))
    conv = np.linalg.norm(Fn - Fn.min(0), axis=1)
    D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    kk = min(k, n - 1)
    knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)       # decision sparsity (keep large)
    key = knn / (1.0 + lam * conv)                     # penalise poor convergence
    if mode_labels is not None:
        labels = np.asarray(mode_labels)
        uniq, counts = np.unique(labels[labels >= 0], return_counts=True)
        if counts.size:
            occ = dict(zip(uniq.tolist(), counts.tolist())); mx = counts.max()
            rarity = np.array([1.0 - (occ.get(int(l), mx) - 1) / max(mx, 1) for l in labels])
            key = key * (1.0 + niche_boost * rarity)
    return key


def niche_balanced_truncation(F, X, labels, need, niche_boost=0.5):
    """Keep `need` of the splitting front by ROUND-ROBIN across decision niches.

    Each niche contributes its best-spread members in turn, so no decision mode is
    squeezed out (improves decision-space coverage / IGDX) while, within a niche,
    the most spread (and thus typically well-distributed near the PS) members are
    kept -- convergence is NOT traded away (unlike a global penalised-density key).
    """
    from algorithms.equivalence_fitness import special_crowding_distance
    n = len(F)
    if need >= n:
        return np.arange(n)
    if labels is None:
        div = special_crowding_distance(F, X)
        return np.argsort(-div)[:need]
    labels = np.asarray(labels)
    # order members within each niche by special crowding distance (desc)
    scd = special_crowding_distance(F, X)
    niches = {}
    for lb in np.unique(labels):
        idx = np.where(labels == lb)[0]
        niches[lb] = list(idx[np.argsort(-scd[idx])])
    # round-robin pick
    chosen = []
    order = list(niches.keys())
    while len(chosen) < need:
        progressed = False
        for lb in order:
            if niches[lb]:
                chosen.append(niches[lb].pop(0))
                progressed = True
                if len(chosen) >= need:
                    break
        if not progressed:
            break
    return np.asarray(chosen, dtype=int)


def niche_protected_truncation(F, X, labels, need, niche_boost=0.5):
    """Anti-extinction hybrid: first guarantee each decision niche keeps its single
    best member (by special crowding distance) so no Pareto-equivalent mode is wiped
    out, THEN fill the remaining slots by the validated equivalence diversity.

    This is a *minimal* change over the equivalence selection -- it only protects
    modes that would otherwise go extinct -- so it cannot regress on problems where
    equivalence already preserves all modes, while improving decision-space coverage
    where a mode would be squeezed out. Convergence is untouched (members are ranked
    by crowding within the same non-dominated front)."""
    from algorithms.equivalence_fitness import (equivalence_diversity,
                                                special_crowding_distance)
    n = len(F)
    if need >= n:
        return np.arange(n)
    if labels is None:
        div = equivalence_diversity(F, X, None, niche_boost=niche_boost)
        return np.argsort(-div)[:need]
    labels = np.asarray(labels)
    scd = special_crowding_distance(F, X)
    uniq = np.unique(labels)
    protected = []
    for lb in uniq:
        idx = np.where(labels == lb)[0]
        protected.append(idx[int(np.argmax(scd[idx]))])
    protected = list(dict.fromkeys(protected))[:need]   # 1 best per niche
    chosen = set(protected)
    if len(chosen) < need:
        div = equivalence_diversity(F, X, labels, niche_boost=niche_boost)
        order = np.argsort(-div)
        for i in order:
            if len(chosen) >= need:
                break
            chosen.add(int(i))
    return np.asarray(sorted(chosen), dtype=int)[:need]


def hybrid_diversity(F, X, mode_labels=None, niche_boost=0.5, beta=1.0, k=3):
    """Equivalence diversity MULTIPLIED by a decision-space sparsity bonus.

    key = equivalence_diversity(SCD + niche rarity) * (1 + beta * normalised kNN
    decision-space distance). Because the bonus is multiplicative on top of the
    validated equivalence key, it preserves the equivalence selection's behaviour
    (so it should not regress problems where equivalence already covers the PS) while
    *adding* preference for decision-space-sparse solutions (which improves coverage
    on hard, close-mode problems). Boundary/infinite SCD values are preserved.
    """
    from algorithms.equivalence_fitness import equivalence_diversity
    base = equivalence_diversity(F, X, mode_labels, use_equivalence=True,
                                 niche_boost=niche_boost)
    n = len(X)
    if n <= 2:
        return base
    Xn = _norm(np.asarray(X, float))
    D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    kk = min(k, n - 1)
    knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)
    lo, hi = knn.min(), knn.max()
    sp = (knn - lo) / (hi - lo) if hi > lo else np.zeros(n)   # 0..1, sparse=1
    out = base.copy()
    finite = np.isfinite(base)
    out[finite] = base[finite] * (1.0 + beta * sp[finite])
    return out


def hybrid_additive_diversity(F, X, mode_labels=None, niche_boost=0.5, beta=1.0, k=3):
    """Controlled counterfactual to `hybrid_diversity`: the SAME equivalence key E and
    the SAME decision-space sparsity S, but combined ADDITIVELY (E + beta*median(E)*S)
    instead of multiplicatively (E*(1+beta*S)). The median(E) scale makes the additive
    bonus magnitude-comparable to the multiplicative one. Used to isolate whether the
    *multiplicative within-front form* itself (vs additive fusion of the same signals)
    carries any unique benefit. Boundary/infinite values are preserved.
    """
    from algorithms.equivalence_fitness import equivalence_diversity
    base = equivalence_diversity(F, X, mode_labels, use_equivalence=True,
                                 niche_boost=niche_boost)
    n = len(X)
    if n <= 2:
        return base
    Xn = _norm(np.asarray(X, float))
    D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    kk = min(k, n - 1)
    knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)
    lo, hi = knn.min(), knn.max()
    sp = (knn - lo) / (hi - lo) if hi > lo else np.zeros(n)
    out = base.copy()
    finite = np.isfinite(base)
    scale = np.median(base[finite]) if finite.any() else 1.0
    out[finite] = base[finite] + beta * scale * sp[finite]
    return out


def environmental_selection(X, F, CV, n_select, *, mode_labels=None,
                            use_equivalence=True, niche_boost=0.5,
                            selection_mode="equivalence", penalty_lambda=2.0,
                            hybrid_beta=1.0, X_dec=None):
    """Front-based selection; the splitting-front diversity key is either the
    original equivalence diversity (`selection_mode='equivalence'`) or the
    Phase-8 convergence-penalised decision density (`'penalized_density'`).

    `X_dec` is the DECISION REPRESENTATION used for all decision-space diversity
    (crowding / sparsity). It defaults to X, but the UAV application passes a
    topology-aware feature map so diversity tracks route-family structure."""
    X = np.asarray(X, dtype=float); F = np.asarray(F, dtype=float)
    Xd = X if X_dec is None else np.asarray(X_dec, dtype=float)
    CV = np.zeros(len(X)) if CV is None else np.asarray(CV, dtype=float)
    n_select = min(int(n_select), len(X))

    fronts = fast_nondominated_sort(F, CV)

    if selection_mode == "in_sort_density":
        # GENUINE in-sort placement: the SAME convergence-penalised decision-density
        # key as the within-front `penalized_density` variant, but applied GLOBALLY
        # over the whole pool rather than only to the splitting front. The key then
        # decides survival ACROSS front boundaries, so a decision-diverse but
        # less-converged solution can displace a converged one (front precedence is
        # not preserved). Holding the key fixed and moving it from within-front to
        # in-sort isolates the effect of PLACEMENT alone.
        feasible = CV <= 0
        if feasible.any():
            div = np.full(len(X), -np.inf)
            fidx = np.where(feasible)[0]
            lbl = None if mode_labels is None else np.asarray(mode_labels)[fidx]
            div[fidx] = penalized_decision_density(F[fidx], Xd[fidx], lbl,
                                                   niche_boost=niche_boost, lam=penalty_lambda)
        else:
            div = -CV
        return np.argsort(-div)[:n_select]

    if selection_mode == "in_sort_pure_s":
        # GENUINE in-sort placement of the PURE sparsity signal S (the same kNN
        # decision-space sparsity used by the within-front hybrid key), fused with
        # a continuous convergence scalar so S competes with convergence ACROSS
        # front boundaries: score = -conv + beta * S (higher = keep). A
        # decision-sparse but less-converged solution can now displace a converged
        # one. This is the most direct test of "keep S out of the dominance sort".
        feasible = CV <= 0
        score = np.full(len(X), -np.inf)
        if feasible.any():
            fidx = np.where(feasible)[0]
            Fn = _norm(F[fidx])
            conv = np.linalg.norm(Fn - Fn.min(0), axis=1)
            conv = conv / conv.max() if conv.max() > 0 else conv      # 0..1
            n = len(fidx)
            if n > 2:
                Xn = _norm(Xd[fidx])
                D = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=2)
                np.fill_diagonal(D, np.inf)
                kk = min(3, n - 1)
                knn = np.sort(D, axis=1)[:, :kk].sum(axis=1)
                lo, hi = knn.min(), knn.max()
                sp = (knn - lo) / (hi - lo) if hi > lo else np.zeros(n)
            else:
                sp = np.ones(n)
            score[fidx] = -conv + hybrid_beta * sp
        else:
            score = -CV
        return np.argsort(-score)[:n_select]

    chosen: list[int] = []
    for fr in fronts:
        if len(chosen) + len(fr) <= n_select:
            chosen.extend(fr.tolist())
            continue
        need = n_select - len(chosen)
        lbl = None if mode_labels is None else np.asarray(mode_labels)[fr]
        if use_equivalence and selection_mode == "hybrid":
            div = hybrid_diversity(F[fr], Xd[fr], lbl, niche_boost=niche_boost,
                                   beta=hybrid_beta)
            keep = fr[np.argsort(-div)[:need]]
        elif use_equivalence and selection_mode == "hybrid_additive":
            div = hybrid_additive_diversity(F[fr], Xd[fr], lbl, niche_boost=niche_boost,
                                            beta=hybrid_beta)
            keep = fr[np.argsort(-div)[:need]]
        elif use_equivalence and selection_mode == "niche_protected":
            sub = niche_protected_truncation(F[fr], Xd[fr], lbl, need,
                                             niche_boost=niche_boost)
            keep = fr[sub]
        elif use_equivalence and selection_mode == "niche_balanced":
            sub = niche_balanced_truncation(F[fr], Xd[fr], lbl, need,
                                            niche_boost=niche_boost)
            keep = fr[sub]
        elif use_equivalence and selection_mode == "penalized_density":
            div = penalized_decision_density(F[fr], Xd[fr], lbl,
                                             niche_boost=niche_boost, lam=penalty_lambda)
            keep = fr[np.argsort(-div)[:need]]
        else:
            div = equivalence_diversity(F[fr], Xd[fr], lbl,
                                        use_equivalence=use_equivalence,
                                        niche_boost=niche_boost)
            keep = fr[np.argsort(-div)[:need]]
        chosen.extend(keep.tolist())
        break
    idx = np.asarray(chosen, dtype=int)
    return idx
