"""Transferability probe -- is the within-front placement a portable design rule?

The controlled-attribution results (`run_novelty.py`, `run_insort_sweep.py`) live
entirely inside EARS-MMOEA, so they can be read as an ablation of *our* framework
rather than as a statement about MMOEA selection in general. This experiment moves
the *same* sparsity signal S, in the *same* within-front placement, onto three
FOREIGN backbones and asks whether the benefit follows the placement:

  DN-NSGAII      (CEC 2016)  -- decision-space crowding, NSGA-II family
  OmniOptimizer  (EJOR 2008) -- fused objective+decision crowding, NSGA-II family
  MO_Ring_PSO_SCD(TEVC 2018) -- SCD + ring-topology PSO with an external archive
                                (a different search paradigm entirely)

For each backbone we compare its published diversity key `d` against
`d * (1 + beta * S)` -- nothing else changes: same backbone, same operators, same
budget, same algorithm-independent seed per run index (so the two arms are PAIRED
on identical initial populations), same frozen beta = EARS's `hybrid_beta`.

No per-backbone tuning of beta is performed. That is deliberately conservative: if
the rule transfers under EARS's own frozen beta, it is not a tuning artefact.

Usage:
  python experiments/run_transfer.py --config configs/benchmark.yaml \
      --params configs/selected_params.yaml
  python experiments/run_transfer.py --quick    # tiny smoke test
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
EXPERIMENT = "transfer"

# label -> (registry name, extra params). The label is what the statistics layer
# treats as the "algorithm"; the paired arms differ ONLY in the wf_sparsity switch.
VARIANTS: dict[str, tuple[str, dict]] = {
    "DN_NSGAII_base":  ("DN_NSGAII", {}),
    "DN_NSGAII_WFS":   ("DN_NSGAII", {"wf_sparsity": True}),
    "Omni_base":       ("OmniOptimizer", {}),
    "Omni_WFS":        ("OmniOptimizer", {"wf_sparsity": True}),
    "MORingPSO_base":  ("MO_Ring_PSO_SCD", {}),
    "MORingPSO_WFS":   ("MO_Ring_PSO_SCD", {"wf_sparsity": True}),
    # In-sort counterfactual: the SAME S, fused into a global key that overrides
    # front precedence. Only defined for the NSGA-II family -- MO_Ring_PSO_SCD's
    # external archive is a single non-dominated front, so "across front
    # boundaries" has no meaning there and no in-sort arm exists for it.
    "DN_NSGAII_INSORT": ("DN_NSGAII", {"insort_sparsity": True}),
    "Omni_INSORT":      ("OmniOptimizer", {"insort_sparsity": True}),
    # ... swept over the in-sort weight, mirroring `run_insort_sweep.py`. A single
    # in-sort point can be dismissed as set up to fail; the claim must hold for the
    # whole in-sort weight curve, not for one weight.
    # The grid is extended past the point where the in-sort curve stops improving:
    # in-sort quality rises monotonically up to lam=1, so a grid ending there would
    # invite "you did not sweep far enough". The curve must be shown to turn.
    **{f"DN_NSGAII_INSORT_lam{lam:g}": ("DN_NSGAII",
                                        {"insort_sparsity": True, "insort_beta": lam})
       for lam in (0.05, 0.1, 0.25, 1.0, 2.0, 4.0, 8.0, 16.0)},
    **{f"Omni_INSORT_lam{lam:g}": ("OmniOptimizer",
                                   {"insort_sparsity": True, "insort_beta": lam})
       for lam in (0.05, 0.1, 0.25, 1.0, 2.0, 4.0, 8.0, 16.0)},
}

# The in-sort weight grid actually run (0.5 is the `*_INSORT` arm above).
INSORT_LAMBDAS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)

# Paired arms for the statistics step (base, treated).
PAIRS = [
    ("DN_NSGAII_base", "DN_NSGAII_WFS"),
    ("Omni_base", "Omni_WFS"),
    ("MORingPSO_base", "MORingPSO_WFS"),
]

# Placement counterfactual: same signal, in-sort instead of within-front.
PAIRS_INSORT = [
    ("DN_NSGAII_base", "DN_NSGAII_INSORT"),
    ("Omni_base", "Omni_INSORT"),
]

# Head-to-head: within-front vs in-sort placement on the same backbone.
PAIRS_PLACEMENT = [
    ("DN_NSGAII_INSORT", "DN_NSGAII_WFS"),
    ("Omni_INSORT", "Omni_WFS"),
]


def _exists(label, problem, ri):
    return (RAW_DIR / EXPERIMENT / problem / label / f"run_{ri:03d}.json").exists()


def _run_one(task):
    label, problem, ri, pop, evals, params = task
    if _exists(label, problem, ri):
        return (label, problem, ri, "skip")
    try:
        algo_name, extra = VARIANTS[label]
        p = mmf.make(problem)
        ref_pf = p.pareto_front(1000)
        ref_ps = p.pareto_set(2000)
        ctx = make_run_context(problem, label, ri)
        run_params = {**params, **extra}
        a = build(algo_name, problem=p, pop_size=pop, max_evaluations=evals,
                  rng=ctx.rng, params=run_params)
        res = a.run()
        m = compute_all(p, res.X, res.F, rng=ctx.rng, ref_pf=ref_pf, ref_ps=ref_ps)
        save_run(EXPERIMENT, problem, label, ri, objectives=res.F, decisions=res.X,
                 metrics=m, seed=ctx.seed,
                 meta={"n_evaluations": int(res.n_evaluations),
                       "backbone": algo_name,
                       "hyperparams": {
                           "wf_sparsity": bool(extra.get("wf_sparsity", False)),
                           "insort_sparsity": bool(extra.get("insort_sparsity", False)),
                           "wf_beta": float(run_params.get("wf_beta")) if extra else None,
                           "wf_k": int(run_params.get("wf_k")) if extra else None,
                       }})
        return (label, problem, ri, "ok")
    except Exception as e:
        return (label, problem, ri, f"ERR:{type(e).__name__}:{e}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/benchmark.yaml")
    ap.add_argument("--params", default="configs/selected_params.yaml")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--quick", action="store_true",
                    help="tiny smoke run (2 problems, 2 runs, small budget)")
    args = ap.parse_args(argv)

    cfg = load_config(ROOT / args.config)
    params = dict(load_config(ROOT / args.params).get("ears_mmoea", {}))
    # The transferred term reuses EARS's frozen beta and k -- no re-tuning.
    params.setdefault("wf_beta", params.get("hybrid_beta", 0.5))
    params.setdefault("wf_k", 3)

    proto = cfg["protocol"]
    problems = list(mmf.MMF_NAMES)
    n_runs, pop, evals = proto["n_runs"], proto["pop_size"], proto["max_evaluations"]
    if args.quick:
        problems, n_runs, pop, evals = problems[:2], 2, 40, 2000

    tasks = [(lbl, pr, ri, pop, evals, params)
             for pr in problems for lbl in VARIANTS for ri in range(n_runs)]
    todo = [t for t in tasks if not _exists(t[0], t[1], t[2])]
    print(f"[transfer] {len(VARIANTS)} arms x {len(problems)} problems x {n_runs} runs "
          f"= {len(tasks)} ({len(todo)} to run), beta={params['wf_beta']}", flush=True)

    t0 = time.time()
    done = 0
    errors = []
    with Pool(processes=args.workers) as pool:
        for r in pool.imap_unordered(_run_one, todo):
            done += 1
            if r[3].startswith("ERR"):
                errors.append(r)
            if done % 40 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"[transfer] done in {time.time()-t0:.0f}s; {len(errors)} errors", flush=True)
    for e in errors[:10]:
        print("  ERROR", e, flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
