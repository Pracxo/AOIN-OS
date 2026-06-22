"""Operator registry integration tests."""

from __future__ import annotations

from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.status_cards import StatusCardBuilder
from aion_brain.resource_registry.validator import ReferenceValidator
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import repository


def test_operator_status_cards_include_registry() -> None:
    cards = StatusCardBuilder(registry_service=object()).build_cards(["workspace:main"])

    assert any(card.card_id == "card-registry" for card in cards)


def test_operator_queues_include_broken_reference_queue() -> None:
    repo = repository()
    validator = ReferenceValidator(repo, AllowPolicy())
    queues = QueueSummaryBuilder(reference_validator=validator).build_queues(["workspace:main"])

    assert any(queue.queue_type == "broken_references" for queue in queues)
