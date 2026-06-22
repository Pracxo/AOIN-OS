from __future__ import annotations

from tests.outcome_helpers import bundle


def test_observed_effect_collector_creates_command_completed_effect() -> None:
    env = bundle()
    effects = env.observed.collect_for_source("command", "command-1", ["workspace:main"])

    assert effects[0].effect_type == "command_completed"
    assert effects[0].observed_value["status"] == "completed"


def test_observed_effect_collector_creates_workflow_completed_effect() -> None:
    env = bundle()
    effects = env.observed.collect_for_source("workflow", "workflow-run-1", ["workspace:main"])

    assert effects[0].effect_type == "workflow_completed"
    assert effects[0].observation_source_type == "workflow"


def test_situation_state_atom_can_be_collected_as_observed_effect() -> None:
    env = bundle()
    effects = env.observed.collect_for_source("state_atom", "state-1", ["workspace:main"])

    assert effects[0].effect_type == "state_change"
    assert effects[0].observed_value["status"] == "changed"
