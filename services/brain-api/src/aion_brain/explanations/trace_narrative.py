"""Trace narrative builder."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.trace_narratives import TraceNarrative, TraceNarrativeRequest
from aion_brain.explanations._shared import (
    authorize,
    clamp,
    emit_explanation_telemetry,
    items_from_source,
    now_utc,
    object_id,
    object_value,
    string_refs,
    unique,
)
from aion_brain.explanations.redaction import sanitize_explanation_payload
from aion_brain.explanations.repository import ExplanationRepository


class TraceNarrativeBuilder:
    """Build public narratives from observable records in one trace."""

    def __init__(
        self,
        explanation_repository: ExplanationRepository,
        policy_adapter: object,
        *,
        audit_ledger: object | None = None,
        provenance_service: object | None = None,
        event_repository: object | None = None,
        command_service: object | None = None,
        policy_service: object | None = None,
        approval_service: object | None = None,
        decision_service: object | None = None,
        outcome_service: object | None = None,
        response_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = explanation_repository
        self._policy_adapter = policy_adapter
        self._audit_ledger = audit_ledger
        self._provenance_service = provenance_service
        self._event_repository = event_repository
        self._command_service = command_service
        self._policy_service = policy_service
        self._approval_service = approval_service
        self._decision_service = decision_service
        self._outcome_service = outcome_service
        self._response_service = response_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def build(self, request: TraceNarrativeRequest) -> TraceNarrative:
        """Build and persist a trace narrative."""

        if not bool(getattr(self._settings, "trace_narratives_enabled", True)):
            raise RuntimeError("trace_narratives_disabled")
        authorize(
            self._policy_adapter,
            action_type="explanation.trace_narrative.create",
            resource_type="trace",
            resource_id=request.trace_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            context={"max_timeline_items": request.max_timeline_items},
        )
        records = _records_for(request, self)
        timeline, redaction = _timeline(records, request.max_timeline_items)
        audit_refs = unique(
            [object_id(record, "audit_entry_id") or "" for record in records["audit_entries"]]
        )
        decisions = _public_records(records["policy_decisions"], ("decision_id",))
        outcomes = _public_records(records["outcomes"], ("outcome_id",))
        approvals = _public_records(records["approvals"], ("approval_request_id",))
        blockers = [
            item
            for item in decisions
            if str(item.get("allow", "true")).lower() == "false"
            or str(item.get("reason", "")).endswith("denied")
        ]
        blockers.extend(
            item
            for item in approvals
            if str(item.get("status", "")).lower() in {"pending", "denied", "expired"}
        )
        narrative = TraceNarrative(
            trace_narrative_id=request.trace_narrative_id or f"trace-narrative-{uuid4().hex}",
            trace_id=request.trace_id,
            status=cast(Any, "completed" if timeline else "insufficient_records"),
            title=f"Trace narrative for {request.trace_id}",
            summary=(
                f"This trace contains {len(records['audit_entries'])} audit entries, "
                f"{len(decisions)} decisions, {len(outcomes)} outcomes, "
                f"and {len(blockers)} blockers."
            ),
            timeline=timeline,
            key_decisions=decisions,
            blockers=blockers,
            approvals=approvals,
            outcomes=outcomes,
            evidence_refs=unique(
                [
                    ref
                    for record in [*records["outcomes"], *records["responses"]]
                    for ref in string_refs(object_value(record, "evidence_refs", []))
                ]
            ),
            audit_refs=audit_refs,
            confidence=clamp(0.4 + (0.1 if timeline else 0.0) + (0.1 if audit_refs else 0.0)),
            redaction_metadata=redaction,
            metadata={"owner_scope": request.owner_scope, **request.metadata},
            created_by=request.created_by,
            created_at=now_utc(),
        )
        stored = self._repository.save_trace_narrative(narrative)
        self._audit(request, stored)
        emit_explanation_telemetry(
            self._telemetry_service,
            event_type="trace_narrative_created",
            node_type="trace_narrative",
            node_id=stored.trace_narrative_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            owner_scope=request.owner_scope,
            payload={"status": stored.status, "timeline_count": len(stored.timeline)},
        )
        return stored

    def get(self, trace_narrative_id: str, scope: list[str]) -> TraceNarrative | None:
        """Return one trace narrative."""

        authorize(
            self._policy_adapter,
            action_type="explanation.trace_narrative.read",
            resource_type="trace_narrative",
            resource_id=trace_narrative_id,
            scope=scope,
        )
        narrative = self._repository.get_trace_narrative(trace_narrative_id)
        if narrative is None:
            return None
        owner_scope = narrative.metadata.get("owner_scope")
        if isinstance(owner_scope, list) and not set(owner_scope) & set(scope):
            return None
        return narrative

    def list(self, trace_id: str | None = None, limit: int = 50) -> list[TraceNarrative]:
        """List trace narratives."""

        return self._repository.list_trace_narratives(trace_id=trace_id, limit=limit)

    def _audit(self, request: TraceNarrativeRequest, narrative: TraceNarrative) -> None:
        record_audit_event(
            self._audit_ledger,
            action_type="explanation.trace_narrative.create",
            resource_type="trace_narrative",
            resource_id=narrative.trace_narrative_id,
            event_type="trace_narrative_created",
            outcome="completed" if narrative.status != "failed" else "failed",
            source_component="trace_narrative_builder",
            trace_id=narrative.trace_id,
            payload={
                "timeline_count": len(narrative.timeline),
                "decision_count": len(narrative.key_decisions),
                "blocker_count": len(narrative.blockers),
            },
            metadata={"owner_scope": request.owner_scope},
        )


def _records_for(
    request: TraceNarrativeRequest, builder: TraceNarrativeBuilder
) -> dict[str, list[Any]]:
    return {
        "audit_entries": (
            items_from_source(
                builder._audit_ledger,
                ("list_entries", "list"),
                trace_id=request.trace_id,
                limit=request.max_timeline_items,
                ascending=True,
            )
            if request.include_audit
            else []
        ),
        "provenance_links": (
            items_from_source(
                builder._provenance_service,
                ("graph_for_trace", "list_links"),
                request.trace_id,
                limit=request.max_timeline_items,
            )
            if request.include_provenance
            else []
        ),
        "events": (
            items_from_source(
                builder._event_repository,
                ("list_by_trace", "list_events", "list"),
                request.trace_id,
            )
            if request.include_events
            else []
        ),
        "commands": items_from_source(
            builder._command_service, ("list_commands", "list"), request.trace_id
        ),
        "policy_decisions": (
            items_from_source(
                builder._policy_service,
                ("list_policy_decisions", "list_decisions"),
                request.trace_id,
            )
            if request.include_decisions
            else []
        ),
        "approvals": (
            items_from_source(
                builder._approval_service,
                ("list_pending", "list_requests", "list"),
                request.owner_scope,
            )
            if request.include_approvals
            else []
        ),
        "decisions": (
            items_from_source(
                builder._decision_service,
                ("list_decisions", "list_records", "list"),
                request.trace_id,
            )
            if request.include_decisions
            else []
        ),
        "outcomes": (
            items_from_source(
                builder._outcome_service,
                ("list_outcomes", "list", "query"),
                scope=request.owner_scope,
                limit=100,
            )
            if request.include_outcomes
            else []
        ),
        "responses": items_from_source(
            builder._response_service, ("list_responses", "list"), request.trace_id
        ),
    }


def _timeline(
    records: dict[str, list[Any]], limit: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    redaction: dict[str, Any] = {
        "redacted": False,
        "redaction_count": 0,
        "removed_count": 0,
        "field_paths": [],
        "removed_field_paths": [],
    }
    for source_type, items in records.items():
        for item in items:
            raw_payload = _public_payload(item)
            payload, item_redaction = sanitize_explanation_payload(raw_payload)
            redaction = _merge_redaction(redaction, item_redaction)
            rows.append(
                {
                    "source_type": source_type.rstrip("s"),
                    "source_id": _generic_id(item),
                    "event_type": str(
                        object_value(
                            item, "event_type", object_value(item, "action_type", source_type)
                        )
                    ),
                    "title": _title(source_type, item),
                    "timestamp": _timestamp(item),
                    "status": str(
                        object_value(item, "status", object_value(item, "outcome", "unknown"))
                    ),
                    "payload": payload,
                    "source": source_type,
                }
            )
    rows.sort(key=lambda item: str(item.get("timestamp") or ""))
    return rows[:limit], redaction


def _public_records(items: list[Any], id_names: tuple[str, ...]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in items:
        payload = _public_payload(item)
        payload["id"] = object_id(item, *id_names) or _generic_id(item)
        records.append(payload)
    return records


def _public_payload(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return {
            key: value
            for key, value in item.items()
            if key not in {"canonical_payload", "payload", "raw_prompt", "hidden_reasoning"}
        }
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        data = dump(mode="json")
        return {
            key: value
            for key, value in data.items()
            if key not in {"canonical_payload", "payload", "raw_prompt", "hidden_reasoning"}
        }
    return {
        "id": _generic_id(item),
        "status": object_value(item, "status", "unknown"),
    }


def _generic_id(item: object) -> str | None:
    return object_id(
        item,
        "audit_entry_id",
        "provenance_link_id",
        "event_id",
        "command_id",
        "decision_id",
        "decision_record_id",
        "approval_request_id",
        "outcome_id",
        "response_id",
    )


def _timestamp(item: object) -> str | None:
    raw = object_value(item, "created_at", object_value(item, "timestamp", None))
    return str(raw) if raw is not None else None


def _title(source_type: str, item: object) -> str:
    explicit = object_value(item, "title", None)
    if explicit:
        return str(explicit)
    event_type = object_value(item, "event_type", object_value(item, "action_type", source_type))
    return f"{source_type.rstrip('s')} {event_type}"


def _merge_redaction(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "redacted": bool(left.get("redacted")) or bool(right.get("redacted")),
        "redaction_count": int(left.get("redaction_count", 0))
        + int(right.get("redaction_count", 0)),
        "removed_count": int(left.get("removed_count", 0)) + int(right.get("removed_count", 0)),
        "field_paths": [*left.get("field_paths", []), *right.get("field_paths", [])],
        "removed_field_paths": [
            *left.get("removed_field_paths", []),
            *right.get("removed_field_paths", []),
        ],
    }


__all__ = ["TraceNarrativeBuilder"]
