# 0068: Capability Conformance Harness and Readiness Gate

## Status

Accepted.

## Context

AION Brain v0.1 can stage extension packages, module slots, and capability
bindings, but staged metadata needs a deterministic conformance path before any
future activation layer exists.

## Decision

AION Brain adds a backend-only Capability Conformance Harness. It owns
conformance profiles, capability test vectors, schema-only mock invocation
records, conformance runs, findings, and extension readiness assessments.

The harness validates metadata and schemas only. It does not load package code,
install packages, invoke capabilities, register dynamic routes, activate
extensions, call MCP servers, call sandbox runtimes, or call external services.

Readiness assessments stay conservative. They can report blockers and warnings,
but `activation_ready` remains false in v0.1.

## Consequences

Future extension activation can consume local conformance and readiness records,
but activation must still be implemented by a later task behind explicit policy
and execution boundaries.

## Constraints

- No code execution.
- No package installation.
- No activation.
- No external network calls.
- No MCP calls.
- No sandbox code execution.
- No domain-specific conformance logic.
