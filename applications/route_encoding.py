"""Random-key encoding of multi-UAV route plans (Phase 10).

Bridges the continuous EA decision vector and the discrete multi-UAV routing
problem. A decision vector x in [0,1]^(2*n_targets) encodes:
  * assignment keys  x[0:n_targets]          -> UAV index = floor(key * n_uav)
  * order keys       x[n_targets:2n_targets] -> visiting order within each UAV
This "random-key" scheme (Bean 1994) keeps the search space continuous (so all the
real-coded operators apply) while distinct decision vectors decode to distinct route
families -- exactly what MMOP needs. Graph-agnostic: it returns the assignment and
per-UAV target ORDER; realising the order as graph paths/waypoints is done by the
application problem (which owns the graph).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RouteEncoder:
    n_targets: int
    n_uav: int
    n_styles: int = 1          # per-UAV routing style (corridor choice); 1 = legacy

    @property
    def n_var(self) -> int:
        extra = self.n_uav if self.n_styles > 1 else 0
        return 2 * self.n_targets + extra

    @property
    def bounds(self):
        return np.zeros(self.n_var), np.ones(self.n_var)

    def decode(self, x: np.ndarray) -> dict:
        """Decode one decision vector to {assignment, order, style}."""
        x = np.clip(np.asarray(x, float), 0.0, 1.0)
        akeys = x[:self.n_targets]
        okeys = x[self.n_targets:2 * self.n_targets]
        uav = np.minimum((akeys * self.n_uav).astype(int), self.n_uav - 1)
        assignment = {int(t): int(uav[t]) for t in range(self.n_targets)}
        order = {}
        for u in range(self.n_uav):
            ts = [t for t in range(self.n_targets) if uav[t] == u]
            ts.sort(key=lambda t: okeys[t])      # visiting order by order-key
            order[u] = ts
        if self.n_styles > 1:
            skeys = x[2 * self.n_targets:2 * self.n_targets + self.n_uav]
            style = {u: int(min(int(skeys[u] * self.n_styles), self.n_styles - 1))
                     for u in range(self.n_uav)}
        else:
            style = {u: 0 for u in range(self.n_uav)}
        return {"assignment": assignment, "order": order, "style": style}

    def random(self, rng: np.random.Generator, n: int) -> np.ndarray:
        return rng.random((n, self.n_var))

    def encode(self, assignment: dict, order: dict) -> np.ndarray:
        """Inverse: build a representative decision vector from assignment+order
        (useful for seeding from k-shortest-path heuristics)."""
        x = np.zeros(self.n_var)
        for t, u in assignment.items():
            # place assignment key in the middle of the UAV's key band
            x[t] = (u + 0.5) / self.n_uav
        for u, ts in order.items():
            m = len(ts)
            for rank, t in enumerate(ts):
                x[self.n_targets + t] = (rank + 0.5) / max(m, 1)
        return x
