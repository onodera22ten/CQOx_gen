"""
MLOps Model Registry with Versioning and Drift Detection
Semantic versioning, shadow evaluation, and model degradation monitoring
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json
import hashlib
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model lifecycle status"""
    TRAINING = "training"
    STAGED = "staged"  # Passed validation, ready for shadow eval
    PRODUCTION = "production"  # Serving live traffic
    ARCHIVED = "archived"  # Deprecated
    FAILED = "failed"


@dataclass
class ModelVersion:
    """
    Model version with semantic versioning

    Format: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes (different features, algorithm)
    - MINOR: New features, compatible improvements
    - PATCH: Bug fixes, no functional changes
    """
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> 'ModelVersion':
        """Parse version string"""
        parts = version_str.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        return cls(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2])
        )

    def bump_major(self) -> 'ModelVersion':
        """Increment major version (breaking change)"""
        return ModelVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> 'ModelVersion':
        """Increment minor version (new feature)"""
        return ModelVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> 'ModelVersion':
        """Increment patch version (bug fix)"""
        return ModelVersion(self.major, self.minor, self.patch + 1)

    def __lt__(self, other: 'ModelVersion') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: 'ModelVersion') -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)


@dataclass
class ModelMetadata:
    """Model metadata for registry"""
    model_id: str
    policy_id: str
    version: ModelVersion

    # Model info
    estimator_type: str  # s_learner, t_learner, dr_learner, etc.
    hyperparameters: Dict[str, Any]
    features: List[str]

    # Training info
    training_dataset_id: str
    dataset_schema_version: str
    trained_at: datetime
    trained_by: str

    # Storage
    s3_artifact_key: str  # S3 path to model pickle/joblib

    # Performance
    performance_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]

    # Status
    status: ModelStatus
    promoted_at: Optional[datetime] = None

    # Lineage
    parent_model_id: Optional[str] = None  # For incremental training

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'model_id': self.model_id,
            'policy_id': self.policy_id,
            'version': str(self.version),
            'estimator_type': self.estimator_type,
            'hyperparameters': self.hyperparameters,
            'features': self.features,
            'training_dataset_id': self.training_dataset_id,
            'dataset_schema_version': self.dataset_schema_version,
            'trained_at': self.trained_at.isoformat(),
            'trained_by': self.trained_by,
            's3_artifact_key': self.s3_artifact_key,
            'performance_metrics': self.performance_metrics,
            'validation_metrics': self.validation_metrics,
            'status': self.status.value,
            'promoted_at': self.promoted_at.isoformat() if self.promoted_at else None,
            'parent_model_id': self.parent_model_id,
        }


