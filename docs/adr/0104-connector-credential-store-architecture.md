# 0104: Connector Credential Store Architecture

## Status

Accepted for AION-113.

## Context

The connector runtime, policy catalog, simulator, and sandbox lanes remain disabled or preview-only. Future real connectors will eventually require credential and token handling, but AION OS must first define secret handling, lifecycle, redaction, audit, provenance, authorization, and no-go gates.

## Decision

Add connector credential architecture contracts, services, API, SDK, CLI preview commands, static console data, examples, docs, and regressions without implementing storage. The architecture/readiness/redaction previews are enabled, while credential storage, token storage, secret material, external identity runtime, and connector runtime credential access stay disabled.

## Consequences

Operators can inspect the future credential boundary and readiness blockers. No credential material can be stored, read, rotated, revoked, exchanged, or materialized. Future implementation requires a separate milestone and release gate.
