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

## Connector Simulator Projection

AION-110 adds frontend-agnostic telemetry for synthetic connector simulator
evidence:

- `connector_simulation_completed` with node type `connector_simulation`
- `connector_policy_readiness_checked` with node type `connector_policy_readiness`

These events show local dry-run and readiness evidence only. They must not
imply connector execution, trusted ingress, route registration, activation,
external calls, credential use, token use, tool execution, or write execution.

## Self-Improvement Shadow Evaluation Projection

AION-179 evidence can be projected as read-only visual nodes for
`shadow_operator_evaluation`, `shadow_evaluation_scenario`, and
`shadow_activation_review_boundary`. These nodes represent advisory evidence and
must not imply runtime activation, source mutation, Git mutation, approval
creation, pull request creation, merge, deployment, provider calls, connector
calls, or model training.

## Module Mock Runtime Projection

AION-085 adds frontend-agnostic visual telemetry for deterministic module mock
runtime records. The projection uses:

- `module_mock_profile_created` with node type `module_mock_profile`
- `module_mock_invocation_started` with node type `module_mock_run`
- `module_mock_invocation_completed` with node type `module_mock_run`
- `module_mock_output` with node type `module_mock_output`
- `module_mock_finding_dismissed` with node type `module_mock_finding`

These events show dry-run readiness evidence only. They must not imply module
activation, real output, route registration, code loading, external calls, MCP
tool calls, model calls, or capability execution.

## Contract Registry Projection

Contract Registry telemetry projects interface readiness into the visual brain
map. Contract snapshots, compatibility scans, interface drift findings,
migration notes, and contract reports use frontend-agnostic node types:
`contract_snapshot`, `compatibility_scan`, `interface_drift`,
`migration_note`, and `contract_report`.

Snapshot events should appear as source-of-truth inventory points. Compatibility
scan events should appear as advisory gate activity. Breaking drift findings
should appear as blocked or warning pulses depending on severity. Migration
notes are informational nodes only; they must not imply that migration steps
were executed.

Projection payloads must remain redacted and generic. They must not include raw
prompts, hidden reasoning, raw headers, provider payloads, secrets, generated
source, or domain-specific interface logic.

## Bootstrap Projection

First-run bootstrap emits frontend-agnostic visual telemetry for bootstrap
profiles, seed bundles, seed executions, setup doctor runs, setup findings,
bootstrap runs, and setup reports. The projection uses node types such as
`bootstrap`, `bootstrap_profile`, `seed_bundle`, `seed_execution`,
`setup_doctor`, `setup_finding`, and `setup_report`.

Critical setup findings should appear as blocked or failed readiness pulses.
Dry-run seed executions should appear as local metadata activity, not as
external provisioning. Bootstrap projection payloads must remain redacted and
must not include raw secrets, raw headers, production credentials, external
provider payloads, package installation records, source mutation details, or
domain-specific setup logic.

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

## Action Proposal Projection

Action proposal telemetry projects reviewed action intent into the Visual Brain
Projection. Generic event types include:

- `action_proposal_created`
- `action_proposal_reviewed`
- `action_proposal_blocked`
- `action_blocker_created`
- `action_blocker_resolved`
- `tool_intent_reviewed`
- `execution_handoff_created`
- `execution_handoff_blocked`

Generic visual node types include:

- `action_proposal`
- `action_blocker`
- `action_review`
- `execution_handoff`
- `tool_intent_review`

The generic action path is:

`tool intent / decision / plan -> proposal -> review -> handoff -> governed target system`

Blocked proposals, open blockers, and blocked handoffs should project with
higher intensity than normal dry-run handoffs. Handoff nodes represent
handoff records, not completed target execution. The projection remains
backend-only and frontend-agnostic, and must not expose raw payloads, hidden
reasoning, secrets, target service internals, or domain-specific action logic.

## Run Supervision Projection

Run supervision telemetry projects governed run observation into the Visual
Brain Projection. Generic event types include:

- `run_supervision_created`
- `run_status_sampled`
- `run_stalled_detected`
- `run_timeout_detected`
- `run_control_requested`
- `run_control_handed_off`
- `run_control_blocked`
- `compensation_plan_created`
- `compensation_plan_approved`
- `compensation_steps_converted`
- `run_supervision_report_created`

Generic visual node types include:

- `run_supervision`
- `run_status_sample`
- `run_control`
- `timeout_policy`
- `compensation_plan`
- `compensation_step`
- `supervision_report`

The generic supervision path is:

`handoff -> supervised run -> status sample -> control request / compensation plan -> outcome`

Stalled and timed-out runs should project with higher intensity than ordinary
status samples. Control request nodes represent requests, not direct target
mutation. Compensation plan nodes represent proposed recovery paths, not
execution. The projection remains backend-only and frontend-agnostic, and must
not expose raw target internals, raw headers, secrets, or domain-specific
remediation logic.

## Notification Projection

Internal notification telemetry projects local operator-awareness records into
the Visual Brain Projection. Generic event types include:

- `notification_topic_created`
- `notification_subscription_created`
- `notification_published`
- `notification_delivered_local`
- `notification_acknowledged`
- `alert_created`
- `alert_acknowledged`
- `alert_resolved`
- `escalation_record_created`
- `notification_digest_created`

