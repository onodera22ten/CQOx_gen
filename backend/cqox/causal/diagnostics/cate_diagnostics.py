"""
CATE (Conditional Average Treatment Effect) diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from scipy.stats import spearmanr, pearsonr
from loguru import logger


def cate_distribution_analysis(cate: np.ndarray) -> Dict[str, Any]:
    """
    Analyze CATE distribution

    Args:
        cate: CATE estimates

    Returns:
        Distribution statistics
    """
    logger.info("Analyzing CATE distribution")

    result = {
        'mean': float(np.mean(cate)),
        'std': float(np.std(cate)),
        'min': float(np.min(cate)),
        'max': float(np.max(cate)),
        'median': float(np.median(cate)),
        'q25': float(np.percentile(cate, 25)),
        'q75': float(np.percentile(cate, 75)),
        'negative_share': float((cate < 0).mean()),
        'positive_share': float((cate > 0).mean()),
        'histogram': {
            'bins': 20,
            'counts': np.histogram(cate, bins=20)[0].tolist(),
            'edges': np.histogram(cate, bins=20)[1].tolist()
        }
    }

    logger.info(f"CATE mean: {result['mean']:.2f}, negative share: {result['negative_share']:.1%}")

    return result


def qini_curve_data(
    cate: np.ndarray,
    treatment: pd.Series,
    y: pd.Series
) -> Dict[str, Any]:
    """
    Calculate Qini curve data

    Qini curve shows cumulative uplift as a function of targeting fraction

    Args:
        cate: CATE estimates
        treatment: Treatment assignment
        y: Outcomes

    Returns:
        Qini curve data
    """
    logger.info("Calculating Qini curve")

    treatment_array = np.asarray(treatment)
    y_array = np.asarray(y)

    # Sort by CATE (descending)
    sorted_idx = np.argsort(-cate)

    cate_sorted = cate[sorted_idx]
    treatment_sorted = treatment_array[sorted_idx]
    y_sorted = y_array[sorted_idx]

    n = len(cate)
    fractions = np.linspace(0, 1, 21)

    qini_values = []
    random_values = []

    for frac in fractions:
        n_targeted = int(n * frac)

        if n_targeted == 0:
            qini_values.append(0.0)
            random_values.append(0.0)
            continue

        # Uplift in targeted population
        targeted_treated = treatment_sorted[:n_targeted] == 1
        targeted_control = treatment_sorted[:n_targeted] == 0

        if targeted_treated.sum() > 0 and targeted_control.sum() > 0:
            uplift_targeted = (
                y_sorted[:n_targeted][targeted_treated].mean() -
                y_sorted[:n_targeted][targeted_control].mean()
            )
        else:
            uplift_targeted = 0.0

        qini = uplift_targeted * n_targeted
        qini_values.append(float(qini))

        # Random targeting baseline
        random_uplift = np.mean(y_sorted[treatment_sorted == 1]) - np.mean(y_sorted[treatment_sorted == 0])
        random_values.append(float(random_uplift * n_targeted))

    # Calculate area under Qini curve
    auqc = np.trapz(qini_values, fractions)
    auqc_random = np.trapz(random_values, fractions)
    qini_coefficient = (auqc - auqc_random) / auqc_random if auqc_random != 0 else 0

    result = {
        'fractions': fractions.tolist(),
        'qini_values': qini_values,
        'random_values': random_values,
        'auqc': float(auqc),
        'qini_coefficient': float(qini_coefficient)
    }

    logger.info(f"Qini coefficient: {qini_coefficient:.3f}")

    return result


def calibration_analysis(
    predicted_cate: np.ndarray,
    observed_outcomes_treated: np.ndarray,
    observed_outcomes_control: np.ndarray,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calibration analysis: predicted CATE vs observed uplift

    Args:
        predicted_cate: Predicted CATE values
        observed_outcomes_treated: Observed outcomes for treated units
        observed_outcomes_control: Observed outcomes for control units
        n_bins: Number of calibration bins

    Returns:
        Calibration data
    """
    logger.info("Running calibration analysis")

    # Bin predicted CATE
    bins = np.percentile(predicted_cate, np.linspace(0, 100, n_bins + 1))
    bin_indices = np.digitize(predicted_cate, bins[1:-1])

    predicted_by_bin = []
    observed_by_bin = []
    bin_centers = []

    for i in range(n_bins):
        mask = bin_indices == i

        if mask.sum() > 0:
            pred_mean = predicted_cate[mask].mean()

            # This is simplified - in practice need to match treated/control
            # within each bin
            obs_mean = pred_mean  # Placeholder

            predicted_by_bin.append(float(pred_mean))
            observed_by_bin.append(float(obs_mean))
            bin_centers.append(float(bins[i:i+2].mean()))

    # Calibration slope (ideally = 1)
    if len(predicted_by_bin) > 1:
        correlation = pearsonr(predicted_by_bin, observed_by_bin)[0]
    else:
        correlation = 0.0

    result = {
        'bin_centers': bin_centers,
        'predicted_means': predicted_by_bin,
        'observed_means': observed_by_bin,
        'calibration_correlation': float(correlation),
        'n_bins': n_bins
    }

    logger.info(f"Calibration correlation: {correlation:.3f}")

    return result


