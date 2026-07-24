# Phase 7 Report — Formal Benchmark Comparison

## 1. Completed
- Full formal study: **MMF1–8 × 6 algorithms × 30 runs**, pop=200, 50k evals, frozen
  params, algorithm-independent seeds. **1440 runs, 0 errors, ~30 min** (14-worker
  multiprocessing, resumable).
- All 8 indicators per run; Friedman (all metrics significant), Wilcoxon+Holm pairwise,
  average-rank, win/tie/loss; CSV + LaTeX tables; 18 figures (rank bars, per-problem
  Pareto fronts, decision-space clusters).

## 2. Files generated
`experiments/run_benchmark.py`, `experiments/run_ablation.py` (Phase 9-ready),
`plotting/plot_all.py`, `results/raw/benchmark/**` (1440 runs),
`results/statistics/benchmark_*`, `results/tables/*.tex`, `results/figures/*`,
`docs/benchmark_result_report.md`, `docs/failure_diagnosis.md` (entry #1).

## 3. Sanity check
- 1440/1440 runs, 0 errors; resumability + budget fairness verified (smoke).
- Friedman significant on every metric (IGDX p=6e-4, PSP p=5e-4, IGD p=1e-3).

## 4. Result (honest)
- **EARS-MMOEA = best overall average rank (2.25)**, well ahead of 2nd (3.13);
  **dominates objective space** (beats CPDEA 8/0/0 on IGD and HV; ties Omni).
- **NOT rank-1 on the defining MMOP decision-space metrics:** CPDEA beats EARS on
  IGDX/PSP/mode_coverage (W/T/L 1/2/5), winning the harder problems MMF3/4/5/8.
- **Verdict: rank-1 overall, but not on IGDX/PSP → Phase 8 redesign triggered.**

## 5. Next phase
**Phase 8 — Redesign Loop.** Root cause: EARS is too convergence-greedy in decision
space. Plan (see `failure_diagnosis.md` #1): add a CPDEA-style convergence-penalised
decision-density key to environmental selection + strengthen the Decision-Mode Archive
in the final reported set, **without regressing IGD/HV**. Re-validate on MMF5, then
re-run the full Phase 7 judgement.

## 6. Failures / blockers / risks (honest)
- **This is the integrity path working as designed:** we did NOT achieve rank-1 on the
  headline MMOP metrics, and we are reporting it plainly and entering redesign rather
  than overclaiming. CPDEA is a strong, faithfully-implemented SOTA baseline, and it
  genuinely wins decision-space coverage on hard problems.
- No blockers. The redesign is well-scoped and the experiment harness makes re-running
  cheap (~30 min).
