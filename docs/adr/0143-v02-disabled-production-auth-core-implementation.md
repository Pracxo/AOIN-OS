# 0143: v0.2 Disabled Production Auth Core Implementation

## Status

Accepted for AION-152.

## Context

AION-151 approved one scoped implementation transaction:
`authorization_transaction_id=AION-151-PA-0001`,
`authorization_scope=disabled-production-auth-core`, and
`implementation_task=AION-152`. The approval does not authorize production auth
runtime behavior.

The existing `aion_brain.auth_runtime` package owns prototype/status/preview
surfaces: disabled runtime status, mock claims previews, actor-context previews,
read-only API evidence, and no-go audit proof.

The new `aion_brain.production_auth` package owns an internal implemented core:
strict contracts, fail-closed config, blocked policy interfaces, redacted
audit/provenance construction, diagnostics, and kernel wiring with zero public
runtime effect.

## Decision

Create a separate internal package,
`services/brain-api/src/aion_brain/production_auth/`, rather than converting the
preview package into production runtime.

## Consequences

This preserves API stability, keeps preview evidence isolated, prevents
accidental runtime activation, and gives future tasks a controlled implementation
boundary.

AION-152 reports:

- `production_auth_core_implemented=true`
- `production_auth_core_state=implemented_disabled`
- `authorization_consumed_by_task=AION-152`
- `authorization_reusable=false`
- `authorization_expires_on_aion_152_merge=true`
- `runtime_guard_hold_active=true`
- `runtime_no_go_status=true`
- `runtime_implementation_approved=false`
- `production_auth_runtime_enabled=false`

No login, logout, callback, credential, token, session, cookie, provider,
OAuth, OIDC, SAML, external-call, SDK, CLI, migration, package, tag, or release
surface is added.
