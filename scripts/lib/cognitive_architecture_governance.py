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
AION184_CANDIDATE_ID = "persistent-cognitive-state-core"
AION184_SCOPE = (
    "persistent-cognitive-state-belief-goal-hypothesis-uncertainty-resource-core"
)

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


def validate_required_files(root: Path) -> None:
    for relative in REQUIRED_DOCS:
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
        == AION183_AUTHORIZATION_ID,
        "wrong active authorization",
    )
    _assert(
        payload["active_cognitive_implementation_authorization_count"] == 1,
        "active authorization count must be one",
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
        == AION183_AUTHORIZATION_ID,
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
    _assert(len(records) == 1, "AION-183 must create exactly one authorization")
    record = records[0]
    _assert(record["authorization_id"] == AION183_AUTHORIZATION_ID, "authorization id mismatch")
    _assert(record["authorization_active"] is True, "authorization must be active")
    _assert(record["authorization_consumed"] is False, "authorization must not be consumed")
    _assert(record["authorization_expired"] is False, "authorization must not be expired")
    _assert(record["authorization_reusable"] is False, "authorization must be non-reusable")
    _assert(record["implementation_task"] == AION184_TASK_ID, "implementation task mismatch")
    _assert(record["formal_closeout_task"] == AION185_TASK_ID, "formal closeout mismatch")
    _assert(record["candidate_id"] == AION184_CANDIDATE_ID, "candidate mismatch")
    _assert(record["scope"] == AION184_SCOPE, "scope mismatch")
    _assert(record["parent_evaluation"] == AION182_EVALUATION_ID, "parent evaluation mismatch")
    _assert(record["parent_commit"] == AION182_MERGE_COMMIT, "parent commit mismatch")
    _assert(record["parent_pr"] == 93, "parent PR mismatch")
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
            path.startswith("services/brain-api/src/aion_brain/cognitive_architecture")
            for path in record["allowed_source_paths"]
        ),
        "cognitive namespace not allowed",
    )
    _assert(".github/workflows/" in record["prohibited_source_paths"], "workflow prohibition missing")


def validate_no_claim_terms(root: Path) -> None:
    scan_roots = [
        root / "docs/cognitive-architecture",
        root / "examples/cognitive-architecture",
    ]
    violations: list[str] = []
    for scan_root in scan_roots:
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".txt"}:
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=("authorization", "no-go"), default="authorization")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.mode == "authorization":
        validate_repo(root)
        print("cognitive architecture authorization validation PASS")
    else:
        validate_no_go(root)
        print("cognitive architecture no-go validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
