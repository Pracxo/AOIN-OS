"""Contract serialization tests."""

from datetime import UTC, datetime

from aion_brain.contracts import (
    AIONEvent,
    BrainState,
    CapabilityManifest,
    ContextPacket,
    DecisionTrace,
    IntentFrame,
    LearningSignal,
    MemoryRecord,
    PlanGraph,
    PlanStep,
    PolicyDecision,
)


def test_contracts_dump_and_preserve_required_ids() -> None:
    """Every public contract can serialize and keeps its primary ID."""
    now = datetime.now(UTC)
    instances = [
        (
            "event_id",
            AIONEvent(
                event_id="event-1",
                source="test",
                event_type="test.received",
                actor_id=None,
                workspace_id="workspace-1",
                payload_type="test",
                payload={"message": "hello"},
                timestamp=now,
                correlation_id=None,
                trace_id="trace-1",
                security_scope=["workspace:read"],
            ),
        ),
        (
            "intent_id",
            IntentFrame(
                intent_id="intent-1",
                event_id="event-1",
                intent_type="scaffold",
                goal="Validate contracts",
                urgency="low",
                risk_level="low",
                requires_memory=False,
                requires_capability=False,
                requires_approval=None,
                confidence=1.0,
            ),
        ),
        (
            "context_id",
            ContextPacket(
                context_id="context-1",
                intent_id="intent-1",
                goal="Validate contracts",
                known_context=[{"source": "test"}],
                retrieved_memory_ids=[],
                available_capability_ids=[],
                constraints=[],
                open_questions=[],
                execution_limits={"max_steps": 0},
            ),
        ),
        (
            "memory_id",
            MemoryRecord(
                memory_id="memory-1",
                memory_type="episodic",
                owner_scope=["workspace-1"],
                source_event_id="event-1",
                content_ref=None,
                summary="Test memory",
                confidence=1.0,
                sensitivity="low",
                created_at=now,
                expires_at=None,
                metadata={"test": True},
            ),
        ),
        (
            "module_id",
            CapabilityManifest(
                module_id="module-1",
                version="0.1.0",
                capabilities=[{"id": "capability-1", "risk": "low"}],
                permissions_required=[],
                memory_read_scopes=[],
                memory_write_scopes=[],
                events_subscribed=[],
                events_published=[],
                execution_mode="manual",
            ),
        ),
        (
            "plan_id",
            PlanGraph(
                plan_id="plan-1",
                intent_id="intent-1",
                goal="Validate contracts",
                steps=[
                    PlanStep(
                        step_id="retrieve_context",
                        action_type="memory.retrieve",
                        capability_required="memory.retrieve",
                        risk_level="low",
                        status="pending",
                    )
                ],
                dependencies=[],
                risk_level="low",
                approval_required=False,
                status="draft",
            ),
        ),
        (
            "decision_id",
            PolicyDecision(
                decision_id="decision-1",
                trace_id="trace-1",
                allow=True,
                approval_required=False,
                reason="Scaffold test",
                constraints=[],
                audit_level="standard",
            ),
        ),
        (
            "trace_id",
            DecisionTrace(
                trace_id="trace-1",
                event_id="event-1",
                intent_id="intent-1",
                context_id="context-1",
                plan_id="plan-1",
                memory_refs=["memory-1"],
                capability_refs=["capability-1"],
                policy_decisions=["decision-1"],
                outcome={"status": "ok"},
                created_at=now,
            ),
        ),
        (
            "status",
            BrainState(
                event=AIONEvent(
                    event_id="event-state",
                    source="test",
                    event_type="question.answer",
                    actor_id=None,
                    workspace_id=None,
                    payload_type="test",
                    payload={"question": "what is the state?"},
                    timestamp=now,
                    correlation_id=None,
                    trace_id="trace-state",
                    security_scope=[],
                ),
                status="started",
            ),
        ),
        (
            "learning_id",
            LearningSignal(
                learning_id="learning-1",
                trace_id="trace-1",
                learning_type="planning_pattern_candidate",
                signal={"score": 1},
                confidence=0.9,
                promotion_status="candidate",
                created_at=now,
            ),
        ),
    ]

    for id_field, instance in instances:
        dumped = instance.model_dump(mode="json")

        assert dumped[id_field] == getattr(instance, id_field)
        assert isinstance(dumped, dict)


def test_datetime_fields_serialize_cleanly() -> None:
    """Datetime contract fields become JSON-safe strings."""
    now = datetime.now(UTC)
    event = AIONEvent(
        event_id="event-2",
        source="test",
        event_type="test.received",
        actor_id=None,
        workspace_id=None,
        payload_type="test",
        payload={},
        timestamp=now,
        correlation_id=None,
        trace_id=None,
        security_scope=[],
    )

    dumped = event.model_dump(mode="json")

    assert isinstance(dumped["timestamp"], str)
