"""
DiD: Difference-in-Differences Estimator

Estimates causal effects using time-series variation with treatment/control groups.
Removes time-invariant confounders via double differencing.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.base import clone
from loguru import logger
from typing import Optional, Union

from .base import BaseEstimator


class DIDEstimator(BaseEstimator):
    """
    Difference-in-Differences (DiD) Estimator

    Estimates treatment effects by comparing the change in outcomes over time
    between treatment and control groups:

    τ̂_DiD = (Ȳ_treat,post - Ȳ_treat,pre) - (Ȳ_control,post - Ȳ_control,pre)

    Assumptions:
    1. Parallel Trends: In absence of treatment, treatment and control groups
       would have followed parallel trends
    2. No anticipation: Treatment group doesn't anticipate treatment before it occurs
    3. Stable composition: Same units in pre/post periods

    Advantages:
    - Removes time-invariant confounders (e.g., region fixed effects)
    - Intuitive interpretation
    - Robust to selection on observables

    Reference:
    - Card & Krueger (1994). "Minimum Wages and Employment"
    - Angrist & Pischke (2009). "Mostly Harmless Econometrics"
    """

    def __init__(
        self,
        model: Optional[object] = None,
        time_col: str = 'time_period',
        unit_col: Optional[str] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        model : sklearn-compatible regressor
            Model for regression-based DiD (default: OLS)
        time_col : str
            Name of time period column (0=pre, 1=post)
        unit_col : str, optional
            Name of unit identifier column (for panel data)
        """
        super().__init__(**kwargs)
        self.model = model or LinearRegression()
        self.time_col = time_col
        self.unit_col = unit_col

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """
        Fit DiD estimator

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix. MUST contain time_col (0=pre, 1=post)
        treatment : pd.Series
            Binary treatment indicator (0=control, 1=treated)
        y : pd.Series
            Outcome variable

        Returns
        -------
        self
        """
        logger.info(f"Fitting DiD estimator with {len(X)} observations")

        # Validate time column exists
        if self.time_col not in X.columns:
            raise ValueError(f"Time column '{self.time_col}' not found in X")

        # Extract time period
        time_period = X[self.time_col].values
        unique_periods = np.unique(time_period)

        if len(unique_periods) != 2:
            raise ValueError(f"DiD requires exactly 2 time periods. Found: {unique_periods}")

        if not set(unique_periods).issubset({0, 1}):
            logger.warning(f"Time periods {unique_periods} will be recoded to [0, 1]")
            time_period = (time_period == unique_periods[1]).astype(int)

        # Validate treatment is binary
        unique_treatments = treatment.unique()
        if len(unique_treatments) != 2 or not set(unique_treatments).issubset({0, 1}):
            raise ValueError("Treatment must be binary (0 or 1)")

        # Store data
        self.X_train = X.copy()
        self.treatment_train = treatment.copy()
        self.y_train = y.copy()
        self.time_period = time_period

        # Compute means for each group-period
        mask_treat_pre = (treatment == 1) & (time_period == 0)
        mask_treat_post = (treatment == 1) & (time_period == 1)
        mask_control_pre = (treatment == 0) & (time_period == 0)
        mask_control_post = (treatment == 0) & (time_period == 1)

        self.mean_treat_pre = y[mask_treat_pre].mean()
        self.mean_treat_post = y[mask_treat_post].mean()
        self.mean_control_pre = y[mask_control_pre].mean()
        self.mean_control_post = y[mask_control_post].mean()

        # Log sample sizes
        logger.info(f"Sample sizes: "
                   f"Treat Pre={mask_treat_pre.sum()}, "
                   f"Treat Post={mask_treat_post.sum()}, "
                   f"Control Pre={mask_control_pre.sum()}, "
                   f"Control Post={mask_control_post.sum()}")

        # Check parallel trends (pre-treatment)
        if mask_treat_pre.sum() > 0 and mask_control_pre.sum() > 0:
            diff_pre = self.mean_treat_pre - self.mean_control_pre
            logger.info(f"Pre-treatment difference: {diff_pre:.4f}")

        # Fit regression-based DiD for covariate adjustment
        self._fit_regression_did(X, treatment, y, time_period)

        self.is_fitted = True
        logger.info("DiD estimator fitted successfully")

        return self

    def _fit_regression_did(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        time_period: np.ndarray
    ):
        """
        Fit regression-based DiD:
        Y = β0 + β1·Treat + β2·Post + β3·(Treat × Post) + X'γ + ε

        where β3 is the DiD estimate
        """
        # Create interaction term
        treat_post = treatment.values * time_period

        # Prepare regression features
        X_reg = X.copy()
        X_reg['treat'] = treatment.values
        X_reg['post'] = time_period
        X_reg['treat_post'] = treat_post

        # Remove time_col if it's in X (we're using 'post' now)
        if self.time_col in X_reg.columns:
            X_reg = X_reg.drop(columns=[self.time_col])

        # Fit regression
        self.reg_model = clone(self.model)
        self.reg_model.fit(X_reg, y)

        # Extract DiD coefficient (coefficient on treat_post)
        if hasattr(self.reg_model, 'coef_'):
            treat_post_idx = list(X_reg.columns).index('treat_post')
            self.did_coef_ = self.reg_model.coef_[treat_post_idx]
            logger.info(f"Regression DiD coefficient: {self.did_coef_:.4f}")

    def estimate_ate(self) -> float:
        """
        Estimate ATE using simple DiD estimator

        τ̂_DiD = (Ȳ_treat,post - Ȳ_treat,pre) - (Ȳ_control,post - Ȳ_control,pre)

        Returns
        -------
        float
            Estimated ATE
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Difference for treated group (post - pre)
        diff_treated = self.mean_treat_post - self.mean_treat_pre

        # Difference for control group (post - pre)
        diff_control = self.mean_control_post - self.mean_control_pre

        # Difference-in-differences
        self.ate_ = diff_treated - diff_control

        logger.info(f"DiD estimate: {self.ate_:.4f} "
                   f"(Treated: {diff_treated:.4f}, Control: {diff_control:.4f})")

        return self.ate_

    def estimate_att(self) -> float:
        """
        For DiD, ATE = ATT under parallel trends assumption

        Returns
        -------
        float
            Estimated ATT (same as ATE)
        """
        return self.estimate_ate()

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        DiD provides constant treatment effect estimate.
        Returns ATE for all observations.

        For heterogeneous effects over time, consider event study design.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix

        Returns
        -------
        np.ndarray
            Array of constant ATE values
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        logger.warning("DiD provides constant treatment effect. Returning ATE for all units.")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        return np.full(len(X), self.ate_)

    def test_parallel_trends(self, pre_periods: Optional[pd.Series] = None) -> dict:
        """
        Test parallel trends assumption using pre-treatment periods

        If multiple pre-treatment periods available, tests whether
        treatment and control groups had parallel trends before intervention.

        Parameters
        ----------
        pre_periods : pd.Series, optional
            Time periods for pre-treatment data (if more than 2 periods available)

        Returns
        -------
        dict
            Test results including p-value and trend difference
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if pre_periods is None:
            # Simple check: pre-treatment outcome difference
            pre_diff = self.mean_treat_pre - self.mean_control_pre
            logger.info(f"Pre-treatment difference: {pre_diff:.4f}")
            logger.warning("Cannot formally test parallel trends with only 2 time periods. "
                          "Requires multiple pre-treatment periods.")
            return {
                'pre_treatment_diff': pre_diff,
                'test': 'Cannot test with 2 periods only'
            }

        # TODO: Implement formal parallel trends test with multiple pre-periods
        logger.warning("Parallel trends test with multiple periods not yet implemented")
        return {}

    def event_study(
        self,
        relative_time_col: str,
        baseline_period: int = -1
    ) -> pd.DataFrame:
        """
        Estimate event study coefficients (dynamic treatment effects)

        Estimates treatment effects for each time period relative to treatment:
        Y_it = α_i + λ_t + Σ_τ β_τ·D_i·1(t - t_i = τ) + ε_it

        Parameters
        ----------
        relative_time_col : str
            Column name containing relative time (t - treatment_time)
        baseline_period : int
            Reference period (typically -1, just before treatment)

        Returns
        -------
        pd.DataFrame
            Event study coefficients with standard errors
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if relative_time_col not in self.X_train.columns:
            raise ValueError(f"Relative time column '{relative_time_col}' not found")

        logger.info("Event study analysis not fully implemented. Returning simple DiD estimate.")

        # Return simple result
        return pd.DataFrame({
            'period': [0],
            'coefficient': [self.ate_],
            'std_error': [np.nan]
        })

    def estimate_variance(self) -> float:
        """
        Estimate variance of DiD estimator

        Var(τ̂_DiD) = Var(Ȳ_treat,post) + Var(Ȳ_treat,pre) +
                      Var(Ȳ_control,post) + Var(Ȳ_control,pre)

        Returns
        -------
        float
            Estimated variance
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        T = self.treatment_train.values
        Y = self.y_train.values
        time = self.time_period

        # Compute variances for each group-period
        mask_treat_pre = (T == 1) & (time == 0)
        mask_treat_post = (T == 1) & (time == 1)
        mask_control_pre = (T == 0) & (time == 0)
        mask_control_post = (T == 0) & (time == 1)

        var_treat_pre = Y[mask_treat_pre].var() / mask_treat_pre.sum()
        var_treat_post = Y[mask_treat_post].var() / mask_treat_post.sum()
        var_control_pre = Y[mask_control_pre].var() / mask_control_pre.sum()
        var_control_post = Y[mask_control_post].var() / mask_control_post.sum()

        self.variance_ = var_treat_pre + var_treat_post + var_control_pre + var_control_post

        logger.info(f"Estimated variance: {self.variance_:.6f}")
        return self.variance_

    def get_means_table(self) -> pd.DataFrame:
        """
        Get means table for visualization

        Returns
        -------
        pd.DataFrame
            Table with means for each group-period
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        return pd.DataFrame({
            'Group': ['Treatment', 'Treatment', 'Control', 'Control'],
            'Period': ['Pre', 'Post', 'Pre', 'Post'],
            'Mean': [
                self.mean_treat_pre,
                self.mean_treat_post,
                self.mean_control_pre,
                self.mean_control_post
            ],
            'Diff': [
                np.nan,
                self.mean_treat_post - self.mean_treat_pre,
                np.nan,
                self.mean_control_post - self.mean_control_pre
            ]
        })
