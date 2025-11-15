"""
Covariate balance diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from loguru import logger


def standardized_mean_difference(
    X: pd.DataFrame,
    treatment: pd.Series
) -> pd.Series:
    """
    Calculate standardized mean difference (SMD) for each covariate

    Args:
        X: Covariates
        treatment: Treatment assignment

    Returns:
        Series of SMD values for each covariate
    """
    mask_treat = treatment == 1
    mask_control = treatment == 0

    X_treat = X[mask_treat]
    X_control = X[mask_control]

    # Calculate SMD for each column
    smd = {}
    for col in X.columns:
        if X[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            mean_treat = X_treat[col].mean()
            mean_control = X_control[col].mean()

            std_treat = X_treat[col].std()
            std_control = X_control[col].std()

            pooled_std = np.sqrt((std_treat**2 + std_control**2) / 2)

            if pooled_std > 0:
                smd[col] = (mean_treat - mean_control) / pooled_std
            else:
                smd[col] = 0.0

    return pd.Series(smd)


def covariate_balance_test(
    X: pd.DataFrame,
    treatment: pd.Series,
    threshold: float = 0.1
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test covariate balance

    Args:
        X: Covariates
        treatment: Treatment assignment
        threshold: SMD threshold for balance (typically 0.1)

    Returns:
        (passed, report)
    """
    logger.info("Running covariate balance test")

    smd = standardized_mean_difference(X, treatment)

    # Check if all SMDs are below threshold
    passed = (smd.abs() < threshold).all()

    report = {
        'passed': passed,
        'smd': smd.to_dict(),
        'max_smd': float(smd.abs().max()),
        'mean_smd': float(smd.abs().mean()),
        'threshold': threshold,
        'imbalanced_covariates': list(smd[smd.abs() >= threshold].index)
    }

    logger.info(f"Balance test: {'PASSED' if passed else 'FAILED'} "
                f"(max SMD: {report['max_smd']:.3f})")

    return passed, report


def love_plot_data(
    X: pd.DataFrame,
    treatment: pd.Series
) -> Dict[str, Any]:
    """
    Generate data for Love plot (SMD plot)

    Args:
        X: Covariates
        treatment: Treatment assignment

    Returns:
        Dict with plotting data
    """
    smd = standardized_mean_difference(X, treatment)

    return {
        'covariates': list(smd.index),
        'smd': list(smd.values),
        'abs_smd': list(smd.abs().values)
    }
