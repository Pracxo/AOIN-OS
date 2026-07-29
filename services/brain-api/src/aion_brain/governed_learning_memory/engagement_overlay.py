"""In-memory engagement overlay records, snapshots, and repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from aion_brain.contracts.governed_engagement_learning import (
    EngagementAdaptationIdentity,
    EngagementAdaptationVersionPlan,
    EngagementApplicationApprovalBundle,
    EngagementApplicationQuery,
    EngagementApplicationQueryResult,
    EngagementApplicationRiskAssessment,
    EngagementBaselineSnapshot,
    EngagementCandidateBinding,
    EngagementOverlayRecord,
    EngagementOverlaySnapshot,
    EngagementOverlayStatus,
    EngagementRollbackPlan,
    EngagementTargetPolicy,
    build_record,
    utc_now,
)


def build_engagement_overlay_record(
    *,
    overlay_record_id: str,
    shadow_session_id: str,
    binding: EngagementCandidateBinding,
    identity: EngagementAdaptationIdentity,
    version_plan: EngagementAdaptationVersionPlan,
    target_policy: EngagementTargetPolicy,
    risk_assessment: EngagementApplicationRiskAssessment,
    approval_bundle: EngagementApplicationApprovalBundle,
    baseline_snapshot: EngagementBaselineSnapshot,
    fixture_fingerprint: str,
    rollback_plan: EngagementRollbackPlan,
    status: EngagementOverlayStatus = EngagementOverlayStatus.PLANNED,
) -> EngagementOverlayRecord:
    """Create an immutable overlay record with zero production effects."""

    payload = {
        "schema_version": "aion-glm-engagement-overlay-record/v1",
        "overlay_record_id": overlay_record_id,
        "shadow_session_id": shadow_session_id,
        "adaptation_identity_id": identity.adaptation_identity_id,
        "adaptation_version": version_plan.planned_version_number,
        "candidate_id": binding.learning_candidate_id,
        "candidate_fingerprint": binding.candidate_fingerprint,
        "candidate_kind": binding.candidate_kind,
        "signal_fingerprints": binding.signal_fingerprints,
        "target_policy": target_policy,
        "risk_assessment_fingerprint": risk_assessment.assessment_fingerprint,
        "approval_bundle_fingerprint": approval_bundle.bundle_fingerprint,
        "baseline_snapshot_fingerprint": baseline_snapshot.snapshot_fingerprint,
        "fixture_fingerprint": fixture_fingerprint,
        "rollback_plan_fingerprint": rollback_plan.rollback_plan_fingerprint,
        "effective_from": version_plan.effective_from,
        "expires_at": version_plan.expires_at,
        "status": status,
        "reason_codes": ("engagement_overlay_planned",),
        "persistent_write_applied": False,
        "aion_224_store_write_applied": False,
        "production_policy_effect": False,
        "factual_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "source_independence_effect": False,
        "citation_coverage_effect": False,
        "provenance_effect": False,
        "contradiction_resolution_effect": False,
        "freshness_effect": False,
        "cognitive_memory_effect": False,
        "belief_effect": False,
        "model_weight_effect": False,
        "runtime_effect": False,
    }
    return build_record(EngagementOverlayRecord, payload, "overlay_fingerprint")


def build_engagement_overlay_snapshot(
    *,
    overlay_snapshot_id: str,
    shadow_session_id: str,
    records: tuple[EngagementOverlayRecord, ...],
    created_at: datetime | None = None,
    expires_at: datetime,
) -> EngagementOverlaySnapshot:
    """Create an immutable deterministic overlay snapshot."""

    ordered = tuple(sorted(records, key=lambda item: item.overlay_record_id))
    payload = {
        "schema_version": "aion-glm-engagement-overlay-snapshot/v1",
        "overlay_snapshot_id": overlay_snapshot_id,
        "shadow_session_id": shadow_session_id,
        "records": ordered,
        "record_count": len(ordered),
        "adaptation_identity_ids": tuple(
            sorted(record.adaptation_identity_id for record in ordered)
        ),
        "adaptation_version_vector": tuple(
            f"{record.adaptation_identity_id}:{record.adaptation_version}"
            for record in ordered
        ),
        "created_at": created_at or utc_now(),
        "expires_at": expires_at,
        "immutable": True,
        "in_memory_only": True,
        "persistent_write_applied": False,
        "production_policy_effect": False,
        "runtime_effect": False,
    }
    return build_record(EngagementOverlaySnapshot, payload, "snapshot_fingerprint")


@dataclass(frozen=True)
class InMemoryEngagementOverlayRepository:
    """Copy-on-write in-memory overlay repository."""

    _overlays: dict[str, EngagementOverlayRecord] = field(default_factory=dict)
    _snapshots: dict[str, EngagementOverlaySnapshot] = field(default_factory=dict)

    def with_overlay(
        self, overlay: EngagementOverlayRecord
    ) -> InMemoryEngagementOverlayRepository:
        existing = self._overlays.get(overlay.overlay_record_id)
        if existing is not None and existing.overlay_fingerprint != overlay.overlay_fingerprint:
            raise ValueError("changed overlay replay rejected")
        next_overlays = dict(self._overlays)
        next_overlays[overlay.overlay_record_id] = overlay
        return InMemoryEngagementOverlayRepository(next_overlays, dict(self._snapshots))

    def with_overlays(
        self, overlays: tuple[EngagementOverlayRecord, ...]
    ) -> InMemoryEngagementOverlayRepository:
        repo = self
        for overlay in overlays:
            repo = repo.with_overlay(overlay)
        return repo

    def with_snapshot(
        self, snapshot: EngagementOverlaySnapshot
    ) -> InMemoryEngagementOverlayRepository:
        existing = self._snapshots.get(snapshot.overlay_snapshot_id)
        if existing is not None and existing.snapshot_fingerprint != snapshot.snapshot_fingerprint:
            raise ValueError("changed snapshot replay rejected")
        next_snapshots = dict(self._snapshots)
        next_snapshots[snapshot.overlay_snapshot_id] = snapshot
        return InMemoryEngagementOverlayRepository(dict(self._overlays), next_snapshots)

    def overlay_by_id(self, overlay_record_id: str) -> EngagementOverlayRecord | None:
        return self._overlays.get(overlay_record_id)

    def overlays_by_candidate(self, candidate_id: str) -> tuple[EngagementOverlayRecord, ...]:
        return tuple(
            sorted(
                (
                    overlay
                    for overlay in self._overlays.values()
                    if overlay.candidate_id == candidate_id
                ),
                key=lambda item: item.overlay_record_id,
            )
        )

    def overlays_by_adaptation_identity(
        self, adaptation_identity_id: str
    ) -> tuple[EngagementOverlayRecord, ...]:
        return tuple(
            sorted(
                (
                    overlay
                    for overlay in self._overlays.values()
                    if overlay.adaptation_identity_id == adaptation_identity_id
                ),
                key=lambda item: item.overlay_record_id,
            )
        )

    def snapshots_by_session(self, shadow_session_id: str) -> tuple[EngagementOverlaySnapshot, ...]:
        return tuple(
            sorted(
                (
                    snapshot
                    for snapshot in self._snapshots.values()
                    if snapshot.shadow_session_id == shadow_session_id
                ),
                key=lambda item: item.overlay_snapshot_id,
            )
        )

    def _matches_query(
        self,
        overlay: EngagementOverlayRecord,
        query: EngagementApplicationQuery,
    ) -> bool:
        return (
            (
                query.shadow_session_id is None
                or overlay.shadow_session_id == query.shadow_session_id
            )
            and (query.candidate_id is None or overlay.candidate_id == query.candidate_id)
            and (
                query.candidate_fingerprint is None
                or overlay.candidate_fingerprint == query.candidate_fingerprint
            )
            and (query.candidate_kind is None or overlay.candidate_kind == query.candidate_kind)
            and (
                query.adaptation_identity_id is None
                or overlay.adaptation_identity_id == query.adaptation_identity_id
            )
            and (
                query.adaptation_version is None
                or overlay.adaptation_version == query.adaptation_version
            )
            and (
                query.target_component_code is None
                or overlay.target_policy.target_component_code == query.target_component_code
            )
            and (
                query.target_policy_code is None
                or overlay.target_policy.target_policy_code == query.target_policy_code
            )
            and (query.overlay_status is None or overlay.status == query.overlay_status)
        )

    def query(self, query: EngagementApplicationQuery) -> EngagementApplicationQueryResult:
        records = tuple(
            overlay
            for overlay in sorted(self._overlays.values(), key=lambda item: item.overlay_record_id)
            if self._matches_query(overlay, query)
        )[: query.limit]
        payload = {
            "schema_version": "aion-glm-engagement-application-query-result/v1",
            "query_fingerprint": query.query_fingerprint,
            "overlay_records": records,
            "result_count": len(records),
            "read_only": True,
            "redacted": True,
            "runtime_effect": False,
        }
        return build_record(EngagementApplicationQueryResult, payload, "result_fingerprint")

    def audit(self) -> dict[str, int]:
        return {
            "overlay_count": len(self._overlays),
            "snapshot_count": len(self._snapshots),
            "persistent_overlay_writes": 0,
            "production_policy_mutations": 0,
        }

    def active_overlay_count(self) -> int:
        """Return active shadow overlays without exposing repository internals."""

        return sum(
            1
            for overlay in self._overlays.values()
            if overlay.status is EngagementOverlayStatus.ACTIVE_SHADOW
        )

    def _overlay_payload(self, overlay: EngagementOverlayRecord) -> dict[str, object]:
        payload = overlay.model_dump(mode="python", exclude={"overlay_fingerprint"})
        payload["target_policy"] = overlay.target_policy
        return payload

    def expire_session(self, shadow_session_id: str) -> InMemoryEngagementOverlayRepository:
        overlays = {
            key: (
                build_record(
                    EngagementOverlayRecord,
                    {
                        **self._overlay_payload(overlay),
                        "status": EngagementOverlayStatus.EXPIRED,
                        "reason_codes": tuple(
                            sorted((*overlay.reason_codes, "engagement_overlay_expired"))
                        ),
                    },
                    "overlay_fingerprint",
                )
                if overlay.shadow_session_id == shadow_session_id
                else overlay
            )
            for key, overlay in self._overlays.items()
        }
        return InMemoryEngagementOverlayRepository(overlays, dict(self._snapshots))

    def rollback_session(self, shadow_session_id: str) -> InMemoryEngagementOverlayRepository:
        overlays = {
            key: (
                build_record(
                    EngagementOverlayRecord,
                    {
                        **self._overlay_payload(overlay),
                        "status": EngagementOverlayStatus.ROLLED_BACK,
                        "reason_codes": tuple(
                            sorted((*overlay.reason_codes, "engagement_overlay_rolled_back"))
                        ),
                    },
                    "overlay_fingerprint",
                )
                if overlay.shadow_session_id == shadow_session_id
                else overlay
            )
            for key, overlay in self._overlays.items()
        }
        return InMemoryEngagementOverlayRepository(overlays, dict(self._snapshots))


__all__ = [
    "InMemoryEngagementOverlayRepository",
    "build_engagement_overlay_record",
    "build_engagement_overlay_snapshot",
]
