"""Phase 4: all 6 algorithms share one interface, respect the shared budget,
and emit the same Result format (fairness is structural, not assumed)."""
from __future__ import annotations

import warnings

import numpy as np
import pytest

from algorithms.base import Result
from baselines.baseline_registry import ALL_ALGORITHMS, build
from benchmarks import mmf
from utils.seeds import make_run_context

POP, BUDGET = 24, 600  # tiny: just exercise the interface


@pytest.mark.parametrize("algo", ALL_ALGORITHMS)
def test_algorithm_runs_and_respects_budget(algo):
    p = mmf.make("MMF1")
    ctx = make_run_context("MMF1", algo, 0)
    a = build(algo, problem=p, pop_size=POP, max_evaluations=BUDGET, rng=ctx.rng,
              params={"max_modes": 4, "clustering_update_freq": 3})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = a.run()
    assert isinstance(res, Result)
    # budget fairness: never exceed the shared evaluation budget
    assert res.n_evaluations <= BUDGET
    # used most of the budget (no early give-up advantage)
    assert res.n_evaluations >= BUDGET - POP
    # output format: feasible 2-objective solution set within bounds
    assert res.F.ndim == 2 and res.F.shape[1] == p.n_obj
    assert res.X.shape[1] == p.n_var
    assert len(res.X) == len(res.F) and len(res.X) >= 1
    assert np.all(res.X >= p.xl - 1e-6) and np.all(res.X <= p.xu + 1e-6)


def test_seed_protocol_is_algorithm_independent():
    # the runner gives every algorithm the same seed for the same (problem, run)
    s1 = make_run_context("MMF5", "EARS_MMOEA", 3).seed
    s2 = make_run_context("MMF5", "CPDEA", 3).seed
    assert s1 == s2


def test_all_six_baselines_plus_ours_present():
    # ours + 6 frozen comparison baselines + the NSGA-II control
    assert len(ALL_ALGORITHMS) == 8
    assert ALL_ALGORITHMS[0] == "EARS_MMOEA"
