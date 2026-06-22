"""Release candidate finding service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.release_candidate import RCFinding, RCFindingType
from aion_brain.contracts.verification_matrix import VerificationCheck
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.repository import ReleaseCandidateRepository
from aion_brain.release_candidate.telemetry import emit_rc_telemetry


class RCFindingService:
    """Create, list, and dismiss RC findings."""

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

    def create_for_check(
        self,
        check: VerificationCheck,
        *,
        trace_id: str | None,
        rc_run_id: str,
        release_candidate_id: str | None,
    ) -> RCFinding:
        """Create an open finding for a failed, blocked, warning, or missing check."""

        finding_type = _finding_type_for(check)
        finding = RCFinding(
            rc_finding_id=f"rc-finding-{uuid4().hex}",
            trace_id=trace_id,
            rc_run_id=rc_run_id,
            release_candidate_id=release_candidate_id,
            finding_type=finding_type,
            severity=check.severity,
            status="open",
            blocking=check.required and check.status in {"failed", "blocked", "unknown"},
            title=f"{check.title} requires release candidate review.",
            description=check.summary,
            check_key=check.check_key,
            source_type="verification_check",
            source_id=check.verification_check_id,
            recommended_action=_recommendation_for(check),
            evidence_refs=[f"aion://verification_check/{check.verification_check_id}"],
            metadata={"check_status": check.status, "required": check.required},
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_finding(finding)
        emit_rc_telemetry(
            self._telemetry_service,
            event_type="rc_finding_created",
            node_type="rc_finding",
            node_id=saved.rc_finding_id,
            scope=["workspace:main"],
            intensity=1.0 if saved.severity in {"high", "critical"} else 0.7,
            payload={"check_key": saved.check_key, "severity": saved.severity},
        )
        return saved

    def list_findings(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        blocking: bool | None = None,
        limit: int = 100,
    ) -> list[RCFinding]:
        """List RC findings."""

        authorize_rc_action(self._policy_adapter, "release_candidate.finding.read", scope)
        return self._repository.list_findings(
            status=status,
            severity=severity,
            blocking=blocking,
            limit=limit,
        )

    def dismiss_finding(
        self,
        rc_finding_id: str,
        scope: list[str],
        *,
        actor_id: str | None,
        reason: str,
    ) -> RCFinding | None:
        """Dismiss one RC finding without altering the original run."""

        authorize_rc_action(
            self._policy_adapter,
            "release_candidate.finding.update",
            scope,
            actor_id=actor_id,
            resource_type="rc_finding",
            resource_id=rc_finding_id,
            risk_level="medium",
            context={"source_mutation": False, "reason": reason},
        )
        finding = self._repository.dismiss_finding(rc_finding_id, reason)
        if finding is not None:
            emit_rc_telemetry(
                self._telemetry_service,
                event_type="rc_finding_dismissed",
                node_type="rc_finding",
                node_id=finding.rc_finding_id,
                scope=scope,
                intensity=0.3,
                payload={"reason": reason},
            )
        return finding


def _finding_type_for(check: VerificationCheck) -> RCFindingType:
    if check.status == "unknown":
        return "missing_required_check"
    if check.check_key == "golden_path":
        return "golden_path_failed"
    if check.check_key == "freeze_gate":
        return "freeze_gate_failed"
    if check.check_key == "release_package_dry_run":
        return "release_package_failed"
    if check.check_key == "contract_registry":
        return "contract_drift"
    if check.check_key == "resource_registry":
        return "registry_integrity"
    if check.check_key == "lifecycle_safety":
        return "lifecycle_risk"
    if check.check_key in {"extension_safety", "module_binding_safety", "conformance_safety"}:
        return "activation_enabled"
    if check.check_key == "typecheck":
        return "typecheck_failed"
    if check.check_key in {"tests.brain", "tests.sdk"}:
        return "test_failed"
    if check.status == "warning" and check.severity in {"high", "critical"}:
        return "critical_warning"
    return "failed_required_check"


def _recommendation_for(check: VerificationCheck) -> str:
    mapping = {
        "tests.brain": "fix_failed_required_check",
        "tests.sdk": "fix_failed_required_check",
        "golden_path": "rerun_golden_path",
        "bootstrap_doctor": "rerun_bootstrap_doctor",
        "freeze_gate": "rerun_freeze_gate",
        "contract_registry": "inspect_contract_drift",
        "resource_registry": "inspect_registry_integrity",
        "operator_overview": "inspect_operator_overview",
    }
    return mapping.get(check.check_key, "fix_failed_required_check")


__all__ = ["RCFindingService"]
