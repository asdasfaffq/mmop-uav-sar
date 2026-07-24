"""Phase 6 -- parameter analysis for EARS-MMOEA on the VALIDATION subset only.

One-factor-at-a-time (OFAT) sensitivity study around a base configuration, run on
the validation problems declared in configs/benchmark.yaml (MMF1/2/5). For each
parameter and value we measure mean IGD (convergence) and IGDX (decision-space
diversity) over a few independent runs, normalise per problem, and pick the value
minimising a balanced score 0.5*nIGD + 0.5*nIGDX. The chosen values are frozen to
configs/selected_params.yaml and used UNCHANGED for all later experiments.

Integrity: tuning happens ONLY on the validation subset; the final test set
(full MMF1-8 in Phase 7) is never used for parameter selection.

Usage:
  python experiments/run_parameter_analysis.py --config configs/benchmark.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from baselines.baseline_registry import build
from benchmarks import mmf
from metrics.indicators import igd, igdx
from utils.config import load_config
from utils.io_utils import FIG_DIR, SUMMARY_DIR
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent

BASE = dict(  # base config for the search (search pop/budget are reduced for speed)
    decision_mode_archive_ratio=0.5,
    niche_boost=0.5,
    cross_mode_mating_prob=0.3,
    max_modes=12,
    clustering_update_freq=5,
    operator_lr=0.1,
    restart_ratio=0.05,
)

SWEEPS = {
    "niche_boost": [0.0, 0.25, 0.5, 1.0],
    "cross_mode_mating_prob": [0.0, 0.2, 0.3, 0.5],
    "decision_mode_archive_ratio": [0.25, 0.5, 1.0],
    "max_modes": [5, 8, 12, 20],
    "clustering_update_freq": [1, 5, 10],
    "operator_lr": [0.05, 0.1, 0.2],
    # NOTE: archive-guided restart / random-immigrants are reserved for the Phase 8
    # redesign loop and are not yet active in the main loop, so `restart_ratio` is
    # intentionally NOT swept here (it would be an inert knob). It stays at its
    # default in the frozen config and will be tuned if/when restart is added.
}


def _params_from(cfg, pop):
    return {
        "decision_mode_archive_size": int(cfg["decision_mode_archive_ratio"] * pop),
        "niche_boost": cfg["niche_boost"],
        "cross_mode_mating_prob": cfg["cross_mode_mating_prob"],
        "max_modes": int(cfg["max_modes"]),
        "clustering_update_freq": int(cfg["clustering_update_freq"]),
        "operator_lr": cfg["operator_lr"],
        "restart_ratio": cfg["restart_ratio"],
    }


def evaluate_config(cfg, problems, pop, evals, runs):
    """Return mean (IGD, IGDX) per problem for a config."""
    out = {}
    for pname in problems:
        p = mmf.make(pname)
        ref_pf = p.pareto_front(600); ref_ps = p.pareto_set(1200)
        igds, igdxs = [], []
        for ri in range(runs):
            ctx = make_run_context(f"valid:{pname}", f"EARS_search", ri)
            algo = build("EARS_MMOEA", problem=p, pop_size=pop,
                         max_evaluations=evals, rng=ctx.rng,
                         params=_params_from(cfg, pop))
            res = algo.run()
            igds.append(igd(ref_pf, res.F))
            igdxs.append(igdx(ref_ps, res.X))
        out[pname] = (np.mean(igds), np.std(igds), np.mean(igdxs), np.std(igdxs))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--pop", type=int, default=100)
    ap.add_argument("--evals", type=int, default=15000)
    ap.add_argument("--runs", type=int, default=4)
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    problems = cfg["validation_subset"]
    print(f"[param-analysis] validation subset = {problems}; "
          f"pop={args.pop} evals={args.evals} runs={args.runs}", flush=True)

    rows = []
    chosen = dict(BASE)
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    axes = axes.ravel()

    for k, (param, values) in enumerate(SWEEPS.items()):
        scores_igd, scores_igdx = {p: {} for p in problems}, {p: {} for p in problems}
        for v in values:
            c = dict(BASE); c[param] = v
            res = evaluate_config(c, problems, args.pop, args.evals, args.runs)
            for p in problems:
                mIGD, sIGD, mIGDX, sIGDX = res[p]
                scores_igd[p][v] = mIGD; scores_igdx[p][v] = mIGDX
                rows.append(dict(param=param, value=v, problem=p,
                                 mean_IGD=mIGD, std_IGD=sIGD,
                                 mean_IGDX=mIGDX, std_IGDX=sIGDX))
            print(f"  {param}={v}: " +
                  " ".join(f"{p}(IGD={res[p][0]:.4f},IGDX={res[p][2]:.4f})" for p in problems),
                  flush=True)
        # balanced normalised score per value
        combined = {v: 0.0 for v in values}
        for p in problems:
            gi = np.array([scores_igd[p][v] for v in values])
            gx = np.array([scores_igdx[p][v] for v in values])
            ni = (gi - gi.min()) / (np.ptp(gi) + 1e-12)
            nx = (gx - gx.min()) / (np.ptp(gx) + 1e-12)
            for j, v in enumerate(values):
                combined[v] += 0.5 * (ni[j] + nx[j]) / len(problems)
        best_v = min(values, key=lambda v: (combined[v], abs(values.index(v) - values.index(BASE[param]))))
        chosen[param] = best_v
        # plot: mean IGDX (avg over problems) and combined score
        ax = axes[k]
        igdx_avg = [np.mean([scores_igdx[p][v] for p in problems]) for v in values]
        comb = [combined[v] for v in values]
        ax.plot(range(len(values)), igdx_avg, "o-", label="mean IGDX")
        ax2 = ax.twinx()
        ax2.plot(range(len(values)), comb, "s--", color="tab:red", label="balanced score")
        ax.set_xticks(range(len(values))); ax.set_xticklabels([str(v) for v in values])
        ax.set_title(f"{param}  (chosen={best_v})"); ax.set_xlabel("value")
        ax.set_ylabel("mean IGDX"); ax2.set_ylabel("balanced score", color="tab:red")
        ax.axvline(values.index(best_v), color="green", ls=":", alpha=0.6)

    for kk in range(len(SWEEPS), len(axes)):
        axes[kk].axis("off")
    fig.suptitle("EARS-MMOEA parameter sensitivity (validation subset; OFAT)", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / "parameter_sensitivity.png", dpi=300)
    fig.savefig(FIG_DIR / "parameter_sensitivity.pdf")
    plt.close(fig)

    df = pd.DataFrame(rows)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(SUMMARY_DIR / "parameter_analysis.csv", index=False)

    # freeze selected params at the PROTOCOL population size (200)
    final_pop = 200
    selected = {
        "ears_mmoea": {
            "pop_size": final_pop,
            "pareto_archive_size": final_pop,
            "decision_mode_archive_size": int(chosen["decision_mode_archive_ratio"] * final_pop),
            "route_family_archive_size": 50,
            "niche_boost": float(chosen["niche_boost"]),
            "cross_mode_mating_prob": float(chosen["cross_mode_mating_prob"]),
            "max_modes": int(chosen["max_modes"]),
            "min_modes": 2,
            "clustering_update_freq": int(chosen["clustering_update_freq"]),
            "operator_lr": float(chosen["operator_lr"]),
            "operator_min_prob": 0.05,
            "restart_ratio": float(chosen["restart_ratio"]),
            "epsilon_relax_coef": 0.1,
            "epsilon_decay": 0.95,
            "sbx_eta": 20, "sbx_prob": 0.9, "pm_eta": 20, "de_F": 0.5, "de_CR": 0.9,
        }
    }
    sel_path = ROOT / "configs" / "selected_params.yaml"
    header = ("# FROZEN parameter set (Phase 6 parameter analysis on the validation\n"
              "# subset MMF1/2/5 only). Do NOT hand-edit. Used unchanged for Phase 7\n"
              "# benchmark, Phase 9 ablation, and the UAV application.\n")
    sel_path.write_text(header + yaml.safe_dump(selected, sort_keys=False), encoding="utf-8")

    print("\n[chosen]", {k: chosen[k] for k in SWEEPS})
    print(f"[ok] wrote parameter_analysis.csv, parameter_sensitivity.png/pdf, "
          f"and froze {sel_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
