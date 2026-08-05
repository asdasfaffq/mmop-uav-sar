"""EARS-MMOEA -- Equivalence-Aware Route/Structure-Preserving Multimodal
Multi-Objective Evolutionary Algorithm (main loop).

Ties together the seven modules:
  1. Dual-Space Equivalence-Aware Fitness   (equivalence_fitness.py)
  2. Three-Archive System                    (archives.py / route_family_archive.py)
  3. Adaptive Multimodal Niching             (niching.py)
  4. Within-Mode / Cross-Mode Mating         (this file)
  5. Constraint-Aware Multimodal Selection   (constraint_handling.py + selection.py)
  6. Adaptive Operator Portfolio             (operators.py)
  7. Environmental Selection                 (selection.py)

Ablation switches (Phase 9) are exposed as `params` flags:
  use_decision_mode_archive, use_route_family_archive, use_equivalence_fitness,
  use_adaptive_niching, use_cross_mode_mating, use_constraint_aware,
  use_operator_portfolio, backbone_only.
"""
from __future__ import annotations

import numpy as np

from algorithms.base import Algorithm, Result
from algorithms.archives import (DecisionModeArchive, EpsilonBandDiversityArchive,
                                 ParetoObjectiveArchive)
from algorithms.constraint_handling import EpsilonController
from algorithms.equivalence_fitness import fast_nondominated_sort
from algorithms.niching import (adaptive_niching, assign_to_centers,
                                occupancy_entropy)
from algorithms.operators import OperatorPortfolio, op_sbx_pm
from algorithms.selection import environmental_selection
from baselines.baseline_registry import register


