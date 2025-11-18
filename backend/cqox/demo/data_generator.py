"""
Synthetic Data Generator for Demo Mode

Generates three types of causal inference datasets:
1. RCT (Randomized Controlled Trial) - Perfect randomization
2. Observational Study - Selection bias and confounding
3. Panel Data - Difference-in-Differences design
"""
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from loguru import logger


class DemoDataGenerator:
    """Generate realistic synthetic datasets for causal inference"""

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize data generator

        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

    def generate_rct_data(
        self,
        n_samples: int = 10000,
        treatment_effect: float = 50.0,
        noise_std: float = 100.0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate RCT (Randomized Controlled Trial) data

        Perfect randomization ensures no confounding.
        The true treatment effect is known and constant.

        Args:
            n_samples: Number of samples
            treatment_effect: True average treatment effect (ATE)
            noise_std: Standard deviation of outcome noise

        Returns:
            DataFrame with columns: treatment, age, income, gender, region, outcome, true_ate
        """
        logger.info(f"Generating RCT data: n={n_samples}, ATE={treatment_effect}")

        # Features (independent of treatment in RCT)
        age = np.random.normal(45, 15, n_samples).clip(18, 85)
        income = np.random.lognormal(10.5, 0.6, n_samples).clip(20000, 500000)
        gender = np.random.choice(['M', 'F'], n_samples)
        region = np.random.choice(['North', 'South', 'East', 'West'], n_samples)

        # Perfect randomization (50/50 split)
        treatment = np.random.binomial(1, 0.5, n_samples)

        # Baseline outcome (independent of treatment)
        # Outcome depends on features but not on treatment assignment
        baseline = (
            200 +                           # Intercept
            0.5 * age +                    # Age effect
            0.001 * income +               # Income effect
            30 * (gender == 'M') +         # Gender effect
            np.random.randn(n_samples) * noise_std  # Random noise
        )

        # Treatment effect (constant across all units in basic RCT)
        treatment_effect_vec = treatment_effect * treatment

        # Final outcome
        outcome = baseline + treatment_effect_vec

        # Create dataframe
        df = pd.DataFrame({
            'treatment': treatment,
            'age': age,
            'income': income,
            'gender': gender,
            'region': region,
            'outcome': outcome,
            'true_ate': treatment_effect,  # Known ground truth
            'propensity_score': 0.5,  # Known in RCT
            'baseline_outcome': baseline
        })

        logger.info(f"Generated RCT data: {len(df)} samples, true ATE={treatment_effect}")
        logger.info(f"Observed ATE: {df[df.treatment==1].outcome.mean() - df[df.treatment==0].outcome.mean():.2f}")

        return df

    def generate_observational_data(
        self,
        n_samples: int = 50000,
        true_treatment_effect: float = 40.0,
        selection_strength: float = 2.0,
        noise_std: float = 120.0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate observational study data with selection bias

        Treatment assignment depends on covariates (confounding).
        Requires adjustment methods to estimate true effect.

        Args:
            n_samples: Number of samples
            true_treatment_effect: True average treatment effect
            selection_strength: Strength of selection bias (higher = more bias)
            noise_std: Standard deviation of outcome noise

        Returns:
            DataFrame with confounded treatment assignment
        """
        logger.info(f"Generating observational data: n={n_samples}, ATE={true_treatment_effect}, bias={selection_strength}")

        # Features
        age = np.random.normal(45, 15, n_samples).clip(18, 85)
        income = np.random.lognormal(10.5, 0.6, n_samples).clip(20000, 500000)
        education = np.random.choice(['HS', 'College', 'Graduate'], n_samples, p=[0.3, 0.5, 0.2])
        gender = np.random.choice(['M', 'F'], n_samples)
        region = np.random.choice(['North', 'South', 'East', 'West'], n_samples)
        health_status = np.random.normal(70, 15, n_samples).clip(0, 100)

        # Selection bias: Treatment probability depends on features
        # Wealthier, more educated, healthier people more likely to receive treatment
        propensity_logit = (
            -2.0 +                                          # Base rate
            selection_strength * 0.02 * (age - 45) +       # Older more likely
            selection_strength * 0.00001 * (income - 70000) +  # Wealthier more likely
            selection_strength * 0.5 * (education == 'Graduate') +  # Educated more likely
            selection_strength * 0.02 * (health_status - 70)  # Healthier more likely
        )

        propensity_score = 1 / (1 + np.exp(-propensity_logit))
        treatment = np.random.binomial(1, propensity_score)

        # Outcome (confounded by same features that affect treatment)
        baseline = (
            200 +
            1.5 * age +                               # Age affects outcome
            0.002 * income +                          # Income affects outcome
            50 * (education == 'Graduate') +          # Education affects outcome
            30 * (education == 'College') +
            25 * (gender == 'M') +
            1.0 * health_status +                     # Health affects outcome
            np.random.randn(n_samples) * noise_std
        )

        # Heterogeneous treatment effect (varies by income)
        # Wealthier people benefit more (interaction)
        heterogeneous_effect = true_treatment_effect + 0.0001 * (income - 70000)
        treatment_effect_vec = heterogeneous_effect * treatment

        outcome = baseline + treatment_effect_vec

        # Create dataframe
        df = pd.DataFrame({
            'treatment': treatment,
            'age': age,
            'income': income,
            'education': education,
            'gender': gender,
            'region': region,
            'health_status': health_status,
            'outcome': outcome,
            'propensity_score': propensity_score,
            'true_ate': true_treatment_effect,
            'baseline_outcome': baseline,
            'true_cate': heterogeneous_effect
        })

        # Calculate naive vs true effect
        naive_ate = df[df.treatment==1].outcome.mean() - df[df.treatment==0].outcome.mean()
        logger.info(f"Generated observational data: {len(df)} samples")
        logger.info(f"True ATE: {true_treatment_effect:.2f}, Naive ATE: {naive_ate:.2f} (bias: {naive_ate - true_treatment_effect:.2f})")
        logger.info(f"Propensity score range: [{propensity_score.min():.3f}, {propensity_score.max():.3f}]")

        return df

    def generate_panel_data(
        self,
        n_units: int = 1000,
        n_periods: int = 12,
        treatment_start: int = 6,
        treatment_effect: float = 30.0,
        noise_std: float = 50.0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate panel data for Difference-in-Differences (DiD) analysis

        Panel structure with pre/post treatment periods.
        Allows testing parallel trends assumption.

        Args:
            n_units: Number of individual units (e.g., stores, regions)
            n_periods: Number of time periods
            treatment_start: Period when treatment begins (for treated group)
            treatment_effect: Average treatment effect after treatment
            noise_std: Standard deviation of idiosyncratic noise

        Returns:
            DataFrame with panel structure (unit_id, period, treatment, outcome)
        """
        logger.info(f"Generating panel data: units={n_units}, periods={n_periods}, treatment_start={treatment_start}")

        # Create panel structure
        units = np.repeat(np.arange(n_units), n_periods)
        periods = np.tile(np.arange(n_periods), n_units)

        # Assign 50% of units to treatment group
        treated_units = np.random.choice(n_units, size=n_units // 2, replace=False)
        is_treated_unit = np.isin(units, treated_units)

        # Treatment indicator (1 if treated unit AND post-treatment period)
        post_period = periods >= treatment_start
        treatment = (is_treated_unit & post_period).astype(int)

        # Unit-specific characteristics (time-invariant)
        unit_fixed_effect = np.random.normal(100, 30, n_units)[units]
        unit_trend = np.random.normal(2, 0.5, n_units)[units]

        # Time fixed effects (common to all units)
        time_fixed_effect = np.random.normal(0, 10, n_periods)[periods]

        # Common time trend (parallel trends in pre-period)
        common_trend = 5 * periods

        # Unit-specific trends (violates parallel trends if too strong)
        unit_specific_trend = unit_trend * periods

        # Baseline outcome (before treatment)
        baseline = (
            unit_fixed_effect +           # Unit fixed effect
            time_fixed_effect +           # Time fixed effect
            common_trend +                # Common trend
            0.3 * unit_specific_trend +   # Small unit-specific trend
            np.random.randn(len(units)) * noise_std  # Idiosyncratic noise
        )

        # Treatment effect (grows over time after treatment)
        periods_since_treatment = np.maximum(0, periods - treatment_start)
        dynamic_effect = treatment_effect * (1 - np.exp(-0.5 * periods_since_treatment))
        treatment_effect_vec = dynamic_effect * treatment

        outcome = baseline + treatment_effect_vec

        # Create dataframe
        df = pd.DataFrame({
            'unit_id': units,
            'period': periods,
            'treatment': treatment,
            'treated_unit': is_treated_unit.astype(int),
            'post_period': post_period.astype(int),
            'outcome': outcome,
            'true_ate': treatment_effect,
            'baseline_outcome': baseline
        })

        # Add some unit-level covariates
        unit_size = np.random.choice(['Small', 'Medium', 'Large'], n_units, p=[0.3, 0.5, 0.2])
        unit_region = np.random.choice(['North', 'South', 'East', 'West'], n_units)

        df['unit_size'] = unit_size[units]
        df['unit_region'] = unit_region[units]

        # Calculate DiD estimate
        pre_treated = df[(df.treated_unit==1) & (df.post_period==0)].outcome.mean()
        pre_control = df[(df.treated_unit==0) & (df.post_period==0)].outcome.mean()
        post_treated = df[(df.treated_unit==1) & (df.post_period==1)].outcome.mean()
        post_control = df[(df.treated_unit==0) & (df.post_period==1)].outcome.mean()

        did_estimate = (post_treated - pre_treated) - (post_control - pre_control)

        logger.info(f"Generated panel data: {len(df)} observations")
        logger.info(f"True ATE: {treatment_effect:.2f}, DiD estimate: {did_estimate:.2f}")

        return df

    def generate_dataset(
        self,
        dataset_type: Literal['rct', 'observational', 'panel'],
        **kwargs
    ) -> pd.DataFrame:
        """
        Generate dataset of specified type

        Args:
            dataset_type: Type of dataset ('rct', 'observational', 'panel')
            **kwargs: Parameters specific to dataset type

        Returns:
            Generated DataFrame
        """
        if dataset_type == 'rct':
            return self.generate_rct_data(**kwargs)
        elif dataset_type == 'observational':
            return self.generate_observational_data(**kwargs)
        elif dataset_type == 'panel':
            return self.generate_panel_data(**kwargs)
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

    def save_dataset(
        self,
        df: pd.DataFrame,
        output_path: Path,
        format: Literal['csv', 'parquet'] = 'csv'
    ) -> None:
        """
        Save generated dataset to file

        Args:
            df: DataFrame to save
            output_path: Output file path
            format: File format ('csv' or 'parquet')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'csv':
            df.to_csv(output_path, index=False)
        elif format == 'parquet':
            df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Saved dataset to {output_path} ({format} format)")

    @staticmethod
    def get_dataset_info(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary information about generated dataset

        Args:
            df: Generated DataFrame

        Returns:
            Dictionary with dataset statistics
        """
        info = {
            'n_samples': len(df),
            'n_features': len(df.columns),
            'columns': list(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }

        # Treatment statistics
        if 'treatment' in df.columns:
            info['treatment_stats'] = {
                'n_treated': int(df.treatment.sum()),
                'n_control': int((1 - df.treatment).sum()),
                'treatment_rate': float(df.treatment.mean())
            }

        # Outcome statistics
        if 'outcome' in df.columns:
            treated_outcome = df[df.treatment == 1].outcome.mean() if 'treatment' in df.columns else None
            control_outcome = df[df.treatment == 0].outcome.mean() if 'treatment' in df.columns else None

            info['outcome_stats'] = {
                'mean': float(df.outcome.mean()),
                'std': float(df.outcome.std()),
                'min': float(df.outcome.min()),
                'max': float(df.outcome.max()),
                'treated_mean': float(treated_outcome) if treated_outcome is not None else None,
                'control_mean': float(control_outcome) if control_outcome is not None else None,
                'naive_ate': float(treated_outcome - control_outcome) if treated_outcome is not None else None
            }

        # True effect (if available)
        if 'true_ate' in df.columns:
            info['true_ate'] = float(df.true_ate.iloc[0])

        return info
