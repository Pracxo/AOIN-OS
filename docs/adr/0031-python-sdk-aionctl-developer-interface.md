# ADR 0031: Python SDK and aionctl Developer Interface

## Status

Accepted for AION Brain v0.1.

## Decision

AION provides a standalone Python SDK and `aionctl` CLI under
`packages/aion-sdk-python`.

The SDK communicates with AION Brain through public HTTP APIs only. The CLI
communicates with AION Brain only through the SDK.

## Reasons

Developers need a stable local interface for health checks, kernel diagnostics,
event intake, memory recall, command dispatch, workflow status, autonomy status,
smoke tests, and contract export.

Keeping the SDK outside the server package prevents accidental coupling to
repositories, adapters, framework objects, or implementation details.

## Consequences

- SDK tests can run without Docker.
- Contract drift is visible through public HTTP behavior.
- Future clients can share the same public API assumptions.

## Constraints

- No `aion_brain` imports.
- No database or provider SDK dependencies.
- No production authentication in v0.1.
- No vertical/domain-specific commands.
- No live network calls in tests.

