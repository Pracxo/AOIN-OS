# AION OS Project Status

## Current Release Baseline

The frozen release baseline remains `AION Brain v0.1.0` at the immutable
`aion-v0.1.0` tag. The repository is now carrying v0.2 work in progress, but no
v0.2 tag or release exists.

## Current Main Milestone

The current main milestone is v0.2 request identity stabilization closeout and
actor-context trust-boundary authorization. AION-158 implemented and merged the
pure ASGI disabled request identity stabilization. AION-159 closes
`AION-157-PA-0004` and creates `AION-159-PA-0005` as the active authorization
for AION-160.

Current milestone: AION-158 request-identity stabilization merged.
Current authorization: AION-159-PA-0005 active for AION-160.
Next task: AION-160 actor-context trust-boundary remediation.

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
`authorization_consumed_by_task=AION-156`, `authorization_active=false`,
`authorization_expired=true`, and `authorization_reusable=false`.

`AION-157-PA-0004` is consumed by AION-158 PR 68 under
`authorization_scope=disabled-request-identity-boundary-stabilization`.
`authorization_active=false`, `authorization_consumed=true`,
`authorization_expired=true`, and `authorization_reusable=false`.

`AION-159-PA-0005` is active for AION-160 under
`authorization_scope=fail-closed-actor-context-resolution`.

`AION-153-PA-0002` is historical, consumed by AION-154 PR 64, expired, inactive,
and non-reusable. `AION-151-PA-0001` remains historical evidence consumed by
AION-152.

## Current Test Posture

The repository has focused gates for the production-auth authorization lineage,
the disabled production-auth core, AION-154 stabilization, AION-155 request
boundary authorization, AION-157 request identity stabilization authorization,
and AION-159 actor-context trust-boundary authorization. These gates are local,
deterministic, and do not enable runtime authentication.

## Current Release Posture

`v02_release_ready=false`
`v02_tag_created=false`
`v02_release_created=false`

The v0.2 release remains blocked until actor-context trust-boundary
remediation, real identity verification, external provider integration,
protected-material, credential, token, session, deployment, rollback,
observability, threat-model, release-candidate, tag, and release authorization
work is complete.

## Current Implementation Task

AION-160 is authorized to remediate the actor-context trust boundary by
removing non-development trust in identity-bearing `X-AION` headers, isolating
development simulation behind the explicit development gate, preserving
RequestIdentityContext precedence, preserving RequestContext correlation, and
returning anonymous zero-permission ActorContext outside development
simulation. Real identity verification, external provider integration,
protected material lifecycle, and runtime guard release remain blocked.

## Implemented Code Versus Enabled Runtime

Implemented code can exist while runtime behavior remains disabled. The
production-auth core is implemented internally and disabled. The request
identity boundary is implemented internally, observe-only, and disabled by
default. No user is authenticated, no headers or cookies are parsed, no
credentials or tokens are verified or stored, no sessions are created, no
providers are contacted, and no production-auth or request-identity API route
exists.

The current actor-context trust-boundary finding is documented as a
non-development identity-header trust fallback. AION-159 does not alter source
implementation; AION-160 owns the fail-closed remediation.
