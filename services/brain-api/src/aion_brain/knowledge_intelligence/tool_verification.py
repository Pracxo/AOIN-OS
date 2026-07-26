"""Independent deterministic verification rules for synthetic tool simulations."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.knowledge_tool_verification import (
    ToolFindingSeverity,
    ToolInvocationPlan,
    ToolRiskClass,
    ToolSchemaDescriptor,
    ToolSimulationResult,
    ToolVerificationFinding,
    ToolVerificationResourceUsage,
    ToolVerificationRule,
    ToolVerificationStatus,
    ToolVerifierProfile,
    VerifierRole,
    risk_requires_extra_verification,
    tool_finding_fingerprint,
    tool_verification_rule_fingerprint,
    tool_verifier_profile_fingerprint,
)


def _safe_type_matches(value: object, expected_type: str) -> bool:
    if expected_type == "str":
        return isinstance(value, str)
    if expected_type == "bool":
        return isinstance(value, bool)
    if expected_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "dict":
        return isinstance(value, dict)
    if expected_type == "list":
        return isinstance(value, list)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    return False


def validate_payload_against_schema(
    payload: dict[str, Any],
    schema: ToolSchemaDescriptor,
) -> tuple[bool, tuple[str, ...]]:
    """Validate a payload against a strict descriptor."""

    required = set(schema.required_fields)
    optional = set(schema.optional_fields)
    forbidden = set(schema.forbidden_fields)
    keys = set(payload)
    if required - keys:
        return False, ("tool_schema_invalid",)
    if forbidden & keys:
        return False, ("tool_schema_invalid",)
    if schema.strict and keys - (required | optional):
        return False, ("tool_schema_invalid",)
    for key, expected_type in schema.field_types.items():
        if key in payload and not _safe_type_matches(payload[key], expected_type):
            return False, ("tool_schema_invalid",)
    return True, ("tool_schema_valid",)


def build_default_verifier_profiles() -> tuple[ToolVerifierProfile, ...]:
    """Build independent verifier profiles for every AION-215 verifier role."""

    profiles: list[ToolVerifierProfile] = []
    for role in VerifierRole:
        payload = {
            "schema_version": "aion-knowledge-tool-verifier-profile/v1",
            "profile_id": f"profile-{role.value}",
            "verifier_role": role,
            "independence_group": f"independence-{role.value}",
            "profile_version": "1.0.0",
            "can_execute_tools": False,
            "can_mutate_state": False,
            "synthetic": True,
            "read_only": True,
            "redacted": True,
        }
        profiles.append(
            ToolVerifierProfile.model_validate(
                {**payload, "profile_fingerprint": tool_verifier_profile_fingerprint(payload)}
            )
        )
    return tuple(profiles)


def build_default_verification_rules(
    required_roles: tuple[VerifierRole, ...],
) -> tuple[ToolVerificationRule, ...]:
    """Build deterministic verification rules for the required roles."""

    reason_by_role: dict[VerifierRole, tuple[str, ...]] = {
        VerifierRole.SCHEMA: ("tool_schema_valid",),
        VerifierRole.POLICY: ("tool_permission_valid", "tool_runtime_disabled"),
        VerifierRole.EFFECT: ("tool_effect_expected_matched", "tool_effect_forbidden_absent"),
        VerifierRole.PROVENANCE: ("tool_provenance_preserved",),
        VerifierRole.DETERMINISM: ("tool_artifact_fingerprinted",),
        VerifierRole.SAFETY: ("tool_high_risk_safety_verified",),
        VerifierRole.ROLLBACK: ("tool_high_risk_rollback_verified",),
        VerifierRole.RESOURCE: ("tool_high_risk_resource_verified",),
    }
    rules: list[ToolVerificationRule] = []
    for role in required_roles:
        payload = {
            "schema_version": "aion-knowledge-tool-verification-rule/v1",
            "rule_id": f"rule-{role.value}",
            "verifier_role": role,
            "rule_name": f"{role.value}-rule",
            "required_for_risk_classes": (
                ToolRiskClass.MINIMAL,
                ToolRiskClass.LOW,
                ToolRiskClass.MODERATE,
                ToolRiskClass.HIGH,
                ToolRiskClass.CRITICAL,
            ),
            "reason_codes": reason_by_role[role],
        }
        rules.append(
            ToolVerificationRule.model_validate(
                {**payload, "rule_fingerprint": tool_verification_rule_fingerprint(payload)}
            )
        )
    return tuple(rules)


def _runtime_counters_zero(usage: ToolVerificationResourceUsage) -> bool:
    return all(
        value == 0
        for value in (
            usage.persistent_tool_state_write_batch,
            usage.actual_tool_executions,
            usage.shell_commands,
            usage.subprocess_executions,
            usage.network_calls,
            usage.dns_resolutions,
            usage.browser_actions,
            usage.connector_calls,
            usage.model_provider_calls,
            usage.filesystem_mutations,
            usage.source_mutations,
            usage.git_operations,
            usage.runtime_created_pull_requests,
            usage.approvals_created,
            usage.autonomous_actions,
            usage.high_stakes_actions,
            usage.deployments,
            usage.knowledge_promotions,
            usage.belief_mutations,
            usage.model_weight_changes,
        )
    )


def _role_passes(
    role: VerifierRole,
    *,
    plan: ToolInvocationPlan,
    simulation: ToolSimulationResult,
    usage: ToolVerificationResourceUsage,
) -> tuple[bool, tuple[str, ...]]:
    step = plan.steps[0]
    if role is VerifierRole.SCHEMA:
        input_valid = all(item.satisfied for item in step.preconditions)
        output_valid = all(item.satisfied for item in step.postconditions)
        return input_valid and output_valid, ("tool_schema_valid",)
    if role is VerifierRole.POLICY:
        policy_valid = (
            plan.actual_tool_executed is False
            and plan.persistent_write_applied is False
            and step.actual_execution_enabled is False
            and step.runtime_effect is False
        )
        return policy_valid, ("tool_permission_valid", "tool_runtime_disabled")
    if role is VerifierRole.EFFECT:
        effect_valid = simulation.expected_effects_satisfied and simulation.forbidden_effects_absent
        return effect_valid, ("tool_effect_expected_matched", "tool_effect_forbidden_absent")
    if role is VerifierRole.PROVENANCE:
        provenance_valid = bool(
            plan.intent.case_id
            and plan.intent.claim_ids
            and plan.intent.epistemic_assessment_ids
            and plan.intent.mesh_synthesis_id
            and simulation.output_fingerprint
        )
        return provenance_valid, ("tool_provenance_preserved",)
    if role is VerifierRole.DETERMINISM:
        artifact_valid = bool(simulation.artifacts) and all(
            item.artifact_fingerprint for item in simulation.artifacts
        )
        return artifact_valid, ("tool_artifact_fingerprinted",)
    if role is VerifierRole.SAFETY:
        safety_valid = (
            simulation.actual_tool_executed is False
            and simulation.runtime_effect is False
            and plan.intent.operator_review_required is True
        )
        return safety_valid, ("tool_high_risk_safety_verified",)
    if role is VerifierRole.ROLLBACK:
        rollback_valid = step.rollback_plan.validated and step.compensation_plan.validated
        return rollback_valid, ("tool_high_risk_rollback_verified",)
    if role is VerifierRole.RESOURCE:
        return _runtime_counters_zero(usage), ("tool_high_risk_resource_verified",)
    return False, ("tool_plan_invalid",)


def verify_tool_plan_and_simulation(
    *,
    plan: ToolInvocationPlan,
    simulation: ToolSimulationResult,
    profiles: tuple[ToolVerifierProfile, ...],
    rules: tuple[ToolVerificationRule, ...],
    usage: ToolVerificationResourceUsage,
) -> tuple[ToolVerificationFinding, ...]:
    """Apply independent verifier rules and return immutable findings."""

    required_roles = plan.required_verifier_roles
    if risk_requires_extra_verification(plan.steps[0].risk_class):
        required_roles = tuple(dict.fromkeys(required_roles))
    profile_by_role = {profile.verifier_role: profile for profile in profiles}
    rule_by_role = {rule.verifier_role: rule for rule in rules}
    groups = [
        profile_by_role[role].independence_group
        for role in required_roles
        if role in profile_by_role
    ]
    independence_ok = len(groups) == len(set(groups)) and len(groups) == len(required_roles)
    findings: list[ToolVerificationFinding] = []
    for index, role in enumerate(required_roles, start=1):
        profile = profile_by_role.get(role)
        rule = rule_by_role.get(role)
        reason_codes: tuple[str, ...]
        if profile is None or rule is None:
            passed = False
            reason_codes = ("tool_verifier_independence_missing",)
        else:
            passed, reason_codes = _role_passes(role, plan=plan, simulation=simulation, usage=usage)
            if not independence_ok:
                passed = False
                reason_codes = ("tool_verifier_independence_missing",)
        status = (
            ToolVerificationStatus.VERIFICATION_PASSED
            if passed
            else ToolVerificationStatus.VERIFICATION_FAILED
        )
        payload = {
            "schema_version": "aion-knowledge-tool-verification-finding/v1",
            "finding_id": f"finding-{plan.plan_id}-{index:03d}",
            "plan_id": plan.plan_id,
            "simulation_id": simulation.simulation_id,
            "verifier_profile_id": profile.profile_id if profile else "profile-missing",
            "verifier_role": role,
            "rule_id": rule.rule_id if rule else "rule-missing",
            "status": status,
            "severity": ToolFindingSeverity.INFO if passed else ToolFindingSeverity.ERROR,
            "passed": passed,
            "abstained": False,
            "reason_codes": reason_codes,
            "evidence_fingerprint": simulation.simulation_fingerprint,
            "actual_execution_verified": False,
            "approval_created": False,
            "knowledge_promoted": False,
            "belief_mutated": False,
            "runtime_effect": False,
        }
        findings.append(
            ToolVerificationFinding.model_validate(
                {**payload, "finding_fingerprint": tool_finding_fingerprint(payload)}
            )
        )
    return tuple(findings)


__all__ = [
    "build_default_verification_rules",
    "build_default_verifier_profiles",
    "validate_payload_against_schema",
    "verify_tool_plan_and_simulation",
]