class ModelRegistry:
    """
    Centralized model registry

    Features:
    - Semantic versioning
    - Model lineage tracking
    - Shadow evaluation
    - Promotion workflow (training -> staged -> production)
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def register_model(self,
                            policy_id: str,
                            estimator_type: str,
                            hyperparameters: Dict,
                            features: List[str],
                            training_dataset_id: str,
                            dataset_schema_version: str,
                            s3_artifact_key: str,
                            performance_metrics: Dict,
                            validation_metrics: Dict,
                            trained_by: str,
                            parent_model_id: Optional[str] = None) -> ModelMetadata:
        """
        Register new model in registry

        Args:
            policy_id: Associated policy ID
            estimator_type: Type of estimator
            hyperparameters: Model hyperparameters
            features: List of features used
            training_dataset_id: Dataset used for training
            dataset_schema_version: Schema version
            s3_artifact_key: S3 path to model artifact
            performance_metrics: Training performance
            validation_metrics: Validation performance
            trained_by: User ID who trained the model
            parent_model_id: Parent model for incremental training

        Returns:
            ModelMetadata object
        """
        # Determine version
        latest_version = await self._get_latest_version(policy_id)

        if latest_version is None:
            # First model for this policy
            version = ModelVersion(1, 0, 0)
        else:
            # Check if this is a breaking change
            latest_model = await self._get_model(policy_id, latest_version)

            if set(features) != set(latest_model.features):
                # Feature set changed -> major version bump
                version = latest_version.bump_major()
            elif estimator_type != latest_model.estimator_type:
                # Algorithm changed -> major version bump
                version = latest_version.bump_major()
            else:
                # Same features and algorithm -> minor version bump
                version = latest_version.bump_minor()

        # Generate model ID
        model_id = f"{policy_id}-v{version}"

        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            policy_id=policy_id,
            version=version,
            estimator_type=estimator_type,
            hyperparameters=hyperparameters,
            features=features,
            training_dataset_id=training_dataset_id,
            dataset_schema_version=dataset_schema_version,
            trained_at=datetime.utcnow(),
            trained_by=trained_by,
            s3_artifact_key=s3_artifact_key,
            performance_metrics=performance_metrics,
            validation_metrics=validation_metrics,
            status=ModelStatus.TRAINING,
            parent_model_id=parent_model_id
        )

        # Store in database
        await self._store_model(metadata)

        logger.info(f"Registered model {model_id} v{version}")

        return metadata

    async def promote_to_staged(self, model_id: str) -> ModelMetadata:
        """Promote model to staged (ready for shadow evaluation)"""
        metadata = await self.get_model_by_id(model_id)

        if metadata.status != ModelStatus.TRAINING:
            raise ValueError(f"Can only promote TRAINING models, got {metadata.status}")

        metadata.status = ModelStatus.STAGED

        await self._update_model_status(model_id, ModelStatus.STAGED)

        logger.info(f"Promoted model {model_id} to STAGED")

        return metadata

    async def promote_to_production(self, model_id: str) -> ModelMetadata:
        """
        Promote model to production

        - Demotes current production model to ARCHIVED
        - Promotes new model to PRODUCTION
        """
        metadata = await self.get_model_by_id(model_id)

        if metadata.status not in [ModelStatus.STAGED, ModelStatus.TRAINING]:
            raise ValueError(f"Can only promote STAGED models, got {metadata.status}")

        # Get current production model
        current_prod = await self._get_production_model(metadata.policy_id)

        # Demote current production model
        if current_prod:
            await self._update_model_status(current_prod.model_id, ModelStatus.ARCHIVED)
            logger.info(f"Archived previous production model {current_prod.model_id}")

        # Promote new model
        metadata.status = ModelStatus.PRODUCTION
        metadata.promoted_at = datetime.utcnow()

        await self._update_model_status(model_id, ModelStatus.PRODUCTION)

        logger.info(f"Promoted model {model_id} to PRODUCTION")

        return metadata

    async def get_model_by_id(self, model_id: str) -> ModelMetadata:
        """Get model metadata by ID"""
        # Query database
        # In production: SELECT * FROM model_registry WHERE model_id = :model_id

        raise NotImplementedError("Database integration required")

    async def get_production_model(self, policy_id: str) -> Optional[ModelMetadata]:
        """Get current production model for a policy"""
        return await self._get_production_model(policy_id)

    async def list_models(self,
                         policy_id: str,
                         status: Optional[ModelStatus] = None) -> List[ModelMetadata]:
        """List all models for a policy"""
        # Query database with filters
        raise NotImplementedError("Database integration required")

    async def _get_latest_version(self, policy_id: str) -> Optional[ModelVersion]:
        """Get latest version for a policy"""
        # Query: SELECT MAX(version) FROM model_registry WHERE policy_id = :policy_id
        return None

    async def _get_model(self, policy_id: str, version: ModelVersion) -> Optional[ModelMetadata]:
        """Get specific model version"""
        return None

    async def _get_production_model(self, policy_id: str) -> Optional[ModelMetadata]:
        """Get current production model"""
        return None

    async def _store_model(self, metadata: ModelMetadata):
        """Store model metadata in database"""
        # INSERT INTO model_registry (...) VALUES (...)
        pass

    async def _update_model_status(self, model_id: str, status: ModelStatus):
        """Update model status"""
        # UPDATE model_registry SET status = :status WHERE model_id = :model_id
        pass


class DriftDetector:
    """
    Detect data drift and model degradation

    Methods:
    - Kolmogorov-Smirnov test for feature distribution drift
    - Population Stability Index (PSI)
    - Model performance degradation (linear regression on metrics)
    """

    @staticmethod
    def kolmogorov_smirnov_test(
        reference_data: np.ndarray,
        current_data: np.ndarray,
        alpha: float = 0.05
    ) -> Tuple[bool, float, float]:
        """
        Two-sample Kolmogorov-Smirnov test

        Tests if two samples come from the same distribution.

        Args:
            reference_data: Historical/training data
            current_data: Current/production data
            alpha: Significance level

        Returns:
            (drift_detected, statistic, p_value)
        """
        statistic, p_value = stats.ks_2samp(reference_data, current_data)

        drift_detected = p_value < alpha

        return drift_detected, statistic, p_value

    @staticmethod
    def population_stability_index(
        reference_data: np.ndarray,
        current_data: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI)

        PSI measures distribution shift.

        PSI = Σ (p_current - p_reference) * ln(p_current / p_reference)

        Interpretation:
        - PSI < 0.1: No significant change
        - 0.1 <= PSI < 0.2: Moderate change
        - PSI >= 0.2: Significant change (investigate)

        Args:
            reference_data: Historical data
            current_data: Current data
            n_bins: Number of bins for discretization

        Returns:
            PSI score
        """
        # Create bins from reference data
        bins = np.linspace(
            min(reference_data.min(), current_data.min()),
            max(reference_data.max(), current_data.max()),
            n_bins + 1
        )

        # Compute histograms
        ref_counts, _ = np.histogram(reference_data, bins=bins)
        cur_counts, _ = np.histogram(current_data, bins=bins)

        # Convert to proportions
        ref_props = ref_counts / len(reference_data)
        cur_props = cur_counts / len(current_data)

        # Avoid division by zero
        ref_props = np.where(ref_props == 0, 0.0001, ref_props)
        cur_props = np.where(cur_props == 0, 0.0001, cur_props)

        # Calculate PSI
        psi = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))

        return float(psi)

    @staticmethod
    def detect_performance_degradation(
        timestamps: List[datetime],
        metric_values: List[float],
        threshold: float = -0.01,  # -1% per day
        min_observations: int = 7
    ) -> Tuple[bool, float, float]:
        """
        Detect model performance degradation using linear regression

        Fits linear model: metric = a * days_since_start + b

        If slope (a) is significantly negative, model is degrading.

        Args:
            timestamps: List of evaluation timestamps
            metric_values: Corresponding metric values (e.g., AUC, accuracy)
            threshold: Minimum acceptable slope (e.g., -0.01 = -1% per day)
            min_observations: Minimum data points required

        Returns:
            (degradation_detected, slope, p_value)
        """
        if len(timestamps) < min_observations:
            return False, 0.0, 1.0

        # Convert timestamps to days since start
        start_time = min(timestamps)
        days = np.array([(t - start_time).total_seconds() / 86400 for t in timestamps])

        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(days, metric_values)

        # Check if slope is significantly negative
        degradation_detected = (slope < threshold) and (p_value < 0.05)

        return degradation_detected, float(slope), float(p_value)


