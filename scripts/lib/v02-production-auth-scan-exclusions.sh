#!/usr/bin/env bash

aion221_is_scoped_governed_learning_memory_path() {
  # Exact AION-221 charter, evidence, and validation paths. This program
  # creates a separate GLM authorization and no production-auth runtime source.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-*|\
    docs/adr/0185-governed-learning-and-memory-integration-program-charter.md|\
    docs/adr/README.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/governed-learning-memory-*.json|\
    scripts/governed-learning-memory-program-authorization-check.sh|\
    scripts/governed-learning-memory-program-no-go-regression.sh|\
    scripts/governed-learning-memory-runtime-hold.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
  esac
  return 1
}

aion224_is_scoped_governed_learning_memory_local_persistence_path() {
  # Exact AION-224 GLM local persistence implementation and validation paths.
  # This keeps production-auth no-go scans focused on auth runtime surfaces
  # while the AION-224 gates enforce local persistence no-go rules.
  case "$1" in
    docs/adr/0188-operator-approved-local-append-only-knowledge-and-memory-projection-persistence.md|\
    scripts/governed-learning-memory-local-persistence-check.sh|\
    scripts/governed-learning-memory-local-persistence-no-go-regression.sh|\
    scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh|\
    scripts/governed-learning-memory-local-persistence-run.py|\
    scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh|\
    scripts/lib/governed_learning_memory_local_persistence_authorization.py|\
    services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py)
      return 0
      ;;
  esac
  return 1
}

