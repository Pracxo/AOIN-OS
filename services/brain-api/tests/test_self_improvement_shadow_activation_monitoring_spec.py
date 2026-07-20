"""AION-180 monitoring and deactivation specification tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS,
    SHADOW_ACTIVATION_MONITORED_VALUES,
)


def test_monitoring_values_are_exact_and_forbidden_counters_zero() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    monitoring = _json("examples/self-improvement/shadow-activation-monitoring-plan.json")
    assert tuple(record["monitored_values"]) == SHADOW_ACTIVATION_MONITORED_VALUES
    assert tuple(monitoring["monitored_values"]) == SHADOW_ACTIVATION_MONITORED_VALUES
    assert monitoring["forbidden_counters_must_remain_zero"] is True
    for key in (
        "network_call_count",
        "git_operation_count",
        "source_mutation_count",
        "real_pr_count",
        "approval_creation_count",
        "runtime_promotion_count",
        "runtime_influence_count",
    ):
        assert key in monitoring["monitored_values"]


def test_deactivation_triggers_and_requirements_are_exact() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    plan = _json("examples/self-improvement/shadow-activation-deactivation-plan.json")
    assert tuple(record["deactivation_triggers"]) == SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS
    assert tuple(plan["deactivation_triggers"]) == SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS
    assert "operator kill switch" in plan["deactivation_triggers"]
    assert "any network call" in plan["deactivation_triggers"]
    assert "any source mutation" in plan["deactivation_triggers"]
    assert "any approval creation" in plan["deactivation_triggers"]
    assert plan["operator_kill_switch_required"] is True
    assert "require a new authorization before reactivation" in plan["deactivation_requirements"]


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
