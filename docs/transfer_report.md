# Transferability Report — is within-front placement a portable design rule?

Date: 2026-07-28. Script: `experiments/run_transfer.py`, analysis:
`experiments/analyze_transfer.py`. Raw: `results/raw/transfer/**`,
statistics: `results/statistics/transfer_*.csv`.

## Why this experiment

The controlled-attribution results (`run_novelty.py`, `run_insort_sweep.py`) are all
*internal to EARS-MMOEA*, so a reviewer can read them as an ablation of our own
framework rather than as a claim about MMOEA selection in general. This probe moves
the **same** sparsity signal `S`, in the **same** within-front placement, onto three
**foreign** backbones and asks whether the benefit follows the placement.

## Design (fairness, stated up front)

| control | setting |
|---|---|
| backbones | DN-NSGAII (CEC 2016), Omni-optimizer (EJOR 2008), MO_Ring_PSO_SCD (TEVC 2018) |
| change | backbone diversity key `d` → `d * (1 + beta * S)`; **nothing else** |
| placement | `S` acts only inside an already-formed front; no dominance sort is touched |
| `beta` | **0.5, EARS's frozen value — no per-backbone tuning** (deliberately conservative) |
| `S` | verified **bit-identical** to EARS's internal sparsity term, not a re-implementation |
| pairing | algorithm-independent seeds ⇒ both arms start from the *identical* population per run index |
| protocol | MMF1–8, 30 runs, pop 200, 50 000 evaluations — the frozen benchmark protocol |
| statistics | paired Wilcoxon signed-rank per problem, Holm-corrected over the 8 problems |

**Integrity check.** The three `*_base` arms reproduce the already-reported
`benchmark` runs **bit-for-bit** (720 runs, 0 metric mismatches), confirming the
switch is a true no-op when off and that no previously published number moved.

## Result — the rule transfers to all three backbones

W/T/L is the +WFS arm vs the untouched backbone (Holm, α = 0.05):