class ShadowEvaluator:
    """
    Shadow evaluation for new models

    Runs new model alongside production model without affecting decisions.
    Compares predictions to evaluate if new model is better.
    """

    def __init__(self, production_model_id: str, shadow_model_id: str):
        self.production_model_id = production_model_id
        self.shadow_model_id = shadow_model_id
        self.evaluations = []

    async def evaluate_batch(self,
                            X: np.ndarray,
                            y_true: np.ndarray,
                            production_predictions: np.ndarray,
                            shadow_predictions: np.ndarray) -> Dict[str, Any]:
        """
        Compare production and shadow model on a batch

        Args:
            X: Feature matrix
            y_true: True outcomes
            production_predictions: Production model predictions
            shadow_predictions: Shadow model predictions

        Returns:
            Comparison metrics
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        # Calculate metrics for both models
        prod_mse = mean_squared_error(y_true, production_predictions)
        shadow_mse = mean_squared_error(y_true, shadow_predictions)

        prod_mae = mean_absolute_error(y_true, production_predictions)
        shadow_mae = mean_absolute_error(y_true, shadow_predictions)

        prod_r2 = r2_score(y_true, production_predictions)
        shadow_r2 = r2_score(y_true, shadow_predictions)

        # Calculate improvement
        mse_improvement = (prod_mse - shadow_mse) / prod_mse * 100
        mae_improvement = (prod_mae - shadow_mae) / prod_mae * 100
        r2_improvement = (shadow_r2 - prod_r2) * 100

        result = {
            'timestamp': datetime.utcnow(),
            'n_samples': len(y_true),
            'production_model_id': self.production_model_id,
            'shadow_model_id': self.shadow_model_id,
            'production_metrics': {
                'mse': float(prod_mse),
                'mae': float(prod_mae),
                'r2': float(prod_r2),
            },
            'shadow_metrics': {
                'mse': float(shadow_mse),
                'mae': float(shadow_mae),
                'r2': float(shadow_r2),
            },
            'improvements': {
                'mse': float(mse_improvement),
                'mae': float(mae_improvement),
                'r2': float(r2_improvement),
            }
        }

        self.evaluations.append(result)

        logger.info(f"Shadow evaluation: MSE {mse_improvement:+.2f}%, MAE {mae_improvement:+.2f}%, R2 {r2_improvement:+.2f}%")

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all evaluations"""
        if not self.evaluations:
            return {}

        mse_improvements = [e['improvements']['mse'] for e in self.evaluations]
        mae_improvements = [e['improvements']['mae'] for e in self.evaluations]
        r2_improvements = [e['improvements']['r2'] for e in self.evaluations]

        return {
            'n_evaluations': len(self.evaluations),
            'total_samples': sum(e['n_samples'] for e in self.evaluations),
            'avg_improvements': {
                'mse': float(np.mean(mse_improvements)),
                'mae': float(np.mean(mae_improvements)),
                'r2': float(np.mean(r2_improvements)),
            },
            'recommendation': 'promote' if np.mean(mse_improvements) > 5.0 else 'keep_testing'
        }
