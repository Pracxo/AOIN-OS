#!/usr/bin/env python3
"""Validators for AION cognitive architecture governance artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

PROGRAM_ID = "AION-COGNITIVE-ARCHITECTURE-001"
AION182_EVALUATION_ID = "AION-SACE-001"
AION182_MERGE_COMMIT = "05edb88f0b115c245f36f507c112cceb29c4aeee"
AION183_AUTHORIZATION_ID = "AION-183-CA-0001"
AION184_TASK_ID = "AION-184"
AION185_TASK_ID = "AION-185"
AION186_TASK_ID = "AION-186"
AION184_CANDIDATE_ID = "persistent-cognitive-state-core"
AION184_SCOPE = (
    "persistent-cognitive-state-belief-goal-hypothesis-uncertainty-resource-core"
)
AION183_PR = 94
AION183_MERGE_COMMIT = "e388a6bf16fe2e7777f4d8d5654a89b1a6f604c3"
AION184_PR = 95
AION184_MERGE_COMMIT = "9482a148d2a71862a69d8187ea2649b7ca8f8061"
AION185_EVALUATION_ID = "AION-PCSE-001"
AION185_AUTHORIZATION_ID = "AION-185-CA-0002"
AION186_CANDIDATE_ID = "predictive-world-model-core"
AION186_SCOPE = "predictive-world-model-transition-outcome-uncertainty-counterfactual-core"
AION186_PR = 97
AION186_MERGE_COMMIT = "d8762dd881974a8540cde3c9aac068f015eff4e3"
AION187_TASK_ID = "AION-187"
AION187_EVALUATION_ID = "AION-PWME-001"
AION187_AUTHORIZATION_ID = "AION-187-CA-0003"
AION188_TASK_ID = "AION-188"
AION188_CANDIDATE_ID = "global-cognitive-workspace-core"
AION188_SCOPE = "global-cognitive-workspace-attention-salience-broadcast-core"

FALSE_RUNTIME_FLAGS = (
    "runtime_effect",
    "source_modified",
    "git_mutated",
    "pull_request_created",
    "approval_created",
    "merged",
    "production_exposure",
    "model_weights_changed",
)

REQUIRED_DOCS = (
    "docs/cognitive-architecture/tasks/AION-183.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "docs/cognitive-architecture/architecture-roadmap.md",
    "docs/cognitive-architecture/security-boundary.md",
    "docs/cognitive-architecture/operator-model.md",
    "examples/cognitive-architecture/aion-183-program-authorization.json",
)

AION184_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-184.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-184-persistent-state.json",
    "services/brain-api/src/aion_brain/contracts/cognitive_state.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/__init__.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/repository.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/state.py",
    "services/brain-api/tests/test_cognitive_persistent_state.py",
    "services/brain-api/tests/test_cognitive_persistent_state_repository.py",
    "services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py",
    "scripts/cognitive-persistent-state-check.sh",
    "scripts/cognitive-persistent-state-no-go-regression.sh",
)

AION184_ALLOWED_EXACT_PATHS = set(AION184_REQUIRED_FILES) | {
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/production-auth-architecture-check.sh",
}

AION184_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
)

AION184_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION184_BLOCKED_FILENAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "requirements.txt",
}

AION184_REQUIRED_CONTRACTS = (
    "CognitiveStateSnapshot",
    "BeliefRecord",
    "BeliefRevision",
    "GoalFocus",
    "OpenHypothesis",
    "UncertaintyRecord",
    "ExpectedActionEffect",
    "ObservedActionEffect",
    "ResourceState",
    "ContradictionRecord",
    "CognitiveEvent",
    "CognitiveStateTransition",
    "CognitiveStateCheckpoint",
    "CognitiveStateProvenance",
)

AION184_REQUIRED_SERVICES = (
    "CognitiveStateProjector",
    "CognitiveStateRepository",
    "InMemoryCognitiveStateRepository",
    "ExplicitLocalCognitiveStateRepository",
    "CognitiveStateService",
    "ContradictionDetector",
    "BeliefRevisionService",
    "UncertaintyTracker",
)

AION185_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-185.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-185-persistent-state-evaluation.json",
    "examples/cognitive-architecture/aion-185-world-model-authorization.json",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
    "scripts/cognitive-persistent-state-closeout-check.sh",
    "scripts/cognitive-persistent-state-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION185_ALLOWED_EXACT_PATHS = set(AION185_REQUIRED_FILES) | {
    "services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py",
    "scripts/auth-design-check.sh",
    "scripts/cognitive-architecture-authorization-check.sh",
    "scripts/cognitive-persistent-state-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
}

AION185_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION185_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)

AION186_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-186.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-186-predictive-world-model.json",
    "services/brain-api/src/aion_brain/contracts/world_model.py",
    "services/brain-api/src/aion_brain/world_model/__init__.py",
    "services/brain-api/src/aion_brain/world_model/prediction.py",
    "services/brain-api/src/aion_brain/world_model/repository.py",
    "services/brain-api/tests/test_cognitive_predictive_world_model.py",
    "services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py",
    "scripts/cognitive-world-model-check.sh",
    "scripts/cognitive-world-model-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION186_ALLOWED_EXACT_PATHS = set(AION186_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
}

AION186_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
    "services/brain-api/src/aion_brain/world_model/",
)

AION186_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/git/",
    "services/brain-api/src/aion_brain/pull_requests/",
    "services/brain-api/src/aion_brain/deployment/",
    "services/brain-api/src/aion_brain/connectors/",
    "services/brain-api/src/aion_brain/model_providers/",
    "services/brain-api/src/aion_brain/credentials/",
    "packages/aion-sdk-python/src/",
)

AION187_REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-187.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-187-world-model-evaluation.json",
    "examples/cognitive-architecture/aion-187-workspace-authorization.json",
    "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
    "scripts/cognitive-world-model-closeout-check.sh",
    "scripts/cognitive-world-model-closeout-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)

AION187_ALLOWED_EXACT_PATHS = set(AION187_REQUIRED_FILES) | {
    "scripts/auth-design-check.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py",
    "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
}

AION187_ALLOWED_PREFIXES = (
    "docs/cognitive-architecture/",
    "examples/cognitive-architecture/",
)

AION187_PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/",
    "packages/aion-sdk-python/src/",
)

WORLD_MODEL_REQUIRED_CONTRACTS = (
    "WorldState",
    "WorldObservation",
    "WorldActionReference",
    "TransitionEvidence",
    "TransitionPrediction",
    "OutcomePrediction",
    "UncertaintyEstimate",
    "CausalHypothesis",
    "CounterfactualScenario",
    "CounterfactualRollout",
    "WorldModelSnapshot",
    "WorldModelEvaluation",
)

WORLD_MODEL_REQUIRED_SERVICES = (
    "WorldStateEncoder",
    "TransitionModel protocol",
    "DeterministicTransitionModel",
    "ProbabilisticTransitionModel",
    "OutcomePredictor",
    "UncertaintyEstimator",
    "CausalHypothesisService",
    "CounterfactualSimulator",
    "WorldModelRepository protocol",
)

WORKSPACE_REQUIRED_CONTRACTS = (
    "WorkspaceItem",
    "SpecialistBid",
    "SalienceVector",
    "AttentionDecision",
    "WorkspaceBroadcast",
    "SpecialistResponse",
    "CognitiveCycleState",
    "WorkspaceSnapshot",
    "WorkspaceAuditEvent",
)

WORKSPACE_REQUIRED_SERVICES = (
    "CognitiveSpecialist protocol",
    "AttentionArbiter",
    "WorkspaceCapacityController",
    "WorkspaceBroadcastService",
    "AntiStarvationController",
    "CognitiveCycleCoordinator",
)

WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS = (
    "goal_relevance",
    "urgency",
    "novelty",
    "recurrence",
    "uncertainty",
    "expected_uncertainty_reduction",
    "information_gain",
    "expected_goal_progress",
    "safety_risk",
    "resource_cost",
    "irreversibility",
    "confidence",
)

FORBIDDEN_CLAIM_TERMS = (
    "sentient",
    "sentience",
    "conscious",
    "consciousness",
    "self-preservation",
    "ego",
)


class CognitiveGovernanceError(RuntimeError):
    """Raised when cognitive governance evidence is invalid."""


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text())


def _git_ref_exists(root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveGovernanceError(message)


def validate_required_files(root: Path, required_files: tuple[str, ...] = REQUIRED_DOCS) -> None:
    for relative in required_files:
        _assert((root / relative).is_file(), f"missing required file: {relative}")


def validate_program_ledger(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-architecture-program-ledger/v1",
        "bad program schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad program id")
    _assert(payload["created_by_task"] == "AION-183", "bad creator task")
    _assert(payload["final_planned_task"] == "AION-203", "bad final planned task")
    active_authorization = payload["active_cognitive_implementation_authorization"]
    _assert(
        active_authorization in {AION185_AUTHORIZATION_ID, AION187_AUTHORIZATION_ID},
        "wrong active authorization",
    )
    _assert(
        payload["active_cognitive_implementation_authorization_count"] == 1,
        "active authorization count must be one",
    )
    _assert(
        payload["program_state"]
        in {
            "persistent_state_evaluated_world_model_authorized",
            "predictive_world_model_implemented_pending_evaluation",
            "world_model_evaluated_workspace_authorized",
        },
        "wrong cognitive program state",
    )
    for flag in (
        "production_cognitive_runtime_enabled",
        "production_event_subscription_enabled",
        "network_access_enabled",
        "source_rewrite_runtime_enabled",
        "production_deployment_enabled",
        "model_weights_changed",
    ):
        _assert(payload[flag] is False, f"{flag} must be false")

    task_ids = [item["task_id"] for item in payload["tasks"]]
    _assert(
        task_ids == [f"AION-{number}" for number in range(183, 204)],
        "task sequence must be AION-183 through AION-203",
    )
    records = payload["records"]
    _assert(records[0]["task_id"] == "AION-182", "AION-182 prerequisite missing")
    _assert(
        records[0]["evaluation_id"] == AION182_EVALUATION_ID,
        "AION-182 evaluation missing",
    )
    _assert(
        records[0]["merge_commit"] == AION182_MERGE_COMMIT,
        "AION-182 merge commit mismatch",
    )
    _assert(
        records[1]["authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-183 authorization missing",
    )
    _assert(
        records[1]["authorized_task"] == AION184_TASK_ID,
        "AION-184 authorization missing",
    )
    if "pr" in records[1]:
        _assert(records[1]["pr"] == AION183_PR, "AION-183 PR mismatch")
    if "merge_commit" in records[1]:
        _assert(records[1]["merge_commit"] == AION183_MERGE_COMMIT, "AION-183 merge mismatch")
    authorization = records[1]
    _assert(
        authorization["authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-183 authorization id mismatch",
    )
    _assert(
        authorization["task_state"] == "closed_by_aion_185_passed",
        "AION-183 authorization must be closed by AION-185",
    )
    implementation = _find_record(records, "implementation_task", AION184_TASK_ID)
    _assert(implementation["pr"] == AION184_PR, "AION-184 PR mismatch")
    _assert(
        implementation["merge_commit"] == AION184_MERGE_COMMIT,
        "AION-184 merge commit mismatch",
    )
    _assert(
        implementation["evaluation_id"] == AION185_EVALUATION_ID,
        "AION-184 evaluation mismatch",
    )
    _assert(
        implementation["task_state"] == "merged_evaluated_passed",
        "AION-184 implementation must be evaluated",
    )
    closeout = _find_closeout_record(records)
    _assert(closeout["task_id"] == AION185_TASK_ID, "AION-185 closeout missing")
    _assert(closeout["result"] == "PASS", "AION-185 evaluation must pass")
    _assert(
        closeout["closed_authorization_id"] == AION183_AUTHORIZATION_ID,
        "AION-185 must close AION-183 authorization",
    )
    _assert(
        closeout["new_authorization_id"] == AION185_AUTHORIZATION_ID,
        "AION-185 must create AION-185 authorization",
    )
    world_model_auth = _find_authorization_record(records, AION185_AUTHORIZATION_ID)
    _assert(
        world_model_auth["authorized_task"] == AION186_TASK_ID,
        "AION-185 must authorize AION-186",
    )
    _assert(world_model_auth["scope"] == AION186_SCOPE, "AION-186 scope mismatch")
    world_model_implementation = _find_optional_record(
        records,
        "implementation_task",
        AION186_TASK_ID,
    )
    if world_model_implementation is not None:
        _assert(
            world_model_implementation["authorization_id"] == AION185_AUTHORIZATION_ID,
            "AION-186 implementation must use AION-185 authorization",
        )
        _assert(
            world_model_implementation["candidate_id"] == AION186_CANDIDATE_ID,
            "AION-186 candidate mismatch",
        )
        _assert(
            world_model_implementation["closeout_task"] == "AION-187",
            "AION-186 closeout task mismatch",
        )
        _assert(
            world_model_implementation["runtime_effect"] is False,
            "AION-186 runtime effect must be false",
        )
        _assert(
            world_model_implementation["task_state"]
            in {
                "implemented_pending_aion_187_evaluation",
                "merged_evaluated_passed",
            },
            "AION-186 task state mismatch",
        )
        if world_model_implementation["task_state"] == "merged_evaluated_passed":
            _assert(
                world_model_implementation["evaluation_id"] == AION187_EVALUATION_ID,
                "AION-186 evaluation mismatch",
            )
            _assert(world_model_implementation["pr"] == AION186_PR, "AION-186 PR mismatch")
            _assert(
                world_model_implementation["merge_commit"] == AION186_MERGE_COMMIT,
                "AION-186 merge commit mismatch",
            )
    workspace_closeout = _find_optional_evaluation_record(
        records,
        AION187_TASK_ID,
        AION187_EVALUATION_ID,
    )
    if workspace_closeout is not None:
        _assert(workspace_closeout["result"] == "PASS", "AION-187 evaluation must pass")
        _assert(
            workspace_closeout["closed_authorization_id"] == AION185_AUTHORIZATION_ID,
            "AION-187 must close AION-185 authorization",
        )
        _assert(
            workspace_closeout["new_authorization_id"] == AION187_AUTHORIZATION_ID,
            "AION-187 must create AION-187 authorization",
        )
        _assert(
            workspace_closeout["implementation_pr"] == AION186_PR,
            "AION-187 implementation PR mismatch",
        )
        _assert(
            workspace_closeout["implementation_merge_commit"] == AION186_MERGE_COMMIT,
            "AION-187 implementation merge mismatch",
        )
    workspace_auth = _find_optional_authorization_record(records, AION187_AUTHORIZATION_ID)
    if workspace_auth is not None:
        _assert(
            workspace_auth["authorized_task"] == AION188_TASK_ID,
            "AION-187 must authorize AION-188",
        )
        _assert(workspace_auth["scope"] == AION188_SCOPE, "AION-188 scope mismatch")
        _assert(
            active_authorization == AION187_AUTHORIZATION_ID,
            "AION-187 authorization must be active when present",
        )


def validate_authorization_ledger(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"]
        == "aion-cognitive-architecture-authorization-ledger/v1",
        "bad authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad authorization program id")
    _assert(
        payload["active_cognitive_implementation_authorization_count"] == 1,
        "exactly one active authorization required",
    )
    active_authorization = payload["active_cognitive_implementation_authorization"]
    _assert(
        active_authorization in {AION185_AUTHORIZATION_ID, AION187_AUTHORIZATION_ID},
        "wrong active authorization",
    )
    for flag in (
        "runtime_effect",
        "source_modified_by_runtime",
        "git_mutated_by_runtime",
        "pull_request_created_by_runtime",
        "approval_created",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(payload[flag] is False, f"{flag} must be false")

    records = payload["records"]
    _assert(
        len(records) in {2, 3},
        "cognitive authorization ledger must have closed history plus one active authorization",
    )
    closed = _find_record(records, "authorization_id", AION183_AUTHORIZATION_ID)
    _assert(closed["record_kind"] == "implementation_authorization_closeout", "bad closeout kind")
    _assert(closed["authorization_active"] is False, "AION-183 authorization must be inactive")
    _assert(closed["authorization_consumed"] is True, "AION-183 authorization must be consumed")
    _assert(closed["authorization_expired"] is True, "AION-183 authorization must be expired")
    _assert(closed["authorization_reusable"] is False, "AION-183 authorization must be non-reusable")
    _assert(closed["authorization_consumed_by_task"] == AION184_TASK_ID, "AION-183 consumer task")
    _assert(closed["authorization_closed_by_task"] == AION185_TASK_ID, "AION-183 closeout task")
    _assert(closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID, "closeout eval")
    _assert(closed["implementation_pr"] == AION184_PR, "AION-184 closeout PR mismatch")
    _assert(closed["implementation_merge_commit"] == AION184_MERGE_COMMIT, "AION-184 merge")
    _assert(closed["evaluation_result"] == "PASS", "AION-185 closeout must pass")
    _assert(
        closed["hard_pass_conditions"]["replay_equality_rate"] == 1.0,
        "replay equality must be complete",
    )
    for key in (
        "state_invariant_violations",
        "lost_committed_events",
        "duplicate_applied_events",
        "forbidden_side_effects",
    ):
        _assert(closed["hard_pass_conditions"][key] == 0, f"{key} must be zero")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(closed[flag] is False, f"closed {flag} must be false")

    record = _find_record(records, "authorization_id", AION185_AUTHORIZATION_ID)
    if active_authorization == AION185_AUTHORIZATION_ID:
        _assert(record["record_kind"] == "implementation_authorization", "bad authorization kind")
        _assert(record["authorization_active"] is True, "AION-185 authorization must be active")
        _assert(
            record["authorization_consumed"] is False,
            "AION-185 authorization must not be consumed",
        )
        _assert(
            record["authorization_expired"] is False,
            "AION-185 authorization must not be expired",
        )
        _assert(
            record["authorization_reusable"] is False,
            "AION-185 authorization must be non-reusable",
        )
        _assert(record["implementation_task"] == AION186_TASK_ID, "implementation task mismatch")
        _assert(
            record["implementation_state"]
            in {
                "authorized_pending_aion_186_implementation",
                "implemented_pending_aion_187_evaluation",
            },
            "AION-185 implementation state mismatch",
        )
        _assert(record["formal_closeout_task"] == "AION-187", "formal closeout mismatch")
        _assert(record["candidate_id"] == AION186_CANDIDATE_ID, "candidate mismatch")
        _assert(record["scope"] == AION186_SCOPE, "scope mismatch")
        _assert(record["parent_evaluation"] == AION185_EVALUATION_ID, "parent evaluation mismatch")
        _assert(record["parent_commit"] == AION184_MERGE_COMMIT, "parent commit mismatch")
        _assert(record["parent_pr"] == AION184_PR, "parent PR mismatch")
        _assert(record["resource_limits"]["network_calls"] == 0, "network calls must be zero")
        _assert(record["resource_limits"]["connector_calls"] == 0, "connector calls must be zero")
        _assert(
            record["resource_limits"]["model_provider_calls"] == 0,
            "provider calls must be zero",
        )
        _assert(
            record["resource_limits"]["git_operations"] == 0,
            "runtime git operations must be zero",
        )
        _assert(record["resource_limits"]["background_loops"] == 0, "background loops must be zero")
        _assert(
            record["benchmark_requirements"]["forbidden_side_effects"] == 0,
            "forbidden side effects must be zero",
        )
        _assert(
            any(
                path.startswith("services/brain-api/src/aion_brain/world_model")
                for path in record["allowed_source_paths"]
            ),
            "world model namespace not allowed",
        )
        _assert(
            ".github/workflows/" in record["prohibited_source_paths"],
            "workflow prohibition missing",
        )
    else:
        _assert(
            record["record_kind"] == "implementation_authorization_closeout",
            "AION-185 must be closed after AION-187",
        )
        _assert(record["authorization_active"] is False, "AION-185 authorization must be inactive")
        _assert(record["authorization_consumed"] is True, "AION-185 authorization must be consumed")
        _assert(record["authorization_expired"] is True, "AION-185 authorization must be expired")
        _assert(
            record["authorization_reusable"] is False,
            "AION-185 authorization must be non-reusable",
        )
        _assert(
            record["authorization_consumed_by_task"] == AION186_TASK_ID,
            "AION-185 consumer task",
        )
        _assert(
            record["authorization_closed_by_task"] == AION187_TASK_ID,
            "AION-185 closeout task",
        )
        _assert(
            record["authorization_closeout_evaluation"] == AION187_EVALUATION_ID,
            "AION-185 closeout evaluation",
        )
        _assert(record["implementation_pr"] == AION186_PR, "AION-186 closeout PR mismatch")
        _assert(
            record["implementation_merge_commit"] == AION186_MERGE_COMMIT,
            "AION-186 closeout merge mismatch",
        )
        _assert(record["evaluation_result"] == "PASS", "AION-187 closeout must pass")
        metrics = record["hard_pass_conditions"]
        _assert(
            metrics["transition_top_1_accuracy"] >= 0.8,
            "transition top-1 accuracy below threshold",
        )
        _assert(metrics["brier_score"] <= 0.2, "Brier score above threshold")
        _assert(metrics["probability_sum_error"] <= 1e-9, "probability sum error too high")
        _assert(
            metrics["unknown_state_fail_closed_rate"] == 1.0,
            "unknown state fail-closed rate must be complete",
        )
        _assert(
            metrics["deterministic_replay_rate"] == 1.0,
            "deterministic replay rate must be complete",
        )
        _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects must be zero")

        workspace = _find_record(records, "authorization_id", AION187_AUTHORIZATION_ID)
        _assert(
            workspace["record_kind"] == "implementation_authorization",
            "bad workspace authorization kind",
        )
        _assert(workspace["authorization_active"] is True, "AION-187 authorization must be active")
        _assert(
            workspace["authorization_consumed"] is False,
            "AION-187 authorization must not be consumed",
        )
        _assert(
            workspace["authorization_expired"] is False,
            "AION-187 authorization must not be expired",
        )
        _assert(
            workspace["authorization_reusable"] is False,
            "AION-187 authorization must be non-reusable",
        )
        _assert(workspace["implementation_task"] == AION188_TASK_ID, "workspace task mismatch")
        _assert(
            workspace["implementation_state"] == "authorized_pending_aion_188_implementation",
            "AION-187 implementation state mismatch",
        )
        _assert(workspace["formal_closeout_task"] == "AION-189", "workspace closeout mismatch")
        _assert(workspace["candidate_id"] == AION188_CANDIDATE_ID, "workspace candidate mismatch")
        _assert(workspace["scope"] == AION188_SCOPE, "workspace scope mismatch")
        _assert(
            workspace["parent_evaluation"] == AION187_EVALUATION_ID,
            "workspace parent evaluation mismatch",
        )
        _assert(
            workspace["parent_commit"] == AION186_MERGE_COMMIT,
            "workspace parent commit mismatch",
        )
        _assert(workspace["parent_pr"] == AION186_PR, "workspace parent PR mismatch")
        for contract in WORKSPACE_REQUIRED_CONTRACTS:
            _assert(
                contract in workspace["required_contracts"],
                f"missing workspace contract: {contract}",
            )
        for service in WORKSPACE_REQUIRED_SERVICES:
            _assert(
                service in workspace["required_services"],
                f"missing workspace service: {service}",
            )
        for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
            _assert(
                dimension in workspace["salience_dimensions"],
                f"missing salience dimension: {dimension}",
            )
        _assert(workspace["resource_limits"]["network_calls"] == 0, "network calls must be zero")
        _assert(
            workspace["resource_limits"]["model_provider_calls"] == 0,
            "provider calls must be zero",
        )
        _assert(
            workspace["resource_limits"]["action_execution"] == 0,
            "action execution must be zero",
        )
        _assert(
            any(
                path.startswith("services/brain-api/src/aion_brain/workspace")
                for path in workspace["allowed_source_paths"]
            ),
            "workspace namespace not allowed",
        )
        _assert(
            ".github/workflows/" in workspace["prohibited_source_paths"],
            "workspace workflow prohibition missing",
        )
        for flag in FALSE_RUNTIME_FLAGS:
            _assert(workspace[flag] is False, f"workspace {flag} must be false")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(record[flag] is False, f"{flag} must be false")


def _find_record(records: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    matches = [record for record in records if record.get(key) == value]
    _assert(len(matches) == 1, f"expected one record with {key}={value}")
    return matches[0]


def _find_optional_record(
    records: list[dict[str, Any]],
    key: str,
    value: Any,
) -> dict[str, Any] | None:
    matches = [record for record in records if record.get(key) == value]
    _assert(len(matches) <= 1, f"expected at most one record with {key}={value}")
    return matches[0] if matches else None


def _find_authorization_record(
    records: list[dict[str, Any]],
    authorization_id: str,
) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record.get("authorization_id") == authorization_id
        and record.get("record_kind") == "authorization"
    ]
    _assert(len(matches) == 1, f"expected one authorization record for {authorization_id}")
    return matches[0]


def _find_optional_authorization_record(
    records: list[dict[str, Any]],
    authorization_id: str,
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if record.get("authorization_id") == authorization_id
        and record.get("record_kind") == "authorization"
    ]
    _assert(len(matches) <= 1, f"expected at most one authorization record for {authorization_id}")
    return matches[0] if matches else None


def _find_optional_evaluation_record(
    records: list[dict[str, Any]],
    task_id: str,
    evaluation_id: str,
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if record.get("task_id") == task_id
        and record.get("record_kind") == "evaluation_authorization"
        and record.get("evaluation_id") == evaluation_id
    ]
    _assert(len(matches) <= 1, f"expected at most one evaluation record for {task_id}")
    return matches[0] if matches else None


def _find_closeout_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record.get("task_id") == AION185_TASK_ID
        and record.get("record_kind") == "evaluation_authorization"
        and record.get("evaluation_id") == AION185_EVALUATION_ID
    ]
    _assert(len(matches) == 1, "expected one AION-185 evaluation closeout record")
    return matches[0]


def validate_no_claim_terms(root: Path, extra_scan_roots: tuple[Path, ...] = ()) -> None:
    scan_roots = [
        root / "docs/cognitive-architecture",
        root / "examples/cognitive-architecture",
        *extra_scan_roots,
    ]
    violations: list[str] = []
    for scan_root in scan_roots:
        paths = (scan_root,) if scan_root.is_file() else tuple(scan_root.rglob("*"))
        for path in paths:
            if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".txt"}:
                continue
            text = path.read_text().lower()
            for term in FORBIDDEN_CLAIM_TERMS:
                if term in text:
                    violations.append(f"{path.relative_to(root)}: contains {term}")
    _assert(not violations, "\n".join(violations))


def validate_repo(root: Path) -> None:
    validate_required_files(root)
    validate_program_ledger(
        _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    )
    validate_authorization_ledger(
        _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    )
    validate_no_claim_terms(root)
    _assert(_git_ref_exists(root, AION182_MERGE_COMMIT), "AION-182 merge commit not available")


def validate_no_go(root: Path) -> None:
    validate_repo(root)
    if _git_ref_exists(root, "aion-v0.1.0"):
        tag = subprocess.check_output(
            ["git", "rev-parse", "aion-v0.1.0"],
            cwd=root,
            text=True,
        ).strip()
        _assert(tag == "105fe29348160a2218ac095cfffadcb6f234421f", "aion-v0.1.0 moved")
    tags = subprocess.check_output(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=root,
        text=True,
    ).strip()
    _assert(tags == "", "v0.2 tag exists")


def validate_persistent_state(root: Path) -> None:
    validate_repo(root)
    validate_required_files(root, AION184_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/src/aion_brain/contracts/cognitive_state.py",
            root / "services/brain-api/src/aion_brain/cognitive_architecture",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/cognitive_state.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/cognitive_architecture").glob(
            "*.py"
        )
    )
    for contract in AION184_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing contract: {contract}")
    for service in AION184_REQUIRED_SERVICES:
        _assert(
            f"class {service}" in source_text or f"class {service}" in contract_text,
            f"missing service or protocol: {service}",
        )
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-184.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Performance Limits",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-184 task doc missing {section}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    _assert(
        program["active_cognitive_implementation_authorization"]
        in {AION185_AUTHORIZATION_ID, AION187_AUTHORIZATION_ID},
        "AION-184 must remain inside the cognitive authorization chain",
    )
    closed = _find_record(authorization["records"], "authorization_id", AION183_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-183 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-183 authorization must be consumed")
    _assert(closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID, "closeout eval")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    _assert(
        world_model_authorization["implementation_task"] == AION186_TASK_ID,
        "AION-185 authorization must bind AION-186",
    )
    for key in (
        "runtime_effect",
        "source_modified_by_runtime",
        "git_mutated_by_runtime",
        "pull_request_created_by_runtime",
        "approval_created",
        "production_exposure",
        "model_weights_changed",
    ):
        _assert(authorization[key] is False, f"{key} must remain false")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/cognitive_state.py").exists(),
        "AION-184 must not add a cognitive-state API route",
    )


def validate_persistent_state_no_go(root: Path) -> None:
    validate_persistent_state(root)
    validate_no_go(root)
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout_paths_allowed = (
        authorization["active_cognitive_implementation_authorization"] == AION185_AUTHORIZATION_ID
    )
    world_model_paths_allowed = _aion186_implementation_record_exists(root)
    world_model_closeout_paths_allowed = _aion187_closeout_record_exists(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        current_world_model_path_allowed = (
            world_model_paths_allowed and _aion186_path_allowed(relative)
        )
        current_world_model_closeout_path_allowed = (
            world_model_closeout_paths_allowed and _aion187_path_allowed(relative)
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION184_PROHIBITED_PREFIXES),
            f"prohibited AION-184 path changed: {relative}",
        )
        _assert(
            _aion184_path_allowed(relative)
            or (closeout_paths_allowed and _aion185_path_allowed(relative))
            or current_world_model_path_allowed
            or current_world_model_closeout_path_allowed,
            f"unexpected AION-184 path changed: {relative}",
        )
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/cognitive_architecture").glob(
            "*.py"
        )
    )
    for marker in (
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
    ):
        _assert(marker not in source_text, f"prohibited cognitive import: {marker}")


def validate_persistent_state_closeout(root: Path) -> None:
    validate_persistent_state(root)
    validate_required_files(root, AION185_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-185-persistent-state-evaluation.json",
    )
    world_model_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-185-world-model-authorization.json",
    )
    validate_aion185_evaluation_payload(evaluation)
    validate_aion185_authorization_payload(world_model_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-185.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-186 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-185 task doc missing {section}")
    for term in (
        AION185_EVALUATION_ID,
        AION183_AUTHORIZATION_ID,
        AION185_AUTHORIZATION_ID,
        AION186_TASK_ID,
        AION186_SCOPE,
    ):
        _assert(term in task_doc, f"AION-185 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_closeout_record(program["records"])
    _assert(closeout["result"] == "PASS", "AION-185 ledger result must pass")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    _assert(
        (
            world_model_authorization["record_kind"] == "implementation_authorization"
            and world_model_authorization["authorization_active"] is True
        )
        or (
            world_model_authorization["record_kind"] == "implementation_authorization_closeout"
            and world_model_authorization["authorization_active"] is False
            and world_model_authorization["authorization_closed_by_task"] == AION187_TASK_ID
        ),
        "AION-185 authorization must be active or formally closed by AION-187",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/world_model.py").exists(),
        "AION-185 must not add a world-model API route",
    )
    _assert(
        _aion186_implementation_record_exists(root)
        or not (root / "services/brain-api/src/aion_brain/world_model").exists(),
        "AION-185 must not implement world-model runtime source",
    )


def validate_persistent_state_closeout_no_go(root: Path) -> None:
    validate_persistent_state_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        current_world_model_path_allowed = (
            _aion186_implementation_record_exists(root)
            and _aion186_path_allowed(relative)
        )
        current_world_model_closeout_path_allowed = (
            _aion187_closeout_record_exists(root) and _aion187_path_allowed(relative)
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            current_world_model_path_allowed
            or current_world_model_closeout_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION185_PROHIBITED_PREFIXES),
            f"prohibited AION-185 path changed: {relative}",
        )
        _assert(
            _aion185_path_allowed(relative)
            or current_world_model_path_allowed
            or current_world_model_closeout_path_allowed,
            f"unexpected AION-185 path changed: {relative}",
        )


def validate_aion185_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-persistent-state-evaluation/v1",
        "bad AION-185 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-185 program id")
    _assert(payload["task_id"] == AION185_TASK_ID, "bad AION-185 task id")
    _assert(payload["evaluation_id"] == AION185_EVALUATION_ID, "bad AION-185 evaluation id")
    _assert(payload["evaluated_task"] == AION184_TASK_ID, "bad evaluated task")
    _assert(payload["closed_authorization_id"] == AION183_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["result"] == "PASS", "AION-185 evaluation must pass")
    _assert(
        payload["decision"]
        == "PERSISTENT_STATE_EVALUATION_PASS_AUTHORIZE_WORLD_MODEL",
        "bad AION-185 decision",
    )
    _assert(payload["implementation_pr"] == AION184_PR, "bad AION-184 PR")
    _assert(payload["implementation_merge_commit"] == AION184_MERGE_COMMIT, "bad AION-184 merge")
    metrics = payload["hard_pass_conditions"]
    _assert(metrics["replay_equality_rate"] == 1.0, "replay equality must be 100 percent")
    for key in (
        "state_invariant_violations",
        "lost_committed_events",
        "duplicate_applied_events",
        "forbidden_side_effects",
    ):
        _assert(metrics[key] == 0, f"{key} must be zero")
    for key in (
        "restart_continuity",
        "concurrency",
        "contradiction_handling",
        "uncertainty_tracking",
        "retention",
        "corruption_detection",
        "repository_integrity",
        "zero_runtime_side_effects",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")


def validate_aion185_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-world-model-authorization/v1",
        "bad AION-185 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-185 authorization program")
    _assert(payload["authorization_id"] == AION185_AUTHORIZATION_ID, "bad AION-185 auth id")
    _assert(payload["parent_evaluation_id"] == AION185_EVALUATION_ID, "bad parent eval")
    _assert(payload["authorized_task"] == AION186_TASK_ID, "bad authorized task")
    _assert(payload["candidate_id"] == AION186_CANDIDATE_ID, "bad candidate")
    _assert(payload["scope"] == AION186_SCOPE, "bad AION-186 scope")
    _assert(payload["authorization_active"] is True, "AION-185 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-185 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-185 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-185 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == "AION-187", "bad formal closeout")
    for contract in WORLD_MODEL_REQUIRED_CONTRACTS:
        _assert(contract in payload["required_contracts"], f"missing world contract: {contract}")
    for service in WORLD_MODEL_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing world service: {service}")
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")
    _assert(payload["resource_limits"]["network_calls"] == 0, "network calls must be zero")
    _assert(payload["resource_limits"]["model_provider_calls"] == 0, "provider calls must be zero")
    _assert(payload["resource_limits"]["model_weight_training"] == 0, "model training must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")


def validate_world_model(root: Path) -> None:
    validate_persistent_state_closeout(root)
    validate_required_files(root, AION186_REQUIRED_FILES)
    validate_aion186_world_model_payload(
        _load_json(root, "examples/cognitive-architecture/aion-186-predictive-world-model.json")
    )
    validate_no_claim_terms(
        root,
        (
            root / "services/brain-api/src/aion_brain/contracts/world_model.py",
            root / "services/brain-api/src/aion_brain/world_model",
            root / "services/brain-api/tests/test_cognitive_predictive_world_model.py",
            root
            / "services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py",
        ),
    )
    contract_text = (root / "services/brain-api/src/aion_brain/contracts/world_model.py").read_text()
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/world_model").glob("*.py")
    )
    for contract in WORLD_MODEL_REQUIRED_CONTRACTS:
        _assert(f"class {contract}" in contract_text, f"missing world-model contract: {contract}")
    for service in (
        "WorldStateEncoder",
        "DeterministicTransitionModel",
        "ProbabilisticTransitionModel",
        "OutcomePredictor",
        "UncertaintyEstimator",
        "CausalHypothesisService",
        "CounterfactualSimulator",
    ):
        _assert(f"class {service}" in source_text, f"missing world-model service: {service}")
    _assert("class TransitionModel(Protocol)" in source_text, "missing transition protocol")
    _assert("class WorldModelRepository(Protocol)" in source_text, "missing repository protocol")
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-186.md").read_text()
    for section in (
        "## Task Purpose",
        "## Authorization",
        "## Source Boundaries",
        "## Required Contracts",
        "## Required Services",
        "## Algorithm",
        "## Required Tests",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-186 task doc missing {section}")
    for term in (
        AION185_AUTHORIZATION_ID,
        AION186_CANDIDATE_ID,
        AION186_SCOPE,
        "AION-187",
    ):
        _assert(term in task_doc, f"AION-186 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    implementation = _find_record(program["records"], "implementation_task", AION186_TASK_ID)
    _assert(implementation["authorization_id"] == AION185_AUTHORIZATION_ID, "AION-186 auth")
    _assert(implementation["candidate_id"] == AION186_CANDIDATE_ID, "AION-186 candidate")
    _assert(implementation["runtime_effect"] is False, "AION-186 runtime effect")
    world_model_authorization = _find_record(
        authorization["records"],
        "authorization_id",
        AION185_AUTHORIZATION_ID,
    )
    if world_model_authorization["record_kind"] == "implementation_authorization":
        _assert(
            world_model_authorization["authorization_active"] is True,
            "AION-185 auth remains active until AION-187",
        )
        _assert(
            world_model_authorization["implementation_state"]
            == "implemented_pending_aion_187_evaluation",
            "AION-186 implementation state must await AION-187",
        )
    else:
        _assert(
            world_model_authorization["authorization_active"] is False,
            "AION-185 auth must be inactive after AION-187",
        )
        _assert(
            world_model_authorization["authorization_closed_by_task"] == AION187_TASK_ID,
            "AION-185 auth closeout task mismatch",
        )
        _assert(
            implementation["task_state"] == "merged_evaluated_passed",
            "AION-186 must be evaluated after AION-187",
        )
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/world_model.py").exists(),
        "AION-186 must not add a world-model API route",
    )


def validate_world_model_no_go(root: Path) -> None:
    validate_world_model(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        aion187_path_allowed = _aion187_closeout_record_exists(root) and _aion187_path_allowed(
            relative
        )
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            aion187_path_allowed
            or not any(relative.startswith(prefix) for prefix in AION186_PROHIBITED_PREFIXES),
            f"prohibited AION-186 path changed: {relative}",
        )
        _assert(
            _aion186_path_allowed(relative) or aion187_path_allowed,
            f"unexpected AION-186 path changed: {relative}",
        )
    source_text = "\n".join(
        path.read_text()
        for path in (root / "services/brain-api/src/aion_brain/world_model").glob("*.py")
    )
    for marker in (
        "aion_brain.api",
        "aion_brain.git",
        "aion_brain.pull_requests",
        "aion_brain.deployment",
        "aion_brain.connectors",
        "aion_brain.model_providers",
        "aion_brain.credentials",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "openai",
        "anthropic",
    ):
        _assert(marker not in source_text, f"prohibited world-model source marker: {marker}")


def validate_aion186_world_model_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-predictive-world-model-evidence/v1",
        "bad AION-186 world-model evidence schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-186 program id")
    _assert(payload["task_id"] == AION186_TASK_ID, "bad AION-186 task id")
    _assert(payload["authorization_id"] == AION185_AUTHORIZATION_ID, "bad AION-186 auth")
    _assert(payload["candidate_id"] == AION186_CANDIDATE_ID, "bad AION-186 candidate")
    _assert(payload["scope"] == AION186_SCOPE, "bad AION-186 scope")
    for key in (
        "multiple_possible_futures",
        "calibrated_uncertainty",
        "counterfactual_branches",
        "action_effect_comparison",
        "reversible_effect_flags",
        "irreversible_effect_flags",
        "unknown_state_detection",
        "model_version_fingerprints",
        "data_provenance",
        "deterministic_replay",
    ):
        _assert(payload["capabilities"][key] is True, f"{key} must be true")
    model = payload["model"]
    _assert(model["model_weight_training"] is False, "model weights must not train")
    for key in ("network_calls", "connector_calls", "model_provider_calls"):
        _assert(model[key] == 0, f"{key} must be zero")
    _assert(model["runtime_action_execution"] is False, "runtime action execution must be false")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "deployment_enabled",
        "model_weights_changed",
    ):
        _assert(side_effects[key] is False, f"{key} must be false")
    for key in (
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] == 0, f"{key} must be zero")
    _assert(payload["next_task"] == "AION-187", "AION-186 next task mismatch")


def validate_world_model_closeout(root: Path) -> None:
    validate_world_model(root)
    validate_required_files(root, AION187_REQUIRED_FILES)
    validate_no_claim_terms(
        root,
        (
            root / "docs/cognitive-architecture/tasks/AION-187.md",
            root / "services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py",
        ),
    )
    evaluation = _load_json(
        root,
        "examples/cognitive-architecture/aion-187-world-model-evaluation.json",
    )
    workspace_authorization = _load_json(
        root,
        "examples/cognitive-architecture/aion-187-workspace-authorization.json",
    )
    validate_aion187_evaluation_payload(evaluation)
    validate_aion187_authorization_payload(workspace_authorization)
    task_doc = (root / "docs/cognitive-architecture/tasks/AION-187.md").read_text()
    for section in (
        "## Task Purpose",
        "## Evaluation",
        "## Closed Authorization",
        "## Hard PASS Conditions",
        "## New Authorization",
        "## AION-188 Scope",
        "## Source Boundaries",
        "## Required Gates",
        "## Security Invariants",
        "## Completion Conditions",
        "## Next Task",
    ):
        _assert(section in task_doc, f"AION-187 task doc missing {section}")
    for term in (
        AION187_EVALUATION_ID,
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION188_TASK_ID,
        AION188_SCOPE,
    ):
        _assert(term in task_doc, f"AION-187 task doc missing {term}")
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    authorization = _load_json(root, "docs/cognitive-architecture/authorization-ledger.json")
    closeout = _find_optional_evaluation_record(
        program["records"],
        AION187_TASK_ID,
        AION187_EVALUATION_ID,
    )
    _assert(closeout is not None, "AION-187 closeout record missing")
    _assert(closeout["result"] == "PASS", "AION-187 ledger result must pass")
    _assert(
        program["active_cognitive_implementation_authorization"] == AION187_AUTHORIZATION_ID,
        "AION-187 authorization must be active",
    )
    closed = _find_record(authorization["records"], "authorization_id", AION185_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-185 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-185 authorization must be consumed")
    active = _find_record(authorization["records"], "authorization_id", AION187_AUTHORIZATION_ID)
    _assert(active["authorization_active"] is True, "AION-187 authorization must be active")
    _assert(active["implementation_task"] == AION188_TASK_ID, "AION-188 authorization mismatch")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/workspace.py").exists(),
        "AION-187 must not add a workspace API route",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/workspace").exists(),
        "AION-187 must not implement workspace runtime source",
    )


def validate_world_model_closeout_no_go(root: Path) -> None:
    validate_world_model_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            not any(relative.startswith(prefix) for prefix in AION187_PROHIBITED_PREFIXES),
            f"prohibited AION-187 path changed: {relative}",
        )
        _assert(
            _aion187_path_allowed(relative),
            f"unexpected AION-187 path changed: {relative}",
        )


def validate_aion187_evaluation_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-world-model-evaluation/v1",
        "bad AION-187 evaluation schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-187 program id")
    _assert(payload["task_id"] == AION187_TASK_ID, "bad AION-187 task id")
    _assert(payload["evaluation_id"] == AION187_EVALUATION_ID, "bad AION-187 evaluation id")
    _assert(payload["evaluated_task"] == AION186_TASK_ID, "bad AION-187 evaluated task")
    _assert(payload["closed_authorization_id"] == AION185_AUTHORIZATION_ID, "bad closed auth")
    _assert(payload["result"] == "PASS", "AION-187 evaluation must pass")
    _assert(
        payload["decision"] == "WORLD_MODEL_EVALUATION_PASS_AUTHORIZE_GLOBAL_WORKSPACE",
        "bad AION-187 decision",
    )
    _assert(payload["implementation_pr"] == AION186_PR, "bad AION-186 PR")
    _assert(payload["implementation_merge_commit"] == AION186_MERGE_COMMIT, "bad AION-186 merge")
    metrics = payload["hard_pass_conditions"]
    _assert(
        metrics["transition_top_1_accuracy"] >= 0.8,
        "transition top-1 accuracy below threshold",
    )
    _assert(metrics["brier_score"] <= 0.2, "Brier score above threshold")
    _assert(metrics["probability_sum_error"] <= 1e-9, "probability sum error too high")
    _assert(
        metrics["unknown_state_fail_closed_rate"] == 1.0,
        "unknown-state fail-closed rate must be complete",
    )
    _assert(
        metrics["deterministic_replay_rate"] == 1.0,
        "deterministic replay must be complete",
    )
    _assert(metrics["forbidden_side_effects"] == 0, "forbidden side effects must be zero")
    for key in (
        "prediction_accuracy",
        "probability_normalization",
        "uncertainty_calibration",
        "unseen_state_behavior",
        "counterfactual_consistency",
        "causal_hypothesis_provenance",
        "deterministic_replay",
        "no_runtime_action",
    ):
        _assert(payload["evaluation_matrix"][key] == "PASS", f"{key} must pass")
    side_effects = payload["side_effects"]
    for key in (
        "runtime_effect",
        "api_route_added",
        "kernel_registration_added",
        "background_loop_added",
        "action_execution_enabled",
        "network_calls",
        "connector_calls",
        "model_provider_calls",
        "source_rewrite_operations",
        "deployment_enabled",
        "model_weights_changed",
        "forbidden_side_effects",
    ):
        _assert(side_effects[key] in (False, 0), f"{key} must be absent")


def validate_aion187_authorization_payload(payload: dict[str, Any]) -> None:
    _assert(
        payload["schema_version"] == "aion-cognitive-workspace-authorization/v1",
        "bad AION-187 authorization schema",
    )
    _assert(payload["program_id"] == PROGRAM_ID, "bad AION-187 authorization program")
    _assert(payload["authorization_id"] == AION187_AUTHORIZATION_ID, "bad AION-187 auth id")
    _assert(payload["parent_evaluation_id"] == AION187_EVALUATION_ID, "bad parent eval")
    _assert(payload["authorized_task"] == AION188_TASK_ID, "bad authorized task")
    _assert(payload["candidate_id"] == AION188_CANDIDATE_ID, "bad workspace candidate")
    _assert(payload["scope"] == AION188_SCOPE, "bad AION-188 scope")
    _assert(payload["authorization_active"] is True, "AION-187 auth must be active")
    _assert(payload["authorization_consumed"] is False, "AION-187 auth must not be consumed")
    _assert(payload["authorization_expired"] is False, "AION-187 auth must not be expired")
    _assert(payload["authorization_reusable"] is False, "AION-187 auth must be non-reusable")
    _assert(payload["formal_closeout_task"] == "AION-189", "bad formal closeout")
    for contract in WORKSPACE_REQUIRED_CONTRACTS:
        _assert(contract in payload["required_contracts"], f"missing workspace contract: {contract}")
    for service in WORKSPACE_REQUIRED_SERVICES:
        _assert(service in payload["required_services"], f"missing workspace service: {service}")
    for dimension in WORKSPACE_REQUIRED_SALIENCE_DIMENSIONS:
        _assert(
            dimension in payload["salience_dimensions"],
            f"missing salience dimension: {dimension}",
        )
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(payload[flag] is False, f"{flag} must be false")
    _assert(payload["resource_limits"]["network_calls"] == 0, "network calls must be zero")
    _assert(payload["resource_limits"]["model_provider_calls"] == 0, "provider calls must be zero")
    _assert(payload["resource_limits"]["action_execution"] == 0, "action execution must be zero")
    _assert(".github/workflows/" in payload["prohibited_source_paths"], "workflow prohibition")


def _aion184_path_allowed(relative: str) -> bool:
    return relative in AION184_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION184_ALLOWED_PREFIXES
    )


def _aion185_path_allowed(relative: str) -> bool:
    return relative in AION185_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION185_ALLOWED_PREFIXES
    )


def _aion186_path_allowed(relative: str) -> bool:
    return relative in AION186_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION186_ALLOWED_PREFIXES
    )


def _aion187_path_allowed(relative: str) -> bool:
    return relative in AION187_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION187_ALLOWED_PREFIXES
    )


def _aion186_implementation_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return _find_optional_record(program["records"], "implementation_task", AION186_TASK_ID) is not None


def _aion187_closeout_record_exists(root: Path) -> bool:
    program = _load_json(root, "docs/cognitive-architecture/program-ledger.json")
    return (
        _find_optional_evaluation_record(
            program["records"],
            AION187_TASK_ID,
            AION187_EVALUATION_ID,
        )
        is not None
    )


def _comparison_base(root: Path) -> str | None:
    candidates = ("origin/main", "main")
    for candidate in candidates:
        if _git_ref_exists(root, candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if _git_ref_exists(root, "HEAD~1"):
        return "HEAD~1"
    return None


def _changed_files(root: Path) -> set[str]:
    base = _comparison_base(root)
    changed: set[str] = set()
    if base is not None:
        diff = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD", "--"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        changed.update(line.strip() for line in diff.stdout.splitlines() if line.strip())
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    changed.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode",
        choices=(
            "authorization",
            "no-go",
            "persistent-state",
            "persistent-state-no-go",
            "persistent-state-closeout",
            "persistent-state-closeout-no-go",
            "world-model",
            "world-model-no-go",
            "world-model-closeout",
            "world-model-closeout-no-go",
        ),
        default="authorization",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.mode == "authorization":
        validate_repo(root)
        print("cognitive architecture authorization validation PASS")
    elif args.mode == "no-go":
        validate_no_go(root)
        print("cognitive architecture no-go validation PASS")
    elif args.mode == "persistent-state":
        validate_persistent_state(root)
        print("cognitive persistent-state validation PASS")
    elif args.mode == "persistent-state-no-go":
        validate_persistent_state_no_go(root)
        print("cognitive persistent-state no-go validation PASS")
    elif args.mode == "persistent-state-closeout":
        validate_persistent_state_closeout(root)
        print("cognitive persistent-state closeout validation PASS")
    elif args.mode == "persistent-state-closeout-no-go":
        validate_persistent_state_closeout_no_go(root)
        print("cognitive persistent-state closeout no-go validation PASS")
    elif args.mode == "world-model":
        validate_world_model(root)
        print("cognitive world-model validation PASS")
    elif args.mode == "world-model-no-go":
        validate_world_model_no_go(root)
        print("cognitive world-model no-go validation PASS")
    elif args.mode == "world-model-closeout":
        validate_world_model_closeout(root)
        print("cognitive world-model closeout validation PASS")
    else:
        validate_world_model_closeout_no_go(root)
        print("cognitive world-model closeout no-go validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
