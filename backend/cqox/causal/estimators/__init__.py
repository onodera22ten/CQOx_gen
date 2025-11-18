"""
Causal Inference Estimators

This module provides 7 state-of-the-art causal inference estimators:

1. DR-Learner (Doubly Robust): Combines propensity scores + outcome regression
2. IPW (Inverse Propensity Weighting): Reweights by inverse propensity scores
3. DiD (Difference-in-Differences): Time-series with parallel trends assumption
4. IV (Instrumental Variables): Handles endogeneity with 2SLS
5. Causal Forest: Heterogeneous treatment effects using random forests
6. SCM (Synthetic Control Method): Constructs synthetic control from weighted units
7. RD (Regression Discontinuity): Exploits sharp cutoffs in treatment assignment

Additional meta-learners:
- S-Learner: Single model for all units
- T-Learner: Separate models for treatment/control
- X-Learner: Cross-fitted treatment effect estimation
- Doubly Robust Forest: Forest-based doubly robust estimator
- Uplift Forest: Direct uplift modeling

All estimators inherit from BaseEstimator and implement:
- fit(X, treatment, y): Fit the estimator
- estimate_ate(): Average Treatment Effect
- estimate_cate(X): Conditional Average Treatment Effect (heterogeneous effects)
"""

from .base import BaseEstimator
from .dr_learner import DRLearner
from .ipw import IPWEstimator
from .did import DIDEstimator
from .iv import IVEstimator
from .causal_forest import CausalForest, CausalForest as CausalForestEstimator
from .scm import SCMEstimator
from .rd import RDEstimator
from .s_learner import SLearner
from .t_learner import TLearner
from .x_learner import XLearner
from .doubly_robust_forest import DoublyRobustForest
from .uplift_forest import UpliftForest

__all__ = [
    'BaseEstimator',
    # Nobel Prize-winning methods (7 core estimators)
    'DRLearner',
    'IPWEstimator',
    'DIDEstimator',
    'IVEstimator',
    'CausalForestEstimator',
    'SCMEstimator',
    'RDEstimator',
    # Meta-learners
    'SLearner',
    'TLearner',
    'XLearner',
    'DoublyRobustForest',
    'UpliftForest',
]

# Mapping from string names to estimator classes
ESTIMATOR_REGISTRY = {
    'dr': DRLearner,
    'dr_learner': DRLearner,
    'doubly_robust': DRLearner,
    'ipw': IPWEstimator,
    'inverse_propensity': IPWEstimator,
    'did': DIDEstimator,
    'difference_in_differences': DIDEstimator,
    'iv': IVEstimator,
    'instrumental_variables': IVEstimator,
    '2sls': IVEstimator,
    'cf': CausalForest,
    'causal_forest': CausalForest,
    'scm': SCMEstimator,
    'synthetic_control': SCMEstimator,
    'rd': RDEstimator,
    'regression_discontinuity': RDEstimator,
    's_learner': SLearner,
    't_learner': TLearner,
    'x_learner': XLearner,
    'dr_forest': DoublyRobustForest,
    'uplift_forest': UpliftForest,
}


def get_estimator(name: str, **kwargs):
    """
    Get estimator by name

    Parameters
    ----------
    name : str
        Estimator name (e.g., 'dr', 'ipw', 'did', 'iv', 'cf', 'scm', 'rd')
    **kwargs
        Additional parameters passed to estimator constructor

    Returns
    -------
    BaseEstimator
        Initialized estimator

    Examples
    --------
    >>> from cqox.causal.estimators import get_estimator
    >>> estimator = get_estimator('dr')
    >>> estimator.fit(X, treatment, y)
    >>> ate = estimator.estimate_ate()
    """
    name_lower = name.lower().strip()

    if name_lower not in ESTIMATOR_REGISTRY:
        available = ', '.join(sorted(set(ESTIMATOR_REGISTRY.keys())))
        raise ValueError(
            f"Unknown estimator: '{name}'. "
            f"Available estimators: {available}"
        )

    estimator_class = ESTIMATOR_REGISTRY[name_lower]
    return estimator_class(**kwargs)
