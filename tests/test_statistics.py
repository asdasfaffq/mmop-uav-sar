"""Phase 5: indicators correctness + statistics layer + aggregation pipeline."""
from __future__ import annotations

import numpy as np

from metrics import indicators as I
from metrics import statistics as S
from metrics import tables as T


# --------------------------- indicators -----------------------------------
def test_igd_zero_when_identical():
    ref = np.array([[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]])
    assert I.igd(ref, ref.copy()) == 0.0
    assert I.igd_plus(ref, ref.copy()) == 0.0


def test_igd_plus_ignores_better_than_reference():
    ref = np.array([[1.0, 1.0]])
    better = np.array([[0.0, 0.0]])           # dominates ref
    assert I.igd_plus(ref, better) == 0.0      # no penalty for being better
    assert I.igd(ref, better) > 0.0            # plain IGD penalises distance


def test_hv_monotone_in_convergence():
    ref = np.array([[0.0, 1.0], [1.0, 0.0]])
    near = np.array([[0.1, 0.1]])
    far = np.array([[0.5, 0.5]])
    assert I.hypervolume(near, ref) > I.hypervolume(far, ref)


def test_igdx_and_psp_reward_coverage():
    ps = np.linspace(0, 1, 50)[:, None] * np.ones((1, 2))
    good = ps.copy()
    bad = ps[:5]                                # covers only a corner
    assert I.igdx(ps, good) < I.igdx(ps, bad)
    assert I.psp(ps, good) > I.psp(ps, bad)


def test_spacing_uniform_lower_than_irregular():
    # spacing (Schott) measures uniformity of nearest-neighbour gaps: even gaps
    # -> low; irregular gaps -> high.
    t = np.linspace(0, 1, 20)
    uniform = np.column_stack([t, 1 - t])
    rng = np.random.default_rng(0)
    s = np.sort(rng.random(20))                 # irregular positions on the line
    irregular = np.column_stack([s, 1 - s])
    assert I.spacing(uniform) < I.spacing(irregular)


# --------------------------- statistics -----------------------------------
def _synthetic():
    rng = np.random.default_rng(0)
    problems = [f"P{i}" for i in range(4)]
    algos = ["REF", "A", "B"]
    per_run = {}
    for p in problems:
        per_run[p] = {
            "REF": rng.normal(0.10, 0.01, 30),
            "A":   rng.normal(0.20, 0.01, 30),
            "B":   rng.normal(0.30, 0.01, 30),
        }
    return per_run, problems, algos


def test_average_rank_orders_reference_first():
    per_run, problems, algos = _synthetic()
    _, mean_rank = S.average_rank(per_run, problems, algos, lower_better=True)
    assert mean_rank[0] < mean_rank[1] < mean_rank[2]
    assert abs(mean_rank[0] - 1.0) < 1e-9


def test_friedman_detects_difference():
    per_run, problems, algos = _synthetic()
    fr = S.friedman_test(per_run, problems, algos, lower_better=True)
    assert fr["pvalue"] < 0.05


def test_wilcoxon_holm_wins():
    per_run, problems, algos = _synthetic()
    cmp = S.wilcoxon_holm(per_run, problems, algos, "REF", lower_better=True)
    for a, (w, t, l) in cmp.wtl.items():
        assert w == len(problems) and l == 0
    for pv in cmp.pairs:
        assert pv.pvalue_holm >= pv.pvalue - 1e-12


def test_tables_build():
    per_run, problems, algos = _synthetic()
    summ = T.summary_table(per_run, problems, algos, "REF", lower_better=True)
    assert summ.shape == (4, 3)
    rk = T.rank_frame(per_run, problems, algos, lower_better=True)
    assert rk.iloc[0]["algorithm"] == "REF"
    wtl = T.wtl_frame(per_run, problems, algos, "REF", lower_better=True)
    assert set(wtl["vs"]) == {"A", "B"}


# --------------------------- aggregation pipeline -------------------------
def test_load_per_run_pipeline(tmp_path):
    from utils import io_utils
    from experiments.run_statistics import load_per_run
    io_utils.RAW_DIR = tmp_path
    rng = np.random.default_rng(1)
    for prob in ["MMF1", "MMF2"]:
        for algo in ["EARS_MMOEA", "CPDEA"]:
            for ri in range(3):
                io_utils.save_run("benchmark", prob, algo, ri,
                                  objectives=rng.random((5, 2)),
                                  decisions=rng.random((5, 2)),
                                  metrics={"IGD": rng.random(), "IGDX": rng.random()},
                                  seed=ri)
    per_run, problems, algos = load_per_run(tmp_path, "benchmark")
    assert problems == ["MMF1", "MMF2"]
    assert set(algos) == {"EARS_MMOEA", "CPDEA"}
    assert per_run["IGD"]["MMF1"]["CPDEA"].shape == (3,)
