"""
Analysis Service - Business logic for causal inference analysis
"""
import os
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from cqox.db.models import Analysis, Dataset, User


class AnalysisService:
    """Service for causal analysis operations"""

    @staticmethod
    def get_analyses_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Analysis]:
        """Get all analyses for a user"""
        query = db.query(Analysis).filter(Analysis.user_id == user_id)

        if status:
            query = query.filter(Analysis.status == status)

        return query.order_by(Analysis.started_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_analysis_by_id(db: Session, analysis_id: int, user_id: int) -> Optional[Analysis]:
        """Get a specific analysis by ID (with user ownership check)"""
        return db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == user_id
        ).first()

    @staticmethod
    def create_analysis(
        db: Session,
        user_id: int,
        dataset_id: int,
        estimator_type: str,
        treatment_col: str,
        outcome_col: str,
        feature_cols: List[str]
    ) -> Analysis:
        """Create a new analysis record"""
        analysis = Analysis(
            user_id=user_id,
            dataset_id=dataset_id,
            estimator_type=estimator_type,
            treatment_col=treatment_col,
            outcome_col=outcome_col,
            feature_cols=feature_cols,
            status='pending'
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def run_causal_analysis(
        db: Session,
        analysis_id: int,
        dataset_path: str,
        treatment_col: str,
        outcome_col: str,
        feature_cols: List[str],
        estimators: List[str]
    ) -> Dict[str, Any]:
        """
        Run causal inference analysis

        This is a simplified implementation for Phase 2.
        Full estimator implementation will be in later phases.
        """
        # Update status to running
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = 'running'
            db.commit()

        try:
            # Load dataset
            if dataset_path.endswith('.csv'):
                df = pd.read_csv(dataset_path)
            elif dataset_path.endswith('.parquet'):
                df = pd.read_parquet(dataset_path)
            else:
                raise ValueError("Unsupported file format")

            # Validate columns exist
            required_cols = [treatment_col, outcome_col] + feature_cols
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing columns in dataset: {missing_cols}")

            # Simple treatment effect estimation (placeholder)
            # This will be replaced with proper causal estimators
            treated = df[df[treatment_col] == 1]
            control = df[df[treatment_col] == 0]

            if len(treated) == 0 or len(control) == 0:
                raise ValueError("Need both treated and control groups")

            # Calculate simple difference in means (ATE)
            ate = treated[outcome_col].mean() - control[outcome_col].mean()

            # Bootstrap for confidence intervals
            bootstrap_ates = []
            n_bootstrap = 100

            for _ in range(n_bootstrap):
                # Resample
                treated_sample = treated.sample(n=len(treated), replace=True)
                control_sample = control.sample(n=len(control), replace=True)

                boot_ate = treated_sample[outcome_col].mean() - control_sample[outcome_col].mean()
                bootstrap_ates.append(boot_ate)

            # Calculate confidence intervals
            ci_low = np.percentile(bootstrap_ates, 2.5)
            ci_high = np.percentile(bootstrap_ates, 97.5)

            # Determine verdict based on ATE and CI
            if ci_low > 0:
                verdict = 'Go'
            elif ci_high < 0:
                verdict = 'Hold'
            else:
                verdict = 'Canary'

            # Calculate some basic metrics
            n_treated = len(treated)
            n_control = len(control)

            results = {
                'ate': float(ate),
                'ci_low': float(ci_low),
                'ci_high': float(ci_high),
                'verdict': verdict,
                'n_treated': int(n_treated),
                'n_control': int(n_control),
                'estimators_used': estimators,
                'treatment_col': treatment_col,
                'outcome_col': outcome_col,
                'feature_cols': feature_cols,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Update analysis with results
            if analysis:
                analysis.status = 'completed'
                analysis.completed_at = datetime.utcnow()
                analysis.results = results
                db.commit()

            return results

        except Exception as e:
            # Update analysis with error
            if analysis:
                analysis.status = 'failed'
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                db.commit()

            raise ValueError(f"Analysis failed: {str(e)}")

    @staticmethod
    def delete_analysis(db: Session, analysis_id: int, user_id: int) -> bool:
        """Delete an analysis (with ownership check)"""
        analysis = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == user_id
        ).first()

        if not analysis:
            return False

        db.delete(analysis)
        db.commit()
        return True
