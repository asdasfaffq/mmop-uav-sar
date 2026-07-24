"""CEC2020 Multimodal Multi-Objective Optimization (MMO) suite access.

Scope note (honest)
--------------------
The CEC2019/CEC2020 MMO competition suite is built ON the MMF problems
(Yue et al.) plus scalable variants (MMF9-MMF16, MMF10-14 with np/q params,
and the IDMP family). This project's *verified, analytical-reference* core is
MMF1-MMF8 (Pareto sets transcribed from PlatEMO with exact closed-form PS/PF).

`cec2020_mmo` therefore currently exposes the verified MMF1-MMF8 under the
CEC2020 umbrella. The scalable MMF9-14 (objective formulas verified from the
smoof CEC2019 reference, but PF/PS requiring numerical computation) are listed
as `PENDING` and will be added with numerical reference sets before the formal
Phase 7 comparison if needed. We do NOT silently claim full-suite coverage.
"""
from __future__ import annotations

from benchmarks import mmf

# Verified, analytical-reference problems available now.
CEC2020_AVAILABLE = list(mmf.MMF_NAMES)  # MMF1..MMF8

# Declared-but-not-yet-implemented (transparency; no silent gaps).
CEC2020_PENDING = ["MMF9", "MMF10", "MMF11", "MMF12", "MMF13", "MMF14"]


def make(name: str):
    if name in CEC2020_AVAILABLE:
        return mmf.make(name)
    if name in CEC2020_PENDING:
        raise NotImplementedError(
            f"{name} is part of CEC2020 MMO but not yet implemented with a "
            f"verified reference set (see module docstring).")
    raise KeyError(f"unknown CEC2020 MMO problem '{name}'.")


def available_problems():
    return [mmf.make(n) for n in CEC2020_AVAILABLE]
