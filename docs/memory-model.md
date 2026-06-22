# Memory Model

AION Brain treats memory as a governed subsystem, not a raw data lake.

Memory retrieval is recall, not truth. A retrieved record is a ranked candidate
that may help reconstruct context. Canonical truth remains in the source systems
or raw evidence referenced by `content_ref`.

## Memory Classes

## Working Memory

Short-lived context used during a Brain loop execution.

## Episodic Memory

Records tied to events, traces, or interactions.

## Semantic Memory

Stable knowledge summaries, concepts, and facts that can be retrieved by
semantic memory adapters.

## Procedural Memory

Reusable methods, runbooks, or procedures that may be promoted after evaluation.
In v0.1 these live in the Skill Registry, not in `MemoryRecord`.

## Preference Memory

User or workspace preferences that require explicit scope and sensitivity.

## Graph Memory

Nodes and edges representing temporal relationships between generic Brain
objects such as events, memories, intents, contexts, plans, capabilities,
policies, traces, evaluations, learning signals, entities, and concepts.

## Audit Memory

Decision traces, policy decisions, learning signals, and execution outcomes
stored for accountability.

## Storage Responsibilities

Postgres remains the canonical source of memory metadata in v0.1. It stores
`MemoryRecord` fields: IDs, type, owner scope, source references, summary,
confidence, sensitivity, timestamps, metadata, and soft-delete state.

`MemoryRecord` is metadata plus summary. Raw evidence should be referenced
through `content_ref`, not copied into memory records.

## Memory Governance

Memory Governance makes memory safe, current, scoped, compacted, and
auditable. It owns generic lifecycle records:

- `MemoryGovernanceRule`
- `MemoryGovernanceDecision`
- `MemoryDecayRecord`
- `ForgetMemoryRequest` and `ForgetMemoryResult`
- `MemoryConflict`
- `MemoryCompactionRequest` and `MemoryCompactionResult`
- `MemoryRetentionSweepRequest` and `MemoryRetentionSweepResult`

Rules are domain-neutral and can apply to write gates, retrieval gates,
retention, decay, forgetting, compaction, and conflict detection. Governance
decisions can allow, deny, require approval, decay, expire, compact, flag a
conflict, or forget. Policy authorizes the governance action first; governance
then decides the memory lifecycle outcome.

Decay is deterministic. It uses age, confidence, missing source references,
missing evidence references, and recent access metadata. Decay changes recall
score and metadata; it does not rewrite source evidence or assert truth.

Forgetting is policy-gated and approval-aware. It uses soft deletion or
relationship disabling for memory-owned targets such as canonical memory,
semantic indexes, graph nodes, graph edges, evidence links, skills, and skill
candidates. Evidence records and chunks are not hard-deleted by default.

Conflict detection is generic. v0.1 detects duplicate summaries, structured
metadata disagreement, stale preferences, competing procedures, and scope
conflicts. Conflict resolution records the selected generic resolution without
silently rewriting evidence.

Compaction is deterministic and model-free. It can merge duplicates, group by
safe metadata keys, roll up preferences, roll up procedures, or perform a
deterministic extract. Output records reference input memory IDs and remain
recall summaries, not truth.

## Evidence Grounding

Memory records should use `content_ref` to point to evidence whenever a summary
comes from source material. Evidence stores source material and source
provenance. Semantic and graph memory retrieve context. Evidence grounds
claims.

Evidence links connect source material to memories, traces, plans, executions,
skills, evaluations, learning signals, and other Brain-owned targets. A memory
record can help AION recall relevant context, but a grounding claim must point
back to `EvidenceRecord` and `EvidenceChunk` IDs when AION needs source support.

## Belief State

Belief state sits beside memory, not inside raw memory records. A belief is an
explicit claim with status, confidence, provenance, supports, contradictions,
and revision history. Memory retrieval can surface `belief_state` items as
context, but those items are labeled as claims, not absolute truth.

Postgres remains canonical for the belief ledger. Vector recall, graph recall,
or future compressed memory adapters may retrieve belief-adjacent context later,
but they must not become the source of truth for claim status or revisions.

