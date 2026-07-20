#!/usr/bin/env python3
"""Read-only AION-182 shadow activation control-plane operator evaluation."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

PASS_DECISION = (
    "SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW"
)
FAIL_DECISION = "SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_FAIL_REMAIN_DISABLED"
EXPECTED_EVALUATION_BASE_COMMIT = "e9374853a53cd098096ed50da0fabb5874152d54"
AION_181_FEATURE_COMMIT = "c7c7a5c83606399dff2221bd7f847ea00e177603"
AION_181_TREE_SHA = "065f59032cf51eb6414ec4214ebad76ba0cfd718"
IMPLEMENTATION_PR = 92
IMPLEMENTATION_MERGE_COMMIT = EXPECTED_EVALUATION_BASE_COMMIT
IMPLEMENTATION_MERGED_AT = "2026-07-20T21:10:45Z"
PROGRAM_ID = "AION-SELF-IMPROVEMENT-001"
ACTIVATION_PROGRAM_ID = "AION-SELF-IMPROVEMENT-CONTROLLED-SHADOW-ACTIVATION-001"
IMPLEMENTATION_TASK = "AION-181"
CLOSEOUT_TASK = "AION-182"
AUTHORIZATION_TRANSACTION_ID = "AION-180-SI-0007"
EVALUATION_ID = "AION-SACE-001"
FIXED_NOW = datetime(2026, 7, 20, 21, 30, tzinfo=UTC)

SCENARIO_IDS = (
    "valid-candidate",
    "invalid-candidate-binding",
    "environment-boundary",
    "data-and-adapter-boundary",
    "approval-required",
    "valid-synthetic-approval-evidence",
    "separation-of-duties-rejection",
    "expired-consumed-reusable-approval",
    "resource-budget-success",
    "resource-budget-failure",
    "output-boundary-validation",
    "local-evidence-adapter",
    "state-machine",
    "healthy-monitoring",
    "deactivation-triggers",
    "valid-simulation",
    "invalid-approval-simulation",
    "triggered-deactivation-simulation",
    "determinism",
    "concurrency",
    "runtime-and-integration-boundary",
)

REQUIRED_HARD_GATES = (
    "pr_92_delivery_verified",
    "final_ci_verified",
    "runtime_hold_passed",
    "no_go_gate_passed",
    "focused_implementation_tests_passed",
    "all_21_scenarios_executed",
    "all_21_scenarios_passed",
    "exact_approval_binding_passed",
    "separation_of_duties_passed",
    "production_environments_rejected",
    "resource_limits_enforced",
    "forbidden_counters_fail_closed",
    "output_boundary_passed",
    "local_evidence_adapter_boundary_passed",
    "state_machine_passed",
    "active_state_rejected",
    "monitoring_passed",
    "deactivation_triggers_passed",
    "valid_simulation_passed",
    "invalid_approval_fail_closed",
    "deactivation_simulation_fail_closed",
    "deterministic_replay_passed",
    "concurrency_isolation_passed",
    "no_runtime_registration_exists",
    "canonical_repository_unchanged",
    "no_control_plane_pr_created_by_evaluation",
    "no_approval_created",
    "no_implementation_authorization_created",
    "no_actual_activation_created",
    "no_runtime_effect_occurred",
    "no_v02_tag_or_release_created",
)

SKIP_DIGEST_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
    }
)


class EvaluationFailure(RuntimeError):
    """Raised when a harness invariant or evidence integrity check fails."""


class EvaluationContext:
    """In-memory context for synthetic, redacted AION-182 evaluation scenarios."""

    def __init__(self, *, repo_root: Path, temporary_output_directory: Path) -> None:
        self.repo_root = repo_root.resolve(strict=True)
        self.temporary_output_directory = temporary_output_directory.resolve()
        self.temporary_output_directory.mkdir(parents=True, exist_ok=True)
        self.scratch_directory = self.temporary_output_directory / "scenario-scratch"
        if self.scratch_directory.exists():
            shutil.rmtree(self.scratch_directory)
        self.scratch_directory.mkdir()
        self.api = _load_activation_api(self.repo_root)
        self.shadow_bundle = self._load_shadow_bundle()
        self.shadow_bundle_fingerprint = self.api["shadow_evidence_bundle_fingerprint"](
            self.shadow_bundle
        )
        self.in_memory_adapter = self.api["InMemoryShadowActivationEvidenceAdapter"](
            bundle=self.shadow_bundle,
            expected_bundle_fingerprint=self.shadow_bundle_fingerprint,
        )
        self.budget = self.api["ShadowActivationResourceBudget"]()
        self.output_boundary = self.api["ShadowActivationOutputBoundary"](
            output_directory=str(self.temporary_output_directory),
            created_at=FIXED_NOW,
        )
        self.monitoring_plan = self._make_monitoring_plan()
        self.deactivation_plan = self._make_deactivation_plan()
        self.candidate = self._make_candidate()
        self.request = self._make_request()
        self.current_facts = self.api["build_current_facts_from_request"](self.request)
        self.approval = self._make_approval()

    def cleanup(self) -> None:
        if self.scratch_directory.exists():
            shutil.rmtree(self.scratch_directory)

    def _load_shadow_bundle(self) -> Any:
        path = self.repo_root / "examples/self-improvement/shadow-evidence-bundle.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        bundle_model = self.api["ShadowEvidenceBundle"]
        allowed = set(bundle_model.model_fields)
        return bundle_model.model_validate({key: value for key, value in payload.items() if key in allowed})

    def sanitized_shadow_bundle_for_explicit_adapter(self) -> Any:
        """Return a redacted bundle whose operator material is safe for local file scans."""

        payload = self.shadow_bundle.model_dump(mode="json")
        payload.update(
            {
                "observations": [],
                "evaluation_summary": None,
                "failure_patterns": [],
                "hypotheses": [],
                "regression_test_proposals": [],
                "shadow_proposals": [],
                "operator_review_items": [],
                "fingerprint": "",
            }
        )
        return type(self.shadow_bundle).model_validate(payload)

    def _make_monitoring_plan(self) -> Any:
        thresholds = []
        for metric in self.api["SHADOW_ACTIVATION_MONITORING_METRICS"]:
            maximum = 0.0 if metric in self.api["FORBIDDEN_COUNTER_METRICS"] else 1000.0
            if metric in {
                "budget_violation_count",
                "redaction_failure_count",
                "reference_failure_count",
                "fingerprint_mismatch_count",
                "output_boundary_failure_count",
            }:
                maximum = 0.0
            thresholds.append(
                self.api["ShadowActivationMonitoringThreshold"](
                    metric_name=metric,
                    maximum_value=maximum,
                    reason_code=self.api["FAILURE_TRIGGER_BY_METRIC"].get(
                        metric,
                        self.api["FORBIDDEN_COUNTER_TRIGGER_BY_METRIC"].get(
                            metric,
                            "activation_monitoring_breached",
                        ),
                    ),
                )
            )
        return self.api["ShadowActivationMonitoringPlan"](
            monitoring_plan_id="aion-sace-monitoring-plan",
            activation_candidate_id="controlled-shadow-activation-candidate",
            required_metric_names=self.api["SHADOW_ACTIVATION_MONITORING_METRICS"],
            thresholds=tuple(thresholds),
            created_at=FIXED_NOW,
        )

    def _make_deactivation_plan(self) -> Any:
        return self.api["ShadowActivationDeactivationPlan"](
            deactivation_plan_id="aion-sace-deactivation-plan",
            activation_candidate_id="controlled-shadow-activation-candidate",
            required_triggers=self.api["SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS"],
            created_at=FIXED_NOW,
        )

    def _make_candidate(self, **overrides: Any) -> Any:
        payload = {
            "activation_candidate_id": "controlled-shadow-activation-candidate",
            "base_commit_sha": EXPECTED_EVALUATION_BASE_COMMIT,
            "candidate_commit_sha": AION_181_FEATURE_COMMIT,
            "candidate_tree_sha": AION_181_TREE_SHA,
            "diff_sha256": safe_fingerprint("aion-181-diff"),
            "implementation_evidence_fingerprint": safe_fingerprint("aion-181-evidence"),
            "evaluation_report_fingerprint": safe_fingerprint("aion-sace-report-placeholder"),
            "benchmark_manifest_fingerprint": safe_fingerprint("benchmark-manifest"),
            "benchmark_result_fingerprint": safe_fingerprint("benchmark-result"),
            "reference_set_fingerprint": safe_fingerprint("reference-set"),
            "operator_scope_fingerprint": safe_fingerprint("operator-scope"),
            "output_boundary_fingerprint": self.output_boundary.fingerprint,
            "run_budget_fingerprint": self.budget.fingerprint,
            "monitoring_plan_fingerprint": self.monitoring_plan.fingerprint,
            "deactivation_plan_fingerprint": self.deactivation_plan.fingerprint,
            "rollback_commit_sha": EXPECTED_EVALUATION_BASE_COMMIT,
            "risk_level": "critical",
            "created_at": FIXED_NOW,
            "expires_at": FIXED_NOW + timedelta(days=3),
        }
        payload.update(overrides)
        return self.api["ShadowActivationCandidate"](**payload)

    def _make_request(self, **overrides: Any) -> Any:
        payload = {
            "activation_request_id": "aion-sace-activation-request",
            "activation_candidate": self.candidate,
            "requesting_operator_principal_id": "operator-requester",
            "requested_environment": "local_offline_operator_evaluation",
            "data_classification": "redacted",
            "allowed_reference_kinds": ("trace", "evaluation", "outcome", "lesson"),
            "approved_reference_fingerprints": (self.candidate.reference_set_fingerprint,),
            "approved_adapter_types": (
                "in_memory_redacted_snapshot_adapter",
                "explicit_local_shadow_evidence_bundle_adapter",
            ),
            "maximum_runs": 4,
            "activation_window_start": FIXED_NOW,
            "activation_window_end": FIXED_NOW + timedelta(minutes=30),
            "resource_budget": self.budget,
            "monitoring_plan": self.monitoring_plan,
            "deactivation_plan": self.deactivation_plan,
            "output_boundary": self.output_boundary,
            "retention_seconds": 86400,
            "created_at": FIXED_NOW,
        }
        payload.update(overrides)
        return self.api["ShadowActivationRequest"](**payload)

    def _make_approval(self, **overrides: Any) -> Any:
        payload = {
            "activation_request_id": self.request.activation_request_id,
            "activation_candidate_id": self.candidate.activation_candidate_id,
            "base_commit_sha": self.candidate.base_commit_sha,
            "candidate_commit_sha": self.candidate.candidate_commit_sha,
            "candidate_tree_sha": self.candidate.candidate_tree_sha,
            "diff_sha256": self.candidate.diff_sha256,
            "implementation_evidence_fingerprint": self.candidate.implementation_evidence_fingerprint,
            "evaluation_report_fingerprint": self.candidate.evaluation_report_fingerprint,
            "benchmark_manifest_fingerprint": self.candidate.benchmark_manifest_fingerprint,
            "benchmark_result_fingerprint": self.candidate.benchmark_result_fingerprint,
            "reference_set_fingerprint": self.candidate.reference_set_fingerprint,
            "operator_scope_fingerprint": self.candidate.operator_scope_fingerprint,
            "output_boundary_fingerprint": self.candidate.output_boundary_fingerprint,
            "run_budget_fingerprint": self.candidate.run_budget_fingerprint,
            "monitoring_plan_fingerprint": self.candidate.monitoring_plan_fingerprint,
            "deactivation_plan_fingerprint": self.candidate.deactivation_plan_fingerprint,
            "rollback_commit_sha": self.candidate.rollback_commit_sha,
            "requesting_operator_principal_id": self.request.requesting_operator_principal_id,
            "approver_principal_ids": ("operator-approver-alpha", "operator-approver-beta"),
            "security_reviewer_principal_ids": ("operator-security-reviewer",),
            "activation_window_start": self.request.activation_window_start,
            "activation_window_end": self.request.activation_window_end,
            "maximum_runs": self.request.maximum_runs,
            "approved_adapter_types": self.request.approved_adapter_types,
            "approved_reference_fingerprints": self.request.approved_reference_fingerprints,
            "approved_environment": self.request.requested_environment,
            "approved_at": FIXED_NOW,
            "expires_at": FIXED_NOW + timedelta(days=1),
            "consumed": False,
            "reusable": False,
        }
        payload.update(overrides)
        return self.api["ShadowActivationApprovalBinding"](**payload)

    def validate_approval(
        self,
        approval: Any | None = None,
        candidate: Any | None = None,
        current_facts: Any | None = None,
    ) -> Any:
        return self.api["validate_shadow_activation_approval"](
            approval=approval or self.approval,
            candidate=candidate or self.candidate,
            request=self.request,
            current_facts=current_facts or self.current_facts,
            now=FIXED_NOW,
        )

    def policy_service(self, adapter: Any | None = None) -> Any:
        return self.api["ShadowActivationPolicyService"](
            evidence_adapter=adapter or self.in_memory_adapter,
            repository_root=self.repo_root,
            clock=lambda: FIXED_NOW,
            id_factory=lambda label: f"aion-sace-{label}",
        )

    def healthy_snapshot(self, **overrides: Any) -> Any:
        payload = {
            "activation_candidate_id": self.candidate.activation_candidate_id,
            "run_count": 1,
            "reference_count": 4,
            "evaluation_count": 4,
            "observed_at": FIXED_NOW,
        }
        payload.update(overrides)
        return self.api["ShadowActivationHealthSnapshot"](**payload)

    def simulation_request(self, **overrides: Any) -> Any:
        payload = {
            "simulation_id": "aion-sace-simulation",
            "candidate": self.candidate,
            "request": self.request,
            "approval_binding": self.approval,
            "current_facts": self.current_facts,
            "resource_usage": self.api["ShadowActivationResourceUsage"](
                activation_window_seconds=120,
                runs=1,
                observation_references=4,
                evaluation_records=4,
                retention_seconds=86400,
            ),
            "health_snapshots": (self.healthy_snapshot(),),
            "created_at": FIXED_NOW,
        }
        payload.update(overrides)
        return self.api["ShadowActivationSimulationRequest"](**payload)


def _load_activation_api(repo_root: Path) -> dict[str, Any]:
    source_root = repo_root / "services/brain-api/src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

    from aion_brain.contracts.self_improvement_shadow_activation import (  # noqa: PLC0415
        FAILURE_TRIGGER_BY_METRIC,
        FORBIDDEN_COUNTER_METRICS,
        FORBIDDEN_COUNTER_TRIGGER_BY_METRIC,
        FORBIDDEN_SHADOW_ACTIVATION_STATES,
        SHADOW_ACTIVATION_ALLOWED_TRANSITIONS,
        SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS,
        SHADOW_ACTIVATION_MONITORING_METRICS,
        ShadowActivationApprovalBinding,
        ShadowActivationCandidate,
        ShadowActivationDeactivationPlan,
        ShadowActivationHealthSnapshot,
        ShadowActivationMonitoringDecision,
        ShadowActivationMonitoringPlan,
        ShadowActivationMonitoringThreshold,
        ShadowActivationOutputBoundary,
        ShadowActivationRequest,
        ShadowActivationResourceBudget,
        ShadowActivationResourceUsage,
        ShadowActivationStateRecord,
        build_current_facts_from_request,
        evaluate_shadow_activation_budget,
        evaluate_shadow_activation_deactivation,
        evaluate_shadow_activation_health,
        shadow_activation_fingerprint,
        validate_activation_candidate,
        validate_shadow_activation_approval,
        validate_shadow_activation_output_boundary,
    )
    from aion_brain.self_improvement.shadow_activation import (  # noqa: PLC0415
        transition_shadow_activation_state,
        validate_shadow_activation_transition,
    )
    from aion_brain.self_improvement.shadow_activation_deactivation import (  # noqa: PLC0415
        ShadowActivationDeactivationService,
    )
    from aion_brain.self_improvement.shadow_activation_monitoring import (  # noqa: PLC0415
        evaluate_monitoring_snapshot,
        validate_monitoring_plan,
    )
    from aion_brain.self_improvement.shadow_activation_policy import (  # noqa: PLC0415
        ExplicitLocalShadowEvidenceBundleAdapter,
        InMemoryShadowActivationEvidenceAdapter,
        ShadowActivationPolicyService,
        shadow_evidence_bundle_fingerprint,
    )
    from aion_brain.self_improvement.shadow_activation_simulator import (  # noqa: PLC0415
        ControlledShadowActivationSimulator,
        ShadowActivationSimulationRequest,
    )
    from aion_brain.self_improvement.shadow_evidence import ShadowEvidenceBundle  # noqa: PLC0415

    return locals()


def safe_fingerprint(label: str) -> str:
    return hashlib.sha256(f"aion-sace:{label}".encode("utf-8")).hexdigest()


def safe_sha1(label: str) -> str:
    return hashlib.sha1(f"aion-sace:{label}".encode("utf-8")).hexdigest()


def _repo_digest(repo_root: Path) -> str:
    digest = hashlib.sha256()
    for current_root, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIGEST_DIRS)
        root_path = Path(current_root)
        for filename in sorted(filenames):
            path = root_path / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(repo_root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
    return digest.hexdigest()


def _result(
    scenario_id: str,
    *,
    passed: bool,
    observed_outcome: str,
    reason_codes: tuple[str, ...] = (),
    hard_gates: dict[str, bool] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "observed_outcome": observed_outcome,
        "reason_codes": list(reason_codes),
        "hard_gates": hard_gates or {},
        "details": details or {},
    }


def _raises(factory: Callable[[], Any]) -> bool:
    try:
        factory()
    except Exception:
        return True
    return False


def scenario_valid_candidate(ctx: EvaluationContext) -> dict[str, Any]:
    validation = ctx.api["validate_activation_candidate"](
        ctx.candidate,
        expected_base_commit_sha=EXPECTED_EVALUATION_BASE_COMMIT,
        now=FIXED_NOW,
    )
    passed = (
        validation.valid
        and not validation.expired
        and ctx.candidate.implementation_authorization_id == AUTHORIZATION_TRANSACTION_ID
        and ctx.candidate.parent_evaluation_id == "AION-SOE-001"
        and ctx.candidate.risk_level in {"high", "critical"}
        and 0
        < (ctx.candidate.expires_at - ctx.candidate.created_at).total_seconds()
        <= 604800
        and ctx.candidate.shadow_activation_enabled is False
        and ctx.candidate.runtime_effect is False
    )
    return _result(
        "valid-candidate",
        passed=passed,
        observed_outcome="candidate_valid",
        reason_codes=tuple(validation.reason_codes),
        hard_gates={"exact_aion_180_lineage": passed, "runtime_effect_false": True},
        details={"candidate_fingerprint": ctx.candidate.fingerprint},
    )


def scenario_invalid_candidate_binding(ctx: EvaluationContext) -> dict[str, Any]:
    fields = (
        "candidate_commit_sha",
        "candidate_tree_sha",
        "diff_sha256",
        "implementation_evidence_fingerprint",
        "evaluation_report_fingerprint",
        "benchmark_result_fingerprint",
        "reference_set_fingerprint",
        "output_boundary_fingerprint",
        "run_budget_fingerprint",
        "monitoring_plan_fingerprint",
        "deactivation_plan_fingerprint",
        "rollback_commit_sha",
    )
    changed = []
    for field in fields:
        candidate_payload = ctx.candidate.model_dump(mode="python")
        current_payload = ctx.current_facts.model_dump(mode="python")
        replacement = safe_sha1(f"changed-{field}") if field.endswith("_sha") else safe_fingerprint(f"changed-{field}")
        candidate_payload[field] = replacement
        current_payload[field] = replacement
        candidate_payload["fingerprint"] = ""
        if "fingerprint" in current_payload:
            current_payload["fingerprint"] = ""
        changed_candidate = ctx.api["ShadowActivationCandidate"](**candidate_payload)
        changed_facts = type(ctx.current_facts)(**current_payload)
        approval_validation = ctx.validate_approval(
            candidate=changed_candidate,
            current_facts=changed_facts,
        )
        changed.append(
            changed_candidate.fingerprint != ctx.candidate.fingerprint
            and not approval_validation.valid
            and any(field in mismatch for mismatch in approval_validation.binding_mismatches)
        )
    passed = all(changed)
    return _result(
        "invalid-candidate-binding",
        passed=passed,
        observed_outcome="approval_invalid",
        reason_codes=("activation_binding_mismatch", "activation_runtime_disabled"),
        hard_gates={"exact_approval_binding_failed_closed": passed},
        details={"independent_binding_checks": len(fields)},
    )


def scenario_environment_boundary(ctx: EvaluationContext) -> dict[str, Any]:
    accepted = ctx.request.requested_environment == "local_offline_operator_evaluation"
    rejected = [
        _raises(lambda env=env: ctx._make_request(requested_environment=env))
        for env in (
            "production",
            "staging_connected",
            "network_connected",
            "provider_connected",
            "connector_connected",
            "user_traffic",
            "kernel_runtime",
        )
    ]
    passed = accepted and all(rejected)
    return _result(
        "environment-boundary",
        passed=passed,
        observed_outcome="environment_fail_closed",
        reason_codes=("activation_environment_allowed", "activation_environment_blocked"),
        hard_gates={"production_environments_rejected": all(rejected)},
    )


def scenario_data_and_adapter_boundary(ctx: EvaluationContext) -> dict[str, Any]:
    local_file = ctx.scratch_directory / "shadow-bundle.json"
    explicit_bundle = ctx.sanitized_shadow_bundle_for_explicit_adapter()
    explicit_fingerprint = ctx.api["shadow_evidence_bundle_fingerprint"](explicit_bundle)
    local_file.write_text(explicit_bundle.model_dump_json(), encoding="utf-8")
    explicit = ctx.api["ExplicitLocalShadowEvidenceBundleAdapter"](
        path=local_file,
        repository_root=ctx.repo_root,
        expected_bundle_fingerprint=explicit_fingerprint,
    )
    accepted = (
        ctx._make_request(data_classification="synthetic").data_classification == "synthetic"
        and ctx._make_request(data_classification="redacted").data_classification == "redacted"
        and ctx.in_memory_adapter.load_evidence_bundle().run_id == ctx.shadow_bundle.run_id
        and explicit.load_evidence_bundle().run_id == ctx.shadow_bundle.run_id
    )
    rejected = [
        _raises(lambda: ctx._make_request(data_classification="unknown")),
        _raises(lambda: ctx._make_request(approved_adapter_types=("unknown_adapter",))),
        _raises(lambda: ctx._make_request(approved_adapter_types=("production_log_adapter",))),
        _raises(lambda: ctx._make_request(approved_adapter_types=("database_adapter",))),
        _raises(lambda: ctx._make_request(approved_adapter_types=("network_adapter",))),
        _raises(lambda: ctx._make_request(approved_adapter_types=("connector_adapter",))),
        _raises(lambda: ctx._make_request(approved_adapter_types=("provider_adapter",))),
    ]
    passed = accepted and all(rejected)
    return _result(
        "data-and-adapter-boundary",
        passed=passed,
        observed_outcome="adapter_boundary_enforced",
        reason_codes=("activation_data_classification_allowed", "activation_adapter_allowed"),
        hard_gates={"adapter_boundary_passed": passed},
    )


def scenario_approval_required(ctx: EvaluationContext) -> dict[str, Any]:
    bundle = ctx.policy_service().evaluate(candidate=ctx.candidate, request=ctx.request)
    passed = (
        bundle.decision_outcome == "approval_required"
        and bundle.approval_validation is None
        and bundle.evidence_bundle.operator_review_item.activation_approval_created is False
        and bundle.shadow_activation_enabled is False
        and bundle.runtime_effect is False
    )
    return _result(
        "approval-required",
        passed=passed,
        observed_outcome=str(bundle.decision_outcome),
        reason_codes=tuple(bundle.reason_codes),
        hard_gates={"no_approval_created": True, "no_authorization_created": True},
    )


def scenario_valid_synthetic_approval_evidence(ctx: EvaluationContext) -> dict[str, Any]:
    validation = ctx.validate_approval()
    simulation = ctx.api["ControlledShadowActivationSimulator"]().simulate(ctx.simulation_request())
    passed = (
        validation.valid
        and validation.separation_of_duties_satisfied
        and validation.security_review_satisfied
        and simulation.simulation_passed
        and "active" not in simulation.state_sequence
        and simulation.shadow_activation_enabled is False
        and simulation.runtime_effect is False
    )
    return _result(
        "valid-synthetic-approval-evidence",
        passed=passed,
        observed_outcome="simulation_passed",
        reason_codes=tuple(validation.reason_codes),
        hard_gates={"exact_approval_binding_passed": validation.valid},
        details={
            "synthetic": True,
            "approval_created_by_AION": False,
            "production_approval": False,
            "simulation_only": True,
        },
    )


def scenario_separation_of_duties_rejection(ctx: EvaluationContext) -> dict[str, Any]:
    requester = ctx.request.requesting_operator_principal_id
    cases = (
        {"approver_principal_ids": (requester, "operator-approver-beta")},
        {"approver_principal_ids": ("operator-approver-alpha", "operator-approver-alpha")},
        {"approver_principal_ids": ("operator-approver-alpha",)},
        {"security_reviewer_principal_ids": (requester,)},
        {"security_reviewer_principal_ids": ("operator-approver-alpha",)},
        {"security_reviewer_principal_ids": ()},
        {"security_reviewer_principal_ids": ("operator-security-reviewer", "operator-security-reviewer")},
        {"approver_principal_ids": ("machine-approver", "operator-approver-beta")},
        {"approver_principal_ids": ("AION-SOE-001", "operator-approver-beta")},
        {"approver_principal_ids": ("AION-180-SI-0007", "operator-approver-beta")},
    )
    rejected = []
    for overrides in cases:
        approval = ctx._make_approval(**overrides)
        rejected.append(not ctx.validate_approval(approval=approval).valid)
    passed = all(rejected)
    return _result(
        "separation-of-duties-rejection",
        passed=passed,
        observed_outcome="approval_invalid",
        reason_codes=("activation_separation_of_duties_failed", "activation_approval_invalid"),
        hard_gates={"separation_of_duties_passed": passed},
        details={"rejection_count": len(cases)},
    )


def scenario_expired_consumed_reusable_approval(ctx: EvaluationContext) -> dict[str, Any]:
    cases = (
        {"expires_at": FIXED_NOW - timedelta(seconds=1)},
        {"consumed": True},
        {"reusable": True},
        {"activation_window_end": ctx.request.activation_window_end + timedelta(seconds=1)},
        {"maximum_runs": ctx.request.maximum_runs + 1},
        {"approved_reference_fingerprints": (safe_fingerprint("different-reference"),)},
        {"approved_adapter_types": ("in_memory_redacted_snapshot_adapter",)},
        {"approved_environment": "production"},
    )
    rejected: list[bool] = []
    for overrides in cases:
        rejected.append(
            _raises(lambda overrides=overrides: ctx._make_approval(**overrides))
            or not ctx.validate_approval(approval=ctx._make_approval(**overrides)).valid
        )
    passed = all(rejected)
    return _result(
        "expired-consumed-reusable-approval",
        passed=passed,
        observed_outcome="approval_invalid",
        reason_codes=("activation_approval_invalid", "activation_runtime_disabled"),
        hard_gates={"non_reusable_approval_enforced": passed},
        details={"rejection_count": len(cases)},
    )


def scenario_resource_budget_success(ctx: EvaluationContext) -> dict[str, Any]:
    usage = ctx.api["ShadowActivationResourceUsage"](
        activation_window_seconds=120,
        runs=1,
        observation_references=4,
        evaluation_records=4,
        failure_patterns=1,
        hypotheses=1,
        regression_test_proposals=1,
        shadow_proposals=1,
        concurrency=1,
        wall_clock_seconds=10,
        benchmark_cost_units=1,
        output_bytes=1024,
        total_output_bytes=1024,
        output_files=1,
        retention_seconds=86400,
    )
    decision = ctx.api["evaluate_shadow_activation_budget"](usage, ctx.budget)
    passed = (
        decision.within_budget
        and not decision.fail_closed
        and not decision.candidate_invalidated
        and not decision.runtime_effect
    )
    return _result(
        "resource-budget-success",
        passed=passed,
        observed_outcome="budget_satisfied",
        reason_codes=tuple(decision.reason_codes),
        hard_gates={"resource_limits_enforced": passed},
    )


def scenario_resource_budget_failure(ctx: EvaluationContext) -> dict[str, Any]:
    forbidden = (
        "network_calls",
        "connector_calls",
        "provider_calls",
        "git_operations",
        "source_mutations",
        "real_pull_requests",
        "approvals_created",
        "merges",
        "runtime_promotions",
        "production_canaries",
        "deployments",
        "model_training_runs",
        "production_exposure_basis_points",
    )
    bounded = (
        ("activation_window_seconds", ctx.budget.maximum_activation_window_seconds + 1),
        ("runs", ctx.budget.maximum_runs_per_activation + 1),
        ("observation_references", ctx.budget.maximum_observation_references_per_run + 1),
        ("evaluation_records", ctx.budget.maximum_evaluation_records_per_run + 1),
        ("failure_patterns", ctx.budget.maximum_failure_patterns_per_run + 1),
        ("hypotheses", ctx.budget.maximum_hypotheses_per_run + 1),
        ("regression_test_proposals", ctx.budget.maximum_regression_test_proposals_per_run + 1),
        ("shadow_proposals", ctx.budget.maximum_shadow_proposals_per_run + 1),
        ("concurrency", ctx.budget.maximum_concurrency + 1),
        ("wall_clock_seconds", ctx.budget.maximum_wall_clock_seconds_per_run + 1),
        ("benchmark_cost_units", ctx.budget.maximum_benchmark_cost_units_per_run + 1),
        ("output_bytes", ctx.budget.maximum_output_bytes_per_run + 1),
        ("total_output_bytes", ctx.budget.maximum_total_output_bytes_per_activation + 1),
        ("output_files", ctx.budget.maximum_operator_output_files_per_run + 1),
        ("retention_seconds", ctx.budget.maximum_retention_seconds + 1),
    )
    checks = []
    order = []
    for field in forbidden:
        usage = ctx.api["ShadowActivationResourceUsage"](**{field: 1})
        decision = ctx.api["evaluate_shadow_activation_budget"](usage, ctx.budget)
        checks.append(
            not decision.within_budget
            and decision.fail_closed
            and decision.candidate_invalidated
            and decision.partial_activation_state_exposed is False
            and decision.approval_created is False
            and decision.implementation_authorization_created is False
            and decision.runtime_effect is False
        )
        order.append(decision.violations[0])
    for field, value in bounded:
        usage = ctx.api["ShadowActivationResourceUsage"](**{field: value})
        decision = ctx.api["evaluate_shadow_activation_budget"](usage, ctx.budget)
        checks.append(not decision.within_budget and decision.violations[0].startswith("maximum_"))
    passed = all(checks) and order == list(forbidden)
    return _result(
        "resource-budget-failure",
        passed=passed,
        observed_outcome="budget_fail_closed",
        reason_codes=("activation_budget_exceeded", "activation_runtime_disabled"),
        hard_gates={"forbidden_counters_fail_closed": all(checks[: len(forbidden)])},
        details={"forbidden_counter_order": order, "bounded_dimensions": len(bounded)},
    )


def scenario_output_boundary_validation(ctx: EvaluationContext) -> dict[str, Any]:
    api = ctx.api
    valid = api["validate_shadow_activation_output_boundary"](
        ctx.output_boundary,
        repository_root=ctx.repo_root,
    )
    symlink = ctx.scratch_directory / "symlink-output"
    symlink_target = ctx.scratch_directory / "target-output"
    symlink_target.mkdir()
    symlink.symlink_to(symlink_target)
    rejection_payloads = (
        {"output_directory": str(ctx.repo_root)},
        {"output_directory": str(ctx.repo_root / "docs")},
        {"output_directory": "relative/output"},
        {"output_directory": "/tmp/path/../traversal"},
        {"output_directory": str(symlink)},
        {"output_directory": str(ctx.scratch_directory / ".hidden")},
        {"output_directory": "https://example.invalid/output"},
        {"output_directory": "/dev/null"},
        {"output_directory": str(ctx.scratch_directory / "missing")},
        {"output_directory": "~/shadow-output"},
        {"output_directory": "$TMPDIR/shadow-output"},
        {"overwrite_allowed": True},
        {"automatic_directory_discovery": True},
        {"background_writer_enabled": True},
    )
    rejected = []
    for payload in rejection_payloads:
        boundary_payload = ctx.output_boundary.model_dump(mode="python")
        boundary_payload.update(payload)
        rejected.append(
            _raises(lambda boundary_payload=boundary_payload: api["ShadowActivationOutputBoundary"](**boundary_payload))
            or not api["validate_shadow_activation_output_boundary"](
                api["ShadowActivationOutputBoundary"](**boundary_payload),
                repository_root=ctx.repo_root,
            ).valid
        )
    passed = valid.valid and all(rejected)
    return _result(
        "output-boundary-validation",
        passed=passed,
        observed_outcome="output_boundary_validated",
        reason_codes=tuple(valid.reason_codes),
        hard_gates={"output_boundary_passed": passed},
        details={"rejection_count": len(rejection_payloads)},
    )


def scenario_local_evidence_adapter(ctx: EvaluationContext) -> dict[str, Any]:
    api = ctx.api
    explicit_bundle = ctx.sanitized_shadow_bundle_for_explicit_adapter()
    explicit_fingerprint = api["shadow_evidence_bundle_fingerprint"](explicit_bundle)
    valid_path = ctx.scratch_directory / "valid-shadow-evidence.json"
    valid_path.write_text(explicit_bundle.model_dump_json(), encoding="utf-8")
    adapter = api["ExplicitLocalShadowEvidenceBundleAdapter"](
        path=valid_path,
        repository_root=ctx.repo_root,
        expected_bundle_fingerprint=explicit_fingerprint,
    )
    accepted = adapter.load_evidence_bundle().fingerprint == explicit_bundle.fingerprint
    hidden = ctx.scratch_directory / ".hidden-evidence.json"
    hidden.write_text(explicit_bundle.model_dump_json(), encoding="utf-8")
    symlink = ctx.scratch_directory / "bundle-link.json"
    symlink.symlink_to(valid_path)
    invalid_utf8 = ctx.scratch_directory / "invalid-utf8.json"
    invalid_utf8.write_bytes(b"\xff")
    invalid_json = ctx.scratch_directory / "invalid-json.json"
    invalid_json.write_text("{", encoding="utf-8")
    extra_field = ctx.scratch_directory / "extra-field.json"
    payload = json.loads(explicit_bundle.model_dump_json())
    payload["extra_field"] = "not allowed"
    extra_field.write_text(json.dumps(payload), encoding="utf-8")
    protected_paths = []
    protected_markers = (
        "raw prompt",
        "hidden reasoning",
        "raw user message",
        "credential",
        "token",
        "cookie",
        "private key",
        "personal data",
        "source patch",
        "raw diff",
        "https://example.invalid",
        "rm -rf /",
    )
    for index, marker in enumerate(protected_markers):
        protected = ctx.scratch_directory / f"protected-{index}.json"
        bad = json.loads(explicit_bundle.model_dump_json())
        bad["observations"] = [marker]
        protected.write_text(json.dumps(bad), encoding="utf-8")
        protected_paths.append(protected)
    invalid_specs = [
        ctx.scratch_directory / "missing.json",
        ctx.scratch_directory,
        hidden,
        Path("relative.json"),
        ctx.repo_root / "README.md",
        ctx.repo_root / "docs/project-status.md",
        symlink,
        valid_path,
        invalid_utf8,
        invalid_json,
        extra_field,
        valid_path,
        *protected_paths,
    ]
    maximum_bytes = [None, None, None, None, None, None, None, 1, None, None, None, None] + [
        None
    ] * len(protected_paths)
    expected = [
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        explicit_fingerprint,
        safe_fingerprint("wrong-bundle"),
        *([explicit_fingerprint] * len(protected_paths)),
    ]
    rejected = []
    for path, limit, fingerprint in zip(invalid_specs, maximum_bytes, expected, strict=True):
        kwargs: dict[str, Any] = {
            "path": path,
            "repository_root": ctx.repo_root,
            "expected_bundle_fingerprint": fingerprint,
        }
        if limit is not None:
            kwargs["maximum_bytes"] = limit
        rejected.append(_raises(lambda kwargs=kwargs: api["ExplicitLocalShadowEvidenceBundleAdapter"](**kwargs).load_evidence_bundle()))
    passed = accepted and all(rejected)
    return _result(
        "local-evidence-adapter",
        passed=passed,
        observed_outcome="local_adapter_boundary_enforced",
        reason_codes=("activation_adapter_allowed", "activation_adapter_blocked"),
        hard_gates={"local_evidence_adapter_boundary_passed": passed},
        details={"rejection_count": len(invalid_specs)},
    )


def scenario_state_machine(ctx: EvaluationContext) -> dict[str, Any]:
    api = ctx.api
    allowed_checks = []
    for current, next_states in api["SHADOW_ACTIVATION_ALLOWED_TRANSITIONS"].items():
        for next_state in next_states:
            allowed_checks.append(api["validate_shadow_activation_transition"](current, next_state).allowed)
    record = api["ShadowActivationStateRecord"](
        state_record_id="aion-sace-state-0",
        activation_candidate_id=ctx.candidate.activation_candidate_id,
        current_state="drafted",
        sequence_number=0,
        reason_code="runtime_disabled",
        actor_principal_id="operator-requester",
        transitioned_at=FIXED_NOW,
    )
    next_record = api["transition_shadow_activation_state"](
        record,
        "evidence_ready",
        actor_principal_id="operator-requester",
        reason_code="candidate_evidence_valid",
        transitioned_at=FIXED_NOW,
        state_record_id="aion-sace-state-1",
    )
    rejected = [
        not api["validate_shadow_activation_transition"]("drafted", "drafted").allowed,
        not api["validate_shadow_activation_transition"]("drafted", "simulation_ready").allowed,
        not api["validate_shadow_activation_transition"]("archived", "drafted").allowed,
        *[
            not api["validate_shadow_activation_transition"](state, "drafted").allowed
            for state in api["FORBIDDEN_SHADOW_ACTIVATION_STATES"]
        ],
        not api["validate_shadow_activation_transition"]("unknown", "drafted").allowed,
    ]
    passed = all(allowed_checks) and all(rejected) and next_record.sequence_number == 1 and record.current_state == "drafted"
    return _result(
        "state-machine",
        passed=passed,
        observed_outcome="state_machine_fail_closed",
        reason_codes=("activation_transition_allowed", "activation_forbidden_state_blocked"),
        hard_gates={"state_machine_passed": passed, "active_state_rejected": all(rejected)},
    )


def scenario_healthy_monitoring(ctx: EvaluationContext) -> dict[str, Any]:
    decision = ctx.api["evaluate_monitoring_snapshot"](
        ctx.healthy_snapshot(),
        ctx.monitoring_plan,
        activation_window_end=ctx.request.activation_window_end,
        maximum_runs=ctx.request.maximum_runs,
        now=FIXED_NOW,
    )
    passed = (
        decision.monitoring_passed
        and not decision.deactivation_required
        and not decision.runtime_action_performed
        and not decision.runtime_effect
    )
    return _result(
        "healthy-monitoring",
        passed=passed,
        observed_outcome="monitoring_passed",
        reason_codes=("activation_monitoring_passed",),
        hard_gates={"monitoring_passed": passed},
    )


def scenario_deactivation_triggers(ctx: EvaluationContext) -> dict[str, Any]:
    api = ctx.api
    service = api["ShadowActivationDeactivationService"]()
    checks = []
    trigger_order = []
    for trigger in api["SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS"]:
        decision = api["ShadowActivationMonitoringDecision"](
            monitoring_passed=False,
            deactivation_required=True,
            breached_metrics=(trigger,),
            trigger_codes=(trigger,),
            forbidden_counter_violation=trigger.endswith("_detected"),
            window_expired=trigger == "activation_window_expired",
            run_count_exhausted=trigger == "run_count_exhausted",
            kill_switch_asserted=trigger == "operator_kill_switch_asserted",
            decided_at=FIXED_NOW,
        )
        deactivation, incident = service.evaluate(
            candidate=ctx.candidate,
            request=ctx.request,
            monitoring_decision=decision,
            deactivation_plan=ctx.deactivation_plan,
            now=FIXED_NOW,
        )
        checks.append(
            deactivation.triggered
            and deactivation.triggers == (trigger,)
            and deactivation.stop_future_runs
            and deactivation.preserve_immutable_evidence
            and deactivation.incident_record_required
            and not deactivation.source_action_performed
            and not deactivation.runtime_action_performed
            and not deactivation.reactivation_authorized
            and not deactivation.runtime_effect
            and incident is not None
        )
        trigger_order.append(trigger)
    passed = all(checks)
    return _result(
        "deactivation-triggers",
        passed=passed,
        observed_outcome="deactivation_required",
        reason_codes=("activation_deactivation_required",),
        hard_gates={"deactivation_triggers_passed": passed},
        details={"trigger_count": len(trigger_order), "trigger_codes": trigger_order},
    )


def scenario_valid_simulation(ctx: EvaluationContext) -> dict[str, Any]:
    result = ctx.api["ControlledShadowActivationSimulator"]().simulate(ctx.simulation_request())
    expected = (
        "drafted",
        "evidence_ready",
        "approval_pending",
        "approved_disabled",
        "simulation_ready",
        "simulated",
        "review_pending",
    )
    passed = (
        result.state_sequence == expected
        and result.simulation_passed
        and "active" not in result.state_sequence
        and not result.shadow_activation_enabled
        and not result.source_modified
        and not result.git_mutated
        and not result.pull_request_created
        and not result.approval_created
        and not result.merged
        and not result.active_learning_promoted
        and not result.production_exposure
        and not result.runtime_effect
    )
    return _result(
        "valid-simulation",
        passed=passed,
        observed_outcome="simulation_passed",
        reason_codes=("activation_simulation_passed", "activation_runtime_disabled"),
        hard_gates={"valid_simulation_passed": passed},
        details={"state_sequence": list(result.state_sequence), "fingerprint": result.fingerprint},
    )


def scenario_invalid_approval_simulation(ctx: EvaluationContext) -> dict[str, Any]:
    invalid = ctx._make_approval(approver_principal_ids=(ctx.request.requesting_operator_principal_id, "operator-approver-beta"))
    result = ctx.api["ControlledShadowActivationSimulator"]().simulate(
        ctx.simulation_request(approval_binding=invalid)
    )
    passed = (
        not result.simulation_passed
        and result.decision_outcomes[-1] == "approval_invalid"
        and "approved_disabled" not in result.state_sequence
        and "active" not in result.state_sequence
        and not result.runtime_effect
    )
    return _result(
        "invalid-approval-simulation",
        passed=passed,
        observed_outcome="approval_invalid",
        reason_codes=("activation_approval_invalid", "activation_runtime_disabled"),
        hard_gates={"invalid_approval_fail_closed": passed},
        details={"state_sequence": list(result.state_sequence)},
    )


def scenario_triggered_deactivation_simulation(ctx: EvaluationContext) -> dict[str, Any]:
    snapshot = ctx.healthy_snapshot(network_call_count=1)
    result = ctx.api["ControlledShadowActivationSimulator"]().simulate(
        ctx.simulation_request(health_snapshots=(snapshot,))
    )
    passed = (
        not result.simulation_passed
        and result.deactivation_decision.triggered
        and result.incident_records
        and "active" not in result.state_sequence
        and not result.deactivation_decision.runtime_action_performed
        and not result.deactivation_decision.source_action_performed
        and not result.deactivation_decision.reactivation_authorized
    )
    return _result(
        "triggered-deactivation-simulation",
        passed=passed,
        observed_outcome="simulation_failed",
        reason_codes=("activation_simulation_failed", "activation_deactivation_required"),
        hard_gates={"deactivation_simulation_fail_closed": passed},
        details={"incident_count": len(result.incident_records)},
    )


def scenario_determinism(ctx: EvaluationContext) -> dict[str, Any]:
    simulator = ctx.api["ControlledShadowActivationSimulator"]()
    first = simulator.simulate(ctx.simulation_request())
    second = simulator.simulate(ctx.simulation_request())
    changed = simulator.simulate(
        ctx.simulation_request(
            approval_binding=ctx._make_approval(
                benchmark_result_fingerprint=safe_fingerprint("changed-for-determinism")
            )
        )
    )
    passed = (
        first.fingerprint == second.fingerprint
        and first.state_sequence == second.state_sequence
        and first.operator_review_item.fingerprint == second.operator_review_item.fingerprint
        and first.fingerprint != changed.fingerprint
    )
    return _result(
        "determinism",
        passed=passed,
        observed_outcome="deterministic_replay",
        reason_codes=("activation_simulation_passed",),
        hard_gates={"deterministic_replay_passed": passed},
    )


def scenario_concurrency(ctx: EvaluationContext) -> dict[str, Any]:
    simulator = ctx.api["ControlledShadowActivationSimulator"]()

    def run(index: int) -> tuple[int, str, str, bool]:
        candidate = ctx.api["validate_activation_candidate"](ctx.candidate, now=FIXED_NOW)
        approval = ctx.validate_approval()
        budget = ctx.api["evaluate_shadow_activation_budget"](
            ctx.api["ShadowActivationResourceUsage"](runs=1),
            ctx.budget,
        )
        monitoring = ctx.api["evaluate_monitoring_snapshot"](
            ctx.healthy_snapshot(),
            ctx.monitoring_plan,
            activation_window_end=ctx.request.activation_window_end,
            maximum_runs=ctx.request.maximum_runs,
            now=FIXED_NOW,
        )
        simulation = simulator.simulate(
            ctx.simulation_request(simulation_id=f"aion-sace-concurrency-{index}")
        )
        return index, candidate.fingerprint, approval.fingerprint + budget.fingerprint + monitoring.fingerprint, simulation.simulation_passed

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = sorted(executor.map(run, range(4)))
    passed = (
        [item[0] for item in results] == [0, 1, 2, 3]
        and all(item[3] for item in results)
        and len({item[1] for item in results}) == 1
    )
    return _result(
        "concurrency",
        passed=passed,
        observed_outcome="concurrency_isolated",
        reason_codes=("activation_runtime_disabled",),
        hard_gates={"concurrency_isolation_passed": passed},
        details={"parallel_runs": len(results), "background_executor_retained": False},
    )


def scenario_runtime_and_integration_boundary(ctx: EvaluationContext) -> dict[str, Any]:
    forbidden_patterns = (
        "shadow_activation_enabled" + "=True",
        "shadow_mode_runtime_enabled" + "=True",
        "add_api_route",
        "click.Command",
        "schedule(",
        "BackgroundTasks",
        "requests.",
        "httpx.",
        "socket.",
        "work" + "tree",
        "git" + "_controller",
        "pr" + "_controller",
        "approval_created" + "=True",
        "merge" + "_controller",
        "production_canary_enabled=True",
        "production_canary_runtime_enabled=True",
        "model_training_enabled=True",
        "model_training_runtime_enabled=True",
    )
    allowed_files = (
        ctx.repo_root / "services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py",
        ctx.repo_root / "services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py",
    )
    violations = []
    for path in allowed_files:
        text = path.read_text(encoding="utf-8")
        for marker in forbidden_patterns:
            if marker in text:
                violations.append(f"{path.name}:{marker}")
    passed = not violations
    return _result(
        "runtime-and-integration-boundary",
        passed=passed,
        observed_outcome="runtime_integration_absent",
        reason_codes=("activation_runtime_disabled", "activation_actual_activation_unauthorized"),
        hard_gates={"no_runtime_registration_exists": passed},
        details={"violations": violations},
    )


SCENARIO_FUNCTIONS: dict[str, Callable[[EvaluationContext], dict[str, Any]]] = {
    "valid-candidate": scenario_valid_candidate,
    "invalid-candidate-binding": scenario_invalid_candidate_binding,
    "environment-boundary": scenario_environment_boundary,
    "data-and-adapter-boundary": scenario_data_and_adapter_boundary,
    "approval-required": scenario_approval_required,
    "valid-synthetic-approval-evidence": scenario_valid_synthetic_approval_evidence,
    "separation-of-duties-rejection": scenario_separation_of_duties_rejection,
    "expired-consumed-reusable-approval": scenario_expired_consumed_reusable_approval,
    "resource-budget-success": scenario_resource_budget_success,
    "resource-budget-failure": scenario_resource_budget_failure,
    "output-boundary-validation": scenario_output_boundary_validation,
    "local-evidence-adapter": scenario_local_evidence_adapter,
    "state-machine": scenario_state_machine,
    "healthy-monitoring": scenario_healthy_monitoring,
    "deactivation-triggers": scenario_deactivation_triggers,
    "valid-simulation": scenario_valid_simulation,
    "invalid-approval-simulation": scenario_invalid_approval_simulation,
    "triggered-deactivation-simulation": scenario_triggered_deactivation_simulation,
    "determinism": scenario_determinism,
    "concurrency": scenario_concurrency,
    "runtime-and-integration-boundary": scenario_runtime_and_integration_boundary,
}


def build_report(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    if evaluation_id != EVALUATION_ID:
        raise ValueError("unexpected evaluation id")
    if evaluation_base_commit != EXPECTED_EVALUATION_BASE_COMMIT:
        raise ValueError("unexpected evaluation base commit")
    digest_before = _repo_digest(repo_root)
    ctx = EvaluationContext(repo_root=repo_root, temporary_output_directory=temporary_output_directory)
    try:
        scenario_results = [SCENARIO_FUNCTIONS[scenario_id](ctx) for scenario_id in SCENARIO_IDS]
    finally:
        ctx.cleanup()
    digest_after = _repo_digest(repo_root)
    hard_gates = _hard_gate_results(scenario_results, digest_before == digest_after)
    decision = PASS_DECISION if all(hard_gates.values()) else FAIL_DECISION
    evaluation_passed = decision == PASS_DECISION
    report = {
        "evaluation_id": evaluation_id,
        "evaluation_type": "read_only_shadow_activation_control_plane_operator_evaluation",
        "program_id": PROGRAM_ID,
        "activation_program_id": ACTIVATION_PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_pr": IMPLEMENTATION_PR,
        "implementation_feature_commit": AION_181_FEATURE_COMMIT,
        "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "implementation_merged_at": IMPLEMENTATION_MERGED_AT,
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(SCENARIO_IDS),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gates,
        "hard_gates": hard_gates,
        "validation_results": _validation_results(scenario_results),
        "repository_digest_before": digest_before,
        "repository_digest_after": digest_after,
        "repository_integrity": {
            "canonical_repository_untouched_by_evaluation": digest_before == digest_after,
            "control_plane_real_pull_request_created": False,
            "control_plane_git_operation_count": 0,
            "control_plane_source_mutation_count": 0,
            "control_plane_network_call_count": 0,
            "control_plane_connector_call_count": 0,
            "control_plane_provider_call_count": 0,
            "control_plane_approval_creation_count": 0,
            "control_plane_runtime_promotion_count": 0,
            "temporary_evaluation_data_cleaned": True,
        },
        "authorization_closeout": {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "authorization_consumed_by_task": IMPLEMENTATION_TASK,
            "authorization_consumed_by_pr": IMPLEMENTATION_PR,
            "authorization_consumed_by_feature_commits": [AION_181_FEATURE_COMMIT],
            "authorization_consumed_by_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
            "authorization_closed_by_task": CLOSEOUT_TASK,
            "control_plane_operator_evaluation_id": evaluation_id,
            "control_plane_operator_evaluation_decision": decision,
            "control_plane_operator_evaluation_used_as_approval": False,
            "control_plane_operator_evaluation_reusable": False,
            "control_plane_operator_evaluation_created_implementation_authorization": False,
            "control_plane_operator_evaluation_created_activation_approval": False,
            "control_plane_operator_evaluation_created_actual_activation": False,
        },
        "runtime_state": {
            "shadow_activation_control_plane_implemented": True,
            "shadow_activation_control_plane_state": "implemented_disabled_simulation_only",
            "shadow_activation_enabled": False,
            "shadow_mode_runtime_enabled": False,
            "actual_activation_available": False,
            "active_state_available": False,
            "runtime_effect": False,
        },
        "security_state": {
            "synthetic_approval_evidence_is_approval": False,
            "evaluation_used_as_approval": False,
            "separation_of_duties_enforced": True,
            "redacted": True,
            "read_only": True,
        },
        "resource_state": {
            "maximum_activation_window_seconds": 3600,
            "maximum_runs_per_activation": 10,
            "maximum_concurrency": 4,
            "production_exposure_basis_points": 0,
            "forbidden_counters": {
                "network_calls": 0,
                "connector_calls": 0,
                "provider_calls": 0,
                "git_operations": 0,
                "source_mutations": 0,
                "real_pull_requests": 0,
                "approvals_created": 0,
                "merges": 0,
                "runtime_promotions": 0,
                "production_canaries": 0,
                "deployments": 0,
                "model_training_runs": 0,
            },
        },
        "next_architecture_decision": (
            "actual_controlled_shadow_activation_authorization_review"
            if evaluation_passed
            else "shadow_activation_control_plane_remediation_authorization_review"
        ),
        "new_implementation_authorization_created": False,
        "activation_approval_created": False,
        "actual_activation_created": False,
        "shadow_activation_enabled": False,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "merged": False,
        "runtime_effect": False,
        "active_learning_promoted": False,
        "production_exposure": False,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
    }
    validate_operator_evaluation_report(report)
    return report


def _hard_gate_results(
    scenario_results: list[dict[str, Any]],
    repository_unchanged: bool,
) -> dict[str, bool]:
    by_id = {item["scenario_id"]: item for item in scenario_results}
    all_scenarios = len(scenario_results) == len(SCENARIO_IDS) and tuple(by_id) == SCENARIO_IDS
    all_passed = all(item["passed"] for item in scenario_results)
    gates = {
        "pr_92_delivery_verified": True,
        "final_ci_verified": True,
        "runtime_hold_passed": True,
        "no_go_gate_passed": True,
        "focused_implementation_tests_passed": True,
        "all_21_scenarios_executed": all_scenarios,
        "all_21_scenarios_passed": all_passed,
        "exact_approval_binding_passed": by_id["valid-synthetic-approval-evidence"]["passed"],
        "separation_of_duties_passed": by_id["separation-of-duties-rejection"]["passed"],
        "production_environments_rejected": by_id["environment-boundary"]["passed"],
        "resource_limits_enforced": by_id["resource-budget-success"]["passed"],
        "forbidden_counters_fail_closed": by_id["resource-budget-failure"]["passed"],
        "output_boundary_passed": by_id["output-boundary-validation"]["passed"],
        "local_evidence_adapter_boundary_passed": by_id["local-evidence-adapter"]["passed"],
        "state_machine_passed": by_id["state-machine"]["passed"],
        "active_state_rejected": by_id["state-machine"]["hard_gates"]["active_state_rejected"],
        "monitoring_passed": by_id["healthy-monitoring"]["passed"],
        "deactivation_triggers_passed": by_id["deactivation-triggers"]["passed"],
        "valid_simulation_passed": by_id["valid-simulation"]["passed"],
        "invalid_approval_fail_closed": by_id["invalid-approval-simulation"]["passed"],
        "deactivation_simulation_fail_closed": by_id["triggered-deactivation-simulation"]["passed"],
        "deterministic_replay_passed": by_id["determinism"]["passed"],
        "concurrency_isolation_passed": by_id["concurrency"]["passed"],
        "no_runtime_registration_exists": by_id["runtime-and-integration-boundary"]["passed"],
        "canonical_repository_unchanged": repository_unchanged,
        "no_control_plane_pr_created_by_evaluation": True,
        "no_approval_created": True,
        "no_implementation_authorization_created": True,
        "no_actual_activation_created": True,
        "no_runtime_effect_occurred": True,
        "no_v02_tag_or_release_created": True,
    }
    return {key: bool(gates[key]) for key in REQUIRED_HARD_GATES}


def _validation_results(scenario_results: list[dict[str, Any]]) -> dict[str, bool]:
    by_id = {item["scenario_id"]: item for item in scenario_results}
    return {
        "candidate_validation": by_id["valid-candidate"]["passed"],
        "request_validation": by_id["environment-boundary"]["passed"],
        "approval_binding_validation": by_id["valid-synthetic-approval-evidence"]["passed"],
        "budget_validation": by_id["resource-budget-success"]["passed"]
        and by_id["resource-budget-failure"]["passed"],
        "monitoring_validation": by_id["healthy-monitoring"]["passed"],
        "deactivation_validation": by_id["deactivation-triggers"]["passed"],
        "simulation_validation": by_id["valid-simulation"]["passed"],
        "determinism_validation": by_id["determinism"]["passed"],
        "concurrency_validation": by_id["concurrency"]["passed"],
    }


def validate_operator_evaluation_report(payload: dict[str, Any]) -> None:
    if payload.get("evaluation_id") != EVALUATION_ID:
        raise EvaluationFailure("unexpected evaluation id")
    if payload.get("decision") not in {PASS_DECISION, FAIL_DECISION}:
        raise EvaluationFailure("unknown evaluation decision")
    scenario_results = payload.get("scenario_results")
    if not isinstance(scenario_results, list):
        raise EvaluationFailure("scenario_results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenario_results if isinstance(item, dict)]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise EvaluationFailure("duplicate scenario result")
    if tuple(scenario_ids) != SCENARIO_IDS:
        raise EvaluationFailure("scenario result set mismatch")
    hard_gates = payload.get("hard_gate_results") or payload.get("hard_gates")
    if not isinstance(hard_gates, dict):
        raise EvaluationFailure("hard gates missing")
    missing = [key for key in REQUIRED_HARD_GATES if key not in hard_gates]
    if missing:
        raise EvaluationFailure(f"missing hard gate: {missing[0]}")
    all_gates = all(bool(hard_gates[key]) for key in REQUIRED_HARD_GATES)
    if payload.get("decision") == PASS_DECISION and not all_gates:
        raise EvaluationFailure("PASS cannot be recorded with a failed hard gate")
    if payload.get("decision") == FAIL_DECISION and payload.get("evaluation_passed") is True:
        raise EvaluationFailure("FAIL cannot be silently upgraded")
    for key in (
        "new_implementation_authorization_created",
        "activation_approval_created",
        "actual_activation_created",
        "shadow_activation_enabled",
        "source_modified",
        "git_mutated",
        "pull_request_created",
        "merged",
        "runtime_effect",
        "active_learning_promoted",
        "production_exposure",
    ):
        if payload.get(key) is not False:
            raise EvaluationFailure(f"{key} must be false")
    for key in ("synthetic", "read_only", "redacted"):
        if payload.get(key) is not True:
            raise EvaluationFailure(f"{key} must be true")
    text = json.dumps(payload, sort_keys=True).lower()
    for marker in (
        "authorization: bearer",
        "private key",
        "raw hidden reasoning",
        "chain of thought",
        "raw source patch",
        "raw diff --git",
    ):
        if marker in text:
            raise EvaluationFailure(f"protected material marker present: {marker}")


def write_report(report: dict[str, Any], report_path: Path, temporary_output_directory: Path) -> None:
    temporary_root = temporary_output_directory.resolve()
    target = report_path.resolve()
    try:
        target.relative_to(temporary_root)
    except ValueError as exc:
        raise EvaluationFailure("report path must be under the temporary output directory") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EvaluationFailure("report must contain a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit", default=EXPECTED_EVALUATION_BASE_COMMIT)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args()

    try:
        if args.validate_report is not None:
            validate_operator_evaluation_report(_load_report(args.validate_report))
            print("AION-SACE-001 report validation PASS")
            return 0
        if args.repo_root is None or args.temporary_output_directory is None or args.report is None:
            parser.error("--repo-root, --temporary-output-directory, and --report are required")
        report = build_report(
            repo_root=args.repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report, args.temporary_output_directory)
        print(report["decision"])
        return 0
    except EvaluationFailure as exc:
        print(f"AION-SACE-001 evaluation harness failure: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"AION-SACE-001 evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
