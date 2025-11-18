"""
Unit tests for CAS (Causal Assurance Score) calculation

Tests:
- CAS score calculation
- Component scores
- Quality level determination
- Recommendations
"""
import pytest
import numpy as np

from cqox.causal.diagnostics.cas_score import (
    calculate_cas_score,
    _get_recommendation
)


class TestCASScore:
    """Test CAS Score calculation"""

    def test_high_quality_score(self):
        """Test CAS score with high quality diagnostics"""
        diagnostics = {
            'balance': {'max_smd': 0.05},           # Good balance
            'overlap': {'violation_rate': 0.01},    # Good overlap
            'sensitivity': {'critical_gamma': 2.5}, # Strong robustness
            'e_value': {'e_value_point_estimate': 3.0},  # High E-value
            'positivity': {'violation_rate': 0.02},
            'cate_distribution': {'negative_share': 0.10},
            'calibration': {'calibration_correlation': 0.85},
            'network_spillover': {'correlation_with_own_treatment': 0.05}
        }

        result = calculate_cas_score(diagnostics)

        assert 'cas_score' in result
        assert 'quality_level' in result
        assert 'component_scores' in result
        assert 'recommendation' in result

        # Should be high quality
        assert result['cas_score'] >= 0.8
        assert result['quality_level'] == 'HIGH'

    def test_medium_quality_score(self):
        """Test CAS score with medium quality diagnostics"""
        diagnostics = {
            'balance': {'max_smd': 0.15},           # Moderate balance
            'overlap': {'violation_rate': 0.05},    # Some violations
            'sensitivity': {'critical_gamma': 1.5}, # Moderate robustness
            'e_value': {'e_value_point_estimate': 1.8},
        }

        result = calculate_cas_score(diagnostics)

        # Should be medium quality
        assert 0.6 <= result['cas_score'] < 0.8
        assert result['quality_level'] == 'MEDIUM'

    def test_low_quality_score(self):
        """Test CAS score with low quality diagnostics"""
        diagnostics = {
            'balance': {'max_smd': 0.30},           # Poor balance
            'overlap': {'violation_rate': 0.15},    # Many violations
            'sensitivity': {'critical_gamma': 1.1}, # Weak robustness
            'e_value': {'e_value_point_estimate': 1.2},
        }

        result = calculate_cas_score(diagnostics)

        # Should be low quality
        assert result['cas_score'] < 0.6
        assert result['quality_level'] == 'LOW'

    def test_custom_weights(self):
        """Test CAS score with custom weights"""
        diagnostics = {
            'balance': {'max_smd': 0.10},
            'overlap': {'violation_rate': 0.03},
        }

        # Emphasize balance heavily
        custom_weights = {
            'balance': 0.9,
            'overlap': 0.1
        }

        result = calculate_cas_score(diagnostics, weights=custom_weights)

        assert 'cas_score' in result
        assert result['weights_used'] == custom_weights

    def test_partial_diagnostics(self):
        """Test CAS score with only some diagnostics available"""
        diagnostics = {
            'balance': {'max_smd': 0.08},
            'overlap': {'violation_rate': 0.02}
            # Missing other diagnostics
        }

        result = calculate_cas_score(diagnostics)

        # Should still compute score based on available diagnostics
        assert 'cas_score' in result
        assert 0 <= result['cas_score'] <= 1

    def test_component_scores(self):
        """Test individual component score calculation"""
        diagnostics = {
            'balance': {'max_smd': 0.10},
            'overlap': {'violation_rate': 0.05},
            'sensitivity': {'critical_gamma': 2.0},
        }

        result = calculate_cas_score(diagnostics)

        component_scores = result['component_scores']

        # Check balance score
        assert 'balance' in component_scores
        assert 0 <= component_scores['balance'] <= 1

        # Check overlap score
        assert 'overlap' in component_scores
        assert 0 <= component_scores['overlap'] <= 1

        # Check sensitivity score
        assert 'sensitivity' in component_scores
        assert 0 <= component_scores['sensitivity'] <= 1

    def test_recommendation_high_quality(self):
        """Test recommendation for high quality"""
        component_scores = {
            'balance': 0.9,
            'overlap': 0.85,
            'sensitivity': 0.8
        }

        recommendation = _get_recommendation(0.85, component_scores)

        assert 'High confidence' in recommendation
        assert 'proceed' in recommendation.lower()

    def test_recommendation_medium_quality(self):
        """Test recommendation for medium quality"""
        component_scores = {
            'balance': 0.7,
            'overlap': 0.6,
            'sensitivity': 0.65
        }

        recommendation = _get_recommendation(0.65, component_scores)

        assert 'Moderate confidence' in recommendation
        assert 'validation' in recommendation.lower()

    def test_recommendation_low_quality(self):
        """Test recommendation for low quality"""
        component_scores = {
            'balance': 0.3,
            'overlap': 0.4,
            'sensitivity': 0.2
        }

        recommendation = _get_recommendation(0.35, component_scores)

        assert 'Low confidence' in recommendation
        assert 'balance' in recommendation or 'overlap' in recommendation

    def test_empty_diagnostics(self):
        """Test handling of empty diagnostics"""
        diagnostics = {}

        result = calculate_cas_score(diagnostics)

        # Should return 0 score when no diagnostics available
        assert result['cas_score'] == 0.0
        assert result['quality_level'] == 'LOW'

    def test_boundary_values(self):
        """Test boundary values for diagnostics"""
        # Perfect diagnostics
        perfect_diagnostics = {
            'balance': {'max_smd': 0.0},
            'overlap': {'violation_rate': 0.0},
            'sensitivity': {'critical_gamma': 10.0},
            'e_value': {'e_value_point_estimate': 10.0},
        }

        result = calculate_cas_score(perfect_diagnostics)
        assert result['cas_score'] > 0.9

    def test_score_normalization(self):
        """Test that scores are properly normalized to [0, 1]"""
        diagnostics = {
            'balance': {'max_smd': 0.12},
            'overlap': {'violation_rate': 0.04},
            'sensitivity': {'critical_gamma': 1.8},
        }

        result = calculate_cas_score(diagnostics)

        # Check all component scores are in [0, 1]
        for score in result['component_scores'].values():
            assert 0 <= score <= 1

        # Check overall CAS score is in [0, 1]
        assert 0 <= result['cas_score'] <= 1


