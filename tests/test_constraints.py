"""Phase 10: UAV-SAR application problem + constraints (offline synthetic graph)."""
from __future__ import annotations

import numpy as np

from applications.osm_graph_builder import synthetic_flight_graph
from applications.scenario_generator import generate_scenario
from applications.application_problem import UAVSARProblem


def _problem(seed=1):
    fg = synthetic_flight_graph(n=12, seed=0)
    sc = generate_scenario(fg, n_uav=3, n_targets=8, n_risk=3, n_nofly=2, seed=seed)
    return UAVSARProblem(sc), sc


def test_problem_protocol():
    prob, sc = _problem()
    assert prob.n_var == 2 * len(sc.target_idx)
    assert prob.n_obj == 3
    assert prob.xl.shape == (prob.n_var,) and np.all(prob.xu == 1)


def test_evaluate_shapes_and_finite_risk():
    prob, _ = _problem()
    X = np.random.default_rng(0).random((15, prob.n_var))
    out = prob.evaluate(X)
    assert out["F"].shape == (15, 3) and out["CV"].shape == (15,)
    # risk objective must be finite (no-fly handled as constraint, not inf risk)
    assert np.all(np.isfinite(out["F"]))
    assert np.all(out["F"][:, 0] >= 0)             # distances non-negative


def test_route_plan_covers_all_targets_and_returns_to_depot():
    prob, sc = _problem()
    x = np.random.default_rng(2).random(prob.n_var)
    rp = prob.route_plan(x)
    assigned = sorted(t for ts in rp["order"].values() for t in ts)
    assert assigned == list(range(len(sc.target_idx)))
    depot_node = sc.graph.node_ids[sc.depot_idx]
    for u, path in rp["routes"].items():
        if path:
            assert path[0] == depot_node and path[-1] == depot_node


def test_battery_constraint_detects_overlong_plans():
    prob, sc = _problem()
    x = np.zeros(prob.n_var)
    x[:len(sc.target_idx)] = 0.01           # all assignment keys -> UAV 0 (overlong)
    x[len(sc.target_idx):] = np.linspace(0, 1, len(sc.target_idx))
    out = prob.evaluate(x[None, :])
    assert out["CV"][0] > 0                  # battery/range violated


def test_optimizer_can_reach_feasibility():
    from algorithms.ears_mmoea import EARSMMOEA
    from utils.seeds import make_run_context
    prob, _ = _problem()
    params = {"max_modes": 4, "clustering_update_freq": 5, "selection_mode": "hybrid"}
    a = EARSMMOEA(prob, 40, 2000, make_run_context("t", "EARS", 0).rng, params)
    res = a.run()
    assert res.CV is not None and (res.CV <= 0).sum() >= 1
