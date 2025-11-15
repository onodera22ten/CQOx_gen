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
