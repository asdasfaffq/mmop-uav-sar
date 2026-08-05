# Revision plan — from a JCDE reject (scope + novelty) to an acceptable ASOC paper

Date: 2026-07-28. Decision taken on the user's instruction to choose.

## Diagnosis: why the current manuscript reads as "not novel"

The manuscript is already placement-led (intro's key insight, first Results subsection).
The reject was not caused by a wrong thesis. It was caused by **the thesis and the
artefact competing**:

The paper currently tries to be three papers at once.

| strand | what a reviewer applies | verdict it invites |
|---|---|---|
| (a) placement as a controlled attribution | "is the finding general?" | *all evidence is inside your own framework → this is an ablation* |
| (b) EARS-MMOEA, a 7-module framework beating 5 baselines | "what is algorithmically new?" | *sparsity-in-selection is not new; you already conceded intra-front priority* |
| (c) five-city OSM facility-placement application | "is the application real?" | passes, but is read as a demo attached to (b) |

Strand (b) is what triggers the novelty standard the paper cannot meet, and it
simultaneously drowns strand (a), which is the part that is actually defensible.
A 35-page single-column manuscript with a 7-module framework diagram *announces*
"new algorithm paper", so reviewers grade it as one.

## Decision

**Demote the algorithm. Promote the design rule. Keep the application.**

- **Target: Applied Soft Computing** (Elsevier, 1区). Scope fits natively — no
  "out of scope" risk, and MMOP + real application is standard fare there.
  Fallback after ASOC: EAAI. Do not send to SWEVO/Information Sciences: with the
  intra-front priority already conceded, they will grade on mechanism novelty.
- **Claim**: *where* a decision-space diversity signal is applied in the selection
  layer is a **portable design decision**, not a property of one framework —
  established by controlled attribution, cross-algorithm transfer, and a stated
  failure regime.
- **EARS-MMOEA becomes the realization**, not the contribution. It stops being the
  headline and becomes "the framework in which the rule was first isolated".

This is not a downgrade of the work. It is the only framing in which the evidence
that actually exists is *sufficient* for the claim being made.

## Evidence chain (all of it already exists or is now run)

| # | evidence | status | role |
|---|---|---|---|
| E1 | within-front vs in-sort vs additive, same E and S, inside EARS (`run_novelty`) | done | isolates placement from algebraic form |
| E2 | in-sort weight sweep inside EARS (`run_insort_sweep`) | done | kills the strawman objection |
| E3 | **transfer to 3 published MMOEAs, 2 search paradigms (`run_transfer`)** | **done** | **load-bearing: makes the rule portable, not an ablation** |
| E4 | in-sort transfer + weight sweep on foreign backbones | running | supports the *negative* half of the rule, honestly bounded (see below) |
| E5 | deceptive counter-regime (`run_deceptive`) | done | states where the rule does NOT hold — buys credibility |
| E6 | benchmark rank-1 vs 5 baselines + ablation | done | demoted to "the realization is competent", not the claim |
| E7 | five-city OSM facility placement | done | shows the rule survives outside benchmark geometry |
| E8 | high-dimensional study | done | scope boundary |

E3 is the piece that was missing when JCDE reviewed it. Nothing else needs new runs.

## Structural rewrite

1. **Title** — drop the algorithm name from the head position. Working:
   *Where you apply decision-space diversity decides what you get: a portable
   within-front selection rule for multimodal multi-objective optimization*
   (application named in the abstract, not the title).
2. **Intro** — lead with the design question, not with a framework. State the rule,
   state that it transfers across three published algorithms, state the failure regime.
3. **Method** — compress hard. The 7-module description is currently 197 lines;
   the *rule* needs ~1 page, the framework becomes a subsection. Modules whose
   ablation showed no benchmark effect (decision-mode archive, cross-mode mating,
   route-family archive, constraint-aware selection) move to an appendix — they are
   application machinery and they inflate the "new algorithm" signal.
4. **Results order** (this is the persuasion order, and it is *not* the current one):
   E1/E2 attribution → **E3 transfer** → E4 in-sort counterfactual → E5 failure
   regime → E6 realization competitive → E7 real-city application → E8 boundary.
5. **Framework figure** — demote from Figure 1. Figure 1 should be the placement
   schematic (where the signal enters selection); the framework diagram moves later.
   A 7-box architecture as Figure 1 is what makes reviewers grade this as (b).
6. **Length** — target ≤ 30 pages double-column-equivalent; Elsevier `els-cas-templates`
   is already on disk.
7. **Cover letter** — state plainly that this is a design-rule study validated across
   independent algorithms, not a new-algorithm submission. Pre-empting the wrong
   review standard is most of the battle.

## What must NOT be claimed

- Not "first use of intra-front decision-space selection" — already conceded, keep it
  conceded.
- Not "in-sort placement fails" as a general statement. On a bare backbone the in-sort
  substitution removes dominance precedence with nothing left to maintain convergence,
  so its collapse (~183× IGD on foreign backbones vs ~20× inside EARS) partly measures
  the missing scaffolding, not the placement. The defensible form is: *no in-sort
  weight in the swept range recovers the within-front result* — pending E4.
- Not "the rule helps everywhere". It is absent where the mechanism cannot act
  (MO_Ring_PSO_SCD on MMF2/MMF3, archive never reaches capacity), an order of
  magnitude weaker on the PSO backbone, and reversed in the deceptive regime.
  Stating all three is what makes the positive result believable.

## Acceptance odds, honestly

With E3 added and the framework demoted, this is a credible ASOC submission: the
contribution is a controlled, transferable finding with a real application and an
explicit failure regime — a shape ASOC accepts. The residual risk is a reviewer who
still wants a new mechanism; the mitigation is the cover letter plus the transfer
section, not more experiments. Without E3 it would very likely repeat the JCDE
outcome at a journal with a higher bar.
