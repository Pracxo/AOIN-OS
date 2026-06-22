# ADR 0043: Tamper-Evident Audit and Provenance

## Status

Accepted for AION Brain v0.1.

## Decision

AION adds a local tamper-evident audit hash chain.

AION adds generic provenance links between Brain records.

AION does not use external anchoring in v0.1.

Corrections and redaction markers are append-only. The original audit entry is
not mutated or hard-deleted.

## Reason

AION needs a verifiable local audit history before broader module, execution,
and operational use. The Brain must be able to answer what happened, what policy
allowed or blocked it, what command or event caused it, and whether the local
audit chain is intact.

## Consequences

Major Brain actions can be traced and verified locally. Future external audit
sinks can consume AION-owned contracts without becoming the source of truth.

## Constraints

- No raw secrets.
- No raw prompts.
- No chain-of-thought storage.
- No domain-specific audit logic.
- No external notarization or compliance certification in v0.1.
