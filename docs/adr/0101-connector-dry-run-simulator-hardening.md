# ADR 0101: Connector Dry-Run Simulator Hardening

## Status

Accepted for AION-110.

## Context

AION-106 defined connector boundaries, AION-108 added a disabled connector
runtime preview, and AION-109 added a runtime review gate. AION-110 needs local
simulation and replay evidence without crossing into real connector runtime
behavior.

## Decision

Add a stateless deterministic connector simulator with synthetic request shape
validation, synthetic response shape validation, fixture replay, policy
readiness checks, audit evidence, telemetry, SDK helpers, CLI commands, docs,
examples, and static console demo data.

The simulator remains separate from connector runtime execution. It cannot call
external services, use credential or token material, activate runtime features,
register routes, execute tools, execute writes, or trust ingress.

## Consequences

Operators can review connector request and response shape readiness before a
future implementation gate. The release, hardening, freeze, and diagnostics
surfaces now include explicit simulator checks while connector runtime remains
disabled.
