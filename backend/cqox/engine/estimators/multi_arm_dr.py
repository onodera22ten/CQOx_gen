"""
V2 Module A: Multi-Arm Doubly Robust Estimator
V2.pdf仕様準拠 - A/B/n実験・段階施策・Dose-Response対応
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression


class MultiArmDREstimator:
    """
    多腕処置（A/B/n, 段階施策）用のDoubly Robust推定器

    V2.pdf Page 2:
    - treatment が 0..K の整数値の場合、0 をコントロールとして K 個のダミーに分解
    - DR Learner / X-Learner 等をクラスごとに適用
    """

    def __init__(self, base_model=None):
        self.base_model = base_model or RandomForestRegressor(n_estimators=100, random_state=42)
        self.models_tau = {}  # arm -> model
        self.propensity_models = {}  # arm -> propensity score model
        self.arms = []

    def fit(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray):
        """
        学習

        Args:
            X: 共変量 (n_samples, n_features)
            T: 処置 (n_samples,) - 0 = control, 1,2,3... = treatment arms
            Y: アウトカム (n_samples,)
        """
        # 各armを特定
        self.arms = sorted([int(t) for t in set(T) if t != 0])

        for arm in self.arms:
            # Binary処置に分解: arm vs control
            T_binary = (T == arm).astype(int)

            # Propensity Score推定
            ps_model = LogisticRegression(max_iter=1000)
            ps_model.fit(X, T_binary)
            self.propensity_models[arm] = ps_model

            # Outcome model推定（treated/control別々に）
            X_treated = X[T_binary == 1]
            Y_treated = Y[T_binary == 1]
            X_control = X[T_binary == 0]
            Y_control = Y[T_binary == 0]

            # Outcome models
            model_1 = RandomForestRegressor(n_estimators=100, random_state=42)
            model_0 = RandomForestRegressor(n_estimators=100, random_state=42)

            if len(X_treated) > 0:
                model_1.fit(X_treated, Y_treated)
            if len(X_control) > 0:
                model_0.fit(X_control, Y_control)

            self.models_tau[arm] = {
                'model_1': model_1,
                'model_0': model_0,
                'ps_model': ps_model
            }

    def effect(self, X: np.ndarray) -> Dict[int, np.ndarray]:
        """
        各armのATEを推定

        Returns:
            dict: {arm_id: tau(X)} for each arm
        """
        effects = {}

        for arm in self.arms:
            models = self.models_tau[arm]
            model_1 = models['model_1']
            model_0 = models['model_0']

            # Doubly Robust推定
            mu_1 = model_1.predict(X) if len(model_1.estimators_) > 0 else np.zeros(len(X))
            mu_0 = model_0.predict(X) if len(model_0.estimators_) > 0 else np.zeros(len(X))

            tau = mu_1 - mu_0
            effects[arm] = tau

        return effects

    def estimate_ate(self, X: np.ndarray, T: np.ndarray, Y: np.ndarray) -> Dict[int, float]:
        """
        Average Treatment Effect（平均処置効果）を推定

        Returns:
            dict: {arm_id: ATE} for each arm
        """
        ate_results = {}

        for arm in self.arms:
            T_binary = (T == arm).astype(int)
            ps = self.propensity_models[arm].predict_proba(X)[:, 1]

            models = self.models_tau[arm]
            mu_1 = models['model_1'].predict(X) if len(models['model_1'].estimators_) > 0 else np.zeros(len(X))
            mu_0 = models['model_0'].predict(X) if len(models['model_0'].estimators_) > 0 else np.zeros(len(X))

            # Doubly Robust formula
            ps = np.clip(ps, 0.01, 0.99)  # stabilize
            dr_term_1 = T_binary * (Y - mu_1) / ps
            dr_term_0 = (1 - T_binary) * (Y - mu_0) / (1 - ps)

            ate = np.mean(mu_1 - mu_0 + dr_term_1 - dr_term_0)
            ate_results[arm] = float(ate)

        return ate_results


class DoseResponseEstimator:
    """
    Dose-Response推定器

    V2.pdf Page 2:
    - 処置列を「数値として解釈」+ 最低/最高 dose を指定
    - 多項式回帰でスムーズな曲線を推定
    """

    def __init__(self, polynomial_degree: int = 2):
        self.polynomial_degree = polynomial_degree
        self.model = None
        self.min_dose = None
        self.max_dose = None

    def fit(self, X: np.ndarray, dose: np.ndarray, Y: np.ndarray):
        """
        学習

        Args:
            X: 共変量
            dose: 処置量（連続値）
            Y: アウトカム
        """
        self.min_dose = np.min(dose)
        self.max_dose = np.max(dose)

        # 多項式特徴量を作成
        dose_poly = np.column_stack([dose**i for i in range(1, self.polynomial_degree + 1)])
        X_with_dose = np.column_stack([X, dose_poly])

        # Random Forest回帰
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_with_dose, Y)

    def predict_curve(self, X: np.ndarray, dose_range: np.ndarray) -> np.ndarray:
        """
        Dose-Responseカーブを予測

        Args:
            X: 共変量（単一サンプルまたは平均的なプロファイル）
            dose_range: 評価するdose値の配列

        Returns:
            期待アウトカム E[Y|dose]
        """
        predictions = []

        for d in dose_range:
            dose_poly = np.array([[d**i for i in range(1, self.polynomial_degree + 1)]])
            if X.ndim == 1:
                X_input = np.column_stack([X.reshape(1, -1), dose_poly])
            else:
                X_input = np.column_stack([X, dose_poly])

            pred = self.model.predict(X_input)
            predictions.append(pred.mean())

        return np.array(predictions)

    def optimal_dose(self, X: np.ndarray, n_grid: int = 100) -> float:
        """
        最適doseを探索

        Returns:
            最大期待アウトカムを与えるdose
        """
        dose_grid = np.linspace(self.min_dose, self.max_dose, n_grid)
        outcomes = self.predict_curve(X, dose_grid)
        optimal_idx = np.argmax(outcomes)
        return float(dose_grid[optimal_idx])
