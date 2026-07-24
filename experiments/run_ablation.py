"""Phase 9 -- ablation study of EARS-MMOEA.

Runs ablated variants (A0..A8) under the SAME frozen params and SHARED protocol,
so the contribution of each module is isolated. Each variant is persisted as a
distinct "algorithm" under experiment='ablation', then compared with
run_statistics.py (reference = A0_Full).

Honest note: on the unconstrained MMF benchmark, A2 (no route-family archive) and
A6 (no constraint-aware selection) are expected to be ~neutral -- those modules act
on the UAV application (route families) and on constrained problems. Their real
ablation is in Phase 10. They are still run here for completeness and the neutrality
is reported, not hidden.

Usage:
  python experiments/run_ablation.py --config configs/benchmark.yaml \
      --params configs/selected_params.yaml
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
EXPERIMENT = "ablation"

# variant -> extra flags merged onto the frozen EARS params
VARIANTS = {
    "A0_Full":            {},
    "A1_noDMArchive":     {"use_decision_mode_archive": False},
    "A2_noRouteFamily":   {"use_route_family_archive": False},
    "A3_noEquivFitness":  {"use_equivalence_fitness": False},
    "A4_noNiching":       {"use_adaptive_niching": False},
    "A5_noCrossMode":     {"use_cross_mode_mating": False},
    "A6_noConstraintAware": {"use_constraint_aware": False},
    "A7_noPortfolio":     {"use_operator_portfolio": False},
    "A8_BackboneOnly":    {"backbone_only": True},
    # A9 isolates the Phase-8 hybrid contribution: revert the diversity key from
    # hybrid (equivalence x decision-sparsity) back to plain equivalence selection.
    "A9_noSparsityBonus": {"selection_mode": "equivalence"},
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
        ctx = make_run_context(problem, variant, ri)
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
        problems = problems[:2]; variants = variants[:3]; n_runs, pop, evals = 2, 40, 1500

    tasks = [(v, prob, ri, pop, evals, params)
             for prob in problems for v in variants for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[ablation] {len(variants)} variants x {len(problems)} problems x {n_runs} runs "
          f"= {len(tasks)} tasks ({len(todo)} to run); workers={args.workers}", flush=True)

    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[ablation] finished in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:20]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
