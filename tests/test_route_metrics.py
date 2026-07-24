"""Phase 10: topology-aware route-plan distances behave correctly."""
from __future__ import annotations

import numpy as np

from applications import route_metrics as rm


def _plan(routes, assignment=None, waypoints=None):
    return {"routes": routes, "assignment": assignment or {},
            "waypoints": waypoints or {}}


def test_identical_plans_zero_distance():
    p = _plan({0: [1, 2, 3, 4]}, {1: 0, 2: 0})
    assert rm.edge_jaccard_distance(p, p) == 0.0
    assert rm.assignment_difference(p, p) == 0.0
    assert rm.visiting_order_difference(p, p) == 0.0
    assert rm.route_plan_distance(p, p) == 0.0


def test_edge_jaccard_disjoint_is_one():
    a = _plan({0: [1, 2, 3]})
    b = _plan({0: [7, 8, 9]})
    assert rm.edge_jaccard_distance(a, b) == 1.0
    assert rm.route_overlap_ratio(a, b) == 0.0


def test_edge_jaccard_partial_overlap():
    a = _plan({0: [1, 2, 3]})        # edges (1,2),(2,3)
    b = _plan({0: [1, 2, 4]})        # edges (1,2),(2,4)
    d = rm.edge_jaccard_distance(a, b)
    assert 0.0 < d < 1.0
    assert abs(d - (1 - 1 / 3)) < 1e-9   # inter=1, union=3


def test_edge_undirected():
    a = _plan({0: [1, 2, 3]})
    b = _plan({0: [3, 2, 1]})        # reversed -> same undirected edges
    assert rm.edge_jaccard_distance(a, b) == 0.0


def test_assignment_difference():
    a = _plan({}, {1: 0, 2: 0, 3: 1})
    b = _plan({}, {1: 0, 2: 1, 3: 1})    # target 2 reassigned
    assert abs(rm.assignment_difference(a, b) - 1 / 3) < 1e-9


def test_visiting_order_difference_detects_reversal():
    a = _plan({0: [1, 2, 3, 4]})
    b = _plan({0: [4, 3, 2, 1]})         # fully reversed
    assert rm.visiting_order_difference(a, b) > 0.9


def test_waypoint_hausdorff_and_frechet():
    a = _plan({0: [0, 1]}, waypoints={0: np.array([[0, 0], [1, 0]])})
    b = _plan({0: [0, 1]}, waypoints={0: np.array([[0, 1], [1, 1]])})
    assert abs(rm.waypoint_hausdorff(a, b) - 1.0) < 1e-9
    fr = rm.frechet_like_distance(a["waypoints"][0], b["waypoints"][0])
    assert abs(fr - 1.0) < 1e-9


def test_route_plan_distance_in_unit_range_and_monotone():
    base = _plan({0: [1, 2, 3, 4]}, {1: 0, 2: 0, 3: 0},
                 {0: np.array([[0, 0], [1, 0], [2, 0], [3, 0]])})
    near = _plan({0: [1, 2, 3, 5]}, {1: 0, 2: 0, 3: 0},
                 {0: np.array([[0, 0], [1, 0], [2, 0], [3, 0.2]])})
    far = _plan({0: [9, 8, 7, 6]}, {1: 1, 2: 1, 3: 1},
                {0: np.array([[0, 9], [1, 9], [2, 9], [3, 9]])})
    d_near = rm.route_plan_distance(base, near)
    d_far = rm.route_plan_distance(base, far)
    assert 0.0 <= d_near <= 1.0 and 0.0 <= d_far <= 1.0
    assert d_near < d_far
