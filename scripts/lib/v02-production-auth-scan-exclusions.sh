#!/usr/bin/env bash

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
        if ! aion151_is_scoped_authorization_path "$file"; then
          printf '%s\n' "$file"
        fi
      done < <(find "$path" -type f -print)
    elif [[ -f "$path" ]]; then
      file="${path#./}"
      if ! aion151_is_scoped_authorization_path "$file"; then
        printf '%s\n' "$file"
      fi
    fi
  done
}

aion151_validate_scoped_authorization_if_present() {
  if [[ -f examples/release/v02-production-auth-implementation-authorization.json ]]; then
    python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode no-go
  fi
}
