"""MMOP performance indicators -- BOTH objective space and decision space.

Objective space : IGD, IGD+, HV (normalised), spacing.
Decision space  : IGDX, PSP (Pareto-Set Proximity), mode coverage, #modes.

All "distance-to-reference" indicators take a reference set sampled from the
analytical PS/PF (benchmarks/*). Lower is better for IGD/IGD+/IGDX/spacing;
higher is better for HV/PSP/mode_coverage. Definitions follow Yue et al.
(IEEE TEVC 2018 / Swarm Evol. Comput. 2019) for the MMOP-specific metrics.
"""
from __future__ import annotations

import numpy as np

# lower-is-better flags consumed by the statistics layer
DIRECTION = {
    "IGD": "min", "IGDplus": "min", "HV": "max", "IGDX": "min",
    "PSP": "max", "mode_coverage": "max", "n_modes": "max",
    "spacing": "min",
    # UAV-SAR application metrics (Phase 10)
    "IGD_ref": "min", "feasible_ratio": "max", "n_route_families": "max",
    "route_family_diversity": "max", "total_distance": "min",
    "risk_exposure": "min", "makespan": "min",
    # facility-placement application
    "IGDX_ref": "min", "n_modes": "max", "placement_diversity": "max",
    "mean_access": "min", "max_access": "min",
}


def _pairwise(A, B):
    return np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)


# --------------------------------------------------------------------------
# Objective-space indicators
# --------------------------------------------------------------------------
def igd(ref_pf: np.ndarray, F: np.ndarray) -> float:
    if len(F) == 0:
        return np.inf
    return float(_pairwise(ref_pf, F).min(axis=1).mean())


def igd_plus(ref_pf: np.ndarray, F: np.ndarray) -> float:
    """IGD+ (Ishibuchi 2015): only the dominated component of the distance,
    i.e. how much each obtained point is worse than the reference (minimisation)."""
    if len(F) == 0:
        return np.inf
    # d+(r, f) = || max(f - r, 0) ||  over objectives
    diff = np.maximum(F[None, :, :] - ref_pf[:, None, :], 0.0)
    d = np.linalg.norm(diff, axis=2)
    return float(d.min(axis=1).mean())


def _hv2d(F: np.ndarray, ref_point: np.ndarray) -> float:
    """Exact 2-D hypervolume of the points in F bounded by ref_point (minimisation)."""
    P = F[(F <= ref_point).all(axis=1)]
    if len(P) == 0:
        return 0.0
    P = P[np.argsort(P[:, 0])]
    hv = 0.0
    prev_x = P[0, 0]
    # standard sweep keeping the best (lowest) f2 so far
    # build the staircase of non-dominated points
    nd = []
    best_f2 = np.inf
    for p in P:
        if p[1] < best_f2:
            nd.append(p); best_f2 = p[1]
    nd = np.array(nd)
    prev_f1 = nd[0, 0]
    hv = 0.0
    last_f2 = ref_point[1]
    for i in range(len(nd)):
        f1, f2 = nd[i]
        width = ref_point[0] - f1
        height = last_f2 - f2
        hv += width * height
        last_f2 = f2
    return float(hv)


def hypervolume(F: np.ndarray, ref_pf: np.ndarray, ref_point=None) -> float:
    """Normalised HV. Objectives normalised by the reference-PF ideal/nadir; the
    reference point is (1.1,...) in normalised space (shared across algorithms)."""
    if len(F) == 0:
        return 0.0
    ideal = ref_pf.min(axis=0)
    nadir = ref_pf.max(axis=0)
    span = nadir - ideal
    span[span < 1e-12] = 1.0
    Fn = (F - ideal) / span
    rp = np.full(F.shape[1], 1.1) if ref_point is None else np.asarray(ref_point)
    if F.shape[1] == 2:
        return _hv2d(Fn, rp)
    # general fallback
    try:
        from pymoo.indicators.hv import HV
        return float(HV(ref_point=rp)(Fn))
    except Exception:
        return float("nan")


def spacing(F: np.ndarray) -> float:
    if len(F) < 2:
        return 0.0
    D = _pairwise(F, F)
    np.fill_diagonal(D, np.inf)
    d = D.min(axis=1)
    return float(np.sqrt(((d - d.mean()) ** 2).sum() / (len(d) - 1)))


# --------------------------------------------------------------------------
# Decision-space indicators
# --------------------------------------------------------------------------
def igdx(ref_ps: np.ndarray, X: np.ndarray) -> float:
    if len(X) == 0:
        return np.inf
    return float(_pairwise(ref_ps, X).min(axis=1).mean())


def cover_rate(ref_ps: np.ndarray, X: np.ndarray) -> float:
    """CR: per-dimension overlap of obtained vs true PS bounding box, geometric mean.

    CR = ( prod_i delta_i )^(1/(2D)),
    delta_i = ( (min(vmax,Vmax) - max(vmin,Vmin)) / (Vmax - Vmin) )^2, clamped >=0.
    (Yue et al. 2018.)
    """
    D = ref_ps.shape[1]
    Vmin, Vmax = ref_ps.min(0), ref_ps.max(0)
    vmin, vmax = X.min(0), X.max(0)
    span = Vmax - Vmin
    span[span < 1e-12] = 1e-12
    overlap = np.minimum(vmax, Vmax) - np.maximum(vmin, Vmin)
    delta = np.clip(overlap / span, 0.0, None) ** 2
    delta = np.clip(delta, 1e-12, None)
    return float(np.prod(delta) ** (1.0 / (2 * D)))


def psp(ref_ps: np.ndarray, X: np.ndarray) -> float:
    """Pareto-Set Proximity = CR / IGDX (higher is better)."""
    ix = igdx(ref_ps, X)
    if ix <= 0:
        return np.inf
    return float(cover_rate(ref_ps, X) / ix)


def n_modes(X, xl, xu, rng=None, min_modes=2, max_modes=20) -> int:
    """Number of decision-space modes detected in the obtained set."""
    from algorithms.niching import adaptive_niching
    if len(X) < 4:
        return 1
    info = adaptive_niching(X, xl, xu, min_modes=min_modes, max_modes=max_modes, rng=rng)
    return int(info.n_modes)


def mode_coverage(ref_ps: np.ndarray, X: np.ndarray, radius: float | None = None) -> float:
    """Fraction of reference-PS points that have an obtained solution within `radius`
    (decision-space recall). Radius defaults to a small fraction of the PS extent."""
    if len(X) == 0:
        return 0.0
    if radius is None:
        extent = np.linalg.norm(ref_ps.max(0) - ref_ps.min(0))
        radius = 0.02 * extent
    dmin = _pairwise(ref_ps, X).min(axis=1)
    return float((dmin <= radius).mean())


# --------------------------------------------------------------------------
# Convenience: compute all benchmark indicators for one run
# --------------------------------------------------------------------------
def compute_all(problem, X, F, rng=None, ref_pf=None, ref_ps=None) -> dict[str, float]:
    if ref_pf is None:
        ref_pf = problem.pareto_front(1000)
    if ref_ps is None:
        ref_ps = problem.pareto_set(2000)
    return {
        "IGD": igd(ref_pf, F),
        "IGDplus": igd_plus(ref_pf, F),
        "HV": hypervolume(F, ref_pf),
        "IGDX": igdx(ref_ps, X),
        "PSP": psp(ref_ps, X),
        "mode_coverage": mode_coverage(ref_ps, X),
        "n_modes": float(n_modes(X, problem.xl, problem.xu, rng=rng)),
        "spacing": spacing(F),
    }
