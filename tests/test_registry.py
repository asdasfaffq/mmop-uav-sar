"""Phase 1: baseline registry is fixed, consistent, and fails loudly pre-impl."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from baselines import baseline_registry as reg
from utils.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def test_six_baselines_fixed():
    # The comparison set stays frozen at 6; the NSGA-II control must not leak into it.
    assert len(reg.BASELINES) == 6
    assert "NSGAII" not in reg.BASELINES and "NSGAII" in reg.CONTROLS
    types = sorted(reg.BASELINE_INFO[b]["type"] for b in reg.BASELINES)
    assert types.count("sota") == 3 and types.count("classic") == 3


def test_all_algorithms_includes_ours():
    assert reg.OURS == "EARS_MMOEA"
    assert reg.ALL_ALGORITHMS[0] == reg.OURS
    assert set(reg.BASELINES).issubset(set(reg.ALL_ALGORITHMS))


def test_config_matches_registry():
    cfg = load_config(ROOT / "configs" / "baselines.yaml")
    assert set(cfg["baselines"].keys()) == set(reg.BASELINES)


def test_build_unknown_raises_keyerror():
    with pytest.raises(KeyError):
        reg.build("NOPE", problem=None, pop_size=10,
                  max_evaluations=100, rng=np.random.default_rng(0))


def test_all_algorithms_build_after_phase4():
    # As of Phase 4 every fixed baseline + EARS is implemented and constructible.
    from benchmarks import mmf
    p = mmf.make("MMF1")
    for name in reg.ALL_ALGORITHMS:
        algo = reg.build(name, problem=p, pop_size=10, max_evaluations=100,
                         rng=np.random.default_rng(0))
        assert algo.name == name
