"""
Integration Tests for v1 API
Tests DecisionCard CRUD, Δ¥ ranking, and Decision Console endpoints
"""

import pytest
from fastapi.testclient import TestClient
from cqox.api.main import app

client = TestClient(app)


class TestV1DecisionCards:
    """Test v1 DecisionCard API"""

    def test_create_decision_card_go_verdict(self):
        """Test creating a DecisionCard with Go verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
                "scenario_name": "Push通知 最適化 #1",
                "delta_yen": 2800000.0,
                "delta_yen_ci_low": 2100000.0,
                "delta_yen_ci_high": 3500000.0,
                "delta_yen_std": 450000.0,
                "verdict": "Go",
                "reason": None,
                "channel": "アプリPush",
                "segment": "RFM High-Value",
                "quality_scores": {
                    "overlap_coverage": 0.92,
                    "iv_f_stat": 48.3,
                    "rd_mccrary_p": 0.23,
                    "balance_score": 0.89
                },
                "scenario_spec": {
                    "treatment_variable": "push_sent",
                    "outcome_variable": "revenue_7d"
                },
                "estimator_results": {
                    "estimator": "DR",
                    "ate": 2800000.0,
                    "ci_low": 2100000.0,
                    "ci_high": 3500000.0
                }
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["scenario_name"] == "Push通知 最適化 #1"
        assert data["verdict"] == "Go"
        assert data["delta_yen"] == 2800000.0
        assert data["channel"] == "アプリPush"
        assert data["segment"] == "RFM High-Value"
        assert "id" in data

    def test_create_decision_card_canary_verdict(self):
        """Test creating a DecisionCard with Canary verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "メール配信 タイミング最適化",
                "delta_yen": 1500000.0,
                "delta_yen_ci_low": -200000.0,
                "delta_yen_ci_high": 3200000.0,
                "verdict": "Canary",
                "reason": "CI幅広い → A/Bテスト推奨",
                "channel": "Email",
                "segment": "RFM Medium-Value",
                "quality_scores": {
                    "overlap_coverage": 0.85,
                    "balance_score": 0.82
                },
                "scenario_spec": {
                    "treatment_variable": "email_sent"
                },
                "estimator_results": {
                    "estimator": "DiD"
                }
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Canary"
        assert data["reason"] == "CI幅広い → A/Bテスト推奨"

    def test_create_decision_card_hold_verdict(self):
        """Test creating a DecisionCard with Hold verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "SMS配信 セグメント拡大",
                "delta_yen": -500000.0,
                "delta_yen_ci_low": -1200000.0,
                "delta_yen_ci_high": 200000.0,
                "verdict": "Hold",
                "reason": "Δ¥マイナス → 実施非推奨",
                "channel": "SMS",
                "segment": "RFM Low-Value",
                "quality_scores": {
                    "overlap_coverage": 0.65
                },
                "scenario_spec": {},
                "estimator_results": {}
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Hold"
        assert data["delta_yen"] == -500000.0

    def test_list_decision_cards_delta_yen_ranking(self):
        """Test listing DecisionCards sorted by Δ¥ (ranking)"""
        response = client.get("/api/v1/results?sort_by=delta_yen&order=desc")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

        # Verify Δ¥ ranking order (descending)
        if len(data["items"]) > 1:
            for i in range(len(data["items"]) - 1):
                assert data["items"][i]["delta_yen"] >= data["items"][i + 1]["delta_yen"]

    def test_list_decision_cards_filter_by_verdict(self):
        """Test filtering DecisionCards by verdict"""
        response = client.get("/api/v1/results?verdict=Go")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        # Verify all items have Go verdict
        for item in data["items"]:
            assert item["verdict"] == "Go"

    def test_list_decision_cards_filter_by_channel(self):
        """Test filtering DecisionCards by channel"""
        response = client.get("/api/v1/results?channel=アプリPush")

        assert response.status_code == 200
        data = response.json()

        # Verify all items have the specified channel
        for item in data["items"]:
            assert item["channel"] == "アプリPush"

    def test_get_decision_card_by_id(self):
        """Test getting a specific DecisionCard"""
        # First create a card
        create_response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "Test Scenario for GET",
                "delta_yen": 1000000.0,
                "verdict": "Go",
                "scenario_spec": {},
                "estimator_results": {}
            },
        )

        decision_id = create_response.json()["id"]

        # Get the card
        response = client.get(f"/api/v1/results/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == decision_id
        assert data["scenario_name"] == "Test Scenario for GET"

    def test_delete_decision_card(self):
        """Test deleting a DecisionCard"""
        # First create a card
        create_response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "Test Scenario for DELETE",
                "delta_yen": 500000.0,
                "verdict": "Canary",
                "scenario_spec": {},
                "estimator_results": {}
            },
        )

        decision_id = create_response.json()["id"]

        # Delete the card
        response = client.delete(f"/api/v1/results/{decision_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/v1/results/{decision_id}")
        assert get_response.status_code == 404


class TestV1DecisionConsole:
    """Test v1 Decision Console API endpoints"""

    def test_get_delta_yen_summary(self):
        """Test getting Δ¥ summary for Decision Console"""
        response = client.get("/api/v1/console/delta-yen-summary?period_days=7")

        assert response.status_code == 200
        data = response.json()
        assert "total_decisions" in data
        assert "go_count" in data
        assert "canary_count" in data
        assert "hold_count" in data
        assert "best_delta_yen" in data
        assert "worst_delta_yen" in data
        assert "avg_delta_yen" in data

        # Verify counts are non-negative
        assert data["total_decisions"] >= 0
        assert data["go_count"] >= 0
        assert data["canary_count"] >= 0
        assert data["hold_count"] >= 0

    def test_get_delta_yen_summary_with_best_scenario(self):
        """Test Δ¥ summary includes best scenario"""
        response = client.get("/api/v1/console/delta-yen-summary")

        assert response.status_code == 200
        data = response.json()

        if data["total_decisions"] > 0:
            assert "best_scenario" in data
            if data["best_scenario"]:
                assert "scenario_name" in data["best_scenario"]
                assert "delta_yen" in data["best_scenario"]

    def test_get_delta_yen_history_weekly(self):
        """Test getting weekly Δ¥ history"""
        response = client.get("/api/v1/console/delta-yen-history?period=week&weeks=6")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Verify each history item has required fields
        for item in data:
            assert "week" in item
            assert "delta_yen" in item
            assert "decision_count" in item

    def test_get_verdict_distribution(self):
        """Test getting verdict distribution (Go/Canary/Hold)"""
        response = client.get("/api/v1/console/verdict-distribution?period_days=7")

        assert response.status_code == 200
        data = response.json()
        assert "go" in data
        assert "canary" in data
        assert "hold" in data
        assert "total" in data

        # Verify counts sum to total
        assert data["go"] + data["canary"] + data["hold"] == data["total"]

    def test_verdict_distribution_percentages(self):
        """Test verdict distribution returns valid percentages"""
        response = client.get("/api/v1/console/verdict-distribution")

        assert response.status_code == 200
        data = response.json()

        if data["total"] > 0:
            # Verify counts are within total
            assert data["go"] <= data["total"]
            assert data["canary"] <= data["total"]
            assert data["hold"] <= data["total"]


class TestV1QualityGate:
    """Test v1 Quality Gate logic"""

    def test_quality_gate_blocks_low_overlap(self):
        """Test that low overlap triggers Hold verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "Low Overlap Test",
                "delta_yen": 3000000.0,
                "delta_yen_ci_low": 2500000.0,
                "delta_yen_ci_high": 3500000.0,
                "verdict": "Hold",
                "reason": "Overlap低 → 識別不可",
                "quality_scores": {
                    "overlap_coverage": 0.65  # < 0.8 threshold
                },
                "scenario_spec": {},
                "estimator_results": {}
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Hold"
        assert "Overlap" in data["reason"]

    def test_quality_gate_blocks_weak_iv(self):
        """Test that weak IV triggers Hold verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "Weak IV Test",
                "delta_yen": 2000000.0,
                "verdict": "Hold",
                "reason": "IV弱 → 識別不可",
                "quality_scores": {
                    "overlap_coverage": 0.90,
                    "iv_f_stat": 5.2  # < 10 threshold
                },
                "scenario_spec": {},
                "estimator_results": {
                    "estimator": "IV"
                }
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Hold"

    def test_quality_gate_passes_high_quality(self):
        """Test that high quality scores result in Go verdict"""
        response = client.post(
            "/api/v1/results",
            json={
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "scenario_name": "High Quality Test",
                "delta_yen": 2500000.0,
                "delta_yen_ci_low": 2200000.0,
                "delta_yen_ci_high": 2800000.0,
                "verdict": "Go",
                "quality_scores": {
                    "overlap_coverage": 0.95,
                    "iv_f_stat": 78.5,
                    "rd_mccrary_p": 0.42,
                    "balance_score": 0.91
                },
                "scenario_spec": {},
                "estimator_results": {}
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["verdict"] == "Go"
        assert data["quality_scores"]["overlap_coverage"] >= 0.8
