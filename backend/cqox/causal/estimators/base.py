"""
Base class for causal estimators
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
from loguru import logger


class BaseEstimator(ABC):
    """Base class for all causal estimators"""

    def __init__(self, **kwargs):
        self.is_fitted = False
        self.params = kwargs
        self.ate_ = None
        self.cate_ = None

    @abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series
    ):
        """
        Fit the estimator

        Args:
            X: Covariates
            treatment: Treatment assignment
            y: Outcome
        """
        pass

    @abstractmethod
    def estimate_ate(self) -> float:
        """
        Estimate Average Treatment Effect (ATE)

        Returns:
            ATE estimate
        """
        pass

    @abstractmethod
    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        Estimate Conditional Average Treatment Effect (CATE)

        Args:
            X: Covariates

        Returns:
            CATE estimates for each unit
        """
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.is_fitted:
            raise ValueError("Estimator must be fitted first")

        return {
            'ate': float(self.ate_) if self.ate_ is not None else None,
            'cate_mean': float(np.mean(self.cate_)) if self.cate_ is not None else None,
            'cate_std': float(np.std(self.cate_)) if self.cate_ is not None else None,
            'cate_min': float(np.min(self.cate_)) if self.cate_ is not None else None,
            'cate_max': float(np.max(self.cate_)) if self.cate_ is not None else None,
        }
