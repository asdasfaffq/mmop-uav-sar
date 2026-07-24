# Phase 2 Report — Standard Benchmark Wrapping

## 1. Completed
- Implemented **MMF1–MMF8** with objective formulas + analytical Pareto Sets/Fronts
  transcribed **verbatim from PlatEMO** (verified via a sourced extraction of the
  exact constants, e.g. `sin(6*pi*|x1-2|+pi)`, MMF7 coefficient 1, MMF6 sixths bands).
- Each problem implements the shared `Problem` protocol: vectorised `evaluate(X)->{F,CV}`,
  `pareto_set(n)` (covering ALL equivalent decision-space branches), `pareto_front(n)`
  (analytic closed form), and records `n_ps_branches` (multimodality metadata).
- `reference_sets.py`: caching API + a generic non-dominated extractor (fallback for
  future numerical-PF problems).
- `cec2020_mmo.py`: exposes the verified MMF1–8 under the CEC2020 umbrella and
  **transparently** lists MMF9–14 as PENDING (raises, no silent coverage claim).
- `benchmark_validation.py`: 5-point validation per problem.

## 2. Files generated
`benchmarks/mmf.py`, `benchmarks/reference_sets.py`, `benchmarks/cec2020_mmo.py`,
`benchmarks/benchmark_validation.py`, `tests/test_benchmark_wrapper.py` (real tests).

## 3. Sanity check
- `python benchmarks/benchmark_validation.py` → **ALL 8 MMF PROBLEMS VALIDATED**:
  (1) bounds well-formed; (2) PS within bounds; (3) **PS lies on analytic PF**
  (p99 deviation = 0, machine precision); (4) **no PS point dominated** by an 8000-pt
  uniform random cloud (PS genuinely optimal); (5) vectorised == row-wise eval.
- `pytest tests/` → **29 passed, 4 skipped** (benchmark tests now active).

## 4. Next phase
**Phase 3 — EARS-MMOEA prototype.** Implement the 7 modules (dual-space fitness,
three-archive system, adaptive niching, within/cross-mode mating, constraint-aware
selection, operator portfolio, environmental selection) and get a minimal full run on
≥1 MMF problem, emitting population/archives/metrics. (Metrics formalised in Phase 5;
Phase 3 may use quick IGD/IGDX probes to sanity-check progress.)

## 5. Failures / blockers / risks
- No blockers. Two bugs were caught and fixed during validation (honest log):
  - dataclass turned annotated `_xl/_xu` into fields → subclass bounds ignored;
    fixed by dropping `@dataclass` for plain class attributes.
  - MMF2/3 measure-zero PS endpoint sat exactly on the piecewise threshold; resolved
    by computing the PF from the analytic `_pf_f2` formula instead of pushing PS through
    the piecewise objective (and validating at p99 to exclude the degenerate corner).
- **Scope risk (tracked & disclosed):** only MMF1–8 have verified analytical reference
  sets so far. MMF9–14 (objective formulas known; PF/PS need numerical reference) are
  marked PENDING and will be added before Phase 7 if the suite needs widening. This is
  surfaced in code, not hidden.
