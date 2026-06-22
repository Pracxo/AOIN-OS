"""Release candidate evidence pack service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.release_candidate import RCEvidencePack, RCGateRun
from aion_brain.release_candidate.hash import hash_rc_report
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.redaction import safe_rc_summary
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry


class RCEvidencePackService:
    """Build and query redacted RC evidence packs."""

    def __init__(
        self,
        repository: ReleaseCandidateRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def build(self, run: RCGateRun, created_by: str | None = None) -> RCEvidencePack:
        """Build and persist a redacted evidence pack for a gate run."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.evidence_pack.create",
            run.owner_scope,
            actor_id=created_by,
            trace_id=run.trace_id,
            resource_type="rc_evidence_pack",
            risk_level="medium",
            context={"source_mutation": False, "external_calls": False},
        )
        redacted_report = safe_rc_summary(
            {
                "run": run.model_dump(mode="json"),
                "checks": [check.model_dump(mode="json") for check in run.verification_checks],
                "findings": [finding.model_dump(mode="json") for finding in run.findings],
            }
        )
        pack = RCEvidencePack(
            evidence_pack_id=f"rc-evidence-pack-{uuid4().hex}",
            trace_id=run.trace_id,
            rc_run_id=run.rc_run_id,
            release_candidate_id=run.release_candidate_id,
            status="created" if run.status not in {"failed", "blocked"} else "warning",
            owner_scope=run.owner_scope,
            pack_type="rc",
            title="AION v0.1 Release Candidate Evidence Pack",
            summary="Redacted local evidence for one release candidate gate run.",
            evidence_refs=[
                f"aion://verification_check/{check.verification_check_id}"
                for check in run.verification_checks
            ],
            check_summaries=[
                {
                    "check_key": check.check_key,
                    "status": check.status,
                    "required": check.required,
                    "passed": check.passed,
                }
                for check in run.verification_checks
            ],
            artifact_refs=[],
            report_hash=hash_rc_report(redacted_report),
            redacted_report=redacted_report,
            metadata={"external_calls": False, "source_content_included": False},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_evidence_pack(pack)
        emit_rc_telemetry(
            self._telemetry_service,
            event_type="rc_evidence_pack_created",
            node_type="rc_evidence_pack",
            node_id=saved.evidence_pack_id,
            scope=saved.owner_scope,
            intensity=0.7,
            payload={"rc_run_id": saved.rc_run_id, "report_hash": saved.report_hash},
        )
        return saved

    def get_pack(self, evidence_pack_id: str, scope: list[str]) -> RCEvidencePack | None:
        """Return one evidence pack."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.evidence_pack.read",
            scope,
            resource_type="rc_evidence_pack",
            resource_id=evidence_pack_id,
        )
        return self._repository.get_evidence_pack(evidence_pack_id)

    def list_packs(
        self, scope: list[str], *, status: str | None = None, limit: int = 50
    ) -> list[RCEvidencePack]:
        """List evidence packs."""

        authorize_rc_action(self._policy_adapter, "release_candidate.evidence_pack.read", scope)
        return self._repository.list_evidence_packs(status=status, limit=limit)


__all__ = ["RCEvidencePackService"]
