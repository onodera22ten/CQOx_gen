"""
Unit tests for causal inference estimators

Tests for all 7 core estimators:
- DR-Learner
- IPW
- DiD
- IV
- Causal Forest
- SCM
- RD
"""
import pytest
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification

from cqox.causal.estimators import (
    DRLearner,
    IPWEstimator,
    DIDEstimator,
    IVEstimator,
    CausalForestEstimator,
    SCMEstimator,
    RDEstimator,
    get_estimator
)


@pytest.fixture
def synthetic_data():
    """Generate synthetic causal inference dataset"""
    np.random.seed(42)
    n = 1000

    # Features
    X = np.random.randn(n, 5)

    # Treatment (with confounding)
    propensity = 1 / (1 + np.exp(-(X[:, 0] + 0.5 * X[:, 1])))
    treatment = (np.random.rand(n) < propensity).astype(int)

    # Outcome (with treatment effect)
    true_ate = 2.0
    noise = np.random.randn(n) * 0.5
    outcome = (
        X[:, 0] + 0.5 * X[:, 1] +  # Baseline
        true_ate * treatment +      # Treatment effect
        noise                       # Noise
    )

    df = pd.DataFrame(X, columns=[f'x{i}' for i in range(5)])
    df['treatment'] = treatment
    df['outcome'] = outcome

    return df, true_ate


@pytest.fixture
def panel_data():
    """Generate synthetic panel data for DiD"""
    np.random.seed(42)
    n_units = 100
    n_periods = 4

    data = []
    for unit_id in range(n_units):
        for time_period in range(n_periods):
            # Treatment starts at period 2 for half the units
            is_treated_unit = unit_id < 50
            post_treatment = time_period >= 2
            treatment = 1 if (is_treated_unit and post_treatment) else 0

            # Outcome with parallel trends + treatment effect
            unit_effect = np.random.randn() * 2  # Fixed effect
            time_effect = time_period * 0.5
            treatment_effect = 3.0 if treatment == 1 else 0

            outcome = (
                5.0 +               # Baseline
                unit_effect +       # Unit fixed effect
                time_effect +       # Time trend
                treatment_effect +  # Treatment effect
                np.random.randn() * 0.5  # Noise
            )

            data.append({
                'unit_id': unit_id,
                'time_period': time_period,
                'treatment': treatment,
                'outcome': outcome,
                'x0': np.random.randn(),
                'x1': np.random.randn()
            })

    return pd.DataFrame(data), 3.0  # True ATE


class TestDRLearner:
    """Test DR-Learner (Doubly Robust)"""

    def test_fit_and_estimate_ate(self, synthetic_data):
        df, true_ate = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = DRLearner()
        estimator.fit(X, T, y)

        ate = estimator.estimate_ate()

        # Check ATE is within reasonable range of true effect
        assert isinstance(ate, float)
        assert 0 < ate < 5  # Should be positive and reasonable

    def test_estimate_cate(self, synthetic_data):
        df, _ = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = DRLearner()
        estimator.fit(X, T, y)

        cate = estimator.estimate_cate(X)

        assert len(cate) == len(X)
        assert isinstance(cate, np.ndarray)


class TestIPWEstimator:
    """Test Inverse Propensity Weighting"""

    def test_fit_and_estimate_ate(self, synthetic_data):
        df, true_ate = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = IPWEstimator(trim_threshold=0.05)
        estimator.fit(X, T, y)

        ate = estimator.estimate_ate()

        assert isinstance(ate, float)
        assert 0 < ate < 5

    def test_estimate_att(self, synthetic_data):
        df, _ = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = IPWEstimator()
        estimator.fit(X, T, y)

        att = estimator.estimate_att()

        assert isinstance(att, float)

    def test_propensity_scores(self, synthetic_data):
        df, _ = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = IPWEstimator(trim_threshold=0.01)
        estimator.fit(X, T, y)

        ps = estimator.get_propensity_scores()

        # Check propensity scores are in valid range
        assert len(ps) == len(X)
        assert np.all(ps >= 0.01)  # Trimmed
        assert np.all(ps <= 0.99)  # Trimmed

    def test_estimate_variance(self, synthetic_data):
        df, _ = synthetic_data

        X = df[[f'x{i}' for i in range(5)]]
        T = df['treatment']
        y = df['outcome']

        estimator = IPWEstimator()
        estimator.fit(X, T, y)
        estimator.estimate_ate()

        variance = estimator.estimate_variance()

        assert isinstance(variance, float)
        assert variance > 0


