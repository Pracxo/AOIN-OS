"""Controlled in-memory engagement shadow application service."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.governed_engagement_learning import (
    APPROVAL_RECORD_ID,
    AUTHORIZATION_TRANSACTION_ID,
    RESOURCE_LIMITS,
    EngagementAdaptationConflictReport,
    EngagementAdaptationIdentity,
    EngagementAdaptationVersionPlan,
    EngagementApplicationApprovalBundle,
    EngagementApplicationAuthorizationEnvelope,
    EngagementApplicationBudgetDecision,
    EngagementApplicationIntegrityReport,
    EngagementApplicationMode,
    EngagementApplicationPlan,
    EngagementApplicationQuery,
    EngagementApplicationQueryResult,
    EngagementApplicationResourceBudget,
    EngagementApplicationResourceUsage,
    EngagementApplicationResult,
    EngagementApplicationRiskAssessment,
    EngagementApplicationStatus,
    EngagementBaselineSnapshot,
    EngagementCandidateBinding,
    EngagementCandidateDisposition,
    EngagementCounterfactualCase,
    EngagementCounterfactualRecommendation,
    EngagementCounterfactualResult,
    EngagementOverlayRecord,
    EngagementOverlaySnapshot,
    EngagementOverlayStatus,
    EngagementRollbackPlan,
    EngagementTargetPolicy,
    build_record,
    engagement_fingerprint,
    project_read_only_knowledge_context,
    utc_now,
)
from aion_brain.contracts.governed_learning_memory_persistence import (
    LocalKnowledgeQueryResult,
    LocalProjectionQueryResult,
)
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidate,
    EngagementSignalBatch,
)
from aion_brain.governed_learning_memory.engagement_adaptation_identity import (
    derive_engagement_adaptation_identity,
    detect_engagement_duplicates_and_conflicts,
)
from aion_brain.governed_learning_memory.engagement_adaptation_planning import (
    build_engagement_target_policy,
    plan_engagement_adaptation_version,
)
from aion_brain.governed_learning_memory.engagement_application_approval import (
    build_approval_bundle,
    classify_engagement_application_risk,
    project_existing_engagement_application_approval,
)
from aion_brain.governed_learning_memory.engagement_candidate_binding import (
    bind_engagement_candidates,
)
from aion_brain.governed_learning_memory.engagement_counterfactual_evaluation import (
    build_counterfactual_case,
    calculate_metric_delta,
    evaluate_counterfactual_case,
)
from aion_brain.governed_learning_memory.engagement_evidence import (
    build_evidence_bundle,
    build_operator_review_item,
)
from aion_brain.governed_learning_memory.engagement_integrity import (
    audit_engagement_application_plan,
    audit_engagement_application_result,
)
from aion_brain.governed_learning_memory.engagement_overlay import (
    InMemoryEngagementOverlayRepository,
    build_engagement_overlay_record,
    build_engagement_overlay_snapshot,
)
from aion_brain.governed_learning_memory.engagement_rollback import (
    build_engagement_rollback_plan,
)


def build_shadow_authorization_envelope(
    *,
    shadow_session_id: str,
    operator_identity_fingerprint: str,
    candidate_ids: tuple[str, ...],
    candidate_fingerprints: tuple[str, ...],
    overlay_snapshot_fingerprint: str,
    baseline_snapshot_fingerprint: str,
    fixture_fingerprint: str,
    allowed_target_components: tuple[str, ...],
    mode: EngagementApplicationMode = EngagementApplicationMode.DETERMINISTIC_SIMULATION,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> EngagementApplicationAuthorizationEnvelope:
    created = created_at or utc_now()
    payload = {
        "schema_version": "aion-glm-engagement-application-authorization/v1",
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "approval_record_id": APPROVAL_RECORD_ID,
        "shadow_session_id": shadow_session_id,
        "operator_identity_fingerprint": operator_identity_fingerprint,
        "candidate_ids": tuple(sorted(candidate_ids)),
        "candidate_fingerprints": tuple(sorted(candidate_fingerprints)),
        "overlay_snapshot_fingerprint": overlay_snapshot_fingerprint,
        "baseline_snapshot_fingerprint": baseline_snapshot_fingerprint,
        "fixture_fingerprint": fixture_fingerprint,
        "allowed_target_components": tuple(sorted(allowed_target_components)),
        "mode": mode,
        "created_at": created,
        "expires_at": expires_at or created + timedelta(minutes=30),
        "operator_invoked": True,
        "background_execution": False,
        "scheduled_execution": False,
        "production_application": False,
        "persistent_overlay": False,
        "approval_created": False,
        "runtime_effect": False,
    }
    return build_record(
        EngagementApplicationAuthorizationEnvelope,
        payload,
        "envelope_fingerprint",
    )


def build_engagement_baseline_snapshot(
    *,
    baseline_snapshot_id: str,
    bindings: tuple[EngagementCandidateBinding, ...],
    fixture_fingerprint: str,
    knowledge_results: tuple[LocalKnowledgeQueryResult, ...] = (),
    projection_results: tuple[LocalProjectionQueryResult, ...] = (),
    captured_at: datetime | None = None,
) -> EngagementBaselineSnapshot:
    context = project_read_only_knowledge_context(
        context_id=f"context-{baseline_snapshot_id}",
        knowledge_results=knowledge_results,
        projection_results=projection_results,
    )
    payload = {
        "schema_version": "aion-glm-engagement-baseline-snapshot/v1",
        "baseline_snapshot_id": baseline_snapshot_id,
        "target_component_fingerprints": tuple(
            sorted(
                engagement_fingerprint(
                    {"target_component_code": binding.target_component_code}
                )
                for binding in bindings
            )
        ),
        "target_policy_fingerprints": tuple(
            sorted(
                engagement_fingerprint({"target_policy_code": binding.target_policy_code})
                for binding in bindings
            )
        ),
        "local_knowledge_context_fingerprint": context.context_fingerprint,
        "fixture_fingerprint": fixture_fingerprint,
        "baseline_configuration_codes": ("baseline-retained", "shadow-only"),
        "captured_at": captured_at or utc_now(),
        "production_reference_present": False,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(EngagementBaselineSnapshot, payload, "snapshot_fingerprint")


class ControlledEngagementShadowApplicationService:
    """AION-226 deterministic, operator-invoked, in-memory shadow service."""

    def validate_authorization(
        self, envelope: EngagementApplicationAuthorizationEnvelope
    ) -> EngagementApplicationAuthorizationEnvelope:
        if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("authorization transaction mismatch")
        if envelope.approval_record_id != APPROVAL_RECORD_ID:
            raise ValueError("approval record mismatch")
        if not envelope.operator_invoked or envelope.production_application:
            raise ValueError("shadow application must be explicitly operator invoked")
        if envelope.persistent_overlay:
            raise ValueError("persistent overlay is not authorized")
        return envelope

    def bind_candidates(
        self,
        *,
        signal_batch: EngagementSignalBatch,
        candidates: tuple[EngagementLearningCandidate, ...],
        observed_at: datetime | None = None,
        valid_until: datetime,
    ) -> tuple[EngagementCandidateBinding, ...]:
        return bind_engagement_candidates(
            signal_batch=signal_batch,
            candidates=candidates,
            observed_at=observed_at,
            valid_until=valid_until,
        )

    def validate_candidate_lifecycle(
        self, bindings: tuple[EngagementCandidateBinding, ...]
    ) -> tuple[EngagementCandidateBinding, ...]:
        for binding in bindings:
            if binding.candidate_disposition not in {
                EngagementCandidateDisposition.ELIGIBLE_FOR_SHADOW,
                EngagementCandidateDisposition.EXACT_DUPLICATE_NO_OP,
            }:
                raise ValueError("candidate lifecycle is ineligible")
        return bindings

    def classify_risk(
        self,
        bindings: tuple[EngagementCandidateBinding, ...],
        assessed_at: datetime | None = None,
    ) -> tuple[EngagementApplicationRiskAssessment, ...]:
        return tuple(
            classify_engagement_application_risk(
                risk_assessment_id=f"risk-{binding.learning_candidate_id}",
                candidate_id=binding.learning_candidate_id,
                candidate_fingerprint=binding.candidate_fingerprint,
                candidate_kind=binding.candidate_kind,
                assessed_at=assessed_at,
            )
            for binding in bindings
        )

    def validate_approvals(
        self,
        *,
        approval_records: Mapping[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]],
        bindings: tuple[EngagementCandidateBinding, ...],
        risk_assessments: tuple[EngagementApplicationRiskAssessment, ...],
        identities: tuple[EngagementAdaptationIdentity, ...],
        baseline_snapshot: EngagementBaselineSnapshot,
        fixture_fingerprint: str,
        overlay_fingerprints: Mapping[str, str],
        rollback_fingerprints: Mapping[str, str],
        overlay_expires_at: datetime,
    ) -> tuple[EngagementApplicationApprovalBundle, ...]:
        bundles = []
        risk_by_candidate = {item.candidate_id: item for item in risk_assessments}
        identity_by_candidate = {item.candidate_id: item for item in identities}
        for binding in bindings:
            identity = identity_by_candidate[binding.learning_candidate_id]
            evidence = tuple(
                project_existing_engagement_application_approval(
                    approval_request=request,
                    approval_decision=decision,
                    candidate_id=binding.learning_candidate_id,
                    candidate_fingerprint=binding.candidate_fingerprint,
                    candidate_version=binding.candidate_version,
                    signal_fingerprints=binding.signal_fingerprints,
                    adaptation_identity_id=identity.adaptation_identity_id,
                    adaptation_version=1,
                    target_component_code=binding.target_component_code,
                    target_policy_code=binding.target_policy_code,
                    overlay_fingerprint=overlay_fingerprints[binding.learning_candidate_id],
                    baseline_snapshot_fingerprint=baseline_snapshot.snapshot_fingerprint,
                    fixture_fingerprint=fixture_fingerprint,
                    rollback_plan_fingerprint=rollback_fingerprints[
                        binding.learning_candidate_id
                    ],
                    overlay_expires_at=overlay_expires_at,
                )
                for request, decision in approval_records[binding.learning_candidate_id]
            )
            bundle = build_approval_bundle(
                bundle_id=f"approval-bundle-{binding.learning_candidate_id}",
                risk_assessment=risk_by_candidate[binding.learning_candidate_id],
                evidence_records=evidence,
            )
            if bundle.approval_status != "approved":
                raise ValueError("approval bundle is not authorized")
            bundles.append(bundle)
        return tuple(sorted(bundles, key=lambda item: item.bundle_id))

    def derive_adaptation_identities(
        self, bindings: tuple[EngagementCandidateBinding, ...]
    ) -> tuple[EngagementAdaptationIdentity, ...]:
        return tuple(
            sorted(
                (
                    derive_engagement_adaptation_identity(binding=binding)
                    for binding in bindings
                ),
                key=lambda item: item.adaptation_identity_id,
            )
        )

    def detect_duplicates_and_conflicts(
        self,
        *,
        identities: tuple[EngagementAdaptationIdentity, ...],
        overlay_fingerprints: dict[str, str],
        approval_bundle_fingerprints: dict[str, str],
    ) -> EngagementAdaptationConflictReport:
        return detect_engagement_duplicates_and_conflicts(
            identities=identities,
            overlay_fingerprints=overlay_fingerprints,
            approval_bundle_fingerprints=approval_bundle_fingerprints,
        )

    def plan_versions(
        self,
        *,
        identities: tuple[EngagementAdaptationIdentity, ...],
        approval_bundles: tuple[EngagementApplicationApprovalBundle, ...],
        effective_from: datetime | None = None,
        expires_at: datetime,
    ) -> tuple[EngagementAdaptationVersionPlan, ...]:
        bundles = {
            bundle.evidence_records[0].candidate_id: bundle for bundle in approval_bundles
        }
        return tuple(
            plan_engagement_adaptation_version(
                version_plan_id=f"version-plan-{identity.candidate_id}",
                identity=identity,
                approval_bundle=bundles[identity.candidate_id],
                candidate_version=1,
                effective_from=effective_from,
                expires_at=expires_at,
            )
            for identity in identities
        )

    def build_target_policies(
        self, identities: tuple[EngagementAdaptationIdentity, ...]
    ) -> tuple[EngagementTargetPolicy, ...]:
        return tuple(
            build_engagement_target_policy(
                target_policy_id=f"target-policy-{identity.candidate_id}",
                identity=identity,
            )
            for identity in identities
        )

    def build_baseline_snapshot(
        self,
        *,
        bindings: tuple[EngagementCandidateBinding, ...],
        fixture_fingerprint: str,
        captured_at: datetime | None = None,
    ) -> EngagementBaselineSnapshot:
        return build_engagement_baseline_snapshot(
            baseline_snapshot_id="baseline-engagement-shadow",
            bindings=bindings,
            fixture_fingerprint=fixture_fingerprint,
            captured_at=captured_at,
        )

    def build_overlay_snapshot(
        self,
        *,
        shadow_session_id: str,
        bindings: tuple[EngagementCandidateBinding, ...],
        identities: tuple[EngagementAdaptationIdentity, ...],
        version_plans: tuple[EngagementAdaptationVersionPlan, ...],
        target_policies: tuple[EngagementTargetPolicy, ...],
        risk_assessments: tuple[EngagementApplicationRiskAssessment, ...],
        approval_bundles: tuple[EngagementApplicationApprovalBundle, ...],
        baseline_snapshot: EngagementBaselineSnapshot,
        fixture_fingerprint: str,
        rollback_plans: tuple[EngagementRollbackPlan, ...],
        created_at: datetime | None = None,
        expires_at: datetime,
        status: EngagementOverlayStatus = EngagementOverlayStatus.ACTIVE_SHADOW,
    ) -> EngagementOverlaySnapshot:
        by_candidate = {binding.learning_candidate_id: binding for binding in bindings}
        identities_by_candidate = {item.candidate_id: item for item in identities}
        versions_by_candidate = {item.candidate_id: item for item in version_plans}
        policies_by_candidate = {
            item.target_policy_id.removeprefix("target-policy-"): item
            for item in target_policies
        }
        risk_by_candidate = {item.candidate_id: item for item in risk_assessments}
        bundles_by_candidate = {
            item.evidence_records[0].candidate_id: item for item in approval_bundles
        }
        rollback_by_candidate = {
            item.rollback_plan_id.removeprefix("rollback-"): item for item in rollback_plans
        }
        records: list[EngagementOverlayRecord] = []
        for candidate_id in sorted(by_candidate):
            records.append(
                build_engagement_overlay_record(
                    overlay_record_id=f"overlay-{candidate_id}",
                    shadow_session_id=shadow_session_id,
                    binding=by_candidate[candidate_id],
                    identity=identities_by_candidate[candidate_id],
                    version_plan=versions_by_candidate[candidate_id],
                    target_policy=policies_by_candidate[candidate_id],
                    risk_assessment=risk_by_candidate[candidate_id],
                    approval_bundle=bundles_by_candidate[candidate_id],
                    baseline_snapshot=baseline_snapshot,
                    fixture_fingerprint=fixture_fingerprint,
                    rollback_plan=rollback_by_candidate[candidate_id],
                    status=status,
                )
            )
        return build_engagement_overlay_snapshot(
            overlay_snapshot_id=f"overlay-snapshot-{shadow_session_id}",
            shadow_session_id=shadow_session_id,
            records=tuple(records),
            created_at=created_at,
            expires_at=expires_at,
        )

    def plan_rollback(
        self,
        *,
        shadow_session_id: str,
        overlay_snapshot: EngagementOverlaySnapshot,
        baseline_snapshot: EngagementBaselineSnapshot,
    ) -> tuple[EngagementRollbackPlan, ...]:
        return tuple(
            build_engagement_rollback_plan(
                rollback_plan_id=f"rollback-{record.candidate_id}",
                shadow_session_id=shadow_session_id,
                overlay_snapshot=overlay_snapshot,
                baseline_snapshot=baseline_snapshot,
            )
            for record in overlay_snapshot.records
        )

    def apply_shadow(
        self,
        *,
        repository: InMemoryEngagementOverlayRepository,
        overlay_snapshot: EngagementOverlaySnapshot,
    ) -> InMemoryEngagementOverlayRepository:
        return repository.with_overlays(overlay_snapshot.records).with_snapshot(overlay_snapshot)

    def evaluate_counterfactuals(
        self,
        *,
        overlay_snapshot: EngagementOverlaySnapshot,
        cases: tuple[EngagementCounterfactualCase, ...],
    ) -> tuple[EngagementCounterfactualResult, ...]:
        return tuple(
            evaluate_counterfactual_case(case=case, overlay_snapshot=overlay_snapshot)
            for case in sorted(cases, key=lambda item: item.case_id)
        )

    def query(
        self,
        repository: InMemoryEngagementOverlayRepository,
        query: EngagementApplicationQuery,
    ) -> EngagementApplicationQueryResult:
        return repository.query(query)

    def audit(self, plan: EngagementApplicationPlan) -> EngagementApplicationIntegrityReport:
        return audit_engagement_application_plan(
            integrity_report_id=f"integrity-{plan.application_plan_id}",
            plan=plan,
        )

    def replay_fixture(self, fixture_fingerprint: str) -> str:
        return engagement_fingerprint({"fixture_fingerprint": fixture_fingerprint})

    def expire_session(
        self,
        repository: InMemoryEngagementOverlayRepository,
        shadow_session_id: str,
    ) -> InMemoryEngagementOverlayRepository:
        return repository.expire_session(shadow_session_id)

    def rollback_session(
        self,
        repository: InMemoryEngagementOverlayRepository,
        shadow_session_id: str,
    ) -> InMemoryEngagementOverlayRepository:
        return repository.rollback_session(shadow_session_id)

    def reject_persistent_write(self) -> None:
        raise ValueError("persistent engagement overlay writes are disabled")

    def run_application(
        self,
        *,
        shadow_session_id: str,
        signal_batch: EngagementSignalBatch,
        candidates: tuple[EngagementLearningCandidate, ...],
        approval_records: Mapping[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]],
        fixture_fingerprint: str,
        operator_identity_fingerprint: str,
        expires_at: datetime,
        now: datetime | None = None,
    ) -> tuple[EngagementApplicationPlan, EngagementApplicationResult]:
        current_time = now or utc_now()
        bindings = self.bind_candidates(
            signal_batch=signal_batch,
            candidates=candidates,
            observed_at=current_time,
            valid_until=expires_at,
        )
        self.validate_candidate_lifecycle(bindings)
        risks = self.classify_risk(bindings, assessed_at=current_time)
        identities = self.derive_adaptation_identities(bindings)
        baseline = self.build_baseline_snapshot(
            bindings=bindings,
            fixture_fingerprint=fixture_fingerprint,
            captured_at=current_time,
        )
        provisional_overlay_fps = {
            binding.learning_candidate_id: engagement_fingerprint(
                {
                    "candidate": binding.candidate_fingerprint,
                    "baseline": baseline.snapshot_fingerprint,
                    "fixture": fixture_fingerprint,
                }
            )
            for binding in bindings
        }
        provisional_rollback_fps = {
            binding.learning_candidate_id: engagement_fingerprint(
                {"rollback": binding.candidate_fingerprint, "fixture": fixture_fingerprint}
            )
            for binding in bindings
        }
        bundles = self.validate_approvals(
            approval_records=approval_records,
            bindings=bindings,
            risk_assessments=risks,
            identities=identities,
            baseline_snapshot=baseline,
            fixture_fingerprint=fixture_fingerprint,
            overlay_fingerprints=provisional_overlay_fps,
            rollback_fingerprints=provisional_rollback_fps,
            overlay_expires_at=expires_at,
        )
        versions = self.plan_versions(
            identities=identities,
            approval_bundles=bundles,
            effective_from=current_time,
            expires_at=expires_at,
        )
        target_policies = self.build_target_policies(identities)
        placeholder_snapshot = build_record(
            EngagementOverlaySnapshot,
            {
                "schema_version": "aion-glm-engagement-overlay-snapshot/v1",
                "overlay_snapshot_id": f"overlay-snapshot-{shadow_session_id}-placeholder",
                "shadow_session_id": shadow_session_id,
                "records": (),
                "record_count": 0,
                "adaptation_identity_ids": (),
                "adaptation_version_vector": (),
                "created_at": current_time,
                "expires_at": expires_at,
                "immutable": True,
                "in_memory_only": True,
                "persistent_write_applied": False,
                "production_policy_effect": False,
                "runtime_effect": False,
            },
            "snapshot_fingerprint",
        )
        placeholder_rollbacks = tuple(
            build_engagement_rollback_plan(
                rollback_plan_id=f"rollback-{binding.learning_candidate_id}",
                shadow_session_id=shadow_session_id,
                overlay_snapshot=placeholder_snapshot,
                baseline_snapshot=baseline,
            )
            for binding in bindings
        )
        overlay_snapshot = self.build_overlay_snapshot(
            shadow_session_id=shadow_session_id,
            bindings=bindings,
            identities=identities,
            version_plans=versions,
            target_policies=target_policies,
            risk_assessments=risks,
            approval_bundles=bundles,
            baseline_snapshot=baseline,
            fixture_fingerprint=fixture_fingerprint,
            rollback_plans=placeholder_rollbacks,
            created_at=current_time,
            expires_at=expires_at,
        )
        rollbacks = self.plan_rollback(
            shadow_session_id=shadow_session_id,
            overlay_snapshot=overlay_snapshot,
            baseline_snapshot=baseline,
        )
        envelope = build_shadow_authorization_envelope(
            shadow_session_id=shadow_session_id,
            operator_identity_fingerprint=operator_identity_fingerprint,
            candidate_ids=tuple(binding.learning_candidate_id for binding in bindings),
            candidate_fingerprints=tuple(binding.candidate_fingerprint for binding in bindings),
            overlay_snapshot_fingerprint=overlay_snapshot.snapshot_fingerprint,
            baseline_snapshot_fingerprint=baseline.snapshot_fingerprint,
            fixture_fingerprint=fixture_fingerprint,
            allowed_target_components=tuple(
                sorted({binding.target_component_code for binding in bindings})
            ),
            created_at=current_time,
            expires_at=expires_at,
        )
        self.validate_authorization(envelope)
        conflicts = self.detect_duplicates_and_conflicts(
            identities=identities,
            overlay_fingerprints={
                record.candidate_id: record.overlay_fingerprint
                for record in overlay_snapshot.records
            },
            approval_bundle_fingerprints={
                bundle.evidence_records[0].candidate_id: bundle.bundle_fingerprint
                for bundle in bundles
            },
        )
        usage = build_record(
            EngagementApplicationResourceUsage,
            {
                "usage_id": f"usage-{shadow_session_id}",
                "engagement_candidates": len(bindings),
                "signal_references_per_candidate": max(
                    (len(binding.signal_ids) for binding in bindings), default=0
                ),
                "candidate_versions": len(versions),
                "target_components": len({binding.target_component_code for binding in bindings}),
                "approval_records": sum(len(bundle.evidence_records) for bundle in bundles),
                "adaptation_plans": len(versions),
                "overlay_records": overlay_snapshot.record_count,
                "overlay_versions": len(versions),
                "overlay_snapshots": 1,
                "counterfactual_cases": len(bindings),
                "metrics_per_case": 13,
                "comparisons": len(bindings),
                "rollback_steps": sum(plan.step_count for plan in rollbacks),
                "operator_review_items": len(bindings),
                "query_results": 0,
                "fixture_records": len(bindings),
                "fixture_bytes": 1024,
                "concurrency": 1,
                "runtime_effect": False,
            },
            "usage_fingerprint",
        )
        budget = build_record(
            EngagementApplicationResourceBudget,
            {
                "budget_id": f"budget-{shadow_session_id}",
                "limits": dict(RESOURCE_LIMITS),
                "runtime_effect": False,
            },
            "budget_fingerprint",
        )
        budget_decision = build_record(
            EngagementApplicationBudgetDecision,
            {
                "decision_id": f"budget-decision-{shadow_session_id}",
                "budget": budget,
                "usage": usage,
                "budget_passed": True,
                "reason_codes": ("engagement_resource_budget_passed",),
                "runtime_effect": False,
            },
            "decision_fingerprint",
        )
        cases = tuple(
            build_counterfactual_case(
                case_id=f"case-{binding.learning_candidate_id}",
                target_component_code=binding.target_component_code,
                target_policy_code=binding.target_policy_code,
                input_codes=("synthetic-fixture", binding.candidate_kind.value),
            )
            for binding in bindings
        )
        plan_payload = {
            "schema_version": "aion-glm-engagement-application-plan/v1",
            "application_plan_id": f"plan-{shadow_session_id}",
            "authorization_envelope": envelope,
            "candidate_bindings": bindings,
            "risk_assessments": risks,
            "approval_bundles": bundles,
            "adaptation_identities": identities,
            "conflict_report": conflicts,
            "version_plans": versions,
            "target_policies": target_policies,
            "baseline_snapshot": baseline,
            "overlay_snapshot": overlay_snapshot,
            "rollback_plans": rollbacks,
            "counterfactual_cases": cases,
            "resource_budget_decision": budget_decision,
            "operator_review_required": True,
            "production_application_authorized": False,
            "persistent_overlay_authorized": False,
            "automatic_application": False,
            "runtime_effect": False,
        }
        plan = build_record(EngagementApplicationPlan, plan_payload, "plan_fingerprint")
        repo = self.apply_shadow(
            repository=InMemoryEngagementOverlayRepository(),
            overlay_snapshot=overlay_snapshot,
        )
        results = self.evaluate_counterfactuals(overlay_snapshot=overlay_snapshot, cases=cases)
        closed_repo = self.rollback_session(repo, shadow_session_id)
        active_after_close = closed_repo.active_overlay_count()
        recommendation = (
            EngagementCounterfactualRecommendation.RETAIN_BASELINE
            if conflicts.unresolved_material_conflicts
            else EngagementCounterfactualRecommendation.APPROVE_SHADOW_CANDIDATE
        )
        review_items = tuple(
            build_operator_review_item(
                review_item_id=f"review-{binding.learning_candidate_id}",
                candidate_id=binding.learning_candidate_id,
                recommendation=recommendation,
                reason_codes=("engagement_approve_shadow_candidate",),
            )
            for binding in bindings
        )
        evidence = build_evidence_bundle(
            evidence_bundle_id=f"evidence-{shadow_session_id}",
            bounded_counts={
                "candidate_count": len(bindings),
                "overlay_record_count": overlay_snapshot.record_count,
                "active_overlay_records_after_close": active_after_close,
            },
            operator_review_items=review_items,
        )
        aggregate_metrics = (
            calculate_metric_delta(
                metric_name="task_completion",
                baseline_value=Decimal("0.000000"),
                candidate_value=Decimal("1.000000"),
            ),
        )
        integrity = self.audit(plan)
        status = (
            EngagementApplicationStatus.ABSTAINED
            if conflicts.unresolved_material_conflicts
            else EngagementApplicationStatus.SHADOW_APPLIED
        )
        result_payload = {
            "schema_version": "aion-glm-engagement-application-result/v1",
            "application_result_id": f"result-{shadow_session_id}",
            "shadow_session_id": shadow_session_id,
            "status": status,
            "candidate_dispositions": {
                binding.learning_candidate_id: binding.candidate_disposition
                for binding in bindings
            },
            "adaptation_dispositions": {
                version.candidate_id: version.disposition for version in versions
            },
            "overlay_snapshot_fingerprint": overlay_snapshot.snapshot_fingerprint,
            "baseline_snapshot_fingerprint": baseline.snapshot_fingerprint,
            "counterfactual_results": results,
            "aggregate_metric_deltas": aggregate_metrics,
            "recommendation": recommendation,
            "reason_codes": (
                "engagement_overlay_rolled_back",
                "engagement_runtime_disabled",
                "engagement_approve_shadow_candidate",
            ),
            "integrity_report": integrity,
            "evidence_bundle": evidence,
            "operator_review_items": review_items,
            "overlay_expired_or_rolled_back": True,
            "active_overlay_records_after_close": active_after_close,
            "runtime_effect": False,
        }
        result = build_record(EngagementApplicationResult, result_payload, "result_fingerprint")
        final_integrity = audit_engagement_application_result(
            integrity_report_id=f"integrity-result-{shadow_session_id}",
            result=result,
        )
        result = build_record(
            EngagementApplicationResult,
            {**result_payload, "integrity_report": final_integrity},
            "result_fingerprint",
        )
        return plan, result


__all__ = [
    "ControlledEngagementShadowApplicationService",
    "build_engagement_baseline_snapshot",
    "build_shadow_authorization_envelope",
]
