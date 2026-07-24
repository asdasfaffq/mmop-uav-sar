# Paper Number Integrity Audit (2026-06-20)

**Method.** Every headline number in the paper was recomputed *independently* from the raw
`run_*.json` metric files (script `verify_paper_numbers.py`), i.e. a different code path from
the statistics pipeline that produced the tables. In addition, deterministic metrics were
recomputed from the stored `.npz` solution arrays to rule out any hand-editing of result files.

## Run inventory (matches experimental design exactly)
- benchmark: 1440 runs = 8 problems × 6 algorithms × 30 runs
- ablation: 2400 runs = 8 problems × 10 variants × 30 runs
- placement × 5 cities: 540 each = 3 instances × 6 algorithms × 30 runs
- 0 runs missing `.npz` arrays.

## Headline numbers — paper vs recomputed-from-raw (all MATCH)
| Claim | Paper | Recomputed |
|---|---|---|
| Benchmark avg rank (all-8) | 2.20 | 2.203 ✓ |
| Benchmark next-best (MO_Ring) | 3.20 | 3.20 ✓ |
| EARS vs MMEA-WI IGDX / PSP | 8/0/0 | 8/0/0 ✓ |
| EARS vs MMEA-WI IGD / HV | 7/0/1, 6/1/1 | 7/0/1, 6/1/1 ✓ |
| EARS vs CPDEA IGD / HV | 8/0/0 | 8/0/0 ✓ |
| EARS vs CPDEA IGDX | 2/4/2 (tie) | 2/4/2 ✓ |
| Ablation A0 losses on IGDX / mode_cov | 0 (never beaten) | 0 ✓ |
| Ablation A8/A3/A7/A9 IGDX delta | 623/181/35/11 % | 623/181/35/11 % ✓ |
| Ablation full IGD vs no-bonus (A9) | "within 3%" | +1.0% ✓ (conservative) |
| Placement per-city full ranks | 2.74/1.95/2.14/2.38/2.52 | identical ✓ |
| Placement 5-city avg full / core | 2.35 / 1.71 | 2.35 / 1.71 ✓ |
| Placement next-best (Omni) full / core | 3.12 / 2.74 | 3.12 / 2.74 ✓ |
| Hong Kong core (Omni edges EARS) | 1.92 vs 1.75 | 1.92 vs 1.75 ✓ |
| Macau mean HV EARS / CPDEA | 0.77 / 0.25 | 0.770 / 0.246 ✓ |
| Macau mean #modes EARS / CPDEA | 14.7 / ~2.0 | 14.74 / 1.96 ✓ |
| Figure mode counts (EARS, p11) | shown in Fig | 18.7/7.0/14.2/13.3/19.7 ✓ |

## Anti-tampering checks (all PASS)
- **npz vs json:** 60/60 deterministic metric values (IGD, IGD+, HV, IGDX, PSP, spacing) across
  10 random EARS+CPDEA runs match the stored `.npz` arrays exactly → JSON metrics are computed
  from real solutions, not edited.
- **Seeds:** algorithm-independent (same problem/run → identical seed across all 6 algorithms →
  fair comparison, no per-algorithm seed cherry-picking); 240/240 (problem,run) seeds distinct.
- **Timestamps:** runs span 2026-06-17T15:31 → 2026-06-18T20:26 (~29 h real compute), not a
  single fabricated instant.
- **File mtimes:** no JSON modified >2 h after its `.npz` (no post-hoc edits; placement's 2nd
  metric pass is the only intended JSON rewrite).

## One imprecision found and fixed
- Abstract said "Friedman $p<0.003$"; true for 7/8 metrics, but #modes is $p{=}0.021$. Reworded
  to "significant for every metric, $p<0.003$ on the convergence and decision-space indicators".

## Verdict
All quantitative claims in the paper are reproduced from the real run data; no fabrication,
no cherry-picked seeds, no hand-edited result files, no baseline weakening (baselines were in
fact corrected to be *more* fair). Reproduce with: `python verify_paper_numbers.py`.
