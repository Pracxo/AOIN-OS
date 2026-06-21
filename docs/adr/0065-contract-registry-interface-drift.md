# 0065: Contract Registry and Interface Drift Gate

## Status

Accepted

## Context

AION Brain exposes public contracts across Pydantic models, FastAPI APIs, SDK
resources, CLI commands, policy actions, environment settings, resource types,
and visual telemetry vocabulary. Release readiness needs a deterministic way to
inventory and compare those interfaces without making generated files the
source of truth.

## Decision

AION Brain adds a Contract Registry and Interface Drift Gate. The registry scans
AION-owned source surfaces, stores contract index records, stores interface
inventory records, creates point-in-time snapshots, seeds generic compatibility
rules, runs compatibility scans, records interface drift findings, generates
informational migration notes, and emits local reports.

Source code remains the source of truth. The registry records what exists; it
does not generate source, mutate source contracts, rewrite routes, repair SDK
methods, or execute migration steps.

## Consequences

Release packaging, freeze gates, operator queues, runtime configuration,
resource registry indexing, audit/provenance, policy catalog, SDK, CLI, and
visual telemetry can inspect contract state through AION-owned contracts.

Compatibility failures are advisory records until another governed release or
freeze gate consumes them. Migration notes are instructions for humans or
future governed workflows; they do not execute.

## Constraints

- No source mutation.
- No code generation.
- No external network calls.
- No domain-specific interface rules.
- No raw prompts, raw headers, hidden reasoning, provider payloads, or secrets
  in snapshots, reports, telemetry, SDK output, or CLI output.
- Public APIs return AION contracts only.
