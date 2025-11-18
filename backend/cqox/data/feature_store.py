"""
Feature engineering and feature store
"""
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger


class FeatureStore:
    """Feature store for managing feature engineering"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def compute_rfm_features(
        self,
        user_col: str = 'unit_id',
        time_col: str = 'time',
        monetary_col: str = 'y',
        reference_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Compute RFM (Recency, Frequency, Monetary) features

        Args:
            user_col: User ID column
            time_col: Timestamp column
            monetary_col: Monetary value column
            reference_date: Reference date for recency calculation

        Returns:
            DataFrame with RFM features per user
        """
        logger.info("Computing RFM features")

        if reference_date is None:
            reference_date = self.df[time_col].max()

        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(self.df[time_col]):
            df_rfm = self.df.copy()
            df_rfm[time_col] = pd.to_datetime(df_rfm[time_col])
        else:
            df_rfm = self.df

        # Compute RFM
        rfm = df_rfm.groupby(user_col).agg({
            time_col: lambda x: (reference_date - x.max()).days,  # Recency
            monetary_col: ['count', 'sum']  # Frequency, Monetary
        }).reset_index()

        rfm.columns = [user_col, 'X_rfm_recency', 'X_rfm_frequency', 'X_rfm_monetary']

        logger.info(f"Computed RFM features for {len(rfm)} users")
        return rfm

    def compute_behavioral_features(
        self,
        user_col: str = 'unit_id',
        time_col: str = 'time',
        lookback_days: int = 30
    ) -> pd.DataFrame:
        """
        Compute behavioral features (session count, activity patterns)

        Args:
            user_col: User ID column
            time_col: Timestamp column
            lookback_days: Number of days to look back

        Returns:
            DataFrame with behavioral features
        """
        logger.info("Computing behavioral features")

        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(self.df[time_col]):
            df_behavior = self.df.copy()
            df_behavior[time_col] = pd.to_datetime(df_behavior[time_col])
        else:
            df_behavior = self.df

        # Filter to lookback period
        cutoff_date = df_behavior[time_col].max() - timedelta(days=lookback_days)
        df_recent = df_behavior[df_behavior[time_col] >= cutoff_date]

        # Session count (number of distinct days)
        sessions = df_recent.groupby(user_col)[time_col].agg([
            ('X_session_count', lambda x: x.dt.date.nunique()),
            ('X_avg_events_per_day', 'count')
        ]).reset_index()

        sessions['X_avg_events_per_day'] = sessions['X_avg_events_per_day'] / lookback_days

        logger.info(f"Computed behavioral features for {len(sessions)} users")
        return sessions

    def compute_treatment_history(
        self,
        user_col: str = 'unit_id',
        treatment_col: str = 'treatment',
        time_col: str = 'time',
        lookback_days: int = 90
    ) -> pd.DataFrame:
        """
        Compute treatment history features

        Args:
            user_col: User ID column
            treatment_col: Treatment column
            time_col: Timestamp column
            lookback_days: Number of days to look back

        Returns:
            DataFrame with treatment history features
        """
        logger.info("Computing treatment history features")

        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(self.df[time_col]):
            df_treatment = self.df.copy()
            df_treatment[time_col] = pd.to_datetime(df_treatment[time_col])
        else:
            df_treatment = self.df

        # Filter to lookback period
        cutoff_date = df_treatment[time_col].max() - timedelta(days=lookback_days)
        df_recent = df_treatment[df_treatment[time_col] >= cutoff_date]

        # Treatment count
        treatment_counts = df_recent.groupby(user_col)[treatment_col].agg([
            ('X_treatment_count', 'sum'),
            ('X_treatment_rate', 'mean')
        ]).reset_index()

        # Days since last treatment
        last_treatment = df_recent[df_recent[treatment_col] == 1].groupby(user_col)[time_col].max()
        reference_date = df_treatment[time_col].max()
        days_since = (reference_date - last_treatment).dt.days
        days_since_df = days_since.reset_index()
        days_since_df.columns = [user_col, 'X_days_since_treatment']

        # Merge
        result = treatment_counts.merge(days_since_df, on=user_col, how='left')
        result['X_days_since_treatment'].fillna(999, inplace=True)

        logger.info(f"Computed treatment history for {len(result)} users")
        return result

    def build_feature_table(
        self,
        user_col: str = 'unit_id',
        time_col: str = 'time',
        monetary_col: str = 'y',
        treatment_col: str = 'treatment',
        static_features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Build comprehensive feature table

        Args:
            user_col: User ID column
            time_col: Timestamp column
            monetary_col: Monetary value column
            treatment_col: Treatment column
            static_features: List of static feature columns to include

        Returns:
            DataFrame with all features per user
        """
        logger.info("Building feature table")

        # Start with RFM features
        features = self.compute_rfm_features(user_col, time_col, monetary_col)

        # Add behavioral features
        behavioral = self.compute_behavioral_features(user_col, time_col)
        features = features.merge(behavioral, on=user_col, how='left')

        # Add treatment history
        if treatment_col in self.df.columns:
            treatment_history = self.compute_treatment_history(user_col, treatment_col, time_col)
            features = features.merge(treatment_history, on=user_col, how='left')

        # Add static features if specified
        if static_features:
            static_cols = [user_col] + [col for col in static_features if col in self.df.columns]
            static_df = self.df[static_cols].drop_duplicates(subset=[user_col])
            features = features.merge(static_df, on=user_col, how='left')

        logger.info(f"Built feature table with {len(features)} rows, {len(features.columns)} columns")
        return features


def create_time_based_features(
    df: pd.DataFrame,
    time_col: str = 'time'
) -> pd.DataFrame:
    """
    Create time-based features (hour, day of week, etc.)

    Args:
        df: Input DataFrame
        time_col: Timestamp column

    Returns:
        DataFrame with additional time features
    """
    df_time = df.copy()

    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df_time[time_col]):
        df_time[time_col] = pd.to_datetime(df_time[time_col])

    # Extract time features
    df_time['X_hour'] = df_time[time_col].dt.hour
    df_time['X_day_of_week'] = df_time[time_col].dt.dayofweek
    df_time['X_day_of_month'] = df_time[time_col].dt.day
    df_time['X_month'] = df_time[time_col].dt.month
    df_time['X_is_weekend'] = (df_time['X_day_of_week'] >= 5).astype(int)

    return df_time


def create_interaction_features(
    df: pd.DataFrame,
    feature_pairs: List[tuple]
) -> pd.DataFrame:
    """
    Create interaction features

    Args:
        df: Input DataFrame
        feature_pairs: List of (feature1, feature2) tuples

    Returns:
        DataFrame with interaction features
    """
    df_interact = df.copy()

    for feat1, feat2 in feature_pairs:
        if feat1 in df.columns and feat2 in df.columns:
            interaction_name = f"{feat1}_x_{feat2}"
            df_interact[interaction_name] = df[feat1] * df[feat2]

    return df_interact
