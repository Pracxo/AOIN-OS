"""AION-107 operator action write-path architecture regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/operator-actions/write-path-architecture.md",
    "docs/operator-actions/approval-boundary-design.md",
    "docs/operator-actions/execution-boundary-design.md",
    "docs/operator-actions/action-intent-lifecycle.md",
    "docs/operator-actions/controlled-execution-prerequisites.md",
    "docs/operator-actions/rollback-and-undo-model.md",
    "docs/operator-actions/separation-of-duties.md",
    "docs/operator-actions/write-path-threat-model.md",
    "docs/operator-actions/write-path-release-gates.md",
    "docs/operator-actions/write-path-no-go-regression-pack.md",
    "docs/adr/0098-operator-action-write-path-architecture.md",
]

EXAMPLES = [
    "examples/operator-actions/write-path-architecture.json",
    "examples/operator-actions/action-intent-lifecycle.json",
    "examples/operator-actions/write-path-release-gates.json",
    "examples/operator-actions/write-path-no-go-regression-result.json",
]

FALSE_KEYS = {
    "execution_enabled",
    "external_calls_enabled",
    "activation_enabled",
    "write_execution_enabled",
    "tool_execution_enabled",
    "model_generated_execution_enabled",
    "controlled_handoff_execution_enabled",
    "connector_runtime_enabled",
    "production_auth_enabled",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "approval_bypass_enabled",
    "hard_delete_enabled",
    "contains_secrets",
    "contains_credentials",
    "contains_tokens",
    "contains_external_endpoints",
    "contains_unredacted_prompts",
    "contains_private_reasoning",
}


def test_operator_action_write_path_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0098-operator-action-write-path-architecture.md" in adr_index

    design = _text("docs/operator-actions/write-path-architecture.md")
    for heading in [
        "## Purpose",
        "## Current dry-run state",
        "## Why write execution is not implemented",
        "## Future write-path components",
        "## Action intent lifecycle",
        "## Approval boundary",
        "## Execution boundary",
        "## Policy boundary",
        "## Connector boundary",
        "## Audit/provenance boundary",
        "## Rollback/undo model",
        "## Operator review model",
        "## No-go conditions",
    ]:
        assert heading in design

    combined = "\n".join(_text(relative).lower() for relative in DOCS)
    for marker in [
        "no write execution",
        "execution is future-only",
        "approval does not execute",
        "approval cannot bypass policy",
        "no direct tool execution",
        "no model-generated execution",
        "current lifecycle stops at previewed/reviewed/blocked",
        "future_execution_ready and future_executed are not reachable today",
    ]:
        assert marker in combined


def test_operator_action_write_path_lifecycle_and_threat_model() -> None:
    lifecycle = _text("docs/operator-actions/action-intent-lifecycle.md")
    for state in [
        "drafted",
        "requested",
        "dry_run_authorized",
        "previewed",
        "reviewed",
        "approval_required",
        "approved_for_future_execution",
        "blocked",
        "expired",
        "cancelled",
        "future_execution_ready",
        "future_executed",
        "rollback_requested",
        "rollback_completed",
        "archived",
    ]:
        assert state in lifecycle

    threat_model = _text("docs/operator-actions/write-path-threat-model.md").lower()
    for threat in [
        "approval bypass",
        "policy bypass",
        "model-generated tool execution",
        "confused deputy",
        "replayed approval",
        "stale preview",
        "target drift",
        "irreversible action",
        "rollback failure",
        "audit tampering",
        "privilege escalation",
        "connector boundary bypass",
        "external call leakage",
    ]:
        assert threat in threat_model


def test_operator_action_write_path_examples_are_valid_synthetic_and_disabled() -> None:
    payloads = []
    for relative in EXAMPLES:
        payload = json.loads(_text(relative))
        assert payload["status"] == "passed"
        _assert_false_keys(payload)
        payloads.append(payload)

    serialized = json.dumps(payloads, sort_keys=True).lower()
    for marker in [
        "sk-",
        "ghp_",
        "xoxb-",
        "-----begin private key-----",
        "bearer ",
        "basic ",
        "api_key",
        "private_key",
        "access_token",
        "refresh_token",
        "id_token",
        "client_secret",
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
        "http://",
        "https://",
    ]:
        assert marker not in serialized


def test_operator_action_write_path_release_gates_and_scripts() -> None:
    release = json.loads(_text("examples/operator-actions/write-path-release-gates.json"))
    expected_gates = {
        "write-path ADR approved",
        "threat model approved",
        "production auth ready",
        "connector boundary ready",
        "approval workflow tested",
        "rollback tested",
        "policy enforcement tested",
        "audit/provenance tested",
        "dry-run parity tested",
        "release/freeze gate green",
    }
    assert expected_gates <= {row["gate"] for row in release["gates"]}
    assert all(row["release_blocker"] is True for row in release["gates"])

    for relative in [
        "scripts/operator-action-write-path-design-check.sh",
        "scripts/operator-action-write-path-no-go-regression.sh",
    ]:
        path = ROOT / relative
        assert path.exists(), relative
        assert os.access(path, os.X_OK), relative


def _assert_false_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FALSE_KEYS:
                assert item is False, key
            _assert_false_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_false_keys(item)


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
