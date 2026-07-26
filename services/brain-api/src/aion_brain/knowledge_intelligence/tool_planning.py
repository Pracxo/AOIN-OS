"""Deterministic tool intent, candidate, and plan construction."""

from __future__ import annotations

from aion_brain.contracts.knowledge_tool_verification import (
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ToolCandidate,
    ToolCapabilityManifest,
    ToolCompensationPlan,
    ToolEffectType,
    ToolExpectedEffect,
    ToolForbiddenEffect,
    ToolIntent,
    ToolInvocationPlan,
    ToolManifestRegistrySnapshot,
    ToolOperationClass,
    ToolPlanStep,
    ToolPostcondition,
    ToolPrecondition,
    ToolRiskClass,
    ToolRollbackPlan,
    ToolVerificationError,
    VerifierRole,
    risk_lte,
    risk_requires_extra_verification,
    tool_candidate_fingerprint,
    tool_compensation_fingerprint,
    tool_condition_fingerprint,
    tool_intent_fingerprint,
    tool_plan_fingerprint,
    tool_plan_step_fingerprint,
    tool_rollback_fingerprint,
)
from aion_brain.knowledge_intelligence.tool_effects import (
    build_expected_effect,
    default_forbidden_runtime_effects,
)


def build_tool_intent(
    *,
    intent_id: str = "intent-aion-215-001",
    case_id: str = "case-001",
    claim_ids: tuple[str, ...] = ("claim-001",),
    epistemic_assessment_ids: tuple[str, ...] = ("assessment-001",),
    mesh_synthesis_id: str = "mesh-synthesis-001",
    requested_tool_ids: tuple[str, ...] = (),
    required_operation_classes: tuple[ToolOperationClass, ...] = (
        ToolOperationClass.DETERMINISTIC_VALIDATOR,
    ),
    expected_effects: tuple[ToolExpectedEffect, ...] | None = None,
    forbidden_effects: tuple[ToolForbiddenEffect, ...] | None = None,
    max_risk_class: ToolRiskClass = ToolRiskClass.LOW,
    input_payload: dict[str, object] | None = None,
    idempotency_key: str = "idempotency-aion-215-001",
) -> ToolIntent:
    """Build a fingerprinted explicit tool intent."""

    payload = {
        "schema_version": "aion-knowledge-tool-intent/v1",
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "intent_id": intent_id,
        "case_id": case_id,
        "claim_ids": claim_ids,
        "epistemic_assessment_ids": epistemic_assessment_ids,
        "mesh_synthesis_id": mesh_synthesis_id,
        "requested_tool_ids": requested_tool_ids,
        "required_operation_classes": required_operation_classes,
        "expected_effects": expected_effects
        or (
            build_expected_effect(
                effect_id=f"effect-{intent_id}-validate",
                effect_type=ToolEffectType.VALIDATE,
                effect_scope="synthetic-artifact",
                artifact_id=f"artifact-{intent_id}",
            ),
        ),
        "forbidden_effects": forbidden_effects or default_forbidden_runtime_effects(),
        "max_risk_class": max_risk_class,
        "input_payload": input_payload
        or {
            "artifact_kind": "knowledge-intelligence-tool-verification-fixture",
            "content_fingerprint": "0" * 64,
            "case_id": case_id,
        },
        "idempotency_key": idempotency_key,
        "operator_review_required": True,
        "explicit_abstention_supported": True,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "actual_tool_executed": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolIntent.model_validate(
        {**payload, "intent_fingerprint": tool_intent_fingerprint(payload)}
    )


def _manifest_matches_intent(manifest: ToolCapabilityManifest, intent: ToolIntent) -> bool:
    if intent.requested_tool_ids and manifest.tool_id not in intent.requested_tool_ids:
        return False
    if manifest.operation_class not in intent.required_operation_classes:
        return False
    if not risk_lte(manifest.risk_class, intent.max_risk_class):
        return False
    manifest_effect_types = {item.effect_type for item in manifest.declared_effects}
    expected_effect_types = {item.effect_type for item in intent.expected_effects}
    if not expected_effect_types.issubset(manifest_effect_types):
        return False
    forbidden_types = {item.effect_type for item in intent.forbidden_effects}
    if manifest_effect_types & forbidden_types:
        return False
    return True


def enumerate_eligible_tool_candidates(
    intent: ToolIntent,
    registry: ToolManifestRegistrySnapshot,
) -> tuple[ToolCandidate, ...]:
    """Enumerate eligible tool candidates deterministically from exact requirements."""

    eligible_manifests = tuple(
        manifest
        for manifest in sorted(
            registry.manifests, key=lambda item: (item.tool_id, item.manifest_id)
        )
        if _manifest_matches_intent(manifest, intent)
    )
    candidates: list[ToolCandidate] = []
    for index, manifest in enumerate(eligible_manifests, start=1):
        payload = {
            "schema_version": "aion-knowledge-tool-candidate/v1",
            "candidate_id": f"candidate-{intent.intent_id}-{index:03d}",
            "intent_id": intent.intent_id,
            "manifest_id": manifest.manifest_id,
            "tool_id": manifest.tool_id,
            "risk_class": manifest.risk_class,
            "eligible": True,
            "candidate_rank": index,
            "matched_effect_types": tuple(
                sorted({item.effect_type for item in manifest.declared_effects}, key=str)
            ),
            "reason_codes": ("tool_candidate_eligible",),
        }
        candidates.append(
            ToolCandidate.model_validate(
                {**payload, "candidate_fingerprint": tool_candidate_fingerprint(payload)}
            )
        )
    return tuple(candidates)


def select_tool_candidate(candidates: tuple[ToolCandidate, ...]) -> ToolCandidate:
    """Select the first deterministic eligible candidate."""

    for candidate in sorted(candidates, key=lambda item: (item.candidate_rank, item.tool_id)):
        if candidate.eligible:
            return candidate
    raise ToolVerificationError("no eligible synthetic tool candidate")


def required_verifier_roles_for_risk(risk_class: ToolRiskClass) -> tuple[VerifierRole, ...]:
    """Return mandatory independent verifier roles for the risk class."""

    base = (
        VerifierRole.SCHEMA,
        VerifierRole.POLICY,
        VerifierRole.EFFECT,
        VerifierRole.PROVENANCE,
        VerifierRole.DETERMINISM,
    )
    if not risk_requires_extra_verification(risk_class):
        return base
    return base + (
        VerifierRole.SAFETY,
        VerifierRole.ROLLBACK,
        VerifierRole.RESOURCE,
    )


def _precondition(condition_id: str, check_name: str, reason_code: str) -> ToolPrecondition:
    payload = {
        "condition_id": condition_id,
        "check_name": check_name,
        "satisfied": True,
        "reason_codes": (reason_code,),
    }
    return ToolPrecondition.model_validate(
        {**payload, "condition_fingerprint": tool_condition_fingerprint(payload)}
    )


def _postcondition(condition_id: str, check_name: str, reason_code: str) -> ToolPostcondition:
    payload = {
        "condition_id": condition_id,
        "check_name": check_name,
        "satisfied": True,
        "reason_codes": (reason_code,),
    }
    return ToolPostcondition.model_validate(
        {**payload, "condition_fingerprint": tool_condition_fingerprint(payload)}
    )


def _rollback_plan(step_id: str) -> ToolRollbackPlan:
    payload = {
        "rollback_id": f"rollback-{step_id}",
        "step_ids": (step_id,),
        "available": True,
        "validated": True,
        "requires_actual_execution": False,
        "requires_persistent_write": False,
        "reason_codes": ("tool_rollback_valid",),
    }
    return ToolRollbackPlan.model_validate(
        {**payload, "rollback_fingerprint": tool_rollback_fingerprint(payload)}
    )


def _compensation_plan(step_id: str) -> ToolCompensationPlan:
    payload = {
        "compensation_id": f"compensation-{step_id}",
        "step_ids": (step_id,),
        "available": True,
        "validated": True,
        "requires_actual_execution": False,
        "requires_persistent_write": False,
        "reason_codes": ("tool_compensation_valid",),
    }
    return ToolCompensationPlan.model_validate(
        {**payload, "compensation_fingerprint": tool_compensation_fingerprint(payload)}
    )


def build_tool_plan(
    *,
    intent: ToolIntent,
    registry: ToolManifestRegistrySnapshot,
) -> ToolInvocationPlan:
    """Build a bounded ordered deterministic tool plan."""

    candidates = enumerate_eligible_tool_candidates(intent, registry)
    selected = select_tool_candidate(candidates)
    manifest = next(item for item in registry.manifests if item.manifest_id == selected.manifest_id)
    roles = required_verifier_roles_for_risk(manifest.risk_class)
    step_id = f"step-{intent.intent_id}-001"
    step_payload = {
        "schema_version": "aion-knowledge-tool-plan-step/v1",
        "step_id": step_id,
        "step_order": 1,
        "intent_id": intent.intent_id,
        "manifest_id": manifest.manifest_id,
        "tool_id": manifest.tool_id,
        "operation_class": manifest.operation_class,
        "risk_class": manifest.risk_class,
        "input_payload": intent.input_payload,
        "expected_effects": intent.expected_effects,
        "forbidden_effects": intent.forbidden_effects,
        "preconditions": (
            _precondition(
                f"precondition-{step_id}-schema",
                "input-schema-validated",
                "tool_schema_valid",
            ),
            _precondition(
                f"precondition-{step_id}-permission",
                "permission-envelope-validated",
                "tool_permission_valid",
            ),
            _precondition(
                f"precondition-{step_id}-idempotency",
                "idempotency-key-validated",
                "tool_idempotency_valid",
            ),
        ),
        "postconditions": (
            _postcondition(
                f"postcondition-{step_id}-schema",
                "output-schema-validated",
                "tool_schema_valid",
            ),
            _postcondition(
                f"postcondition-{step_id}-effect",
                "effect-boundary-validated",
                "tool_effect_forbidden_absent",
            ),
        ),
        "idempotency_key": intent.idempotency_key,
        "rollback_plan": _rollback_plan(step_id),
        "compensation_plan": _compensation_plan(step_id),
        "required_verifier_roles": roles,
        "simulation_only": True,
        "actual_execution_enabled": False,
        "actual_tool_executed": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    step = ToolPlanStep.model_validate(
        {**step_payload, "step_fingerprint": tool_plan_step_fingerprint(step_payload)}
    )
    plan_payload = {
        "schema_version": "aion-knowledge-tool-plan/v1",
        "plan_id": f"plan-{intent.intent_id}",
        "intent": intent,
        "candidates": candidates,
        "selected_candidate_id": selected.candidate_id,
        "steps": (step,),
        "required_verifier_roles": roles,
        "reason_codes": ("tool_plan_valid", "tool_candidate_selected"),
        "explicit_abstention_required": True,
        "operator_review_required": True,
        "simulation_only": True,
        "actual_tool_executed": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolInvocationPlan.model_validate(
        {**plan_payload, "plan_fingerprint": tool_plan_fingerprint(plan_payload)}
    )


def validate_tool_plan(plan: ToolInvocationPlan) -> ToolInvocationPlan:
    """Return the plan after model-level validation."""

    return ToolInvocationPlan.model_validate(plan.model_dump(mode="python"))


__all__ = [
    "build_tool_intent",
    "build_tool_plan",
    "enumerate_eligible_tool_candidates",
    "required_verifier_roles_for_risk",
    "select_tool_candidate",
    "validate_tool_plan",
]
