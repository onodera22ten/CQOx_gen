"""
Module D Governance tests
"""
import pytest

from cqox.engine.governance.fairness import (
    FairnessChecker,
    DataQualityChecker,
    ComplianceChecker
)
from cqox.api.routes.v2 import governance as governance_api


def test_fairness_checker_detects_disparity():
    checker = FairnessChecker(threshold=100.0)
    payload = [
        {"delta_yen": 500, "gender": "male"},
        {"delta_yen": 40, "gender": "female"},
        {"delta_yen": 520, "gender": "male"},
        {"delta_yen": 20, "gender": "female"},
    ]

    violations = checker.check_multiple_attributes(
        df_uplift=governance_api.pd.DataFrame(payload),
        sensitive_attributes={"gender": ["male", "female"]}
    )

    assert violations, "Expected fairness checker to detect disparity"
    assert violations[0].violation_type == "fairness"


def test_data_quality_checker_flags_small_sample():
    checker = DataQualityChecker()
    df = governance_api.pd.DataFrame([{"value": i} for i in range(10)])

    violation = checker.check_sample_size(df, min_samples=50)

    assert violation is not None
    assert violation.violation_type == "data_quality"
    assert violation.details["required_samples"] == 50


def test_compliance_checker_detects_frequency_cap():
    checker = ComplianceChecker()
    exposures = {"user_1": 5, "user_2": 15}

    violations = checker.check_frequency_cap(exposures, max_frequency=10)

    assert len(violations) == 1
    assert violations[0].details["user_id"] == "user_2"


@pytest.mark.asyncio
async def test_check_fairness_endpoint_returns_violation(monkeypatch):
    captured = {}

    async def fake_log(db, tenant_id, violations, rule_type):
        captured["count"] = len(violations)
        captured["rule_type"] = rule_type

    monkeypatch.setattr(governance_api, "_log_violations", fake_log)

    request = governance_api.FairnessCheckRequest(
        data=[
            {"delta_yen": 2000, "gender": "male"},
            {"delta_yen": 100, "gender": "female"}
        ],
        sensitive_attributes={"gender": ["male", "female"]},
        threshold=500.0
    )

    response = await governance_api.check_fairness(
        request=request,
        db=None,
        current_user={"tenant_id": "00000000-0000-0000-0000-000000000001"}
    )

    assert len(response.violations) == 1
    assert captured["count"] == 1
    assert captured["rule_type"] == "fairness"


@pytest.mark.asyncio
async def test_data_quality_endpoint_logs(monkeypatch):
    captured = {}

    async def fake_log(db, tenant_id, violations, rule_type):
        captured["count"] = len(violations)
        captured["rule_type"] = rule_type

    monkeypatch.setattr(governance_api, "_log_violations", fake_log)

    request = governance_api.DataQualityRequest(
        data=[{"value": v} for v in [1000, -2000, 3000]],
        min_samples=10
    )

    response = await governance_api.check_data_quality(
        request=request,
        db=None,
        current_user={"tenant_id": "default-tenant"}
    )

    assert response.violations
    assert captured["rule_type"] == "data_quality"
    assert captured["count"] >= 1


@pytest.mark.asyncio
async def test_compliance_endpoint_flags_over_cap(monkeypatch):
    captured = {}

    async def fake_log(db, tenant_id, violations, rule_type):
        captured["count"] = len(violations)
        captured["rule_type"] = rule_type

    monkeypatch.setattr(governance_api, "_log_violations", fake_log)

    request = governance_api.ComplianceRequest(
        user_exposures={"user_a": 12, "user_b": 3},
        max_frequency=10
    )

    response = await governance_api.check_compliance(
        request=request,
        db=None,
        current_user={"tenant_id": None}
    )

    assert response.violations
    assert captured["rule_type"] == "compliance"
    assert captured["count"] == 1
