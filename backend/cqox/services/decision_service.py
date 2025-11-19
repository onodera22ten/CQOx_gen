"""
Decision Service - Business logic for decision management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from cqox.db.models import Decision, Analysis, User


class DecisionService:
    """Service for decision management operations"""

    @staticmethod
    def get_decisions_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        verdict: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Decision]:
        """Get all decisions for a user with optional filters"""
        query = db.query(Decision).filter(Decision.user_id == user_id)

        if verdict:
            query = query.filter(Decision.verdict == verdict)

        if start_date:
            query = query.filter(Decision.created_at >= start_date)

        if end_date:
            query = query.filter(Decision.created_at <= end_date)

        return query.order_by(Decision.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_decision_by_id(db: Session, decision_id: int, user_id: int) -> Optional[Decision]:
        """Get a specific decision by ID (with user ownership check)"""
        return db.query(Decision).filter(
            Decision.id == decision_id,
            Decision.user_id == user_id
        ).first()

    @staticmethod
    def create_decision_from_analysis(
        db: Session,
        analysis_id: int,
        user_id: int,
        policy_name: Optional[str] = None
    ) -> Decision:
        """
        Create a decision record from a completed analysis
        """
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == user_id
        ).first()

        if not analysis:
            raise ValueError("Analysis not found")

        if analysis.status != 'completed':
            raise ValueError("Analysis is not completed yet")

        if not analysis.results:
            raise ValueError("Analysis has no results")

        # Extract decision metrics from analysis results
        results = analysis.results
        delta_yen = results.get('ate', 0)
        ci_low = results.get('ci_low', 0)
        ci_high = results.get('ci_high', 0)
        verdict = results.get('verdict', 'Hold')

        # Calculate CAS score (simple version based on CI width)
        ci_width = ci_high - ci_low
        if ci_width > 0:
            cas_score = min(1.0, abs(delta_yen) / ci_width)
        else:
            cas_score = 0.0

        # Calculate risk score (inverse of confidence)
        if delta_yen != 0:
            risk_score = min(1.0, ci_width / abs(delta_yen))
        else:
            risk_score = 1.0

        # Create decision
        decision = Decision(
            analysis_id=analysis_id,
            user_id=user_id,
            policy_name=policy_name or f"Policy_{analysis_id}",
            verdict=verdict,
            delta_yen=delta_yen,
            cas_score=cas_score,
            risk_score=risk_score,
            confidence_interval_low=ci_low,
            confidence_interval_high=ci_high
        )

        db.add(decision)
        db.commit()
        db.refresh(decision)

        return decision

    @staticmethod
    def get_decision_summary(db: Session, user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Get summary statistics for decisions

        Returns counts and total delta_yen by verdict for the past N days
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get decisions from the past N days
        decisions = db.query(Decision).filter(
            Decision.user_id == user_id,
            Decision.created_at >= start_date
        ).all()

        # Calculate summary stats
        summary = {
            'total_decisions': len(decisions),
            'go_count': 0,
            'canary_count': 0,
            'hold_count': 0,
            'total_delta_yen': 0.0,
            'go_delta_yen': 0.0,
            'canary_delta_yen': 0.0,
            'hold_delta_yen': 0.0,
            'avg_cas_score': 0.0,
            'avg_risk_score': 0.0,
            'period_days': days,
            'start_date': start_date.isoformat()
        }

        if not decisions:
            return summary

        # Aggregate by verdict
        for decision in decisions:
            summary['total_delta_yen'] += decision.delta_yen or 0

            if decision.verdict == 'Go':
                summary['go_count'] += 1
                summary['go_delta_yen'] += decision.delta_yen or 0
            elif decision.verdict == 'Canary':
                summary['canary_count'] += 1
                summary['canary_delta_yen'] += decision.delta_yen or 0
            elif decision.verdict == 'Hold':
                summary['hold_count'] += 1
                summary['hold_delta_yen'] += decision.delta_yen or 0

        # Calculate averages
        summary['avg_cas_score'] = sum(d.cas_score or 0 for d in decisions) / len(decisions)
        summary['avg_risk_score'] = sum(d.risk_score or 0 for d in decisions) / len(decisions)

        return summary

    @staticmethod
    def update_decision(
        db: Session,
        decision_id: int,
        user_id: int,
        verdict: Optional[str] = None,
        policy_name: Optional[str] = None
    ) -> Decision:
        """Update a decision"""
        decision = db.query(Decision).filter(
            Decision.id == decision_id,
            Decision.user_id == user_id
        ).first()

        if not decision:
            raise ValueError("Decision not found")

        if verdict:
            decision.verdict = verdict

        if policy_name:
            decision.policy_name = policy_name

        db.commit()
        db.refresh(decision)

        return decision

    @staticmethod
    def delete_decision(db: Session, decision_id: int, user_id: int) -> bool:
        """Delete a decision (with ownership check)"""
        decision = db.query(Decision).filter(
            Decision.id == decision_id,
            Decision.user_id == user_id
        ).first()

        if not decision:
            return False

        db.delete(decision)
        db.commit()
        return True
