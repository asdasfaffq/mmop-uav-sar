# Phase 5 Report — Metrics & Statistics

## 1. Completed
- **Indicators** (`metrics/indicators.py`), both spaces:
  - objective: IGD, IGD+ (dominated-component distance), normalised HV (exact 2-D
    sweep + pymoo fallback), spacing;
  - decision: IGDX, PSP (= CR/IGDX, Yue 2018 cover-rate), mode_coverage
    (decision-space recall), n_modes (adaptive-niching cluster count);
  - `DIRECTION` table encodes min/max per metric; `compute_all` returns all 8 for a run.
- **Statistics** (`metrics/statistics.py`): average rank (1=best, tie-aware),
  Friedman omnibus, paired Wilcoxon signed-rank + **Holm step-down correction**,
  per-problem win/tie/loss verdicts and aggregated W/T/L vs a reference.
- **Tables** (`metrics/tables.py`): per-problem mean(std) summary with best-marking
  (`*`) and significance markers (`+/-/=`), rank table, W/T/L table; CSV + LaTeX export.
- **Driver** (`experiments/run_statistics.py`): reads `results/raw/<exp>/.../run_*.json`,
  builds paired-run arrays, writes summary/WTL/ranks/Friedman CSVs + LaTeX tables.

## 2. Files generated
`metrics/{indicators,statistics,tables}.py`, `experiments/run_statistics.py`,
real `tests/test_statistics.py`.

## 3. Sanity check
- `pytest tests/` → **53 passed, 2 skipped**. Indicator tests pin correctness:
  IGD/IGD+ = 0 on identical sets; IGD+ ignores better-than-reference; HV monotone in
  convergence; IGDX/PSP reward coverage; spacing lower for uniform gaps. Statistics
  tests: average rank orders a clearly-best reference first; Friedman detects the
  difference; Wilcoxon+Holm yields all-wins with adjusted p >= raw p.
- **End-to-end pipeline validated on REAL runs** (3 algos x 2 problems x 3 runs,
  metrics via `compute_all`): all 8 metrics' summary/WTL CSVs + LaTeX + ranks + Friedman
  produced correctly; LaTeX escaped/captioned/best-marked. (Smoke artifacts removed.)

## 4. Next phase
**Phase 6 — parameter analysis** on the validation subset (MMF1/2/5 per
`configs/benchmark.yaml`): search EARS-MMOEA's key parameters, produce sensitivity
figures, freeze `configs/selected_params.yaml`. No tuning on the final test set.

## 5. Failures / blockers / risks (honest)
- Fixed a bad unit test (degenerate duplicate points made `spacing`=0) — the metric was
  correct; the test now uses irregular-gap points.
- Hardened `summary_table` best-marking to be NaN-safe.
- **Observed (expected) low power at small n:** with 3 runs, Wilcoxon+Holm marks
  everything a tie even where means clearly differ. Phase 7's 30 runs restore power.
  This confirms the integrity guard works: no significance is claimed without evidence.
- No blockers. Standard protocol confirmed for Phase 7 (30 runs, pop=200, 50k evals,
  MMF1-8).
