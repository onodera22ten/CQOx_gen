"""
Celery tasks for policy evaluation
"""
from celery import Task
from loguru import logger
import pandas as pd
import yaml

from cqox.tasks.celery_app import celery_app
from cqox.data.loader import DataLoader
from cqox.causal.policy.offline_eval import OfflinePolicyEvaluator
from cqox.export.targets import PolicyExporter


class PolicyTask(Task):
    """Base task for policy operations"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Policy task {task_id} failed: {exc}")


@celery_app.task(base=PolicyTask, bind=True)
def evaluate_policy_offline(
    self,
    policy_id: str,
    policy_file_path: str,
    dataset_path: str
):
    """
    Offline policy evaluation

    Args:
        policy_id: Policy ID
        policy_file_path: Path to policy YAML
        dataset_path: Path to dataset

    Returns:
        Evaluation results
    """
    logger.info(f"Starting offline policy evaluation: {policy_id}")

    try:
        # Load policy
        with open(policy_file_path, 'r') as f:
            policy = yaml.safe_load(f)

        # Load data
        df = DataLoader.load_auto(dataset_path)

        # Run offline evaluation
        evaluator = OfflinePolicyEvaluator()

        # Extract features
        X = df[[col for col in df.columns if col.startswith('X_')]]
        treatment = df['treatment']
        y = df['y']

        # Simple policy: use target rule to determine policy_treatment
        # (Simplified - in practice would evaluate target_rule)
        policy_treatment = treatment  # Placeholder

        result = evaluator.evaluate_policy(
            X, treatment, y, policy_treatment,
            method='dr'
        )

        # Calculate ROI
        from cqox.causal.policy.offline_eval import evaluate_policy_roi

        roi_metrics = evaluate_policy_roi(
            policy_value=result['value'],
            baseline_value=y[treatment == 0].mean(),
            cost=policy.get('budget_limit', 0) * 0.1  # Estimate cost
        )

        logger.info(f"Policy evaluation completed: {policy_id}")

        return {
            'policy_id': policy_id,
            'task_id': self.request.id,
            'status': 'completed',
            'policy_value': result['value'],
            'std_error': result['std_error'],
            'roi': roi_metrics['roi'],
            'incremental_profit': roi_metrics['incremental_value']
        }

    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        raise


@celery_app.task(bind=True)
def export_policy_targets_task(
    self,
    policy_id: str,
    policy_file_path: str,
    dataset_path: str,
    output_format: str = 'csv'
):
    """
    Export policy targets

    Args:
        policy_id: Policy ID
        policy_file_path: Path to policy YAML
        dataset_path: Path to dataset
        output_format: Output format

    Returns:
        Export result
    """
    logger.info(f"Starting target export: {policy_id}")

    try:
        exporter = PolicyExporter(policy_file_path)
        output_path = exporter.export_targets(dataset_path, output_format)

        logger.info(f"Target export completed: {policy_id}")

        return {
            'policy_id': policy_id,
            'task_id': self.request.id,
            'status': 'completed',
            'output_path': str(output_path)
        }

    except Exception as e:
        logger.error(f"Target export failed: {e}")
        raise
