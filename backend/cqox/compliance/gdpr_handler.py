"""
GDPR Compliance Handler

Features:
- Right to be forgotten (data erasure)
- Right to data portability (data export)
- Consent management
- Data retention policies
- Audit logging for data access
- Anonymization

Compliance: GDPR, CCPA, HIPAA
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
from loguru import logger
import json
import hashlib

from cqox.storage.postgres_client import get_postgres_client


class ConsentType(str, Enum):
    """GDPR consent types"""
    ESSENTIAL = "essential"  # Required for service
    ANALYTICS = "analytics"  # Usage analytics
    MARKETING = "marketing"  # Marketing communications
    DATA_SHARING = "data_sharing"  # Third-party sharing


class DataCategory(str, Enum):
    """Data categories for retention policies"""
    USER_PROFILE = "user_profile"
    MODEL_DATA = "model_data"
    DIAGNOSTIC_DATA = "diagnostic_data"
    AUDIT_LOGS = "audit_logs"
    ANALYTICS_DATA = "analytics_data"


class UserConsent(BaseModel):
    """User consent record"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class DataAccessLog(BaseModel):
    """Audit log for data access"""
    user_id: str
    accessed_by: str  # User or system that accessed the data
    data_category: DataCategory
    action: str  # "read", "write", "delete", "export"
    timestamp: datetime
    ip_address: Optional[str] = None
    reason: Optional[str] = None


