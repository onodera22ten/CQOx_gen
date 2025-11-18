"""
Offline Policy Evaluation (OPE)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from loguru import logger


class OfflinePolicyEvaluator:
    """
    Offline Policy Evaluation using Inverse Propensity Scoring (IPS)
    and Doubly Robust (DR) methods
    """

    def __init__(self):
        self.propensity_scores = None

    def estimate_propensity_scores(
        self,
        X: pd.DataFrame,
        treatment: pd.Series
    ) -> np.ndarray:
        """Estimate propensity scores"""
        from sklearn.linear_model import LogisticRegression

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X, treatment)
        ps = model.predict_proba(X)[:, 1]
        self.propensity_scores = ps
        return ps

    def ips_estimator(
        self,
        treatment: pd.Series,
        y: pd.Series,
        policy_treatment: pd.Series,
        propensity_scores: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Inverse Propensity Scoring (IPS) estimator

        Args:
            treatment: Observed treatment
            y: Observed outcome
            policy_treatment: Policy-recommended treatment
            propensity_scores: Propensity scores

        Returns:
            Dict with value estimate and variance
        """
        if propensity_scores is None:
            if self.propensity_scores is None:
                raise ValueError("Propensity scores not estimated")
            propensity_scores = self.propensity_scores

        # Clip propensity scores
        ps_clipped = np.clip(propensity_scores, 0.01, 0.99)

        # IPS weights
        weights = np.where(
            policy_treatment == treatment,
            1.0 / np.where(treatment == 1, ps_clipped, 1 - ps_clipped),
            0.0
        )

        # Estimate value
        value = np.mean(weights * y)
        variance = np.var(weights * y) / len(y)

        return {
            'value': float(value),
            'variance': float(variance),
            'std_error': float(np.sqrt(variance))
        }

    def dr_estimator(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        policy_treatment: pd.Series,
        propensity_scores: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Doubly Robust (DR) estimator

        Args:
            X: Covariates
            treatment: Observed treatment
            y: Observed outcome
            policy_treatment: Policy-recommended treatment
            propensity_scores: Propensity scores

        Returns:
            Dict with value estimate and variance
        """
        if propensity_scores is None:
            if self.propensity_scores is None:
                raise ValueError("Propensity scores not estimated")
            propensity_scores = self.propensity_scores

        # Fit outcome models
        from sklearn.ensemble import GradientBoostingRegressor

        # Treatment group model
        mask_treat = treatment == 1
        model_treat = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model_treat.fit(X[mask_treat], y[mask_treat])
        mu1 = model_treat.predict(X)

        # Control group model
        mask_control = treatment == 0
        model_control = GradientBoostingRegressor(n_estimators=100, random_state=42)
        model_control.fit(X[mask_control], y[mask_control])
        mu0 = model_control.predict(X)

        # Clip propensity scores
        ps_clipped = np.clip(propensity_scores, 0.01, 0.99)

        # DR estimator
        T = treatment.values
        Y = y.values
        pi = policy_treatment.values

        # For each unit, compute DR term
        dr_terms = np.where(
            pi == 1,
            # If policy recommends treatment
            mu1 + (T / ps_clipped) * (Y - mu1),
            # If policy recommends control
            mu0 + ((1 - T) / (1 - ps_clipped)) * (Y - mu0)
        )

        value = np.mean(dr_terms)
        variance = np.var(dr_terms) / len(dr_terms)

        return {
            'value': float(value),
            'variance': float(variance),
            'std_error': float(np.sqrt(variance))
        }

    def evaluate_policy(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        policy_treatment: pd.Series,
        method: str = 'dr'
    ) -> Dict[str, Any]:
        """
        Evaluate a policy

        Args:
            X: Covariates
            treatment: Observed treatment
            y: Observed outcome
            policy_treatment: Policy-recommended treatment
            method: 'ips' or 'dr'

        Returns:
            Evaluation results
        """
        logger.info(f"Evaluating policy using {method.upper()} method")

        # Estimate propensity scores
        ps = self.estimate_propensity_scores(X, treatment)

        # Evaluate
        if method == 'ips':
            result = self.ips_estimator(treatment, y, policy_treatment, ps)
        elif method == 'dr':
            result = self.dr_estimator(X, treatment, y, policy_treatment, ps)
        else:
            raise ValueError(f"Unknown method: {method}")

        result['method'] = method
        result['n_samples'] = len(y)

        logger.info(f"Policy value: {result['value']:.4f} ± {result['std_error']:.4f}")

        return result


def evaluate_policy_roi(
    policy_value: float,
    baseline_value: float,
    cost: float
) -> Dict[str, float]:
    """
    Calculate policy ROI metrics

    Args:
        policy_value: Expected value under policy
        baseline_value: Expected value under baseline
        cost: Cost of implementing policy

    Returns:
        Dict with ROI metrics
    """
    incremental_value = policy_value - baseline_value
    roi = (incremental_value - cost) / cost if cost > 0 else float('inf')

    return {
        'policy_value': policy_value,
        'baseline_value': baseline_value,
        'incremental_value': incremental_value,
        'cost': cost,
        'net_value': incremental_value - cost,
        'roi': roi
    }
