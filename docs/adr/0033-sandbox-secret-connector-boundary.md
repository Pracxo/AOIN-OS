# ADR 0033: Sandbox, Secret, and Connector Boundary

## Status

Accepted

## Decision

AION Brain adds a Sandbox Control Plane for future sandboxed execution.

AION Brain adds a Secret Reference Vault with metadata-only secret refs. Raw
secret material is never stored in Brain state.

AION Brain adds a Connector Registry for connector metadata only. Connectors do
not call external systems in v0.1.

Sandbox execution is disabled in v0.1. Docker and Firecracker remain
placeholder adapters that return `unsupported`.

## Reason

Future modules need explicit isolation, permission, secret reference, connector
reference, risk, approval, autonomy, and audit boundaries before any controlled
execution can be trusted.

## Consequence

The module runtime gateway, MCP service, command bus, and certification harness
can validate sandbox constraints before any future controlled action. Runtime
permission grants define what a target may access, and sandbox run records make
that validation auditable.

## Constraints

No raw secrets are stored.

No external connector calls are made.

No container execution is performed.

No subprocess execution is allowed in sandbox code.

No domain-specific connectors live in Brain core.