def calibration_check(
    cate: np.ndarray,
    treatment: pd.Series,
    y: pd.Series,
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    CATE キャリブレーションチェック
    - CATE の分位でビン分割し、
      「予測 CATE の平均」と「実測 uplift (treated vs control の平均差)」の
      線形回帰の R^2 を返す。

    戻り値例:
        {
            "r_squared": 0.85,
            "slope": 0.9,
            "intercept": 0.01,
            "bin_data": [...],
        }
    """
    logger.info("Running CATE calibration check")

    cate_arr = np.asarray(cate)
    treat_arr = np.asarray(treatment)
    y_arr = np.asarray(y)

    n = len(cate_arr)
    if not (len(treat_arr) == len(y_arr) == n):
        raise ValueError(
            f"Length mismatch: cate={len(cate_arr)}, "
            f"treatment={len(treat_arr)}, y={len(y_arr)}"
        )

    # CATE の分位でビンに切る（均等サイズ）
    order = np.argsort(cate_arr)
    cate_sorted = cate_arr[order]
    treat_sorted = treat_arr[order]
    y_sorted = y_arr[order]

    bins = np.array_split(np.arange(n), n_bins)

    pred_uplift = []
    obs_uplift = []
    bin_data = []

    for idxs in bins:
        if len(idxs) == 0:
            continue

        c_bin = cate_sorted[idxs]
        t_bin = treat_sorted[idxs]
        y_bin = y_sorted[idxs]

        # 予測 uplift = そのビンの平均 CATE
        pred = float(c_bin.mean())

        mask_t = t_bin == 1
        mask_c = t_bin == 0
        if mask_t.sum() == 0 or mask_c.sum() == 0:
            # どちらかが無いビンはスキップ（不安定なため）
            continue

        # 実測 uplift = treated と control の平均差
        obs = float(y_bin[mask_t].mean() - y_bin[mask_c].mean())

        pred_uplift.append(pred)
        obs_uplift.append(obs)

        bin_data.append(
            {
                "bin_size": int(len(idxs)),
                "pred_uplift": pred,
                "obs_uplift": obs,
                "cate_min": float(c_bin.min()),
                "cate_max": float(c_bin.max()),
            }
        )

    if len(pred_uplift) < 2:
        logger.warning("Not enough bins for calibration regression; returning r_squared=0")
        return {
            "r_squared": 0.0,
            "slope": 0.0,
            "intercept": float(np.mean(obs_uplift) if obs_uplift else 0.0),
            "bin_data": bin_data,
        }

    x = np.array(pred_uplift)
    y_obs = np.array(obs_uplift)

    # 実測 uplift ~ 予測 uplift の単回帰
    slope, intercept = np.polyfit(x, y_obs, deg=1)
    y_pred = slope * x + intercept

    ss_res = float(np.sum((y_obs - y_pred) ** 2))
    ss_tot = float(np.sum((y_obs - y_obs.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    result = {
        "r_squared": float(r_squared),
        "slope": float(slope),
        "intercept": float(intercept),
        "bin_data": bin_data,
    }

    logger.info(f"CATE calibration R^2: {r_squared:.3f}")
    return result


def cate_heterogeneity_test(
    cate: np.ndarray,
    X: pd.DataFrame,
    top_k: int = 10,
    corr_threshold: float = 0.1,
) -> Dict[str, Any]:
    """
    CATE の異質性（どの特徴量で uplift が変わるか）をざっくり評価する。

    - 各特徴量と CATE の Spearman 相関を計算
    - |corr| が閾値を超える特徴量があれば「有意な異質性あり」とみなす
    """
    logger.info("Running CATE heterogeneity test")

    cate_arr = np.asarray(cate)
    feature_corrs = []

    for col in X.columns:
        try:
            x_col = np.asarray(X[col])
            # 欠損を素朴に除外（高級な処理は後で）
            mask = ~np.isnan(cate_arr) & ~np.isnan(x_col)
            if mask.sum() < 10:
                continue

            corr, pval = spearmanr(cate_arr[mask], x_col[mask])
            feature_corrs.append(
                {
                    "feature": col,
                    "spearman_corr": float(corr),
                    "p_value": float(pval),
                }
            )
        except Exception as e:
            logger.warning(f"Skipping feature {col} in heterogeneity test: {e}")

    # 相関の絶対値でソート
    feature_corrs.sort(key=lambda d: abs(d["spearman_corr"]), reverse=True)

    top_features = feature_corrs[:top_k]
    significant = any(abs(f["spearman_corr"]) >= corr_threshold for f in feature_corrs)

    result = {
        "significant": bool(significant),
        "corr_threshold": float(corr_threshold),
        "top_features": top_features,
        "n_features_tested": len(feature_corrs),
    }

    logger.info(
        f"Heterogeneity significant={significant}, "
        f"top feature corr={top_features[0]['spearman_corr'] if top_features else 'NA'}"
    )

    return result

