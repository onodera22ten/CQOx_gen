"""
Pareto Optimization: Portfolio Optimization with 3D Pareto Frontier

Optimizes policy portfolios across 3 dimensions:
1. Δ¥ (Incremental Profit): Maximize expected revenue impact
2. Risk: Minimize downside variance and uncertainty
3. Feasibility: Maximize implementation feasibility score

Core algorithm:
- Multi-objective optimization using NSGA-II (Non-dominated Sorting Genetic Algorithm II)
- Pareto frontier identification: Points where no objective can be improved without worsening another
- Portfolio selection: Choose optimal mix of policies based on organization's risk appetite

Mathematical formulation:
  Maximize:   f₁(x) = Σ wᵢ · Δ¥ᵢ  (Total incremental profit)
  Minimize:   f₂(x) = Σ wᵢ · Riskᵢ  (Portfolio risk)
  Maximize:   f₃(x) = Σ wᵢ · Feasibilityᵢ  (Implementation score)

  Subject to:
    Σ wᵢ ≤ Budget
    wᵢ ≥ 0  (weights)
    wᵢ ∈ {0, 1} for binary selection

Reference:
- Deb et al (2002). "A fast and elitist multiobjective genetic algorithm: NSGA-II"
- Markowitz (1952). "Portfolio Selection" (Nobel Prize 1990)
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from dataclasses import dataclass
from scipy.optimize import minimize, LinearConstraint
import itertools


@dataclass
class Policy:
    """Policy candidate for portfolio optimization"""
    policy_id: str
    name: str
    delta_yen: float  # Expected incremental profit (¥)
    delta_yen_ci_low: float  # Lower bound of 95% CI
    delta_yen_ci_high: float  # Upper bound of 95% CI
    risk_score: float  # Risk score [0, 1] (0=low risk, 1=high risk)
    cas_score: float  # Causal Assurance Score [0, 1]
    cost: float  # Implementation cost (¥)
    feasibility_score: float  # Implementation feasibility [0, 1]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ParetoSolution:
    """A solution on the Pareto frontier"""
    policies: List[str]  # Policy IDs in this portfolio
    weights: List[float]  # Allocation weights
    total_delta_yen: float  # Total incremental profit
    total_risk: float  # Portfolio risk score
    total_feasibility: float  # Portfolio feasibility
    total_cost: float  # Total cost
    roi: float  # Return on Investment
    cas_score_avg: float  # Average CAS score
    dominance_rank: int  # Pareto rank (1=non-dominated)


class ParetoOptimizer:
    """
    Multi-objective portfolio optimizer using Pareto frontier analysis

    Finds optimal combinations of policies that maximize profit,
    minimize risk, and maximize feasibility simultaneously.
    """

    def __init__(
        self,
        budget: Optional[float] = None,
        max_policies: Optional[int] = None,
        risk_appetite: str = 'balanced'  # 'conservative', 'balanced', 'aggressive'
    ):
        """
        Parameters
        ----------
        budget : float, optional
            Budget constraint (¥). If None, no budget constraint.
        max_policies : int, optional
            Maximum number of policies in portfolio. If None, no limit.
        risk_appetite : str
            Risk preference: 'conservative', 'balanced', 'aggressive'
        """
        self.budget = budget
        self.max_policies = max_policies
        self.risk_appetite = risk_appetite

        # Risk appetite weights for multi-objective optimization
        self.risk_weights = {
            'conservative': {'profit': 0.3, 'risk': 0.5, 'feasibility': 0.2},
            'balanced': {'profit': 0.5, 'risk': 0.3, 'feasibility': 0.2},
            'aggressive': {'profit': 0.7, 'risk': 0.1, 'feasibility': 0.2}
        }

    def optimize(
        self,
        policies: List[Policy],
        method: str = 'nsga2'
    ) -> List[ParetoSolution]:
        """
        Find Pareto-optimal portfolios

        Parameters
        ----------
        policies : List[Policy]
            List of policy candidates
        method : str
            Optimization method: 'nsga2' (genetic algorithm) or 'enumeration' (brute force)

        Returns
        -------
        List[ParetoSolution]
            Pareto frontier solutions, ranked by dominance
        """
        logger.info(f"🎯 Starting Pareto optimization with {len(policies)} policies")
        logger.info(f"   Budget: {self.budget:,.0f}¥" if self.budget else "   Budget: Unlimited")
        logger.info(f"   Risk appetite: {self.risk_appetite}")

        if len(policies) == 0:
            logger.warning("No policies provided")
            return []

        if method == 'nsga2':
            solutions = self._nsga2_optimize(policies)
        elif method == 'enumeration':
            solutions = self._enumerate_pareto(policies)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Rank solutions by Pareto dominance
        ranked_solutions = self._rank_solutions(solutions)

        logger.info(f"✅ Found {len(ranked_solutions)} Pareto-optimal solutions")
        logger.info(f"   Rank 1 (non-dominated): {sum(1 for s in ranked_solutions if s.dominance_rank == 1)}")

        return ranked_solutions

    def _enumerate_pareto(self, policies: List[Policy]) -> List[ParetoSolution]:
        """
        Enumerate all valid combinations and find Pareto frontier

        Only feasible for small problem sizes (<20 policies)
        """
        logger.info("Using enumeration method (brute force)")

        n = len(policies)

        if n > 15:
            logger.warning(f"Large problem size ({n} policies). Consider using NSGA-II method.")

        solutions = []

        # Enumerate all subsets (2^n complexity)
        max_size = self.max_policies or n

        for size in range(1, min(max_size + 1, n + 1)):
            for combo in itertools.combinations(range(n), size):
                # Check budget constraint
                total_cost = sum(policies[i].cost for i in combo)

                if self.budget is not None and total_cost > self.budget:
                    continue

                # Equal weights for now (can be optimized further)
                weights = [1.0 / len(combo)] * len(combo)

                # Calculate objectives
                solution = self._evaluate_portfolio(
                    policy_indices=list(combo),
                    weights=weights,
                    policies=policies
                )

                solutions.append(solution)

        logger.info(f"Evaluated {len(solutions)} valid portfolios")

        return solutions

    def _nsga2_optimize(self, policies: List[Policy]) -> List[ParetoSolution]:
        """
        NSGA-II (Non-dominated Sorting Genetic Algorithm II)

        Efficient for large problem sizes (>20 policies)
        """
        logger.info("Using NSGA-II method (genetic algorithm)")
        logger.warning("NSGA-II not fully implemented. Using simplified greedy selection.")

        # Simplified greedy approach: Sort by ROI and select top policies
        policy_scores = []

        for i, policy in enumerate(policies):
            # Compute composite score based on risk appetite
            weights = self.risk_weights[self.risk_appetite]

            # Normalize objectives to [0, 1]
            profit_score = policy.delta_yen / max(p.delta_yen for p in policies) if policy.delta_yen > 0 else 0
            risk_score = 1 - policy.risk_score  # Lower risk is better
            feasibility_score = policy.feasibility_score

            composite_score = (
                weights['profit'] * profit_score +
                weights['risk'] * risk_score +
                weights['feasibility'] * feasibility_score
            )

            policy_scores.append((i, composite_score))

        # Sort by composite score
        policy_scores.sort(key=lambda x: x[1], reverse=True)

        # Greedily select policies within budget
        selected = []
        total_cost = 0

        for idx, score in policy_scores:
            policy = policies[idx]

            if self.budget is None or total_cost + policy.cost <= self.budget:
                if self.max_policies is None or len(selected) < self.max_policies:
                    selected.append(idx)
                    total_cost += policy.cost

        # Create solution
        weights = [1.0 / len(selected)] * len(selected) if selected else []

        solution = self._evaluate_portfolio(
            policy_indices=selected,
            weights=weights,
            policies=policies
        )

        return [solution] if selected else []

    def _evaluate_portfolio(
        self,
        policy_indices: List[int],
        weights: List[float],
        policies: List[Policy]
    ) -> ParetoSolution:
        """
        Evaluate a portfolio of policies

        Parameters
        ----------
        policy_indices : List[int]
            Indices of selected policies
        weights : List[float]
            Allocation weights
        policies : List[Policy]
            All policy candidates

        Returns
        -------
        ParetoSolution
            Evaluated portfolio
        """
        selected_policies = [policies[i] for i in policy_indices]

        # Calculate weighted objectives
        total_delta_yen = sum(
            w * p.delta_yen
            for w, p in zip(weights, selected_policies)
        )

        # Risk calculation: Portfolio risk with diversification effect
        # σ_portfolio = sqrt(Σw²σ² + ΣΣw_i·w_j·ρ_ij·σ_i·σ_j)
        # Simplified: Assume independent (ρ=0), use weighted average
        total_risk = sum(
            w * p.risk_score
            for w, p in zip(weights, selected_policies)
        )

        # Feasibility: Weighted average
        total_feasibility = sum(
            w * p.feasibility_score
            for w, p in zip(weights, selected_policies)
        )

        # Total cost
        total_cost = sum(p.cost for p in selected_policies)

        # ROI
        roi = total_delta_yen / total_cost if total_cost > 0 else 0

        # Average CAS score
        cas_score_avg = np.mean([p.cas_score for p in selected_policies])

        return ParetoSolution(
            policies=[p.policy_id for p in selected_policies],
            weights=weights,
            total_delta_yen=total_delta_yen,
            total_risk=total_risk,
            total_feasibility=total_feasibility,
            total_cost=total_cost,
            roi=roi,
            cas_score_avg=cas_score_avg,
            dominance_rank=0  # Will be assigned later
        )

    def _rank_solutions(
        self,
        solutions: List[ParetoSolution]
    ) -> List[ParetoSolution]:
        """
        Rank solutions by Pareto dominance

        Rank 1: Non-dominated (Pareto frontier)
        Rank 2: Dominated by rank 1 only
        etc.
        """
        ranked = []
        remaining = solutions.copy()
        rank = 1

        while remaining:
            # Find non-dominated solutions in remaining set
            non_dominated = []

            for i, sol_i in enumerate(remaining):
                is_dominated = False

                for j, sol_j in enumerate(remaining):
                    if i == j:
                        continue

                    # Check if sol_j dominates sol_i
                    # Dominance: sol_j is better or equal in all objectives,
                    # and strictly better in at least one
                    if self._dominates(sol_j, sol_i):
                        is_dominated = True
                        break

                if not is_dominated:
                    sol_i.dominance_rank = rank
                    non_dominated.append(sol_i)

            ranked.extend(non_dominated)

            # Remove non-dominated from remaining
            remaining = [s for s in remaining if s not in non_dominated]
            rank += 1

        return ranked

    def _dominates(self, sol_a: ParetoSolution, sol_b: ParetoSolution) -> bool:
        """
        Check if solution A dominates solution B

        Objectives (to maximize):
        1. total_delta_yen (profit)
        2. -total_risk (minimize risk)
        3. total_feasibility
        """
        # Extract objectives (all to maximize)
        obj_a = [sol_a.total_delta_yen, -sol_a.total_risk, sol_a.total_feasibility]
        obj_b = [sol_b.total_delta_yen, -sol_b.total_risk, sol_b.total_feasibility]

        # A dominates B if:
        # - A is >= B in all objectives
        # - A is > B in at least one objective
        better_or_equal = all(a >= b for a, b in zip(obj_a, obj_b))
        strictly_better = any(a > b for a, b in zip(obj_a, obj_b))

        return better_or_equal and strictly_better

    def recommend_portfolio(
        self,
        pareto_solutions: List[ParetoSolution]
    ) -> ParetoSolution:
        """
        Recommend best portfolio based on risk appetite

        Parameters
        ----------
        pareto_solutions : List[ParetoSolution]
            Pareto-optimal solutions

        Returns
        -------
        ParetoSolution
            Recommended portfolio
        """
        if not pareto_solutions:
            raise ValueError("No solutions provided")

        # Filter to rank 1 (non-dominated) only
        frontier = [s for s in pareto_solutions if s.dominance_rank == 1]

        if not frontier:
            frontier = pareto_solutions  # Fallback

        # Score solutions based on risk appetite
        weights = self.risk_weights[self.risk_appetite]

        scored = []
        for sol in frontier:
            # Normalize objectives
            max_profit = max(s.total_delta_yen for s in frontier)
            max_feasibility = max(s.total_feasibility for s in frontier)
            min_risk = min(s.total_risk for s in frontier)

            profit_score = sol.total_delta_yen / max_profit if max_profit > 0 else 0
            risk_score = (1 - sol.total_risk) if min_risk < 1 else 0  # Lower risk is better
            feasibility_score = sol.total_feasibility / max_feasibility if max_feasibility > 0 else 0

            composite = (
                weights['profit'] * profit_score +
                weights['risk'] * risk_score +
                weights['feasibility'] * feasibility_score
            )

            scored.append((sol, composite))

        # Return highest scoring solution
        scored.sort(key=lambda x: x[1], reverse=True)

        recommended = scored[0][0]

        logger.info(f"📊 Recommended portfolio ({self.risk_appetite} strategy):")
        logger.info(f"   Policies: {len(recommended.policies)}")
        logger.info(f"   Total Δ¥: ¥{recommended.total_delta_yen:,.0f}")
        logger.info(f"   Risk score: {recommended.total_risk:.2f}")
        logger.info(f"   ROI: {recommended.roi:.1f}x")

        return recommended

    def visualize_frontier(
        self,
        pareto_solutions: List[ParetoSolution]
    ) -> pd.DataFrame:
        """
        Generate data for 3D Pareto frontier visualization

        Returns
        -------
        pd.DataFrame
            Data for plotting (profit, risk, feasibility, rank)
        """
        data = []

        for sol in pareto_solutions:
            data.append({
                'total_delta_yen': sol.total_delta_yen,
                'total_risk': sol.total_risk,
                'total_feasibility': sol.total_feasibility,
                'dominance_rank': sol.dominance_rank,
                'n_policies': len(sol.policies),
                'roi': sol.roi,
                'total_cost': sol.total_cost,
                'cas_score_avg': sol.cas_score_avg
            })

        return pd.DataFrame(data)
