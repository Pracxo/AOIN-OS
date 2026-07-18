# AION OS Project Status

## Current Release Baseline

The frozen release baseline remains `AION Brain v0.1.0` at the immutable
`aion-v0.1.0` tag. The repository is now carrying v0.2 work in progress, but no
v0.2 tag or release exists.

## Current Main Milestone

The current main milestone is v0.2 offline identity assertion verification core implementation.
AION-158 implemented and merged the pure ASGI disabled request identity
stabilization. AION-159 closed `AION-157-PA-0004` and created
`AION-159-PA-0005` for AION-160. AION-160 merged the fail-closed actor-context
trust-boundary remediation.

Current milestone: AION-162 offline Ed25519 identity assertion verification core implemented and post-merge verification corrected.
Current implementation state:

- fixed Ed25519 verification
- public-key-only trust
- canonical domain-separated payloads
- strict key, issuer, audience, time, and claim validation
- safe verification evidence
- request integration absent
- replay protection absent
- production authentication disabled

Current authorization: AION-163-PA-0007 active for AION-164.
AION-161-PA-0006 consumed by AION-162 when merged.
Formal lifecycle closeout: AION-163 complete on this branch.

Prior actor-context closeout remains in force: non-development identity headers ignored,
anonymous zero-permission ActorContext, RequestIdentityContext precedence,
RequestContext trace/correlation projection, development simulation isolated, and
production authentication disabled.
Historical AION-160 marker: Next implementation task: AION-162 offline Ed25519 identity assertion verification core.

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
- Fail-closed ActorContext resolution: non-development identity-header
  rejection, anonymous zero-permission fallback, RequestIdentityContext
  precedence, RequestContext trace/correlation projection, and development
  identity simulation isolation.
- Offline Ed25519 identity assertion verification core: strict assertion
  contracts, public-key registry, canonical domain-separated signing input,
  fixed Ed25519 signature verification, redacted evidence, concurrency tests,
  replay-boundary tests, and runtime/no-go gates.

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

`AION-159-PA-0005` is historical, consumed by AION-160 PR 70, expired,
inactive, and non-reusable under
`authorization_scope=fail-closed-actor-context-resolution`.

`AION-161-PA-0006` is consumed by AION-162 when merged under
`authorization_scope=offline-ed25519-identity-assertion-verification`.
`authorization_reusable=false`; formal lifecycle closeout is deferred to
AION-163.

`AION-153-PA-0002` is historical, consumed by AION-154 PR 64, expired, inactive,
and non-reusable. `AION-151-PA-0001` remains historical evidence consumed by
AION-152.

## Current Test Posture

The repository has focused gates for the production-auth authorization lineage,
the disabled production-auth core, AION-154 stabilization, AION-155 request
boundary authorization, AION-157 request identity stabilization authorization,
and AION-159 actor-context trust-boundary authorization. AION-160 adds
fail-closed actor-context remediation gates, privilege-escalation regressions,
route regressions, concurrency coverage, redaction coverage, and runtime-hold
checks. These gates are local, deterministic, and do not enable runtime
authentication.

## Current Release Posture

`v02_release_ready=false`
`v02_tag_created=false`
`v02_release_created=false`

The v0.2 release remains blocked until formal AION-161 authorization closeout,
persistent identity-assertion replay protection, replay-ledger production schema provisioning, request-level verified identity integration, operational
public-key provisioning and rotation evidence, external provider integration,
protected-material, credential, token, session,
deployment, rollback, observability, threat-model, release-candidate, runtime
guard release decision, tag, and release authorization work is complete.

## Current Implementation Task

AION-164 is the next implementation task: persistent identity-assertion replay-protection core. AION-162 implements the offline Ed25519 identity assertion verification core
authorized by AION-161. It adds exactly `cryptography>=49.0.0,<50.0.0`,
strict offline verification, public verification keys, canonical payloads,
domain separation, issuer/audience/time/assertion-ID validation, claim
constraints, audit/provenance evidence, deterministic negative fixtures, and
test-only ephemeral signing keys. Request authentication, ActorContext
application, RequestIdentityContext application, runtime private keys, provider
networking, replay cache, endpoints, package manifests, lockfiles, migrations,
SDK/CLI runtime surfaces, and v0.2 release actions remain blocked.

## Implemented Code Versus Enabled Runtime

Implemented code can exist while runtime behavior remains disabled. The
production-auth core is implemented internally and disabled. The request
identity boundary is implemented internally, observe-only, and disabled by
default. No user is authenticated, no headers or cookies are parsed, no
credentials or tokens are verified or stored, no sessions are created, no
providers are contacted, and no production-auth or request-identity API route
exists.

The actor-context trust-boundary finding was documented by AION-159 as a
non-development identity-header trust fallback. AION-160 implemented the
fail-closed remediation. AION-161 closes `AION-159-PA-0005` and creates
`AION-161-PA-0006` for the next offline verification core.


## AION-163 Authorization State

AION-163 closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable after AION-162 PR #72 and corrective PR #73. `AION-163-PA-0007` is the sole active production-auth authorization for AION-164 under `authorization_scope=persistent-identity-assertion-replay-protection-core`.

AION-164 is authorized to implement a persistent SQLAlchemy replay ledger, domain-separated issuer/assertion-ID replay key, atomic unique-insert claim, assertion-fingerprint collision detection, fail-closed repository behavior, retention policy, explicit cleanup, internal verification pipeline, redacted replay evidence, test-only schema auto-create, and performance smoke coverage. Dependency changes, migrations, production schema auto-create, runtime in-memory replay stores, background cleanup schedulers, HTTP parsing, request authentication, middleware integration, ActorContext and RequestIdentityContext application, providers, endpoints, SDK/CLI runtime surfaces, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
## AION-164 Persistent Identity Assertion Replay Protection

Current state: AION-164 replay protection is implemented and unintegrated. AION-163-PA-0007 remains the canonical authorization record until AION-165 lifecycle closeout. Runtime authentication, request identity context application, ActorContext application, API routes, middleware, SDK/CLI surfaces, migrations, v0.2 tags, and releases remain disabled or absent.
