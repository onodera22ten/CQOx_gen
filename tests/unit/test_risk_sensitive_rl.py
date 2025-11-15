"""
Unit tests for risk-sensitive offline RL
"""
import pytest
import pandas as pd
import numpy as np
from cqox.causal.policy.risk_sensitive_rl import (
    RiskSensitiveOfflineRL,
    calculate_cvar,
    fit_behavior_policy
)


@pytest.fixture
def sample_trajectories():
    """Generate sample offline trajectories"""
    np.random.seed(42)
    n = 500

    trajectories = pd.DataFrame({
        'state_x1': np.random.normal(0, 1, n),
        'state_x2': np.random.normal(0, 1, n),
        'action': np.random.binomial(1, 0.5, n),
        'reward': np.random.normal(10, 5, n),
        'next_state_x1': np.random.normal(0, 1, n),
        'next_state_x2': np.random.normal(0, 1, n)
    })

    return trajectories


def test_calculate_cvar():
    """Test CVaR calculation"""
    returns = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    cvar_05 = calculate_cvar(returns, alpha=0.05)
    cvar_10 = calculate_cvar(returns, alpha=0.10)

    assert isinstance(cvar_05, float)
    assert isinstance(cvar_10, float)
    assert cvar_05 < cvar_10  # Lower alpha = more conservative


def test_fit_behavior_policy(sample_trajectories):
    """Test behavior policy fitting"""
    states = sample_trajectories[['state_x1', 'state_x2']].values
    actions = sample_trajectories['action'].values

    behavior_policy = fit_behavior_policy(states, actions)

    assert behavior_policy is not None
    assert hasattr(behavior_policy, 'predict_proba')


def test_risk_sensitive_rl_init():
    """Test RiskSensitiveOfflineRL initialization"""
    rl = RiskSensitiveOfflineRL(alpha=0.05, gamma=0.99)

    assert rl.alpha == 0.05
    assert rl.gamma == 0.99


def test_risk_sensitive_rl_fit(sample_trajectories):
    """Test fitting risk-sensitive policy"""
    rl = RiskSensitiveOfflineRL(alpha=0.05)

    states = sample_trajectories[['state_x1', 'state_x2']].values
    actions = sample_trajectories['action'].values
    rewards = sample_trajectories['reward'].values
    next_states = sample_trajectories[['next_state_x1', 'next_state_x2']].values

    rl.fit(states, actions, rewards, next_states)

    assert rl.is_fitted
    assert rl.policy_model is not None


def test_risk_sensitive_rl_predict(sample_trajectories):
    """Test predicting optimal actions"""
    rl = RiskSensitiveOfflineRL(alpha=0.05)

    states = sample_trajectories[['state_x1', 'state_x2']].values
    actions = sample_trajectories['action'].values
    rewards = sample_trajectories['reward'].values
    next_states = sample_trajectories[['next_state_x1', 'next_state_x2']].values

    rl.fit(states, actions, rewards, next_states)

    test_states = states[:10]
    predictions = rl.predict(test_states)

    assert len(predictions) == 10
    assert all(p in [0, 1] for p in predictions)


def test_risk_sensitive_rl_evaluate(sample_trajectories):
    """Test policy evaluation"""
    rl = RiskSensitiveOfflineRL(alpha=0.05)

    states = sample_trajectories[['state_x1', 'state_x2']].values
    actions = sample_trajectories['action'].values
    rewards = sample_trajectories['reward'].values
    next_states = sample_trajectories[['next_state_x1', 'next_state_x2']].values

    rl.fit(states, actions, rewards, next_states)

    eval_result = rl.evaluate_policy(states, actions, rewards)

    assert 'expected_return' in eval_result
    assert 'cvar' in eval_result
    assert isinstance(eval_result['expected_return'], float)
    assert isinstance(eval_result['cvar'], float)
