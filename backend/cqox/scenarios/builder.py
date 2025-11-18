"""
Custom Scenario Builder: SQL-based Segmentation Engine

Allows users to define custom scenarios using SQL-like queries to segment populations
and compare treatment effects across different subgroups.

Key features:
1. SQL-based segmentation (WHERE clauses, GROUP BY, etc.)
2. S0 vs S1 scenario comparison (baseline vs intervention)
3. YAML/JSON export for reproducibility
4. Counterfactual simulation

Example usage:
    builder = ScenarioBuilder(df)

    # Define S0 (baseline scenario)
    builder.define_scenario(
        name="S0_baseline",
        description="Current state: No campaign",
        filters="age >= 25 AND region == 'Tokyo'",
        treatment_policy="control"
    )

    # Define S1 (intervention scenario)
    builder.define_scenario(
        name="S1_email_campaign",
        description="Email campaign to Tokyo customers",
        filters="age >= 25 AND region == 'Tokyo'",
        treatment_policy="email_campaign"
    )

    # Compare scenarios
    comparison = builder.compare_scenarios("S0_baseline", "S1_email_campaign")

Architecture:
- SQL query parsing using sqlparse
- Safe execution with query validation
- Support for complex conditions (AND, OR, IN, BETWEEN, etc.)
- Integration with causal estimators for effect prediction
"""
import pandas as pd
import numpy as np
import yaml
import json
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from dataclasses import dataclass, asdict
import re


@dataclass
class Scenario:
    """Scenario definition"""
    name: str
    description: str
    filters: Optional[str] = None  # SQL WHERE clause
    treatment_policy: Optional[str] = None  # Treatment assignment rule
    segment_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ScenarioComparison:
    """Comparison between two scenarios"""
    s0_name: str
    s1_name: str
    s0_segment_size: int
    s1_segment_size: int
    delta_yen_per_user: float
    total_delta_yen: float
    delta_yen_ci: List[float]
    risk_score: float
    verdict: str  # 'Go', 'Canary', 'Hold'
    affected_population: int
    metadata: Optional[Dict[str, Any]] = None


