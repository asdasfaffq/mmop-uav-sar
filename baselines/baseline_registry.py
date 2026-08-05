"""Central registry of the 5 FIXED baselines + EARS-MMOEA.

The 5 baselines are frozen in Phase 1 (see docs/baseline_selection_note.md).
Implementations are added in Phase 4; until then the registry resolves names to
classes that raise an explicit NotImplemented error, so the wiring is testable
without faking results.

Usage
-----
    from baselines.baseline_registry import build, BASELINES, ALL_ALGORITHMS
    algo = build("CPDEA", problem=prob, pop_size=200, max_evaluations=50000,
                 rng=rng, params=params)
    result = algo.run()
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np

from algorithms.base import Algorithm, Problem

# ----------------------------------------------------------------------------
# Frozen baseline metadata (Phase 1 decision). 2 SOTA + 3 classic.
# ----------------------------------------------------------------------------
BASELINE_INFO: dict[str, dict[str, str]] = {
    # --- 3 popular classics ---
    "MO_Ring_PSO_SCD": dict(
        type="classic", mechanism="PSO + ring topology + special crowding distance",
        venue="IEEE TEVC 2018", code="MATLAB FileExchange #68662 + PlatEMO",
        module="baselines.mo_ring_pso_scd"),
    "DN_NSGAII": dict(
        type="classic", mechanism="decision-space niching NSGA-II",
        venue="IEEE CEC 2016", code="PlatEMO (DNNSGAII)",
        module="baselines.dn_nsga2"),
    "NSGAII": dict(
        type="control", mechanism="objective-space crowding only (no decision-space machinery)",
        venue="IEEE TEVC 2002", code="canonical",
        module="baselines.nsga2"),
    "OmniOptimizer": dict(
        type="classic", mechanism="epsilon-dominance + decision&objective crowding",
        venue="EJOR 2008", code="PlatEMO (OmniOptimizer)",
        module="baselines.omni_optimizer"),
    # --- 2 SOTA ---
    "CPDEA": dict(
        type="sota", mechanism="convergence-penalized density (decision-space) + DE",
        venue="IEEE TEVC 2020", code="official GitHub yiping0liu/CPDEA",
        module="baselines.cpdea"),
    "MMEA_WI": dict(
        type="sota", mechanism="weighted indicator (decision-space diversity in indicator)",
        venue="IEEE TEVC 2021", code="Wenhua-Li comparative-study repo",
        module="baselines.mmea_wi"),
    "HREA": dict(
        type="sota", mechanism="hierarchy ranking (global + within-peak local Pareto fronts)",
        venue="IEEE TEVC 2023", code="gengfengli/HREA",
        module="baselines.hrea"),
}

# The 6 comparison baselines are frozen (Phase 1) and must stay 6: 3 SOTA + 3 classic.
# NSGA-II is a *control*, not a comparison baseline -- it carries no decision-space
# machinery and exists to test whether the multimodal apparatus is needed at all. It is
# therefore excluded from BASELINES and kept in CONTROLS.
CONTROLS: tuple[str, ...] = ("NSGAII",)
BASELINES: tuple[str, ...] = tuple(k for k in BASELINE_INFO if k not in CONTROLS)
OURS = "EARS_MMOEA"
ALL_ALGORITHMS: tuple[str, ...] = (OURS,) + BASELINES + CONTROLS

# Registry of constructors filled by register() decorators in each module.
_REGISTRY: dict[str, Callable[..., Algorithm]] = {}


def register(name: str) -> Callable[[type], type]:
    def deco(cls: type) -> type:
        _REGISTRY[name] = cls
        cls.name = name
        return cls
    return deco


def _import_implementations() -> None:
    """Import baseline + algorithm modules so their @register runs (best-effort)."""
    import importlib
    modules = [info["module"] for info in BASELINE_INFO.values()]
    modules.append("algorithms.ears_mmoea")
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception:
            # not implemented yet (earlier phase) -- silently skip; build() will
            # raise a clear error if the name is actually requested.
            pass


def build(name: str, *, problem: Problem, pop_size: int, max_evaluations: int,
          rng: np.random.Generator, params: dict[str, Any] | None = None) -> Algorithm:
    if name not in ALL_ALGORITHMS:
        raise KeyError(f"unknown algorithm '{name}'. Known: {ALL_ALGORITHMS}")
    if name not in _REGISTRY:          # import lazily; a direct import of one
        _import_implementations()      # algorithm must not hide the others
    if name not in _REGISTRY:
        raise NotImplementedError(
            f"algorithm '{name}' is fixed in the registry but not implemented yet "
            f"(added in Phase 3/4). Info: {BASELINE_INFO.get(name, 'ours')}")
    cls = _REGISTRY[name]
    return cls(problem=problem, pop_size=pop_size, max_evaluations=max_evaluations,
               rng=rng, params=params)
