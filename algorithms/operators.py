"""Module 6 -- Adaptive Operator Portfolio.

A small portfolio of real-coded variation operators whose selection probabilities
are adapted online by a credit-assignment bandit (probability matching with a
floor). Reward combines objective improvement and (in the application) feasibility
and decision-space novelty gains; on the benchmark we use the objective/novelty
reward. This lets the algorithm shift between exploitation (SBX/DE-best) and
exploration (DE-rand/Gaussian/mode-interpolation) as the search state changes.

Operator signature
-------------------
op(parents, pop, rng, xl, xu, params) -> child_vector
  parents : (2, n_var) the two selected parents (p1 is the base)
  pop     : (N, n_var) current population (for DE difference vectors)
"""
from __future__ import annotations

import numpy as np


# --------------------------------------------------------------------------
# Operators (each returns ONE child, clipped to bounds)
# --------------------------------------------------------------------------
def _clip(x, xl, xu):
    return np.clip(x, xl, xu)


def op_sbx_pm(parents, pop, rng, xl, xu, params):
    eta_c = params.get("sbx_eta", 20); eta_m = params.get("pm_eta", 20)
    p1, p2 = parents
    # SBX
    u = rng.random(len(p1))
    beta = np.where(u <= 0.5, (2 * u) ** (1 / (eta_c + 1)),
                    (1 / (2 * (1 - u))) ** (1 / (eta_c + 1)))
    child = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2)
    child = _polynomial_mutation(child, xl, xu, rng, eta_m,
                                 params.get("pm_prob", 1.0 / len(p1)))
    return _clip(child, xl, xu)


def op_de_rand(parents, pop, rng, xl, xu, params):
    F = params.get("de_F", 0.5); CR = params.get("de_CR", 0.9)
    base = parents[0]
    r = pop[rng.choice(len(pop), size=2, replace=False)]
    mutant = base + F * (r[0] - r[1])
    return _clip(_binomial(base, mutant, CR, rng), xl, xu)


def op_de_ctb(parents, pop, rng, xl, xu, params):
    F = params.get("de_F", 0.5); CR = params.get("de_CR", 0.9)
    cur, best = parents[0], parents[1]  # p2 acts as a 'good' guide
    r = pop[rng.choice(len(pop), size=2, replace=False)]
    mutant = cur + F * (best - cur) + F * (r[0] - r[1])
    return _clip(_binomial(cur, mutant, CR, rng), xl, xu)


def op_gaussian(parents, pop, rng, xl, xu, params):
    sigma = params.get("gauss_sigma", 0.1) * (np.asarray(xu) - np.asarray(xl))
    return _clip(parents[0] + rng.normal(0, 1, len(parents[0])) * sigma, xl, xu)


def op_mode_interp(parents, pop, rng, xl, xu, params):
    """Mode-guided interpolation/extrapolation between two (ideally cross-mode)
    parents -- generates candidate equivalent solutions between decision modes."""
    p1, p2 = parents
    alpha = rng.uniform(-0.25, 1.25)
    child = p1 + alpha * (p2 - p1)
    # light mutation
    child = _polynomial_mutation(child, xl, xu, rng, params.get("pm_eta", 20),
                                 params.get("pm_prob", 1.0 / len(p1)))
    return _clip(child, xl, xu)


def _polynomial_mutation(x, xl, xu, rng, eta, prob):
    x = x.copy(); xl = np.asarray(xl); xu = np.asarray(xu)
    do = rng.random(len(x)) < prob
    if not do.any():
        return x
    u = rng.random(len(x))
    span = xu - xl
    span[span < 1e-12] = 1e-12
    d1 = (x - xl) / span
    d2 = (xu - x) / span
    # clamp each branch's base to >=0; np.where selects the valid branch, the
    # clamp only sanitises the (discarded) other branch to avoid nan warnings.
    b1 = np.maximum(2 * u + (1 - 2 * u) * (1 - d1) ** (eta + 1), 0.0)
    b2 = np.maximum(2 * (1 - u) + 2 * (u - 0.5) * (1 - d2) ** (eta + 1), 0.0)
    deltaq = np.where(u <= 0.5,
                      b1 ** (1 / (eta + 1)) - 1,
                      1 - b2 ** (1 / (eta + 1)))
    x[do] = (x + deltaq * span)[do]
    return x


def _binomial(base, mutant, CR, rng):
    mask = rng.random(len(base)) < CR
    mask[rng.integers(len(base))] = True  # at least one
    return np.where(mask, mutant, base)


# --------------------------------------------------------------------------
# Bandit portfolio
# --------------------------------------------------------------------------
class OperatorPortfolio:
    """Probability-matching bandit over the operator set."""

    def __init__(self, rng: np.random.Generator, lr: float = 0.1,
                 min_prob: float = 0.05, operators=None):
        self.ops = operators or [
            ("sbx_pm", op_sbx_pm),
            ("de_rand", op_de_rand),
            ("de_ctb", op_de_ctb),
            ("gaussian", op_gaussian),
            ("mode_interp", op_mode_interp),
        ]
        self.k = len(self.ops)
        self.rng = rng
        self.lr = lr
        self.min_prob = min_prob
        self.q = np.ones(self.k) / self.k          # quality estimates
        self.prob = np.ones(self.k) / self.k       # selection probabilities
        self.usage = np.zeros(self.k, dtype=int)
        self.reward_sum = np.zeros(self.k)

    def select(self) -> int:
        return int(self.rng.choice(self.k, p=self.prob))

    def generate(self, op_idx, parents, pop, xl, xu, params):
        self.usage[op_idx] += 1
        return self.ops[op_idx][1](parents, pop, self.rng, xl, xu, params)

    def reward(self, op_idx, value: float):
        value = max(0.0, float(value))
        self.reward_sum[op_idx] += value
        # exponential recency-weighted update of quality
        self.q[op_idx] = (1 - self.lr) * self.q[op_idx] + self.lr * value
        self._update_probs()

    def _update_probs(self):
        q = np.maximum(self.q, 1e-12)
        p = q / q.sum()
        # probability matching with a floor
        p = self.min_prob + (1 - self.k * self.min_prob) * p
        self.prob = p / p.sum()

    def names(self):
        return [n for n, _ in self.ops]
