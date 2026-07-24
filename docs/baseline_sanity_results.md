# Baseline Sanity Results (Phase 4)

Single-run, **untuned**, low-budget probe (pop=100, 15k evaluations) to confirm
every algorithm is real, converges, and exhibits MMOP behaviour. **This is NOT the
formal comparison** (that is Phase 7: 30 runs, frozen params, full statistics).

| Algorithm | MMF1 IGD | MMF1 IGDX | MMF5 IGD | MMF5 IGDX | MMF5 branches (lo,hi) |
|---|---|---|---|---|---|
| EARS_MMOEA (ours) | 0.0059 | 0.0756 | 0.0053 | 0.1251 | (49, 49) |
| MO_Ring_PSO_SCD | 0.0066 | 0.0841 | 0.0052 | 0.1310 | (58, 42) |
| DN-NSGA-II | 0.0065 | 0.0885 | 0.0062 | 0.1769 | (54, 45) |
| Omni-optimizer | 0.0054 | 0.0941 | 0.0053 | 0.1745 | (51, 49) |
| CPDEA | 0.0072 | **0.0655** | 0.0075 | **0.1263** | (43, 56) |
| MMEA-WI | 0.0071 | 0.2121 | 0.0069 | 0.1881 | (62, 38) |

## Honest reading
- **All six converge** (IGD same order of magnitude) and **all cover both MMF5
  decision-space branches** -> the baselines are genuine MMOP methods, not strawmen.
- **EARS-MMOEA is competitive but NOT yet clearly rank-1**: CPDEA beats it on IGDX
  for MMF1 (0.0655 < 0.0756) and is ~tied on MMF5. This is the intended honest state
  going into parameter analysis (Phase 6) and, if needed, the redesign loop (Phase 8).
  The "rank-1" goal is pursued by tuning/redesign with statistics, never by weakening
  these baselines.

## Validation-gate flags (to resolve before Phase 7 conclusions)
- **MMEA-WI** shows a high MMF1 IGDX (0.2121). It converges and finds both branches,
  so it is functioning, but the decision-diversity weight (`gamma`) and IBEA `kappa`
  may need calibration to match the paper. Tracked for the validation gate.
- CPDEA's strong IGDX confirms the faithful reimplementation captures its decision-space
  diversity mechanism.
