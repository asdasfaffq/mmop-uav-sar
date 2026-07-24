"""Real-OSM figures for the facility-placement MMOP (Phase 11/12).

  * placement_map     -- real city + demand points + several Pareto-equivalent
                         station-placement families (the core MMOP visual).
  * placement_pareto  -- objective-space fronts (mean vs max access), EARS vs baselines.
  * placement_clusters-- decision-space clustering of EARS placement layouts.

Usage:
  python plotting/plot_placement.py --config configs/placement.yaml --instance-seed 11
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from algorithms.equivalence_fitness import fast_nondominated_sort
from algorithms.niching import adaptive_niching
from applications.osm_graph_builder import build_flight_graph
from applications.placement_problem import FacilityPlacementProblem
from plotting._style import apply_style, algo_style, save, PALETTE
from utils.config import load_config
from utils.io_utils import FIG_DIR, RAW_DIR


def _load(inst, algo, run=0):
    npz = RAW_DIR / "placement" / inst / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None, None
    with np.load(npz) as d:
        return d["objectives"], d["decisions"]


def _draw_city(ax, prob):
    g = prob.g
    for u, v in g.G.edges():
        xu, yu = g.nodes[g.id_to_idx[u]]; xv, yv = g.nodes[g.id_to_idx[v]]
        ax.plot([xu, xv], [yu, yv], color="0.85", lw=0.4, zorder=1)
    ax.scatter(prob.demand[:, 0], prob.demand[:, 1], s=10, c="#0072B2", alpha=0.5,
               zorder=2, label="Demand")
    ax.set_aspect("equal"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")


def placement_map(prob, families, out_stem, title=None):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    _draw_city(ax, prob)
    for k, x in enumerate(families):
        st = prob.stations_xy(x); col = PALETTE[k % len(PALETTE)]
        ax.scatter(st[:, 0], st[:, 1], s=180, marker="*", color=col,
                   edgecolor="black", linewidth=0.6, zorder=5,
                   label=f"Layout family {k+1}")
    ax.set_title(title or "Pareto-equivalent station-placement families")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf")


def placement_pareto(inst, algorithms, out_stem):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for a in algorithms:
        F, X = _load(inst, a)
        if F is None:
            continue
        nd = fast_nondominated_sort(F)[0]; P = F[nd]; st = algo_style(a)
        ax.scatter(P[:, 0], P[:, 1], s=16, alpha=0.8, label=a, color=st["color"], marker=st["marker"])
    ax.set_xlabel("mean access distance (m)"); ax.set_ylabel("max access distance (m)")
    ax.set_title(f"Placement Pareto front -- {inst}")
    ax.legend(fontsize=8, framealpha=0.9)
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf")


def access_heatmap(prob, x, out_stem, title=None):
    """Access-distance field for one placement, on the real city."""
    apply_style()
    import matplotlib.pyplot as plt
    g = prob.g; bb = g.bbox
    xs = np.linspace(bb[0], bb[2], 160); ys = np.linspace(bb[1], bb[3], 160)
    XX, YY = np.meshgrid(xs, ys)
    P = np.column_stack([XX.ravel(), YY.ravel()])
    st = prob.stations_xy(x)
    acc = np.linalg.norm(P[:, None, :] - st[None, :, :], axis=2).min(1).reshape(XX.shape)
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.pcolormesh(XX, YY, acc, cmap="YlGnBu", shading="auto")
    fig.colorbar(im, ax=ax, label="access distance to nearest station (m)")
    ax.scatter(prob.demand[:, 0], prob.demand[:, 1], s=8, c="0.3", alpha=0.4, zorder=3)
    ax.scatter(st[:, 0], st[:, 1], s=200, marker="*", color="#D55E00",
               edgecolor="black", zorder=5, label="Stations")
    ax.set_aspect("equal"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_title(title or "Station coverage (access-distance field)")
    ax.legend(loc="upper right", framealpha=0.9)
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf")


def placement_clusters(prob, inst, out_stem):
    apply_style()
    import matplotlib.pyplot as plt
    F, X = _load(inst, "EARS_MMOEA")
    if X is None:
        return
    nd = fast_nondominated_sort(F)[0]; feat = prob.feature_map(X[nd])
    info = adaptive_niching(feat, np.zeros(feat.shape[1]), np.ones(feat.shape[1]),
                            rng=np.random.default_rng(0))
    fig, ax = plt.subplots(figsize=(6, 5))
    for m in range(info.n_modes):
        sel = info.labels == m
        ax.scatter(feat[sel, 0], feat[sel, 1], s=22, color=PALETTE[m % len(PALETTE)],
                   edgecolor="white", linewidth=0.3, label=f"layout family {m+1}")
    ax.set_xlabel("station-1 x (norm)"); ax.set_ylabel("station-1 y (norm)")
    ax.set_title(f"Decision-space placement families -- {inst} ({info.n_modes} modes)")
    if info.n_modes <= 8:
        ax.legend(fontsize=7, framealpha=0.9)
    save(fig, out_stem); plt.close(fig); print(f"[ok] {out_stem}.png/.pdf")


def _pick_families(prob, X, F, k=5, thr=0.15):
    nd = fast_nondominated_sort(F)[0]
    Xn = X[nd]; feat = prob.feature_map(Xn)
    reps = []
    for i in range(len(Xn)):
        if all(np.linalg.norm(feat[i] - feat[j]) >= thr for j in reps):
            reps.append(i)
        if len(reps) >= k:
            break
    return [Xn[i] for i in reps]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/placement.yaml")
    ap.add_argument("--instance-seed", type=int, default=11)
    args = ap.parse_args(argv)
    cfg = load_config(Path(__file__).resolve().parent.parent / args.config)
    city = cfg["osm"]["city"]; sd = args.instance_seed
    fg = build_flight_graph(city)
    prob = FacilityPlacementProblem(fg, n_stations=cfg["n_stations"],
                                    n_demand=cfg["n_demand"], seed=sd)
    inst = f"{city}_p{sd}"
    from baselines.baseline_registry import ALL_ALGORITHMS
    F, X = _load(inst, "EARS_MMOEA")
    if X is not None:
        fams = _pick_families(prob, X, F, k=5)
        placement_map(prob, fams, FIG_DIR / "placement_map",
                      f"Pareto-equivalent station layouts -- {city} ({len(fams)} families)")
        access_heatmap(prob, fams[0], FIG_DIR / "placement_access_heatmap",
                       f"Station coverage field -- {city}")
        placement_clusters(prob, inst, FIG_DIR / "placement_clusters")
    placement_pareto(inst, list(ALL_ALGORITHMS), FIG_DIR / "placement_pareto")
    print("[ok] placement figures generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
