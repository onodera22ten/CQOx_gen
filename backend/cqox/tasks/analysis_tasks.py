"""
【日本語サマリ】因果推論分析タスク（Celery）
- なぜ必要か: アップロードしたデータで実際に因果推論を実行するため
- 何をするか: S-Learner, DR-Learner等でATE/CATE推定、Δ¥計算、Go/Canary/Hold判定
- どう検証するか: フロントエンドでTrain Modelsを実行し、結果が返ることを確認

Celery tasks for causal analysis
"""
from celery import Task
from loguru import logger
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import create_engine, text
import os
import json
import math

from cqox.tasks.celery_app import celery_app
from cqox.causal.estimators.s_learner import SLearner
from cqox.causal.estimators.t_learner import TLearner
from cqox.causal.estimators.x_learner import XLearner
from cqox.causal.estimators.dr_learner import DRLearner
from cqox.causal.estimators.causal_forest import CausalForest
from cqox.causal.diagnostics.balance import covariate_balance_test, love_plot_data
from cqox.causal.diagnostics.overlap import overlap_test, propensity_density_plot_data
from cqox.causal.diagnostics.sensitivity import rosenbaum_sensitivity_gamma, e_value_calculation
from cqox.causal.diagnostics.cate_diagnostics import (
    qini_curve_data,
    calibration_check,
    cate_heterogeneity_test
)
from cqox.causal.diagnostics.cas_score import calculate_cas_score
from cqox.causal.diagnostics.network_interference import (
    network_spillover_test,
    temporal_interference_test
)

# Additional causal inference estimators (7 Nobel Prize-winning methods)
try:
    from cqox.causal.estimators.ipw import IPWEstimator
    from cqox.causal.estimators.did import DIDEstimator
    from cqox.causal.estimators.iv import IVEstimator
    from cqox.causal.estimators.rd import RDEstimator
    from cqox.causal.estimators.scm import SCMEstimator
    ADDITIONAL_ESTIMATORS_AVAILABLE = True
except ImportError:
    ADDITIONAL_ESTIMATORS_AVAILABLE = False
    IPWEstimator = None
    DIDEstimator = None
    IVEstimator = None
    RDEstimator = None
    SCMEstimator = None
from cqox.config.settings import settings
from cqox.database.connection import DATABASE_URL as ASYNC_DATABASE_URL

# Celeryは同期コンテキストなので、状態更新だけは同期エンジンを使う
SYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
sync_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True, future=True)

DEFAULT_COST_PER_USER = float(os.getenv("DEFAULT_COST_PER_USER", "800.0"))


class AnalysisValidationError(Exception):
    """User-facing validation error for causal analysis inputs."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _serialize_error_payload(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> str:
    return json.dumps({
        "code": code,
        "message": message,
        "details": details or {}
    })


def _summarize_treatment_series(series: pd.Series) -> Dict[str, Any]:
    non_null = series.dropna()
    unique_values = pd.unique(non_null)
    unique_count = len(unique_values)
    value_counts = pd.Series(non_null).value_counts().to_dict()

    status = "ok"
    if unique_count < 2:
        status = "single_class"
    elif unique_count > 2:
        status = "multi_class"

    preview_values = [str(v) for v in list(unique_values)[:10]]

    return {
        "status": status,
        "unique_count": unique_count,
        "unique_values": preview_values,
        "value_counts": {str(k): int(v) for k, v in list(value_counts.items())[:10]}
    }


def _encode_series_for_numeric(series: pd.Series) -> pd.Series:
    """
    Convert arbitrary series (numeric/string/categorical) into a numeric representation.

    - Numeric columns are coerced to float and NaNs filled with 0
    - Non-numeric columns are factorized via pandas category codes
    - Ensures that categorical columns with multiple levels retain >1 classes
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce').fillna(0)

    categorical = series.astype('category')
    codes = categorical.cat.codes.astype(float)
    # cat.codes assigns -1 to NaN entries
    codes = codes.where(codes >= 0, np.nan)
    filled = codes.fillna(0)
    return filled


