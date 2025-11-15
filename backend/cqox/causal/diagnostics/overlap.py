"""
Overlap/Positivity diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from loguru import logger


def estimate_propensity_scores(
    X: pd.DataFrame,
    treatment: pd.Series
) -> np.ndarray:
    """
    Estimate propensity scores

    Args:
        X: Covariates
        treatment: Treatment assignment

    Returns:
        Propensity scores
    """
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X, treatment)
    ps = model.predict_proba(X)[:, 1]
    return ps


def overlap_test(
    X: pd.DataFrame,
    treatment: pd.Series,
    min_ps: float = 0.1,
    max_ps: float = 0.9
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test overlap/positivity assumption

    Args:
        X: Covariates
        treatment: Treatment assignment
        min_ps: Minimum acceptable propensity score
        max_ps: Maximum acceptable propensity score

    Returns:
        (passed, report)
    """
    logger.info("Running overlap test")

    ps = estimate_propensity_scores(X, treatment)

    # Check for extreme propensity scores
    violations = ((ps < min_ps) | (ps > max_ps)).sum()
    violation_rate = violations / len(ps)

    passed = violation_rate < 0.05  # Allow up to 5% violations

    report = {
        'passed': passed,
        'propensity_scores': ps.tolist(),
        'min_ps': float(ps.min()),
        'max_ps': float(ps.max()),
        'mean_ps': float(ps.mean()),
        'violations': int(violations),
        'violation_rate': float(violation_rate),
        'threshold_min': min_ps,
        'threshold_max': max_ps
    }

    logger.info(f"Overlap test: {'PASSED' if passed else 'FAILED'} "
                f"(violation rate: {violation_rate:.2%})")

    return passed, report


def propensity_density_plot_data(
    X: pd.DataFrame,
    treatment: pd.Series
) -> Dict[str, Any]:
    """
    Generate data for propensity density plot

    Args:
        X: Covariates
        treatment: Treatment assignment

    Returns:
        Dict with plotting data
    """
    ps = estimate_propensity_scores(X, treatment)

    return {
        'propensity_scores': ps.tolist(),
        'treatment': treatment.tolist(),
        'ps_treated': ps[treatment == 1].tolist(),
        'ps_control': ps[treatment == 0].tolist()
    }
