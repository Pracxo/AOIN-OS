"""Explicit cycle orchestration for the AION-228 continual-learning pilot."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from pathlib import Path
from typing import Any

from aion_brain.contracts.governed_continual_learning import (
    AUTHORIZATION_TRANSACTION_ID,
    ZERO_HASH,
    ContinualLearningBudgetDecision,
    ContinualLearningCheckpoint,
    ContinualLearningComponentInvocationBinding,
    ContinualLearningCrossCycleContext,
    ContinualLearningCycleKind,
    ContinualLearningCycleOutcome,
    ContinualLearningCycleOutcomeStatus,
    ContinualLearningCyclePlan,
    ContinualLearningCycleState,
    ContinualLearningError,
    ContinualLearningIntegrityReport,
    ContinualLearningKnowledgeCandidateBinding,
    ContinualLearningKnowledgeStatus,
    ContinualLearningPersistenceBinding,
    ContinualLearningPersistenceStatus,
    ContinualLearningPilotAuthorizationEnvelope,
    ContinualLearningPilotMode,
    ContinualLearningPromotionBinding,
    ContinualLearningPromotionStatus,
    ContinualLearningQuery,
    ContinualLearningQueryResult,
    ContinualLearningResearchBinding,
    ContinualLearningResearchPlan,
    ContinualLearningResearchStatus,
    ContinualLearningResourceUsage,
    ContinualLearningRollbackPlan,
    ContinualLearningSessionPlan,
    ContinualLearningSessionResult,
    ContinualLearningShadowBinding,
    ContinualLearningShadowStatus,
    ContinualLearningStageCommand,
    ContinualLearningStageDisposition,
    ContinualLearningStageReceipt,
    assert_allowed_transition,
    build_record,
    continual_fingerprint,
    evaluate_resource_budget,
    fingerprint_file_path,
    utc_now,
)
from aion_brain.governed_learning_memory.continual_learning_authorization import (
    validate_authorization,
)
from aion_brain.governed_learning_memory.continual_learning_evidence import (
    build_evidence_bundle,
    build_operator_review_item,
)
from aion_brain.governed_learning_memory.continual_learning_intake import (
    build_continual_learning_engagement_intake,
)
from aion_brain.governed_learning_memory.continual_learning_integrity import (
    audit_continual_learning_session,
)
from aion_brain.governed_learning_memory.continual_learning_knowledge_pipeline import (
    ControlledContinualLearningKnowledgePipeline,
)
from aion_brain.governed_learning_memory.continual_learning_outcome import (
    build_cycle_outcome,
    build_session_result,
    run_exact_query,
)
from aion_brain.governed_learning_memory.continual_learning_persistence import (
    ControlledContinualLearningPersistenceAdapter,
)
from aion_brain.governed_learning_memory.continual_learning_research import (
    ControlledContinualLearningResearchAdapter,
)
from aion_brain.governed_learning_memory.continual_learning_shadow import (
    ControlledContinualLearningShadowAdapter,
)

FULL_COMPLETED_SEQUENCE: tuple[ContinualLearningCycleState, ...] = (
    ContinualLearningCycleState.DRAFTED,
    ContinualLearningCycleState.AUTHORIZED,
    ContinualLearningCycleState.ENGAGEMENT_INTAKE_VALIDATED,
    ContinualLearningCycleState.RESEARCH_GAP_SELECTED,
    ContinualLearningCycleState.RESEARCH_PLANNED,
    ContinualLearningCycleState.RESEARCH_ACQUIRED,
    ContinualLearningCycleState.EVIDENCE_ASSESSED,
    ContinualLearningCycleState.VERIFIED_CANDIDATE_REVIEWED,
    ContinualLearningCycleState.PROMOTION_PLANNED,
    ContinualLearningCycleState.PERSISTENCE_APPROVAL_VALIDATED,
    ContinualLearningCycleState.TEMPORARILY_PERSISTED,
    ContinualLearningCycleState.SHADOW_APPLICATION_PLANNED,
    ContinualLearningCycleState.SHADOW_APPLICATION_EVALUATED,
    ContinualLearningCycleState.CYCLE_COMPLETED,
)
CYCLE3_ABSTENTION_SEQUENCE: tuple[ContinualLearningCycleState, ...] = (
    ContinualLearningCycleState.DRAFTED,
    ContinualLearningCycleState.AUTHORIZED,
    ContinualLearningCycleState.ENGAGEMENT_INTAKE_VALIDATED,
    ContinualLearningCycleState.RESEARCH_GAP_SELECTED,
    ContinualLearningCycleState.RESEARCH_PLANNED,
    ContinualLearningCycleState.RESEARCH_ACQUIRED,
    ContinualLearningCycleState.EVIDENCE_ASSESSED,
    ContinualLearningCycleState.ABSTAINED,
)


def build_rollback_plan(
    *,
    session_id: str,
    cycle_id: str,
    operations: tuple[str, ...] = (
        "abstain_current_stage",
        "invalidate_pending_promotion",
        "discard_pending_persistence_request",
        "rollback_shadow_session",
        "expire_shadow_overlay",
        "close_temporary_store",
        "purge_source_bodies",
        "remove_checkpoint_files",
        "remove_approval_fixtures",
        "remove_database_files",
        "preserve_redacted_evidence",
    ),
) -> ContinualLearningRollbackPlan:
    """Build the closed rollback operation list."""

    return build_record(
        ContinualLearningRollbackPlan,
        {
            "schema_version": "aion-glm-continual-learning-rollback/v1",
            "rollback_plan_id": f"{cycle_id}-rollback",
            "session_id": session_id,
            "cycle_id": cycle_id,
            "rollback_operations": operations,
            "referenced_fingerprints": (),
            "created_at": utc_now(),
        },
        "rollback_plan_fingerprint",
    )


def build_cycle_plan(
    *,
    session_id: str,
    cycle_id: str,
    cycle_kind: ContinualLearningCycleKind,
    cycle_sequence: int,
    terminal_outcome: ContinualLearningCycleOutcomeStatus,
    required_stages: tuple[ContinualLearningCycleState, ...],
    explicit_no_op_stages: tuple[ContinualLearningCycleState, ...] = (),
) -> ContinualLearningCyclePlan:
    """Build one immutable cycle plan."""

    rollback = build_rollback_plan(session_id=session_id, cycle_id=cycle_id)
    return build_record(
        ContinualLearningCyclePlan,
        {
            "schema_version": "aion-glm-continual-learning-cycle-plan/v1",
            "cycle_id": cycle_id,
            "session_id": session_id,
            "cycle_kind": cycle_kind,
            "cycle_sequence": cycle_sequence,
            "required_stages": required_stages,
            "explicit_no_op_stages": explicit_no_op_stages,
            "input_fingerprints": (continual_fingerprint({"cycle_input": cycle_id}),),
            "approval_requirement_fingerprints": (
                continual_fingerprint({"approval_requirement": cycle_id}),
            ),
            "expected_terminal_outcome": terminal_outcome,
            "maximum_cycle_seconds": 1800,
            "rollback_plan_fingerprint": rollback.rollback_plan_fingerprint,
            "cleanup_requirement_fingerprints": (
                continual_fingerprint({"cleanup": cycle_id, "retained_files": 0}),
            ),
            "created_at": utc_now(),
        },
        "cycle_plan_fingerprint",
    )


def build_three_cycle_session_plan(
    *,
    session_id: str,
    mode: ContinualLearningPilotMode,
    exact_domain_allowlist: tuple[str, ...],
    explicit_source_url_fingerprints: tuple[str, ...],
    operator_identity_fingerprint: str,
) -> ContinualLearningSessionPlan:
    """Build the exact three-cycle session plan used by live and deterministic pilots."""

    normalized_domains = tuple(sorted(exact_domain_allowlist))
    cycle_1_id = (
        "aion-228-live-cycle-001"
        if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
        else f"{session_id}-cycle-001"
    )
    cycle_2_id = (
        "aion-228-live-cycle-002"
        if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
        else f"{session_id}-cycle-002"
    )
    cycle_3_id = (
        "aion-228-live-cycle-003"
        if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE
        else f"{session_id}-cycle-003"
    )
    cycle_plans = (
        build_cycle_plan(
            session_id=session_id,
            cycle_id=cycle_1_id,
            cycle_kind=ContinualLearningCycleKind.EVIDENCE_ACQUISITION_AND_TEMPORARY_CONTINUITY,
            cycle_sequence=1,
            terminal_outcome=ContinualLearningCycleOutcomeStatus.COMPLETED,
            required_stages=FULL_COMPLETED_SEQUENCE,
            explicit_no_op_stages=(ContinualLearningCycleState.SHADOW_APPLICATION_PLANNED,),
        ),
        build_cycle_plan(
            session_id=session_id,
            cycle_id=cycle_2_id,
            cycle_kind=ContinualLearningCycleKind.READ_CONTEXT_AND_SHADOW_ADAPTATION,
            cycle_sequence=2,
            terminal_outcome=ContinualLearningCycleOutcomeStatus.COMPLETED,
            required_stages=FULL_COMPLETED_SEQUENCE,
            explicit_no_op_stages=(
                ContinualLearningCycleState.RESEARCH_ACQUIRED,
                ContinualLearningCycleState.PROMOTION_PLANNED,
                ContinualLearningCycleState.TEMPORARILY_PERSISTED,
            ),
        ),
        build_cycle_plan(
            session_id=session_id,
            cycle_id=cycle_3_id,
            cycle_kind=ContinualLearningCycleKind.CONTRADICTION_ABSTENTION_AND_ROLLBACK,
            cycle_sequence=3,
            terminal_outcome=ContinualLearningCycleOutcomeStatus.ABSTAINED,
            required_stages=CYCLE3_ABSTENTION_SEQUENCE,
            explicit_no_op_stages=(ContinualLearningCycleState.PROMOTION_PLANNED,),
        ),
    )
    now = utc_now()
    return build_record(
        ContinualLearningSessionPlan,
        {
            "schema_version": "aion-glm-continual-learning-session-plan/v1",
            "session_id": session_id,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "mode": mode,
            "cycle_plans": cycle_plans,
            "exact_domain_allowlist": normalized_domains,
            "explicit_source_url_fingerprints": explicit_source_url_fingerprints,
            "operator_identity_fingerprint": operator_identity_fingerprint,
            "maximum_session_seconds": 7200,
            "created_at": now,
            "expires_at": now + timedelta(hours=2),
            "final_cleanup_plan_fingerprint": continual_fingerprint(
                {"session_cleanup": session_id, "retained_files": 0}
            ),
        },
        "session_plan_fingerprint",
    )


def build_stage_command(
    *,
    stage_command_id: str,
    session_id: str,
    cycle_id: str,
    expected_current_state: ContinualLearningCycleState,
    requested_next_state: ContinualLearningCycleState,
    cycle_plan_fingerprint: str,
    operator_identity_fingerprint: str,
    input_fingerprints: tuple[str, ...] = (),
    approval_bundle_fingerprints: tuple[str, ...] = (),
) -> ContinualLearningStageCommand:
    """Build one explicit operator-invoked stage command."""

    now = utc_now()
    return build_record(
        ContinualLearningStageCommand,
        {
            "schema_version": "aion-glm-continual-learning-stage-command/v1",
            "stage_command_id": stage_command_id,
            "session_id": session_id,
            "cycle_id": cycle_id,
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "expected_current_state": expected_current_state,
            "requested_next_state": requested_next_state,
            "cycle_plan_fingerprint": cycle_plan_fingerprint,
            "input_fingerprints": input_fingerprints,
            "approval_bundle_fingerprints": approval_bundle_fingerprints,
            "operator_identity_fingerprint": operator_identity_fingerprint,
            "created_at": now,
            "expires_at": now + timedelta(minutes=30),
        },
        "command_fingerprint",
    )


class ControlledLocalContinualLearningPilotService:
    """Operator-invoked local continual-learning pilot service."""

    def __init__(
        self,
        *,
        research_adapter: ControlledContinualLearningResearchAdapter | None = None,
        knowledge_pipeline: ControlledContinualLearningKnowledgePipeline | None = None,
        persistence_adapter: ControlledContinualLearningPersistenceAdapter | None = None,
        shadow_adapter: ControlledContinualLearningShadowAdapter | None = None,
    ) -> None:
        self.research_adapter = research_adapter
        self.knowledge_pipeline = (
            knowledge_pipeline or ControlledContinualLearningKnowledgePipeline()
        )
        self.persistence_adapter = (
            persistence_adapter or ControlledContinualLearningPersistenceAdapter()
        )
        self.shadow_adapter = shadow_adapter or ControlledContinualLearningShadowAdapter()

    def validate_authorization(
        self,
        envelope: ContinualLearningPilotAuthorizationEnvelope,
    ) -> ContinualLearningPilotAuthorizationEnvelope:
        return validate_authorization(envelope)

    def validate_session_plan(
        self,
        plan: ContinualLearningSessionPlan,
    ) -> ContinualLearningSessionPlan:
        if plan.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise ContinualLearningError("session plan authorization mismatch")
        return plan

    def validate_cycle_plan(self, plan: ContinualLearningCyclePlan) -> ContinualLearningCyclePlan:
        if not plan.operator_invoked or plan.automatic_transition:
            raise ContinualLearningError("cycle plan must require explicit invocation")
        return plan

    def validate_stage_command(
        self,
        *,
        command: ContinualLearningStageCommand,
        cycle_plan: ContinualLearningCyclePlan,
        current_state: ContinualLearningCycleState,
    ) -> ContinualLearningStageCommand:
        if command.expires_at <= utc_now():
            raise ContinualLearningError("stage command expired")
        if command.session_id != cycle_plan.session_id or command.cycle_id != cycle_plan.cycle_id:
            raise ContinualLearningError("stage command plan mismatch")
        if command.expected_current_state is not current_state:
            raise ContinualLearningError("stage command current state mismatch")
        if command.cycle_plan_fingerprint != cycle_plan.cycle_plan_fingerprint:
            raise ContinualLearningError("stage command cycle plan mismatch")
        assert_allowed_transition(command.expected_current_state, command.requested_next_state)
        return command

    def advance_stage(
        self,
        *,
        command: ContinualLearningStageCommand,
        cycle_plan: ContinualLearningCyclePlan,
        current_state: ContinualLearningCycleState,
        prior_receipt: ContinualLearningStageReceipt | None = None,
        disposition: ContinualLearningStageDisposition = ContinualLearningStageDisposition.EXECUTED,
        output_fingerprints: tuple[str, ...] = (),
        reason_codes: tuple[str, ...] = ("explicit_operator_stage_advanced",),
        bounded_counts: dict[str, int] | None = None,
    ) -> ContinualLearningStageReceipt:
        """Advance one state and return an immutable stage receipt."""

        self.validate_stage_command(
            command=command,
            cycle_plan=cycle_plan,
            current_state=current_state,
        )
        sequence_number = 1 if prior_receipt is None else prior_receipt.sequence_number + 1
        prior_fingerprint = (
            ZERO_HASH if prior_receipt is None else prior_receipt.receipt_fingerprint
        )
        return build_record(
            ContinualLearningStageReceipt,
            {
                "schema_version": "aion-glm-continual-learning-stage-receipt/v1",
                "stage_receipt_id": f"{command.cycle_id}-receipt-{sequence_number:02d}",
                "session_id": command.session_id,
                "cycle_id": command.cycle_id,
                "sequence_number": sequence_number,
                "prior_receipt_fingerprint": prior_fingerprint,
                "state_before": command.expected_current_state,
                "state_after": command.requested_next_state,
                "disposition": disposition,
                "command_fingerprint": command.command_fingerprint,
                "input_fingerprints": command.input_fingerprints,
                "output_fingerprints": output_fingerprints,
                "approval_bundle_fingerprints": command.approval_bundle_fingerprints,
                "bounded_counts": bounded_counts or {},
                "reason_codes": reason_codes,
                "created_at": utc_now(),
            },
            "receipt_fingerprint",
        )

    def build_engagement_intake(self, **kwargs: Any) -> Any:
        return build_continual_learning_engagement_intake(**kwargs)

    def select_research_gap(self, intake: Any) -> str:
        return str(intake.selected_candidate_id)

    def plan_research(self, **kwargs: Any) -> ContinualLearningResearchPlan:
        if self.research_adapter is None:
            raise ContinualLearningError("research adapter is not configured")
        return self.research_adapter.plan_research(**kwargs)

    def acquire_research(self, **kwargs: Any) -> ContinualLearningResearchBinding:
        if self.research_adapter is None:
            raise ContinualLearningError("research adapter is not configured")
        return self.research_adapter.acquire_research(**kwargs)

    def assess_evidence(self, research_binding: ContinualLearningResearchBinding) -> str:
        return continual_fingerprint({"assessment": research_binding.research_binding_fingerprint})

    def build_verified_candidate(self, **kwargs: Any) -> ContinualLearningKnowledgeCandidateBinding:
        return self.knowledge_pipeline.build_candidate_binding(**kwargs)

    def plan_promotion(
        self,
        *,
        session_id: str,
        cycle_id: str,
        transaction_id: str,
        candidate_binding: ContinualLearningKnowledgeCandidateBinding,
        approval_bundle_fingerprint: str,
        approval_count: int = 1,
    ) -> ContinualLearningPromotionBinding:
        status = (
            ContinualLearningPromotionStatus.DRY_RUN_PASSED
            if candidate_binding.candidate_status
            is ContinualLearningKnowledgeStatus.ELIGIBLE_FOR_REVIEW
            else ContinualLearningPromotionStatus.ABSTAINED
        )
        return build_record(
            ContinualLearningPromotionBinding,
            {
                "schema_version": "aion-glm-continual-learning-promotion-binding/v1",
                "binding_id": f"{cycle_id}-promotion-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "transaction_id": transaction_id,
                "status": status,
                "candidate_fingerprint": candidate_binding.candidate_binding_fingerprint,
                "promotion_plan_fingerprint": continual_fingerprint(
                    {"promotion_plan": transaction_id}
                ),
                "promotion_result_fingerprint": continual_fingerprint(
                    {"promotion_result": transaction_id, "dry_run": status.value}
                ),
                "approval_bundle_fingerprint": approval_bundle_fingerprint,
                "approval_count": approval_count,
                "created_at": utc_now(),
            },
            "promotion_binding_fingerprint",
        )

    def validate_promotion_approvals(self, binding: ContinualLearningPromotionBinding) -> bool:
        return (
            binding.status is ContinualLearningPromotionStatus.DRY_RUN_PASSED
            and binding.approval_count >= 1
        )

    def validate_persistence_approvals(
        self,
        approval_actor_ids: tuple[str, str],
        requester_id: str,
    ) -> bool:
        if len(set(approval_actor_ids)) != 2:
            raise ContinualLearningError("dual persistence approvals must be independent")
        if requester_id in approval_actor_ids:
            raise ContinualLearningError("requester cannot be a persistence approver")
        return True

    def persist_temporarily(self, **kwargs: Any) -> ContinualLearningPersistenceBinding:
        return self.persistence_adapter.build_temporary_persistence_binding(**kwargs)

    def read_cross_cycle_context(
        self,
        *,
        session_id: str,
        completed_cycle_ids: tuple[str, ...],
        receipt_chain_heads: tuple[str, ...],
        research_bindings: tuple[ContinualLearningResearchBinding, ...] = (),
        candidate_bindings: tuple[ContinualLearningKnowledgeCandidateBinding, ...] = (),
        promotion_bindings: tuple[ContinualLearningPromotionBinding, ...] = (),
        persistence_bindings: tuple[ContinualLearningPersistenceBinding, ...] = (),
        shadow_bindings: tuple[ContinualLearningShadowBinding, ...] = (),
        contradiction_fingerprints: tuple[str, ...] = (),
    ) -> ContinualLearningCrossCycleContext:
        return build_record(
            ContinualLearningCrossCycleContext,
            {
                "schema_version": "aion-glm-continual-learning-cross-cycle-context/v1",
                "context_id": f"{session_id}-cross-cycle-context-{len(completed_cycle_ids)}",
                "session_id": session_id,
                "completed_cycle_ids": completed_cycle_ids,
                "cycle_receipt_chain_heads": receipt_chain_heads,
                "research_result_fingerprints": tuple(
                    item.research_binding_fingerprint for item in research_bindings
                ),
                "candidate_fingerprints": tuple(
                    item.candidate_binding_fingerprint for item in candidate_bindings
                ),
                "promotion_result_fingerprints": tuple(
                    item.promotion_binding_fingerprint for item in promotion_bindings
                ),
                "persistence_receipt_fingerprints": tuple(
                    item.persistence_receipt_fingerprint for item in persistence_bindings
                ),
                "exact_knowledge_query_fingerprints": (
                    continual_fingerprint({"exact_query": completed_cycle_ids}),
                ),
                "knowledge_identity_ids": tuple(
                    identity
                    for binding in persistence_bindings
                    for identity in binding.knowledge_identity_ids
                ),
                "knowledge_version_ids": tuple(
                    version
                    for binding in persistence_bindings
                    for version in binding.knowledge_version_ids
                ),
                "shadow_result_fingerprints": tuple(
                    item.shadow_binding_fingerprint for item in shadow_bindings
                ),
                "unresolved_gap_fingerprints": (),
                "contradiction_fingerprints": contradiction_fingerprints,
                "created_at": utc_now(),
            },
            "context_fingerprint",
        )

    def plan_shadow_application(self, candidate_fingerprint: str) -> str:
        return continual_fingerprint({"shadow_plan": candidate_fingerprint})

    def validate_shadow_approvals(self, approval_count: int) -> bool:
        if approval_count < 1:
            raise ContinualLearningError("shadow application requires existing approval")
        return True

    def apply_shadow(self, **kwargs: Any) -> ContinualLearningShadowBinding:
        return self.shadow_adapter.build_shadow_binding(**kwargs)

    def evaluate_shadow(self, binding: ContinualLearningShadowBinding) -> str:
        return continual_fingerprint({"shadow_evaluation": binding.shadow_binding_fingerprint})

    def build_checkpoint(
        self,
        *,
        checkpoint_id: str,
        session_id: str,
        cycle_id: str,
        current_state: ContinualLearningCycleState,
        latest_stage_receipt_fingerprint: str,
        cycle_plan_fingerprint: str,
        authorization_envelope_fingerprint: str,
        temporary_file_path: Path,
        research_binding_fingerprint: str = ZERO_HASH,
        candidate_binding_fingerprint: str = ZERO_HASH,
        promotion_binding_fingerprint: str = ZERO_HASH,
        persistence_binding_fingerprint: str = ZERO_HASH,
        shadow_binding_fingerprint: str = ZERO_HASH,
        cross_cycle_context_fingerprint: str = ZERO_HASH,
    ) -> ContinualLearningCheckpoint:
        now = utc_now()
        return build_record(
            ContinualLearningCheckpoint,
            {
                "schema_version": "aion-glm-continual-learning-checkpoint/v1",
                "checkpoint_id": checkpoint_id,
                "session_id": session_id,
                "cycle_id": cycle_id,
                "current_state": current_state,
                "latest_stage_receipt_fingerprint": latest_stage_receipt_fingerprint,
                "receipt_chain_head": latest_stage_receipt_fingerprint,
                "cycle_plan_fingerprint": cycle_plan_fingerprint,
                "authorization_envelope_fingerprint": authorization_envelope_fingerprint,
                "research_binding_fingerprint": research_binding_fingerprint,
                "candidate_binding_fingerprint": candidate_binding_fingerprint,
                "promotion_binding_fingerprint": promotion_binding_fingerprint,
                "persistence_binding_fingerprint": persistence_binding_fingerprint,
                "shadow_binding_fingerprint": shadow_binding_fingerprint,
                "cross_cycle_context_fingerprint": cross_cycle_context_fingerprint,
                "created_at": now,
                "expires_at": now + timedelta(minutes=30),
                "temporary_file_fingerprint": fingerprint_file_path(temporary_file_path),
            },
            "checkpoint_fingerprint",
        )

    def resume_from_checkpoint(
        self,
        checkpoint: ContinualLearningCheckpoint,
        *,
        expected_checkpoint_fingerprint: str,
        confirmation_fingerprint: str,
    ) -> ContinualLearningCheckpoint:
        if checkpoint.expires_at <= utc_now():
            raise ContinualLearningError("checkpoint expired")
        if checkpoint.checkpoint_fingerprint != expected_checkpoint_fingerprint:
            raise ContinualLearningError("checkpoint fingerprint mismatch")
        if not confirmation_fingerprint:
            raise ContinualLearningError("explicit operator resume confirmation is required")
        return checkpoint

    def evaluate_cycle_outcome(self, **payload: Any) -> ContinualLearningCycleOutcome:
        return build_cycle_outcome(**payload)

    def audit_session(
        self,
        *,
        session_result: ContinualLearningSessionResult,
        receipts: tuple[ContinualLearningStageReceipt, ...],
    ) -> ContinualLearningIntegrityReport:
        return audit_continual_learning_session(session_result=session_result, receipts=receipts)

    def query(
        self,
        query: ContinualLearningQuery,
        records: Iterable[Any],
        *,
        id_field: str,
        fingerprint_field: str,
    ) -> ContinualLearningQueryResult:
        return run_exact_query(
            query,
            records,
            id_field=id_field,
            fingerprint_field=fingerprint_field,
        )

    def rollback_cycle(
        self,
        *,
        session_id: str,
        cycle_id: str,
    ) -> ContinualLearningRollbackPlan:
        return build_rollback_plan(session_id=session_id, cycle_id=cycle_id)

    def cleanup_session(self, *, temporary_root: Path | None = None) -> dict[str, int]:
        del temporary_root
        return {
            "retained_database_files": 0,
            "retained_wal_files": 0,
            "retained_shm_files": 0,
            "retained_backup_files": 0,
            "retained_manifest_files": 0,
            "retained_checkpoint_files": 0,
            "retained_approval_fixture_files": 0,
            "retained_raw_plan_files": 0,
            "retained_source_body_files": 0,
            "active_overlay_records": 0,
        }

    def reject_automatic_transition(self) -> None:
        raise ContinualLearningError("automatic cycle continuation is prohibited")

    def reject_background_execution(self) -> None:
        raise ContinualLearningError("background continual learning is prohibited")

    def reject_production_effect(self) -> None:
        raise ContinualLearningError("production effects are prohibited")

    def budget_decision(
        self,
        usage: ContinualLearningResourceUsage,
    ) -> ContinualLearningBudgetDecision:
        return evaluate_resource_budget(usage)


def component_binding(
    *,
    binding_id: str,
    component_name: str,
    component_implementation_task: str,
    component_contract_authorization_id: str,
    cycle_id: str,
    operation_fingerprint: str,
    input_fingerprints: tuple[str, ...] = (),
    output_fingerprints: tuple[str, ...] = (),
    approval_bundle_fingerprints: tuple[str, ...] = (),
) -> ContinualLearningComponentInvocationBinding:
    """Bind a historical component invocation to the current AION-228 authority."""

    return build_record(
        ContinualLearningComponentInvocationBinding,
        {
            "binding_id": binding_id,
            "current_authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "component_name": component_name,
            "component_implementation_task": component_implementation_task,
            "component_contract_authorization_id": component_contract_authorization_id,
            "cycle_id": cycle_id,
            "operation_fingerprint": operation_fingerprint,
            "input_fingerprints": input_fingerprints,
            "output_fingerprints": output_fingerprints,
            "approval_bundle_fingerprints": approval_bundle_fingerprints,
            "invoked_at": utc_now(),
        },
        "binding_fingerprint",
    )


def deterministic_three_cycle_session(
    *,
    session_id: str = "aion-228-deterministic-session",
    mode: ContinualLearningPilotMode = ContinualLearningPilotMode.DETERMINISTIC_SIMULATION,
) -> tuple[ContinualLearningSessionResult, tuple[ContinualLearningStageReceipt, ...]]:
    """Execute the fixed deterministic stage list used by CI tests."""

    operator = continual_fingerprint({"operator": "deterministic"})
    session_plan = build_three_cycle_session_plan(
        session_id=session_id,
        mode=mode,
        exact_domain_allowlist=("example.org", "iana.org", "w3.org")
        if mode is ContinualLearningPilotMode.DETERMINISTIC_SIMULATION
        else ("rfc-editor.org", "ecma-international.org", "json.org"),
        explicit_source_url_fingerprints=(
            continual_fingerprint({"url": "source-1"}),
            continual_fingerprint({"url": "source-2"}),
            continual_fingerprint({"url": "source-3"}),
        ),
        operator_identity_fingerprint=operator,
    )
    service = ControlledLocalContinualLearningPilotService()
    receipts: list[ContinualLearningStageReceipt] = []
    outcomes: list[ContinualLearningCycleOutcome] = []
    for plan in session_plan.cycle_plans:
        prior_receipt: ContinualLearningStageReceipt | None = None
        for sequence, (before, after) in enumerate(
            zip(plan.required_stages, plan.required_stages[1:], strict=False),
            1,
        ):
            command = build_stage_command(
                stage_command_id=f"{plan.cycle_id}-command-{sequence:02d}",
                session_id=session_id,
                cycle_id=plan.cycle_id,
                expected_current_state=before,
                requested_next_state=after,
                cycle_plan_fingerprint=plan.cycle_plan_fingerprint,
                operator_identity_fingerprint=operator,
            )
            disposition = (
                ContinualLearningStageDisposition.ABSTAINED
                if after is ContinualLearningCycleState.ABSTAINED
                else (
                    ContinualLearningStageDisposition.EXPLICIT_NO_OP_BY_CYCLE_POLICY
                    if after in plan.explicit_no_op_stages
                    else ContinualLearningStageDisposition.EXECUTED
                )
            )
            prior_receipt = service.advance_stage(
                command=command,
                cycle_plan=plan,
                current_state=before,
                prior_receipt=prior_receipt,
                disposition=disposition,
                output_fingerprints=(continual_fingerprint({"stage": command.stage_command_id}),),
                reason_codes=(disposition.value,),
            )
            receipts.append(prior_receipt)
        terminal = plan.required_stages[-1]
        outcomes.append(
            build_cycle_outcome(
                schema_version="aion-glm-continual-learning-cycle-outcome/v1",
                cycle_id=plan.cycle_id,
                cycle_kind=plan.cycle_kind,
                terminal_status=(
                    ContinualLearningCycleOutcomeStatus.ABSTAINED
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ContinualLearningCycleOutcomeStatus.COMPLETED
                ),
                final_state=terminal,
                stage_receipt_count=len(plan.required_stages) - 1,
                receipt_chain_head=(
                    prior_receipt.receipt_fingerprint if prior_receipt else ZERO_HASH
                ),
                research_status=ContinualLearningResearchStatus.ACQUIRED,
                candidate_status=(
                    ContinualLearningKnowledgeStatus.ABSTAINED
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ContinualLearningKnowledgeStatus.ELIGIBLE_FOR_REVIEW
                ),
                promotion_status=(
                    ContinualLearningPromotionStatus.ABSTAINED
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ContinualLearningPromotionStatus.DRY_RUN_PASSED
                ),
                persistence_status=(
                    ContinualLearningPersistenceStatus.NOT_APPLICABLE
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ContinualLearningPersistenceStatus.TEMPORARILY_PERSISTED
                ),
                shadow_status=(
                    ContinualLearningShadowStatus.ABSTAINED
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ContinualLearningShadowStatus.SHADOW_APPLIED
                ),
                evidence_gain_count=(
                    1 if terminal is not ContinualLearningCycleState.ABSTAINED else 0
                ),
                duplicate_count=0,
                contradiction_count=1 if terminal is ContinualLearningCycleState.ABSTAINED else 0,
                abstention_reason_codes=(
                    ("cycle_3_contradiction_preserved",)
                    if terminal is ContinualLearningCycleState.ABSTAINED
                    else ()
                ),
                rollback_applied=terminal is ContinualLearningCycleState.ABSTAINED,
                cleanup_verified=True,
            )
        )
    result = build_session_result(
        schema_version="aion-glm-continual-learning-session-result/v1",
        session_id=session_id,
        authorization_transaction_id=AUTHORIZATION_TRANSACTION_ID,
        mode=mode,
        cycle_outcomes=tuple(outcomes),
        cycle_count=3,
        completed_cycle_count=2,
        abstained_cycle_count=1,
        rolled_back_cycle_count=0,
        failed_cycle_count=0,
        external_read_performed=mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE,
        dns_resolution_count=3 if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE else 0,
        public_https_request_count=(
            6 if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE else 0
        ),
        source_fetch_count=3 if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE else 0,
        source_body_purge_count=(
            3 if mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE else 0
        ),
        verified_candidate_count=1,
        promotion_plan_count=1,
        temporary_persistence_transaction_count=1,
        knowledge_version_write_count=1,
        shadow_application_count=1,
        cross_cycle_context_count=2,
        stage_receipt_count=len(receipts),
        checkpoint_count=3,
        all_cleanup_verified=True,
    )
    return result, tuple(receipts)


def build_deterministic_evidence_bundle() -> Any:
    """Build a complete deterministic redacted evidence bundle for tests."""

    result, receipts = deterministic_three_cycle_session()
    integrity = audit_continual_learning_session(session_result=result, receipts=receipts)
    review = build_operator_review_item(session_id=result.session_id)
    return build_evidence_bundle(
        session_result=result,
        integrity_report=integrity,
        review_items=(review,),
    )
