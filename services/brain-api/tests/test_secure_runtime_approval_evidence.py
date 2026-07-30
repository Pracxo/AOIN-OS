from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_existing_approval_evidence_is_projected_without_runtime_creation() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.approval_evidence.approved is True
    assert fixture.approval_evidence.actual_execution_authorized is False
    assert fixture.approval_evidence.production_effect_authorized is False
    assert fixture.approval_bundle.approvals_created_by_runtime == 0
    assert fixture.approval_bundle.read_only is True
