"""
Customer Digital Twin / Causal Twin (v2)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class CustomerDigitalTwin:
    """
    Digital Twin for customer simulation

    Simulates customer behavior under different policy sequences
    """

    def __init__(
        self,
        transition_model,
        reward_model,
        initial_state: Dict[str, Any]
    ):
        """
        Args:
            transition_model: Model for state transitions
            reward_model: Model for rewards
            initial_state: Initial customer state
        """
        self.transition_model = transition_model
        self.reward_model = reward_model
        self.initial_state = initial_state
        self.state_history = []
        self.reward_history = []

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate one time step

        Args:
            action: Action/treatment to apply

        Returns:
            Dict with next state and reward
        """
        # Get current state
        if len(self.state_history) == 0:
            current_state = self.initial_state
        else:
            current_state = self.state_history[-1]

        # Predict next state
        state_features = self._state_to_features(current_state)
        action_features = self._action_to_features(action)

        combined_features = {**state_features, **action_features}
        next_state = self.transition_model.predict(combined_features)

        # Calculate reward
        reward = self.reward_model.predict(combined_features, next_state)

        # Update history
        self.state_history.append(next_state)
        self.reward_history.append(reward)

        return {
            'next_state': next_state,
            'reward': reward
        }

    def simulate_episode(
        self,
        policy: callable,
        num_steps: int = 12
    ) -> Dict[str, Any]:
        """
        Simulate an episode (sequence of steps)

        Args:
            policy: Policy function mapping state to action
            num_steps: Number of steps to simulate

        Returns:
            Dict with simulation results
        """
        logger.info(f"Simulating episode for {num_steps} steps")

        # Reset
        self.state_history = [self.initial_state]
        self.reward_history = []

        # Simulate
        for t in range(num_steps):
            current_state = self.state_history[-1]
            action = policy(current_state, t)
            result = self.step(action)

        # Calculate metrics
        total_reward = sum(self.reward_history)
        avg_reward = np.mean(self.reward_history)

        return {
            'states': self.state_history,
            'rewards': self.reward_history,
            'total_reward': total_reward,
            'avg_reward': avg_reward,
            'num_steps': num_steps
        }

    def _state_to_features(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Convert state dict to feature dict"""
        # Simple passthrough for now
        return {k: float(v) if isinstance(v, (int, float)) else 0.0
                for k, v in state.items()}

    def _action_to_features(self, action: Dict[str, Any]) -> Dict[str, float]:
        """Convert action dict to feature dict"""
        # Simple passthrough for now
        return {f"action_{k}": float(v) if isinstance(v, (int, float)) else 0.0
                for k, v in action.items()}


class SimplifiedTransitionModel:
    """Simplified transition model for demo purposes"""

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict next state (simplified)"""
        # Simple rule-based transition
        next_state = features.copy()

        # Add some randomness
        for key in next_state:
            if isinstance(next_state[key], (int, float)):
                next_state[key] += np.random.normal(0, 0.1)

        return next_state


class SimplifiedRewardModel:
    """Simplified reward model for demo purposes"""

    def predict(self, features: Dict[str, Any], next_state: Dict[str, Any]) -> float:
        """Predict reward (simplified)"""
        # Simple reward based on state improvement
        reward = 0.0

        # Example: reward for increased engagement
        if 'engagement' in next_state and 'engagement' in features:
            reward += (next_state['engagement'] - features['engagement']) * 10

        return reward
