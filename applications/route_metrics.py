"""Topology-aware distances between multi-UAV route plans (Phase 10).

In the UAV application a "solution" is a *route plan*: an assignment of targets to
UAVs and, per UAV, an ordered visiting sequence realised as a path (sequence of
graph nodes / waypoints). Decision-space diversity for MMOP route families needs
distances that respect route TOPOLOGY, not raw decision-vector Euclidean distance.

This module provides the building blocks (each normalised to [0,1] where sensible):
  * edge_jaccard_distance       -- 1 - |E1 ∩ E2| / |E1 ∪ E2| over traversed edges
  * route_overlap_ratio         -- fraction of shared edges (similarity)
  * waypoint_hausdorff          -- symmetric Hausdorff between waypoint clouds
  * frechet_like_distance       -- coarse discrete-Fréchet on ordered waypoints
  * assignment_difference       -- normalised target-to-UAV assignment mismatch
  * visiting_order_difference   -- normalised Kendall-tau-style order mismatch
  * route_plan_distance         -- weighted combination (the route-family metric)

A route plan is represented as a dict:
    {
      "assignment": {target_id: uav_id, ...},
      "routes": {uav_id: [node0, node1, ...], ...},      # graph node sequence
      "waypoints": {uav_id: np.ndarray (L,2), ...},      # optional xy coords
    }
Functions accept partial info and degrade gracefully (missing waypoints -> the
geometric terms are skipped and weights renormalised).
"""
from __future__ import annotations

import numpy as np


# --------------------------------------------------------------------------
# edge-set distances
# --------------------------------------------------------------------------
def _edges(route: list) -> set:
    return {(min(a, b), max(a, b)) for a, b in zip(route[:-1], route[1:])}


def _all_edges(plan: dict) -> set:
    e = set()
    for r in plan.get("routes", {}).values():
        e |= _edges(r)
    return e


def edge_jaccard_distance(plan_a: dict, plan_b: dict) -> float:
    ea, eb = _all_edges(plan_a), _all_edges(plan_b)
    if not ea and not eb:
        return 0.0
    inter = len(ea & eb); union = len(ea | eb)
    return 1.0 - inter / union if union else 0.0


def route_overlap_ratio(plan_a: dict, plan_b: dict) -> float:
    ea, eb = _all_edges(plan_a), _all_edges(plan_b)
    union = len(ea | eb)
    return (len(ea & eb) / union) if union else 1.0


# --------------------------------------------------------------------------
# geometric (waypoint) distances
# --------------------------------------------------------------------------
def _stack_waypoints(plan: dict) -> np.ndarray | None:
    wp = plan.get("waypoints")
    if not wp:
        return None
    arrs = [np.asarray(v, dtype=float).reshape(-1, 2) for v in wp.values() if len(v)]
    return np.vstack(arrs) if arrs else None


def waypoint_hausdorff(plan_a: dict, plan_b: dict) -> float:
    A, B = _stack_waypoints(plan_a), _stack_waypoints(plan_b)
    if A is None or B is None:
        return 0.0
    D = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    return float(max(D.min(axis=1).max(), D.min(axis=0).max()))


def frechet_like_distance(route_a_xy: np.ndarray, route_b_xy: np.ndarray) -> float:
    """Coarse discrete-Fréchet on two ordered polylines (O(n*m) DP)."""
    P = np.asarray(route_a_xy, float).reshape(-1, 2)
    Q = np.asarray(route_b_xy, float).reshape(-1, 2)
    n, m = len(P), len(Q)
    if n == 0 or m == 0:
        return 0.0
    ca = np.full((n, m), -1.0)
    d = np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=2)
    ca[0, 0] = d[0, 0]
    for i in range(1, n):
        ca[i, 0] = max(ca[i - 1, 0], d[i, 0])
    for j in range(1, m):
        ca[0, j] = max(ca[0, j - 1], d[0, j])
    for i in range(1, n):
        for j in range(1, m):
            ca[i, j] = max(min(ca[i - 1, j], ca[i - 1, j - 1], ca[i, j - 1]), d[i, j])
    return float(ca[-1, -1])


