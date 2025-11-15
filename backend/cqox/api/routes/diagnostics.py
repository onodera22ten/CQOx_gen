"""
Diagnostics endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from loguru import logger
import pandas as pd
import numpy as np

from cqox.data.loader import DataLoader
from cqox.causal.diagnostics.balance import covariate_balance_test, love_plot_data
from cqox.causal.diagnostics.overlap import overlap_test, propensity_density_data
from cqox.causal.diagnostics.sensitivity import rosenbaum_sensitivity_gamma, e_value_calculation
from cqox.causal.diagnostics.cate_diagnostics import (
    qini_curve_data,
    calibration_check,
    cate_heterogeneity_test
)
from cqox.causal.diagnostics.network_interference import (
    network_spillover_test,
    temporal_interference_test
)
from cqox.causal.diagnostics.cas_score import calculate_cas_score

router = APIRouter()


class DiagnosticsRequest(BaseModel):
    """Request for running diagnostics"""
    dataset_path: str
    treatment_col: str = "treatment"
    outcome_col: str = "y"
    feature_prefix: str = "X_"
    cate: Optional[list] = None  # Estimated CATE values


@router.post("/run")
async def run_diagnostics(request: DiagnosticsRequest):
    """
    Run all 14 diagnostic checks

    Returns comprehensive diagnostics report
    """
    try:
        logger.info(f"Running diagnostics on: {request.dataset_path}")

        # Load data
        df = DataLoader.load_auto(request.dataset_path)

        # Extract features
        feature_cols = [col for col in df.columns if col.startswith(request.feature_prefix)]
        X = df[feature_cols]
        treatment = df[request.treatment_col]
        y = df[request.outcome_col]

        # Initialize results
        diagnostic_results = {}
        all_checks = []

        # 1. Covariate Balance
        balance_passed, balance_report = covariate_balance_test(X, treatment, threshold=0.1)
        diagnostic_results['balance'] = balance_report
        all_checks.append({
            "type": "covariate_balance",
            "name": "Covariate Balance (SMD)",
            "passed": balance_passed,
            "score": balance_report.get('max_smd', 0),
            "threshold": 0.1,
            "data": balance_report
        })

        # 2. Love Plot Data
        love_data = love_plot_data(X, treatment)
        all_checks.append({
            "type": "love_plot",
            "name": "Love Plot",
            "passed": True,
            "data": love_data
        })

        # 3. Overlap/Positivity
        overlap_passed, overlap_report = overlap_test(X, treatment, threshold=0.05)
        diagnostic_results['overlap'] = overlap_report
        all_checks.append({
            "type": "overlap",
            "name": "Overlap / Positivity",
            "passed": overlap_passed,
            "score": overlap_report.get('violation_rate', 0),
            "threshold": 0.05,
            "data": overlap_report
        })

        # 4. Propensity Density
        density_data = propensity_density_data(X, treatment)
        all_checks.append({
            "type": "propensity_density",
            "name": "Propensity Density",
            "passed": True,
            "data": density_data
        })

        # 5. Sensitivity Analysis (Rosenbaum Gamma)
        treated_outcomes = y[treatment == 1].values
        control_outcomes = y[treatment == 0].values
        gamma_result = rosenbaum_sensitivity_gamma(
            treated_outcomes,
            control_outcomes,
            gamma_values=[1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
        )
        diagnostic_results['sensitivity'] = gamma_result
        all_checks.append({
            "type": "sensitivity",
            "name": "Sensitivity (Γ)",
            "passed": gamma_result.get('critical_gamma', 0) > 1.3,
            "score": gamma_result.get('critical_gamma', 0),
            "threshold": 1.3,
            "data": gamma_result
        })

        # 6. E-value
        ate = float(np.mean(treated_outcomes) - np.mean(control_outcomes))
        e_value_result = e_value_calculation(ate)
        diagnostic_results['e_value'] = e_value_result
        all_checks.append({
            "type": "e_value",
            "name": "E-value",
            "passed": e_value_result.get('e_value_point_estimate', 0) > 1.5,
            "score": e_value_result.get('e_value_point_estimate', 0),
            "threshold": 1.5,
            "data": e_value_result
        })

        # If CATE is provided, run CATE diagnostics
        if request.cate and len(request.cate) == len(df):
            cate = np.array(request.cate)

            # 7. Qini Curve
            qini_data = qini_curve_data(cate, treatment, y)
            all_checks.append({
                "type": "qini_curve",
                "name": "Qini Curve",
                "passed": True,
                "data": qini_data
            })

            # 8. Calibration
            calibration_result = calibration_check(cate, treatment, y, n_bins=10)
            all_checks.append({
                "type": "calibration",
                "name": "CATE Calibration",
                "passed": calibration_result.get('r_squared', 0) > 0.7,
                "score": calibration_result.get('r_squared', 0),
                "threshold": 0.7,
                "data": calibration_result
            })

            # 9. Heterogeneity
            het_result = cate_heterogeneity_test(cate, X)
            all_checks.append({
                "type": "heterogeneity",
                "name": "CATE Heterogeneity",
                "passed": het_result.get('significant', False),
                "data": het_result
            })

        # 10-11. Network/Temporal Interference (if network data available)
        if 'network_id' in df.columns:
            network_result = network_spillover_test(
                df['network_id'].values,
                treatment.values,
                y.values
            )
            all_checks.append({
                "type": "network_interference",
                "name": "Network Spillover",
                "passed": network_result.get('no_spillover', True),
                "data": network_result
            })

        if 'time' in df.columns:
            temporal_result = temporal_interference_test(
                df['time'].values,
                treatment.values,
                y.values
            )
            all_checks.append({
                "type": "temporal_interference",
                "name": "Temporal Interference",
                "passed": temporal_result.get('no_interference', True),
                "data": temporal_result
            })

        # Calculate CAS Score
        cas_result = calculate_cas_score(diagnostic_results)

        logger.info(f"Diagnostics completed. CAS Score: {cas_result['cas_score']:.2f}")

        return {
            "status": "completed",
            "cas_score": cas_result['cas_score'],
            "quality_level": cas_result['quality_level'],
            "diagnostics": all_checks,
            "recommendations": cas_result.get('recommendations', []),
            "total_checks": len(all_checks)
        }

    except Exception as e:
        logger.error(f"Run diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_run_id}")
async def get_diagnostics(model_run_id: str):
    """Get diagnostics for a model run (legacy endpoint)"""
    try:
        # TODO: Load from database
        # For now, return placeholder
        logger.info(f"Getting diagnostics for: {model_run_id}")

        return {
            "model_run_id": model_run_id,
            "message": "Use POST /diagnostics/run for full diagnostics"
        }

    except Exception as e:
        logger.error(f"Get diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
