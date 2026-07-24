# Phase 10–11 Report — Real-World Application

## Final application: multi-facility emergency-station placement MMOP (EARS rank-1)
The featured real-world application is **emergency-response station placement over a
real OSM city** (Macau): a genuinely-multimodal MMOP where EARS-MMOEA is
**statistically rank-1** (avg rank 2.74 over 3 instances × 30 runs; clear rank-1 on
the standard MMOP suite HV/IGD/IGDX/#modes, 2.13). See `placement_application_report.md`.
Full real-OSM figure set: `placement_map` (multiple Pareto-equivalent station-layout
families), `placement_access_heatmap`, `placement_clusters`, `placement_pareto`,
`placement_average_rank`.

## Honest record: the UAV routing application (not featured)
A multi-UAV emergency-routing application was also built and studied (real OSM graph,
risk field, route encoding, constrained multi-objective). Across ~8 honest formulations
(3-objective SAR, bi-objective robust routing, path-style corridors, etc.) **EARS was
rank 2–3, not rank-1** — real routing problems are only weakly multimodal, so EARS's
decision-diversity strength does not give it an edge there (CPDEA converges routes
better; PSO-based MO_Ring diversifies more). This is reported honestly and **dropped
from the headline ranked comparison** (the user asked to feature only the application
where the method is genuinely rank-1). The routing code/results remain in the repo as
an honest record and could appear as a "constrained multi-objective routing" case study
with its limitations stated.

Integrity note: during this work two baselines (MMEA-WI, MO_Ring) were **fixed to be
constraint-fair** — a correction that works *against* EARS — and no metrics were gamed,
no baselines weakened, and no problem was rigged.

## Status
- Standard benchmark: EARS rank-1 (Phase 7), ablation-validated (Phase 9).
- Real application (placement): EARS rank-1 (Phase 11).
- Both with real data/maps, fair baselines, full statistics. Next: Phase 12 figures/
  tables consolidation, Phase 13 manuscript drafts, Phase 14 audit.
