"""Phase 3: archives, equivalence fitness, niching primitives."""
from __future__ import annotations

import numpy as np

from algorithms.archives import DecisionModeArchive, ParetoObjectiveArchive
from algorithms.equivalence_fitness import (constrained_dominates,
                                            crowding_distance,
                                            fast_nondominated_sort,
                                            special_crowding_distance)
from algorithms.niching import adaptive_niching, assign_to_centers


def test_constrained_domination():
    assert constrained_dominates(np.array([1, 1]), 0.0, np.array([0, 0]), 5.0)
    assert constrained_dominates(np.array([1, 1]), 0.0, np.array([2, 2]), 0.0)
    assert not constrained_dominates(np.array([1, 2]), 0.0, np.array([2, 1]), 0.0)
    assert constrained_dominates(np.array([9, 9]), 1.0, np.array([0, 0]), 2.0)


def test_nondominated_sort_partitions():
    F = np.array([[1, 4], [2, 3], [3, 2], [4, 1], [2, 5], [3, 4]])
    fronts = fast_nondominated_sort(F)
    assert set(fronts[0].tolist()) == {0, 1, 2, 3}
    assert sum(len(f) for f in fronts) == len(F)


def test_crowding_and_scd_finite():
    rng = np.random.default_rng(0)
    F = rng.random((20, 2)); X = rng.random((20, 2))
    cd = crowding_distance(F)
    scd = special_crowding_distance(F, X)
    assert cd.shape == (20,) and scd.shape == (20,)
    assert np.isinf(cd).sum() >= 2


def test_pareto_archive_keeps_nondominated_and_bounded():
    rng = np.random.default_rng(1)
    arc = ParetoObjectiveArchive(capacity=10)
    for _ in range(5):
        arc.update(rng.random((30, 3)), rng.random((30, 2)))
    assert len(arc) <= 10
    assert len(fast_nondominated_sort(arc.F)[0]) == len(arc)


def test_decision_mode_archive_bounded():
    rng = np.random.default_rng(2)
    arc = DecisionModeArchive(capacity=8)
    arc.update(rng.random((40, 2)), rng.random((40, 2)))
    assert len(arc) <= 8


def test_niching_detects_two_clusters():
    rng = np.random.default_rng(3)
    X = np.vstack([rng.normal([0, 0], 0.02, (40, 2)),
                   rng.normal([1, 1], 0.02, (40, 2))])
    info = adaptive_niching(X, [-0.5, -0.5], [1.5, 1.5], rng=rng)
    assert info.n_modes >= 2
    lbl = assign_to_centers(X, [-0.5, -0.5], [1.5, 1.5], info.centers)
    assert len(np.unique(lbl)) >= 2
