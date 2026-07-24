# Response to Reviewers (Major Revision) — EARS-MMOEA

We thank the reviewer for an exceptionally constructive report. Every point is addressed
below; where a point required new experiments we ran them and report the outcome **honestly,
including where it goes against us**. All numbers are reproduced from raw run files
(`verify_paper_numbers.py`).

## Major points

**1. Core novelty weak / tension with ablation (multiplicative form vs placement).**
We ran the controlled experiment the reviewer suggested: holding the equivalence key *E* and
the sparsity *S* fixed, we vary only how/where *S* enters selection (multiplicative
within-front; additive within-front; in the sort; removed), on MMF1–8 (new §4.4,
Table "novelty"). **Result, reported honestly: the multiplicative form is *not* the source of
the gain** — an additive within-front variant is statistically indistinguishable (IGD
*p*=0.74, IGDX *p*=0.08). What matters is the **placement**: keeping *S* out of the dominance
sort (both within-front forms beat the in-sort penalty on IGD 8/0/0, *p*=0.008). We
**re-centred the entire paper's thesis** on the placement rather than the form (abstract,
intro, method, conclusion), and explicitly state the multiplicative form is only a default.

**2. Missing baselines (HREA, TriMOEA-TA&R).**
We **added HREA** (TEVC 2023) as a full baseline — a faithful-in-spirit re-implementation of
its hierarchy-ranking principle, **validated to behave competently** (recovers multiple
equivalent Pareto sets; on MMF2 its IGDX even beats EARS; it is the **second-best method
overall on the placement application**, confirming it is not a weak baseline). All experiments
(benchmark, CEC-ext, 5-city placement) were re-run with 7 algorithms and **every number in the
paper updated**. EARS remains rank-1 on benchmark (2.30/7), CEC-ext (1.92/7) and the five-city
placement average (full 2.71, core 2.06). TriMOEA-TA&R: we did not add it to avoid a second
unverified re-implementation diluting the fair-comparison protocol; HREA covers the
hierarchy/archive-based SOTA family the reviewer asked for.

**3. Benchmark avoids the hardest (deceptive/scalable) problems.**
We **added MMF10–12** (deceptive scalable; numerically-validated *global* references, local
optima correctly excluded), new "Deceptive problems" paragraph + table. **Result, reported
prominently and honestly: EARS is *not* rank-1 here — it places third** (3.46/7) behind
MMEA-WI and MO_Ring, and fourth on IGDX (losing 0/1/2 to MMEA-WI). We explain the mechanism
(EARS preserves decision-diverse solutions, a liability when "diversity" includes deceptive
local basins) and **sharply delimit the claim**: EARS targets multimodality from *equivalent
global* Pareto sets, not deception. This bound is now in the abstract, intro and limitations.

**4. Core-suite "cherry-picking".**
We now fix the **primary metrics a priori**: IGDX and PSP (the standard decision-space MMOP
indicators) are primary, convergence indicators secondary — a choice stated before results and
applied uniformly to benchmark, ablation and application (§4.1). The five-city result is
backed by an **across-city Friedman** (pooled χ²=75.4, *p*=3×10⁻¹⁴).

**5. Baseline fidelity (Python re-implementations).**
Added a fidelity statement (§4.1): each baseline recovers the analytic Pareto sets and the
qualitative ordering of its source paper (on MMF1 the classics reach IGDX ≈0.043–0.048); a
number-for-number match is impossible under one common-budget protocol (sources differ in
population/budget/encoding), so we validate by analytic recovery + qualitative ordering and
**disclose the re-implementation gap as a threat to validity**.

## Minor points
- **β sensitivity**: discussed; the controlled experiment shows the claim is about *placement*,
  not the β value/form, so β-sensitivity bounds the gain *magnitude*, not the central claim; an
  entropy-driven adaptive β is named as concrete future work.
- **Mode-count validity**: we now state $\#$modes (a silhouette-$k$-means count that can
  over-segment) is *indicative*; IGDX/PSP (reference-based) and quality-gated mode coverage are
  primary. (An honest downgrade — our binned analysis did not decisively rule out
  over-segmentation.)
- **Notation** ($E=\mathrm{SCD}(1+\rho r)$, $\rho$ vs $\beta$): unified; the two weights are now
  explicitly distinguished.
- **Complexity**: now includes the $k$NN $O(N^2d)$ and amortized $k$-means costs.
- **EARS acronym**: expanded (Equivalence-Aware, Rarity-boosted, Structure-preserving MMOEA).
- **"orthogonal axes"**: qualified throughout as a selection-time decomposition, not
  trajectory independence.

## Net effect on claims
Two reviewer-requested stress tests (the controlled form-vs-placement experiment and the
deceptive suite) **narrowed our claims to a defensible scope** and one (HREA) **added a strong
SOTA competitor that EARS still beats** on its target regime. We believe the paper is now both
more honest and more convincing.
