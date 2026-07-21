"""AION-184 persistent cognitive-state service tests."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

import pytest
from pydantic import ValidationError

from aion_brain.cognitive_architecture.repository import (
    InMemoryCognitiveStateRepository,
    StaleCognitiveStateVersionError,
)
from aion_brain.cognitive_architecture.state import (
    BeliefRevisionService,
    CognitiveStateProjector,
    CognitiveStateService,
    ContradictionDetector,
    UncertaintyTracker,
)
from aion_brain.contracts.cognitive_state import (
    BeliefRecord,
    CognitiveEvent,
    CognitiveStateProvenance,
    ResourceState,
    UncertaintyRecord,
)

NOW = datetime(2026, 7, 21, 6, 30, tzinfo=UTC)


def provenance(operation_id: str = "op-test") -> CognitiveStateProvenance:
    return CognitiveStateProvenance(
        provenance_id=f"prov-{operation_id}",
        operation_id=operation_id,
        actor_id="operator",
        source="synthetic-test",
        evidence_refs=("aion://evidence/test",),
        created_at=NOW,
    )


def belief_payload(
    belief_id: str,
    statement: str,
    confidence: float = 0.8,
) -> dict:
    return BeliefRecord(
        belief_id=belief_id,
        statement=statement,
        confidence=confidence,
        source_refs=("aion://evidence/belief",),
        revision_sequence=1,
        created_at=NOW,
        updated_at=NOW,
    ).model_dump(mode="json")


def event(
    *,
    event_id: str,
    idempotency_key: str,
    expected_previous_sequence: int,
    payload: dict,
    event_type: str = "belief_recorded",
) -> CognitiveEvent:
    return CognitiveEvent(
        event_id=event_id,
        idempotency_key=idempotency_key,
        event_type=event_type,
        expected_previous_sequence=expected_previous_sequence,
        payload=payload,
        provenance=provenance(event_id),
        created_at=NOW,
    )


def test_contracts_are_immutable_and_redacted() -> None:
    record = BeliefRecord(
        belief_id="belief-1",
        statement="weather: stable",
        confidence=0.7,
        revision_sequence=1,
        created_at=NOW,
        updated_at=NOW,
    )

    with pytest.raises(ValidationError):
        record.confidence = 0.9  # type: ignore[misc]

    cognitive_event = event(
        event_id="event-1",
        idempotency_key="idem-1",
        expected_previous_sequence=0,
        payload={"safe": {"nested": ["value"]}},
    )
    with pytest.raises(TypeError):
        cognitive_event.payload["safe"] = "changed"

    with pytest.raises(ValidationError):
        CognitiveEvent(
            event_id="event-unsafe",
            idempotency_key="idem-unsafe",
            event_type="belief_recorded",
            expected_previous_sequence=0,
            payload={"api_key": "sk-test"},
            provenance=provenance("unsafe"),
            created_at=NOW,
        )


def test_deterministic_event_and_snapshot_fingerprints() -> None:
    first = event(
        event_id="event-stable",
        idempotency_key="idem-stable",
        expected_previous_sequence=0,
        payload={"b": 2, "a": 1},
    )
    second = event(
        event_id="event-stable",
        idempotency_key="idem-stable",
        expected_previous_sequence=0,
        payload={"a": 1, "b": 2},
    )
    assert first.payload_hash == second.payload_hash
    assert first.event_hash == second.event_hash

    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    first_result = service.record_event(
        event(
            event_id="event-belief-1",
            idempotency_key="idem-belief-1",
            expected_previous_sequence=0,
            payload=belief_payload("belief-1", "weather: stable"),
        )
    )
    replayed = CognitiveStateProjector().replay(repository.list_events())

    assert first_result.snapshot.content_hash == replayed.content_hash
    assert first_result.snapshot.sequence == 1
    assert first_result.snapshot.event_count == 1


def test_belief_revision_contradiction_and_uncertainty_tracking() -> None:
    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    service.record_event(
        event(
            event_id="event-belief-1",
            idempotency_key="idem-belief-1",
            expected_previous_sequence=0,
            payload=belief_payload("belief-1", "route: clear", 0.8),
        )
    )
    service.record_event(
        event(
            event_id="event-belief-2",
            idempotency_key="idem-belief-2",
            expected_previous_sequence=1,
            payload=belief_payload("belief-2", "route: blocked", 0.9),
        )
    )
    snapshot = service.current_snapshot()
    contradictions = ContradictionDetector().detect(snapshot)
    assert len(contradictions) == 1
    service.record_payload(
        event_type="contradiction_recorded",
        payload=contradictions[0].model_dump(mode="json"),
        expected_previous_sequence=2,
        provenance=provenance("contradiction"),
        idempotency_key="idem-contradiction",
        event_id="event-contradiction",
    )

    revision_event = BeliefRevisionService().build_revision_event(
        snapshot=service.current_snapshot(),
        belief_id="belief-1",
        revised_confidence=0.4,
        reason="new evidence reduced confidence",
        provenance=provenance("revision"),
        idempotency_key="idem-revision",
        evidence_refs=("aion://evidence/revision",),
    )
    service.record_event(revision_event)

    uncertainty_event = UncertaintyTracker().build_uncertainty_event(
        subject="route",
        uncertainty_score=0.6,
        previous_score=0.2,
        rationale="conflicting local evidence",
        provenance=provenance("uncertainty"),
        expected_previous_sequence=4,
        idempotency_key="idem-uncertainty",
        uncertainty_id="uncertainty-route",
    )
    final = service.record_event(uncertainty_event).snapshot

    revised = next(item for item in final.beliefs if item.belief_id == "belief-1")
    assert revised.confidence == 0.4
    assert revised.revision_sequence == 2
    assert final.uncertainties[0].direction == "increased"
    assert final.contradictions[0].belief_ids == ("belief-1", "belief-2")


def test_stale_version_rejected_and_resource_invariants_hold() -> None:
    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    service.record_event(
        event(
            event_id="event-belief-1",
            idempotency_key="idem-belief-1",
            expected_previous_sequence=0,
            payload=belief_payload("belief-1", "capacity: available"),
        )
    )

    with pytest.raises(StaleCognitiveStateVersionError):
        service.record_event(
            event(
                event_id="event-stale",
                idempotency_key="idem-stale",
                expected_previous_sequence=0,
                payload=belief_payload("belief-stale", "capacity: stale"),
            )
        )

    with pytest.raises(ValidationError):
        ResourceState(
            resource_id="cpu",
            resource_type="compute",
            capacity=10,
            used=11,
            pressure="critical",
            measured_at=NOW,
        )

    reduced = UncertaintyRecord(
        uncertainty_id="uncertainty-1",
        subject="capacity",
        uncertainty_score=0.1,
        direction="reduced",
        rationale="new bounded measurement",
        updated_at=NOW,
    )
    assert reduced.direction == "reduced"


def test_performance_smoke_replays_one_thousand_events() -> None:
    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    started = perf_counter()
    for index in range(1000):
        service.record_event(
            event(
                event_id=f"event-{index}",
                idempotency_key=f"idem-{index}",
                expected_previous_sequence=index,
                payload=belief_payload(
                    f"belief-{index}",
                    f"item-{index}: observed",
                    confidence=0.5,
                ),
            )
        )
    snapshot = service.current_snapshot()
    elapsed = perf_counter() - started

    assert snapshot.sequence == 1000
    assert len(snapshot.beliefs) == 1000
    assert elapsed < 30
