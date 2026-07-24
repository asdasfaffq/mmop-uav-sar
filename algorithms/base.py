"""Unified algorithm interface shared by EARS-MMOEA and all baselines.

Every algorithm in this project -- ours and the 5 baselines -- implements the
same `Algorithm` protocol and returns the same `Result` object, so that the
experiment runners, metrics, and fairness checks are algorithm-agnostic.

Fairness is structural: the runner constructs every algorithm with the *same*
`Problem`, the *same* `pop_size`, and the *same* `max_evaluations`, and passes a
seeded `numpy.random.Generator` derived only from (problem, run_index). An
algorithm therefore cannot widen its own budget or pick its own seed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np


class Problem(Protocol):
    """Minimal problem protocol (both benchmark MMOPs and the UAV application).

    Implementations live in benchmarks/ and applications/.
    """

    name: str
    n_var: int
    n_obj: int
    xl: np.ndarray  # lower bounds (n_var,)
    xu: np.ndarray  # upper bounds (n_var,)

    def evaluate(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """Evaluate a population.

        Parameters
        ----------
        X : (N, n_var) decision matrix.

        Returns
        -------
        dict with at least:
          'F'  : (N, n_obj) objective matrix (all minimised)
          'CV' : (N,) total constraint violation (0 if feasible); zeros if
                 the problem is unconstrained.
        Optional extras (e.g. route metadata) may be returned under other keys.
        """
        ...


@dataclass
class Result:
    """Standard result container persisted by the runners."""

    X: np.ndarray                      # (N, n_var) final solution set (decision)
    F: np.ndarray                      # (N, n_obj) objectives (minimised)
    CV: np.ndarray | None = None       # (N,) constraint violation, if any
    n_evaluations: int = 0
    history: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)  # archives, labels, ...


class Algorithm(ABC):
    """Base class enforcing the shared, fairness-respecting interface."""

    #: human-readable registry name; set on each subclass.
    name: str = "BASE"

    def __init__(self, problem: Problem, pop_size: int, max_evaluations: int,
                 rng: np.random.Generator, params: dict[str, Any] | None = None):
        self.problem = problem
        self.pop_size = int(pop_size)
        self.max_evaluations = int(max_evaluations)
        self.rng = rng
        self.params = dict(params or {})
        self._n_eval = 0

    # --- budget accounting (shared so no algorithm can over-spend silently) ---
    def _evaluate(self, X: np.ndarray) -> dict[str, np.ndarray]:
        X = np.atleast_2d(X)
        out = self.problem.evaluate(X)
        self._n_eval += X.shape[0]
        return out

    @property
    def evaluations_used(self) -> int:
        return self._n_eval

    @property
    def budget_left(self) -> int:
        return self.max_evaluations - self._n_eval

    @abstractmethod
    def run(self) -> Result:
        """Execute the search under the shared budget and return a Result."""
        raise NotImplementedError
