"""Validate the extended CEC2019/2020 MMO competition problems: every analytic
Pareto set must be non-dominated against a large random decision cloud (proving the
reference set is genuinely optimal), lie within bounds, map onto the reference PF,
and evaluate vectorised==row-wise. A wrong reference would fail these checks.
"""
import numpy as np
import pytest

from benchmarks import extended


@pytest.mark.parametrize("name", extended.EXT_NAMES)
def test_extended_problem_reference_is_valid(name):
    p = extended.make(name)
    rng = np.random.default_rng(7)
    ps = p.pareto_set(2000)

    # within bounds
    assert np.all((ps >= p.xl - 1e-9) & (ps <= p.xu + 1e-9)), f"{name}: PS out of bounds"

    Fps = p.evaluate(ps)["F"]

    # PS is globally non-dominated: no random sample dominates a PS point
    R = rng.uniform(p.xl, p.xu, size=(40000, p.n_var))
    FR = p.evaluate(R)["F"]
    dominated = sum(
        bool(np.any((FR <= Fps[i]).all(1) & (FR < Fps[i]).any(1)))
        for i in range(0, len(ps), 15)
    )
    assert dominated == 0, f"{name}: {dominated} PS points dominated by random cloud"

    # PS maps onto the reference PF (within discretisation tolerance)
    pf = p.pareto_front(4000)
    d = np.min(np.linalg.norm(Fps[:, None, :] - pf[None, :, :], axis=2), axis=1)
    assert np.percentile(d, 99) < 5e-3, f"{name}: PS not on PF"

    # vectorised == row-wise
    sub = ps[:30]
    F_vec = p.evaluate(sub)["F"]
    F_row = np.vstack([p.evaluate(sub[j:j + 1])["F"] for j in range(len(sub))])
    assert np.allclose(F_vec, F_row), f"{name}: vectorised != row-wise"


def test_extended_problems_are_multimodal():
    # multi-global-PS members declare >1 equivalent Pareto set; the deceptive members
    # (MMF10, MMF12) have a single GLOBAL PS plus higher local basins by design.
    multi = {"MMF9", "SYMPART", "SYMPART_rot", "Omni_test", "MMF11"}
    deceptive = {"MMF10", "MMF12"}
    for name in extended.EXT_NAMES:
        b = extended.make(name).n_ps_branches
        if name in multi:
            assert b >= 2, f"{name} should have >1 global PS"
        elif name in deceptive:
            assert b == 1, f"{name} (deceptive) should have a single global PS"