class TestDIDEstimator:
    """Test Difference-in-Differences"""

    def test_fit_and_estimate_ate(self, panel_data):
        df, true_ate = panel_data

        X = df[['time_period', 'x0', 'x1']]
        T = df['treatment']
        y = df['outcome']

        estimator = DIDEstimator(time_col='time_period')
        estimator.fit(X, T, y)

        ate = estimator.estimate_ate()

        # DiD should recover treatment effect
        assert isinstance(ate, float)
        assert 1 < ate < 5  # Should be close to 3.0

    def test_get_means_table(self, panel_data):
        df, _ = panel_data

        X = df[['time_period', 'x0', 'x1']]
        T = df['treatment']
        y = df['outcome']

        estimator = DIDEstimator(time_col='time_period')
        estimator.fit(X, T, y)

        means_table = estimator.get_means_table()

        assert isinstance(means_table, pd.DataFrame)
        assert len(means_table) == 4  # 2 groups × 2 periods
        assert 'Mean' in means_table.columns

    def test_estimate_variance(self, panel_data):
        df, _ = panel_data

        X = df[['time_period', 'x0', 'x1']]
        T = df['treatment']
        y = df['outcome']

        estimator = DIDEstimator(time_col='time_period')
        estimator.fit(X, T, y)
        estimator.estimate_ate()

        variance = estimator.estimate_variance()

        assert isinstance(variance, float)
        assert variance > 0


class TestIVEstimator:
    """Test Instrumental Variables (2SLS)"""

    def test_fit_and_estimate_ate(self):
        """Test IV with synthetic instrument"""
        np.random.seed(42)
        n = 1000

        # Instrument (exogenous)
        Z = np.random.randn(n)

        # Endogenous treatment (affected by Z and unobserved confounder)
        U = np.random.randn(n)  # Unobserved confounder
        T = (0.5 * Z + 0.3 * U + np.random.randn(n) * 0.3 > 0).astype(int)

        # Outcome (affected by T and U)
        true_ate = 2.0
        Y = 5.0 + true_ate * T + 0.5 * U + np.random.randn(n) * 0.5

        # Covariates
        X = pd.DataFrame({
            'instrument': Z,
            'x0': np.random.randn(n),
            'x1': np.random.randn(n)
        })

        estimator = IVEstimator(instrument_col='instrument')
        estimator.fit(X, pd.Series(T), pd.Series(Y))

        ate = estimator.estimate_ate()

        # IV should recover causal effect despite endogeneity
        assert isinstance(ate, float)
        assert 0 < ate < 5

    def test_diagnostics(self):
        """Test IV diagnostic statistics"""
        np.random.seed(42)
        n = 500

        Z = np.random.randn(n)
        T = (0.8 * Z + np.random.randn(n) * 0.3 > 0).astype(int)
        Y = 5.0 + 2.0 * T + np.random.randn(n) * 0.5

        X = pd.DataFrame({
            'instrument': Z,
            'x0': np.random.randn(n)
        })

        estimator = IVEstimator(instrument_col='instrument')
        estimator.fit(X, pd.Series(T), pd.Series(Y))
        estimator.estimate_ate()

        diagnostics = estimator.get_diagnostics()

        assert 'late' in diagnostics
        assert 'first_stage_f_stat' in diagnostics
        assert 'instrument_correlation' in diagnostics


class TestRDEstimator:
    """Test Regression Discontinuity"""

    def test_fit_sharp_rd(self):
        """Test Sharp RD with synthetic data"""
        np.random.seed(42)
        n = 500
        cutoff = 0.0

        # Running variable
        X_run = np.random.randn(n) * 2

        # Sharp treatment assignment
        T = (X_run >= cutoff).astype(int)

        # Outcome with discontinuity at cutoff
        true_effect = 3.0
        Y = (
            5.0 +                           # Baseline
            0.5 * X_run +                   # Continuous function of running var
            true_effect * T +               # Treatment effect (discontinuity)
            np.random.randn(n) * 0.5        # Noise
        )

        X = pd.DataFrame({
            'running_var': X_run,
            'x0': np.random.randn(n)
        })

        estimator = RDEstimator(running_var_col='running_var', cutoff=cutoff)
        estimator.fit(X, pd.Series(T), pd.Series(Y))

        ate = estimator.estimate_ate()

        # RD should recover treatment effect
        assert isinstance(ate, float)
        assert 1 < ate < 5

    def test_bandwidth_selection(self):
        """Test automatic bandwidth selection"""
        np.random.seed(42)
        n = 300

        X_run = np.random.randn(n) * 2
        T = (X_run >= 0).astype(int)
        Y = 5.0 + 0.5 * X_run + 2.0 * T + np.random.randn(n) * 0.5

        X = pd.DataFrame({'running_var': X_run})

        estimator = RDEstimator(
            running_var_col='running_var',
            cutoff=0.0,
            bandwidth=None,  # Auto-select
            bandwidth_method='auto'
        )
        estimator.fit(X, pd.Series(T), pd.Series(Y))

        assert estimator.bandwidth > 0


