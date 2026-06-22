# 0046: Belief State and Truth Maintenance

## Status

Accepted

## Context

AION Brain needs a way to remember explicit claims, their support, and their
contradictions without pretending retrieved memory is truth. Dialogue, evidence,
reasoning, and future modules all need a generic claim boundary before the
system can reason safely over changing state.

## Decision

AION Brain owns a Belief State Manager with a canonical claim ledger, support
ledger, contradiction ledger, revision ledger, and truth-maintenance run ledger.
Beliefs are represented by AION contracts such as `BeliefClaim`,
`BeliefSupport`, `BeliefContradiction`, `BeliefRevision`, `BeliefQueryResult`,
and `TruthMaintenanceRun`.

Truth maintenance is deterministic and local in v0.1. It recomputes confidence,
marks stale claims, records contradiction state, and persists revisions. It does
not call model providers, external fact-checkers, web search, or domain-specific
knowledge systems.

Dialogue and evidence can opt in to deterministic claim extraction. Extracted
claims pass through the same policy, provenance, audit, telemetry, and storage
boundaries as manually created claims.

## Consequences

Reasoning and context compilation can retrieve belief state as scoped claims
with explicit status metadata. Stale and contradicted beliefs become visible
constraints instead of invisible facts.

Future vector, graph, or compressed recall systems may index belief-adjacent
context, but Postgres remains canonical for belief status, support,
contradiction, revision, and truth-maintenance records.

## Constraints

- Belief state is not absolute truth.
- Belief contracts must not expose SQLAlchemy rows, vector DB handles, graph
  engine objects, provider SDK objects, external fact-check responses, or raw
  model outputs.
- Belief services must stay domain-neutral and Brain-only.
- Stored claims, supports, contradictions, telemetry, audit, and docs must not
  contain raw secrets, raw prompts, hidden reasoning, chain-of-thought, or raw
  headers.
