"""
Unit tests for causal estimators
"""
import pytest
import pandas as pd
import numpy as np
from cqox.causal.estimators.s_learner import SLearner
from cqox.causal.estimators.t_learner import TLearner
from cqox.causal.estimators.dr_learner import DRLearner


@pytest.fixture
def synthetic_data():
    """Generate synthetic data with known treatment effect"""
    np.random.seed(42)
    n = 1000

    # Features
    X = pd.DataFrame({
        'X1': np.random.normal(0, 1, n),
        'X2': np.random.normal(0, 1, n)
    })

    # Treatment (random assignment)
    treatment = pd.Series(np.random.binomial(1, 0.5, n))

    # True CATE = 10 + 2*X1
    true_cate = 10 + 2 * X['X1']

    # Outcome: Y = 100 + 5*X1 + 3*X2 + treatment * true_cate + noise
    y = pd.Series(
        100 + 5 * X['X1'] + 3 * X['X2'] +
        treatment * true_cate +
        np.random.normal(0, 1, n)
    )

    return X, treatment, y, true_cate


def test_s_learner_fit(synthetic_data):
    """Test S-Learner fitting"""
    X, treatment, y, _ = synthetic_data

    estimator = SLearner()
    estimator.fit(X, treatment, y)

    assert estimator.is_fitted
    assert estimator._model is not None


def test_s_learner_ate(synthetic_data):
    """Test S-Learner ATE estimation"""
    X, treatment, y, true_cate = synthetic_data

    estimator = SLearner()
    estimator.fit(X, treatment, y)

    ate = estimator.estimate_ate()

    # True ATE should be around 10 (mean of true_cate)
    assert isinstance(ate, float)
    assert 8 < ate < 12  # Allow some estimation error


def test_t_learner_fit(synthetic_data):
    """Test T-Learner fitting"""
    X, treatment, y, _ = synthetic_data

    estimator = TLearner()
    estimator.fit(X, treatment, y)

    assert estimator.is_fitted
    assert estimator.model_treat is not None
    assert estimator.model_control is not None


def test_dr_learner_fit(synthetic_data):
    """Test DR-Learner fitting"""
    X, treatment, y, _ = synthetic_data

    estimator = DRLearner()
    estimator.fit(X, treatment, y)

    assert estimator.is_fitted
    assert estimator.ps_model is not None
    assert estimator.mu1_model is not None
    assert estimator.mu0_model is not None


def test_cate_estimation(synthetic_data):
    """Test CATE estimation"""
    X, treatment, y, true_cate = synthetic_data

    estimator = SLearner()
    estimator.fit(X, treatment, y)

    cate = estimator.estimate_cate(X)

    assert len(cate) == len(X)
    assert isinstance(cate, np.ndarray)

    # Correlation with true CATE should be high
    correlation = np.corrcoef(cate, true_cate)[0, 1]
    assert correlation > 0.5  # Reasonable correlation