Generic visual node types include:

- `notification`
- `notification_topic`
- `notification_subscription`
- `alert`
- `escalation`
- `digest`

The generic projection path is:

`source record -> notification -> local delivery -> alert / escalation -> digest`

High and critical alerts should project with higher intensity than ordinary
informational notifications. Escalation nodes represent local queue records, not
external paging or remediation. Digest nodes represent deterministic summaries.
The projection remains backend-only and frontend-agnostic, and must not expose
hidden reasoning, raw prompts, raw headers, provider payloads, secrets,
external delivery metadata, or domain-specific alert logic.

## Scheduler Projection

Temporal scheduler telemetry projects local time coordination into the Visual
Brain Projection. Generic event types include:

- `schedule_created`
- `schedule_paused`
- `schedule_resumed`
- `schedule_disabled`
- `schedule_due_item_created`
- `schedule_due_item_processed`
- `reminder_created`
- `reminder_acknowledged`
- `reminder_snoozed`
- `reminder_dismissed`
- `scheduler_tick_started`
- `scheduler_tick_completed`
- `schedule_missed_detected`
- `scheduler_report_created`

Generic visual node types include:

- `schedule`
- `due_item`
- `reminder`
- `scheduler_tick`
- `schedule_policy`
- `scheduler_report`

The generic scheduler path is:

`schedule -> tick -> due item -> notification / action proposal / operator item`

Missed schedules project with higher intensity than ordinary due items.
Scheduler nodes represent local scheduler records, not target execution.
The projection remains backend-only and frontend-agnostic, and must not expose
external calendar objects, external delivery metadata, secrets, or
domain-specific scheduling logic.

## Incident Projection

Incident telemetry projects local incident correlation records into the Visual
Brain Projection. Generic event types include:

- `incident_signal_created`
- `incident_created`
- `incident_acknowledged`
- `incident_resolved`
- `incident_correlation_rule_created`
- `incident_correlation_started`
- `incident_correlation_completed`
- `root_cause_candidate_created`
- `root_cause_candidate_confirmed`
- `recovery_review_created`

Generic visual node types include:

- `incident_signal`
- `incident`
- `correlation_rule`
- `correlation_run`
- `root_cause`
- `recovery_review`

The generic projection path is:

`signal -> correlation run -> incident -> root cause candidate -> recovery review`

High and critical incident signals should project with higher intensity than
informational signals. Root cause nodes represent candidates, not established
truth. Recovery review nodes represent local review artifacts, not executed
remediation. The projection remains backend-only and frontend-agnostic, and
must not expose external incident-system payloads, raw headers, secrets, source
internals, or domain-specific incident logic.

## Lifecycle Projection

Data lifecycle telemetry projects retention and review activity into the Visual
Brain Projection. Generic event types include:

- `lifecycle_policy_created`
- `lifecycle_evaluation_started`
- `lifecycle_evaluation_completed`
- `resource_lifecycle_classified`
- `archive_candidate_created`
- `archive_candidate_converted`
- `redaction_candidate_created`
- `redaction_candidate_converted`
- `purge_preview_created`
- `lifecycle_review_recorded`
- `lifecycle_report_created`

Generic visual node types include:

- `lifecycle`
- `retention_classification`
- `archive_candidate`
- `redaction_candidate`
- `purge_preview`
- `lifecycle_review`
- `lifecycle_report`

The generic projection path is:

`resource -> classification -> archive / redaction / purge preview -> review -> report`

Archive and redaction nodes represent advisory candidates, not executed
actions. Purge preview nodes represent blocked or warning impact previews, not
deletion. Lifecycle projection remains backend-only and frontend-agnostic, and
must not expose raw headers, hidden reasoning, raw prompts, secrets,
source-system internals, or domain-specific retention logic.

## Extension Registry Projection

Extension Registry telemetry projects metadata intake and compatibility
readiness into the Visual Brain Projection. Generic event types include:

- `extension_package_registered`
- `extension_manifest_validated`
- `extension_compatibility_checked`
- `extension_intake_started`
- `extension_intake_completed`
- `extension_review_recorded`
- `extension_install_plan_created`

Generic visual node types include:

- `extension`
- `extension_package`
- `extension_manifest`
- `extension_capability`
- `extension_dependency`
- `extension_compatibility`
- `extension_review`
- `extension_install_plan`

The generic projection path is:

`extension -> manifest -> compatibility -> review -> install plan`

Blocked compatibility and unsafe runtime flags should project with higher
intensity than ordinary metadata intake. Install-plan nodes represent future
records only, not executable installation. Extension projection remains
backend-only and frontend-agnostic, and must not expose source code payloads,
package bytes, raw headers, hidden reasoning, raw prompts, provider payloads,
secrets, external source metadata, or domain-specific module logic.

## Module Binding Projection

Capability Binding Registry telemetry projects staged module readiness into the
Visual Brain Projection. Generic event types include:

- `module_slot_created`
- `module_slot_archived`
- `capability_binding_created`
- `capability_binding_disabled`
- `binding_conflict_detected`
- `binding_validation_started`
- `binding_validation_completed`
- `module_mount_plan_created`
- `route_binding_preview_created`

