"""Compatibility helpers for historical branch-boundary tests during AION-243."""

from __future__ import annotations

import json
from pathlib import Path

AION243_ALLOWED_EXACT_PATHS: frozenset[str] = frozenset(
    {
        "docs/adr/0207-deterministic-local-v02-release-candidate-artifact-bundle-build-and-retention.md",
        "docs/adr/README.md",
        "docs/project-status.md",
        "docs/v02-release-qualification/aion-243-checklist.md",
        "docs/v02-release-qualification/authorization-ledger.json",
        "docs/v02-release-qualification/program-ledger.json",
        "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json",
        "examples/v02-release-qualification/v02-release-candidate-artifact-build-plan.json",
        "operator-console-static/demo-data/v02-release-candidate-artifact-build.json",
        "packages/aion-sdk-python/pyproject.toml",
        "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
        "scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh",
        "scripts/lib/v02-production-auth-scan-exclusions.sh",
        "scripts/lib/v02_staging_qualification_operator_evaluation.py",
        "scripts/model-gateway-operator-evaluation-no-go-regression.sh",
        "scripts/operator-console-static-check.sh",
        "scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh",
        "scripts/secure-runtime-integration-program-no-go-regression.sh",
        "scripts/self-improvement-governance-no-go-regression.sh",
        "scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh",
        "scripts/v02-production-auth-stabilization-authorization-check.sh",
        "services/brain-api/pyproject.toml",
        "services/brain-api/src/aion_brain/contracts/v02_release_candidate.py",
        "services/brain-api/tests/aion243_release_candidate_scope.py",
        "services/brain-api/tests/test_governed_learning_memory_no_runtime_source.py",
        "services/brain-api/tests/test_identity_assertion_no_runtime_integration.py",
        "services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py",
        "services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py",
        "services/brain-api/tests/test_knowledge_intelligence_program_repository_integrity.py",
        "services/brain-api/tests/test_knowledge_research_evaluation_repository_integrity.py",
        "services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py",
        "services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py",
        "services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py",
        "services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py",
        "services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py",
        "services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py",
        "services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py",
        "services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py",
        "services/brain-api/tests/test_v02_staging_qualification_operator_evaluation_aion242.py",
        "services/brain-api/tests/test_v02_release_candidate_artifact_build_aion243.py",
    }
)

AION243_ALLOWED_PREFIXES: tuple[str, ...] = (
    "docs/release/v02-release-candidate-",
    "docs/v02-release-qualification/release-candidate-",
    "scripts/v02-release-candidate-",
    "services/brain-api/src/aion_brain/v02_release_candidate/",
)

AION246_ALLOWED_EXACT_PATHS: frozenset[str] = frozenset(
    {
        "docs/adaptive-intelligence/aion-246-checklist.md",
        "docs/adaptive-intelligence/authorization-ledger.json",
        "docs/adaptive-intelligence/external-cognition-audit.md",
        "docs/adaptive-intelligence/external-cognition-budgets.md",
        "docs/adaptive-intelligence/external-cognition-circuit-breaker.md",
        "docs/adaptive-intelligence/external-cognition-component-lineage.md",
        "docs/adaptive-intelligence/external-cognition-contracts.md",
        "docs/adaptive-intelligence/external-cognition-fixture-pilot.md",
        "docs/adaptive-intelligence/external-cognition-foundation-implementation.md",
        "docs/adaptive-intelligence/external-cognition-observability.md",
        "docs/adaptive-intelligence/external-cognition-operator-runbook.md",
        "docs/adaptive-intelligence/external-cognition-redaction.md",
        "docs/adaptive-intelligence/external-cognition-replay.md",
        "docs/adaptive-intelligence/external-cognition-routing.md",
        "docs/adaptive-intelligence/external-cognition-security-review.md",
        "docs/adaptive-intelligence/external-cognition-trust.md",
        "docs/adaptive-intelligence/message-normalization.md",
        "docs/adaptive-intelligence/model-manifests.md",
        "docs/adaptive-intelligence/program-ledger.json",
        "docs/adaptive-intelligence/provider-manifests.md",
        "docs/adaptive-intelligence/request-response-envelopes.md",
        "docs/adaptive-intelligence/structured-output-validation.md",
        "docs/adr/0210-controlled-provider-neutral-external-cognition-gateway-foundation.md",
        "docs/release/v03-external-cognition-checklist.md",
        "docs/release/v03-external-cognition-fixture-pilot.md",
        "docs/release/v03-external-cognition-foundation.md",
        "docs/release/v03-external-cognition-runtime-hold.md",
        "docs/release/v03-external-cognition-security-evidence.md",
        "examples/adaptive-intelligence/external-cognition-contract-examples.json",
        "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json",
        "examples/adaptive-intelligence/external-cognition-foundation-authorization.json",
        "examples/adaptive-intelligence/external-cognition-runtime-hold.json",
        "examples/adaptive-intelligence/program-authorization.json",
        "examples/adaptive-intelligence/program-roadmap.json",
        "examples/adaptive-intelligence/runtime-hold.json",
        "operator-console-static/demo-data/adaptive-intelligence-program.json",
        "operator-console-static/demo-data/adaptive-intelligence-runtime-hold.json",
        "operator-console-static/demo-data/external-cognition-authorization.json",
        "operator-console-static/demo-data/external-cognition-foundation.json",
        "operator-console-static/demo-data/external-cognition-static-console-evidence.json",
        "scripts/adaptive-intelligence-program-authorization-check.sh",
        "scripts/adaptive-intelligence-program-authorization-no-go-regression.sh",
        "scripts/adaptive-intelligence-runtime-hold.sh",
        "scripts/external-cognition-fixture-local-run.py",
        "scripts/external-cognition-fixture-pilot-evidence-check.sh",
        "scripts/external-cognition-foundation-check.sh",
        "scripts/external-cognition-foundation-no-go-regression.sh",
        "scripts/external-cognition-runtime-hold.sh",
        "services/brain-api/src/aion_brain/contracts/external_cognition.py",
        "services/brain-api/tests/test_external_cognition_foundation_aion246.py",
    }
)

AION246_ALLOWED_PREFIXES: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/external_cognition/",
)


def is_aion243_allowed_path(path: str) -> bool:
    return (
        path in AION243_ALLOWED_EXACT_PATHS
        or path.startswith(AION243_ALLOWED_PREFIXES)
        or is_aion246_allowed_path(path)
    )


def is_aion246_allowed_path(path: str) -> bool:
    return _aion246_state_active() and (
        path in AION246_ALLOWED_EXACT_PATHS or path.startswith(AION246_ALLOWED_PREFIXES)
    )


def without_aion243_allowed_paths(paths: set[str]) -> set[str]:
    return {
        path
        for path in paths
        if not is_aion243_allowed_path(path) and not is_aion246_allowed_path(path)
    }


def _aion246_state_active() -> bool:
    ledger = Path(__file__).resolve().parents[3] / "docs/adaptive-intelligence/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    return (
        payload.get("program_state")
        in {
            "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout",
            "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented",
        }
        and payload.get("external_cognition_gateway_implemented") is True
        and payload.get("external_cognition_gateway_state")
        in {
            "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout",
            "implemented_disabled_deterministic_fixture_only_operator_evaluated_live_provider_pilot_authorized_not_implemented",
        }
    )
