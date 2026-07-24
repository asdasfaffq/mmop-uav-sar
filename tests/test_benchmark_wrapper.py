"""Phase 2: MMF / CEC2020 benchmark wrappers behave correctly."""
from __future__ import annotations

import numpy as np
import pytest

from benchmarks import mmf, cec2020_mmo
from benchmarks.benchmark_validation import validate_problem
from benchmarks.reference_sets import nondominated_front, get_reference_front


@pytest.mark.parametrize("name", mmf.MMF_NAMES)
def test_mmf_validates(name):
    assert validate_problem(mmf.make(name)) == []


@pytest.mark.parametrize("name", mmf.MMF_NAMES)
def test_evaluate_shapes_and_protocol(name):
    p = mmf.make(name)
    X = np.random.default_rng(0).uniform(p.xl, p.xu, size=(20, p.n_var))
    out = p.evaluate(X)
    assert out["F"].shape == (20, p.n_obj)
    assert out["CV"].shape == (20,)
    assert np.all(out["CV"] == 0)  # MMF suite is unconstrained


def test_pareto_front_is_nondominated():
    p = mmf.make("MMF1")
    pf = get_reference_front(p, 500)
    nd = nondominated_front(pf)
    # the analytic PF is a non-dominated curve: almost all points survive
    assert len(nd) >= 0.95 * len(pf)


def test_n_ps_branches_recorded():
    assert all(mmf.make(n).n_ps_branches >= 1 for n in mmf.MMF_NAMES)
    assert mmf.make("MMF2").n_ps_branches == 2


def test_cec2020_scope_is_honest():
    # available subset works; pending problems raise (no silent gaps)
    assert "MMF1" in cec2020_mmo.CEC2020_AVAILABLE
    with pytest.raises(NotImplementedError):
        cec2020_mmo.make("MMF12")
    assert len(cec2020_mmo.available_problems()) == 8
