"""
Experiment Design Recommender
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from loguru import logger


class ExperimentDesignRecommender:
    """
    Recommends experiment design based on uncertainty and value of information

    v1: Rule-based recommendations
    v2: Utility maximization
    """

    def __init__(self, mode: str = "rule_based"):
        """
        Args:
            mode: 'rule_based' or 'utility_maximization'
        """
        self.mode = mode

    def recommend_experiments_rule_based(
        self,
        X: pd.DataFrame,
        cate: np.ndarray,
        cate_std: np.ndarray = None,
        diagnostic_results: Dict[str, Any] = None,
        budget: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Rule-based experiment recommendations

        Recommends experiments in areas with:
        - High uncertainty (high CATE variance)
        - Poor overlap
        - High negative CATE share
        - Important segments

        Args:
            X: Features
            cate: CATE estimates
            cate_std: CATE standard errors (optional)
            diagnostic_results: Diagnostic results
            budget: Experiment budget (number of units)

        Returns:
            List of experiment recommendations
        """
        logger.info("Generating rule-based experiment recommendations")

        recommendations = []

        # 1. High uncertainty regions
        if cate_std is not None:
            high_uncertainty_mask = cate_std > np.percentile(cate_std, 75)

            if high_uncertainty_mask.sum() > 0:
                recommendations.append({
                    'reason': 'high_uncertainty',
                    'segment': 'High CATE uncertainty',
                    'n_units': min(int(high_uncertainty_mask.sum() * 0.1), budget // 3),
                    'priority': 'HIGH',
                    'description': f'{high_uncertainty_mask.sum()} units with high uncertainty',
                    'filter': 'cate_std > p75'
                })

        # 2. Negative CATE regions
        negative_cate_mask = cate < 0

        if negative_cate_mask.sum() > int(len(cate) * 0.05):  # More than 5%
            recommendations.append({
                'reason': 'negative_cate',
                'segment': 'Negative CATE region',
                'n_units': min(int(negative_cate_mask.sum() * 0.2), budget // 3),
                'priority': 'MEDIUM',
                'description': f'{negative_cate_mask.sum()} units with negative CATE',
                'filter': 'cate < 0'
            })

        # 3. Poor overlap regions
        if diagnostic_results and 'overlap' in diagnostic_results:
            # Assume we have propensity scores in diagnostic results
            # This is simplified
            recommendations.append({
                'reason': 'poor_overlap',
                'segment': 'Poor overlap region',
                'n_units': budget // 4,
                'priority': 'HIGH',
                'description': 'Regions with extreme propensity scores',
                'filter': 'ps < 0.1 or ps > 0.9'
            })

        # 4. Important segments (high value)
        high_value_mask = cate > np.percentile(cate, 90)

        if high_value_mask.sum() > 0:
            recommendations.append({
                'reason': 'high_value_validation',
                'segment': 'High-value segment',
                'n_units': min(int(high_value_mask.sum() * 0.15), budget // 4),
                'priority': 'MEDIUM',
                'description': f'{high_value_mask.sum()} units with high CATE - validate before scaling',
                'filter': 'cate > p90'
            })

        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        recommendations.sort(key=lambda x: priority_order[x['priority']])

        # Allocate budget
        total_allocated = sum(r['n_units'] for r in recommendations)
        if total_allocated > budget:
            # Scale down proportionally
            scale = budget / total_allocated
            for r in recommendations:
                r['n_units'] = int(r['n_units'] * scale)

        logger.info(f"Generated {len(recommendations)} experiment recommendations")

        return recommendations

    def recommend_experiments_utility_maximization(
        self,
        X: pd.DataFrame,
        cate: np.ndarray,
        cate_var: np.ndarray,
        value_per_unit: np.ndarray,
        budget: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Utility maximization approach (v2)

        Allocates experiment budget to maximize expected value of information

        Args:
            X: Features
            cate: CATE estimates
            cate_var: CATE variance
            value_per_unit: Expected value per unit
            budget: Experiment budget

        Returns:
            Optimal experiment allocation
        """
        logger.info("Generating utility-maximizing experiment design")

        # Expected value of information (EVOI)
        # EVOI ≈ √(variance) * value_per_unit
        # Higher variance = more to learn
        # Higher value = more important to get right

        evoi = np.sqrt(cate_var) * value_per_unit

        # Sort by EVOI
        sorted_idx = np.argsort(-evoi)

        # Allocate budget to top EVOI units
        allocated_units = sorted_idx[:budget]

        # Group into segments
        # This is simplified - in practice, would cluster similar units
        segments = self._cluster_into_segments(X.iloc[allocated_units], n_segments=5)

        recommendations = []
        for seg_id, seg_mask in enumerate(segments):
            seg_indices = allocated_units[seg_mask]

            recommendations.append({
                'reason': 'high_evoi',
                'segment': f'EVOI Segment {seg_id + 1}',
                'n_units': len(seg_indices),
                'priority': 'HIGH',
                'description': f'High expected value of information',
                'mean_evoi': float(evoi[seg_indices].mean()),
                'unit_indices': seg_indices.tolist()
            })

        logger.info(f"Allocated {budget} units across {len(recommendations)} segments")

        return recommendations

    def _cluster_into_segments(
        self,
        X: pd.DataFrame,
        n_segments: int = 5
    ) -> List[np.ndarray]:
        """Cluster units into segments"""
        from sklearn.cluster import KMeans

        # Simple K-means clustering
        kmeans = KMeans(n_clusters=n_segments, random_state=42)
        labels = kmeans.fit_predict(X)

        segments = [labels == i for i in range(n_segments)]

        return segments
