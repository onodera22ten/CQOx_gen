"""
Counterfactual Recourse Engine
Generate actionable interventions for individuals to achieve desired outcomes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from sklearn.base import BaseEstimator
from scipy.optimize import minimize, differential_evolution
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecourseCandidate:
    """A single recourse intervention option"""
    intervention: Dict[str, float]  # feature → new value
    predicted_outcome: float
    cost: float
    feasibility: float  # 0-1
    actionability: float  # 0-1
    diversity: Optional[float] = None


class RecourseGenerator:
    """Generate counterfactual recourse plans for individuals"""

    def __init__(self,
                 model: BaseEstimator,
                 feature_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
                 feature_costs: Optional[Dict[str, float]] = None,
                 cost_type: str = 'L1'):
        """
        Args:
            model: Trained outcome prediction model
            feature_ranges: Valid range for each feature (min, max)
            feature_costs: Cost of changing each feature
            cost_type: 'L1', 'L2', or 'custom'
        """
        self.model = model
        self.feature_ranges = feature_ranges or {}
        self.feature_costs = feature_costs or {}
        self.cost_type = cost_type

    def compute_cost(self,
                    original: Dict[str, float],
                    modified: Dict[str, float],
                    actionable_features: List[str]) -> float:
        """
        Compute cost of changing features from original to modified

        Args:
            original: Original feature values
            modified: Modified feature values
            actionable_features: Which features can be changed
        """
        if self.cost_type == 'L1':
            cost = sum(
                abs(modified.get(feat, original[feat]) - original[feat]) *
                self.feature_costs.get(feat, 1.0)
                for feat in actionable_features
            )
        elif self.cost_type == 'L2':
            cost = np.sqrt(sum(
                ((modified.get(feat, original[feat]) - original[feat]) ** 2) *
                self.feature_costs.get(feat, 1.0)
                for feat in actionable_features
            ))
        else:
            # Custom cost function
            cost = sum(
                abs(modified.get(feat, original[feat]) - original[feat])
                for feat in actionable_features
            )

        return cost

    def compute_feasibility(self,
                           modified: Dict[str, float],
                           actionable_features: List[str]) -> float:
        """
        Compute feasibility score based on feature ranges

        Returns:
            Score in [0, 1], where 1 = all features in valid range
        """
        if not self.feature_ranges:
            return 1.0

        violations = 0
        total = 0

        for feat in actionable_features:
            if feat in self.feature_ranges:
                total += 1
                min_val, max_val = self.feature_ranges[feat]
                val = modified.get(feat, 0)

                if val < min_val or val > max_val:
                    # Compute how far out of range
                    if val < min_val:
                        violation = (min_val - val) / (max_val - min_val)
                    else:
                        violation = (val - max_val) / (max_val - min_val)
                    violations += violation

        if total == 0:
            return 1.0

        # Convert violations to feasibility score
        feasibility = max(0.0, 1.0 - violations / total)
        return feasibility

    def compute_actionability(self,
                             original: Dict[str, float],
                             modified: Dict[str, float],
                             actionable_features: List[str]) -> float:
        """
        Compute actionability score based on magnitude of changes

        Smaller changes are more actionable.

        Returns:
            Score in [0, 1], where 1 = very actionable (small changes)
        """
        if not actionable_features:
            return 0.0

        # Compute normalized change magnitude
        changes = []
        for feat in actionable_features:
            original_val = original[feat]
            modified_val = modified.get(feat, original_val)

            # Normalize by feature range if available
            if feat in self.feature_ranges:
                min_val, max_val = self.feature_ranges[feat]
                if max_val > min_val:
                    normalized_change = abs(modified_val - original_val) / (max_val - min_val)
                else:
                    normalized_change = abs(modified_val - original_val)
            else:
                # Normalize by original value or use absolute change
                if abs(original_val) > 1e-6:
                    normalized_change = abs(modified_val - original_val) / abs(original_val)
                else:
                    normalized_change = abs(modified_val - original_val)

            changes.append(normalized_change)

        # Average normalized change
        avg_change = np.mean(changes)

        # Convert to actionability score (inverse of change)
        # Use exponential decay: actionability = exp(-k * change)
        k = 2.0  # decay rate
        actionability = np.exp(-k * avg_change)

        return float(actionability)

    def predict_outcome(self, features: Dict[str, float], all_features: List[str]) -> float:
        """Predict outcome for given feature values"""
        # Convert dict to array in correct order
        X = np.array([features.get(feat, 0.0) for feat in all_features]).reshape(1, -1)
        prediction = self.model.predict(X)[0]
        return float(prediction)

    def generate_recourse_optimization(self,
                                      current_features: Dict[str, float],
                                      target_outcome: float,
                                      actionable_features: List[str],
                                      immutable_features: List[str] = None,
                                      all_features: Optional[List[str]] = None,
                                      cost_weight: float = 1.0,
                                      feasibility_weight: float = 10.0) -> Optional[RecourseCandidate]:
        """
        Generate recourse using optimization

        Minimize: cost + feasibility_penalty
        Subject to: predicted_outcome >= target_outcome

        Args:
            current_features: Current feature values
            target_outcome: Desired outcome value
            actionable_features: Features that can be changed
            immutable_features: Features that cannot be changed
            all_features: All feature names in model order
            cost_weight: Weight for cost term
            feasibility_weight: Weight for feasibility penalty

        Returns:
            RecourseCandidate or None if no solution found
        """
        if immutable_features is None:
            immutable_features = []

        if all_features is None:
            all_features = list(current_features.keys())

        # Define optimization objective
        def objective(x_actionable):
            """Objective: minimize cost + feasibility penalty"""
            # Construct full feature vector
            modified = current_features.copy()
            for i, feat in enumerate(actionable_features):
                modified[feat] = x_actionable[i]

            # Compute cost
            cost = self.compute_cost(current_features, modified, actionable_features)

            # Compute feasibility penalty
            feasibility = self.compute_feasibility(modified, actionable_features)
            feasibility_penalty = feasibility_weight * (1.0 - feasibility)

            # Predict outcome
            predicted = self.predict_outcome(modified, all_features)

            # Penalty for not reaching target
            target_penalty = max(0, target_outcome - predicted) * 100.0

            total = cost_weight * cost + feasibility_penalty + target_penalty

            return total

        # Define constraint: predicted outcome >= target
        def constraint(x_actionable):
            modified = current_features.copy()
            for i, feat in enumerate(actionable_features):
                modified[feat] = x_actionable[i]

            predicted = self.predict_outcome(modified, all_features)
            return predicted - target_outcome  # >= 0

        # Initial guess: current values
        x0 = np.array([current_features[feat] for feat in actionable_features])

        # Bounds from feature ranges
        bounds = []
        for feat in actionable_features:
            if feat in self.feature_ranges:
                bounds.append(self.feature_ranges[feat])
            else:
                # No bounds specified, use +/- 3 std from current
                current_val = current_features[feat]
                bounds.append((current_val - 3.0, current_val + 3.0))

        # Optimize
        try:
            result = minimize(
                objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints={'type': 'ineq', 'fun': constraint},
                options={'maxiter': 1000}
            )

            if not result.success:
                logger.warning(f"Optimization failed: {result.message}")
                return None

            # Extract solution
            x_solution = result.x
            modified = current_features.copy()
            for i, feat in enumerate(actionable_features):
                modified[feat] = float(x_solution[i])

            # Compute metrics
            predicted = self.predict_outcome(modified, all_features)
            cost = self.compute_cost(current_features, modified, actionable_features)
            feasibility = self.compute_feasibility(modified, actionable_features)
            actionability = self.compute_actionability(current_features, modified, actionable_features)

            return RecourseCandidate(
                intervention=modified,
                predicted_outcome=predicted,
                cost=cost,
                feasibility=feasibility,
                actionability=actionability
            )

        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return None

    def generate_diverse_recourse(self,
                                 current_features: Dict[str, float],
                                 target_outcome: float,
                                 actionable_features: List[str],
                                 immutable_features: List[str] = None,
                                 all_features: Optional[List[str]] = None,
                                 n_candidates: int = 5,
                                 diversity_weight: float = 0.1) -> List[RecourseCandidate]:
        """
        Generate diverse set of recourse candidates

        Uses evolutionary algorithm to find multiple diverse solutions

        Args:
            current_features: Current feature values
            target_outcome: Desired outcome
            actionable_features: Features that can be changed
            immutable_features: Features that cannot be changed
            all_features: All feature names in model order
            n_candidates: Number of diverse candidates to generate
            diversity_weight: Weight for diversity term

        Returns:
            List of RecourseCandidate objects
        """
        if immutable_features is None:
            immutable_features = []

        if all_features is None:
            all_features = list(current_features.keys())

        candidates = []

        # Generate multiple candidates with different random seeds
        for seed in range(n_candidates * 3):  # Try more seeds to ensure diversity
            np.random.seed(seed)

            # Define objective with diversity penalty
            def objective(x_actionable):
                modified = current_features.copy()
                for i, feat in enumerate(actionable_features):
                    modified[feat] = x_actionable[i]

                # Cost
                cost = self.compute_cost(current_features, modified, actionable_features)

                # Feasibility
                feasibility = self.compute_feasibility(modified, actionable_features)
                feasibility_penalty = 10.0 * (1.0 - feasibility)

                # Outcome constraint
                predicted = self.predict_outcome(modified, all_features)
                target_penalty = max(0, target_outcome - predicted) * 100.0

                # Diversity penalty: penalize being similar to existing candidates
                diversity_penalty = 0.0
                if candidates:
                    for candidate in candidates:
                        # L2 distance in feature space
                        distance = np.sqrt(sum(
                            (modified.get(feat, current_features[feat]) -
                             candidate.intervention.get(feat, current_features[feat])) ** 2
                            for feat in actionable_features
                        ))
                        # Penalize small distances
                        diversity_penalty += diversity_weight * np.exp(-distance)

                return cost + feasibility_penalty + target_penalty + diversity_penalty

            # Bounds
            bounds = []
            for feat in actionable_features:
                if feat in self.feature_ranges:
                    bounds.append(self.feature_ranges[feat])
                else:
                    current_val = current_features[feat]
                    bounds.append((current_val - 3.0, current_val + 3.0))

            # Differential evolution (global optimizer)
            try:
                result = differential_evolution(
                    objective,
                    bounds,
                    seed=seed,
                    maxiter=100,
                    popsize=10
                )

                if result.success:
                    x_solution = result.x
                    modified = current_features.copy()
                    for i, feat in enumerate(actionable_features):
                        modified[feat] = float(x_solution[i])

                    predicted = self.predict_outcome(modified, all_features)

                    # Only accept if target is met
                    if predicted >= target_outcome:
                        cost = self.compute_cost(current_features, modified, actionable_features)
                        feasibility = self.compute_feasibility(modified, actionable_features)
                        actionability = self.compute_actionability(current_features, modified, actionable_features)

                        candidate = RecourseCandidate(
                            intervention=modified,
                            predicted_outcome=predicted,
                            cost=cost,
                            feasibility=feasibility,
                            actionability=actionability
                        )

                        candidates.append(candidate)

                        if len(candidates) >= n_candidates:
                            break

            except Exception as e:
                logger.warning(f"Differential evolution failed with seed {seed}: {e}")
                continue

        # Compute diversity scores
        if len(candidates) > 1:
            for i, candidate_i in enumerate(candidates):
                # Average distance to other candidates
                distances = []
                for j, candidate_j in enumerate(candidates):
                    if i != j:
                        distance = np.sqrt(sum(
                            (candidate_i.intervention.get(feat, current_features[feat]) -
                             candidate_j.intervention.get(feat, current_features[feat])) ** 2
                            for feat in actionable_features
                        ))
                        distances.append(distance)

                candidate_i.diversity = float(np.mean(distances)) if distances else 0.0

        # Sort by cost (prefer lower cost)
        candidates.sort(key=lambda c: c.cost)

        return candidates[:n_candidates]

    def generate_greedy_recourse(self,
                                current_features: Dict[str, float],
                                target_outcome: float,
                                actionable_features: List[str],
                                all_features: Optional[List[str]] = None,
                                max_iterations: int = 100) -> Optional[RecourseCandidate]:
        """
        Generate recourse using greedy feature modification

        Iteratively modify the feature that gives the best improvement in outcome per unit cost.

        Args:
            current_features: Current feature values
            target_outcome: Desired outcome
            actionable_features: Features that can be changed
            all_features: All feature names in model order
            max_iterations: Maximum number of feature modifications

        Returns:
            RecourseCandidate or None
        """
        if all_features is None:
            all_features = list(current_features.keys())

        modified = current_features.copy()
        current_outcome = self.predict_outcome(modified, all_features)

        for iteration in range(max_iterations):
            if current_outcome >= target_outcome:
                # Target reached
                break

            best_improvement_per_cost = -np.inf
            best_feature = None
            best_new_value = None

            # Try modifying each actionable feature
            for feat in actionable_features:
                # Try small positive and negative changes
                current_val = modified[feat]

                # Determine step size
                if feat in self.feature_ranges:
                    min_val, max_val = self.feature_ranges[feat]
                    step = (max_val - min_val) * 0.1
                else:
                    step = abs(current_val) * 0.1 if abs(current_val) > 1e-6 else 0.1

                for direction in [1, -1]:
                    new_val = current_val + direction * step

                    # Check bounds
                    if feat in self.feature_ranges:
                        min_val, max_val = self.feature_ranges[feat]
                        if new_val < min_val or new_val > max_val:
                            continue

                    # Predict outcome with this change
                    test_modified = modified.copy()
                    test_modified[feat] = new_val
                    new_outcome = self.predict_outcome(test_modified, all_features)

                    # Compute improvement
                    improvement = new_outcome - current_outcome

                    # Compute cost of this change
                    cost = abs(new_val - current_val) * self.feature_costs.get(feat, 1.0)

                    # Improvement per unit cost
                    if cost > 1e-6:
                        improvement_per_cost = improvement / cost
                    else:
                        improvement_per_cost = improvement

                    if improvement_per_cost > best_improvement_per_cost:
                        best_improvement_per_cost = improvement_per_cost
                        best_feature = feat
                        best_new_value = new_val

            # Apply best modification
            if best_feature is not None:
                modified[best_feature] = best_new_value
                current_outcome = self.predict_outcome(modified, all_features)
            else:
                # No improvement found
                break

        # Check if target was reached
        if current_outcome < target_outcome:
            logger.warning("Greedy recourse did not reach target outcome")
            return None

        # Compute final metrics
        cost = self.compute_cost(current_features, modified, actionable_features)
        feasibility = self.compute_feasibility(modified, actionable_features)
        actionability = self.compute_actionability(current_features, modified, actionable_features)

        return RecourseCandidate(
            intervention=modified,
            predicted_outcome=current_outcome,
            cost=cost,
            feasibility=feasibility,
            actionability=actionability
        )
