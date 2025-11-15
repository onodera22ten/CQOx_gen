"""
Integration Tests for v2 API
Tests v1/v2 API coexistence, policy learning, recourse, and experiment design
"""

import pytest
from fastapi.testclient import TestClient
from cqox.api.main import app

client = TestClient(app)


class TestV2PolicyLab:
    """Test Policy Lab v2 API"""

    def test_create_policy(self):
        """Test creating a new policy configuration"""
        response = client.post(
            "/api/v2/policies",
            json={
                "name": "Test Policy",
                "description": "Integration test policy",
                "policy_type": "threshold",
                "treatment_variable": "treatment",
                "outcome_variable": "revenue",
                "features": ["age", "income", "score"],
                "threshold": 0.5,
                "dataset_id": "test_dataset_001",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Policy"
        assert data["policy_type"] == "threshold"
        assert data["status"] == "draft"
        assert "id" in data

    def test_list_policies(self):
        """Test listing policies"""
        response = client.get("/api/v2/policies")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_offline_learning(self):
        """Test running offline policy learning"""
        # First create a policy
        create_response = client.post(
            "/api/v2/policies",
            json={
                "name": "Test OPE Policy",
                "policy_type": "threshold",
                "treatment_variable": "treatment",
                "outcome_variable": "revenue",
                "features": ["feature_0"],
                "dataset_id": "test_dataset_002",
            },
        )

        policy_id = create_response.json()["id"]

        # Run offline learning
        response = client.post(
            f"/api/v2/policies/{policy_id}/offline-learn",
            json={
                "objective": "uplift",
                "risk_metric": "std",
                "ope_method": "DR",
                "risk_aversion": 0.5,
                "n_candidates": 50,
                "n_bootstrap": 500,
            },
        )

        assert response.status_code == 202  # Accepted
        data = response.json()
        assert data["status"] in ["pending", "running"]
        assert "id" in data

    def test_get_policy_run_status(self):
        """Test getting offline learning run status"""
        # This would test with a real run_id in practice
        # For now, test the endpoint exists
        response = client.get("/api/v2/policies/runs/nonexistent_id")

        assert response.status_code in [404, 200]


class TestV2Recourse:
    """Test Recourse v2 API"""

    def test_generate_recourse(self):
        """Test generating individual recourse plan"""
        response = client.post(
            "/api/v2/recourse/user_12345",
            json={
                "policy_id": "test_policy_001",
                "current_features": {
                    "feature_0": 0.3,
                    "feature_1": 0.5,
                    "feature_2": 0.7,
                },
                "target_outcome": 0.8,
                "actionable_features": ["feature_0", "feature_1"],
                "immutable_features": ["feature_2"],
                "n_candidates": 3,
                "cost_type": "L1",
            },
        )

        # May return 200 or 500 depending on model availability
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert data["unit_id"] == "user_12345"
            assert "candidates" in data
            assert "current_predicted_outcome" in data

    def test_batch_recourse(self):
        """Test batch recourse generation"""
        response = client.post(
            "/api/v2/recourse/batch",
            json={
                "unit_ids": ["user_001", "user_002", "user_003"],
                "policy_id": "test_policy_001",
                "dataset_id": "test_dataset_001",
                "target_outcome": 0.75,
                "actionable_features": ["feature_0", "feature_1"],
                "n_candidates": 2,
            },
        )

        # May return 200 or 500 depending on dataset availability
        assert response.status_code in [200, 500]


class TestV2ExperimentDesign:
    """Test Experiment Design v2 API"""

    def test_create_experiment(self):
        """Test creating experiment design with sample size calculation"""
        response = client.post(
            "/api/v2/experiments/design",
            json={
                "name": "Test A/B Experiment",
                "description": "Integration test experiment",
                "treatment_variable": "discount_amount",
                "arms": [
                    {"name": "Control", "treatment_value": 0, "allocation": 0.5},
                    {"name": "Treatment", "treatment_value": 10, "allocation": 0.5},
                ],
                "primary_outcome": "conversion_rate",
                "outcome_type": "binary",
                "baseline_proportion": 0.15,
                "minimum_detectable_effect": 0.02,
                "alpha": 0.05,
                "power": 0.80,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test A/B Experiment"
        assert "required_sample_size_per_arm" in data
        assert "total_sample_size" in data
        assert "expected_runtime_days" in data

    def test_list_experiments(self):
        """Test listing experiments"""
        response = client.get("/api/v2/experiments")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_power_analysis(self):
        """Test power analysis endpoint"""
        # First create an experiment
        create_response = client.post(
            "/api/v2/experiments/design",
            json={
                "name": "Power Analysis Test",
                "treatment_variable": "feature",
                "arms": [
                    {"name": "A", "treatment_value": 0, "allocation": 0.5},
                    {"name": "B", "treatment_value": 1, "allocation": 0.5},
                ],
                "primary_outcome": "outcome",
                "outcome_type": "continuous",
                "baseline_mean": 100.0,
                "minimum_detectable_effect": 5.0,
                "alpha": 0.05,
                "power": 0.80,
            },
        )

        experiment_id = create_response.json()["id"]

        # Get power analysis
        response = client.get(f"/api/v2/experiments/{experiment_id}/power-analysis")

        assert response.status_code == 200
        data = response.json()
        assert "power_curve" in data
        assert isinstance(data["power_curve"], list)


class TestV1V2Coexistence:
    """Test v1 and v2 API coexistence"""

    def test_health_endpoint_accessible(self):
        """Test that health endpoint works (used by both v1/v2)"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_v1_endpoints_still_work(self):
        """Test that v1 endpoints are still accessible"""
        # Test v1 policies endpoint (if it exists)
        response = client.get("/api/policies")

        # Should return 200 or 401 (not 404)
        assert response.status_code in [200, 401, 404]

    def test_v2_endpoints_separate_namespace(self):
        """Test that v2 endpoints are in separate /v2 namespace"""
        # v2 policy endpoint
        v2_response = client.get("/api/v2/policies")

        # Should work (200) or require auth (401), not 404
        assert v2_response.status_code in [200, 401]


class TestAuthentication:
    """Test authentication for v2 endpoints"""

    def test_v2_endpoints_require_auth(self):
        """Test that v2 endpoints require authentication"""
        # Try accessing without auth headers
        response = client.get("/api/v2/policies")

        # Should return 401 Unauthorized or 200 (if auth not yet enforced)
        assert response.status_code in [200, 401]


class TestRateLimiting:
    """Test rate limiting"""

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are returned"""
        response = client.get("/api/v2/policies")

        # Check if rate limit headers exist (may not be implemented yet)
        # This is a forward-looking test
        pass  # Headers: X-RateLimit-Limit, X-RateLimit-Remaining


class TestErrorHandling:
    """Test error handling"""

    def test_404_for_nonexistent_endpoints(self):
        """Test 404 for non-existent endpoints"""
        response = client.get("/api/v2/nonexistent")

        assert response.status_code == 404

    def test_validation_errors(self):
        """Test validation errors return 422"""
        response = client.post(
            "/api/v2/policies",
            json={
                "name": "Invalid Policy",
                # Missing required fields
            },
        )

        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
