from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.guardrails import GuardrailDecision
from aion_brain.contracts.identity_assertion import assertion_fingerprint
from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.contracts.secure_runtime import (
    AUTHORIZATION_TRANSACTION_ID,
    CLOSED_CAPABILITY_CODES,
    ZERO_FINGERPRINT,
    ControlledLocalSecureRuntimeService,
    InMemorySecureRuntimeAuditLedger,
    SecureActorContextBinding,
    SecureApprovalEvidence,
    SecureApprovalEvidenceBundle,
    SecureCapabilityInvocationPlan,
    SecureOperatorIdentityBinding,
    SecureRequestIdentityBinding,
    SecureRuntimeAuthorizationEnvelope,
    SecureRuntimeGuardDecision,
    SecureRuntimeIntegrityStatus,
    SecureRuntimeKillSwitch,
    SecureRuntimeKillSwitchState,
    SecureRuntimeKillSwitchStatus,
    SecureRuntimeRequestEnvelope,
    SecureRuntimeSession,
    SecureRuntimeSessionCheckpoint,
    SecureRuntimeSessionPlan,
    SecureRuntimeSessionResult,
    SecureRuntimeSessionState,
    SecureRuntimeStageCommand,
    SecureSideEffectBudget,
    SecureSideEffectBudgetDecision,
    SecureSideEffectUsage,
    SecureSimulatedDispatchResult,
    bind_guardrail_decision,
    bind_policy_decision,
    bind_risk_assessment,
    bind_secure_actor_context,
    bind_secure_request_identity,
    bind_verified_local_operator_identity,
    create_capability_plan,
    evaluate_side_effect_budget,
    local_operator_confirmation_fingerprint,
    secure_runtime_fingerprint,
    text_fingerprint,
)
from aion_brain.production_auth.identity_assertion_pipeline import (
    OfflineIdentityAssertionVerificationPipeline,
)
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from aion_brain.production_auth.identity_assertion_replay_service import (
    IdentityAssertionReplayProtectionService,
)
from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import (
    make_envelope,
    make_key_pair,
    make_payload,
    make_policy,
)
from tests.test_identity_assertion_replay_contracts import memory_engine

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
SESSION_ID = "session-AION-231"
REQUEST_ID = "request-AION-231"
TRACE_ID = "trace-AION-231"
CORRELATION_ID = "correlation-AION-231"
ALLOWED_ROLES = ("operator", "viewer")
ALLOWED_PERMISSIONS = (
    "brain:think:simulate",
    "secure_runtime:audit:read",
    "secure_runtime:fixture:replay",
    "secure_runtime:read",
)
ALLOWED_SCOPES = (
    "secure-runtime:audit",
    "secure-runtime:fixture-replay",
    "secure-runtime:health",
    "secure-runtime:observability",
    "secure-runtime:simulate-capability",
)


@dataclass(frozen=True)
class SecureRuntimeFixture:
    authorization: SecureRuntimeAuthorizationEnvelope
    pipeline: OfflineIdentityAssertionVerificationPipeline
    assertion_envelope: object
    operator_identity: SecureOperatorIdentityBinding
    request_identity: SecureRequestIdentityBinding
    actor_context: SecureActorContextBinding
    side_effect_budget: SecureSideEffectBudget
    kill_switch_state: SecureRuntimeKillSwitchState
    kill_switch: SecureRuntimeKillSwitch
    session_plan: SecureRuntimeSessionPlan
    session: SecureRuntimeSession
    request: SecureRuntimeRequestEnvelope
    capability_plan: SecureCapabilityInvocationPlan
    policy_binding: object
    risk_binding: object
    guardrail_binding: object
    approval_evidence: SecureApprovalEvidence
    approval_bundle: SecureApprovalEvidenceBundle
    usage: SecureSideEffectUsage
    budget_decision: SecureSideEffectBudgetDecision
    guard_decision: SecureRuntimeGuardDecision
    dispatch: SecureSimulatedDispatchResult
    checkpoint: SecureRuntimeSessionCheckpoint
    service: ControlledLocalSecureRuntimeService
    audit_ledger: InMemorySecureRuntimeAuditLedger


