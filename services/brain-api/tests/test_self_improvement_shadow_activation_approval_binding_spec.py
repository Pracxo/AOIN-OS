"""AION-180 approval-binding specification tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_ALLOWED_OUTCOMES,
    SHADOW_ACTIVATION_APPROVAL_BINDING_FIELDS,
    SHADOW_ACTIVATION_FORBIDDEN_STATES,
    SHADOW_ACTIVATION_REQUIRED_CANDIDATE_FIELDS,
    SHADOW_ACTIVATION_REQUIRED_REQUEST_FIELDS,
    require_shadow_activation_transition,
    validate_shadow_activation_transition,
)


def test_contract_required_fields_are_exact() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert (
        tuple(record["candidate_contract_required_fields"])
        == SHADOW_ACTIVATION_REQUIRED_CANDIDATE_FIELDS
    )
    assert (
        tuple(record["request_contract_required_fields"])
        == SHADOW_ACTIVATION_REQUIRED_REQUEST_FIELDS
    )
    assert (
        tuple(record["approval_binding_required_fields"])
        == SHADOW_ACTIVATION_APPROVAL_BINDING_FIELDS
    )

    binding = _json("examples/self-improvement/shadow-activation-approval-binding.json")
    assert tuple(binding["required_fields"]) == SHADOW_ACTIVATION_APPROVAL_BINDING_FIELDS
    for required in (
        "base_commit_sha",
        "candidate_commit_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "evaluation_report_fingerprint",
        "benchmark_manifest_fingerprint",
        "benchmark_result_fingerprint",
        "reference_set_fingerprint",
        "operator_scope_fingerprint",
        "output_boundary_fingerprint",
        "run_budget_fingerprint",
        "monitoring_plan_fingerprint",
        "deactivation_plan_fingerprint",
        "rollback_commit_sha",
        "expires_at",
        "reusable",
    ):
        assert required in binding["required_fields"]
    assert binding["approval_created"] is False
    assert binding["approval_satisfied"] is False
    assert binding["reusable"] is False


def test_activation_decisions_are_simulation_only() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert tuple(record["shadow_activation_allowed_outcomes"]) == SHADOW_ACTIVATION_ALLOWED_OUTCOMES
    assert record["shadow_activation_forbidden_outcomes"] == ["active"]


def test_state_machine_accepts_only_disabled_simulation_transitions() -> None:
    require_shadow_activation_transition("drafted", "evidence_ready")
    require_shadow_activation_transition("approval_pending", "approved_disabled")
    require_shadow_activation_transition("approved_disabled", "simulation_ready")
    require_shadow_activation_transition("simulation_ready", "simulated")
    require_shadow_activation_transition("simulated", "review_pending")
    require_shadow_activation_transition("review_pending", "archived")

    for state in SHADOW_ACTIVATION_FORBIDDEN_STATES:
        assert not validate_shadow_activation_transition("drafted", state).allowed
        assert not validate_shadow_activation_transition(state, "archived").allowed
    assert not validate_shadow_activation_transition("simulation_ready", "active").allowed
    assert not validate_shadow_activation_transition("archived", "drafted").allowed
    assert validate_shadow_activation_transition("expired", "archived").allowed
    assert not validate_shadow_activation_transition("expired", "simulation_ready").allowed


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
