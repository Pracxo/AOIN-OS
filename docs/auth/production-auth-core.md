# Production Auth Core

AION-152 implements the disabled production-auth core authorized by
`authorization_transaction_id=AION-151-PA-0001` for
`authorization_scope=disabled-production-auth-core`.

The core lives in `aion_brain.production_auth` as an internal package separate
from the preview-oriented `aion_brain.auth_runtime` package.

Required state:

- `production_auth_core_implemented=true`
- `production_auth_core_state=implemented_disabled`
- `authorization_consumed_by_task=AION-152`
- `authorization_reusable=false`
- `authorization_expires_on_aion_152_merge=true`
- `runtime_guard_hold_active=true`
- `runtime_no_go_status=true`
- `runtime_implementation_approved=false`
- `production_auth_runtime_enabled=false`

AION-153 closes `AION-151-PA-0001` as approved historical evidence:
`authorization_active=false`, `authorization_consumed=true`,
`authorization_consumed_by_pr=62`, `authorization_expired=true`, and
`authorization_reusable=false`.

The next active authorization is `AION-153-PA-0002` for future AION-154
`disabled-production-auth-core-stabilization` work only. AION-153 does not
modify this production-auth core package.

## AION-154 Stabilized Core Evidence

AION-154 adds canonical serialization, fingerprints, reason-code registry
validation, typed internal operation checks, immutable evidence records,
idempotency and concurrency tests, redaction hardening, and runtime-hold gates.
The internal core remains `implemented_disabled`, and production-auth runtime
remains disabled.

The implementation adds strict contracts, fail-closed configuration, blocked
policy decisions, redacted audit/provenance builders, redacted diagnostics, and
kernel wiring. It does not add login, logout, callback, credential, token,
session, cookie, provider, SDK, CLI, or public API behavior.
