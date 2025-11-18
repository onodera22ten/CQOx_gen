"""
Multi-objective optimization for policy selection
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger


class MultiObjectiveOptimizer:
    """
    Multi-objective optimization for marketing policies

    Finds Pareto frontier across multiple objectives
    (e.g., profit vs risk, profit vs churn, profit vs fairness)
    """

    def __init__(self, objectives: List[str]):
        """
        Args:
            objectives: List of objective names
        """
        self.objectives = objectives

    def evaluate_policies(
        self,
        policies: List[Dict[str, Any]],
        objective_functions: Dict[str, callable]
    ) -> pd.DataFrame:
        """
        Evaluate policies across all objectives

        Args:
            policies: List of policy dicts
            objective_functions: Dict mapping objective name to evaluation function

        Returns:
            DataFrame with policy evaluations
        """
        logger.info(f"Evaluating {len(policies)} policies across {len(self.objectives)} objectives")

        results = []

        for policy in policies:
            policy_result = {'policy_id': policy['id'], 'policy_name': policy['name']}

            for obj_name in self.objectives:
                if obj_name in objective_functions:
                    obj_value = objective_functions[obj_name](policy)
                    policy_result[obj_name] = obj_value
                else:
                    policy_result[obj_name] = None

            results.append(policy_result)

        df = pd.DataFrame(results)
        logger.info(f"Evaluated policies: {len(df)} rows")
        return df

    def find_pareto_frontier(
        self,
        evaluations: pd.DataFrame,
        maximize: Optional[List[bool]] = None
    ) -> pd.DataFrame:
        """
        Find Pareto frontier

        Args:
            evaluations: DataFrame with policy evaluations
            maximize: List of bools indicating whether to maximize each objective
                      (default: True for all)

        Returns:
            DataFrame with Pareto-optimal policies
        """
        logger.info("Finding Pareto frontier")

        if maximize is None:
            maximize = [True] * len(self.objectives)

        # Extract objective values
        obj_cols = [col for col in evaluations.columns if col in self.objectives]
        obj_values = evaluations[obj_cols].values.copy()

        # Convert minimization to maximization
        for i, (col, is_max) in enumerate(zip(obj_cols, maximize)):
            if not is_max:
                obj_values[:, i] = -obj_values[:, i]

        # Find Pareto frontier
        is_pareto = np.ones(len(obj_values), dtype=bool)

        for i, point in enumerate(obj_values):
            if is_pareto[i]:
                # Check if any other point dominates this one
                is_dominated = np.any(
                    np.all(obj_values[is_pareto] >= point, axis=1) &
                    np.any(obj_values[is_pareto] > point, axis=1)
                )
                if is_dominated:
                    is_pareto[i] = False

        pareto_df = evaluations[is_pareto].copy()
        logger.info(f"Found {len(pareto_df)} Pareto-optimal policies")

        return pareto_df

    def get_frontier_2d(
        self,
        evaluations: pd.DataFrame,
        obj1: str,
        obj2: str
    ) -> Dict[str, Any]:
        """
        Get 2D frontier data for plotting

        Args:
            evaluations: DataFrame with policy evaluations
            obj1: First objective name (x-axis)
            obj2: Second objective name (y-axis)

        Returns:
            Dict with plotting data
        """
        pareto = self.find_pareto_frontier(evaluations)

        return {
            'all_policies': {
                'x': evaluations[obj1].tolist(),
                'y': evaluations[obj2].tolist(),
                'policy_ids': evaluations['policy_id'].tolist()
            },
            'pareto_frontier': {
                'x': pareto[obj1].tolist(),
                'y': pareto[obj2].tolist(),
                'policy_ids': pareto['policy_id'].tolist()
            },
            'obj1_name': obj1,
            'obj2_name': obj2
        }

    def recommend_policy(
        self,
        evaluations: pd.DataFrame,
        weights: Dict[str, float],
        constraints: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict[str, Any]:
        """
        Recommend a single policy based on weighted objectives

        Args:
            evaluations: DataFrame with policy evaluations
            weights: Dict mapping objective name to weight
            constraints: Dict mapping objective name to (min, max) bounds

        Returns:
            Recommended policy info
        """
        logger.info("Recommending policy based on weighted objectives")

        # Apply constraints
        df = evaluations.copy()
        if constraints:
            for obj, (min_val, max_val) in constraints.items():
                if obj in df.columns:
                    df = df[(df[obj] >= min_val) & (df[obj] <= max_val)]

        if len(df) == 0:
            logger.warning("No policies satisfy constraints")
            return None

        # Calculate weighted score
        df['weighted_score'] = 0.0
        for obj, weight in weights.items():
            if obj in df.columns:
                # Normalize objective values to [0, 1]
                obj_min = df[obj].min()
                obj_max = df[obj].max()
                if obj_max > obj_min:
                    df[f'{obj}_normalized'] = (df[obj] - obj_min) / (obj_max - obj_min)
                else:
                    df[f'{obj}_normalized'] = 1.0

                df['weighted_score'] += weight * df[f'{obj}_normalized']

        # Select best policy
        best_idx = df['weighted_score'].idxmax()
        best_policy = df.loc[best_idx].to_dict()

        logger.info(f"Recommended policy: {best_policy['policy_id']}")
        return best_policy
