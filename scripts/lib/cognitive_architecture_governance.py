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
    _assert(
        payload["active_cognitive_implementation_authorization"]
        == AION185_AUTHORIZATION_ID,
        "wrong active authorization",
    )
    _assert(
        payload["active_cognitive_implementation_authorization_count"] == 1,
        "active authorization count must be one",
    )
    _assert(
        payload["program_state"] == "persistent_state_evaluated_world_model_authorized",
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
    world_model_auth = _find_record(records, "authorization_id", AION185_AUTHORIZATION_ID)
    _assert(
        world_model_auth["authorized_task"] == AION186_TASK_ID,
        "AION-185 must authorize AION-186",
    )
    _assert(world_model_auth["scope"] == AION186_SCOPE, "AION-186 scope mismatch")


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
    _assert(
        payload["active_cognitive_implementation_authorization"]
        == AION185_AUTHORIZATION_ID,
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
    _assert(len(records) == 2, "AION-185 must leave one closed and one active authorization")
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
    _assert(record["record_kind"] == "implementation_authorization", "bad authorization kind")
    _assert(record["authorization_active"] is True, "AION-185 authorization must be active")
    _assert(record["authorization_consumed"] is False, "AION-185 authorization must not be consumed")
    _assert(record["authorization_expired"] is False, "AION-185 authorization must not be expired")
    _assert(record["authorization_reusable"] is False, "AION-185 authorization must be non-reusable")
    _assert(record["implementation_task"] == AION186_TASK_ID, "implementation task mismatch")
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
    _assert(record["resource_limits"]["git_operations"] == 0, "runtime git operations must be zero")
    _assert(record["resource_limits"]["background_loops"] == 0, "background loops must be zero")
    _assert(
        record["benchmark_requirements"]["forbidden_side_effects"] == 0,
        "forbidden side effects must be zero",
    )
    for flag in FALSE_RUNTIME_FLAGS:
        _assert(record[flag] is False, f"{flag} must be false")
    _assert(
        any(
            path.startswith("services/brain-api/src/aion_brain/world_model")
            for path in record["allowed_source_paths"]
        ),
        "world model namespace not allowed",
    )
    _assert(".github/workflows/" in record["prohibited_source_paths"], "workflow prohibition missing")


def _find_record(records: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    matches = [record for record in records if record.get(key) == value]
    _assert(len(matches) == 1, f"expected one record with {key}={value}")
    return matches[0]


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
        program["active_cognitive_implementation_authorization"] == AION185_AUTHORIZATION_ID,
        "AION-184 must be evaluated before AION-186 authorization becomes active",
    )
    closed = _find_record(authorization["records"], "authorization_id", AION183_AUTHORIZATION_ID)
    _assert(closed["authorization_active"] is False, "AION-183 authorization must be closed")
    _assert(closed["authorization_consumed"] is True, "AION-183 authorization must be consumed")
    _assert(closed["authorization_closeout_evaluation"] == AION185_EVALUATION_ID, "closeout eval")
    active = _find_record(authorization["records"], "authorization_id", AION185_AUTHORIZATION_ID)
    _assert(active["implementation_task"] == AION186_TASK_ID, "active authorization must bind AION-186")
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
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            not any(relative.startswith(prefix) for prefix in AION184_PROHIBITED_PREFIXES),
            f"prohibited AION-184 path changed: {relative}",
        )
        _assert(
            _aion184_path_allowed(relative)
            or (closeout_paths_allowed and _aion185_path_allowed(relative)),
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
    active = _find_record(authorization["records"], "authorization_id", AION185_AUTHORIZATION_ID)
    _assert(active["authorization_active"] is True, "AION-185 authorization must be active")
    _assert(
        not (root / "services/brain-api/src/aion_brain/api/world_model.py").exists(),
        "AION-185 must not add a world-model API route",
    )
    _assert(
        not (root / "services/brain-api/src/aion_brain/world_model").exists(),
        "AION-185 must not implement world-model runtime source",
    )


def validate_persistent_state_closeout_no_go(root: Path) -> None:
    validate_persistent_state_closeout(root)
    validate_no_go(root)
    changed = _changed_files(root)
    for relative in sorted(changed):
        path = Path(relative)
        _assert(
            path.name not in AION184_BLOCKED_FILENAMES,
            f"blocked package or dependency file changed: {relative}",
        )
        _assert(
            not any(relative.startswith(prefix) for prefix in AION185_PROHIBITED_PREFIXES),
            f"prohibited AION-185 path changed: {relative}",
        )
        _assert(
            _aion185_path_allowed(relative),
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


def _aion184_path_allowed(relative: str) -> bool:
    return relative in AION184_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION184_ALLOWED_PREFIXES
    )


def _aion185_path_allowed(relative: str) -> bool:
    return relative in AION185_ALLOWED_EXACT_PATHS or any(
        relative.startswith(prefix) for prefix in AION185_ALLOWED_PREFIXES
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
    else:
        validate_persistent_state_closeout_no_go(root)
        print("cognitive persistent-state closeout no-go validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
