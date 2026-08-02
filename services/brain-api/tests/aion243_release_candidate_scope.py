"""Compatibility helpers for historical branch-boundary tests during AION-243."""

from __future__ import annotations

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


def is_aion243_allowed_path(path: str) -> bool:
    return path in AION243_ALLOWED_EXACT_PATHS or path.startswith(AION243_ALLOWED_PREFIXES)


def without_aion243_allowed_paths(paths: set[str]) -> set[str]:
    return {path for path in paths if not is_aion243_allowed_path(path)}
