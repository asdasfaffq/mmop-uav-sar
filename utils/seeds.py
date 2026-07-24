"""Unified random-seed management.

The whole project derives every run's RNG from a single integer seed via a
deterministic protocol, so that:

* the same (algorithm, problem, run_index) always reproduces bit-for-bit,
* no algorithm can "cherry-pick" a favourable seed -- run indices 0..R-1 are
  fixed and shared across all algorithms,
* seeds are derived, not hand-listed, so the protocol is auditable.

Protocol
--------
A run is identified by a string key ``f"{problem}|{algorithm}|{run_index}"``.
Crucially the *seed for a given (problem, run_index) is independent of the
algorithm name*, so every algorithm sees the *same* initial population /
problem instantiation for run ``r``.  We achieve this by hashing only
``(global_seed, problem, run_index)``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

# Project-wide master seed. Fixed constant; never tuned.
GLOBAL_SEED = 20260616


def derive_seed(problem: str, run_index: int, global_seed: int = GLOBAL_SEED) -> int:
    """Deterministically derive a 32-bit seed from (problem, run_index).

    The algorithm name is intentionally *not* part of the hash so that every
    competing algorithm observes the identical problem instance and initial
    sampling for a given run index -- a core fairness requirement.
    """
    key = f"{global_seed}|{problem}|{int(run_index)}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    # take first 4 bytes -> uint32 in [0, 2**32)
    return int.from_bytes(digest[:4], "big")


@dataclass
class RunContext:
    """Everything an experiment run needs to be reproducible."""

    problem: str
    algorithm: str
    run_index: int
    seed: int
    rng: np.random.Generator

    @property
    def key(self) -> str:
        return f"{self.problem}|{self.algorithm}|{self.run_index}"


def make_run_context(problem: str, algorithm: str, run_index: int,
                     global_seed: int = GLOBAL_SEED) -> RunContext:
    """Build a RunContext with an algorithm-independent seed."""
    seed = derive_seed(problem, run_index, global_seed)
    rng = np.random.default_rng(seed)
    return RunContext(problem=problem, algorithm=algorithm,
                      run_index=run_index, seed=seed, rng=rng)


def seed_everything(seed: int) -> np.random.Generator:
    """Seed Python's stdlib + numpy global state and return a fresh Generator.

    Prefer passing the returned Generator explicitly; the global seeding is a
    safety net for third-party code that uses the legacy global RNG.
    """
    import random as _random

    _random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    return np.random.default_rng(seed)
