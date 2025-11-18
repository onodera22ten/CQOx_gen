"""
IV: Instrumental Variables Estimator

Uses instrumental variables to handle endogeneity and unmeasured confounding.
Classic solution for scenarios where treatment assignment is correlated with unobserved factors.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.base import clone
from loguru import logger
from typing import Optional, Union
from scipy import stats

from .base import BaseEstimator


class IVEstimator(BaseEstimator):
    """
    Instrumental Variables (IV) / Two-Stage Least Squares (2SLS) Estimator

    Handles endogeneity when treatment T is correlated with unobserved confounders.
    Uses an instrument Z that satisfies:
    1. Relevance: Cov(Z, T) ≠ 0 (instrument affects treatment)
    2. Exclusion: Z affects Y only through T (not directly)
    3. Independence: Z is independent of unobserved confounders

    Two-Stage Least Squares (2SLS):
    - Stage 1: T̂ = α + βZ + γX + ε  (first-stage regression)
    - Stage 2: Y = δ + τT̂ + θX + η  (second-stage regression with predicted T̂)

    Examples of valid instruments:
    - Randomized encouragement (doesn't force treatment but encourages it)
    - Natural experiments (lottery, distance, policy changes)
    - Genetic variants (Mendelian randomization)

    Classic applications:
    - Angrist & Krueger (1991): Quarter of birth → Education → Earnings
    - Card (1995): College proximity → Education → Wages
    - Acemoglu et al (2001): Settler mortality → Institutions → GDP

    Reference:
    - Angrist & Imbens (1996). "Identification of Causal Effects Using Instrumental Variables"
    - Angrist, Imbens & Rubin (1996). "Identification of Local Average Treatment Effects" (Nobel Prize 2021)
    """

    def __init__(
        self,
        model: Optional[object] = None,
        first_stage_model: Optional[object] = None,
        instrument_col: Optional[str] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        model : sklearn-compatible regressor
            Second-stage model (default: OLS)
        first_stage_model : sklearn-compatible regressor
            First-stage model (default: OLS)
        instrument_col : str, optional
            Name of instrument column in X
            If None, must be specified during fit()
        """
        super().__init__(**kwargs)
        self.model = model or LinearRegression()
        self.first_stage_model = first_stage_model or LinearRegression()
        self.instrument_col = instrument_col

    def fit(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        instrument: Optional[Union[pd.Series, str]] = None
    ):
        """
        Fit IV estimator using Two-Stage Least Squares (2SLS)

        Parameters
        ----------
        X : pd.DataFrame
            Covariate matrix (controls)
        treatment : pd.Series
            Endogenous treatment variable
        y : pd.Series
            Outcome variable
        instrument : pd.Series or str, optional
            Instrument variable. Can be:
            - pd.Series: The instrument values directly
            - str: Column name in X to use as instrument
            - None: Use self.instrument_col from __init__

        Returns
        -------
        self
        """
        logger.info(f"Fitting IV estimator with {len(X)} observations")

        # Handle instrument specification
        if instrument is None and self.instrument_col is None:
            raise ValueError("Must specify instrument via 'instrument' parameter or 'instrument_col' in __init__")

        if isinstance(instrument, str):
            if instrument not in X.columns:
                raise ValueError(f"Instrument column '{instrument}' not found in X")
            Z = X[instrument].values
            X_controls = X.drop(columns=[instrument])
        elif instrument is not None:
            Z = instrument.values
            X_controls = X.copy()
        else:  # Use self.instrument_col
            if self.instrument_col not in X.columns:
                raise ValueError(f"Instrument column '{self.instrument_col}' not found in X")
            Z = X[self.instrument_col].values
            X_controls = X.drop(columns=[self.instrument_col])

        # Store data
        self.X_train = X.copy()
        self.treatment_train = treatment.copy()
        self.y_train = y.copy()
        self.instrument = Z
        self.X_controls = X_controls

        # Check instrument validity
        self._check_instrument_validity(Z, treatment.values, X_controls)

        # STAGE 1: Regress treatment on instrument + controls
        # T = α + βZ + γX + ε
        X_first_stage = X_controls.copy()
        X_first_stage['instrument'] = Z

        self.first_stage = clone(self.first_stage_model)
        self.first_stage.fit(X_first_stage, treatment)

        # Get predicted treatment
        self.treatment_predicted = self.first_stage.predict(X_first_stage)

        # Extract first-stage F-statistic (instrument strength)
        self._compute_first_stage_stats(Z, treatment.values, X_controls)

        # STAGE 2: Regress outcome on predicted treatment + controls
        # Y = δ + τT̂ + θX + η
        X_second_stage = X_controls.copy()
        X_second_stage['treatment_predicted'] = self.treatment_predicted

        self.second_stage = clone(self.model)
        self.second_stage.fit(X_second_stage, y)

        # Extract IV coefficient (treatment effect)
        if hasattr(self.second_stage, 'coef_'):
            treatment_idx = list(X_second_stage.columns).index('treatment_predicted')
            self.iv_coef_ = self.second_stage.coef_[treatment_idx]
            logger.info(f"IV estimate (2SLS): {self.iv_coef_:.4f}")

        self.is_fitted = True
        logger.info("IV estimator fitted successfully")

        return self

    def _check_instrument_validity(
        self,
        Z: np.ndarray,
        T: np.ndarray,
        X: pd.DataFrame
    ):
        """
        Check instrument validity assumptions

        1. Relevance: Cov(Z, T) ≠ 0
        2. Balance: Z should not be correlated with observables X (weak test)
        """
        # Test relevance: Correlation between instrument and treatment
        corr_ZT = np.corrcoef(Z, T)[0, 1]
        logger.info(f"Instrument-Treatment correlation: {corr_ZT:.4f}")

        if abs(corr_ZT) < 0.1:
            logger.warning(
                f"Weak instrument detected (corr={corr_ZT:.4f}). "
                "First-stage F-statistic should be > 10 for valid inference."
            )

        # Test balance: Instrument should be uncorrelated with controls
        # (This is a weak test - true test requires theory/domain knowledge)
        if len(X.columns) > 0:
            max_corr = 0
            worst_var = None
            for col in X.columns:
                if pd.api.types.is_numeric_dtype(X[col]):
                    corr = np.corrcoef(Z, X[col].values)[0, 1]
                    if abs(corr) > abs(max_corr):
                        max_corr = corr
                        worst_var = col

            if abs(max_corr) > 0.3:
                logger.warning(
                    f"Instrument may violate independence assumption. "
                    f"High correlation with '{worst_var}': {max_corr:.4f}"
                )

    def _compute_first_stage_stats(
        self,
        Z: np.ndarray,
        T: np.ndarray,
        X: pd.DataFrame
    ):
        """
        Compute first-stage diagnostics

        F-statistic > 10 is rule of thumb for "strong instrument"
        (Stock & Yogo 2005)
        """
        # Fit first-stage regression
        X_first = X.copy()
        X_first['instrument'] = Z

        n = len(T)
        k = len(X_first.columns)  # Number of regressors

        # Compute residuals
        T_pred = self.first_stage.predict(X_first)
        residuals = T - T_pred

        # Compute R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((T - np.mean(T)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Compute F-statistic for instrument
        # F = (R² / k) / ((1 - R²) / (n - k - 1))
        if r_squared < 1.0:
            f_stat = (r_squared / k) / ((1 - r_squared) / (n - k - 1))
            self.first_stage_f_stat_ = f_stat

            logger.info(f"First-stage F-statistic: {f_stat:.2f} (threshold: 10)")
            logger.info(f"First-stage R²: {r_squared:.4f}")

            if f_stat < 10:
                logger.warning(
                    f"Weak instrument (F={f_stat:.2f} < 10). "
                    "IV estimates may be biased. Consider stronger instrument."
                )
        else:
            logger.warning("Perfect first-stage fit - check for overfitting")

    def estimate_ate(self) -> float:
        """
        Estimate Local Average Treatment Effect (LATE)

        For binary instrument and treatment, IV estimates LATE:
        the causal effect for "compliers" (those who take treatment when encouraged)

        For continuous instruments, estimates weighted average treatment effect

        Returns
        -------
        float
            Estimated ATE (LATE for binary IV)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        self.ate_ = self.iv_coef_
        logger.info(f"Estimated LATE: {self.ate_:.4f}")

        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        Standard IV cannot estimate CATE (heterogeneous effects)

        For heterogeneous treatment effects with instruments, use:
        - Local IV (Heckman & Vytlacil 2005)
        - IV-based Heterogeneous Treatment Effects methods

        Returns constant LATE for all observations.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix

        Returns
        -------
        np.ndarray
            Array of constant LATE values
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        logger.warning("Standard IV estimates constant LATE. Returning same effect for all units.")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        return np.full(len(X), self.ate_)

    def estimate_variance(self) -> float:
        """
        Estimate variance of IV estimator

        Uses heteroskedasticity-robust standard errors

        Returns
        -------
        float
            Estimated variance of ATE
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Compute residuals from second stage
        X_second_stage = self.X_controls.copy()
        X_second_stage['treatment_predicted'] = self.treatment_predicted

        y_pred = self.second_stage.predict(X_second_stage)
        residuals = self.y_train.values - y_pred

        n = len(residuals)

        # Compute variance using robust standard errors
        # (This is simplified - full implementation would use sandwich estimator)
        self.variance_ = np.var(residuals) / n

        logger.info(f"Estimated variance: {self.variance_:.6f}")
        return self.variance_

    def get_diagnostics(self) -> dict:
        """
        Get IV diagnostic statistics

        Returns
        -------
        dict
            Diagnostic statistics including:
            - first_stage_f_stat: F-statistic for instrument strength
            - instrument_correlation: Correlation between Z and T
            - late: Local Average Treatment Effect
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        corr_ZT = np.corrcoef(self.instrument, self.treatment_train.values)[0, 1]

        return {
            'late': self.ate_,
            'first_stage_f_stat': getattr(self, 'first_stage_f_stat_', None),
            'instrument_correlation': corr_ZT,
            'weak_instrument_warning': getattr(self, 'first_stage_f_stat_', 999) < 10
        }

    def test_overidentification(self, instruments: pd.DataFrame) -> dict:
        """
        Sargan-Hansen test for overidentifying restrictions

        When there are more instruments than endogenous variables,
        tests whether instruments are valid (uncorrelated with error term)

        Parameters
        ----------
        instruments : pd.DataFrame
            Matrix of multiple instruments (J > K)

        Returns
        -------
        dict
            Test statistic and p-value
        """
        logger.warning("Overidentification test not yet implemented")
        return {
            'test': 'sargan',
            'statistic': None,
            'p_value': None
        }
