# Connector Runtime Gate

## Purpose

The connector runtime gate reports hard-off connector posture. It is the local
proof point that connector runtime is not enabled in AION-108.

## Gate Checks

The gate reports false for:

- connector runtime
- external connector calls
- connector credentials
- connector token storage
- connector activation
- connector route registration

It also emits disabled-runtime blockers and visual telemetry event
`connector_runtime_status_checked`.

## Policy Boundary

The gate uses policy action `connector_runtime.status.read`. Preview and audit
actions use scoped policy actions but do not grant execution, write paths,
external calls, or activation.
