"""In-sort weight sweep for the placement-isolation claim (reviewer: the single
in-sort point may look 'set up to fail'). We sweep the weight lambda of the pure-S
in-sort fusion (score = -conv + lambda*S) over a grid and compare the whole in-sort
IGD-IGDX trade-off curve against the within-front variants, on MMF1-8 under the
frozen protocol. If the within-front points dominate the in-sort curve for every
lambda, the placement claim is robust to the in-sort weight (not a strawman).

Variants (full framework, only the splitting-front / sort key changes):
  WF_mult, WF_add, NoS            -- within-front references (S out of the sort)
  InSort_lam{0.05..1.0}           -- pure-S in the sort at increasing weight
Also includes a lexicographic rank->E->S key (S strictly after convergence, still
out of the dominance sort) as an additional within-front reference point.

Usage: python experiments/run_insort_sweep.py --params configs/selected_params.yaml
"""
from __future__ import annotations
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse, sys, time
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
EXPERIMENT = "insort_sweep"

VARIANTS = {
    "WF_mult": {"selection_mode": "hybrid"},
    "WF_add":  {"selection_mode": "hybrid_additive"},
    "NoS":     {"selection_mode": "equivalence"},
    "InSort_lam0.05": {"selection_mode": "in_sort_pure_s", "hybrid_beta": 0.05},
    "InSort_lam0.10": {"selection_mode": "in_sort_pure_s", "hybrid_beta": 0.10},
    "InSort_lam0.25": {"selection_mode": "in_sort_pure_s", "hybrid_beta": 0.25},
    "InSort_lam0.50": {"selection_mode": "in_sort_pure_s", "hybrid_beta": 0.50},
    "InSort_lam1.00": {"selection_mode": "in_sort_pure_s", "hybrid_beta": 1.00},
}


def _exists(v, p, ri):
    return (RAW_DIR / EXPERIMENT / p / v / f"run_{ri:03d}.json").exists()


def _run_one(task):
    v, problem, ri, pop, evals, params = task
    if _exists(v, problem, ri):
        return (v, problem, ri, "skip")
    try:
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(v, problem, ri)
        a = build("EARS_MMOEA", problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params={**params, **VARIANTS[v]})
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, v, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed, meta=hyperparam_stamp(params))
        return (v, problem, ri, "ok")
    except Exception as e:
        return (v, problem, ri, f"ERR:{type(e).__name__}:{e}")


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
    proto = cfg["protocol"]; n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    variants = list(VARIANTS)
    if args.quick:
        problems = problems[:2]; n_runs, pop, evals = 2, 40, 1500
    tasks = [(v, prob, ri, pop, evals, params)
             for prob in problems for v in variants for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[insort_sweep] {len(variants)} variants x {len(problems)} x {n_runs} = {len(tasks)} "
          f"({len(todo)} to run)", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[insort_sweep] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
