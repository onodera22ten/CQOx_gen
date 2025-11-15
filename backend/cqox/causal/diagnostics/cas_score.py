"""
CAS (Causal Assurance Score) - Integrated quality score
"""
import numpy as np
from typing import Dict, Any
from loguru import logger


def calculate_cas_score(
    diagnostic_results: Dict[str, Any],
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Calculate Causal Assurance Score (CAS)

    Integrates multiple diagnostic checks into a single 0-1 score

    Args:
        diagnostic_results: Dict of diagnostic results
        weights: Weights for each diagnostic (optional)

    Returns:
        CAS score and breakdown
    """
    logger.info("Calculating Causal Assurance Score (CAS)")

    if weights is None:
        weights = {
            'balance': 0.20,
            'overlap': 0.20,
            'sensitivity': 0.15,
            'e_value': 0.10,
            'positivity': 0.10,
            'cate_distribution': 0.10,
            'calibration': 0.10,
            'network_spillover': 0.05
        }

    scores = {}

    # Balance score (SMD)
    if 'balance' in diagnostic_results:
        max_smd = diagnostic_results['balance'].get('max_smd', 1.0)
        scores['balance'] = max(0, 1 - max_smd / 0.25)  # Normalize by 0.25 threshold

    # Overlap score
    if 'overlap' in diagnostic_results:
        violation_rate = diagnostic_results['overlap'].get('violation_rate', 1.0)
        scores['overlap'] = max(0, 1 - violation_rate / 0.1)  # Normalize by 10% threshold

    # Sensitivity score (Gamma)
    if 'sensitivity' in diagnostic_results:
        critical_gamma = diagnostic_results['sensitivity'].get('critical_gamma', 1.0)
        scores['sensitivity'] = min(1.0, (critical_gamma - 1.0) / 2.0)  # Gamma > 2 is good

    # E-value score
    if 'e_value' in diagnostic_results:
        e_value = diagnostic_results['e_value'].get('e_value_point_estimate', 1.0)
        scores['e_value'] = min(1.0, (e_value - 1.0) / 2.0)  # E-value > 2 is good

    # Positivity score
    if 'positivity' in diagnostic_results:
        violation_rate = diagnostic_results['positivity'].get('violation_rate', 1.0)
        scores['positivity'] = max(0, 1 - violation_rate / 0.1)

    # CATE distribution score
    if 'cate_distribution' in diagnostic_results:
        negative_share = diagnostic_results['cate_distribution'].get('negative_share', 0.5)
        scores['cate_distribution'] = max(0, 1 - negative_share / 0.2)  # < 20% negative is good

    # Calibration score
    if 'calibration' in diagnostic_results:
        correlation = abs(diagnostic_results['calibration'].get('calibration_correlation', 0))
        scores['calibration'] = correlation

    # Network spillover score
    if 'network_spillover' in diagnostic_results:
        correlation = abs(diagnostic_results['network_spillover'].get('correlation_with_own_treatment', 0))
        scores['network_spillover'] = max(0, 1 - correlation)  # Low correlation is good

    # Calculate weighted CAS
    cas_score = 0.0
    total_weight = 0.0

    for metric, score in scores.items():
        weight = weights.get(metric, 0.0)
        cas_score += score * weight
        total_weight += weight

    if total_weight > 0:
        cas_score = cas_score / total_weight

    # Determine quality level
    if cas_score >= 0.8:
        quality_level = "HIGH"
    elif cas_score >= 0.6:
        quality_level = "MEDIUM"
    else:
        quality_level = "LOW"

    result = {
        'cas_score': float(cas_score),
        'quality_level': quality_level,
        'component_scores': {k: float(v) for k, v in scores.items()},
        'weights_used': weights,
        'recommendation': _get_recommendation(cas_score, scores)
    }

    logger.info(f"CAS Score: {cas_score:.2f} ({quality_level})")

    return result


def _get_recommendation(cas_score: float, component_scores: Dict[str, float]) -> str:
    """Generate recommendation based on CAS score"""

    if cas_score >= 0.8:
        return "High confidence in causal estimates. Safe to proceed with policy deployment."
    elif cas_score >= 0.6:
        return "Moderate confidence. Consider additional validation or run targeted experiments."
    else:
        # Find weakest components
        weak_components = [k for k, v in component_scores.items() if v < 0.5]

        if weak_components:
            return f"Low confidence. Address issues with: {', '.join(weak_components)}. Consider redesigning study or collecting more data."
        else:
            return "Low confidence. Recommend additional diagnostics and validation."
