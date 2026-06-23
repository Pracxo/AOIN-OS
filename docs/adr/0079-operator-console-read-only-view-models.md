# 0079: Operator Console Read-Only View Models

## Status

Accepted.

## Context

AION-087 kept the Operator Console CLI/API-first and delayed runtime UI work.
Future UI work still needs stable data contracts before a rendering layer exists.

## Decision

Add read-only Operator Console view-model extraction in AION Brain.

View models are redacted and read-only. They summarize existing Brain state,
return unavailable sections when source services are missing, and expose actions
as descriptors only. Write actions remain disabled.

No frontend runtime is added. No frontend dependencies are added. The console
contract has no privileged bypass around policy, audit, approval, redaction, or
module governance.

## Reason

The future console needs a stable backend data shape before implementation. A
read-only API contract lets SDK and CLI consumers verify the shape while keeping
runtime activation, execution, route registration, package installation, and
external calls disabled.

## Consequences

Future UI can consume Operator Console view models without bypassing Brain
policy, audit, approval, and safety boundaries.

Console views can show status, blockers, warnings, refs, safe summaries, and
descriptor-only actions. They must not expose source payloads that are blocked
by the redaction contract.

## Constraints

- no runtime UI
- no frontend dependencies
- no privileged bypass
- no raw prompt exposure
- no hidden reasoning exposure
- no secret exposure
- no activation
- no execution
- no external service calls
- no database migrations
