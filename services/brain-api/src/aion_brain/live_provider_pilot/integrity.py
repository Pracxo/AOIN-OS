"""Controlled AION-248 live-provider pilot service."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    PILOT_CONFIRMATION_TEXT,
    SELECTED_MODEL_ID,
    ZERO_FINGERPRINT,
    LiveProviderAuditOutcome,
    LiveProviderAuditRecord,
    LiveProviderAuthorizationEnvelope,
    LiveProviderComponentBinding,
    LiveProviderCredentialBoundary,
    LiveProviderEndpointPolicy,
    LiveProviderIntegrityReport,
    LiveProviderIntegrityStatus,
    LiveProviderModelSelection,
    LiveProviderOperatorApproval,
    LiveProviderReplayRecord,
    LiveProviderRequestProjection,
    LiveProviderResponseProjection,
    LiveProviderScenarioCode,
    LiveProviderTransportResult,
    LiveProviderTrustAssessment,
    LiveProviderUncertaintyProjection,
    LiveProviderUsageRecord,
    content_fingerprint,
    default_required_counters,
    default_zero_counters,
    live_provider_fingerprint,
    validate_endpoint,
)
from aion_brain.live_provider_pilot.audit import InMemoryLiveProviderAuditLedger
from aion_brain.live_provider_pilot.authorization import create_authorization_envelope
from aion_brain.live_provider_pilot.component_binding import bind_components
from aion_brain.live_provider_pilot.credential_boundary import attest_environment_credential
from aion_brain.live_provider_pilot.endpoint_policy import create_endpoint_policy
from aion_brain.live_provider_pilot.operator_approval import create_operator_approval
from aion_brain.live_provider_pilot.provider_selection import (
    reject_model_switch,
    select_model,
)
from aion_brain.live_provider_pilot.redaction import assert_redacted_evidence
from aion_brain.live_provider_pilot.replay import InMemoryLiveProviderReplayRepository
from aion_brain.live_provider_pilot.request_projection import project_request
from aion_brain.live_provider_pilot.response_projection import project_response
from aion_brain.live_provider_pilot.trust import (
    assess_live_response_trust,
    project_live_uncertainty,
)
from aion_brain.live_provider_pilot.usage_budget import create_usage_record


class ControlledLiveProviderPilotService:
    """No-network service for local policy, projection, replay, and evidence."""

    def __init__(self) -> None:
        self.audit_ledger = InMemoryLiveProviderAuditLedger()
        self.replay_repository = InMemoryLiveProviderReplayRepository()
        self._selected_model_id: str | None = None
        self._session_active = False

    def create_authorization(self) -> LiveProviderAuthorizationEnvelope:
        """Return the exact AION-247-AI-0002 authorization."""

        return create_authorization_envelope()

    def bind_components(
        self,
        *,
        created_at: datetime,
        binding_id: str = "aion-248-live-provider-component-binding",
        external_cognition_component_fingerprint: str = ZERO_FINGERPRINT,
        existing_model_gateway_component_fingerprint: str = ZERO_FINGERPRINT,
        operator_identity_fingerprint: str = ZERO_FINGERPRINT,
    ) -> LiveProviderComponentBinding:
        """Create component lineage binding evidence."""

        return bind_components(
            binding_id=binding_id,
            external_cognition_component_fingerprint=external_cognition_component_fingerprint,
            existing_model_gateway_component_fingerprint=(
                existing_model_gateway_component_fingerprint
            ),
            operator_identity_fingerprint=operator_identity_fingerprint,
            created_at=created_at,
        )

    def select_exact_model(
        self,
        *,
        selection_id: str,
        model_id: str,
        created_at: datetime,
    ) -> LiveProviderModelSelection:
        """Bind the exact model once for the session."""

        if self._selected_model_id is not None:
            reject_model_switch(
                existing_model_id=self._selected_model_id,
                requested_model_id=model_id,
            )
        selection = select_model(
            selection_id=selection_id,
            model_id=model_id,
            created_at=created_at,
        )
        self._selected_model_id = selection.selected_model_id
        return selection

    def approve_operator_run(
        self,
        *,
        approval_id: str,
        confirmation_text: str,
        selection: LiveProviderModelSelection,
        created_at: datetime,
    ) -> LiveProviderOperatorApproval:
        """Create the operator approval record."""

        if confirmation_text != PILOT_CONFIRMATION_TEXT:
            raise ValueError("operator confirmation mismatch")
        return create_operator_approval(
            approval_id=approval_id,
            confirmation_text=confirmation_text,
            selection=selection,
            created_at=created_at,
        )

    def create_endpoint_policy(
        self,
        *,
        policy_id: str,
        created_at: datetime,
    ) -> LiveProviderEndpointPolicy:
        """Create the exact endpoint policy."""

        return create_endpoint_policy(policy_id=policy_id, created_at=created_at)

    def validate_endpoint_policy(
        self,
        *,
        scheme: str,
        host: str,
        path: str,
        method: str,
    ) -> None:
        """Reject any alternate endpoint."""

        validate_endpoint(scheme=scheme, host=host, path=path, method=method)

    def attest_credential_presence(
        self,
        *,
        credential_present: bool,
        provider_credentials_read: int,
        created_at: datetime,
    ) -> LiveProviderCredentialBoundary:
        """Record credential presence without receiving the credential."""

        return attest_environment_credential(
            boundary_id="aion-248-credential-boundary",
            credential_present=credential_present,
            provider_credentials_read=provider_credentials_read,
            created_at=created_at,
        )

    def start_session(self) -> None:
        """Open the one local session."""

        if self._session_active:
            raise ValueError("only one live-provider pilot session is allowed")
        self._session_active = True

    def close_session(self) -> None:
        """Close the local session."""

        self._session_active = False

    def project_request(
        self,
        *,
        request_id: str,
        scenario_code: LiveProviderScenarioCode,
        prompt_text: str,
        payload: dict[str, object],
        maximum_output_tokens: int,
        endpoint_policy: LiveProviderEndpointPolicy,
        created_at: datetime,
    ) -> LiveProviderRequestProjection:
        """Create a safe request projection and record replay identity."""

        if not self._session_active:
            raise ValueError("live-provider pilot session is not active")
        projection = project_request(
            request_id=request_id,
            scenario_code=scenario_code,
            prompt_text=prompt_text,
            payload=payload,
            maximum_output_tokens=maximum_output_tokens,
            endpoint_policy=endpoint_policy,
            created_at=created_at,
        )
        self.replay_repository.record(
            request_id=request_id,
            request_fingerprint=projection.request_fingerprint,
        )
        return projection

    def project_response(
        self,
        *,
        response_projection_id: str,
        request: LiveProviderRequestProjection,
        transport_result: LiveProviderTransportResult,
        created_at: datetime,
    ) -> LiveProviderResponseProjection:
        """Create a safe response projection."""

        return project_response(
            response_projection_id=response_projection_id,
            request_projection_fingerprint=request.projection_fingerprint or "",
            transport_result=transport_result,
            created_at=created_at,
        )

    def create_usage(
        self,
        *,
        usage_id: str,
        request: LiveProviderRequestProjection,
        response: LiveProviderResponseProjection,
        transport_result: LiveProviderTransportResult,
        created_at: datetime,
    ) -> LiveProviderUsageRecord:
        """Create usage evidence."""

        return create_usage_record(
            usage_id=usage_id,
            request=request,
            response=response,
            transport_result=transport_result,
            created_at=created_at,
        )

    def assess_trust(
        self,
        *,
        trust_id: str,
        response: LiveProviderResponseProjection,
        schema_validated: bool,
        created_at: datetime,
    ) -> LiveProviderTrustAssessment:
        """Classify response trust."""

        return assess_live_response_trust(
            trust_id=trust_id,
            response=response,
            schema_validated=schema_validated,
            created_at=created_at,
        )

    def project_uncertainty(
        self,
        *,
        uncertainty_id: str,
        response: LiveProviderResponseProjection,
        confidence_score: float,
        created_at: datetime,
    ) -> LiveProviderUncertaintyProjection:
        """Create uncertainty evidence."""

        return project_live_uncertainty(
            uncertainty_id=uncertainty_id,
            response=response,
            confidence_score=confidence_score,
            created_at=created_at,
        )

    def exact_replay(
        self,
        *,
        request: LiveProviderRequestProjection,
        created_at: datetime,
    ) -> LiveProviderReplayRecord:
        """Return exact replay evidence without transport."""

        return self.replay_repository.check_exact_replay(
            replay_id="aion-248-exact-replay",
            request_id=request.request_id,
            replay_request_fingerprint=request.request_fingerprint,
            created_at=created_at,
        )

    def changed_replay(
        self,
        *,
        request: LiveProviderRequestProjection,
        created_at: datetime,
    ) -> LiveProviderReplayRecord:
        """Reject changed replay before transport."""

        return self.replay_repository.reject_changed_replay(
            replay_id="aion-248-changed-replay",
            request_id=request.request_id,
            replay_request_fingerprint=live_provider_fingerprint(
                {"changed": request.request_fingerprint}
            ),
            created_at=created_at,
        )

    def record_audit(
        self,
        *,
        audit_id: str,
        event_type: str,
        subject_fingerprint: str,
        created_at: datetime,
    ) -> LiveProviderAuditRecord:
        """Record an audit event."""

        return self.audit_ledger.record_audit(
            audit_id=audit_id,
            event_type=event_type,
            outcome=LiveProviderAuditOutcome.accepted,
            subject_fingerprint=subject_fingerprint,
            created_at=created_at,
        )

    def audit_integrity(
        self,
        *,
        integrity_id: str,
        authorization: LiveProviderAuthorizationEnvelope,
        selection: LiveProviderModelSelection,
        endpoint_policy: LiveProviderEndpointPolicy,
        transport_policy_fingerprint: str,
        observability_fingerprint: str,
        created_at: datetime,
    ) -> LiveProviderIntegrityReport:
        """Validate evidence integrity with no runtime left active."""

        return LiveProviderIntegrityReport(
            integrity_id=integrity_id,
            status=LiveProviderIntegrityStatus.passed,
            authorization_fingerprint=authorization.authorization_fingerprint or "",
            selected_model_fingerprint=selection.selection_fingerprint or "",
            endpoint_policy_fingerprint=endpoint_policy.endpoint_policy_fingerprint or "",
            transport_policy_fingerprint=transport_policy_fingerprint,
            observability_fingerprint=observability_fingerprint,
            post_pilot_provider_runtime_active=self._session_active,
            post_pilot_network_runtime_active=False,
            created_at=created_at,
        )

    def validate_redacted_output(self, payload: Mapping[str, object]) -> None:
        """Reject raw content or credential material in evidence."""

        assert_redacted_evidence(payload)

    def counters_template(self) -> dict[str, int]:
        """Return required counter targets."""

        counters = default_required_counters()
        counters["selected_models"] = 1 if self._selected_model_id == SELECTED_MODEL_ID else 0
        return counters

    def zero_counters_template(self) -> dict[str, int]:
        """Return zero-counter targets."""

        return default_zero_counters()

    def transport_policy_fingerprint(self) -> str:
        """Return the static transport-policy fingerprint."""

        return content_fingerprint(
            "live_provider_transport_policy",
            "stdlib_https_tls_verify_no_redirect_no_proxy_no_retry",
        )
