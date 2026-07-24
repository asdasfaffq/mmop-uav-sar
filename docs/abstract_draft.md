# Abstract (draft)

Multimodal multi-objective optimization (MMOP) seeks not a single Pareto set but the
multiple, geometrically distinct decision-space solution sets that map to the (near-)
same Pareto front. Existing methods sit on a convergence/diversity trade-off:
convergence specialists collapse decision-space diversity, while diversity specialists
sacrifice objective-space quality. We propose **EARS-MMOEA**, an equivalence-aware,
structure-preserving multimodal multi-objective evolutionary algorithm whose core is a
**hybrid dual-space diversity key** that multiplies an equivalence-aware special
crowding distance by a decision-space sparsity bonus. Because the bonus is
multiplicative and acts only among non-dominated solutions, it augments decision-space
coverage **without trading away objective-space convergence** — resolving the trade-off
that limits prior MMOEAs. EARS-MMOEA further integrates a three-archive system, adaptive
niching, within/cross-mode mating, constraint-aware selection, and a bandit operator
portfolio. On the standard MMF1-8 benchmark (30 runs, Friedman + Wilcoxon-Holm),
EARS-MMOEA attains the **best average rank (2.20 of six algorithms)**, matching or
beating the decision-space SOTA on IGDX/PSP while dominating it on IGD and HV (8/0/0); a
ten-variant ablation confirms each claimed module contributes, the hybrid sparsity bonus
significantly so. We then model **emergency-response facility placement over a real
OpenStreetMap city** as a genuinely multimodal MMOP and show, on real urban data with
code-generated maps, that EARS-MMOEA is again **rank-1 (average rank 2.74; 2.13 on the
standard MMOP suite)**, finding multiple Pareto-equivalent station layouts where a
convergence-only SOTA collapses to last. All baselines, protocols, seeds, and statistics
are released for full reproducibility.
