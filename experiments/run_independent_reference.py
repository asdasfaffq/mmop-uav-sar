"""Build an INDEPENDENT high-budget reference set for the placement case study.

Current weakness (disclosed in the manuscript): the real-city IGD/IGDX/HV reference is the
non-dominated union of the compared algorithms' own outputs, so every scored algorithm also
contributes to the yardstick it is scored against. That is a self-inclusive reference and it
can flatter contributors.

This script removes the confound. For each city instance it runs a small panel of methods at
a MUCH larger budget and with seeds drawn from a different stream than the evaluation runs,
then stores the non-dominated union of those high-budget runs as a fixed reference. The
evaluation runs are then scored against a yardstick that none of them contributed to.

The reference panel deliberately includes methods with different search biases so the
reference is not shaped by one algorithm's blind spots.

Outputs: results/reference/<experiment>/<instance>.npz  with arrays `F` and `PS`.

Usage:
  python experiments/run_independent_reference.py
  python experiments/run_independent_reference.py --budget-mult 5 --seeds 3
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from applications.app_metrics import canonical_nd_placements, combined_reference_front  # noqa: E402
from baselines.baseline_registry import build  # noqa: E402
from experiments.run_placement import _build_problems  # noqa: E402
from utils.config import load_config  # noqa: E402

# Different search biases, so the reference is not shaped by one method's blind spots.
PANEL = ["EARS_MMOEA", "HREA", "OmniOptimizer", "MO_Ring_PSO_SCD"]
# Seed stream deliberately disjoint from utils.seeds.GLOBAL_SEED (20260616).
REF_SEED = 90210077

CITIES = [("Macau", "placement"), ("Guangzhou", "placement_guangzhou"),
          ("Shenzhen", "placement_shenzhen"),
          ("SanFrancisco", "placement_sanfrancisco"),
          ("HongKong", "placement_hongkong")]


def ref_rng(inst: str, algo: str, k: int) -> np.random.Generator:
    key = f"{REF_SEED}|{inst}|{algo}|{k}".encode()
    return np.random.default_rng(int.from_bytes(hashlib.sha256(key).digest()[:4], "big"))


def _one(task):
    city, exp, inst, algo, k, pop, evals, params = task
    try:
        prob = _PROBLEMS[exp][inst]
        a = build(algo, problem=prob, pop_size=pop, max_evaluations=evals,
                  rng=ref_rng(inst, algo, k), params=params)
        res = a.run()
        return (exp, inst, res.F, canonical_nd_placements(prob, res.X, res.F), None)
    except Exception as e:
        return (exp, inst, None, None, f"{type(e).__name__}: {e}")


_PROBLEMS: dict = {}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/placement.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--budget-mult", type=int, default=5)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    proto = cfg["protocol"]
    pop = proto["pop_size"]
    evals = proto["max_evaluations"] * args.budget_mult
    instance_seeds = cfg.get("instance_seeds", [11, 22, 33])

    tasks = []
    for city, exp in CITIES:
        print(f"[ref] building {city} ...", flush=True)
        _PROBLEMS[exp] = _build_problems(city, instance_seeds, cfg["n_stations"],
                                         cfg["n_demand"])
        for inst in _PROBLEMS[exp]:
            for algo in PANEL:
                for k in range(args.seeds):
                    tasks.append((city, exp, inst, algo, k, pop, evals, params))

    print(f"[ref] {len(tasks)} high-budget runs "
          f"({args.budget_mult}x budget = {evals} evals, {args.seeds} seeds x {len(PANEL)} methods)",
          flush=True)

    acc: dict = {}
    t0 = time.time(); done = 0; errs = []
    with Pool(processes=args.workers) as pool:
        for exp, inst, F, PS, err in pool.imap_unordered(_one, tasks):
            done += 1
            if err:
                errs.append((exp, inst, err))
            else:
                acc.setdefault((exp, inst), ([], []))
                acc[(exp, inst)][0].append(F); acc[(exp, inst)][1].append(PS)
            if done % 20 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} ({time.time()-t0:.0f}s)", flush=True)

    outdir = ROOT / "results/reference"
    for (exp, inst), (Fs, PSs) in acc.items():
        d = outdir / exp; d.mkdir(parents=True, exist_ok=True)
        ref = combined_reference_front(np.vstack(Fs))
        refPS = np.vstack(PSs)
        if len(refPS) > 800:
            refPS = refPS[np.random.default_rng(0).choice(len(refPS), 800, replace=False)]
        np.savez_compressed(d / f"{inst}.npz", F=ref, PS=refPS)
        print(f"  [ok] {exp}/{inst}: ref |F|={len(ref)} |PS|={len(refPS)}")

    print(f"[ref] done in {time.time()-t0:.0f}s; {len(errs)} errors", flush=True)
    for e in errs[:5]:
        print("  ERROR", e, flush=True)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
