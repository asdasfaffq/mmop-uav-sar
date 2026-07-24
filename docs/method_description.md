# EARS-MMOEA — Method Description

**Equivalence-Aware Route/Structure-Preserving Multimodal Multi-Objective
Evolutionary Algorithm.** A single-population MMOEA whose distinctive contribution is
a **hybrid diversity key** that resolves the convergence/diversity trade-off that
limits prior MMOP methods, plus a modular set of supporting components (some specific
to the constrained UAV application).

## Problem
MMOP: find solutions that approximate the Pareto front in OBJECTIVE space while
covering the multiple, geometrically distinct **decision-space pre-images** (Pareto
sets) that map to it. Prior methods sit on a trade-off curve: convergence specialists
(NSGA-II/Omni) lose decision diversity; decision-diversity specialists (CPDEA) lose
convergence (near-worst IGD).

## Core contribution — Hybrid Equivalence/Sparsity Diversity (Module 1)
Environmental selection ranks the splitting non-dominated front by a diversity key

  `D(i) = E(i) · (1 + β · S(i))`

where
- `E(i)` = **equivalence diversity** = Special Crowding Distance (Yue 2018; the larger
  of objective- and decision-space crowding) boosted by **niche rarity** (members of
  rarer decision modes scored higher);
- `S(i)` = **normalised decision-space kNN sparsity** of solution i (0..1), large for
  solutions far from their decision-space neighbours;
- `β` controls the sparsity bonus.

The bonus is **multiplicative**: it preserves the validated equivalence selection
(so convergence and easy-problem behaviour are not regressed) while *adding* explicit
preference for decision-space-sparse solutions (so hard, close-mode problems gain
Pareto-set coverage). Unlike CPDEA's additive convergence penalty on a DE search —
which keeps somewhat-unconverged solutions and damages IGD — the multiplicative bonus
acts only as a tie-break among already non-dominated solutions, so **IGD is preserved**.
Empirically this lifts EARS to rank-1 overall and ties/beats the decision-space SOTA
(CPDEA) on IGDX/PSP **without** sacrificing its objective-space dominance.
`β = 0.5` was selected on the validation subset (MMF1/2/5) as the only value improving
IGDX with no IGD regression on all three.

## Supporting components (modular; ablated in Phase 9)
2. **Three-Archive System** — Pareto-objective archive (convergence/quality),
   decision-mode archive (mode representatives), and a **route-family archive** used
   only by the UAV application.
3. **Adaptive multimodal niching** — silhouette-selected k-means decision-space modes,
   adaptive niche radius, occupancy entropy; feeds the niche-rarity term and the mating
   controller.
4. **Within-/cross-mode mating** — entropy-adaptive cross-mode mating probability
   (more cross-mode exploration when modes collapse).
5. **Constraint-aware multimodal selection** — ε-relaxation schedule + boundary-near
   preservation (active in the constrained UAV application).
6. **Adaptive operator portfolio** — SBX+PM / DE-rand / DE-current-to-best / Gaussian /
   mode-interpolation, with a probability-matching bandit on credit assignment.
7. **Environmental selection** — constraint-aware non-dominated sorting + the hybrid
   diversity key.

## Benchmark evidence (MMF1–8, 30 runs)
Statistically rank-1 overall (avg rank 2.20); rank-1 on PSP, tied-rank-1 on IGDX;
beats CPDEA 8/0/0 on IGD and HV; the only method top-2 in both spaces. Ablation
(Phase 9) isolates the contribution of each module, including **A9 (no sparsity
bonus)** which reverts the hybrid key to plain equivalence selection.

## Honest scope
On the unconstrained benchmark the benchmark-significant drivers are the **hybrid
diversity key** and the **operator portfolio**; the route-family/constraint/
decision-mode-archive modules are **application modules** validated in Phase 10 (the
benchmark cannot exercise route families or constraints).
