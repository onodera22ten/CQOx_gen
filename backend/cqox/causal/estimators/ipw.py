"""
IPW: Inverse Propensity Weighting Estimator

Reweights observations by inverse propensity scores to create pseudo-randomization.
Handles selection bias in non-randomized treatment assignment.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.base import clone
from loguru import logger
from typing import Optional

from .base import BaseEstimator


class IPWEstimator(BaseEstimator):
    """
    Inverse Propensity Weighting (IPW) Estimator

    Creates "pseudo-randomization" by reweighting samples according to
    inverse propensity scores: w_i = T_i/e(X_i) - (1-T_i)/(1-e(X_i))

    Advantages:
    - Simple and interpretable
    - Does not require outcome modeling
    - Consistent if propensity model is correct

    Disadvantages:
    - High variance if propensity scores near 0 or 1
    - Sensitive to model misspecification

    Reference:
    - Rosenbaum & Rubin (1983). "The central role of the propensity score
      in observational studies for causal effects"
    """

    def __init__(
        self,
        propensity_model: Optional[object] = None,
        trim_threshold: float = 0.01,
        stabilize: bool = True,
        **kwargs
    ):
        """
        Parameters
        ----------
        propensity_model : sklearn-compatible classifier
            Model for estimating propensity scores P(T=1|X)
            Default: LogisticRegression
        trim_threshold : float
            Clip propensity scores to [threshold, 1-threshold]
            Prevents extreme weights from unstable propensity scores
        stabilize : bool
            Whether to use stabilized weights (reduces variance)
        """
        super().__init__(**kwargs)
        self.propensity_model = propensity_model or LogisticRegression(
            max_iter=1000,
            penalty='l2',
            C=1.0,
            solver='lbfgs'
        )
        self.trim_threshold = trim_threshold
        self.stabilize = stabilize

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """
        Fit IPW estimator

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix
        treatment : pd.Series
            Binary treatment indicator (0 or 1)
        y : pd.Series
            Outcome variable
        """
        logger.info(f"Fitting IPW estimator with {len(X)} samples")

        # Validate treatment is binary
        unique_treatments = treatment.unique()
        if len(unique_treatments) != 2 or not set(unique_treatments).issubset({0, 1}):
            raise ValueError("Treatment must be binary (0 or 1)")

        # Fit propensity score model
        self.ps_model = clone(self.propensity_model)
        self.ps_model.fit(X, treatment)

        # Store training data
        self.X_train = X.copy()
        self.treatment_train = treatment.copy()
        self.y_train = y.copy()

        # Compute propensity scores
        self.propensity_scores_ = self.ps_model.predict_proba(X)[:, 1]

        # Trim propensity scores to avoid extreme weights
        self.propensity_scores_ = np.clip(
            self.propensity_scores_,
            self.trim_threshold,
            1 - self.trim_threshold
        )

        # Compute IPW weights
        T = treatment.values
        ps = self.propensity_scores_

        if self.stabilize:
            # Stabilized weights: w_i = P(T=t) / P(T=t|X_i)
            p_treat = np.mean(T)
            self.weights_ = np.where(
                T == 1,
                p_treat / ps,
                (1 - p_treat) / (1 - ps)
            )
        else:
            # Unstabilized weights: w_i = 1 / P(T=t|X_i)
            self.weights_ = np.where(
                T == 1,
                1 / ps,
                1 / (1 - ps)
            )

        # Log weight statistics
        logger.info(f"Weight statistics: mean={self.weights_.mean():.3f}, "
                   f"std={self.weights_.std():.3f}, "
                   f"min={self.weights_.min():.3f}, "
                   f"max={self.weights_.max():.3f}")

        # Check for extreme weights (potential positivity violation)
        if self.weights_.max() > 100:
            logger.warning(f"Extreme weights detected (max={self.weights_.max():.1f}). "
                          "Consider checking overlap/positivity assumption.")

        self.is_fitted = True
        logger.info("IPW estimator fitted successfully")

        return self

    def estimate_ate(self) -> float:
        """
        Estimate Average Treatment Effect (ATE) using IPW

        ATE = E[Y(1) - Y(0)]
            = E[T·Y/e(X)] - E[(1-T)·Y/(1-e(X))]

        Returns
        -------
        float
            Estimated ATE
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        T = self.treatment_train.values
        Y = self.y_train.values
        ps = self.propensity_scores_

        # IPW estimator
        ate_treated = np.mean((T * Y) / ps)
        ate_control = np.mean(((1 - T) * Y) / (1 - ps))

        self.ate_ = ate_treated - ate_control

        logger.info(f"Estimated ATE: {self.ate_:.4f}")
        return self.ate_

    def estimate_att(self) -> float:
        """
        Estimate Average Treatment Effect on the Treated (ATT)

        ATT = E[Y(1) - Y(0) | T=1]
            = E[Y | T=1] - E[(1-e(X))/e(X) · Y | T=0]

        Returns
        -------
        float
            Estimated ATT
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        T = self.treatment_train.values
        Y = self.y_train.values
        ps = self.propensity_scores_

        # ATT estimator
        att_treated = np.mean(Y[T == 1])

        # Reweight control group to match treated distribution
        weights_control = ((1 - T) * ps) / (1 - ps)
        att_control = np.sum(weights_control * Y) / np.sum(weights_control)

        self.att_ = att_treated - att_control

        logger.info(f"Estimated ATT: {self.att_:.4f}")
        return self.att_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        IPW cannot directly estimate CATE (conditional treatment effects).
        Returns constant ATE for all observations.

        For heterogeneous effects, use Causal Forest or X-Learner instead.

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

        logger.warning("IPW cannot estimate CATE. Returning constant ATE for all units.")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        return np.full(len(X), self.ate_)

    def estimate_variance(self) -> float:
        """
        Estimate variance of ATE estimator using Hájek variance formula

        Returns
        -------
        float
            Estimated variance of ATE
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        T = self.treatment_train.values
        Y = self.y_train.values
        ps = self.propensity_scores_
        n = len(T)

        # Residuals
        residuals_treated = (T * (Y - self.ate_)) / ps
        residuals_control = ((1 - T) * (Y - 0)) / (1 - ps)
        residuals = residuals_treated - residuals_control

        # Variance estimate
        self.variance_ = np.var(residuals) / n

        logger.info(f"Estimated variance: {self.variance_:.6f}")
        return self.variance_

    def get_propensity_scores(self) -> np.ndarray:
        """Get propensity scores for training data"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        return self.propensity_scores_

    def get_weights(self) -> np.ndarray:
        """Get IPW weights for training data"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")
        return self.weights_

    def predict_propensity(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict propensity scores for new data

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix

        Returns
        -------
        np.ndarray
            Propensity scores P(T=1|X)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        ps = self.ps_model.predict_proba(X)[:, 1]
        ps = np.clip(ps, self.trim_threshold, 1 - self.trim_threshold)

        return ps
