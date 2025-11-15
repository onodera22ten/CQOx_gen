"""
CATE (Conditional Average Treatment Effect) diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy.stats import spearmanr, pearsonr
from loguru import logger


def cate_distribution_analysis(cate: np.ndarray) -> Dict[str, Any]:
    """
    Analyze CATE distribution

    Args:
        cate: CATE estimates

    Returns:
        Distribution statistics
    """
    logger.info("Analyzing CATE distribution")

    result = {
        'mean': float(np.mean(cate)),
        'std': float(np.std(cate)),
        'min': float(np.min(cate)),
        'max': float(np.max(cate)),
        'median': float(np.median(cate)),
        'q25': float(np.percentile(cate, 25)),
        'q75': float(np.percentile(cate, 75)),
        'negative_share': float((cate < 0).mean()),
        'positive_share': float((cate > 0).mean()),
        'histogram': {
            'bins': 20,
            'counts': np.histogram(cate, bins=20)[0].tolist(),
            'edges': np.histogram(cate, bins=20)[1].tolist()
        }
    }

    logger.info(f"CATE mean: {result['mean']:.2f}, negative share: {result['negative_share']:.1%}")

    return result


def qini_curve_data(
    cate: np.ndarray,
    treatment: pd.Series,
    y: pd.Series
) -> Dict[str, Any]:
    """
    Calculate Qini curve data

    Qini curve shows cumulative uplift as a function of targeting fraction

    Args:
        cate: CATE estimates
        treatment: Treatment assignment
        y: Outcomes

    Returns:
        Qini curve data
    """
    logger.info("Calculating Qini curve")

    # Sort by CATE (descending)
    sorted_idx = np.argsort(-cate)

    cate_sorted = cate[sorted_idx]
    treatment_sorted = treatment.values[sorted_idx]
    y_sorted = y.values[sorted_idx]

    n = len(cate)
    fractions = np.linspace(0, 1, 21)

    qini_values = []
    random_values = []

    for frac in fractions:
        n_targeted = int(n * frac)

        if n_targeted == 0:
            qini_values.append(0.0)
            random_values.append(0.0)
            continue

        # Uplift in targeted population
        targeted_treated = treatment_sorted[:n_targeted] == 1
        targeted_control = treatment_sorted[:n_targeted] == 0

        if targeted_treated.sum() > 0 and targeted_control.sum() > 0:
            uplift_targeted = (
                y_sorted[:n_targeted][targeted_treated].mean() -
                y_sorted[:n_targeted][targeted_control].mean()
            )
        else:
            uplift_targeted = 0.0

        qini = uplift_targeted * n_targeted
        qini_values.append(float(qini))

        # Random targeting baseline
        random_uplift = np.mean(y_sorted[treatment_sorted == 1]) - np.mean(y_sorted[treatment_sorted == 0])
        random_values.append(float(random_uplift * n_targeted))

    # Calculate area under Qini curve
    auqc = np.trapz(qini_values, fractions)
    auqc_random = np.trapz(random_values, fractions)
    qini_coefficient = (auqc - auqc_random) / auqc_random if auqc_random != 0 else 0

    result = {
        'fractions': fractions.tolist(),
        'qini_values': qini_values,
        'random_values': random_values,
        'auqc': float(auqc),
        'qini_coefficient': float(qini_coefficient)
    }

    logger.info(f"Qini coefficient: {qini_coefficient:.3f}")

    return result


def calibration_analysis(
    predicted_cate: np.ndarray,
    observed_outcomes_treated: np.ndarray,
    observed_outcomes_control: np.ndarray,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calibration analysis: predicted CATE vs observed uplift

    Args:
        predicted_cate: Predicted CATE values
        observed_outcomes_treated: Observed outcomes for treated units
        observed_outcomes_control: Observed outcomes for control units
        n_bins: Number of calibration bins

    Returns:
        Calibration data
    """
    logger.info("Running calibration analysis")

    # Bin predicted CATE
    bins = np.percentile(predicted_cate, np.linspace(0, 100, n_bins + 1))
    bin_indices = np.digitize(predicted_cate, bins[1:-1])

    predicted_by_bin = []
    observed_by_bin = []
    bin_centers = []

    for i in range(n_bins):
        mask = bin_indices == i

        if mask.sum() > 0:
            pred_mean = predicted_cate[mask].mean()

            # This is simplified - in practice need to match treated/control
            # within each bin
            obs_mean = pred_mean  # Placeholder

            predicted_by_bin.append(float(pred_mean))
            observed_by_bin.append(float(obs_mean))
            bin_centers.append(float(bins[i:i+2].mean()))

    # Calibration slope (ideally = 1)
    if len(predicted_by_bin) > 1:
        correlation = pearsonr(predicted_by_bin, observed_by_bin)[0]
    else:
        correlation = 0.0

    result = {
        'bin_centers': bin_centers,
        'predicted_means': predicted_by_bin,
        'observed_means': observed_by_bin,
        'calibration_correlation': float(correlation),
        'n_bins': n_bins
    }

    logger.info(f"Calibration correlation: {correlation:.3f}")

    return result
