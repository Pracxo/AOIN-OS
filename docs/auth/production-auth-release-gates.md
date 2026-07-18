# Production Auth Release Gates

Production auth runtime cannot be enabled until every gate below is satisfied.
AION-098 adds no runtime implementation and keeps `production_auth_enabled`
false.

AION-099 does not satisfy or bypass these gates. It adds disabled status,
mock-claims preview, and audit proof only; production auth remains disabled.

| Gate | Required Evidence | Blocker Behavior |
| --- | --- | --- |
| threat model approved | reviewed `docs/auth/production-auth-threat-model.md` | block runtime auth |
| provider selected | approved provider decision and fallback posture | block provider integration |
| token/session storage design approved | approved storage decision and migration plan | block token/session storage |
| CSRF/CORS plan approved | browser/API protection review | block cookie or browser auth flow |
| audit correlation tested | provider subject to ActorContext to policy to trace test | block release |
| role mapping tested | group/claim mapping and fail-closed tests | block operator access |
| revocation tested | provider and local revocation proof | block release |
| disabled-by-default prototype green | AION-099 mock-only prototype checks | block runtime enablement |
| security review complete | signed review record | block release |
| no secret leakage | examples, logs, telemetry, docs, and audit scans | block release |
| rollback plan | documented disablement and recovery path | block release |

No gate can be waived by the Operator Console, local auth simulation,
ActorContext headers, reverse proxy headers, policy shortcuts, or action
authorization decisions.
## AION-154 Stabilization Gates

AION-154 adds:

```bash
./scripts/production-auth-core-stabilization-no-go-regression.sh
./scripts/production-auth-core-stabilization-check.sh
./scripts/production-auth-core-stabilization-runtime-hold.sh
```

These gates validate canonical evidence, fingerprints, reason codes,
immutability, idempotency, concurrency, redaction, diagnostics, kernel
stability, route absence, inherited production-auth authorization checks, and
runtime/release no-go state.

## AION-155 Request Boundary Authorization Gates

AION-155 adds:

```bash
./scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh
./scripts/v02-production-auth-request-boundary-authorization-check.sh
```

The gates verify AION-153 is historical, `AION-155-PA-0003` is the only active
authorization, the AION-156 scope is exact, and runtime authentication,
protected-material handling, provider integration, package files, migrations,
SDK/CLI runtime surfaces, v0.2 tags, and v0.2 releases remain blocked.
# AION-156 Gate Addition

AION-156 adds:

- `scripts/production-auth-request-identity-no-go-regression.sh`
- `scripts/production-auth-request-identity-check.sh`
- `scripts/production-auth-request-identity-runtime-hold.sh`

These gates keep the request identity boundary implemented-disabled,
default-off, anonymous, route-free, provider-free, package-free, migration-free,
and v0.2-release-free.

## AION-157 Request Identity Stabilization Authorization Gates

AION-157 adds:

```bash
./scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh
./scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh
```

These gates verify `AION-155-PA-0003` is historical consumed evidence,
`AION-157-PA-0004` is historical and `AION-159-PA-0005` is the only active authorization, AION-160 scope is exact,
runtime authentication remains disabled, implementation source remains
unchanged in AION-157, and v0.2 tag or release creation remains absent.

## AION-158 Request Identity Stabilization Gates

AION-158 adds:

```bash
./scripts/production-auth-request-identity-stabilization-no-go-regression.sh
./scripts/production-auth-request-identity-stabilization-check.sh
./scripts/production-auth-request-identity-stabilization-runtime-hold.sh
```

These gates verify the request identity middleware remains pure ASGI,
receive/send passthrough and non-HTTP bypass are preserved, forged state is
replaced, duplicate registration is rejected, runtime authentication remains
disabled, public auth routes and OpenAPI security remain absent, and package
files, lockfiles, migrations, SDK/CLI runtime surfaces, v0.2 tags, and v0.2
releases remain absent.

## Actor Context Trust Boundary Authorization Gate

```bash
./scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh
./scripts/v02-actor-context-trust-boundary-authorization-check.sh
```

These gates verify that AION-157 is historical, `AION-159-PA-0005` is the only
active authorization, the current non-development identity-header trust
fallback is documented, AION-160 scope is fail-closed actor-context
resolution, implementation source is unchanged in AION-159, runtime
authentication remains disabled, and v0.2 tags and releases remain absent.

## AION-161 Offline Verification Authorization Gates

The AION-161 gates verify `AION-159-PA-0005` is historical and consumed by
AION-160 PR 70, `AION-161-PA-0006` is the only active authorization, the
AION-162 scope is offline Ed25519 identity assertion verification, the approved
dependency is exactly `cryptography>=49.0.0,<50.0.0`, and runtime
authentication, HTTP parsing, ActorContext application, RequestIdentityContext
application, runtime private keys, provider networking, replay cache, packages,
lockfiles, migrations, SDK/CLI runtime surfaces, v0.2 tags, and v0.2 releases
remain blocked.
## AION-162 Gates

AION-162 adds these gates:

- `scripts/production-auth-offline-identity-assertion-no-go-regression.sh`
- `scripts/production-auth-offline-identity-assertion-check.sh`
- `scripts/production-auth-offline-identity-assertion-runtime-hold.sh`

The gates verify the exact `cryptography>=49.0.0,<50.0.0` dependency,
fixed Ed25519 behavior, strict base64url handling, canonical payload reuse,
public-key-only registry behavior, no runtime private-key source, no HTTP
parsing, no request authentication, no ActorContext or RequestIdentityContext
application, no routes, no OpenAPI security, no SDK/CLI runtime surface, no
lockfiles, no migrations, and no v0.2 tag or release.


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
