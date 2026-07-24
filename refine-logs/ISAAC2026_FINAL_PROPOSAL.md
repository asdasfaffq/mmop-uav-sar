# ISAAC 2026 Final Proposal

## Problem Anchor

Multimodal multi-objective optimization needs to recover multiple decision-space solution sets that are equivalent in objective space. The key algorithmic obstacle is preserving decision-space diversity without sacrificing Pareto convergence.

## Method Thesis

A pure decision-space sparsity signal should be placed only inside the splitting non-dominated front. This preserves dominance-front precedence and gives coverage without the convergence loss caused by fusing the signal into global selection.

## Dominant Contribution

The dominant contribution is the **placement principle**:

> diversity signal inside the front, convergence in the rank.

EARS-MMOEA is the system realization and empirical validation of that principle.

## Evidence Package

- Controlled placement experiment: within-front placement dominates in-sort fusion.
- Standard MMOP benchmark: EARS average rank 2.20, rank-1.
- Real OSM emergency-facility placement: EARS average rank 2.74, rank-1; core-suite rank 2.13, rank-1.
- Protocol integrity: common budget, common seeds, frozen parameters, code-generated results, retained negative cases.

## ISAAC Readiness

**Verdict**: promising but requires a venue-specific rewrite.

The current paper is strong as a SWEVO/TEVC-style journal submission. For ISAAC, it must be shortened and sharpened around an algorithmic insight. The rank-1 real application is an important validation block, not the whole paper.