Generic visual node types include:

- `module_slot`
- `capability_binding`
- `binding_conflict`
- `binding_validation`
- `module_mount_plan`
- `route_binding_preview`

The generic projection path is:

`extension package -> module slot -> capability binding -> validation -> mount plan`

Route preview nodes may attach after validation or mount planning. Binding
conflict nodes represent review findings, not runtime failures. Mount-plan
nodes represent non-executable future records. Route-preview nodes represent
preview metadata and must not imply registered routes.

Module binding projection remains backend-only and frontend-agnostic, and must
not expose source code payloads, package bytes, raw headers, hidden reasoning,
raw prompts, provider payloads, secrets, runtime internals, or
domain-specific module logic.

## Module Activation Projection

Module Activation telemetry projects future activation review without
activation. Generic event types include:

- `module_activation_request_created`
- `module_activation_blocker_created`
- `module_activation_blocker_dismissed`
- `module_activation_gate_started`
- `module_activation_gate_completed`
- `module_activation_plan_created`
- `runtime_registration_preview_created`
- `module_activation_review_recorded`

Generic visual node types include:

- `module_activation_request`
- `module_activation_blocker`
- `module_activation_gate`
- `module_activation_plan`
- `runtime_registration_preview`
- `module_activation_review`

The generic projection path is:

`module slot -> activation request -> gate -> blocker/review -> plan -> runtime registration preview`

Activation blocker nodes should appear blocked. Activation plan and runtime
registration preview nodes are metadata-only review artifacts and must not
imply execution, activation, or route registration.

Module activation projection remains backend-only and frontend-agnostic, and
must not expose source code payloads, package bytes, raw headers, hidden
reasoning, raw prompts, provider payloads, secrets, runtime internals, or
domain-specific module logic.

## Capability Conformance Projection

Capability Conformance telemetry projects schema-only conformance work into the
Visual Brain Projection. Generic event types include:

- `conformance_profile_created`
- `capability_test_vector_created`
- `mock_invocation_simulated`
- `conformance_run_started`
- `conformance_run_completed`
- `conformance_finding_dismissed`
- `readiness_assessment_created`

Generic visual node types include:

- `conformance_profile`
- `test_vector`
- `mock_invocation`
- `conformance_run`
- `conformance_finding`
- `readiness_assessment`

These nodes represent backend projection records only. They do not imply
package installation, route registration, capability execution, sandbox
execution, external calls, or activation.

## Golden Path Projection

Golden Path telemetry projects local end-to-end verification into the Visual
Brain Projection. It is backend projection data only and does not implement a
frontend renderer.

Generic event types include:

- `golden_path_scenario_created`
- `golden_path_fixture_pack_created`
- `golden_path_run_started`
- `golden_path_step_completed`
- `golden_path_run_completed`
- `golden_path_run_failed`
- `golden_path_run_blocked`
- `golden_path_report_created`
- `golden_path_release_smoke_completed`

Generic visual node types include:

- `golden_path_scenario`
- `golden_path_step`
- `golden_path_fixture`
- `golden_path_run`
- `golden_path_report`
- `release_smoke`

These nodes represent dry-run verification records and report readiness. They
must not imply production workload execution, external service calls, frontend
rendering behavior, source-record mutation, or automatic remediation.

## Release Candidate Projection

Release Candidate telemetry projects final readiness into the Visual Brain
Projection. It is backend projection data only and does not implement a
frontend renderer.

Generic event types include:

- `release_candidate_created`
- `verification_matrix_created`
- `rc_gate_started`
- `rc_gate_completed`
- `rc_gate_blocked`
- `rc_finding_created`
- `rc_finding_dismissed`
- `rc_evidence_pack_created`
- `rc_report_created`

Generic visual node types include:

- `release_candidate`
- `verification_matrix`
- `verification_check`
- `rc_gate`
- `rc_finding`
- `rc_report`
- `rc_evidence_pack`

These nodes represent local release-readiness evidence and review records.
They must not imply deployment, publishing, source mutation, external service
calls, or domain-specific release behavior.

## Release Handoff Projection Note

AION-079 adds no new visual node types. Demo and runbook scripts visualize
through existing setup, golden path, release smoke, release candidate, freeze,
operator, extension, module binding, and conformance telemetry.

## Model Provider Hardening Projection

AION-086 emits provider-hardening telemetry:

- `model_provider_profile_created`
- `prompt_egress_preview_created`
- `model_provider_simulation_completed`
- `model_provider_readiness_assessed`
- `model_provider_blocker_created`
- `model_provider_blocker_dismissed`

Node types include provider profiles, egress previews, simulations, readiness
records, and blockers. These visual records represent readiness and blockers
only; they do not represent provider activation or model calls.

## Operator Console Projection Note

Future console visualizations use read-only console view models, existing
visual telemetry nodes, and existing operator, release, module, provider,
notification, incident, registry, lifecycle, audit, and provenance records.

AION-088 adds backend visual telemetry vocabulary for
`operator_console_view_model_created`,
`operator_console_contract_audit_completed`, `operator_console_view`, and
`operator_console_audit`. It adds no renderer, no runtime UI, no frontend
dependencies, no activation, and no execution. Console telemetry must preserve
no raw prompt exposure, no hidden reasoning exposure, and no secret exposure.

