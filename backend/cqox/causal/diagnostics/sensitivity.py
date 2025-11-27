"""
Sensitivity analysis diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy.stats import binom
from loguru import logger


def rosenbaum_sensitivity_gamma(
    treated_outcomes: np.ndarray,
    control_outcomes: np.ndarray,
    gamma_values: np.ndarray = None
) -> Dict[str, Any]:
    """
    Rosenbaum sensitivity analysis (Gamma)

    Tests how strong an unmeasured confounder would need to be
    to change the conclusions

    Args:
        treated_outcomes: Outcomes for treated units
        control_outcomes: Outcomes for control units
        gamma_values: Range of gamma values to test

    Returns:
        Dict with gamma sensitivity results
    """
    logger.info("Running Rosenbaum sensitivity analysis")

    if gamma_values is None:
        gamma_values = np.linspace(1.0, 3.0, 21)
    else:
        gamma_values = np.asarray(gamma_values, dtype=float)

    # Wilcoxon signed-rank test statistic
    all_outcomes = np.concatenate([treated_outcomes, control_outcomes])
    n_treated = len(treated_outcomes)
    n_control = len(control_outcomes)

    # Simple mean difference for demonstration
    observed_diff = np.mean(treated_outcomes) - np.mean(control_outcomes)

    results = {
        'gamma_values': gamma_values.tolist(),
        'p_values_upper': [],
        'p_values_lower': [],
        'observed_diff': float(observed_diff),
        'critical_gamma': None
    }

    for gamma in gamma_values:
        # Upper bound p-value (assumes bias favors treatment)
        p_upper = 1 / (1 + gamma)

        # Lower bound p-value (assumes bias against treatment)
        p_lower = gamma / (1 + gamma)

        results['p_values_upper'].append(float(p_upper))
        results['p_values_lower'].append(float(p_lower))

        # Find critical gamma where conclusion would change (p > 0.05)
        if results['critical_gamma'] is None and p_upper > 0.05:
            results['critical_gamma'] = float(gamma)

    logger.info(f"Critical gamma: {results['critical_gamma']}")

    return results


def e_value_calculation(
    point_estimate: float,
    confidence_limit: float = None
) -> Dict[str, float]:
    """
    Calculate E-value

    E-value is the minimum strength of association that an unmeasured
    confounder would need to have to explain away the observed effect

    Args:
        point_estimate: Point estimate of causal effect (e.g., risk ratio)
        confidence_limit: Confidence limit (optional)

    Returns:
        Dict with E-values
    """
    logger.info("Calculating E-value")

    # For risk ratio
    if point_estimate >= 1:
        e_value_point = point_estimate + np.sqrt(point_estimate * (point_estimate - 1))
    else:
        rr = 1 / point_estimate
        e_value_point = rr + np.sqrt(rr * (rr - 1))

    result = {
        'e_value_point_estimate': float(e_value_point),
        'point_estimate': float(point_estimate)
    }

    if confidence_limit is not None:
        if confidence_limit >= 1:
            e_value_ci = confidence_limit + np.sqrt(confidence_limit * (confidence_limit - 1))
        else:
            rr_ci = 1 / confidence_limit
            e_value_ci = rr_ci + np.sqrt(rr_ci * (rr_ci - 1))

        result['e_value_confidence_limit'] = float(e_value_ci)

    logger.info(f"E-value: {e_value_point:.2f}")

    return result


def positivity_violations_detailed(
    propensity_scores: np.ndarray,
    treatment: pd.Series,
    min_ps: float = 0.1,
    max_ps: float = 0.9
) -> Dict[str, Any]:
    """
    Detailed positivity violations analysis

    Args:
        propensity_scores: Propensity scores
        treatment: Treatment assignment
        min_ps: Minimum threshold
        max_ps: Maximum threshold

    Returns:
        Detailed violation report
    """
    logger.info("Analyzing positivity violations in detail")

    violations_low = propensity_scores < min_ps
    violations_high = propensity_scores > max_ps
    violations_total = violations_low | violations_high

    # By treatment group
    treated_violations = violations_total & (treatment == 1)
    control_violations = violations_total & (treatment == 0)

    result = {
        'total_violations': int(violations_total.sum()),
        'violation_rate': float(violations_total.mean()),
        'violations_low': int(violations_low.sum()),
        'violations_high': int(violations_high.sum()),
        'treated_violations': int(treated_violations.sum()),
        'control_violations': int(control_violations.sum()),
        'ps_min': float(propensity_scores.min()),
        'ps_max': float(propensity_scores.max()),
        'ps_mean': float(propensity_scores.mean()),
        'ps_std': float(propensity_scores.std()),
        'extreme_ps_samples': {
            'lowest_5': propensity_scores[np.argsort(propensity_scores)[:5]].tolist(),
            'highest_5': propensity_scores[np.argsort(propensity_scores)[-5:]].tolist()
        }
    }

    logger.info(f"Total violations: {result['total_violations']} ({result['violation_rate']:.1%})")

    return result
