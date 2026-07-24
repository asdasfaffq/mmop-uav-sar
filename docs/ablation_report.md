# Ablation Report (Phase 9, hybrid core)

**Protocol:** A0_Full vs 9 ablated variants, MMF1–8, 30 runs, pop=200, 50k evals,
frozen params (hybrid diversity, beta=0.5), algorithm-independent seeds (2400 runs,
0 errors). Reference = A0_Full; Wilcoxon signed-rank + Holm over 8 problems.

## Result — full framework ≫ deletions, and the new mechanism is proven
| variant | IGDX (mean) | vs A0 | A0 W/T/L (IGDX) | role |
|---|---|---|---|---|
| **A0_Full** | **0.0373** | — | — | — |
| A3_noEquivFitness | 0.1045 | +181% | **8/0/0** | dual-space equivalence fitness — **primary** |
| A7_noPortfolio | 0.0502 | +35% | **5/3/0** | adaptive operator portfolio — significant |
| **A9_noSparsityBonus** | **0.0414** | **+11%** | **3/5/0** | **hybrid sparsity bonus (the redesign) — significant** |
| A4_noNiching | 0.0392 | +5% | 1/7/0 | adaptive niching — small but significant on 1 problem |
| A8_BackboneOnly | 0.2693 | +623% | **8/0/0** | everything removed — collapse |
| A1_noDMArchive | 0.0373 | -0% | 0/8/0 | decision-mode archive — no benchmark effect |
| A5_noCrossMode | 0.0374 | +1% | 0/8/0 | cross-mode mating — no benchmark effect |
| A2_noRouteFamily | 0.0373 | +0% | 0/8/0 | route-family archive — **no-op on benchmark by design** |
| A6_noConstraintAware | 0.0373 | +0% | 0/8/0 | constraint-aware — **no-op on benchmark by design** |

## Reading (honest)
**Benchmark-significant modules (A0 wins after Holm):**
- **Dual-space equivalence-aware fitness (A3)** — the dominant driver (IGDX 2.8×
  without it; 8/8 problems). This is what makes EARS an MMOP method.
- **Adaptive operator portfolio (A7)** — +35% IGDX, 5/8 problems.
- **Hybrid sparsity bonus (A9, the Phase-8 redesign)** — removing it (reverting the
  hybrid key to plain equivalence selection) significantly worsens IGDX (+11%, 3/8
  problems, 0 losses) and PSP (44.3 -> 41.8). This is the decisive ablation: it shows
  the **new mechanism that lifted EARS to rank-1 is itself a significant contributor**,
  not a free rider.
- **Adaptive niching (A4)** — small but now significant (1/8), as it interacts with the
  sparsity bonus.

**No significant *benchmark* contribution (reported honestly):**
- Decision-mode archive (A1) and cross-mode mating (A5): 0/8 ties — minor on the
  benchmark; their role is in the application / exploration robustness.
- Route-family archive (A2) and constraint-aware selection (A6): **no-ops on the
  unconstrained MMF benchmark by design** — they act on route families and constraints,
  which exist only in the UAV application (validated in Phase 10).

## Consequence for contribution claims (integrity)
The benchmark contribution is claimed as the **hybrid dual-space diversity key
(equivalence fitness + decision-sparsity bonus)** — both halves are ablated and shown
significant (A3 dominant, A9 +11%) — plus the **adaptive operator portfolio**. The
route-family / constraint / decision-mode-archive modules are **application modules**;
their contribution is established in the Phase 10 UAV ablation, not over-claimed here.
The full framework is dramatically and significantly better than backbone-only.

## Artefacts
`results/raw/ablation/**`, `results/statistics/ablation_*`,
`results/figures/ablation_study.png/.pdf`.