class TestCASScoreEdgeCases:
    """Test edge cases in CAS score calculation"""

    def test_extreme_bad_balance(self):
        """Test extremely bad balance (SMD >> 0.25)"""
        diagnostics = {
            'balance': {'max_smd': 2.0}  # Very large imbalance
        }

        result = calculate_cas_score(diagnostics)

        # Balance score should be 0 (or very close)
        assert result['component_scores']['balance'] <= 0.01

    def test_extreme_good_sensitivity(self):
        """Test extremely good sensitivity (Gamma >> 2)"""
        diagnostics = {
            'sensitivity': {'critical_gamma': 5.0}
        }

        result = calculate_cas_score(diagnostics)

        # Sensitivity score should be capped at 1.0
        assert result['component_scores']['sensitivity'] <= 1.0

    def test_negative_share_boundary(self):
        """Test CATE distribution negative share at boundary"""
        diagnostics = {
            'cate_distribution': {'negative_share': 0.20}  # At threshold
        }

        result = calculate_cas_score(diagnostics)

        # Should be near 0 (but not negative)
        assert result['component_scores']['cate_distribution'] >= 0

    def test_calibration_correlation(self):
        """Test calibration correlation scoring"""
        # High correlation (good)
        diagnostics_good = {
            'calibration': {'calibration_correlation': 0.95}
        }

        result_good = calculate_cas_score(diagnostics_good)
        assert result_good['component_scores']['calibration'] >= 0.9

        # Low correlation (bad)
        diagnostics_bad = {
            'calibration': {'calibration_correlation': 0.1}
        }

        result_bad = calculate_cas_score(diagnostics_bad)
        assert result_bad['component_scores']['calibration'] <= 0.2
