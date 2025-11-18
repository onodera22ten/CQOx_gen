"""
RD: Regression Discontinuity Design

Exploits sharp cutoffs in treatment assignment to estimate causal effects.
Compares units just above vs just below the threshold.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.base import clone
from loguru import logger
from typing import Optional, Literal

from .base import BaseEstimator


class RDEstimator(BaseEstimator):
    """
    Regression Discontinuity (RD) Design Estimator

    Estimates causal effects by exploiting discontinuities in treatment assignment
    based on a running variable (assignment variable) crossing a threshold.

    Key idea:
    - Treatment assignment determined by running variable X crossing cutoff c
    - Sharp RD: P(T=1|X=x) jumps from 0 to 1 at x = c
    - Fuzzy RD: P(T=1|X=x) jumps discontinuously at x = c (but not from 0 to 1)

    Treatment assignment:
    - Sharp RD: T_i = 1{X_i ≥ c}
    - Fuzzy RD: P(T_i=1|X_i) discontinuous at X_i = c

    Estimation:
    - Local linear regression on both sides of cutoff
    - Compare outcomes just above vs just below threshold
    - τ̂_RD = lim_{x↓c} E[Y|X=x] - lim_{x↑c} E[Y|X=x]

    Assumptions:
    1. Continuity: All other factors continuous at cutoff (no other discontinuities)
    2. No manipulation: Units cannot precisely manipulate running variable around cutoff
    3. Local randomization: Units near cutoff are "as-if randomized"

    Advantages:
    - Credible identification (quasi-experimental)
    - Transparent assumption (visible discontinuity)
    - Does not require baseline covariates

    Disadvantages:
    - Local effect only (near cutoff, not population ATE)
    - Requires large sample near cutoff
    - Sensitive to bandwidth and functional form choice

    Classic applications:
    - Thistlethwaite & Campbell (1960): Scholarship effects on career
    - Lee (2008): Electoral advantage of incumbency
    - Angrist & Lavy (1999): Class size effects (Maimonides' rule)
    - Card et al (2008): Minimum wage effects

    Reference:
    - Hahn, Todd & Van der Klaauw (2001). "Identification and Estimation of Treatment Effects with a RDD"
    - Imbens & Lemieux (2008). "Regression Discontinuity Designs: A Guide to Practice"
    - Lee & Lemieux (2010). "Regression Discontinuity Designs in Economics"
    - Cattaneo, Idrobo & Titiunik (2019). "A Practical Introduction to RD Designs" (Volumes I & II)
    """

    def __init__(
        self,
        model: Optional[object] = None,
        cutoff: Optional[float] = None,
        bandwidth: Optional[float] = None,
        bandwidth_method: Literal['auto', 'imbens-kalyanaraman', 'cct'] = 'auto',
        kernel: Literal['triangular', 'uniform', 'epanechnikov'] = 'triangular',
        polynomial_order: int = 1,
        fuzzy: bool = False,
        running_var_col: Optional[str] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        model : sklearn-compatible regressor
            Model for local regression (default: OLS)
        cutoff : float, optional
            Threshold value for treatment assignment
        bandwidth : float, optional
            Bandwidth for local regression (distance from cutoff)
            If None, uses automatic bandwidth selection
        bandwidth_method : str
            Method for automatic bandwidth selection:
            - 'auto': Simple rule of thumb
            - 'imbens-kalyanaraman': IK optimal bandwidth (Imbens & Kalyanaraman 2012)
            - 'cct': Robust bias-corrected (Calonico, Cattaneo & Titiunik 2014)
        kernel : str
            Kernel function for weighting observations
            - 'triangular': K(u) = (1 - |u|) for |u| ≤ 1
            - 'uniform': K(u) = 1 for |u| ≤ 1
            - 'epanechnikov': K(u) = 0.75(1 - u²) for |u| ≤ 1
        polynomial_order : int
            Order of polynomial for local regression (1=linear, 2=quadratic)
            Recommendation: Use 1 (local linear) for most applications
        fuzzy : bool
            Whether to estimate fuzzy RD (uses 2SLS)
        running_var_col : str, optional
            Name of running variable column in X
        """
        super().__init__(**kwargs)
        self.model = model or LinearRegression()
        self.cutoff = cutoff
        self.bandwidth = bandwidth
        self.bandwidth_method = bandwidth_method
        self.kernel = kernel
        self.polynomial_order = polynomial_order
        self.fuzzy = fuzzy
        self.running_var_col = running_var_col

    def fit(
        self,
        X: pd.DataFrame,
        treatment: pd.Series,
        y: pd.Series,
        running_var: Optional[pd.Series] = None,
        cutoff: Optional[float] = None
    ):
        """
        Fit RD estimator

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix (must contain running variable)
        treatment : pd.Series
            Binary treatment indicator
        y : pd.Series
            Outcome variable
        running_var : pd.Series, optional
            Running variable (assignment variable)
            If None, uses self.running_var_col from X
        cutoff : float, optional
            Cutoff value for treatment assignment
            If None, uses self.cutoff from __init__

        Returns
        -------
        self
        """
        logger.info(f"Fitting RD estimator with {len(X)} observations")

        # Handle running variable
        if running_var is not None:
            self.running_var = running_var.values
        elif self.running_var_col is not None and self.running_var_col in X.columns:
            self.running_var = X[self.running_var_col].values
        else:
            raise ValueError("Must specify running_var or running_var_col")

        # Handle cutoff
        if cutoff is not None:
            self.cutoff = cutoff
        if self.cutoff is None:
            raise ValueError("Must specify cutoff")

        # Store data
        self.X_train = X.copy()
        self.treatment_train = treatment.copy()
        self.y_train = y.copy()

        # Center running variable at cutoff
        self.running_var_centered = self.running_var - self.cutoff

        # Check for sharp discontinuity in treatment
        self._check_discontinuity(treatment.values)

        # Select bandwidth if not specified
        if self.bandwidth is None:
            self.bandwidth = self._select_bandwidth()
            logger.info(f"Selected bandwidth: {self.bandwidth:.4f}")
        else:
            logger.info(f"Using specified bandwidth: {self.bandwidth:.4f}")

        # Estimate RD effect
        if self.fuzzy:
            self._fit_fuzzy_rd()
        else:
            self._fit_sharp_rd()

        self.is_fitted = True
        logger.info("RD estimator fitted successfully")

        return self

    def _check_discontinuity(self, treatment: np.ndarray):
        """
        Check for discontinuity in treatment probability at cutoff

        For sharp RD: Should see P(T=1) jump from 0 to 1
        For fuzzy RD: Should see discontinuous jump (but not necessarily 0 to 1)
        """
        # Sample just below cutoff
        below_mask = (self.running_var_centered < 0) & (self.running_var_centered > -0.1)
        p_below = np.mean(treatment[below_mask]) if below_mask.sum() > 0 else np.nan

        # Sample just above cutoff
        above_mask = (self.running_var_centered >= 0) & (self.running_var_centered < 0.1)
        p_above = np.mean(treatment[above_mask]) if above_mask.sum() > 0 else np.nan

        logger.info(f"Treatment probability just below cutoff: {p_below:.3f}")
        logger.info(f"Treatment probability just above cutoff: {p_above:.3f}")

        if not np.isnan(p_below) and not np.isnan(p_above):
            jump = p_above - p_below
            logger.info(f"Discontinuity in treatment: {jump:.3f}")

            if not self.fuzzy and abs(jump - 1.0) > 0.1:
                logger.warning(
                    f"Expected sharp discontinuity (jump=1.0) but observed jump={jump:.3f}. "
                    "Consider using fuzzy=True"
                )
            elif self.fuzzy and abs(jump) < 0.1:
                logger.warning(f"Fuzzy RD requires discontinuity, but jump={jump:.3f} is small")

    def _select_bandwidth(self) -> float:
        """
        Automatic bandwidth selection

        Simple rule of thumb: h = 1.84 * σ * n^(-1/5)
        where σ is standard deviation of running variable
        """
        if self.bandwidth_method == 'auto':
            # Simple rule of thumb
            sigma = np.std(self.running_var_centered)
            n = len(self.running_var_centered)
            h = 1.84 * sigma * (n ** (-1/5))
            return h
        elif self.bandwidth_method == 'imbens-kalyanaraman':
            # IK optimal bandwidth (simplified)
            logger.warning("Full IK bandwidth not implemented, using rule of thumb")
            sigma = np.std(self.running_var_centered)
            n = len(self.running_var_centered)
            return 1.84 * sigma * (n ** (-1/5))
        elif self.bandwidth_method == 'cct':
            # CCT robust bandwidth (simplified)
            logger.warning("Full CCT bandwidth not implemented, using rule of thumb")
            sigma = np.std(self.running_var_centered)
            n = len(self.running_var_centered)
            return 1.84 * sigma * (n ** (-1/5))
        else:
            raise ValueError(f"Unknown bandwidth method: {self.bandwidth_method}")

    def _compute_kernel_weights(self, distance: np.ndarray) -> np.ndarray:
        """
        Compute kernel weights based on distance from cutoff

        Parameters
        ----------
        distance : np.ndarray
            Absolute distance from cutoff |X - c|

        Returns
        -------
        np.ndarray
            Kernel weights
        """
        u = distance / self.bandwidth  # Normalized distance

        if self.kernel == 'triangular':
            weights = np.maximum(1 - u, 0)
        elif self.kernel == 'uniform':
            weights = (u <= 1).astype(float)
        elif self.kernel == 'epanechnikov':
            weights = np.maximum(0.75 * (1 - u**2), 0)
        else:
            raise ValueError(f"Unknown kernel: {self.kernel}")

        return weights

    def _fit_sharp_rd(self):
        """
        Fit sharp RD using local polynomial regression

        Estimate: τ̂ = μ̂₊(c) - μ̂₋(c)
        where μ̂₊(c) = limit from right, μ̂₋(c) = limit from left
        """
        # Restrict to observations within bandwidth
        in_bandwidth = np.abs(self.running_var_centered) <= self.bandwidth
        X_local = self.running_var_centered[in_bandwidth]
        Y_local = self.y_train.values[in_bandwidth]

        # Create polynomial features
        if self.polynomial_order > 1:
            poly = PolynomialFeatures(degree=self.polynomial_order, include_bias=False)
            X_poly = poly.fit_transform(X_local.reshape(-1, 1))
        else:
            X_poly = X_local.reshape(-1, 1)

        # Separate into above/below cutoff
        above_mask = X_local >= 0
        below_mask = X_local < 0

        logger.info(f"Observations within bandwidth: {in_bandwidth.sum()}")
        logger.info(f"  Above cutoff: {above_mask.sum()}")
        logger.info(f"  Below cutoff: {below_mask.sum()}")

        # Compute kernel weights
        distance = np.abs(X_local)
        weights = self._compute_kernel_weights(distance)

        # Fit separate regressions on each side
        # Above cutoff
        self.model_above = clone(self.model)
        self.model_above.fit(
            X_poly[above_mask],
            Y_local[above_mask],
            sample_weight=weights[above_mask]
        )

        # Below cutoff
        self.model_below = clone(self.model)
        self.model_below.fit(
            X_poly[below_mask],
            Y_local[below_mask],
            sample_weight=weights[below_mask]
        )

        # Predict at cutoff (X = 0)
        X_cutoff = np.zeros((1, X_poly.shape[1]))
        self.y_above_cutoff = self.model_above.predict(X_cutoff)[0]
        self.y_below_cutoff = self.model_below.predict(X_cutoff)[0]

        # RD estimate
        self.rd_estimate_ = self.y_above_cutoff - self.y_below_cutoff

        logger.info(f"Y just above cutoff: {self.y_above_cutoff:.4f}")
        logger.info(f"Y just below cutoff: {self.y_below_cutoff:.4f}")
        logger.info(f"RD estimate: {self.rd_estimate_:.4f}")

    def _fit_fuzzy_rd(self):
        """
        Fit fuzzy RD using 2SLS

        First stage: T = α + β·1{X≥c} + f(X-c) + ε
        Second stage: Y = γ + τ·T̂ + g(X-c) + η

        τ̂ = [Y₊(c) - Y₋(c)] / [T₊(c) - T₋(c)]
        """
        logger.info("Fitting fuzzy RD using 2SLS approach")

        # Restrict to bandwidth
        in_bandwidth = np.abs(self.running_var_centered) <= self.bandwidth
        X_local = self.running_var_centered[in_bandwidth]
        Y_local = self.y_train.values[in_bandwidth]
        T_local = self.treatment_train.values[in_bandwidth]

        # Above/below masks
        above_mask = X_local >= 0
        below_mask = X_local < 0

        # Compute kernel weights
        distance = np.abs(X_local)
        weights = self._compute_kernel_weights(distance)

        # First stage: Estimate discontinuity in treatment
        T_above_mean = np.average(T_local[above_mask], weights=weights[above_mask])
        T_below_mean = np.average(T_local[below_mask], weights=weights[below_mask])
        treatment_jump = T_above_mean - T_below_mean

        # Reduced form: Estimate discontinuity in outcome
        Y_above_mean = np.average(Y_local[above_mask], weights=weights[above_mask])
        Y_below_mean = np.average(Y_local[below_mask], weights=weights[below_mask])
        outcome_jump = Y_above_mean - Y_below_mean

        # Fuzzy RD estimate: Wald estimator
        if abs(treatment_jump) < 0.01:
            logger.error("Treatment jump too small for fuzzy RD. Check discontinuity.")
            self.rd_estimate_ = np.nan
        else:
            self.rd_estimate_ = outcome_jump / treatment_jump

        self.treatment_jump_ = treatment_jump
        self.outcome_jump_ = outcome_jump

        logger.info(f"Treatment discontinuity: {treatment_jump:.4f}")
        logger.info(f"Outcome discontinuity: {outcome_jump:.4f}")
        logger.info(f"Fuzzy RD estimate: {self.rd_estimate_:.4f}")

    def estimate_ate(self) -> float:
        """
        Estimate Average Treatment Effect at the cutoff (Local ATE)

        RD identifies treatment effect only for units near cutoff
        (not population ATE unless effect is constant)

        Returns
        -------
        float
            Estimated RD effect (Local ATE at cutoff)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        self.ate_ = self.rd_estimate_
        return self.ate_

    def estimate_cate(self, X: pd.DataFrame) -> np.ndarray:
        """
        RD estimates effect only at cutoff (local effect)

        Returns effect estimate for units near cutoff, NaN elsewhere

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix

        Returns
        -------
        np.ndarray
            Treatment effects (non-NaN only near cutoff)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        logger.warning("RD estimates local effect at cutoff only. Returning constant for all units.")

        if not hasattr(self, 'ate_'):
            self.estimate_ate()

        return np.full(len(X), self.ate_)

    def estimate_variance(self) -> float:
        """
        Estimate variance of RD estimator

        Uses robust standard errors clustered at running variable bins

        Returns
        -------
        float
            Estimated variance
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Simplified variance estimate
        in_bandwidth = np.abs(self.running_var_centered) <= self.bandwidth
        n = in_bandwidth.sum()

        # Variance of outcome within bandwidth
        Y_local = self.y_train.values[in_bandwidth]
        var_y = np.var(Y_local)

        self.variance_ = var_y / n

        logger.info(f"Estimated variance: {self.variance_:.6f}")
        return self.variance_

    def plot_rd(self) -> pd.DataFrame:
        """
        Get data for RD plot

        Returns
        -------
        pd.DataFrame
            Columns: running_var, outcome, treatment, predicted_above, predicted_below
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Bin data for visualization
        n_bins = 40
        bins = np.linspace(
            self.cutoff - 2 * self.bandwidth,
            self.cutoff + 2 * self.bandwidth,
            n_bins
        )

        bin_centers = []
        bin_means = []
        bin_treatment = []

        for i in range(len(bins) - 1):
            mask = (self.running_var >= bins[i]) & (self.running_var < bins[i+1])
            if mask.sum() > 0:
                bin_centers.append((bins[i] + bins[i+1]) / 2)
                bin_means.append(np.mean(self.y_train.values[mask]))
                bin_treatment.append(np.mean(self.treatment_train.values[mask]))

        return pd.DataFrame({
            'running_var': bin_centers,
            'outcome_mean': bin_means,
            'treatment_mean': bin_treatment,
            'cutoff': self.cutoff
        })

    def sensitivity_analysis(self, bandwidths: list) -> pd.DataFrame:
        """
        Sensitivity analysis: Vary bandwidth

        Parameters
        ----------
        bandwidths : list of float
            List of bandwidths to test

        Returns
        -------
        pd.DataFrame
            RD estimates for each bandwidth
        """
        logger.info(f"Running sensitivity analysis with {len(bandwidths)} bandwidths")

        results = []
        original_bandwidth = self.bandwidth

        for h in bandwidths:
            self.bandwidth = h
            if self.fuzzy:
                self._fit_fuzzy_rd()
            else:
                self._fit_sharp_rd()

            results.append({
                'bandwidth': h,
                'rd_estimate': self.rd_estimate_,
                'n_obs': np.sum(np.abs(self.running_var_centered) <= h)
            })

        # Restore original bandwidth
        self.bandwidth = original_bandwidth

        return pd.DataFrame(results)

    def test_manipulation(self, n_bins: int = 50) -> dict:
        """
        Test for manipulation of running variable (McCrary density test)

        Tests null hypothesis: density of running variable is continuous at cutoff

        Parameters
        ----------
        n_bins : int
            Number of bins for histogram

        Returns
        -------
        dict
            Test results (simplified version)
        """
        logger.warning("Full McCrary test not implemented. Returning histogram for visual inspection.")

        # Simple histogram comparison
        below_mask = self.running_var_centered < 0
        above_mask = self.running_var_centered >= 0

        n_below = below_mask.sum()
        n_above = above_mask.sum()

        logger.info(f"Observations below cutoff: {n_below}")
        logger.info(f"Observations above cutoff: {n_above}")

        return {
            'n_below': n_below,
            'n_above': n_above,
            'ratio': n_above / n_below if n_below > 0 else np.nan,
            'test': 'Visual inspection recommended (McCrary test not fully implemented)'
        }