@register("EARS_MMOEA")
class EARSMMOEA(Algorithm):
    name = "EARS_MMOEA"

    def __init__(self, problem, pop_size, max_evaluations, rng, params=None):
        super().__init__(problem, pop_size, max_evaluations, rng, params)
        p = self.params
        # ablation / feature switches (all on by default)
        self.use_dm_archive = p.get("use_decision_mode_archive", True)
        self.use_rf_archive = p.get("use_route_family_archive", True)
        self.use_equiv = p.get("use_equivalence_fitness", True)
        self.use_niching = p.get("use_adaptive_niching", True)
        self.use_cross_mode = p.get("use_cross_mode_mating", True)
        self.use_constraint_aware = p.get("use_constraint_aware", True)
        self.use_portfolio = p.get("use_operator_portfolio", True)
        self.backbone_only = p.get("backbone_only", False)
        if self.backbone_only:
            self.use_dm_archive = self.use_equiv = self.use_niching = False
            self.use_cross_mode = self.use_portfolio = False
        # hyper-parameters
        self.cross_mode_prob0 = p.get("cross_mode_mating_prob", 0.3)
        self.niche_boost = p.get("niche_boost", 0.5)
        # Phase-8: selection key for the splitting front -- "equivalence" (original)
        # or "penalized_density" (convergence-penalised decision density).
        self.selection_mode = p.get("selection_mode", "equivalence")
        # Phase-8: the FINAL reported set can use a different (decision-coverage)
        # key than the search. Selecting the final set from the already-converged
        # non-dominated union by decision sparsity maximises IGDX without changing
        # the search (so IGD/HV are preserved). Defaults to selection_mode.
        self.finalize_selection_mode = p.get("finalize_selection_mode",
                                             self.selection_mode)
        self.penalty_lambda = p.get("penalty_lambda", 2.0)
        self.hybrid_beta = p.get("hybrid_beta", 1.0)
        # Diagnostic switch (off by default; every reported result uses the default).
        # When on, the final report is the POPULATION only -- the Pareto and
        # decision-mode archives are excluded from the reported set. Because the
        # archives retain converged solutions, they mask convergence damage that the
        # selection layer inflicts on the population; excluding them tests whether a
        # selection-layer conclusion drawn inside this framework survives without that
        # masking. See docs/PLACEMENT_CLAIM_REFUTATION.md.
        self.report_population_only = bool(p.get("report_population_only", False))
        # Phase-8 redesign: convergence-gated epsilon-band diversity archive (the new
        # MMOP core). When on, the final reported set is this archive (converged AND
        # decision-diverse), and a fraction of matings draw a diverse converged mate
        # from it (cross-feeding), so the search refines all discovered modes.
        self.use_eps_archive = p.get("use_epsilon_archive", False)
        self.epsilon_band = p.get("epsilon_band", 0.02)
        self.da_capacity = int(p.get("da_size", 2 * self.pop_size))
        self.da_feed_prob = p.get("da_feed_prob", 0.3)
        self.cluster_freq = int(p.get("clustering_update_freq", 5))
        self.min_modes = int(p.get("min_modes", 2))
        self.max_modes = int(p.get("max_modes", 20))
        self.restart_ratio = p.get("restart_ratio", 0.05)
        # structure-preserving diversity (opt-in): if enabled AND the problem exposes
        # a topology-aware feature map, measure decision-space diversity in that
        # feature space. NOTE: on the constrained UAV problem this did NOT recover the
        # route-family collapse (the convergence pressure loses diversity during the
        # search, not just at selection), so it is OFF by default. Kept for the record.
        self.feature_fn = (getattr(self.problem, "feature_map", None)
                           if p.get("use_feature_diversity", False) else None)

    def _dec(self, X):
        """Decision representation + bounds used for diversity (feature map if any)."""
        if self.feature_fn is None:
            return X, self.problem.xl, self.problem.xu
        feat = self.feature_fn(X)
        d = feat.shape[1]
        return feat, np.zeros(d), np.ones(d)

    # ----------------------------------------------------------------- run
    def run(self) -> Result:
        prob, rng, N = self.problem, self.rng, self.pop_size
        X = rng.uniform(prob.xl, prob.xu, size=(N, prob.n_var))
        out = self._evaluate(X)
        F, CV = out["F"], out["CV"]

        pareto_arc = ParetoObjectiveArchive(self.params.get("pareto_archive_size", N))
        dm_arc = DecisionModeArchive(self.params.get("decision_mode_archive_size", N // 2))
        portfolio = OperatorPortfolio(rng, lr=self.params.get("operator_lr", 0.1),
                                      min_prob=self.params.get("operator_min_prob", 0.05))
        eps = EpsilonController(self.params.get("epsilon_relax_coef", 0.1),
                                self.params.get("epsilon_decay", 0.95))
        da = (EpsilonBandDiversityArchive(
                  self.da_capacity, self.epsilon_band,
                  feature_fn=getattr(self.problem, "feature_map", None))
              if self.use_eps_archive else None)
        pareto_arc.update(X, F, CV)
        if self.use_dm_archive:
            dm_arc.update(X, F, CV)
        if da is not None:
            da.update(X, F, CV)

        niche = self._niche(X) if self.use_niching else None
        cross_mode_prob = self.cross_mode_prob0
        gen = 0

        while self.budget_left >= N:
            gen += 1
            if self.use_niching and (gen % self.cluster_freq == 0):
                niche = self._niche(X)
            labels = niche.labels if (niche is not None) else None
            entropy = niche.entropy if (niche is not None) else 0.0

            # adapt cross-mode probability: lower mode entropy (collapse risk)
            # -> more cross-mode exploration.
            if self.use_cross_mode:
                cross_mode_prob = float(np.clip(
                    self.cross_mode_prob0 + 0.5 * (1.0 - entropy), 0.05, 0.9))
            else:
                cross_mode_prob = 0.0

            # ---- reproduction ----
            children = np.empty((N, prob.n_var))
            op_used = np.empty(N, dtype=int)
            parent_F = np.empty((N, prob.n_obj))
            for i in range(N):
                p1, p2 = self._mate(X, F, labels, cross_mode_prob, rng)
                parent1, parent2 = X[p1], X[p2]
                # cross-feeding: occasionally mate with a diverse CONVERGED solution
                # from the epsilon-band archive to refine an under-explored mode.
                if da is not None and len(da) > 1 and rng.random() < self.da_feed_prob:
                    parent2 = da.X[rng.integers(len(da))]
                if self.use_portfolio:
                    oi = portfolio.select()
                    child = portfolio.generate(oi, (parent1, parent2), X,
                                               prob.xl, prob.xu, self.params)
                else:
                    oi = 0
                    child = op_sbx_pm((parent1, parent2), X, rng,
                                      prob.xl, prob.xu, self.params)
                children[i] = child
                op_used[i] = oi
                parent_F[i] = F[p1]

            co = self._evaluate(children)
            cF, cCV = co["F"], co["CV"]

            # ---- operator credit assignment ----
            if self.use_portfolio:
                for i in range(N):
                    r = self._reward(cF[i], cCV[i], parent_F[i])
                    portfolio.reward(op_used[i], r)

            # ---- archives ----
            pareto_arc.update(children, cF, cCV)
            if self.use_dm_archive:
                dm_arc.update(children, cF, cCV)

            # ---- environmental selection (parents + offspring) ----
            poolX = np.vstack([X, children])
            poolF = np.vstack([F, cF])
            poolCV = np.concatenate([CV, cCV])
            if da is not None:
                da.update(poolX, poolF, poolCV)  # accumulate converged + diverse
            eps.step()
            sel_CV = eps.effective_cv(poolCV) if self.use_constraint_aware else poolCV
            pool_rep, rlo, rhi = self._dec(poolX)     # topology-aware repr if any
            if self.use_niching and self.use_equiv and niche is not None:
                # cheap: label the pool by nearest existing mode centre (in repr space)
                sel_labels = assign_to_centers(pool_rep, rlo, rhi, niche.centers)
            else:
                sel_labels = None
            idx = environmental_selection(
                poolX, poolF, sel_CV, N,
                mode_labels=sel_labels,
                use_equivalence=self.use_equiv,
                niche_boost=self.niche_boost,
                selection_mode=self.selection_mode,
                penalty_lambda=self.penalty_lambda, hybrid_beta=self.hybrid_beta,
                X_dec=pool_rep)
            X, F, CV = poolX[idx], poolF[idx], poolCV[idx]

        return self._finalize(X, F, CV, pareto_arc, dm_arc, portfolio, gen, da)

    # ----------------------------------------------------------------- helpers
    def _niche(self, X):
        rep, lo, hi = self._dec(X)
        return adaptive_niching(rep, lo, hi,
                                min_modes=self.min_modes, max_modes=self.max_modes,
                                rng=self.rng)

    def _mate(self, X, F, labels, cross_mode_prob, rng):
        n = len(X)
        if labels is None or len(np.unique(labels)) < 2:
            a, b = rng.choice(n, size=2, replace=False)
            return a, b
        if rng.random() < cross_mode_prob:
            # cross-mode: parents from two distinct clusters
            uniq = np.unique(labels)
            c1, c2 = rng.choice(uniq, size=2, replace=False)
            a = rng.choice(np.where(labels == c1)[0])
            b = rng.choice(np.where(labels == c2)[0])
            return a, b
        # within-mode: two parents from the same cluster
        c = rng.choice(np.unique(labels))
        members = np.where(labels == c)[0]
        if len(members) >= 2:
            a, b = rng.choice(members, size=2, replace=False)
            return a, b
        a, b = rng.choice(n, size=2, replace=False)
        return a, b

    @staticmethod
    def _reward(cF, cCV, pF):
        """Reward operator for producing a child that improves on its base parent."""
        if cCV > 0:
            return 0.0
        better = np.all(cF <= pF) and np.any(cF < pF)
        if better:
            return 1.0
        nondom = not (np.all(pF <= cF) and np.any(pF < cF))
        return 0.3 if nondom else 0.0

    def _finalize(self, X, F, CV, pareto_arc, dm_arc, portfolio, gen, da=None) -> Result:
        """Report the final solution set.

        With the epsilon-band diversity archive on (the redesigned core), the report
        IS that archive -- already convergence-gated and decision-spread. Otherwise,
        fall back to the non-dominated union of population + archives."""
        if da is not None and len(da) > 0:
            uX, uF = da.report(self.pop_size)
            return Result(X=uX, F=uF, CV=np.zeros(len(uX)),
                          n_evaluations=self.evaluations_used,
                          history={"generations": gen},
                          extra={"operator_usage": dict(zip(portfolio.names(),
                                                            portfolio.usage.tolist())),
                                 "da_size": len(da),
                                 "pareto_archive_size": len(pareto_arc)})
        parts_X = [X]
        parts_F = [F]
        if not self.report_population_only:
            if len(pareto_arc):
                parts_X.append(pareto_arc.X); parts_F.append(pareto_arc.F)
            if self.use_dm_archive and len(dm_arc):
                parts_X.append(dm_arc.X); parts_F.append(dm_arc.F)
        uX = np.vstack(parts_X); uF = np.vstack(parts_F)
        # feasible non-dominated
        uCV = np.zeros(len(uX))
        fronts = fast_nondominated_sort(uF, uCV)
        nd = fronts[0]
        uX, uF = uX[nd], uF[nd]
        if len(uX) > self.pop_size:
            idx = environmental_selection(uX, uF, None, self.pop_size,
                                          use_equivalence=self.use_equiv,
                                          niche_boost=self.niche_boost,
                                          selection_mode=self.finalize_selection_mode,
                                          penalty_lambda=self.penalty_lambda, hybrid_beta=self.hybrid_beta)
            uX, uF = uX[idx], uF[idx]
        return Result(
            X=uX, F=uF, CV=np.zeros(len(uX)),
            n_evaluations=self.evaluations_used,
            history={"generations": gen},
            extra={"operator_usage": dict(zip(portfolio.names(),
                                              portfolio.usage.tolist())),
                   "operator_prob": portfolio.prob.tolist(),
                   "pareto_archive_size": len(pareto_arc),
                   "decision_mode_archive_size": len(dm_arc)})
