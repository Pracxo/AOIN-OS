# ADR 0024: Memory Governance, Decay, Forgetting, and Compaction

## Status

Accepted.

## Decision

AION Brain adds a Memory Governance layer that owns memory lifecycle decisions:
rules, decisions, decay records, retention sweeps, forget requests, generic
conflicts, conflict resolutions, compaction runs, and compacted-record links.

Postgres remains the canonical store for memory metadata and governance ledgers.
Semantic and graph memory adapters remain recall engines only. They can index
and retrieve candidates, but they do not decide truth, lifecycle state,
authorization, forgetting, or compaction.

Governance remains deterministic in v0.1. It uses rule conditions, metadata,
scope, timestamps, confidence, evidence references, policy decisions, risk, and
approval status. It does not call LLMs, external memory services, external
observability services, or domain-specific workflows.

## Reason

AION needs memory to be safe, current, scoped, auditable, and compactable before
real intelligence and external adapters become stronger. Without a governance
layer, vector and graph recall could be mistaken for truth or retain stale and
unsafe context.

## Consequences

Memory writes and retrieval are policy-gated and governance-aware. Retrieval can
filter expired or forbidden memories and carry governance constraints into
context compilation. Forgetting is approval-aware and uses soft deletion or
relationship disabling. Evidence is preserved by default. Compaction creates
deterministic summary records that reference input memory IDs.

Future memory engines can be added behind adapters without changing public
AION contracts. Future domain policies may live outside Brain core, while core
governance vocabulary stays generic.

## Constraints

- No hard deletion of evidence by default.
- No external model calls.
- No external network calls.
- No domain-specific memory logic.
- No public exposure of vector database rows, graph engine records, approval
  internals, policy engine internals, or vendor client objects.
