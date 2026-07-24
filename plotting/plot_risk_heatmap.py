"""Risk heatmap over the real city area, with no-fly zones, depot and targets,
optionally overlaid with one UAV route family (Phase 10 figure).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from plotting._style import apply_style, save
from utils.io_utils import FIG_DIR


def plot_risk_heatmap(prob, overlay_routes=None, out_stem=None, title=None):
    apply_style()
    import matplotlib.pyplot as plt
    import matplotlib.patches as mp
    s = prob.s; g = s.graph
    XX, YY, R = s.risk.grid(160)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.pcolormesh(XX, YY, R, cmap="YlOrRd", shading="auto", zorder=1)
    fig.colorbar(im, ax=ax, label="risk intensity")
    for (x, y, r) in s.risk.no_fly_zones:
        ax.add_patch(mp.Circle((x, y), r, facecolor="none", edgecolor="black",
                               hatch="xx", lw=1.2, zorder=3))
    dx, dy = g.nodes[s.depot_idx]
    ax.plot(dx, dy, "ks", ms=10, zorder=5, label="Depot")
    T = g.nodes[s.target_idx]
    ax.scatter(T[:, 0], T[:, 1], c="#0072B2", s=40, marker="^", zorder=5,
               edgecolor="white", linewidth=0.6, label="Targets")
    if overlay_routes is not None:
        rp = prob.route_plan(overlay_routes)
        for u in range(s.n_uav):
            wp = rp["waypoints"][u]
            if len(wp) >= 2:
                ax.plot(wp[:, 0], wp[:, 1], color="#0072B2", lw=1.8, alpha=0.9, zorder=4)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_aspect("equal")
    ax.set_title(title or f"Urban risk field — {g.name}")
    ax.legend(loc="upper right", framealpha=0.9)
    out_stem = out_stem or (FIG_DIR / "risk_heatmap")
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")
