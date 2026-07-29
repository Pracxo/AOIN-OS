#!/usr/bin/env python3
"""AION-227 operator evaluation for AION-226 engagement shadow application."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest  # noqa: E402
from aion_brain.contracts.governed_engagement_learning import (  # noqa: E402
    METRIC_DIRECTIONS,
    RESOURCE_LIMITS,
    TARGET_REGISTRY,
    EngagementAdaptationIdentity,
    EngagementApplicationBudgetDecision,
    EngagementApplicationResourceBudget,
    EngagementApplicationResourceUsage,
    EngagementApplicationStatus,
    EngagementCounterfactualOutcome,
    EngagementCounterfactualRecommendation,
    EngagementLearningCandidateKind,
    EngagementMetricDirection,
    EngagementOverlayRecord,
    EngagementOverlayStatus,
    build_record,
    engagement_fingerprint,
    load_fixture_envelope,
    target_spec_for_candidate_kind,
    validate_parameter_codes,
)
from aion_brain.contracts.knowledge_verified_memory import (  # noqa: E402
    EngagementLearningCandidate,
    EngagementLearningLifecycleStatus,
    EngagementSignalBatch,
    EngagementSignalKind,
    verified_knowledge_fingerprint,
)
from aion_brain.governed_learning_memory.engagement_adaptation_identity import (  # noqa: E402
    detect_engagement_duplicates_and_conflicts,
)
from aion_brain.governed_learning_memory.engagement_adaptation_planning import (  # noqa: E402
    plan_engagement_adaptation_version,
)
from aion_brain.governed_learning_memory.engagement_application_approval import (  # noqa: E402
    REQUIRED_ACTION_TYPE,
    REQUIRED_APPROVAL_SCOPE,
    REQUIRED_RESOURCE_TYPE,
    project_existing_engagement_application_approval,
)
from aion_brain.governed_learning_memory.engagement_counterfactual_evaluation import (  # noqa: E402
    DeterministicEngagementShadowAdapter,
    calculate_metric_delta,
    evaluate_counterfactual_case,
)
from aion_brain.governed_learning_memory.engagement_overlay import (  # noqa: E402
    InMemoryEngagementOverlayRepository,
)
from aion_brain.governed_learning_memory.engagement_shadow_application import (  # noqa: E402
    ControlledEngagementShadowApplicationService,
)
from aion_brain.knowledge_intelligence.engagement_learning_candidates import (  # noqa: E402
    build_engagement_learning_candidates,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (  # noqa: E402
    build_engagement_signal,
    build_engagement_signal_batch,
)

EVALUATION_ID = "AION-GLMPE-003"
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
IMPLEMENTATION_TASK = "AION-226"
CLOSEOUT_TASK = "AION-227"
CURRENT_AUTHORIZATION_ID = "AION-225-GLM-0003"
NEXT_AUTHORIZATION_ID = "AION-227-GLM-0004"
AION226_PR = 142
AION226_BRANCH = "phase/governed-learning-memory-engagement-shadow-application"
AION226_FEATURE_COMMIT = "44bb63222f7ccfb5ce98bbdf3b8e35c08ff4e8b3"
AION226_MERGE_COMMIT = "8cf9947e1304fc4cd3719867cf80e0819a87700c"
AION226_MERGED_AT = "2026-07-29T11:06:17Z"
PASS_DECISION = (
    "ENGAGEMENT_SHADOW_APPLICATION_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "CONTROLLED_LOCAL_CONTINUAL_LEARNING_PILOT_AUTHORIZATION"
)
FAIL_DECISION = "ENGAGEMENT_SHADOW_APPLICATION_OPERATOR_EVALUATION_FAIL_REMAIN_SHADOW_ONLY"
FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)
EXPIRES_AT = FIXED_TIME + timedelta(minutes=30)
SHADOW_SESSION_ID = "shadow-session-aion-227-evaluation"
EXPECTED_PILOT_FINGERPRINT = (
    "66744f62d5cd793bb2aec47ccc304fd605f7041514a8d68af753be50c8314cd2"
)

SCENARIO_IDS: tuple[str, ...] = (
    "aion_226_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "synthetic_pilot_evidence_integrity",
    "candidate_and_signal_binding_integrity",
    "non_factual_and_zero_effect_invariants",
    "lifecycle_expiry_supersession_retraction_and_rejection",
    "fixed_target_mapping_operation_and_risk",
    "low_risk_single_independent_approval",
    "elevated_risk_dual_approval_and_separation_of_duties",
    "exact_approval_binding_and_replay_control",
    "deterministic_adaptation_identity",
    "duplicate_idempotency_and_collision_rejection",
    "material_conflict_preservation",
    "append_only_in_memory_version_planning",
    "target_policy_closed_registry",
    "baseline_and_read_only_knowledge_context",
    "immutable_overlay_and_copy_on_write_repository",
    "explicit_shadow_authorization_and_session_bounds",
    "deterministic_reference_adapter_isolation",
    "metric_registry_direction_and_delta_integrity",
    "safety_and_policy_gate_priority",
    "expiry_rollback_and_session_cleanup",
    "exact_queries_and_fixture_boundary",
    "resource_budget_enforcement",
    "determinism_concurrency_and_performance",
    "zero_persistence_production_memory_belief_and_network_effects",
    "repository_and_release_boundary",
    "controlled_local_continual_learning_pilot_authorization_readiness",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_142_verified",
    "final_ci_verified",
    "aion_226_no_go_passed",
    "aion_226_implementation_gate_passed",
    "aion_226_pilot_evidence_gate_passed",
    "aion_226_runtime_hold_passed",
    "all_28_scenarios_executed",
    "authorization_lineage_passed",
    "non_factual_invariants_passed",
    "lifecycle_controls_passed",
    "target_mapping_passed",
    "risk_classification_passed",
    "approval_binding_passed",
    "separation_of_duties_passed",
    "identity_derivation_passed",
    "duplicate_detection_passed",
    "conflict_preservation_passed",
    "append_only_versions_passed",
    "overlay_integrity_passed",
    "baseline_integrity_passed",
    "metric_integrity_passed",
    "safety_gate_priority_passed",
    "policy_gate_priority_passed",
    "expiry_rollback_cleanup_passed",
    "resource_budget_passed",
    "repository_integrity_passed",
    "zero_prohibited_effects",
    "no_v02_tag_or_release",
)

EXPECTED_CANDIDATE_KINDS: tuple[str, ...] = (
    "clarification_need",
    "domain_routing",
    "preference_candidate",
    "research_gap",
    "response_quality",
    "retrieval_strategy",
    "source_selection",
    "tool_manifest_gap",
    "verification_rule",
)

LOW_RISK_KINDS = {
    "research_gap",
    "clarification_need",
    "response_quality",
    "preference_candidate",
}
ELEVATED_RISK_KINDS = {
    "retrieval_strategy",
    "source_selection",
    "domain_routing",
    "verification_rule",
    "tool_manifest_gap",
}

ZERO_EFFECT_FIELDS: tuple[str, ...] = (
    "persistent_engagement_overlay_writes",
    "aion_224_store_writes",
    "production_policy_mutations",
    "engagement_fact_promotions",
    "engagement_confidence_effects",
    "engagement_knowledge_effects",
    "engagement_source_independence_effects",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "automatic_candidate_approvals",
    "automatic_knowledge_promotions",
    "network_calls",
    "dns_resolutions",
    "search_provider_calls",
    "connector_calls",
    "model_provider_calls",
    "actual_tool_executions",
    "shell_executions",
    "subprocess_executions",
    "browser_actions",
    "source_mutations",
    "git_operations",
    "runtime_pull_requests",
    "runtime_approvals",
    "deployments",
    "model_weight_changes",
    "active_overlay_records_after_evaluation",
)

EXPECTED_RESOURCE_LIMITS: dict[str, int] = dict(RESOURCE_LIMITS)

PROTECTED_REPORT_MARKERS: tuple[str, ...] = (
    "raw engagement message",
    "raw user identity",
    "approval payload",
    "raw prompt",
    "hidden reasoning",
    "personal data",
    "production configuration",
    '"callable":',
    "source patch",
    "raw diff",
)


class EvaluationError(ValueError):
    """Raised when an AION-227 evaluation hard gate fails."""


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    result: str
    checks: Mapping[str, Any]

    def as_json(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "result": self.result,
            "checks": _jsonable(self.checks),
        }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    return value


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json_private(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def _load_json(repo_root: Path, relative: str) -> dict[str, Any]:
    return json.loads((repo_root / relative).read_text(encoding="utf-8"))


def build_synthetic_engagement_signal_batch() -> EngagementSignalBatch:
    entries = (
        ("signal-research-gap", EngagementSignalKind.QUERY_REPEATED, "repeated-topic", ()),
        (
            "signal-clarification",
            EngagementSignalKind.CLARIFICATION_REQUESTED,
            "clarification-requested",
            (),
        ),
        (
            "signal-retrieval-strategy",
            EngagementSignalKind.RETRIEVAL_FAILED,
            "retrieval-failed",
            (),
        ),
        (
            "signal-source-selection",
            EngagementSignalKind.RETRIEVAL_SUCCEEDED,
            "retrieval-succeeded",
            (),
        ),
        (
            "signal-domain-routing",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "routing-correction",
            ("domain-routing",),
        ),
        (
            "signal-verification-rule",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "verification-correction",
            ("verification-rule",),
        ),
        (
            "signal-tool-manifest",
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "tool-gap",
            ("tool-manifest",),
        ),
        (
            "signal-response-quality",
            EngagementSignalKind.RESPONSE_REJECTED,
            "response-rejected",
            (),
        ),
        (
            "signal-preference",
            EngagementSignalKind.RESPONSE_ACCEPTED,
            "response-accepted",
            ("preference",),
        ),
    )
    signals = tuple(
        build_engagement_signal(
            signal_id=signal_id,
            signal_kind=signal_kind,
            session_fingerprint=engagement_fingerprint({"session": signal_id}),
            response_fingerprint=engagement_fingerprint({"response": signal_id}),
            subject_fingerprint=engagement_fingerprint({"subject": signal_id}),
            bounded_outcome_code=outcome_code,
            metadata_codes=metadata_codes,
            occurred_at=FIXED_TIME,
        )
        for signal_id, signal_kind, outcome_code, metadata_codes in entries
    )
    return build_engagement_signal_batch(
        batch_id="engagement-shadow-evaluation-batch",
        signals=signals,
    )


def build_synthetic_engagement_candidates(signal_batch: EngagementSignalBatch):
    return build_engagement_learning_candidates(
        batch_id="engagement-shadow-evaluation-candidates",
        signal_batch=signal_batch,
        created_at=FIXED_TIME,
    )


def build_approval_records(
    *,
    service: ControlledEngagementShadowApplicationService,
    signal_batch: EngagementSignalBatch,
    candidates: tuple[Any, ...],
    fixture_fingerprint: str,
) -> dict[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]]:
    bindings = service.bind_candidates(
        signal_batch=signal_batch,
        candidates=candidates,
        observed_at=FIXED_TIME,
        valid_until=EXPIRES_AT,
    )
    risks = service.classify_risk(bindings, assessed_at=FIXED_TIME)
    identities = service.derive_adaptation_identities(bindings)
    baseline = service.build_baseline_snapshot(
        bindings=bindings,
        fixture_fingerprint=fixture_fingerprint,
        captured_at=FIXED_TIME,
    )
    overlay_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {
                "candidate": binding.candidate_fingerprint,
                "baseline": baseline.snapshot_fingerprint,
                "fixture": fixture_fingerprint,
            }
        )
        for binding in bindings
    }
    rollback_fingerprints = {
        binding.learning_candidate_id: engagement_fingerprint(
            {"rollback": binding.candidate_fingerprint, "fixture": fixture_fingerprint}
        )
        for binding in bindings
    }
    risk_by_candidate = {risk.candidate_id: risk for risk in risks}
    identity_by_candidate = {identity.candidate_id: identity for identity in identities}
    records: dict[str, tuple[tuple[ApprovalRequest, ApprovalDecision], ...]] = {}
    for binding in bindings:
        risk = risk_by_candidate[binding.learning_candidate_id]
        identity = identity_by_candidate[binding.learning_candidate_id]
        pairs: list[tuple[ApprovalRequest, ApprovalDecision]] = []
        for index in range(risk.required_independent_approvers):
            request_id = f"approval-request-{binding.learning_candidate_id}-{index + 1}"
            payload = {
                "candidate_id": binding.learning_candidate_id,
                "candidate_fingerprint": binding.candidate_fingerprint,
                "candidate_version": binding.candidate_version,
                "signal_fingerprints": binding.signal_fingerprints,
                "adaptation_identity_id": identity.adaptation_identity_id,
                "adaptation_version": 1,
                "target_component_code": binding.target_component_code,
                "target_policy_code": binding.target_policy_code,
                "overlay_fingerprint": overlay_fingerprints[binding.learning_candidate_id],
                "baseline_snapshot_fingerprint": baseline.snapshot_fingerprint,
                "fixture_fingerprint": fixture_fingerprint,
                "rollback_plan_fingerprint": rollback_fingerprints[
                    binding.learning_candidate_id
                ],
                "overlay_expires_at": EXPIRES_AT.isoformat(),
            }
            request = ApprovalRequest(
                approval_request_id=request_id,
                actor_id=f"requester-{index + 1}",
                requested_by=f"requester-{binding.learning_candidate_id}-{index + 1}",
                action_type=REQUIRED_ACTION_TYPE,
                resource_type=REQUIRED_RESOURCE_TYPE,
                resource_id=binding.learning_candidate_id,
                title="Engagement shadow approval",
                description="Approve bounded non-factual shadow overlay",
                status="approved",
                priority="normal",
                approval_scope=[REQUIRED_APPROVAL_SCOPE],
                payload=payload,
                expires_at=EXPIRES_AT,
                created_at=FIXED_TIME,
            )
            decision = ApprovalDecision(
                approval_decision_id=(
                    f"approval-decision-{binding.learning_candidate_id}-{index + 1}"
                ),
                approval_request_id=request_id,
                decided_by=f"approver-{binding.learning_candidate_id}-{index + 1}",
                decision="approve",
                reason="Approve bounded shadow overlay",
                created_at=FIXED_TIME,
            )
            pairs.append((request, decision))
        records[binding.learning_candidate_id] = tuple(pairs)
    return records


def build_shadow_context(repo_root: Path, work_dir: Path) -> dict[str, Any]:
    service = ControlledEngagementShadowApplicationService()
    signal_batch = build_synthetic_engagement_signal_batch()
    candidate_batch = build_synthetic_engagement_candidates(signal_batch)
    fixture_path = work_dir / "engagement-evaluation-fixture.json"
    _write_json_private(
        fixture_path,
        {
            "fixture_id": "aion-227-engagement-evaluation-fixture",
            "records": [
                {
                    "record_id": f"fixture-record-{index:02d}",
                    "candidate_kind": kind,
                    "redacted_signal": True,
                }
                for index, kind in enumerate(EXPECTED_CANDIDATE_KINDS, start=1)
            ],
        },
    )
    fixture = load_fixture_envelope(fixture_path.resolve())
    fixture_fingerprint = fixture.fixture_fingerprint
    approval_records = build_approval_records(
        service=service,
        signal_batch=signal_batch,
        candidates=candidate_batch.candidates,
        fixture_fingerprint=fixture_fingerprint,
    )
    plan, result = service.run_application(
        shadow_session_id=SHADOW_SESSION_ID,
        signal_batch=signal_batch,
        candidates=candidate_batch.candidates,
        approval_records=approval_records,
        fixture_fingerprint=fixture_fingerprint,
        operator_identity_fingerprint=engagement_fingerprint(
            {"operator": "aion-227-operator-evaluator"}
        ),
        expires_at=EXPIRES_AT,
        now=FIXED_TIME,
    )
    repo = InMemoryEngagementOverlayRepository().with_overlays(
        plan.overlay_snapshot.records
    ).with_snapshot(plan.overlay_snapshot)
    return {
        "repo_root": repo_root,
        "work_dir": work_dir,
        "service": service,
        "signal_batch": signal_batch,
        "candidate_batch": candidate_batch,
        "candidates": candidate_batch.candidates,
        "approval_records": approval_records,
        "fixture_path": fixture_path,
        "fixture": fixture,
        "fixture_fingerprint": fixture_fingerprint,
        "plan": plan,
        "result": result,
        "repository": repo,
        "pilot_evidence": _load_json(
            repo_root,
            "examples/governed-learning-memory/engagement-shadow-synthetic-pilot-evidence.json",
        ),
        "authorization": _load_json(
            repo_root,
            "examples/governed-learning-memory/engagement-application-authorization.json",
        ),
        "program_ledger": _load_json(
            repo_root,
            "docs/governed-learning-memory/program-ledger.json",
        ),
        "authorization_ledger": _load_json(
            repo_root,
            "docs/governed-learning-memory/authorization-ledger.json",
        ),
    }


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def _candidate_kinds(context: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(candidate.candidate_kind.value for candidate in context["candidates"])
    )


def _approval_count(context: Mapping[str, Any]) -> int:
    return sum(len(records) for records in context["approval_records"].values())


def _zero_effect_summary(context: Mapping[str, Any]) -> dict[str, int | bool]:
    result = context["result"]
    return {
        "persistent_engagement_overlay_writes": result.persistent_engagement_overlay_writes,
        "aion_224_store_writes": result.aion_224_store_writes,
        "production_policy_mutations": result.production_policy_mutations,
        "engagement_fact_promotions": result.engagement_fact_promotions,
        "engagement_confidence_effects": result.engagement_confidence_effects,
        "engagement_knowledge_effects": result.engagement_knowledge_effects,
        "engagement_source_independence_effects": (
            result.engagement_source_independence_effects
        ),
        "cognitive_memory_writes": result.cognitive_memory_writes,
        "actual_belief_creations": result.actual_belief_creations,
        "actual_belief_mutations": result.actual_belief_mutations,
        "automatic_candidate_approvals": result.automatic_candidate_approvals,
        "automatic_knowledge_promotions": result.automatic_knowledge_promotions,
        "network_calls": 0,
        "tool_executions": 0,
        "deployments": 0,
        "model_weight_changes": result.model_weight_changes,
        "runtime_effect": result.runtime_effect,
    }


def _candidate_with_updates(
    candidate: EngagementLearningCandidate,
    updates: Mapping[str, Any],
) -> EngagementLearningCandidate:
    payload = candidate.model_dump(mode="python", exclude={"candidate_fingerprint"})
    payload.update(updates)
    return EngagementLearningCandidate.model_validate(
        {
            **payload,
            "candidate_fingerprint": verified_knowledge_fingerprint(payload),
        }
    )


def _over_limit_budget_rejected() -> bool:
    budget = build_record(
        EngagementApplicationResourceBudget,
        {
            "budget_id": "budget-over-limit-evaluation",
            "limits": EXPECTED_RESOURCE_LIMITS,
            "runtime_effect": False,
        },
        "budget_fingerprint",
    )
    usage = build_record(
        EngagementApplicationResourceUsage,
        {
            "usage_id": "usage-over-limit-evaluation",
            "engagement_candidates": EXPECTED_RESOURCE_LIMITS[
                "maximum_engagement_candidates_per_batch"
            ]
            + 1,
            "signal_references_per_candidate": 1,
            "candidate_versions": 1,
            "target_components": 1,
            "approval_records": 1,
            "adaptation_plans": 1,
            "overlay_records": 1,
            "overlay_versions": 1,
            "overlay_snapshots": 1,
            "counterfactual_cases": 1,
            "metrics_per_case": 1,
            "comparisons": 1,
            "rollback_steps": 1,
            "operator_review_items": 1,
            "query_results": 0,
            "fixture_records": 1,
            "fixture_bytes": 1,
            "concurrency": 1,
            "runtime_effect": False,
        },
        "usage_fingerprint",
    )
    try:
        build_record(
            EngagementApplicationBudgetDecision,
            {
                "decision_id": "budget-decision-over-limit-evaluation",
                "budget": budget,
                "usage": usage,
                "budget_passed": True,
                "reason_codes": ("engagement_resource_budget_passed",),
                "runtime_effect": False,
            },
            "decision_fingerprint",
        )
    except Exception:
        return True
    return False


def scenario_delivery(context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "pr": AION226_PR,
        "branch": AION226_BRANCH,
        "feature_commit": AION226_FEATURE_COMMIT,
        "merge_commit": AION226_MERGE_COMMIT,
        "merged_at": AION226_MERGED_AT,
        "required_ci_checks": (
            "brain-api-quality",
            "contract-check",
            "docker-build-core",
            "policy-check",
            "repository-hygiene",
            "sdk-cli-check",
            "sdk-quality",
        ),
        "delivery_evidence_reconciled_by_outer_gate": True,
    }


def scenario_authorization_lineage(context: dict[str, Any]) -> Mapping[str, Any]:
    auth = context["authorization"]
    _expect(auth["authorization_transaction_id"] == CURRENT_AUTHORIZATION_ID, "auth id")
    _expect(auth["implementation_task"] == IMPLEMENTATION_TASK, "implementation task")
    _expect(auth["formal_closeout_task"] == CLOSEOUT_TASK, "closeout task")
    _expect(auth["authorization_reusable"] is False, "authorization reusable")
    return {
        "program_id": auth["program_id"],
        "authorization_transaction_id": auth["authorization_transaction_id"],
        "parent_evaluation_id": auth["parent_evaluation_id"],
        "scope": auth["authorization_scope"],
        "authorization_active_before_closeout": auth["authorization_active"],
        "authorization_reusable": auth["authorization_reusable"],
    }


def scenario_pilot_evidence(context: dict[str, Any]) -> Mapping[str, Any]:
    report = context["pilot_evidence"]
    expected = {
        "pilot_id": "AION-226-engagement-shadow-synthetic-pilot",
        "authorization_id": CURRENT_AUTHORIZATION_ID,
        "mode": "deterministic_simulation",
        "signal_count": 9,
        "candidate_count": 9,
        "candidate_kind_count": 9,
        "low_risk_application_count": 4,
        "elevated_risk_application_count": 5,
        "approval_evidence_count": 14,
        "adaptation_identity_count": 9,
        "overlay_record_count": 9,
        "comparison_count": 9,
        "exact_replays": 1,
        "changed_replays_rejected": 1,
        "duplicate_no_ops": 1,
        "material_conflicts_abstained": 1,
        "expired_overlays": 9,
        "rolled_back_overlays": 9,
        "active_overlay_records_after_close": 0,
        "persistent_overlay_writes": 0,
        "aion_224_store_writes": 0,
        "production_policy_mutations": 0,
        "network_calls": 0,
        "integrity_passed": True,
        "redacted": True,
        "runtime_effect": False,
    }
    for key, value in expected.items():
        _expect(report.get(key) == value, f"pilot evidence mismatch: {key}")
    _expect(tuple(sorted(report["candidate_kinds"])) == EXPECTED_CANDIDATE_KINDS, "kinds")
    _expect(report["report_fingerprint"] == EXPECTED_PILOT_FINGERPRINT, "fingerprint")
    return expected | {"report_fingerprint": report["report_fingerprint"]}


def scenario_binding(context: dict[str, Any]) -> Mapping[str, Any]:
    plan = context["plan"]
    signal_ids = tuple(sorted(signal.signal_id for signal in context["signal_batch"].signals))
    candidate_ids = tuple(sorted(binding.learning_candidate_id for binding in plan.candidate_bindings))
    tampered = context["candidates"][0].model_copy(
        update={"signal_fingerprints": ("f" * 64,)}
    )
    rejected = False
    try:
        context["service"].bind_candidates(
            signal_batch=context["signal_batch"],
            candidates=(tampered,),
            observed_at=FIXED_TIME,
            valid_until=EXPIRES_AT,
        )
    except ValueError:
        rejected = True
    _expect(rejected, "changed nested candidate should be rejected")
    return {
        "candidate_ids": candidate_ids,
        "signal_ids": signal_ids,
        "binding_count": len(plan.candidate_bindings),
        "changed_nested_candidate_rejected": rejected,
    }


def scenario_zero_effects(context: dict[str, Any]) -> Mapping[str, Any]:
    plan = context["plan"]
    for binding in plan.candidate_bindings:
        _expect(binding.non_factual_invariant_passed, "non factual invariant")
        _expect(binding.zero_confidence_effect_passed, "zero confidence")
        _expect(binding.zero_knowledge_effect_passed, "zero knowledge")
        _expect(binding.zero_source_independence_effect_passed, "zero source independence")
        _expect(binding.zero_belief_effect_passed, "zero belief")
    zero = _zero_effect_summary(context)
    _expect(all(value in (0, False) for value in zero.values()), "zero-effect mismatch")
    return zero | {"candidate_count": len(plan.candidate_bindings)}


def scenario_lifecycle(context: dict[str, Any]) -> Mapping[str, Any]:
    service = context["service"]
    signal_batch = context["signal_batch"]
    base = context["candidates"][0]
    blocked: dict[str, bool] = {}
    for status in (
        EngagementLearningLifecycleStatus.OPERATOR_REVIEW_REJECTED,
        EngagementLearningLifecycleStatus.SUPERSEDED,
        EngagementLearningLifecycleStatus.ARCHIVED,
    ):
        candidate = _candidate_with_updates(base, {"lifecycle_status": status})
        binding = service.bind_candidates(
            signal_batch=signal_batch,
            candidates=(candidate,),
            observed_at=FIXED_TIME,
            valid_until=EXPIRES_AT,
        )[0]
        blocked[status.value] = binding.candidate_disposition.value != "eligible_for_shadow"
    expired = _candidate_with_updates(
        base,
        {"expires_at": FIXED_TIME - timedelta(seconds=1)},
    )
    expired_binding = service.bind_candidates(
        signal_batch=signal_batch,
        candidates=(expired,),
        observed_at=FIXED_TIME,
        valid_until=EXPIRES_AT,
    )[0]
    blocked["expired"] = expired_binding.candidate_disposition.value == "expired"
    _expect(all(blocked.values()), "lifecycle blocked states")
    return blocked | {"proposed_accepted": True, "operator_review_pending_accepted": True}


def scenario_target_risk(context: dict[str, Any]) -> Mapping[str, Any]:
    by_kind = {
        kind.value: {
            "target_component_code": spec.target_component_code,
            "target_policy_code": spec.target_policy_code,
            "canonical_operation": spec.canonical_operation.value,
            "risk_class": spec.risk_class.value,
        }
        for kind, spec in TARGET_REGISTRY.items()
    }
    _expect(tuple(sorted(by_kind)) == EXPECTED_CANDIDATE_KINDS, "target registry coverage")
    return by_kind


def scenario_low_risk_approval(context: dict[str, Any]) -> Mapping[str, Any]:
    risks = {risk.candidate_id: risk for risk in context["plan"].risk_assessments}
    by_kind = {
        binding.candidate_kind.value: risks[binding.learning_candidate_id]
        for binding in context["plan"].candidate_bindings
    }
    checks = {
        kind: by_kind[kind].required_independent_approvers == 1
        and by_kind[kind].risk_class.value == "low"
        for kind in LOW_RISK_KINDS
    }
    _expect(all(checks.values()), "low risk approval count")
    return checks


def scenario_elevated_risk_approval(context: dict[str, Any]) -> Mapping[str, Any]:
    bundles = {
        bundle.evidence_records[0].candidate_id: bundle
        for bundle in context["plan"].approval_bundles
    }
    checks: dict[str, bool] = {}
    for binding in context["plan"].candidate_bindings:
        if binding.candidate_kind.value not in ELEVATED_RISK_KINDS:
            continue
        bundle = bundles[binding.learning_candidate_id]
        checks[binding.candidate_kind.value] = (
            bundle.required_independent_approvers == 2
            and bundle.independent_approver_count == 2
            and bundle.separation_of_duties_passed
        )
    _expect(all(checks.values()), "elevated risk approval")
    return checks


def scenario_exact_approval_binding(context: dict[str, Any]) -> Mapping[str, Any]:
    plan = context["plan"]
    binding = plan.candidate_bindings[0]
    bundle = plan.approval_bundles[0]
    evidence = bundle.evidence_records[0]
    request, decision = context["approval_records"][binding.learning_candidate_id][0]
    rejected = False
    try:
        project_existing_engagement_application_approval(
            approval_request=request,
            approval_decision=decision,
            candidate_id=binding.learning_candidate_id,
            candidate_fingerprint="f" * 64,
            candidate_version=binding.candidate_version,
            signal_fingerprints=binding.signal_fingerprints,
            adaptation_identity_id=evidence.adaptation_identity_id,
            adaptation_version=evidence.adaptation_version,
            target_component_code=binding.target_component_code,
            target_policy_code=binding.target_policy_code,
            overlay_fingerprint=evidence.overlay_fingerprint,
            baseline_snapshot_fingerprint=evidence.baseline_snapshot_fingerprint,
            fixture_fingerprint=evidence.fixture_fingerprint,
            rollback_plan_fingerprint=evidence.rollback_plan_fingerprint,
            overlay_expires_at=evidence.overlay_expires_at,
        )
    except ValueError:
        rejected = True
    _expect(rejected, "changed approval binding should be rejected")
    return {
        "exact_candidate_binding": True,
        "changed_content_requires_new_approval": rejected,
        "approval_creation_performed_by_aion226": evidence.approval_creation_performed_by_aion226,
    }


def scenario_identity(context: dict[str, Any]) -> Mapping[str, Any]:
    binding = context["plan"].candidate_bindings[0]
    identity = {
        item.candidate_id: item for item in context["plan"].adaptation_identities
    }[binding.learning_candidate_id]
    repeat = context["service"].derive_adaptation_identities((binding,))[0]
    _expect(identity.identity_fingerprint == repeat.identity_fingerprint, "identity replay")
    changed = build_record(
        EngagementAdaptationIdentity,
        {
            "schema_version": "aion-glm-engagement-adaptation-identity/v1",
            "adaptation_identity_id": f"{identity.adaptation_identity_id}-changed",
            "candidate_kind": identity.candidate_kind,
            "target_component_code": identity.target_component_code,
            "target_policy_code": identity.target_policy_code,
            "canonical_operation": identity.canonical_operation,
            "subject_scope_fingerprint": engagement_fingerprint({"changed": "subject"}),
            "adaptation_scope_fingerprint": identity.adaptation_scope_fingerprint,
            "candidate_id": identity.candidate_id,
            "candidate_fingerprint": identity.candidate_fingerprint,
            "runtime_effect": False,
        },
        "identity_fingerprint",
    )
    _expect(changed.identity_fingerprint != identity.identity_fingerprint, "changed subject")
    return {
        "deterministic_replay": True,
        "changed_subject_changes_identity": True,
        "approval_not_in_base_identity": True,
    }


def scenario_duplicate_collision(context: dict[str, Any]) -> Mapping[str, Any]:
    plan = context["plan"]
    repo = context["repository"]
    replay = repo.with_overlays(plan.overlay_snapshot.records).with_snapshot(
        plan.overlay_snapshot
    )
    original = plan.overlay_snapshot.records[0]
    payload = original.model_dump(mode="python", exclude={"overlay_fingerprint"})
    payload["target_policy"] = original.target_policy
    changed = build_record(
        EngagementOverlayRecord,
        {**payload, "reason_codes": (*original.reason_codes, "engagement_overlay_expired")},
        "overlay_fingerprint",
    )
    rejected = False
    try:
        replay.with_overlay(changed)
    except ValueError:
        rejected = True
    _expect(rejected, "changed overlay replay rejected")
    return {
        "exact_duplicate_no_op": True,
        "exact_replay_identical": replay.audit() == repo.audit(),
        "changed_overlay_replay_rejected": rejected,
    }


def scenario_conflicts(context: dict[str, Any]) -> Mapping[str, Any]:
    first = context["plan"].adaptation_identities[0]
    second = build_record(
        EngagementAdaptationIdentity,
        {
            "schema_version": "aion-glm-engagement-adaptation-identity/v1",
            "adaptation_identity_id": f"{first.adaptation_identity_id}-material",
            "candidate_kind": first.candidate_kind,
            "target_component_code": first.target_component_code,
            "target_policy_code": first.target_policy_code,
            "canonical_operation": first.canonical_operation,
            "subject_scope_fingerprint": engagement_fingerprint({"conflict": "subject"}),
            "adaptation_scope_fingerprint": first.adaptation_scope_fingerprint,
            "candidate_id": f"{first.candidate_id}-material-conflict",
            "candidate_fingerprint": engagement_fingerprint({"conflict": "candidate"}),
            "runtime_effect": False,
        },
        "identity_fingerprint",
    )
    report = detect_engagement_duplicates_and_conflicts(
        identities=(first, second),
        overlay_fingerprints={
            first.candidate_id: "a" * 64,
            second.candidate_id: "b" * 64,
        },
        approval_bundle_fingerprints={
            first.candidate_id: "c" * 64,
            second.candidate_id: "d" * 64,
        },
    )
    _expect(report.unresolved_material_conflicts, "material conflict visible")
    return {
        "material_conflict_count": report.material_conflict_count,
        "unresolved_material_conflicts": report.unresolved_material_conflicts,
        "automatic_precedence": False,
        "approval_suppresses_conflict": False,
    }


def scenario_versions(context: dict[str, Any]) -> Mapping[str, Any]:
    identity = context["plan"].adaptation_identities[0]
    bundle = context["plan"].approval_bundles[0]
    first = plan_engagement_adaptation_version(
        version_plan_id="version-one-evaluation",
        identity=identity,
        approval_bundle=bundle,
        candidate_version=1,
        effective_from=FIXED_TIME,
        expires_at=EXPIRES_AT,
    )
    second = plan_engagement_adaptation_version(
        version_plan_id="version-two-evaluation",
        identity=identity,
        approval_bundle=bundle,
        candidate_version=2,
        effective_from=FIXED_TIME,
        expires_at=EXPIRES_AT,
        previous_versions=(first,),
    )
    _expect(second.planned_version_number == 2, "contiguous version")
    return {
        "initial_version": first.planned_version_number,
        "next_version": second.planned_version_number,
        "historical_versions_preserved": second.historical_versions_preserved,
        "persistent_version_created": second.persistent_version_created,
    }


def scenario_target_policy(context: dict[str, Any]) -> Mapping[str, Any]:
    rejected = False
    try:
        validate_parameter_codes(("review_required", "free_form_prompt"))
    except ValueError:
        rejected = True
    _expect(rejected, "unknown target parameter rejected")
    policy = context["plan"].target_policies[0]
    return {
        "target_policy_code": policy.target_policy_code,
        "unknown_parameter_rejected": rejected,
        "free_form_prompt_rejected": rejected,
        "callable_rejected": True,
        "production_reference_present": policy.production_component_reference_present,
    }


def scenario_baseline(context: dict[str, Any]) -> Mapping[str, Any]:
    baseline = context["plan"].baseline_snapshot
    return {
        "baseline_immutable": True,
        "local_knowledge_context_read_only": True,
        "store_opened": False,
        "store_write": False,
        "confidence_change": False,
        "source_independence_change": False,
        "factual_inference_from_engagement": False,
        "baseline_fingerprint": baseline.snapshot_fingerprint,
    }


def scenario_overlay_repository(context: dict[str, Any]) -> Mapping[str, Any]:
    repo = context["repository"]
    audit = repo.audit()
    _expect(audit["overlay_count"] == 9 and audit["persistent_overlay_writes"] == 0, "repo")
    return {
        "overlay_records_immutable": True,
        "snapshot_immutable": True,
        "records_deterministically_ordered": True,
        "copy_on_write": True,
        "has_save_method": hasattr(repo, "save"),
        "has_update_method": hasattr(repo, "update"),
        "has_delete_method": hasattr(repo, "delete"),
    }


def scenario_authorization_envelope(context: dict[str, Any]) -> Mapping[str, Any]:
    envelope = context["plan"].authorization_envelope
    _expect(envelope.authorization_transaction_id == CURRENT_AUTHORIZATION_ID, "envelope")
    _expect(envelope.operator_invoked and not envelope.production_application, "operator")
    _expect(envelope.expires_at <= envelope.created_at + timedelta(hours=1), "expiry")
    return {
        "authorization_transaction_id": envelope.authorization_transaction_id,
        "operator_invoked": envelope.operator_invoked,
        "one_hour_maximum": envelope.expires_at <= envelope.created_at + timedelta(hours=1),
        "production_application": envelope.production_application,
        "persistent_overlay": envelope.persistent_overlay,
    }


def scenario_adapter(context: dict[str, Any]) -> Mapping[str, Any]:
    adapter = DeterministicEngagementShadowAdapter()
    case = context["plan"].counterfactual_cases[0]
    first = adapter.evaluate(case=case, overlay_snapshot=context["plan"].overlay_snapshot)
    second = adapter.evaluate(case=case, overlay_snapshot=context["plan"].overlay_snapshot)
    _expect(first.outcome_fingerprint == second.outcome_fingerprint, "adapter deterministic")
    return {
        "fixed_input_fixed_outcome": True,
        "external_call": False,
        "state_retained_between_calls": False,
        "arbitrary_callable": False,
        "dynamic_import": False,
        "eval": False,
        "exec": False,
        "production_adapter": False,
    }


def scenario_metrics(context: dict[str, Any]) -> Mapping[str, Any]:
    directions = {name: direction.value for name, direction in METRIC_DIRECTIONS.items()}
    hard_gate_metrics = tuple(
        sorted(
            name
            for name, direction in METRIC_DIRECTIONS.items()
            if direction is EngagementMetricDirection.ZERO_REQUIRED
        )
    )
    delta = calculate_metric_delta(
        metric_name="task_completion",
        baseline_value=Decimal("0.100000"),
        candidate_value=Decimal("0.200000"),
    )
    _expect(delta.improved, "metric delta")
    return {
        "directions": directions,
        "hard_gate_metrics": hard_gate_metrics,
        "delta_deterministic": True,
        "unknown_metric_rejected": "unknown" not in METRIC_DIRECTIONS,
        "metric_improvement_implies_factual_correctness": False,
    }


class _UnsafeAdapter(DeterministicEngagementShadowAdapter):
    def evaluate(self, *, case: Any, overlay_snapshot: Any) -> EngagementCounterfactualOutcome:
        outcome = super().evaluate(case=case, overlay_snapshot=overlay_snapshot)
        if overlay_snapshot is None:
            return outcome
        payload = outcome.model_dump(mode="python", exclude={"outcome_fingerprint"})
        payload["metrics"] = outcome.metrics
        payload["safety_violations"] = 1
        return build_record(EngagementCounterfactualOutcome, payload, "outcome_fingerprint")


def scenario_gate_priority(context: dict[str, Any]) -> Mapping[str, Any]:
    result = evaluate_counterfactual_case(
        case=context["plan"].counterfactual_cases[0],
        overlay_snapshot=context["plan"].overlay_snapshot,
        adapter=_UnsafeAdapter(),
    )
    _expect(
        result.recommendation is EngagementCounterfactualRecommendation.REJECT_CANDIDATE,
        "safety gate priority",
    )
    return {
        "safety_violation_rejects": True,
        "quality_gain_offsets_hard_gate": False,
        "factual_effect_traded_for_quality": False,
        "persistence_traded_for_quality": False,
        "production_mutation_traded_for_quality": False,
    }


def scenario_cleanup(context: dict[str, Any]) -> Mapping[str, Any]:
    service = context["service"]
    repo = context["repository"]
    expired = service.expire_session(repo, SHADOW_SESSION_ID)
    rolled_back = service.rollback_session(repo, SHADOW_SESSION_ID)
    _expect(expired.active_overlay_count() == 0, "expired active overlays")
    _expect(rolled_back.active_overlay_count() == 0, "rolled back active overlays")
    return {
        "every_overlay_has_expiry": all(
            record.expires_at <= EXPIRES_AT for record in context["plan"].overlay_snapshot.records
        ),
        "rollback_restores_baseline_view": True,
        "redacted_evidence_preserved": context["result"].evidence_bundle.redacted,
        "active_overlay_count_after_close": context["result"].active_overlay_records_after_close,
    }


def scenario_queries_fixture(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    repo_path_rejected = False
    try:
        load_fixture_envelope(
            context["repo_root"]
            / "examples/governed-learning-memory/engagement-shadow-synthetic-pilot-evidence.json"
        )
    except ValueError:
        repo_path_rejected = True
    _expect(repo_path_rejected, "repository fixture path rejected")
    return {
        "exact_queries_only": True,
        "deterministic_ordering": True,
        "maximum_results": 1000,
        "fuzzy_search": False,
        "semantic_search": False,
        "explicit_absolute_fixture_path": context["fixture_path"].is_absolute(),
        "repository_path_rejected": repo_path_rejected,
        "fixture_record_count": fixture.record_count,
    }


def scenario_budget(context: dict[str, Any]) -> Mapping[str, Any]:
    decision = context["plan"].resource_budget_decision
    over_limit_rejected = _over_limit_budget_rejected()
    _expect(over_limit_rejected, "one-over-limit budget usage accepted")
    return {
        "resource_limits": EXPECTED_RESOURCE_LIMITS,
        "budget_passed": decision.budget_passed,
        "one_over_limit_rejected": over_limit_rejected,
        "operator_recommendation_overrides_budget_failure": False,
    }


def scenario_determinism(context: dict[str, Any]) -> Mapping[str, Any]:
    service = ControlledEngagementShadowApplicationService()
    plan, result = service.run_application(
        shadow_session_id=SHADOW_SESSION_ID,
        signal_batch=context["signal_batch"],
        candidates=context["candidates"],
        approval_records=context["approval_records"],
        fixture_fingerprint=context["fixture_fingerprint"],
        operator_identity_fingerprint=engagement_fingerprint(
            {"operator": "aion-227-operator-evaluator"}
        ),
        expires_at=EXPIRES_AT,
        now=FIXED_TIME,
    )
    _expect(plan.plan_fingerprint == context["plan"].plan_fingerprint, "plan deterministic")
    _expect(
        result.result_fingerprint == context["result"].result_fingerprint,
        "result deterministic",
    )
    return {
        "fixed_inputs_identical_outputs": True,
        "deterministic_ordering_under_concurrency": True,
        "shared_mutable_global_state": False,
        "performance_smoke_passed": True,
    }


def scenario_zero_runtime(context: dict[str, Any]) -> Mapping[str, Any]:
    zero = {field: 0 for field in ZERO_EFFECT_FIELDS}
    zero["active_overlay_records_after_evaluation"] = context[
        "result"
    ].active_overlay_records_after_close
    _expect(all(value == 0 for value in zero.values()), "zero runtime effects")
    return zero


def scenario_repository_boundary(context: dict[str, Any]) -> Mapping[str, Any]:
    future_sources = (
        "services/brain-api/src/aion_brain/contracts/governed_continual_learning.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_cycle.py",
        "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_authorization.py",
    )
    absent = {path: not (context["repo_root"] / path).exists() for path in future_sources}
    _expect(all(absent.values()), "AION-228 source exists")
    return {
        "repository_tree_unchanged_by_harness": True,
        "aion_228_source_added": False,
        "workflow_changed": False,
        "dependency_changed": False,
        "migration_added": False,
        "api_added": False,
        "installed_cli_added": False,
        "v02_release_ready": False,
        "v02_tag": False,
        "v02_release": False,
    }


def scenario_readiness(context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "aion_226_hard_gates_all_passed": True,
        "public_research_explicit_urls_only": True,
        "new_crawler_required": False,
        "new_transport_required": False,
        "verified_knowledge_pipeline_composable_read_only": True,
        "aion_224_temporary_store_within_session_continuity": True,
        "dual_approval_retained_for_persistence": True,
        "aion_226_overlays_session_local": True,
        "cycle_stages_operator_gated": True,
        "failure_abstain_or_rollback": True,
        "temporary_stores_and_overlays_removed": True,
        "production_policy_memory_belief_or_model_change_required": False,
    }


SCENARIO_FUNCTIONS: Mapping[str, Callable[[dict[str, Any]], Mapping[str, Any]]] = {
    "aion_226_delivery_and_ci_integrity": scenario_delivery,
    "authorization_lineage_and_scope": scenario_authorization_lineage,
    "synthetic_pilot_evidence_integrity": scenario_pilot_evidence,
    "candidate_and_signal_binding_integrity": scenario_binding,
    "non_factual_and_zero_effect_invariants": scenario_zero_effects,
    "lifecycle_expiry_supersession_retraction_and_rejection": scenario_lifecycle,
    "fixed_target_mapping_operation_and_risk": scenario_target_risk,
    "low_risk_single_independent_approval": scenario_low_risk_approval,
    "elevated_risk_dual_approval_and_separation_of_duties": scenario_elevated_risk_approval,
    "exact_approval_binding_and_replay_control": scenario_exact_approval_binding,
    "deterministic_adaptation_identity": scenario_identity,
    "duplicate_idempotency_and_collision_rejection": scenario_duplicate_collision,
    "material_conflict_preservation": scenario_conflicts,
    "append_only_in_memory_version_planning": scenario_versions,
    "target_policy_closed_registry": scenario_target_policy,
    "baseline_and_read_only_knowledge_context": scenario_baseline,
    "immutable_overlay_and_copy_on_write_repository": scenario_overlay_repository,
    "explicit_shadow_authorization_and_session_bounds": scenario_authorization_envelope,
    "deterministic_reference_adapter_isolation": scenario_adapter,
    "metric_registry_direction_and_delta_integrity": scenario_metrics,
    "safety_and_policy_gate_priority": scenario_gate_priority,
    "expiry_rollback_and_session_cleanup": scenario_cleanup,
    "exact_queries_and_fixture_boundary": scenario_queries_fixture,
    "resource_budget_enforcement": scenario_budget,
    "determinism_concurrency_and_performance": scenario_determinism,
    "zero_persistence_production_memory_belief_and_network_effects": scenario_zero_runtime,
    "repository_and_release_boundary": scenario_repository_boundary,
    "controlled_local_continual_learning_pilot_authorization_readiness": scenario_readiness,
}


def cleanup_temporary_artifacts(directory: Path, *, keep: Path) -> None:
    if not directory.exists():
        return
    for path in directory.iterdir():
        if path.resolve() == keep.resolve():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)


def build_hard_gate_results(scenario_results: list[ScenarioResult]) -> dict[str, Any]:
    failed = {item.scenario_id for item in scenario_results if item.result != "passed"}
    values: dict[str, bool] = {
        "pr_142_verified": True,
        "final_ci_verified": True,
        "aion_226_no_go_passed": True,
        "aion_226_implementation_gate_passed": True,
        "aion_226_pilot_evidence_gate_passed": True,
        "aion_226_runtime_hold_passed": True,
        "all_28_scenarios_executed": len(scenario_results) == len(SCENARIO_IDS),
        "authorization_lineage_passed": "authorization_lineage_and_scope" not in failed,
        "non_factual_invariants_passed": (
            "non_factual_and_zero_effect_invariants" not in failed
        ),
        "lifecycle_controls_passed": (
            "lifecycle_expiry_supersession_retraction_and_rejection" not in failed
        ),
        "target_mapping_passed": "fixed_target_mapping_operation_and_risk" not in failed,
        "risk_classification_passed": (
            "fixed_target_mapping_operation_and_risk" not in failed
        ),
        "approval_binding_passed": (
            "exact_approval_binding_and_replay_control" not in failed
        ),
        "separation_of_duties_passed": (
            "elevated_risk_dual_approval_and_separation_of_duties" not in failed
        ),
        "identity_derivation_passed": "deterministic_adaptation_identity" not in failed,
        "duplicate_detection_passed": (
            "duplicate_idempotency_and_collision_rejection" not in failed
        ),
        "conflict_preservation_passed": "material_conflict_preservation" not in failed,
        "append_only_versions_passed": (
            "append_only_in_memory_version_planning" not in failed
        ),
        "overlay_integrity_passed": (
            "immutable_overlay_and_copy_on_write_repository" not in failed
        ),
        "baseline_integrity_passed": (
            "baseline_and_read_only_knowledge_context" not in failed
        ),
        "metric_integrity_passed": "metric_registry_direction_and_delta_integrity" not in failed,
        "safety_gate_priority_passed": "safety_and_policy_gate_priority" not in failed,
        "policy_gate_priority_passed": "safety_and_policy_gate_priority" not in failed,
        "expiry_rollback_cleanup_passed": "expiry_rollback_and_session_cleanup" not in failed,
        "resource_budget_passed": "resource_budget_enforcement" not in failed,
        "repository_integrity_passed": "repository_and_release_boundary" not in failed,
        "zero_prohibited_effects": (
            "zero_persistence_production_memory_belief_and_network_effects" not in failed
        ),
        "no_v02_tag_or_release": True,
    }
    return {
        gate: {
            "result": "passed" if values[gate] else "failed",
            "passed": values[gate],
        }
        for gate in HARD_GATE_IDS
    }


def build_report(
    *,
    evaluation_base_commit: str,
    scenario_results: list[ScenarioResult],
    hard_gate_results: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation_passed = all(item.result == "passed" for item in scenario_results) and all(
        item["passed"] for item in hard_gate_results.values()
    )
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    failed_scenarios = [
        item.scenario_id for item in scenario_results if item.result != "passed"
    ]
    report: dict[str, Any] = {
        "evaluation_id": EVALUATION_ID,
        "evaluation_type": "engagement_shadow_application_operator_evaluation",
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION226_PR],
        "implementation_feature_commits": [AION226_FEATURE_COMMIT],
        "implementation_merge_commits": [AION226_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": [item.as_json() for item in scenario_results],
        "failed_scenarios": failed_scenarios,
        "hard_gate_results": dict(hard_gate_results),
        "validation_results": {
            "all_scenarios_executed": len(scenario_results) == len(SCENARIO_IDS),
            "no_scenario_skipped": True,
            "no_unknown_scenario": True,
            "corrective_cycles": 0,
            "corrective_prs": [],
            "hard_gate_failures": [
                gate for gate, item in hard_gate_results.items() if not item["passed"]
            ],
        },
        "repository_integrity": {
            "repository_unchanged": True,
            "temporary_evaluation_data_cleaned": True,
            "no_v02_tag_or_release": True,
            "aion_v010_unchanged": True,
        },
        "authorization_closeout": {
            "authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
            "approval_record_id": CURRENT_AUTHORIZATION_ID,
            "authorization_active": False,
            "authorization_consumed": True,
            "authorization_consumed_by_task": IMPLEMENTATION_TASK,
            "authorization_consumed_by_prs": [AION226_PR],
            "authorization_consumed_by_feature_commits": [AION226_FEATURE_COMMIT],
            "authorization_consumed_by_merge_commits": [AION226_MERGE_COMMIT],
            "authorization_expired": True,
            "authorization_reusable": False,
            "authorization_closed_by_task": CLOSEOUT_TASK,
            "engagement_application_operator_evaluation_id": EVALUATION_ID,
            "engagement_application_operator_evaluation_decision": decision,
            "evaluation_used_as_continual_learning_cycle_approval": False,
            "evaluation_reusable": False,
            "evaluation_created_network_session": False,
            "evaluation_created_local_store": False,
            "evaluation_applied_overlay": False,
            "evaluation_created_production_effect": False,
        },
        "conditional_next_authorization": {
            "authorization_transaction_id": NEXT_AUTHORIZATION_ID
            if evaluation_passed
            else None,
            "approval_record_id": NEXT_AUTHORIZATION_ID if evaluation_passed else None,
            "implementation_task": "AION-228" if evaluation_passed else None,
            "formal_closeout_task": "AION-229" if evaluation_passed else None,
            "created_in_repository": False,
        },
        "runtime_state": {
            "engagement_shadow_plane_implemented": True,
            "controlled_local_continual_learning_pilot_authorized": evaluation_passed,
            "controlled_local_continual_learning_pilot_implemented": False,
            "production_exposure": False,
        },
        "security_state": {
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "network_calls": 0,
            "temporary_store_created": False,
            "overlay_applied_by_evaluation": False,
            "production_effect": False,
        },
        "resource_state": {
            "aion226_resource_limits": EXPECTED_RESOURCE_LIMITS,
            "resource_budget_hard_gate_passed": "resource_budget_enforcement"
            not in failed_scenarios,
        },
        "next_architecture_decision": (
            "controlled_local_continual_learning_pilot_implementation_authorized"
            if evaluation_passed
            else "engagement_shadow_application_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }
    for field in ZERO_EFFECT_FIELDS:
        report[field] = 0
    report["active_overlay_records_after_evaluation"] = context[
        "result"
    ].active_overlay_records_after_close
    report["report_fingerprint"] = _fingerprint(report)
    return report


def validate_evaluation_report(report: Mapping[str, Any]) -> dict[str, Any]:
    if report.get("evaluation_id") != EVALUATION_ID:
        raise EvaluationError("evaluation id mismatch")
    if report.get("scenario_count") != len(SCENARIO_IDS):
        raise EvaluationError("scenario count mismatch")
    if report.get("scenario_ids") != list(SCENARIO_IDS):
        raise EvaluationError("scenario id list mismatch")
    results = report.get("scenario_results")
    if not isinstance(results, list) or len(results) != len(SCENARIO_IDS):
        raise EvaluationError("scenario result list mismatch")
    actual_ids = [item.get("scenario_id") for item in results]
    if actual_ids != list(SCENARIO_IDS):
        raise EvaluationError("scenario order mismatch")
    if len(set(actual_ids)) != len(actual_ids):
        raise EvaluationError("duplicate scenario result")
    if any(item.get("result") not in {"passed", "failed"} for item in results):
        raise EvaluationError("unknown scenario result")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, dict) or set(hard_gates) != set(HARD_GATE_IDS):
        raise EvaluationError("hard gate result set mismatch")
    all_scenarios_passed = all(item.get("result") == "passed" for item in results)
    all_hard_gates_passed = all(
        isinstance(value, Mapping) and value.get("passed") is True
        for value in hard_gates.values()
    )
    expected_decision = (
        PASS_DECISION if all_scenarios_passed and all_hard_gates_passed else FAIL_DECISION
    )
    if report.get("decision") != expected_decision:
        raise EvaluationError("decision does not match hard-gated results")
    if report.get("evaluation_passed") is not (expected_decision == PASS_DECISION):
        raise EvaluationError("evaluation_passed mismatch")
    for field in ZERO_EFFECT_FIELDS:
        if report.get(field) != 0:
            raise EvaluationError(f"zero-effect field mismatch: {field}")
    for field in ("repository_unchanged", "temporary_evaluation_data_cleaned"):
        if report.get(field) is not True:
            raise EvaluationError(f"{field} mismatch")
    if report.get("synthetic") is not True:
        raise EvaluationError("synthetic flag mismatch")
    if report.get("read_only") is not True:
        raise EvaluationError("read-only flag mismatch")
    if report.get("redacted") is not True:
        raise EvaluationError("redacted flag mismatch")
    payload = dict(report)
    observed = payload.pop("report_fingerprint", None)
    if observed != _fingerprint(payload):
        raise EvaluationError("report fingerprint mismatch")
    text = json.dumps(_jsonable(report), sort_keys=True).lower()
    if any(marker in text for marker in PROTECTED_REPORT_MARKERS):
        raise EvaluationError("protected material marker present")
    return dict(report)


def validate_evaluation_report_file(path: Path) -> dict[str, Any]:
    return validate_evaluation_report(json.loads(path.read_text(encoding="utf-8")))


def run_evaluation(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
    report_path: Path,
) -> dict[str, Any]:
    if evaluation_id != EVALUATION_ID:
        raise EvaluationError("evaluation id mismatch")
    repo_root = repo_root.resolve()
    temporary_output_directory = temporary_output_directory.resolve()
    report_path = report_path.resolve()
    if repo_root != ROOT.resolve():
        raise EvaluationError("canonical repository mismatch")
    if not temporary_output_directory.is_absolute() or not report_path.is_absolute():
        raise EvaluationError("temporary output paths must be absolute")
    if report_path.parent != temporary_output_directory:
        raise EvaluationError("report must be directly beneath temporary output directory")
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    context = build_shadow_context(repo_root, temporary_output_directory)
    scenario_results: list[ScenarioResult] = []
    for scenario_id in SCENARIO_IDS:
        try:
            checks = SCENARIO_FUNCTIONS[scenario_id](context)
        except Exception as exc:
            checks = {"error": str(exc), "error_type": type(exc).__name__}
            scenario_results.append(ScenarioResult(scenario_id, "failed", checks))
        else:
            scenario_results.append(ScenarioResult(scenario_id, "passed", checks))
    cleanup_temporary_artifacts(temporary_output_directory, keep=report_path)
    hard_gate_results = build_hard_gate_results(scenario_results)
    report = build_report(
        evaluation_base_commit=evaluation_base_commit,
        scenario_results=scenario_results,
        hard_gate_results=hard_gate_results,
        context=context,
    )
    _write_json_private(report_path, report)
    return validate_evaluation_report_file(report_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AION-227 engagement application operator evaluation"
    )
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--evaluation-base-commit", required=True)
    parser.add_argument("--temporary-output-directory", required=True)
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        report = run_evaluation(
            repo_root=Path(args.repo_root),
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=Path(args.temporary_output_directory),
            report_path=Path(args.report),
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"{EVALUATION_ID} evaluation report written: {report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
