"""Application-level metrics for the multi-UAV SAR MMOP (Phase 10).

The true Pareto front/set are unknown for the real problem, so:
  * objective-space quality uses HV and an IGD-to-combined-front, where the
    reference front is the non-dominated set of ALL algorithms' feasible solutions
    across all runs (standard practice), with a shared ideal/nadir normalisation;
  * decision-space (MMOP) quality is measured by ROUTE-FAMILY diversity: the number
    of topologically-distinct route families and their mean pairwise route distance
    (route_metrics) -- this is the application analogue of IGDX / #modes.

`feasible_ratio` and mean objective values are reported for the application table.
"""
from __future__ import annotations

import numpy as np

from applications import route_metrics as rm
from metrics.indicators import hypervolume
from algorithms.equivalence_fitness import fast_nondominated_sort

DIRECTION = {
    "HV": "max", "IGD_ref": "min", "feasible_ratio": "max",
    "n_route_families": "max", "route_family_diversity": "max",
    "total_distance": "min", "risk_exposure": "min", "makespan": "min",
}


def hungarian_layout_distance(a: np.ndarray, b: np.ndarray, K: int) -> float:
    """Exact permutation-invariant distance between two K-station layouts.

    Each flat layout (length 2K) is reshaped to K points; the distance is the
    minimum-cost assignment (Hungarian) of stations in `a` to stations in `b`,
    averaged over the K matched pairs. This is the rigorous set distance the
    canonical-coordinate sort only approximates (the two agree when stations are
    well separated, and differ when layouts cross). Cost is negligible for K=5.
    """
    from scipy.optimize import linear_sum_assignment
    A = np.asarray(a, float).reshape(K, -1)
    B = np.asarray(b, float).reshape(K, -1)
    C = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    ri, ci = linear_sum_assignment(C)
    return float(C[ri, ci].mean())


def igdx_hungarian(ref_ps: np.ndarray, X_layouts: np.ndarray, K: int) -> float:
    """IGDX using the exact Hungarian set distance instead of sorted-coordinate
    Euclidean: mean over reference-PS layouts of the nearest obtained layout."""
    if ref_ps is None or len(ref_ps) == 0 or len(X_layouts) == 0:
        return float("inf")
    total = 0.0
    for r in ref_ps:
        total += min(hungarian_layout_distance(r, x, K) for x in X_layouts)
    return total / len(ref_ps)


def compute_placement_metrics(prob, X, F, ref_front, ref_ps) -> dict:
    """Metrics for the facility-placement MMOP: objective-space (HV, IGD to combined
    front) + decision-space multimodality (IGDX to combined PS, #modes, layout
    diversity) computed on the non-dominated, canonicalised placements."""
    from algorithms.equivalence_fitness import fast_nondominated_sort
    from algorithms.niching import adaptive_niching
    from metrics.indicators import hypervolume, igd
    if len(X) == 0:
        return {"HV": 0.0, "IGD_ref": np.inf, "IGDX_ref": np.inf,
                "n_modes": 0.0, "placement_diversity": 0.0,
                "mean_access": np.nan, "max_access": np.nan}
    nd = fast_nondominated_sort(F)[0]
    Fnd = F[nd]; Xc = prob.feature_map(X[nd])
    hv = hypervolume(Fnd, ref_front)
    igd_ref = igd(ref_front, Fnd)
    if ref_ps is not None and len(ref_ps):
        igdx = float(np.linalg.norm(ref_ps[:, None, :] - Xc[None, :, :], axis=2).min(1).mean())
    else:
        igdx = np.inf
    info = adaptive_niching(Xc, np.zeros(Xc.shape[1]), np.ones(Xc.shape[1]),
                            rng=np.random.default_rng(0)) if len(Xc) >= 4 else None
    n_modes = float(info.n_modes) if info else 1.0
    if len(Xc) > 1:
        D = np.linalg.norm(Xc[:, None, :] - Xc[None, :, :], axis=2)
        place_div = float(D[np.triu_indices(len(Xc), 1)].mean())
    else:
        place_div = 0.0
    means = Fnd.mean(0)
    return {"HV": hv, "IGD_ref": igd_ref, "IGDX_ref": igdx, "n_modes": n_modes,
            "placement_diversity": place_div,
            "mean_access": float(means[0]), "max_access": float(means[1])}


