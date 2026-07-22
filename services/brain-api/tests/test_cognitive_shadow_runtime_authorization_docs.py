"""AION-198 cognitive shadow-runtime authorization tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from cognitive_architecture_governance import (  # noqa: E402
    AION197_DECISION,
    AION197_EVALUATION_ID,
    AION197_MERGE_COMMIT,
    AION197_PR,
    AION197_TASK_ID,
    AION198_AUTHORIZATION_ID,
    AION198_PROGRAM_STATE,
    AION198_TASK_ID,
    AION199_CANDIDATE_ID,
    AION199_IMPLEMENTATION_BRANCH,
    AION199_PROGRAM_STATE,
    AION199_SCOPE,
    AION199_TASK_ID,
    AION200_EVALUATION_ID,
    AION200_TASK_ID,
    PROGRAM_ID,
    SHADOW_RUNTIME_AUTHORIZED_CAPABILITIES,
    SHADOW_RUNTIME_PROHIBITED_BEHAVIORS,
    SHADOW_RUNTIME_REQUIRED_CONTRACTS,
    SHADOW_RUNTIME_REQUIRED_CYCLE,
    SHADOW_RUNTIME_REQUIRED_SERVICES,
    validate_aion198_authorization_payload,
    validate_shadow_runtime_authorization,
    validate_shadow_runtime_authorization_no_go,
)

REQUIRED_FILES = (
    "docs/cognitive-architecture/tasks/AION-198.md",
    "docs/cognitive-architecture/program-ledger.json",
    "docs/cognitive-architecture/authorization-ledger.json",
    "examples/cognitive-architecture/aion-198-shadow-runtime-authorization.json",
    "services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py",
    "scripts/cognitive-shadow-runtime-authorization-check.sh",
    "scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def test_aion_198_required_files_exist() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), f"not executable: {relative}"


def test_aion_198_task_doc_contains_required_sections_and_terms() -> None:
    text = _text("docs/cognitive-architecture/tasks/AION-198.md")
    for section in (
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
        assert section in text
    for term in (
        AION198_AUTHORIZATION_ID,
        AION197_EVALUATION_ID,
        AION197_MERGE_COMMIT,
        AION199_TASK_ID,
        AION199_SCOPE,
        AION200_EVALUATION_ID,
    ):
        assert term in text


def test_aion_198_authorization_payload_matches_runtime_boundary() -> None:
    payload = _json("examples/cognitive-architecture/aion-198-shadow-runtime-authorization.json")
    validate_aion198_authorization_payload(payload)

    assert payload["program_id"] == PROGRAM_ID
    assert payload["task_id"] == AION198_TASK_ID
    assert payload["authorization_id"] == AION198_AUTHORIZATION_ID
    assert payload["parent_task"] == AION197_TASK_ID
    assert payload["parent_evaluation_id"] == AION197_EVALUATION_ID
    assert payload["parent_pr"] == AION197_PR
    assert payload["parent_commit"] == AION197_MERGE_COMMIT
    assert payload["parent_decision"] == AION197_DECISION
    assert payload["authorized_task"] == AION199_TASK_ID
    assert payload["implementation_branch"] == AION199_IMPLEMENTATION_BRANCH
    assert payload["candidate_id"] == AION199_CANDIDATE_ID
    assert payload["scope"] == AION199_SCOPE
    assert payload["formal_closeout_task"] == AION200_TASK_ID
    assert set(SHADOW_RUNTIME_REQUIRED_CONTRACTS).issubset(payload["required_contracts"])
    assert set(SHADOW_RUNTIME_REQUIRED_SERVICES).issubset(payload["required_services"])
    assert set(SHADOW_RUNTIME_AUTHORIZED_CAPABILITIES).issubset(
        payload["authorized_capabilities"]
    )
    assert tuple(payload["required_cycle"]) == SHADOW_RUNTIME_REQUIRED_CYCLE
    assert set(SHADOW_RUNTIME_PROHIBITED_BEHAVIORS).issubset(
        payload["prohibited_behaviors"]
    )

    boundary = payload["runtime_boundary"]
    assert boundary["operator_invoked"] is True
    assert boundary["local_offline"] is True
    for key in (
        "production_runtime_enabled",
        "network_access",
        "connector_access",
        "provider_access",
        "api_route_added",
        "kernel_registration_added",
        "startup_registration",
        "background_loop_added",
        "cli_installation",
        "consequential_action_execution",
    ):
        assert boundary[key] is False


def test_aion_198_ledgers_create_single_active_authorization() -> None:
    validate_shadow_runtime_authorization(ROOT)
    validate_shadow_runtime_authorization_no_go(ROOT)

    program = _json("docs/cognitive-architecture/program-ledger.json")
    authorization = _json("docs/cognitive-architecture/authorization-ledger.json")
    aion199_implemented = any(
        record.get("implementation_task") == AION199_TASK_ID
        for record in program["records"]
    )
    expected_program_state = (
        AION199_PROGRAM_STATE if aion199_implemented else AION198_PROGRAM_STATE
    )

    assert program["program_state"] == expected_program_state
    assert program["active_cognitive_implementation_authorization"] == AION198_AUTHORIZATION_ID
    assert (
        authorization["active_cognitive_implementation_authorization"]
        == AION198_AUTHORIZATION_ID
    )
    assert program["active_cognitive_implementation_authorization_count"] == 1
    assert authorization["active_cognitive_implementation_authorization_count"] == 1

    aion198 = next(
        record
        for record in authorization["records"]
        if record["authorization_id"] == AION198_AUTHORIZATION_ID
    )
    assert aion198["record_kind"] == "implementation_authorization"
    assert aion198["authorization_active"] is True
    assert aion198["authorization_consumed"] is False
    assert aion198["authorization_expired"] is False
    assert aion198["authorization_reusable"] is False
    assert aion198["implementation_task"] == AION199_TASK_ID
    assert aion198["implementation_state"] == (
        "implemented_pending_aion_200_evaluation"
        if aion199_implemented
        else "authorized_pending_implementation"
    )
    assert aion198["scope"] == AION199_SCOPE
    assert aion198["formal_closeout_task"] == AION200_TASK_ID
    assert aion198["resource_limits"]["network_calls"] == 0
    assert aion198["resource_limits"]["connector_calls"] == 0
    assert aion198["resource_limits"]["model_provider_calls"] == 0
    assert aion198["resource_limits"]["source_rewrite_operations"] == 0
    assert aion198["resource_limits"]["git_operations"] == 0
    assert aion198["resource_limits"]["pull_request_creation"] == 0
    assert aion198["resource_limits"]["approval_creation"] == 0
    assert aion198["resource_limits"]["merge_operations"] == 0
    assert aion198["resource_limits"]["deployment_operations"] == 0
    assert aion198["resource_limits"]["model_weight_training"] == 0


def test_aion_198_does_not_implement_shadow_runtime_surface() -> None:
    program = _json("docs/cognitive-architecture/program-ledger.json")
    aion199_implemented = any(
        record.get("implementation_task") == AION199_TASK_ID
        for record in program["records"]
    )
    assert not (ROOT / "services/brain-api/src/aion_brain/api/cognitive_runtime.py").exists()
    if aion199_implemented:
        assert (ROOT / "services/brain-api/src/aion_brain/cognitive_runtime").is_dir()
    else:
        assert not (ROOT / "services/brain-api/src/aion_brain/cognitive_runtime").exists()
    for relative in (
        "services/brain-api/src/aion_brain/kernel/container.py",
        "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    ):
        text = (ROOT / relative).read_text()
        assert "ControlledCognitiveShadowRuntime" not in text
        assert "aion_brain.cognitive_runtime" not in text


def test_aion_198_scripts_are_executable_and_pass() -> None:
    env = {
        **os.environ,
        "PYTEST_CURRENT_TEST": "AION-198 focused script test",
    }
    scripts = (
        "scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh",
        "scripts/cognitive-shadow-runtime-authorization-check.sh",
    )
    for script in scripts:
        path = ROOT / script
        assert path.is_file()
        assert os.access(path, os.X_OK)
        subprocess.run([str(path)], cwd=ROOT, env=env, check=True)
