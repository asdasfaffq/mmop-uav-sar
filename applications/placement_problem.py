"""Multi-facility emergency-station placement over a real OSM city -- a genuinely
MULTIMODAL real-world MMOP (Phase 11, second application).

Place K emergency-response stations to serve M demand points (real OSM nodes).
Bi-objective (both minimised):
  1. mean access distance  (p-median: average response efficiency)
  2. max access distance   (p-center: worst-case / fairness)
These two objectives trade off, and -- crucially -- on a real city with several
districts there are MANY geographically-distinct station layouts that achieve
near-identical (mean, max) access. That genuine objective-space degeneracy makes
this a true MMOP: the goal is to find multiple Pareto-equivalent *placement families*,
exactly the decision-space multimodality EARS is designed for (and that pure-
convergence methods miss).

Decision vector: K station positions in normalised [0,1]^2 (n_var = 2K), mapped to
the city bbox and snapped to the nearest graph node. Evaluation is cheap (M x K).
`feature_map` returns canonicalised (sorted) station coordinates so decision-space
diversity counts GENUINELY distinct layouts, not mere station permutations.
"""
from __future__ import annotations

import numpy as np

from applications.osm_graph_builder import FlightGraph


class FacilityPlacementProblem:
    name = "Placement"
    n_obj = 2

    def __init__(self, graph: FlightGraph, n_stations: int = 4, n_demand: int = 120,
                 seed: int = 0):
        self.g = graph
        self.K = int(n_stations)
        self.n_var = 2 * self.K
        self.xl = np.zeros(self.n_var)
        self.xu = np.ones(self.n_var)
        rng = np.random.default_rng(seed)
        # demand points = sampled real OSM nodes (population proxy = node sample)
        idx = rng.choice(len(graph.nodes), size=min(n_demand, len(graph.nodes)),
                         replace=False)
        self.demand = graph.nodes[idx]                       # (M,2) metres
        lo = graph.nodes.min(0); hi = graph.nodes.max(0)
        self._lo, self._span = lo, np.where(hi - lo < 1e-9, 1.0, hi - lo)

    # ------------------------------------------------------------------
    def _stations(self, x: np.ndarray) -> np.ndarray:
        """Map a decision vector to K station xy positions (snapped to nodes)."""
        pos = np.clip(x, 0, 1).reshape(self.K, 2) * self._span + self._lo
        D = np.linalg.norm(self.g.nodes[None, :, :] - pos[:, None, :], axis=2)  # (K,N)
        return self.g.nodes[np.argmin(D, axis=1)]

    def _evaluate_one(self, x):
        st = self._stations(x)
        D = np.linalg.norm(self.demand[:, None, :] - st[None, :, :], axis=2)  # (M,K)
        nearest = D.min(axis=1)
        return np.array([float(nearest.mean()), float(nearest.max())])

    def evaluate(self, X: np.ndarray) -> dict:
        X = np.atleast_2d(np.asarray(X, float))
        F = np.array([self._evaluate_one(x) for x in X])
        return {"F": F, "CV": np.zeros(len(X))}            # unconstrained

    # ------------------------------------------------------------------
    def feature_map(self, X: np.ndarray) -> np.ndarray:
        """Permutation-invariant placement features: each solution's K stations are
        snapped and sorted by (x,y), so Euclidean distance in feature space measures
        GENUINE layout difference (two permutations of the same layout -> identical)."""
        X = np.atleast_2d(np.asarray(X, float))
        feats = np.empty((len(X), self.n_var))
        for i, x in enumerate(X):
            st = self._stations(x)
            stn = (st - self._lo) / self._span                # normalise to [0,1]
            order = np.lexsort((stn[:, 1], stn[:, 0]))
            feats[i] = stn[order].ravel()
        return feats

    def stations_xy(self, x: np.ndarray) -> np.ndarray:
        return self._stations(x)
