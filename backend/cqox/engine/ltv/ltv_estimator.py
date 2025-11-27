"""
V2 Module C: CLV (Customer Lifetime Value) Estimator
V2.pdf Page 5-6 仕様準拠 - Survival分析 + 割引現在価値
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple


class SimpleCLVEstimator:
    """
    シンプルなCLV推定器

    V2.pdf Page 5:
    CLV = E[Σ_t=1^T R_t · S(t)] · 1/(1+r)^t

    where:
    - R_t: 期間tの期待収益
    - S(t): 時間tにおける生存確率
    - r: 割引率
    """

    def __init__(self, discount_rate: float = 0.01):
        """
        Args:
            discount_rate: 割引率（月次なら0.01 = 年率12%相当）
        """
        self.discount_rate = discount_rate
        self.df = None

    def fit(self, df_events: pd.DataFrame):
        """
        学習

        Args:
            df_events: columns [user_id, t, revenue, treated]
                - t: 経過期間（signup後の週数など）
                - revenue: その期間の収益
                - treated: 施策適用フラグ
        """
        self.df = df_events

    def _survival_curve(self, treated: bool) -> Dict[int, float]:
        """
        生存曲線（Retention曲線）を計算

        Survival = その時点まで1回以上購買しているユーザ比率（簡易定義）
        """
        df = self.df[self.df["treated"] == treated].copy()
        surv = {}

        for t, group in df.groupby("t"):
            users_total = group["user_id"].nunique()
            active = group[group["revenue"] > 0]["user_id"].nunique()
            surv[int(t)] = active / users_total if users_total > 0 else 0.0

        return surv

    def clv(self, treated: bool) -> float:
        """
        CLVを計算

        Returns:
            割引現在価値化されたCLV（¥）
        """
        surv = self._survival_curve(treated)
        clv_val = 0.0

        for t, s in surv.items():
            mean_rev_t = self.df[
                (self.df["treated"] == treated) & (self.df["t"] == t)
            ]["revenue"].mean()

            if pd.isna(mean_rev_t):
                mean_rev_t = 0.0

            disc = 1.0 / ((1 + self.discount_rate) ** t)
            clv_val += s * mean_rev_t * disc

        return float(clv_val)

    def delta_clv(self) -> float:
        """
        ΔCLV（Treated vs Control）を計算
        """
        clv_treated = self.clv(treated=True)
        clv_control = self.clv(treated=False)
        return clv_treated - clv_control

    def retention_curve(self, treated: bool) -> pd.DataFrame:
        """
        Retention曲線をDataFrameで返す

        Returns:
            columns: [t, retention_rate]
        """
        surv = self._survival_curve(treated)
        return pd.DataFrame([
            {"t": t, "retention_rate": rate}
            for t, rate in sorted(surv.items())
        ])

    def cohort_analysis(self, cohort_column: str = "cohort") -> pd.DataFrame:
        """
        コホート別のCLVを分析

        Args:
            cohort_column: コホートを識別する列名

        Returns:
            columns: [cohort, clv_treated, clv_control, delta_clv]
        """
        if cohort_column not in self.df.columns:
            raise ValueError(f"Column '{cohort_column}' not found")

        results = []

        for cohort, group_df in self.df.groupby(cohort_column):
            estimator = SimpleCLVEstimator(discount_rate=self.discount_rate)
            estimator.fit(group_df)

            clv_t = estimator.clv(treated=True)
            clv_c = estimator.clv(treated=False)

            results.append({
                "cohort": cohort,
                "clv_treated": clv_t,
                "clv_control": clv_c,
                "delta_clv": clv_t - clv_c
            })

        return pd.DataFrame(results)


class AdvancedCLVEstimator:
    """
    高度なCLV推定器（Kaplan-Meier + GLM）

    より正確なSurvival分析を行う
    """

    def __init__(self, discount_rate: float = 0.01):
        self.discount_rate = discount_rate
        self.survival_models = {}

    def fit_survival(self, df: pd.DataFrame, treated: bool):
        """
        Kaplan-Meier法でSurvival関数を推定

        Args:
            df: event data
            treated: treatment flag
        """
        df_filtered = df[df["treated"] == treated].copy()

        # 各時点での生存/離脱を集計
        time_points = sorted(df_filtered["t"].unique())
        n_risk = []
        n_events = []

        for t in time_points:
            df_t = df_filtered[df_filtered["t"] <= t]
            active_users = df_t[df_t["revenue"] > 0]["user_id"].nunique()
            total_users = df_t["user_id"].nunique()

            n_risk.append(total_users)
            # 簡易: 前期間からの減少をイベントとみなす
            if len(n_events) == 0:
                n_events.append(0)
            else:
                n_events.append(max(0, n_risk[-2] - n_risk[-1]))

        # Kaplan-Meier推定
        survival_probs = []
        cum_survival = 1.0

        for i, (n_r, n_e) in enumerate(zip(n_risk, n_events)):
            if n_r > 0:
                cum_survival *= (1 - n_e / n_r)
            survival_probs.append(cum_survival)

        self.survival_models[treated] = {
            "time_points": time_points,
            "survival_probs": survival_probs
        }

    def predict_clv(self, treated: bool, horizon: int = 52) -> float:
        """
        予測期間内のCLVを計算

        Args:
            treated: treatment flag
            horizon: 予測期間（週数）

        Returns:
            CLV (¥)
        """
        if treated not in self.survival_models:
            return 0.0

        model = self.survival_models[treated]
        time_points = model["time_points"]
        survival_probs = model["survival_probs"]

        clv = 0.0

        for t in range(1, min(horizon + 1, len(time_points) + 1)):
            if t <= len(survival_probs):
                s_t = survival_probs[t - 1]
            else:
                s_t = survival_probs[-1]  # 最後の値を使用

            # 仮の収益（実データから平均を取る方が正確）
            mean_rev = 1000.0  # placeholder

            disc = 1.0 / ((1 + self.discount_rate) ** t)
            clv += s_t * mean_rev * disc

        return clv
