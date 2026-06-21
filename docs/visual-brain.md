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

## Dialogue Projection

Dialogue telemetry projects backend conversation artifacts into generic visual
nodes:

- `dialogue`
- `message`
- `clarification`
- `response`
- `feedback`

Dialogue events can show session creation, message creation, turn start and
completion, clarification requested or answered, response composed, response
verified, local delivery recorded, feedback recorded, and memory handoff
created. These events remain frontend-agnostic. A future renderer may animate
conversation pulses beside reasoning, memory, policy, and trace nodes, but
AION-051 adds no React, Canvas, WebSocket, or UI implementation.

Dialogue projection must not include raw prompts, hidden reasoning,
chain-of-thought, secrets, raw headers, or provider chat objects. The graph
shows AION-owned cognitive events and references only.

## Belief Projection

Belief telemetry projects claim lifecycle events into the visual brain map
without adding any frontend dependency. Generic belief events include claim
creation, support addition, contradiction detection or resolution, belief
queries, and truth maintenance runs.

Future renderers can show belief nodes, claim nodes, contradiction nodes, and
truth-maintenance pulses. Stale or contradicted claims should be visually
distinguishable from supported claims, but the backend contract only emits
frontend-agnostic node, edge, pulse, status, and metadata values.

Belief projection must not display raw secrets, hidden reasoning, or raw prompt
content. It should show claim IDs, source references, status, confidence, and
trace references only.

## Concept and Entity Projection

Concept and entity telemetry projects canonical reference activity into the
Visual Brain Projection without adding frontend dependencies.

New generic visual nodes include:

- `concept`
- `entity`
- `mention`
- `reference`
- `resolution`
- `merge`
- `split`

Concept creation and archival produce concept pulses. Entity creation,
archival, deletion, alias creation, mention creation, resolution start and
completion, reference link creation, merge proposal/completion, and split
proposal/completion produce entity resolver pulses.

A future renderer may show the generic resolution path:

`mention -> candidate -> entity -> reference link -> provenance`

Reference edges are canonical pointers, not proof. Merge and split pulses show
operator-governed lifecycle changes only. AION v0.1 adds no React, Canvas,
Three.js, WebSocket, or UI implementation for this projection.
## Decision Projection Nodes

The visual projection layer can render decision frame nodes, option nodes,
option evaluation nodes, tradeoff nodes, counterfactual projection nodes, and
decision journal nodes.

The generic decision path is:

`situation -> frame -> options -> evaluation -> counterfactual -> recommendation -> journal`

Decision visual telemetry never implies that an option executed. It only shows
the recommendation and journal path.

## Outcome Projection

Outcome telemetry projects expected effects, observed effects, outcome records,
verification runs, causal attributions, and outcome feedback into the Visual
Brain Projection.

Generic visual nodes include:

- `expected_effect`
- `observed_effect`
- `outcome`
- `effect_verification`
- `causal_attribution`
- `outcome_feedback`

A future renderer may show the generic path:

`expected effect -> observed effect -> outcome -> verification -> feedback`

Outcome projection is frontend-agnostic. It does not render UI, call external
observability services, mutate source records, or imply that an observed
completion has been verified.

## Learning Projection

Learning synthesis telemetry projects experience records, pattern mining runs,
learning patterns, lessons, skill suggestions, regression suggestions, and
synthesis runs into the Visual Brain Projection.

Generic visual nodes include:

- `experience`
- `learning_pattern`
- `lesson`
- `synthesis`
- `skill_suggestion`
- `regression_suggestion`

A future renderer may show the generic path:

`experience -> learning pattern -> lesson -> suggestion -> operator review`

Learning projection is review-only. A pulse for a suggestion does not mean a
skill was promoted, a regression was created, code was modified, or an
external service was called.

## Self Model Projection

Self-model telemetry adds frontend-agnostic graph signals for:

- `self_model`
- `capability_awareness`
- `limitation`
- `confidence`
- `self_assessment`
- `introspection`

The generic self-model visual path is:

`kernel/config/capabilities -> awareness -> limitations -> confidence -> response disclosure`

Self-description generation creates a `self_model` node for `aion`.
Capability refresh creates a `capability_awareness` node for the capability
inventory. Limitation creation creates limitation pulses, with critical
limitations receiving the highest intensity. Confidence calibration creates
confidence pulses using the calibrated score. Self-assessment and
introspection snapshots create diagnostic pulses only.

