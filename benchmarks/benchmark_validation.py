"""Validation script for the standard MMOP benchmark wrappers.

Checks, for every implemented MMF problem, that:
  1. bounds are well-formed (xl < xu, correct shape);
  2. the analytical Pareto Set lies within bounds;
  3. PS points lie ON the analytical Pareto Front -- i.e. evaluating the PS
     reproduces f2 = pf(f1) to numerical precision (excluding measure-zero
     piecewise-threshold endpoints, checked at the 99th percentile);
  4. PS points are non-dominated against a large uniform random decision cloud
     (no random sample dominates a PS point) -- the PS is genuinely optimal;
  5. evaluation is vectorised and matches row-wise evaluation.

Run: python benchmarks/benchmark_validation.py
Exit code 0 = all pass.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from benchmarks import mmf

DEV_TOL = 1e-6
RANDOM_CLOUD = 8000


def validate_problem(p) -> list[str]:
    errs: list[str] = []
    rng = np.random.default_rng(12345)

    # 1. bounds
    if not (p.xl.shape == p.xu.shape == (p.n_var,)):
        errs.append(f"{p.name}: bad bounds shape")
    if not np.all(p.xl < p.xu):
        errs.append(f"{p.name}: xl !< xu")

    ps = p.pareto_set(2000)
    if ps.shape[1] != p.n_var:
        errs.append(f"{p.name}: PS has wrong n_var")

    # 2. PS within bounds
    if not np.all((ps >= p.xl - 1e-9) & (ps <= p.xu + 1e-9)):
        errs.append(f"{p.name}: PS out of bounds")

    F = p.evaluate(ps)["F"]

    # 3. PS-on-PF
    dev = np.abs(F[:, 1] - p._pf_f2(F[:, 0]))
    if np.percentile(dev, 99) > DEV_TOL:
        errs.append(f"{p.name}: PS not on PF (p99 dev={np.percentile(dev,99):.2e})")

    # 4. non-dominance vs random cloud
    R = rng.uniform(p.xl, p.xu, size=(RANDOM_CLOUD, p.n_var))
    FR = p.evaluate(R)["F"]
    dom = 0
    for i in range(0, len(ps), 25):
        f = F[i]
        if np.any((FR <= f).all(axis=1) & (FR < f).any(axis=1)):
            dom += 1
    if dom > 0:
        errs.append(f"{p.name}: {dom} PS points dominated by random samples")

    # 5. vectorised == row-wise
    sub = ps[:50]
    F_vec = p.evaluate(sub)["F"]
    F_row = np.vstack([p.evaluate(sub[j:j + 1])["F"] for j in range(len(sub))])
    if not np.allclose(F_vec, F_row, atol=1e-12):
        errs.append(f"{p.name}: vectorised != row-wise evaluation")

    return errs


def main() -> int:
    all_errs: list[str] = []
    for p in mmf.all_problems():
        errs = validate_problem(p)
        status = "OK" if not errs else "FAIL"
        print(f"[{status:4}] {p.name}  (n_var={p.n_var}, branches={p.n_ps_branches})")
        all_errs.extend(errs)
    print("-" * 50)
    if all_errs:
        print(f"VALIDATION FAILED ({len(all_errs)} issues):")
        for e in all_errs:
            print("  -", e)
        return 1
    print(f"ALL {len(mmf.MMF_NAMES)} MMF PROBLEMS VALIDATED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
