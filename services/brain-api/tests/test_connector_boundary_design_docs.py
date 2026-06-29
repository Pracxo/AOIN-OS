"""AION-106 external connector boundary design regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/connectors/external-connector-boundary-design.md",
    "docs/connectors/connector-trust-model.md",
    "docs/connectors/connector-credential-boundary.md",
    "docs/connectors/connector-egress-guard.md",
    "docs/connectors/connector-ingress-guard.md",
    "docs/connectors/connector-capability-declaration.md",
    "docs/connectors/connector-threat-model.md",
    "docs/connectors/connector-release-gates.md",
    "docs/connectors/connector-no-go-regression-pack.md",
    "docs/connectors/future-connector-implementation-prerequisites.md",
    "docs/adr/0097-external-connector-boundary-design.md",
]

EXAMPLES = [
    "examples/connectors/connector-boundary-design.json",
    "examples/connectors/connector-trust-model.json",
    "examples/connectors/connector-threat-model.json",
    "examples/connectors/connector-release-gates.json",
    "examples/connectors/connector-no-go-regression-result.json",
]

FALSE_KEYS = {
    "connector_runtime_enabled",
    "external_calls_enabled",
    "credentials_present",
    "token_storage_enabled",
    "dynamic_routes_enabled",
    "activation_enabled",
    "connector_sdk_dependency_present",
    "provider_sdk_dependency_present",
    "network_client_present",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "contains_real_endpoints",
    "contains_secrets",
}


def test_connector_boundary_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0097-external-connector-boundary-design.md" in adr_index

    design = _text("docs/connectors/external-connector-boundary-design.md")
    for heading in [
        "## Purpose",
        "## Current State",
        "## Why No Connector Runtime Exists Yet",
        "## Connector Lifecycle Proposal",
        "## Trust Boundary",
        "## Credential Boundary",
        "## Egress Boundary",
        "## Ingress Boundary",
        "## Policy Integration",
        "## Action Authorization Integration",
        "## Audit/Provenance Requirements",
        "## Operator Review Requirements",
        "## Future Implementation Phases",
        "## No-Go Conditions",
    ]:
        assert heading in design

    combined = "\n".join(_text(relative).lower() for relative in DOCS)
    assert "untrusted by default" in combined
    assert "no connector runtime" in combined
    assert "external calls remain disabled" in combined
    assert "credentials and tokens remain absent" in combined


def test_connector_examples_are_valid_synthetic_and_disabled() -> None:
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


def test_connector_threat_model_and_release_gates_cover_required_rows() -> None:
    threat_model = json.loads(_text("examples/connectors/connector-threat-model.json"))
    expected_threats = {
        "credential exfiltration",
        "prompt injection through connector response",
        "malicious connector metadata",
        "overbroad scopes",
        "SSRF-style egress abuse",
        "data exfiltration",
        "stale response trust",
        "rate limit exhaustion",
        "audit tampering",
        "policy bypass",
        "action authorization bypass",
        "hidden external calls",
        "provider impersonation",
        "dependency confusion",
    }
    assert expected_threats <= {row["threat"] for row in threat_model["threats"]}
    assert all(
        {"threat", "entry_point", "current_control", "future_required_control", "no_go_condition"}
        <= set(row)
        for row in threat_model["threats"]
    )

    release = json.loads(_text("examples/connectors/connector-release-gates.json"))
    expected_gates = {
        "threat model approved",
        "credential boundary approved",
        "egress guard approved",
        "ingress guard approved",
        "policy model approved",
        "action authorization integration tested",
        "audit provenance tested",
        "operator review tested",
        "sandbox requirements approved",
        "disabled-by-default prototype green",
        "release freeze gate green",
    }
    assert expected_gates <= {row["gate"] for row in release["gates"]}
    assert all(row["release_blocker"] is True for row in release["gates"])


def test_connector_scripts_are_executable_and_package_files_absent() -> None:
    for relative in [
        "scripts/connector-boundary-design-check.sh",
        "scripts/connector-no-go-regression.sh",
    ]:
        path = ROOT / relative
        assert path.exists(), relative
        assert os.access(path, os.X_OK), relative

    blocked_names = {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
    }
    assert not [
        path
        for path in ROOT.rglob("*")
        if ".git" not in path.parts and path.is_file() and path.name in blocked_names
    ]


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
