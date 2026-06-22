"""Release candidate record service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.release_candidate import (
    ReleaseCandidate,
    ReleaseCandidateCreateRequest,
)
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.redaction import safe_rc_summary
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry


class ReleaseCandidateService:
    """Create and query release candidate records."""

    def __init__(
        self,
        repository: ReleaseCandidateRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service

    def create_candidate(self, request: ReleaseCandidateCreateRequest) -> ReleaseCandidate:
        """Create an RC shell without running verification."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.create",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="release_candidate",
            resource_id=request.release_candidate_id,
            risk_level="medium",
            context={"source_mutation": False, "external_calls": False},
        )
        now = datetime.now(UTC)
        candidate = ReleaseCandidate(
            release_candidate_id=request.release_candidate_id or f"rc-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            rc_key=request.rc_key,
            version=request.version,
            status="proposed",
            owner_scope=request.owner_scope,
            source_ref=request.source_ref,
            commit_ref=request.commit_ref,
            tag_ref=request.tag_ref,
            verification_matrix_id=request.verification_matrix_id,
            rc_run_id=None,
            rc_report_id=None,
            freeze_gate_id=None,
            release_package_id=None,
            readiness_score=0.0,
            release_ready=False,
            blocker_count=0,
            warning_count=0,
            evidence_pack_ref=None,
            metadata=safe_rc_summary(request.metadata),
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_candidate(candidate)
        record_audit_event(
            self._audit_sink,
            action_type="release_candidate.create",
            resource_type="release_candidate",
            resource_id=saved.release_candidate_id,
            event_type="release_candidate_created",
            outcome="completed",
            source_component="release_candidate_service",
            actor_id=request.created_by or request.actor_id,
            payload={"rc_key": saved.rc_key, "version": saved.version},
        )
        self._emit(
            "release_candidate_created",
            "release_candidate",
            saved.release_candidate_id,
            saved.owner_scope,
            0.5,
            {"rc_key": saved.rc_key, "version": saved.version},
        )
        return saved

    def get_candidate(self, release_candidate_id: str, scope: list[str]) -> ReleaseCandidate | None:
        """Return one candidate."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.read",
            scope,
            resource_type="release_candidate",
            resource_id=release_candidate_id,
        )
        return self._repository.get_candidate(release_candidate_id)

    def list_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        version: str | None = None,
        release_ready: bool | None = None,
        limit: int = 100,
    ) -> list[ReleaseCandidate]:
        """List local candidates."""

        authorize_rc_action(self._policy_adapter, "release_candidate.query", scope)
        return self._repository.list_candidates(
            status=status,
            version=version,
            release_ready=release_ready,
            limit=limit,
        )

    def archive_candidate(
        self, release_candidate_id: str, actor_id: str | None, reason: str
    ) -> ReleaseCandidate:
        """Archive one candidate without deleting evidence."""

        candidate = self._repository.get_candidate(release_candidate_id)
        scope = candidate.owner_scope if candidate is not None else ["workspace:main"]
        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.update",
            scope,
            actor_id=actor_id,
            resource_type="release_candidate",
            resource_id=release_candidate_id,
            risk_level="medium",
            context={"source_mutation": False, "reason": reason},
        )
        archived = self._repository.archive_candidate(release_candidate_id, reason)
        if archived is None:
            raise ValueError("release_candidate_not_found")
        return archived

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit_rc_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload=payload,
        )


__all__ = ["ReleaseCandidateService"]
