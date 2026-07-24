# ISAAC 2026 Validation Plan

This plan converts the existing EARS-MMOEA evidence into an ISAAC experimental-algorithms submission.

## Claim 1: Signal Placement Principle

- **Main result**: within-front placement dominates in-sort fusion.
- **Evidence**: `paper/tables/novelty.tex`, `paper/tables/isolation.tex`, `insort_tradeoff.pdf`.
- **Main-text requirement**: include a concise proposition showing within-front keys preserve front precedence.

## Claim 2: Benchmark Rank-1 / Balanced Performance

- **Evidence**: `paper/tables/benchmark_avg_rank.tex`, `results/tables/benchmark_avg_rank.tex`.
- **Main-text requirement**: report objective-space and decision-space groups separately; emphasize top-2 in both, not pooled rank gaming.

## Claim 3: Real Application Rank-1

- **Evidence**: `docs/final_audit_report.md`, `paper/tables/placement_avg_rank.tex`, placement figures.
- **Main-text requirement**: present OSM emergency-facility placement as the real combinatorial optimization application; one figure plus one compact table.

## Claim 4: Reproducibility and Fairness

- **Evidence**: `docs/final_audit_report.md`, `tests/`, configs, raw CSVs.
- **Main-text requirement**: short protocol paragraph; move full audit to appendix.

## Claim 5: Scope Boundary

- **Evidence**: deceptive problem section.
- **Main-text requirement**: one paragraph: not rank-1 on deceptive local Pareto-set problems; method targets equivalent global Pareto sets.

