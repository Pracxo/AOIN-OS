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
`AION-157-PA-0004` is the only active authorization, AION-158 scope is exact,
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
