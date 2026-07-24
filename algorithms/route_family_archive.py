"""Module 2 (Archive 3) -- Route-Family Archive (UAV application only).

Stores representatives of distinct UAV *route families* using a topology-aware
distance (edge Jaccard, waypoint Hausdorff, assignment difference, visiting
order). It is only instantiated for the OSM multi-UAV application (Phase 10); the
benchmark uses Archives 1 & 2 (in archives.py). The interface mirrors the other
archives so the main loop can treat all three uniformly.

This is a scaffold for Phase 10: the topology distance and route encoding land in
applications/route_metrics.py and applications/route_encoding.py.
"""
from __future__ import annotations

import numpy as np


class RouteFamilyArchive:
    """Bounded archive of route-family representatives (Phase 10).

    Parameters
    ----------
    capacity : max number of route families retained.
    distance : callable(route_a, route_b) -> float, topology-aware (injected from
        applications/route_metrics.py at Phase 10). If None, falls back to decision
        vector Euclidean distance so the class is testable now.
    """

    def __init__(self, capacity: int, distance=None, min_family_dist: float = 0.1):
        self.capacity = int(capacity)
        self.distance = distance
        self.min_family_dist = float(min_family_dist)
        self.members: list[dict] = []   # each: {X, F, CV, route, label}

    def _dist(self, a, b) -> float:
        if self.distance is not None:
            return float(self.distance(a["route"], b["route"]))
        return float(np.linalg.norm(np.asarray(a["X"]) - np.asarray(b["X"])))

    def update(self, candidates: list[dict]):
        for c in candidates:
            if c.get("CV", 0) and c["CV"] > 0:
                continue  # feasible-first for the family archive
            if not self.members:
                self.members.append(c)
                continue
            dmin = min(self._dist(c, m) for m in self.members)
            if dmin >= self.min_family_dist:
                self.members.append(c)
            else:
                # replace nearest if candidate dominates it in objective sum
                j = int(np.argmin([self._dist(c, m) for m in self.members]))
                if np.sum(c["F"]) < np.sum(self.members[j]["F"]):
                    self.members[j] = c
        if len(self.members) > self.capacity:
            self._truncate()

    def _truncate(self):
        # drop the member whose nearest-neighbour distance is smallest (densest)
        while len(self.members) > self.capacity:
            dens = []
            for i, m in enumerate(self.members):
                others = [self._dist(m, o) for k, o in enumerate(self.members) if k != i]
                dens.append(min(others) if others else np.inf)
            self.members.pop(int(np.argmin(dens)))

    def __len__(self):
        return len(self.members)
