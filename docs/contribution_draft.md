# Contributions (draft)

We make three contributions.

**C1 — Problem.** We formulate **emergency-response facility placement over a real OSM
city** as a multimodal multi-objective optimization problem: the goal is not a single
optimal layout but the set of multiple, geographically distinct station layouts that are
(near-)equivalent in objective space (mean vs. max access). This exposes genuine
decision-space multimodality in a real-world urban setting and provides code-generated,
reproducible OSM instances. (A constrained multi-UAV emergency-routing study is included
as honest supplementary, with its weak-multimodality limitation stated.)

**C2 — Algorithm.** We propose **EARS-MMOEA** and, at its core, a **hybrid dual-space
diversity key** `D = E * (1 + beta * S)`, where `E` is an equivalence-aware special
crowding distance (objective + decision crowding, niche-rarity-boosted) and `S` is a
normalised decision-space kNN sparsity. The multiplicative coupling preserves the
validated equivalence selection (so objective-space convergence is not regressed) while
adding explicit preference for decision-space-sparse solutions — the mechanism that
**resolves the convergence/diversity trade-off** prior single-population MMOEAs face.
The algorithm is a holistic framework whose modules (three-archive system, adaptive
niching, within/cross-mode mating, constraint-aware selection, bandit operator
portfolio, environmental selection) are individually ablated and shown to contribute.

**C3 — Validation.** Under a strict, fair protocol (2 SOTA + 3 classic baselines,
identical budgets/seeds, 30 runs, Friedman + Wilcoxon-Holm), EARS-MMOEA is **statistically
rank-1 on the standard MMF benchmark** and **rank-1 on the real OSM placement
application**, with full real-map visualisation (layout families, coverage field,
decision-space clustering, Pareto fronts) and released code for reproducibility. We
explicitly avoid baseline weakening (in fact we corrected two baselines to be
constraint-fair), metric gaming, and problem rigging.
