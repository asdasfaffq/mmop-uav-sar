"""Multi-UAV emergency-SAR MMOP over a real OSM city graph (Phase 10).

A decision vector (random-key, `route_encoding`) decodes to a target->UAV
assignment and per-UAV visiting order; each UAV flies depot -> ordered targets ->
depot along graph shortest paths. We precompute all-pairs shortest paths among the
{depot} + targets ONCE, so evaluation is O(n_targets) lookups -- fast enough for the
30-run study.

Objectives (all MINIMISED), chosen to create genuine trade-offs and admit multiple
geographically-distinct but objective-equivalent route families:
  1. total_distance  -- sum of all UAV path lengths
  2. risk_exposure   -- sum of path-integrated risk over the risk field
  3. makespan        -- max per-UAV path length (mission time / load balance)

Constraints (total violation -> CV):
  * battery/range: each UAV path length <= max_route_length
  * reachability: all legs must exist (else large penalty)

This is a CONSTRAINED MMOP, so the constraint-aware selection and route-family
modules (no-ops on the unconstrained MMF benchmark) are actually exercised here.
"""
from __future__ import annotations

import numpy as np

from applications.route_encoding import RouteEncoder
from applications.scenario_generator import Scenario


class UAVSARProblem:
    name = "UAV_SAR"

    def __init__(self, scenario: Scenario, samples_per_seg: int = 6, n_styles: int = 1,
                 objective_mode: str = "triobj"):
        self.s = scenario
        self.n_styles = int(n_styles)
        # 'triobj' = [distance, risk, makespan]; 'biobj' = [distance, risk].
        # The bi-objective robust-route-planning variant (find multiple geographically
        # distinct route families at similar distance/risk) is the MMOP-native setting.
        self.objective_mode = objective_mode
        self.n_obj = 2 if objective_mode == "biobj" else 3
        self.enc = RouteEncoder(n_targets=len(scenario.target_idx),
                                n_uav=scenario.n_uav, n_styles=self.n_styles)
        self.n_var = self.enc.n_var
        self.xl, self.xu = self.enc.bounds
        self._precompute(samples_per_seg)

    # ------------------------------------------------------------------
    def _precompute(self, sps):
        s = self.s; g = s.graph
        self._nodes = [s.depot_idx] + list(s.target_idx)   # 0 = depot
        m = len(self._nodes)
        ns = self.n_styles
        # per-style leg tables: style 0 = shortest length, style 1 = risk-avoiding
        self._len = [np.full((m, m), np.inf) for _ in range(ns)]
        self._risk = [np.zeros((m, m)) for _ in range(ns)]
        self._nofly = [np.zeros((m, m)) for _ in range(ns)]
        self._path = [dict() for _ in range(ns)]
        risk_w = self._risk_weighted_graph() if ns > 1 else None
        for st in range(ns):
            for a in range(m):
                self._len[st][a, a] = 0.0
                self._path[st][(a, a)] = [self._nodes[a]]
        for a in range(m):
            for b in range(a + 1, m):
                for st in range(ns):
                    path = self._style_path(a, b, st, risk_w)
                    L = self._path_length(path)
                    self._len[st][a, b] = self._len[st][b, a] = L
                    self._path[st][(a, b)] = path
                    self._path[st][(b, a)] = path[::-1]
                    xy = g.nodes[path]
                    self._risk[st][a, b] = self._risk[st][b, a] = s.risk.path_risk(xy, samples_per_seg=sps)
                    self._nofly[st][a, b] = self._nofly[st][b, a] = s.risk.nofly_length(xy)

    def _risk_weighted_graph(self):
        """Edge weights = length * (1 + risk at edge midpoint) for risk-avoiding paths."""
        import networkx as nx
        g = self.s.graph; G = g.G
        H = nx.Graph()
        for u, v, data in G.edges(data=True):
            xu, yu = g.nodes[g.id_to_idx[u]]; xv, yv = g.nodes[g.id_to_idx[v]]
            mid = np.array([[(xu + xv) / 2, (yu + yv) / 2]])
            r = float(self.s.risk.risk_at(mid)[0])
            H.add_edge(u, v, w=data["length"] * (1.0 + 3.0 * r))
        return H

    def _style_path(self, a, b, st, risk_w):
        """Node-index path for a leg (local indices a,b -> node indices via _nodes)."""
        import networkx as nx
        g = self.s.graph
        ia, ib = self._nodes[a], self._nodes[b]      # graph node indices
        try:
            if st == 0 or risk_w is None:
                _, path = g.shortest_path_idx(ia, ib); return path
            sa, sb = g.node_ids[ia], g.node_ids[ib]  # graph node ids
            nodes = nx.shortest_path(risk_w, sa, sb, weight="w")
            return [g.id_to_idx[n] for n in nodes]
        except Exception:
            _, path = g.shortest_path_idx(ia, ib); return path

    def _path_length(self, path):
        g = self.s.graph
        L = 0.0
        for u, v in zip(path[:-1], path[1:]):
            su, sv = g.node_ids[u], g.node_ids[v]
            L += g.G[su][sv]["length"] if g.G.has_edge(su, sv) else \
                float(np.linalg.norm(g.nodes[u] - g.nodes[v]))
        return L

    # ------------------------------------------------------------------
    def route_plan(self, x: np.ndarray) -> dict:
        """Decode + realise: returns assignment, per-UAV graph-node routes, waypoints.

        `routes[u]` is the full sequence of graph node indices traversed by UAV u;
        `waypoints[u]` is the corresponding (L,2) xy polyline (for plotting and the
        topology-aware route-family distance)."""
        dec = self.enc.decode(x)
        g = self.s.graph
        routes, waypoints, lengths, risks = {}, {}, {}, {}
        for u in range(self.s.n_uav):
            st = dec["style"][u]
            seq = [0] + [1 + t for t in dec["order"][u]] + [0]   # local indices
            gpath, L, R = [], 0.0, 0.0
            for a, b in zip(seq[:-1], seq[1:]):
                L += self._len[st][a, b]; R += self._risk[st][a, b]
                gpath += self._path[st][(a, b)][:-1]    # drop shared junction
            if len(seq) > 1:
                gpath.append(self._path[st][(seq[-2], seq[-1])][-1])
            routes[u] = gpath
            waypoints[u] = g.nodes[gpath] if gpath else np.empty((0, 2))
            lengths[u] = L; risks[u] = R
        return {"assignment": dec["assignment"], "order": dec["order"],
                "routes": routes, "waypoints": waypoints,
                "lengths": lengths, "risks": risks}

    # ------------------------------------------------------------------
    def _evaluate_one(self, x):
        dec = self.enc.decode(x)
        total_len = 0.0; total_risk = 0.0; max_len = 0.0; cv = 0.0
        s = self.s
        for u in range(s.n_uav):
            st = dec["style"][u]
            seq = [0] + [1 + t for t in dec["order"][u]] + [0]
            L = R = nofly = 0.0
            for a, b in zip(seq[:-1], seq[1:]):
                Lab = self._len[st][a, b]
                if not np.isfinite(Lab):
                    cv += 10.0; Lab = 0.0
                L += Lab; R += self._risk[st][a, b]; nofly += self._nofly[st][a, b]
            total_len += L; total_risk += R; max_len = max(max_len, L)
            over = L - s.max_route_length
            if over > 0:
                cv += over / s.max_route_length          # battery violation
            if nofly > 0:
                cv += nofly / max(s.max_route_length, 1.0)   # no-fly intrusion
        if self.objective_mode == "biobj":
            F = np.array([total_len, total_risk])
        else:
            F = np.array([total_len, total_risk, max_len])
        return F, cv

    def feature_map(self, X: np.ndarray) -> np.ndarray:
        """Topology-aware decision features for MMOP route-family diversity.

        Returns a one-hot encoding of each target's UAV assignment (+ a light
        visiting-order signal), so that Euclidean distance in feature space tracks
        ROUTE-FAMILY distance (which UAV serves which target) rather than raw
        random-key distance. EARS uses this for niching and the sparsity bonus,
        realising the 'route/structure-preserving' design on the application."""
        X = np.atleast_2d(np.asarray(X, float))
        n_t, n_u = self.enc.n_targets, self.s.n_uav
        akeys = np.clip(X[:, :n_t], 0, 1)
        uav = np.minimum((akeys * n_u).astype(int), n_u - 1)     # (N, n_t)
        onehot = np.zeros((len(X), n_t * n_u))
        rows = np.arange(len(X))[:, None]
        cols = np.arange(n_t)[None, :] * n_u + uav
        onehot[rows, cols] = 1.0
        # light order signal (rank within UAV) keeps families with same assignment
        # but different visiting order slightly apart
        okeys = np.clip(X[:, n_t:2 * n_t], 0, 1) * 0.3
        feats = [onehot, okeys]
        if self.n_styles > 1:                      # routing style is a route-family axis
            skeys = np.clip(X[:, 2 * n_t:2 * n_t + n_u], 0, 1)
            style = np.minimum((skeys * self.n_styles).astype(int), self.n_styles - 1)
            soh = np.zeros((len(X), n_u * self.n_styles))
            cols = np.arange(n_u)[None, :] * self.n_styles + style
            soh[np.arange(len(X))[:, None], cols] = 1.0
            feats.append(soh)
        return np.hstack(feats)

    def evaluate(self, X: np.ndarray) -> dict:
        X = np.atleast_2d(np.asarray(X, float))
        F = np.empty((len(X), self.n_obj)); CV = np.empty(len(X))
        for i in range(len(X)):
            F[i], CV[i] = self._evaluate_one(X[i])
        return {"F": F, "CV": CV}
