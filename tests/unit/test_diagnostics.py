"""
Unit tests for diagnostics
"""
import pytest
import pandas as pd
import numpy as np
from cqox.causal.diagnostics.balance import covariate_balance_test
from cqox.causal.diagnostics.overlap import overlap_test
from cqox.causal.diagnostics.cas_score import calculate_cas_score


@pytest.fixture
def balanced_data():
    """Generate balanced treatment/control data"""
    np.random.seed(42)
    n = 1000

    X = pd.DataFrame({
        'X1': np.random.normal(0, 1, n),
        'X2': np.random.normal(0, 1, n)
    })

    # Random treatment (balanced)
    treatment = pd.Series(np.random.binomial(1, 0.5, n))

    return X, treatment


@pytest.fixture
def imbalanced_data():
    """Generate imbalanced treatment/control data"""
    np.random.seed(42)
    n = 1000

    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(0, 1, n)

    # Treatment depends on X1 (imbalanced)
    ps = 1 / (1 + np.exp(-2 * X1))
    treatment = pd.Series(np.random.binomial(1, ps))

    X = pd.DataFrame({'X1': X1, 'X2': X2})

    return X, treatment


def test_balance_test_balanced(balanced_data):
    """Test balance on balanced data"""
    X, treatment = balanced_data

    passed, report = covariate_balance_test(X, treatment, threshold=0.1)

    assert isinstance(passed, bool)
    assert isinstance(report, dict)
    assert 'max_smd' in report
    assert passed  # Should pass for balanced data


def test_balance_test_imbalanced(imbalanced_data):
    """Test balance on imbalanced data"""
    X, treatment = imbalanced_data

    passed, report = covariate_balance_test(X, treatment, threshold=0.1)

    assert isinstance(passed, bool)
    assert not passed  # Should fail for imbalanced data
    assert report['max_smd'] > 0.1


def test_overlap_test(balanced_data):
    """Test overlap/positivity"""
    X, treatment = balanced_data

    passed, report = overlap_test(X, treatment)

    assert isinstance(passed, bool)
    assert isinstance(report, dict)
    assert 'violation_rate' in report
    assert 'propensity_scores' in report


def test_cas_score_calculation():
    """Test CAS score calculation"""
    diagnostic_results = {
        'balance': {'max_smd': 0.05},
        'overlap': {'violation_rate': 0.02},
        'sensitivity': {'critical_gamma': 2.0},
        'e_value': {'e_value_point_estimate': 2.5}
    }

    result = calculate_cas_score(diagnostic_results)

    assert isinstance(result, dict)
    assert 'cas_score' in result
    assert 'quality_level' in result
    assert 0 <= result['cas_score'] <= 1
    assert result['quality_level'] in ['HIGH', 'MEDIUM', 'LOW']