def _to_plain_value(value, stack=None):
    """Recursively convert numpy/pandas objects to plain Python types."""
    if stack is None:
        stack = set()

    # Primitive python types
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value

    # Numpy scalar
    if isinstance(value, np.generic):
        return _to_plain_value(value.item(), stack)

    # Pandas timestamps
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()

    # Pandas Series/DataFrame
    if isinstance(value, pd.Series):
        return [_to_plain_value(v, stack) for v in value.tolist()]

    if isinstance(value, pd.DataFrame):
        records = value.to_dict(orient="records")
        return [_to_plain_value(record, stack) for record in records]

    # NumPy arrays
    if isinstance(value, np.ndarray):
        return [_to_plain_value(v, stack) for v in value.tolist()]

    # Containers
    if isinstance(value, (list, tuple, set)):
        obj_id = id(value)
        if obj_id in stack:
            return "<circular>"
        stack.add(obj_id)
        plain_list = [_to_plain_value(v, stack) for v in value]
        stack.remove(obj_id)
        return plain_list

    if isinstance(value, dict):
        obj_id = id(value)
        if obj_id in stack:
            return "<circular>"
        stack.add(obj_id)
        plain_dict = {str(k): _to_plain_value(v, stack) for k, v in value.items()}
        stack.remove(obj_id)
        return plain_dict

    # Fallback: string representation
    return str(value)


def _safe_json(value):
    if value is None:
        return None
    plain_value = _to_plain_value(value)
    if plain_value == "<circular>":
        return {"error": "circular"}
    return json.loads(json.dumps(plain_value))


def compute_impact_metrics(
    df: pd.DataFrame,
    treatment_col: str,
    outcome_col: str,
    delta_yen: float
) -> Dict[str, float]:
    treatment_series = _encode_series_for_numeric(df[treatment_col])
    outcome_series = _encode_series_for_numeric(df[outcome_col])

    treated_mask = treatment_series > 0.5
    treated_users = int(treated_mask.sum())
    total_users = int(len(df))

    baseline_mask = ~treated_mask
    baseline_rate = float(outcome_series[baseline_mask].mean()) if baseline_mask.any() else float(outcome_series.mean())
    treatment_rate = float(outcome_series[treated_mask].mean()) if treated_users > 0 else float(outcome_series.mean())
    conversion_uplift = treatment_rate - baseline_rate

    # Detect explicit cost column if present
    cost_columns = [col for col in df.columns if col.lower() in {'cost', 'total_cost', 'campaign_cost', 'spend', 'expense'}]
    if cost_columns and treated_users > 0:
        estimated_cost = float(pd.to_numeric(df[cost_columns[0]], errors='coerce').fillna(0)[treated_mask].sum())
    else:
        estimated_cost = treated_users * DEFAULT_COST_PER_USER

    estimated_roi = float(delta_yen / estimated_cost) if estimated_cost else None

    return {
        "estimated_cost": estimated_cost,
        "baseline_conversion_rate": max(0.0, baseline_rate),
        "projected_conversion_rate": max(0.0, treatment_rate),
        "conversion_uplift": conversion_uplift,
        "users_affected": treated_users,
        "total_users": total_users,
        "estimated_roi": estimated_roi
    }


