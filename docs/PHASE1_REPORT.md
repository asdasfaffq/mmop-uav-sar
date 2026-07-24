# Phase 1 Report — Literature & Baseline Selection

## 1. Completed
- Focused literature/code-availability scan of the MMOP field (classics + 2019–2025 SOTA).
- **Key finding:** MMOP algorithms are overwhelmingly MATLAB/PlatEMO; no trusted
  Python SOTA MMEA repo exists. Resolved with an explicit strategy decision
  (unified Python impl + faithful port from official code + MMF validation gate),
  documented in `baseline_selection_note.md`.
- **5 baselines FIXED** (2 SOTA + 3 classic), mechanism-diverse, all with public code:
  1. MO_Ring_PSO_SCD (classic, PSO+ring+SCD, TEVC'18)
  2. DN-NSGA-II (classic, decision-space niching GA, CEC'16)
  3. Omni-optimizer (classic, ε-dominance dual crowding, EJOR'08)
  4. CPDEA (SOTA, convergence-penalized density+DE, TEVC'20, official code)
  5. MMEA-WI (SOTA, weighted indicator, TEVC'21)
- Defined the **unified algorithm interface** (`algorithms/base.py`: `Algorithm` ABC,
  `Problem` protocol, `Result`) with structural fairness (shared budget accounting).
- Built the **baseline registry** (`baselines/baseline_registry.py`) that fails loudly
  (NotImplementedError) until Phase 4 — no fake algorithms.

## 2. Files generated
- `docs/baseline_selection_note.md` (full rationale, swap-in plan, sources)
- `algorithms/base.py`, `baselines/baseline_registry.py`
- `configs/baselines.yaml` (fixed, with fairness block + swap candidates)
- `tests/test_registry.py`

## 3. Sanity check
- `pytest tests/` → **10 passed, 5 skipped**.
- Registry tests confirm: exactly 5 baselines (2 SOTA + 3 classic), EARS-MMOEA is
  algorithm[0], config keys match registry, unknown name → KeyError, unimplemented
  name → NotImplementedError (loud failure, no fabrication).

## 4. Next phase
**Phase 2 — Standard benchmark wrapping.** Implement MMF series + CEC2020 MMO wrappers
behind the `Problem` protocol, with reference Pareto fronts/sets, decision-space
metrics, and `benchmark_validation.py`. This also stands up the validation gate that
Phase 4 baseline ports must pass.

## 5. Failures / blockers / risks
- No blockers.
- **Tracked risk:** faithful Python ports of MATLAB baselines may deviate. Mitigation:
  port from official code, validate on MMF against published numbers, keep authors'
  params, never weaken. TriMOEA-TA&R / MMOEA-DC reserved as swap-ins.
- **Tracked risk:** MMEA-WI exact PlatEMO container unconfirmed; will port from the
  Wenhua-Li comparative repo and validate.
