# v0.2 Production Auth Request Boundary Scope

Status: `authorized-for-future-implementation`

## AION-156 May Implement

1. Request identity contracts.
2. A provider-agnostic internal verifier protocol.
3. A disabled verifier implementation that always returns an unauthenticated,
   disabled, no-runtime-effect result.
4. A deterministic local test verifier used only by tests or an explicit
   non-production test harness.
5. A request-identity boundary component that can attach an anonymous,
   disabled identity context to request state.
6. Disabled-by-default app-factory integration.
7. Request ID, trace ID, audit, and provenance correlation.
8. Read-only diagnostics and health evidence.
9. Unit, integration, concurrency, redaction, and route-absence tests.
10. Documentation and static-console read-only evidence.

## Authorized Future Paths

- `services/brain-api/src/aion_brain/contracts/request_identity.py`
- `services/brain-api/src/aion_brain/production_auth/request_boundary.py`
- `services/brain-api/src/aion_brain/production_auth/verifier.py`
- `services/brain-api/src/aion_brain/production_auth/request_middleware.py`
- `services/brain-api/src/aion_brain/config.py`
- `services/brain-api/src/aion_brain/kernel/app_factory.py`
- `services/brain-api/src/aion_brain/kernel/container.py`
- `services/brain-api/src/aion_brain/kernel/diagnostics.py`
- `services/brain-api/tests/`
- `docs/`
- `examples/`
- `operator-console-static/`
- `scripts/`

## Setting Boundary

AION-156 may add `AION_PRODUCTION_AUTH_REQUEST_BOUNDARY_ENABLED` with default
false. The setting must not contain a secret value. A true value remains
prohibited unless the exact AION-156 implementation contract defines
observe-only disabled behavior.

## Permitted Request-State Result

- `authentication_state=disabled`
- `authenticated=false`
- `actor_id=null`
- `subject=null`
- `roles=[]`
- `runtime_effect=false`

## Must Not Implement

AION-156 must not authenticate a user, parse Authorization headers, parse
cookies, verify credentials, verify passwords, parse tokens, issue tokens,
refresh tokens, store tokens, create sessions, persist sessions, issue cookies,
persist cookies, contact an identity provider, add OAuth/OIDC/SAML runtime, call
external services, add provider SDKs, create login/logout/callback/token/session
or credential endpoints, add migrations, add package or lockfiles, add SDK or
CLI runtime surfaces, enable connector runtime, enable operator writes, enable
module activation, enable sandbox execution, or create a v0.2 tag or release.
# AION-156 Scope Update

The authorized scope is now implemented by AION-156 as
`authorization_scope=disabled-request-identity-boundary`. The boundary is
observe-only and disabled by default. Identity verification, authenticated
requests, provider integration, protected-material lifecycle, runtime routes,
SDK/CLI runtime surfaces, migrations, package files, v0.2 tags, and v0.2
releases remain outside the scope.
