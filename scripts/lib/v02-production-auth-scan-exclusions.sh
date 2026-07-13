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
    docs/adr/0142-v02-production-auth-implementation-authorization.md|\
    docs/adr/0144-v02-production-auth-core-stabilization-authorization.md|\
    examples/release/v02-production-auth-authorization-evidence-matrix.json|\
    examples/release/v02-production-auth-core-implementation-closeout.json|\
    examples/release/v02-production-auth-explicit-approval-record.json|\
    examples/release/v02-production-auth-implementation-authorization.json|\
    examples/release/v02-production-auth-runtime-guard-hold.json|\
    examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json|\
    examples/release/v02-production-auth-stabilization-authorization.json|\
    examples/release/v02-production-auth-stabilization-explicit-approval-record.json|\
    examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json|\
    operator-console-static/demo-data/v02-production-auth-authorization.json|\
    operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json|\
    operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json|\
    operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json|\
    services/brain-api/tests/test_v02_production_auth_authorization_docs.py|\
    scripts/v02-production-auth-authorization-check.sh|\
    scripts/v02-production-auth-runtime-guard-hold.sh|\
    scripts/v02-production-auth-authorization-no-go-regression.sh|\
    scripts/v02-production-auth-stabilization-authorization-check.sh|\
    scripts/v02-production-auth-stabilization-runtime-guard-hold.sh|\
    scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh|\
    services/brain-api/tests/test_v02_production_auth_stabilization_authorization_docs.py|\
    scripts/lib/v02_production_auth_authorization.py|\
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