## Operator Actions Projection Note

AION-092 emits visual telemetry for:

- `operator_action_request_created`
- `operator_action_preview_created`
- `operator_action_blocker_created`
- `operator_action_blocker_dismissed`
- `operator_action_review_recorded`

Visual node types are `operator_action_request`, `operator_action_preview`,
`operator_action_blocker`, and `operator_action_review`. The projection remains
frontend-agnostic and represents dry-run governance records only.

## Local Auth Projection Note

AION-094 emits visual telemetry for `local_auth_context_simulated`,
`local_auth_console_filtered`, and `local_auth_audit_completed`.

Node types are `local_auth_context` and `local_auth_audit`. These records
represent dev-only simulation, read-only console filtering, and safety audit
evidence. They do not represent login, production identity, sessions,
credentials, execution, activation, or external identity provider integration.

## Local Session Projection Note

AION-095 emits visual telemetry for `local_session_preview_created`,
`local_session_boundary_checked`, and `local_session_audit_completed`.

Node types are `local_session_preview` and `local_session_audit`. These records
are local-only and carry no credentials, tokens, cookies, raw prompts, hidden
reasoning, production auth state, or persisted browser session state.

## Role Access Projection Note

AION-096 emits `local_auth_role_access_audited` for role matrix audit reports.
The node type is `local_auth_role_matrix`. The payload is read-only and carries
no raw prompts, hidden reasoning, credentials, production auth state, or
privileged grants.

## Action Authorization Telemetry

AION-097 emits `dry_run_action_authorization_decided` and
`action_authorization_audit_completed`. Node types are
`action_authorization_decision` and `action_authorization_audit`. Payloads keep
write, execution, activation, and external-call flags false.

## Auth Runtime Telemetry

AION-099 emits `auth_runtime_status_checked`,
`mock_claims_preview_created`, and `auth_runtime_audit_completed`. Node types
are `auth_runtime_status`, `mock_claims_preview`, and `auth_runtime_audit`.
Payloads represent disabled runtime status and synthetic preview evidence only;
they do not represent production auth, login, credentials, tokens, cookies,
sessions, external identity calls, execution, or activation.
## Connector Runtime Telemetry

AION-108 adds visual telemetry event types for disabled connector prototype
evidence: `connector_runtime_status_checked`, `connector_manifest_validated`,
`connector_egress_preview_created`, `connector_ingress_preview_created`, and
`connector_runtime_audit_completed`.

The corresponding node types are preview/audit evidence nodes only. They do not
represent external connector calls or activation.

## Connector Policy Telemetry

AION-111 adds connector policy telemetry events for catalog reads, matrix
reads, dry-run completion, and traceability queries:

- `connector_policy_catalog_read`
- `connector_authorization_matrix_read`
- `connector_policy_dry_run_completed`
- `connector_policy_traceability_queried`

These events carry read-only policy evidence and keep runtime and external
call fields false.

## Connector Credential Telemetry

AION-113 registers connector credential boundary, lifecycle, authorization,
readiness, and redaction-preview telemetry events. Payloads contain disabled
boundary facts only and never include credential or token material.
AION-114 static connector release evidence is represented by bundled JSON demo
data for the connector release gate and safety freeze. These static panels are
read-only and do not add runtime calls, browser storage, inputs, or activation
controls.

## AION-115 Connector Checkpoint Projection

AION-115 adds bundled static connector platform checkpoint and phase closeout
demo data. These panels are read-only evidence projections only; they do not
emit runtime connector events, call external systems, store credentials or
tokens, enable sandbox execution, or add activation controls.

## AION-116 Connector Stabilization Projection

AION-116 adds bundled static connector platform stabilization and phase freeze
gate demo data. These panels are read-only evidence projections only; they do
not emit runtime connector events, call external systems, store credentials or
tokens, enable sandbox execution, add activation controls, register routes, or
execute tools.

## AION-117 Platform Integration Projection

AION-117 adds bundled static platform integration checkpoint and future runtime
boundary freeze demo data. These panels are read-only evidence projections
only; they do not emit runtime events, call external systems, store credentials
or tokens, enable production auth, enable module activation, enable sandbox
execution, register routes, or execute tools.

## AION-118 Release Candidate Projection

AION-118 adds bundled static post-v0.1 release candidate and v0.2 planning
boundary demo data. These panels are read-only evidence projections only; they
do not emit runtime events, create a release, create a v0.2 tag, move
`aion-v0.1.0`, call external systems, store credentials or tokens, enable
production auth, enable module activation, enable sandbox execution, register
routes, execute tools, or execute write paths.

## AION-119 v0.2 Planning Projection

AION-119 adds bundled static v0.2 planning charter and gate dependency matrix
demo data. These panels are read-only evidence projections only; they do not
emit runtime events, create a release, create a v0.2 tag, call external
systems, store credentials or tokens, enable production auth, enable module
activation, enable sandbox execution, register routes, execute tools, or
execute write paths.

## AION-120 v0.2 Planning Stabilization Projection

