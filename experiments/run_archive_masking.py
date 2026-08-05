"""Causal test of the archive-masking mechanism, inside EARS.

The extended in-sort sweep showed that within EARS a large, swept in-sort weight matches
the within-front key on IGDX and beats it on IGD -- while on archive-free backbones the
in-sort key never catches up at any weight. We attributed the difference to EARS
reporting the non-dominated union of population + archives, so the Pareto archive retains
converged solutions and masks the convergence damage the in-sort key inflicts.

That attribution is currently a CROSS-SETTING inference: it confounds "has an archive"
with "is a different algorithm". This experiment removes the confound by toggling only
the reporting inside EARS, holding the algorithm, operators, budget and seeds fixed:

  report = population + archives   (default, as reported everywhere else)
  report = population only         (archives excluded from the reported set)

Prediction if the mechanism is real: with the archives excluded, the in-sort key's
recovery at large lambda should disappear, while the within-front key should be
comparatively unaffected (it never relied on the repair).

Usage:
  python experiments/run_archive_masking.py
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baselines.baseline_registry import build
from benchmarks import mmf
from metrics.indicators import compute_all
from utils.config import load_config
from utils.io_utils import RAW_DIR, save_run
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT = "archive_masking"

# Within-front at its frozen default, and in-sort at the weight where it recovered.
_ARMS = {
    "WF_arch":       {"selection_mode": "hybrid"},
    "WF_pop":        {"selection_mode": "hybrid", "report_population_only": True},
    "InSort8_arch":  {"selection_mode": "in_sort_pure_s", "hybrid_beta": 8.0},
    "InSort8_pop":   {"selection_mode": "in_sort_pure_s", "hybrid_beta": 8.0,
                      "report_population_only": True},
    "NoS_arch":      {"selection_mode": "equivalence"},
    "NoS_pop":       {"selection_mode": "equivalence", "report_population_only": True},
}

PAIRS = [("WF_pop", "InSort8_pop"), ("WF_arch", "InSort8_arch")]


def _exists(a, p, ri):
    return (RAW_DIR / EXPERIMENT / p / a / f"run_{ri:03d}.json").exists()


def _run_one(task):
    arm, problem, ri, pop, evals, params = task
    if _exists(arm, problem, ri):
        return (arm, problem, ri, "skip")
    try:
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000); ref_ps = p.pareto_set(2000)
        ctx = make_run_context(problem, arm, ri)
        a = build("EARS_MMOEA", problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params={**params, **_ARMS[arm]})
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, arm, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed,
                 meta={"n_evaluations": int(res.n_evaluations),
                       "hyperparams": dict(_ARMS[arm])})
        return (arm, problem, ri, "ok")
    except Exception as e:
        return (arm, problem, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = dict(load_config(ROOT / args.params).get("ears_mmoea", {}))
    proto = cfg["protocol"]
    problems = list(mmf.MMF_NAMES)
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]

    tasks = [(a, pr, ri, pop, evals, params)
             for pr in problems for a in _ARMS for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[archive_masking] {len(_ARMS)} arms x {len(problems)} x {n_runs} "
          f"= {len(tasks)} ({len(todo)} to run)", flush=True)

    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 40 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[archive_masking] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
