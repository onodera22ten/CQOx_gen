"""
Causal Forest
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class CausalForest(BaseEstimator):
    """
    Causal Forest (simplified implementation)

    Note: Full implementation would use econml.CausalForestDML
    This is a simplified version using sklearn
    """

    def __init__(self, n_estimators=100, **kwargs):
        super().__init__(**kwargs)
        self.n_estimators = n_estimators
        self.model_treat = None
        self.model_control = None

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit Causal Forest"""
        logger.info("Fitting Causal Forest (simplified)")

        # Split data
        mask_treat = treatment == 1
        mask_control = treatment == 0

        # Fit random forests for each group
        self.model_treat = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=10,
            min_samples_leaf=20,
            random_state=42
        )
        self.model_control = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=10,
            min_samples_leaf=20,
            random_state=42
        )

        self.model_treat.fit(X[mask_treat], y[mask_treat])
        self.model_control.fit(X[mask_control], y[mask_control])

        # Store training data
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("Causal Forest fitted successfully")

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

        y1 = self.model_treat.predict(X)
        y0 = self.model_control.predict(X)

        self.cate_ = y1 - y0
        return self.cate_