AION-120 adds bundled static v0.2 planning stabilization and implementation
readiness scorecard demo data. These panels are read-only evidence projections
only; they do not emit runtime events, approve backlog implementation, create a
release, create a v0.2 tag, call external systems, store credentials or tokens,
enable production auth, enable module activation, enable sandbox execution,
register routes, execute tools, or execute write paths.

## AION-121 v0.2 Readiness Final Review Projection

AION-121 adds bundled static v0.2 readiness final review and implementation
approval guard demo data. These panels are read-only evidence projections only;
they do not emit runtime events, approve backlog implementation, create a
release, create a v0.2 tag, call external systems, store credentials or tokens,
enable production auth, enable module activation, enable sandbox execution,
register routes, execute tools, or execute write paths.

## AION-122 v0.2 Implementation Kickoff Projection

AION-122 adds bundled static v0.2 implementation kickoff boundary and runtime
workstream lock demo data. These panels are read-only evidence projections
only; they do not emit runtime events, approve backlog implementation, bypass
approval workflow, bypass ADR dependency, bypass gate dependency, create a
release, create a v0.2 tag, call external systems, store credentials or tokens,
enable production auth, enable module activation, enable sandbox execution,
register routes, execute tools, or execute write paths.

## AION-123 v0.2 Approval Workflow Projection

AION-123 adds bundled static v0.2 approval workflow stabilization and
implementation request intake demo data. These panels are read-only evidence
projections only; they do not emit runtime events, approve backlog
implementation, bypass approval workflow, bypass ADR dependency, bypass gate
dependency, bypass approval expiry, bypass approval revocation, bypass
dual-control review, create a release, create a v0.2 tag, call external
systems, store credentials or tokens, enable production auth, enable module
activation, enable sandbox execution, register routes, execute tools, or
execute write paths.

## AION-124 v0.2 Workstream Intake Projection

AION-124 adds bundled static v0.2 workstream intake readiness and implementation
sequencing freeze demo data. These panels are read-only evidence projections
only; they do not emit runtime events, approve backlog implementation, approve
workstream implementation, bypass approval workflow, mark approval records
missing, bypass ADR dependency, bypass gate dependency, bypass approval expiry,
bypass approval revocation, bypass dual-control review, create a release,
create a v0.2 tag, call external systems, store credentials or tokens, enable
production auth, enable module activation, enable sandbox execution, register
routes, execute tools, or execute write paths.
AION-125 adds static preview data for the v0.2 pre-implementation master freeze
and final planning baseline. The visual surface remains read-only and local:
it displays bundled JSON evidence only, exposes no input controls, and keeps
runtime implementation approval, workstream implementation approval, approval
workflow bypass, external calls, credential/token storage, sandbox execution,
v0.2 tag creation, and v0.2 release creation false.

AION-126 adds static preview data for the v0.2 workstream proposal registry and
approval queue preview. The visual surface remains read-only and local: it
displays bundled JSON evidence only, exposes no input controls, and keeps the
proposal registry preview-only, the approval queue preview-only, approval
queue item approval false, runtime implementation approval false, workstream
implementation approval false, external calls false, credential/token storage
false, sandbox execution false, v0.2 tag creation false, and v0.2 release
creation false.

AION-127 adds static preview data for proposal registry stabilization and the
approval queue freeze. The visual surface remains read-only and local: it
displays bundled JSON evidence only, exposes no input controls, and keeps the
proposal registry preview-only, the approval queue preview-only, approval
queue item approval false, proposal implementation approval false, runtime
implementation approval false, workstream implementation approval false,
external calls false, credential/token storage false, sandbox execution false,
v0.2 tag creation false, and v0.2 release creation false.

AION-128 adds static preview data for the planning master checkpoint and
implementation lock freeze. The visual surface remains read-only and local: it
displays bundled JSON evidence only, exposes no input controls, and keeps the
proposal registry preview-only, the approval queue preview-only, approval
queue item approval false, proposal implementation approval false, runtime
implementation approval false, backlog implementation approval false,
workstream implementation approval false, external calls false,
credential/token storage false, sandbox execution false, v0.2 tag creation
false, and v0.2 release creation false.

## AION-129 Static Console Preview

The static console now includes final planning release gate and
no-implementation freeze preview data. The panels are read-only, redacted,
synthetic, and local. They expose no inputs, no write controls, no release
controls, no tag controls, no approval controls, no runtime controls, no
external calls, no credentials/tokens, and no sandbox execution.

## AION-132 Static Console Preview

The static console now includes request pack stabilization and evidence
completeness gate preview data. The panels are read-only, redacted, synthetic,
and local. They expose no inputs, no write controls, no release controls, no
tag controls, no approval controls, no runtime controls, no external calls, no
credentials/tokens, and no sandbox execution.

## AION-133 Static Console Preview

The static console now includes request pack final review and pre-approval
submission gate preview data. The panels are read-only, redacted, synthetic,
and local. They expose no inputs, no write controls, no release controls, no
tag controls, no approval controls, no runtime controls, no external calls, no
credentials/tokens, and no sandbox execution.

## AION-130 Static Console Preview

