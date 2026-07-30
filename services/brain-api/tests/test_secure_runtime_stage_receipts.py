from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import (
    SecureRuntimeSessionState,
    SecureRuntimeStageCommand,
    SecureRuntimeStageDisposition,
    SecureRuntimeStageReceipt,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


def test_stage_receipt_chain_starts_from_zero_and_is_contiguous() -> None:
    fixture = secure_runtime_fixture()
    command = SecureRuntimeStageCommand(
        command_id="receipt-command-AION-231",
        session_id=fixture.session.session_id,
        expected_current_state=SecureRuntimeSessionState.drafted,
        requested_next_state=SecureRuntimeSessionState.authorized,
        session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
        input_fingerprints=(fixture.session_plan.plan_fingerprint or "",),
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
        created_at=NOW,
        expires_at=fixture.authorization.expires_at,
    )
    receipt = fixture.service.advance_stage(session=fixture.session, command=command)

    assert receipt.sequence_number == 1
    assert receipt.prior_receipt_fingerprint == "0" * 64
    assert receipt.receipt_fingerprint


def test_receipt_sequence_gap_is_rejected() -> None:
    fixture = secure_runtime_fixture()
    receipt = SecureRuntimeStageReceipt(
        receipt_id="receipt-gap-AION-231",
        session_id=fixture.session.session_id,
        sequence_number=2,
        prior_receipt_fingerprint="0" * 64,
        state_before=SecureRuntimeSessionState.drafted,
        state_after=SecureRuntimeSessionState.authorized,
        disposition=SecureRuntimeStageDisposition.executed,
        command_fingerprint=fixture.session_plan.plan_fingerprint or "",
        created_at=NOW,
    )
    with pytest.raises(ValueError, match="receipt sequence"):
        fixture.service.repository.with_stage_receipt(receipt)