Truth maintenance updates belief confidence and status through explicit
revision records. It never rewrites source evidence, hides contradictions, or
promotes retrieved memory into truth without a policy-gated claim.

## Adapter Boundaries

`SemanticMemoryAdapter` is the public semantic memory interface. AION Brain
exposes AION contracts only, not storage engine rows, vector DB objects, or graph
engine objects. Brain services call this adapter boundary rather than pgvector,
TurboVec, or any vector engine directly.

Lexical retrieval remains available in v0.1 through the canonical memory
service. It uses Postgres metadata and deterministic lexical ranking:

- exact token overlap
- recency tie-break
- confidence tie-break

Semantic retrieval adds vector recall. pgvector is the working local baseline,
using the `pgvector/pgvector:pg16` Docker image and the
`aion_semantic_embeddings` table. The development embedding adapter is
`HashEmbeddingAdapter`, which is deterministic, local, and does not call any
external embedding provider.

`InMemorySemanticMemoryAdapter` exists for tests. `PgVectorSemanticMemoryAdapter`
is the default local semantic baseline. `TurboVecSemanticMemoryAdapter` is an
optional compressed recall adapter. It is disabled by default, uses
`turbovec_compat.py` as the only optional package boundary, and can fall open to
pgvector when the TurboVec package is unavailable.

TurboVec stores compressed recall index metadata in `aion_turbovec_indexes` and
`aion_turbovec_index_entries`. Those rows contain index IDs, vector IDs, memory
IDs, text hashes, scope, memory type, and status. They do not replace
`MemoryRecord` and do not store raw evidence.

## Vector Recall

Vector memory is recall only. It can suggest relevant records, but it cannot
prove truth by itself. Postgres remains canonical truth for `MemoryRecord`
metadata and auditability. pgvector stores recall vectors derived from
`MemoryRecord.summary`; TurboVec stores compressed recall indexes derived from
the same canonical summaries.

Raw evidence is not embedded directly. `content_ref` links to source evidence.
Memory write policy controls indexing and reindexing. Scope filtering is
mandatory for semantic retrieval.

TurboVec status, rebuild, and reindex operations are exposed only through
AION-owned contracts:

- `GET /brain/memory/semantic/adapters`
- `GET /brain/memory/semantic/turbovec/status`
- `POST /brain/memory/semantic/turbovec/rebuild`
- `POST /brain/memory/semantic/turbovec/reindex/{memory_id}`

## Temporal Graph Memory

Temporal graph memory stores relationship recall in Postgres for v0.1.
`GraphNode` records describe generic objects. `GraphEdge` records describe
generic relationships such as `references`, `derived_from`, `related_to`,
`depends_on`, `activates`, `produced`, and `constrained_by`.

Graph memory is relationship recall, not truth. It helps the Context Compiler
find related context and future visualization paths, but source evidence remains
outside graph rows. Provenance is tracked with `source_event_id`, and raw
evidence should still be referenced through `content_ref` on canonical memory
records when applicable.

Temporal fields have explicit meaning:

- `valid_from` and `valid_to` describe when a node or edge is considered valid.
- `observed_at` records when AION observed the relationship.
- `confidence` records retrieval confidence or source confidence.
- `sensitivity` informs policy and future retention handling.
- `owner_scope` enforces workspace or actor visibility.

Scope filtering is mandatory for node, edge, query, neighbor, and delete
operations. Deleted graph objects are excluded by default. Expired graph objects
are excluded unless a query explicitly sets `include_expired: true`.

`GraphMemoryAdapter` is the public graph boundary. AION Brain calls this
adapter, not Graphiti, Neo4j, FalkorDB, Memgraph, or any graph engine directly.
`PostgresGraphAdapter` is the v0.1 local baseline. `GraphitiGraphMemoryAdapter`
is optional and disabled by default. It uses `memory/graphiti_compat.py` as the
only vendor import boundary, records AION-owned sync metadata, and falls open to
Postgres graph memory when configured to do so.

