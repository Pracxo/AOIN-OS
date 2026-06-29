# 0097: External Connector Boundary Design

## Status

Accepted.

## Context

AION has metadata-only connector registry boundaries, model provider hardening,
prompt egress preview, disabled auth runtime, local auth/session preview,
module activation design review, operator platform freeze gates, static console
release gates, and dry-run action authorization. None of these allow external
connector runtime calls.

External connectors are untrusted integration boundaries. AION needs connector
safety architecture before any integration work can begin.

## Decision

Add external connector boundary design.

No connector runtime is implemented in AION-106.

Connectors are untrusted by default.

External calls remain disabled.

Credentials and tokens remain absent.

Future connector work must pass connector boundary and no-go regression gates.

## Reason

AION needs connector safety architecture before integration work. The boundary
must define trust, credentials, egress, ingress, policy, action authorization,
audit/provenance, operator review, release gates, and no-go regression before
any future runtime can call an external system.

## Consequence

Future connector runtime must be disabled by default and policy-gated. It must
also pass action authorization, operator review, audit/provenance, credential
boundary, egress guard, ingress guard, sandbox, release gate, and rollback
checks.

## Constraints

- no network calls
- no credentials
- no tokens
- no SDK dependencies
- no privileged bypass
- no connector runtime
- no external calls by default
- no dynamic routes