The static console now includes planning track closeout and governance handoff
pack preview data. The panels are read-only, redacted, synthetic, and local.
They expose no inputs, no write controls, no release controls, no tag controls,
no approval controls, no runtime controls, no external calls, no
credentials/tokens, and no sandbox execution.

## AION-131 Static Console Preview

The static console now includes implementation request pack and proposal
submission template preview data. The panels are read-only, redacted,
synthetic, and local. They expose no inputs, no write controls, no release
controls, no tag controls, no approval controls, no runtime controls, no
external calls, no credentials/tokens, and no sandbox execution.

## AION-134 Static Console Preview

The static console now includes submission registry preview and pre-approval
queue boundary preview data. The panels are read-only, redacted, synthetic,
and local. They expose no inputs, no write controls, no release controls, no
tag controls, no approval controls, no runtime controls, no external calls, no
credentials/tokens, and no sandbox execution.

## AION-135 Static Evidence Panels

The static visual brain includes AION-135 submission registry stabilization and
pre-approval queue freeze panels backed by bundled JSON. The panels remain
read-only, redacted, and non-executing. They present planning evidence,
blockers, warnings, and false approval states only; they do not expose inputs,
write controls, activation controls, external-call controls, credential
storage, token storage, sandbox execution, a v0.2 tag, or a v0.2 release.

## AION-136 Review Board Panels

The static visual brain now includes AION-136 pre-approval review board and
submission review routing panels backed by bundled JSON. The panels remain
read-only, redacted, and non-executing. They expose reviewer routing,
decision-readiness blockers, and false approval states only; they do not expose
inputs, write controls, activation controls, external-call controls,
credential/token storage, sandbox execution, a v0.2 tag, or a v0.2 release.

## AION-137 Review Board Stabilization Panels

The static visual brain includes AION-137 review board stabilization and review
routing freeze panels backed by bundled JSON. The panels remain read-only,
redacted, and non-executing. They expose routing freeze evidence, quorum
evidence, decision-readiness blockers, and false approval states only; they do
not expose inputs, write controls, activation controls, external-call controls,
credential/token storage, sandbox execution, a v0.2 tag, or a v0.2 release.

## AION-138 Decision Package Panels

The static visual brain includes AION-138 decision package preview and approval
readiness evidence panels backed by bundled JSON. The panels remain read-only,
redacted, and non-executing. They expose decision package completeness,
approval-readiness evidence, runtime boundary blockers, and false approval
states only; they do not expose inputs, write controls, approval controls,
activation controls, external-call controls, credential/token storage, sandbox
execution, a v0.2 tag, or a v0.2 release.

## AION-139 Decision Package Stabilization Panels

The static visual brain includes AION-139 decision package stabilization and
approval readiness freeze panels backed by bundled JSON. The panels remain
read-only, redacted, and non-executing. They expose stabilization status,
approval readiness freeze status, runtime decision readiness false, and
closeout blockers only; they do not expose inputs, write controls, approval
controls, activation controls, external-call controls, credential/token
storage, sandbox execution, runtime decision approval, a v0.2 tag, or a v0.2
release.

## AION-140 Decision Package Final Review Panels

The static visual brain includes AION-140 decision package final review and
runtime decision lock panels backed by bundled JSON. The panels remain
read-only, redacted, and non-executing. They expose final review status,
approval readiness closeout status, runtime decision lock release approval
false, runtime decision readiness approval false, and release blockers only;
they do not expose inputs, write controls, approval controls, activation
controls, external-call controls, credential/token storage, sandbox execution,
runtime enablement, a v0.2 tag, or a v0.2 release.

## AION-141 Approval Docket Preview Panels

The static visual brain includes AION-141 approval docket preview and
implementation decision record guard panels backed by bundled JSON. The panels
remain read-only, redacted, and non-executing. They expose approval docket
preview status, implementation decision record guard status, runtime approval
review approval false, approval docket item approval false, implementation
decision record approval false, and release blockers only; they do not expose
inputs, write controls, approval controls, activation controls,
external-call controls, credential/token storage, sandbox execution, runtime
enablement, a v0.2 tag, or a v0.2 release.

## AION-142 Approval Docket Stabilization Panels

The static visual brain includes AION-142 approval docket stabilization and
implementation decision record freeze panels backed by bundled JSON. The
panels remain read-only, redacted, and non-executing. They expose approval
docket stabilization status, implementation decision record freeze status,
runtime approval review evidence status, approval docket stabilization approval
false, implementation decision record freeze approval false, runtime approval
review approval false, and release blockers only; they do not expose inputs,
write controls, approval controls, activation controls, external-call
controls, credential/token storage, sandbox execution, runtime enablement, a
v0.2 tag, or a v0.2 release.

## AION-143 Approval Docket Final Review Panels

The static visual brain includes AION-143 approval docket final review and
runtime approval lock panels backed by bundled JSON. The panels remain
read-only, redacted, and non-executing. They expose final review status,
implementation decision record closeout status, runtime approval lock release
approval false, runtime approval review approval false, approval docket item
approval false, and release blockers only; they do not expose inputs, write
controls, approval controls, activation controls, external-call controls,
credential/token storage, sandbox execution, runtime enablement, a v0.2 tag, or
a v0.2 release.

