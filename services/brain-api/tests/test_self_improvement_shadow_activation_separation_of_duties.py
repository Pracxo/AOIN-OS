"""AION-181 separation-of-duties tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationApprovalBinding,
    validate_shadow_activation_approval,
)


def _result(tmp_path: Path, **patch: object) -> bool:
    ctx = make_context(tmp_path)
    payload = ctx["approval"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload.update(patch)
    approval = ShadowActivationApprovalBinding(**payload)
    return validate_shadow_activation_approval(
        approval=approval,
        candidate=ctx["candidate"],
        request=ctx["request"],
        current_facts=ctx["facts"],
        now=NOW,
    ).valid


def test_requester_duplicate_and_single_approver_are_invalid(tmp_path: Path) -> None:
    assert _result(tmp_path, approver_principal_ids=("operator-requester", "operator-b")) is False
    assert _result(tmp_path, approver_principal_ids=("operator-a", "operator-a")) is False
    assert _result(tmp_path, approver_principal_ids=("operator-a",)) is False


def test_security_reviewer_must_be_independent_human(tmp_path: Path) -> None:
    assert _result(tmp_path, security_reviewer_principal_ids=()) is False
    assert _result(tmp_path, security_reviewer_principal_ids=("operator-approver-a",)) is False
    assert _result(tmp_path, security_reviewer_principal_ids=("operator-requester",)) is False
    assert _result(tmp_path, approver_principal_ids=("machine-a", "operator-b")) is False
    assert _result(tmp_path, approver_principal_ids=("AION-SOE-001", "operator-b")) is False
    assert _result(tmp_path, approver_principal_ids=("AION-180-SI-0007", "operator-b")) is False
