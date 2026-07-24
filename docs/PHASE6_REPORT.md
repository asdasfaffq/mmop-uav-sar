# Phase 6 Report — Parameter Analysis

## 1. Completed
- OFAT sensitivity analysis of 6 EARS-MMOEA parameters on the **validation subset only**
  (MMF1/2/5), balanced IGD+IGDX score, frozen to `configs/selected_params.yaml`.
- Built the analysis driver (`experiments/run_parameter_analysis.py`) + plotting modules
  (`plotting/_style.py`, `plot_parameter_analysis.py`, and -- prepared for Phase 7 --
  `plot_pareto_front.py`, `plot_rank_tables.py`, `plot_decision_clusters.py`).
- **Chosen:** niche_boost=1.0, cross_mode_mating_prob=0.2, decision_mode_archive=50,
  max_modes=5, clustering_update_freq=10, operator_lr=0.05.

## 2. Files generated
`experiments/run_parameter_analysis.py`, `plotting/{_style,plot_parameter_analysis,
plot_pareto_front,plot_rank_tables,plot_decision_clusters}.py`,
`results/summary/parameter_analysis.csv`, `results/figures/parameter_sensitivity.{png,pdf}`,
`configs/selected_params.yaml` (frozen), `docs/parameter_analysis_report.md`.

## 3. Sanity check
- Full pipeline validated (CSV + 300dpi PNG + vector PDF + frozen YAML all produced);
  plotting re-render from CSV works.
- The analysis shows EARS's distinctive components measurably help (niche_boost 1.0:
  IGDX 0.071 vs 0.094 at 0; cross-mode mating: IGD 0.0060 vs 0.0069 at 0) — early
  positive signal for the Phase 9 ablation.

## 4. Next phase
**Phase 7 — formal benchmark comparison.** Run all 6 algorithms on MMF1–8, 30 runs,
pop=200, 50k evals, frozen params; compute all 8 metrics; Friedman + Wilcoxon-Holm +
ranks + W/T/L; Pareto/cluster/rank figures; judge whether EARS is rank-1. `run_benchmark.py`
will use multiprocessing across the independent runs (full study ~1 h; a single full
EARS run is ~13 s).

## 5. Failures / blockers / risks (honest)
- **Bug caught early (by the progress monitor):** `ndarray.ptp()` removed in NumPy 2.0
  → switched to `np.ptp()`. The monitor's error-signal coverage caught it after the
  first sweep, saving a wasted ~25 min run.
- **Honest, documented deviation:** auto-selection picked `clustering_update_freq=1`,
  but a full-budget validation re-check (MMF5, a validation problem) showed `freq=10`
  is both faster and better — `freq=1` overfit the reduced search budget. Froze
  `freq=10`. No test-set leakage.
- **Disclosed:** `restart_ratio` not tuned (archive-guided restart inert until Phase 8);
  OFAT noise at 3 runs handled via balanced-score + default-proximity tie-breaking.
- No blockers. `selected_params.yaml` is now frozen and binding for all later phases.
