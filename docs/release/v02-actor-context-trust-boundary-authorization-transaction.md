# v0.2 Actor Context Trust Boundary Authorization Transaction

Status: `approved`

## Purpose

AION-159 closes the consumed AION-157 request identity stabilization
authorization and creates `AION-159-PA-0005` as the single active
authorization for AION-160.

## Current Trust-Boundary Finding

The observed source behavior in
`services/brain-api/src/aion_brain/identity/dev_auth.py` is a
non-development identity-header trust fallback. When
`settings.env != "development"` or `settings.dev_auth_enabled == false`,
`actor_context_from_headers` still reads:

- `X-AION-Actor-ID`
- `X-AION-Workspace-ID`
- `X-AION-Roles`
- `X-AION-Permissions`
- `X-AION-Security-Scope`

Security consequence: unverified caller-controlled identity metadata can be
projected into `ActorContext` when development authentication is disabled.

This document does not describe an unverified exploit scenario. AION-159
changes no implementation source. AION-159 changes no implementation source
outside governance, evidence, documentation, validation, and static-console
artifacts. AION-160 performs the remediation.

## Authorization Transaction

- `authorization_transaction_id=AION-159-PA-0005`
- `approval_record_id=AION-159-PA-0005`
- `parent_authorization_transaction_id=AION-157-PA-0004`
- `candidate_id=production-auth-actor-context-trust-boundary`
- `workstream=production-auth-route-context-hardening`
- `implementation_task=AION-160`
- `authorization_scope=fail-closed-actor-context-resolution`

## AION-158 Closeout

`AION-157-PA-0004` is inactive, consumed by AION-158 PR 68, expired, and
non-reusable. The AION-158 feature commit is
`767fd9b228b00b04569df2e3b1b3f6bc9ecd846f`; the merge commit is
`f792c92e1d8a73ec8e7377b5d59269dea359006d`.

## Exact Remediation Scope

AION-160 may implement a fail-closed actor-context resolver, preferably
`ProductionAuthActorContextResolver` in
`services/brain-api/src/aion_brain/production_auth/actor_context.py`.

It may refactor `identity/dev_auth.py` so development headers are read only
when `settings.env == "development"` and
`settings.dev_auth_enabled == true`.

Outside that explicit development gate, identity-bearing `X-AION` headers must
be ignored and an anonymous zero-permission `ActorContext` returned:
`actor_id=null`, `actor_type=null`, `workspace_id=null`, `roles=[]`,
`permissions=[]`, `security_scope=[]`, and `dev_mode=false`.

`RequestIdentityContext` is the primary identity-evidence source. In the
current disabled state it remains unauthenticated, anonymous, and grants zero
roles, permissions, or security scope. Safe `trace_id` and `correlation_id`
projection comes from `RequestContext`, not actor headers when RequestContext
exists.

## Allowed Future Paths

- `services/brain-api/src/aion_brain/identity/dev_auth.py`
- `services/brain-api/src/aion_brain/contracts/scopes.py`
- `services/brain-api/src/aion_brain/contracts/actor_context_resolution.py`
- `services/brain-api/src/aion_brain/production_auth/actor_context.py`
- `services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py`
- `services/brain-api/src/aion_brain/production_auth/__init__.py`
- `services/brain-api/src/aion_brain/config.py`
- `services/brain-api/src/aion_brain/kernel/container.py`
- `services/brain-api/src/aion_brain/kernel/diagnostics.py`
- focused tests, docs, examples, static-console evidence, and scripts

Route files may change only to replace direct legacy dependency access with a
compatible hardened dependency. Route paths and request/response contracts must
not change.

## Prohibited Scope

Real identity verification, authenticated requests, production actor headers,
role headers, permission headers, security-scope headers, Authorization or
Cookie parsing, credentials, passwords, tokens, sessions, providers, external
calls, auth endpoints, OpenAPI security, packages, lockfiles, migrations,
SDK/CLI runtime surfaces, connector runtime, operator writes, module
activation, sandbox execution, runtime guard release, v0.2 tags, and v0.2
releases remain prohibited.

## Runtime Guard

`runtime_guard_hold_active=true`, `runtime_no_go_status=true`,
`runtime_implementation_approved=false`,
`production_auth_runtime_enabled=false`,
`identity_verification_enabled=false`, and
`authenticated_requests_enabled=false`.

## Review, Expiry, and Revocation

Required reviewers are security, runtime governance, platform, and audit.
This authorization expires when AION-160 merges or when
`AION-159-PA-0005` is explicitly revoked. Revocation must preserve runtime
guards and must not reactivate historical authorizations.

## No-Go Conditions

The no-go gate rejects historical reactivation, a second active authorization,
unknown approved authorization records, scope widening, implementation-source
changes in AION-159, runtime authentication, protected material, provider or
network work, packages, migrations, tags, and releases.

## AION-161 Lifecycle Update

After AION-160 PR 70 merged, `AION-159-PA-0005` became historical: inactive,
consumed, expired, and non-reusable. AION-161 creates `AION-161-PA-0006` as the
sole active authorization for AION-162 offline Ed25519 identity assertion
verification. The AION-159 approval values remain historical evidence and are
not rewritten to false.
