"""
v1 API Integration Tests
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestDatasetsAPI:
    """Dataset management API tests"""
    
    @pytest.mark.asyncio
    async def test_list_datasets(self, async_client: AsyncClient, auth_headers):
        """Test dataset list endpoint"""
        response = await async_client.get("/api/v1/datasets", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_create_dataset_upload(self, async_client: AsyncClient, auth_headers):
        """Test dataset upload creation"""
        payload = {
            "name": "Test Dataset",
            "description": "Test description"
        }
        response = await async_client.post("/api/v1/datasets/upload", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "dataset_id" in data
        assert "upload_url" in data


class TestPoliciesAPI:
    """Policy management API tests"""
    
    @pytest.mark.asyncio
    async def test_list_policies(self, async_client: AsyncClient, auth_headers):
        """Test policy list endpoint"""
        response = await async_client.get("/api/v1/policies", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_create_policy(self, async_client: AsyncClient, auth_headers, sample_dataset_id):
        """Test policy creation"""
        payload = {
            "name": "Test Policy",
            "description": "Test policy description",
            "dataset_id": sample_dataset_id,
            "target_rule": "age > 25",
            "channels": ["email", "push"]
        }
        response = await async_client.post("/api/v1/policies", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Policy"


class TestDecisionCardsAPI:
    """DecisionCard API tests"""
    
    @pytest.mark.asyncio
    async def test_list_decision_cards(self, async_client: AsyncClient, auth_headers):
        """Test decision card list"""
        response = await async_client.get("/api/v1/results", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_create_decision_card(self, async_client: AsyncClient, auth_headers, sample_policy_id):
        """Test decision card creation"""
        payload = {
            "policy_id": sample_policy_id,
            "scenario_name": "Test Scenario",
            "delta_yen": 150000.0,
            "delta_yen_ci_low": 120000.0,
            "delta_yen_ci_high": 180000.0,
            "verdict": "Go",
            "scenario_spec": {"S0": {}, "S1": {}},
            "estimator_results": {}
        }
        response = await async_client.post("/api/v1/results", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Go"
        assert data["delta_yen"] == 150000.0


class TestConsoleAPI:
    """Console summary API tests"""
    
    @pytest.mark.asyncio
    async def test_delta_yen_summary(self, async_client: AsyncClient, auth_headers):
        """Test Δ¥ summary endpoint"""
        response = await async_client.get("/api/v1/console/delta-yen-summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_decisions" in data
        assert "go_count" in data
        assert "avg_delta_yen" in data

