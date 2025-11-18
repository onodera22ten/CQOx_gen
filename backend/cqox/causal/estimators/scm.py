"""
SCM: Synthetic Control Method

Creates a synthetic control unit as a weighted combination of control units
to estimate counterfactual outcomes for a treated unit.
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from loguru import logger
from typing import Optional, List

from .base import BaseEstimator


class SCMEstimator(BaseEstimator):
    """
    Synthetic Control Method (SCM)

    Constructs a synthetic control unit as a convex combination of control units
    to estimate the counterfactual outcome for a treated unit.

    Key idea:
    - One unit receives treatment at time T₀
    - Construct weighted average of untreated units that mimics treated unit pre-treatment
    - Use this "synthetic control" to estimate counterfactual post-treatment

    Mathematical formulation:
    - Pre-treatment periods: t ∈ {1, ..., T₀-1}
    - Post-treatment periods: t ∈ {T₀, ..., T}
    - Treated unit: i = 1
    - Control units: i ∈ {2, ..., J+1}

    Find weights W = (w₂, ..., w_{J+1}) that minimize:
    ||X₁ - X₀W||² subject to w_j ≥ 0, Σw_j = 1

    where X₁ = pre-treatment characteristics of treated unit
          X₀ = pre-treatment characteristics of control units

    Treatment effect:
    τ̂_t = Y₁t - Σ_j w_j Y_{jt} for t ≥ T₀

    Advantages:
    - Transparent weighting (interpretable which units form synthetic control)
    - No extrapolation (weights are convex combination)
    - Visual diagnostic (can plot treated vs synthetic control)

    Disadvantages:
    - Requires long pre-treatment period for good fit
    - Only one treated unit (or aggregate multiple)
    - Assumes no spillover effects

    Classic applications:
    - Abadie & Gardeazabal (2003): Basque terrorism and economic growth
    - Abadie et al (2010): California tobacco control program
    - Abadie et al (2015): German reunification

    Reference:
    - Abadie & Gardeazabal (2003). "The Economic Costs of Conflict"
    - Abadie et al (2010). "Synthetic Control Methods for Comparative Case Studies"
    - Abadie (2021). "Using Synthetic Controls: Feasibility, Data Requirements, and Methodological Aspects"
    """

    def __init__(
        self,
        time_col: str = 'time_period',
        unit_col: str = 'unit_id',
        treatment_time: Optional[int] = None,
        treated_unit: Optional[str] = None,
        predictor_cols: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        time_col : str
            Name of time period column
        unit_col : str
            Name of unit identifier column
        treatment_time : int, optional
            Time period when treatment begins (T₀)
        treated_unit : str, optional
            Identifier of treated unit
        predictor_cols : list of str, optional
            Columns to use for matching (pre-treatment characteristics)
            If None, uses all numeric columns except time/unit/outcome
        """
        super().__init__(**kwargs)
        self.time_col = time_col
        self.unit_col = unit_col
        self.treatment_time = treatment_time
        self.treated_unit = treated_unit
        self.predictor_cols = predictor_cols

    def fit(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        treatment_time: Optional[int] = None,
        treated_unit: Optional[str] = None
    ):
        """
        Fit Synthetic Control Method

        Parameters
        ----------
        X : pd.DataFrame
            Panel data with time_col and unit_col
        treatment : pd.Series
            Binary treatment indicator (1 for treated unit post-treatment)
        y : pd.Series
            Outcome variable
        treatment_time : int, optional
            Time period when treatment begins
        treated_unit : str, optional
            Identifier of treated unit

        Returns
        -------
        self
        """
        logger.info(f"Fitting Synthetic Control Method with {len(X)} observations")

        # Handle treatment time and treated unit
        if treatment_time is not None:
            self.treatment_time = treatment_time
        if treated_unit is not None:
            self.treated_unit = treated_unit

        if self.treatment_time is None:
            raise ValueError("Must specify treatment_time")
        if self.treated_unit is None:
            raise ValueError("Must specify treated_unit")

        # Validate required columns
        if self.time_col not in X.columns:
            raise ValueError(f"Time column '{self.time_col}' not found in X")
        if self.unit_col not in X.columns:
            raise ValueError(f"Unit column '{self.unit_col}' not found in X")

        # Store data
        self.X_train = X.copy()
        self.X_train['outcome'] = y.values
        self.X_train['treatment'] = treatment.values
        self.y_train = y.copy()
        self.treatment_train = treatment.copy()

        # Identify treated and control units
        units = X[self.unit_col].unique()
        self.control_units = [u for u in units if u != self.treated_unit]

        logger.info(f"Treated unit: {self.treated_unit}")
        logger.info(f"Control units: {len(self.control_units)} units")
        logger.info(f"Treatment time: {self.treatment_time}")

        # Extract pre-treatment data
        pre_treatment_mask = X[self.time_col] < self.treatment_time
        X_pre = X[pre_treatment_mask].copy()
        y_pre = y[pre_treatment_mask]

        # Get pre-treatment characteristics for treated unit
        treated_mask = X_pre[self.unit_col] == self.treated_unit
        self.X1_pre = X_pre[treated_mask]
        self.y1_pre = y_pre[treated_mask]

        # Get pre-treatment characteristics for control units
        control_mask = X_pre[self.unit_col].isin(self.control_units)
        X0_pre = X_pre[control_mask]
        y0_pre = y_pre[control_mask]

        # Determine predictor columns
        if self.predictor_cols is None:
            # Use outcome variable across all pre-treatment periods
            self.predictor_cols = ['outcome']

        # Construct matrices for optimization
        self._construct_matrices(X_pre, y_pre)

        # Optimize weights
        self._optimize_weights()

        # Store pre-treatment fit
        self._compute_pretreatment_fit()

        self.is_fitted = True
        logger.info("Synthetic Control Method fitted successfully")
        logger.info(f"Pre-treatment RMSPE: {self.pretreatment_rmspe_:.4f}")

        return self

    def _construct_matrices(self, X_pre: pd.DataFrame, y_pre: pd.Series):
        """
        Construct X₁ (treated) and X₀ (control) matrices

        For outcome-based matching, uses average outcome across pre-treatment periods
        """
        # Treated unit pre-treatment outcomes
        treated_mask = X_pre[self.unit_col] == self.treated_unit
        y1_values = y_pre[treated_mask].values
        time1_values = X_pre[treated_mask][self.time_col].values

        # Control units pre-treatment outcomes (matrix: time × units)
        self.control_unit_list = []
        y0_matrix = []

        for unit in self.control_units:
            unit_mask = X_pre[self.unit_col] == unit
            y_unit = y_pre[unit_mask].values
            time_unit = X_pre[unit_mask][self.time_col].values

            # Ensure same time periods
            if len(y_unit) == len(y1_values) and np.array_equal(time_unit, time1_values):
                y0_matrix.append(y_unit)
                self.control_unit_list.append(unit)
            else:
                logger.warning(f"Unit {unit} has different time periods, excluding")

        self.X1 = y1_values  # Shape: (T₀,)
        self.X0 = np.array(y0_matrix).T  # Shape: (T₀, J)

        logger.info(f"Pre-treatment periods: {len(self.X1)}")
        logger.info(f"Control units after alignment: {len(self.control_unit_list)}")

    def _optimize_weights(self):
        """
        Optimize synthetic control weights

        Minimize ||X₁ - X₀W||²
        Subject to: w_j ≥ 0, Σw_j = 1
        """
        J = self.X0.shape[1]  # Number of control units

        # Objective function: minimize squared distance
        def objective(w):
            synthetic = self.X0 @ w
            return np.sum((self.X1 - synthetic) ** 2)

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Σw_j = 1
        ]

        # Bounds: 0 ≤ w_j ≤ 1
        bounds = [(0, 1) for _ in range(J)]

        # Initial guess: equal weights
        w0 = np.ones(J) / J

        # Optimize
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")

        self.weights_ = result.x
        logger.info(f"Optimization converged: {result.success}")
        logger.info(f"Number of units with non-zero weight: {np.sum(self.weights_ > 0.01)}")

        # Log top contributing units
        top_indices = np.argsort(self.weights_)[::-1][:5]
        for idx in top_indices:
            if self.weights_[idx] > 0.01:
                unit = self.control_unit_list[idx]
                weight = self.weights_[idx]
                logger.info(f"  Unit {unit}: weight = {weight:.4f}")

    def _compute_pretreatment_fit(self):
        """
        Compute pre-treatment fit quality (RMSPE)

        Root Mean Squared Prediction Error
        """
        synthetic_pre = self.X0 @ self.weights_
        self.pretreatment_rmspe_ = np.sqrt(np.mean((self.X1 - synthetic_pre) ** 2))

    def estimate_ate(self) -> float:
        """
        Estimate Average Treatment Effect on the Treated (ATT)

        ATT = (1/T_post) Σ_{t≥T₀} [Y₁t - Σ_j w_j Y_{jt}]

        Returns
        -------
        float
            Estimated ATT (average effect post-treatment)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Post-treatment data
        post_mask = self.X_train[self.time_col] >= self.treatment_time
        X_post = self.X_train[post_mask]

        # Treated unit outcomes
        treated_mask = X_post[self.unit_col] == self.treated_unit
        y1_post = X_post[treated_mask]['outcome'].values

        # Synthetic control outcomes
        y0_post = []
        for unit in self.control_unit_list:
            unit_mask = X_post[self.unit_col] == unit
            y_unit = X_post[unit_mask]['outcome'].values
            y0_post.append(y_unit)

        y0_post_matrix = np.array(y0_post).T  # Shape: (T_post, J)
        synthetic_post = y0_post_matrix @ self.weights_

        # Compute treatment effects
        self.treatment_effects_ = y1_post - synthetic_post
        self.ate_ = np.mean(self.treatment_effects_)

        logger.info(f"Estimated ATT (post-treatment average): {self.ate_:.4f}")

        return self.ate_

    def estimate_att(self) -> float:
        """
        For SCM, ATE = ATT (effect on the treated unit)

        Returns
        -------
        float
            Estimated ATT
        """
        return self.estimate_ate()

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        SCM estimates effect for one treated unit only

        Returns treatment effect for treated unit, 0 for control units

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix with unit_col

        Returns
        -------
        np.ndarray
            Treatment effects (non-zero only for treated unit)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        logger.warning("SCM estimates effect for treated unit only. Returning 0 for control units.")

        # Return ATE for treated unit, 0 for others
        effects = np.zeros(len(X))
        treated_mask = X[self.unit_col] == self.treated_unit
        effects[treated_mask] = self.ate_

        return effects

    def get_time_series(self) -> pd.DataFrame:
        """
        Get time series of treated vs synthetic control

        Returns
        -------
        pd.DataFrame
            Columns: time, treated, synthetic, effect
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Full time series
        times = sorted(self.X_train[self.time_col].unique())

        treated_series = []
        synthetic_series = []

        for t in times:
            time_mask = self.X_train[self.time_col] == t

            # Treated unit
            treated_mask = time_mask & (self.X_train[self.unit_col] == self.treated_unit)
            y_treated = self.X_train[treated_mask]['outcome'].values[0]

            # Synthetic control
            y_synthetic = 0
            for i, unit in enumerate(self.control_unit_list):
                unit_mask = time_mask & (self.X_train[self.unit_col] == unit)
                if unit_mask.sum() > 0:
                    y_unit = self.X_train[unit_mask]['outcome'].values[0]
                    y_synthetic += self.weights_[i] * y_unit

            treated_series.append(y_treated)
            synthetic_series.append(y_synthetic)

        return pd.DataFrame({
            'time': times,
            'treated': treated_series,
            'synthetic': synthetic_series,
            'effect': np.array(treated_series) - np.array(synthetic_series),
            'post_treatment': np.array(times) >= self.treatment_time
        })

    def placebo_test(self, n_placebos: int = None) -> pd.DataFrame:
        """
        Placebo test: Apply SCM to control units as if they were treated

        Tests whether observed effect is unusually large compared to
        effects estimated for untreated units (falsification test)

        Parameters
        ----------
        n_placebos : int, optional
            Number of placebo tests to run
            If None, runs for all control units

        Returns
        -------
        pd.DataFrame
            Placebo effects for each control unit
        """
        logger.info("Placebo test not yet fully implemented")
        return pd.DataFrame()

    def get_weights(self) -> pd.DataFrame:
        """
        Get synthetic control weights

        Returns
        -------
        pd.DataFrame
            Unit identifiers and their weights
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        return pd.DataFrame({
            'unit': self.control_unit_list,
            'weight': self.weights_
        }).sort_values('weight', ascending=False)
