# 0069: Golden Path Scenario Harness

## Status

Accepted.

## Context

AION Brain v0.1 has many local governance, memory, dialogue, registry, release,
and operator subsystems. The project needs one canonical deterministic path that
proves these layers can connect before release without becoming a production
monitoring system or a frontend demo.

## Decision

Add a Brain-owned Golden Path Scenario Harness with contracts for scenarios,
fixture packs, step results, assertion results, runs, reports, and release smoke
checks.

The harness is local-only and dry-run by default. It seeds synthetic
scenario-owned fixtures, runs deterministic service availability steps, evaluates
assertions, persists reports, emits telemetry, records audit/provenance where
available, and can create operator recommendations for failures.

The release smoke matrix reads local readiness only. It does not execute shell
commands, call external services, run real backups, package releases, or mutate
non-scenario records.

## Constraints

- Policy, autonomy, and approval boundaries remain in force.
- Unknown assertion types fail closed.
- Controlled mode is disabled by default.
- No external services or model providers are called.
- No tools, action proposals, or execution handoffs are executed.
- No domain-specific scenarios or vertical workflows are added.
- No frontend code is introduced.

## Consequences

AION gets a canonical local end-to-end verification surface that can feed the
Operator Control Tower, Freeze Gate, Release Package, Resource Registry, visual
telemetry, SDK, CLI, and local scripts.

Future external runners can integrate behind governed adapters without changing
Brain-owned scenario and report semantics.
