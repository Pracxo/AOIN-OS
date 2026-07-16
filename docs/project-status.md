# AION OS Project Status

## Current Release Baseline

The frozen release baseline remains `AION Brain v0.1.0` at the immutable
`aion-v0.1.0` tag. The repository is now carrying v0.2 work in progress, but no
v0.2 tag or release exists.

## Current Main Milestone

The current main milestone is v0.2 disabled production-auth request identity
boundary implementation. AION-156 consumes `AION-155-PA-0003` and implements
the request identity boundary as observe-only and disabled.

## Implemented Subsystems

- AION Brain v0.1 kernel, contract, policy, audit, and local verification
  baseline.
- Connector, operator, planning, and approval governance evidence tracks.
- Internal disabled production-auth core with AION-154 stabilization evidence:
  canonical serialization, SHA-256 fingerprints, reason-code registry,
  evidence immutability, idempotency, concurrency, redaction, diagnostic,
  kernel, route-absence, and performance-smoke coverage.
- Disabled request identity boundary under `aion_brain.production_auth`:
  strict contracts, provider-agnostic verifier protocol, disabled verifier,
  deterministic disabled test verifier, anonymous request-state attachment,
  audit/provenance correlation, diagnostics, middleware ordering coverage, and
  runtime/no-go gates.

## Disabled Subsystems

- Production authentication runtime remains disabled.
- Identity verification and authenticated requests remain disabled.
- External connectors remain disabled.
- Operator write execution remains disabled.
- Module activation remains disabled.
- Sandbox execution remains disabled.

## Current Authorization Transaction

`AION-155-PA-0003` is consumed by `AION-156` under
`authorization_scope=disabled-request-identity-boundary`.
`authorization_consumed_by_task=AION-156` and `authorization_reusable=false`.

`AION-153-PA-0002` is historical, consumed by AION-154 PR 64, expired, inactive,
and non-reusable. `AION-151-PA-0001` remains historical evidence consumed by
AION-152.

## Current Test Posture

The repository has focused gates for the production-auth authorization lineage,
the disabled production-auth core, AION-154 stabilization, and AION-155 request
boundary authorization. These gates are local, deterministic, and do not enable
runtime authentication.

## Current Release Posture

`v02_release_ready=false`
`v02_tag_created=false`
`v02_release_created=false`

The v0.2 release remains blocked until request identity, verification,
protected-material, credential, token, session, deployment, rollback,
observability, threat-model, release-candidate, tag, and release authorization
work is complete.

## Next Implementation Task

The next critical-path task is formal lifecycle closeout after the AION-156
merge. Real identity verification, external provider integration, protected
material lifecycle, and runtime guard release remain blocked.

## Implemented Code Versus Enabled Runtime

Implemented code can exist while runtime behavior remains disabled. The
production-auth core is implemented internally and disabled. The request
identity boundary is implemented internally, observe-only, and disabled by
default. No user is authenticated, no headers or cookies are parsed, no
credentials or tokens are verified or stored, no sessions are created, no
providers are contacted, and no production-auth or request-identity API route
exists.
