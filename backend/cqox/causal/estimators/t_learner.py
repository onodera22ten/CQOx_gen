"""
T-Learner: Two model approach
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class TLearner(BaseEstimator):
    """
    T-Learner (Two model learner)

    Trains separate models for treatment and control groups
    """

    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model or GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.model_treat = None
        self.model_control = None

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit T-Learner"""
        logger.info("Fitting T-Learner")

        # Split data by treatment
        mask_treat = treatment == 1
        mask_control = treatment == 0

        X_treat = X[mask_treat]
        y_treat = y[mask_treat]

        X_control = X[mask_control]
        y_control = y[mask_control]

        # Fit treatment model
        self.model_treat = clone(self.model)
        self.model_treat.fit(X_treat, y_treat)

        # Fit control model
        self.model_control = clone(self.model)
        self.model_control.fit(X_control, y_control)

        # Store training data
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("T-Learner fitted successfully")

        return self

    def estimate_ate(self) -> float:
        """Estimate ATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Predict using both models
        y1 = self.model_treat.predict(self.X_train)
        y0 = self.model_control.predict(self.X_train)

        # ATE = E[Y(1) - Y(0)]
        self.ate_ = np.mean(y1 - y0)
        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """Estimate CATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Predict using both models
        y1 = self.model_treat.predict(X)
        y0 = self.model_control.predict(X)

        # CATE = Y(1) - Y(0)
        self.cate_ = y1 - y0
        return self.cate_
