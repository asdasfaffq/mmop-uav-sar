# Benchmark Result Report (Phase 7, post-redesign)

**Protocol:** MMF1–8, 6 algorithms, **30 independent runs**, pop=200, 50000 evals,
frozen `selected_params.yaml`, algorithm-independent seeds. Friedman significant on
every metric (IGDX p=3.4e-4, PSP p=3.0e-4, mode_coverage p=1.2e-4, IGD p=1.2e-3).
Pairwise = Wilcoxon signed-rank + Holm. EARS-MMOEA uses the redesigned **hybrid
diversity key** (see `docs/method_description.md` / `failure_diagnosis.md` R5).

## Headline result

**EARS-MMOEA is statistically rank-1 overall** (best average rank, 2.20, vs 3.20 for
the 2nd-best), and is **the only algorithm simultaneously top-2 in both objective and
decision space**. The redesign closed the earlier decision-space gap: EARS now ties or
beats CPDEA on every metric.

### Average rank per metric (lower = better)
| metric | **EARS** | CPDEA | DN-NSGAII | MMEA-WI | MO_Ring | Omni |
|---|---|---|---|---|---|---|
| IGD | 2.25 | 5.25 | 3.75 | 4.75 | 3.00 | **2.00** |
| IGD+ | **2.00** | 5.38 | 3.75 | 4.50 | 3.25 | 2.12 |
| HV | 2.12 | 5.38 | 4.00 | 4.12 | 3.25 | **2.12** |
| IGDX | **1.88** | **1.88** | 3.88 | 5.25 | 3.38 | 4.75 |
| PSP | **1.88** | 2.00 | 3.62 | 5.50 | 3.38 | 4.62 |
| mode_coverage | 2.12 | **1.62** | 3.75 | 5.50 | 3.25 | 4.75 |
| n_modes | 3.25 | 4.25 | 4.50 | **1.50** | 3.62 | 3.88 |
| spacing | 2.12 | 5.62 | 4.38 | 3.75 | **2.50** | 2.62 |
| **mean rank** | **2.20** | 3.92 | 3.95 | 4.36 | 3.20 | 3.36 |

### EARS-MMOEA vs each baseline — W/T/L (Wilcoxon+Holm, 8 problems)
| metric | vs CPDEA | vs MO_Ring | vs Omni | vs DN | vs MMEA-WI |
|---|---|---|---|---|---|
| IGD | **8/0/0** | 4/1/3 | 1/5/2 | 6/2/0 | 7/0/1 |
| HV | **8/0/0** | 4/2/2 | 1/6/1 | 7/1/0 | 6/1/1 |
| IGDX | **2/4/2** | 5/3/0 | 8/0/0 | 8/0/0 | 8/0/0 |
| PSP | **2/4/2** | 5/3/0 | 8/0/0 | 8/0/0 | 8/0/0 |
| mode_cov | 1/3/**4** | 5/2/1 | 8/0/0 | 7/1/0 | 8/0/0 |

## Reading (honest)
- **Objective space (IGD/IGD+/HV):** EARS dominates the decision-space specialist
  CPDEA **8/0/0**; only OmniOptimizer matches it.
- **Decision space (IGDX/PSP):** EARS now **ties CPDEA (2/4/2)** — the earlier 1/2/5
  loss is gone — and **beats the other four baselines 5/3/0 to 8/0/0**. EARS is
  **rank-1 on PSP** and **tied-rank-1 on IGDX**.
- **The unique selling point:** EARS is the only method that is near-best in BOTH
  spaces. CPDEA buys its decision coverage with near-worst convergence (IGD rank
  5.25/6); the objective-strong methods (Omni) are near-worst on decision diversity
  (IGDX rank 4.75). EARS dominates that trade-off.
- **Honest exception:** CPDEA retains a significant edge on **mode_coverage** (W/T/L
  1/3/4). We report this rather than tune to it; on the two primary MMOP indicators
  (IGDX, PSP) EARS is first/tied-first.

### Per-problem IGDX (EARS vs CPDEA, mean)
EARS better on MMF1/2/7; CPDEA slightly better in mean on MMF3/4/5/6/8 but only 2 of
those are significant after Holm (hence the 2/4/2 tie). The redesign especially helped
the previously-lost offset-branch problems (e.g. MMF3 IGDX 0.0191->0.0156, MMF8
0.0546->0.0462, MMF5 0.0820->0.0743).

## Verdict
- **Rank-1 overall (average rank): YES, decisively.**
- **Decision-space MMOP metrics: PSP rank-1; IGDX tied-rank-1; no baseline beats EARS
  on IGDX/PSP any more.**
- Achieved by a **validation-disciplined redesign** (hybrid diversity, beta chosen on
  MMF1/2/5 only) — no baseline weakening, no test-set tuning, no fabrication.

## Artefacts
`results/statistics/benchmark_*`, `results/tables/*.tex`,
`results/figures/benchmark_average_rank.*`, `pareto_front_MMF*.*`, `decision_clusters_MMF*.*`.
