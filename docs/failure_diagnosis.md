# Failure Diagnosis Log

Append one entry per redesign trigger (Phase 8 / application redesign loops),
following the template in the project brief (experiment, baseline group, metric,
EARS rank, which baselines won, which problems/metrics lost, root-cause class,
next-version change, reruns required, whether it improved).

---

## Diagnosis #1 — Phase 7 benchmark (2026-06-17)

1. **Experiment:** standard MMF1–8 comparison, 30 runs, pop=200, 50k evals.
2. **Baseline group:** 2 SOTA (CPDEA, MMEA-WI) + 3 classic (MO_Ring_PSO_SCD, DN-NSGAII, Omni).
3. **Metric(s) failed:** IGDX, PSP, mode_coverage (the decision-space MMOP metrics).
4. **EARS rank:** overall avg rank **1st (2.25)**; on IGDX/PSP **2nd, behind CPDEA**.
5. **Who beat EARS:** **CPDEA** — Wilcoxon+Holm W/T/L (EARS vs CPDEA) = **1/2/5** on
   IGDX, PSP, and mode_coverage. (EARS beats CPDEA 8/0/0 on IGD and HV.)
6. **Lost on which problems:** MMF3, MMF4, MMF5, MMF8 (IGDX) — the harder multimodal
   problems with offset/overlapping PS branches. Wins/ties MMF1, MMF2, MMF7.
7. **Lost on which metrics:** decision-space coverage (IGDX/PSP/mode_coverage) only;
   EARS leads all objective-space metrics (IGD/IGD+/HV) and spacing.
8. **Root-cause class:** *decision-space diversity / Pareto-set coverage insufficient.*
   EARS converges best (objective space) but is too convergence-greedy in decision
   space: (a) its environmental selection fills whole non-dominated fronts first, so
   slightly-dominated-but-decision-novel solutions (which improve IGDX) are dropped;
   (b) the final reported set is the convergence-filtered non-dominated union, further
   trimming decision-diverse points; (c) CPDEA explicitly *keeps* such points via its
   convergence-penalized density, which is exactly why it wins IGDX on hard problems.
9. **Next-version change (Phase 8 plan):**
   - Adopt a CPDEA-style **convergence-penalised decision density** as the secondary
     key in environmental selection (replace/augment SCD on the splitting front), so
     decision-diverse solutions survive even at small convergence cost.
   - Strengthen the **Decision-Mode Archive**'s role in the FINAL reported set
     (report archive ∪ population, decision-space-truncated) and consider a larger
     archive; this directly targets IGDX/PSP/mode_coverage.
   - Keep the objective-space advantage (don't regress IGD/HV).
10. **Reruns required:** local re-validation on MMF3/4/5/8 (validation-safe subset is
    MMF5 only; full re-judgement on MMF1–8 after the change). Re-run Phase 7.
11. **Improved?** **NO — honest negative result.** Two redesigns were implemented and
    A/B-tested at full budget:
    - **(R1) convergence-penalised decision density in the search** (CPDEA's mechanism):
      regressed ALL THREE validation problems (MMF1/2/5) on both IGD and IGDX; only
      helped the offset-branch test problems (MMF3, MMF8) and always at an IGD cost.
    - **(R2) decoupled: equivalence search + penalised-density final-set selection**
      (+ front-0 decision-mode archive): regressed IGD broadly (the decision-sparse
      final set sacrifices objective-space coverage) with no consistent IGDX gain.
    - **(R3) niche-balanced (round-robin) selection:** preserved IGD (good) but
      regressed validation IGDX on MMF1 (-11%) and MMF5 (-5%) by over-forcing equal
      per-mode representation (over-fragments e.g. MMF8 -41%).
    - **(R4) niche-protected (anti-extinction hybrid) selection:** the gentlest variant
      (guarantee 1 best member per mode, else equivalence); still regressed all three
      validation problems on IGDX (MMF1 -4%, MMF2 -14%, MMF5 -8%) while preserving IGD.
    **Four** principled selection-side strengthenings were tested; ALL fail the
    validation gate on IGDX. Per the no-test-set-tuning rule, none was adopted (default
    `selection_mode` stays `equivalence` = validated Phase-7 design; the alternative
    modes remain opt-in for documentation/ablation).
    **Root insight:** CPDEA's IGDX win is a convergence/diversity TRADE-OFF —
    CPDEA is rank **5.25/6 on IGD**. EARS already sits at a better balance point
    (top-2 on BOTH spaces); moving it toward CPDEA's mechanism just slides it down the
    same trade-off curve. The validated balanced design was **retained** (changes
    reverted; deployed algorithm == Phase-7 algorithm).
12. **RESOLVED (R5, adopted).** A sixth redesign finally passed the validation gate and
    fixed the IGDX shortfall: the **HYBRID diversity key** =
    `equivalence_diversity (SCD + niche rarity) x (1 + beta * decision-space kNN sparsity)`.
    Because the sparsity bonus is *multiplicative* on top of the validated equivalence
    key, it preserves EARS's convergence (no IGD trade) while adding decision-space
    coverage. **beta=0.5 is the ONLY value that improves IGDX with no IGD regression on
    ALL THREE validation problems** (MMF1 0.0404->0.0399, MMF2 0.0099->0.0096, MMF5
    0.0820->0.0721); beta=1.0 regressed MMF2, beta=2.0 regressed MMF1's IGD. Chosen by
    validation only.
    **Full-study outcome (30 runs, MMF1-8):** EARS overall average rank improved to
    **2.20 (rank-1)**; vs CPDEA the IGDX W/T/L went **1/2/5 -> 2/4/2 (statistical tie)**
    and PSP likewise; EARS is now **rank-1 on PSP and tied-rank-1 on IGDX**, while still
    beating CPDEA **8/0/0 on IGD and HV**. CPDEA retains a lead only on mode_coverage
    (1/3/4) — reported honestly, not chased. Frozen in `selected_params.yaml`.

