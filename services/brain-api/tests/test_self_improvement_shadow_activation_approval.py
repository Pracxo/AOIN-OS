"""AION-181 approval-binding tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationApprovalBinding,
    validate_shadow_activation_approval,
)


def test_exact_binding_is_required(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    result = validate_shadow_activation_approval(
        approval=ctx["approval"],
        candidate=ctx["candidate"],
        request=ctx["request"],
        current_facts=ctx["facts"],
        now=NOW,
    )
    assert result.valid is True
    for field, value in (
        ("activation_request_id", "other-request"),
        ("candidate_commit_sha", "8" * 40),
        ("candidate_tree_sha", "7" * 40),
        ("diff_sha256", "6" * 64),
        ("implementation_evidence_fingerprint", "5" * 64),
        ("evaluation_report_fingerprint", "4" * 64),
        ("benchmark_manifest_fingerprint", "3" * 64),
        ("benchmark_result_fingerprint", "2" * 64),
        ("reference_set_fingerprint", "1" * 64),
        ("operator_scope_fingerprint", "9" * 64),
        ("output_boundary_fingerprint", "8" * 64),
        ("run_budget_fingerprint", "7" * 64),
        ("monitoring_plan_fingerprint", "6" * 64),
        ("deactivation_plan_fingerprint", "5" * 64),
        ("rollback_commit_sha", "9" * 40),
        ("requesting_operator_principal_id", "operator-other"),
        ("maximum_runs", 1),
    ):
        payload = ctx["approval"].model_dump(mode="python")
        payload.pop("fingerprint", None)
        payload[field] = value
        changed = ShadowActivationApprovalBinding(**payload)
        assert validate_shadow_activation_approval(
            approval=changed,
            candidate=ctx["candidate"],
            request=ctx["request"],
            current_facts=ctx["facts"],
            now=NOW,
        ).valid is False


def test_expired_consumed_and_reusable_are_invalid(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    for patch in (
        {"approved_at": NOW - timedelta(hours=2), "expires_at": NOW - timedelta(seconds=1)},
        {"consumed": True},
        {"reusable": True},
    ):
        payload = ctx["approval"].model_dump(mode="python")
        payload.pop("fingerprint", None)
        payload.update(patch)
        approval = ShadowActivationApprovalBinding(**payload)
        assert validate_shadow_activation_approval(
            approval=approval,
            candidate=ctx["candidate"],
            request=ctx["request"],
            current_facts=ctx["facts"],
            now=NOW,
        ).valid is False
