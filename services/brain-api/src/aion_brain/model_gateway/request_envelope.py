"""Model-gateway request envelopes and idempotency."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ZERO_FINGERPRINT,
    ModelGatewayContextBudgetDecision,
    ModelGatewayContextItem,
    ModelGatewayMessage,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelGatewayRequestEnvelope,
    ModelGatewayRequestIdentity,
    ModelGatewayRequestReplayRecord,
    ModelGatewaySession,
    ModelGatewaySystemInstructionPolicyBinding,
    ModelGatewayTokenBudgetDecision,
    ModelStructuredOutputSchema,
    ensure_gateway_sha256,
    ensure_gateway_utc,
)
from aion_brain.model_gateway.context_budget import safe_metadata_fingerprint


def build_request_identity(
    *,
    request_id: str,
    session: ModelGatewaySession,
    secure_runtime_request_id: str,
    created_at: datetime,
) -> ModelGatewayRequestIdentity:
    """Build a session-scoped request identity."""

    return ModelGatewayRequestIdentity(
        request_id=request_id,
        model_gateway_session_id=session.session_id,
        secure_runtime_request_id=secure_runtime_request_id,
        created_at=ensure_gateway_utc(created_at),
    )


def build_request_envelope(
    *,
    request_envelope_id: str,
    session: ModelGatewaySession,
    secure_runtime_request_id: str,
    operation: ModelGatewayOperation,
    system_policy: ModelGatewaySystemInstructionPolicyBinding,
    messages: tuple[ModelGatewayMessage, ...],
    context_items: tuple[ModelGatewayContextItem, ...],
    context_budget_decision: ModelGatewayContextBudgetDecision,
    token_budget_decision: ModelGatewayTokenBudgetDecision,
    output_mode: ModelGatewayOutputMode,
    requested_output_tokens: int,
    structured_schema: ModelStructuredOutputSchema | None,
    safe_metadata: Mapping[str, object] | None,
    created_at: datetime,
    expires_at: datetime,
) -> ModelGatewayRequestEnvelope:
    """Build a bounded request envelope without retaining raw prompt content."""

    plan = session.session_plan
    return ModelGatewayRequestEnvelope(
        request_envelope_id=request_envelope_id,
        model_gateway_session_id=session.session_id,
        secure_runtime_session_id=plan.authorization_envelope.secure_runtime_component_binding.secure_runtime_session_id,
        secure_runtime_request_id=secure_runtime_request_id,
        parent_capability_plan_fingerprint=plan.parent_capability_plan_fingerprint,
        actor_context_binding_fingerprint=plan.authorization_envelope.actor_context_binding_fingerprint,
        operation=operation,
        provider_allowlist=plan.authorization_envelope.allowed_provider_ids,
        model_allowlist=plan.authorization_envelope.allowed_model_ids,
        system_instruction_policy_fingerprint=system_policy.binding_fingerprint or "",
        message_fingerprints=tuple(item.message_fingerprint or "" for item in messages),
        context_item_fingerprints=tuple(item.item_fingerprint or "" for item in context_items),
        context_budget_fingerprint=context_budget_decision.decision_fingerprint or "",
        token_budget_fingerprint=token_budget_decision.decision_fingerprint or "",
        structured_output_schema_fingerprint=(
            structured_schema.schema_fingerprint
            if structured_schema is not None
            else ZERO_FINGERPRINT
        )
        or ZERO_FINGERPRINT,
        requested_output_mode=output_mode,
        requested_output_tokens=requested_output_tokens,
        safe_metadata_fingerprint=safe_metadata_fingerprint(safe_metadata),
        created_at=ensure_gateway_utc(created_at),
        expires_at=ensure_gateway_utc(expires_at),
    )


class InMemoryModelGatewayRequestRepository:
    """In-memory idempotency ledger; no database or file persistence."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], ModelGatewayRequestReplayRecord] = {}

    def check_request_idempotency(
        self, envelope: ModelGatewayRequestEnvelope
    ) -> tuple[str, ModelGatewayRequestReplayRecord | None]:
        """Return ``new``, ``exact_replay``, or raise on changed replay."""

        key = (envelope.model_gateway_session_id, envelope.request_envelope_id)
        existing = self._records.get(key)
        if existing is None:
            return "new", None
        if existing.request_fingerprint == envelope.request_fingerprint:
            replay = existing.model_copy(update={"exact_replay_returned": True})
            self._records = {**self._records, key: replay}
            return "exact_replay", replay
        rejected = existing.model_copy(update={"changed_replay_rejected": True})
        self._records = {**self._records, key: rejected}
        raise ValueError("changed replay rejected")

    def record_safe_result(
        self,
        *,
        envelope: ModelGatewayRequestEnvelope,
        safe_result_fingerprint: str,
        created_at: datetime,
    ) -> ModelGatewayRequestReplayRecord:
        """Record the safe result fingerprint for exact replay."""

        safe_result_fingerprint = ensure_gateway_sha256(safe_result_fingerprint)
        key = (envelope.model_gateway_session_id, envelope.request_envelope_id)
        record = ModelGatewayRequestReplayRecord(
            request_id=envelope.request_envelope_id,
            model_gateway_session_id=envelope.model_gateway_session_id,
            request_fingerprint=envelope.request_fingerprint or "",
            safe_result_fingerprint=safe_result_fingerprint,
            created_at=ensure_gateway_utc(created_at),
        )
        self._records = {**self._records, key: record}
        return record

    def list_records(self) -> tuple[ModelGatewayRequestReplayRecord, ...]:
        """Return replay records in deterministic order."""

        return tuple(self._records[key] for key in sorted(self._records))
