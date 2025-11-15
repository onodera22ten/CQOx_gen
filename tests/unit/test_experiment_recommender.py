"""
Unit tests for experiment recommender
"""
import pytest
import pandas as pd
import numpy as np
from cqox.causal.policy.experiment_recommender import (
    ExperimentDesignRecommender,
    recommend_sample_size,
    recommend_stratification
)


@pytest.fixture
def sample_data():
    """Generate sample data"""
    np.random.seed(42)
    n = 1000

    df = pd.DataFrame({
        'X1': np.random.normal(0, 1, n),
        'X2': np.random.normal(0, 1, n),
        'X3': np.random.choice(['A', 'B', 'C'], n),
        'segment': np.random.choice(['high', 'medium', 'low'], n)
    })

    return df


def test_experiment_recommender_init():
    """Test recommender initialization"""
    recommender = ExperimentDesignRecommender(mode='rule_based')
    assert recommender.mode == 'rule_based'


def test_recommend_sample_size():
    """Test sample size recommendation"""
    result = recommend_sample_size(
        mde=0.05,
        baseline_rate=0.1,
        power=0.8,
        alpha=0.05
    )

    assert 'total_sample_size' in result
    assert 'treatment_size' in result
    assert 'control_size' in result
    assert result['total_sample_size'] > 0


def test_recommend_stratification(sample_data):
    """Test stratification recommendation"""
    result = recommend_stratification(
        sample_data,
        outcome_col=None,
        stratify_cols=['segment', 'X3']
    )

    assert 'stratification_recommended' in result
    assert 'strata' in result
    assert isinstance(result['strata'], list)


def test_recommender_rule_based(sample_data):
    """Test rule-based recommendations"""
    recommender = ExperimentDesignRecommender(mode='rule_based')

    recommendations = recommender.recommend(
        data=sample_data,
        mde=0.05,
        power=0.8
    )

    assert 'sample_size' in recommendations
    assert 'stratification' in recommendations
    assert 'duration_weeks' in recommendations
