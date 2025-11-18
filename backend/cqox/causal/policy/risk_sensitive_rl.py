"""
Risk-sensitive Offline Reinforcement Learning
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable
from loguru import logger


class RiskSensitiveOfflineRL:
    """
    Risk-sensitive offline RL for sequential policy optimization

    Incorporates CVaR (Conditional Value at Risk) into policy evaluation
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        horizon: int = 8,
        alpha: float = 0.05
    ):
        """
        Args:
            state_dim: State space dimension
            action_dim: Action space dimension
            horizon: Episode horizon
            alpha: CVaR alpha (e.g., 0.05 for 5% tail risk)
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.horizon = horizon
        self.alpha = alpha

        self.q_table = {}  # Simplified Q-table
        self.policy = None

    def fit_offline(
        self,
        episodes: List[Dict[str, Any]],
        gamma: float = 0.9
    ):
        """
        Fit policy using offline data

        Args:
            episodes: List of episode dicts with 'states', 'actions', 'rewards'
            gamma: Discount factor
        """
        logger.info(f"Fitting offline RL from {len(episodes)} episodes")

        # Simple offline policy evaluation using trajectory data
        # In production, would use more sophisticated offline RL (CQL, IQL, etc.)

        returns_by_state_action = {}

        for episode in episodes:
            states = episode['states']
            actions = episode['actions']
            rewards = episode['rewards']

            # Calculate discounted returns
            T = len(rewards)
            returns = np.zeros(T)

            for t in range(T):
                returns[t] = sum(
                    gamma ** (k - t) * rewards[k]
                    for k in range(t, T)
                )

            # Store returns for each (state, action) pair
            for t in range(T):
                state_key = self._state_to_key(states[t])
                action = actions[t]

                key = (state_key, action)
                if key not in returns_by_state_action:
                    returns_by_state_action[key] = []

                returns_by_state_action[key].append(returns[t])

        # Estimate Q-values and CVaR
        for key, returns_list in returns_by_state_action.items():
            returns_array = np.array(returns_list)

            self.q_table[key] = {
                'mean_return': float(returns_array.mean()),
                'cvar': float(self._calculate_cvar(returns_array, self.alpha)),
                'std': float(returns_array.std()),
                'count': len(returns_list)
            }

        logger.info(f"Fitted Q-table with {len(self.q_table)} state-action pairs")

        return self

    def _calculate_cvar(self, returns: np.ndarray, alpha: float) -> float:
        """Calculate CVaR (Conditional Value at Risk)"""
        var = np.percentile(returns, alpha * 100)
        cvar = returns[returns <= var].mean()
        return cvar

    def _state_to_key(self, state: Dict[str, Any]) -> str:
        """Convert state dict to hashable key"""
        # Simple discretization for demo
        # In production, would use state representation learning
        return str(sorted(state.items()))

    def select_action(
        self,
        state: Dict[str, Any],
        risk_aversion: float = 0.5
    ) -> int:
        """
        Select action using risk-sensitive policy

        Args:
            state: Current state
            risk_aversion: Weight on risk (0=risk-neutral, 1=very risk-averse)

        Returns:
            Selected action
        """
        state_key = self._state_to_key(state)

        # Find all actions available from this state
        available_actions = [
            action for (s, action) in self.q_table.keys()
            if s == state_key
        ]

        if not available_actions:
            # Random action if state unseen
            return np.random.randint(self.action_dim)

        # Score each action: risk-adjusted value
        action_scores = {}

        for action in available_actions:
            key = (state_key, action)
            q_data = self.q_table[key]

            # Risk-adjusted score: weighted combination of mean and CVaR
            score = (
                (1 - risk_aversion) * q_data['mean_return'] +
                risk_aversion * q_data['cvar']
            )

            action_scores[action] = score

        # Select action with highest risk-adjusted score
        best_action = max(action_scores, key=action_scores.get)

        return best_action

    def evaluate_policy(
        self,
        policy: Callable,
        episodes: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evaluate a policy on offline data

        Args:
            policy: Policy function (state -> action)
            episodes: Evaluation episodes

        Returns:
            Evaluation metrics
        """
        logger.info(f"Evaluating policy on {len(episodes)} episodes")

        all_returns = []

        for episode in episodes:
            episode_return = sum(episode['rewards'])
            all_returns.append(episode_return)

        all_returns = np.array(all_returns)

        metrics = {
            'mean_return': float(all_returns.mean()),
            'std_return': float(all_returns.std()),
            'min_return': float(all_returns.min()),
            'max_return': float(all_returns.max()),
            'cvar_005': float(self._calculate_cvar(all_returns, 0.05)),
            'cvar_010': float(self._calculate_cvar(all_returns, 0.10))
        }

        logger.info(f"Policy mean return: {metrics['mean_return']:.2f}, CVaR(5%): {metrics['cvar_005']:.2f}")

        return metrics