def build_identity_pipeline() -> tuple[
    OfflineIdentityAssertionVerificationPipeline,
    object,
]:
    signing_material, public_key = make_key_pair(
        active_from=NOW - timedelta(minutes=5),
        active_until=NOW + timedelta(minutes=30),
    )
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    replay_service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )
    return (
        OfflineIdentityAssertionVerificationPipeline(
            verifier=verifier,
            replay_protection=replay_service,
            clock=lambda: NOW,
        ),
        signing_material,
    )


def make_authorization(assertion: object) -> SecureRuntimeAuthorizationEnvelope:
    payload = assertion.payload
    return SecureRuntimeAuthorizationEnvelope(
        session_id=SESSION_ID,
        operator_identity_fingerprint=text_fingerprint("operator_identity", payload.subject),
        assertion_fingerprint=assertion_fingerprint(payload) or "",
        expected_issuer=payload.issuer,
        expected_audience=payload.audience,
        allowed_workspace_id=payload.workspace_id or "",
        allowed_roles=ALLOWED_ROLES,
        allowed_permissions=ALLOWED_PERMISSIONS,
        allowed_security_scopes=ALLOWED_SCOPES,
        allowed_capability_codes=CLOSED_CAPABILITY_CODES,
        maximum_requests=100,
        maximum_concurrent_requests=4,
        maximum_session_seconds=3600,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
        confirmation_fingerprint=local_operator_confirmation_fingerprint(),
    )


def make_signed_assertion(signing_material: object) -> object:
    payload = make_payload(
        assertion_id="assertion-AION-231",
        subject="operator-subject-AION-231",
        actor_id="operator-AION-231",
        workspace_id="workspace-AION-231",
        roles=ALLOWED_ROLES,
        permissions=ALLOWED_PERMISSIONS,
        security_scope=ALLOWED_SCOPES,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + timedelta(minutes=5),
        metadata={"purpose": "aion-231-test"},
    )
    return make_envelope(signing_material, payload)


