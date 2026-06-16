# ADR 0047: Concept Registry and Entity Resolver

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds a Concept Registry and Entity Resolver as the canonical
reference layer for generic Brain records.

The Concept Registry owns abstract, domain-neutral concepts. The Entity
Registry owns canonical references, aliases, mentions, reference links,
resolution runs, merge proposals, and split proposals.

AION v0.1 uses deterministic mention extraction and deterministic resolution
scoring. It does not use LLM-based extraction, external NLP services,
image-based identification, auto-merge, hard deletes, or a domain ontology in
Brain core.

## Reason

AION needs one canonical way to name and link things across evidence, memory,
beliefs, dialogue, graph records, traces, audit entries, and provenance links.
Future modules can refer to canonical entities without owning entity semantics
or duplicating resolver logic.

## Consequences

Entity references are pointers, not verified truth. Beliefs remain explicit
claims. Evidence remains source material. Memory remains recall. Graph memory
remains graph structure.

Merge and split workflows are proposal-based and policy-gated. Duplicate
entities are marked merged, not hard-deleted. Split approval can create
proposed entities while keeping the original entity unless another explicit
action changes it.

## Constraints

- No LLM-based entity extraction.
- No external NLP service calls.
- No image-based person identification.
- No sensitive identity inference.
- No auto-merge.
- No hard deletes.
- No domain-specific entity types, concept types, or ontologies in Brain core.
