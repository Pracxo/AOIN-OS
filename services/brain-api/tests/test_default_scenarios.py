"""Default scenario pack tests."""

from aion_brain.contracts.scenarios import ALLOWED_STEP_TYPES, BANNED_DOMAIN_TERMS
from aion_brain.scenarios.defaults import list_default_scenarios


def test_default_scenarios_contain_only_allowed_step_types() -> None:
    scenarios = list_default_scenarios(["workspace:main"])

    assert scenarios
    assert all(step.step_type in ALLOWED_STEP_TYPES for item in scenarios for step in item.steps)


def test_default_scenarios_contain_no_domain_terms() -> None:
    parts: list[str] = []
    for scenario in list_default_scenarios(["workspace:main"]):
        parts.extend(
            [
                scenario.scenario_id,
                scenario.name,
                scenario.description,
                " ".join(scenario.tags),
            ]
        )
    text = " ".join(parts).lower()

    assert not any(term in text for term in BANNED_DOMAIN_TERMS)