def secure_runtime_fixture() -> SecureRuntimeFixture:
    pipeline, signing_material = build_identity_pipeline()
    assertion = make_signed_assertion(signing_material)
    authorization = make_authorization(assertion)
    operator_identity = bind_verified_local_operator_identity(
        authorization_envelope=authorization,
        assertion_envelope=assertion,
        verification_pipeline=pipeline,
    )
    request_identity = bind_secure_request_identity(
        authorization_envelope=authorization,
        operator_identity_binding=operator_identity,
        assertion_envelope=assertion,
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
        correlation_id=CORRELATION_ID,
        created_at=NOW,
    )
    actor_context = bind_secure_actor_context(
        request_identity_binding=request_identity,
        allowed_roles=ALLOWED_ROLES,
        allowed_permissions=ALLOWED_PERMISSIONS,
        allowed_security_scopes=ALLOWED_SCOPES,
        created_at=NOW,
    )
    side_effect_budget = SecureSideEffectBudget()
    kill_switch_state = SecureRuntimeKillSwitchState(
        session_id=SESSION_ID,
        status=SecureRuntimeKillSwitchStatus.clear,
        reason_code="operator_clear",
        activation_fingerprint=ZERO_FINGERPRINT,
        operator_identity_fingerprint=operator_identity.operator_identity_fingerprint,
        created_at=NOW,
    )
    kill_switch = SecureRuntimeKillSwitch(kill_switch_state)
    session_plan = SecureRuntimeSessionPlan(
        session_plan_id="session-plan-AION-231",
        authorization_envelope=authorization,
        operator_identity_binding_fingerprint=operator_identity.binding_fingerprint or "",
        request_identity_binding_fingerprint=request_identity.binding_fingerprint or "",
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        allowed_capability_codes=CLOSED_CAPABILITY_CODES,
        side_effect_budget=side_effect_budget,
        initial_kill_switch_fingerprint=kill_switch_state.state_fingerprint or "",
        maximum_requests=100,
        maximum_concurrent_requests=4,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
    )
    service = ControlledLocalSecureRuntimeService()
    session = service.start_session(session_plan)
    request = SecureRuntimeRequestEnvelope(
        request_envelope_id="request-envelope-AION-231",
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
        correlation_id=CORRELATION_ID,
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        capability_code="brain.think.simulate",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-231",
        requested_permissions=("brain:think:simulate",),
        requested_security_scopes=("secure-runtime:simulate-capability",),
        safe_payload_fingerprint=secure_runtime_fingerprint({"payload": "redacted"}),
        metadata_fingerprint=secure_runtime_fingerprint({"metadata": "redacted"}),
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )
    capability_plan = create_capability_plan(
        request=request,
        side_effect_budget=side_effect_budget,
        created_at=NOW,
    )
    policy_decision = PolicyDecision(
        decision_id="policy-decision-AION-231",
        trace_id=TRACE_ID,
        allow=True,
        approval_required=True,
        reason="approved_for_simulation",
        constraints=["simulation_only"],
        audit_level="medium",
    )
    policy_binding = bind_policy_decision(
        plan=capability_plan,
        decision=policy_decision,
        created_at=NOW,
    )
    risk_assessment = RiskAssessment(
        risk_assessment_id="risk-assessment-AION-231",
        trace_id=TRACE_ID,
        actor_id="operator-AION-231",
        workspace_id="workspace-AION-231",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-231",
        requested_risk_level="medium",
        computed_risk_level="medium",
        risk_score=0.45,
        factors=[{"factor": "simulation_only", "weight": 0.0}],
        constraints=["approval_required"],
        decision="require_approval",
        metadata={"approval_present": True},
        created_at=NOW,
    )
    risk_binding = bind_risk_assessment(
        plan=capability_plan,
        assessment=risk_assessment,
        created_at=NOW,
    )
    guardrail_decision = GuardrailDecision(
        guardrail_decision_id="guardrail-decision-AION-231",
        trace_id=TRACE_ID,
        risk_assessment_id="risk-assessment-AION-231",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-231",
        matched_guardrails=[],
        allow=True,
        approval_required=False,
        blocked=False,
        severity="medium",
        reason="guardrails_allow_simulation",
        constraints=[],
        metadata={},
        created_at=NOW,
    )
    guardrail_binding = bind_guardrail_decision(
        plan=capability_plan,
        decision=guardrail_decision,
        created_at=NOW,
    )
    approval_request = ApprovalRequest(
        approval_request_id="approval-request-AION-231",
        trace_id=TRACE_ID,
        actor_id="operator-AION-231",
        workspace_id="workspace-AION-231",
        requested_by="operator-AION-231",
        assigned_to="reviewer-AION-231",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id=capability_plan.plan_fingerprint,
        title="AION-231 simulation approval",
        description="Allow one local simulation-only secure runtime dispatch.",
        risk_assessment_id="risk-assessment-AION-231",
        guardrail_decision_id="guardrail-decision-AION-231",
        status="approved",
        priority="normal",
        approval_scope=["secure-runtime:simulate-capability"],
        payload={"plan_fingerprint": capability_plan.plan_fingerprint},
        constraints=["simulation_only"],
        expires_at=NOW + timedelta(minutes=10),
        created_at=NOW,
        updated_at=NOW,
        resolved_at=NOW,
    )
    approval_decision = ApprovalDecision(
        approval_decision_id="approval-decision-AION-231",
        approval_request_id="approval-request-AION-231",
        trace_id=TRACE_ID,
        decided_by="reviewer-AION-231",
        decision="approve",
        reason="existing_approval_for_simulation",
        decision_payload={"plan_fingerprint": capability_plan.plan_fingerprint},
        created_at=NOW,
    )
    approval_evidence = service.validate_approval_evidence(
        approval_request=approval_request,
        approval_decision=approval_decision,
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        capability_code="brain.think.simulate",
        capability_plan_fingerprint=capability_plan.plan_fingerprint or "",
        actor_context_fingerprint=actor_context.actor_context_fingerprint,
        policy_binding_fingerprint=policy_binding.binding_fingerprint or "",
        risk_binding_fingerprint=risk_binding.binding_fingerprint or "",
        guardrail_binding_fingerprint=guardrail_binding.binding_fingerprint or "",
        side_effect_budget_fingerprint=side_effect_budget.budget_fingerprint or "",
        now=NOW,
    )
    approval_bundle = SecureApprovalEvidenceBundle(
        bundle_id="approval-bundle-AION-231",
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        capability_code="brain.think.simulate",
        approval_required=True,
        evidence=(approval_evidence,),
        created_at=NOW,
    )
    usage = SecureSideEffectUsage(
        local_operator_sessions=1,
        session_seconds=60,
        requests=1,
        concurrent_requests=1,
        capability_plans_per_request=1,
        capability_invocations_per_session=1,
        policy_decisions_per_request=1,
        risk_assessments_per_request=1,
        guardrail_decisions_per_request=1,
        approval_evidence_records_per_request=1,
        stage_receipts_per_session=1,
        audit_records_per_session=1,
        telemetry_events_per_session=1,
        operator_review_items_per_session=1,
        response_bytes_per_request=128,
        session_checkpoints=1,
        replay_validations_per_request=1,
        kill_switch_checks_per_request=3,
    )
    budget_decision = evaluate_side_effect_budget(
        budget=side_effect_budget,
        usage=usage,
        created_at=NOW,
    )
    guard_decision = service.evaluate_runtime_guard(
        authorization_envelope=authorization,
        operator_identity_binding=operator_identity,
        request_identity_binding=request_identity,
        actor_context_binding=actor_context,
        session=session,
        request=request,
        capability_plan=capability_plan,
        policy_binding=policy_binding,
        risk_binding=risk_binding,
        guardrail_binding=guardrail_binding,
        approval_bundle=approval_bundle,
        side_effect_budget_decision=budget_decision,
        kill_switch_state=kill_switch_state,
        created_at=NOW,
    )
    dispatch = service.simulate_dispatch(
        guard_decision=guard_decision,
        capability_plan=capability_plan,
        created_at=NOW,
    )
    checkpoint = service.create_checkpoint(
        session=session,
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        kill_switch_fingerprint=kill_switch_state.state_fingerprint or "",
        budget_usage_fingerprint=usage.usage_fingerprint or "",
    )
    return SecureRuntimeFixture(
        authorization=authorization,
        pipeline=pipeline,
        assertion_envelope=assertion,
        operator_identity=operator_identity,
        request_identity=request_identity,
        actor_context=actor_context,
        side_effect_budget=side_effect_budget,
        kill_switch_state=kill_switch_state,
        kill_switch=kill_switch,
        session_plan=session_plan,
        session=session,
        request=request,
        capability_plan=capability_plan,
        policy_binding=policy_binding,
        risk_binding=risk_binding,
        guardrail_binding=guardrail_binding,
        approval_evidence=approval_evidence,
        approval_bundle=approval_bundle,
        usage=usage,
        budget_decision=budget_decision,
        guard_decision=guard_decision,
        dispatch=dispatch,
        checkpoint=checkpoint,
        service=service,
        audit_ledger=service.audit_ledger,
    )


