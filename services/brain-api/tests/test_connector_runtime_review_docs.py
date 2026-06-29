"""AION-109 connector runtime review gate regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/connectors/connector-runtime-review-gate.md",
    "docs/connectors/no-external-call-evidence-pack.md",
    "docs/connectors/connector-credential-token-absence-proof.md",
    "docs/connectors/connector-egress-ingress-traceability-matrix.md",
    "docs/connectors/connector-runtime-disabled-proof.md",
    "docs/connectors/connector-pre-implementation-gate.md",
    "docs/connectors/connector-runtime-review-no-go-pack.md",
    "docs/connectors/future-connector-runtime-implementation-plan.md",
    "docs/adr/0100-connector-runtime-review-gate.md",
]

EXAMPLES = [
    "examples/connectors/connector-runtime-review-gate.json",
    "examples/connectors/no-external-call-evidence-pack.json",
    "examples/connectors/connector-credential-token-absence-proof.json",
    "examples/connectors/connector-egress-ingress-traceability-matrix.json",
    "examples/connectors/connector-runtime-review-no-go-result.json",
]

AION110_ALLOWED_CHANGED_FILES = {
    ".env.example",
    "services/brain-api/src/aion_brain/api/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/client.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/main.py",
    "packages/aion-sdk-python/src/aion_sdk/cli/commands/connector_simulator.py",
    "packages/aion-sdk-python/src/aion_sdk/resources/connector_simulator.py",
}


def test_connector_runtime_review_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    index = _text("docs/adr/README.md")
    assert "0100-connector-runtime-review-gate.md" in index

    review_gate = _text("docs/connectors/connector-runtime-review-gate.md")
    for heading in [
        "## Purpose",
        "## Scope Reviewed",
        "## AION-106 And AION-108 Summary",
        "## Current Safe State",
        "## What Remains Disabled",
        "## What Remains Preview-Only",
        "## Known Gaps",
        "## Review Decision",
        "## Next Phase Recommendation",
    ]:
        assert heading in review_gate

    combined = "\n".join(_text(relative).lower() for relative in DOCS)
    for required in [
        "connector runtime remains disabled",
        "external calls",
        "credential",
        "token",
        "route registration",
        "connector activation",
        "no network calls",
        "no sdk dependencies",
    ]:
        assert required in combined


def test_connector_runtime_review_examples_are_valid_and_safe() -> None:
    payloads = [_json(relative) for relative in EXAMPLES]
    for payload in payloads:
        assert payload["synthetic"] is True
        assert payload["status"] == "passed"
        _assert_false_keys(payload)

    evidence = _json("examples/connectors/no-external-call-evidence-pack.json")
    expected_areas = {
        "connector boundary design",
        "connector trust model",
        "credential boundary",
        "egress guard",
        "ingress guard",
        "disabled connector runtime gate",
        "mock manifest validation",
        "egress preview",
        "ingress preview",
        "connector runtime audit",
        "static console connector panel",
        "policy checks",
        "boundary checks",
    }
    assert expected_areas <= {item["area"] for item in evidence["evidence"]}
    assert all(item["expected_status"] == "passed" for item in evidence["evidence"])
    assert all(item["release_blocker"] is True for item in evidence["evidence"])

    trace = _json("examples/connectors/connector-egress-ingress-traceability-matrix.json")
    assert trace["no_external_call"] is True
    assert {"manifest", "egress preview", "ingress preview", "audit", "review gate"} <= {
        item["stage"] for item in trace["lifecycle_stages"]
    }

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


def test_connector_runtime_review_scripts_exist_and_pass() -> None:
    for relative, expected in [
        (
            "scripts/connector-runtime-no-external-call-regression.sh",
            "Connector runtime no-external-call regression PASS",
        ),
        ("scripts/connector-runtime-review.sh", "Connector runtime review PASS"),
    ]:
        script = ROOT / relative
        assert script.exists(), relative
        assert os.access(script, os.X_OK)
        assert script.stat().st_mode & stat.S_IXUSR
        result = subprocess.run(
            [str(script)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in result.stdout


def test_connector_runtime_review_keeps_blocked_files_absent() -> None:
    changed = _changed_files() - AION110_ALLOWED_CHANGED_FILES
    blocked_names = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
    }
    assert not any(Path(name).name in blocked_names for name in changed)
    assert not any("migrations" in Path(name).parts for name in changed)
    assert not any(name.startswith("services/brain-api/src/aion_brain/api/") for name in changed)
    assert not any(name.startswith("packages/aion-sdk-python/src/aion_sdk/") for name in changed)
    assert not any(name == ".env.example" for name in changed)


def _assert_false_keys(value: object) -> None:
    false_keys = {
        "connector_runtime_enabled",
        "external_calls_enabled",
        "credentials_enabled",
        "token_storage_enabled",
        "activation_enabled",
        "route_registration_enabled",
        "network_clients_present",
        "connector_sdk_dependency_present",
        "provider_sdk_dependency_present",
        "api_router_added",
        "migration_added",
        "package_files_present",
        "external_calls_found",
        "external_destination_present",
        "credentials_present",
        "token_storage_present",
        "provider_sdk_present",
        "secret_examples_present",
        "static_console_secret_input_present",
        "secret_storage_present",
        "migration_present",
        "external_identity_runtime_present",
        "connector_credentials_enabled",
        "connector_token_storage_enabled",
        "external_call",
        "present",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in false_keys:
                assert nested is False, key
            _assert_false_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _assert_false_keys(item)


def _changed_files() -> set[str]:
    files: set[str] = set()
    for command in [
        ("diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"),
        ("diff", "--cached", "--name-only", "--diff-filter=ACMRT", "--"),
        ("ls-files", "--others", "--exclude-standard"),
    ]:
        result = subprocess.run(
            ["git", *command],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        files.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return files


def _json(relative: str) -> dict[str, Any]:
    return json.loads(_text(relative))


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
