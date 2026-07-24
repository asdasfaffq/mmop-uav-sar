# Method (draft) — EARS-MMOEA

## 3.1 Preliminaries and notation
An MMOP minimises `F(x)=(f_1,...,f_m)` over decision space `Omega`. Distinct decision
regions can map to the same Pareto front; the MMOP goal is to approximate the Pareto
front (objective space) **and** cover all its decision-space pre-images (Pareto sets).
We use constraint-aware non-dominated sorting (Deb's rule), the Special Crowding Distance
(SCD; the larger of objective- and decision-space crowding), and standard real-coded
variation.

## 3.2 Core: hybrid dual-space diversity (Module 1)
The environmental selection ranks the splitting non-dominated front by

    D(i) = E(i) * (1 + beta * S(i)),

- `E(i)`: **equivalence diversity** = SCD(i) boosted by niche rarity (members of rarer
  decision-space modes scored higher). Captures objective+decision spread.
- `S(i)`: **decision-space sparsity** = normalised sum of i's k nearest-neighbour
  distances in (a problem feature representation of) decision space, in [0,1].
- `beta`: sparsity weight (frozen at 0.5 by validation-only analysis).

**Why it works.** The bonus is *multiplicative* and applied only among already
non-dominated solutions, so (i) where the equivalence selection already covers the
Pareto set it is preserved (no convergence regression), and (ii) on hard, close-mode
problems it adds preference for decision-space-sparse solutions, raising decision-space
coverage. Unlike additive convergence-penalty schemes (e.g. CPDEA) that retain somewhat-
unconverged solutions and damage IGD, EARS keeps IGD intact while reaching comparable
or better IGDX. The ablation (A9) confirms removing `S` significantly worsens IGDX/PSP.

## 3.3 Supporting modules
- **M2 Three-archive system**: a Pareto-objective archive (convergence/quality), a
  decision-mode archive (mode representatives), and a route/structure-family archive
  (application).
- **M3 Adaptive niching**: silhouette-selected k-means decision-space modes, adaptive
  radius, occupancy entropy; supplies the niche-rarity term and the mating controller.
- **M4 Within-/cross-mode mating**: cross-mode probability adapted by mode-occupancy
  entropy (more cross-mode exploration when modes collapse).
- **M5 Constraint-aware selection**: epsilon-relaxation schedule + boundary-near
  preservation (active on constrained applications).
- **M6 Operator portfolio**: SBX+PM, DE/rand, DE/current-to-best, Gaussian,
  mode-interpolation, with a probability-matching bandit on credit assignment.
- **M7 Environmental selection**: constraint-aware fronts + the hybrid diversity key.

## 3.4 Structure-preserving diversity for structured decision spaces
For applications whose decision space is structured (e.g. station layouts), EARS measures
decision-space diversity in a problem-provided, permutation-invariant feature map, so the
hybrid key tracks genuine structural difference rather than raw encoding distance.

## 3.5 Algorithm and complexity
Per generation: niching (periodic), feature/repr computation, variation, archive updates,
and the vectorised constraint-aware sort + hybrid-key truncation. The non-dominated sort
is vectorised (domination matrix), giving the dominant `O(N^2 m)` cost at population size
`N`, `m` objectives.

*(Pseudocode and per-module equations to be finalised in LaTeX; see `algorithms/` for the
reference implementation.)*
