"""Phase 0 smoke tests: project imports, seed protocol, IO round-trip, configs."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from utils import seeds, io_utils
from utils.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def test_packages_import():
    import algorithms, baselines, benchmarks, applications  # noqa: F401
    import experiments, plotting, metrics, utils            # noqa: F401


def test_seed_is_algorithm_independent():
    # Same problem + run index -> same seed regardless of algorithm.
    s_a = seeds.make_run_context("MMF1", "EARS_MMOEA", 7).seed
    s_b = seeds.make_run_context("MMF1", "DN_NSGAII", 7).seed
    assert s_a == s_b
    # Different run index -> (almost surely) different seed.
    s_c = seeds.make_run_context("MMF1", "EARS_MMOEA", 8).seed
    assert s_a != s_c


def test_seed_is_deterministic():
    assert seeds.derive_seed("MMF1", 0) == seeds.derive_seed("MMF1", 0)
    rng1 = seeds.make_run_context("MMF1", "x", 3).rng
    rng2 = seeds.make_run_context("MMF1", "x", 3).rng
    assert np.array_equal(rng1.random(5), rng2.random(5))


def test_save_load_run_roundtrip(tmp_path, monkeypatch):
    # redirect RAW_DIR into tmp so we don't pollute results/
    monkeypatch.setattr(io_utils, "RAW_DIR", tmp_path)
    obj = np.random.default_rng(0).random((10, 2))
    dec = np.random.default_rng(1).random((10, 3))
    jp = io_utils.save_run("smoke", "MMF1", "EARS_MMOEA", 0,
                           objectives=obj, decisions=dec,
                           metrics={"IGD": 0.123}, seed=42)
    rec = io_utils.load_run(jp)
    assert rec["metrics"]["IGD"] == 0.123
    assert np.allclose(rec["arrays"]["objectives"], obj)
    assert rec["provenance"]["seed"] == 42


def test_configs_load():
    for name in ["benchmark.yaml", "uav_sar.yaml", "params.yaml",
                 "selected_params.yaml", "baselines.yaml", "real_app2.yaml"]:
        cfg = load_config(ROOT / "configs" / name)
        assert isinstance(cfg, dict) and cfg