def canonical_nd_placements(prob, X, F):
    """Canonicalised non-dominated placements (for building the combined reference PS)."""
    from algorithms.equivalence_fitness import fast_nondominated_sort
    if len(X) == 0:
        return np.empty((0, prob.n_var))
    nd = fast_nondominated_sort(F)[0]
    return prob.feature_map(X[nd])


def combined_reference_front(all_F: np.ndarray, max_in: int = 2500,
                             max_out: int = 800, seed: int = 0) -> np.ndarray:
    """Non-dominated set of all (feasible) objective vectors -> reference front.

    The O(n^2) sort is capped by subsampling the input (the union of thousands of
    solutions) to `max_in`, and the resulting front is thinned to `max_out` so the
    per-run IGD computation stays fast. Both are approximations of the true (unknown)
    front, applied identically to every algorithm, so comparisons stay fair."""
    all_F = np.asarray(all_F, float)
    rng = np.random.default_rng(seed)
    if len(all_F) > max_in:
        all_F = all_F[rng.choice(len(all_F), max_in, replace=False)]
    nd = fast_nondominated_sort(all_F)[0]
    front = all_F[nd]
    if len(front) > max_out:
        front = front[rng.choice(len(front), max_out, replace=False)]
    return front


def _near_front_mask(F, ref_front, eps=0.10):
    """Solutions within eps (normalised) of the reference front -- near-Pareto."""
    if ref_front is None or len(F) == 0:
        return np.ones(len(F), bool)
    ideal = ref_front.min(0); nadir = ref_front.max(0)
    span = np.where(nadir - ideal < 1e-12, 1.0, nadir - ideal)
    Fn = (F - ideal) / span; Rn = (ref_front - ideal) / span
    d = np.linalg.norm(Fn[:, None, :] - Rn[None, :, :], axis=2).min(1)
    return d <= eps


def _route_families(prob, X, F=None, ref_front=None, threshold=0.35, max_n=60,
                    quality_eps=0.10):
    """Count GENUINE Pareto-equivalent route families: topologically-distinct routes
    that are also NEAR the reference front (quality-gated, so scattered low-quality
    routes are not credited as families). Returns (n_families, mean pairwise dist)."""
    if len(X) == 0:
        return 0, 0.0
    # quality gate: keep only near-Pareto solutions
    if F is not None and ref_front is not None:
        near = _near_front_mask(F, ref_front, quality_eps)
        if near.any():
            X = X[near]
    if len(X) == 0:
        return 0, 0.0
    idx = np.arange(len(X))
    if len(X) > max_n:                      # cap cost
        idx = np.linspace(0, len(X) - 1, max_n).astype(int)
    plans = [prob.route_plan(X[i]) for i in idx]
    reps = []
    for p in plans:                                  # cheap topology distance (no Hausdorff)
        if all(rm.cheap_route_distance(p, q) >= threshold for q in reps):
            reps.append(p)
    dists = []
    for i in range(len(plans)):
        for j in range(i + 1, len(plans)):
            dists.append(rm.cheap_route_distance(plans[i], plans[j]))
    div = float(np.mean(dists)) if dists else 0.0
    return len(reps), div


def compute_app_metrics(prob, X, F, CV, ref_front, *, family_threshold=0.35) -> dict:
    feas = (CV <= 0) if CV is not None else np.ones(len(X), bool)
    feasible_ratio = float(np.mean(feas)) if len(X) else 0.0
    Xf, Ff = (X[feas], F[feas]) if feas.any() else (X, F)
    hv = hypervolume(Ff, ref_front) if len(Ff) else 0.0
    # IGD to combined reference front (objective space)
    if len(Ff):
        ideal = ref_front.min(0); nadir = ref_front.max(0)
        span = np.where(nadir - ideal < 1e-12, 1.0, nadir - ideal)
        rn = (ref_front - ideal) / span; fn = (Ff - ideal) / span
        igd_ref = float(np.linalg.norm(rn[:, None, :] - fn[None, :, :], axis=2).min(1).mean())
    else:
        igd_ref = np.inf
    nfam, fdiv = _route_families(prob, Xf, F=Ff, ref_front=ref_front,
                                 threshold=family_threshold)
    means = Ff.mean(0) if len(Ff) else np.full(prob.n_obj, np.nan)
    out = {
        "HV": hv, "IGD_ref": igd_ref, "feasible_ratio": feasible_ratio,
        "n_route_families": float(nfam), "route_family_diversity": fdiv,
        "total_distance": float(means[0]), "risk_exposure": float(means[1]),
    }
    if len(means) > 2:
        out["makespan"] = float(means[2])
    return out