class GDPRHandler:
    """
    GDPR compliance handler

    Features:
    - Right to erasure (Article 17)
    - Right to data portability (Article 20)
    - Consent management (Article 7)
    - Data retention policies
    - Audit logging (Article 30)
    """

    # Data retention policies (in days)
    RETENTION_POLICIES = {
        DataCategory.USER_PROFILE: 365 * 7,  # 7 years
        DataCategory.MODEL_DATA: 365 * 3,  # 3 years
        DataCategory.DIAGNOSTIC_DATA: 365 * 2,  # 2 years
        DataCategory.AUDIT_LOGS: 365 * 7,  # 7 years (compliance requirement)
        DataCategory.ANALYTICS_DATA: 365,  # 1 year
    }

    async def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Record user consent

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent was granted
            ip_address: User's IP address
            user_agent: User's browser user agent
        """
        db = await get_postgres_client()

        consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            granted_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )

        await db.execute(
            """
            INSERT INTO user_consents
            (user_id, consent_type, granted, granted_at, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            consent_type.value,
            granted,
            consent.granted_at,
            ip_address,
            user_agent
        )

        logger.info(
            f"Consent recorded: user={user_id}, type={consent_type.value}, "
            f"granted={granted}"
        )

    async def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted specific consent

        Args:
            user_id: User identifier
            consent_type: Type of consent to check

        Returns:
            True if consent granted
        """
        db = await get_postgres_client()

        result = await db.fetchrow(
            """
            SELECT granted FROM user_consents
            WHERE user_id = $1 AND consent_type = $2
            ORDER BY granted_at DESC
            LIMIT 1
            """,
            user_id,
            consent_type.value
        )

        return result["granted"] if result else False

    async def log_data_access(
        self,
        user_id: str,
        accessed_by: str,
        data_category: DataCategory,
        action: str,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """
        Log data access for audit trail

        Required for GDPR Article 30 (Records of processing activities)

        Args:
            user_id: User whose data was accessed
            accessed_by: User or system that accessed the data
            data_category: Category of data accessed
            action: Action performed (read/write/delete/export)
            ip_address: IP address of accessor
            reason: Reason for access
        """
        db = await get_postgres_client()

        log = DataAccessLog(
            user_id=user_id,
            accessed_by=accessed_by,
            data_category=data_category,
            action=action,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            reason=reason
        )

        await db.execute(
            """
            INSERT INTO data_access_logs
            (user_id, accessed_by, data_category, action, timestamp, ip_address, reason)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            log.user_id,
            log.accessed_by,
            log.data_category.value,
            log.action,
            log.timestamp,
            log.ip_address,
            log.reason
        )

    async def export_user_data(
        self,
        user_id: str,
        requester_id: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all user data (Right to data portability - Article 20)

        Args:
            user_id: User identifier
            requester_id: ID of user requesting export
            ip_address: IP address of requester

        Returns:
            Dictionary containing all user data
        """
        # Log the export request
        await self.log_data_access(
            user_id=user_id,
            accessed_by=requester_id,
            data_category=DataCategory.USER_PROFILE,
            action="export",
            ip_address=ip_address,
            reason="GDPR data portability request"
        )

        db = await get_postgres_client()

        # Collect all user data from different tables
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data": {}
        }

        # User profile
        user_profile = await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
        if user_profile:
            export_data["data"]["profile"] = dict(user_profile)

        # Model runs
        model_runs = await db.fetch(
            "SELECT * FROM model_runs WHERE user_id = $1",
            user_id
        )
        export_data["data"]["model_runs"] = [dict(row) for row in model_runs]

        # Policies
        policies = await db.fetch(
            "SELECT * FROM policies WHERE user_id = $1",
            user_id
        )
        export_data["data"]["policies"] = [dict(row) for row in policies]

        # Consents
        consents = await db.fetch(
            "SELECT * FROM user_consents WHERE user_id = $1",
            user_id
        )
        export_data["data"]["consents"] = [dict(row) for row in consents]

        # Data access logs (last 90 days)
        cutoff = datetime.utcnow() - timedelta(days=90)
        access_logs = await db.fetch(
            """
            SELECT * FROM data_access_logs
            WHERE user_id = $1 AND timestamp > $2
            """,
            user_id,
            cutoff
        )
        export_data["data"]["access_logs"] = [dict(row) for row in access_logs]

        logger.info(f"User data exported: {user_id}")

        return export_data

    async def erase_user_data(
        self,
        user_id: str,
        requester_id: str,
        ip_address: Optional[str] = None,
        reason: str = "GDPR erasure request"
    ) -> Dict[str, int]:
        """
        Erase user data (Right to be forgotten - Article 17)

        Performs soft deletion (anonymization) to preserve referential integrity
        and compliance records.

        Args:
            user_id: User identifier
            requester_id: ID of user requesting erasure
            ip_address: IP address of requester
            reason: Reason for erasure

        Returns:
            Dictionary with counts of erased records
        """
        # Log the erasure request (before deletion)
        await self.log_data_access(
            user_id=user_id,
            accessed_by=requester_id,
            data_category=DataCategory.USER_PROFILE,
            action="delete",
            ip_address=ip_address,
            reason=reason
        )

        db = await get_postgres_client()
        erased_counts = {}

        # Anonymize user profile (keep record for audit but remove PII)
        anonymized_id = self._anonymize_user_id(user_id)

        result = await db.execute(
            """
            UPDATE users
            SET
                email = $1,
                name = 'ANONYMIZED',
                deleted_at = $2,
                anonymized = true
            WHERE id = $3
            """,
            f"anonymized_{anonymized_id}@deleted.local",
            datetime.utcnow(),
            user_id
        )
        erased_counts["user_profile"] = 1

        # Anonymize model runs (keep for statistical purposes)
        result = await db.execute(
            """
            UPDATE model_runs
            SET user_id = NULL
            WHERE user_id = $1
            """,
            user_id
        )
        erased_counts["model_runs"] = result

        # Anonymize policies
        result = await db.execute(
            """
            UPDATE policies
            SET user_id = NULL
            WHERE user_id = $1
            """,
            user_id
        )
        erased_counts["policies"] = result

        # Delete user sessions and tokens
        result = await db.execute(
            "DELETE FROM user_sessions WHERE user_id = $1",
            user_id
        )
        erased_counts["sessions"] = result

        # Keep consents and audit logs for compliance (7 years)
        # But anonymize personal identifiers
        await db.execute(
            """
            UPDATE user_consents
            SET ip_address = NULL, user_agent = NULL
            WHERE user_id = $1
            """,
            user_id
        )

        await db.execute(
            """
            UPDATE data_access_logs
            SET ip_address = NULL
            WHERE user_id = $1
            """,
            user_id
        )

        logger.warning(
            f"User data erased: {user_id} (reason: {reason}). "
            f"Records: {erased_counts}"
        )

        return erased_counts

    async def apply_retention_policies(self):
        """
        Apply data retention policies

        Deletes or anonymizes data older than retention period.
        Should be run as scheduled job (e.g., daily).
        """
        db = await get_postgres_client()
        deleted_counts = {}

        for category, retention_days in self.RETENTION_POLICIES.items():
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            if category == DataCategory.ANALYTICS_DATA:
                # Delete old analytics data
                result = await db.execute(
                    """
                    DELETE FROM analytics_events
                    WHERE created_at < $1
                    """,
                    cutoff_date
                )
                deleted_counts[category.value] = result

            elif category == DataCategory.DIAGNOSTIC_DATA:
                # Delete old diagnostic data
                result = await db.execute(
                    """
                    DELETE FROM diagnostic_runs
                    WHERE created_at < $1
                    """,
                    cutoff_date
                )
                deleted_counts[category.value] = result

            # Audit logs are kept for 7 years (compliance requirement)
            # User profile and model data have longer retention

        logger.info(f"Retention policies applied: {deleted_counts}")

        return deleted_counts

    def _anonymize_user_id(self, user_id: str) -> str:
        """Generate anonymized user ID hash"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]

    async def generate_privacy_report(self, user_id: str) -> Dict[str, Any]:
        """
        Generate privacy report for user

        Shows:
        - What data is collected
        - How long it's retained
        - Who has accessed it
        - Current consents

        Args:
            user_id: User identifier

        Returns:
            Privacy report
        """
        db = await get_postgres_client()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "data_inventory": {},
            "retention_policies": {},
            "recent_access": [],
            "consents": []
        }

        # Data inventory
        model_runs_count = await db.fetchval(
            "SELECT COUNT(*) FROM model_runs WHERE user_id = $1",
            user_id
        )
        policies_count = await db.fetchval(
            "SELECT COUNT(*) FROM policies WHERE user_id = $1",
            user_id
        )

        report["data_inventory"] = {
            "model_runs": model_runs_count,
            "policies": policies_count
        }

        # Retention policies
        report["retention_policies"] = {
            category.value: f"{days} days"
            for category, days in self.RETENTION_POLICIES.items()
        }

        # Recent data access (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        access_logs = await db.fetch(
            """
            SELECT accessed_by, data_category, action, timestamp
            FROM data_access_logs
            WHERE user_id = $1 AND timestamp > $2
            ORDER BY timestamp DESC
            LIMIT 50
            """,
            user_id,
            cutoff
        )
        report["recent_access"] = [dict(row) for row in access_logs]

        # Current consents
        consents = await db.fetch(
            """
            SELECT DISTINCT ON (consent_type)
                consent_type, granted, granted_at
            FROM user_consents
            WHERE user_id = $1
            ORDER BY consent_type, granted_at DESC
            """,
            user_id
        )
        report["consents"] = [dict(row) for row in consents]

        return report


# Global GDPR handler
_gdpr_handler: Optional[GDPRHandler] = None


def get_gdpr_handler() -> GDPRHandler:
    """Get or create GDPR handler"""
    global _gdpr_handler

    if _gdpr_handler is None:
        _gdpr_handler = GDPRHandler()

    return _gdpr_handler
