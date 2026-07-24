# Phase 3 Report — EARS-MMOEA Prototype

## 1. Completed
All seven modules implemented and integrated into a runnable algorithm that
subclasses the shared `Algorithm` interface and is registered as `EARS_MMOEA`:

1. **Dual-Space Equivalence-Aware Fitness** (`equivalence_fitness.py`):
   constraint-aware non-dominated sort (vectorised), objective & decision crowding,
   Special Crowding Distance (SCD, Yue 2018), niche-rarity-boosted diversity.
2. **Three-Archive System** (`archives.py` + `route_family_archive.py` scaffold):
   Pareto-objective archive (objective-crowding truncation) + decision-mode archive
   (decision-crowding truncation); route-family archive ready for Phase 10.
3. **Adaptive Multimodal Niching** (`niching.py`): silhouette-selected k-means modes,
   adaptive niche radius, occupancy entropy, cheap nearest-centre assignment.
4. **Within-/Cross-Mode Mating** (`ears_mmoea.py`): entropy-adaptive cross-mode
   probability (more cross-mode when modes collapse).
5. **Constraint-Aware Selection** (`constraint_handling.py`): epsilon-relaxation
   schedule + boundary-near preservation (pass-through on unconstrained MMF).
6. **Adaptive Operator Portfolio** (`operators.py`): SBX+PM, DE/rand, DE/current-to-best,
   Gaussian, mode-interpolation; probability-matching bandit with credit assignment.
7. **Environmental Selection** (`selection.py`): constraint-aware fronts + equivalence
   diversity truncation. All modules expose ablation switches (Phase 9).

## 2. Files generated
`algorithms/{equivalence_fitness,archives,niching,operators,constraint_handling,
selection,route_family_archive,ears_mmoea}.py`; real `tests/test_archives.py`.

## 3. Sanity check (pop=100, 15k evals — quick, untuned)
| Problem | IGD | IGDX | branches | result |
|---|---|---|---|---|
| MMF1 (1 PS) | 0.0059 | 0.0756 | — | converges, covers PS |
| MMF5 (2 PS) | 0.0053 | 0.1251 | lower=49 / upper=49 | **both equivalent PS branches found, balanced** |

- Operator bandit active (probability mass spread across all 5 operators).
- `pytest tests/` → **35 passed, 3 skipped**; vectorised non-dominated sort verified
  against brute force on 20 random constrained cases.
- The MMF5 balanced 49/49 branch coverage is the core MMOP behaviour: the algorithm
  does **not** collapse onto a single Pareto set.

## 4. Next phase
**Phase 4 — baseline implementation & unified interface.** Port the 5 fixed baselines
(MO_Ring_PSO_SCD, DN-NSGA-II, Omni-optimizer, CPDEA, MMEA-WI) to Python behind the
shared `Algorithm` interface, with the MMF validation gate (Phase 2/4) and a baseline
sanity-check harness; identical pop/budget/seed protocol.

## 5. Failures / blockers / risks (honest)
- **Bug fixed:** polynomial mutation emitted nan-power warnings from the unused
  `np.where` branch → clamped branch bases (results were already correct).
- **Performance fix (important):** the initial pure-Python O(n²) non-dominated sort
  made a single run >90s. Vectorised the domination matrix → **~25× faster (3.6s/run)**,
  verified equivalent to brute force. This was essential before the 30-run Phase 7 study.
- **Open item:** final solution set is the non-dominated union of population + both
  archives (richer PS coverage); this is standard archive reporting and is documented,
  but Phase 5 metrics will confirm it does not distort comparisons (all algorithms
  report their final solution set the same way).
- No blockers.
