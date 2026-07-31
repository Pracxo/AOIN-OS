"""AION-233 authorization, component binding, and gateway sessions."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    AUTHORIZATION_TRANSACTION_ID,
    DETERMINISTIC_PROVIDER_ID,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    ModelGatewayAuthorizationEnvelope,
    ModelGatewayComponentInvocationBinding,
    ModelGatewayContextBudget,
    ModelGatewaySession,
    ModelGatewaySessionPlan,
    ModelGatewaySessionStatus,
    ModelGatewayTokenBudget,
    ensure_gateway_sha256,
    ensure_gateway_utc,
    local_model_gateway_confirmation_fingerprint,
)
from aion_brain.contracts.secure_runtime import (
    SecureCapabilityInvocationPlan,
    SecureRuntimeDispatchStatus,
    SecureRuntimeGuardDecision,
    SecureRuntimeGuardOutcome,
    SecureRuntimeSession,
    SecureRuntimeSessionState,
    SecureSimulatedDispatchResult,
)


def bind_secure_runtime_component(
    *,
    binding_id: str,
    secure_runtime_session: SecureRuntimeSession,
    parent_capability_plan: SecureCapabilityInvocationPlan,
    parent_runtime_guard: SecureRuntimeGuardDecision,
    parent_simulated_dispatch: SecureSimulatedDispatchResult,
    actor_context_binding_fingerprint: str,
    invoked_at: datetime,
) -> ModelGatewayComponentInvocationBinding:
    """Bind the AION-231 secure-runtime foundation under AION-232 authority."""

    if parent_capability_plan.capability_code != "brain.think.simulate":
        raise ValueError("parent capability must be brain.think.simulate")
    if parent_runtime_guard.outcome != SecureRuntimeGuardOutcome.allow_simulation:
        raise ValueError("parent runtime guard must allow simulation")
    if parent_simulated_dispatch.status != SecureRuntimeDispatchStatus.simulated:
        raise ValueError("parent dispatch must be simulated")
    if (
        parent_simulated_dispatch.actual_execution_performed
        or parent_simulated_dispatch.external_call_performed
        or parent_simulated_dispatch.production_effect
    ):
        raise ValueError("parent dispatch cannot have external or production effects")
    if secure_runtime_session.current_state not in {
        SecureRuntimeSessionState.session_active,
        SecureRuntimeSessionState.request_validated,
        SecureRuntimeSessionState.response_recorded,
    }:
        raise ValueError("parent secure-runtime session must be active")
    if secure_runtime_session.expires_at <= ensure_gateway_utc(invoked_at):
        raise ValueError("parent secure-runtime session is expired")
    return ModelGatewayComponentInvocationBinding(
        binding_id=binding_id,
        secure_runtime_session_id=secure_runtime_session.session_id,
        secure_runtime_request_id=parent_capability_plan.request_id,
        actor_context_binding_fingerprint=actor_context_binding_fingerprint,
        parent_capability_plan_fingerprint=parent_capability_plan.plan_fingerprint or "",
        parent_runtime_guard_fingerprint=parent_runtime_guard.guard_decision_fingerprint or "",
        parent_simulated_dispatch_fingerprint=parent_simulated_dispatch.result_fingerprint or "",
        input_fingerprints=(
            secure_runtime_session.session_fingerprint or "",
            parent_capability_plan.plan_fingerprint or "",
        ),
        output_fingerprints=(
            parent_runtime_guard.guard_decision_fingerprint or "",
            parent_simulated_dispatch.result_fingerprint or "",
        ),
        invoked_at=ensure_gateway_utc(invoked_at),
    )


def create_authorization_envelope(
    *,
    model_gateway_session_id: str,
    secure_runtime_component_binding: ModelGatewayComponentInvocationBinding,
    operator_identity_fingerprint: str,
    actor_context_binding_fingerprint: str,
    created_at: datetime,
    expires_at: datetime,
    context_budget: ModelGatewayContextBudget | None = None,
    token_budget: ModelGatewayTokenBudget | None = None,
) -> ModelGatewayAuthorizationEnvelope:
    """Create the exact AION-232-SRI-0002 gateway authorization envelope."""

    return ModelGatewayAuthorizationEnvelope(
        model_gateway_session_id=model_gateway_session_id,
        secure_runtime_component_binding=secure_runtime_component_binding,
        operator_identity_fingerprint=operator_identity_fingerprint,
        actor_context_binding_fingerprint=actor_context_binding_fingerprint,
        context_budget=context_budget or ModelGatewayContextBudget(),
        token_budget=token_budget or ModelGatewayTokenBudget(),
        created_at=ensure_gateway_utc(created_at),
        expires_at=ensure_gateway_utc(expires_at),
        confirmation_fingerprint=local_model_gateway_confirmation_fingerprint(),
    )


def create_session_plan(
    *,
    session_plan_id: str,
    authorization_envelope: ModelGatewayAuthorizationEnvelope,
    secure_runtime_session_fingerprint: str,
    parent_capability_plan_fingerprint: str,
    parent_runtime_guard_fingerprint: str,
    parent_simulated_dispatch_fingerprint: str,
    provider_manifest_fingerprints: tuple[str, ...],
    model_manifest_fingerprints: tuple[str, ...],
    created_at: datetime,
    expires_at: datetime,
) -> ModelGatewaySessionPlan:
    """Create a bounded local model-gateway session plan."""

    return ModelGatewaySessionPlan(
        session_plan_id=session_plan_id,
        authorization_envelope=authorization_envelope,
        secure_runtime_session_fingerprint=ensure_gateway_sha256(
            secure_runtime_session_fingerprint
        ),
        parent_capability_plan_fingerprint=parent_capability_plan_fingerprint,
        parent_runtime_guard_fingerprint=parent_runtime_guard_fingerprint,
        parent_simulated_dispatch_fingerprint=parent_simulated_dispatch_fingerprint,
        provider_manifest_fingerprints=provider_manifest_fingerprints,
        model_manifest_fingerprints=model_manifest_fingerprints,
        allowed_operations=authorization_envelope.allowed_operations,
        created_at=ensure_gateway_utc(created_at),
        expires_at=ensure_gateway_utc(expires_at),
    )


def validate_authorization(envelope: ModelGatewayAuthorizationEnvelope) -> None:
    """Fail closed unless the envelope is exactly AION-232-SRI-0002."""

    if (
        envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
        or envelope.allowed_provider_ids != (DETERMINISTIC_PROVIDER_ID,)
        or envelope.allowed_model_ids != (REFERENCE_JSON_MODEL_ID, REFERENCE_TEXT_MODEL_ID)
        or not envelope.simulation_only
        or envelope.actual_provider_call
        or envelope.network_access
        or envelope.credential_access
        or envelope.production_runtime
        or envelope.production_effect
    ):
        raise ValueError("model-gateway authorization mismatch")


class InMemoryModelGatewaySessionRepository:
    """Copy-on-write session repository with one active gateway session."""

    def __init__(self) -> None:
        self._sessions: dict[str, ModelGatewaySession] = {}

    def start_session(self, plan: ModelGatewaySessionPlan) -> ModelGatewaySession:
        """Start one authorized session."""

        if any(
            session.status == ModelGatewaySessionStatus.active
            for session in self._sessions.values()
        ):
            raise ValueError("only one active model-gateway session is allowed")
        session = ModelGatewaySession(
            session_id=plan.authorization_envelope.model_gateway_session_id,
            session_plan=plan,
            status=ModelGatewaySessionStatus.active,
            created_at=plan.created_at,
            expires_at=plan.expires_at,
        )
        self._sessions = {**self._sessions, session.session_id: session}
        return session

    def session_by_id(self, session_id: str) -> ModelGatewaySession | None:
        """Return a session snapshot."""

        return self._sessions.get(session_id)

    def active_sessions(self) -> tuple[ModelGatewaySession, ...]:
        """Return active sessions in deterministic order."""

        return tuple(
            self._sessions[key]
            for key in sorted(self._sessions)
            if self._sessions[key].status == ModelGatewaySessionStatus.active
        )

    def mark_request_active(self, session_id: str, request_id: str) -> ModelGatewaySession:
        """Add an active request to a session snapshot."""

        session = self._require_session(session_id)
        if (
            request_id not in session.active_request_ids
            and len(session.active_request_ids) >= session.session_plan.maximum_concurrent_requests
        ):
            raise ValueError("model-gateway concurrent request limit exceeded")
        active = tuple(sorted({*session.active_request_ids, request_id}))
        payload = session.model_dump(mode="python")
        payload["active_request_ids"] = active
        payload.pop("session_fingerprint", None)
        updated = ModelGatewaySession.model_validate(payload)
        self._sessions = {**self._sessions, session_id: updated}
        return updated

    def close_request(self, session_id: str, request_id: str) -> ModelGatewaySession:
        """Close one request and release its active reference."""

        session = self._require_session(session_id)
        active = tuple(item for item in session.active_request_ids if item != request_id)
        completed = tuple(sorted({*session.completed_request_ids, request_id}))
        payload = session.model_dump(mode="python")
        payload["active_request_ids"] = active
        payload["completed_request_ids"] = completed
        payload.pop("session_fingerprint", None)
        updated = ModelGatewaySession.model_validate(payload)
        self._sessions = {**self._sessions, session_id: updated}
        return updated

    def close_session(self, session_id: str, closed_at: datetime) -> ModelGatewaySession:
        """Close a session and release every request reference."""

        session = self._require_session(session_id)
        payload = session.model_dump(mode="python")
        payload["status"] = ModelGatewaySessionStatus.closed
        payload["active_request_ids"] = ()
        payload["closed_at"] = ensure_gateway_utc(closed_at)
        payload.pop("session_fingerprint", None)
        updated = ModelGatewaySession.model_validate(payload)
        self._sessions = {**self._sessions, session_id: updated}
        return updated

    def _require_session(self, session_id: str) -> ModelGatewaySession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError("unknown model-gateway session")
        return session