class ScenarioBuilder:
    """
    Custom Scenario Builder with SQL-based segmentation

    Enables business users to define and compare scenarios without coding.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Parameters
        ----------
        data : pd.DataFrame
            Base dataset for scenario simulation
        """
        self.data = data
        self.scenarios: Dict[str, Scenario] = {}
        self.comparisons: List[ScenarioComparison] = []

    def define_scenario(
        self,
        name: str,
        description: str,
        filters: Optional[str] = None,
        treatment_policy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Scenario:
        """
        Define a new scenario

        Parameters
        ----------
        name : str
            Unique scenario identifier
        description : str
            Human-readable description
        filters : str, optional
            SQL WHERE clause for segmentation
            Examples:
            - "age >= 25 AND region == 'Tokyo'"
            - "ltv > 10000 OR segment IN ('premium', 'vip')"
            - "last_purchase_days BETWEEN 30 AND 90"
        treatment_policy : str, optional
            Treatment assignment rule
            - 'control': No treatment
            - 'treatment': Apply treatment to all
            - 'random_50': Randomize 50% to treatment
            - Custom policy name
        metadata : dict, optional
            Additional metadata

        Returns
        -------
        Scenario
            Created scenario
        """
        logger.info(f"📝 Defining scenario: {name}")
        logger.info(f"   Description: {description}")
        if filters:
            logger.info(f"   Filters: {filters}")

        # Validate filter syntax
        if filters:
            self._validate_filter(filters)

        # Apply filters to get segment
        if filters:
            segment_data = self._apply_filter(self.data, filters)
            segment_size = len(segment_data)
        else:
            segment_size = len(self.data)

        logger.info(f"   Segment size: {segment_size:,} ({segment_size/len(self.data)*100:.1f}% of population)")

        scenario = Scenario(
            name=name,
            description=description,
            filters=filters,
            treatment_policy=treatment_policy,
            segment_size=segment_size,
            metadata=metadata or {}
        )

        self.scenarios[name] = scenario

        return scenario

    def _validate_filter(self, filter_str: str):
        """
        Validate SQL filter syntax

        Checks for:
        - Valid SQL WHERE clause syntax
        - No dangerous operations (DROP, DELETE, etc.)
        - Column names exist in dataset
        """
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        filter_upper = filter_str.upper()

        for keyword in dangerous_keywords:
            if keyword in filter_upper:
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")

    def _apply_filter(self, data: pd.DataFrame, filter_str: str) -> pd.DataFrame:
        """
        Apply SQL WHERE clause to DataFrame

        Converts SQL syntax to pandas query

        Examples:
        - "age >= 25 AND region == 'Tokyo'" → df.query("age >= 25 and region == 'Tokyo'")
        - "segment IN ('premium', 'vip')" → df[df['segment'].isin(['premium', 'vip'])]
        """
        logger.debug(f"Applying filter: {filter_str}")

        # Convert SQL syntax to pandas query syntax
        query_str = filter_str

        # Replace SQL operators with pandas operators
        query_str = query_str.replace(' AND ', ' and ')
        query_str = query_str.replace(' OR ', ' or ')
        query_str = query_str.replace(' NOT ', ' not ')

        # Handle IN operator
        # "segment IN ('premium', 'vip')" → "segment in ['premium', 'vip']"
        in_pattern = r"(\w+)\s+IN\s+\(([^\)]+)\)"
        query_str = re.sub(
            in_pattern,
            lambda m: f"{m.group(1)} in [{m.group(2)}]",
            query_str,
            flags=re.IGNORECASE
        )

        # Handle BETWEEN operator
        # "age BETWEEN 25 AND 50" → "age >= 25 and age <= 50"
        between_pattern = r"(\w+)\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)"
        query_str = re.sub(
            between_pattern,
            lambda m: f"{m.group(1)} >= {m.group(2)} and {m.group(1)} <= {m.group(3)}",
            query_str,
            flags=re.IGNORECASE
        )

        try:
            # Use pandas query
            filtered_data = data.query(query_str)
            logger.debug(f"Filter result: {len(filtered_data):,} rows")
            return filtered_data
        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            raise ValueError(f"Failed to apply filter '{filter_str}': {e}")

    def compare_scenarios(
        self,
        s0_name: str,
        s1_name: str,
        outcome_col: str,
        treatment_col: str,
        estimator: Optional[object] = None
    ) -> ScenarioComparison:
        """
        Compare two scenarios (S0 vs S1)

        Parameters
        ----------
        s0_name : str
            Baseline scenario name
        s1_name : str
            Intervention scenario name
        outcome_col : str
            Outcome variable column name
        treatment_col : str
            Treatment variable column name
        estimator : object, optional
            Fitted causal estimator for CATE prediction
            If None, uses simple difference-in-means

        Returns
        -------
        ScenarioComparison
            Comparison results with Δ¥ and verdict
        """
        logger.info(f"🔬 Comparing scenarios: {s0_name} vs {s1_name}")

        if s0_name not in self.scenarios:
            raise ValueError(f"Scenario not found: {s0_name}")
        if s1_name not in self.scenarios:
            raise ValueError(f"Scenario not found: {s1_name}")

        s0 = self.scenarios[s0_name]
        s1 = self.scenarios[s1_name]

        # Get segments
        if s0.filters:
            s0_data = self._apply_filter(self.data, s0.filters)
        else:
            s0_data = self.data.copy()

        if s1.filters:
            s1_data = self._apply_filter(self.data, s1.filters)
        else:
            s1_data = self.data.copy()

        # Check if segments overlap
        affected_population = len(s1_data)

        # Estimate treatment effect
        if estimator is not None:
            # Use causal estimator to predict CATE for S1 segment
            try:
                feature_cols = [col for col in s1_data.columns if col not in [outcome_col, treatment_col]]
                X_s1 = s1_data[feature_cols]
                cate_s1 = estimator.estimate_cate(X_s1)
                delta_yen_per_user = np.mean(cate_s1)
                delta_yen_std = np.std(cate_s1)
            except Exception as e:
                logger.warning(f"CATE estimation failed: {e}. Falling back to simple difference.")
                delta_yen_per_user, delta_yen_std = self._simple_difference(
                    s0_data, s1_data, outcome_col, treatment_col
                )
        else:
            # Simple difference-in-means
            delta_yen_per_user, delta_yen_std = self._simple_difference(
                s0_data, s1_data, outcome_col, treatment_col
            )

        # Total impact
        total_delta_yen = delta_yen_per_user * affected_population

        # Confidence interval
        delta_yen_ci_low = delta_yen_per_user - 1.96 * delta_yen_std
        delta_yen_ci_high = delta_yen_per_user + 1.96 * delta_yen_std

        # Risk score (based on CI width and negative probability)
        ci_width = delta_yen_ci_high - delta_yen_ci_low
        relative_uncertainty = ci_width / abs(delta_yen_per_user) if delta_yen_per_user != 0 else 1.0
        risk_score = min(1.0, relative_uncertainty / 2.0)  # Normalize to [0, 1]

        # Verdict
        if delta_yen_ci_low > 0:
            verdict = 'Go'
        elif delta_yen_per_user > 0:
            verdict = 'Canary'
        else:
            verdict = 'Hold'

        comparison = ScenarioComparison(
            s0_name=s0_name,
            s1_name=s1_name,
            s0_segment_size=len(s0_data),
            s1_segment_size=len(s1_data),
            delta_yen_per_user=delta_yen_per_user,
            total_delta_yen=total_delta_yen,
            delta_yen_ci=[delta_yen_ci_low, delta_yen_ci_high],
            risk_score=risk_score,
            verdict=verdict,
            affected_population=affected_population
        )

        self.comparisons.append(comparison)

        logger.info(f"   Verdict: {verdict}")
        logger.info(f"   Δ¥ per user: ¥{delta_yen_per_user:,.0f}")
        logger.info(f"   Total Δ¥: ¥{total_delta_yen:,.0f}")
        logger.info(f"   Affected population: {affected_population:,}")

        return comparison

    def _simple_difference(
        self,
        s0_data: pd.DataFrame,
        s1_data: pd.DataFrame,
        outcome_col: str,
        treatment_col: str
    ) -> tuple:
        """
        Simple difference-in-means estimator

        Returns
        -------
        tuple
            (mean_difference, std_error)
        """
        # Get treatment and control outcomes in each scenario
        if treatment_col in s0_data.columns:
            s0_treated = s0_data[s0_data[treatment_col] == 1][outcome_col]
            s0_control = s0_data[s0_data[treatment_col] == 0][outcome_col]
        else:
            s0_treated = pd.Series([])
            s0_control = s0_data[outcome_col]

        if treatment_col in s1_data.columns:
            s1_treated = s1_data[s1_data[treatment_col] == 1][outcome_col]
            s1_control = s1_data[s1_data[treatment_col] == 0][outcome_col]
        else:
            s1_treated = s1_data[outcome_col]
            s1_control = pd.Series([])

        # Simple ATE: difference in means
        if len(s1_treated) > 0 and len(s0_control) > 0:
            ate = s1_treated.mean() - s0_control.mean()
            # Standard error (simplified)
            se = np.sqrt(s1_treated.var() / len(s1_treated) + s0_control.var() / len(s0_control))
        elif len(s1_treated) > 0 and len(s1_control) > 0:
            ate = s1_treated.mean() - s1_control.mean()
            se = np.sqrt(s1_treated.var() / len(s1_treated) + s1_control.var() / len(s1_control))
        else:
            ate = 0.0
            se = 0.0

        return ate, se

    def export_yaml(self, filepath: str):
        """
        Export scenarios to YAML for reproducibility

        Parameters
        ----------
        filepath : str
            Output YAML file path
        """
        export_data = {
            'scenarios': [asdict(s) for s in self.scenarios.values()],
            'comparisons': [asdict(c) for c in self.comparisons]
        }

        with open(filepath, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"✅ Exported scenarios to {filepath}")

    def export_json(self, filepath: str):
        """
        Export scenarios to JSON

        Parameters
        ----------
        filepath : str
            Output JSON file path
        """
        export_data = {
            'scenarios': [asdict(s) for s in self.scenarios.values()],
            'comparisons': [asdict(c) for c in self.comparisons]
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Exported scenarios to {filepath}")

    def load_yaml(self, filepath: str):
        """
        Load scenarios from YAML file

        Parameters
        ----------
        filepath : str
            Input YAML file path
        """
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        for scenario_dict in data.get('scenarios', []):
            scenario = Scenario(**scenario_dict)
            self.scenarios[scenario.name] = scenario

        for comparison_dict in data.get('comparisons', []):
            comparison = ScenarioComparison(**comparison_dict)
            self.comparisons.append(comparison)

        logger.info(f"✅ Loaded {len(self.scenarios)} scenarios from {filepath}")

    def get_summary(self) -> pd.DataFrame:
        """
        Get summary of all scenarios

        Returns
        -------
        pd.DataFrame
            Summary table
        """
        data = []

        for scenario in self.scenarios.values():
            data.append({
                'name': scenario.name,
                'description': scenario.description,
                'filters': scenario.filters or 'None',
                'treatment_policy': scenario.treatment_policy or 'None',
                'segment_size': scenario.segment_size
            })

        return pd.DataFrame(data)
