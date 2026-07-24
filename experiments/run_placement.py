"""Phase 11 -- multi-facility emergency-station placement MMOP over a real OSM city.

A genuinely-multimodal real-world application: many geographically-distinct station
layouts achieve near-identical (mean, max) access, so the goal is to find multiple
Pareto-equivalent placement families -- the decision-space multimodality EARS targets.

Runs EARS + 5 baselines on several placement instances (different demand samples on
the same real city), 30 runs each, then computes objective- and decision-space
metrics against per-instance combined reference front/set. Same format as the other
experiments, so run_statistics.py works.

Usage:
  python experiments/run_placement.py --config configs/placement.yaml \
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

from applications.app_metrics import (combined_reference_front, canonical_nd_placements,
                                      compute_placement_metrics)
from applications.osm_graph_builder import build_flight_graph
from applications.placement_problem import FacilityPlacementProblem
from baselines.baseline_registry import ALL_ALGORITHMS, build
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, load_run, hyperparam_stamp
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "placement"
PROBLEMS: dict = {}


def _build_problems(city, instance_seeds, n_stations, n_demand):
    fg = build_flight_graph(city)
    return {f"{city}_p{sd}": FacilityPlacementProblem(fg, n_stations=n_stations,
                                                      n_demand=n_demand, seed=sd)
            for sd in instance_seeds}


def _exists(inst, algo, ri):
    return (RAW_DIR / EXPERIMENT / inst / algo / f"run_{ri:03d}.json").exists()


def _run_one(task):
    inst, algo, ri, pop, evals, params = task
    if _exists(inst, algo, ri):
        return (inst, algo, ri, "skip")
    try:
        prob = PROBLEMS[inst]
        ctx = make_run_context(inst, algo, ri)
        a = build(algo, problem=prob, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params=params)
        res = a.run()
        save_run(EXPERIMENT, inst, algo, ri, objectives=res.F, decisions=res.X,
                 metrics={"n": len(res.X)}, seed=ctx.seed,
                 meta=hyperparam_stamp(params) if algo == "EARS_MMOEA" else None)
        return (inst, algo, ri, "ok")
    except Exception as e:
        return (inst, algo, ri, f"ERR:{type(e).__name__}:{e}")


def _phase_b(instances, algorithms, n_runs):
    for inst in instances:
        prob = PROBLEMS[inst]
        allF, allPS = [], []
        for algo in algorithms:
            for ri in range(n_runs):
                jp = RAW_DIR / EXPERIMENT / inst / algo / f"run_{ri:03d}.json"
                if not jp.exists():
                    continue
                rec = load_run(jp); F = rec["arrays"]["objectives"]; X = rec["arrays"]["decisions"]
                allF.append(F); allPS.append(canonical_nd_placements(prob, X, F))
        ref = combined_reference_front(np.vstack(allF)) if allF else None
        refPS = np.vstack(allPS) if allPS else None
        if refPS is not None and len(refPS) > 800:
            refPS = refPS[np.random.default_rng(0).choice(len(refPS), 800, replace=False)]
        for algo in algorithms:
            for ri in range(n_runs):
                jp = RAW_DIR / EXPERIMENT / inst / algo / f"run_{ri:03d}.json"
                if not jp.exists():
                    continue
                rec = load_run(jp); X = rec["arrays"]["decisions"]; F = rec["arrays"]["objectives"]
                m = compute_placement_metrics(prob, X, F, ref, refPS)
                meta = json.loads(jp.read_text()); meta["metrics"] = {k: float(v) for k, v in m.items()}
                jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/placement.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--city", default=None,
                    help="override OSM city (else config osm.city)")
    ap.add_argument("--experiment", default=None,
                    help="override experiment/raw-dir name (else 'placement')")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    global EXPERIMENT
    if args.experiment:
        EXPERIMENT = args.experiment

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    city = args.city or cfg["osm"]["city"]; proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    instance_seeds = cfg.get("instance_seeds", [11, 22, 33])
    algorithms = list(ALL_ALGORITHMS)
    if args.quick:
        instance_seeds = instance_seeds[:1]; algorithms = algorithms[:3]; n_runs, pop, evals = 3, 40, 2000

    global PROBLEMS
    print(f"[placement] building {city} + {len(instance_seeds)} instances "
          f"(K={cfg['n_stations']}, M={cfg['n_demand']}) ...", flush=True)
    PROBLEMS = _build_problems(city, instance_seeds, cfg["n_stations"], cfg["n_demand"])
    instances = list(PROBLEMS.keys())

    tasks = [(s, a, ri, pop, evals, params)
             for s in instances for a in algorithms for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[placement] {len(instances)} instances x {len(algorithms)} algos x {n_runs} "
          f"runs = {len(tasks)} ({len(todo)} to run)", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[placement] phase-A done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    print("[placement] phase-B: metrics ...", flush=True)
    _phase_b(instances, algorithms, n_runs)
    print("[placement] done.", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
