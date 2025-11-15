"""
Quality Gate Logic for v1 API

品質ゲート: 2段階判定
- レベル1: API 400エラー（契約違反・識別不能 → 走らない）
- レベル2: UI 赤札（DecisionCard verdict = Hold → 走るが採用不可）
"""
from typing import Literal, Optional, Tuple
from decimal import Decimal
from fastapi import HTTPException


class QualityGate:
    """品質ゲート判定"""

    # レベル1: API 400エラー閾値
    MIN_SAMPLE_SIZE = 1000

    # レベル2: UI 赤札（Hold）閾値
    MIN_OVERLAP_COVERAGE = 0.8
    MIN_IV_F_STAT = 10.0
    MAX_RD_MCCRARY_P = 0.05
    MIN_BALANCE_SCORE = 0.7

    # Canary判定閾値
    MAX_RELATIVE_CI_WIDTH = 0.5  # CI幅が期待値の50%以下ならGo

    @staticmethod
    def validate_contract(
        dataset: dict,
        required_sets: list[list[str]]
    ) -> Tuple[bool, list[str]]:
        """
        Data Contract検証（レベル1）

        Args:
            dataset: データセット（カラム名のリスト）
            required_sets: 必須カラムセットのリスト
                例: [["y", "treatment"], ["unit_id", "time"]]

        Returns:
            (ok, missing): 検証結果と欠損カラムリスト

        Raises:
            HTTPException(400): 契約違反
        """
        available_columns = set(dataset.get("columns", []))
        missing_columns = []

        for required_set in required_sets:
            for col in required_set:
                if col not in available_columns:
                    missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Data Contract violation: missing columns {missing_columns}"
            )

        return True, []

    @staticmethod
    def validate_sample_size(sample_size: int) -> None:
        """
        サンプルサイズ検証（レベル1）

        Args:
            sample_size: サンプルサイズ

        Raises:
            HTTPException(400): サンプルサイズ不足
        """
        if sample_size < QualityGate.MIN_SAMPLE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient sample size: {sample_size} < {QualityGate.MIN_SAMPLE_SIZE}"
            )

    @staticmethod
    def validate_types(dataset: dict) -> None:
        """
        型エラー検証（レベル1）

        Args:
            dataset: データセット

        Raises:
            HTTPException(400): 型エラー
        """
        # 簡易チェック（実際はPandasで型チェック）
        if "y_type" in dataset and dataset["y_type"] not in ["float", "int"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid y type: {dataset['y_type']} (must be numeric)"
            )

        if "treatment_type" in dataset and dataset["treatment_type"] != "binary":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid treatment type: {dataset['treatment_type']} (must be binary)"
            )

    @staticmethod
    def determine_verdict(
        delta_yen: Decimal,
        delta_yen_ci_low: Decimal,
        delta_yen_ci_high: Decimal,
        quality_scores: dict,
        estimator_type: str = "DR"
    ) -> Tuple[Literal["Go", "Canary", "Hold"], Optional[str]]:
        """
        DecisionCard の verdict を決定（レベル2）

        Args:
            delta_yen: Δ¥期待値
            delta_yen_ci_low: 95%CI下限
            delta_yen_ci_high: 95%CI上限
            quality_scores: 品質スコア辞書
            estimator_type: 推定器タイプ

        Returns:
            (verdict, reason): 判定と理由
        """
        # レベル2: 品質不合格 → Hold
        overlap_coverage = quality_scores.get("overlap_coverage", 1.0)
        iv_f_stat = quality_scores.get("iv_f_stat", 100.0)
        rd_mccrary_p = quality_scores.get("rd_mccrary_p", 1.0)
        balance_score = quality_scores.get("balance_score", 1.0)

        # Overlap低 → Hold
        if overlap_coverage < QualityGate.MIN_OVERLAP_COVERAGE:
            return "Hold", f"Overlap低 {overlap_coverage:.2f} → 識別不可（外挿リスク高）"

        # IV弱 → Hold（IV推定の場合のみ）
        if estimator_type == "IV" and iv_f_stat < QualityGate.MIN_IV_F_STAT:
            return "Hold", f"IV弱 F={iv_f_stat:.1f} → 識別不可（操作変数が弱い）"

        # RD品質不合格 → Hold（RD推定の場合のみ）
        if estimator_type == "RD" and rd_mccrary_p < QualityGate.MAX_RD_MCCRARY_P:
            return "Hold", f"RD品質不合格 p={rd_mccrary_p:.3f} → バイアス疑い（ソーティング検出）"

        # Balance不良 → Hold（DiD推定の場合のみ）
        if estimator_type == "DiD" and balance_score < QualityGate.MIN_BALANCE_SCORE:
            return "Hold", f"Balance不良 {balance_score:.2f} → DiD前提崩壊"

        # CI幅をチェック（相対幅）
        ci_width = float(delta_yen_ci_high - delta_yen_ci_low)
        delta_yen_float = float(delta_yen)
        relative_width = ci_width / abs(delta_yen_float) if delta_yen_float != 0 else float('inf')

        # Δ¥有意にプラス かつ CI幅狭い → Go
        if float(delta_yen_ci_low) > 0 and relative_width < QualityGate.MAX_RELATIVE_CI_WIDTH:
            return "Go", None

        # Δ¥プラスだがCI幅広い → Canary（A/Bテスト推奨）
        if delta_yen_float > 0:
            return "Canary", f"Δ¥プラスだがCI幅広い（相対幅 {relative_width:.1%}） → A/Bテスト推奨"

        # Δ¥ゼロまたはマイナス → Hold
        if delta_yen_float <= 0:
            return "Hold", f"Δ¥マイナス（{delta_yen_float:,.0f}円） → 実施非推奨"

        # デフォルト: Hold
        return "Hold", "判定不能"

    @staticmethod
    def check_quality_gate(
        delta_yen: Decimal,
        delta_yen_ci_low: Decimal,
        delta_yen_ci_high: Decimal,
        quality_scores: dict,
        estimator_type: str = "DR"
    ) -> dict:
        """
        品質ゲート総合チェック

        Args:
            delta_yen: Δ¥期待値
            delta_yen_ci_low: 95%CI下限
            delta_yen_ci_high: 95%CI上限
            quality_scores: 品質スコア辞書
            estimator_type: 推定器タイプ

        Returns:
            品質ゲート結果辞書
        """
        verdict, reason = QualityGate.determine_verdict(
            delta_yen,
            delta_yen_ci_low,
            delta_yen_ci_high,
            quality_scores,
            estimator_type
        )

        return {
            "passed": verdict == "Go",
            "verdict": verdict,
            "reason": reason,
            "quality_scores": quality_scores
        }


