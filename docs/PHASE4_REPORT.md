# Phase 4 Report — Baseline Implementation & Unified Interface

## 1. Completed
- Implemented all **5 fixed baselines** in Python behind the shared `Algorithm`
  interface, each registered and constructible via `baseline_registry.build`:
  - **MO_Ring_PSO_SCD** — constriction PSO + ring topology + SCD external archive.
  - **DN-NSGA-II** — NSGA-II with decision-space crowding (mating + truncation).
  - **Omni-optimizer** — NSGA-II with combined objective+decision crowding.
  - **CPDEA** (SOTA) — DE + convergence-penalized decision-space density truncation.
  - **MMEA-WI** (SOTA) — IBEA additive-epsilon indicator + decision-space sparsity weight.
- Shared scaffolding (`baselines/_common.py`): vectorised SBX, polynomial mutation,
  DE/rand/1, binary tournament, generic NSGA-II environmental selection with pluggable
  diversity functions — so DN-NSGA-II vs Omni differ only by their diversity rule.
- All baselines reuse the project's verified Pareto primitives (identical sorting/crowding
  semantics across every algorithm).

## 2. Files generated
`baselines/{_common,mo_ring_pso_scd,dn_nsga2,omni_optimizer,cpdea,mmea_wi}.py`;
`tests/test_baselines.py`; `docs/baseline_sanity_results.md`.

## 3. Sanity check
- `pytest tests/` → **43 passed, 3 skipped**. `test_baselines.py` verifies, for all 6
  algorithms: shared interface, **budget never exceeded and nearly fully used** (no
  early-stop advantage), uniform `Result` format, solutions within bounds, and the
  algorithm-independent seed protocol.
- Baseline probe (untuned, pop=100, 15k evals; `baseline_sanity_results.md`): all six
  converge and **all cover both MMF5 decision-space branches** — the baselines are real
  and strong (e.g. CPDEA's IGDX beats EARS on MMF1).

## 4. Next phase
**Phase 5 — metrics & statistics.** Implement IGD, IGD+, HV, IGDX, PSP, decision-space
mode coverage / #modes, spacing; Friedman test, Wilcoxon signed-rank + Holm correction,
average-rank and win/tie/loss tables, with CSV + LaTeX export. (These formalise the
ad-hoc IGD/IGDX probes used so far.)

## 5. Failures / blockers / risks (honest)
- **Integrity-positive finding:** EARS-MMOEA is competitive but **NOT yet clearly
  rank-1** — CPDEA matches/beats it on IGDX in this untuned probe. This is the correct
  honest starting point; rank-1 is pursued via Phase 6 tuning and, if needed, Phase 8
  redesign, **with** statistics, and **never** by weakening baselines.
- **Fidelity flag (tracked):** the 2 SOTA (CPDEA, MMEA-WI) are faithful-in-spirit Python
  reimplementations of the papers' mechanisms (official MATLAB referenced), with documented
  simplifications (CPDEA: front-structured one-shot penalised-density truncation; MMEA-WI:
  IBEA core + sparsity weight). MMEA-WI's high MMF1 IGDX suggests its weighting needs
  calibration. The **validation gate** (compare to published IGDX/PSP on MMF1-8) runs with
  Phase 5 metrics + Phase 7; any gap will be reported and, if a baseline cannot be made
  faithful, swapped for TriMOEA-TA&R / MMOEA-DC (reserved in Phase 1).
- No blockers.
