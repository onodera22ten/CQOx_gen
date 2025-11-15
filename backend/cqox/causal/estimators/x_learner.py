"""
X-Learner: Cross-fitted meta-learner
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class XLearner(BaseEstimator):
    """
    X-Learner

    Two-stage approach with propensity score weighting
    """

    def __init__(self, outcome_model=None, effect_model=None, propensity_model=None, **kwargs):
        super().__init__(**kwargs)
        self.outcome_model = outcome_model or GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.effect_model = effect_model or GradientBoostingRegressor(
            n_estimators=100, max_depth=3, random_state=42
        )
        from sklearn.linear_model import LogisticRegression
        self.propensity_model = propensity_model or LogisticRegression(max_iter=1000)

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit X-Learner"""
        logger.info("Fitting X-Learner")

        # Split data
        mask_treat = treatment == 1
        mask_control = treatment == 0

        X_treat, y_treat = X[mask_treat], y[mask_treat]
        X_control, y_control = X[mask_control], y[mask_control]

        # Stage 1: Fit outcome models
        self.mu1_model = clone(self.outcome_model)
        self.mu0_model = clone(self.outcome_model)

        self.mu1_model.fit(X_treat, y_treat)
        self.mu0_model.fit(X_control, y_control)

        # Stage 2: Impute treatment effects
        # D1 = Y1 - mu0(X1)  (for treated units)
        # D0 = mu1(X0) - Y0  (for control units)
        D1 = y_treat.values - self.mu0_model.predict(X_treat)
        D0 = self.mu1_model.predict(X_control) - y_control.values

        # Fit effect models
        self.tau1_model = clone(self.effect_model)
        self.tau0_model = clone(self.effect_model)

        self.tau1_model.fit(X_treat, D1)
        self.tau0_model.fit(X_control, D0)

        # Fit propensity model
        self.ps_model = clone(self.propensity_model)
        self.ps_model.fit(X, treatment)

        # Store training data
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("X-Learner fitted successfully")

        return self

    def estimate_ate(self) -> float:
        """Estimate ATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        cate = self.estimate_cate(self.X_train)
        self.ate_ = np.mean(cate)
        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """Estimate CATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Get propensity scores
        ps = self.ps_model.predict_proba(X)[:, 1]

        # Weighted combination
        tau1 = self.tau1_model.predict(X)
        tau0 = self.tau0_model.predict(X)

        # CATE = ps * tau0 + (1-ps) * tau1
        self.cate_ = ps * tau0 + (1 - ps) * tau1
        return self.cate_
