# Production Auth Policy And Audit

The production-auth policy interface is deterministic and fail-closed. Every
policy evaluation returns `outcome=blocked` or `outcome=denied` with
`runtime_effect=false`.

Required reason codes:

- `production_auth_runtime_disabled`
- `runtime_enablement_guard_locked`
- `authorization_scope_implementation_only`
- `endpoint_surface_absent`
- `protected_material_storage_absent`
- `external_identity_provider_absent`

Audit and provenance records are redacted and traceable to
`authorization_transaction_id=AION-151-PA-0001`. They may describe status
reads, policy previews, guard checks, configuration validation, and no-go
findings only. They must not contain credentials, tokens, cookies, sessions,
raw identity claims, provider payloads, raw prompts, or hidden reasoning.
