"""Verify the scalable high-dimensional MMOP has a correct analytic reference."""
import numpy as np
import pytest

from benchmarks.scalable import make, DIMS


@pytest.mark.parametrize("d", [2, 5, 10, 30, 50, 100])
def test_ps_maps_to_analytic_pf(d):
    p = make(d)
    ps = p.pareto_set(2000)
    F = p.evaluate(ps)["F"]
    # every Pareto-set point images exactly onto f2 = 1 - sqrt(f1)
    assert np.max(np.abs(F[:, 1] - (1.0 - np.sqrt(F[:, 0])))) < 1e-9


@pytest.mark.parametrize("d", [2, 10, 50, 100])
def test_ps_is_nondominated(d):
    p = make(d)
    rng = np.random.default_rng(0)
    F_ps = p.evaluate(p.pareto_set(1000))["F"]
    cloud = p.xl + (p.xu - p.xl) * rng.random((20000, d))
    Fc = p.evaluate(cloud)["F"]
    for f in F_ps[::40]:
        dominated = np.any(np.all(Fc <= f, axis=1) & np.any(Fc < f, axis=1))
        assert not dominated


@pytest.mark.parametrize("d", list(DIMS))
def test_two_distinct_branches(d):
    p = make(d)
    assert p.n_ps_branches == 2
    assert p.n_var == d
    ps = p.pareto_set(2000)
    a, b = ps[: len(ps) // 2], ps[len(ps) // 2:]
    # branches separated by 1.0 in x2, identical in the distance tail (= 0.5)
    assert np.min(np.abs(a[:, 1] - b[:, 1])) > 0.99
    if d > 2:
        assert np.allclose(ps[:, 2:], 0.5)


# --- second family: distance-minimization scalable problem ---
from benchmarks.scalable import make_dmp


@pytest.mark.parametrize("d", [2, 5, 30, 100])
def test_dmp_ps_on_linear_front(d):
    p = make_dmp(d)
    F = p.evaluate(p.pareto_set(2000))["F"]
    assert np.max(np.abs(F[:, 0] + F[:, 1] - 2.0 * p.r)) < 1e-9


@pytest.mark.parametrize("d", [2, 50, 100])
def test_dmp_ps_nondominated_two_branches(d):
    p = make_dmp(d)
    rng = np.random.default_rng(0)
    F_ps = p.evaluate(p.pareto_set(1000))["F"]
    cloud = p.xl + (p.xu - p.xl) * rng.random((20000, d))
    Fc = p.evaluate(cloud)["F"]
    for f in F_ps[::40]:
        assert not np.any(np.all(Fc <= f, axis=1) & np.any(Fc < f, axis=1))
    assert p.n_ps_branches == 2
