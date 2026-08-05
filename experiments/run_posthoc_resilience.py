"""Post-hoc constraint resilience: does a portfolio of layouts actually help?

The paper's motivation is that a planner who loses a site, or is refused a district,
should be able to switch to another already-computed layout instead of re-running the
study. That motivation has never been tested. This experiment tests it directly, using
ONLY the layouts each algorithm already returned -- no re-optimization is permitted,
which is the entire point.

Protocol
--------
For each city instance and each optimisation run, we draw S post-hoc scenarios that
were NOT visible during optimisation. Each scenario forbids a region of the map:

  site      -- a disk of radius r around a random point (a parcel becomes unavailable)
  district  -- a rectangular cell of the city grid (an administrative refusal)

A returned layout survives a scenario iff none of its K stations lies in the forbidden
region. For each algorithm we then ask:

  recovery        -- did at least one returned layout survive? (no re-run needed)
  n_feasible      -- how many survived
  regret          -- how much mean-access is lost by the best surviving layout,
                     relative to the best layout before the constraint appeared

Fairness
--------
* Scenarios depend only on (instance, run index, scenario index) -- never on the
  algorithm -- so every algorithm faces exactly the same constraints.
* Output-set size is a confound: an algorithm returning more layouts has more chances
  to survive. Six of the seven algorithms return the same 120 layouts; MO_Ring_PSO_SCD
  returns fewer. We therefore report the set size alongside, and additionally report a
  size-controlled variant in which every algorithm is subsampled to the smallest set
  available for that (instance, run).
* The regret baseline is the best pre-constraint layout of the SAME algorithm, so the
  metric asks what the portfolio adds, not which algorithm converged better.

Usage: python experiments/run_posthoc_resilience.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.io_utils import RAW_DIR, STATS_DIR  # noqa: E402

EXP = "placement"
ALGOS = ["EARS_MMOEA", "CPDEA", "DN_NSGAII", "MMEA_WI", "MO_Ring_PSO_SCD",
         "OmniOptimizer", "HREA", "NSGAII"]   # NSGAII = non-multimodal control
N_SCEN = 100
GLOBAL_SEED = 20260804


def scenario_rng(instance: str, run: int, scen: int) -> np.random.Generator:
    """Algorithm-independent scenario stream (mirrors utils.seeds' fairness rule)."""
    import hashlib
    key = f"{GLOBAL_SEED}|{instance}|{run}|{scen}".encode()
    return np.random.default_rng(int.from_bytes(hashlib.sha256(key).digest()[:4], "big"))


def load_run(instance: str, algo: str, run: int):
    npz = RAW_DIR / EXP / instance / algo / f"run_{run:03d}.npz"
    if not npz.exists():
        return None, None
    d = np.load(npz)
    return d["decisions"], d["objectives"]


def stations_of(X: np.ndarray, K: int) -> np.ndarray:
    """(n, K, 2) station coordinates in the normalised [0,1] decision encoding."""
    return np.clip(X, 0, 1).reshape(len(X), K, 2)


def make_scenario(rng, kind: str):
    """Return a predicate mask function over stations in normalised [0,1]^2."""
    if kind == "site":
        c = rng.uniform(0.15, 0.85, size=2)
        r = rng.uniform(0.06, 0.12)          # ~6-12% of the city extent
        return lambda S: (np.linalg.norm(S - c, axis=2) < r)
    # district: one cell of a 4x4 grid
    gi, gj = rng.integers(0, 4), rng.integers(0, 4)
    lo = np.array([gi / 4, gj / 4]); hi = lo + 0.25
    return lambda S: np.all((S >= lo) & (S <= hi), axis=2)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--scenarios", type=int, default=N_SCEN)
    args = ap.parse_args(argv)

    instances = sorted(p.name for p in (RAW_DIR / EXP).iterdir() if p.is_dir())
    rows = []
    for inst in instances:
        for run in range(args.runs):
            # cache every algorithm's layouts for this run
            data = {}
            for a in ALGOS:
                X, F = load_run(inst, a, run)
                if X is not None:
                    data[a] = (X, F)
            if not data:
                continue
            K = next(iter(data.values()))[0].shape[1] // 2
            min_size = min(len(X) for X, _ in data.values())

            for s in range(args.scenarios):
                rng = scenario_rng(inst, run, s)
                kind = "site" if s % 2 == 0 else "district"
                hits = make_scenario(rng, kind)
                for a, (X, F) in data.items():
                    S = stations_of(X, K)
                    bad = hits(S).any(axis=1)              # layout loses any station
                    ok = ~bad
                    base = F[:, 0].min()                   # best pre-constraint mean access
                    # ABSOLUTE post-constraint quality. Regret relative to an algorithm's
                    # own baseline is misleading when the baselines differ in quality: a
                    # method whose layouts are uniformly poor shows small "regret" while
                    # delivering a worse service level. We record both.
                    if ok.any():
                        best_after = float(F[ok, 0].min())
                        regret = (best_after - base) / base * 100.0
                    else:
                        best_after, regret = np.nan, np.nan
                    # size-controlled: same scenario, first min_size layouts only
                    okc = ok[:min_size]
                    rows.append({
                        "instance": inst, "run": run, "scenario": s, "kind": kind,
                        "algo": a, "set_size": int(len(X)),
                        "recovered": int(ok.any()), "n_feasible": int(ok.sum()),
                        "regret_pct": regret,
                        "mean_access_before": float(base),
                        "mean_access_after": best_after,
                        "recovered_ctrl": int(okc.any()),
                        "n_feasible_ctrl": int(okc.sum()),
                    })

    import pandas as pd
    df = pd.DataFrame(rows)
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    out = STATS_DIR / "posthoc_resilience_raw.csv"
    df.to_csv(out, index=False)

    agg = df.groupby("algo").agg(
        set_size=("set_size", "median"),
        recovery=("recovered", "mean"),
        recovery_ctrl=("recovered_ctrl", "mean"),
        n_feasible=("n_feasible", "median"),
        regret_pct=("regret_pct", "mean"),
        access_before=("mean_access_before", "mean"),
        access_after=("mean_access_after", "mean"),
    ).sort_values("recovery", ascending=False)
    agg["recovery"] *= 100; agg["recovery_ctrl"] *= 100
    agg.to_csv(STATS_DIR / "posthoc_resilience_summary.csv")

    print(f"scenarios: {args.scenarios} per run x {args.runs} runs x {len(instances)} instances")
    print(f"rows: {len(df)}  ->  {out}\n")
    print(agg.to_string(float_format=lambda x: f"{x:.2f}"))
    print("\nBy scenario kind (recovery %):")
    print((df.groupby(["algo", "kind"])["recovered"].mean() * 100)
          .unstack().round(2).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
