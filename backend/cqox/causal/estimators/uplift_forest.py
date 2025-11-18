"""
Uplift Forest
"""
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from loguru import logger

from .base import BaseEstimator


class UpliftForest(BaseEstimator):
    """
    Uplift Random Forest (simplified)

    Trains an ensemble of trees optimized for uplift
    """

    def __init__(self, n_estimators=100, **kwargs):
        super().__init__(**kwargs)
        self.n_estimators = n_estimators
        self.trees_treat = []
        self.trees_control = []

    def fit(self, X: pd.DataFrame, treatment: pd.Series, y: pd.Series):
        """Fit Uplift Forest"""
        logger.info("Fitting Uplift Forest")

        mask_treat = treatment == 1
        mask_control = treatment == 0

        X_treat, y_treat = X[mask_treat], y[mask_treat]
        X_control, y_control = X[mask_control], y[mask_control]

        # Train ensemble
        for i in range(self.n_estimators):
            # Bootstrap samples
            n_treat = len(X_treat)
            n_control = len(X_control)

            idx_treat = np.random.choice(n_treat, n_treat, replace=True)
            idx_control = np.random.choice(n_control, n_control, replace=True)

            # Train trees
            tree_treat = DecisionTreeRegressor(max_depth=10, min_samples_leaf=20, random_state=i)
            tree_control = DecisionTreeRegressor(max_depth=10, min_samples_leaf=20, random_state=i)

            tree_treat.fit(X_treat.iloc[idx_treat], y_treat.iloc[idx_treat])
            tree_control.fit(X_control.iloc[idx_control], y_control.iloc[idx_control])

            self.trees_treat.append(tree_treat)
            self.trees_control.append(tree_control)

        self.X_train = X
        self.treatment_train = treatment
        self.y_train = y

        self.is_fitted = True
        logger.info("Uplift Forest fitted successfully")

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

        # Average predictions across all trees
        y1_preds = np.array([tree.predict(X) for tree in self.trees_treat])
        y0_preds = np.array([tree.predict(X) for tree in self.trees_control])

        y1 = np.mean(y1_preds, axis=0)
        y0 = np.mean(y0_preds, axis=0)

        self.cate_ = y1 - y0
        return self.cate_
