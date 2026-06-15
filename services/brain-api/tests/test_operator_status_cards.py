"""Operator status-card builder tests."""

from __future__ import annotations

from aion_brain.operator.status_cards import StatusCardBuilder
from tests.operator_fakes import SCOPE, FakeStatusService


def test_status_card_builder_builds_kernel_card_with_fake_kernel_service() -> None:
    cards = StatusCardBuilder(kernel_service=FakeStatusService("healthy")).build_cards(SCOPE)

    kernel = next(card for card in cards if card.category == "kernel")
    assert kernel.status == "healthy"


def test_status_card_builder_handles_missing_optional_service_as_warning() -> None:
    cards = StatusCardBuilder().build_cards(SCOPE)

    assert any(card.status == "warning" and card.metadata["available"] is False for card in cards)
