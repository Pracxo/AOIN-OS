"""Deterministic truth maintenance."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.beliefs.confidence import score_belief_confidence
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.contracts.beliefs import (
    BeliefClaim,
    BeliefClaimStatus,
    BeliefContradiction,
    BeliefQuery,
    BeliefRevision,
    TruthMaintenanceRequest,
    TruthMaintenanceRun,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry


class TruthMaintenanceService:
    """Run deterministic truth maintenance over belief claims."""

    def __init__(
        self,
        repository: BeliefRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings

    def run(self, request: TruthMaintenanceRequest) -> TruthMaintenanceRun:
        """Run a dry-run or write truth maintenance pass."""
        authorize(
            self._policy_adapter,
            action_type="belief.truth_maintenance.run",
            resource_type="truth_maintenance",
            resource_id=request.truth_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium" if request.dry_run else "high",
            context={"dry_run": request.dry_run},
        )
        truth_run_id = request.truth_run_id or f"truth-run-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="truth_maintenance_started",
            node_type="truth_maintenance",
            node_id=truth_run_id,
            intensity=0.5,
            trace_id=request.trace_id,
            payload={"dry_run": request.dry_run},
        )
        claims = self._load_claims(request)
        revised: list[str] = []
        stale: list[str] = []
        contradiction_ids: list[str] = []
        proposed: list[dict[str, object]] = []
        for claim in claims:
            supports = self._repository.list_supports(claim.claim_id)
            contradictions = self._repository.list_contradictions(
                claim_id=claim.claim_id,
                status="open",
            )
            contradiction_ids.extend(item.contradiction_id for item in contradictions)
            age_days = _age_days(claim.observed_at)
            new_confidence = score_belief_confidence(
                claim.confidence,
                supports,
                contradictions,
                claim.evidence_refs,
                claim.memory_refs,
                claim.source_type,
                age_days,
            )
            new_status = _status_for(
                claim,
                new_confidence,
                contradictions,
                age_days,
                _setting_float(self._settings, "belief_min_supported_confidence", 0.65),
                _setting_int(self._settings, "belief_stale_after_days", 180),
            )
            if new_status == "stale":
                stale.append(claim.claim_id)
            if new_status == claim.status and abs(new_confidence - claim.confidence) < 0.001:
                continue
            proposed.append(
                {
                    "claim_id": claim.claim_id,
                    "from_status": claim.status,
                    "to_status": new_status,
                    "previous_confidence": claim.confidence,
                    "new_confidence": new_confidence,
                }
            )
            if not request.dry_run:
                revision = BeliefRevision(
                    revision_id=f"belief-revision-{uuid4().hex}",
                    claim_id=claim.claim_id,
                    trace_id=request.trace_id or claim.trace_id,
                    from_status=claim.status,
                    to_status=new_status,
                    previous_confidence=claim.confidence,
                    new_confidence=new_confidence,
                    reason="truth_maintenance_recompute",
                    evidence_refs=claim.evidence_refs,
                    metadata={"truth_run_id": truth_run_id},
                    created_by=request.created_by,
                    created_at=datetime.now(UTC),
                )
                self._repository.save_revision(revision)
                self._repository.save_claim(
                    claim.model_copy(
                        update={
                            "status": new_status,
                            "confidence": new_confidence,
                            "updated_at": datetime.now(UTC),
                        }
                    )
                )
                revised.append(claim.claim_id)
        completed = datetime.now(UTC)
        run = TruthMaintenanceRun(
            truth_run_id=truth_run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="dry_run" if request.dry_run else "completed",
            owner_scope=request.owner_scope,
            input_claim_ids=[claim.claim_id for claim in claims],
            revised_claim_ids=revised,
            contradiction_ids=sorted(set(contradiction_ids)),
            stale_claim_ids=sorted(set(stale)),
            result={"proposed_revisions": proposed, "dry_run": request.dry_run},
            created_by=request.created_by,
            created_at=completed,
            completed_at=completed,
        )
        stored = self._repository.save_truth_run(run)
        emit_telemetry(
            self._telemetry_service,
            event_type="truth_maintenance_completed",
            node_type="truth_maintenance",
            node_id=stored.truth_run_id,
            intensity=0.8 if stored.status in {"completed", "dry_run"} else 1.0,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "revised_count": len(revised)},
        )
        return stored

    def get(self, truth_run_id: str) -> TruthMaintenanceRun | None:
        """Return one truth maintenance run."""
        return self._repository.get_truth_run(truth_run_id)

    def _load_claims(self, request: TruthMaintenanceRequest) -> list[BeliefClaim]:
        if request.claim_ids:
            return [
                claim
                for claim in self._repository.list_claims_by_ids(request.claim_ids)
                if bool(set(claim.owner_scope) & set(request.owner_scope))
            ]
        return self._repository.query_claims(
            BeliefQuery(
                scope=request.owner_scope,
                statuses=request.statuses,
                include_stale=True,
                limit=500,
            )
        )


def _status_for(
    claim: BeliefClaim,
    confidence: float,
    contradictions: list[BeliefContradiction],
    age_days: float,
    threshold: float,
    stale_after_days: int,
) -> BeliefClaimStatus:
    if any(getattr(item, "severity", "") in {"high", "critical"} for item in contradictions):
        return "contradicted"
    if age_days > stale_after_days:
        return "stale"
    if confidence >= threshold and claim.evidence_refs:
        return "supported"
    return "uncertain"


def _age_days(observed_at: datetime) -> float:
    return max(0.0, (datetime.now(UTC) - observed_at).total_seconds() / 86400.0)


def _setting_float(settings: object | None, name: str, default: float) -> float:
    return float(getattr(settings, name, default))


def _setting_int(settings: object | None, name: str, default: int) -> int:
    return int(getattr(settings, name, default))
