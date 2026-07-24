# Parameter Analysis Report (Phase 6)

## Protocol
- **Validation subset only:** MMF1, MMF2, MMF5 (from `configs/benchmark.yaml`).
  The final test set (full MMF1-8, Phase 7) is **never** used for tuning.
- **Method:** one-factor-at-a-time (OFAT) around a base config; per value, mean IGD
  (convergence) + IGDX (decision diversity) over 3 independent runs, normalised per
  problem, balanced score `0.5*nIGD + 0.5*nIGDX`; pick the minimiser (ties -> closest
  to default).
- **Search budget:** pop=100, 15000 evaluations (reduced for tractability), single-
  threaded. Selected values are then frozen at the protocol population (200).

## Swept parameters and chosen values
| Parameter | Range | Chosen | Note |
|---|---|---|---|
| `niche_boost` | 0, 0.25, 0.5, 1.0 | **1.0** | clear benefit: IGDX 0.071 @1.0 vs 0.094 @0 — validates the equivalence-fitness niche boost (Module 1) |
| `cross_mode_mating_prob` | 0, 0.2, 0.3, 0.5 | **0.2** | cross-mode mating helps (IGD 0.0069 @0 vs 0.0060 @0.2) |
| `decision_mode_archive_ratio` (×pop) | 0.25, 0.5, 1.0 | **0.25** | -> archive size 50 at pop 200 |
| `max_modes` | 5, 8, 12, 20 | **5** | small cap best on the 2-branch validation problems; also cheaper |
| `clustering_update_freq` | 1, 5, 10 | **10** | see below |
| `operator_lr` | 0.05, 0.1, 0.2 | **0.05** | slower bandit adaptation slightly better |

`restart_ratio` / random-immigrants are **not** swept: archive-guided restart is a
Phase 8 enhancement and is currently inert in the main loop, so tuning it would be
meaningless (an OFAT smoke confirmed a perfectly flat curve). Left at default.

## clustering_update_freq -- a documented, budget-aware refinement
The reduced-budget OFAT marginally favoured `freq=1` (IGDX 0.0733) over `freq=10`
(0.0753) -- a difference well within the 3-run noise. A **full-budget re-check on the
validation problem MMF5** (pop=200, 50000 evals) showed `freq=10` is **both faster
(12.3s vs 15.6s) and better (IGDX 0.0741 vs 0.0860)**: the `freq=1` edge overfit the
reduced search budget. We therefore froze **`freq=10`**. This check used only a
validation problem (MMF5) -- no test-set leakage -- and gives a ~order-of-magnitude
cheaper niching schedule, which keeps the 30-run Phase 7 protocol tractable.

## Frozen configuration
`configs/selected_params.yaml` (pop_size=200, pareto_archive=200,
decision_mode_archive=50, niche_boost=1.0, cross_mode_mating_prob=0.2, max_modes=5,
clustering_update_freq=10, operator_lr=0.05, ...). **Used unchanged** for Phase 7
benchmark, Phase 9 ablation, and the UAV application.

## Artefacts
- `results/summary/parameter_analysis.csv`
- `results/figures/parameter_sensitivity.png` / `.pdf`
- `configs/selected_params.yaml` (frozen)

## Honesty notes
- The validation OFAT shows EARS is well-behaved and that its distinctive components
  (niche boost, cross-mode mating) measurably help -- early evidence the modules are
  not decorative (the ablation in Phase 9 tests this rigorously).
- Some sweeps are non-monotonic at 3 runs (noise); choices were made on the balanced
  score with default-proximity tie-breaking, and the one consequential tie
  (`clustering_update_freq`) was resolved by an explicit full-budget validation check.