# Helper functions for specific estimator diagnostics

def check_overlap(propensity_scores: list[float], threshold: float = 0.1) -> dict:
    """
    Overlap（共通サポート領域）チェック

    Args:
        propensity_scores: 傾向スコアのリスト
        threshold: 端点閾値（デフォルト0.1 → [0.1, 0.9]が共通サポート）

    Returns:
        { overlap_coverage, trimmed_count }
    """
    import numpy as np

    ps_array = np.array(propensity_scores)
    n_total = len(ps_array)

    # 共通サポート領域: [threshold, 1-threshold]
    in_support = (ps_array >= threshold) & (ps_array <= 1 - threshold)
    n_in_support = np.sum(in_support)

    overlap_coverage = n_in_support / n_total if n_total > 0 else 0.0

    return {
        "overlap_coverage": float(overlap_coverage),
        "trimmed_count": int(n_total - n_in_support),
        "threshold": threshold
    }


def check_iv_strength(first_stage_f_stat: float) -> dict:
    """
    IV（操作変数）強度チェック

    Args:
        first_stage_f_stat: First-stage F統計量

    Returns:
        { iv_f_stat, is_weak }
    """
    is_weak = first_stage_f_stat < QualityGate.MIN_IV_F_STAT

    return {
        "iv_f_stat": float(first_stage_f_stat),
        "is_weak": is_weak,
        "threshold": QualityGate.MIN_IV_F_STAT
    }


def check_rd_manipulation(mccrary_p_value: float) -> dict:
    """
    RD（回帰不連続）操作チェック（McCraryテスト）

    Args:
        mccrary_p_value: McCraryテストp値

    Returns:
        { rd_mccrary_p, manipulation_detected }
    """
    manipulation_detected = mccrary_p_value < QualityGate.MAX_RD_MCCRARY_P

    return {
        "rd_mccrary_p": float(mccrary_p_value),
        "manipulation_detected": manipulation_detected,
        "threshold": QualityGate.MAX_RD_MCCRARY_P
    }


def check_balance(standardized_mean_differences: dict[str, float]) -> dict:
    """
    Balance（共変量バランス）チェック

    Args:
        standardized_mean_differences: 標準化平均差分の辞書 {covariate: smd}

    Returns:
        { balance_score, unbalanced_covariates }
    """
    import numpy as np

    if not standardized_mean_differences:
        return {"balance_score": 1.0, "unbalanced_covariates": []}

    smd_values = np.array(list(standardized_mean_differences.values()))

    # Balance score: バランス良好な共変量の割合
    # 通常、|SMD| < 0.1 が良好
    balanced = np.abs(smd_values) < 0.1
    balance_score = np.mean(balanced)

    unbalanced_covariates = [
        cov for cov, smd in standardized_mean_differences.items()
        if abs(smd) >= 0.1
    ]

    return {
        "balance_score": float(balance_score),
        "unbalanced_covariates": unbalanced_covariates,
        "mean_abs_smd": float(np.mean(np.abs(smd_values)))
    }
