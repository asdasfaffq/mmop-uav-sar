# The manuscript's central placement claim is refuted by a properly-swept in-sort weight

Date: 2026-08-03. Evidence: `results/raw/insort_sweep/**` (extended to λ = 32),
`results/raw/transfer/**`. This supersedes the corresponding claim in the submitted
manuscript and in `docs/transfer_report.md`.

## What the manuscript claims

> "Placing $S$ in the sort degrades *both* convergence and coverage … the within-front
> placement lies below-left of and **dominates the entire in-sort curve on both axes**
> … The placement effect is thus robust to the in-sort weight, not an artefact of one
> comparison. **This is the contribution.**"
> — `paper/sections/experiments.tex`, §"Controlled study", Figure 8

## What a properly-swept sweep shows

The submitted sweep stopped at λ = 1, where **both axes were still improving
monotonically**. Extending it to λ = 32 (MMF1–8, 30 runs, frozen protocol):

| λ | 0.05 | 0.5 | 1 | 2 | 4 | 8 | 16 | 32 | WF_mult | NoS |
|---|---|---|---|---|---|---|---|---|---|---|
| IGD | .0808 | .0293 | .0125 | .0036 | .0032 | **.0032** | .0032 | .0032 | .0029 | .0028 |
| IGDX | .1492 | .1048 | .0656 | .0404 | .0384 | .0381 | .0381 | **.0379** | .0377 | .0403 |

Wilcoxon signed-rank, Holm-corrected over the 8 problems, reference = within-front:

| comparison | IGD (W/T/L) | IGDX (W/T/L) |
|---|---|---|
| WF_mult vs InSort λ=2 | 2/4/2 | 4/4/0 |
| WF_mult vs InSort λ=4 | **2/0/6** | 2/5/1 |
| WF_mult vs InSort λ=8 | **2/0/6** | 2/5/1 |
| WF_mult vs InSort λ=32 | **2/0/6** | 2/5/1 |

**At λ ≥ 4 the in-sort placement is statistically *better* than within-front on
convergence (losing 6 of 8 problems) and statistically indistinguishable on coverage
(5 ties, 2 wins, 1 loss).** Per-problem medians at λ = 8 confirm it: in-sort has the
better IGD on 6 of 8 problems and the differences in IGDX are in the third decimal.

The published claim therefore held **only because the sweep was truncated at λ = 1**.
The same single-weight flaw affects the skeleton isolation study
(`run_placement_isolation.py` uses the default β = 0.5 only).

## Why — the mechanism (verified, not assumed)

EARS reports the **non-dominated union of population + Pareto archive + decision-mode
archive** (`algorithms/ears_mmoea.py:253-260`). When the in-sort key scatters the
population, the Pareto archive still holds the converged solutions, so the convergence
damage never reaches the reported set. The archive repairs the very damage the
experiment was meant to measure.

This is confirmed by the contrast with bare backbones, which have no archive — the
population *is* the output:

| setting | does any in-sort weight catch within-front? |
|---|---|
| inside EARS (archive present) | **yes**, at λ ≥ 4 it matches on IGDX and beats on IGD |
| DN-NSGAII / Omni (no archive), λ ∈ [0.05, 16] | **no**, 0 losses for within-front across 9 weights × 8 problems × 2 backbones; in-sort saturates at 21–25× worse IGD |

## Consequence

1. **The claim "placement is the decisive factor, and within-front dominates the
   entire in-sort curve" cannot be made.** It is false as stated. Figure 8 and the
   surrounding paragraph must be rewritten or removed; this is not a matter of
   softening wording.
2. **The contribution as currently framed does not survive.** "This is the
   contribution" pointed at exactly the refuted sentence.
3. **What does survive** is narrower, conditional, and mechanistically explained:

   > An unpenalised decision-space sparsity signal placed in the dominance sort
   > destroys convergence *unless the algorithm independently preserves converged
   > solutions* (e.g. an external Pareto archive). Within-front placement obtains the
   > coverage benefit without that dependency and without weight tuning: it works at
   > β = 0.5, whereas the in-sort route needs a weight an order of magnitude larger,
   > found by sweeping, and only then matches.

   Supporting evidence: the transfer study (3 published MMOEAs, 2 paradigms, 0 losses
   at any weight) is exactly the archive-free case, and it is *unaffected* by this
   refutation — it compares "term present vs absent", not placement.

4. **Robustness/portability, not superiority, is the honest headline.** Within-front
   is the placement that works without tuning and without surrounding scaffolding.
   That is a real, useful, defensible finding — but it is materially weaker than what
   the manuscript currently claims, and it changes what venue is realistic.

## Status of the ASOC repositioning plan

`docs/REVISION_PLAN_ASOC.md` was written assuming the placement claim held and only
needed external validation. That assumption is now false. The plan's evidence chain
must be rebuilt around the conditional claim above before any submission. Blocks E3
(transfer) and E5 (deceptive regime) survive intact; E1/E2 (internal attribution) must
be re-run in reporting terms and largely re-interpreted.
