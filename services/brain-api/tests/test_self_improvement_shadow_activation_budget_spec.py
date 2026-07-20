"""AION-180 resource-budget specification tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import SHADOW_ACTIVATION_RESOURCE_LIMITS  # noqa: E402


def test_resource_limits_are_exact_and_zero_for_side_effects() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert record["resource_limits"] == SHADOW_ACTIVATION_RESOURCE_LIMITS
    assert record["resource_limits"]["maximum_activation_window_seconds"] == 3600
    assert record["resource_limits"]["maximum_runs_per_activation"] == 10
    assert record["resource_limits"]["maximum_concurrency"] == 4
    assert record["resource_limits"]["maximum_total_output_bytes_per_activation"] == 52428800
    for key in (
        "production_exposure_basis_points",
        "network_calls",
        "connector_calls",
        "provider_calls",
        "git_operations",
        "source_mutations",
        "real_pull_requests",
        "approvals_created",
        "merges",
        "runtime_promotions",
        "production_canaries",
        "deployments",
        "model_training_runs",
    ):
        assert record["resource_limits"][key] == 0


def test_quality_gain_cannot_override_fail_closed_budget() -> None:
    budget = _json("examples/self-improvement/shadow-activation-resource-budget.json")
    assert budget["resource_limits"] == SHADOW_ACTIVATION_RESOURCE_LIMITS
    assert budget["quality_gain_override_allowed"] is False
    assert budget["violation_result"] == "fail_closed_no_runtime_effect"
    assert budget["shadow_activation_enabled"] is False
    assert budget["runtime_effect"] is False


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
