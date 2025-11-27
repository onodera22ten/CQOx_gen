"""
V2 Module B: Thompson Sampling Bandit
V2.pdf Page 3-4 仕様準拠 - オンライン配信比率最適化
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ArmState:
    """
    各armのBeta分布パラメータ

    V2.pdf: alpha = 成功数 + 1, beta = 失敗数 + 1
    """
    alpha: float = 1.0
    beta: float = 1.0


class BernoulliThompsonBandit:
    """
    Bernoulli報酬のThompson Samplingバンディット

    V2.pdf Page 3:
    - Beta分布からサンプリングして配信比率を決定
    - reward in {0,1} でalphaとbetaを更新
    """

    def __init__(self, arm_ids: List[str]):
        self.state = {arm: ArmState() for arm in arm_ids}
        self.arm_ids = arm_ids

    def sample_allocation(self, n_samples: int = 10000) -> Dict[str, float]:
        """
        Thompson Samplingで配信比率をサンプリング

        Args:
            n_samples: モンテカルロサンプル数

        Returns:
            各armの配信比率 {arm_id: allocation_rate}
        """
        scores = {}

        for arm, s in self.state.items():
            # Beta分布からサンプル
            score = np.random.beta(s.alpha, s.beta, size=n_samples).mean()
            scores[arm] = score

        # 正規化して配分比率に
        total = sum(scores.values())
        if total > 0:
            return {arm: val / total for arm, val in scores.items()}
        else:
            # 全て0の場合は均等配分
            return {arm: 1.0 / len(self.arm_ids) for arm in self.arm_ids}

    def update(self, outcomes: List[Tuple[str, int]]):
        """
        観測結果でBeta分布を更新

        Args:
            outcomes: [(arm_id, reward), ...] where reward in {0,1}
        """
        for arm_id, reward in outcomes:
            if arm_id not in self.state:
                continue

            s = self.state[arm_id]
            if reward == 1:
                s.alpha += 1
            else:
                s.beta += 1

    def get_state(self) -> Dict[str, Dict[str, float]]:
        """
        現在の状態を取得（API返却用）

        Returns:
            {arm_id: {"alpha": ..., "beta": ..., "mean": ..., "var": ...}}
        """
        result = {}

        for arm, s in self.state.items():
            mean = s.alpha / (s.alpha + s.beta)
            var = (s.alpha * s.beta) / ((s.alpha + s.beta)**2 * (s.alpha + s.beta + 1))

            result[arm] = {
                "alpha": s.alpha,
                "beta": s.beta,
                "mean": mean,
                "variance": var
            }

        return result


class GaussianThompsonBandit:
    """
    連続報酬（Gaussian）のThompson Sampling

    Δ¥など連続値報酬に対応
    """

    @dataclass
    class GaussianState:
        mu: float = 0.0      # 平均の事後平均
        sigma_sq: float = 1.0  # 平均の事後分散
        n: int = 0           # 観測数

    def __init__(self, arm_ids: List[str], prior_sigma: float = 1.0):
        self.state = {arm: self.GaussianState() for arm in arm_ids}
        self.prior_sigma = prior_sigma
        self.arm_ids = arm_ids

    def sample_allocation(self, n_samples: int = 10000) -> Dict[str, float]:
        """
        Gaussianサンプリングで配信比率を決定
        """
        scores = {}

        for arm, s in self.state.items():
            # 事後分布 N(mu, sigma_sq) からサンプル
            score = np.random.normal(s.mu, np.sqrt(s.sigma_sq), size=n_samples).mean()
            scores[arm] = score

        # スコアを正規化（負の値も考慮）
        min_score = min(scores.values())
        if min_score < 0:
            scores = {arm: val - min_score for arm, val in scores.items()}

        total = sum(scores.values())
        if total > 0:
            return {arm: val / total for arm, val in scores.items()}
        else:
            return {arm: 1.0 / len(self.arm_ids) for arm in self.arm_ids}

    def update(self, outcomes: List[Tuple[str, float]]):
        """
        Gaussian報酬で更新

        Args:
            outcomes: [(arm_id, reward), ...] where reward is continuous
        """
        for arm_id, reward in outcomes:
            if arm_id not in self.state:
                continue

            s = self.state[arm_id]

            # Bayesian更新（既知分散と仮定）
            s.n += 1
            old_mu = s.mu
            s.mu = (s.mu * (s.n - 1) + reward) / s.n
            s.sigma_sq = self.prior_sigma**2 / s.n  # simplified

    def get_state(self) -> Dict[str, Dict[str, float]]:
        result = {}

        for arm, s in self.state.items():
            result[arm] = {
                "mu": s.mu,
                "sigma_sq": s.sigma_sq,
                "n": s.n,
                "ci_lower": s.mu - 1.96 * np.sqrt(s.sigma_sq),
                "ci_upper": s.mu + 1.96 * np.sqrt(s.sigma_sq)
            }

        return result
