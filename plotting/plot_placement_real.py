"""Photorealistic real-OSM figures for the placement application (Phase 12+).

Renders results on a REAL OpenStreetMap basemap (contextily map tiles), with an
osmnx street-network / plain fallback if tiles are unavailable. Two figures:
  * realistic_map  -- the real city + demand + EARS's Pareto-equivalent station-layout
                      families (each family a distinct colour).
  * comparison     -- EARS vs key baselines side by side, each panel showing the
                      distinct near-optimal layouts that algorithm finds -- visually
                      demonstrating EARS's decision-space diversity advantage (and the
                      collapse of a convergence-only baseline).

All data are real OSM; figures are code-generated (no AI image generation).

Usage:
  python plotting/plot_placement_real.py --config configs/placement.yaml --instance-seed 11
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from algorithms.equivalence_fitness import fast_nondominated_sort
from applications.osm_graph_builder import build_flight_graph
from applications.placement_problem import FacilityPlacementProblem
from plotting._style import apply_style, save, PALETTE
from utils.config import load_config
from utils.io_utils import FIG_DIR, RAW_DIR

EXP = "placement"   # raw-dir / experiment name; overridden per city in main()


def _load(inst, algo, run=0):
    npz = RAW_DIR / EXP / inst / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None, None
    with np.load(npz) as d:
        return d["objectives"], d["decisions"]


def _basemap(ax, prob, pad=0.06):
    """Add a real OSM map-tile basemap; fall back to the street network if offline."""
    g = prob.g; bb = g.bbox
    dx, dy = (bb[2] - bb[0]) * pad, (bb[3] - bb[1]) * pad
    ax.set_xlim(bb[0] - dx, bb[2] + dx); ax.set_ylim(bb[1] - dy, bb[3] + dy)
    ax.set_aspect("equal")
    try:
        import contextily as cx
        cx.add_basemap(ax, crs=g.crs, source=cx.providers.CartoDB.Positron,
                       attribution_size=5)
        return "tiles"
    except Exception:
        for u, v in g.G.edges():       # fallback: real street network
            xu, yu = g.nodes[g.id_to_idx[u]]; xv, yv = g.nodes[g.id_to_idx[v]]
            ax.plot([xu, xv], [yu, yv], color="0.8", lw=0.4, zorder=1)
        return "streets"


def _distinct_layouts(prob, X, F, k=5, thr=0.12, ref_front=None, eps=0.10):
    """Distinct NEAR-OPTIMAL layouts: non-dominated AND (if a reference front is given)
    within eps of it in normalised objective space, so scattered poorly-converged
    solutions are not counted as 'layouts' (honest quality gate)."""
    nd = fast_nondominated_sort(F)[0]
    Xn = X[nd]; Fn = F[nd]
    if ref_front is not None and len(ref_front):
        ide = ref_front.min(0); nad = ref_front.max(0)
        span = np.where(nad - ide < 1e-12, 1.0, nad - ide)
        Fnorm = (Fn - ide) / span; Rn = (ref_front - ide) / span
        d = np.linalg.norm(Fnorm[:, None, :] - Rn[None, :, :], axis=2).min(1)
        near = d <= eps
        if near.any():
            Xn = Xn[near]
    feat = prob.feature_map(Xn)
    reps = []
    for i in range(len(Xn)):
        if all(np.linalg.norm(feat[i] - feat[j]) >= thr for j in reps):
            reps.append(i)
        if len(reps) >= k:
            break
    return [Xn[i] for i in reps]


def _combined_ref(inst, algorithms):
    from applications.app_metrics import combined_reference_front
    Fs = []
    for a in algorithms:
        F, X = _load(inst, a)
        if F is not None:
            Fs.append(F)
    return combined_reference_front(np.vstack(Fs)) if Fs else None


def realistic_map(prob, layouts, out_stem, title=None):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 8))
    mode = _basemap(ax, prob)
    ax.scatter(prob.demand[:, 0], prob.demand[:, 1], s=10, c="#34495E", alpha=0.45,
               zorder=3, label="Demand")
    for kk, x in enumerate(layouts):
        st = prob.stations_xy(x); col = PALETTE[kk % len(PALETTE)]
        ax.scatter(st[:, 0], st[:, 1], s=240, marker="*", color=col,
                   edgecolor="black", linewidth=0.8, zorder=5,
                   label=f"Layout family {kk+1}")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title or "Pareto-equivalent station layouts on real OSM map")
    ax.legend(loc="upper right", framealpha=0.92, fontsize=8)
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf (basemap={mode})")


def _mean_nmodes_and_repr(inst, algo, n_runs=30):
    """Aggregate mean n_modes (over all runs of this instance) + the run index whose
    n_modes is closest to the median (a representative, not cherry-picked-best, run)."""
    import json
    vals = []
    for ri in range(n_runs):
        jp = RAW_DIR / EXP / inst / algo / f"run_{ri:03d}.json"
        if jp.exists():
            vals.append((ri, json.loads(jp.read_text())["metrics"].get("n_modes", 0)))
    if not vals:
        return 0.0, 0
    arr = np.array([v for _, v in vals]); med = np.median(arr)
    repr_ri = vals[int(np.argmin(np.abs(arr - med)))][0]
    return float(arr.mean()), repr_ri


def comparison(prob, inst, algorithms, out_stem):
    apply_style()
    import matplotlib.pyplot as plt
    ref = _combined_ref(inst, algorithms)          # honest shared quality gate
    n = len(algorithms)
    fig, axes = plt.subplots(1, n, figsize=(5.2 * n, 5.6))
    if n == 1:
        axes = [axes]
    for ax, algo in zip(axes, algorithms):
        _basemap(ax, prob)
        ax.scatter(prob.demand[:, 0], prob.demand[:, 1], s=6, c="#34495E", alpha=0.3, zorder=3)
        mean_nm, ri = _mean_nmodes_and_repr(inst, algo)
        F, X = _load(inst, algo, run=ri)
        if X is not None:
            # all near-optimal station positions in a representative run -> the spread
            # visualises decision-space diversity (many distinct layouts vs collapse).
            lays = _distinct_layouts(prob, X, F, k=200, thr=0.0, ref_front=ref)
            pts = np.vstack([prob.stations_xy(x) for x in lays]) if lays else np.empty((0, 2))
            col = "#D55E00" if algo == "EARS_MMOEA" else "#1F618D"
            ax.scatter(pts[:, 0], pts[:, 1], s=60, marker="*", color=col, alpha=0.45,
                       edgecolor="none", zorder=5)
        ax.set_xticks([]); ax.set_yticks([])
        tag = "  (ours)" if algo == "EARS_MMOEA" else ""
        ax.set_title(f"{algo}{tag}\nmean {mean_nm:.1f} near-optimal layout modes "
                     f"(over 30 runs)", fontsize=10)
    fig.suptitle("Decision-space diversity on the real OSM placement MMOP: EARS-MMOEA "
                 "recovers the most near-optimal station layouts; CPDEA collapses",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf")


def main(argv=None):
    global EXP
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/placement.yaml")
    ap.add_argument("--instance-seed", type=int, default=11)
    ap.add_argument("--city", default=None, help="override OSM city (else config)")
    ap.add_argument("--experiment", default=None,
                    help="raw-dir name (else 'placement')")
    ap.add_argument("--suffix", default="", help="filename suffix, e.g. _guangzhou")
    args = ap.parse_args(argv)
    cfg = load_config(Path(__file__).resolve().parent.parent / args.config)
    city = args.city or cfg["osm"]["city"]; sd = args.instance_seed
    if args.experiment:
        EXP = args.experiment
    suf = args.suffix
    fg = build_flight_graph(city)
    prob = FacilityPlacementProblem(fg, n_stations=cfg["n_stations"],
                                    n_demand=cfg["n_demand"], seed=sd)
    inst = f"{city}_p{sd}"
    from baselines.baseline_registry import ALL_ALGORITHMS
    ref = _combined_ref(inst, list(ALL_ALGORITHMS))
    F, X = _load(inst, "EARS_MMOEA")
    if X is not None:
        realistic_map(prob, _distinct_layouts(prob, X, F, k=5, ref_front=ref),
                      FIG_DIR / f"placement_real_map{suf}",
                      f"EARS-MMOEA: Pareto-equivalent station layouts -- {city}")
    comparison(prob, inst, ["EARS_MMOEA", "CPDEA", "MO_Ring_PSO_SCD"],
               FIG_DIR / f"placement_real_comparison{suf}")
    print(f"[ok] photorealistic placement figures generated for {city}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
