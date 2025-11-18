"""
Regression Discontinuity (RD) Estimator

回帰不連続デザイン：Threshold（閾値）でのTreatment割り当てを利用
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from .base import BaseEstimator


class RDEstimator(BaseEstimator):
    """
    RD推定器
    
    **手法**:
    - Running variable（連続変数）がThresholdを超えるとTreatmentが割り当てられる
    - Threshold付近での局所的な因果効果を推定
    - Sharp RD: Treatment assignment = 1(X >= c)
    - Fuzzy RD: Treatment probabilityがThresholdで不連続に変化
    
    **前提**:
    - Threshold付近でのみ推定（Local ATE）
    - Running variableを操作できない（Manipulation test）
    
    **利点**:
    - As-if randomization（Threshold付近でランダム化されたようなもの）
    - Confounding biasが少ない
    
    **欠点**:
    - Threshold付近のみでしか推定できない（External validity）
    - Bandwidth選択が結果に影響
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 running_var: str,  # Running variable (X)
                 threshold: float,  # Cutoff point (c)
                 bandwidth: Optional[float] = None,  # Bandwidth for local regression
                 polynomial_order: int = 1,  # Order of polynomial (1=linear, 2=quadratic)
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.running_var = running_var
        self.threshold = threshold
        self.bandwidth = bandwidth
        self.polynomial_order = polynomial_order
        self.model_below = None  # X < threshold
        self.model_above = None  # X >= threshold
    
    def fit(self, data: pd.DataFrame) -> 'RDEstimator':
        """RD回帰を学習"""
        # Center running variable at threshold
        X_centered = data[self.running_var] - self.threshold
        
        # Apply bandwidth (if specified)
        if self.bandwidth is not None:
            mask = np.abs(X_centered) <= self.bandwidth
            data = data[mask].copy()
            X_centered = X_centered[mask]
        
        # Separate data by threshold
        below_threshold = X_centered < 0
        above_threshold = X_centered >= 0
        
        # Polynomial features
        poly = PolynomialFeatures(degree=self.polynomial_order, include_bias=False)
        
        # Fit models on both sides
        if np.sum(below_threshold) > 0:
            X_below = poly.fit_transform(X_centered[below_threshold].values.reshape(-1, 1))
            Y_below = data[self.outcome_col].values[below_threshold]
            self.model_below = LinearRegression()
            self.model_below.fit(X_below, Y_below)
        
        if np.sum(above_threshold) > 0:
            X_above = poly.fit_transform(X_centered[above_threshold].values.reshape(-1, 1))
            Y_above = data[self.outcome_col].values[above_threshold]
            self.model_above = LinearRegression()
            self.model_above.fit(X_above, Y_above)
        
        self.fitted = True
        return self
    
    def estimate_ate(self, data: Optional[pd.DataFrame] = None) -> Tuple[float, float]:
        """ATE推定（Discontinuity at threshold）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Predict at threshold (X = 0 after centering)
        poly = PolynomialFeatures(degree=self.polynomial_order, include_bias=False)
        X_at_threshold = poly.fit_transform(np.array([[0]]))
        
        # Predict from both sides
        Y_limit_below = self.model_below.predict(X_at_threshold)[0]
        Y_limit_above = self.model_above.predict(X_at_threshold)[0]
        
        # RD estimate = jump at threshold
        ate = Y_limit_above - Y_limit_below
        
        # TODO: Robust standard error (clustered, heteroskedasticity-robust)
        ate_std = 0.1  # Placeholder
        
        return ate, ate_std
    
    def plot_rd(self, data: pd.DataFrame):
        """
        RD plot（可視化用）
        
        Returns:
            dict: Plot用のデータ
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X_centered = data[self.running_var] - self.threshold
        Y = data[self.outcome_col]
        
        # Sort by running variable
        sort_idx = np.argsort(X_centered)
        X_sorted = X_centered.values[sort_idx]
        Y_sorted = Y.values[sort_idx]
        
        # Fitted values
        poly = PolynomialFeatures(degree=self.polynomial_order, include_bias=False)
        
        below_mask = X_sorted < 0
        above_mask = X_sorted >= 0
        
        Y_fitted = np.zeros_like(Y_sorted)
        if np.sum(below_mask) > 0:
            X_below = poly.fit_transform(X_sorted[below_mask].reshape(-1, 1))
            Y_fitted[below_mask] = self.model_below.predict(X_below)
        if np.sum(above_mask) > 0:
            X_above = poly.fit_transform(X_sorted[above_mask].reshape(-1, 1))
            Y_fitted[above_mask] = self.model_above.predict(X_above)
        
        return {
            'running_var': X_sorted,
            'outcome': Y_sorted,
            'fitted': Y_fitted,
            'threshold': 0.0
        }

