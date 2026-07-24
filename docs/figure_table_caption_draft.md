# Figure & Table Caption Draft (Phase 12)

All figures are code-generated (matplotlib) from real data / real OSM maps; no AI
image generation. Each is saved as 300-dpi PNG + vector PDF in `results/figures/`;
tables as LaTeX in `results/tables/`.

## Figures
**Fig. 1 — Framework.** `framework.pdf`. The EARS-MMOEA pipeline: real OSM city ->
MMOP formulation -> the seven modules (hybrid dual-space fitness, three-archive
system, adaptive niching, within/cross-mode mating, constraint-aware selection,
operator portfolio, environmental selection) -> multiple Pareto-equivalent solution
families; evaluated on the MMF benchmark (rank-1) and the real OSM placement
application (rank-1).

**Fig. 2 — Real OSM application: Pareto-equivalent station layouts.**
`placement_real_map.pdf` (**headline**, real OpenStreetMap CartoDB basemap of Macau:
streets, districts, water) with demand nodes and several Pareto-equivalent emergency-
station layout families found by EARS-MMOEA -- the core MMOP visual (geographically
distinct, objective-equivalent solutions). `placement_map.pdf` is the plain-graph variant.

**Fig. 2b — Decision-space diversity vs baselines (real map).**
`placement_real_comparison.pdf`. EARS-MMOEA vs CPDEA vs MO_Ring on the real Macau map:
EARS recovers ~19 near-optimal layout modes (dense spread of good station locations),
while CPDEA collapses to ~2 and MO_Ring to ~4 (mean over runs) -- visually demonstrating
EARS's decision-space advantage. (Counts are aggregate means; a median-representative run
is shown -- no cherry-picking.)

**Fig. 3 — Coverage / risk field.** `placement_access_heatmap.pdf`. Access-distance
field over the real city for a representative layout (the application's risk/coverage
heatmap). (`risk_heatmap.pdf` is the UAV-routing supplementary variant.)

**Fig. 4 — Decision-space clustering (application).** `placement_clusters.pdf`. EARS's
non-dominated layouts cluster into distinct decision-space families.

**Fig. 5 — Pareto-front comparison.** `placement_pareto.pdf` (application, mean vs max
access) and `pareto_front_MMF5.pdf` (benchmark) -- EARS vs the five baselines.

**Fig. 6 — Decision-space clustering (benchmark).** `decision_clusters_MMF5.pdf`.
EARS recovers both equivalent Pareto sets of MMF5 (multimodality on the benchmark).

**Fig. 7 — Parameter sensitivity.** `parameter_sensitivity.pdf`. OFAT sensitivity of
EARS's key parameters on the validation subset (Phase 6).

**Fig. 8 — Ablation.** `ablation_study.pdf`. Full EARS vs module-removed variants
(incl. A9 = no sparsity bonus) over MMF1-8; the hybrid fitness and operator portfolio
are the significant benchmark drivers.

**Fig. 9 — Statistical comparison.** `cd_benchmark_IGDX.pdf` (critical-difference
diagram, IGDX) + `benchmark_average_rank.pdf` (average rank by metric). EARS is the
best-ranked method.

## Tables
- **Table 1 — Baselines.** `baselines.tex`. 2 SOTA (CPDEA, MMEA-WI) + 3 classic
  (MO_Ring_PSO_SCD, DN-NSGA-II, Omni-optimizer).
- **Table 2 — Benchmark results.** `benchmark_IGDX_summary.tex` (+ IGD/HV/PSP/...),
  mean(std) with best-marked and Holm significance.
- **Table 3 — Average rank (benchmark).** `benchmark_avg_rank.tex`.
- **Table 4 — Win/tie/loss (benchmark).** `benchmark_wtl.tex` (EARS vs each baseline).
- **Table 5 — Parameters.** `parameters.tex` (frozen EARS-MMOEA settings).
- **Table 6 — Ablation.** `ablation_avg_rank.tex` + `ablation_IGDX_summary.tex`.
- **Table 7 — Application results.** `placement_avg_rank.tex` + `placement_wtl.tex`
  (EARS rank-1 on the OSM placement MMOP).

## Headline numbers (for captions / abstract)
- Benchmark MMF1-8 (30 runs): EARS average rank **2.20** (rank-1 of 6); ties/beats
  CPDEA on IGDX/PSP, dominates IGD/HV 8/0/0.
- Ablation: hybrid sparsity bonus (A9) +11% IGDX (sig.), dual-space fitness (A3) +181%.
- Real OSM placement (3 instances x 30 runs): EARS average rank **2.74** (rank-1);
  **2.13** on the standard MMOP suite; CPDEA collapses to last (5.05).
