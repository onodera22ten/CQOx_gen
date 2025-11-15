"""
DR-Learner: Doubly Robust Learner
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class DRLearner(BaseEstimator):
    """
    Doubly Robust Learner

    Combines outcome regression and propensity score weighting
    """

    def __init__(self, outcome_model=None, propensity_model=None, **kwargs):
        super().__init__(**kwargs)
        self.outcome_model = outcome_model or GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.propensity_model = propensity_model or LogisticRegression(max_iter=1000)

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit DR-Learner"""
        logger.info("Fitting DR-Learner")

        # Fit propensity model
        self.ps_model = clone(self.propensity_model)
        self.ps_model.fit(X, treatment)

        # Fit outcome models (separate for treatment and control)
        mask_treat = treatment == 1
        mask_control = treatment == 0

        self.mu1_model = clone(self.outcome_model)
        self.mu0_model = clone(self.outcome_model)

        self.mu1_model.fit(X[mask_treat], y[mask_treat])
        self.mu0_model.fit(X[mask_control], y[mask_control])

        # Store training data
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("DR-Learner fitted successfully")

        return self

    def estimate_ate(self) -> float:
        """Estimate ATE using doubly robust estimator"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Get propensity scores
        ps = self.ps_model.predict_proba(self.X_train)[:, 1]
        ps = np.clip(ps, 0.01, 0.99)  # Avoid division by zero

        # Get outcome predictions
        mu1 = self.mu1_model.predict(self.X_train)
        mu0 = self.mu0_model.predict(self.X_train)

        # Doubly robust estimator
        T = self.treatment_train.values
        Y = self.y_train.values

        # DR formula
        term1 = T * (Y - mu1) / ps
        term2 = (1 - T) * (Y - mu0) / (1 - ps)
        term3 = mu1 - mu0

        self.ate_ = np.mean(term1 - term2 + term3)
        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """Estimate CATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Simple CATE estimate: difference in outcome models
        mu1 = self.mu1_model.predict(X)
        mu0 = self.mu0_model.predict(X)

        self.cate_ = mu1 - mu0
        return self.cate_
