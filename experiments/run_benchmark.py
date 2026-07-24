"""Phase 7 -- formal benchmark comparison.

Runs every algorithm on every MMF problem for n_runs independent runs under the
SHARED protocol (identical pop size, evaluation budget, and algorithm-independent
seeds), computes all 8 indicators per run, and persists raw results. Statistics
and figures are produced by run_statistics.py / plotting/*.

Parallelism: tasks (problem, algorithm, run) are embarrassingly parallel because
seeds depend only on (problem, run). A process pool runs them; each worker is
single-threaded (env set below, before numpy import) to avoid BLAS oversubscription.

Resumable: a task whose result json already exists is skipped, so the study can be
stopped and restarted.

Usage:
  python experiments/run_benchmark.py --config configs/benchmark.yaml \
      --params configs/selected_params.yaml
  python experiments/run_benchmark.py ... --quick   # tiny smoke
"""
from __future__ import annotations

import os

# single-threaded workers (must be set before numpy/BLAS import)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from baselines.baseline_registry import ALL_ALGORITHMS, build
from benchmarks import mmf
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, hyperparam_stamp
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "benchmark"


def _result_exists(problem, algo, ri):
    return (RAW_DIR / EXPERIMENT / problem / algo / f"run_{ri:03d}.json").exists()


def _run_one(task):
    problem, algo, ri, pop, evals, params = task
    if _result_exists(problem, algo, ri):
        return (problem, algo, ri, "skip", 0.0)
    t0 = time.time()
    try:
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(problem, algo, ri)
        a = build(algo, problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params=params)
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, algo, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed,
                 meta={"n_evaluations": int(res.n_evaluations),
                       **(hyperparam_stamp(params) if algo == "EARS_MMOEA" else {})})
        return (problem, algo, ri, "ok", time.time() - t0)
    except Exception as e:  # never let one run kill the pool
        return (problem, algo, ri, f"ERR:{type(e).__name__}:{e}", time.time() - t0)


def build_tasks(problems, algorithms, n_runs, pop, evals, params):
    tasks = []
    for prob in problems:
        for algo in algorithms:
            for ri in range(n_runs):
                tasks.append((prob, algo, ri, pop, evals, params))
    return tasks


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    problems = list(mmf.MMF_NAMES)                      # MMF1..MMF8
    algorithms = list(ALL_ALGORITHMS)
    proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]

    if args.quick:
        problems = problems[:2]; algorithms = algorithms[:3]
        n_runs, pop, evals = 2, 40, 2000

    tasks = build_tasks(problems, algorithms, n_runs, pop, evals, params)
    todo = [t for t in tasks if not _result_exists(t[0], t[1], t[2])]
    print(f"[benchmark] {len(problems)} problems x {len(algorithms)} algos x {n_runs} runs "
          f"= {len(tasks)} tasks ({len(tasks)-len(todo)} already done, {len(todo)} to run); "
          f"pop={pop} evals={evals} workers={args.workers}", flush=True)

    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for (prob, algo, ri, status, dt) in pool.imap_unordered(_run_one, todo):
            done += 1
            if status.startswith("ERR"):
                errors.append((prob, algo, ri, status))
            if done % 25 == 0 or done == len(todo):
                el = time.time() - t0
                print(f"  {done}/{len(todo)} done ({el:.0f}s, ~{el/max(done,1):.1f}s/task)",
                      flush=True)
    print(f"[benchmark] finished in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:20]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
