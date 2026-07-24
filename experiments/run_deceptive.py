"""Extended-suite benchmark: the CEC2019/2020 MMO competition members
(MMF9, SYM-PART, SYM-PART rotated, Omni-test) under the IDENTICAL frozen protocol
as the MMF1-8 core (6 algorithms, 30 runs, 50k evals, pop 200). Same output format
as run_benchmark.py, so run_statistics.py works unchanged.

Usage:
  python experiments/run_benchmark_ext.py --config configs/benchmark.yaml \
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

from benchmarks import extended
from baselines.baseline_registry import ALL_ALGORITHMS, build
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, hyperparam_stamp
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "deceptive"


def _exists(problem, algo, ri):
    return (RAW_DIR / EXPERIMENT / problem / algo / f"run_{ri:03d}.json").exists()


def _run_one(task):
    problem, algo, ri, pop, evals, params = task
    if _exists(problem, algo, ri):
        return (problem, algo, ri, "skip")
    try:
        p = extended.make(problem)
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
        return (problem, algo, ri, "ok")
    except Exception as e:
        return (problem, algo, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    problems = ["MMF10", "MMF11", "MMF12"]  # deceptive scalable MMF10-12
    algorithms = list(ALL_ALGORITHMS)
    proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    if args.quick:
        problems = problems[:2]; algorithms = algorithms[:3]; n_runs, pop, evals = 2, 40, 2000

    tasks = [(pr, a, ri, pop, evals, params)
             for pr in problems for a in algorithms for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[benchmark_ext] {len(problems)} problems x {len(algorithms)} algos x {n_runs} "
          f"= {len(tasks)} ({len(todo)} to run); pop={pop} evals={evals}", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[benchmark_ext] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
