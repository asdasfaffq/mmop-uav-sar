"""Controlled placement-isolation study (reviewer point 1).

The original novelty experiment compared a multiplicative within-front key, an
additive within-front key, a CPDEA-style penalised-density within-front key, and
no sparsity. It established that the within-front *form* (multiplicative vs
additive) does not matter, but it did NOT cleanly isolate *placement*: the
penalised variant used a different key AND was still applied within the splitting
front (front precedence preserved). This study fixes that.

It runs, on MMF1-8 under the frozen protocol, the SAME convergence-penalised
decision-density key in two placements:
  * `penalized_density`  -- within-front (front precedence preserved), and
  * `in_sort_density`    -- in-sort (the key decides survival globally, across
                            front boundaries; front precedence NOT preserved).
Holding the key fixed and moving only its placement isolates the placement effect.
We run each in two settings: the full EARS framework, and a MINIMAL skeleton with
the auxiliary modules (decision-mode archive, cross-mode mating, operator
portfolio, structure-family archive) turned off, so the effect is not an artefact
of those modules. For reference we also run the multiplicative within-front key
(EARS default) and no-sparsity in both settings.

Usage:
  python experiments/run_placement_isolation.py --params configs/selected_params.yaml
"""
from __future__ import annotations

import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks import mmf
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, hyperparam_stamp
from utils.seeds import make_run_context
from baselines.baseline_registry import build

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "placement_isolation"

# auxiliary modules off => minimal skeleton (equivalence selection + niching only)
_SKELETON = {"use_decision_mode_archive": False, "use_route_family_archive": False,
             "use_cross_mode_mating": False, "use_operator_portfolio": False}

VARIANTS = {
    # full framework
    "Full_within_mult":   {"selection_mode": "hybrid"},
    "Full_within_pen":    {"selection_mode": "penalized_density"},
    "Full_insort_pen":    {"selection_mode": "in_sort_density"},
    "Full_insort_pureS":  {"selection_mode": "in_sort_pure_s"},
    "Full_noS":           {"selection_mode": "equivalence"},
    # minimal skeleton (auxiliary modules off)
    "Skel_within_mult":   {**_SKELETON, "selection_mode": "hybrid"},
    "Skel_within_pen":    {**_SKELETON, "selection_mode": "penalized_density"},
    "Skel_insort_pen":    {**_SKELETON, "selection_mode": "in_sort_density"},
    "Skel_insort_pureS":  {**_SKELETON, "selection_mode": "in_sort_pure_s"},
    "Skel_noS":           {**_SKELETON, "selection_mode": "equivalence"},
}


def _exists(variant, problem, ri):
    return (RAW_DIR / EXPERIMENT / problem / variant / f"run_{ri:03d}.json").exists()


def _run_one(task):
    variant, problem, ri, pop, evals, params = task
    if _exists(variant, problem, ri):
        return (variant, problem, ri, "skip")
    try:
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(variant, problem, ri)
        a = build("EARS_MMOEA", problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params={**params, **VARIANTS[variant]})
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, variant, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed, meta=hyperparam_stamp(params))
        return (variant, problem, ri, "ok")
    except Exception as e:
        return (variant, problem, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    problems = list(mmf.MMF_NAMES)
    proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    variants = list(VARIANTS)
    if args.quick:
        problems = problems[:2]; n_runs, pop, evals = 2, 40, 1500

    tasks = [(v, prob, ri, pop, evals, params)
             for prob in problems for v in variants for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[isolation] {len(variants)} variants x {len(problems)} problems x {n_runs} "
          f"= {len(tasks)} ({len(todo)} to run)", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[isolation] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
