"""Real OSM city map with depot, targets, risk/no-fly zones, and multi-UAV route
families (Phase 10 figures). Everything is drawn from real OSM data + computed
routes -- no AI image generation.

Two figures:
  * plot_scenario(): the city graph + depot + targets + risk zones + no-fly zones.
  * plot_route_families(): several Pareto-equivalent route families on the map,
    each family in a distinct colour (the core MMOP visual).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from plotting._style import apply_style, save, PALETTE
from utils.io_utils import FIG_DIR


def _draw_base(ax, prob):
    s = prob.s; g = s.graph
    # street graph (light grey)
    for u, v in g.G.edges():
        xu, yu = g.nodes[g.id_to_idx[u]]; xv, yv = g.nodes[g.id_to_idx[v]]
        ax.plot([xu, xv], [yu, yv], color="0.82", lw=0.5, zorder=1)
    # risk zones (orange), no-fly (red hatched), disaster (red star)
    import matplotlib.patches as mp
    for (x, y, r, inten) in s.risk.risk_zones:
        ax.add_patch(mp.Circle((x, y), r, color="#E69F00", alpha=0.18, zorder=2))
    for (x, y, r) in s.risk.no_fly_zones:
        ax.add_patch(mp.Circle((x, y), r, facecolor="none", edgecolor="#D55E00",
                               hatch="xx", lw=1.2, zorder=3))
    for (x, y, inten) in s.risk.disaster_points:
        ax.plot(x, y, marker="*", color="#D55E00", ms=16, zorder=5)
    # depot + targets
    dx, dy = g.nodes[s.depot_idx]
    ax.plot(dx, dy, marker="s", color="black", ms=11, zorder=6, label="Depot")
    T = g.nodes[s.target_idx]
    ax.scatter(T[:, 0], T[:, 1], c="#0072B2", s=45, marker="^", zorder=6,
               edgecolor="white", linewidth=0.6, label="Targets")
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_aspect("equal")


def plot_scenario(prob, out_stem=None, title=None):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 7))
    _draw_base(ax, prob)
    ax.set_title(title or f"Multi-UAV SAR scenario — {prob.s.graph.name}")
    ax.legend(loc="upper right", framealpha=0.9)
    out_stem = out_stem or (FIG_DIR / "osm_scenario")
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


def plot_route_families(prob, families, out_stem=None, title=None):
    """families: list of decision vectors (each decodes to a route plan)."""
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 7))
    _draw_base(ax, prob)
    for k, x in enumerate(families):
        rp = prob.route_plan(x)
        col = PALETTE[k % len(PALETTE)]
        for u in range(prob.s.n_uav):
            wp = rp["waypoints"][u]
            if len(wp) >= 2:
                ax.plot(wp[:, 0], wp[:, 1], color=col, lw=2.0, alpha=0.85,
                        zorder=4, label=f"Family {k+1}" if u == 0 else None)
    ax.set_title(title or "Pareto-equivalent UAV route families")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
    out_stem = out_stem or (FIG_DIR / "osm_routes")
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")
