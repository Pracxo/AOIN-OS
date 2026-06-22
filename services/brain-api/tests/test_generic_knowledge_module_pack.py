"""AION-084 Generic Knowledge Intelligence module pack tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from aion_brain.contracts.capability_bindings import (
    BindingValidationRequest,
    CapabilityBindingCreateRequest,
)
from aion_brain.contracts.conformance import (
    CapabilityTestVectorCreateRequest,
    ConformanceProfileCreateRequest,
    ConformanceRunRequest,
)
from aion_brain.contracts.extensions import ExtensionIntakeRequest, ExtensionManifest
from aion_brain.contracts.module_activation import (
    ActivationReviewRequest,
    ModuleActivationCreateRequest,
)
from aion_brain.contracts.module_slots import ModuleSlotCreateRequest
from aion_brain.contracts.readiness import ReadinessAssessmentRequest

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "examples/modules/generic-knowledge-intelligence"

EXPECTED_CAPABILITIES = {
    "generic.knowledge.retrieve",
    "generic.knowledge.summarize",
    "generic.knowledge.ground",
    "generic.knowledge.explain",
    "generic.knowledge.answer",
}


def test_generic_knowledge_manifest_is_valid_metadata_only_json() -> None:
    manifest = _json("manifest.json")
    ExtensionManifest.model_validate(manifest)

    assert manifest["extension_key"] == "generic.knowledge_intelligence"
    assert manifest["name"] == "Generic Knowledge Intelligence"
    assert manifest["package_type"] == "module"
    assert manifest["version"] == "0.1.0-preview"
    assert manifest["declared_routes"] == []
    assert manifest["declared_dependencies"] == []
    assert {item["capability_key"] for item in manifest["declared_capabilities"]} == (
        EXPECTED_CAPABILITIES
    )

    for capability in manifest["declared_capabilities"]:
        assert capability["capability_key"].startswith("generic.")
        assert capability["risk_level"] in {"low", "medium"}
        assert capability["dry_run_supported"] is True
        assert capability["controlled_supported"] is False
        assert capability["requires_policy"] is True
        assert capability["requires_approval"] is False
        assert capability["requires_sandbox"] is True

    manifest_keys = _keys(manifest)
    for forbidden in {
        "executable_payload",
        "code",
        "source_url",
        "external_source",
        "install",
        "pip",
        "npm",
        "full_autonomy",
        "route_registration_enabled",
        "raw_secret_access",
    }:
        assert forbidden not in manifest_keys


def test_generic_knowledge_request_fixtures_match_public_contracts() -> None:
    ExtensionIntakeRequest.model_validate(_json("intake-request.json"))
    ModuleSlotCreateRequest.model_validate(_json("module-slot-request.json"))
    BindingValidationRequest.model_validate(_json("binding-validation-request.json"))
    ConformanceProfileCreateRequest.model_validate(_json("conformance-profile.json"))
    ConformanceRunRequest.model_validate(_json("conformance-run-request.json"))
    ReadinessAssessmentRequest.model_validate(_json("readiness-assessment-request.json"))
    ModuleActivationCreateRequest.model_validate(_json("activation-request.json"))
    ActivationReviewRequest.model_validate(_json("operator-review-request.json"))

    for binding in _json_list("capability-bindings.json"):
        CapabilityBindingCreateRequest.model_validate(binding)

    for vector in _json_list("test-vectors.json"):
        CapabilityTestVectorCreateRequest.model_validate(vector)


def test_generic_knowledge_bindings_and_activation_expectations_are_blocked() -> None:
    bindings = _json_list("capability-bindings.json")
    assert len(bindings) == 5
    assert {item["capability_key"] for item in bindings} == EXPECTED_CAPABILITIES

    for binding in bindings:
        assert binding["target_runtime"] == "metadata_only"
        assert binding["controlled_supported"] is False
        assert binding["dry_run_supported"] is True
        assert binding["requires_sandbox"] is True

    activation = _json("activation-request.json")
    assert activation["requested_mode"] == "dry_run"
    assert activation["request_type"] == "future_activation"
    assert activation["activation_target"] == "module_slot"
    assert activation["metadata"]["expected_activation_allowed"] is False
    assert activation["metadata"]["expected_execution_allowed"] is False
    assert activation["metadata"]["expected_registration_allowed"] is False

    readiness = _json("readiness-assessment-request.json")
    assert readiness["require_approved_review"] is True
    assert readiness["require_passing_conformance"] is True
    assert readiness["metadata"]["expected_activation_ready"] is False

    gate = _json("activation-gate-request.json")
    assert gate["request"]["mode"] == "dry_run"
    assert gate["expect"]["activation_allowed"] is False
    assert "activation_disabled" in gate["expect"]["blockers"]
    assert "runtime_registration_disabled" in gate["expect"]["blockers"]
    assert "code_loading_disabled" in gate["expect"]["blockers"]


def test_generic_knowledge_test_vectors_are_synthetic_and_safe() -> None:
    vectors = _json_list("test-vectors.json")
    assert {item["vector_type"] for item in vectors} == {"schema_only", "mock_input"}

    serialized = json.dumps(vectors).lower()
    for forbidden in {
        "secret",
        "password",
        "token",
        "api_key",
        "raw prompt",
        "hidden reasoning",
        "chain-of-thought",
    }:
        assert forbidden not in serialized

    for vector in vectors:
        assert vector["metadata"]["synthetic"] is True
        assert vector["metadata"]["contains_user_data"] is False


def test_generic_knowledge_scripts_exist_and_pass_offline() -> None:
    for script in [
        ROOT / "scripts/module-pack-check.sh",
        ROOT / "scripts/generic-knowledge-demo.sh",
        PACK / "demo-sequence.sh",
    ]:
        assert script.exists()
        assert script.stat().st_mode & 0o111

    subprocess.run(
        ["./scripts/module-pack-check.sh"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["./scripts/generic-knowledge-demo.sh", "--offline-ok", "--skip-api"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_generic_knowledge_docs_are_linked_and_state_blocked_boundaries() -> None:
    expected_docs = [
        "docs/modules/generic-knowledge-intelligence-demo.md",
        "docs/modules/generic-knowledge-intelligence-readiness-trail.md",
        "docs/modules/generic-knowledge-intelligence-operator-review.md",
        "docs/modules/generic-knowledge-intelligence-no-go.md",
        "docs/modules/generic-knowledge-intelligence-mock-runtime.md",
        "docs/modules/module-mock-runtime.md",
        "docs/adr/0075-generic-knowledge-intelligence-module-pack.md",
        "docs/adr/0076-deterministic-module-mock-runtime.md",
    ]
    for relative in expected_docs:
        assert (ROOT / relative).exists(), relative

    combined = "\n".join(
        (ROOT / relative).read_text()
        for relative in [
            *expected_docs,
            "README.md",
            "AGENTS.md",
            "docs/architecture.md",
            "docs/modules/module-activation-state-machine.md",
            "docs/modules/module-mock-runtime.md",
            "docs/modules/generic-knowledge-intelligence-mock-runtime.md",
        ]
    )
    for phrase in [
        "activation blocked",
        "metadata-only",
        "does not activate",
        "registration_allowed=false",
        "synthetic",
        "no code loading",
        "Generic Knowledge Intelligence",
    ]:
        assert phrase in combined

    assert "0076-deterministic-module-mock-runtime.md" in (
        ROOT / "docs/adr/README.md"
    ).read_text()
    assert "0075-generic-knowledge-intelligence-module-pack.md" in (
        ROOT / "docs/adr/README.md"
    ).read_text()
    assert "docs/modules/generic-knowledge-intelligence-demo.md" in (
        ROOT / "README.md"
    ).read_text()


def test_generic_knowledge_pack_does_not_add_runtime_surfaces() -> None:
    assert not list((ROOT / "infra/postgres/migrations").glob("*0084*"))
    assert not list((ROOT / "infra/postgres/migrations").glob("*generic*knowledge*"))
    assert not list((ROOT / "services/brain-api/src/aion_brain/api").glob("*knowledge*"))
    assert not list((ROOT / "packages/aion-sdk-python/src/aion_sdk/resources").glob("*knowledge*"))
    assert not list(
        (ROOT / "packages/aion-sdk-python/src/aion_sdk/cli/commands").glob("*knowledge*")
    )


def _json(name: str) -> dict[str, Any]:
    return json.loads((PACK / name).read_text())


def _json_list(name: str) -> list[dict[str, Any]]:
    payload = json.loads((PACK / name).read_text())
    assert isinstance(payload, list)
    return payload


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {str(key).lower() for key in value}
        for nested in value.values():
            found.update(_keys(nested))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(_keys(item))
        return found
    return set()
