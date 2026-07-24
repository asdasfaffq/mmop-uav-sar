"""Risk field over a city area for multi-UAV SAR (Phase 10).

Builds a continuous 2-D risk surface from spatial hazard sources, and evaluates
risk along UAV paths. Sources (all optional):
  * risk_zones      -- (x, y, radius, intensity) Gaussian-ish hazard blobs
  * no_fly_zones    -- (x, y, radius) hard-forbidden discs (risk -> +inf inside)
  * disaster_points -- (x, y, intensity) emergency hotspots (raise risk nearby)
  * building_density / weak_comm -- optional scalar fields sampled on a grid

The field is graph-agnostic: it works on raw (x, y) coordinates, so it composes
with either an OSMnx graph (real lat/lon projected to metres) or a synthetic graph.
Deterministic given a seed; no AI image generation -- everything is code/data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

INF_RISK = 1e6


@dataclass
class RiskField:
    bbox: tuple                      # (xmin, ymin, xmax, ymax) in metres
    risk_zones: list = field(default_factory=list)       # (x,y,r,intensity)
    no_fly_zones: list = field(default_factory=list)     # (x,y,r)
    disaster_points: list = field(default_factory=list)  # (x,y,intensity)
    base_risk: float = 0.05

    def risk_at(self, P: np.ndarray) -> np.ndarray:
        """FINITE risk at points P (N,2) from risk zones + disaster hotspots.

        No-fly zones are handled as a HARD CONSTRAINT (see `nofly_length`), not as
        infinite risk, so the risk objective stays finite and comparable."""
        P = np.atleast_2d(np.asarray(P, float))
        r = np.full(len(P), self.base_risk)
        for (x, y, rad, inten) in self.risk_zones:
            d2 = (P[:, 0] - x) ** 2 + (P[:, 1] - y) ** 2
            r += inten * np.exp(-d2 / (2.0 * max(rad, 1e-6) ** 2))
        for (x, y, inten) in self.disaster_points:
            d2 = (P[:, 0] - x) ** 2 + (P[:, 1] - y) ** 2
            r += inten * np.exp(-d2 / (2.0 * (0.15 * self._scale()) ** 2))
        return r

    def nofly_length(self, xy: np.ndarray, samples_per_seg: int = 10) -> float:
        """Approximate length of a polyline that lies INSIDE any no-fly disc."""
        xy = np.asarray(xy, float).reshape(-1, 2)
        if len(xy) < 2 or not self.no_fly_zones:
            return 0.0
        total = 0.0
        for a, b in zip(xy[:-1], xy[1:]):
            t = np.linspace(0, 1, samples_per_seg)[:, None]
            seg = a[None, :] * (1 - t) + b[None, :] * t
            inside = self.in_no_fly(seg)
            seglen = np.linalg.norm(b - a)
            total += float(inside.mean()) * seglen
        return total

    def in_no_fly(self, P: np.ndarray) -> np.ndarray:
        P = np.atleast_2d(np.asarray(P, float))
        m = np.zeros(len(P), bool)
        for (x, y, rad) in self.no_fly_zones:
            m |= (P[:, 0] - x) ** 2 + (P[:, 1] - y) ** 2 <= rad ** 2
        return m

    def path_risk(self, xy: np.ndarray, samples_per_seg: int = 8) -> float:
        """Cumulative risk exposure along a polyline (integral approximation)."""
        xy = np.asarray(xy, float).reshape(-1, 2)
        if len(xy) < 2:
            return float(self.risk_at(xy).sum()) if len(xy) else 0.0
        total = 0.0
        for a, b in zip(xy[:-1], xy[1:]):
            t = np.linspace(0, 1, samples_per_seg)[:, None]
            seg = a[None, :] * (1 - t) + b[None, :] * t
            seglen = np.linalg.norm(b - a)
            total += float(self.risk_at(seg).mean()) * seglen
        return total

    def _scale(self) -> float:
        return float(np.hypot(self.bbox[2] - self.bbox[0], self.bbox[3] - self.bbox[1]))

    def grid(self, n: int = 120) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (XX, YY, R) for heatmap plotting (no-fly clipped to a large value)."""
        xs = np.linspace(self.bbox[0], self.bbox[2], n)
        ys = np.linspace(self.bbox[1], self.bbox[3], n)
        XX, YY = np.meshgrid(xs, ys)
        P = np.column_stack([XX.ravel(), YY.ravel()])
        R = self.risk_at(P).reshape(XX.shape)
        R = np.clip(R, 0, np.percentile(R[R < INF_RISK], 99) if (R < INF_RISK).any() else 1)
        return XX, YY, R


def random_field(bbox, n_risk=4, n_nofly=3, n_disaster=2, rng=None) -> RiskField:
    """Deterministically sample a risk field within bbox (for scenario generation)."""
    rng = rng or np.random.default_rng(0)
    xmin, ymin, xmax, ymax = bbox
    w, h = xmax - xmin, ymax - ymin

    def pt():
        return (xmin + rng.uniform(0.1, 0.9) * w, ymin + rng.uniform(0.1, 0.9) * h)

    rz = [(*pt(), rng.uniform(0.08, 0.18) * max(w, h), rng.uniform(0.5, 1.0))
          for _ in range(n_risk)]
    nf = [(*pt(), rng.uniform(0.04, 0.09) * max(w, h)) for _ in range(n_nofly)]
    dp = [(*pt(), rng.uniform(0.6, 1.2)) for _ in range(n_disaster)]
    return RiskField(bbox=tuple(bbox), risk_zones=rz, no_fly_zones=nf, disaster_points=dp)
