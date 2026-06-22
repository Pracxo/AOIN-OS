"""Scenario contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.scenarios import (
    DemoFixture,
    ScenarioDefinition,
    ScenarioRunRequest,
    ScenarioStep,
)


def test_scenario_step_validates_step_type() -> None:
    with pytest.raises(ValidationError):
        ScenarioStep(
            step_id="step-1",
            step_type="not_allowed",
            description="Invalid.",
            request={},
            expected={},
        )


def test_scenario_definition_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        ScenarioDefinition(
            scenario_id="scenario-1",
            name="Scenario",
            description="Generic scenario.",
            status="active",
            scenario_type="smoke",
            owner_scope=[],
            steps=[_step()],
            tags=[],
            expected={},
            metadata={},
        )


def test_scenario_definition_rejects_domain_specific_tags() -> None:
    with pytest.raises(ValidationError):
        ScenarioDefinition(
            scenario_id="scenario-1",
            name="Scenario",
            description="Generic scenario.",
            status="active",
            scenario_type="smoke",
            owner_scope=["workspace:main"],
            steps=[_step()],
            tags=["finance"],
            expected={},
            metadata={},
        )


def test_scenario_run_request_requires_scenario_reference() -> None:
    with pytest.raises(ValidationError):
        ScenarioRunRequest(owner_scope=["workspace:main"])


def test_demo_fixture_rejects_secret_like_content() -> None:
    with pytest.raises(ValidationError):
        DemoFixture(
            fixture_id="fixture-1",
            name="Fixture",
            description="Generic fixture.",
            status="active",
            fixture_type="event",
            owner_scope=["workspace:main"],
            content={"api_key": "nope"},
            loaded=False,
            result={},
        )


def _step() -> ScenarioStep:
    return ScenarioStep(
        step_id="step-1",
        step_type="noop",
        description="No operation.",
        request={},
        expected={},
    )