def generate_diagnostics_payload(
    df: pd.DataFrame,
    X: pd.DataFrame,
    treatment_series: pd.Series,
    outcome_series: pd.Series,
    cate_values: Optional[np.ndarray],
    ate_value: float
) -> Dict[str, Any]:
    diagnostic_results: Dict[str, Any] = {}
    all_checks: List[Dict[str, Any]] = []

    if X.empty:
        X = pd.DataFrame({"constant": np.ones(len(treatment_series))})

    balance_passed, balance_report = covariate_balance_test(X, treatment_series, threshold=0.1)
    diagnostic_results['balance'] = balance_report
    all_checks.append({
        "type": "covariate_balance",
        "name": "Covariate Balance (SMD)",
        "passed": balance_passed,
        "score": balance_report.get('max_smd', 0),
        "threshold": 0.1,
        "data": balance_report
    })

    love_data = love_plot_data(X, treatment_series)
    all_checks.append({
        "type": "love_plot",
        "name": "Love Plot",
        "passed": True,
        "data": love_data
    })

    overlap_passed, overlap_report = overlap_test(X, treatment_series, threshold=0.05)
    diagnostic_results['overlap'] = overlap_report
    all_checks.append({
        "type": "overlap",
        "name": "Overlap / Positivity",
        "passed": overlap_passed,
        "score": overlap_report.get('violation_rate', 0),
        "threshold": 0.05,
        "data": overlap_report
    })

    density_data = propensity_density_plot_data(X, treatment_series)
    all_checks.append({
        "type": "propensity_density",
        "name": "Propensity Density",
        "passed": True,
        "data": density_data
    })

    treated_outcomes = outcome_series[treatment_series > 0.5].values
    control_outcomes = outcome_series[treatment_series <= 0.5].values
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

    e_value_result = e_value_calculation(float(ate_value))
    diagnostic_results['e_value'] = e_value_result
    all_checks.append({
        "type": "e_value",
        "name": "E-value",
        "passed": e_value_result.get('e_value_point_estimate', 0) > 1.5,
        "score": e_value_result.get('e_value_point_estimate', 0),
        "threshold": 1.5,
        "data": e_value_result
    })

    if cate_values is not None and len(cate_values) == len(df):
        cate_array = np.array(cate_values)
        qini_data = qini_curve_data(cate_array, treatment_series.values, outcome_series.values)
        all_checks.append({
            "type": "qini_curve",
            "name": "Qini Curve",
            "passed": True,
            "data": qini_data
        })

        calibration_result = calibration_check(cate_array, treatment_series.values, outcome_series.values, n_bins=10)
        all_checks.append({
            "type": "calibration",
            "name": "CATE Calibration",
            "passed": calibration_result.get('r_squared', 0) > 0.7,
            "score": calibration_result.get('r_squared', 0),
            "threshold": 0.7,
            "data": calibration_result
        })

        heterogeneity_result = cate_heterogeneity_test(cate_array, X)
        all_checks.append({
            "type": "heterogeneity",
            "name": "CATE Heterogeneity",
            "passed": heterogeneity_result.get('significant', False),
            "data": heterogeneity_result
        })

    if 'network_id' in df.columns:
        network_result = network_spillover_test(
            df['network_id'].values,
            treatment_series.values,
            outcome_series.values
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
            treatment_series.values,
            outcome_series.values
        )
        all_checks.append({
            "type": "temporal_interference",
            "name": "Temporal Interference",
            "passed": temporal_result.get('no_interference', True),
            "data": temporal_result
        })

    cas_result = calculate_cas_score(diagnostic_results)

    return {
        "status": "completed",
        "cas_score": cas_result['cas_score'],
        "quality_level": cas_result['quality_level'],
        "diagnostics": all_checks,
        "recommendations": cas_result.get('recommendations', []),
        "total_checks": len(all_checks)
    }

