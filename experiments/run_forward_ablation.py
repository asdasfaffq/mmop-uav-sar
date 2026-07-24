"""Forward (constructive) ablation of EARS-MMOEA.

Complements the subtractive ablation (run_ablation.py, full-minus-one-module) with
a constructive ladder: starting from an NSGA-II-like base, each rung ADDS exactly
one capability, so the reader sees where performance comes from rather than only
which removals hurt. This answers the "kitchen-sink / module-stacking" concern
directly: it shows the gain is concentrated in the core selection idea (the
equivalence key E and the within-front sparsity S), with the auxiliary modules
contributing little on the unconstrained benchmark (they act on the constrained
application).

Endpoints are internal consistency checks: F0_NSGAII reproduces the subtractive
A8 (backbone-only) and F5_Full reproduces A0 (full), under the same frozen params
and shared protocol.

Usage:
  python experiments/run_forward_ablation.py --config configs/benchmark.yaml \
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
EXPERIMENT = "forward_ablation"

# Constructive ladder: each rung adds ONE capability onto the previous.
# Modules not yet added are explicitly disabled; everything else takes the frozen
# default. selection_mode "equivalence" = D=E (no within-front sparsity S);
# "hybrid" = D=E(1+beta*S) (adds the within-front sparsity term).
_OFF_ARCH = {"use_decision_mode_archive": False}
_OFF_XMODE = {"use_cross_mode_mating": False}
_OFF_PORT = {"use_operator_portfolio": False}
FORWARD = {
    # F0: no equivalence key, no niching, no archives/cross-mode/portfolio -> NSGA-II-like
    "F0_NSGAII": {"use_equivalence_fitness": False, "use_adaptive_niching": False,
                  **_OFF_ARCH, **_OFF_XMODE, **_OFF_PORT, "selection_mode": "equivalence"},
    # F1: + equivalence key E (SCD x niche rarity); still no within-front S
    "F1_plusE": {**_OFF_ARCH, **_OFF_XMODE, **_OFF_PORT, "selection_mode": "equivalence"},
    # F2: + within-front sparsity S -> the core selection mechanism D=E(1+beta*S)
    "F2_plusS_core": {**_OFF_ARCH, **_OFF_XMODE, **_OFF_PORT, "selection_mode": "hybrid"},
    # F3: + operator portfolio (bandit)
    "F3_plusPortfolio": {**_OFF_ARCH, **_OFF_XMODE, "selection_mode": "hybrid"},
    # F4: + cross-mode mating
    "F4_plusCrossMode": {**_OFF_ARCH, "selection_mode": "hybrid"},
    # F5: + decision-mode archive = full EARS (= A0)
    "F5_Full": {},
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
                  rng=ctx.rng, params={**params, **FORWARD[variant]})
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
    variants = list(FORWARD)
    if args.quick:
        problems = problems[:2]; n_runs, pop, evals = 2, 40, 1500

    tasks = [(v, prob, ri, pop, evals, params)
             for prob in problems for v in variants for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[forward] {len(variants)} variants x {len(problems)} problems x {n_runs} runs "
          f"= {len(tasks)} tasks ({len(todo)} to run); workers={args.workers}", flush=True)

    t0 = time.time(); done = 0; errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[forward] finished in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:20]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
