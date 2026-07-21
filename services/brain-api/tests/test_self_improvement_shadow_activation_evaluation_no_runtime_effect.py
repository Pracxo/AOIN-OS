"""AION-182 no-runtime-effect evidence tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


FALSE_KEYS = (
    "new_implementation_authorization_created",
    "activation_approval_created",
    "actual_activation_created",
    "shadow_activation_enabled",
    "source_modified",
    "git_mutated",
    "pull_request_created",
    "merged",
    "runtime_effect",
    "active_learning_promoted",
    "production_exposure",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def test_evaluation_report_records_zero_side_effects() -> None:
    report = _json(
        "examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json"
    )
    integrity = report["repository_integrity"]

    for key in FALSE_KEYS:
        assert report[key] is False, key
    assert integrity["control_plane_real_pull_request_created"] is False
    assert integrity["control_plane_git_operation_count"] == 0
    assert integrity["control_plane_source_mutation_count"] == 0
    assert integrity["control_plane_network_call_count"] == 0
    assert integrity["control_plane_connector_call_count"] == 0
    assert integrity["control_plane_provider_call_count"] == 0
    assert integrity["control_plane_approval_creation_count"] == 0
    assert integrity["control_plane_runtime_promotion_count"] == 0
    assert integrity["temporary_evaluation_data_cleaned"] is True


def test_review_boundary_does_not_authorize_activation() -> None:
    boundary = _json("examples/self-improvement/actual-shadow-activation-review-boundary.json")

    assert boundary["next_authorization_required"] is True
    assert boundary["next_authorization_must_be_separate"] is True
    assert boundary["actual_activation_authorized"] is False
    assert boundary["actual_activation_created"] is False
    assert boundary["activation_approval_created"] is False
    assert boundary["new_implementation_authorization_created"] is False
    assert boundary["runtime_enablement_allowed"] is False
    assert boundary["evaluation_used_as_approval"] is False
    assert boundary["evaluation_reusable"] is False


def test_static_console_evidence_is_read_only() -> None:
    payload = _json(
        "operator-console-static/demo-data/self-improvement-shadow-activation-control-plane-evaluation.json"
    )
    boundary = _json(
        "operator-console-static/demo-data/self-improvement-actual-shadow-activation-review-boundary.json"
    )

    assert payload["status"] == "passed_disabled"
    assert "shadow_activation_enabled=false" in payload["safety_labels"]
    assert "runtime_effect=false" in payload["safety_labels"]
    assert boundary["actual_activation_authorized"] is False
    assert boundary["evaluation_reusable"] is False
