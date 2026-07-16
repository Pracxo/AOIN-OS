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
