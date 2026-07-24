"""Generate all Phase-10 UAV-SAR application figures from results + a rebuilt problem.

Figures:
  * osm_scenario   -- real city map, depot, targets, risk/no-fly zones
  * risk_heatmap   -- urban risk field
  * osm_routes     -- multiple Pareto-equivalent UAV route families (core MMOP visual)
  * uav_pareto     -- objective-space Pareto fronts (distance vs risk), EARS vs baselines
  * route_clusters -- decision/route-space clustering of EARS's solutions

Usage:
  python plotting/plot_uav_app.py --config configs/uav_sar.yaml --scenario-seed 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from applications.application_problem import UAVSARProblem
from applications.osm_graph_builder import build_flight_graph
from applications.scenario_generator import generate_scenario
from algorithms.equivalence_fitness import fast_nondominated_sort
from algorithms.niching import adaptive_niching
from plotting._style import apply_style, algo_style, save, PALETTE
from plotting.plot_osm_routes import plot_scenario, plot_route_families
from plotting.plot_risk_heatmap import plot_risk_heatmap
from utils.config import load_config
from utils.io_utils import FIG_DIR, RAW_DIR


def _load(scen, algo, run=0):
    npz = RAW_DIR / "uav_sar" / scen / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None, None, None
    with np.load(npz) as d:
        return d["objectives"], d["decisions"], d.get("CV")


def _pick_route_families(prob, X, F, CV, k=5, thr=0.3):
    """Greedy pick of k topologically-distinct feasible route families near the front."""
    from applications import route_metrics as rm
    feas = (CV <= 0) if CV is not None else np.ones(len(X), bool)
    if not feas.any():
        feas = np.ones(len(X), bool)
    Xf, Ff = X[feas], F[feas]
    nd = fast_nondominated_sort(Ff)[0]
    Xn = Xf[nd]
    plans = [(x, prob.route_plan(x)) for x in Xn]
    reps = []
    for x, p in plans:
        if all(rm.route_plan_distance(p, q) >= thr for _, q in reps):
            reps.append((x, p))
        if len(reps) >= k:
            break
    return [x for x, _ in reps]


def uav_pareto(scen, algorithms, out_stem):
    apply_style()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for a in algorithms:
        F, X, CV = _load(scen, a)
        if F is None:
            continue
        feas = (CV <= 0) if CV is not None else np.ones(len(F), bool)
        if not feas.any():
            continue
        Ff = F[feas]; nd = fast_nondominated_sort(Ff)[0]; P = Ff[nd]
        st = algo_style(a)
        ax.scatter(P[:, 0], P[:, 1], s=18, alpha=0.8, label=a,
                   color=st["color"], marker=st["marker"])
    ax.set_xlabel("total distance (m)"); ax.set_ylabel("risk exposure")
    ax.set_title(f"UAV-SAR Pareto front (distance vs risk) — {scen}")
    ax.legend(fontsize=8, framealpha=0.9)
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


def route_clusters(prob, scen, out_stem):
    apply_style()
    import matplotlib.pyplot as plt
    F, X, CV = _load(scen, "EARS_MMOEA")
    if X is None:
        print("[skip] no EARS results"); return
    feas = (CV <= 0) if CV is not None else np.ones(len(X), bool)
    Xf = X[feas] if feas.any() else X
    info = adaptive_niching(Xf, prob.xl, prob.xu, rng=np.random.default_rng(0))
    # 2-D projection via the first two decision variables (assignment keys)
    fig, ax = plt.subplots(figsize=(6, 5))
    for m in range(info.n_modes):
        sel = info.labels == m
        ax.scatter(Xf[sel, 0], Xf[sel, 1], s=22, color=PALETTE[m % len(PALETTE)],
                   label=f"family {m+1}", edgecolor="white", linewidth=0.3)
    ax.set_xlabel("assignment key $x_1$"); ax.set_ylabel("assignment key $x_2$")
    ax.set_title(f"Decision-space route families — {scen} ({info.n_modes} modes)")
    ax.legend(fontsize=8, framealpha=0.9)
    save(fig, out_stem); plt.close(fig)
    print(f"[ok] wrote {out_stem}.png/.pdf")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/uav_sar.yaml")
    ap.add_argument("--scenario-seed", type=int, default=1)
    args = ap.parse_args(argv)
    cfg = load_config(Path(__file__).resolve().parent.parent / args.config)
    city = cfg["osm"]["city"]; sd = args.scenario_seed
    sc_cfg = cfg["scenario"]
    fg = build_flight_graph(city)
    sc = generate_scenario(fg, n_uav=sc_cfg["n_uav"], n_targets=sc_cfg["n_targets"], seed=sd)
    sc.max_route_length *= cfg.get("battery_mult", 1.0)
    prob = UAVSARProblem(sc, n_styles=cfg.get("n_styles", 1),
                         objective_mode=cfg.get("objective_mode", "triobj"))
    scen = f"{city}_s{sd}"
    from baselines.baseline_registry import ALL_ALGORITHMS

    plot_scenario(prob, FIG_DIR / "osm_scenario", f"Multi-UAV SAR scenario — {city} (s{sd})")
    plot_risk_heatmap(prob, out_stem=FIG_DIR / "risk_heatmap")
    F, X, CV = _load(scen, "EARS_MMOEA")
    if X is not None:
        fams = _pick_route_families(prob, X, F, CV, k=5)
        plot_route_families(prob, fams, FIG_DIR / "osm_routes",
                            f"Pareto-equivalent UAV route families — {city} (s{sd})")
        route_clusters(prob, scen, FIG_DIR / "route_clusters")
    uav_pareto(scen, list(ALL_ALGORITHMS), FIG_DIR / "uav_pareto")
    print("[ok] UAV application figures generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
