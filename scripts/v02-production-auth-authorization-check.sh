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
- historical authorization_transaction_id: AION-151-PA-0001
- historical candidate_id: production-auth-core
- historical implementation_task: AION-152
- historical authorization_scope: disabled-production-auth-core
- historical lifecycle: inactive, consumed, expired, non-reusable
- historical authorization_transaction_id: AION-153-PA-0002
- historical candidate_id: production-auth-core-stabilization
- historical implementation_task: AION-154
- historical authorization_scope: disabled-production-auth-core-stabilization
- historical lifecycle: inactive, consumed, expired, non-reusable
- historical authorization_transaction_id: AION-155-PA-0003
- historical candidate_id: production-auth-request-identity-boundary
- historical implementation_task: AION-156
- historical authorization_scope: disabled-request-identity-boundary
- historical lifecycle: inactive, consumed, expired, non-reusable
- historical authorization_transaction_id: AION-157-PA-0004
- historical candidate_id: production-auth-request-identity-boundary-stabilization
- historical implementation_task: AION-158
- historical authorization_scope: disabled-request-identity-boundary-stabilization
- historical lifecycle: inactive, consumed, expired, non-reusable
- historical authorization_transaction_id: AION-159-PA-0005
- historical candidate_id: production-auth-actor-context-trust-boundary
- historical implementation_task: AION-160
- historical authorization_scope: fail-closed-actor-context-resolution
- historical lifecycle: inactive, consumed, expired, non-reusable
- historical authorization_transaction_id: AION-161-PA-0006
- historical candidate_id: production-auth-offline-identity-assertion-verification
- historical implementation_task: AION-162
- historical authorization_scope: offline-ed25519-identity-assertion-verification
- historical lifecycle: inactive, consumed, expired, non-reusable
- active authorization_transaction_id: AION-163-PA-0007
- active candidate_id: production-auth-identity-assertion-replay-protection
- active implementation_task: AION-164
- active authorization_scope: persistent-identity-assertion-replay-protection-core
- implementation authorization: approved for the exact lifecycle records only
- implementation go: true for the exact active lifecycle record only
- runtime implementation approved: false
- production auth runtime enabled: false
- runtime guard release approved: false
- endpoint, storage, provider, external-call, package, migration, connector, operator, module, and sandbox approvals: false
v0.2 production auth authorization check PASS
SUMMARY
