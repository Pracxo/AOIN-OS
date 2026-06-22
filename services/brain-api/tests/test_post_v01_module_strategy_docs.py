"""AION-082 post-v0.1 module ecosystem strategy docs tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/roadmap/module-ecosystem.md",
    "docs/architecture/module-activation-design.md",
    "docs/security/module-activation-threat-model.md",
    "docs/modules/first-module-selection.md",
    "docs/modules/generic-knowledge-intelligence-module.md",
    "docs/modules/module-intake-checklist.md",
    "docs/modules/module-activation-state-machine.md",
    "docs/modules/module-risk-classification.md",
    "docs/modules/module-branching-and-release-discipline.md",
    "docs/adr/0073-post-v0.1-module-ecosystem-strategy.md",
]

EXPECTED_CAPABILITIES = {
    "generic.knowledge.retrieve",
    "generic.knowledge.summarize",
    "generic.knowledge.ground",
    "generic.knowledge.explain",
    "generic.knowledge.answer",
}


def test_post_v01_module_strategy_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0073-post-v0.1-module-ecosystem-strategy.md" in adr_index


def test_generic_knowledge_manifest_is_metadata_only() -> None:
    manifest = _json("examples/modules/generic-knowledge-intelligence-manifest.json")

    assert manifest["extension_key"] == "generic.knowledge_intelligence"
    assert manifest["name"] == "Generic Knowledge Intelligence"
    assert manifest["package_type"] == "module"
    assert manifest["version"] == "0.1.0-preview"
    assert manifest["declared_dependencies"] == []
    assert manifest["declared_routes"] == []
    assert manifest["declared_resources"] == []
    assert manifest["metadata"]["metadata_only"] is True
    assert manifest["metadata"]["remote_sources_allowed"] is False
    assert manifest["metadata"]["code_loading_allowed"] is False
    assert manifest["metadata"]["activation_allowed"] is False
    assert manifest["metadata"]["route_registration_allowed"] is False
    assert manifest["metadata"]["full_autonomy"] is False
    assert manifest["metadata"]["payloads_included"] is False
    assert manifest["metadata"]["external_model_calls_allowed"] is False
    assert manifest["metadata"]["controlled_handoff_allowed"] is False

    capabilities = manifest["declared_capabilities"]
    assert {item["capability_key"] for item in capabilities} == EXPECTED_CAPABILITIES
    for capability in capabilities:
        assert capability["risk_level"] in {"low", "medium"}
        assert capability["dry_run_supported"] is True
        assert capability["controlled_supported"] is False
        assert capability["requires_policy"] is True
        assert capability["requires_approval"] is False
        assert capability["requires_sandbox"] is True

    serialized = json.dumps(manifest).lower()
    assert "http://" not in serialized
    assert "https://" not in serialized
    for forbidden_key in {
        "entrypoint",
        "binary",
        "package_bytes",
        "source_code",
        "source_url",
        "package_url",
        "install_command",
    }:
        assert forbidden_key not in _keys(manifest)


def test_docs_state_disabled_boundaries_and_brain_core_rule() -> None:
    combined = "\n".join(_text(relative) for relative in [*DOCS, "README.md", "AGENTS.md"])

    for statement in [
        "Activation remains disabled",
        "Code loading remains disabled",
        "Modules must not modify Brain core",
        "Brain core is frozen after v0.1",
        "Generic Knowledge Intelligence",
    ]:
        assert statement in combined

    readme = _text("README.md")
    for link in [
        "docs/roadmap/module-ecosystem.md",
        "docs/architecture/module-activation-design.md",
        "docs/security/module-activation-threat-model.md",
        "docs/modules/first-module-selection.md",
        "docs/modules/generic-knowledge-intelligence-module.md",
        "docs/modules/module-intake-checklist.md",
        "docs/modules/module-activation-state-machine.md",
        "docs/modules/module-risk-classification.md",
        "docs/modules/module-branching-and-release-discipline.md",
    ]:
        assert link in readme


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key).lower() for key in value}
        for nested in value.values():
            keys.update(_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_keys(item))
        return keys
    return set()
