from __future__ import annotations

from aion_brain.contracts.dialogue import DialogueTurnRequest
from tests.kernel_fakes import kernel_container


def test_audit_integration_records_dialogue_turn() -> None:
    container = kernel_container()

    result = container.dialogue_turn_service.turn(
        DialogueTurnRequest(message="hello", owner_scope=["workspace:main"])
    )

    entries = container.audit_integrity_ledger.list_entries(action_type="dialogue.turn")
    assert result.response is not None
    assert entries
