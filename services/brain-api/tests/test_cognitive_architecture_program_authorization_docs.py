"""AION-183 cognitive architecture authorization document tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION183_AUTHORIZATION_ID,
    AION184_TASK_ID,
    AION185_AUTHORIZATION_ID,
    AION185_TASK_ID,
    AION186_SCOPE,
    AION186_TASK_ID,
    AION187_AUTHORIZATION_ID,
    AION188_TASK_ID,
    AION189_AUTHORIZATION_ID,
    AION190_TASK_ID,
    AION191_AUTHORIZATION_ID,
    AION192_TASK_ID,
    AION193_AUTHORIZATION_ID,
    AION194_TASK_ID,
    AION195_AUTHORIZATION_ID,
    AION196_TASK_ID,
    PROGRAM_ID,
    validate_authorization_ledger,
    validate_no_go,
    validate_program_ledger,
    validate_repo,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-183.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "docs/cognitive-architecture/architecture-roadmap.md",
    "docs/cognitive-architecture/security-boundary.md",
    "docs/cognitive-architecture/operator-model.md",
    "examples/cognitive-architecture/aion-183-program-authorization.json",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/cognitive-architecture-authorization-check.sh",
    "scripts/cognitive-architecture-no-go-regression.sh",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_aion_183_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        assert (ROOT / relative).is_file(), relative


def test_aion_183_task_doc_contains_required_sections() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-183.md")
    for marker in (
        "## Task Purpose",
        "## Authorization ID",
        "## Exact Scope",
        "## Role Comparison",
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
        assert marker in text
    assert AION183_AUTHORIZATION_ID in text
    assert AION184_TASK_ID in text
    assert AION185_TASK_ID in text


def test_aion_183_ledgers_validate_and_close_authorization_after_aion_185() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")

    validate_program_ledger(program)
    validate_authorization_ledger(authorization)
    validate_repo(ROOT)
    validate_no_go(ROOT)

    assert program["program_id"] == PROGRAM_ID
    active_authorization = program["active_cognitive_implementation_authorization"]
    if active_authorization is None:
        assert program["active_cognitive_implementation_authorization_count"] == 0
    else:
        assert program["active_cognitive_implementation_authorization_count"] == 1
    assert active_authorization is None or active_authorization in {
        AION185_AUTHORIZATION_ID,
        AION187_AUTHORIZATION_ID,
        AION189_AUTHORIZATION_ID,
        AION191_AUTHORIZATION_ID,
        AION193_AUTHORIZATION_ID,
        AION195_AUTHORIZATION_ID,
    }
    assert program["tasks"][0]["task_id"] == "AION-183"
    assert program["tasks"][-1]["task_id"] == "AION-203"

    closed = authorization["records"][0]
    world_model = next(
        item
        for item in authorization["records"]
        if item["authorization_id"] == AION185_AUTHORIZATION_ID
    )
    assert closed["authorization_id"] == AION183_AUTHORIZATION_ID
    assert closed["implementation_task"] == AION184_TASK_ID
    assert closed["authorization_closed_by_task"] == AION185_TASK_ID
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False
    assert world_model["authorization_id"] == AION185_AUTHORIZATION_ID
    assert world_model["implementation_task"] == AION186_TASK_ID
    if world_model["record_kind"] == "implementation_authorization":
        assert world_model["scope"] == AION186_SCOPE
    if active_authorization == AION187_AUTHORIZATION_ID:
        active = next(
            item
            for item in authorization["records"]
            if item["authorization_id"] == AION187_AUTHORIZATION_ID
        )
        assert active["implementation_task"] == AION188_TASK_ID
    if active_authorization == AION189_AUTHORIZATION_ID:
        active = next(
            item
            for item in authorization["records"]
            if item["authorization_id"] == AION189_AUTHORIZATION_ID
        )
        assert active["implementation_task"] == AION190_TASK_ID
    if active_authorization == AION191_AUTHORIZATION_ID:
        active = next(
            item
            for item in authorization["records"]
            if item["authorization_id"] == AION191_AUTHORIZATION_ID
        )
        assert active["implementation_task"] == AION192_TASK_ID
    if active_authorization == AION193_AUTHORIZATION_ID:
        active = next(
            item
            for item in authorization["records"]
            if item["authorization_id"] == AION193_AUTHORIZATION_ID
        )
        assert active["implementation_task"] == AION194_TASK_ID
    if active_authorization == AION195_AUTHORIZATION_ID:
        active = next(
            item
            for item in authorization["records"]
            if item["authorization_id"] == AION195_AUTHORIZATION_ID
        )
        assert active["implementation_task"] == AION196_TASK_ID


def test_aion_183_preserves_runtime_disabled_boundaries() -> None:
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    closed = authorization["records"][0]
    active_authorization = authorization["active_cognitive_implementation_authorization"]
    records_to_check = (
        tuple(authorization["records"])
        if active_authorization is None
        else (
            next(
                item
                for item in authorization["records"]
                if item["authorization_id"] == active_authorization
            ),
        )
    )
    false_flags = (
        "runtime_effect",
        "source_modified",
        "git_mutated",
        "pull_request_created",
        "approval_created",
        "merged",
        "production_exposure",
        "model_weights_changed",
    )
    for key in false_flags:
        assert closed[key] is False
        for record in records_to_check:
            assert record[key] is False
    for record in records_to_check:
        if "resource_limits" not in record:
            continue
        assert record["resource_limits"]["network_calls"] == 0
        assert record["resource_limits"]["connector_calls"] == 0
        assert record["resource_limits"]["model_provider_calls"] == 0
        assert record["resource_limits"]["git_operations"] == 0
        assert record["resource_limits"]["background_loops"] == 0


def test_aion_183_docs_do_not_claim_subjective_state() -> None:
    for relative in (
        "docs/cognitive-architecture/tasks/AION-183.md",
        "docs/cognitive-architecture/architecture-roadmap.md",
        "docs/cognitive-architecture/security-boundary.md",
        "docs/cognitive-architecture/operator-model.md",
        "examples/cognitive-architecture/aion-183-program-authorization.json",
    ):
        lowered = _text(relative).lower()
        for term in (
            "sentient",
            "sentience",
            "conscious",
            "consciousness",
            "self-preservation",
            "ego",
        ):
            assert term not in lowered, f"{relative} contains {term}"
