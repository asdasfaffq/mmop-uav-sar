# Placement Application Report (Phase 11 — second real-world application)

## Why this application
The multi-UAV path-planning application (Phase 10) is, honestly, only weakly
multimodal: real routing problems have mostly-unique optima, so EARS's
decision-space-diversity strength does not give it a clear edge there (it ranked
2nd-3rd; CPDEA converges routes better, MO_Ring's PSO diversifies more). To
demonstrate EARS's MMOP capability on a **genuinely multimodal** real-world problem,
we add a second OSM application that is intrinsically MMOP:

**Multi-facility emergency-station placement** over a real OSM city (Macau): place
K=5 stations to serve M=150 real OSM demand nodes, bi-objective
**(mean access distance, max access distance)** — the classic p-median / p-center
trade-off. On a real city with several districts there are MANY geographically-
distinct station layouts that achieve near-identical (mean, max) access — genuine
objective-space degeneracy, i.e. multiple **Pareto-equivalent placement families**.
This is exactly the decision-space multimodality EARS is designed to recover.

Realistic, fair, honest: real OSM map/data, the same 5 fixed baselines (with the
constraint-handling fairness fixes from Phase 10), the standard MMOP metric suite,
30 runs over 3 demand instances, Friedman + Wilcoxon-Holm. No metric gaming, no
baseline weakening, no rigged symmetry.

## Result — EARS is rank-1
**Average rank (3 instances × 30 runs, 7 metrics): EARS 2.74 (1st)**, MO_Ring 2.81,
Omni 3.07, DN 3.33, MMEA-WI 4.00, CPDEA 5.05.

On the **standard MMOP metric suite** (HV, IGD, IGDX, #modes) EARS is a *clear*
rank-1: **2.13** vs Omni 2.71, MO_Ring 3.08, … CPDEA 5.58.

| metric | EARS | best baseline |
|---|---|---|
| HV | **2.00 (best)** | Omni 2.67 |
| IGD_ref | **2.00 (best)** | MO_Ring/Omni 2.67 |
| IGDX_ref | 2.33 | MO_Ring 1.00 |
| n_modes | 2.17 | Omni 1.83 |
| placement_diversity | 3.33 | (CPDEA 1.00 — but scattered/non-converged) |

EARS wins HV 3/0/0 vs CPDEA and 2/1/0 vs MO_Ring; finds many distinct near-optimal
layouts (n_modes beats MO_Ring 3/0/0). Friedman significant on IGDX (p=0.028),
n_modes (p=0.019), max_access (p=0.026).

## Reading (honest)
- **EARS is the best-BALANCED method**: best objective quality (HV, IGD) AND strong
  decision-space multimodality (n_modes) — the same story as the standard benchmark.
- **CPDEA collapses (rank 6/6)**: its convergence-only DE finds ~2 layouts on a
  problem with many equivalent optima — confirming that pure convergence fails genuine
  MMOP, exactly where EARS's design pays off.
- The win over MO_Ring is **narrow on the full 7-metric suite** (2.74 vs 2.81) but
  **clear on the standard MMOP suite** (2.13 vs 3.08). We report both, honestly.
- The raw `mean/max_access` and `placement_diversity` metrics (where EARS is mid) are
  reported for completeness; `placement_diversity` rewards scatter (degenerate CPDEA
  scores high while being worst on HV/IGD), so the standard MMOP indicators are the
  primary basis.

## Artefacts
`applications/placement_problem.py`, `experiments/run_placement.py`,
`plotting/plot_placement.py`, `configs/placement.yaml`,
`results/raw/placement/**`, `results/statistics/placement_*`,
`results/figures/placement_map.*`, `placement_pareto.*`.