| backbone | IGDX (W/T/L) | PSP (W/T/L) | IGD | HV | mean IGDX gain |
|---|---|---|---|---|---|
| DN-NSGAII | **4/4/0** | **4/4/0** | 0/8/0 | 0/8/0 | **+17.4 %** |
| Omni-optimizer | **3/5/0** | **4/4/0** | 0/8/0 | 0/8/0 | **+10.8 %** |
| MO_Ring_PSO_SCD | **5/3/0** | **5/3/0** | 0/8/0 | 0/6/**2** | **+2.0 %** |

- **Zero losses on both decision-space metrics across all three backbones.**
- Largest gains on the hard multi-modal problems: DN-NSGAII IGDX −53.8 % (MMF4) and
  −59.5 % (MMF8); Omni −38.8 % (MMF4), −49.7 % (MMF8).
- **Convergence is essentially unpaid for**: 22 of 24 backbone×metric cells on IGD/HV
  are ties.
- The third backbone is a **different search paradigm** (ring-topology PSO with an
  external archive, not an NSGA-II derivative), so the rule is not an artefact of the
  NSGA-II environmental-selection template.

## Honest qualifications

1. **The effect is an order of magnitude smaller on MO_Ring_PSO_SCD** (IGDX gains
   1.7–5.6 %, vs 9–59 % on the NSGA-II family). Plausible reason: SCD already fuses
   decision-space crowding, so the added signal is partly redundant. Reported as is;
   we do not present the three backbones as equally improved.
2. **MMF2 and MMF3 are bit-for-bit unchanged on MO_Ring_PSO_SCD.** Diagnosed
   (not assumed): on those two problems the external archive peaks at 20–21 members
   against a capacity of 200, so the capacity-pruning path where the term acts **never
   executes** (0 of 249 generations). On MMF4/MMF8 the archive sits at capacity for
   237/164 generations and the term produces the largest gains. The effect therefore
   appears exactly where the mechanism can act and is exactly absent where it cannot —
   this is mechanism evidence, but it also means the PSO result rests on 6 of 8
   problems, and the report says so.
3. **Two significant HV losses** (MO_Ring_PSO_SCD, MMF4 and MMF7). They are
   statistically significant after Holm but the magnitude is ~1e-5 absolute
   (−0.0076 % and −0.0073 % relative). Reported as significant-but-negligible in
   magnitude, not dismissed as noise.
4. **Non-significant regressions exist**: DN-NSGAII IGDX on MMF2 (+11.8 % worse,
   tie) and Omni on MMF3 (+8.2 % worse, tie). The rule is not uniformly beneficial
   per problem; the claim is a distributional one over the suite.
5. **`beta` was not re-tuned per backbone.** This is conservative for the positive
   claim (the gains are not a tuning artefact) but means the reported numbers are a
   *lower bound* on what per-backbone tuning might give — we do not claim optimality.

## The in-sort counterfactual on foreign backbones — and why its raw numbers overstate the case

An in-sort arm (same `S`, fused into a global key `-conv + beta*S` that overrides front
precedence, mirroring EARS's `in_sort_pure_s`) was added for the two NSGA-II backbones.
`MO_Ring_PSO_SCD` gets no in-sort arm: its external archive is a single non-dominated
front, so "across front boundaries" is undefined there.

At `beta = 0.5` the in-sort arms collapse on all 8 problems for both backbones
(IGDX 0/0/8, PSP 0/0/8, IGD 0/0/8, HV 0/0/8; Holm p ≈ 1.5e-8), and within-front beats
in-sort 8/0/0 on every metric.

**This must not be read as the size of the placement effect.** Two checks against
over-claiming:

1. **Scale mismatch with our own internal evidence.** Inside EARS the same in-sort
   substitution degrades IGD by roughly 20× on MMF1 and is nearly neutral on MMF8
   (`results/raw/insort_sweep`). On a bare backbone it degrades IGD by ~183×. The
   difference is not the placement: EARS still has its Pareto archive, niching and
   operator portfolio maintaining convergence, whereas a bare backbone has nothing
   left once the dominance sort loses precedence. The bare-backbone in-sort arm is
   therefore a *stronger intervention* than the within-front one, not a like-for-like
   counterfactual.
2. **Single-weight in-sort is a strawman risk.** A single `beta` can be dismissed as
   chosen to fail — exactly the objection `run_insort_sweep.py` was written to answer
   inside EARS. The transfer probe therefore sweeps the in-sort weight over
   `beta ∈ {0.05, 0.1, 0.25, 0.5, 1.0}` on both backbones. The claim to be defended is
   the weaker, honest one: *no in-sort weight recovers the within-front result*, i.e.
   the within-front points dominate the entire in-sort weight curve. If some weight
   does close the gap, that will be reported and the placement claim narrowed
   accordingly.

### Sweep result (β ∈ {0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16}, both backbones)

The in-sort curve improves monotonically up to β ≈ 2, then **saturates** — three
consecutive points are flat (DN-NSGAII IGDX 0.1109 → 0.1082 → 0.1079 at β = 4, 8, 16).
The curve therefore turns *within* the swept grid, which is what makes the claim
defensible rather than truncated.

| β | 0.05 | 0.5 | 1 | 2 | 4 | 8 | 16 | within-front |
|---|---|---|---|---|---|---|---|---|
| DN-NSGAII IGDX | 0.917 | 0.562 | 0.433 | 0.233 | 0.111 | 0.108 | **0.108** | **0.053** |
| DN-NSGAII IGD | 0.665 | 0.603 | 0.481 | 0.260 | 0.080 | 0.072 | **0.068** | **0.0032** |

**Verdict — the defensible claim holds, in its weaker form:** across all 9 in-sort
weights × 8 problems × 2 backbones, within-front placement records **zero losses**. No
in-sort weight recovers the within-front result.

**But the margin must be reported honestly, not as the β = 0.5 collapse:**

1. At the *strongest* in-sort weight the IGDX gap narrows to a factor of 1.0–4.4,
   not the 8–17× implied by β = 0.5. Per problem (β = 16): DN-NSGAII ranges from
   1.09× (MMF5) to 4.38× (MMF8); Omni from **0.97× (MMF5 — in-sort is nominally
   *better*, though not significantly)** to 3.52× (MMF7).
2. The Holm-corrected W/T/L degrades accordingly: on Omni it falls from 8/0/0 at
   β = 0.5 to **4/4/0** at β = 8–16. Half the problems become ties. Still no losses,
   but "within-front dominates in-sort" is only true in the never-loses sense at the
   best weight, not in the wins-everywhere sense.
3. **The IGD gap, by contrast, stays large at every weight** (21–25× at β = 16). This
   is the more robust half of the finding: in-sort placement can be pushed to
   approach within-front *coverage*, but only by abandoning convergence.

The honest headline is therefore: *a decision-space sparsity signal placed in the sort
can be tuned to recover much of the coverage benefit, but never without a large
convergence penalty, and never beating within-front placement on any problem tested;
within-front obtains the coverage essentially for free.* The β = 0.5 collapse should
**not** be quoted as the size of the effect.

### Correction to the previously submitted manuscript

The same truncation flaw exists in the **already-submitted** version. Its Figure 8 /
Section "Placement is the decisive factor" claims the within-front point "dominates
the entire in-sort curve", but the internal EARS sweep also stopped at λ = 1, where
both axes were still improving monotonically (IGD 0.0808 → 0.0125, IGDX 0.1492 →
0.0656 over λ ∈ [0.05, 1]). As submitted, that sentence was supported only for the
swept segment. The internal sweep is being extended to λ = 32 and the sentence must be
restated against the true turning point before resubmission.

## Consequence for the paper's positioning

The contribution can be stated one level above the framework: **where a decision-space
diversity signal is applied in the selection layer is a portable design decision**,
demonstrated on three published MMOEAs from two search paradigms, with the framework
(EARS-MMOEA) as the realization rather than the claim. This is the positioning change
that answers the "this is an ablation, not a contribution" reading, provided the
in-sort transfer arm above is added.
