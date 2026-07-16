# Production Auth Core Stabilization

AION-154 stabilizes the internal `aion_brain.production_auth` core while keeping
the production-auth runtime disabled. The work consumes the active AION-153
authorization only when PR 64 merges.

Role comparison:

- AION-151 authorized initial disabled-core implementation through
  `AION-151-PA-0001`; it is historical, inactive, expired, consumed by
  AION-152, and non-reusable.
- AION-152 implemented the internal disabled production-auth core without public
  production-auth API routes.
- AION-153 created `AION-153-PA-0002` for AION-154 stabilization only.
- AION-154 hardens contracts, canonical evidence, reason codes, redaction,
  idempotency, concurrency, diagnostics, and gates without enabling runtime.

Architecture separation remains unchanged:

- `aion_brain.auth_runtime` remains the preview/status/mock-claims boundary.
- `aion_brain.production_auth` remains the internal implemented disabled core.

Stabilization fields are separate from historical implementation fields:

- `implementation_authorization_transaction_id=AION-151-PA-0001`
- `implementation_authorization_task=AION-152`
- `implementation_authorization_scope=disabled-production-auth-core`
- `stabilization_authorization_transaction_id=AION-153-PA-0002`
- `stabilization_authorization_task=AION-154`
- `stabilization_authorization_scope=disabled-production-auth-core-stabilization`
- `stabilization_authorization_reusable=false`
- `stabilization_authorization_expires_on_aion_154_merge=true`

Runtime state remains blocked:

- `production_auth_core_state=implemented_disabled`
- `production_auth_runtime_enabled=false`
- `runtime_no_go_status=true`
- `runtime_implementation_approved=false`
- `runtime_enablement_guard_release_approved=false`
- login, logout, callback, token, session, credential, provider, external-call,
  package, migration, SDK, CLI, tag, and release surfaces remain absent.

Local gates:

```bash
./scripts/production-auth-core-stabilization-no-go-regression.sh
./scripts/production-auth-core-stabilization-check.sh
./scripts/production-auth-core-stabilization-runtime-hold.sh
```
