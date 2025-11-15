"""
Policy export and target list generation
"""
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from cqox.config import settings
from cqox.data.loader import DataLoader


class PolicyExporter:
    """Export target lists based on policy rules"""

    def __init__(self, policy_file: Path):
        """
        Args:
            policy_file: Path to policy YAML file
        """
        with open(policy_file, 'r') as f:
            self.policy = yaml.safe_load(f)

        self.policy_id = self.policy['id']

    def evaluate_target_rule(
        self,
        df: pd.DataFrame,
        rule: str
    ) -> pd.Series:
        """
        Evaluate target rule expression

        Args:
            df: DataFrame with features
            rule: Rule expression (e.g., "uplift >= 0.8 and churn_risk >= 0.6")

        Returns:
            Boolean mask of selected users
        """
        # Simple eval-based rule evaluation
        # In production, use a safer DSL parser
        try:
            mask = df.eval(rule)
            return mask
        except Exception as e:
            logger.error(f"Rule evaluation failed: {e}")
            raise

    def export_targets(
        self,
        dataset_path: Path,
        output_format: str = 'csv'
    ) -> Path:
        """
        Export target list

        Args:
            dataset_path: Path to dataset
            output_format: 'csv' or 'parquet'

        Returns:
            Path to exported file
        """
        logger.info(f"Exporting targets for policy: {self.policy_id}")

        # Load dataset
        df = DataLoader.load_auto(dataset_path)

        # Evaluate target rule
        target_rule = self.policy.get('target_rule', 'True')
        mask = self.evaluate_target_rule(df, target_rule)

        # Select targets
        targets = df[mask]

        # Apply frequency cap if specified
        freq_cap = self.policy.get('frequency_cap')
        if freq_cap:
            # Simple implementation: limit per user
            targets = targets.groupby('unit_id').head(freq_cap).reset_index(drop=True)

        # Apply budget limit if specified
        budget_limit = self.policy.get('budget_limit')
        if budget_limit:
            # Sort by uplift/value and limit total
            if 'uplift' in targets.columns:
                targets = targets.sort_values('uplift', ascending=False)

            # Simple budget: assume cost per unit
            cost_per_unit = self.policy.get('offer', {}).get('amount', 100)
            max_targets = int(budget_limit / cost_per_unit)
            targets = targets.head(max_targets)

        # Select export columns
        export_cols = ['unit_id']
        if 'offer' in self.policy:
            # Add offer details
            targets['offer_type'] = self.policy['offer'].get('type')
            targets['offer_template'] = self.policy['offer'].get('template_id')
            export_cols.extend(['offer_type', 'offer_template'])

        targets_export = targets[export_cols]

        # Export
        output_path = settings.exports_dir / f"{self.policy_id}_targets.{output_format}"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == 'csv':
            targets_export.to_csv(output_path, index=False)
        elif output_format == 'parquet':
            targets_export.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        logger.info(f"Exported {len(targets_export)} targets to {output_path}")
        return output_path


def export_policy_targets(
    policy_id: str,
    dataset_id: str,
    output_format: str = 'csv'
) -> Dict[str, Any]:
    """
    Export targets for a policy

    Args:
        policy_id: Policy ID
        dataset_id: Dataset ID
        output_format: Output format

    Returns:
        Export result info
    """
    policy_file = settings.policies_dir / f"{policy_id}.yaml"
    dataset_path = settings.artifacts_dir / dataset_id / "normalized.parquet"

    if not policy_file.exists():
        raise ValueError(f"Policy not found: {policy_id}")

    if not dataset_path.exists():
        raise ValueError(f"Dataset not found: {dataset_id}")

    exporter = PolicyExporter(policy_file)
    output_path = exporter.export_targets(dataset_path, output_format)

    return {
        'policy_id': policy_id,
        'dataset_id': dataset_id,
        'output_path': str(output_path),
        'output_format': output_format,
        'success': True
    }
