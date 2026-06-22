"""Contract Registry contract validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractSnapshot,
    InterfaceInventoryRecord,
    MigrationNote,
)
from tests.contract_registry_helpers import SCOPE, contract_record, interface_record, snapshot


def test_contract_index_record_validates_contract_type() -> None:
    assert contract_record().contract_type == "pydantic_model"
    with pytest.raises(ValidationError):
        ContractIndexRecord(**{**contract_record().model_dump(), "contract_type": "finance"})


def test_interface_inventory_record_validates_interface_type() -> None:
    assert interface_record().interface_type == "api_route"
    with pytest.raises(ValidationError):
        InterfaceInventoryRecord(**{**interface_record().model_dump(), "interface_type": "finance"})


def test_contract_snapshot_validates_root_hash() -> None:
    item = snapshot("snapshot-1")
    assert item.root_hash
    with pytest.raises(ValidationError):
        ContractSnapshot(**{**item.model_dump(), "root_hash": ""})


def test_migration_note_rejects_executing_steps() -> None:
    with pytest.raises(ValidationError):
        MigrationNote(
            migration_note_id="note-1",
            note_type="generic",
            status="open",
            title="Unsafe",
            description="Unsafe step.",
            migration_steps=["rm -rf /tmp/example"],
            owner_scope=SCOPE,
        )
