# 0155: v0.2 Persistent Identity Assertion Replay Protection

## Context

AION-162 introduced offline Ed25519 identity assertion verification. AION-163-PA-0007 authorizes AION-164 to add persistent replay protection before any future request-authentication integration.

## Decision

Use a dedicated SQLAlchemy replay ledger with a domain-separated replay key derived from issuer plus assertion ID. The ledger persists only `replay_key`, `issuer_fingerprint`, `assertion_fingerprint`, `claimed_at`, `assertion_expires_at`, `retain_until`, and `created_at`.

The generic idempotency repository is rejected for this role because replay protection needs assertion-identity semantics, fingerprint collision detection, and a security-specific evidence contract. An in-memory runtime replay store is rejected because it cannot protect multiple workers, multiple processes, or restarts.

The repository uses one insert under a unique primary-key constraint as the primary claim algorithm. `IntegrityError` is handled by reading the existing row and comparing assertion fingerprints. Same fingerprint means replay. Different fingerprint means identifier collision. Missing schema, unavailable repository, malformed existing row, and duplicate-without-readable-row all fail closed.

No new dependency is added. No migration is added. `auto_create=true` exists only for tests; production schema provisioning remains a future blocker. Production schema auto-create remains prohibited.

## Role Comparison

The offline verifier proves cryptographic validity and redacted claim shape. The replay service proves one-time use of a verified assertion. The pipeline composes them for internal tests only and does not authenticate requests.

## Consequences

Replay evidence includes deterministic fingerprints, safe reason codes, audit events, provenance, and diagnostics. It excludes raw issuer, raw assertion ID, raw assertion, signature, subject, actor ID, workspace ID, roles, permissions, security scopes, metadata, database URL, SQL, and exception text.

Runtime integration remains prohibited: no KernelContainer registration, app-factory integration, middleware, API route, OpenAPI security scheme, SDK resource, CLI command, connector runtime, operator action, module activation, sandbox execution, startup hook, shutdown hook, scheduler, package file, lockfile, migration, v0.2 tag, or v0.2 release.

The AION-163 authorization expires when AION-164 merges. Formal lifecycle closeout belongs to AION-165.
