# Baseline Selection Note (Phase 1 — FIXED)

This document fixes the **5 baselines** (2 SOTA + 3 popular classics) for the
entire project. They are chosen to be **strong, representative, mechanism-diverse,
and backed by public code**, per the project's fairness rules (no strawmen).

## The MATLAB/PlatEMO reality (key constraint)

A literature/code scan (2026-06-16) confirms the MMOP algorithm ecosystem is
**overwhelmingly MATLAB/PlatEMO**. Official, citable implementations exist for our
chosen baselines, but in MATLAB:

* `MO_Ring_PSO_SCD` — MATLAB Central File Exchange #68662 + PlatEMO.
* `DN-NSGA-II`, `Omni-optimizer` — PlatEMO (`DNNSGAII`, `OmniOptimizer`).
* `CPDEA` — official GitHub `yiping0liu/CPDEA` (PlatEMO-based).
* `MMEA-WI` — `Wenhua-Li/ComparativeStudyofMMOP` (PlatEMO codes; arXiv:2207.04730,
  *Swarm Evol. Comput.* 2023), the authoritative aggregator of 12 MMOP methods.

There is **no widely-trusted Python SOTA MMEA repository**.

### Decision: unified Python implementation + validation gate

Our project needs **one** codebase that runs both the standard MMOP benchmarks
**and** the OSM multi-UAV application (which requires `osmnx`/`networkx`/`geopandas`,
i.e. Python). A pure-MATLAB study cannot deliver the application contribution.

Therefore we implement everything in **Python**, and **faithfully port** the 5
baselines from their official MATLAB sources, with an explicit **validation gate**
(Phase 2/4): each ported baseline must reproduce the published IGDX/PSP/HV behaviour
on the MMF suite within tolerance, or the discrepancy is documented. Every porting
decision (operators, parameters, selection rules) is recorded per-baseline in
`baselines/<name>.py` docstrings.

* **Risk:** reimplementation can deviate from the original. **Mitigation:** port from
  official code (not just pseudo-code) where it exists (CPDEA, MMEA-WI, MO_Ring_PSO_SCD);
  validate against published numbers; keep authors' recommended parameters; never
  weaken a baseline to help EARS-MMOEA.
* **Optional cross-check:** if results are close, we may additionally run the
  official MATLAB code in PlatEMO on a subset of problems as an external sanity check
  and report any gap honestly.

## The 5 fixed baselines

| # | Method | Type | Mechanism | Venue | Code source |
|---|---|---|---|---|---|
| 1 | **MO_Ring_PSO_SCD** | classic | PSO + ring topology + special crowding distance (SCD) | IEEE TEVC 2018 | FileExchange #68662 + PlatEMO |
| 2 | **DN-NSGA-II** | classic | decision-space niching NSGA-II | IEEE CEC 2016 | PlatEMO `DNNSGAII` |
| 3 | **Omni-optimizer** | classic | ε-dominance + decision&objective crowding | EJOR 2008 | PlatEMO `OmniOptimizer` |
| 4 | **CPDEA** | SOTA | convergence-penalized density (decision-space distance transform) + DE | IEEE TEVC 2020 | official `yiping0liu/CPDEA` |
| 5 | **MMEA-WI** | SOTA | weighted indicator folding decision-space diversity into the indicator | IEEE TEVC 2021 | `Wenhua-Li/ComparativeStudyofMMOP` |

### Why this set (representativeness & fairness)

* **Mechanism coverage** spans the field: PSO (1) · niching-GA (2) · ε-dominance dual
  crowding (3) · density/DE (4) · indicator-based (5). EARS-MMOEA is not being
  compared against five variants of one idea.
* **MO_Ring_PSO_SCD** is the canonical MMOP baseline and CEC2019-MMO competition
  winner — omitting it would itself be a reviewer red flag.
* **CPDEA** and **MMEA-WI** are highly-cited, recent TEVC SOTA with public code; they
  directly target the decision-space convergence/diversity trade-off that EARS-MMOEA
  also addresses — i.e. they are *hard* baselines, not easy ones.

### Considered but not selected (and why)

* **TriMOEA-TA&R** (TEVC 2019, official code `yiping0liu/TriMOEA-TAnR`): excellent and
  has the cleanest official code. Held as the **first swap-in** if any chosen baseline
  proves hard to port faithfully (two-archive mechanism, complements the set).
* **MMOEA/DC** (TEVC 2021): strong dual-clustering method; reserve as second swap-in.
* **HREA** (TEVC 2023): newest, handles local Pareto fronts, but a clean standalone code
  repo could not be confirmed in the scan — adopting it now would raise porting risk.
  Revisit if a verified source is found.
* **MO_PSO_MM**: fuzzy provenance (maps to a speciation/SOM-PSO line); MO_Ring_PSO_SCD
  is the cleaner PSO baseline.

## Fairness settings (binding)

Per `docs/experiment_protocol.md`: identical pop size, identical evaluation budget,
identical 30-run seed protocol (seeds independent of algorithm), authors' recommended
hyper-parameters for each baseline, no weakening. Any baseline-specific parameter is
recorded in its module and in `configs/baselines.yaml`.

## Status

**FIXED.** Registry: `baselines/baseline_registry.py`. Config: `configs/baselines.yaml`.
Implementations: Phase 4 (with the Phase 2/4 validation gate).

### Sources
- MO_Ring_PSO_SCD: Yue, Qu, Liang, IEEE TEVC 22(5):805–817, 2018.
- DN-NSGA-II: Liang, Yue, Qu, IEEE CEC 2016, 2454–2461.
- Omni-optimizer: Deb & Tiwari, EJOR 185(3):1062–1087, 2008.
- CPDEA: Liu, Ishibuchi, Yen, Nojima, Masuyama, IEEE TEVC 24(3):551–565, 2020. (`yiping0liu/CPDEA`)
- MMEA-WI: Li, Zhang, Wang, Ishibuchi et al., IEEE TEVC 25(6):1064–1078, 2021.
- Aggregator: Li et al., *Swarm Evol. Comput.* 2023 (arXiv:2207.04730); `Wenhua-Li/ComparativeStudyofMMOP`.
- PlatEMO: Tian et al., arXiv:1701.00879; `BIMK/PlatEMO`.
