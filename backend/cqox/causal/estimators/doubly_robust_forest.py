"""
Doubly Robust Forest / R-Learner
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class DoublyRobustForest(BaseEstimator):
    """
    Doubly Robust Forest (R-Learner style)

    Combines propensity score estimation with residualized outcome modeling
    """

    def __init__(self, n_estimators=100, **kwargs):
        super().__init__(**kwargs)
        self.n_estimators = n_estimators
        self.propensity_model = None
        self.outcome_model = None
        self.effect_model = None

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit Doubly Robust Forest"""
        logger.info("Fitting Doubly Robust Forest")

        # Step 1: Estimate propensity scores
        self.propensity_model = LogisticRegression(max_iter=1000, random_state=42)
        self.propensity_model.fit(X, treatment)
        ps = self.propensity_model.predict_proba(X)[:, 1]
        ps = np.clip(ps, 0.01, 0.99)

        # Step 2: Estimate outcome model (marginal outcome E[Y|X])
        self.outcome_model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=42
        )
        self.outcome_model.fit(X, y)
        m_hat = self.outcome_model.predict(X)

        # Step 3: Compute residuals
        # Pseudo-outcome for effect estimation
        T = treatment.values
        Y = y.values

        # Residualized treatment
        t_residual = T - ps

        # Residualized outcome (doubly robust adjustment)
        y_residual = (Y - m_hat) / (T - ps + 1e-6)

        # Step 4: Fit effect model on residuals
        self.effect_model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=10,
            min_samples_leaf=20,
            random_state=42
        )

        # Weight by inverse variance
        weights = np.abs(t_residual) + 1e-6
        self.effect_model.fit(X, y_residual, sample_weight=weights)

        # Store training data
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("Doubly Robust Forest fitted successfully")

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

        self.cate_ = self.effect_model.predict(X)
        return self.cate_
