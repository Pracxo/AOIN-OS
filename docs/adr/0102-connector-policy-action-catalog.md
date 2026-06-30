# 0102: Connector Policy Action Catalog

## Status

Accepted

## Context

AION already has a disabled connector runtime prototype and a synthetic
connector dry-run simulator. The next step needs policy action visibility,
role-aware authorization, denial rules, and traceability without enabling any
connector runtime.

## Decision

Add a connector policy action catalog, authorization matrix, dry-run gate,
denial service, traceability service, API router, SDK resource, CLI preview
commands, static console demo data, examples, and regression scripts.

The implementation remains local and preview-only. It does not create external
connector runtime, external calls, credential handling, token handling,
activation, route registration, code loading, tool execution, or write
execution.

## Consequences

Future connector runtime work must reference this catalog and denial evidence.
Unknown or future runtime actions fail closed until a later implementation
milestone explicitly changes the boundary.
