# Visual Brain

AION Brain is designed to become an Obsidian-inspired living memory graph. The
v0.1 backend stores visual telemetry events so a future interface can animate
how a thought moves through the Brain.

Nodes represent:

- Events
- Intents
- Contexts
- Memories
- Graph nodes
- Capabilities
- Plans
- Policies
- Evaluations
- Learning signals
- Reflections
- Skill candidates
- Skills
- Evidence
- Evidence chunks
- Grounding claims
- Traces
- Event router subscriptions
- Dispatches
- Reaction actions
- Dead letters

Edges represent cognitive relationships, such as an event becoming an intent, an
intent producing context, context activating memory, policy checking a plan, and
evaluation producing a learning candidate.

Temporal graph memory will provide visual nodes and visual edges for the future
Brain map. A `GraphNode` becomes a visual node. A `GraphEdge` becomes a visual
edge. Active retrieval emits pulses through `memory_node_activated` telemetry,
and traversal paths become the active thought path.

Pulses represent active reasoning. Glow represents relevance or current
activity. Decay will represent stale memory in future memory visualizations.
The active path is the current thought route through the deterministic Brain
loop.

Confidence maps to intensity. Expired or stale graph items can visually decay
later. v0.1 only emits backend telemetry and graph contracts; no UI
implementation exists in this task.

A `RetrievedContextItem` becomes a node pulse. A `RetrievalResult` becomes a
thought activation cluster. A `ContextBundle` becomes the active context shell
around the current Brain loop. Retrieval scores map to glow intensity, and
deduplicated items should visually collapse into one node in future UI work.

Reflection and skill telemetry extends the learning path:

```text
learning signal -> reflection -> candidate -> skill -> active procedural memory
```

`reflection_created` creates a reflection node with intensity mapped to
reflection confidence. `skill_candidate_created` and
`skill_candidate_updated` create candidate nodes. `skill_promoted`,
`skill_activated`, `skill_disabled`, and `skill_archived` pulse skill nodes
with activation intensity. `skill_node_seen` represents retrieval of active
procedural memory and should appear as a skill glow in future UI work.

Evidence telemetry extends the grounded reasoning path:

```text
evidence -> chunk -> retrieved context -> prompt packet -> reasoning -> claim
```

`evidence_created` creates an evidence node. `evidence_chunk_created` creates a
chunk node. `evidence_retrieved` pulses evidence during retrieval and maps
search score to glow intensity. `evidence_linked` represents evidence links as
future graph edges. `evidence_grounded` creates a claim node with intensity
mapped to deterministic grounding score. `evidence_deleted` dims the evidence
node after soft delete.

No UI implementation exists in v0.1. Visual telemetry is a Brain-owned data
contract for future visualization work.

## AION Brain Map

The AION Brain Map is a backend projection of cognitive telemetry. It is
Obsidian-inspired in its graph form, but it is not coupled to Obsidian or any
other renderer. The projection owns semantics; a future UI only renders them.

### Nodes

Nodes are deduplicated by AION identity and node type. They preserve owner
scope, trace references, source references, status, intensity, first-seen time,
and last-seen time. Supported families include event, intent, context, memory,
graph, evidence, chunk, claim, retrieval, reasoning, model, plan, policy,
execution, lifecycle, learning, identity, capability, trace, and telemetry.

### Edges

Edges describe generic cognitive relationships. Timeline ordering creates
`triggered` edges. Explicit telemetry references create `linked_to` edges.
Known generic sequences create typed edges such as `classified_as`,
`compiled_into`, `retrieved`, `reasoned_over`, `planned`, `authorized_by`,
`blocked_by`, `executed_as`, `evaluated_by`, `learned_from`,
`reflected_into`, `promoted_to`, and `grounded_by`.

### Pulses

Each projected telemetry event can become a pulse. Pulses encode recent neural
firing behavior through intensity and duration, without prescribing animation
technology. A future renderer may turn pulses into glow, movement, or path
activation.

### Clusters

Clusters group nodes into stable trace, memory, reasoning, execution,
lifecycle, learning, and identity families. Evidence, chunks, and claims join
the memory family. Capabilities, modules, and runtimes join the execution
family. Cluster intensity is the average intensity of its member nodes.

### Trace Timeline

The trace timeline combines available decision trace, visual telemetry,
evaluation, and learning artifacts into chronological `TraceTimelineEvent`
records. Missing optional sources do not make timeline construction fail.

### Intensity Decay and Status

Intensity is always between zero and one. Optional deterministic exponential
decay uses a configurable half-life. Recent activity remains active. Old,
low-intensity activity becomes dormant. Blocked, failed, and completed event
names map to their corresponding visual statuses.

## Projection APIs

Brain Map, snapshot, telemetry query, trace timeline, and SSE endpoints expose
only AION-owned contracts. The SSE stream emits JSON `visual_telemetry` events
and supports a bounded `max_events` value for tests and local inspection.

## Future Rendering

A future frontend may render an Obsidian-style graph and neural firing
animations from these contracts. It may choose any rendering technology
without changing Brain semantics. No frontend implementation, frontend
dependency, WebSocket server, or external observability service exists in
AION-020.

## Attention Projection

The Visual Brain Projection supports focus, working memory, attention,
interrupt, and budget nodes.

- Focus nodes represent active focus sessions and can be rendered with an
  active glow by future UI.
- Working memory nodes represent short-lived slots; expired or deleted slots
  should dim or disappear depending on query scope.
- Attention signal pulses represent generic signals competing for focus.
- Interrupt pulses represent accepted, deferred, dismissed, or resolved
  interruptions.
- Context budget nodes represent the context shell. Overflow items are recorded
  outside that shell and can be rendered dimmed by future UI.

These semantics remain frontend-agnostic. AION emits nodes, edges, pulses, and
clusters; renderers decide how to animate them.

## Event Reaction Projection

The Event Reaction Router emits telemetry for subscription creation/disable,
dispatch, reaction start/completion/block, dead-letter creation/resolution, and
replay request. These events project into `event_router`, `subscription`,
`dispatch`, `reaction`, and `dead_letter` node types.

Router visualization remains generic. It shows how an accepted event triggered
or failed to trigger internal Brain reactions; it does not encode vertical
workflow semantics. Dead-letter pulses should appear as blocked or failed
activity in a future graph, and replay requests should appear as explicit
operator-driven pulses rather than autonomous background activity.
