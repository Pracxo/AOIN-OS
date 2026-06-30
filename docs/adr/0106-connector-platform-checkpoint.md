# ADR 0106: Connector Platform Checkpoint

## Status

Accepted.

## Context

AION-106 through AION-114 established the external connector boundary,
disabled runtime preview, runtime review gate, synthetic dry-run simulator,
policy action catalog, sandbox design, credential store architecture, release
gate, and safety freeze. The connector phase now needs one checkpoint baseline
before any later implementation work can be proposed.

## Decision

Freeze the connector platform checkpoint after AION-115.

Connector implementation remains unapproved.

Connector runtime, external calls, credentials/tokens, sandbox execution,
activation, and route registration remain disabled.

Future connector implementation requires a new explicit ADR and gate evidence.

## Reason

AION needs a stable connector phase baseline before implementation work.

## Consequence

Future connector work starts from a reviewed checkpoint. The checkpoint
provides evidence, risk, closeout, and no-go material, but it does not approve
runtime behavior.

## Constraints

- no runtime enablement
- no external calls
- no credentials/tokens
- no sandbox execution
- no privileged bypass
