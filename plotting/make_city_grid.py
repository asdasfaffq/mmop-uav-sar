"""All-cities real-OSM decision-space comparison grid (rows = algorithms, cols = cities).

Publication-quality figure: every compared city (Macau, Guangzhou, Shenzhen, San Francisco,
Hong Kong) on a REAL, high-zoom OpenStreetMap basemap. Each panel overlays the near-optimal
station layouts of a median-representative run and shades their convex hull, so the reader
SEES the decision-space coverage: EARS-MMOEA (top, highlighted) spreads across the city; the
convergence-only CPDEA (middle) collapses to a single layout; the PSO niching baseline
(bottom) is intermediate. All data are real OSM; figures are code-generated (no AI imagery).

Usage:
  python plotting/make_city_grid.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import plotting.plot_placement_real as ppr
from applications.osm_graph_builder import build_flight_graph
from applications.placement_problem import FacilityPlacementProblem
from baselines.baseline_registry import ALL_ALGORITHMS
from plotting._style import apply_style
from utils.config import load_config
from utils.io_utils import FIG_DIR

ROOT = Path(__file__).resolve().parent.parent
CITIES = [("Macau", "Macau", "placement"),
          ("Guangzhou", "Guangzhou", "placement_guangzhou"),
          ("Shenzhen", "Shenzhen", "placement_shenzhen"),
          ("San Francisco", "SanFrancisco", "placement_sanfrancisco"),
          ("Hong Kong", "HongKong", "placement_hongkong")]
# (algo key, row label, point colour, hull colour)
ALGOS = [("EARS_MMOEA", "EARS-MMOEA\n(ours)", "#D55E00", "#F6A24E"),
         ("CPDEA", "CPDEA", "#0072B2", "#6FA8DC"),
         ("MO_Ring_PSO_SCD", "MO_Ring_PSO_SCD", "#009E73", "#76C7A8")]
ZOOM = 14   # high-zoom tiles -> crisp streets


def _crisp_basemap(ax, prob, pad=0.04):
    g = prob.g; bb = g.bbox
    dx, dy = (bb[2] - bb[0]) * pad, (bb[3] - bb[1]) * pad
    ax.set_xlim(bb[0] - dx, bb[2] + dx); ax.set_ylim(bb[1] - dy, bb[3] + dy)
    ax.set_aspect("equal")
    try:
        import contextily as cx
        cx.add_basemap(ax, crs=g.crs, source=cx.providers.CartoDB.Voyager,
                       zoom=ZOOM, attribution=False)
    except Exception:
        for u, v in g.G.edges():
            xu, yu = g.nodes[g.id_to_idx[u]]; xv, yv = g.nodes[g.id_to_idx[v]]
            ax.plot([xu, xv], [yu, yv], color="0.82", lw=0.4, zorder=1)


def _hull_fill(ax, pts, color):
    """Shade the convex hull of the layout points: the decision-space coverage area."""
    if len(pts) < 3:
        return
    try:
        from scipy.spatial import ConvexHull
        h = ConvexHull(pts)
        poly = pts[h.vertices]
        ax.fill(poly[:, 0], poly[:, 1], color=color, alpha=0.22, zorder=4,
                edgecolor=color, linewidth=1.2)
    except Exception:
        pass


def main(argv=None):
    apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    cfg = load_config(ROOT / "configs/placement.yaml")
    K, M, sd = cfg["n_stations"], cfg["n_demand"], 11
    nr, nc = len(ALGOS), len(CITIES)
    fig, axes = plt.subplots(nr, nc, figsize=(4.3 * nc, 4.6 * nr))
    for c, (disp, city, exp) in enumerate(CITIES):
        ppr.EXP = exp
        fg = build_flight_graph(city)
        prob = FacilityPlacementProblem(fg, n_stations=K, n_demand=M, seed=sd)
        inst = f"{city}_p{sd}"
        ref = ppr._combined_ref(inst, list(ALL_ALGORITHMS))
        for r, (algo, alabel, pcol, hcol) in enumerate(ALGOS):
            ax = axes[r, c]
            _crisp_basemap(ax, prob)
            ax.scatter(prob.demand[:, 0], prob.demand[:, 1], s=7, c="#5D6D7E",
                       alpha=0.30, zorder=3, linewidths=0)
            mean_nm, ri = ppr._mean_nmodes_and_repr(inst, algo)
            F, X = ppr._load(inst, algo, run=ri)
            npts = 0
            if X is not None:
                lays = ppr._distinct_layouts(prob, X, F, k=200, thr=0.0, ref_front=ref)
                pts = (np.vstack([prob.stations_xy(x) for x in lays])
                       if lays else np.empty((0, 2)))
                npts = len(pts)
                _hull_fill(ax, pts, hcol)
                ax.scatter(pts[:, 0], pts[:, 1], s=95, marker="*", color=pcol,
                           alpha=0.92, edgecolor="white", linewidth=0.6, zorder=6)
            ax.set_xticks([]); ax.set_yticks([])
            # mode count placed BELOW the map (as an xlabel) so no text overlays the image
            ax.set_xlabel(f"{mean_nm:.1f} layout modes (mean / 30 runs)",
                          fontsize=11, fontweight="bold", color="#222222", labelpad=4)
            if r == 0:
                ax.set_title(disp, fontsize=17, fontweight="bold", pad=8)
            if c == 0:
                ax.set_ylabel(alabel, fontsize=14, fontweight="bold")
            # highlight the EARS (ours) row with a gold frame
            if algo == "EARS_MMOEA":
                for s in ax.spines.values():
                    s.set_visible(True); s.set_color("#D55E00"); s.set_linewidth(2.6)
        print(f"[ok] column {disp} ({exp}) rendered", flush=True)
    fig.suptitle("Decision-space diversity on real OpenStreetMap maps across five cities: "
                 "EARS-MMOEA (top, gold frame) spreads emergency stations over many "
                 "Pareto-equivalent layouts, while the convergence-only CPDEA collapses to one",
                 fontsize=18, fontweight="bold", y=0.997)
    fig.tight_layout(rect=[0, 0, 1, 0.975])
    out = FIG_DIR / "placement_city_grid"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=360, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out}.png/.pdf (high-res)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
