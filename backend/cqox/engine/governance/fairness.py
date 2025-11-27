"""
V2 Module D: Fairness & Governance Checker
V2.pdf Page 6-7 仕様準拠 - フェアネス監視・データ品質・制約チェック
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ViolationSeverity(str, Enum):
    """違反の重大度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(str, Enum):
    """違反時のアクション"""
    WARN = "warn"
    BLOCK = "block"
    REVIEW = "review"


@dataclass
class GovernanceRule:
    """ガバナンスルール定義"""
    rule_id: str
    rule_name: str
    rule_type: str  # "fairness" | "data_quality" | "compliance"
    sensitive_attributes: List[str]
    threshold_value: float
    action: RuleAction
    enabled: bool = True


@dataclass
class Violation:
    """違反レコード"""
    rule_id: str
    violation_type: str
    severity: ViolationSeverity
    details: Dict
    affected_groups: Optional[List[str]] = None


class FairnessChecker:
    """
    フェアネスチェッカー

    V2.pdf Page 7:
    - Absolute Uplift Disparity: |ΔY_male - ΔY_female|
    - 閾値を超えた場合、施策を「要レビュー」にする
    """

    def __init__(self, threshold: float = 1000.0):
        """
        Args:
            threshold: フェアネス違反とみなす閾値（Δ¥の差分）
        """
        self.threshold = threshold

    def check_uplift_disparity(
        self,
        df_uplift: pd.DataFrame,
        sensitive_col: str,
        group_a: str,
        group_b: str
    ) -> Optional[Violation]:
        """
        Uplift Disparityをチェック

        Args:
            df_uplift: uplift推定結果 (columns: [delta_yen, sensitive_col])
            sensitive_col: 保護属性の列名（例: "gender", "age_group"）
            group_a: グループA識別子（例: "male"）
            group_b: グループB識別子（例: "female"）

        Returns:
            違反があればViolationオブジェクト、なければNone
        """
        if sensitive_col not in df_uplift.columns:
            return None

        df_a = df_uplift[df_uplift[sensitive_col] == group_a]
        df_b = df_uplift[df_uplift[sensitive_col] == group_b]

        if len(df_a) == 0 or len(df_b) == 0:
            return None

        mean_uplift_a = df_a["delta_yen"].mean()
        mean_uplift_b = df_b["delta_yen"].mean()

        disparity = abs(mean_uplift_a - mean_uplift_b)

        if disparity > self.threshold:
            severity = ViolationSeverity.HIGH if disparity > self.threshold * 2 else ViolationSeverity.MEDIUM

            return Violation(
                rule_id="fairness_uplift_disparity",
                violation_type="fairness",
                severity=severity,
                details={
                    "sensitive_attribute": sensitive_col,
                    "group_a": group_a,
                    "group_b": group_b,
                    "mean_uplift_a": float(mean_uplift_a),
                    "mean_uplift_b": float(mean_uplift_b),
                    "disparity": float(disparity),
                    "threshold": self.threshold
                },
                affected_groups=[group_a, group_b]
            )

        return None

    def check_multiple_attributes(
        self,
        df_uplift: pd.DataFrame,
        sensitive_attributes: Dict[str, List[str]]
    ) -> List[Violation]:
        """
        複数の保護属性をチェック

        Args:
            df_uplift: uplift結果
            sensitive_attributes: {attr_name: [group_a, group_b], ...}

        Returns:
            違反リスト
        """
        violations = []

        for attr, groups in sensitive_attributes.items():
            if len(groups) < 2:
                continue

            for i in range(len(groups) - 1):
                violation = self.check_uplift_disparity(
                    df_uplift, attr, groups[i], groups[i + 1]
                )
                if violation:
                    violations.append(violation)

        return violations


class DataQualityChecker:
    """
    データ品質チェッカー

    V2.pdf Page 7:
    - リーク検出
    - 極端な外れ値
    - サンプル数不足
    """

    def check_sample_size(self, df: pd.DataFrame, min_samples: int = 100) -> Optional[Violation]:
        """サンプル数チェック"""
        if len(df) < min_samples:
            return Violation(
                rule_id="data_quality_sample_size",
                violation_type="data_quality",
                severity=ViolationSeverity.HIGH,
                details={
                    "actual_samples": len(df),
                    "required_samples": min_samples
                }
            )
        return None

    def check_outliers(
        self,
        df: pd.DataFrame,
        column: str,
        iqr_multiplier: float = 3.0
    ) -> Optional[Violation]:
        """外れ値検出（IQR法）"""
        if column not in df.columns:
            return None

        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - iqr_multiplier * IQR
        upper_bound = Q3 + iqr_multiplier * IQR

        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

        if len(outliers) > 0:
            outlier_ratio = len(outliers) / len(df)

            if outlier_ratio > 0.05:  # 5%以上が外れ値
                return Violation(
                    rule_id="data_quality_outliers",
                    violation_type="data_quality",
                    severity=ViolationSeverity.MEDIUM,
                    details={
                        "column": column,
                        "outlier_count": len(outliers),
                        "outlier_ratio": float(outlier_ratio),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound)
                    }
                )

        return None

    def check_data_leakage(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        feature_cols: List[str]
    ) -> List[Violation]:
        """
        データリーク検出（相関チェック）

        アウトカムと特徴量の相関が異常に高い場合、リークの可能性
        """
        violations = []

        for feat in feature_cols:
            if feat not in df.columns:
                continue

            corr = df[[outcome_col, feat]].corr().iloc[0, 1]

            if abs(corr) > 0.95:  # 95%以上の相関
                violations.append(Violation(
                    rule_id="data_quality_leakage",
                    violation_type="data_quality",
                    severity=ViolationSeverity.CRITICAL,
                    details={
                        "feature": feat,
                        "outcome": outcome_col,
                        "correlation": float(corr)
                    }
                ))

        return violations


class ComplianceChecker:
    """
    コンプライアンスチェッカー

    V2.pdf Page 7:
    - 特定セグメントへの広告頻度制限
    - 未成年への配信制約
    - GDPR/CCPA対応
    """

    def check_frequency_cap(
        self,
        user_exposures: Dict[str, int],
        max_frequency: int = 10
    ) -> List[Violation]:
        """
        配信頻度制限チェック

        Args:
            user_exposures: {user_id: exposure_count}
            max_frequency: 最大配信回数

        Returns:
            違反リスト
        """
        violations = []

        for user_id, count in user_exposures.items():
            if count > max_frequency:
                violations.append(Violation(
                    rule_id="compliance_frequency_cap",
                    violation_type="compliance",
                    severity=ViolationSeverity.MEDIUM,
                    details={
                        "user_id": user_id,
                        "exposure_count": count,
                        "max_frequency": max_frequency
                    }
                ))

        return violations

    def check_age_restriction(
        self,
        df: pd.DataFrame,
        age_col: str = "age",
        min_age: int = 18
    ) -> Optional[Violation]:
        """
        年齢制限チェック

        Args:
            df: ユーザーデータ
            age_col: 年齢列
            min_age: 最低年齢

        Returns:
            違反があればViolation
        """
        if age_col not in df.columns:
            return None

        under_age = df[df[age_col] < min_age]

        if len(under_age) > 0:
            return Violation(
                rule_id="compliance_age_restriction",
                violation_type="compliance",
                severity=ViolationSeverity.CRITICAL,
                details={
                    "under_age_count": len(under_age),
                    "min_age": min_age,
                    "affected_users": under_age.index.tolist()[:10]  # 最初の10件
                }
            )

        return None
