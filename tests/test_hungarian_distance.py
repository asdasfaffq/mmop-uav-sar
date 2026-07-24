"""The exact Hungarian set-matching layout distance used to re-evaluate placement."""
import numpy as np
from applications.app_metrics import hungarian_layout_distance, igdx_hungarian


def test_permutation_invariance():
    # same layout, stations in different order -> distance 0
    a = np.array([0.0, 0.0, 1.0, 1.0, 0.5, 0.5])      # 3 stations
    b = np.array([1.0, 1.0, 0.5, 0.5, 0.0, 0.0])      # same set, reordered
    assert hungarian_layout_distance(a, b, K=3) < 1e-12


def test_matches_better_than_sorted_when_crossing():
    # two layouts where coordinate-sort mis-pairs; Hungarian gives the true min
    a = np.array([0.0, 0.0, 1.0, 0.0])                # stations (0,0),(1,0)
    b = np.array([1.0, 0.0, 0.0, 0.0])                # same set reordered -> dist 0
    assert hungarian_layout_distance(a, b, K=2) < 1e-12


def test_igdx_hungarian_zero_when_ref_in_obtained():
    ref = np.array([[0.0, 0.0, 1.0, 1.0]])
    obt = np.array([[1.0, 1.0, 0.0, 0.0], [5.0, 5.0, 9.0, 9.0]])
    assert igdx_hungarian(ref, obt, K=2) < 1e-12
