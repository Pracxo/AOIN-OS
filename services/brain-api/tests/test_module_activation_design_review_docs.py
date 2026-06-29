"""AION-105 module activation design review gate regression tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/modules/module-activation-design-review.md",
    "docs/modules/plugin-boundary-evidence-pack.md",
    "docs/modules/module-activation-pre-gate.md",
    "docs/modules/code-loading-disabled-proof.md",
    "docs/modules/runtime-registration-disabled-proof.md",
    "docs/modules/capability-activation-disabled-proof.md",
    "docs/modules/module-lifecycle-traceability-matrix.md",
    "docs/modules/future-activation-implementation-prerequisites.md",
    "docs/modules/module-activation-no-go-regression-pack.md",
    "docs/adr/0096-module-activation-design-review-gate.md",
]

EXAMPLES = [
    "examples/modules/module-activation-design-review.json",
    "examples/modules/plugin-boundary-evidence-pack.json",
    "examples/modules/module-activation-pre-gate-result.json",
    "examples/modules/module-lifecycle-traceability-matrix.json",
    "examples/modules/module-activation-no-go-regression-result.json",
]

DANGEROUS_FALSE_KEYS = {
    "activation_enabled",
    "code_loading_enabled",
    "runtime_registration_enabled",
    "capability_activation_enabled",
    "controlled_execution_enabled",
    "package_installation_enabled",
    "external_calls_enabled",
    "external_dependency_download_enabled",
    "executable_payload_accepted",
    "policy_bypass_enabled",
    "audit_bypass_enabled",
    "module_writes_enabled",
    "activation_ready_default",
}


def test_module_activation_design_review_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0096-module-activation-design-review-gate.md" in adr_index

    design_review = _text("docs/modules/module-activation-design-review.md")
    for heading in [
        "## Purpose",
        "## Scope Reviewed",
        "## Existing Module Lifecycle Gates",
        "## Current Safe State",
        "## What Remains Disabled",
        "## What Remains Mock-Only",
        "## Known Gaps",
        "## Review Decision",
        "## Next Phase Recommendation",
    ]:
        assert heading in design_review


def test_module_activation_review_examples_are_valid_and_disabled() -> None:
    payloads = []
    for relative in EXAMPLES:
        payload = json.loads(_text(relative))
        assert payload["status"] == "passed"
        payloads.append(payload)
        _assert_dangerous_keys_false(payload)

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
        "raw_prompt",
        "hidden_reasoning",
        "chain_of_thought",
    ]:
        assert marker not in serialized


def test_plugin_boundary_evidence_and_traceability_cover_required_areas() -> None:
    plugin = json.loads(_text("examples/modules/plugin-boundary-evidence-pack.json"))
    assert plugin["payload_executable"] is False
    expected_areas = {
        "extension manifest validation",
        "extension intake",
        "module slot",
        "capability binding",
        "binding validation",
        "conformance",
        "readiness",
        "activation request",
        "activation gate",
        "runtime registration preview",
        "module mock runtime",
        "operator review",
        "release and freeze checks",
        "boundary checks",
    }
    assert expected_areas <= {row["area"] for row in plugin["evidence"]}
    assert all(row["expected_status"] == "passed" for row in plugin["evidence"])
    assert all(row["release_blocker"] is True for row in plugin["evidence"])

    trace = json.loads(_text("examples/modules/module-lifecycle-traceability-matrix.json"))
    expected_stages = {
        "manifest",
        "intake",
        "slot",
        "binding",
        "validation",
        "conformance",
        "readiness",
        "activation request",
        "activation gate",
        "blockers",
        "registration preview",
        "mock runtime",
        "operator review",
        "audit/provenance",
        "evidence script",
    }
    assert expected_stages <= {row["stage"] for row in trace["rows"]}
    assert all(row["activation_allowed"] is False for row in trace["rows"])


def test_module_activation_scripts_are_executable_and_no_package_files_exist() -> None:
    for relative in [
        "scripts/module-activation-design-review.sh",
        "scripts/module-activation-no-go-regression.sh",
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


def _assert_dangerous_keys_false(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in DANGEROUS_FALSE_KEYS:
                assert item is False, key
            _assert_dangerous_keys_false(item)
    elif isinstance(value, list):
        for item in value:
            _assert_dangerous_keys_false(item)


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
