# Corrected ISAAC 2026 Idea Report

**Target paper**: EARS-MMOEA / multimodal multi-objective optimization with real OSM emergency-facility placement.
**Date**: 2026-06-25.
**Correction**: the previous temporal-separator direction was the wrong paper. This report is for the user's actual method.

## One-Line Verdict

This is a strong empirical-algorithm paper, not a theory separator paper. For ISAAC 2026, the viable framing is **Experimental Algorithms / Combinatorial Optimization**:

> Within-front decision-space sparsity selection breaks the usual convergence/diversity trade-off in multimodal multi-objective optimization, and EARS-MMOEA validates the principle on benchmarks and a real OSM emergency-facility placement problem.

## Why This Is the Correct Paper

The project matches the user's description:

- `docs/final_audit_report.md` verifies benchmark EARS average rank **2.20**, rank-1.
- It verifies real OSM emergency-facility placement average rank **2.74**, rank-1.
- It verifies placement core-suite average rank **2.13**, rank-1.
- It reports all results as code-generated from raw CSVs, with frozen parameters, common seeds, and no baseline weakening.

## Innovation Core

The paper should not lead with "we propose a new MMOEA with seven modules." That sounds incremental.

The paper should lead with:

1. **Algorithmic principle**: decision-space sparsity belongs in within-front selection, not in dominance sorting.
2. **Controlled isolation**: same sparsity signal, same backbone, only placement changes; within-front placement dominates the in-sort trade-off curve.
3. **Mechanistic explanation**: dominance rank carries convergence; within-front key adds decision-space coverage without promoting dominated solutions.
4. **System realization**: EARS-MMOEA implements this principle with equivalence-aware diversity, archives, mode-aware mating, and operator portfolio.
5. **Empirical strength**: rank-1 on standard MMOP benchmark and rank-1 on real OSM emergency-facility placement.

## ISAAC Fit

### Strengths

- ISAAC CFP includes **Experimental algorithms**, **Algorithms and data structures**, **Combinatorial optimization**, and **Scheduling/resource allocation problems**.
- The real OSM placement task is a clean combinatorial optimization application.
- The method is CPU-only, reproducible, and benchmarked under common-budget/common-seed protocols.
- The controlled placement experiment gives an algorithm-design principle rather than only a performance table.

### Risks

- ISAAC is theory/algorithms-heavy. A pure evolutionary-computation performance paper may be viewed as better suited to SWEVO/TEVC/GECCO unless the contribution is rewritten as an algorithmic principle.
- A 12-page LIPIcs paper cannot carry all journal-style modules, figures, applications, ablations, and limitations.
- "Rank-1 in real application" is strong evidence, but not by itself an ISAAC-level contribution unless tied to a general algorithmic insight.

### Recommendation

Proceed only if the ISAAC version is rewritten as a compact experimental-algorithms paper. Do not submit the current long SWEVO-style manuscript unchanged.

## Strong-Accept Story for ISAAC

Suggested title direction:

> Within-Front Diversity Selection for Multimodal Multi-Objective Optimization

or

> Equivalence-Aware Within-Front Selection for Multimodal Multi-Objective Optimization

Main thesis:

> The placement of the decision-space diversity signal is the decisive algorithmic choice: using it only within a non-dominated front preserves front precedence and avoids the convergence loss caused by in-sort fusion.

Minimal theorem/proposition:

> In Pareto front-by-front selection, any non-negative within-front key preserves dominance-front precedence: no solution from a worse front can displace a solution from a better front. Therefore a decision-space sparsity signal can affect only tie-breaking inside the splitting front, while in-sort fusion can change inter-front priority.

This is not a deep theorem, but it gives ISAAC reviewers a crisp algorithmic object.

## What to Keep in 12 Pages

1. Problem: MMOP as multiple equivalent decision-space Pareto sets, motivated by facility placement.
2. Principle: diversity signal placement, with front-precedence proposition.
3. Algorithm: EARS-Core first; EARS-Full only as the realized system.
4. Controlled experiment: within-front vs in-sort trade-off curve, plus additive/multiplicative non-importance.
5. Benchmark: MMF1-8 and CEC extension, grouped objective-space and decision-space ranks.
6. Real application: OSM emergency-facility placement rank-1, with one figure and one rank table.
7. Boundaries: deceptive local Pareto sets are not the target.
8. Reproducibility: common budget, common seeds, frozen params, code-generated maps/results.

## What to Move to Appendix

- Full seven-module details.
- Full tables for all metrics.
- Hyperparameter sweeps.
- Complete ablation table.
- Full UAV/SAR supplementary application if not headline.
- Porting details for all baselines.
- Extra figures.

## Claims That Are Safe

- EARS-MMOEA is rank-1 on the standard MMOP benchmark by verified average rank.
- EARS-MMOEA is rank-1 on real OSM emergency-facility placement by verified average rank.
- EARS is the only algorithm top-2 in both objective-space and decision-space groups on MMF.
- Within-front placement dominates the tested in-sort trade-off curve.
- Additive vs multiplicative within-front form is not the source of the gain.
- The method is scoped to equivalent global Pareto sets, not deceptive local Pareto sets.

## Claims to Avoid

- Do not claim "solves MMOP" broadly.
- Do not claim dominance diversity is free; the manuscript already reports small convergence cost.
- Do not claim every module is equally novel. The central novelty is signal placement.
- Do not pool correlated indicators into one all-metric rank.
- Do not oversell the real application as a theoretical proof of superiority.

## Immediate Action Plan

1. Create a LIPIcs ISAAC version under a new folder, not by overwriting the SWEVO manuscript.
2. Compress the paper around the principle: within-front selection vs in-sort fusion.
3. Add a short proposition and proof about front-precedence preservation.
4. Put EARS-Core in the main text; EARS-Full modules in a compact table.
5. Keep only two result tables in the main text: benchmark grouped rank and OSM placement rank.
6. Add one real OSM figure.
7. Compile and check body length <= 12 pages.

