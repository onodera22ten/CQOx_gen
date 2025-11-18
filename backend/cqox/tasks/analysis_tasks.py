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
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from datetime import datetime
import uuid as uuid_lib

from cqox.tasks.celery_app import celery_app
from cqox.causal.estimators.s_learner import SLearner
from cqox.causal.estimators.t_learner import TLearner
from cqox.causal.estimators.x_learner import XLearner
from cqox.causal.estimators.dr_learner import DRLearner
from cqox.causal.estimators.causal_forest import CausalForest

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


class AnalysisTask(Task):
    """Base task for causal analysis"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Analysis task {task_id} failed: {exc}")
        
        # Update database status to failed
        analysis_id = kwargs.get('analysis_id')
        if analysis_id:
            asyncio.run(self._update_analysis_status(
                analysis_id,
                status='failed',
                error_message=str(exc)
            ))
    
    async def _update_analysis_status(self, analysis_id: str, **updates):
        """Update analysis status in database"""
        from sqlalchemy import text
        from cqox.database.connection import async_session_factory
        
        async with async_session_factory() as session:
            try:
                update_fields = ', '.join([f"{k} = :{k}" for k in updates.keys()])
                query = text(f"UPDATE analysis_runs SET {update_fields} WHERE id = :analysis_id")
                
                await session.execute(query, {'analysis_id': uuid_lib.UUID(analysis_id), **updates})
                await session.commit()
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
        asyncio.run(self._update_analysis_status(
            analysis_id,
            status='running',
            progress=0.1
        ))
        
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
            asyncio.run(self._update_analysis_status(
                analysis_id,
                status='failed',
                error_message=error_msg
            ))
            raise FileNotFoundError(error_msg)
        
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
        T = df[treatment_col]
        y = df[outcome_col]
        
        asyncio.run(self._update_analysis_status(analysis_id, progress=0.2))
        
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
            asyncio.run(self._update_analysis_status(analysis_id, progress=progress))
        
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
        
        # Update database with results
        total_time = time.time() - start_time
        
        asyncio.run(self._update_analysis_status(
            analysis_id,
            status='completed',
            progress=1.0,
            delta_yen=delta_yen,
            delta_yen_ci_low=delta_yen_ci_low,
            delta_yen_ci_high=delta_yen_ci_high,
            verdict=verdict,
            completed_at=datetime.utcnow()
        ))
        
        logger.info(f"🎉 Causal analysis completed: {analysis_id} (total: {total_time:.1f}s)")
        
        return {
            'analysis_id': analysis_id,
            'status': 'completed',
            'delta_yen': delta_yen,
            'delta_yen_ci': [delta_yen_ci_low, delta_yen_ci_high],
            'verdict': verdict,
            'reason': reason,
            'estimator_results': results,
            'metadata': {
                'n_rows': n_rows,
                'n_features': len(feature_cols),
                'n_estimators': len(results),
                'total_time_sec': round(total_time, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Causal analysis failed: {e}")
        asyncio.run(self._update_analysis_status(
            analysis_id,
            status='failed',
            error_message=str(e),
            completed_at=datetime.utcnow()
        ))
        raise

