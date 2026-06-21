"""Module slot contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.module_slots import ModuleSlotCreateRequest
from tests.module_binding_helpers import slot_request


def test_module_slot_create_request_accepts_generic_metadata() -> None:
    request = slot_request()

    assert request.slot_key == "test.echo"
    assert request.owner_scope == ["workspace:main"]


def test_module_slot_rejects_domain_specific_slot_key() -> None:
    with pytest.raises(ValidationError):
        slot_request(slot_key="finance.trading")


def test_module_slot_rejects_activation_metadata() -> None:
    with pytest.raises(ValidationError):
        ModuleSlotCreateRequest.model_validate(
            {
                "slot_key": "test.echo",
                "name": "Echo Slot",
                "description": "Generic metadata slot.",
                "owner_scope": ["workspace:main"],
                "metadata": {"activation": True},
            }
        )


def test_module_slot_requires_owner_scope() -> None:
    with pytest.raises(ValidationError):
        slot_request(owner_scope=[])
