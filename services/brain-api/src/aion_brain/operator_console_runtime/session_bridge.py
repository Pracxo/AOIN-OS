"""Controlled local Operator Console service bridge."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from aion_brain.capability_runtime.dispatcher import (
    ControlledSandboxedCapabilityRuntimeService,
)
from aion_brain.contracts.model_gateway import (
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelStructuredOutputSchema,
    content_fingerprint,
)
from aion_brain.contracts.operator_console_integration import (
    ALL_RESOURCE_LIMITS,
    LOOPBACK_BIND_HOST,
    ZERO_FINGERPRINT,
    OperatorConsoleActionKind,
    OperatorConsoleCapabilityExecutionRequest,
    OperatorConsoleComponentBinding,
    OperatorConsoleConnectorSimulationRequest,
    OperatorConsoleHttpDisposition,
    OperatorConsoleIntegrationAuthorizationEnvelope,
    OperatorConsoleKillSwitchRequest,
    OperatorConsoleMode,
    OperatorConsoleModelSimulationRequest,
    OperatorConsoleSecurityHeaders,
    OperatorConsoleSession,
    OperatorConsoleSessionBootstrap,
    OperatorConsoleSessionCloseRequest,
    OperatorConsoleSessionStatus,
    OperatorConsoleStaticAssetManifest,
    canonical_json,
    default_route_manifest,
    fingerprint_mapping,
    fingerprint_text,
    json_depth,
    utc_now,
)
from aion_brain.contracts.sandboxed_capability_runtime import (
    CapabilityRuntimeRejected,
)
from aion_brain.contracts.secure_runtime import (
    SecureRuntimeKillSwitch,
    SecureRuntimeKillSwitchState,
    SecureRuntimeKillSwitchStatus,
)
from aion_brain.model_gateway.reference_provider import (
    DeterministicReferenceModelProvider,
    build_reference_provider_request,
)
from aion_brain.operator_console_runtime.audit import InMemoryOperatorConsoleAuditLedger
from aion_brain.operator_console_runtime.authorization import build_authorization_envelope
from aion_brain.operator_console_runtime.component_binding import build_component_binding
from aion_brain.operator_console_runtime.observability import OperatorConsoleObservabilityRecorder
from aion_brain.operator_console_runtime.request_nonce import InMemoryMutationNonceStore
from aion_brain.operator_console_runtime.view_models import (
    action_projection,
    health_projection,
    receipt_projection,
    status_projection,
)


class ControlledLocalOperatorConsoleService:
    """One-session same-origin bridge to AION-231, AION-233, and AION-235."""

    def __init__(
        self,
        *,
        bound_port: int,
        static_asset_manifest: OperatorConsoleStaticAssetManifest,
        nonce_store: InMemoryMutationNonceStore | None = None,
        audit_ledger: InMemoryOperatorConsoleAuditLedger | None = None,
        observability: OperatorConsoleObservabilityRecorder | None = None,
    ) -> None:
        self.bound_port = bound_port
        self.bound_origin = f"http://{LOOPBACK_BIND_HOST}:{bound_port}"
        self.static_asset_manifest = static_asset_manifest
        self.nonce_store = nonce_store or InMemoryMutationNonceStore()
        self.audit_ledger = audit_ledger or InMemoryOperatorConsoleAuditLedger()
        self.observability_recorder = observability or OperatorConsoleObservabilityRecorder()
        self.model_provider = DeterministicReferenceModelProvider()
        self.capability_service = ControlledSandboxedCapabilityRuntimeService.create_default()
        self._console_session: OperatorConsoleSession | None = None
        self._authorization: OperatorConsoleIntegrationAuthorizationEnvelope | None = None
        self._component_binding: OperatorConsoleComponentBinding | None = None
        self._capability_session_id: str | None = None
        self._session_sequence = 0
        self._last_session_id: str | None = None
        self._last_receipt_fingerprint = ZERO_FINGERPRINT
        self._kill_switch = _initial_kill_switch("operator-console-session-000")

    @property
    def console_session(self) -> OperatorConsoleSession | None:
        return self._console_session

    @property
    def authorization(self) -> OperatorConsoleIntegrationAuthorizationEnvelope | None:
        return self._authorization

    @property
    def component_binding(self) -> OperatorConsoleComponentBinding | None:
        return self._component_binding

    def bootstrap(self, *, host: str, origin: str) -> tuple[dict[str, Any], str]:
        session = self._ensure_session(host=host, origin=origin)
        raw_nonce = self.nonce_store.current_raw_nonce(session.console_session_id)
        if raw_nonce is None:
            issued = self.nonce_store.issue(
                console_session_id=session.console_session_id,
                host=host,
                origin=origin or self.bound_origin,
                expires_at=session.expires_at,
            )
            raw_nonce = issued.raw_nonce
            self.audit_ledger.append(
                session_id=session.console_session_id,
                event_type="nonce_issued",
                subject_fingerprints=(issued.record.nonce_fingerprint,),
                reason_codes=("bootstrap_nonce_issued",),
            )
        current = self.nonce_store.current_record(session.console_session_id)
        if current is None:
            raise ValueError("mutation nonce state missing")
        self._console_session = session.model_copy(
            update={"bootstrap_count": session.bootstrap_count + 1}
        )
        self.observability_recorder.increment("bootstrap_reads")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="bootstrap_served",
            subject_fingerprints=(current.nonce_fingerprint,),
            reason_codes=("same_origin_bootstrap",),
        )
        bootstrap = OperatorConsoleSessionBootstrap(
            console_session_id=session.console_session_id,
            secure_runtime_session_fingerprint=fingerprint_text(
                "secure-runtime-session", session.console_session_id
            ),
            operator_identity_fingerprint=session.authorization.operator_identity_fingerprint,
            actor_context_fingerprint=session.authorization.actor_context_fingerprint,
            bound_origin=self.bound_origin,
            route_manifest=default_route_manifest(),
            static_asset_manifest=self.static_asset_manifest,
            security_headers=OperatorConsoleSecurityHeaders(),
            current_nonce_fingerprint=current.nonce_fingerprint,
            expires_at=session.expires_at,
            idle_expires_at=session.idle_expires_at,
            browser_persistence_flags={
                "cookies": False,
                "local_storage": False,
                "session_storage": False,
                "indexeddb": False,
            },
            production_flags={
                "production_runtime_authorized": False,
                "production_effect": False,
                "production_exposure": False,
            },
        )
        return _payload({"ok": True, "bootstrap": bootstrap.model_dump(mode="json")}), raw_nonce

    def validate_nonce(self, *, raw_nonce: str | None, host: str, origin: str) -> None:
        session = self._require_active_or_terminal_session()
        self.nonce_store.validate(
            console_session_id=session.console_session_id,
            raw_nonce=raw_nonce,
            host=host,
            origin=origin,
        )
        self.observability_recorder.increment("nonce_validations")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="nonce_validated",
            reason_codes=("nonce_current",),
        )

    def rotate_nonce(self, *, raw_nonce: str, host: str, origin: str) -> str:
        session = self._require_active_session()
        issued = self.nonce_store.consume_and_rotate(
            console_session_id=session.console_session_id,
            raw_nonce=raw_nonce,
            host=host,
            origin=origin,
            expires_at=session.expires_at,
        )
        self.observability_recorder.increment("mutation_nonce_rotations")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="nonce_rotated",
            subject_fingerprints=(issued.record.nonce_fingerprint,),
            reason_codes=("accepted_non_terminal_post",),
        )
        return issued.raw_nonce

    def invalidate_nonce(self) -> None:
        session_id = self._last_session_id
        if session_id is not None:
            self.nonce_store.invalidate(session_id)

    def status(self) -> dict[str, Any]:
        session = self._require_active_or_terminal_session()
        self.observability_recorder.increment("status_reads")
        projection = status_projection(
            console_session_state=session.status,
            kill_switch_state=self._kill_switch.state.status.value,
            active_request_count=len(session.active_request_ids),
            receipt_count=session.receipt_count,
            audit_count=len(self.audit_ledger.records_by_session(session.console_session_id)),
        )
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="status_projected",
            reason_codes=("redacted_status",),
        )
        return _payload({"ok": True, "status": projection.model_dump(mode="json")})

    def health(self, *, listener_active: bool) -> dict[str, Any]:
        session = self._require_active_or_terminal_session()
        self.observability_recorder.increment("health_reads")
        projection = health_projection(
            session_valid=session.status == OperatorConsoleSessionStatus.active,
            nonce_valid=self.nonce_store.current_record(session.console_session_id) is not None,
            kill_switch_clear=self._kill_switch.state.status == SecureRuntimeKillSwitchStatus.clear,
            listener_active=listener_active,
        )
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="health_projected",
            reason_codes=("redacted_health",),
        )
        return _payload({"ok": True, "health": projection.model_dump(mode="json")})

    def observability(self) -> dict[str, Any]:
        session = self._require_active_or_terminal_session()
        self.observability_recorder.increment("observability_reads")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="observability_projected",
            reason_codes=("redacted_observability",),
        )
        return _payload(
            {
                "ok": True,
                "observability": self.observability_recorder.snapshot().model_dump(
                    mode="json"
                ),
            }
        )

    def audit(self) -> dict[str, Any]:
        session = self._require_active_or_terminal_session()
        self.observability_recorder.increment("audit_reads")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            event_type="audit_projected",
            reason_codes=("redacted_audit",),
        )
        projection = self.audit_ledger.projection(
            session_id=session.console_session_id,
            receipt_chain_heads=self._receipt_chain_heads(),
        )
        return _payload({"ok": True, "audit": projection.model_dump(mode="json")})

    def simulate_model(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        session = self._require_active_session()
        request = OperatorConsoleModelSimulationRequest.model_validate(payload)
        mode = (
            ModelGatewayOutputMode.structured_json
            if request.mode == "structured_json"
            else ModelGatewayOutputMode.text
        )
        operation = (
            ModelGatewayOperation.structured_generate_simulate
            if request.mode == "structured_json"
            else ModelGatewayOperation.text_generate_simulate
        )
        model_id = (
            REFERENCE_JSON_MODEL_ID
            if request.mode == "structured_json"
            else REFERENCE_TEXT_MODEL_ID
        )
        schema = _structured_schema(request.structured_output_schema, request.request_id)
        request_fingerprint = fingerprint_mapping(
            "model-simulation-request",
            {
                "request_id": request.request_id,
                "mode": request.mode,
                "prompt": fingerprint_text("prompt", request.transient_prompt),
                "metadata": request.safe_metadata,
            },
        )
        reference_request = build_reference_provider_request(
            reference_request_id=f"reference-{request.request_id}",
            model_id=model_id,
            request_fingerprint=request_fingerprint,
            operation=operation,
            output_mode=mode,
            requested_output_tokens=256,
            structured_schema=schema,
            created_at=utc_now(),
        )
        response = self.model_provider.simulate(
            reference_request=reference_request,
            structured_schema=schema,
            created_at=utc_now(),
        )
        output = response.transient_output
        encoded = canonical_json({"output": output}).encode("utf-8")
        projection = action_projection(
            action_kind=(
                OperatorConsoleActionKind.model_structured_simulation
                if request.mode == "structured_json"
                else OperatorConsoleActionKind.model_text_simulation
            ),
            request_id=request.request_id,
            transient_output=output,
            output_fingerprint=response.output_fingerprint,
            output_byte_count=len(encoded),
        )
        self._record_receipt(session, request.request_id, projection.receipt_fingerprint)
        self.observability_recorder.increment(f"model_{request.mode}_simulations")
        self.observability_recorder.increment("operator_confirmations_validated")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request.request_id,
            event_type="model_simulation_completed",
            subject_fingerprints=(response.output_fingerprint,),
            reason_codes=("deterministic_reference_provider", "untrusted_output"),
        )
        return _action_payload(projection, output)

    def execute_capability(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        session = self._require_active_session()
        request = OperatorConsoleCapabilityExecutionRequest.model_validate(payload)
        if request.safe_metadata.get("model_output_triggered") is True:
            self.observability_recorder.increment("model_output_triggered_executions_blocked")
            self.audit_ledger.append(
                session_id=session.console_session_id,
                request_id=request.request_id,
                event_type="model_output_triggered_execution_blocked",
                reason_codes=("operator_selection_required",),
            )
            raise PermissionError("model output cannot trigger capability execution")
        capability_session_id = self._require_capability_session_id()
        try:
            result = self.capability_service.execute(
                session_id=capability_session_id,
                request_id=request.request_id,
                capability_id=request.capability_id,
                input_payload=request.transient_input,
            )
        except CapabilityRuntimeRejected as exc:
            raise PermissionError("capability request blocked") from exc
        output = result.output
        encoded = canonical_json({"output": output}).encode("utf-8")
        projection = action_projection(
            action_kind=OperatorConsoleActionKind.reference_capability_execution,
            request_id=request.request_id,
            transient_output=output,
            output_fingerprint=result.output_validation.output_fingerprint,
            output_byte_count=len(encoded),
        )
        self._record_receipt(session, request.request_id, projection.receipt_fingerprint)
        self.observability_recorder.increment("reference_capability_executions")
        self.observability_recorder.increment("operator_confirmations_validated")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request.request_id,
            event_type="capability_execution_completed",
            subject_fingerprints=(projection.output_fingerprint,),
            reason_codes=("explicit_operator_selection", "reference_capability"),
        )
        return _action_payload(projection, output)

    def simulate_connector(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        session = self._require_active_session()
        request = OperatorConsoleConnectorSimulationRequest.model_validate(payload)
        capability_session_id = self._require_capability_session_id()
        input_payload: dict[str, Any] = {
            "fixture_id": request.fixture_id,
            "record_key": request.record_key,
        }
        action_kind = OperatorConsoleActionKind.synthetic_connector_read
        if request.operation == "connector.reference.write.preview":
            input_payload["proposed_value"] = dict(request.transient_proposed_value or {})
            action_kind = OperatorConsoleActionKind.synthetic_connector_write_preview
        try:
            result = self.capability_service.execute(
                session_id=capability_session_id,
                request_id=request.request_id,
                capability_id=request.operation,
                input_payload=input_payload,
            )
        except CapabilityRuntimeRejected as exc:
            raise PermissionError("connector request blocked") from exc
        output = result.output
        encoded = canonical_json({"output": output}).encode("utf-8")
        projection = action_projection(
            action_kind=action_kind,
            request_id=request.request_id,
            transient_output=output,
            output_fingerprint=result.output_validation.output_fingerprint,
            output_byte_count=len(encoded),
        )
        self._record_receipt(session, request.request_id, projection.receipt_fingerprint)
        self.observability_recorder.increment("synthetic_connector_simulations")
        self.observability_recorder.increment("operator_confirmations_validated")
        if request.operation == "connector.reference.write.preview":
            self.observability_recorder.increment("write_previews_created")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request.request_id,
            event_type=(
                "write_preview_created"
                if request.operation == "connector.reference.write.preview"
                else "connector_simulation_completed"
            ),
            subject_fingerprints=(projection.output_fingerprint,),
            reason_codes=("synthetic_connector", "zero_writes_applied"),
        )
        return _action_payload(projection, output)

    def kill(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        session = self._require_active_session()
        request = OperatorConsoleKillSwitchRequest.model_validate(payload)
        self._kill_switch.activate(
            reason_code="operator_console_kill_switch",
            operator_identity_fingerprint=session.authorization.operator_identity_fingerprint,
            created_at=utc_now(),
        )
        self.observability_recorder.increment("kill_switch_activations")
        self.observability_recorder.increment("operator_confirmations_validated")
        self.observability_recorder.increment("requests_blocked_by_kill_switch")
        killed = session.model_copy(
            update={
                "status": OperatorConsoleSessionStatus.killed,
                "active_request_ids": tuple(),
                "killed_at": utc_now(),
            }
        )
        self._console_session = killed
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request.request_id,
            event_type="kill_switch_activated",
            subject_fingerprints=(self._kill_switch.state.state_fingerprint or ZERO_FINGERPRINT,),
            reason_codes=("explicit_operator_kill",),
        )
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request.request_id,
            event_type="request_blocked_by_kill_switch",
            reason_codes=("terminal_kill_switch",),
        )
        projection = receipt_projection(
            request_id=request.request_id,
            action_kind=OperatorConsoleActionKind.kill_switch_activation,
            prior_receipt_fingerprint=self._last_receipt_fingerprint,
            disposition=OperatorConsoleHttpDisposition.killed,
        )
        return _payload(
            {"ok": True, "terminal": "killed", "receipt": projection.model_dump(mode="json")}
        )

    def close(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        session = self._require_active_session()
        request = OperatorConsoleSessionCloseRequest.model_validate(payload)
        if session.active_request_ids:
            raise PermissionError("active requests must close before session close")
        self.observability_recorder.increment("session_close_requests")
        self.observability_recorder.increment("operator_confirmations_validated")
        closed = session.model_copy(
            update={
                "status": OperatorConsoleSessionStatus.closed,
                "active_request_ids": tuple(),
                "closed_at": utc_now(),
            }
        )
        self._console_session = None
        self._authorization = None
        self._component_binding = None
        if self._capability_session_id is not None:
            self.capability_service.close_session(self._capability_session_id)
            self._capability_session_id = None
        self.audit_ledger.append(
            session_id=closed.console_session_id,
            request_id=request.request_id,
            event_type="session_closed",
            reason_codes=("explicit_operator_close",),
        )
        projection = receipt_projection(
            request_id=request.request_id,
            action_kind=OperatorConsoleActionKind.session_close,
            prior_receipt_fingerprint=self._last_receipt_fingerprint,
            disposition=OperatorConsoleHttpDisposition.closed,
        )
        return _payload(
            {"ok": True, "terminal": "closed", "receipt": projection.model_dump(mode="json")}
        )

    def block_after_kill(self, request_id: str) -> None:
        session = self._require_active_or_terminal_session()
        self.observability_recorder.increment("requests_blocked_by_kill_switch")
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request_id,
            event_type="request_blocked_by_kill_switch",
            reason_codes=("kill_switch_active",),
        )

    def is_killed(self) -> bool:
        session = self._console_session
        return session is not None and session.status == OperatorConsoleSessionStatus.killed

    def active_session_count(self) -> int:
        session = self._console_session
        if session is None or session.status != OperatorConsoleSessionStatus.active:
            return 0
        return 1

    def active_request_count(self) -> int:
        session = self._console_session
        return 0 if session is None else len(session.active_request_ids)

    def cleanup(self) -> None:
        if self._console_session is not None:
            self._console_session = self._console_session.model_copy(
                update={
                    "status": OperatorConsoleSessionStatus.closed,
                    "active_request_ids": tuple(),
                }
            )
        self._authorization = None
        self._component_binding = None
        self._capability_session_id = None
        self.nonce_store.clear()

    def _ensure_session(self, *, host: str, origin: str) -> OperatorConsoleSession:
        if self._console_session is not None:
            if self._console_session.status == OperatorConsoleSessionStatus.active:
                return self._console_session
            if self._console_session.status == OperatorConsoleSessionStatus.killed:
                raise PermissionError("killed session cannot be reopened")
        if self._session_sequence >= ALL_RESOURCE_LIMITS["maximum_sessions_per_operator_run"]:
            raise PermissionError("console session limit exceeded")
        self._session_sequence += 1
        session_id = f"operator-console-session-{self._session_sequence:03d}"
        created_at = utc_now()
        operator_identity_fingerprint = fingerprint_text("operator-identity", "local-operator")
        actor_context_fingerprint = fingerprint_text("actor-context", "local-operator")
        self._kill_switch = _initial_kill_switch(session_id)
        component_binding = build_component_binding(
            secure_runtime_session_id=session_id,
            operator_identity_fingerprint=operator_identity_fingerprint,
            actor_context_fingerprint=actor_context_fingerprint,
            secure_runtime_kill_switch_fingerprint=(
                self._kill_switch.state.state_fingerprint or ZERO_FINGERPRINT
            ),
            receipt_chain_heads=self._receipt_chain_heads(),
            audit_chain_heads={"operator_console": self.audit_ledger.chain_head(session_id)},
            bound_at=created_at,
        )
        authorization = build_authorization_envelope(
            console_session_id=session_id,
            component_binding=component_binding,
            operator_identity_fingerprint=operator_identity_fingerprint,
            actor_context_fingerprint=actor_context_fingerprint,
            bound_port=self.bound_port,
            static_asset_manifest=self.static_asset_manifest,
        )
        self._capability_session_id = f"capability-runtime-console-{self._session_sequence:03d}"
        self.capability_service.start_session(self._capability_session_id)
        session = OperatorConsoleSession(
            console_session_id=session_id,
            status=OperatorConsoleSessionStatus.active,
            mode=OperatorConsoleMode.live_local_loopback,
            authorization=authorization,
            bootstrap_count=0,
            request_count=0,
            receipt_count=0,
            audit_count=0,
            created_at=created_at,
            expires_at=created_at
            + timedelta(seconds=ALL_RESOURCE_LIMITS["maximum_session_seconds"]),
            idle_expires_at=created_at
            + timedelta(seconds=ALL_RESOURCE_LIMITS["maximum_idle_seconds"]),
        )
        self._console_session = session
        self._authorization = authorization
        self._component_binding = component_binding
        self._last_session_id = session_id
        self.audit_ledger.append(
            session_id=session_id,
            event_type="authorization_validated",
            subject_fingerprints=(authorization.envelope_fingerprint or ZERO_FINGERPRINT,),
            reason_codes=("aion_236_sri_0004",),
        )
        self.audit_ledger.append(
            session_id=session_id,
            event_type="component_binding_validated",
            subject_fingerprints=(component_binding.binding_fingerprint or ZERO_FINGERPRINT,),
            reason_codes=("aion_231_aion_233_aion_235",),
        )
        if host != f"{LOOPBACK_BIND_HOST}:{self.bound_port}":
            raise PermissionError("host policy mismatch")
        if origin and origin != self.bound_origin:
            raise PermissionError("origin policy mismatch")
        return session

    def _require_active_session(self) -> OperatorConsoleSession:
        session = self._console_session
        if session is None or session.status != OperatorConsoleSessionStatus.active:
            raise PermissionError("active local console session is required")
        if session.expires_at <= utc_now() or session.idle_expires_at <= utc_now():
            self._console_session = session.model_copy(
                update={"status": OperatorConsoleSessionStatus.expired}
            )
            raise PermissionError("local console session expired")
        return session

    def _require_active_or_terminal_session(self) -> OperatorConsoleSession:
        session = self._console_session
        if session is not None:
            return session
        if self._last_session_id is not None:
            raise PermissionError("local console session is closed")
        return self._ensure_session(host=f"{LOOPBACK_BIND_HOST}:{self.bound_port}", origin="")

    def _require_capability_session_id(self) -> str:
        if self._capability_session_id is None:
            raise PermissionError("capability runtime session is unavailable")
        return self._capability_session_id

    def _record_receipt(
        self,
        session: OperatorConsoleSession,
        request_id: str,
        receipt_fingerprint: str,
    ) -> None:
        self._last_receipt_fingerprint = receipt_fingerprint
        self._console_session = session.model_copy(
            update={
                "receipt_count": session.receipt_count + 1,
                "request_count": session.request_count + 1,
                "audit_count": len(
                    self.audit_ledger.records_by_session(session.console_session_id)
                ),
            }
        )
        self.audit_ledger.append(
            session_id=session.console_session_id,
            request_id=request_id,
            event_type="receipt_projected",
            subject_fingerprints=(receipt_fingerprint,),
            reason_codes=("redacted_receipt",),
        )

    def _receipt_chain_heads(self) -> dict[str, str]:
        return {
            "operator_console": self._last_receipt_fingerprint,
            "secure_runtime": ZERO_FINGERPRINT,
            "model_gateway": ZERO_FINGERPRINT,
            "capability_runtime": ZERO_FINGERPRINT,
        }


def _initial_kill_switch(session_id: str) -> SecureRuntimeKillSwitch:
    now = datetime.now(UTC)
    state = SecureRuntimeKillSwitchState(
        session_id=session_id,
        status=SecureRuntimeKillSwitchStatus.clear,
        reason_code="clear",
        activation_fingerprint=ZERO_FINGERPRINT,
        operator_identity_fingerprint=fingerprint_text("operator-identity", "local-operator"),
        created_at=now,
    )
    return SecureRuntimeKillSwitch(state)


def _structured_schema(
    schema: Mapping[str, Any] | None,
    request_id: str,
) -> ModelStructuredOutputSchema | None:
    if schema is None:
        return None
    return ModelStructuredOutputSchema(
        schema_id=f"schema-{request_id}",
        schema_definition=dict(schema),
        schema_byte_count=len(canonical_json(schema).encode("utf-8")),
        schema_depth=json_depth(schema),
    )


def _action_payload(projection: Any, transient_output: Any) -> dict[str, Any]:
    return _payload(
        {
            "ok": True,
            "projection": projection.model_dump(mode="json"),
            "transient_output": transient_output,
            "transient_output_fingerprint": content_fingerprint(
                "operator-console-transient-output",
                canonical_json({"output": transient_output}).encode("utf-8"),
            ),
        }
    )


def _payload(value: Mapping[str, Any]) -> dict[str, Any]:
    return dict(value)