def pilot_evidence_payload() -> dict[str, object]:
    fixture = secure_runtime_fixture()
    second = fixture.pipeline.verify_once(fixture.assertion_envelope)
    session = fixture.session
    for next_state in (
        SecureRuntimeSessionState.authorized,
        SecureRuntimeSessionState.identity_assertion_verified,
        SecureRuntimeSessionState.request_identity_bound,
        SecureRuntimeSessionState.actor_context_bound,
        SecureRuntimeSessionState.replay_validation_passed,
        SecureRuntimeSessionState.runtime_guard_ready,
        SecureRuntimeSessionState.session_active,
    ):
        command = SecureRuntimeStageCommand(
            command_id=f"command-{next_state.value}",
            session_id=SESSION_ID,
            expected_current_state=session.current_state,
            requested_next_state=next_state,
            session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
            input_fingerprints=(fixture.session_plan.plan_fingerprint or "",),
            operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
            created_at=NOW,
            expires_at=fixture.authorization.expires_at,
        )
        fixture.service.validate_stage_command(
            session=session,
            command=command,
            kill_switch_state=fixture.service.check_kill_switch(fixture.kill_switch),
            now=NOW,
        )
        fixture.service.advance_stage(session=session, command=command)
        session = fixture.service.repository.session_by_id(SESSION_ID) or session
    fixture.service.validate_request(fixture.request)
    session = fixture.service.repository.session_by_id(SESSION_ID) or session
    for next_state in (
        SecureRuntimeSessionState.request_validated,
        SecureRuntimeSessionState.capability_plan_created,
        SecureRuntimeSessionState.policy_evaluated,
        SecureRuntimeSessionState.risk_evaluated,
        SecureRuntimeSessionState.guardrails_evaluated,
        SecureRuntimeSessionState.approval_validated,
        SecureRuntimeSessionState.simulated_dispatch_completed,
        SecureRuntimeSessionState.response_recorded,
    ):
        command = SecureRuntimeStageCommand(
            command_id=f"command-{next_state.value}",
            session_id=SESSION_ID,
            request_id=REQUEST_ID,
            expected_current_state=session.current_state,
            requested_next_state=next_state,
            session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
            input_fingerprints=(fixture.request.request_fingerprint or "",),
            operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
            created_at=NOW,
            expires_at=fixture.authorization.expires_at,
        )
        fixture.service.validate_stage_command(
            session=session,
            command=command,
            kill_switch_state=fixture.service.check_kill_switch(fixture.kill_switch),
            now=NOW,
        )
        fixture.service.advance_stage(
            session=session,
            command=command,
            output_fingerprints=(fixture.dispatch.result_fingerprint or "",)
            if next_state is SecureRuntimeSessionState.simulated_dispatch_completed
            else (),
            decision_fingerprints=(fixture.guard_decision.guard_decision_fingerprint or "",)
            if next_state is SecureRuntimeSessionState.simulated_dispatch_completed
            else (),
        )
        session = fixture.service.repository.session_by_id(SESSION_ID) or session
    fixture.service.record_response(
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        response_fingerprint=fixture.dispatch.result_fingerprint or "",
    )
    session = fixture.service.repository.session_by_id(SESSION_ID) or session
    command = SecureRuntimeStageCommand(
        command_id="command-session_closed",
        session_id=SESSION_ID,
        expected_current_state=session.current_state,
        requested_next_state=SecureRuntimeSessionState.session_closed,
        session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
        input_fingerprints=(fixture.dispatch.result_fingerprint or "",),
        operator_identity_fingerprint=fixture.operator_identity.operator_identity_fingerprint,
        created_at=NOW,
        expires_at=fixture.authorization.expires_at,
    )
    fixture.service.validate_stage_command(
        session=session,
        command=command,
        kill_switch_state=fixture.service.check_kill_switch(fixture.kill_switch),
        now=NOW,
    )
    fixture.service.advance_stage(session=session, command=command)
    closed_repo = fixture.service.repository.close_session(session_id=SESSION_ID, closed_at=NOW)
    fixture.service.repository = closed_repo
    fixture.service.audit_ledger.append(
        session_id=SESSION_ID,
        event_type="session_closed",
        reason_codes=("session_closed",),
    )
    closed_session = fixture.service.repository.session_by_id(SESSION_ID)
    assert closed_session is not None
    result = SecureRuntimeSessionResult(
        result_id="session-result-AION-231",
        session_id=SESSION_ID,
        final_state=SecureRuntimeSessionState.session_closed,
        session_plan_fingerprint=fixture.session_plan.plan_fingerprint or "",
        response_fingerprint=fixture.dispatch.result_fingerprint or "",
        stage_receipt_chain_head=closed_session.latest_receipt_fingerprint,
        audit_chain_head=fixture.audit_ledger.chain_head(SESSION_ID),
        checkpoint_fingerprint=fixture.checkpoint.checkpoint_fingerprint or "",
        active_request_count=len(closed_session.active_request_ids),
        completed_request_count=len(closed_session.completed_request_ids),
        simulated_dispatch_count=1,
        closed_at=NOW,
    )
    receipts = fixture.service.repository.receipts_by_session(SESSION_ID)
    report = {
        "pilot_id": "AION-231-controlled-local-operator-runtime-pilot",
        "authorization_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": "operator_invoked_local",
        "assertion_fingerprint": fixture.operator_identity.assertion_fingerprint,
        "public_key_fingerprint": secure_runtime_fingerprint({"public_key": "redacted"}),
        "operator_identity_fingerprint": fixture.operator_identity.operator_identity_fingerprint,
        "session_plan_fingerprint": fixture.session_plan.plan_fingerprint,
        "session_result_fingerprint": result.result_fingerprint,
        "stage_receipt_chain_head": closed_session.latest_receipt_fingerprint,
        "audit_chain_head": fixture.audit_ledger.chain_head(SESSION_ID),
        "identity_assertions_verified": 1,
        "replay_claims_created": 1,
        "exact_replays_rejected": 1 if second.result.outcome == "replay_detected" else 0,
        "request_identity_bindings": 1,
        "actor_context_bindings": 1,
        "sessions_started": 1,
        "sessions_closed": 1,
        "active_sessions_after_close": 0,
        "requests_processed": 1,
        "active_requests_after_close": 0,
        "capability_plans_created": 1,
        "policy_bindings": 1,
        "risk_bindings": 1,
        "guardrail_bindings": 1,
        "approval_bundles_validated": 1,
        "kill_switch_checks": 16,
        "runtime_guard_allow_simulation_decisions": 1,
        "simulated_dispatches": 1,
        "stage_receipts": len(receipts),
        "audit_records": len(fixture.audit_ledger.records_by_session(SESSION_ID)),
        "checkpoint_count": 1,
        "integrity_passed": True,
        "temporary_files_retained": 0,
        "actual_capability_executions": 0,
        "network_calls": 0,
        "model_provider_calls": 0,
        "connector_calls": 0,
        "tool_executions": 0,
        "shell_commands": 0,
        "subprocess_executions": 0,
        "browser_actions": 0,
        "credentials_persisted": 0,
        "tokens_persisted": 0,
        "session_tokens_issued": 0,
        "modules_activated": 0,
        "production_writes": 0,
        "production_memory_writes": 0,
        "production_policy_mutations": 0,
        "cognitive_memory_writes": 0,
        "belief_creations": 0,
        "belief_mutations": 0,
        "glm_live_executions": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "deployments": 0,
        "model_weight_changes": 0,
        "production_exposure": False,
        "redacted": True,
        "production_effect": False,
        "runtime_effect": False,
    }
    report["report_fingerprint"] = secure_runtime_fingerprint(report)
    assert fixture.budget_decision.allowed is True
    assert fixture.guard_decision.outcome.value == "allow_simulation"
    assert fixture.dispatch.status.value == "simulated"
    assert fixture.usage.prohibited_effects_zero() is True
    assert SecureRuntimeIntegrityStatus.passed.value == "passed"
    return report
