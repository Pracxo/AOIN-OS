"""Golden Path Scenario Harness contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.golden_path import (
    GoldenPathFixturePack,
    GoldenPathReport,
    GoldenPathRunRequest,
    GoldenPathScenario,
)


def test_golden_path_scenario_accepts_generic_metadata() -> None:
    scenario = GoldenPathScenario(
        golden_path_scenario_id="scenario-1",
        scenario_key="golden.test",
        name="Generic Test",
        description="Deterministic dry-run verification.",
        status="active",
        scenario_type="generic",
        owner_scope=["workspace:main"],
        metadata={"threshold": 0.9},
    )

    assert scenario.metadata["threshold"] == 0.9


def test_golden_path_scenario_rejects_external_services() -> None:
    with pytest.raises(ValidationError):
        GoldenPathScenario(
            golden_path_scenario_id="scenario-1",
            scenario_key="golden.test",
            name="Generic Test",
            description="Deterministic dry-run verification.",
            status="active",
            scenario_type="generic",
            owner_scope=["workspace:main"],
            required_services=["openai"],
        )


def test_golden_path_scenario_rejects_domain_terms() -> None:
    with pytest.raises(ValidationError):
        GoldenPathScenario(
            golden_path_scenario_id="scenario-1",
            scenario_key="golden.test",
            name="Finance Test",
            description="Deterministic dry-run verification.",
            status="active",
            scenario_type="generic",
            owner_scope=["workspace:main"],
        )


def test_fixture_pack_forces_synthetic_fixtures() -> None:
    pack = GoldenPathFixturePack(
        fixture_pack_id="fixture-1",
        fixture_pack_key="golden.fixtures",
        name="Generic Fixtures",
        description="Synthetic fixtures.",
        status="active",
        owner_scope=["workspace:main"],
        fixtures=[{"fixture_id": "one"}],
    )

    assert pack.fixtures[0]["synthetic"] is True


def test_run_request_defaults_to_dry_run() -> None:
    request = GoldenPathRunRequest(owner_scope=["workspace:main"])

    assert request.mode == "dry_run"
    assert request.run_all_defaults is True


def test_report_critical_finding_blocks_release_candidate() -> None:
    report = GoldenPathReport(
        golden_path_report_id="report-1",
        status="failed",
        owner_scope=["workspace:main"],
        scenario_count=1,
        passed_count=0,
        failed_count=1,
        warning_count=0,
        blocked_count=0,
        readiness_score=1.0,
        release_candidate_ready=True,
        findings=[
            {
                "assertion_key": "no_external_call",
                "severity": "critical",
                "status": "failed",
            }
        ],
        created_at=datetime.now(UTC),
    )

    assert report.release_candidate_ready is False
