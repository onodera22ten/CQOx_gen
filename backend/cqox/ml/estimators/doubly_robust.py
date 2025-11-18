"""
Doubly Robust (DR) Estimator

二重ロバスト推定器：Propensity ScoreとOutcome Regressionの両方を使用
どちらか一方が正しければ一致推定量となる（Robustness）
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .base import BaseEstimator


class DoublyRobustEstimator(BaseEstimator):
    """
    Doubly Robust推定器
    
    **手法**:
    1. Propensity Score e(X) = P(T=1|X) をLogistic Regressionで推定
    2. Outcome Regression μ_0(X), μ_1(X) をLinear Regressionで推定
    3. DR推定量:
       τ_DR = (1/n) Σ [ (T_i - e(X_i)) / (e(X_i)(1-e(X_i))) * (Y_i - μ_T(X_i)) + μ_1(X_i) - μ_0(X_i) ]
    
    **利点**:
    - PropensityとOutcomeのどちらか一方が正しければOK
    - バイアス削減効果が高い
    
    **欠点**:
    - Extreme propensity scores（0や1に近い）で不安定
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 propensity_model: str = "logistic",  # "logistic" or "rf"
                 outcome_model: str = "linear",  # "linear" or "rf"
                 trim_threshold: float = 0.01,  # Propensity trimming
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.propensity_model_type = propensity_model
        self.outcome_model_type = outcome_model
        self.trim_threshold = trim_threshold
        
        # Models
        self.propensity_model = None
        self.outcome_model_0 = None  # E[Y|T=0, X]
        self.outcome_model_1 = None  # E[Y|T=1, X]
    
    def fit(self, data: pd.DataFrame) -> 'DoublyRobustEstimator':
        """モデルを学習"""
        X = data[self.feature_cols].values
        T = data[self.treatment_col].values
        Y = data[self.outcome_col].values
        
        # 1. Propensity Score Model
        if self.propensity_model_type == "logistic":
            self.propensity_model = LogisticRegression(max_iter=1000)
        else:
            self.propensity_model = RandomForestClassifier(n_estimators=100)
        
        self.propensity_model.fit(X, T)
        
        # 2. Outcome Regression Models (separate for T=0 and T=1)
        X_control = X[T == 0]
        Y_control = Y[T == 0]
        X_treated = X[T == 1]
        Y_treated = Y[T == 1]
        
        if self.outcome_model_type == "linear":
            self.outcome_model_0 = LinearRegression()
            self.outcome_model_1 = LinearRegression()
        else:
            self.outcome_model_0 = RandomForestRegressor(n_estimators=100)
            self.outcome_model_1 = RandomForestRegressor(n_estimators=100)
        
        if len(X_control) > 0:
            self.outcome_model_0.fit(X_control, Y_control)
        if len(X_treated) > 0:
            self.outcome_model_1.fit(X_treated, Y_treated)
        
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
        
        # Trimming (extreme propensity scores)
        e_x = np.clip(e_x, self.trim_threshold, 1 - self.trim_threshold)
        
        # Outcome predictions
        mu_0 = self.outcome_model_0.predict(X)
        mu_1 = self.outcome_model_1.predict(X)
        
        # DR estimator
        # τ_DR = E[ (T - e(X)) / (e(X)(1-e(X))) * (Y - μ_T(X)) + μ_1(X) - μ_0(X) ]
        residuals = np.where(T == 1,
                            (Y - mu_1) / e_x,
                            -(Y - mu_0) / (1 - e_x))
        
        ate = np.mean(residuals + mu_1 - mu_0)
        ate_std = np.std(residuals + mu_1 - mu_0) / np.sqrt(len(data))
        
        return ate, ate_std
    
    def estimate_cate(self, data: pd.DataFrame) -> np.ndarray:
        """CATE推定（個別効果）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = data[self.feature_cols].values
        
        # Simple CATE: μ_1(X) - μ_0(X)
        mu_0 = self.outcome_model_0.predict(X)
        mu_1 = self.outcome_model_1.predict(X)
        
        cate = mu_1 - mu_0
        return cate