Graphiti integration is adapter-ready, not a source of truth. Postgres graph
memory remains the canonical local graph ledger. Graphiti sync can index
canonical nodes and edges, add generic temporal episodes, and expose status
without leaking Graphiti client objects or backend rows. If Graphiti requires an
LLM path and the model gateway is disabled, AION reports
`graphiti_llm_disabled` and does not create a client.

## Retrieval Router

Lexical, semantic, and graph memory are candidate sources. The Retrieval Router
merges them with skill registry, capability, and trace candidates through
Brain-owned services and adapter boundaries. Each source contributes recall
candidates; none becomes truth by itself.

The Skill Registry is a separate procedural memory registry. It stores
`SkillRecord` and `SkillVersion` data, not executable code. Skills are retrieved
through the Retrieval Router when `skill_registry` is requested and converted
into procedural `RetrievedContextItem` candidates. They are not duplicated into
`MemoryRecord` automatically.

Active skills may inform planning by contributing matched skill IDs to
`PlanGraph` metadata. They do not execute, rewrite plan steps, or bypass policy.
Draft, disabled, and archived skills are excluded from active skill matching.

The Context Fusion Engine turns a ranked `RetrievalResult` into a
reasoning-ready `ContextBundle`. It deduplicates content, preserves references,
and creates a deterministic summary without LLM calls.

Memory recall is not truth. Canonical memory records, source systems, and raw
evidence references remain the source of truth. Retrieval and fusion only decide
which candidates are useful enough to include in the next `ContextPacket`.

## Working Memory

Working memory is short-lived cognitive state. It differs from long-term
semantic memory because it stores compact task/session context and references
that may expire unless pinned.

Working memory can reference memories, evidence, tasks, goals, skills,
capabilities, traces, retrievals, plans, and approvals. It is not a truth store,
does not promote itself to long-term memory, and must not store secrets or
chain-of-thought. Canonical truth remains in the relevant ledger or repository.

## Dialogue Memory Handoff

Dialogue memory handoff converts approved dialogue content into memory
candidates through AION-owned contracts. It is optional, policy-gated, and
explicitly requested by the caller or future governance layer.

The handoff path stores summaries and references, not raw hidden reasoning, raw
prompts, raw headers, secrets, provider chat objects, or external delivery
payloads. Dialogue messages remain dialogue ledger records; memory records are
separate recall artifacts with their own scope, sensitivity, confidence, and
provenance metadata.

Postgres remains the canonical metadata store. Vector, graph, and future
compressed recall adapters may index dialogue-derived memory later, but they
must consume AION memory contracts and never become the source of truth.

## Entity References in Memory

Memory records may carry entity references as canonical pointers in metadata or
source references. Entity references are not truth and do not replace memory
governance, evidence grounding, or belief status.

The Entity Resolver can link memories to entities through `ReferenceLink`
records when extraction is explicitly requested. Unresolved mentions remain
mentions until a future resolution run links them or an operator reviews them.

Entity merge and split lifecycle state must be visible to memory consumers.
Merged, archived, or unresolved entity references should be surfaced as
constraints during retrieval and context compilation instead of being silently
trusted.

## Preferences and Memory Governance

Preferences are not automatically memory. The Preference Ledger is the
canonical store for preferences, and learned preferences remain candidates
until confirmed.

Any future handoff from preference records into long-term memory must pass
through memory governance, store summaries and references only, and preserve
the rule that preferences cannot override policy, autonomy, approvals, runtime
configuration, capability limits, sandbox limits, or grounding requirements.

## Grounding and Memory Recall

Memory recall is weak support unless it is backed by primary evidence or a
supported belief claim. A memory record can explain why AION recalled context,
but it cannot become primary evidence by itself.

Evidence records are the primary grounding source. Supported beliefs may ground
a response when their support references are preserved and visible. Contradicted
beliefs cannot strongly ground a response and must surface a grounding
constraint instead.

Context packets preserve source attribution metadata from retrieval:

- `source_type`
- `source_id`
- `evidence_refs`
- `belief_refs`
- `memory_refs`
- `entity_refs`
- `trust_level`

The Context Compiler uses these hints to add constraints such as
`memory_only_support`, `weak_source_support`,
`contradicted_source_support`, and `missing_required_evidence`.
