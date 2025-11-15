"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from cqox.api.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "CQOx API"


def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_datasets():
    """Test list datasets endpoint"""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    assert "datasets" in response.json()


def test_list_policies():
    """Test list policies endpoint"""
    response = client.get("/api/policies")
    assert response.status_code == 200
    assert "policies" in response.json()


def test_console_summary():
    """Test console summary endpoint"""
    response = client.get("/api/console/summary")
    assert response.status_code == 200
    data = response.json()
    assert "recommended_policies" in data
    assert "total_incremental_profit" in data


def test_portfolio_summary():
    """Test portfolio summary endpoint"""
    response = client.get("/api/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_policies" in data
    assert "by_channel" in data
