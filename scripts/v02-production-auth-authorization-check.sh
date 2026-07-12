#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

required_docs=(
  docs/release/v02-production-auth-implementation-authorization-transaction.md
  docs/release/v02-production-auth-explicit-approval-record.md
  docs/release/v02-production-auth-implementation-scope.md
  docs/release/v02-production-auth-runtime-guard-hold.md
  docs/release/v02-production-auth-authorization-evidence-matrix.md
  docs/release/v02-production-auth-authorization-no-go.md
  docs/release/v02-production-auth-authorization-checklist.md
  docs/adr/0142-v02-production-auth-implementation-authorization.md
)

required_json=(
  examples/release/v02-production-auth-implementation-authorization.json
  examples/release/v02-production-auth-explicit-approval-record.json
  examples/release/v02-production-auth-runtime-guard-hold.json
  examples/release/v02-production-auth-authorization-evidence-matrix.json
  operator-console-static/demo-data/v02-production-auth-authorization.json
  operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json
)

for file in "${required_docs[@]}" "${required_json[@]}"; do
  test -f "$file" || {
    echo "missing AION-151 production auth authorization artifact: $file" >&2
    exit 1
  }
done

grep -q "0142-v02-production-auth-implementation-authorization.md" docs/adr/README.md || {
  echo "ADR 0142 is not indexed" >&2
  exit 1
}

python3 scripts/lib/v02_production_auth_authorization.py --repo-root "$ROOT_DIR" --mode check

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/v02-authorization-track-closeout.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

cat <<'SUMMARY'
v0.2 production auth authorization check result:
- authorization_transaction_id: AION-151-PA-0001
- candidate_id: production-auth-core
- workstream: production-auth-implementation
- implementation_task: AION-152
- authorization_scope: disabled-production-auth-core
- implementation authorization: approved for the scoped record only
- implementation go: true for the scoped record only
- runtime implementation approved: false
- production auth runtime enabled: false
- runtime guard release approved: false
- endpoint, storage, provider, external-call, package, migration, connector, operator, module, and sandbox approvals: false
v0.2 production auth authorization check PASS
SUMMARY
