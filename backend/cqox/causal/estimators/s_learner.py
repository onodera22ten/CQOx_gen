"""
S-Learner: Single model approach
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.base import clone
from loguru import logger

from .base import BaseEstimator


class SLearner(BaseEstimator):
    """
    S-Learner (Single model learner)

    Trains a single model Y ~ X + T and estimates CATE by taking differences
    """

    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model or GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self._model = None

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit S-Learner"""
        logger.info("Fitting S-Learner")

        # Create feature matrix with treatment
        X_with_t = X.copy()
        X_with_t['treatment'] = treatment.values

        # Fit model
        self._model = clone(self.model)
        self._model.fit(X_with_t, y)

        # Store training data for ATE/CATE estimation
        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("S-Learner fitted successfully")

        return self

    def estimate_ate(self) -> float:
        """Estimate ATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Predict under treatment and control
        X_treat = self.X_train.copy()
        X_treat['treatment'] = 1
        y1 = self._model.predict(X_treat)

        X_control = self.X_train.copy()
        X_control['treatment'] = 0
        y0 = self._model.predict(X_control)

        # ATE = E[Y(1) - Y(0)]
        self.ate_ = np.mean(y1 - y0)
        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """Estimate CATE"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Predict under treatment
        X_treat = X.copy()
        X_treat['treatment'] = 1
        y1 = self._model.predict(X_treat)

        # Predict under control
        X_control = X.copy()
        X_control['treatment'] = 0
        y0 = self._model.predict(X_control)

        # CATE = Y(1) - Y(0)
        self.cate_ = y1 - y0
        return self.cate_
