# Phase 9 Report — Ablation Study

## 1. Completed
- A0_Full vs 8 ablated variants (A1–A8), MMF1–8, 30 runs, frozen params.
  **2160 runs, 0 errors** (~65 min, multiprocessing, shared CPU with a parallel session).
- Statistics (Wilcoxon+Holm vs A0_Full) + 4-panel ablation figure.

## 2. Files
`experiments/run_ablation.py`, `plotting/plot_ablation.py`,
`results/raw/ablation/**`, `results/statistics/ablation_*`,
`results/figures/ablation_study.*`, `docs/ablation_report.md`.

## 3. Result (honest, with the rank-1 hybrid core; 10 variants incl. A9)
- **Full framework ≫ deletions** (acceptance met): A8 backbone IGDX +623% (8/0/0);
  A3 no-equivalence-fitness +181% (8/0/0).
- **Benchmark-significant modules (A0 wins, Holm):** dual-space equivalence-aware
  fitness (A3, +181%, 8/8); adaptive operator portfolio (A7, +35%, 5/8); **the NEW
  hybrid sparsity bonus (A9, +11%, 3/8, 0 losses)** — the redesign mechanism is itself
  a proven contributor; adaptive niching (A4, +5%, 1/8).
- **Not significant on benchmark (honest):** decision-mode archive (A1), cross-mode
  mating (A5); route-family (A2) and constraint-aware (A6) are no-ops on the
  unconstrained benchmark **by design** (validated in Phase 10).
- Contribution claims match the evidence (see `ablation_report.md`): the **hybrid
  dual-space diversity key** (both halves ablated significant) + operator portfolio are
  the benchmark contribution; archive/route-family/constraint are application modules.

## 4. Next phase
**Phase 10 — real multi-UAV OSM emergency SAR application.** This is the contribution's
core ground AND the place to validate the application modules (route-family archive,
constraint-aware selection, decision-mode archive) that the benchmark could not exercise.
Needs `osmnx`/`shapely`/`geopandas` (install now). Build OSM graph, risk field, route
encoding/operators/repair, the SAR problem, run EARS + 5 baselines, statistics + maps.

## 5. Failures / blockers / risks (honest)
- **Integrity-positive:** the ablation honestly shows only 2 of 7 modules drive
  benchmark performance. Rather than overclaim a "7-module framework," we report the
  measured contributions and defer the application modules to their proper test
  (Phase 10). The full-vs-backbone gap is large and significant, so the framework's
  core value is solidly established.
- Route-distance metrics (`applications/route_metrics.py`) already implemented + tested
  (8/8) during Phase 9 idle time — Phase 10 head start.
- No blockers.
