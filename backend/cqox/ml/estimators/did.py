"""
Difference-in-Differences (DiD) Estimator

差分の差分推定器：パネルデータでの因果推論
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .base import BaseEstimator


class DiDEstimator(BaseEstimator):
    """
    DiD推定器
    
    **手法**:
    - Treatment群とControl群の時系列比較
    - τ_DiD = (Y_treated,post - Y_treated,pre) - (Y_control,post - Y_control,pre)
    
    **前提**:
    - Parallel Trends Assumption（平行トレンド仮定）
    - Treatment前のトレンドがTreatment群とControl群で同じ
    
    **利点**:
    - 時間不変の交絡因子を除去できる
    - 政策評価で広く使われる
    
    **欠点**:
    - Parallel Trendsが成立しない場合バイアス
    - Time-varying confoundersには対応できない
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 time_col: str = "time",
                 post_treatment_period: int = 1,
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.time_col = time_col
        self.post_treatment_period = post_treatment_period
        self.model = None
    
    def fit(self, data: pd.DataFrame) -> 'DiDEstimator':
        """DiD回帰モデルを学習"""
        # DiD regression: Y = β0 + β1*T + β2*Post + β3*(T*Post) + X + ε
        # β3 = DiD estimator
        
        # Create interaction term
        data_copy = data.copy()
        data_copy['post'] = (data_copy[self.time_col] >= self.post_treatment_period).astype(int)
        data_copy['T_x_Post'] = data_copy[self.treatment_col] * data_copy['post']
        
        # Feature matrix
        feature_cols = [self.treatment_col, 'post', 'T_x_Post'] + self.feature_cols
        X = data_copy[feature_cols].values
        Y = data_copy[self.outcome_col].values
        
        # Fit regression
        self.model = LinearRegression()
        self.model.fit(X, Y)
        
        self.fitted = True
        return self
    
    def estimate_ate(self, data: Optional[pd.DataFrame] = None) -> Tuple[float, float]:
        """ATE推定（DiD係数）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # DiD estimator = coefficient of (T × Post) interaction
        # Assuming [T, Post, T_x_Post, ...features] order
        ate = self.model.coef_[2]  # T_x_Post coefficient
        
        # TODO: Robust standard error calculation
        ate_std = 0.1  # Placeholder
        
        return ate, ate_std

