# v0.2 Offline Identity Assertion Verification Authorization Transaction

Task: AION-161

## Purpose

AION-161 closes the consumed actor-context remediation authorization and authorizes AION-162 to implement a narrow offline Ed25519 signed identity assertion verification core.

## Role Comparison

`ProductionAuthActorContextResolver` resolves ActorContext fail closed, ignores non-development identity headers, gives disabled RequestIdentityContext precedence, projects trace and correlation from RequestContext, grants zero roles, permissions, and scopes outside development simulation, and performs no cryptographic verification.

`RequestIdentityVerifier` remains provider-agnostic and disabled. It receives correlation-only input, returns anonymous disabled identity evidence, performs no I/O, and authenticates nobody.

AION-162 may add an offline verification core only. A valid cryptographic assertion is not a request authentication result and must not populate ActorContext or RequestIdentityContext.

## Alternatives

HMAC/shared-secret verification is rejected because it requires secret distribution, secret rotation, protected-material handling, and a larger blast radius.

JWT/OIDC/JWKS integration is deferred because it combines HTTP parsing, algorithm selection, key discovery, provider trust, token semantics, and runtime request authentication.

The selected approach is offline Ed25519 identity assertion verification: public-key-only runtime trust, fixed algorithm, no provider network, no runtime signing key, no session, no token issuance, and deterministic negative testing.

## Transaction

- `authorization_transaction_id=AION-161-PA-0006`
- `approval_record_id=AION-161-PA-0006`
- `parent_authorization_transaction_id=AION-159-PA-0005`
- `candidate_id=production-auth-offline-identity-assertion-verification`
- `workstream=production-auth-verification-core`
- `implementation_task=AION-162`
- `authorization_scope=offline-ed25519-identity-assertion-verification`
- `authorization_active=true`
- `authorization_consumed=false`
- `authorization_expired=false`
- `authorization_reusable=false`

## Dependency Authorization

- `approved_dependency_name=cryptography`
- `approved_dependency_specifier=>=49.0.0,<50.0.0`
- `approved_dependency_manifest=services/brain-api/pyproject.toml`
- `approved_dependency_change_count=1`

AION-161 does not add this dependency. It authorizes AION-162 to make exactly one existing manifest change.

## Exact Source Paths

- `services/brain-api/src/aion_brain/contracts/identity_assertion.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py`
- `services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py`
- `services/brain-api/src/aion_brain/production_auth/__init__.py`
- `services/brain-api/pyproject.toml`
- `services/brain-api/tests/`
- `docs/`
- `examples/`
- `operator-console-static/`
- `scripts/`

## Assertion Format

Envelope fields: `schema_version`, `key_id`, `payload`, `signature`.

Payload fields: `assertion_id`, `issuer`, `audience`, `subject`, `actor_id`, `workspace_id`, `roles`, `permissions`, `security_scope`, `issued_at`, `not_before`, `expires_at`, `metadata`.

Contracts must use Pydantic v2, `extra="forbid"`, frozen evidence where applicable, and `hide_input_in_errors=true`.

## Cryptographic Contract

- Fixed algorithm: Ed25519 only
- No algorithm negotiation
- Signature input: `b"AION-IDENTITY-ASSERTION-V1\\0" + canonical_json_bytes(payload)`
- Canonical JSON reuse is required
- Trusted public keys are raw 32-byte Ed25519 public keys encoded as base64url without padding
- Key IDs must match exactly, with no case folding, path characters, whitespace, or Unicode confusables
- Key rotation may use multiple exact key IDs with activation, retirement, and revocation state
- Unknown, revoked, inactive, or expired keys fail closed

## Validation Contract

- Exact issuer validation
- Exact audience validation
- UTC temporal validation for `issued_at`, `not_before`, and `expires_at`
- Maximum assertion lifetime: 300 seconds
- Allowed clock skew: 30 seconds
- Required assertion identifier validation
- Strict claim limits for subject, actor, workspace, roles, permissions, security scope, metadata, and canonical payload size
- Duplicate roles, permissions, and scopes are rejected

## Runtime Integration Prohibition

- `request_authentication_approved=false`
- `actor_context_application_approved=false`
- `request_identity_context_application_approved=false`
- `runtime_effect_approved=false`
- `identity_assertion_header_parsing_approved=false`
- `authorization_header_parsing_approved=false`
- `cookie_parsing_approved=false`
- `identity_assertion_middleware_registration_approved=false`
- `request_identity_verifier_replacement_approved=false`
- `actor_context_resolver_integration_approved=false`

## Private-Key And Replay Boundary

Runtime private keys, private-key configuration, persistence, and serialization are prohibited. Test-only signing keys may be generated in memory, used only inside tests, and never committed, serialized, logged, exported by runtime packages, or placed in examples.

AION-162 may validate assertion ID shape but may not claim replay protection. `replay_check_performed=false` and `replay_protection_required_before_request_integration=true` remain mandatory.

## Evidence Boundary

Audit and provenance may include verification ID, assertion fingerprint, key ID, issuer, audience, validation outcome, reason codes, claim counts, timestamps, and `runtime_effect=false`.

Audit and provenance must not include raw assertions, signatures, full public keys, subject, actor ID, workspace ID, roles, permissions, security scopes, metadata values, signing material, or exception text.

## Required Reviewers And Gates

Required reviewers: security reviewer, runtime governance reviewer, cryptography reviewer, platform reviewer.

Required gates:

- `./scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh`
- `./scripts/v02-offline-identity-assertion-verification-authorization-check.sh`
- inherited actor-context and request-identity gates
- docs, final docs audit, no-domain-drift, boundary, typecheck, lint, and repository check

## Expiry And Revocation

`AION-161-PA-0006` expires when AION-162 merges or when explicitly revoked. No other active approved authorization may exist.

## AION-161 Source Statement

AION-161 changes no production-auth implementation source, no request or actor-context implementation source, no API routes, no package manifest, and no dependency manifest. No v0.2 tag or release is created.
