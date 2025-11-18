"""
Offline Policy Learning with Off-Policy Evaluation
Doubly Robust, IPW, and Direct Method estimators
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from scipy import stats
from sklearn.base import BaseEstimator
from sklearn.model_selection import cross_val_predict
import logging

logger = logging.getLogger(__name__)


@dataclass
class OPEResult:
    """Off-Policy Evaluation result"""
    mean: float
    std: float
    variance: float
    bias: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    estimates: Optional[np.ndarray] = None


class Policy:
    """Abstract policy class"""

    def assign_treatment(self, features: Dict[str, float]) -> Any:
        """Assign treatment given features"""
        raise NotImplementedError

    def get_params(self) -> Dict[str, Any]:
        """Get policy parameters"""
        raise NotImplementedError


class ThresholdPolicy(Policy):
    """Threshold-based policy: treat if score > threshold"""

    def __init__(self, feature: str, threshold: float, treatment_values: Tuple[Any, Any] = (0, 1)):
        self.feature = feature
        self.threshold = threshold
        self.treatment_values = treatment_values  # (control, treatment)

    def assign_treatment(self, features: Dict[str, float]) -> Any:
        score = features.get(self.feature, 0.0)
        return self.treatment_values[1] if score > self.threshold else self.treatment_values[0]

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'threshold',
            'feature': self.feature,
            'threshold': self.threshold,
            'treatment_values': self.treatment_values
        }


class LinearScorePolicy(Policy):
    """Linear scoring policy: treat if linear combination > threshold"""

    def __init__(self, coefficients: Dict[str, float], threshold: float = 0.0,
                 treatment_values: Tuple[Any, Any] = (0, 1)):
        self.coefficients = coefficients
        self.threshold = threshold
        self.treatment_values = treatment_values

    def assign_treatment(self, features: Dict[str, float]) -> Any:
        score = sum(features.get(feat, 0.0) * coef
                   for feat, coef in self.coefficients.items())
        return self.treatment_values[1] if score > self.threshold else self.treatment_values[0]

    def get_params(self) -> Dict[str, Any]:
        return {
            'type': 'linear',
            'coefficients': self.coefficients,
            'threshold': self.threshold,
            'treatment_values': self.treatment_values
        }


class OffPolicyEvaluator:
    """Off-Policy Evaluation using various estimators"""

    def __init__(self,
                 propensity_model: Optional[BaseEstimator] = None,
                 outcome_model: Optional[BaseEstimator] = None):
        """
        Args:
            propensity_model: Model that predicts P(A=1|X), returns probabilities
            outcome_model: Model that predicts E[Y|X,A]
        """
        self.propensity_model = propensity_model
        self.outcome_model = outcome_model

    def inverse_propensity_weighting(self,
                                     policy: Policy,
                                     dataset: pd.DataFrame,
                                     treatment_col: str = 'treatment',
                                     outcome_col: str = 'outcome',
                                     feature_cols: Optional[List[str]] = None,
                                     propensity_col: Optional[str] = 'propensity',
                                     clip_weights: Tuple[float, float] = (0.01, 100.0)) -> OPEResult:
        """
        Inverse Propensity Weighting (IPW) estimator

        V^IPW(π) = 1/n Σ [ π(A_i|X_i) / e(A_i|X_i) * Y_i ]

        Args:
            policy: Policy to evaluate
            dataset: Historical data
            treatment_col: Column name for treatment
            outcome_col: Column name for outcome
            feature_cols: Feature column names
            propensity_col: Column name for propensity scores (if pre-computed)
            clip_weights: Min and max values to clip importance weights
        """
        if feature_cols is None:
            feature_cols = [c for c in dataset.columns
                          if c not in [treatment_col, outcome_col, propensity_col]]

        n = len(dataset)
        estimates = np.zeros(n)

        for i in range(n):
            row = dataset.iloc[i]
            x = {col: row[col] for col in feature_cols}
            a_obs = row[treatment_col]
            y_obs = row[outcome_col]

            # Get propensity score
            if propensity_col in dataset.columns:
                e = row[propensity_col]
            elif self.propensity_model is not None:
                X_i = np.array([row[col] for col in feature_cols]).reshape(1, -1)
                e = self.propensity_model.predict_proba(X_i)[0, 1]
            else:
                raise ValueError("Must provide propensity scores or propensity model")

            # Get policy probability
            a_policy = policy.assign_treatment(x)
            pi = 1.0 if a_policy == a_obs else 0.0

            # Clip importance weight
            weight = pi / max(e, 0.001)
            weight = np.clip(weight, clip_weights[0], clip_weights[1])

            estimates[i] = weight * y_obs

        mean = np.mean(estimates)
        std = np.std(estimates)
        variance = np.var(estimates)

        # Confidence interval using CLT
        se = std / np.sqrt(n)
        ci = (mean - 1.96 * se, mean + 1.96 * se)

        return OPEResult(
            mean=mean,
            std=std,
            variance=variance,
            confidence_interval=ci,
            estimates=estimates
        )

    def direct_method(self,
                     policy: Policy,
                     dataset: pd.DataFrame,
                     treatment_col: str = 'treatment',
                     outcome_col: str = 'outcome',
                     feature_cols: Optional[List[str]] = None) -> OPEResult:
        """
        Direct Method (DM) estimator using outcome regression

        V^DM(π) = 1/n Σ μ(X_i, π(X_i))

        where μ(x,a) = E[Y|X=x,A=a]
        """
        if self.outcome_model is None:
            raise ValueError("Direct method requires outcome_model")

        if feature_cols is None:
            feature_cols = [c for c in dataset.columns
                          if c not in [treatment_col, outcome_col]]

        n = len(dataset)
        estimates = np.zeros(n)

        for i in range(n):
            row = dataset.iloc[i]
            x = {col: row[col] for col in feature_cols}

            # Policy treatment assignment
            a_policy = policy.assign_treatment(x)

            # Predict outcome under policy
            X_i = np.array([row[col] for col in feature_cols]).reshape(1, -1)
            # Assume outcome_model can take treatment as input
            # This requires outcome_model to be trained on features + treatment
            features_with_treatment = np.append(X_i, a_policy).reshape(1, -1)
            mu_policy = self.outcome_model.predict(features_with_treatment)[0]

            estimates[i] = mu_policy

        mean = np.mean(estimates)
        std = np.std(estimates)
        variance = np.var(estimates)

        se = std / np.sqrt(n)
        ci = (mean - 1.96 * se, mean + 1.96 * se)

        return OPEResult(
            mean=mean,
            std=std,
            variance=variance,
            confidence_interval=ci,
            estimates=estimates
        )

    def doubly_robust(self,
                     policy: Policy,
                     dataset: pd.DataFrame,
                     treatment_col: str = 'treatment',
                     outcome_col: str = 'outcome',
                     feature_cols: Optional[List[str]] = None,
                     propensity_col: Optional[str] = 'propensity',
                     clip_weights: Tuple[float, float] = (0.01, 100.0)) -> OPEResult:
        """
        Doubly Robust (DR) estimator

        V^DR(π) = 1/n Σ [ μ(X_i, π(X_i)) +
                         (π(A_i|X_i) / e(A_i|X_i)) * (Y_i - μ(X_i, A_i)) ]

        This estimator is consistent if either the propensity model OR the outcome model
        is correctly specified (hence "doubly robust").

        Args:
            policy: Policy to evaluate
            dataset: Historical data with observed (X, A, Y)
            treatment_col: Treatment column name
            outcome_col: Outcome column name
            feature_cols: Feature column names
            propensity_col: Propensity score column (if pre-computed)
            clip_weights: Min/max for importance weights
        """
        if self.outcome_model is None:
            raise ValueError("Doubly robust requires outcome_model")

        if feature_cols is None:
            feature_cols = [c for c in dataset.columns
                          if c not in [treatment_col, outcome_col, propensity_col]]

        n = len(dataset)
        estimates = np.zeros(n)

        for i in range(n):
            row = dataset.iloc[i]
            x = {col: row[col] for col in feature_cols}
            a_obs = row[treatment_col]
            y_obs = row[outcome_col]

            # Get propensity score e(A_obs|X)
            if propensity_col in dataset.columns:
                e = row[propensity_col]
            elif self.propensity_model is not None:
                X_i = np.array([row[col] for col in feature_cols]).reshape(1, -1)
                probs = self.propensity_model.predict_proba(X_i)[0]
                e = probs[1] if a_obs == 1 else probs[0]
            else:
                raise ValueError("Must provide propensity scores or propensity model")

            # Get outcome predictions
            X_i = np.array([row[col] for col in feature_cols]).reshape(1, -1)

            # μ(X_i, A_obs) - predicted outcome under observed treatment
            features_obs = np.append(X_i, a_obs).reshape(1, -1)
            mu_obs = self.outcome_model.predict(features_obs)[0]

            # μ(X_i, π(X_i)) - predicted outcome under policy treatment
            a_policy = policy.assign_treatment(x)
            features_policy = np.append(X_i, a_policy).reshape(1, -1)
            mu_policy = self.outcome_model.predict(features_policy)[0]

            # Policy probability π(A_obs|X)
            pi = 1.0 if a_policy == a_obs else 0.0

            # Importance weight with clipping
            weight = pi / max(e, 0.001)
            weight = np.clip(weight, clip_weights[0], clip_weights[1])

            # DR estimator
            estimates[i] = mu_policy + weight * (y_obs - mu_obs)

        mean = np.mean(estimates)
        std = np.std(estimates)
        variance = np.var(estimates)

        # Confidence interval
        se = std / np.sqrt(n)
        ci = (mean - 1.96 * se, mean + 1.96 * se)

        return OPEResult(
            mean=mean,
            std=std,
            variance=variance,
            confidence_interval=ci,
            estimates=estimates
        )

    def bootstrap_evaluation(self,
                            policy: Policy,
                            dataset: pd.DataFrame,
                            method: str = 'DR',
                            n_bootstrap: int = 1000,
                            **kwargs) -> OPEResult:
        """
        Bootstrap estimation for confidence intervals

        Args:
            policy: Policy to evaluate
            dataset: Historical data
            method: 'DR', 'IPW', or 'DM'
            n_bootstrap: Number of bootstrap samples
            **kwargs: Additional arguments for the estimator
        """
        estimator_func = {
            'DR': self.doubly_robust,
            'IPW': self.inverse_propensity_weighting,
            'DM': self.direct_method
        }[method]

        # Original estimate
        original = estimator_func(policy, dataset, **kwargs)

        # Bootstrap
        bootstrap_estimates = np.zeros(n_bootstrap)
        n = len(dataset)

        for b in range(n_bootstrap):
            # Resample with replacement
            indices = np.random.choice(n, size=n, replace=True)
            bootstrap_sample = dataset.iloc[indices].reset_index(drop=True)

            # Evaluate on bootstrap sample
            result = estimator_func(policy, bootstrap_sample, **kwargs)
            bootstrap_estimates[b] = result.mean

        # Bootstrap statistics
        boot_mean = np.mean(bootstrap_estimates)
        boot_std = np.std(bootstrap_estimates)

        # Percentile confidence interval
        ci_lower = np.percentile(bootstrap_estimates, 2.5)
        ci_upper = np.percentile(bootstrap_estimates, 97.5)

        # Bias estimation
        bias = boot_mean - original.mean

        return OPEResult(
            mean=original.mean,
            std=boot_std,
            variance=boot_std**2,
            bias=bias,
            confidence_interval=(ci_lower, ci_upper),
            estimates=bootstrap_estimates
        )


class PolicyOptimizer:
    """Optimize policy parameters to maximize expected value"""

    def __init__(self, evaluator: OffPolicyEvaluator):
        self.evaluator = evaluator

    def grid_search_threshold(self,
                             dataset: pd.DataFrame,
                             feature: str,
                             treatment_col: str = 'treatment',
                             outcome_col: str = 'outcome',
                             n_thresholds: int = 100,
                             method: str = 'DR',
                             risk_metric: str = 'std',
                             risk_aversion: float = 0.0) -> List[Dict]:
        """
        Grid search over threshold values to find Pareto frontier

        Args:
            dataset: Historical data
            feature: Feature to threshold on
            treatment_col: Treatment column
            outcome_col: Outcome column
            n_thresholds: Number of threshold values to try
            method: OPE method ('DR', 'IPW', 'DM')
            risk_metric: 'std', 'var', 'cvar'
            risk_aversion: Weight on risk (0 = risk-neutral, 1 = very risk-averse)

        Returns:
            List of frontier points with (expected_value, risk, policy_params)
        """
        # Get threshold range from feature distribution
        feature_values = dataset[feature].values
        thresholds = np.linspace(feature_values.min(), feature_values.max(), n_thresholds)

        results = []

        for threshold in thresholds:
            policy = ThresholdPolicy(feature=feature, threshold=float(threshold))

            # Evaluate policy
            if method == 'DR':
                ope_result = self.evaluator.doubly_robust(
                    policy, dataset,
                    treatment_col=treatment_col,
                    outcome_col=outcome_col
                )
            elif method == 'IPW':
                ope_result = self.evaluator.inverse_propensity_weighting(
                    policy, dataset,
                    treatment_col=treatment_col,
                    outcome_col=outcome_col
                )
            elif method == 'DM':
                ope_result = self.evaluator.direct_method(
                    policy, dataset,
                    treatment_col=treatment_col,
                    outcome_col=outcome_col
                )
            else:
                raise ValueError(f"Unknown method: {method}")

            # Calculate risk
            if risk_metric == 'std':
                risk = ope_result.std
            elif risk_metric == 'var':
                risk = ope_result.variance
            elif risk_metric == 'cvar':
                # Conditional Value at Risk (average of worst 5%)
                if ope_result.estimates is not None:
                    cutoff = np.percentile(ope_result.estimates, 5)
                    risk = -np.mean(ope_result.estimates[ope_result.estimates <= cutoff])
                else:
                    risk = ope_result.std
            else:
                risk = ope_result.std

            # Utility = expected_value - risk_aversion * risk
            utility = ope_result.mean - risk_aversion * risk

            results.append({
                'threshold': float(threshold),
                'expected_value': float(ope_result.mean),
                'risk': float(risk),
                'std': float(ope_result.std),
                'utility': float(utility),
                'ci_lower': float(ope_result.confidence_interval[0]) if ope_result.confidence_interval else None,
                'ci_upper': float(ope_result.confidence_interval[1]) if ope_result.confidence_interval else None,
                'policy_params': policy.get_params()
            })

        return results

    def compute_pareto_frontier(self, results: List[Dict]) -> List[Dict]:
        """
        Extract Pareto frontier from policy evaluation results

        A point is on the frontier if no other point has both:
        - Higher expected value AND
        - Lower risk
        """
        frontier = []

        for i, point_i in enumerate(results):
            is_dominated = False

            for j, point_j in enumerate(results):
                if i == j:
                    continue

                # Check if point_j dominates point_i
                if (point_j['expected_value'] >= point_i['expected_value'] and
                    point_j['risk'] <= point_i['risk'] and
                    (point_j['expected_value'] > point_i['expected_value'] or
                     point_j['risk'] < point_i['risk'])):
                    is_dominated = True
                    break

            if not is_dominated:
                frontier.append(point_i)

        # Sort by expected value (descending)
        frontier.sort(key=lambda x: x['expected_value'], reverse=True)

        return frontier

    def select_best_policy(self,
                          frontier: List[Dict],
                          risk_aversion: float = 0.5) -> Dict:
        """
        Select best policy from frontier given risk aversion

        Utility = expected_value - risk_aversion * risk
        """
        if not frontier:
            return None

        best_policy = max(frontier, key=lambda x: x['utility'])
        return best_policy
