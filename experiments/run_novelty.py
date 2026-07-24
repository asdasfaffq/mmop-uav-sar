"""Controlled novelty experiment (reviewer R1.1 / checklist-3): isolate whether the
*multiplicative within-front placement* of the decision-space sparsity S carries unique
benefit, holding the equivalence key E and the sparsity S fixed. Four EARS variants that
differ ONLY in how/where S enters selection:

  Mult_within  : D = E*(1+beta*S)      -- the proposed key (= A0_Full)
  Add_within   : D = E + beta*med(E)*S -- same E, same S, ADDITIVE within-front form
  Penalized    : S folded into a convergence-penalised density (S influences the key
                 as a penalty, i.e. closer to fusing it into the fitness/sort)
  NoS_equiv    : D = E                 -- sparsity removed (= A9)

Same frozen params and shared protocol as the benchmark. Output format matches the others.
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
from baselines.baseline_registry import build
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, hyperparam_stamp
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "novelty"
VARIANTS = {
    "Mult_within": {"selection_mode": "hybrid"},
    "Add_within":  {"selection_mode": "hybrid_additive"},
    "Penalized":   {"selection_mode": "penalized_density"},
    "NoS_equiv":   {"selection_mode": "equivalence"},
}


def _exists(v, problem, ri):
    return (RAW_DIR / EXPERIMENT / problem / v / f"run_{ri:03d}.json").exists()


def _run_one(task):
    v, problem, ri, pop, evals, params = task
    if _exists(v, problem, ri):
        return (v, problem, ri, "skip")
    try:
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(problem, v, ri)
        a = build("EARS_MMOEA", problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params={**params, **VARIANTS[v]})
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, v, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed,
                 meta={"n_evaluations": int(res.n_evaluations), **hyperparam_stamp(params)})
        return (v, problem, ri, "ok")
    except Exception as e:
        return (v, problem, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args(argv)
    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    problems = list(mmf.MMF_NAMES)
    proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    tasks = [(v, pr, ri, pop, evals, params)
             for pr in problems for v in VARIANTS for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[novelty] {len(VARIANTS)} variants x {len(problems)} problems x {n_runs} "
          f"= {len(tasks)} ({len(todo)} to run)", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 40 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[novelty] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
