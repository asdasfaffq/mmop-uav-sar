"""High-dimensional MMOP study: ScalableMMF2 at d in {5,10,30,50,100}.

Tests whether the decision-space-diversity machinery (kNN sparsity, silhouette
k-means niching) and the overall ranking survive as the decision dimension grows.
The problem keeps exactly two equivalent global Pareto sets at every d (analytic,
verified reference), so any change in IGDX/IGD with d reflects dimension, not a
change in problem structure. Same frozen protocol and all seven algorithms; the
evaluation budget is held fixed across d (identical for every algorithm at each d),
so no method is tuned per dimension.

Usage:
  python experiments/run_highdim.py --params configs/selected_params.yaml
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

from benchmarks import scalable
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run, hyperparam_stamp
from utils.seeds import make_run_context
from baselines.baseline_registry import build, ALL_ALGORITHMS

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "highdim"


def _exists(problem, algo, ri):
    return (RAW_DIR / EXPERIMENT / problem / algo / f"run_{ri:03d}.json").exists()


_FAMILIES = {"mmf2": (scalable.make, "ScalMMF2"), "dmp": (scalable.make_dmp, "ScalDMP")}


def _run_one(task):
    fam, d, algo, ri, pop, evals, params = task
    maker, prefix = _FAMILIES[fam]
    pname = f"{prefix}_d{d}"
    if _exists(pname, algo, ri):
        return (pname, algo, ri, "skip")
    try:
        p = maker(d)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(pname, algo, ri)
        a = build(algo, problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params=params)
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, pname, algo, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed,
                 meta={"n_evaluations": int(res.n_evaluations), "d": int(d),
                       **(hyperparam_stamp(params) if algo == "EARS_MMOEA" else {})})
        return (pname, algo, ri, "ok")
    except Exception as e:
        return (pname, algo, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = load_config(ROOT / args.params).get("ears_mmoea", {})
    dims = list(scalable.DIMS)
    algorithms = list(ALL_ALGORITHMS)
    proto = cfg["protocol"]
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    families = list(_FAMILIES)
    if args.quick:
        dims = [5, 100]; algorithms = algorithms[:3]; n_runs, pop, evals = 2, 40, 2000
        families = ["dmp"]

    tasks = [(fam, d, a, ri, pop, evals, params)
             for fam in families for d in dims for a in algorithms for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(f"{_FAMILIES[t[0]][1]}_d{t[1]}", t[2], t[3])]
    print(f"[highdim] {len(families)} families x {len(dims)} dims x {len(algorithms)} algos x "
          f"{n_runs} = {len(tasks)} ({len(todo)} to run); pop={pop} evals={evals}", flush=True)
    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[highdim] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
