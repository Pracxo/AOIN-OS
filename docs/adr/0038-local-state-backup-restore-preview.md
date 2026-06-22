# 0038: Local State Backup, Restore Preview, and Data Portability

## Status

Accepted.

## Decision

AION Brain v0.1 adds a local, application-level backup and restore-preview
layer. Backups are exported as frontend- and vendor-agnostic AION contracts,
manifest JSON, checksum JSON, validation JSON, and resource JSONL files.

Restore preview analyzes backups and produces conflict-aware plans. Restore
apply is disabled by default and remains approval-gated before any future
application-level writer can apply records.

## Reason

AION needs a safe local portability format before release handoff and before
future modules create more state. Application-level export preserves AION
contracts, redaction, policy gates, and scope semantics in a way raw database
snapshots cannot.

## Consequences

Future local tools can validate and preview AION state without live Docker
dependencies. Future restore writers can be added behind AION-owned application
boundaries without changing backup contracts.

## Constraints

- No `pg_dump`.
- No direct database restore by default.
- No cloud upload.
- No external observability or storage calls.
- No raw secrets, raw headers, `.env` files, or generated caches.
- No domain-specific backup resources.
- Backup and restore APIs must use policy, autonomy, risk, and approval
  boundaries where applicable.
