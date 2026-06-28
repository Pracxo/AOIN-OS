"""Mock-claims preview service for disabled production auth runtime."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.auth_runtime.actor_mapping import build_actor_context_preview
from aion_brain.auth_runtime.blockers import blocker, blockers_for_findings
from aion_brain.auth_runtime.redaction import payload_findings, redact_auth_runtime_payload
from aion_brain.contracts.auth_runtime import (
    MockClaimsPreviewRequest,
    MockClaimsPreviewResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry
from aion_brain.local_auth.roles import LocalRoleService


class MockClaimsPreviewService:
    """Preview synthetic claims without authenticating, issuing, or persisting state."""

    def __init__(
        self,
        *,
        role_service: LocalRoleService | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._role_service = role_service or LocalRoleService()
        self._telemetry_service = telemetry_service
        self._settings = settings

    def preview(self, request: MockClaimsPreviewRequest) -> MockClaimsPreviewResult:
        """Return a mock-only claims preview result."""

        preview_id = f"mock-claims-preview-{uuid4().hex}"
        findings = [
            *payload_findings(request.claims),
            *payload_findings(request.metadata),
        ]
        redacted_claims = redact_auth_runtime_payload(request.claims)
        blockers = blockers_for_findings(findings, source_id=preview_id)
        if request.issuer not in {"mock.local", "test.local"}:
            blockers.append(
                blocker(
                    "unsupported_issuer",
                    "issuer_not_mock_local",
                    source_type="mock_claims",
                    source_id=preview_id,
                    recommended_action="Use mock.local or test.local for previews.",
                )
            )
        if bool(getattr(self._settings, "auth_runtime_external_identity_enabled", False)):
            blockers.append(
                blocker(
                    "external_identity_disabled",
                    "external_identity_provider_disabled",
                    source_type="settings",
                    source_id=preview_id,
                    severity="critical",
                )
            )
        actor_preview, role_decisions = build_actor_context_preview(request, self._role_service)
        result = MockClaimsPreviewResult(
            mock_claims_preview_id=preview_id,
            trace_id=request.trace_id,
            status="blocked" if blockers else "preview",
            issuer=request.issuer,
            subject=request.subject,
            audience=request.audience,
            roles=request.roles,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            production_identity=False,
            credentials_present=False,
            token_present=False,
            cookie_present=False,
            session_persisted=False,
            actor_context_preview=actor_preview,
            role_decisions=role_decisions,
            blockers=blockers,
            warnings=[{"code": "mock_claims_not_authentication", "status": "open"}],
            metadata={
                "mock_only": True,
                "mode": request.mode,
                "claims_preview": redacted_claims if isinstance(redacted_claims, dict) else {},
                "redaction_findings": [
                    {"finding": str(item.get("finding") or "unsafe_payload")} for item in findings
                ],
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="mock_claims_preview_created",
            node_type="mock_claims_preview",
            node_id=result.mock_claims_preview_id,
            intensity=0.85 if blockers else 0.6,
            trace_id=result.trace_id,
            payload={
                "status": result.status,
                "mock_only": True,
                "production_identity": False,
            },
        )
        return result


__all__ = ["MockClaimsPreviewService"]
