"""
Inverse Propensity Weighting (IPW) Estimator

逆傾向スコア重み付け推定器
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from .base import BaseEstimator


class IPWEstimator(BaseEstimator):
    """
    IPW推定器
    
    **手法**:
    1. Propensity Score e(X) = P(T=1|X) を推定
    2. IPW推定量:
       τ_IPW = (1/n) Σ [ T_i * Y_i / e(X_i) - (1-T_i) * Y_i / (1-e(X_i)) ]
    
    **利点**:
    - シンプルで解釈しやすい
    - Propensityが正しければ一致推定量
    
    **欠点**:
    - Extreme propensity scores（0や1に近い）で非常に不安定
    - High variance
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 propensity_model: str = "logistic",
                 trim_threshold: float = 0.01,
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.propensity_model_type = propensity_model
        self.trim_threshold = trim_threshold
        self.propensity_model = None
    
    def fit(self, data: pd.DataFrame) -> 'IPWEstimator':
        """Propensity Score Modelを学習"""
        X = data[self.feature_cols].values
        T = data[self.treatment_col].values
        
        if self.propensity_model_type == "logistic":
            self.propensity_model = LogisticRegression(max_iter=1000)
        else:
            self.propensity_model = RandomForestClassifier(n_estimators=100)
        
        self.propensity_model.fit(X, T)
        self.fitted = True
        return self
    
    def estimate_ate(self, data: Optional[pd.DataFrame] = None) -> Tuple[float, float]:
        """ATE推定"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if data is None:
            raise ValueError("Data is required for estimation")
        
        X = data[self.feature_cols].values
        T = data[self.treatment_col].values
        Y = data[self.outcome_col].values
        
        # Propensity scores
        e_x = self.propensity_model.predict_proba(X)[:, 1]
        
        # Trimming
        e_x = np.clip(e_x, self.trim_threshold, 1 - self.trim_threshold)
        
        # IPW weights
        weights = np.where(T == 1, 1 / e_x, 1 / (1 - e_x))
        
        # Weighted outcomes
        weighted_outcomes = np.where(T == 1, weights * Y, -weights * Y)
        
        ate = np.mean(weighted_outcomes)
        ate_std = np.std(weighted_outcomes) / np.sqrt(len(data))
        
        return ate, ate_std

