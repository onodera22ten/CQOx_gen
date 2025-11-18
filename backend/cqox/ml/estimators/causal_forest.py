"""
Causal Forest (CF) Estimator

因果森林：Heterogeneous Treatment Effectsの推定に最適
"""
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from .base import BaseEstimator


class CausalForestEstimator(BaseEstimator):
    """
    Causal Forest推定器（簡略版）
    
    **手法**:
    - Random Forestを使ったHonest estimation
    - Treatment groupとControl groupで別々にRFを学習
    - τ(X) = E[Y|T=1,X] - E[Y|T=0,X] をRFで推定
    
    **利点**:
    - Heterogeneous Treatment Effects（個別効果）に強い
    - Non-linear効果をキャプチャ
    - Feature importanceでDriving factorsを特定
    
    **欠点**:
    - 計算コストが高い
    - Interpretabilityが低い
    
    NOTE: 本来はgrf（Generalized Random Forests）パッケージ使用推奨
    """
    
    def __init__(self,
                 treatment_col: str,
                 outcome_col: str,
                 feature_cols: list,
                 n_estimators: int = 100,
                 min_samples_leaf: int = 5,
                 **kwargs):
        super().__init__(treatment_col, outcome_col, feature_cols, **kwargs)
        self.n_estimators = n_estimators
        self.min_samples_leaf = min_samples_leaf
        self.forest_0 = None  # Control group
        self.forest_1 = None  # Treatment group
    
    def fit(self, data: pd.DataFrame) -> 'CausalForestEstimator':
        """Causal Forestを学習"""
        X = data[self.feature_cols].values
        T = data[self.treatment_col].values
        Y = data[self.outcome_col].values
        
        # Separate by treatment
        X_control = X[T == 0]
        Y_control = Y[T == 0]
        X_treated = X[T == 1]
        Y_treated = Y[T == 1]
        
        # Train separate forests
        self.forest_0 = RandomForestRegressor(
            n_estimators=self.n_estimators,
            min_samples_leaf=self.min_samples_leaf,
            random_state=42
        )
        self.forest_1 = RandomForestRegressor(
            n_estimators=self.n_estimators,
            min_samples_leaf=self.min_samples_leaf,
            random_state=42
        )
        
        if len(X_control) > 0:
            self.forest_0.fit(X_control, Y_control)
        if len(X_treated) > 0:
            self.forest_1.fit(X_treated, Y_treated)
        
        self.fitted = True
        return self
    
    def estimate_ate(self, data: Optional[pd.DataFrame] = None) -> Tuple[float, float]:
        """ATE推定（平均CATE）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if data is None:
            raise ValueError("Data is required for estimation")
        
        cate = self.estimate_cate(data)
        ate = np.mean(cate)
        ate_std = np.std(cate) / np.sqrt(len(data))
        
        return ate, ate_std
    
    def estimate_cate(self, data: pd.DataFrame) -> np.ndarray:
        """CATE推定（個別効果）"""
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = data[self.feature_cols].values
        
        # Predict for both groups
        mu_0 = self.forest_0.predict(X)
        mu_1 = self.forest_1.predict(X)
        
        # CATE = difference
        cate = mu_1 - mu_0
        return cate
    
    def feature_importance(self) -> pd.DataFrame:
        """
        Feature importanceを取得
        
        Returns:
            DataFrame: feature名とimportanceのペア
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Average importance from both forests
        importance_0 = self.forest_0.feature_importances_
        importance_1 = self.forest_1.feature_importances_
        importance_avg = (importance_0 + importance_1) / 2
        
        return pd.DataFrame({
            'feature': self.feature_cols,
            'importance': importance_avg
        }).sort_values('importance', ascending=False)

