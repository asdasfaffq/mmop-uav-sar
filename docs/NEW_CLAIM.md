# The claim that survives: within-front placement is the tuning-free, scaffolding-free option

Date: 2026-08-03. Supersedes the refuted dominance claim
(`docs/PLACEMENT_CLAIM_REFUTATION.md`). Every number below traces to a raw result file.

## Statement

> A decision-space sparsity signal can be made to work from *either* position in the
> selection layer — but only within-front placement works **without tuning and without
> relying on other machinery to repair convergence damage**. In-sort placement reaches
> comparable quality only after (i) its weight is raised by an order of magnitude and
> found by sweeping, and (ii) the surrounding algorithm independently preserves
> converged solutions. Where neither holds, in-sort never catches up.

This is a robustness/portability claim, not a superiority claim. It is weaker than the
manuscript's current headline and it is what the evidence supports.

## Evidence

### 1. Weight sensitivity — same problems (MMF1/2/5), same protocol, 30 runs

Over the identical weight range [0.25, 2]:

| placement | IGDX variation | IGD variation |
|---|---|---|
| **within-front (β)** | **1.03×** | **1.09×** |
| in-sort (λ) | 3.29× | 16.04× |

Within-front is essentially flat: IGDX 0.0422 → 0.0411 across an 8× change in β; IGD
0.00286 → 0.00311. In-sort over the same range swings IGDX 0.154 → 0.0467 and IGD
0.0658 → 0.0041. Source: `results/summary/beta_sweep.csv`,
`results/raw/insort_sweep/**`.

### 2. In-sort needs a weight an order of magnitude larger before it is competitive

On MMF1/2/5, in-sort only reaches within-front quality at **λ ≥ 2–4**, i.e. 4–8× the
within-front default β = 0.5. Below that it is catastrophically worse (λ = 0.5:
IGD 0.038 vs 0.0029, a 13× gap). Within-front's default was chosen once, on the
validation subset, and never re-tuned — including for the transfer study.

### 3. Without convergence scaffolding, in-sort never catches up at any weight

Foreign backbones (DN-NSGAII, Omni-optimizer) report the population directly — no
archive. Sweeping λ ∈ {0.05 … 16}:

- within-front records **0 losses** across 9 weights × 8 problems × 2 backbones;
- the in-sort curve **saturates** (DN IGDX 0.1109 → 0.1082 → 0.1079 at λ = 4, 8, 16)
  at 2× worse IGDX and **21–25× worse IGD** than within-front.

Inside EARS the same in-sort variant *does* catch up at λ ≥ 4 (IGD 2/0/6 against
within-front, IGDX 2/5/1) — because EARS reports the non-dominated union of population
+ Pareto archive (`algorithms/ears_mmoea.py:253-260`), so the archive repairs the
convergence damage the in-sort key inflicts on the population.

### 3b. The archive mechanism, tested causally rather than inferred (2026-08-03)

The cross-setting contrast above confounds "has an archive" with "is a different
algorithm". `experiments/run_archive_masking.py` removes the confound: inside EARS,
holding algorithm, operators, niching, budget and seeds fixed, only the *reporting rule*
is toggled. In-sort is taken at λ = 8, its strongest weight — not a weak operating point.
MMF1–8, 30 runs, 1440 runs, 0 errors.

| reported set | placement | IGD | IGDX | within-front vs in-sort |
|---|---|---|---|---|
| population ∪ archives | within-front | 0.00287 | 0.0373 | IGDX 2/5/1, **IGD 2/0/6** |
| | in-sort λ=8 | 0.00321 | 0.0380 | |
| **population only** | within-front | **0.00251** | **0.0376** | **IGDX 8/0/0, IGD 8/0/0** |
| | in-sort λ=8 | **0.05848** | **0.2423** | |

- With archives the placements are close; in-sort even wins convergence.
- Without them the within-front key is unchanged on IGDX (0.0373 → 0.0376) and its
  convergence *improves* (0.00287 → 0.00251, 8/0/0), while in-sort collapses on every
  metric and every problem (IGD 18×, IGDX 6.4× worse).
- In-sort loses **0/0/8 on all four metrics** against its own archived version;
  within-front loses none.

The within-front placement never depended on the archive; the in-sort placement's
competitiveness was entirely supplied by it. This is the mechanism, established inside
one algorithm rather than across two.

### 4. The term itself transfers, untuned, to three published MMOEAs

At the frozen β = 0.5, with no per-backbone tuning, adding the within-front term to
DN-NSGAII / Omni-optimizer / MO_Ring_PSO_SCD improves IGDX and PSP with **zero losses**
on either metric, at essentially no convergence cost (22 of 24 IGD/HV cells tie).
Two distinct search paradigms. Source: `docs/transfer_report.md`.

## Why this is publishable

The finding is now a *conditional design rule with a stated mechanism and a stated
failure mode*, validated on independent algorithms:

- **useful**: practitioners get a default that works without a weight search;
- **falsifiable and falsified in part**: we show exactly when the alternative placement
  is equally good (rich framework + tuned weight) — and we found that by testing our
  own claim to destruction;
- **portable**: demonstrated outside the framework that produced it;
- **bounded**: fails in the deceptive regime, absent where the mechanism cannot act
  (MO_Ring_PSO_SCD on MMF2/MMF3), weaker on the PSO paradigm.

## What must be deleted from the manuscript

- Figure 8 and the claim that within-front "dominates the entire in-sort curve".
- "This is the contribution" attached to that sentence.
- Any framing of in-sort placement as simply harmful.
- The skeleton isolation table's single-weight in-sort comparison, unless re-run
  across the weight grid.
