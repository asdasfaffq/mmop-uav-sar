"""Phase 10 -- multi-UAV emergency-SAR application study on a real OSM city map.

Runs EARS-MMOEA + the 5 baselines on several SAR scenarios (different emergency
layouts on the same real city graph) under the shared protocol, then computes
application metrics against a per-scenario combined-front reference, and persists
results in the same format as the benchmark (so run_statistics.py works).

Two phases:
  A) run every (scenario, algorithm, run), save F/X/CV (resumable);
  B) build a per-scenario combined reference front from all feasible solutions and
     compute application metrics for each run.

Usage:
  python experiments/run_uav_sar.py --config configs/uav_sar.yaml \
      --params configs/selected_params.yaml
"""
from __future__ import annotations

import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from applications.app_metrics import combined_reference_front, compute_app_metrics, DIRECTION
from applications.application_problem import UAVSARProblem
from applications.osm_graph_builder import build_flight_graph
from applications.scenario_generator import generate_scenario
from baselines.baseline_registry import ALL_ALGORITHMS, build
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, load_run, hyperparam_stamp
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "uav_sar"
PROBLEMS: dict = {}     # scenario_name -> UAVSARProblem (built in main, fork-inherited)


def _build_problems(city, scenario_seeds, n_uav, n_targets, n_styles=1,
                    objective_mode="triobj", battery_mult=1.0):
    fg = build_flight_graph(city)
    probs = {}
    for sd in scenario_seeds:
        sc = generate_scenario(fg, n_uav=n_uav, n_targets=n_targets, seed=sd)
        sc.max_route_length *= battery_mult
        probs[f"{city}_s{sd}"] = UAVSARProblem(sc, n_styles=n_styles,
                                               objective_mode=objective_mode)
    return probs


def _exists(scen, algo, ri):
    return (RAW_DIR / EXPERIMENT / scen / algo / f"run_{ri:03d}.json").exists()


def _run_one(task):
    scen, algo, ri, pop, evals, params = task
    if _exists(scen, algo, ri):
        return (scen, algo, ri, "skip")
    try:
        prob = PROBLEMS[scen]
        ctx = make_run_context(scen, algo, ri)
        a = build(algo, problem=prob, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params=params)
        res = a.run()
        cv = res.CV if res.CV is not None else np.zeros(len(res.X))
        # phase-A: store raw arrays + placeholder metrics (filled in phase B)
        save_run(EXPERIMENT, scen, algo, ri, objectives=res.F, decisions=res.X,
                 metrics={"feasible_ratio": float(np.mean(cv <= 0))},
                 seed=ctx.seed, extra_arrays={"CV": cv},
                 meta=hyperparam_stamp(params) if algo == "EARS_MMOEA" else None)
        return (scen, algo, ri, "ok")
    except Exception as e:
        return (scen, algo, ri, f"ERR:{type(e).__name__}:{e}")


def _phase_b_metrics(scenarios, algorithms, n_runs, family_threshold):
    """Build per-scenario combined reference and compute app metrics into each json."""
    for scen in scenarios:
        prob = PROBLEMS[scen]
        # gather all feasible F across algorithms/runs for the reference front
        allF = []
        for algo in algorithms:
            for ri in range(n_runs):
                jp = RAW_DIR / EXPERIMENT / scen / algo / f"run_{ri:03d}.json"
                if not jp.exists():
                    continue
                rec = load_run(jp)
                F = rec["arrays"]["objectives"]; CV = rec["arrays"].get("CV")
                feas = (CV <= 0) if CV is not None else np.ones(len(F), bool)
                if feas.any():
                    allF.append(F[feas])
        ref = combined_reference_front(np.vstack(allF)) if allF else None
        for algo in algorithms:
            for ri in range(n_runs):
                jp = RAW_DIR / EXPERIMENT / scen / algo / f"run_{ri:03d}.json"
                if not jp.exists():
                    continue
                rec = load_run(jp)
                X = rec["arrays"]["decisions"]; F = rec["arrays"]["objectives"]
                CV = rec["arrays"].get("CV")
                m = compute_app_metrics(prob, X, F, CV, ref,
                                        family_threshold=family_threshold)
                rec_meta = json.loads(jp.read_text())
                rec_meta["metrics"] = {k: float(v) for k, v in m.items()}
                jp.write_text(json.dumps(rec_meta, indent=2), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/uav_sar.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    city = cfg["osm"]["city"]
    sc_cfg = cfg["scenario"]; proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    scenario_seeds = cfg.get("scenario_seeds", [1, 2, 3])
    family_threshold = cfg.get("family_threshold", 0.35)
    algorithms = list(ALL_ALGORITHMS)
    if args.quick:
        scenario_seeds = scenario_seeds[:1]; algorithms = algorithms[:3]
        n_runs, pop, evals = 3, 40, 2000

    n_styles = cfg.get("n_styles", 1)
    objective_mode = cfg.get("objective_mode", "triobj")
    battery_mult = cfg.get("battery_mult", 1.0)
    global PROBLEMS
    print(f"[uav_sar] building {city} graph + {len(scenario_seeds)} scenarios "
          f"(n_styles={n_styles}, obj={objective_mode}, batt x{battery_mult}) ...", flush=True)
    PROBLEMS = _build_problems(city, scenario_seeds, sc_cfg["n_uav"], sc_cfg["n_targets"],
                               n_styles=n_styles, objective_mode=objective_mode,
                               battery_mult=battery_mult)
    scenarios = list(PROBLEMS.keys())

    tasks = [(s, a, ri, pop, evals, params)
             for s in scenarios for a in algorithms for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[uav_sar] {len(scenarios)} scenarios x {len(algorithms)} algos x {n_runs} "
          f"runs = {len(tasks)} tasks ({len(todo)} to run); pop={pop} evals={evals}", flush=True)

    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[uav_sar] phase-A done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)

    print("[uav_sar] phase-B: computing application metrics ...", flush=True)
    _phase_b_metrics(scenarios, algorithms, n_runs, family_threshold)
    print("[uav_sar] done.", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
