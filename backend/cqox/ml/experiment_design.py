"""
Experiment Design and Sample Size Calculation
A/B testing, power analysis, and sequential testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
from scipy.optimize import brentq
import logging

logger = logging.getLogger(__name__)


@dataclass
class SampleSizeResult:
    """Sample size calculation result"""
    required_sample_size_per_arm: int
    total_sample_size: int
    power: float
    alpha: float
    effect_size: float
    baseline_mean: Optional[float] = None
    baseline_std: Optional[float] = None
    baseline_proportion: Optional[float] = None


@dataclass
class PowerAnalysisResult:
    """Power analysis result"""
    power: float
    sample_size_per_arm: int
    alpha: float
    effect_size: float
    test_type: str


class SampleSizeCalculator:
    """Calculate required sample size for experiments"""

    @staticmethod
    def continuous_outcome(baseline_mean: float,
                          baseline_std: float,
                          minimum_detectable_effect: float,
                          alpha: float = 0.05,
                          power: float = 0.80,
                          two_sided: bool = True,
                          allocation_ratio: float = 1.0) -> SampleSizeResult:
        """
        Calculate sample size for continuous outcome (t-test)

        Args:
            baseline_mean: Mean of outcome in control group
            baseline_std: Standard deviation of outcome
            minimum_detectable_effect: Minimum effect to detect (absolute)
            alpha: Significance level (Type I error rate)
            power: Statistical power (1 - Type II error rate)
            two_sided: Two-sided test (default) or one-sided
            allocation_ratio: Ratio of treatment to control (default 1:1)

        Returns:
            SampleSizeResult with required sample sizes
        """
        # Effect size (Cohen's d)
        effect_size = minimum_detectable_effect / baseline_std

        # Z-scores for alpha and power
        if two_sided:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)

        z_beta = stats.norm.ppf(power)

        # Sample size per arm (assuming equal allocation)
        # n = 2 * (z_alpha + z_beta)^2 / d^2
        # Adjusted for unequal allocation
        n_control = (2 * (z_alpha + z_beta) ** 2) / (effect_size ** 2)
        n_treatment = n_control * allocation_ratio

        # Round up
        n_control = int(np.ceil(n_control))
        n_treatment = int(np.ceil(n_treatment))

        total_n = n_control + n_treatment

        return SampleSizeResult(
            required_sample_size_per_arm=n_control,
            total_sample_size=total_n,
            power=power,
            alpha=alpha,
            effect_size=effect_size,
            baseline_mean=baseline_mean,
            baseline_std=baseline_std
        )

    @staticmethod
    def binary_outcome(baseline_proportion: float,
                      minimum_detectable_effect: float,
                      alpha: float = 0.05,
                      power: float = 0.80,
                      two_sided: bool = True,
                      allocation_ratio: float = 1.0) -> SampleSizeResult:
        """
        Calculate sample size for binary outcome (proportion test)

        Args:
            baseline_proportion: Proportion in control group (e.g., conversion rate)
            minimum_detectable_effect: Minimum absolute difference in proportions
            alpha: Significance level
            power: Statistical power
            two_sided: Two-sided test
            allocation_ratio: Treatment to control ratio

        Returns:
            SampleSizeResult
        """
        p1 = baseline_proportion
        p2 = baseline_proportion + minimum_detectable_effect

        # Pooled proportion (under null hypothesis)
        p_pooled = (p1 + allocation_ratio * p2) / (1 + allocation_ratio)

        # Z-scores
        if two_sided:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)

        z_beta = stats.norm.ppf(power)

        # Sample size formula for proportions
        # n1 = (z_alpha * sqrt(p_pooled*(1-p_pooled)*(1+1/r)) +
        #       z_beta * sqrt(p1*(1-p1) + p2*(1-p2)/r))^2 / (p2 - p1)^2

        numerator = (
            z_alpha * np.sqrt(p_pooled * (1 - p_pooled) * (1 + 1/allocation_ratio)) +
            z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / allocation_ratio)
        ) ** 2

        denominator = (p2 - p1) ** 2

        n_control = numerator / denominator
        n_treatment = n_control * allocation_ratio

        # Round up
        n_control = int(np.ceil(n_control))
        n_treatment = int(np.ceil(n_treatment))

        total_n = n_control + n_treatment

        # Effect size (Cohen's h for proportions)
        h = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))

        return SampleSizeResult(
            required_sample_size_per_arm=n_control,
            total_sample_size=total_n,
            power=power,
            alpha=alpha,
            effect_size=h,
            baseline_proportion=baseline_proportion
        )

    @staticmethod
    def multi_arm(n_arms: int,
                 baseline_mean: float,
                 baseline_std: float,
                 minimum_detectable_effect: float,
                 alpha: float = 0.05,
                 power: float = 0.80,
                 correction: str = 'bonferroni') -> SampleSizeResult:
        """
        Calculate sample size for multi-arm experiments

        Args:
            n_arms: Number of treatment arms (including control)
            baseline_mean: Mean in control
            baseline_std: Standard deviation
            minimum_detectable_effect: Minimum effect to detect
            alpha: Significance level
            power: Statistical power
            correction: Multiple testing correction ('bonferroni', 'holm', 'none')

        Returns:
            SampleSizeResult
        """
        # Adjust alpha for multiple comparisons
        n_comparisons = n_arms - 1  # comparing each treatment to control

        if correction == 'bonferroni':
            adjusted_alpha = alpha / n_comparisons
        elif correction == 'holm':
            # Conservative approximation
            adjusted_alpha = alpha / n_comparisons
        else:
            adjusted_alpha = alpha

        # Calculate sample size using adjusted alpha
        result = SampleSizeCalculator.continuous_outcome(
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            minimum_detectable_effect=minimum_detectable_effect,
            alpha=adjusted_alpha,
            power=power,
            two_sided=True,
            allocation_ratio=1.0
        )

        # Multiply by number of arms
        result.total_sample_size = result.required_sample_size_per_arm * n_arms

        return result


class PowerAnalyzer:
    """Analyze statistical power of experiments"""

    @staticmethod
    def compute_power(sample_size_per_arm: int,
                     effect_size: float,
                     alpha: float = 0.05,
                     two_sided: bool = True,
                     test_type: str = 'continuous') -> PowerAnalysisResult:
        """
        Compute statistical power given sample size and effect size

        Args:
            sample_size_per_arm: Sample size per arm
            effect_size: Effect size (Cohen's d for continuous, h for proportions)
            alpha: Significance level
            two_sided: Two-sided test
            test_type: 'continuous' or 'binary'

        Returns:
            PowerAnalysisResult
        """
        # Z-score for alpha
        if two_sided:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)

        # Non-centrality parameter
        ncp = effect_size * np.sqrt(sample_size_per_arm / 2)

        # Power = P(Z > z_alpha - ncp) where Z ~ N(0,1)
        power = 1 - stats.norm.cdf(z_alpha - ncp)

        return PowerAnalysisResult(
            power=power,
            sample_size_per_arm=sample_size_per_arm,
            alpha=alpha,
            effect_size=effect_size,
            test_type=test_type
        )

    @staticmethod
    def power_curve(effect_sizes: List[float],
                   sample_size_per_arm: int,
                   alpha: float = 0.05) -> List[Tuple[float, float]]:
        """
        Generate power curve for different effect sizes

        Returns:
            List of (effect_size, power) tuples
        """
        results = []
        for effect_size in effect_sizes:
            result = PowerAnalyzer.compute_power(
                sample_size_per_arm=sample_size_per_arm,
                effect_size=effect_size,
                alpha=alpha
            )
            results.append((effect_size, result.power))

        return results


class SequentialTesting:
    """Sequential testing with early stopping rules"""

    @staticmethod
    def o_brien_fleming_boundary(alpha: float,
                                 n_looks: int,
                                 information_fractions: Optional[List[float]] = None) -> List[float]:
        """
        O'Brien-Fleming spending function boundary

        Args:
            alpha: Overall Type I error rate
            n_looks: Number of interim analyses
            information_fractions: Fraction of information at each look (default: equally spaced)

        Returns:
            List of alpha levels for each look
        """
        if information_fractions is None:
            information_fractions = [(i + 1) / n_looks for i in range(n_looks)]

        # O'Brien-Fleming: spend alpha conservatively early, liberally late
        boundaries = []
        for t in information_fractions:
            if t > 0:
                # Spending function: 2 * (1 - Φ(z_α/2 / √t))
                z_alpha = stats.norm.ppf(1 - alpha / 2)
                boundary_z = z_alpha / np.sqrt(t)
                boundary_alpha = 2 * (1 - stats.norm.cdf(boundary_z))
                boundaries.append(boundary_alpha)
            else:
                boundaries.append(0.0)

        return boundaries

    @staticmethod
    def pocock_boundary(alpha: float,
                       n_looks: int) -> List[float]:
        """
        Pocock spending function (constant boundary)

        Args:
            alpha: Overall Type I error rate
            n_looks: Number of interim analyses

        Returns:
            List of alpha levels for each look (constant)
        """
        # Pocock uses constant critical value at each look
        # This requires solving for the constant boundary that controls overall alpha
        # Approximation: alpha_i ≈ alpha / n_looks (conservative)

        boundary_alpha = alpha / n_looks
        boundaries = [boundary_alpha] * n_looks

        return boundaries

    @staticmethod
    def should_stop(current_p_value: float,
                   current_look: int,
                   alpha_spending: List[float]) -> Tuple[bool, str]:
        """
        Determine if experiment should stop early

        Args:
            current_p_value: Current p-value from test
            current_look: Current interim analysis number (1-indexed)
            alpha_spending: Alpha spending function values

        Returns:
            (should_stop, reason)
        """
        if current_look > len(alpha_spending):
            raise ValueError(f"Current look {current_look} exceeds number of planned looks")

        boundary = alpha_spending[current_look - 1]

        if current_p_value < boundary:
            return (True, f"Significant result (p={current_p_value:.4f} < α={boundary:.4f})")
        else:
            return (False, f"Continue (p={current_p_value:.4f} >= α={boundary:.4f})")


class ExperimentAnalyzer:
    """Analyze experiment results"""

    @staticmethod
    def two_sample_t_test(treatment: np.ndarray,
                         control: np.ndarray,
                         alpha: float = 0.05,
                         two_sided: bool = True) -> Dict[str, float]:
        """
        Perform two-sample t-test

        Args:
            treatment: Treatment arm outcomes
            control: Control arm outcomes
            alpha: Significance level
            two_sided: Two-sided test

        Returns:
            Dictionary with test results
        """
        t_stat, p_value = stats.ttest_ind(treatment, control)

        if two_sided:
            significant = p_value < alpha
        else:
            significant = (t_stat > 0) and (p_value / 2 < alpha)

        # Confidence interval for difference in means
        mean_diff = np.mean(treatment) - np.mean(control)
        se = np.sqrt(np.var(treatment) / len(treatment) + np.var(control) / len(control))

        if two_sided:
            z = stats.norm.ppf(1 - alpha / 2)
        else:
            z = stats.norm.ppf(1 - alpha)

        ci_lower = mean_diff - z * se
        ci_upper = mean_diff + z * se

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(treatment) + np.var(control)) / 2)
        effect_size = mean_diff / pooled_std if pooled_std > 0 else 0

        return {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': bool(significant),
            'mean_treatment': float(np.mean(treatment)),
            'mean_control': float(np.mean(control)),
            'mean_diff': float(mean_diff),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'effect_size': float(effect_size),
            'std_treatment': float(np.std(treatment)),
            'std_control': float(np.std(control)),
            'n_treatment': int(len(treatment)),
            'n_control': int(len(control))
        }

    @staticmethod
    def proportion_test(successes_treatment: int,
                       n_treatment: int,
                       successes_control: int,
                       n_control: int,
                       alpha: float = 0.05,
                       two_sided: bool = True) -> Dict[str, float]:
        """
        Test for difference in proportions (z-test)

        Args:
            successes_treatment: Number of successes in treatment
            n_treatment: Total in treatment arm
            successes_control: Number of successes in control
            n_control: Total in control arm
            alpha: Significance level
            two_sided: Two-sided test

        Returns:
            Dictionary with test results
        """
        p1 = successes_treatment / n_treatment
        p2 = successes_control / n_control

        # Pooled proportion
        p_pooled = (successes_treatment + successes_control) / (n_treatment + n_control)

        # Standard error under null hypothesis
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_treatment + 1/n_control))

        # Z-statistic
        z_stat = (p1 - p2) / se if se > 0 else 0

        # P-value
        if two_sided:
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            p_value = 1 - stats.norm.cdf(z_stat)

        significant = p_value < alpha

        # Confidence interval for difference
        se_diff = np.sqrt(p1 * (1 - p1) / n_treatment + p2 * (1 - p2) / n_control)

        if two_sided:
            z = stats.norm.ppf(1 - alpha / 2)
        else:
            z = stats.norm.ppf(1 - alpha)

        diff = p1 - p2
        ci_lower = diff - z * se_diff
        ci_upper = diff + z * se_diff

        # Effect size (Cohen's h)
        h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))

        return {
            'z_statistic': float(z_stat),
            'p_value': float(p_value),
            'significant': bool(significant),
            'proportion_treatment': float(p1),
            'proportion_control': float(p2),
            'proportion_diff': float(diff),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'effect_size': float(h),
            'n_treatment': int(n_treatment),
            'n_control': int(n_control)
        }

    @staticmethod
    def estimate_runtime(required_sample_size: int,
                        current_traffic_per_day: int,
                        allocation_to_experiment: float = 1.0) -> float:
        """
        Estimate experiment runtime in days

        Args:
            required_sample_size: Total required sample size
            current_traffic_per_day: Average daily traffic
            allocation_to_experiment: Fraction of traffic allocated to experiment

        Returns:
            Estimated runtime in days
        """
        effective_daily_rate = current_traffic_per_day * allocation_to_experiment

        if effective_daily_rate <= 0:
            return float('inf')

        runtime_days = required_sample_size / effective_daily_rate

        return float(runtime_days)
