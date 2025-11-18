"""
Instrumental Variables (IV) Estimator

操作変数法：Unmeasured confoundingへの対処
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .base import BaseEstimator


class IVEstimator(BaseEstimator):
    """
    IV推定器（2SLS: Two-Stage Least Squares）
    
    **手法**:
    1. First Stage: T = α0 + α1*Z + X + η （TをZで予測）
    2. Second Stage: Y = β0 + β1*T_hat + X + ε （Yを予測されたTで回帰）
    
    **Instrument Z の条件**:
    - Relevance: Cor(Z, T) ≠ 0 （ZがTに影響）
    - Exogeneity: Cor(Z, ε) = 0 （ZがYに直接影響しない）
    - Exclusion: Z → T → Y のみ（Z → Y の直接パスなし）
    
    **利点**:
    - Unmeasured confoundingがあってもOK
    - Randomized encouragement designで使える
    
    **欠点**:
    - 良いInstrumentを見つけるのが難しい
    - Weak instrumentで推定量が不安定
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 instrument_col: str,  # 操作変数
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.instrument_col = instrument_col
        self.first_stage_model = None
        self.second_stage_model = None
    
    def fit(self, data: pd.DataFrame) -> 'IVEstimator':
        """2SLS を学習"""
        X = data[self.feature_cols].values
        Z = data[[self.instrument_col]].values
        T = data[self.treatment_col].values
        Y = data[self.outcome_col].values
        
        # First Stage: T ~ Z + X
        X_first = np.hstack([Z, X])
        self.first_stage_model = LinearRegression()
        self.first_stage_model.fit(X_first, T)
        
        # Predicted treatment
        T_hat = self.first_stage_model.predict(X_first)
        
        # Second Stage: Y ~ T_hat + X
        X_second = np.hstack([T_hat.reshape(-1, 1), X])
        self.second_stage_model = LinearRegression()
        self.second_stage_model.fit(X_second, Y)
        
        self.fitted = True
        return self
    
    def estimate_ate(self, data: Optional[pd.DataFrame] = None) -> Tuple[float, float]:
        """ATE推定（2SLS coefficient）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # ATE = coefficient of T_hat in second stage
        ate = self.second_stage_model.coef_[0]
        
        # TODO: Robust standard error (Anderson-Rubin, etc.)
        ate_std = 0.1  # Placeholder
        
        return ate, ate_std
    
    def check_instrument_strength(self, data: pd.DataFrame) -> float:
        """
        Instrument strengthをチェック（F-statistic）
        
        F > 10 が目安（Weak instrument問題の回避）
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = data[self.feature_cols].values
        Z = data[[self.instrument_col]].values
        T = data[self.treatment_col].values
        
        X_first = np.hstack([Z, X])
        T_hat = self.first_stage_model.predict(X_first)
        
        # F-statistic for first stage
        residuals = T - T_hat
        r_squared = 1 - (np.var(residuals) / np.var(T))
        n = len(data)
        k = X_first.shape[1]
        f_stat = (r_squared / k) / ((1 - r_squared) / (n - k - 1))
        
        return f_stat

