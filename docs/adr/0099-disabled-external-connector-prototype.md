# 0099: Disabled External Connector Prototype

## Status

Accepted for AION-108.

## Context

AION-106 defined the external connector boundary. AION-107 defined the future
operator write-path architecture. AION-108 needs a local, disabled connector
prototype so operators and developers can inspect mock manifest validation,
egress preview, ingress preview, blockers, and audit evidence before any
connector runtime exists.

## Decision

Add a disabled connector runtime gate and mock-only preview services behind
hard-off settings. The prototype exposes status, mock manifest validation,
egress preview, ingress preview, audit, SDK helpers, CLI helpers, examples, and
static console demo data.

The prototype must not call external services, add connector/provider SDKs, add
network clients, store credentials, store tokens, register routes, activate
capabilities, execute tools, execute write paths, or bypass policy/audit.

## Consequences

Future connector runtime work must pass the connector release gates, no-go
regression pack, policy model, action authorization, audit/provenance review,
and operator approval model before any runtime enablement can be considered.
