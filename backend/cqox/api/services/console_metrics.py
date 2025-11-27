"""
Console metrics calculation utilities (Viz.pdf仕様準拠)
"""
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta


def compute_cvar(delta_values: List[float], alpha: float = 0.1) -> float:
    """
    Compute CVaR (Conditional Value at Risk) - Worst alpha% average

    Args:
        delta_values: List of delta_yen values
        alpha: Percentile threshold (default: 0.1 for worst 10%)

    Returns:
        CVaR value (average of worst alpha%)
    """
    if not delta_values:
        return 0.0

    sorted_vals = np.sort(delta_values)
    cutoff_index = max(1, int(len(sorted_vals) * alpha))
    worst_tail = sorted_vals[:cutoff_index]

    return float(np.mean(worst_tail))


def assign_bcg_quadrant(
    incremental_clv: float,
    user_count: int,
    clv_threshold: float,
    size_threshold: float
) -> str:
    """
    Assign BCG Matrix quadrant based on CLV and segment size

    Args:
        incremental_clv: Incremental CLV per user
        user_count: Segment population
        clv_threshold: Threshold for "High CLV" (e.g., 70th percentile)
        size_threshold: Threshold for "Large Size" (e.g., 70th percentile)

    Returns:
        BCG quadrant: "Star", "Volume", "Niche", or "Low"
    """
    if incremental_clv >= clv_threshold and user_count >= size_threshold:
        return "Star"
    elif incremental_clv >= clv_threshold and user_count < size_threshold:
        return "Niche"
    elif incremental_clv < clv_threshold and user_count >= size_threshold:
        return "Volume"
    else:
        return "Low"


def compute_bcg_thresholds(
    segments: List[Dict[str, Any]],
    percentile: float = 0.7
) -> tuple[float, float]:
    """
    Compute BCG thresholds (70th percentile by default)

    Args:
        segments: List of segment dictionaries with 'incremental_clv' and 'user_count'
        percentile: Percentile to use for threshold (default: 0.7)

    Returns:
        (clv_threshold, size_threshold)
    """
    if not segments:
        return (0.0, 0)

    clv_vals = [s['incremental_clv'] for s in segments if s.get('incremental_clv') is not None]
    size_vals = [s['user_count'] for s in segments if s.get('user_count') is not None]

    clv_threshold = float(np.percentile(clv_vals, percentile * 100)) if clv_vals else 0.0
    size_threshold = int(np.percentile(size_vals, percentile * 100)) if size_vals else 0

    return (clv_threshold, size_threshold)


def compute_iso_week(dt: datetime) -> str:
    """
    Compute ISO week string from datetime

    Args:
        dt: Datetime object

    Returns:
        ISO week string: "2025-W48"
    """
    iso_calendar = dt.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"


def resolve_date_range(window: str) -> tuple[datetime, datetime]:
    """
    Resolve date range from window parameter

    Args:
        window: "14d", "28d", or "56d"

    Returns:
        (from_date, to_date)
    """
    to_date = datetime.utcnow()

    if window == "14d":
        from_date = to_date - timedelta(days=14)
    elif window == "28d":
        from_date = to_date - timedelta(days=28)
    elif window == "56d":
        from_date = to_date - timedelta(days=56)
    else:
        # Default to 28d
        from_date = to_date - timedelta(days=28)

    return (from_date, to_date)
