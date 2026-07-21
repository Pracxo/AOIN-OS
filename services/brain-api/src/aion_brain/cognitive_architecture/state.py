"""Deterministic persistent cognitive-state services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.cognitive_architecture.repository import (
    CognitiveStateCheckpointError,
    CognitiveStateRepository,
)
from aion_brain.contracts.cognitive_state import (
    BeliefRecord,
    BeliefRevision,
    CognitiveEvent,
    CognitiveEventType,
    CognitiveStateCheckpoint,
    CognitiveStateProvenance,
    CognitiveStateSnapshot,
    CognitiveStateTransition,
    ContradictionRecord,
    ExpectedActionEffect,
    GoalFocus,
    ObservedActionEffect,
    OpenHypothesis,
    ResourceState,
    UncertaintyDirection,
    UncertaintyRecord,
    empty_cognitive_state_snapshot,
)


@dataclass(frozen=True)
class CognitiveStateWriteResult:
    """Result returned after one event submission."""

    event: CognitiveEvent
    snapshot: CognitiveStateSnapshot
    transition: CognitiveStateTransition | None
    duplicate: bool


class CognitiveStateProjector:
    """Pure deterministic projector for cognitive-state event streams."""

    def replay(
        self,
        events: tuple[CognitiveEvent, ...],
        *,
        initial_snapshot: CognitiveStateSnapshot | None = None,
    ) -> CognitiveStateSnapshot:
        snapshot = initial_snapshot or empty_cognitive_state_snapshot()
        for event in sorted(events, key=lambda item: item.sequence):
            snapshot, _transition = self.apply(snapshot, event)
        return snapshot

    def apply(
        self,
        snapshot: CognitiveStateSnapshot,
        event: CognitiveEvent,
    ) -> tuple[CognitiveStateSnapshot, CognitiveStateTransition]:
        if event.sequence != snapshot.sequence + 1:
            raise ValueError("cognitive event sequence must be monotonic")
        before_hash = snapshot.content_hash or ""
        updated = self._apply_payload(snapshot, event)
        after = updated.model_copy(
            update={
                "sequence": event.sequence,
                "event_count": snapshot.event_count + 1,
                "provenance": (*snapshot.provenance, event.provenance),
                "content_hash": None,
                "created_at": event.created_at,
            }
        )
        after = CognitiveStateSnapshot.model_validate(after.model_dump(mode="python"))
        transition = CognitiveStateTransition(
            transition_id=f"cognitive-transition-{event.sequence}",
            event_id=event.event_id,
            event_type=event.event_type,
            previous_sequence=snapshot.sequence,
            next_sequence=after.sequence,
            before_hash=before_hash,
            after_hash=after.content_hash or "",
            idempotent_replay=False,
            provenance=event.provenance,
            created_at=event.created_at,
        )
        return after, transition

    def _apply_payload(
        self,
        snapshot: CognitiveStateSnapshot,
        event: CognitiveEvent,
    ) -> CognitiveStateSnapshot:
        payload = dict(event.payload)
        if event.event_type == "belief_recorded":
            belief = BeliefRecord.model_validate(payload)
            return snapshot.model_copy(
                update={"beliefs": _replace_by_id(snapshot.beliefs, belief, "belief_id")}
            )
        if event.event_type == "belief_revised":
            revision = BeliefRevision.model_validate(payload)
            beliefs = tuple(
                _apply_belief_revision(belief, revision, event.created_at)
                for belief in snapshot.beliefs
            )
            return snapshot.model_copy(
                update={
                    "belief_revisions": (*snapshot.belief_revisions, revision),
                    "beliefs": beliefs,
                }
            )
        if event.event_type == "goal_focused":
            goal = GoalFocus.model_validate(payload)
            return snapshot.model_copy(
                update={"goals": _replace_by_id(snapshot.goals, goal, "goal_id")}
            )
        if event.event_type == "hypothesis_opened":
            hypothesis = OpenHypothesis.model_validate(payload)
            return snapshot.model_copy(
                update={
                    "hypotheses": _replace_by_id(
                        snapshot.hypotheses,
                        hypothesis,
                        "hypothesis_id",
                    )
                }
            )
        if event.event_type == "uncertainty_recorded":
            uncertainty = UncertaintyRecord.model_validate(payload)
            return snapshot.model_copy(
                update={
                    "uncertainties": _replace_by_id(
                        snapshot.uncertainties,
                        uncertainty,
                        "uncertainty_id",
                    )
                }
            )
        if event.event_type == "expected_effect_recorded":
            expected = ExpectedActionEffect.model_validate(payload)
            return snapshot.model_copy(
                update={
                    "expected_effects": _replace_by_id(
                        snapshot.expected_effects,
                        expected,
                        "expected_effect_id",
                    )
                }
            )
        if event.event_type == "observed_effect_recorded":
            observed = ObservedActionEffect.model_validate(payload)
            return snapshot.model_copy(
                update={
                    "observed_effects": _replace_by_id(
                        snapshot.observed_effects,
                        observed,
                        "observed_effect_id",
                    )
                }
            )
        if event.event_type == "resource_state_recorded":
            resource = ResourceState.model_validate(payload)
            return snapshot.model_copy(
                update={"resources": _replace_by_id(snapshot.resources, resource, "resource_id")}
            )
        if event.event_type == "contradiction_recorded":
            contradiction = ContradictionRecord.model_validate(payload)
            return snapshot.model_copy(
                update={
                    "contradictions": _replace_by_id(
                        snapshot.contradictions,
                        contradiction,
                        "contradiction_id",
                    )
                }
            )
        if event.event_type == "retention_applied":
            retained_from_sequence = int(payload["retained_from_sequence"])
            return snapshot.model_copy(update={"retained_from_sequence": retained_from_sequence})
        raise ValueError(f"unsupported cognitive event type: {event.event_type}")


class CognitiveStateService:
    """Coordinate append-only writes, replay, checkpoints, and retention."""

    def __init__(
        self,
        *,
        repository: CognitiveStateRepository,
        projector: CognitiveStateProjector | None = None,
    ) -> None:
        self._repository = repository
        self._projector = projector or CognitiveStateProjector()
        self._snapshot_cache: CognitiveStateSnapshot | None = None

    def current_snapshot(self) -> CognitiveStateSnapshot:
        """Replay current state from the latest checkpoint plus retained events."""

        latest_sequence = self._repository.latest_sequence()
        if self._snapshot_cache is not None and self._snapshot_cache.sequence == latest_sequence:
            return self._snapshot_cache
        checkpoint = self._repository.latest_checkpoint()
        initial_snapshot = checkpoint.snapshot if checkpoint is not None else None
        from_sequence = (checkpoint.sequence + 1) if checkpoint is not None else 1
        snapshot = self._projector.replay(
            self._repository.list_events(from_sequence=from_sequence),
            initial_snapshot=initial_snapshot,
        )
        self._snapshot_cache = snapshot
        return snapshot

    def record_event(self, event: CognitiveEvent) -> CognitiveStateWriteResult:
        """Append and apply one event, or return the existing idempotent event."""

        before = self.current_snapshot()
        append_result = self._repository.append_event(event)
        if append_result.duplicate:
            after = self.current_snapshot()
            return CognitiveStateWriteResult(
                event=append_result.event,
                snapshot=after,
                transition=None,
                duplicate=True,
            )
        after, transition = self._projector.apply(before, append_result.event)
        self._snapshot_cache = after
        return CognitiveStateWriteResult(
            event=append_result.event,
            snapshot=after,
            transition=transition,
            duplicate=False,
        )

    def record_payload(
        self,
        *,
        event_type: CognitiveEventType,
        payload: dict[str, Any],
        expected_previous_sequence: int,
        provenance: CognitiveStateProvenance,
        idempotency_key: str,
        event_id: str | None = None,
    ) -> CognitiveStateWriteResult:
        """Build, append, and apply one cognitive event."""

        event = CognitiveEvent(
            event_id=event_id or f"cognitive-event-{uuid4().hex}",
            idempotency_key=idempotency_key,
            event_type=event_type,
            expected_previous_sequence=expected_previous_sequence,
            payload=payload,
            provenance=provenance,
        )
        return self.record_event(event)

    def create_checkpoint(
        self,
        *,
        checkpoint_id: str,
        provenance: CognitiveStateProvenance,
    ) -> CognitiveStateCheckpoint:
        """Create a verifiable checkpoint for the current snapshot."""

        snapshot = self.current_snapshot()
        checkpoint = CognitiveStateCheckpoint(
            checkpoint_id=checkpoint_id,
            sequence=snapshot.sequence,
            snapshot=snapshot,
            snapshot_hash=snapshot.content_hash or "",
            provenance=provenance,
        )
        return self._repository.save_checkpoint(checkpoint)

    def restore_checkpoint(self, checkpoint_id: str) -> CognitiveStateSnapshot:
        """Restore a checkpoint only when its hashes validate."""

        checkpoint = self._repository.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CognitiveStateCheckpointError("cognitive_state_checkpoint_missing")
        if checkpoint.snapshot.content_hash != checkpoint.snapshot_hash:
            raise CognitiveStateCheckpointError("cognitive_state_checkpoint_hash_mismatch")
        return checkpoint.snapshot

    def apply_retention(
        self,
        *,
        retain_from_sequence: int,
        provenance: CognitiveStateProvenance,
        idempotency_key: str,
    ) -> CognitiveStateWriteResult:
        """Apply explicit retention after a suitable checkpoint exists."""

        if retain_from_sequence < 1:
            raise ValueError("retain_from_sequence must be at least 1")
        checkpoint = self._repository.latest_checkpoint()
        required_checkpoint_sequence = retain_from_sequence - 1
        if checkpoint is None or checkpoint.sequence < required_checkpoint_sequence:
            raise CognitiveStateCheckpointError("cognitive_state_retention_checkpoint_missing")
        result = self.record_payload(
            event_type="retention_applied",
            payload={"retained_from_sequence": retain_from_sequence},
            expected_previous_sequence=self._repository.latest_sequence(),
            provenance=provenance,
            idempotency_key=idempotency_key,
            event_id=f"cognitive-retention-{retain_from_sequence}",
        )
        self._repository.delete_events_before(retain_from_sequence)
        return result


class ContradictionDetector:
    """Detect simple contradictory belief pairs without resolving them."""

    def detect(self, snapshot: CognitiveStateSnapshot) -> tuple[ContradictionRecord, ...]:
        records: list[ContradictionRecord] = []
        by_subject: dict[str, list[BeliefRecord]] = {}
        for belief in snapshot.beliefs:
            parsed = _parse_subject_value(belief.statement)
            if parsed is None:
                continue
            subject, _value = parsed
            by_subject.setdefault(subject, []).append(belief)
        for subject, beliefs in by_subject.items():
            for left_index, left in enumerate(beliefs):
                left_value = _parse_subject_value(left.statement)
                for right in beliefs[left_index + 1 :]:
                    right_value = _parse_subject_value(right.statement)
                    if left_value is None or right_value is None:
                        continue
                    if left_value[1] == right_value[1]:
                        continue
                    records.append(
                        ContradictionRecord(
                            contradiction_id=f"contradiction-{left.belief_id}-{right.belief_id}",
                            subject=subject,
                            belief_ids=(left.belief_id, right.belief_id),
                            severity="high",
                            resolved=False,
                            reason="conflicting belief values for the same subject",
                            evidence_refs=tuple(sorted({*left.source_refs, *right.source_refs})),
                        )
                    )
        return tuple(records)


class BeliefRevisionService:
    """Create belief revision events from an existing snapshot."""

    def build_revision_event(
        self,
        *,
        snapshot: CognitiveStateSnapshot,
        belief_id: str,
        revised_confidence: float,
        reason: str,
        provenance: CognitiveStateProvenance,
        idempotency_key: str,
        revision_id: str | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> CognitiveEvent:
        belief = next((item for item in snapshot.beliefs if item.belief_id == belief_id), None)
        if belief is None:
            raise ValueError("belief_id not found")
        revision = BeliefRevision(
            revision_id=revision_id or f"belief-revision-{belief_id}-{snapshot.sequence + 1}",
            belief_id=belief_id,
            previous_confidence=belief.confidence,
            revised_confidence=revised_confidence,
            reason=reason,
            evidence_refs=evidence_refs,
        )
        return CognitiveEvent(
            event_id=f"cognitive-event-{uuid4().hex}",
            idempotency_key=idempotency_key,
            event_type="belief_revised",
            expected_previous_sequence=snapshot.sequence,
            payload=revision.model_dump(mode="json"),
            provenance=provenance,
        )


class UncertaintyTracker:
    """Create uncertainty events with explicit direction calculation."""

    def build_uncertainty_event(
        self,
        *,
        subject: str,
        uncertainty_score: float,
        previous_score: float | None,
        rationale: str,
        provenance: CognitiveStateProvenance,
        expected_previous_sequence: int,
        idempotency_key: str,
        uncertainty_id: str | None = None,
        evidence_refs: tuple[str, ...] = (),
    ) -> CognitiveEvent:
        direction: UncertaintyDirection = "unchanged"
        if previous_score is not None and uncertainty_score > previous_score:
            direction = "increased"
        elif previous_score is not None and uncertainty_score < previous_score:
            direction = "reduced"
        record = UncertaintyRecord(
            uncertainty_id=uncertainty_id or f"uncertainty-{subject.strip().lower()}",
            subject=subject,
            uncertainty_score=uncertainty_score,
            direction=direction,
            rationale=rationale,
            evidence_refs=evidence_refs,
        )
        return CognitiveEvent(
            event_id=f"cognitive-event-{uuid4().hex}",
            idempotency_key=idempotency_key,
            event_type="uncertainty_recorded",
            expected_previous_sequence=expected_previous_sequence,
            payload=record.model_dump(mode="json"),
            provenance=provenance,
        )


def _replace_by_id(
    items: tuple[Any, ...],
    new_item: Any,
    id_attribute: str,
) -> tuple[Any, ...]:
    retained = [
        item
        for item in items
        if getattr(item, id_attribute) != getattr(new_item, id_attribute)
    ]
    retained.append(new_item)
    return tuple(sorted(retained, key=lambda item: getattr(item, id_attribute)))


def _apply_belief_revision(
    belief: BeliefRecord,
    revision: BeliefRevision,
    updated_at: datetime,
) -> BeliefRecord:
    if belief.belief_id != revision.belief_id:
        return belief
    return BeliefRecord(
        belief_id=belief.belief_id,
        statement=belief.statement,
        confidence=revision.revised_confidence,
        status="revised",
        source_refs=tuple(sorted({*belief.source_refs, *revision.evidence_refs})),
        revision_sequence=belief.revision_sequence + 1,
        created_at=belief.created_at,
        updated_at=updated_at.astimezone(UTC),
    )


def _parse_subject_value(statement: str) -> tuple[str, str] | None:
    if ":" in statement:
        subject, value = statement.split(":", 1)
    elif "=" in statement:
        subject, value = statement.split("=", 1)
    else:
        return None
    normalized_subject = " ".join(subject.strip().lower().split())
    normalized_value = " ".join(value.strip().lower().split())
    if not normalized_subject or not normalized_value:
        return None
    return normalized_subject, normalized_value


__all__ = [
    "BeliefRevisionService",
    "CognitiveStateProjector",
    "CognitiveStateService",
    "CognitiveStateWriteResult",
    "ContradictionDetector",
    "UncertaintyTracker",
]
