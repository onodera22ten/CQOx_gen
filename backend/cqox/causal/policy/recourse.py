"""
Counterfactual Recourse Engine
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class RecourseEngine:
    """
    Generate counterfactual recourse recommendations

    Suggests which levers (price, channel, frequency, etc.) to adjust
    to improve uplift/profit
    """

    def __init__(
        self,
        cate_model,
        levers: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            cate_model: Fitted CATE model
            levers: List of actionable feature names
            constraints: Constraints on lever adjustments
        """
        self.cate_model = cate_model
        self.levers = levers
        self.constraints = constraints or {}

    def generate_recourse(
        self,
        X: pd.DataFrame,
        current_cate: np.ndarray,
        target_improvement: float = 0.1,
        max_changes: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate recourse recommendations

        Args:
            X: Current features
            current_cate: Current CATE estimates
            target_improvement: Target CATE improvement
            max_changes: Maximum number of levers to change

        Returns:
            List of recourse recommendations
        """
        logger.info("Generating counterfactual recourse")

        recommendations = []

        # Find units with low/negative CATE
        low_cate_mask = current_cate < target_improvement
        if not low_cate_mask.any():
            logger.info("No units with low CATE found")
            return recommendations

        X_low_cate = X[low_cate_mask]

        # For each low-CATE unit, try adjusting levers
        for idx in range(min(len(X_low_cate), 100)):  # Limit to 100 samples
            unit = X_low_cate.iloc[idx:idx+1]
            current_cate_value = current_cate[low_cate_mask][idx]

            # Try single lever changes
            best_recommendation = None
            best_improvement = 0.0

            for lever in self.levers:
                if lever not in unit.columns:
                    continue

                # Try different values for this lever
                lever_values = self._get_lever_candidates(unit[lever].values[0], lever)

                for new_value in lever_values:
                    # Create counterfactual
                    unit_cf = unit.copy()
                    unit_cf[lever] = new_value

                    # Estimate counterfactual CATE
                    try:
                        cate_cf = self.cate_model.estimate_cate(unit_cf)[0]
                        improvement = cate_cf - current_cate_value

                        if improvement > best_improvement:
                            best_improvement = improvement
                            best_recommendation = {
                                'unit_index': X_low_cate.index[idx],
                                'current_cate': float(current_cate_value),
                                'predicted_cate': float(cate_cf),
                                'improvement': float(improvement),
                                'lever': lever,
                                'current_value': unit[lever].values[0],
                                'recommended_value': new_value,
                                'changes': 1
                            }
                    except Exception as e:
                        logger.warning(f"Error estimating counterfactual CATE: {e}")
                        continue

            if best_recommendation and best_improvement > 0:
                recommendations.append(best_recommendation)

        # Sort by improvement
        recommendations = sorted(
            recommendations,
            key=lambda x: x['improvement'],
            reverse=True
        )

        logger.info(f"Generated {len(recommendations)} recourse recommendations")
        return recommendations

    def _get_lever_candidates(self, current_value: Any, lever_name: str) -> List[Any]:
        """Get candidate values for a lever"""
        # Check constraints
        if lever_name in self.constraints:
            return self.constraints[lever_name].get('values', [current_value])

        # Default candidates based on type
        if isinstance(current_value, (int, float)):
            # Try +/- 10%, 20%, 50%
            return [
                current_value * 0.9,
                current_value * 0.8,
                current_value * 0.5,
                current_value * 1.1,
                current_value * 1.2,
                current_value * 1.5
            ]
        elif isinstance(current_value, str):
            # Try common channel alternatives
            if lever_name == 'channel':
                return ['push', 'email', 'web', 'sms']
            return [current_value]
        else:
            return [current_value]
