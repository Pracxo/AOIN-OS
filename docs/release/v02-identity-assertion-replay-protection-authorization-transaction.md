
# v0.2 Identity Assertion Replay Protection Authorization Transaction

Task: AION-163

## Purpose

AION-163 records the AION-162 closeout and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. AION-163 changes no implementation source, creates no schema or migration, changes no dependency manifest, enables no runtime integration, and creates no v0.2 tag or release.

## AION-162 Closeout

`AION-161-PA-0006` is historical after AION-162 implementation PR #72 and corrective PR #73. The final verified main commit is `d8a1705028796fb35ffb214e7f56d571e7c66025`. Offline Ed25519 verification, public-key registry, positive and negative cryptographic results, exact dependency, runtime private-key absence, request integration absence, and replay absence are verified.

## Role Comparison

`OfflineEd25519IdentityAssertionVerifier` performs offline signature, key, issuer, audience, time, assertion ID, and claim validation. It authenticates no request, applies no ActorContext or RequestIdentityContext, performs no replay check, and stores no state.

A process-local in-memory set is rejected for runtime replay protection because it is lost on restart and cannot provide cross-worker durable uniqueness. The generic idempotency repository is rejected because it stores route and response semantics, uses a different lifecycle, and does not provide an atomic identity-assertion replay claim. A dedicated SQLAlchemy-backed replay ledger with an atomic unique insert is selected.

## Transaction

- `authorization_transaction_id=AION-163-PA-0007`
- `approval_record_id=AION-163-PA-0007`
- `parent_authorization_transaction_id=AION-161-PA-0006`
- `candidate_id=production-auth-identity-assertion-replay-protection`
- `workstream=production-auth-verification-integrity`
- `implementation_task=AION-164`
- `authorization_scope=persistent-identity-assertion-replay-protection-core`
- `authorization_active=true`
- `authorization_consumed=false`
- `authorization_expired=false`
- `authorization_reusable=false`

## Exact Source Paths

AION-164 may create:

- `services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py`
- `services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py`

AION-164 may update tests, docs, examples, operator-console static data, scripts, and `services/brain-api/src/aion_brain/production_auth/__init__.py` only. It must not modify verifier, key registry, request middleware, request boundary, actor-context, config, kernel, API, idempotency, SDK/CLI, pyproject, package, lockfile, or migration paths.

## Replay Key Derivation

- `REPLAY_KEY_SCHEMA_VERSION=identity-assertion-replay-key/v1`
- `REPLAY_KEY_DOMAIN_SEPARATOR=b"AION-IDENTITY-ASSERTION-REPLAY-V1\0"`
- replay identity input: issuer and assertion ID only
- derivation: `sha256(domain_separator + canonical_json_bytes({schema_version, issuer, assertion_id})).hexdigest()`
- persist only the derived replay key
- do not persist raw issuer or raw assertion ID
- do not reuse assertion fingerprint as the replay key

The same issuer and assertion ID must collide even if payload or signature changes. Different issuers may reuse the same assertion ID independently.

## Persistence Model

AION-164 must use `aion_identity_assertion_replay_claims` with primary key `replay_key`, hashed issuer/assertion fingerprints, UTC timestamps, and indexes on retain-until, claimed-at, and assertion-expires-at. Production schema auto-create is prohibited; test-only schema auto-create is authorized. No migration is authorized.

## Atomic Claim Semantics

`claim(record)` must perform a single insert relying on the unique constraint. Duplicate replay key with the same assertion fingerprint reports replay detected. Duplicate replay key with a different assertion fingerprint reports identifier collision. Repository or schema failure fails closed without database exception text.

## Retention And Cleanup

Default minimum retention is 86400 seconds, maximum retention is 604800 seconds, and cleanup batch size is 1000. Records are removed only through explicit `purge_expired(now, limit)`. Background cleanup, request-triggered bulk cleanup, and runtime schedulers remain prohibited.

## Internal Pipeline And Evidence

AION-164 may add an explicitly constructed internal `OfflineIdentityAssertionVerificationPipeline` that calls offline verification before replay protection. It must not be registered in KernelContainer, middleware, or routes. Evidence may include replay key, issuer fingerprint, assertion fingerprint, outcome booleans, retain-until timestamp, fixed reason codes, redaction status, and `runtime_effect=false`; it must not include raw assertion, signature, raw issuer, raw assertion ID, claims, roles, permissions, key bytes, SQL, or exception text.

## Required Reviewers And Gates

Required reviewers: security reviewer, persistence reviewer, database concurrency reviewer, cryptography reviewer, runtime governance reviewer, and platform reviewer.

Required gates: `./scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh`, `./scripts/v02-identity-assertion-replay-protection-authorization-check.sh`, inherited offline identity assertion gates, docs, final docs audit, no-domain-drift, boundary, typecheck, lint, and repository check.

## Expiry And Revocation

`AION-163-PA-0007` expires when AION-164 merges or when explicitly revoked. No other active approved authorization may exist.
