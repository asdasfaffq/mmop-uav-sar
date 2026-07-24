"""The genuine in-sort placement variants used by the placement-isolation study.

Unlike the within-front modes, the in-sort modes let the diversity signal decide
survival ACROSS front boundaries, so they can return a different set than a pure
non-dominated truncation. We check they run, respect the budget, and (for pure-S)
can actually promote a decision-diverse dominated solution over a converged one.
"""
import numpy as np

from algorithms.selection import environmental_selection


def _toy():
    # 6 solutions; first three on a clean front, last three dominated but spread
    F = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0],      # non-dominated
                  [0.6, 0.6], [0.7, 0.7], [0.9, 0.9]])     # dominated
    X = np.array([[0.0], [0.05], [0.1], [5.0], [6.0], [7.0]])  # last three sparse in X
    CV = np.zeros(6)
    return X, F, CV


def test_in_sort_modes_run_and_respect_budget():
    X, F, CV = _toy()
    for mode in ("in_sort_density", "in_sort_pure_s"):
        idx = environmental_selection(X, F, CV, 3, selection_mode=mode,
                                      hybrid_beta=0.5, X_dec=X)
        assert len(idx) == 3
        assert len(set(idx.tolist())) == 3          # no duplicates
        assert idx.max() < 6 and idx.min() >= 0


def test_pure_s_in_sort_can_cross_front_boundary():
    # with a large beta, pure-S in-sort should keep at least one sparse but
    # dominated solution that a within-front truncation would never promote.
    X, F, CV = _toy()
    idx = environmental_selection(X, F, CV, 3, selection_mode="in_sort_pure_s",
                                  hybrid_beta=5.0, X_dec=X)
    assert any(i >= 3 for i in idx)                  # a dominated solution survived


def test_within_front_preserves_front_precedence():
    # the within-front equivalence mode must keep only the non-dominated front here
    X, F, CV = _toy()
    idx = environmental_selection(X, F, CV, 3, selection_mode="equivalence", X_dec=X)
    assert set(idx.tolist()) == {0, 1, 2}            # only the non-dominated front
