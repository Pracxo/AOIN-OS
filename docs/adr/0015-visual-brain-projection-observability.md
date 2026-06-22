# ADR 0015: Visual Brain Projection and Observability Spine

## Status

Accepted

## Decision

Add a Visual Brain Projection backend that converts canonical cognitive
telemetry into frontend-agnostic nodes, edges, pulses, clusters, Brain Maps,
and trace timelines.

Use a local observability recorder in v0.1. Keep Langfuse behind a future
optional `ObservabilityAdapter`; AION public contracts remain independent of
Langfuse internals.

## Reason

AION needs a live Brain data form before a frontend is selected or built. The
projection layer gives future renderers stable cognitive semantics while
keeping telemetry, governance, storage, and policy inside Brain core.

## Consequences

- A future frontend can render an Obsidian-style memory graph and neural firing
  animations without redefining Brain semantics.
- Visual projection and trace timelines are testable without a UI.
- Observability failures do not interrupt the deterministic Brain loop.
- Langfuse or another recorder can be added later behind the adapter boundary.

## Constraints

- No frontend implementation in this task.
- No external observability service calls in v0.1.
- No Langfuse SDK dependency or import.
- No domain-specific visualization logic.
- Public projection contracts remain frontend-agnostic and policy-gated.