## AION-144 Static Runtime Approval Board Preview

The visual brain surface adds read-only panels for the runtime approval board
preview and implementation go/no-go ledger boundary. These panels show board
preview created, vote record created, ledger created, and implementation no-go
status only. They do not expose approval controls, runtime controls, activation
controls, external-call controls, credential/token storage, sandbox execution,
a v0.2 tag, or a v0.2 release.

## AION-145 Static Runtime Approval Board Stabilization

The visual brain surface adds read-only panels for runtime approval board
stabilization and approval vote record freeze. These panels show board
stabilized, board preview-only, vote record created, ledger created,
implementation no-go status, and approval/runtime flags locked false. They do
not expose approval controls, runtime controls, activation controls,
external-call controls, credential/token storage, sandbox execution, a v0.2
tag, or a v0.2 release.


## AION-146 Static Runtime Approval Board Final Review

The visual brain surface adds read-only panels for runtime approval board final
review and implementation go/no-go ledger final lock. These panels show final
review passed, board preview-only, vote record created, ledger final lock
created, implementation no-go status, implementation go final approval false,
and approval/runtime flags locked false. They do not expose approval controls,
runtime controls, activation controls, external-call controls,
credential/token storage, sandbox execution, a v0.2 tag, or a v0.2 release.

## AION-147 Static Implementation Authorization Preview

The visual brain surface adds read-only panels for implementation authorization
preview and runtime enablement guard boundary. These panels show authorization
preview created, explicit approval record created, runtime guard created,
implementation authorization approval false, explicit approval record approval
false, runtime enablement guard release approval false, implementation go
status false, and approval/runtime flags locked false. They do not expose
approval controls, runtime controls, activation controls, external-call
controls, credential/token storage, sandbox execution, a v0.2 tag, or a v0.2
release.

## AION-148 Implementation Authorization Stabilization

AION-148 freezes the implementation authorization preview, explicit approval
record schema, and runtime enablement guard boundary into a stable evidence
baseline. It remains non-approving: `implementation_authorization_preview_only=true`,
`implementation_authorization_approved=false`,
`implementation_authorization_stabilization_approval=false`,
`explicit_approval_record_approval=false`,
`explicit_approval_record_freeze_approval=false`,
`runtime_enablement_guard_release_approved=false`,
`runtime_approval_board_decision_approved=false`, `implementation_go_status=false`,
and `runtime_implementation_approved=false`. No v0.2 tag or release is created.

## AION-149 Implementation Authorization Final Review

Visual Brain surfaces AION-149 as read-only final authorization evidence. It may
display final review, explicit approval record closeout, and runtime guard final
lock status, but it must not expose runtime controls, approval controls, write
execution, connector execution, credential/token storage, sandbox execution,
external calls, package installation, migrations, or release/tag controls.
## AION-150 Authorization Track Closeout

AION-150 adds static-console preview data for the authorization track closeout and runtime enablement master lock. The visual layer remains read-only and synthetic, displaying blocked approval states and closeout evidence without interactive runtime controls.

The console may show `authorization_governance_baseline_complete=true` and `runtime_enablement_master_lock_created=true`, but it must continue to show `runtime_enablement_master_lock_release_approved=false`, `runtime_enablement_guard_release_approved=false`, `implementation_go_status=false`, and `implementation_no_go_status=true`.

## AION-151 Scoped Production Auth Authorization

AION-151 adds the canonical scoped authorization transaction `AION-151-PA-0001` for `production-auth-core` and future task `AION-152`. The authorization is limited to the `disabled-production-auth-core` implementation scope. Production-auth runtime remains disabled, runtime guard releases remain false, endpoint/storage/provider/external-call approvals remain false, package and migration changes remain false, and no v0.2 tag or release is created.

## AION-154 Production Auth Stabilization Evidence

The visual brain may render read-only AION-154 production-auth stabilization
evidence from static demo data. It must treat fingerprints, schema versions,
reason codes, and stabilization lineage as evidence only. It must keep
`production_auth_runtime_enabled=false`, `runtime_no_go_status=true`, no public
production-auth routes, no external identity provider, no credentials or tokens,
and no v0.2 tag or release.

## AION-155 Request Boundary Authorization Evidence

The visual brain may render read-only AION-155 authorization evidence for
`AION-155-PA-0003`. The evidence is synthetic and local. It may show that
future AION-156 request identity boundary work is authorized, but it must also
show that identity verification, authenticated requests, header/cookie parsing,
protected-material handling, provider integration, external calls, runtime API
routes, SDK/CLI runtime surfaces, v0.2 tags, and v0.2 releases remain disabled
or absent.
# AION-156 Static Evidence Note

Static console evidence for the request identity boundary is bundled as JSON
only. It is read-only and does not call the backend, accept credentials, accept
tokens, parse headers, authenticate users, or expose an enable control.

## AION-157 Static Stabilization Authorization Evidence

The visual brain may render read-only AION-157 evidence for
`AION-157-PA-0004`. The panel is synthetic and local-only. It may show future
AION-158 stabilization permissions for pure ASGI migration, middleware order,
streaming preservation, request-body preservation, cancellation and disconnect
handling, non-HTTP bypass, request-state integrity, duplicate registration,
concurrency, state-leakage regression, evidence idempotency, diagnostic
hardening, and performance smoke tests.

