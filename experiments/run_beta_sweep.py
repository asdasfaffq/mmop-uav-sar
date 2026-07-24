"""Parameter-robustness sweep for the sparsity weight beta (the core hyperparameter),
on the VALIDATION subset only (MMF1/MMF2/MMF5), under the frozen protocol. Measures IGD
(convergence) and IGDX (decision-space) vs beta, to show the robustness/sensitivity of
the key knob and to back the beta=0.5 choice with data. Writes a CSV; the figure is made
by plotting/plot_beta_robustness.py.
"""
from __future__ import annotations
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import csv, sys, time
from multiprocessing import Pool
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from benchmarks import mmf
from baselines.baseline_registry import build
from metrics.indicators import igd, igdx
from utils.config import load_config
from utils.seeds import make_run_context

ROOT = Path(__file__).resolve().parent.parent
BETAS = [0.0, 0.25, 0.5, 1.0, 2.0]
PROBLEMS = ["MMF1", "MMF2", "MMF5"]
N_RUNS, POP, EVALS = 30, 200, 50000


def _one(task):
    beta, prob, ri, params = task
    p = mmf.make(prob); pf = p.pareto_front(1000); ps = p.pareto_set(2000)
    ctx = make_run_context(f"beta{beta}", prob, ri)
    a = build("EARS_MMOEA", problem=p, pop_size=POP, max_evaluations=EVALS,
              rng=ctx.rng, params={**params, "hybrid_beta": beta, "selection_mode": "hybrid"})
    res = a.run()
    return (beta, prob, ri, igd(pf, res.F), igdx(ps, res.X))


def main():
    params = load_config(ROOT / "configs/selected_params.yaml").get("ears_mmoea", {})
    tasks = [(b, pr, ri, params) for b in BETAS for pr in PROBLEMS for ri in range(N_RUNS)]
    print(f"[beta-sweep] {len(BETAS)} betas x {len(PROBLEMS)} problems x {N_RUNS} = {len(tasks)}", flush=True)
    out = []
    t0 = time.time()
    with Pool(processes=max(1, (os.cpu_count() or 2) - 2)) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, tasks), 1):
            out.append(r)
            if i % 50 == 0 or i == len(tasks):
                print(f"  {i}/{len(tasks)} ({time.time()-t0:.0f}s)", flush=True)
    f = ROOT / "results/summary/beta_sweep.csv"
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["beta", "problem", "run", "IGD", "IGDX"])
        w.writerows(out)
    print(f"[beta-sweep] wrote {f}")


if __name__ == "__main__":
    main()
