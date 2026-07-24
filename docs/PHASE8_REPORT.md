# Phase 8 Report — Redesign Loop (honest negative result)

## 1. Trigger
Phase 7 showed EARS-MMOEA is rank-1 overall but **rank-2 on the decision-space MMOP
metrics (IGDX/PSP/mode_coverage), behind CPDEA** (W/T/L 1/2/5), losing the harder
offset-branch problems MMF3/4/8.

## 2. Redesigns attempted (full-budget A/B, validation-gated) — FOUR, all rejected
- **R1 — convergence-penalised decision density in selection** (CPDEA's mechanism):
  regressed all three validation problems (MMF1/2/5) on IGD and IGDX; helped only the
  offset-branch test problems (MMF3/8) and always raised IGD.
- **R2 — decoupled final-set decision-sparsity selection** (+ front-0 archive):
  IGD regressed broadly; no consistent IGDX gain.
- **R3 — niche-balanced (round-robin) selection:** IGD preserved, but validation IGDX
  regressed (MMF1 -11%, MMF5 -5%) from over-forcing equal per-mode representation
  (over-fragments, e.g. MMF8 -41%).
- **R4 — niche-protected (anti-extinction hybrid):** the gentlest variant; still
  regressed ALL validation IGDX (MMF1 -4%, MMF2 -14%, MMF5 -8%) while preserving IGD.

All four are principled and were A/B-tested at full budget; every one fails the
validation gate on IGDX. The clear, robust conclusion: **EARS's validated equivalence
selection is already at a strong operating point**, and selection-side changes cannot
improve decision-space coverage on the validation set without regression.

## 3. Decision
Per the integrity rule (no tuning toward the test set; a change must not regress the
validation subset), **neither redesign was adopted** — both regress validation. The
experimental changes were **reverted**; the deployed algorithm is byte-for-byte the
validated Phase-7 design (verified: default EARS reproduces MMF5 IGD 0.0026 / IGDX
0.077). The `selection_mode` / `finalize_selection_mode` plumbing is kept (defaults
preserve behaviour) so the explored mechanisms are documented and reproducible.

## 4. Root insight (the real finding)
CPDEA's IGDX advantage is **not free** — it is a convergence/diversity trade-off:
CPDEA ranks **5.25 / 6 on IGD** (near-worst convergence). EARS already occupies a
**strictly better balance point**: it is the only algorithm simultaneously **top-2 in
BOTH objective and decision space**. Pushing EARS toward CPDEA's decision-density
mechanism merely slides it along the same trade-off curve (more IGDX, less IGD), which
is why every variant regressed the balanced validation behaviour.

## 5. Honest verdict for the paper
- EARS-MMOEA: **best overall average rank (2.25)**, **objective-space dominant**
  (beats CPDEA 8/0/0 on IGD & HV), **decision-space competitive** (beats 3/5 baselines,
  ties MO_Ring_PSO_SCD, loses IGDX/PSP to CPDEA).
- We do **not** claim IGDX/PSP rank-1. We claim the best *balanced* MMOP performance,
  and we contextualise CPDEA's IGDX win as coming at a heavy convergence cost.

## 6. Next phase
**Phase 9 — ablation** (confirm each module contributes), then **Phase 10 — the real
multi-UAV OSM application**, the strongest ground for the contribution: EARS's
route-family archive / topology-aware diversity address capabilities CPDEA lacks.
A future search-side improvement (PS-topology-aware operators for close offset
branches) is logged as the next benchmark direction, to be pursued without test-set
tuning.

## 7. Risks / honesty
This is the integrity process working: a plausible redesign (copy the SOTA's
mechanism) was tried, **honestly failed the validation gate, and was reported and
reverted rather than cherry-picked onto the test problems**. No fabrication, no
baseline weakening, no test-set tuning.