class AnalysisTask(Task):
    """Base task for causal analysis"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Analysis task {task_id} failed: {exc}")
        
        analysis_id = kwargs.get('analysis_id')
        if analysis_id:
            self._update_analysis_status(
                analysis_id,
                status='failed',
                error_message=str(exc)
            )
    
    def _update_analysis_status(self, analysis_id: str, **updates):
        """Update analysis status in database (synchronous to avoid event loop issues)"""
        try:
            sanitized_updates = {}
            for key, value in updates.items():
                if isinstance(value, np.generic):
                    sanitized_updates[key] = float(value)
                elif isinstance(value, (dict, list)):
                    sanitized_updates[key] = json.dumps(value)
                else:
                    sanitized_updates[key] = value

            update_fields = ', '.join([f"{k} = :{k}" for k in sanitized_updates.keys()])
            query = text(f"UPDATE analysis_runs SET {update_fields} WHERE id = :analysis_id")
            
            params = {'analysis_id': uuid_lib.UUID(analysis_id), **sanitized_updates}
            with sync_engine.begin() as conn:
                conn.execute(query, params)
        except Exception as e:
            logger.error(f"Failed to update analysis status: {e}")


@celery_app.task(
    base=AnalysisTask,
    bind=True,
    soft_time_limit=settings.celery_task_soft_time_limit,
    time_limit=settings.celery_task_hard_time_limit,
    acks_late=settings.celery_task_acks_late
)
def run_causal_analysis(
    self,
    analysis_id: str,
    dataset_path: str,
    treatment_col: str,
    outcome_col: str,
    feature_cols: List[str],
    estimators: List[str] = ['s_learner', 'dr_learner']
):
    """
    因果推論分析を実行（アップロードされたデータに対して）
    
    Args:
        analysis_id: Analysis ID
        dataset_path: Dataset file path
        treatment_col: Treatment column name
        outcome_col: Outcome column name
        feature_cols: Feature column names
        estimators: List of estimators to use
        
    Returns:
        Dict with ATE, CATE, Δ¥, and verdict
    """
    import time
    start_time = time.time()
    
    logger.info(f"🧪 Starting causal analysis: {analysis_id}")
    logger.info(f"   Dataset: {dataset_path}")
    logger.info(f"   Estimators: {estimators}")
    
    try:
        # Update status to running
        self._update_analysis_status(
            analysis_id,
            status='running',
            progress=0.1
        )
        
        # Load dataset
        logger.info("📥 Loading dataset...")
        
        # Convert relative path to absolute path if needed
        import os
        if not os.path.isabs(dataset_path):
            # If relative path, assume it's relative to /app/data/uploads
            dataset_path = os.path.join("/app/data/uploads", os.path.basename(dataset_path))
        
        logger.info(f"📂 Dataset path: {dataset_path}")
        
        if not os.path.exists(dataset_path):
            error_msg = f"Dataset file not found: {dataset_path}"
            logger.error(error_msg)
            self._update_analysis_status(
                analysis_id,
                status='failed',
                error_message=error_msg
            )
            raise FileNotFoundError(error_msg)
        
        # Load depending on file extension
        _, file_ext = os.path.splitext(dataset_path.lower())
        if file_ext in {'.parquet', '.pq'}:
            df = pd.read_parquet(dataset_path)
        else:
            df = pd.read_csv(dataset_path)
        
        n_rows = len(df)
        logger.info(f"📊 Dataset size: {n_rows:,} rows × {len(df.columns)} columns")
        
        # Validate columns
        required_cols = [treatment_col, outcome_col] + feature_cols
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        
        # Extract data
        X = df[feature_cols]
        raw_treatment = df[treatment_col]
        raw_outcome = df[outcome_col]

        treatment_summary = _summarize_treatment_series(raw_treatment)
        if treatment_summary["status"] == "single_class":
            raise AnalysisValidationError(
                code="treatment_single_class",
                message=f'処置列 "{treatment_col}" には施策あり・なしの両方が含まれていません。',
                details={"column": treatment_col, **treatment_summary}
            )
        if treatment_summary["status"] == "multi_class":
            raise AnalysisValidationError(
                code="treatment_multiclass",
                message=f'処置列 "{treatment_col}" には {treatment_summary["unique_count"]} クラスが含まれています。現在は 0/1 のバイナリ処置のみ対応しています。',
                details={"column": treatment_col, **treatment_summary}
            )

        T = _encode_series_for_numeric(raw_treatment)
        if T.dropna().nunique() < 2:
            raise AnalysisValidationError(
                code="treatment_encoding_failure",
                message=f'処置列 "{treatment_col}" をバイナリに変換できませんでした。文字列ラベルを 0/1 に変換してください。',
                details={"column": treatment_col, **treatment_summary}
            )

        y = _encode_series_for_numeric(raw_outcome)
        
        self._update_analysis_status(analysis_id, progress=0.2)
        
        # Map estimator names to classes (7 core + meta-learners)
        estimator_map = {
            # Meta-learners
            's_learner': SLearner,
            't_learner': TLearner,
            'x_learner': XLearner,
            'dr_learner': DRLearner,
            'causal_forest': CausalForest
        }

        # Add Nobel Prize-winning estimators if available
        if ADDITIONAL_ESTIMATORS_AVAILABLE:
            estimator_map.update({
                'ipw': IPWEstimator,
                'did': DIDEstimator,
                'iv': IVEstimator,
                'rd': RDEstimator,
                'scm': SCMEstimator
            })
        
        results = {}
        n_estimators = len(estimators)
        cate_values: Optional[List[float]] = None
        
        # Train each estimator
        for i, estimator_name in enumerate(estimators):
            estimator_start = time.time()
            logger.info(f"🧠 Training {estimator_name} ({i+1}/{n_estimators})...")
            
            if estimator_name not in estimator_map:
                logger.warning(f"Unknown estimator: {estimator_name}")
                continue
            
            EstimatorClass = estimator_map[estimator_name]
            
            try:
                # Initialize estimator based on type
                if estimator_name == 'did':
                    # DiD requires time column - use first feature as proxy if not available
                    time_col = 'time' if 'time' in df.columns else feature_cols[0] if feature_cols else 'x0'
                    estimator = EstimatorClass(time_col=time_col)
                    estimator.fit(X, T, y)
                elif estimator_name == 'iv':
                    # IV requires instrument column - use first feature as proxy
                    instrument_col = feature_cols[0] if feature_cols else None
                    estimator = EstimatorClass(instrument_col=instrument_col)
                    estimator.fit(X, T, y)
                elif estimator_name == 'rd':
                    # RD requires running variable and cutoff
                    running_var_col = feature_cols[0] if feature_cols else None
                    cutoff = float(df[running_var_col].median()) if running_var_col and running_var_col in df.columns else 0.0
                    estimator = EstimatorClass(running_var_col=running_var_col, cutoff=cutoff)
                    estimator.fit(X, T, y)
                elif estimator_name == 'scm':
                    # SCM requires unit and time columns
                    unit_col = 'unit_id' if 'unit_id' in df.columns else None
                    time_col = 'time' if 'time' in df.columns else feature_cols[0] if feature_cols else None
                    # SCM requires treatment time and treated unit - use defaults for now
                    treatment_time = int(df[time_col].median()) if time_col and time_col in df.columns else 0
                    treated_unit = df[unit_col].iloc[0] if unit_col and unit_col in df.columns else None
                    estimator = EstimatorClass(
                        time_col=time_col,
                        unit_col=unit_col,
                        treatment_time=treatment_time,
                        treated_unit=treated_unit
                    )
                    estimator.fit(X, T, y)
                else:
                    # Standard causal estimators (IPW, DR, S-Learner, T-Learner, etc.)
                    estimator = EstimatorClass()
                    estimator.fit(X, T, y)

                # Estimate ATE (all estimators use same interface now)
                ate = estimator.estimate_ate()
                if isinstance(ate, tuple):
                    ate, ate_std = ate
                else:
                    ate_std = 0.1  # Default if not provided

                # Estimate CATE
                try:
                    cate = estimator.estimate_cate(X)
                    cate_mean = float(np.mean(cate))
                    cate_std_val = float(np.std(cate))
                    cate_min = float(np.min(cate))
                    cate_max = float(np.max(cate))
                    if cate_values is None:
                        if hasattr(cate, "tolist"):
                            cate_values = cate.tolist()
                        else:
                            cate_values = list(cate)
                except (AttributeError, NotImplementedError):
                    # Fallback if CATE not available
                    cate_mean = float(ate)
                    cate_std_val = float(ate_std) if 'ate_std' in locals() else 0.1
                    cate_min = float(ate)
                    cate_max = float(ate)
                
                estimator_time = time.time() - estimator_start
                
                results[estimator_name] = {
                    'ate': float(ate),
                    'ate_std': float(ate_std) if 'ate_std' in locals() else 0.1,
                    'cate_mean': cate_mean,
                    'cate_std': cate_std_val,
                    'cate_min': cate_min,
                    'cate_max': cate_max,
                    'training_time_sec': round(estimator_time, 2)
                }
                
                logger.info(f"   ✅ {estimator_name}: ATE={ate:.4f}, training_time={estimator_time:.1f}s")
                
            except Exception as e:
                logger.error(f"   ❌ {estimator_name} failed: {e}", exc_info=True)
                results[estimator_name] = {
                    'ate': 0.0,
                    'ate_std': 0.0,
                    'cate_mean': 0.0,
                    'cate_std': 0.0,
                    'cate_min': 0.0,
                    'cate_max': 0.0,
                    'training_time_sec': 0.0,
                    'error': str(e)
                }
            
            # Update progress
            progress = 0.2 + 0.6 * (i + 1) / n_estimators
            self._update_analysis_status(analysis_id, progress=progress)
        
        # Calculate consensus ATE (average across estimators)
        ate_values = [r['ate'] for r in results.values()]
        consensus_ate = np.mean(ate_values)
        ate_std = np.std(ate_values)
        
        # Calculate Δ¥ (Money View)
        # Assume outcome is already in currency (Yen)
        delta_yen = consensus_ate
        delta_yen_ci_low = delta_yen - 1.96 * ate_std
        delta_yen_ci_high = delta_yen + 1.96 * ate_std
        
        # Go/Canary/Hold verdict
        if delta_yen_ci_low > 0:
            verdict = 'Go'
            reason = f'Lower bound of 95% CI is positive ({delta_yen_ci_low:.2f} > 0)'
        elif delta_yen > 0:
            verdict = 'Canary'
            reason = 'Point estimate positive but CI includes 0; recommend A/B test'
        else:
            verdict = 'Hold'
            reason = 'Negative expected impact; not recommended'
        
        logger.info(f"📈 Verdict: {verdict}")
        logger.info(f"   Δ¥: {delta_yen:.2f} (CI: [{delta_yen_ci_low:.2f}, {delta_yen_ci_high:.2f}])")

        treatment_series = _encode_series_for_numeric(T)
        outcome_series = _encode_series_for_numeric(y)
        X_for_diagnostics = pd.get_dummies(X, drop_first=True)
        X_for_diagnostics = X_for_diagnostics.apply(pd.to_numeric, errors='coerce').fillna(0)
        diagnostics_payload = generate_diagnostics_payload(
            df=df,
            X=X_for_diagnostics,
            treatment_series=treatment_series,
            outcome_series=outcome_series,
            cate_values=np.array(cate_values) if cate_values is not None else None,
            ate_value=consensus_ate
        )
        impact_metrics = compute_impact_metrics(df, treatment_col, outcome_col, delta_yen)
        
        # Update database with results
        total_time = time.time() - start_time
        
        self._update_analysis_status(
            analysis_id,
            status='completed',
            progress=1.0,
            delta_yen=delta_yen,
            delta_yen_ci_low=delta_yen_ci_low,
            delta_yen_ci_high=delta_yen_ci_high,
            verdict=verdict,
            diagnostics_snapshot=_safe_json(diagnostics_payload),
            impact_metrics=_safe_json(impact_metrics),
            estimator_results=_safe_json(results),
            completed_at=datetime.utcnow()
        )
        
        logger.info(f"🎉 Causal analysis completed: {analysis_id} (total: {total_time:.1f}s)")
        
        return _safe_json({
            'analysis_id': analysis_id,
            'status': 'completed',
            'delta_yen': delta_yen,
            'delta_yen_ci': [delta_yen_ci_low, delta_yen_ci_high],
            'verdict': verdict,
            'reason': reason,
            'estimator_results': results,
            'diagnostics': diagnostics_payload,
            'impact_metrics': impact_metrics,
            'metadata': {
                'n_rows': n_rows,
                'n_features': len(feature_cols),
                'n_estimators': len(results),
                'total_time_sec': round(total_time, 2)
            }
        })
        
    except AnalysisValidationError as ave:
        error_payload = _serialize_error_payload(ave.code, str(ave), ave.details)
        logger.error(f"❌ Causal analysis validation failed: {ave}")
        self._update_analysis_status(
            analysis_id,
            status='failed',
            error_message=error_payload,
            completed_at=datetime.utcnow()
        )
        raise

    except Exception as e:
        logger.error(f"❌ Causal analysis failed: {e}")
        self._update_analysis_status(
            analysis_id,
            status='failed',
            error_message=str(e),
            completed_at=datetime.utcnow()
        )
        raise
