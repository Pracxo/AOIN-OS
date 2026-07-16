# 0145: v0.2 Production Auth Core Stabilization

## Status

Accepted for AION-154.

## Context

AION-151 authorized the initial disabled production-auth core through
`AION-151-PA-0001`. AION-152 consumed that authorization and implemented only
the internal disabled core. AION-153 created `AION-153-PA-0002` as the active
single-use authorization for AION-154 stabilization.

## Decision

AION-154 stabilizes `aion_brain.production_auth` without enabling runtime auth
or merging it with `aion_brain.auth_runtime`.

Architecture comparison:

- `aion_brain.auth_runtime` remains a preview/status/mock-claims compatibility
  surface.
- `aion_brain.production_auth` remains the implemented internal disabled core.

Authorization lineage:

- Historical implementation lineage remains
  `implementation_authorization_transaction_id=AION-151-PA-0001`,
  `implementation_authorization_task=AION-152`, and
  `implementation_authorization_scope=disabled-production-auth-core`.
- Stabilization lineage is added as
  `stabilization_authorization_transaction_id=AION-153-PA-0002`,
  `stabilization_authorization_task=AION-154`,
  `stabilization_authorization_scope=disabled-production-auth-core-stabilization`,
  `stabilization_authorization_reusable=false`, and
  `stabilization_authorization_expires_on_aion_154_merge=true`.

Stabilization decisions:

- Schema versions are explicit and unknown versions fail closed.
- Canonical evidence uses deterministic UTF-8 JSON with sorted keys, compact
  separators, UTC datetime normalization, and unsupported-value rejection.
- Evidence fingerprints are SHA-256 hashes of canonical payloads with the
  fingerprint field excluded from its own hash.
- Reason codes live in an immutable central registry and unknown or duplicate
  codes fail closed.
- Internal operation strings are replaced with a typed preview taxonomy.
- Evidence models are frozen and metadata mappings are immutable.
- Idempotency is supported by injected clocks and ID factories.
- Concurrency tests cover status reads, policy decisions, reason-code
  immutability, metadata isolation, deterministic fingerprints, and runtime
  no-go state.
- The prohibited configuration matrix remains fail-closed.
- Redaction rejects protected material in nested dictionaries, lists, tuples,
  mixed-case keys, hyphenated keys, Unicode-normalized keys, metadata values,
  exception text, and source references.
- Diagnostics expose only schema versions, implementation state,
  runtime-disabled booleans, guard state, blocker counts, stable reason codes,
  authorization references, fingerprints, and redacted metadata.
- Kernel construction is stable and does not create shared mutable singleton
  state.
- Route absence remains mandatory.

## Runtime Boundary

`production_auth_runtime_enabled=false`, `runtime_no_go_status=true`,
`runtime_implementation_approved=false`, and
`runtime_enablement_guard_release_approved=false`.

No login, logout, callback, OAuth, OIDC, SAML, token, session, credential,
`/production-auth`, or `/auth/production` route is created.

## Dependency and Release Boundary

AION-154 adds no frontend dependencies, provider SDKs, package files, lockfiles,
migrations, SDK runtime resources, CLI runtime commands, v0.2 tag, or v0.2
release.
