
## Extended suite (CEC2019/2020 MMO competition) — added 2026-06-20
- New problems MMF9, Omni-test, SYM-PART (simple/rotated), 720 runs (4×6×30), 0 errors.
- Reference sets validated (PS non-dominated vs 4e4 random cloud; pytest test_extended_problems.py).
- Independent recompute == pipeline: EARS rank-1, all-8 mean 1.89 (next MO_Ring 2.75, MMEA-WI 3.02);
  IGDX 1.25, PSP 1.50. Friedman significant on 7/8 metrics. Honest texture reported (EARS trails
  MMEA-WI on HV; some pairwise ties), but average-rank lead consistent across both suites.
