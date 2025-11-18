"""
Unit tests for Pareto optimization and Scenario Builder

Tests:
- Pareto frontier identification
- Portfolio optimization
- Scenario comparison
- SQL-based segmentation
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile

from cqox.optimization.pareto import (
    ParetoOptimizer,
    Policy,
    ParetoSolution
)
from cqox.scenarios.builder import (
    ScenarioBuilder,
    Scenario,
    ScenarioComparison
)


@pytest.fixture
def sample_policies():
    """Generate sample policies for testing"""
    return [
        Policy(
            policy_id='policy_1',
            name='Email Campaign A',
            delta_yen=1_000_000,
            delta_yen_ci_low=800_000,
            delta_yen_ci_high=1_200_000,
            risk_score=0.1,
            cas_score=0.85,
            cost=200_000,
            feasibility_score=0.9
        ),
        Policy(
            policy_id='policy_2',
            name='SMS Campaign B',
            delta_yen=500_000,
            delta_yen_ci_low=300_000,
            delta_yen_ci_high=700_000,
            risk_score=0.2,
            cas_score=0.75,
            cost=100_000,
            feasibility_score=0.95
        ),
        Policy(
            policy_id='policy_3',
            name='Push Notification C',
            delta_yen=2_000_000,
            delta_yen_ci_low=1_500_000,
            delta_yen_ci_high=2_500_000,
            risk_score=0.3,
            cas_score=0.70,
            cost=500_000,
            feasibility_score=0.7
        ),
        Policy(
            policy_id='policy_4',
            name='Social Media D',
            delta_yen=300_000,
            delta_yen_ci_low=100_000,
            delta_yen_ci_high=500_000,
            risk_score=0.4,
            cas_score=0.60,
            cost=50_000,
            feasibility_score=0.8
        ),
    ]


@pytest.fixture
def sample_dataset():
    """Generate sample dataset for scenario testing"""
    np.random.seed(42)
    n = 1000

    return pd.DataFrame({
        'age': np.random.randint(18, 70, n),
        'region': np.random.choice(['Tokyo', 'Osaka', 'Kyoto'], n),
        'ltv': np.random.lognormal(8, 1, n),
        'segment': np.random.choice(['premium', 'standard', 'basic'], n),
        'last_purchase_days': np.random.randint(1, 180, n),
        'treatment': np.random.randint(0, 2, n),
        'outcome': np.random.randn(n) * 100 + 500
    })


class TestParetoOptimizer:
    """Test Pareto optimization"""

    def test_optimize_enumeration(self, sample_policies):
        """Test Pareto optimization with enumeration method"""
        optimizer = ParetoOptimizer(
            budget=1_000_000,
            max_policies=3,
            risk_appetite='balanced'
        )

        solutions = optimizer.optimize(
            policies=sample_policies,
            method='enumeration'
        )

        assert len(solutions) > 0
        assert all(isinstance(s, ParetoSolution) for s in solutions)

        # Check rank 1 solutions exist
        rank1 = [s for s in solutions if s.dominance_rank == 1]
        assert len(rank1) > 0

    def test_optimize_nsga2(self, sample_policies):
        """Test Pareto optimization with NSGA-II (simplified greedy)"""
        optimizer = ParetoOptimizer(
            budget=800_000,
            risk_appetite='conservative'
        )

        solutions = optimizer.optimize(
            policies=sample_policies,
            method='nsga2'
        )

        assert len(solutions) > 0

        # Check budget constraint
        for sol in solutions:
            assert sol.total_cost <= 800_000

    def test_budget_constraint(self, sample_policies):
        """Test budget constraint enforcement"""
        optimizer = ParetoOptimizer(budget=300_000)

        solutions = optimizer.optimize(
            policies=sample_policies,
            method='enumeration'
        )

        # All solutions should respect budget
        for sol in solutions:
            assert sol.total_cost <= 300_000

    def test_max_policies_constraint(self, sample_policies):
        """Test maximum policies constraint"""
        optimizer = ParetoOptimizer(max_policies=2)

        solutions = optimizer.optimize(
            policies=sample_policies,
            method='enumeration'
        )

        # All solutions should have at most 2 policies
        for sol in solutions:
            assert len(sol.policies) <= 2

    def test_recommend_portfolio(self, sample_policies):
        """Test portfolio recommendation based on risk appetite"""
        for risk_appetite in ['conservative', 'balanced', 'aggressive']:
            optimizer = ParetoOptimizer(
                budget=2_000_000,
                risk_appetite=risk_appetite
            )

            solutions = optimizer.optimize(
                policies=sample_policies,
                method='enumeration'
            )

            recommended = optimizer.recommend_portfolio(solutions)

            assert isinstance(recommended, ParetoSolution)
            assert recommended.dominance_rank == 1  # Should be on frontier

    def test_visualize_frontier(self, sample_policies):
        """Test frontier visualization data generation"""
        optimizer = ParetoOptimizer()

        solutions = optimizer.optimize(
            policies=sample_policies,
            method='enumeration'
        )

        viz_data = optimizer.visualize_frontier(solutions)

        assert isinstance(viz_data, pd.DataFrame)
        assert 'total_delta_yen' in viz_data.columns
        assert 'total_risk' in viz_data.columns
        assert 'total_feasibility' in viz_data.columns
        assert 'dominance_rank' in viz_data.columns

    def test_pareto_dominance(self):
        """Test Pareto dominance logic"""
        # Create two solutions where A dominates B
        sol_a = ParetoSolution(
            policies=['p1'],
            weights=[1.0],
            total_delta_yen=1000,  # Higher profit
            total_risk=0.1,         # Lower risk
            total_feasibility=0.9,  # Higher feasibility
            total_cost=100,
            roi=10.0,
            cas_score_avg=0.8,
            dominance_rank=0
        )

        sol_b = ParetoSolution(
            policies=['p2'],
            weights=[1.0],
            total_delta_yen=500,   # Lower profit
            total_risk=0.3,        # Higher risk
            total_feasibility=0.7,  # Lower feasibility
            total_cost=100,
            roi=5.0,
            cas_score_avg=0.7,
            dominance_rank=0
        )

        optimizer = ParetoOptimizer()

        # A should dominate B
        assert optimizer._dominates(sol_a, sol_b) == True
        assert optimizer._dominates(sol_b, sol_a) == False

    def test_empty_policies(self):
        """Test handling of empty policy list"""
        optimizer = ParetoOptimizer()

        solutions = optimizer.optimize(policies=[], method='enumeration')

        assert len(solutions) == 0


class TestScenarioBuilder:
    """Test Custom Scenario Builder"""

    def test_define_scenario(self, sample_dataset):
        """Test scenario definition"""
        builder = ScenarioBuilder(sample_dataset)

        scenario = builder.define_scenario(
            name='S0_baseline',
            description='Tokyo customers aged 25+',
            filters="age >= 25 and region == 'Tokyo'",
            treatment_policy='control'
        )

        assert isinstance(scenario, Scenario)
        assert scenario.name == 'S0_baseline'
        assert scenario.segment_size > 0
        assert scenario.segment_size < len(sample_dataset)

    def test_sql_filter_parsing(self, sample_dataset):
        """Test SQL filter parsing and application"""
        builder = ScenarioBuilder(sample_dataset)

        # Test simple condition
        scenario1 = builder.define_scenario(
            name='test1',
            description='Age filter',
            filters='age >= 30'
        )
        assert scenario1.segment_size > 0

        # Test AND condition
        scenario2 = builder.define_scenario(
            name='test2',
            description='Multiple conditions',
            filters="age >= 25 and region == 'Tokyo'"
        )
        assert scenario2.segment_size > 0
        assert scenario2.segment_size < scenario1.segment_size

        # Test IN operator
        scenario3 = builder.define_scenario(
            name='test3',
            description='IN operator',
            filters="segment in ['premium', 'standard']"
        )
        assert scenario3.segment_size > 0

    def test_compare_scenarios(self, sample_dataset):
        """Test scenario comparison"""
        builder = ScenarioBuilder(sample_dataset)

        # Define S0 (baseline)
        builder.define_scenario(
            name='S0_baseline',
            description='All customers',
            filters=None,
            treatment_policy='control'
        )

        # Define S1 (intervention)
        builder.define_scenario(
            name='S1_intervention',
            description='Tokyo premium customers',
            filters="region == 'Tokyo' and segment == 'premium'",
            treatment_policy='treatment'
        )

        # Compare scenarios
        comparison = builder.compare_scenarios(
            s0_name='S0_baseline',
            s1_name='S1_intervention',
            outcome_col='outcome',
            treatment_col='treatment'
        )

        assert isinstance(comparison, ScenarioComparison)
        assert comparison.s0_name == 'S0_baseline'
        assert comparison.s1_name == 'S1_intervention'
        assert comparison.verdict in ['Go', 'Canary', 'Hold']
        assert comparison.affected_population > 0

    def test_export_yaml(self, sample_dataset):
        """Test YAML export"""
        builder = ScenarioBuilder(sample_dataset)

        builder.define_scenario(
            name='test_scenario',
            description='Test',
            filters='age >= 25'
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_path = f.name

        try:
            builder.export_yaml(yaml_path)

            # Check file exists
            assert Path(yaml_path).exists()

            # Test loading
            builder2 = ScenarioBuilder(sample_dataset)
            builder2.load_yaml(yaml_path)

            assert 'test_scenario' in builder2.scenarios

        finally:
            Path(yaml_path).unlink(missing_ok=True)

    def test_export_json(self, sample_dataset):
        """Test JSON export"""
        builder = ScenarioBuilder(sample_dataset)

        builder.define_scenario(
            name='test_scenario',
            description='Test',
            filters='age >= 25'
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            builder.export_json(json_path)

            # Check file exists
            assert Path(json_path).exists()

        finally:
            Path(json_path).unlink(missing_ok=True)

    def test_get_summary(self, sample_dataset):
        """Test scenario summary table"""
        builder = ScenarioBuilder(sample_dataset)

        builder.define_scenario(
            name='scenario1',
            description='Test 1',
            filters='age >= 25'
        )

        builder.define_scenario(
            name='scenario2',
            description='Test 2',
            filters='age >= 30'
        )

        summary = builder.get_summary()

        assert isinstance(summary, pd.DataFrame)
        assert len(summary) == 2
        assert 'name' in summary.columns
        assert 'segment_size' in summary.columns

    def test_invalid_filter_detection(self, sample_dataset):
        """Test detection of invalid/dangerous SQL"""
        builder = ScenarioBuilder(sample_dataset)

        # Test dangerous keywords
        with pytest.raises(ValueError, match="Dangerous SQL keyword"):
            builder.define_scenario(
                name='bad1',
                description='SQL injection attempt',
                filters='DROP TABLE users'
            )

        with pytest.raises(ValueError, match="Dangerous SQL keyword"):
            builder.define_scenario(
                name='bad2',
                description='SQL injection attempt',
                filters='DELETE FROM table'
            )

    def test_nonexistent_scenario_comparison(self, sample_dataset):
        """Test error handling for nonexistent scenarios"""
        builder = ScenarioBuilder(sample_dataset)

        with pytest.raises(ValueError, match="Scenario not found"):
            builder.compare_scenarios(
                s0_name='nonexistent',
                s1_name='also_nonexistent',
                outcome_col='outcome',
                treatment_col='treatment'
            )

    def test_between_operator(self, sample_dataset):
        """Test BETWEEN operator parsing"""
        builder = ScenarioBuilder(sample_dataset)

        scenario = builder.define_scenario(
            name='between_test',
            description='BETWEEN operator',
            filters='age BETWEEN 25 AND 50'
        )

        assert scenario.segment_size > 0

        # Verify segment only includes ages 25-50
        df_filtered = builder._apply_filter(sample_dataset, scenario.filters)
        assert df_filtered['age'].min() >= 25
        assert df_filtered['age'].max() <= 50


class TestIntegration:
    """Integration tests combining multiple components"""

    def test_pareto_to_scenario_workflow(self, sample_policies, sample_dataset):
        """Test workflow: Pareto optimization → Scenario comparison"""

        # Step 1: Optimize portfolio
        optimizer = ParetoOptimizer(budget=1_500_000)
        solutions = optimizer.optimize(sample_policies, method='enumeration')
        recommended = optimizer.recommend_portfolio(solutions)

        assert len(recommended.policies) > 0

        # Step 2: Define scenarios based on recommended policies
        builder = ScenarioBuilder(sample_dataset)

        builder.define_scenario(
            name='S0_no_policy',
            description='Baseline without policy',
            filters=None,
            treatment_policy='control'
        )

        builder.define_scenario(
            name='S1_with_policy',
            description='With recommended policy',
            filters="segment == 'premium'",  # Example filter
            treatment_policy='treatment'
        )

        # Step 3: Compare scenarios
        comparison = builder.compare_scenarios(
            s0_name='S0_no_policy',
            s1_name='S1_with_policy',
            outcome_col='outcome',
            treatment_col='treatment'
        )

        assert comparison.verdict in ['Go', 'Canary', 'Hold']
        assert comparison.total_delta_yen != 0  # Should have estimated impact
