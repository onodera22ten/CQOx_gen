"""
Network interference and spillover diagnostics
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from loguru import logger


def network_spillover_analysis(
    treatment: pd.Series,
    network_matrix: Optional[np.ndarray] = None,
    k_neighbors: int = 5
) -> Dict[str, Any]:
    """
    Analyze network spillover effects

    Tests whether treatment of neighbors affects outcomes

    Args:
        treatment: Treatment assignment
        network_matrix: Adjacency matrix (if available)
        k_neighbors: Number of neighbors to consider

    Returns:
        Spillover statistics
    """
    logger.info("Analyzing network spillover")

    n = len(treatment)

    if network_matrix is None:
        # Create simple k-nearest neighbor network based on indices
        logger.warning("No network matrix provided, using sequential neighbors")
        neighbor_treatment_rate = []

        for i in range(n):
            # Get k neighbors (before and after)
            start = max(0, i - k_neighbors // 2)
            end = min(n, i + k_neighbors // 2 + 1)
            neighbors = list(range(start, end))
            neighbors.remove(i)

            if neighbors:
                neighbor_rate = treatment.iloc[neighbors].mean()
            else:
                neighbor_rate = 0.0

            neighbor_treatment_rate.append(neighbor_rate)

        neighbor_treatment_rate = np.array(neighbor_treatment_rate)
    else:
        # Use provided network matrix
        neighbor_treatment_rate = network_matrix @ treatment.values / network_matrix.sum(axis=1)

    result = {
        'mean_neighbor_treatment_rate': float(neighbor_treatment_rate.mean()),
        'std_neighbor_treatment_rate': float(neighbor_treatment_rate.std()),
        'correlation_with_own_treatment': float(np.corrcoef(treatment, neighbor_treatment_rate)[0, 1]),
        'high_spillover_share': float((neighbor_treatment_rate > 0.5).mean()),
        'isolated_units_share': float((neighbor_treatment_rate == 0).mean())
    }

    logger.info(f"Mean neighbor treatment rate: {result['mean_neighbor_treatment_rate']:.2%}")

    return result


def temporal_interference_check(
    treatment: pd.Series,
    time: pd.Series,
    window_days: int = 7
) -> Dict[str, Any]:
    """
    Check for temporal interference (treatment spillover over time)

    Args:
        treatment: Treatment assignment
        time: Timestamp
        window_days: Time window for interference

    Returns:
        Temporal interference statistics
    """
    logger.info("Checking temporal interference")

    # Sort by time
    df = pd.DataFrame({'treatment': treatment, 'time': pd.to_datetime(time)})
    df = df.sort_values('time')

    # For each unit, count treatments in preceding window
    df['preceding_treatments'] = 0

    for i in range(len(df)):
        current_time = df.iloc[i]['time']
        window_start = current_time - pd.Timedelta(days=window_days)

        preceding_mask = (df['time'] >= window_start) & (df['time'] < current_time)
        df.iloc[i, df.columns.get_loc('preceding_treatments')] = df.loc[preceding_mask, 'treatment'].sum()

    result = {
        'mean_preceding_treatments': float(df['preceding_treatments'].mean()),
        'max_preceding_treatments': int(df['preceding_treatments'].max()),
        'units_with_preceding_treatment': int((df['preceding_treatments'] > 0).sum()),
        'share_with_preceding_treatment': float((df['preceding_treatments'] > 0).mean())
    }

    logger.info(f"Units with preceding treatment: {result['share_with_preceding_treatment']:.1%}")

    return result
    
def network_spillover_test(
    network_ids: np.ndarray,
    treatment: np.ndarray,
    y: np.ndarray,
    corr_threshold: float = 0.2,
) -> Dict[str, Any]:
    """
    ネットワーク干渉（spil lover）の簡易チェック。

    - ネットワークごとに「treatment 割合」と
      「control ユーザの平均アウトカム」を計算。
    - 各ユニットに所属ネットワークの treat_rate を割り当て、
      control ユニットについて
      treat_rate とアウトカムの相関を見る。
    """
    logger.info("Running network spillover test")

    network_ids = np.asarray(network_ids)
    treatment = np.asarray(treatment)
    y = np.asarray(y)

    if not (len(network_ids) == len(treatment) == len(y)):
        raise ValueError(
            f"Length mismatch: network_ids={len(network_ids)}, "
            f"treatment={len(treatment)}, y={len(y)}"
        )

    df = pd.DataFrame(
        {"network_id": network_ids, "treatment": treatment, "y": y}
    )

    # ネットワーク単位 summary
    g = df.groupby("network_id")
    treat_rate = g["treatment"].mean()
    mean_y_control = g.apply(
        lambda d: d.loc[d["treatment"] == 0, "y"].mean()
        if (d["treatment"] == 0).any()
        else np.nan
    )

    # control ユーザだけ取り出して、そのネットワークの treat_rate を付与
    df_control = df[df["treatment"] == 0].copy()
    df_control = df_control.join(
        treat_rate.rename("network_treat_rate"),
        on="network_id",
    )

    df_control = df_control.dropna(subset=["network_treat_rate", "y"])
    n_control = len(df_control)

    if n_control < 10:
        # サンプルが少なすぎる場合はテスト不能扱い
        logger.warning("Too few control units for spillover test; returning neutral result")
        return {
            "no_spillover": True,
            "corr": 0.0,
            "n_control": n_control,
            "note": "insufficient control sample; test not reliable",
        }

    x = df_control["network_treat_rate"].to_numpy()
    y_ctrl = df_control["y"].to_numpy()

    corr = float(np.corrcoef(x, y_ctrl)[0, 1])
    no_spillover = abs(corr) < corr_threshold

    result = {
        "no_spillover": bool(no_spillover),
        "corr": corr,
        "corr_threshold": float(corr_threshold),
        "n_control": int(n_control),
        "n_networks": int(len(treat_rate)),
    }

    logger.info(
        f"Network spillover test: corr={corr:.3f}, "
        f"threshold={corr_threshold}, no_spillover={no_spillover}"
    )
    return result


def temporal_interference_test(
    time: np.ndarray,
    treatment: np.ndarray,
    y: np.ndarray,
    corr_threshold: float = 0.2,
) -> Dict[str, Any]:
    """
    時間干渉（temporal interference）の簡易チェック。

    - 時間ごとに treatment 割合と
      control ユーザの平均アウトカムを集計。
    - それらの相関を見ることで、
      「ある時点の control アウトカムが同時期の treat 密度に
      強く影響されていないか」をチェックする。
    """
    logger.info("Running temporal interference test")

    time = np.asarray(time)
    treatment = np.asarray(treatment)
    y = np.asarray(y)

    if not (len(time) == len(treatment) == len(y)):
        raise ValueError(
            f"Length mismatch: time={len(time)}, "
            f"treatment={len(treatment)}, y={len(y)}"
        )

    df = pd.DataFrame({"time": time, "treatment": treatment, "y": y})

    g = df.groupby("time")
    treat_rate_t = g["treatment"].mean()
    mean_y_control_t = g.apply(
        lambda d: d.loc[d["treatment"] == 0, "y"].mean()
        if (d["treatment"] == 0).any()
        else np.nan
    ).dropna()

    # 両方に共通に存在する time のみに揃える
    common_times = mean_y_control_t.index.intersection(treat_rate_t.index)
    if len(common_times) < 3:
        logger.warning("Too few time points for temporal interference test; returning neutral result")
        return {
            "no_interference": True,
            "corr": 0.0,
            "n_time_points": int(len(common_times)),
            "note": "insufficient time points; test not reliable",
        }

    x = treat_rate_t.loc[common_times].to_numpy()
    y_ctrl_t = mean_y_control_t.loc[common_times].to_numpy()

    corr = float(np.corrcoef(x, y_ctrl_t)[0, 1])
    no_interference = abs(corr) < corr_threshold

    result = {
        "no_interference": bool(no_interference),
        "corr": corr,
        "corr_threshold": float(corr_threshold),
        "n_time_points": int(len(common_times)),
    }

    logger.info(
        f"Temporal interference test: corr={corr:.3f}, "
        f"threshold={corr_threshold}, no_interference={no_interference}"
    )
    return result
