"""Generate a reproducible multi-UAV SAR scenario on a flight graph (Phase 10).

Places one depot and N emergency targets (snapped to graph nodes), plus a risk
field (risk zones / no-fly zones / disaster points) within the map bbox. Fully
deterministic given a seed, so every algorithm sees the identical scenario.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from applications.osm_graph_builder import FlightGraph
from applications.risk_field import RiskField, random_field


@dataclass
class Scenario:
    graph: FlightGraph
    depot_idx: int
    target_idx: list           # node indices of targets
    target_priority: np.ndarray
    risk: RiskField
    n_uav: int
    max_route_length: float     # per-UAV battery/range budget (metres)
    uav_speed: float            # m/s
    max_risk_exposure: float


def generate_scenario(graph: FlightGraph, *, n_uav=4, n_targets=12, n_risk=4,
                      n_nofly=3, n_disaster=2, seed=20260616) -> Scenario:
    rng = np.random.default_rng(seed)
    bbox = graph.bbox
    risk = random_field(bbox, n_risk=n_risk, n_nofly=n_nofly,
                        n_disaster=n_disaster, rng=rng)

    # depot near map centre; targets spread, avoiding no-fly interiors
    centre = np.array([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2])
    depot_idx = graph.nearest_node(centre)

    target_idx = []
    tries = 0
    while len(target_idx) < n_targets and tries < 2000:
        tries += 1
        cand = graph.nodes[rng.integers(len(graph.nodes))]
        if risk.in_no_fly(cand[None, :])[0]:
            continue
        idx = graph.nearest_node(cand)
        if idx != depot_idx and idx not in target_idx:
            target_idx.append(idx)
    priority = rng.uniform(0.5, 1.0, size=len(target_idx))

    # range budget: a multiple of the depot->farthest-target straight distance
    dmax = max(np.linalg.norm(graph.nodes[t] - graph.nodes[depot_idx])
               for t in target_idx)
    max_route_length = 4.0 * dmax        # generous but binding for unbalanced plans
    return Scenario(graph=graph, depot_idx=depot_idx, target_idx=target_idx,
                    target_priority=priority, risk=risk, n_uav=n_uav,
                    max_route_length=max_route_length, uav_speed=15.0,
                    max_risk_exposure=np.inf)