The projection remains backend-only in v0.1. It does not implement React,
Canvas, Three.js, Rive, Lottie, WebSocket UI, or frontend-specific state.

## Explanation Projection

Explanation telemetry projects public explanation activity into the Visual
Brain Projection. Generic event types include:

- `explanation_created`
- `explanation_verified`
- `explanation_blocked`
- `trace_narrative_created`
- `why_not_answer_created`
- `explanation_feedback_recorded`

Generic visual node types include:

- `explanation`
- `trace_narrative`
- `why_not`
- `explanation_feedback`

The projection may later render an explanation path such as:

`trace -> explanation -> verification -> feedback`

and a why-not path such as:

`blocked action -> why-not -> missing requirement -> next possible step`

These are frontend-agnostic records. They do not expose hidden reasoning,
raw prompts, raw secrets, or renderer-specific state.

## Instruction Projection

Instruction telemetry projects instruction records, preferences, constraints,
style profiles, conflicts, and instruction resolution runs into the Visual
Brain Projection.

Generic visual nodes include:

- `instruction`
- `preference`
- `constraint`
- `style_profile`
- `instruction_conflict`
- `instruction_resolution`

The generic projection path is:

`instruction/preference/constraint -> conflict detector -> resolver -> context/response`

The projection remains backend-only and frontend-agnostic. It does not expose
hidden prompts, chain-of-thought, raw secrets, policy internals, or renderer
state.

## Grounding Projection

Grounding telemetry projects source attribution activity into the Visual Brain
Projection. Generic event types include:

- `grounding_source_created`
- `citation_record_created`
- `citation_map_created`
- `unsupported_statement_detected`
- `grounding_verification_started`
- `grounding_verification_completed`
- `source_coverage_report_created`

Generic visual node types include:

- `grounding`
- `citation`
- `citation_map`
- `unsupported_statement`
- `source_coverage`

The generic grounding path is:

`response statement -> citation -> source -> evidence/belief/memory -> verification`

Memory nodes in this path represent recall only. A future renderer may dim
memory-only support, highlight unsupported statements, and show source coverage
warnings, but it must consume AION-owned visual contracts rather than reaching
into grounding repositories directly.

Grounding projection remains deterministic and frontend-agnostic. It does not
invent citations, call web search, expose raw prompts, expose hidden reasoning,
or apply domain-specific citation rules.

## Prompt Governance Projection

Prompt telemetry projects prompt governance records into the Visual Brain
Projection. Generic event types include:

- `prompt_template_created`
- `prompt_fragment_created`
- `prompt_packet_compiled`
- `prompt_boundary_checked`
- `prompt_injection_detected`
- `model_input_manifest_created`
- `prompt_preview_created`

Generic visual node types include:

- `prompt`
- `prompt_template`
- `prompt_fragment`
- `prompt_packet`
- `prompt_boundary`
- `prompt_injection`
- `model_input`

The generic prompt path is:

`instruction/context/grounding -> prompt packet -> boundary check -> model input manifest`

Blocked prompt packets and high severity injection findings should project with
higher intensity than normal compiled packets. The projection remains
backend-only and frontend-agnostic. It does not expose raw rendered prompts,
hidden reasoning, provider payloads, raw secrets, or domain-specific prompt
logic.

## Model Output Governance Projection

Model output governance telemetry projects provider-neutral output handling into
the Visual Brain Projection. Generic event types include:

- `model_output_received`
- `model_output_parsed`
- `model_output_governed`
- `model_output_blocked`
- `structured_output_validated`
- `response_candidate_created`
- `response_candidate_promoted`
- `tool_intent_captured`
- `tool_intent_blocked`

Generic visual node types include:

- `model_output`
- `output_segment`
- `structured_validation`
- `response_candidate`
- `tool_intent`
- `output_governance`

The generic projection path is:

`model output -> parsed segment -> structured validation -> governance -> response candidate/tool intent`

Blocked outputs and blocked tool intents should project with higher intensity
than passing governance runs. The projection remains backend-only and
frontend-agnostic. It does not expose raw model output, provider payloads,
hidden reasoning, raw prompts, raw headers, raw secrets, or domain-specific
output logic.