# --------------------------------------------------------------------------
# combinatorial (assignment / order) distances
# --------------------------------------------------------------------------
def assignment_difference(plan_a: dict, plan_b: dict) -> float:
    a, b = plan_a.get("assignment", {}), plan_b.get("assignment", {})
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    diff = sum(1 for k in keys if a.get(k) != b.get(k))
    return diff / len(keys)


def visiting_order_difference(plan_a: dict, plan_b: dict) -> float:
    """Mean normalised pairwise-order disagreement across UAVs (Kendall-tau-like)."""
    ra, rb = plan_a.get("routes", {}), plan_b.get("routes", {})
    uavs = set(ra) | set(rb)
    if not uavs:
        return 0.0
    vals = []
    for u in uavs:
        sa = [x for x in ra.get(u, [])]; sb = [x for x in rb.get(u, [])]
        common = [x for x in sa if x in sb]
        if len(common) < 2:
            vals.append(0.0); continue
        pos_b = {x: i for i, x in enumerate(sb)}
        order_a = common
        order_b_rank = [pos_b[x] for x in order_a]
        # count inversions vs sorted
        inv = sum(1 for i in range(len(order_b_rank))
                  for j in range(i + 1, len(order_b_rank))
                  if order_b_rank[i] > order_b_rank[j])
        maxinv = len(common) * (len(common) - 1) / 2
        vals.append(inv / maxinv if maxinv else 0.0)
    return float(np.mean(vals)) if vals else 0.0


# --------------------------------------------------------------------------
# combined route-family metric
# --------------------------------------------------------------------------
DEFAULT_WEIGHTS = {"edge_jaccard": 0.4, "waypoint_hausdorff": 0.3,
                   "assignment_diff": 0.2, "visiting_order": 0.1}


def cheap_route_distance(plan_a: dict, plan_b: dict,
                         w=(0.6, 0.25, 0.15)) -> float:
    """Fast topology-only route distance (NO waypoint Hausdorff): weighted
    edge-Jaccard + assignment-difference + visiting-order-difference. Used for
    large-N route-family counting/diversity where the O(n*m) Hausdorff is too slow."""
    ej = edge_jaccard_distance(plan_a, plan_b)
    ad = assignment_difference(plan_a, plan_b)
    vo = visiting_order_difference(plan_a, plan_b)
    return float(w[0] * ej + w[1] * ad + w[2] * vo)


def route_plan_distance(plan_a: dict, plan_b: dict, weights: dict | None = None,
                        hausdorff_scale: float | None = None) -> float:
    """Weighted topology-aware distance between two route plans.

    `hausdorff_scale` normalises the (unbounded) Hausdorff term to ~[0,1]; if None
    and waypoints exist it is estimated from the plans' own spatial extent. Terms
    that cannot be computed (e.g. no waypoints) are dropped and weights renormalised.
    """
    w = dict(weights or DEFAULT_WEIGHTS)
    terms = {
        "edge_jaccard": edge_jaccard_distance(plan_a, plan_b),
        "assignment_diff": assignment_difference(plan_a, plan_b),
        "visiting_order": visiting_order_difference(plan_a, plan_b),
    }
    A, B = _stack_waypoints(plan_a), _stack_waypoints(plan_b)
    if A is not None and B is not None:
        h = waypoint_hausdorff(plan_a, plan_b)
        if hausdorff_scale is None:
            allpts = np.vstack([A, B])
            hausdorff_scale = float(np.linalg.norm(allpts.max(0) - allpts.min(0))) or 1.0
        terms["waypoint_hausdorff"] = min(h / hausdorff_scale, 1.0)
    # keep only available terms, renormalise weights
    active = {k: v for k, v in terms.items() if k in w}
    wsum = sum(w[k] for k in active)
    if wsum <= 0:
        return float(np.mean(list(active.values()))) if active else 0.0
    return float(sum(w[k] * active[k] for k in active) / wsum)