The visual surface must still show identity verification, authenticated
requests, header and cookie parsing, protected-material handling, providers,
external calls, runtime routes, OpenAPI security, SDK/CLI runtime surfaces,
packages, lockfiles, migrations, tags, and releases as false or absent.

## AION-159 Actor Context Evidence

Static and visual evidence may show `AION-159-PA-0005` as the active
authorization for AION-160. It must also show `AION-157-PA-0004` as consumed
by AION-158 PR 68 and keep actor-context remediation, runtime authentication,
identity verification, authenticated requests, production header trust,
protected-material handling, providers, external calls, packages, migrations,
tags, and releases in a no-go state until AION-160 lands.

## AION-161 Offline Identity Assertion Evidence

Static and visual evidence may now show `AION-159-PA-0005` as consumed by
AION-160 PR 70 and `AION-161-PA-0006` as the active authorization for
AION-162. The visual surface must remain read-only and must show request
authentication, ActorContext application, RequestIdentityContext application,
runtime private keys, provider networking, replay cache, endpoints, SDK/CLI
runtime surfaces, tags, and releases as blocked.
## AION-162 Static Evidence Projection

The static console can project AION-162 bundled evidence from
`operator-console-static/demo-data/offline-identity-assertion-verification.json`
and `operator-console-static/demo-data/offline-identity-assertion-runtime-hold.json`.

The projection is read-only. It may show the implemented unintegrated verifier,
fixed Ed25519 semantics, public-key registry status, replay-protection absence,
and runtime no-go state. It must not accept assertions, signatures, public keys,
or signing material and must not verify live identities or authenticate
requests.


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
## AION-164 Static Evidence

The static console includes synthetic read-only replay-protection and runtime-hold evidence. These panels show replay readiness and no-go state only; they do not enable runtime authentication or request integration.

## AION-177 Shadow-Mode Static Evidence

The static console can display AION-177 shadow-mode authorization and runtime
hold evidence from synthetic local JSON files. The view is read-only and
operator-facing. It does not activate shadow mode, call an API, execute actions,
create approvals, create pull requests, merge, deploy, or expose provider or
connector payloads.
## AION-178 Static Evidence

The static console may display bundled AION-178 shadow evidence from local demo
JSON. It does not call the backend, run a shadow pipeline, load live traces,
edit source, call Git, create approvals, create pull requests, merge, deploy,
or promote candidates.
## AION-180 Shadow Activation Evidence View

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.

The static console may project the authorization and runtime hold as read-only evidence only.

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

Historical AION-181 note: at implementation time, AION-180-SI-0007 remained active pending the later AION-182 closeout. AION-182 subsequently closed that authorization as consumed, expired, and non-reusable; actual activation still requires a separate future authorization.

## AION-182 Shadow Activation Evaluation Closeout

AION-182 records `AION-SACE-001` with decision `SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW`. The AION-181 control plane is implemented, evaluated, and disabled. `AION-180-SI-0007` is closed, consumed by AION-181 PR #92, expired, and non-reusable.

No implementation authorization, activation approval, actual activation, source mutation, Git mutation, real control-plane PR, merge, promotion, canary, deployment, model training, provider call, connector call, network call, v0.2 tag, or v0.2 release is created by AION-182.

## AION-203 Cognitive Architecture Program Closeout

AION-203 records `AION-CASE-001` with decision `CONTROLLED_LOCAL_OFFLINE_PILOT_PASS_COMPLETE_COGNITIVE_ARCHITECTURE_PROGRAM`. The AION Cognitive Architecture Program is complete: persistent cognitive state, predictive world model, global cognitive workspace, memory consolidation, hierarchical counterfactual planning, active information acquisition, governed continual learning, integrated cognitive shadow runtime, and the controlled local-offline cognitive pilot are available as governed evidence. Production cognitive runtime, production event subscription, unrestricted network access, source rewriting, automatic merge, production canary, production deployment, and model-weight training remain disabled.

## AION-204 Knowledge Intelligence Program Authorization

AION-204 creates `AION-KNOWLEDGE-INTELLIGENCE-001` and `AION-204-KI-0001` as the sole active Knowledge Intelligence implementation authorization for AION-205. The authorized scope is `disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core`. Research plane authorized=true, research plane implemented=false, research runtime enabled=false, network access enabled=false, background crawler enabled=false, automatic knowledge promotion enabled=false, cognitive belief mutation enabled=false, source mutation enabled=false, Git mutation enabled=false, production exposure=false, and model-weight training enabled=false. AION-206 is the formal closeout task.

## AION-205 Controlled Research Acquisition Core

AION-205 implements the controlled research acquisition and immutable source-snapshot core as operator-invoked and runtime-disabled. Acquired content remains untrusted evidence; factual claim verification, knowledge promotion, cognitive belief mutation, public network fetch, crawler execution, search-provider integration, connector integration, source mutation, Git mutation, automatic merge, deployment, and model-weight training remain disabled. AION-204-KI-0001 remains active pending AION-206 closeout.