aion228_is_scoped_governed_learning_memory_continual_learning_path() {
  # Exact AION-228 GLM continual-learning pilot implementation, evidence, and
  # validation paths. AION-228 gates enforce the pilot no-go boundaries.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/governed-learning-memory/*|\
    docs/release/governed-learning-memory-continual-learning-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0192-controlled-operator-invoked-local-continual-learning-pilot-composition-and-execution.md|\
    docs/adr/README.md|\
    examples/governed-learning-memory/*|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/governed-learning-memory-continual-learning-*.json|\
    scripts/governed-learning-memory-controlled-local-continual-learning-run.py|\
    scripts/governed-learning-memory-continual-learning-*.sh|\
    scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py|\
    services/brain-api/src/aion_brain/contracts/governed_continual_learning.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/__init__.py|\
    services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_*.py|\
    services/brain-api/tests/test_governed_learning_memory_*.py)
      return 0
      ;;
  esac
  return 1
}

aion231_is_scoped_secure_runtime_foundation_path() {
  # Exact AION-231 secure runtime foundation implementation, evidence, and
  # validation paths. Production-auth no-go gates still block package files,
  # migrations, API routes, and production authentication runtime surfaces.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/secure-runtime-foundation-*|\
    docs/release/secure-runtime-integration-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0195-controlled-authenticated-local-operator-runtime-foundation.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/index.html|\
    operator-console-static/demo-data/secure-runtime-integration-*.json|\
    scripts/auth-design-check.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/connector-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/post-v01-release-candidate-no-go-regression.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/secure-runtime-foundation-*.sh|\
    scripts/secure-runtime-local-operator-run.py|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/secure-runtime-integration-runtime-hold.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
    scripts/production-auth-offline-identity-assertion-check.sh|\
    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/secure_runtime.py|\
    services/brain-api/src/aion_brain/secure_runtime/*|\
    services/brain-api/tests/secure_runtime_test_support.py|\
    services/brain-api/tests/test_secure_runtime_*.py|\
    services/brain-api/tests/test_secure_runtime_integration_*.py)
      return 0
      ;;
  esac
  return 1
}

aion232_is_scoped_secure_runtime_foundation_evaluation_path() {
  # Exact AION-232 secure runtime foundation evaluation, model-gateway
  # authorization, static evidence, and validation paths. This does not exempt
  # runtime source, API routes, package files, migrations, or provider calls.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/model-gateway-authorization-*|\
    docs/release/secure-runtime-foundation-*|\
    docs/release/secure-runtime-integration-*|\
    docs/adr/0196-secure-runtime-foundation-evaluation-and-controlled-model-gateway-authorization.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/index.html|\
    operator-console-static/demo-data/model-gateway-*.json|\
    operator-console-static/demo-data/secure-runtime-foundation-operator-evaluation.json|\
    scripts/auth-design-check.sh|\
    scripts/model-gateway-authorization-check.sh|\
    scripts/model-gateway-authorization-no-go-regression.sh|\
    scripts/model-gateway-runtime-hold.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-check.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/lib/secure_runtime_foundation_operator_evaluation.py|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/tests/secure_runtime_aion232_test_helpers.py|\
    services/brain-api/tests/test_model_gateway_*.py|\
    services/brain-api/tests/test_secure_runtime_aion231_delivery_reconciliation.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion232.py|\
    services/brain-api/tests/test_secure_runtime_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_foundation_*.py|\
    services/brain-api/tests/test_secure_runtime_integration_*.py)
      return 0
      ;;
  esac
  return 1
}

aion233_is_scoped_controlled_model_gateway_path() {
  # Exact AION-233 controlled model-gateway implementation, evidence, and
  # validation paths. This only covers provider-neutral reference simulation
  # source and static evidence, never API routes, package files, migrations, or
  # live provider integrations.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/model-gateway-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0197-controlled-provider-neutral-model-gateway-and-deterministic-reference-provider.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/model-gateway-*.json|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
	    operator-console-static/index.html|\
	    operator-console-static/demo-data/model-gateway-*.json|\
	    scripts/auth-design-check.sh|\
	    scripts/connector-runtime-no-external-call-regression.sh|\
	    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
	    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
	    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
	    scripts/operator-action-write-path-no-go-regression.sh|\
	    scripts/operator-console-static-check.sh|\
	    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
	    scripts/production-auth-architecture-check.sh|\
	    scripts/production-auth-core-no-go-regression.sh|\
	    scripts/production-auth-core-stabilization-no-go-regression.sh|\
	    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
	    scripts/production-auth-offline-identity-assertion-check.sh|\
	    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
	    scripts/production-auth-request-identity-no-go-regression.sh|\
	    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
	    scripts/static-console-safety-check.sh|\
	    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
	    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
	    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
	    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
	    scripts/model-gateway-*.sh|\
	    scripts/model-gateway-local-simulation-run.py|\
	    scripts/lib/secure_runtime_foundation_operator_evaluation.py|\
	    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/model_gateway.py|\
    services/brain-api/src/aion_brain/model_gateway/*|\
    services/brain-api/tests/model_gateway_aion233_test_support.py|\
    services/brain-api/tests/test_model_gateway_*.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion232.py|\
    services/brain-api/tests/test_secure_runtime_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_integration_program_charter.py|\
    services/brain-api/tests/test_secure_runtime_integration_scope.py)
      return 0
      ;;
  esac
  return 1
}

aion151_is_scoped_authorization_path() {
  # Keep these as exact artifact paths. The no-go scanners must never exempt
  # broad directories such as scripts/ or services/brain-api/src/.
  case "$1" in
    docs/release/v02-production-auth-authorization-checklist.md|\
    docs/release/v02-production-auth-authorization-evidence-matrix.md|\
    docs/release/v02-production-auth-authorization-no-go.md|\
    docs/release/v02-production-auth-core-checklist.md|\
    docs/release/v02-production-auth-core-evidence-matrix.md|\
    docs/release/v02-production-auth-core-implementation-closeout.md|\
    docs/release/v02-production-auth-core-implementation.md|\
    docs/release/v02-production-auth-core-no-go.md|\
    docs/release/v02-production-auth-core-runtime-hold.md|\
    docs/release/v02-production-auth-explicit-approval-record.md|\
    docs/release/v02-production-auth-implementation-authorization-transaction.md|\
    docs/release/v02-production-auth-implementation-scope.md|\
    docs/release/v02-production-auth-runtime-guard-hold.md|\
    docs/release/v02-production-auth-stabilization-authorization-checklist.md|\
    docs/release/v02-production-auth-stabilization-authorization-evidence-matrix.md|\
    docs/release/v02-production-auth-stabilization-authorization-no-go.md|\
    docs/release/v02-production-auth-stabilization-authorization-transaction.md|\
    docs/release/v02-production-auth-stabilization-explicit-approval-record.md|\
    docs/release/v02-production-auth-stabilization-runtime-guard-renewal.md|\
    docs/release/v02-production-auth-stabilization-scope.md|\
    docs/project-status.md|\
    docs/release/v02-production-auth-core-stabilization-closeout.md|\
    docs/release/v02-production-auth-request-boundary-authorization-transaction.md|\
    docs/release/v02-production-auth-request-boundary-scope.md|\
    docs/release/v02-production-auth-request-boundary-runtime-hold.md|\
    docs/release/v02-production-auth-request-boundary-authorization-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0142-v02-production-auth-implementation-authorization.md|\
    docs/adr/0144-v02-production-auth-core-stabilization-authorization.md|\
    docs/adr/0146-v02-production-auth-request-boundary-authorization.md|\
    examples/release/v02-production-auth-authorization-evidence-matrix.json|\
    examples/release/v02-production-auth-core-implementation-closeout.json|\
    examples/release/v02-production-auth-core-stabilization-closeout.json|\
    examples/release/v02-production-auth-explicit-approval-record.json|\
    examples/release/v02-production-auth-implementation-authorization.json|\
    examples/release/v02-production-auth-runtime-guard-hold.json|\
    examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json|\
    examples/release/v02-production-auth-stabilization-authorization.json|\
    examples/release/v02-production-auth-stabilization-explicit-approval-record.json|\
    examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json|\
    examples/release/v02-production-auth-request-boundary-authorization.json|\
    examples/release/v02-production-auth-request-boundary-runtime-hold.json|\
    operator-console-static/demo-data/v02-production-auth-authorization.json|\
    operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json|\
    operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json|\
    operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json|\
    operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json|\
    services/brain-api/tests/test_v02_production_auth_authorization_docs.py|\
    scripts/v02-production-auth-authorization-check.sh|\
    scripts/v02-production-auth-runtime-guard-hold.sh|\
    scripts/v02-production-auth-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-stabilization-runtime-guard-hold.sh|\
    scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-check.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_boundary_authorization_docs.py|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh)
      return 0
      ;;
    *)
      if aion159_is_scoped_actor_context_trust_boundary_authorization_path "$1"; then
        return 0
      fi
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      if aion157_is_scoped_request_identity_stabilization_path "$1"; then
        return 0
      fi
      if aion164_is_scoped_identity_assertion_replay_protection_path "$1"; then
        return 0
      fi
      if aion180_is_scoped_self_improvement_shadow_activation_authorization_path "$1"; then
        return 0
      fi
      if aion182_is_scoped_self_improvement_shadow_activation_operator_evaluation_path "$1"; then
        return 0
      fi
      if aion183_is_scoped_cognitive_architecture_authorization_path "$1"; then
        return 0
      fi
      if aion204_is_scoped_knowledge_intelligence_authorization_path "$1"; then
        return 0
      fi
      if aion205_is_scoped_knowledge_intelligence_research_acquisition_path "$1"; then
        return 0
      fi
      if aion207_is_scoped_knowledge_intelligence_source_registry_path "$1"; then
        return 0
      fi
      if aion209_is_scoped_knowledge_intelligence_claim_graph_path "$1"; then
        return 0
      fi
      if aion211_is_scoped_knowledge_intelligence_epistemic_assessment_path "$1"; then
        return 0
      fi
      if aion212_is_scoped_knowledge_intelligence_epistemic_assessment_evaluation_path "$1"; then
        return 0
      fi
      if aion213_is_scoped_knowledge_intelligence_domain_expert_mesh_path "$1"; then
        return 0
      fi
      if aion215_is_scoped_knowledge_intelligence_tool_verification_path "$1"; then
        return 0
      fi
      if aion219_is_scoped_knowledge_intelligence_public_research_pilot_path "$1"; then
        return 0
      fi
      if aion228_is_scoped_governed_learning_memory_continual_learning_path "$1"; then
        return 0
      fi
      if aion237_is_scoped_operator_console_integrated_local_runtime_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion157_is_scoped_request_identity_stabilization_path() {
  # Exact AION-157 authorization, evidence, and validator paths. This task is
  # governance-only; no implementation source paths are exempted here.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-production-auth-request-boundary-authorization-transaction.md|\
    docs/release/v02-production-auth-request-boundary-authorization-checklist.md|\
    docs/release/v02-production-auth-request-identity-boundary-implementation.md|\
    docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md|\
    docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-boundary-checklist.md|\
    docs/release/v02-production-auth-request-identity-boundary-closeout.md|\
    docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md|\
    docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md|\
    docs/release/v02-production-auth-request-identity-stabilization-scope.md|\
    docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md|\
    docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-stabilization-no-go.md|\
    docs/release/v02-production-auth-request-identity-stabilization-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-explicit-approval-record-master-ledger.md|\
    docs/release/v02-implementation-authorization-final-status.md|\
    docs/adr/0148-v02-production-auth-request-identity-stabilization-authorization.md|\
    docs/adr/README.md|\
    examples/release/v02-production-auth-request-boundary-authorization.json|\
    examples/release/v02-production-auth-request-boundary-runtime-hold.json|\
    examples/release/v02-production-auth-request-identity-boundary-closeout.json|\
    examples/release/v02-production-auth-request-identity-stabilization-authorization.json|\
    examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json|\
    examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json|\
    examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/production-auth-request-identity-boundary.json|\
    operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json|\
    operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json|\
    operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-authorization-check.sh|\
    scripts/v02-production-auth-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-check.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/production-auth-request-identity-check.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    services/brain-api/tests/test_v02_production_auth_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_boundary_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py)
      return 0
      ;;
    *)
      if aion159_is_scoped_actor_context_trust_boundary_authorization_path "$1"; then
        return 0
      fi
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      if aion158_is_scoped_request_identity_stabilization_path "$1"; then
        return 0
      fi
      if aion164_is_scoped_identity_assertion_replay_protection_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion158_is_scoped_request_identity_stabilization_path() {
  # Exact AION-158 disabled request-identity stabilization paths. This permits
  # pure ASGI middleware hardening without exempting auth APIs, SDK runtime,
  # migrations, package files, provider code, or broad source directories.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/request-identity-stabilization.md|\
    docs/auth/request-identity-asgi-middleware.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-production-auth-request-identity-boundary-implementation.md|\
    docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md|\
    docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-boundary-checklist.md|\
    docs/release/v02-production-auth-request-identity-stabilization.md|\
    docs/release/v02-production-auth-request-identity-stabilization-runtime-hold.md|\
    docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-stabilization-no-go.md|\
    docs/release/v02-production-auth-request-identity-stabilization-checklist.md|\
    docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md|\
    docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md|\
    docs/release/v02-production-auth-request-identity-stabilization-scope.md|\
    docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0149-v02-production-auth-request-identity-stabilization.md|\
    docs/adr/README.md|\
    services/brain-api/src/aion_brain/contracts/request_identity.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/production_auth/verifier.py|\
    services/brain-api/src/aion_brain/production_auth/request_boundary.py|\
    services/brain-api/src/aion_brain/production_auth/request_middleware.py|\
    services/brain-api/src/aion_brain/production_auth/request_evidence.py|\
    services/brain-api/src/aion_brain/kernel/app_factory.py|\
    services/brain-api/src/aion_brain/kernel/diagnostics.py|\
    services/brain-api/tests/test_request_identity_contracts.py|\
    services/brain-api/tests/test_request_identity_verifiers.py|\
    services/brain-api/tests/test_request_identity_middleware.py|\
    services/brain-api/tests/test_request_identity_app_factory.py|\
    services/brain-api/tests/test_request_identity_config.py|\
    services/brain-api/tests/test_request_identity_pure_asgi_middleware.py|\
    services/brain-api/tests/test_request_identity_streaming_preservation.py|\
    services/brain-api/tests/test_request_identity_request_body_preservation.py|\
    services/brain-api/tests/test_request_identity_cancellation.py|\
    services/brain-api/tests/test_request_identity_client_disconnect.py|\
    services/brain-api/tests/test_request_identity_non_http_scopes.py|\
    services/brain-api/tests/test_request_identity_state_integrity.py|\
    services/brain-api/tests/test_request_identity_duplicate_registration.py|\
    services/brain-api/tests/test_request_identity_stabilization_concurrency.py|\
    services/brain-api/tests/test_request_identity_stabilization_idempotency.py|\
    services/brain-api/tests/test_request_identity_stabilization_diagnostics.py|\
    services/brain-api/tests/test_request_identity_stabilization_performance.py|\
    examples/auth/request-identity-boundary-status.json|\
    examples/auth/request-identity-disabled-context.json|\
    examples/auth/request-identity-verification-result.json|\
    examples/auth/request-identity-audit-event.json|\
    examples/auth/request-identity-provenance-record.json|\
    examples/auth/request-identity-stabilized-boundary-status.json|\
    examples/auth/request-identity-stabilized-disabled-context.json|\
    examples/auth/request-identity-stabilized-audit-event.json|\
    examples/auth/request-identity-stabilized-provenance-record.json|\
    examples/auth/request-identity-stabilized-diagnostics.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/production-auth-request-identity-stabilization.json|\
    operator-console-static/demo-data/production-auth-request-identity-stabilization-runtime-hold.json|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-check.sh|\
    scripts/production-auth-request-identity-stabilization-runtime-hold.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh)
      return 0
      ;;
    *)
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      if aion164_is_scoped_identity_assertion_replay_protection_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion163_is_scoped_identity_assertion_replay_protection_authorization_path() {
  # Exact AION-163 governance, evidence, validator, and static-console paths.
  # This authorization task creates no replay implementation source, schema,
  # dependency, API route, SDK/CLI runtime surface, migration, package, or lockfile.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/offline-identity-assertion-verification.md|\
    docs/auth/identity-assertion-public-key-registry.md|\
    docs/auth/identity-assertion-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-offline-identity-assertion-verification-closeout.md|\
    docs/release/v02-offline-identity-assertion-verification-implementation.md|\
    docs/release/v02-offline-identity-assertion-verification-security-evidence.md|\
    docs/release/v02-offline-identity-assertion-verification-runtime-hold.md|\
    docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md|\
    docs/release/v02-offline-identity-assertion-verification-checklist.md|\
    docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md|\
    docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md|\
    docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md|\
    docs/release/v02-identity-assertion-replay-protection-explicit-approval-record.md|\
    docs/release/v02-identity-assertion-replay-protection-scope.md|\
    docs/release/v02-identity-assertion-replay-protection-persistence-model.md|\
    docs/release/v02-identity-assertion-replay-protection-threat-model.md|\
    docs/release/v02-identity-assertion-replay-protection-runtime-hold.md|\
    docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md|\
    docs/release/v02-identity-assertion-replay-protection-no-go.md|\
    docs/release/v02-identity-assertion-replay-protection-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-explicit-approval-record-master-ledger.md|\
    docs/release/v02-implementation-authorization-final-status.md|\
    docs/adr/0154-v02-identity-assertion-replay-protection-authorization.md|\
    docs/adr/README.md|\
    examples/release/v02-offline-identity-assertion-verification-closeout.json|\
    examples/release/v02-offline-identity-assertion-verification-authorization.json|\
    examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json|\
    examples/release/v02-identity-assertion-replay-protection-authorization.json|\
    examples/release/v02-identity-assertion-replay-protection-explicit-approval-record.json|\
    examples/release/v02-identity-assertion-replay-protection-runtime-hold.json|\
    examples/release/v02-identity-assertion-replay-protection-evidence-matrix.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/offline-identity-assertion-verification.json|\
    operator-console-static/demo-data/offline-identity-assertion-runtime-hold.json|\
    operator-console-static/demo-data/v02-identity-assertion-replay-protection-authorization.json|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-check.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/production-auth-offline-identity-assertion-check.sh|\
    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-check.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py|\
    services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py)
      return 0
      ;;
    *)
      if aion164_is_scoped_identity_assertion_replay_protection_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion164_is_scoped_identity_assertion_replay_protection_path() {
  # Exact AION-164 implementation, evidence, validator, and static-console
  # paths. This permits only the authorized persistent replay-protection core
  # and keeps API routes, config, kernel wiring, SDK/CLI surfaces, package
  # files, lockfiles, migrations, tags, and releases outside the exemption.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/offline-identity-assertion-verification.md|\
    docs/auth/identity-assertion-public-key-registry.md|\
    docs/auth/identity-assertion-runtime-boundary.md|\
    docs/auth/identity-assertion-replay-protection.md|\
    docs/auth/identity-assertion-replay-ledger.md|\
    docs/auth/identity-assertion-replay-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md|\
    docs/release/v02-identity-assertion-replay-protection-explicit-approval-record.md|\
    docs/release/v02-identity-assertion-replay-protection-scope.md|\
    docs/release/v02-identity-assertion-replay-protection-persistence-model.md|\
    docs/release/v02-identity-assertion-replay-protection-threat-model.md|\
    docs/release/v02-identity-assertion-replay-protection-implementation.md|\
    docs/release/v02-identity-assertion-replay-protection-security-evidence.md|\
    docs/release/v02-identity-assertion-replay-protection-runtime-hold.md|\
    docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md|\
    docs/release/v02-identity-assertion-replay-protection-no-go.md|\
    docs/release/v02-identity-assertion-replay-protection-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0155-v02-persistent-identity-assertion-replay-protection.md|\
    docs/adr/README.md|\
    examples/auth/identity-assertion-replay-first-claim.json|\
    examples/auth/identity-assertion-replay-detected.json|\
    examples/auth/identity-assertion-identifier-collision.json|\
    examples/auth/identity-assertion-replay-repository-failure.json|\
    examples/auth/identity-assertion-replay-audit-event.json|\
    examples/auth/identity-assertion-replay-provenance-record.json|\
    examples/auth/identity-assertion-replay-diagnostics.json|\
    examples/auth/offline-identity-assertion-pipeline-result.json|\
    examples/operator-console/static-console-navigation-map.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/identity-assertion-replay-protection.json|\
    operator-console-static/demo-data/identity-assertion-replay-runtime-hold.json|\
    scripts/auth-design-check.sh|\
    scripts/connector-platform-checkpoint.sh|\
    scripts/connector-release-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/local-auth-check.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-core-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/production-auth-identity-assertion-replay-check.sh|\
    scripts/production-auth-identity-assertion-replay-runtime-hold.sh|\
    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/static-console-ux-check.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    services/brain-api/src/aion_brain/local_auth/audit.py|\
    services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py|\
    services/brain-api/tests/test_identity_assertion_replay_contracts.py|\
    services/brain-api/tests/test_identity_assertion_replay_key.py|\
    services/brain-api/tests/test_identity_assertion_replay_policy.py|\
    services/brain-api/tests/test_identity_assertion_replay_table_contract.py|\
    services/brain-api/tests/test_identity_assertion_replay_repository_schema.py|\
    services/brain-api/tests/test_identity_assertion_replay_repository_claim.py|\
    services/brain-api/tests/test_identity_assertion_replay_repository_concurrency.py|\
    services/brain-api/tests/test_identity_assertion_replay_multiple_engines.py|\
    services/brain-api/tests/test_identity_assertion_replay_service.py|\
    services/brain-api/tests/test_identity_assertion_replay_pipeline.py|\
    services/brain-api/tests/test_identity_assertion_replay_retention.py|\
    services/brain-api/tests/test_identity_assertion_replay_cleanup.py|\
    services/brain-api/tests/test_identity_assertion_replay_cleanup_race.py|\
    services/brain-api/tests/test_identity_assertion_replay_failure_safety.py|\
    services/brain-api/tests/test_identity_assertion_replay_evidence.py|\
    services/brain-api/tests/test_identity_assertion_replay_redaction.py|\
    services/brain-api/tests/test_identity_assertion_replay_concurrency.py|\
    services/brain-api/tests/test_identity_assertion_replay_no_runtime_integration.py|\
    services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py|\
    services/brain-api/tests/test_identity_assertion_replay_performance.py|\
    services/brain-api/tests/test_actor_context_diagnostics.py|\
    services/brain-api/tests/test_auth_design_docs.py|\
    services/brain-api/tests/test_static_console_ux_refinement.py|\
    services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py|\
    services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py|\
    services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_boundary_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion165_is_scoped_self_improvement_governance_authorization_path() {
  # Exact self-improvement authorization document and guard paths. These are
  # not production-auth runtime artifacts and must not suppress package,
  # migration, API, SDK/CLI, or production-auth source checks.
  case "$1" in
    docs/adr/0156-governed-self-improvement-control-plane.md|\
    docs/adr/0157-self-improvement-evaluation-authorization.md|\
    docs/adr/README.md|\
    docs/self-improvement/governance-charter.md|\
    docs/self-improvement/evaluation-authorization.md|\
    docs/self-improvement/protected-core-boundary.md|\
    docs/self-improvement/approval-model.md|\
    docs/self-improvement/change-budget-model.md|\
    docs/self-improvement/risk-model.md|\
    docs/self-improvement/aion-164-closeout-evidence.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-governance-authorization-check.sh|\
    scripts/self-improvement-governance-no-go-regression.sh|\
    scripts/self-improvement-evaluation-authorization-check.sh|\
    scripts/self-improvement-evaluation-no-go-regression.sh|\
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion168_is_scoped_self_improvement_evaluation_plane_path() {
  # Exact AION-168 self-improvement evaluation plane implementation paths. This
  # does not exempt production-auth source, auth APIs, SDK/CLI runtime surfaces,
  # package files, lockfiles, migrations, or broad source directories.
  case "$1" in
    services/brain-api/src/aion_brain/self_improvement/__init__.py|\
    services/brain-api/src/aion_brain/self_improvement/benchmark_contracts.py|\
    services/brain-api/src/aion_brain/self_improvement/benchmark_registry.py|\
    services/brain-api/src/aion_brain/self_improvement/benchmark_runner.py|\
    services/brain-api/src/aion_brain/self_improvement/comparison.py|\
    services/brain-api/src/aion_brain/self_improvement/evaluation_evidence.py|\
    services/brain-api/src/aion_brain/self_improvement/holdout.py|\
    services/brain-api/src/aion_brain/self_improvement/scoring.py|\
    services/brain-api/tests/test_self_improvement_evaluation_plane.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion169_is_scoped_self_improvement_experiment_authorization_path() {
  # Exact AION-169 self-improvement experiment authorization paths. This task
  # is governance-only and does not exempt runtime source, SDK/CLI surfaces,
  # package files, lockfiles, migrations, or API routes.
  case "$1" in
    docs/adr/0158-self-improvement-experiment-authorization.md|\
    docs/adr/README.md|\
    docs/self-improvement/experiment-authorization.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-governance-authorization-check.sh|\
    scripts/self-improvement-evaluation-authorization-check.sh|\
    scripts/self-improvement-experiment-no-go-regression.sh|\
    scripts/self-improvement-experiment-authorization-check.sh|\
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion171_is_scoped_self_improvement_rewrite_authorization_path() {
  # Exact AION-171 self-improvement rewrite authorization paths. This task is
  # governance-only and does not exempt runtime source, SDK/CLI surfaces,
  # package files, lockfiles, migrations, or API routes.
  case "$1" in
    docs/adr/0159-self-improvement-rewrite-authorization.md|\
    docs/adr/README.md|\
    docs/self-improvement/rewrite-authorization.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-governance-authorization-check.sh|\
    scripts/self-improvement-evaluation-authorization-check.sh|\
    scripts/self-improvement-experiment-no-go-regression.sh|\
    scripts/self-improvement-experiment-authorization-check.sh|\
    scripts/self-improvement-rewrite-no-go-regression.sh|\
    scripts/self-improvement-rewrite-authorization-check.sh|\
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion172_is_scoped_self_improvement_rewrite_controller_path() {
  # Exact AION-172 self-improvement rewrite-controller implementation paths.
  # These are disabled-by-default control-plane artifacts and do not exempt
  # production-auth source, auth APIs, SDK/CLI runtime surfaces, package files,
  # lockfiles, migrations, or broad source directories.
  case "$1" in
    docs/self-improvement/program-ledger.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-rewrite-controller-check.sh|\
    scripts/self-improvement-rewrite-controller-no-go-regression.sh|\
    services/brain-api/src/aion_brain/self_improvement/__init__.py|\
    services/brain-api/src/aion_brain/self_improvement/ci_monitor.py|\
    services/brain-api/src/aion_brain/self_improvement/diff_hash.py|\
    services/brain-api/src/aion_brain/self_improvement/git_controller.py|\
    services/brain-api/src/aion_brain/self_improvement/merge_controller.py|\
    services/brain-api/src/aion_brain/self_improvement/patch_generator.py|\
    services/brain-api/src/aion_brain/self_improvement/patch_validator.py|\
    services/brain-api/src/aion_brain/self_improvement/pr_controller.py|\
    services/brain-api/src/aion_brain/self_improvement/rollback.py|\
    services/brain-api/src/aion_brain/self_improvement/sandbox.py|\
    services/brain-api/src/aion_brain/self_improvement/test_first.py|\
    services/brain-api/src/aion_brain/self_improvement/worktree.py|\
    services/brain-api/tests/test_self_improvement_rewrite_controller.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion173_is_scoped_self_improvement_canary_authorization_path() {
  # Exact AION-173 self-improvement canary authorization paths. This task is
  # governance-only and does not exempt runtime source, SDK/CLI surfaces,
  # package files, lockfiles, migrations, or API routes.
  case "$1" in
    docs/adr/0160-self-improvement-canary-authorization.md|\
    docs/adr/README.md|\
    docs/self-improvement/canary-authorization.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    scripts/auth-design-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-canary-no-go-regression.sh|\
    scripts/self-improvement-canary-authorization-check.sh|\
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_evaluation_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_experiment_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_rewrite_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_canary_authorization_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion174_is_scoped_self_improvement_canary_adaptation_path() {
  # Exact AION-174 canary, rollback, and adaptive-learning implementation
  # paths. These are disabled-by-default/data-only self-improvement artifacts
  # and do not exempt production-auth source, auth APIs, SDK/CLI runtime
  # surfaces, package files, lockfiles, migrations, or broad source directories.
  case "$1" in
    docs/self-improvement/program-ledger.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/self-improvement-canary-adaptation-no-go-regression.sh|\
    scripts/self-improvement-canary-adaptation-check.sh|\
    services/brain-api/src/aion_brain/self_improvement/__init__.py|\
    services/brain-api/src/aion_brain/self_improvement/canary_contracts.py|\
    services/brain-api/src/aion_brain/self_improvement/canary.py|\
    services/brain-api/src/aion_brain/self_improvement/monitoring.py|\
    services/brain-api/src/aion_brain/self_improvement/rollback_controller.py|\
    services/brain-api/src/aion_brain/self_improvement/outcome_ledger.py|\
    services/brain-api/src/aion_brain/self_improvement/strategy_selector.py|\
    services/brain-api/src/aion_brain/self_improvement/retrieval_optimizer.py|\
    services/brain-api/src/aion_brain/self_improvement/case_based_planner.py|\
    services/brain-api/src/aion_brain/self_improvement/preference_learning.py|\
    services/brain-api/src/aion_brain/self_improvement/skill_evolution.py|\
    services/brain-api/src/aion_brain/self_improvement/integrated_pipeline.py|\
    services/brain-api/tests/test_self_improvement_canary_adaptation.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion175_is_scoped_self_improvement_final_closeout_path() {
  # Exact AION-175 final closeout, evidence, and guard paths. This task closes
  # the canary authorization and adds no production-auth source, auth APIs,
  # SDK/CLI runtime surfaces, package files, lockfiles, migrations, or broad
  # source-directory exemptions.
  case "$1" in
    docs/adr/0161-governed-self-improvement-platform-complete.md|\
    docs/adr/README.md|\
    docs/self-improvement/final-architecture.md|\
    docs/self-improvement/operator-evaluation-guide.md|\
    docs/self-improvement/security-review.md|\
    docs/self-improvement/benchmark-report.md|\
    docs/self-improvement/end-to-end-evidence.md|\
    docs/self-improvement/known-limitations.md|\
    docs/self-improvement/runtime-activation-checklist.md|\
    docs/self-improvement/future-model-training-boundary.md|\
    docs/self-improvement/canary-authorization.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    examples/self-improvement/final-readiness-report.json|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/self-improvement-governance-authorization-check.sh|\
    scripts/self-improvement-evaluation-authorization-check.sh|\
    scripts/self-improvement-experiment-authorization-check.sh|\
    scripts/self-improvement-rewrite-authorization-check.sh|\
    scripts/self-improvement-canary-authorization-check.sh|\
    scripts/self-improvement-runtime-hold.sh|\
    scripts/self-improvement-final-check.sh|\
    services/brain-api/tests/test_self_improvement_final_closeout_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion161_is_scoped_offline_identity_assertion_verification_authorization_path() {
  # Exact AION-161 governance, evidence, and validator paths. This task closes
  # AION-159 and creates an offline verification authorization only; it does
  # not exempt implementation source, dependency manifests, package files,
  # migrations, routes, SDK/CLI runtime surfaces, or lockfiles.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/actor-context-trust-boundary.md|\
    docs/auth/development-identity-simulation.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-actor-context-trust-boundary-remediation.md|\
    docs/release/v02-actor-context-trust-boundary-runtime-hold.md|\
    docs/release/v02-actor-context-trust-boundary-evidence-matrix.md|\
    docs/release/v02-actor-context-trust-boundary-checklist.md|\
    docs/release/v02-actor-context-trust-boundary-authorization-transaction.md|\
    docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md|\
    docs/release/v02-actor-context-trust-boundary-remediation-closeout.md|\
    docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md|\
    docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md|\
    docs/release/v02-offline-identity-assertion-verification-scope.md|\
    docs/release/v02-offline-identity-assertion-verification-threat-model.md|\
    docs/release/v02-offline-identity-assertion-verification-runtime-hold.md|\
    docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md|\
    docs/release/v02-offline-identity-assertion-verification-no-go.md|\
    docs/release/v02-offline-identity-assertion-verification-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-explicit-approval-record-master-ledger.md|\
    docs/release/v02-implementation-authorization-final-status.md|\
    docs/adr/0152-v02-offline-ed25519-identity-assertion-verification-authorization.md|\
    docs/adr/README.md|\
    examples/release/v02-actor-context-trust-boundary-authorization.json|\
    examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json|\
    examples/release/v02-actor-context-trust-boundary-runtime-hold.json|\
    examples/release/v02-actor-context-trust-boundary-evidence-matrix.json|\
    examples/release/v02-actor-context-trust-boundary-remediation-closeout.json|\
    examples/release/v02-offline-identity-assertion-verification-authorization.json|\
    examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json|\
    examples/release/v02-offline-identity-assertion-verification-runtime-hold.json|\
    examples/release/v02-offline-identity-assertion-verification-evidence-matrix.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json|\
    operator-console-static/demo-data/v02-offline-identity-assertion-verification-authorization.json|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-check.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/production-auth-actor-context-trust-boundary-check.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-boundary-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-check.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    services/brain-api/tests/test_actor_context_trust_boundary_docs.py|\
    services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py|\
    services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py)
      return 0
      ;;
    *)
      if aion163_is_scoped_identity_assertion_replay_protection_authorization_path "$1"; then
        return 0
      fi
      if aion162_is_scoped_offline_identity_assertion_verification_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion162_is_scoped_offline_identity_assertion_verification_path() {
  # Exact AION-162 implementation, evidence, tests, and validators. This keeps
  # the authorized offline verification implementation narrow and unintegrated.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/actor-context-trust-boundary.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/auth/offline-identity-assertion-verification.md|\
    docs/auth/identity-assertion-public-key-registry.md|\
    docs/auth/identity-assertion-runtime-boundary.md|\
    docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md|\
    docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md|\
    docs/release/v02-offline-identity-assertion-verification-scope.md|\
    docs/release/v02-offline-identity-assertion-verification-threat-model.md|\
    docs/release/v02-offline-identity-assertion-verification-runtime-hold.md|\
    docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md|\
    docs/release/v02-offline-identity-assertion-verification-no-go.md|\
    docs/release/v02-offline-identity-assertion-verification-checklist.md|\
    docs/release/v02-offline-identity-assertion-verification-implementation.md|\
    docs/release/v02-offline-identity-assertion-verification-security-evidence.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0153-v02-offline-ed25519-identity-assertion-verification.md|\
    docs/adr/README.md|\
    examples/auth/offline-identity-assertion-verification-result.json|\
    examples/auth/offline-identity-assertion-rejection-result.json|\
    examples/auth/offline-identity-assertion-audit-event.json|\
    examples/auth/offline-identity-assertion-provenance-record.json|\
    examples/auth/offline-identity-assertion-diagnostics.json|\
    examples/auth/offline-identity-public-key-registry-status.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/offline-identity-assertion-verification.json|\
    operator-console-static/demo-data/offline-identity-assertion-runtime-hold.json|\
    services/brain-api/pyproject.toml|\
    services/brain-api/src/aion_brain/contracts/identity_assertion.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py|\
    services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py|\
    services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py|\
    services/brain-api/src/aion_brain/explanations/redaction.py|\
    services/brain-api/src/aion_brain/grounding/redaction.py|\
    services/brain-api/src/aion_brain/model_outputs/redaction.py|\
    services/brain-api/src/aion_brain/prompts/redaction.py|\
    services/brain-api/tests/__init__.py|\
    services/brain-api/tests/test_identity_assertion_contracts.py|\
    services/brain-api/tests/test_identity_assertion_base64url.py|\
    services/brain-api/tests/test_identity_assertion_canonical_payload.py|\
    services/brain-api/tests/test_trusted_public_key_registry.py|\
    services/brain-api/tests/test_offline_identity_assertion_verifier.py|\
    services/brain-api/tests/test_identity_assertion_temporal_validation.py|\
    services/brain-api/tests/test_identity_assertion_claim_constraints.py|\
    services/brain-api/tests/test_identity_assertion_negative_crypto.py|\
    services/brain-api/tests/test_identity_assertion_key_rotation.py|\
    services/brain-api/tests/test_identity_assertion_evidence.py|\
    services/brain-api/tests/test_identity_assertion_replay_boundary.py|\
    services/brain-api/tests/test_identity_assertion_concurrency.py|\
    services/brain-api/tests/test_identity_assertion_dependency_boundary.py|\
    services/brain-api/tests/test_identity_assertion_no_runtime_integration.py|\
    services/brain-api/tests/test_identity_assertion_performance.py|\
    scripts/production-auth-offline-identity-assertion-check.sh|\
    scripts/production-auth-offline-identity-assertion-runtime-hold.sh|\
    scripts/production-auth-offline-identity-assertion-no-go-regression.sh|\
    scripts/connector-platform-checkpoint.sh|\
    scripts/connector-release-no-go-regression.sh|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/connector-no-go-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion159_is_scoped_actor_context_trust_boundary_authorization_path() {
  # Exact AION-159 governance, evidence, and validator paths. This task does
  # not exempt actor-context, production-auth, config, kernel, API, SDK, CLI,
  # migration, package, or lockfile implementation source.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-stabilization.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-request-identity-stabilization-closeout.md|\
    docs/release/v02-actor-context-trust-boundary-authorization-transaction.md|\
    docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md|\
    docs/release/v02-actor-context-trust-boundary-scope.md|\
    docs/release/v02-actor-context-trust-boundary-runtime-hold.md|\
    docs/release/v02-actor-context-trust-boundary-evidence-matrix.md|\
    docs/release/v02-actor-context-trust-boundary-no-go.md|\
    docs/release/v02-actor-context-trust-boundary-checklist.md|\
    docs/release/v02-production-auth-request-identity-stabilization.md|\
    docs/release/v02-production-auth-request-identity-stabilization-runtime-hold.md|\
    docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-stabilization-checklist.md|\
    docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md|\
    docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-explicit-approval-record-master-ledger.md|\
    docs/release/v02-implementation-authorization-final-status.md|\
    docs/adr/0150-v02-actor-context-trust-boundary-authorization.md|\
    docs/adr/README.md|\
    examples/release/v02-request-identity-stabilization-closeout.json|\
    examples/release/v02-actor-context-trust-boundary-authorization.json|\
    examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json|\
    examples/release/v02-actor-context-trust-boundary-runtime-hold.json|\
    examples/release/v02-actor-context-trust-boundary-evidence-matrix.json|\
    examples/release/v02-production-auth-request-identity-stabilization-authorization.json|\
    examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json|\
    examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json|\
    examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json|\
    examples/operator-console/static-console-navigation-map.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json|\
    operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-check.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-check.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/static-console-ux-check.sh|\
    services/brain-api/tests/test_static_console_ux_refinement.py|\
    services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py)
      return 0
      ;;
    *)
      if aion161_is_scoped_offline_identity_assertion_verification_authorization_path "$1"; then
        return 0
      fi
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      if aion164_is_scoped_identity_assertion_replay_protection_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion160_is_scoped_actor_context_trust_boundary_remediation_path() {
  # Exact AION-160 fail-closed actor-context remediation paths. This permits
  # the scoped source remediation and evidence without exempting auth routers,
  # SDK/CLI runtime surfaces, migrations, package files, providers, or broad
  # source directories.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/actor-context-trust-boundary.md|\
    docs/auth/development-identity-simulation.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-stabilization.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-actor-context-trust-boundary-authorization-transaction.md|\
    docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md|\
    docs/release/v02-actor-context-trust-boundary-scope.md|\
    docs/release/v02-actor-context-trust-boundary-remediation.md|\
    docs/release/v02-actor-context-trust-boundary-runtime-hold.md|\
    docs/release/v02-actor-context-trust-boundary-evidence-matrix.md|\
    docs/release/v02-actor-context-trust-boundary-no-go.md|\
    docs/release/v02-actor-context-trust-boundary-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0151-v02-actor-context-trust-boundary-remediation.md|\
    docs/adr/README.md|\
    examples/auth/actor-context-anonymous-resolution.json|\
    examples/auth/actor-context-request-identity-resolution.json|\
    examples/auth/actor-context-development-simulation.json|\
    examples/auth/actor-context-resolution-audit-event.json|\
    examples/auth/actor-context-resolution-provenance.json|\
    examples/auth/actor-context-resolution-diagnostics.json|\
    operator-console-static/demo-data/actor-context-trust-boundary.json|\
    operator-console-static/demo-data/actor-context-runtime-hold.json|\
    services/brain-api/src/aion_brain/contracts/actor_context_resolution.py|\
    services/brain-api/src/aion_brain/identity/dev_auth.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/production_auth/actor_context.py|\
    services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py|\
    services/brain-api/src/aion_brain/kernel/container.py|\
    services/brain-api/src/aion_brain/kernel/diagnostics.py|\
    services/brain-api/tests/test_dev_auth_context.py|\
    services/brain-api/tests/test_actor_context_resolution_contracts.py|\
    services/brain-api/tests/test_actor_context_fail_closed.py|\
    services/brain-api/tests/test_actor_context_development_simulation.py|\
    services/brain-api/tests/test_actor_context_request_identity_precedence.py|\
    services/brain-api/tests/test_actor_context_request_context_correlation.py|\
    services/brain-api/tests/test_actor_context_privilege_escalation.py|\
    services/brain-api/tests/test_actor_context_route_integration.py|\
    services/brain-api/tests/test_actor_context_payload_metadata.py|\
    services/brain-api/tests/test_actor_context_audit_provenance.py|\
    services/brain-api/tests/test_actor_context_concurrency.py|\
    services/brain-api/tests/test_actor_context_redaction.py|\
    services/brain-api/tests/test_actor_context_diagnostics.py|\
    services/brain-api/tests/test_actor_context_no_runtime_surface.py|\
    services/brain-api/tests/test_actor_context_trust_boundary_docs.py|\
    services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-actor-context-trust-boundary-check.sh|\
    scripts/production-auth-actor-context-trust-boundary-runtime-hold.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-check.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion154_is_scoped_stabilization_path() {
  # Exact AION-154 stabilization paths. Keep this list narrow so inherited
  # AION-151/AION-153 no-go gates can run on the stabilization branch without
  # exempting broad source or documentation directories.
  case "$1" in
    services/brain-api/src/aion_brain/contracts/production_auth.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/production_auth/audit.py|\
    services/brain-api/src/aion_brain/production_auth/canonical.py|\
    services/brain-api/src/aion_brain/production_auth/config.py|\
    services/brain-api/src/aion_brain/production_auth/core.py|\
    services/brain-api/src/aion_brain/production_auth/diagnostics.py|\
    services/brain-api/src/aion_brain/production_auth/policy.py|\
    services/brain-api/src/aion_brain/production_auth/provenance.py|\
    services/brain-api/src/aion_brain/production_auth/reason_codes.py|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/container.py|\
    services/brain-api/src/aion_brain/kernel/diagnostics.py|\
    services/brain-api/tests/test_production_auth_stabilization_contracts.py|\
    services/brain-api/tests/test_production_auth_canonicalization.py|\
    services/brain-api/tests/test_production_auth_fingerprints.py|\
    services/brain-api/tests/test_production_auth_reason_codes.py|\
    services/brain-api/tests/test_production_auth_idempotency.py|\
    services/brain-api/tests/test_production_auth_concurrency.py|\
    services/brain-api/tests/test_production_auth_stabilization_redaction.py|\
    services/brain-api/tests/test_production_auth_stabilization_config_matrix.py|\
    services/brain-api/tests/test_production_auth_stabilization_kernel.py|\
    services/brain-api/tests/test_production_auth_stabilization_routes.py|\
    services/brain-api/tests/test_production_auth_stabilization_performance.py|\
    services/brain-api/tests/test_production_auth_contracts.py|\
    services/brain-api/tests/test_production_auth_core.py|\
    services/brain-api/tests/test_production_auth_policy.py|\
    docs/auth/production-auth-core-stabilization.md|\
    docs/auth/production-auth-canonical-evidence.md|\
    docs/auth/production-auth-core.md|\
    docs/auth/production-auth-core-runtime-boundary.md|\
    docs/auth/production-auth-policy-audit.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-production-auth-core-stabilization.md|\
    docs/release/v02-production-auth-core-stabilization-evidence-matrix.md|\
    docs/release/v02-production-auth-core-stabilization-runtime-hold.md|\
    docs/release/v02-production-auth-core-stabilization-no-go.md|\
    docs/release/v02-production-auth-core-stabilization-checklist.md|\
    docs/adr/0145-v02-production-auth-core-stabilization.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    README.md|\
    AGENTS.md|\
    examples/auth/production-auth-stabilized-core-status.json|\
    examples/auth/production-auth-stabilized-policy-decision.json|\
    examples/auth/production-auth-stabilized-audit-event.json|\
    examples/auth/production-auth-stabilized-provenance-record.json|\
    examples/auth/production-auth-stabilized-diagnostics.json|\
    operator-console-static/README.md|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/production-auth-core-stabilization.json|\
    operator-console-static/demo-data/production-auth-core-stabilization-runtime-hold.json|\
    scripts/production-auth-core-stabilization-check.sh|\
    scripts/production-auth-core-stabilization-runtime-hold.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh)
      return 0
      ;;
    *)
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion156_is_scoped_request_identity_path() {
  # Exact AION-156 disabled request-identity implementation paths. Inherited
  # AION-152/AION-154/AION-155 no-go gates may allow only these paths.
  case "$1" in
    services/brain-api/src/aion_brain/contracts/request_identity.py|\
    services/brain-api/src/aion_brain/production_auth/verifier.py|\
    services/brain-api/src/aion_brain/production_auth/request_boundary.py|\
    services/brain-api/src/aion_brain/production_auth/request_middleware.py|\
    services/brain-api/src/aion_brain/production_auth/request_evidence.py|\
    services/brain-api/src/aion_brain/production_auth/__init__.py|\
    services/brain-api/src/aion_brain/config.py|\
    services/brain-api/src/aion_brain/kernel/app_factory.py|\
    services/brain-api/src/aion_brain/kernel/container.py|\
    services/brain-api/src/aion_brain/kernel/diagnostics.py|\
    services/brain-api/tests/test_request_identity_contracts.py|\
    services/brain-api/tests/test_request_identity_verifiers.py|\
    services/brain-api/tests/test_request_identity_boundary.py|\
    services/brain-api/tests/test_request_identity_middleware.py|\
    services/brain-api/tests/test_request_identity_app_factory.py|\
    services/brain-api/tests/test_request_identity_audit_provenance.py|\
    services/brain-api/tests/test_request_identity_concurrency.py|\
    services/brain-api/tests/test_request_identity_redaction.py|\
    services/brain-api/tests/test_request_identity_config.py|\
    services/brain-api/tests/test_request_identity_no_runtime_routes.py|\
    services/brain-api/tests/test_production_auth_config.py|\
    .env.example|\
    README.md|\
    AGENTS.md|\
    docs/project-status.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/visual-brain.md|\
    docs/auth/request-identity-boundary.md|\
    docs/auth/request-identity-runtime-boundary.md|\
    docs/auth/production-auth-core.md|\
    docs/auth/production-auth-core-runtime-boundary.md|\
    docs/auth/production-auth-core-stabilization.md|\
    docs/auth/future-auth-implementation-plan.md|\
    docs/auth/production-auth-release-gates.md|\
    docs/release/v02-production-auth-request-identity-boundary-implementation.md|\
    docs/release/v02-production-auth-request-identity-boundary-runtime-hold.md|\
    docs/release/v02-production-auth-request-identity-boundary-evidence-matrix.md|\
    docs/release/v02-production-auth-request-identity-boundary-no-go.md|\
    docs/release/v02-production-auth-request-identity-boundary-checklist.md|\
    docs/release/v02-production-auth-request-boundary-authorization-transaction.md|\
    docs/release/v02-production-auth-request-boundary-scope.md|\
    docs/release/v02-production-auth-request-boundary-runtime-hold.md|\
    docs/release/v02-production-auth-request-boundary-authorization-checklist.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0147-v02-disabled-production-auth-request-identity-boundary.md|\
    docs/adr/README.md|\
    examples/auth/request-identity-boundary-status.json|\
    examples/auth/request-identity-disabled-context.json|\
    examples/auth/request-identity-verification-result.json|\
    examples/auth/request-identity-audit-event.json|\
    examples/auth/request-identity-provenance-record.json|\
    operator-console-static/demo-data/production-auth-request-identity-boundary.json|\
    operator-console-static/demo-data/production-auth-request-identity-runtime-hold.json|\
    operator-console-static/index.html|\
    operator-console-static/app.js|\
    operator-console-static/README.md|\
    scripts/production-auth-request-identity-check.sh|\
    scripts/production-auth-request-identity-runtime-hold.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/auth-design-check.sh|\
    scripts/local-auth-check.sh|\
    scripts/production-auth-core-stabilization-check.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-request-boundary-authorization-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/production-auth-core-stabilization-no-go-regression.sh|\
    scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py)
      return 0
      ;;
    *)
      if aion160_is_scoped_actor_context_trust_boundary_remediation_path "$1"; then
        return 0
      fi
      return 1
      ;;
  esac
}

aion151_scan_files_excluding_scoped_authorization() {
  local path
  local file
  for path in "$@"; do
    if [[ -d "$path" ]]; then
      while IFS= read -r file; do
        file="${file#./}"
        if ! aion151_is_scoped_authorization_path "$file" \
          && ! aion221_is_scoped_governed_learning_memory_path "$file" \
          && ! aion228_is_scoped_governed_learning_memory_continual_learning_path "$file"; then
          printf '%s\n' "$file"
        fi
      done < <(find "$path" -type f -print)
    elif [[ -f "$path" ]]; then
      file="${path#./}"
      if ! aion151_is_scoped_authorization_path "$file" \
        && ! aion221_is_scoped_governed_learning_memory_path "$file" \
        && ! aion228_is_scoped_governed_learning_memory_continual_learning_path "$file"; then
        printf '%s\n' "$file"
      fi
    fi
  done
}

aion178_is_scoped_self_improvement_shadow_mode_path() {
  # Exact AION-178 disabled self-improvement shadow-mode implementation paths.
  # These paths are covered by the AION-178 shadow no-go gate; production-auth
  # scanners should not treat their redaction vocabulary as auth runtime scope.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0163-controlled-self-improvement-shadow-mode-plane.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/self-improvement-shadow-mode-authorization-transaction.md|\
    docs/release/self-improvement-shadow-mode-checklist.md|\
    docs/release/self-improvement-shadow-mode-implementation-checklist.md|\
    docs/release/self-improvement-shadow-mode-implementation-evidence-matrix.md|\
    docs/release/self-improvement-shadow-mode-implementation-no-go.md|\
    docs/release/self-improvement-shadow-mode-implementation-runtime-hold.md|\
    docs/release/self-improvement-shadow-mode-implementation.md|\
    docs/release/self-improvement-shadow-mode-runtime-hold.md|\
    docs/release/self-improvement-shadow-mode-scope.md|\
    docs/release/self-improvement-shadow-mode-security-evidence.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/self-improvement/aion-178-checklist.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/program-ledger.json|\
    docs/self-improvement/runtime-activation-checklist.md|\
    docs/self-improvement/shadow-mode-architecture.md|\
    docs/self-improvement/shadow-mode-boundary.md|\
    docs/self-improvement/shadow-mode-data-governance.md|\
    docs/self-improvement/shadow-mode-evidence.md|\
    docs/self-improvement/shadow-mode-implementation.md|\
    docs/self-improvement/shadow-mode-operator-runbook.md|\
    docs/self-improvement/shadow-mode-operator-workflow.md|\
    docs/self-improvement/shadow-mode-output-and-retention.md|\
    docs/self-improvement/shadow-mode-pipeline.md|\
    docs/self-improvement/shadow-mode-reference-adapters.md|\
    docs/self-improvement/shadow-mode-resource-budgets.md|\
    docs/self-improvement/shadow-mode-roadmap.md|\
    docs/self-improvement/shadow-mode-security-review.md|\
    docs/visual-brain.md|\
    examples/self-improvement/shadow-budget-failure.json|\
    examples/self-improvement/shadow-evaluation-summary.json|\
    examples/self-improvement/shadow-evidence-bundle.json|\
    examples/self-improvement/shadow-failure-pattern.json|\
    examples/self-improvement/shadow-hypothesis.json|\
    examples/self-improvement/shadow-improvement-proposal.json|\
    examples/self-improvement/shadow-mode-runtime-hold.json|\
    examples/self-improvement/shadow-observation-manifest.json|\
    examples/self-improvement/shadow-operator-review-item.json|\
    examples/self-improvement/shadow-reference-snapshot.json|\
    examples/self-improvement/shadow-regression-test-proposal.json|\
    examples/self-improvement/shadow-run-diagnostics.json|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/self-improvement-shadow-mode-plane.json|\
    operator-console-static/demo-data/self-improvement-shadow-mode-review-items.json|\
    operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json|\
    operator-console-static/index.html|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/operator-action-write-path-no-go-regression.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/self-improvement-runtime-hold.sh|\
    scripts/self-improvement-shadow-mode-authorization-check.sh|\
    scripts/self-improvement-shadow-mode-authorization-no-go-regression.sh|\
    scripts/self-improvement-shadow-mode-check.sh|\
    scripts/self-improvement-shadow-mode-no-go-regression.sh|\
    scripts/self-improvement-shadow-mode-runtime-hold.sh|\
    services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_budget.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_mode.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_observation.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py|\
    services/brain-api/src/aion_brain/self_improvement/shadow_runner.py|\
    services/brain-api/tests/conftest.py|\
    services/brain-api/tests/test_self_improvement_final_closeout_docs.py|\
    services/brain-api/tests/test_self_improvement_postmerge_evidence_reconciliation.py|\
    services/brain-api/tests/test_self_improvement_shadow_budget.py|\
    services/brain-api/tests/test_self_improvement_shadow_concurrency.py|\
    services/brain-api/tests/test_self_improvement_shadow_contracts.py|\
    services/brain-api/tests/test_self_improvement_shadow_deterministic_replay.py|\
    services/brain-api/tests/test_self_improvement_shadow_evaluation.py|\
    services/brain-api/tests/test_self_improvement_shadow_evidence.py|\
    services/brain-api/tests/test_self_improvement_shadow_hypotheses.py|\
    services/brain-api/tests/test_self_improvement_shadow_manifest.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_boundary_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_no_network_git_or_pr.py|\
    services/brain-api/tests/test_self_improvement_shadow_no_runtime_influence.py|\
    services/brain-api/tests/test_self_improvement_shadow_observation.py|\
    services/brain-api/tests/test_self_improvement_shadow_output_boundary.py|\
    services/brain-api/tests/test_self_improvement_shadow_pattern_mining.py|\
    services/brain-api/tests/test_self_improvement_shadow_performance.py|\
    services/brain-api/tests/test_self_improvement_shadow_pipeline.py|\
    services/brain-api/tests/test_self_improvement_shadow_proposals.py|\
    services/brain-api/tests/test_self_improvement_shadow_redaction.py|\
    services/brain-api/tests/test_self_improvement_shadow_reference_adapter.py|\
    services/brain-api/tests/test_self_improvement_shadow_regression_proposals.py|\
    services/brain-api/tests/test_self_improvement_shadow_retention.py|\
    services/brain-api/tests/test_self_improvement_shadow_review_items.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion180_is_scoped_self_improvement_shadow_activation_authorization_path() {
  # Exact AION-180 controlled shadow activation authorization paths.
  # This authorization-only task adds governance evidence, static read-only
  # console data, validation scripts, and tests. It does not exempt production
  # auth source, API routes, SDK/CLI runtime surfaces, package files,
  # lockfiles, migrations, or broad source directories.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0165-controlled-shadow-activation-control-plane-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/self-improvement-shadow-activation-authorization-transaction.md|\
    docs/release/self-improvement-shadow-activation-checklist.md|\
    docs/release/self-improvement-shadow-activation-evidence-matrix.md|\
    docs/release/self-improvement-shadow-activation-explicit-approval-record.md|\
    docs/release/self-improvement-shadow-activation-no-go.md|\
    docs/release/self-improvement-shadow-activation-runtime-hold.md|\
    docs/release/self-improvement-shadow-activation-scope.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/self-improvement/aion-179-delivery-verification.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/known-limitations.md|\
    docs/self-improvement/program-ledger.json|\
    docs/self-improvement/runtime-activation-checklist.md|\
    docs/self-improvement/shadow-activation-approval-binding.md|\
    docs/self-improvement/shadow-activation-authorization-boundary.md|\
    docs/self-improvement/shadow-activation-control-plane-architecture.md|\
    docs/self-improvement/shadow-activation-data-boundary.md|\
    docs/self-improvement/shadow-activation-deactivation.md|\
    docs/self-improvement/shadow-activation-monitoring.md|\
    docs/self-improvement/shadow-activation-resource-budgets.md|\
    docs/self-improvement/shadow-activation-roadmap.md|\
    docs/self-improvement/shadow-activation-threat-model.md|\
    docs/self-improvement/shadow-mode-activation-decision-boundary.md|\
    docs/self-improvement/shadow-mode-roadmap.md|\
    docs/visual-brain.md|\
    examples/self-improvement/shadow-activation-approval-binding.json|\
    examples/self-improvement/shadow-activation-authorization.json|\
    examples/self-improvement/shadow-activation-candidate.json|\
    examples/self-improvement/shadow-activation-deactivation-plan.json|\
    examples/self-improvement/shadow-activation-monitoring-plan.json|\
    examples/self-improvement/shadow-activation-request.json|\
    examples/self-improvement/shadow-activation-resource-budget.json|\
    examples/self-improvement/shadow-activation-runtime-hold.json|\
    examples/self-improvement/shadow-mode-operator-evaluation-report.json|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/self-improvement-shadow-activation-authorization.json|\
    operator-console-static/demo-data/self-improvement-shadow-activation-runtime-hold.json|\
    operator-console-static/index.html|\
    scripts/auth-design-check.sh|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    scripts/self-improvement-runtime-hold.sh|\
    scripts/self-improvement-shadow-activation-authorization-check.sh|\
    scripts/self-improvement-shadow-activation-authorization-no-go-regression.sh|\
    scripts/self-improvement-shadow-activation-runtime-hold.sh|\
    scripts/self-improvement-shadow-mode-runtime-hold.sh|\
    scripts/static-console-safety-check.sh|\
    services/brain-api/tests/test_self_improvement_final_closeout_docs.py|\
    services/brain-api/tests/test_self_improvement_governance_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_postmerge_evidence_reconciliation.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_approval_binding_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_authorization_validator.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_budget_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_monitoring_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_threat_model.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_authorization_closeout.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_authorization_validator.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_boundary_spec.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_budget_spec.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion182_is_scoped_self_improvement_shadow_activation_operator_evaluation_path() {
  # Exact AION-182 shadow activation control-plane evaluation closeout paths.
  # This closeout adds only governance evidence, validation scripts, static
  # read-only console evidence, and tests. It does not exempt production-auth
  # source, API routes, SDK runtime resources, packages, lockfiles, migrations,
  # or broad source directories.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0167-shadow-activation-control-plane-operator-evaluation.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/self-improvement-shadow-activation-control-plane-evaluation-checklist.md|\
    docs/release/self-improvement-shadow-activation-control-plane-evaluation-closeout.md|\
    docs/release/self-improvement-shadow-activation-control-plane-evaluation-evidence-matrix.md|\
    docs/release/self-improvement-shadow-activation-control-plane-evaluation-runtime-hold.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/self-improvement/actual-shadow-activation-decision-boundary.md|\
    docs/self-improvement/authorization-ledger.json|\
    docs/self-improvement/known-limitations.md|\
    docs/self-improvement/program-ledger.json|\
    docs/self-improvement/runtime-activation-checklist.md|\
    docs/self-improvement/shadow-activation-control-plane-architecture.md|\
    docs/self-improvement/shadow-activation-control-plane-evaluation-scenarios.md|\
    docs/self-improvement/shadow-activation-control-plane-implementation.md|\
    docs/self-improvement/shadow-activation-control-plane-operator-evaluation-closeout.md|\
    docs/self-improvement/shadow-activation-control-plane-operator-evaluation-report.md|\
    docs/self-improvement/shadow-activation-roadmap.md|\
    docs/self-improvement/shadow-activation-security-review.md|\
    docs/visual-brain.md|\
    examples/self-improvement/actual-shadow-activation-review-boundary.json|\
    examples/self-improvement/shadow-activation-control-plane-evaluation-scenario-summary.json|\
    examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/self-improvement-actual-shadow-activation-review-boundary.json|\
    operator-console-static/demo-data/self-improvement-shadow-activation-control-plane-evaluation.json|\
    operator-console-static/index.html|\
    scripts/lib/self_improvement_governance.py|\
    scripts/lib/self_improvement_shadow_activation_operator_evaluation.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/self-improvement-runtime-hold.sh|\
    scripts/self-improvement-shadow-activation-authorization-check.sh|\
    scripts/self-improvement-shadow-activation-authorization-no-go-regression.sh|\
    scripts/self-improvement-shadow-activation-control-plane-check.sh|\
    scripts/self-improvement-shadow-activation-operator-evaluation-check.sh|\
    scripts/self-improvement-shadow-activation-operator-evaluation-no-go-regression.sh|\
    scripts/self-improvement-shadow-activation-runtime-hold.sh|\
    scripts/self-improvement-shadow-mode-runtime-hold.sh|\
    services/brain-api/tests/test_self_improvement_shadow_activation_authorization_closeout.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_authorization_docs.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_authorization_validator.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_no_runtime_effect.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation_docs.py|\
    services/brain-api/tests/test_self_improvement_shadow_mode_authorization_closeout.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion183_is_scoped_cognitive_architecture_authorization_path() {
  # Exact cognitive architecture authorization and closeout paths. These
  # governance packages authorize bounded implementation tasks but do not
  # exempt production-auth source, API routes, package files, lockfiles,
  # migrations, external connectors, credentials, or runtime activation.
  case "$1" in
    docs/cognitive-architecture/tasks/AION-183.md|\
    docs/cognitive-architecture/tasks/AION-185.md|\
    docs/cognitive-architecture/tasks/AION-186.md|\
    docs/cognitive-architecture/tasks/AION-187.md|\
    docs/cognitive-architecture/tasks/AION-188.md|\
    docs/cognitive-architecture/tasks/AION-189.md|\
    docs/cognitive-architecture/tasks/AION-190.md|\
    docs/cognitive-architecture/tasks/AION-191.md|\
    docs/cognitive-architecture/tasks/AION-192.md|\
    docs/cognitive-architecture/tasks/AION-193.md|\
    docs/cognitive-architecture/tasks/AION-194.md|\
    docs/cognitive-architecture/tasks/AION-195.md|\
    docs/cognitive-architecture/tasks/AION-196.md|\
    docs/cognitive-architecture/tasks/AION-197.md|\
    docs/cognitive-architecture/tasks/AION-198.md|\
    docs/cognitive-architecture/program-ledger.json|\
    docs/cognitive-architecture/authorization-ledger.json|\
    docs/cognitive-architecture/architecture-roadmap.md|\
    docs/cognitive-architecture/security-boundary.md|\
    docs/cognitive-architecture/operator-model.md|\
    examples/cognitive-architecture/aion-183-program-authorization.json|\
    examples/cognitive-architecture/aion-185-persistent-state-evaluation.json|\
    examples/cognitive-architecture/aion-185-world-model-authorization.json|\
    examples/cognitive-architecture/aion-186-predictive-world-model.json|\
    examples/cognitive-architecture/aion-187-world-model-evaluation.json|\
    examples/cognitive-architecture/aion-187-workspace-authorization.json|\
    examples/cognitive-architecture/aion-188-global-workspace.json|\
    examples/cognitive-architecture/aion-189-workspace-evaluation.json|\
    examples/cognitive-architecture/aion-189-consolidation-authorization.json|\
    examples/cognitive-architecture/aion-190-memory-consolidation.json|\
    examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json|\
    examples/cognitive-architecture/aion-191-planning-authorization.json|\
    examples/cognitive-architecture/aion-192-counterfactual-planning.json|\
    examples/cognitive-architecture/aion-193-counterfactual-planning-evaluation.json|\
    examples/cognitive-architecture/aion-193-information-acquisition-authorization.json|\
    examples/cognitive-architecture/aion-194-information-acquisition.json|\
    examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json|\
    examples/cognitive-architecture/aion-195-continual-learning-authorization.json|\
    examples/cognitive-architecture/aion-196-continual-learning.json|\
    examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json|\
    examples/cognitive-architecture/aion-198-shadow-runtime-authorization.json|\
    scripts/cognitive-architecture-authorization-check.sh|\
    scripts/cognitive-architecture-no-go-regression.sh|\
    scripts/cognitive-memory-consolidation-closeout-check.sh|\
    scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh|\
    scripts/cognitive-memory-consolidation-check.sh|\
    scripts/cognitive-memory-consolidation-no-go-regression.sh|\
    scripts/cognitive-counterfactual-planning-check.sh|\
    scripts/cognitive-counterfactual-planning-closeout-check.sh|\
    scripts/cognitive-counterfactual-planning-closeout-no-go-regression.sh|\
    scripts/cognitive-counterfactual-planning-no-go-regression.sh|\
    scripts/cognitive-information-acquisition-check.sh|\
    scripts/cognitive-information-acquisition-closeout-check.sh|\
    scripts/cognitive-information-acquisition-closeout-no-go-regression.sh|\
    scripts/cognitive-information-acquisition-no-go-regression.sh|\
    scripts/cognitive-continual-learning-check.sh|\
    scripts/cognitive-continual-learning-no-go-regression.sh|\
    scripts/cognitive-integrated-evaluation-check.sh|\
    scripts/cognitive-integrated-evaluation-no-go-regression.sh|\
    scripts/cognitive-shadow-runtime-authorization-check.sh|\
    scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh|\
    scripts/cognitive-persistent-state-check.sh|\
    scripts/cognitive-persistent-state-closeout-check.sh|\
    scripts/cognitive-persistent-state-closeout-no-go-regression.sh|\
    scripts/cognitive-world-model-check.sh|\
    scripts/cognitive-world-model-closeout-check.sh|\
    scripts/cognitive-world-model-closeout-no-go-regression.sh|\
    scripts/cognitive-world-model-no-go-regression.sh|\
    scripts/cognitive-global-workspace-check.sh|\
    scripts/cognitive-global-workspace-no-go-regression.sh|\
    scripts/cognitive-workspace-closeout-check.sh|\
    scripts/cognitive-workspace-closeout-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    services/brain-api/src/aion_brain/contracts/information_acquisition.py|\
    services/brain-api/src/aion_brain/contracts/continual_learning.py|\
    services/brain-api/src/aion_brain/contracts/memory_consolidation.py|\
    services/brain-api/src/aion_brain/contracts/planning.py|\
    services/brain-api/src/aion_brain/contracts/workspace.py|\
    services/brain-api/src/aion_brain/contracts/world_model.py|\
    services/brain-api/src/aion_brain/information_acquisition/__init__.py|\
    services/brain-api/src/aion_brain/information_acquisition/core.py|\
    services/brain-api/src/aion_brain/continual_learning/__init__.py|\
    services/brain-api/src/aion_brain/continual_learning/core.py|\
    services/brain-api/src/aion_brain/memory_consolidation/__init__.py|\
    services/brain-api/src/aion_brain/memory_consolidation/core.py|\
    services/brain-api/src/aion_brain/planning/__init__.py|\
    services/brain-api/src/aion_brain/planning/core.py|\
    services/brain-api/src/aion_brain/workspace/__init__.py|\
    services/brain-api/src/aion_brain/workspace/core.py|\
    services/brain-api/src/aion_brain/world_model/__init__.py|\
    services/brain-api/src/aion_brain/world_model/prediction.py|\
    services/brain-api/src/aion_brain/world_model/repository.py|\
    services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_predictive_world_model.py|\
    services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py|\
    services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_global_workspace.py|\
    services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py|\
    services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_counterfactual_planning.py|\
    services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py|\
    services/brain-api/tests/test_cognitive_information_acquisition.py|\
    services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py|\
    services/brain-api/tests/test_cognitive_continual_learning.py|\
    services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py|\
    services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py|\
    services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_memory_consolidation.py|\
    services/brain-api/tests/test_cognitive_memory_consolidation_closeout_authorization_docs.py|\
    services/brain-api/tests/test_cognitive_memory_consolidation_no_runtime_effect.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion204_is_scoped_knowledge_intelligence_authorization_path() {
  # Exact AION-204 Knowledge Intelligence authorization paths. These records
  # are outside the v0.2 runtime enablement track and do not exempt runtime
  # source, API routes, package files, migrations, credentials, or releases.
  case "$1" in
    docs/release/knowledge-intelligence-research-authorization-transaction.md|\
    operator-console-static/demo-data/knowledge-intelligence-research-authorization.json)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion205_is_scoped_knowledge_intelligence_research_acquisition_path() {
  # Exact/prefix AION-205 Knowledge Intelligence research-acquisition paths.
  # These remain outside production-auth runtime enablement and do not exempt
  # auth APIs, providers, package files, migrations, credentials, or releases.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0169-controlled-research-acquisition-and-immutable-source-snapshots.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/visual-brain.md|\
    scripts/knowledge-intelligence-research-authorization-check.sh|\
    scripts/knowledge-intelligence-research-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-plane-check.sh|\
    scripts/knowledge-intelligence-research-plane-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-runtime-hold.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_research.py|\
    services/brain-api/tests/knowledge_intelligence_test_helpers.py|\
    services/brain-api/tests/knowledge_research_test_helpers.py|\
    services/brain-api/tests/test_knowledge_intelligence_cognitive_closeout_reconciliation.py|\
    services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py|\
    services/brain-api/tests/test_knowledge_intelligence_research_budget_spec.py|\
    docs/knowledge-intelligence/*|\
    docs/release/knowledge-intelligence-research*|\
    examples/knowledge-intelligence/*|\
    operator-console-static/*|\
    services/brain-api/src/aion_brain/knowledge_intelligence/*|\
    services/brain-api/tests/test_knowledge_research*|\
    services/brain-api/tests/test_knowledge_source*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion207_is_scoped_knowledge_intelligence_source_registry_path() {
  # Exact/prefix AION-207 Knowledge Intelligence source-registry paths. These
  # are metadata-only registry implementation artifacts, not production-auth
  # authorization, provider, credential, package, migration, API, or runtime
  # enablement surfaces.
  case "$1" in
    docs/adr/0171-append-only-source-provenance-registry-core.md|\
    docs/adr/README.md|\
    docs/knowledge-intelligence/aion-207-checklist.md|\
    docs/knowledge-intelligence/source-registry-*|\
    docs/release/knowledge-intelligence-source-registry-*|\
    examples/knowledge-intelligence/source-registry-*|\
    operator-console-static/demo-data/knowledge-intelligence-source-registry*.json|\
    scripts/knowledge-intelligence-source-registry-authorization-check.sh|\
    scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-source-registry-check.sh|\
    scripts/knowledge-intelligence-source-registry-no-go-regression.sh|\
    scripts/knowledge-intelligence-source-registry-runtime-hold.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py|\
    services/brain-api/tests/knowledge_source_registry_implementation_helpers.py|\
    services/brain-api/tests/knowledge_source_registry_test_helpers.py|\
    services/brain-api/tests/test_knowledge_source_registry*.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion209_is_scoped_knowledge_intelligence_claim_graph_path() {
  # Exact/prefix AION-209 Knowledge Intelligence claim-graph paths. These
  # artifacts remain outside production-auth runtime enablement and do not
  # exempt auth APIs, providers, credentials, package files, migrations, or
  # releases.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0173-immutable-temporal-claim-evidence-graph-core.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/visual-brain.md|\
    scripts/auth-design-check.sh|\
    scripts/cognitive-local-offline-pilot-closeout-check.sh|\
    scripts/knowledge-intelligence-claim-graph-authorization-check.sh|\
    scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-check.sh|\
    scripts/knowledge-intelligence-claim-graph-no-go-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-runtime-hold.sh|\
    scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-runtime-hold.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/production-auth-core-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py|\
    services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py|\
    docs/knowledge-intelligence/*|\
    docs/release/knowledge-intelligence-claim-graph-*|\
    examples/knowledge-intelligence/*|\
    operator-console-static/*|\
    services/brain-api/src/aion_brain/knowledge_intelligence/*|\
    services/brain-api/tests/test_knowledge_claim_graph*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion211_is_scoped_knowledge_intelligence_epistemic_assessment_path() {
  # Exact/prefix AION-211 Knowledge Intelligence epistemic-assessment paths.
  # These deterministic in-memory assessment artifacts remain outside
  # production-auth runtime enablement and do not exempt auth APIs, providers,
  # credentials, package files, migrations, or releases.
  case "$1" in
    AGENTS.md|\
    README.md|\
    docs/adr/0175-deterministic-epistemic-evidence-assessment-engine-core.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/visual-brain.md|\
    scripts/connector-runtime-no-external-call-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-authorization-check.sh|\
    scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-check.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh|\
    scripts/knowledge-intelligence-research-authorization-check.sh|\
    scripts/knowledge-intelligence-research-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-runtime-hold.sh|\
    scripts/knowledge-intelligence-source-registry-authorization-check.sh|\
    scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-architecture-check.sh|\
    scripts/static-console-safety-check.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py|\
	    services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py|\
	    services/brain-api/tests/knowledge_claim_graph_evaluation_test_helpers.py|\
	    services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py|\
	    services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py|\
	    services/brain-api/tests/test_knowledge_research_authorization_closeout.py|\
	    services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py|\
	    docs/knowledge-intelligence/*|\
	    docs/release/knowledge-intelligence-epistemic-assessment-*|\
	    docs/release/knowledge-intelligence-epistemic-truth-*|\
    examples/knowledge-intelligence/*|\
    operator-console-static/*|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion212_is_scoped_knowledge_intelligence_epistemic_assessment_evaluation_path() {
  # Exact/prefix AION-212 Knowledge Intelligence evaluation and domain expert
  # mesh authorization artifacts. These are docs, static evidence, harnesses,
  # and tests only; no runtime source, API, dependency, migration, or workflow
  # paths are exempted here.
  case "$1" in
    docs/adr/0176-epistemic-assessment-evaluation-and-domain-expert-mesh-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/visual-brain.md|\
    docs/knowledge-intelligence/*|\
    docs/release/knowledge-intelligence-domain-expert-mesh-*|\
    docs/release/knowledge-intelligence-epistemic-assessment-evaluation-*|\
    examples/knowledge-intelligence/*|\
    operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-*.json|\
    operator-console-static/demo-data/knowledge-intelligence-epistemic-assessment-evaluation.json|\
    scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-claim-graph-runtime-hold.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-check.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-runtime-hold.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-check.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-runtime-hold.sh|\
    scripts/knowledge-intelligence-source-registry-runtime-hold.sh|\
    scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py|\
    scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/lib/v02_production_auth_authorization.py|\
    services/brain-api/tests/test_knowledge_domain_expert_mesh_*.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_authorization_closeout.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_*.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_operator_evaluation.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_operator_evaluation_docs.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion213_is_scoped_knowledge_intelligence_domain_expert_mesh_path() {
  # Scoped AION-213 Knowledge Intelligence domain expert mesh implementation
  # artifacts. Production auth runtime files, package files, migrations, API
  # routes, workflows, and releases remain blocked by the caller.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/adr/0177-deterministic-domain-expert-mesh-core.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/visual-brain.md|\
    docs/knowledge-intelligence/*|\
    docs/release/knowledge-intelligence-domain-expert-mesh-*|\
    docs/release/v02-release-readiness-delta.md|\
    examples/knowledge-intelligence/*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/knowledge-intelligence-domain-expert-*.json|\
    scripts/knowledge-intelligence-domain-expert-mesh-*.sh|\
    scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py|\
    services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py|\
    services/brain-api/tests/knowledge_domain_expert_mesh_test_helpers.py|\
    services/brain-api/tests/test_knowledge_domain_expert_mesh_*.py|\
    services/brain-api/tests/test_knowledge_intelligence_current_projection.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion215_is_scoped_knowledge_intelligence_tool_verification_path() {
  # Scoped AION-215 Knowledge Intelligence tool-verification implementation
  # artifacts. This is a deterministic simulation-only fabric; production auth
  # runtime files, API routes, package files, migrations, workflows, and releases
  # remain blocked by the caller.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/adr/0178-domain-expert-mesh-evaluation-and-tool-verification-authorization.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/visual-brain.md|\
    docs/knowledge-intelligence/*|\
    docs/release/knowledge-intelligence-tool-verification-*|\
    docs/release/v02-release-readiness-delta.md|\
    examples/knowledge-intelligence/tool-*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/knowledge-intelligence-program.json|\
    operator-console-static/demo-data/knowledge-intelligence-tool-*.json|\
    scripts/knowledge-intelligence-tool-verification-*.sh|\
    scripts/lib/knowledge_intelligence_tool_verification_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_tool_verification.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_attestation.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_effects.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_integrity.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_manifests.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_planning.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_simulation.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification_fabric.py|\
    services/brain-api/tests/test_knowledge_tool_verification_*.py|\
    services/brain-api/tests/test_knowledge_intelligence_current_projection.py|\
    services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py|\
    services/brain-api/tests/test_knowledge_research_authorization_closeout.py|\
    services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py|\
    services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py|\
    services/brain-api/tests/test_knowledge_claim_graph_authorization_closeout.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_domain_expert_mesh_evaluation_repository_integrity.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion219_is_scoped_knowledge_intelligence_public_research_pilot_path() {
  # Scoped AION-219 controlled public research pilot artifacts. This allows the
  # operator-invoked HTTPS pilot surface through inherited production-auth drift
  # scanners while package files, migrations, API routes, workflows, and releases
  # remain blocked by the caller and by the AION-219 gates.
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/adr/0183-controlled-operator-invoked-public-https-research-and-verified-candidate-pilot.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/policy-model.md|\
    docs/project-status.md|\
    docs/visual-brain.md|\
    docs/knowledge-intelligence/aion-219-checklist.md|\
    docs/knowledge-intelligence/architecture-roadmap.md|\
    docs/knowledge-intelligence/authorization-ledger.json|\
    docs/knowledge-intelligence/operator-model.md|\
    docs/knowledge-intelligence/program-charter.md|\
    docs/knowledge-intelligence/program-ledger.json|\
    docs/knowledge-intelligence/public-research-pilot-*|\
    docs/knowledge-intelligence/security-boundary.md|\
    docs/release/knowledge-intelligence-public-research-pilot-*|\
    docs/release/v02-release-readiness-delta.md|\
    examples/knowledge-intelligence/public-research-*|\
    examples/knowledge-intelligence/public-research-pilot-*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/index.html|\
    operator-console-static/demo-data/knowledge-intelligence-public-research-pilot-*.json|\
    scripts/knowledge-intelligence-claim-graph-authorization-check.sh|\
    scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-check.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-check.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh|\
    scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-public-research-pilot-*.sh|\
    scripts/knowledge-intelligence-public-research-pilot-run.py|\
    scripts/knowledge-intelligence-research-authorization-check.sh|\
    scripts/knowledge-intelligence-research-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-runtime-hold.sh|\
    scripts/knowledge-intelligence-source-registry-authorization-check.sh|\
    scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-source-registry-check.sh|\
    scripts/knowledge-intelligence-source-registry-no-go-regression.sh|\
    scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh|\
    scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py|\
    scripts/lib/knowledge_intelligence_tool_verification_authorization.py|\
    scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/production-auth-identity-assertion-replay-no-go-regression.sh|\
    scripts/production-auth-request-identity-no-go-regression.sh|\
    scripts/production-auth-request-identity-stabilization-no-go-regression.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py|\
    services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py|\
    services/brain-api/tests/public_research_pilot_test_helpers.py|\
    services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py|\
    services/brain-api/tests/test_knowledge_domain_expert_mesh_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_intelligence_aion218_delivery_reconciliation.py|\
    services/brain-api/tests/test_knowledge_intelligence_current_projection.py|\
    services/brain-api/tests/test_knowledge_intelligence_current_state_consistency.py|\
    services/brain-api/tests/test_knowledge_public_research_*.py|\
    services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion235_is_scoped_sandboxed_capability_runtime_path() {
  if [[ ! -f docs/secure-runtime-integration/program-ledger.json ]] || \
    ! grep -q '"program_state": "sandboxed_capability_runtime_implemented_reference_only_pending_closeout"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"active_sri_implementation_authorization": "AION-234-SRI-0003"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"active_sri_implementation_task": "AION-235"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"formal_closeout_task": "AION-236"' docs/secure-runtime-integration/program-ledger.json; then
    return 1
  fi
  case "$1" in
    README.md|AGENTS.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/capability-runtime-*|\
    docs/adr/0199-sandboxed-deterministic-capability-and-synthetic-connector-runtime.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/capability-runtime-*|\
    operator-console-static/app.js|\
    operator-console-static/demo-data/capability-runtime-*.json|\
    scripts/capability-runtime-*.sh|\
    scripts/capability-runtime-local-sandbox-run.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/model-gateway-authorization-check.sh|\
    scripts/model-gateway-authorization-no-go-regression.sh|\
    scripts/model-gateway-check.sh|\
    scripts/model-gateway-no-go-regression.sh|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py|\
    services/brain-api/src/aion_brain/capability_runtime/__init__.py|\
    services/brain-api/src/aion_brain/capability_runtime/authorization.py|\
    services/brain-api/src/aion_brain/capability_runtime/component_binding.py|\
    services/brain-api/src/aion_brain/capability_runtime/manifests.py|\
    services/brain-api/src/aion_brain/capability_runtime/request_envelope.py|\
    services/brain-api/src/aion_brain/capability_runtime/input_validation.py|\
    services/brain-api/src/aion_brain/capability_runtime/execution_plan.py|\
    services/brain-api/src/aion_brain/capability_runtime/sandbox.py|\
    services/brain-api/src/aion_brain/capability_runtime/guard.py|\
    services/brain-api/src/aion_brain/capability_runtime/dispatcher.py|\
    services/brain-api/src/aion_brain/capability_runtime/reference_capabilities.py|\
    services/brain-api/src/aion_brain/capability_runtime/reference_connector.py|\
    services/brain-api/src/aion_brain/capability_runtime/budget.py|\
    services/brain-api/src/aion_brain/capability_runtime/audit.py|\
    services/brain-api/src/aion_brain/capability_runtime/observability.py|\
    services/brain-api/src/aion_brain/capability_runtime/integrity.py|\
    services/brain-api/src/aion_brain/capability_runtime/evidence.py|\
    services/brain-api/tests/capability_runtime_test_support.py|\
    services/brain-api/tests/test_capability_runtime_*.py|\
    services/brain-api/tests/test_secure_runtime_current_state_*.py|\
    services/brain-api/tests/test_secure_runtime_integration_*.py|\
    services/brain-api/tests/test_model_gateway_current_state_consistency.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion237_is_scoped_operator_console_integrated_local_runtime_path() {
  if [[ ! -f docs/secure-runtime-integration/program-ledger.json ]] || \
    ! grep -q '"program_state": "operator_console_integrated_local_runtime_implemented_pending_final_evaluation"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"active_sri_implementation_authorization": "AION-236-SRI-0004"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"active_sri_implementation_task": "AION-237"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"formal_closeout_task": "AION-238"' docs/secure-runtime-integration/program-ledger.json; then
    return 1
  fi
  case "$1" in
    README.md|AGENTS.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/release/operator-console-*|\
    docs/release/capability-runtime-*|\
    docs/release/v02-release-readiness-delta.md|\
    docs/adr/0201-controlled-same-origin-loopback-operator-console-and-integrated-local-runtime.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/operator-console-*.json|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/index.html|\
    operator-console-static/live-console.js|\
    operator-console-static/styles.css|\
    operator-console-static/demo-data/operator-console-*.json|\
    scripts/operator-console-integrated-local-run.py|\
    scripts/operator-console-integrated-pilot-evidence-check.sh|\
    scripts/operator-console-integration-*.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/auth-design-check.sh|\
    scripts/auth-no-go-regression.sh|\
    scripts/auth-runtime-check.sh|\
    scripts/local-auth-check.sh|\
    scripts/local-session-check.sh|\
    scripts/role-filter-check.sh|\
    scripts/capability-runtime-*.sh|\
    scripts/connector-*.sh|\
    scripts/knowledge-intelligence-*-no-go-regression.sh|\
    scripts/model-gateway-*.sh|\
    scripts/operator-platform-*.sh|\
    scripts/platform-integration-no-go-regression.sh|\
    scripts/post-v01-release-candidate-no-go-regression.sh|\
    scripts/secure-runtime-foundation-*.sh|\
    scripts/secure-runtime-integration-*.sh|\
    scripts/v02-*.sh|\
    scripts/lib/cognitive_architecture_governance.py|\
    scripts/lib/portable-search.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/operator_console_integration.py|\
    services/brain-api/src/aion_brain/operator_console_runtime/*|\
    services/brain-api/tests/operator_console_integration_test_support.py|\
    services/brain-api/tests/test_operator_console_integration_*.py|\
    services/brain-api/tests/test_operator_console_integrated_*.py|\
    services/brain-api/tests/test_capability_runtime_current_state_after_aion235.py|\
    services/brain-api/tests/test_model_gateway_*.py|\
    services/brain-api/tests/test_secure_runtime_current_state_*.py|\
    services/brain-api/tests/test_secure_runtime_integration_*.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion238_is_scoped_secure_runtime_final_closeout_path() {
  if [[ ! -f docs/secure-runtime-integration/program-ledger.json ]] || \
    ! grep -q '"program_state": "secure_runtime_integration_program_complete"' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"active_sri_implementation_authorization_count": 0' docs/secure-runtime-integration/program-ledger.json || \
    ! grep -q '"successor_authorization_id": "AION-238-V02RQ-0001"' docs/secure-runtime-integration/program-ledger.json; then
    return 1
  fi
  case "$1" in
    README.md|AGENTS.md|\
    docs/project-status.md|docs/architecture.md|docs/brain-contract.md|docs/policy-model.md|docs/visual-brain.md|\
    docs/secure-runtime-integration/*|\
    docs/v02-release-qualification/*|\
    docs/release/secure-runtime-integration-*|\
    docs/release/operator-console-integration-implementation.md|\
    docs/release/operator-console-integrated-local-pilot.md|\
    docs/release/operator-console-integration-runtime-hold.md|\
    docs/release/v02-release-readiness-delta.md|\
    docs/release/v02-release-qualification-*|\
    docs/adr/0202-final-secure-runtime-integration-evaluation-and-v02-release-qualification-program-authorization.md|\
    docs/adr/0203-disabled-v02-production-readiness-qualification-foundation.md|\
    docs/adr/README.md|\
    examples/secure-runtime-integration/*|\
    examples/v02-release-qualification/*|\
    operator-console-static/README.md|\
    operator-console-static/app.js|\
    operator-console-static/index.html|\
    operator-console-static/demo-data/secure-runtime-integration-*.json|\
    operator-console-static/demo-data/v02-release-qualification-*.json|\
    scripts/auth-design-check.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/operator-console-integration-authorization-check.sh|\
    scripts/operator-console-integration-check.sh|\
    scripts/operator-console-integration-runtime-hold.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh|\
    scripts/static-console-safety-check.sh|\
    scripts/secure-runtime-integration-final-evaluation-check.sh|\
    scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-authorization-check.sh|\
    scripts/secure-runtime-integration-program-complete-check.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/secure-runtime-integration-runtime-hold.sh|\
    scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh|\
    scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-program-authorization-check.sh|\
    scripts/v02-release-qualification-program-authorization-no-go-regression.sh|\
    scripts/v02-release-qualification-runtime-hold.sh|\
    scripts/v02-release-qualification-foundation-check.sh|\
    scripts/v02-release-qualification-foundation-no-go-regression.sh|\
    scripts/v02-release-qualification-foundation-pilot-evidence-check.sh|\
    scripts/v02-release-qualification-foundation-runtime-hold.sh|\
    scripts/v02-release-qualification-local-run.py|\
    scripts/lib/secure_runtime_integration_final_evaluation.py|\
    scripts/lib/v02_production_auth_authorization.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    services/brain-api/src/aion_brain/contracts/v02_release_qualification.py|\
    services/brain-api/src/aion_brain/v02_release_qualification/*|\
    services/brain-api/tests/secure_runtime_integration_final_evaluation_test_support.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py|\
    services/brain-api/tests/test_secure_runtime_integration_final_evaluation_aion238.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion232.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion234.py|\
    services/brain-api/tests/test_secure_runtime_current_state_after_aion236.py|\
    services/brain-api/tests/test_secure_runtime_current_state_consistency.py|\
    services/brain-api/tests/test_secure_runtime_integration_authorization.py|\
    services/brain-api/tests/test_secure_runtime_integration_program_charter.py|\
    services/brain-api/tests/test_secure_runtime_integration_project_status.py|\
    services/brain-api/tests/test_capability_runtime_current_state_after_aion235.py|\
    services/brain-api/tests/test_model_gateway_*.py|\
    services/brain-api/tests/test_operator_console_integration_authorization.py|\
    services/brain-api/tests/test_v02_release_qualification_*.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion243_is_scoped_v02_release_candidate_artifact_build_path() {
  case "$1" in
    docs/adr/0207-deterministic-local-v02-release-candidate-artifact-bundle-build-and-retention.md|\
    docs/adr/README.md|\
    docs/project-status.md|\
    docs/v02-release-qualification/aion-243-checklist.md|\
    docs/v02-release-qualification/authorization-ledger.json|\
    docs/v02-release-qualification/program-ledger.json|\
    examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json|\
    examples/v02-release-qualification/v02-release-candidate-artifact-build-plan.json|\
    operator-console-static/demo-data/v02-release-candidate-artifact-build.json|\
    packages/aion-sdk-python/pyproject.toml|\
    scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-program-final-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh|\
    scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh|\
    scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/lib/v02_staging_qualification_operator_evaluation.py|\
    scripts/model-gateway-operator-evaluation-no-go-regression.sh|\
    scripts/operator-console-static-check.sh|\
    scripts/secure-runtime-foundation-operator-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/self-improvement-governance-no-go-regression.sh|\
    scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    services/brain-api/pyproject.toml|\
    services/brain-api/src/aion_brain/contracts/v02_release_candidate.py|\
    services/brain-api/tests/aion243_release_candidate_scope.py|\
    services/brain-api/tests/test_governed_learning_memory_no_runtime_source.py|\
    services/brain-api/tests/test_identity_assertion_no_runtime_integration.py|\
    services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py|\
    services/brain-api/tests/test_knowledge_epistemic_assessment_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_intelligence_program_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_research_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py|\
    services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py|\
    services/brain-api/tests/test_v02_actor_context_trust_boundary_authorization_docs.py|\
    services/brain-api/tests/test_v02_identity_assertion_replay_protection_authorization_docs.py|\
    services/brain-api/tests/test_v02_offline_identity_assertion_verification_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_request_identity_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py|\
    services/brain-api/tests/test_v02_release_candidate_artifact_build_aion243.py|\
    services/brain-api/tests/test_v02_staging_qualification_operator_evaluation_aion242.py|\
    docs/release/v02-release-candidate-*|\
    docs/v02-release-qualification/release-candidate-*|\
    scripts/v02-release-candidate-*|\
    services/brain-api/src/aion_brain/v02_release_candidate/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion244_is_scoped_v02_release_candidate_final_evaluation_path() {
  case "$1" in
    README.md|\
    AGENTS.md|\
    docs/adr/0208-final-v02-rc1-candidate-evaluation-and-github-prerelease-publication.md|\
    docs/adr/README.md|\
    docs/architecture.md|\
    docs/brain-contract.md|\
    docs/project-status.md|\
    docs/visual-brain.md|\
    docs/release/aion-v0.2.0-rc.1-*|\
    docs/release/v02-release-qualification-program-final-closeout.md|\
    docs/v02-release-qualification/*|\
    examples/v02-release-qualification/*|\
    operator-console-static/demo-data/v02-rc1-*.json|\
    operator-console-static/demo-data/v02-release-candidate-final-evaluation.json|\
    scripts/auth-design-check.sh|\
    scripts/secure-runtime-foundation-no-go-regression.sh|\
    scripts/secure-runtime-integration-final-evaluation-no-go-regression.sh|\
    scripts/secure-runtime-integration-program-no-go-regression.sh|\
    scripts/lib/v02_release_candidate_final_evaluation.py|\
    scripts/lib/v02_release_qualification_foundation_operator_evaluation.py|\
    scripts/lib/v02_staging_qualification_operator_evaluation.py|\
    scripts/lib/v02-production-auth-scan-exclusions.sh|\
    scripts/v02-rc1-release-*.sh|\
    scripts/v02-release-candidate-final-evaluation-*.sh|\
    scripts/v02-release-qualification-foundation-*.sh|\
    scripts/v02-release-qualification-program-authorization-*.sh|\
    scripts/v02-release-qualification-program-final-complete-check.sh|\
    scripts/v02-staging-qualification-*.sh|\
    services/brain-api/tests/test_secure_runtime_integration_final_closeout_aion238.py|\
    services/brain-api/tests/test_v02_release_candidate_artifact_build_aion243.py|\
    services/brain-api/tests/test_v02_release_qualification_pilot_evidence_aion239.py|\
    services/brain-api/tests/test_v02_release_qualification_operator_evaluation_aion240.py|\
    services/brain-api/tests/test_v02_staging_qualification_operator_evaluation_aion242.py|\
    services/brain-api/tests/test_v02_release_candidate_final_evaluation_aion244.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

aion151_validate_scoped_authorization_if_present() {
  if [[ -f examples/release/v02-production-auth-implementation-authorization.json ]]; then
    python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go
  fi
}
