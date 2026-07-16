# v0.2 Production Auth Request Identity Stabilization Scope

Status: `authorized-for-AION-158`

## Allowed AION-158 Work

- Pure ASGI migration for `ProductionAuthRequestIdentityMiddleware`.
- Preserve the existing class name or provide a documented compatibility alias.
- Preserve RequestContextMiddleware ownership of request IDs, trace IDs,
  correlation IDs, API request audit, telemetry, and performance sampling.
- Prove effective middleware execution order.
- Preserve streaming responses without buffering.
- Preserve request bodies without reading or replacing them.
- Propagate `asyncio.CancelledError`.
- Handle client disconnects without creating identity state.
- Bypass websocket, lifespan, and unknown future ASGI scopes.
- Reject or safely replace forged identity state.
- Prevent duplicate middleware registration.
- Preserve anonymous disabled identity:
  `authentication_state=disabled`, `authenticated=false`, `actor_id=null`,
  `subject=null`, `roles=[]`, `runtime_effect=false`.
- Preserve provider-agnostic disabled verifier behavior.
- Harden request-state isolation, concurrency, reentrancy, evidence
  idempotency, diagnostics, and dependency-free performance smoke tests.
- Add documentation and read-only static-console evidence.

Pure ASGI middleware is preferred because it makes ASGI scope handling explicit,
preserves streaming and cancellation behavior, avoids extra BaseHTTPMiddleware
abstraction risk, gives clear non-HTTP bypass behavior, and makes receive/send
invariants easier to test.

## Authorized Future Source Paths

- `services/brain-api/src/aion_brain/contracts/request_identity.py`
- `services/brain-api/src/aion_brain/production_auth/verifier.py`
- `services/brain-api/src/aion_brain/production_auth/request_boundary.py`
- `services/brain-api/src/aion_brain/production_auth/request_middleware.py`
- `services/brain-api/src/aion_brain/production_auth/request_evidence.py`
- `services/brain-api/src/aion_brain/production_auth/__init__.py`
- `services/brain-api/src/aion_brain/config.py`
- `services/brain-api/src/aion_brain/kernel/app_factory.py`
- `services/brain-api/src/aion_brain/kernel/container.py`
- `services/brain-api/src/aion_brain/kernel/diagnostics.py`
- `services/brain-api/tests/`
- `docs/`
- `examples/`
- `operator-console-static/`
- `scripts/`

## Prohibited

AION-158 must not authenticate users, trust `X-AION-Actor-ID`, parse
authorization headers, parse authorization-token material, parse cookies, verify credentials
or passwords, hash passwords, issue or store tokens, create or persist sessions,
issue or persist cookies, contact identity providers, add OAuth/OIDC/SAML
runtime, add network clients, add provider SDKs, add auth API routes, add
OpenAPI security schemes, add migrations, package files, lockfiles, SDK
runtime resources, CLI runtime commands, connector runtime, operator writes,
module activation, sandbox execution, runtime guard release, or v0.2 tags or
releases.

AION-158 implements this scope as disabled stabilization only. The AION-157
authorization expiry condition is satisfied by the AION-158 merge; formal
closeout is deferred to AION-159.