class TestSCMEstimator:
    """Test Synthetic Control Method"""

    def test_fit_and_estimate_ate(self):
        """Test SCM with synthetic panel data"""
        np.random.seed(42)
        n_units = 20
        n_periods = 10
        treatment_time = 7
        treated_unit = 'unit_0'

        data = []
        for unit_id in range(n_units):
            unit_name = f'unit_{unit_id}'
            base_level = np.random.randn() * 2

            for t in range(n_periods):
                is_treated = (unit_name == treated_unit and t >= treatment_time)
                treatment_effect = 5.0 if is_treated else 0.0

                outcome = (
                    10.0 +                      # Baseline
                    base_level +                # Unit fixed effect
                    0.5 * t +                   # Time trend
                    treatment_effect +          # Treatment effect
                    np.random.randn() * 0.3     # Noise
                )

                data.append({
                    'unit_id': unit_name,
                    'time_period': t,
                    'treatment': 1 if is_treated else 0,
                    'outcome': outcome,
                    'x0': np.random.randn()
                })

        df = pd.DataFrame(data)

        X = df[['unit_id', 'time_period', 'x0']]
        T = df['treatment']
        y = df['outcome']

        estimator = SCMEstimator(
            time_col='time_period',
            unit_col='unit_id',
            treatment_time=treatment_time,
            treated_unit=treated_unit
        )

        estimator.fit(X, T, y)
        ate = estimator.estimate_ate()

        # SCM should recover treatment effect
        assert isinstance(ate, float)

    def test_get_weights(self):
        """Test SCM weights extraction"""
        np.random.seed(42)
        n_units = 10
        n_periods = 8

        data = []
        for unit_id in range(n_units):
            for t in range(n_periods):
                data.append({
                    'unit_id': f'unit_{unit_id}',
                    'time_period': t,
                    'treatment': 1 if (unit_id == 0 and t >= 5) else 0,
                    'outcome': 10 + unit_id + 0.5 * t + np.random.randn() * 0.2,
                    'x0': np.random.randn()
                })

        df = pd.DataFrame(data)

        X = df[['unit_id', 'time_period', 'x0']]
        T = df['treatment']
        y = df['outcome']

        estimator = SCMEstimator(
            time_col='time_period',
            unit_col='unit_id',
            treatment_time=5,
            treated_unit='unit_0'
        )

        estimator.fit(X, T, y)

        weights_df = estimator.get_weights()

        assert isinstance(weights_df, pd.DataFrame)
        assert 'unit' in weights_df.columns
        assert 'weight' in weights_df.columns
        # Weights should sum to 1
        assert 0.9 < weights_df['weight'].sum() < 1.1


class TestEstimatorRegistry:
    """Test get_estimator() registry function"""

    def test_get_estimator_by_name(self):
        """Test retrieving estimators by name"""
        # Test all aliases
        assert isinstance(get_estimator('dr'), DRLearner)
        assert isinstance(get_estimator('ipw'), IPWEstimator)
        assert isinstance(get_estimator('did'), DIDEstimator)
        assert isinstance(get_estimator('iv'), IVEstimator)
        assert isinstance(get_estimator('rd'), RDEstimator)
        assert isinstance(get_estimator('scm'), SCMEstimator)

    def test_get_estimator_with_params(self):
        """Test passing parameters to estimator"""
        estimator = get_estimator('ipw', trim_threshold=0.02)

        assert isinstance(estimator, IPWEstimator)
        assert estimator.trim_threshold == 0.02

    def test_get_estimator_unknown(self):
        """Test error handling for unknown estimator"""
        with pytest.raises(ValueError, match="Unknown estimator"):
            get_estimator('unknown_estimator')


class TestEstimatorEdgeCases:
    """Test edge cases and error handling"""

    def test_fit_without_data(self):
        """Test error when fitting with empty data"""
        estimator = DRLearner()

        with pytest.raises((ValueError, IndexError)):
            estimator.fit(pd.DataFrame(), pd.Series([]), pd.Series([]))

    def test_estimate_before_fit(self):
        """Test error when estimating before fitting"""
        estimator = IPWEstimator()

        with pytest.raises(ValueError, match="must be fitted first"):
            estimator.estimate_ate()

    def test_binary_treatment_validation(self):
        """Test validation of binary treatment"""
        np.random.seed(42)
        n = 100

        X = pd.DataFrame(np.random.randn(n, 3))
        T = pd.Series(np.random.randint(0, 3, n))  # Non-binary (0, 1, 2)
        y = pd.Series(np.random.randn(n))

        estimator = IPWEstimator()

        with pytest.raises(ValueError, match="binary"):
            estimator.fit(X, T, y)
