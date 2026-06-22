"""Verification matrix service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.verification_matrix import (
    VerificationMatrix,
    VerificationMatrixCreateRequest,
)
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.redaction import safe_rc_summary
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry

DEFAULT_REQUIRED_CHECKS = [
    "tests.brain",
    "tests.sdk",
    "lint",
    "typecheck",
    "no_domain_drift",
    "boundary_check",
    "policy_coverage",
    "openapi_hygiene",
    "repo_health",
    "docker_compose_config",
    "bootstrap_doctor",
    "golden_path",
    "release_smoke",
    "freeze_gate",
    "release_package_dry_run",
    "contract_registry",
    "resource_registry",
    "lifecycle_safety",
    "extension_safety",
    "module_binding_safety",
    "conformance_safety",
    "security_baseline",
    "runtime_config_safe",
    "operator_overview",
]
DEFAULT_OPTIONAL_CHECKS = ["docker_smoke_live", "rc_evidence_pack"]


class VerificationMatrixService:
    """Create and seed RC verification matrices."""

    def __init__(
        self,
        repository: ReleaseCandidateRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()

    def create_matrix(self, request: VerificationMatrixCreateRequest) -> VerificationMatrix:
        """Create a verification matrix."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.matrix.create",
            request.owner_scope,
            actor_id=request.created_by,
            trace_id=request.trace_id,
            resource_type="verification_matrix",
            resource_id=request.verification_matrix_id,
            risk_level="medium",
            context={"source_mutation": False, "external_calls": False},
        )
        now = datetime.now(UTC)
        matrix = VerificationMatrix(
            verification_matrix_id=request.verification_matrix_id or f"rc-matrix-{uuid4().hex}",
            trace_id=request.trace_id,
            matrix_key=request.matrix_key,
            version=request.version,
            status="active",
            owner_scope=request.owner_scope,
            required_checks=request.required_checks,
            optional_checks=request.optional_checks,
            required_threshold=request.required_threshold,
            release_ready_threshold=request.release_ready_threshold,
            fail_on_critical=request.fail_on_critical,
            fail_on_missing_required=request.fail_on_missing_required,
            metadata=safe_rc_summary(request.metadata),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_matrix(matrix)
        record_audit_event(
            self._audit_sink,
            action_type="release_candidate.matrix.create",
            resource_type="verification_matrix",
            resource_id=saved.verification_matrix_id,
            event_type="verification_matrix_created",
            outcome="completed",
            source_component="verification_matrix_service",
            actor_id=request.created_by,
            payload={"matrix_key": saved.matrix_key, "version": saved.version},
        )
        emit_rc_telemetry(
            self._telemetry_service,
            event_type="verification_matrix_created",
            node_type="verification_matrix",
            node_id=saved.verification_matrix_id,
            scope=saved.owner_scope,
            intensity=0.5,
            payload={"matrix_key": saved.matrix_key, "version": saved.version},
        )
        return saved

    def get_matrix(
        self, verification_matrix_id: str, scope: list[str]
    ) -> VerificationMatrix | None:
        """Return one matrix."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.matrix.read",
            scope,
            resource_type="verification_matrix",
            resource_id=verification_matrix_id,
        )
        return self._repository.get_matrix(verification_matrix_id)

    def list_matrices(
        self, scope: list[str], *, status: str | None = None, limit: int = 100
    ) -> list[VerificationMatrix]:
        """List matrices."""

        authorize_rc_action(self._policy_adapter, "release_candidate.matrix.read", scope)
        return self._repository.list_matrices(status=status, limit=limit)

    def seed_default_matrices(
        self,
        scope: list[str],
        *,
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> dict[str, object]:
        """Seed the default v0.1 RC matrix, or preview it."""

        request = VerificationMatrixCreateRequest(
            matrix_key="rc.v0_1.default",
            version=self._settings.version,
            owner_scope=scope,
            required_checks=DEFAULT_REQUIRED_CHECKS,
            optional_checks=DEFAULT_OPTIONAL_CHECKS,
            required_threshold=1.0,
            release_ready_threshold=self._settings.rc_release_ready_threshold,
            fail_on_critical=self._settings.rc_fail_on_critical,
            fail_on_missing_required=self._settings.rc_fail_on_missing_required,
            metadata={"source": "default_rc_matrix"},
            created_by=created_by,
        )
        if dry_run:
            authorize_rc_action(
                self._policy_adapter,
                "release_candidate.matrix.create",
                scope,
                actor_id=created_by,
                resource_type="verification_matrix",
                risk_level="medium",
                context={"mode": "dry_run", "source_mutation": False},
            )
            return {"dry_run": True, "created": [], "matrices": [request.model_dump(mode="json")]}
        matrix = self.create_matrix(request)
        return {"dry_run": False, "created": [matrix.verification_matrix_id], "matrices": [matrix]}

    def default_matrix(
        self, scope: list[str], *, created_by: str | None = None
    ) -> VerificationMatrix:
        """Return a persisted default matrix, creating it locally when needed."""

        existing = self._repository.get_matrix_by_key("rc.v0_1.default", self._settings.version)
        if existing is not None:
            return existing
        return self.create_matrix(
            VerificationMatrixCreateRequest(
                matrix_key="rc.v0_1.default",
                version=self._settings.version,
                owner_scope=scope,
                required_checks=DEFAULT_REQUIRED_CHECKS,
                optional_checks=DEFAULT_OPTIONAL_CHECKS,
                required_threshold=1.0,
                release_ready_threshold=self._settings.rc_release_ready_threshold,
                fail_on_critical=self._settings.rc_fail_on_critical,
                fail_on_missing_required=self._settings.rc_fail_on_missing_required,
                metadata={"source": "default_rc_matrix"},
                created_by=created_by,
            )
        )


__all__ = ["DEFAULT_OPTIONAL_CHECKS", "DEFAULT_REQUIRED_CHECKS", "VerificationMatrixService"]
