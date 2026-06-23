# Architecture

AION Brain is the first layer of AION OS. It is a domain-neutral cognitive
kernel that defines how events become intents, how context is assembled, how
memory is consulted, how plans are checked, and how outcomes are traced.

## Brain-Only Scope

The core does not contain finance, trading, IT automation, legal, healthcare,
business workflow, or other vertical behavior. Future modules can register
capabilities, but AION Brain only sees capability contracts and policy inputs.

## Core Brain Loop

```text
Event -> Intent -> Context -> Reasoning -> Plan -> Policy -> Trace -> Evaluate -> Learn -> Telemetry
```

In v0.1 the loop is deterministic. It creates intent, compiles context, runs
local deterministic reasoning, plans, checks policy, persists a trace, evaluates
the trace, creates a candidate learning signal, and emits visual telemetry
without external LLM calls, real capability execution, external calls, or domain
side effects.

## Subsystems

- Event intake normalizes every external signal as an AION event.
- Contracts define public Brain data shapes.
- Runtime adapters isolate future orchestration engines.
- Memory adapters isolate semantic and graph memory implementations.
- Reasoning adapters isolate model gateway providers.
- Capability adapters isolate external tools and optional MCP interoperability.
- Module runtime adapters isolate where capabilities may execute.
- Policy adapters gate decisions before execution.
- Execution orchestrators coordinate allowed actions.
- The lifecycle control plane owns goals, cognitive tasks, task runs, schedule
  metadata, and lifecycle events.
- Learning records candidate signals without uncontrolled self-modification.
- Audit records preserve traceable decisions and outcomes.

## Adapter-First Architecture

Every external system is behind an adapter. AION public APIs expose AION
contracts, not LangGraph, pgvector, MCP, LiteLLM, or other framework-specific
objects. This keeps AION in control of its contract surface.

AION Brain public contracts must not depend on vendor-specific infrastructure
clients.

## Infrastructure Boundaries

Postgres, Redis, NATS, and Open Policy Agent are checked through
`aion_brain.infra` readiness boundaries. These modules may use vendor clients
internally, but API routes and Brain contracts expose only stable AION-owned
JSON states such as `ok`, `fail`, `ready`, and `degraded`.

## Event Intake and Ledger

`POST /brain/events` is the first intake boundary for AION Brain. It accepts
only `AIONEvent`, generates missing trace and correlation IDs, persists the
event to the canonical Postgres event ledger, and then publishes the accepted
event to NATS on `aion.events.<event_type>`.

Persistence is mandatory. Publication is best-effort: NATS failure is logged and
reported as `published: false`, but it does not erase the persisted event.

## Event Reaction Router

The Event Reaction Router is the subscription control plane for events that are
already normalized as `AIONEvent`. It stores generic event subscriptions,
matches persisted events with deterministic source filters, wildcard suffix
event patterns, and safe dotted-path trigger rules, then writes dispatch,
action, and dead-letter records.

The router is not a background consumer in v0.1. Automatic dispatch from event
intake is disabled by default and must be explicitly enabled. Manual dispatch
through `/brain/event-router/dispatch` is the default local testing path.

Every dispatch passes policy and autonomy before matching can produce actions.
Each matched action then passes policy, risk, and approval gates. Dry-run mode
creates auditable planned actions without side effects. Controlled mode remains
inside Brain-owned action boundaries: attention signals, interrupts, tasks,
workflow dry-runs, cognitive-cycle dry-runs, memory governance evaluation,
capability dry-runs, trace attachment when supported, or noop.

Dead letters preserve failed controlled actions for inspection and bounded,
policy-gated replay. Replay uses dry-run by default and does not run a
background loop.

## Memory Design

Memory is policy-bound. The Brain decides scope, sensitivity, retention, and
promotion rules. Storage engines are implementation details behind adapters.

Memory Fabric v0.1 stores canonical `MemoryRecord` metadata in Postgres and uses
deterministic lexical recall plus semantic recall through adapter boundaries.
pgvector is the default local semantic baseline. TurboVec is an optional
compressed semantic recall adapter that is disabled by default and loaded only
through `aion_brain.memory.turbovec_compat`. Vector engines provide recall only
and must not replace Postgres as the canonical metadata and audit source.

TurboVec index metadata is persisted separately from canonical memory. The
kernel can select TurboVec when explicitly configured, fall open to pgvector
when the package is unavailable and fallback is enabled, or fail closed when
fallback is disabled. Public APIs still return AION-owned contracts only.

Temporal graph memory stores generic nodes and edges in Postgres through
`GraphMemoryAdapter`. It captures relationships, temporal validity,
provenance, confidence, sensitivity, and scope without domain-specific graph
logic. Graphiti is an optional adapter behind the same boundary. It is disabled
by default, selected only through configuration, and may fall open to Postgres
graph memory when unavailable. Direct Graphiti imports are restricted to
`memory/graphiti_compat.py`, and public APIs return only AION-owned graph
contracts.

## Retrieval Router and Context Fusion

The Retrieval Router sits between Memory Fabric and the Context Compiler. It
collects lexical memory, semantic memory, graph memory, capability declarations,
active procedural skills, and optional trace candidates through services and
adapter boundaries. Each candidate becomes a Brain-owned `RetrievedContextItem`.

Retrieval is policy-gated per source. Memory sources use `memory.retrieve`,
capabilities use `capability.list`, skills use `skill.match`, and recent traces
use `trace.read`. A blocked source becomes a constraint and does not stop other
allowed sources. Unavailable sources also become constraints, so retrieval
failures do not crash context compilation.

Deterministic ranking exists before LLM reasoning so AION can control context
quality without relying on model-side filtering. Scores combine base relevance,
confidence, lexical overlap, recency, and source weight. No domain-specific
ranking logic exists in Brain core.

The Context Fusion Engine turns a `RetrievalResult` into a `ContextBundle`.
Fusion deduplicates content, respects item and character limits, preserves
references, and builds a deterministic plain-text summary without LLM calls.
The Context Compiler consumes that bundle to create the final `ContextPacket`.

Selected retrieval items emit visual telemetry. Memory candidates activate
memory nodes, skill candidates pulse procedural memory nodes, capability
candidates mark capability nodes, and trace candidates mark trace nodes. This
makes retrieval visible to the future Brain map.

## Memory Governance Layer

The Memory Governance layer controls memory lifecycle before recall can become
context. It owns generic retention rules, governance decisions, decay records,
forget requests, conflict records, compaction runs, and compacted-record links.

Governance is evaluated after policy authorization and before memory write or
retrieval results are accepted. Semantic and graph engines remain recall
engines only; they may return candidates, but AION governance decides whether
those candidates can be stored, recalled, decayed, expired, forgotten, flagged,
or compacted.

For v0.1, governance is deterministic and domain-neutral:

- write gates decide whether a `MemoryRecord` can be stored.
- retrieval gates can filter unsafe or expired recall.
- decay scoring reduces stale, low-confidence, or weakly grounded memory.
- retention sweeps annotate or expire memory without hard deletion.
- forgetting requests pass through policy, risk, and approval before soft
  deletion of memory-owned targets.
- conflict scanning detects duplicates, metadata disagreements, stale
  preferences, competing procedures, and scope conflicts generically.
- compaction merges low-level records into deterministic semantic,
  procedural, or preference summaries without model calls.

Postgres remains canonical for memory metadata and governance ledgers. Evidence
records and chunks are preserved by default; forgetting an evidence link removes
the relationship, not the source evidence. Context compilation receives
governance constraints from retrieval and must preserve them in the reasoning
packet.

## Capability Registry

Future modules register capability manifests. AION Brain reads capability IDs,
schemas, permissions, memory scopes, events, risk, and execution modes. It does
not inspect or embed module internals.

## Contract Registry and Interface Drift

The Contract Registry is the local index of AION public and operator-facing
interfaces. It inventories Pydantic contracts, FastAPI routes, SDK resources,
CLI commands, OPA policy actions, environment settings, visual telemetry
vocabulary, and registry resource types through deterministic scanners.

Snapshots preserve point-in-time manifests and root hashes. Compatibility scans
compare baseline and candidate snapshots with generic rules such as no removed
routes, no removed SDK methods, no removed CLI commands, no removed policy
actions, no removed settings, no removed telemetry events, no required-field
additions, no visibility leaks, no secret schema, and no domain drift.

The registry is advisory. It writes registry records, drift findings, migration
notes, reports, audit/provenance events, visual telemetry, resource descriptors,
operator queues, release-package summaries, and freeze-gate checks. It never
mutates source records, generates code, repairs interfaces, executes migration
steps, or calls external systems. Source code remains the source of truth.

## First-Run Bootstrap and Setup Doctor

The First-Run Bootstrap layer prepares local Brain readiness only. It owns
bootstrap profiles, seed bundles, seed execution records, setup findings,
bootstrap runs, and setup reports. It uses existing services to seed local
default metadata idempotently and remains dry-run by default.

The Setup Doctor inspects local configuration, service assembly, policy
availability, SDK/CLI availability, scripts, golden path readiness, release
smoke readiness, and unsafe feature flags. It creates setup findings and setup
reports but does not install packages, create credentials, call external
services, execute tools, mutate source code, or provision production resources.

Bootstrap integrates with Operator Control Tower, Visual Brain telemetry,
audit/provenance, release-package summaries, and optional freeze-gate checks.
Freeze gates only require bootstrap readiness when the request metadata
explicitly asks for it.

## Module Bus and Runtime Gateway

The Module Bus adds the controlled runtime boundary that sits after the
Capability Registry. The registry stores what can be done. `ModuleRuntime`
records store where and how a module can be reached. `CapabilityRuntimeBinding`
connects a capability ID to a runtime for a specific invocation mode.

All capability invocation flows through `CapabilityRuntimeGateway`. The Brain
never calls module code, MCP servers, HTTP endpoints, shell commands, browser
drivers, SaaS APIs, or vendor SDKs directly. The gateway owns policy checks,
binding lookup, runtime health status, dry-run short-circuiting, adapter
selection, telemetry semantics, and provider-neutral invocation results.

Runtime health checks are persisted as `ModuleHealthCheck` records and update
runtime health status. Unhealthy runtimes fail closed before invocation.

v0.1 supports only the safe `local_internal` runtime for ordinary controlled
execution of generic internal capabilities. `local_stub` is healthy but returns
`not_implemented`. HTTP remains a placeholder. MCP is available as an optional,
disabled-by-default runtime boundary that can dry-run mapped tools safely and
can only perform controlled fake in-memory invocation when explicitly enabled
for tests or local demos.

## MCP Capability Protocol Adapter

MCP is an interoperability protocol boundary, not AION's governance contract.
AION Capability Manifest remains the internal source of risk, permissions,
memory scope, execution mode, audit level, and policy semantics. MCP tools may
be discovered and mapped into AION capabilities, but they do not self-authorize
or define Brain behavior.

`MCPCompat` is the only place that may dynamically import the MCP SDK. Public
Brain APIs never expose MCP clients, sessions, transports, prompts, resources,
or raw SDK objects. The architecture boundary checker fails any direct MCP
import outside `aion_brain/mcp/compat.py`.

MCP is disabled by default. With `AION_MCP_ENABLED=false`, real HTTP, SSE, and
stdio transports cannot be used. Network transports additionally require
`AION_MCP_ALLOW_NETWORK=true`; stdio additionally requires
`AION_MCP_ALLOW_STDIO=true`. Stdio configuration rejects shell control
characters, and MCP config rejects secret-like keys. Normal tests do not
require the MCP SDK, do not perform network calls, and do not execute shell
commands.

The adapter owns policy-gated server registration, health checks, tool sync,
mapping reads, and invocation records. Dry-run invocation returns a structured
AION result without calling MCP. Controlled invocation requires MCP to be
enabled, policy to allow `mcp.tool.invoke`, required permissions to be present,
transport safety checks to pass, and approval for higher risk mappings. In
v0.1, controlled execution is exercised only through the deterministic
`in_memory_fake` server.

## Context Compiler and Planner

The Context Compiler builds the exact reasoning packet for the runtime. It calls
the Retrieval Router, fuses the `RetrievalResult` into a `ContextBundle`, then
joins event, intent, retrieved refs, available capabilities, graph refs, policy
constraints, and execution limits into a `ContextPacket`. This prevents context
pollution by keeping raw external signals, memory recall, and capability
declarations inside explicit Brain-owned fields.

The deterministic Planner converts a `ContextPacket` into a generic `PlanGraph`.
Plan steps use generic action identifiers such as `memory.retrieve`,
`plan.create`, `response.draft`, and `clarification.ask`. The planner does not
embed vertical workflow logic or domain-specific capability names.

Active skills may be supplied to the planner as matched procedural memory. The
planner records matched skill IDs in plan metadata only. It does not execute
skill steps, replace plan steps with skill steps, or treat skills as code.

## Internal Notification Center

The Internal Notification Center is the local operator-awareness layer for AION
Brain. It stores notification topics, local subscriptions, delivered
notifications, alerts, escalation records, and deterministic digests. It is
backend-only and local-only in v0.1.

Notifications are generated from AION contracts and source records. The alert
router can create local `AlertRecord` objects for high and critical signals,
but it does not remediate, acknowledge, resolve, retry, cancel, resume, or
mutate the source subsystem. Escalation records are local queue items only and
set `external_delivery=false`.

The notification boundary is policy-gated and redacts hidden reasoning, raw
prompts, raw headers, provider payload markers, and secret-like keys before
persistence or display. It emits visual telemetry for future Brain Map
projection while remaining independent of frontend rendering and external
notification vendors.

## Reasoning Mesh

The Reasoning Mesh is the only Brain core path for generic reasoning. It
receives `ReasoningRequest`, builds `PromptPacket`, asks `ModelRouter` for a
`ModelRouteDecision`, calls `ModelGatewayAdapter`, converts the provider-neutral
`ModelCallRecord` into `ReasoningResult`, and persists both reasoning and model
call ledger records.

v0.1 uses `DeterministicReasoningAdapter` only. The selected route is always
`aion-local` / `deterministic-reasoner-v0`, so reasoning is stable, local, and
free of external model calls. LiteLLM remains a placeholder behind
`ModelGatewayAdapter`; it is not imported or called.

Reasoning is policy-gated through generic actions: `reasoning.run`,
`model.route`, `model.complete`, and future `response.verify`. Unknown providers
fail closed, and high or critical reasoning requires approval.

AION public contracts must never expose provider-specific SDK objects,
LangGraph objects, LiteLLM objects, OpenAI objects, Anthropic objects, Gemini
objects, or local model runtime objects.

## Brain Runtime

`BrainRuntimeAdapter` owns the public runtime boundary:

```text
AIONEvent -> DecisionTrace
```

The first implementation is `LangGraphRuntimeAdapter`. LangGraph is used only to
coordinate private runtime nodes: classify intent, compile context, run
reasoning, create plan, authorize plan, and create trace. AION public contracts,
APIs, and docs must not expose LangGraph objects.

The runtime reports `execution_ready` and `/brain/execute` in trace outcomes
when a plan is available for explicit execution. It does not execute plans.

## Execution Orchestrator

Execution is separate from thinking. `POST /brain/think` reasons and plans;
`POST /brain/execute` explicitly executes a supplied `PlanGraph` through
`ExecutionOrchestrator`.

The orchestrator owns the plan step state machine, approval checkpoints, retry
semantics, audit records, policy gates, and telemetry semantics. It persists
`ExecutionRun`, `ExecutionStepRun`, `ApprovalCheckpoint`, and
`CapabilityInvocationRecord` contracts in Postgres.

`dry_run` is the default execution mode. It validates policy and marks steps
completed with a side-effect-free dry-run message. `controlled` mode executes
only safe internal generic Brain steps such as context retrieval, response
drafting, evaluation, capability listing, and clarification. No shell, browser,
external tool, model provider, or domain module is executed in v0.1.

High and critical steps create approval checkpoints when approval is absent.
Registered capabilities are not automatically executable. Capability invocation
goes through `CapabilityInvoker`, then `CapabilityRuntimeGateway`, then an
AION-owned runtime adapter. Dry-run capability steps never call runtime
adapters. Controlled capability steps can invoke only the safe generic
`local_internal` runtime in v0.1.

Temporal is planned as a durable workflow adapter behind
`ExecutionAdapter`. AION public APIs must never expose Temporal, MCP, shell,
browser, provider, or workflow-engine objects.

## Goal Manager and Cognitive Task Queue

AION Brain owns goal and task lifecycle state. Future modules may request
lifecycle changes through events or capability contracts, but no module may own
the Brain's lifecycle state.

`GoalRecord` stores a generic objective over time. `CognitiveTask` stores a
generic task linked to a goal, trace, plan, or execution. `TaskRunRecord`
captures explicit task run attempts. `ScheduleRecord` stores scheduling
metadata only.

Goal transitions are constrained by the Brain-owned lifecycle state machine:
proposed goals can become active, paused, cancelled, or failed; active goals can
be paused, completed, cancelled, or failed; paused goals can resume, cancel, or
fail. Task transitions are similarly constrained from proposed to queued or
cancelled, then running, waiting for approval, blocked, completed, cancelled, or
failed.

Task runs are explicit and policy-gated through `task.run`. `dry_run` validates
and records the task without external side effects. `controlled` mode remains
limited to generic internal Brain task types and never runs shell commands,
browser drivers, SaaS APIs, external modules, or domain workflows in v0.1.

Lifecycle events are persisted and published to NATS subjects under
`aion.lifecycle.*`. Publication failure is best-effort and never undoes
canonical persistence. Visual telemetry emits generic goal, task, task-run, and
schedule activity for the future Brain graph.

Schedules are metadata only. There is no scheduler loop, worker process, or
Temporal integration in v0.1. Temporal remains a future durable scheduling
adapter behind an AION-owned boundary.

`/brain/think` advertises goal and task creation endpoints in the trace outcome.
It creates proposed lifecycle records only when the event payload explicitly
sets `create_goal: true` or `create_task: true`.

## Identity, Workspace, and Scope Control Plane

AION Brain owns local development identity metadata before production
authentication exists. `ActorRecord`, `WorkspaceRecord`,
`WorkspaceMembership`, and `PermissionGrant` describe who is acting, where the
action is happening, which workspace role is active, and which generic
permissions have been granted or denied.

v0.1 identity is local development metadata and header-based dev context.
Production authentication is deferred. The dev context reads only `X-AION-*`
headers and can synthesize a default local owner when `AION_ENV=development`
and `AION_DEV_AUTH_ENABLED=true`. It never reads cookies, bearer tokens, OAuth
state, SSO state, or external identity provider state.

The Scope Resolver joins actor context, workspace membership, role grants,
actor grants, workspace grants, requested scopes, resource type, and resource
ID into `ScopeResolution`. Deny grants override allow grants. Disabled actors
block resolution. Archived workspaces block normal activity, with only narrow
development read exceptions for trace and policy diagnostics.

Policy input enrichment attaches actor context, roles, permissions, resolved
security scope, workspace ID, and dev-mode state to generic `PolicyRequest`
objects. Event intake, memory retrieval, and the Brain loop can carry actor,
workspace, trace, correlation, and security-scope metadata forward without
changing their public contracts.

Identity and scope lifecycle operations emit visual telemetry events:
`actor_created`, `actor_disabled`, `workspace_created`, `workspace_archived`,
`membership_created`, `membership_revoked`, `permission_granted`,
`permission_revoked`, and `scope_resolved`.

## Evidence Vault and Source Grounding

The Evidence Vault is the grounding layer beneath memory and reasoning. AION
Memory may recall. AION Evidence must ground. AION Brain must never treat vector
memory, graph memory, or model output as truth without evidence linkage.

`EvidenceRecord` stores source metadata, source type, owner scope, sensitivity,
confidence, content hash, and content reference. `EvidenceChunk` stores
deterministic text chunks for lexical evidence search. `EvidenceLink` connects
source material to Brain-owned targets such as memories, traces, plans,
executions, skills, evaluations, and learning signals. `GroundingClaim`
records deterministic source support for statements.

Content addressing is owned by AION. Text hashes normalize line endings and
trailing whitespace before SHA-256 hashing. v0.1 supports text evidence and
metadata-only content references. It does not fetch URLs, parse PDFs, run OCR,
or process binary uploads.

Evidence search is policy-gated through `evidence.search` and uses
deterministic lexical overlap, title and summary overlap, confidence, and
recency. Grounding is deterministic: supported claims require evidence chunk
overlap; insufficient evidence remains explicit and is not upgraded into truth.

Object storage is an adapter boundary. Local object storage and in-memory
storage are available for future byte storage paths. MinIO remains a future
S3-compatible adapter placeholder and is not imported in v0.1.

## Policy-Gated Execution

Every plan and action passes through policy. Modules never self-authorize.
Policy can deny an action, allow it, constrain it, or require approval.

`POST /brain/policy/authorize` is the first public authorization boundary. It
accepts generic `PolicyRequest` contracts and returns `PolicyDecision`
contracts. The OPA adapter owns vendor-specific REST calls and fails closed when
OPA is unavailable.

## Risk, Guardrails, and Approvals

The Risk Engine turns a generic requested action into a persisted
`RiskAssessment`. It uses deterministic factors such as requested risk,
controlled execution, external effects, model use, MCP use, data deletion, and
approval presence. It emits visual telemetry but never executes the action it
scores.

The Guardrail Engine evaluates generic `GuardrailRule` records against the risk
assessment. Rules can allow, require approval, or block. Default rules are
domain-neutral and cover critical risk, controlled execution, external effects,
secret-like payload signals, external model use, MCP use, and skill activation
effects. Guardrail failures fail closed and persist a `GuardrailDecision`.

The Approval Control Plane owns `ApprovalRequest`, `ApprovalDecision`, and
`ApprovalLifecycleEvent` records. Approvals move only from pending to terminal
states. An approved request is evidence for a later governed call; it never
auto-runs the original action.

Execution, workflows, task runs, skill promotion and activation, the model
gateway, module runtime invocation, and MCP controlled invocation all call the
approval gate before side-effect-capable work. Pending approvals stop the path
before adapters, model calls, or capability invocation.

## Learning Loop

Learning is expressed through evaluated traces. The deterministic evaluator
creates bounded scores for goal completion, context quality, memory relevance,
plan quality, policy compliance, execution readiness, and lifecycle readiness.
The learning engine then creates candidate `LearningSignal` records only.

Candidates are never auto-promoted in v0.1. The Brain core does not modify its
own code and does not create domain-specific learning rules.

## Reflection Engine and Skill Registry

The Reflection Engine converts evaluated traces, task runs, retrieval results,
reasoning runs, and execution outcomes into deterministic `ReflectionRecord`
data. It asks policy through `reflection.create`, stores observations,
proposed generic changes, risks, confidence, and status, then emits
`reflection_created` telemetry.

Reflections may create `SkillCandidate` records when there is enough generic
evidence for a reusable procedure. A candidate is still only a review item. It
must be reviewed, policy-gated, promoted explicitly, versioned, and activated
through the Skill Registry before it becomes active procedural memory.

The Skill Registry stores `SkillRecord` and `SkillVersion` data. Skills are
data, not generated code. AION Brain must not rewrite its own source code, run
dynamic code, shell out, or call external model services while learning.

Promotion gates require policy through `skill.promote`. Activation, disabling,
and archiving require policy through `skill.activate`, `skill.disable`, or
`skill.archive`. High and critical risk activation requires approval. Draft
skills are excluded from matching; only active skills can be retrieved as
procedural memory.

`/brain/think` can create a reflection only when the event payload explicitly
sets `reflect: true`. It can create a skill candidate only when the payload also
sets `create_skill_candidate: true`. It never promotes or activates a skill.

## Visual Brain Telemetry

Visual telemetry events describe the future Obsidian-inspired Brain graph. Nodes
represent events, intents, contexts, memories, reflections, skill candidates,
skills, capabilities, plans, policy decisions, reasoning runs, model routes,
evaluations, learning signals, and execution runs, approval checkpoints, goals,
tasks, schedules, traces, and model routes. Edges represent cognitive
relationships across the active thought path.

Temporal graph nodes become future visual nodes, and graph edges become future
visual edges. Graph upserts emit `memory_node_activated` telemetry so future UI
work can animate active relationship memory without coupling UI code to storage
engines.

Telemetry is persisted as Brain-owned contracts only. It powers future UI work
but does not include UI implementation in v0.1.

## Visual Brain Projection Layer

The Visual Brain Projection layer is separate from frontend rendering. It reads
canonical `VisualTelemetryEvent` records and produces AION-owned
`BrainVisualNode`, `BrainVisualEdge`, `BrainPulse`, `BrainVisualCluster`,
`BrainMap`, and `TraceTimeline` contracts. No contract depends on React,
Three.js, Canvas, Rive, Lottie, or any frontend framework.

`BrainMapBuilder` filters telemetry by trace, workspace, scope, event type,
node type, and time range. It deduplicates nodes, aggregates intensity, applies
deterministic half-life decay, constructs generic timeline and cognitive
sequence edges, creates activity pulses, and groups nodes into stable trace,
memory, reasoning, execution, lifecycle, learning, and identity clusters.
Evidence joins the memory family, while capabilities and modules join the
execution family. Missing references do not break projection.

`VisualTelemetryQueryService` is the policy-gated read boundary over canonical
telemetry. `TraceTimelineBuilder` joins the available trace, telemetry,
evaluation, and learning records into an ordered timeline, while tolerating
missing optional sections. Timelines and Brain Map snapshots are persisted
locally for later inspection.

The SSE stream is a polling projection over the same telemetry query boundary.
It emits JSON `visual_telemetry` events and does not introduce WebSockets or a
frontend runtime in v0.1.

## Observability Spine

The Observability Spine records sanitized Brain-loop lifecycle events through
an AION-owned `ObservabilityAdapter`. The local recorder persists
`ObservabilityEvent` records and produces `ObservabilitySummary`. Recorder
failures never break the Brain loop.

Langfuse is reserved behind `LangfuseAdapter` as a future optional
implementation. The SDK is not imported and no external observability call is
made in v0.1. Projection remains separate from rendering so future interfaces
can evolve without changing Brain contracts or governance.

## Cognitive Replay and Regression Harness

Cognitive Replay sits above the canonical event and audit ledgers. A Brain
Snapshot captures available trace state with a deterministic content hash.
Replay loads the source event, creates a fresh replay identity, disables side
effects, runs the local deterministic Brain loop, snapshots the output, and
compares it with the source.

The Trace Comparator performs normalized local semantic comparison. It ignores
identity and timestamp noise, preserves meaningful plan and timeline ordering,
and detects drift in outcome status, plan actions, policy outcomes, evaluation
scores, and required sections.

Golden regression cases pair an input snapshot with an expected snapshot.
Regression runs replay selected active cases and persist per-case comparisons
plus a generic report. Promptfoo and Ragas remain behind replaceable evaluation
adapter placeholders; v0.1 makes no external evaluation calls.

Replay protects AION from architecture drift by turning completed Brain
behavior into reproducible local evidence before external model integration.

## Durable Workflow Engine

The Durable Workflow Engine holds generic long-running Brain work without
introducing vertical workflow logic. `WorkflowDefinition`, `WorkflowRun`,
`WorkflowStepRun`, `WorkflowHeartbeat`, and `WorkflowWorkerRecord` are
AION-owned contracts and persistence records. Public APIs never expose Temporal
objects, database rows, worker internals, or external scheduler handles.

The default `LocalWorkflowEngine` persists definitions, runs, step runs,
heartbeats, workers, and lifecycle events in Postgres. It supports dry-run and
controlled modes, policy checks, approval gates, pause, resume, cancel, retry,
bounded heartbeats, and deterministic retry backoff. Dry-run is the default and
does not execute external modules or shell commands.

`LocalScheduler` and `LocalWorkflowWorker` are explicit one-shot controls. They
do not start background loops during API startup or kernel boot. A scheduler
tick can convert a due workflow schedule into a dry-run workflow request, and a
worker tick can process a bounded number of pending or due retry runs.

Temporal stays behind `TemporalAdapter` and `TemporalCompat`. `TemporalCompat`
is the only source location allowed to touch the optional SDK name. Temporal is
disabled by default, the optional dependency is not required for tests, and the
local engine remains the default adapter.

## Attention Controller Layer

The Attention Controller decides what deserves focus. The Context Compiler does
not own attention, and the Retrieval Router does not own attention. The flow is:

`Event -> Intent -> AttentionDecision -> RetrievalRequest -> RetrievalResult -> ContextBudget -> ContextFusion -> ContextPacket`

Focus sessions preserve continuity across sessions and task boundaries. Working
memory stores short-lived cognitive state and compact references, not raw
secrets, long-term truth, or chain-of-thought. Interrupts are generic records
for high-priority signals. Context budgets allocate deterministic limits before
fusion to prevent context pollution.

Future modules may emit attention signals, but AION Brain core decides focus.
No domain-specific priority logic or external attention scoring exists in v0.1.

## Kernel Assembly Layer

`KernelContainer` is the single AION Brain composition root. It loads settings,
selects approved adapters, builds repositories and services once, and registers
the assembled graph in `KernelServiceRegistry`. `create_app` stores that
container on FastAPI app state. Routes should consume services from the
container; they must not instantiate repositories, adapters, or complete
service graphs.

Kernel boot diagnostics inspect configuration and service presence without
requiring live infrastructure. Optional dependency failures degrade boot rather
than blocking startup, while missing critical boundaries fail boot. The local
self-test exercises deterministic contract and boundary checks without
external AI calls or execution side effects.

`ContractExportService` exports OpenAPI and core Pydantic schemas.
`ArchitectureBoundaryChecker` scans Brain source for direct vendor imports,
shell execution, browser automation, production identity providers, and
domain-specific directories. These controls keep the Brain provider-neutral
before stronger adapters and modules are introduced.

## Model Gateway Layer

The Model Gateway is the only AION Brain path from reasoning to model
inference. `ReasoningMesh` builds a provider-neutral `PromptPacket` and calls
`ModelGatewayService`; it does not call provider SDKs or HTTP clients directly.

The gateway owns provider and profile registries, deterministic routing, prompt
redaction, budget authorization, provider health records, model usage records,
and gateway telemetry. The deterministic provider and
`aion-deterministic-v0` profile are always available as the local fallback.
External providers are disabled by default and require explicit settings,
policy permission, `allow_external=true`, and budget approval.

LiteLLM-compatible and OpenAI-compatible adapters are HTTP boundaries only.
They use provider-neutral AION contracts and return `ModelCallRecord`; no
provider SDK objects, raw provider responses, or vendor types are public Brain
contracts. This keeps AION provider-neutral while allowing stronger models to
be registered later through policy-governed profiles.

## Autonomy Governor Layer

The Autonomy Governor is the final generic control plane before AION performs
execution-capable work. It resolves requested mode, active profile, active run
level, delegation, risk ceiling, approval state, policy decision, and explicit
capability gates into an `AutonomyDecision`.

Modes are ordered from least to most permissive: `disabled`, `observe`,
`assist`, `plan_only`, `dry_run`, `supervised_controlled`, and
`delegated_controlled`. The default profile is intentionally conservative:
`assist` by default, `dry_run` maximum, no external models or tools, no
background workers, no scheduler control, no skill promotion, and no memory
forgetting unless explicitly allowed.

Run levels are temporary overrides that can only reduce or bound effective
operation. Delegations are explicit, scoped, risk-bounded grants for controlled
work. Policy remains mandatory; modules, workflows, models, MCP tools, tasks,
skills, and memory governance never self-authorize.

The governor is wired through `KernelContainer` into Brain loop, execution,
workflows, scheduler, worker, task runner, model gateway, MCP service,
capability runtime gateway, skill service, and memory forgetting. Denials fail
closed and return structured blocked results. Autonomy lifecycle events emit
generic visual telemetry using `autonomy`, `delegation`, and `run_level` node
types.

## Cognitive Cycle Orchestrator

The Cognitive Cycle Orchestrator provides manual operating rhythms for AION
Brain without adding a background loop. It owns `CognitiveCycleTemplate`,
`CognitiveCycleRun`, `CognitiveCycleStepRun`, `SleepConsolidationRecord`, and
`CycleStatus` records. It routes every cycle and step through policy,
autonomy, risk, and approval boundaries before work can proceed.

Cycle types are generic: `wake`, `active`, `review`, `sleep_consolidation`,
`maintenance`, and `shutdown`. `dry_run` is the default mode. Controlled mode
requires approval by default. `AION_CYCLE_AUTO_RUN_ENABLED=false` keeps cycles
manual-only in v0.1.

Sleep consolidation is a coordinator over existing Brain services, not a new
memory engine. It can review attention, preview or perform working-memory
sweeps, recompute memory decay, scan conflicts, compact memory, create
reflections or skill candidates only when explicitly requested, run optional
regression checks, create visual snapshot metadata, and read observability
summaries. It does not hard-delete memory, promote skills, call models, invoke
external services, or add domain-specific rules.

Maintenance cycles perform lightweight diagnostics and safe local reviews such
as approval expiry previews, workflow heartbeat review, and kernel self-test.
All outputs are AION-owned contracts or plain JSON derived from those contracts.

## Command Bus and Consistency Guard

The Command Bus is AION Brain's generic command consistency layer. APIs may
receive requests, but the Command Bus records the intent to perform Brain work
as `BrainCommand` before dispatch. Commands are idempotency-aware, policy
gated, autonomy gated, risk assessed, approval aware, and handler driven.

The Idempotency Service stores request and response hashes so repeat requests
can return the same response without repeating effects. The Transactional
Outbox records messages that should be published after persistence; processing
is manual in v0.1 through `/brain/outbox/process-once`. The Inbox records
incoming message identities so future NATS or module-runtime delivery can be
deduplicated safely.

Processing leases are local DB records that prevent duplicate local processing.
They are not a distributed lock guarantee. The Consistency Checker detects
commands without trace IDs, stuck outbox messages, failed inbox messages,
stale processing leases, and kernel boundary findings. Repairs are limited to
safe state transitions such as expiring leases and idempotency records. It does
not delete records, execute commands, or send messages.

This layer protects event reaction, workflows, execution, cognitive cycles,
and future modules from relying on HTTP, broker, or runtime at-most-once
behavior. It remains Brain-only, domain-neutral, and free of background
processors by default.

## API Contract Hardening Layer

The API Contract Hardening layer makes the public Brain API consistent,
debuggable, and safe for SDK generation. `RequestContextMiddleware` creates a
request ID for every call, propagates correlation IDs and trace IDs, extracts
idempotency keys, adds standard response headers, and records safe request
audit metadata when enabled.

Public errors are mapped to `AIONErrorResponse` through standard exception
handlers. Raw exceptions, SQLAlchemy rows, provider SDK objects, adapter
internals, raw SQL, stack traces, raw headers, and secrets must not reach
public responses. Existing successful endpoint contracts stay
backward-compatible; new support routes may use AION envelopes when useful.

Pagination and filtering helpers define generic cursor, sort, and filter
semantics without generating SQL. Storage-specific pagination remains behind
repositories and services.

The request audit service records method, path, route name, status, duration,
safe client host/user-agent metadata, trace ID, correlation ID, and
idempotency key. It does not store bodies or raw headers.

The OpenAPI Hygiene Checker scans the generated schema for route metadata,
path safety, provider leakage, and domain-specific route prefixes. This layer
is part of the API control surface, not a business domain.

## Audit-First Design

Every decision is traceable through event IDs, intent IDs, memory refs,
capability refs, reasoning refs, model call records, policy decisions, outcomes,
execution refs, capability invocation records, evaluations, learning candidates,
visual telemetry, and timestamps.

## Module Developer Kit

The Module Developer Kit defines the safe plug-in path for future modules.
Modules submit a `ModulePackage` containing an AION `CapabilityManifest` before
runtime registration.

The Capability Certification Harness validates package schema, manifest schema,
generic identifiers, risk metadata, permissions, memory scope metadata, policy
compatibility, autonomy compatibility, dry-run behavior, and audit metadata.

Certification does not execute module code in v0.1. The Contract Test Harness
runs static dry-run tests. The Compatibility Checker reports unsupported
features and execution modes. The Scaffold Generator emits generic static files
only. Runtime registration remains separate and later than certification.

## Sandbox Control Plane

The Sandbox Control Plane defines the future execution boundary before AION
allows real module or tool execution. Future controlled actions must flow
through Capability Certification, Runtime Gateway, Sandbox Control Plane,
Policy, Risk, Approval, Autonomy, and Audit.

AION owns sandbox profiles, resource limits, egress rules, filesystem rules,
runtime permission grants, validation records, sandbox run records, and
telemetry semantics. External sandbox engines provide isolation later; they do
not define AION public contracts.

Sandbox execution is disabled in v0.1. The local no-op adapter performs
validation and returns dry-run metadata without executing code. Docker and
Firecracker adapters are placeholders that return `unsupported`; they do not
import SDKs, call sockets, start containers, call subprocess, or execute
untrusted code.

The Secret Reference Vault stores metadata-only references to secrets that live
outside AION Brain. Raw keys, tokens, passwords, authorization headers, and
secret-like metadata are rejected. Connector definitions are metadata-only and
do not perform network calls in v0.1. Runtime permission grants explicitly tie
future modules, capabilities, MCP servers, workflows, or commands to allowed
permissions, secret refs, connector refs, and sandbox profiles.

This layer remains Brain-only and domain-neutral. It does not contain finance,
trading, IT, legal, healthcare, HR, procurement, or other vertical connector
logic.

## Policy Catalog and Test Harness

The Policy Catalog layer records AION Brain's generic policy vocabulary before
more autonomous runtime behavior is added. It owns action catalog entries,
permission catalog entries, role templates, side-effect-free simulations,
policy test cases, test runs, coverage reports, bundle records, and OPA status
checks.

Routes call policy catalog services through `KernelContainer`; they do not
instantiate repositories or adapters directly. The repository owns SQLAlchemy
tables. The service layer owns authorization and telemetry. The OPA adapter
remains the only boundary for live OPA decisions and status checks.

Policy simulation enriches a `PolicyRequest`, asks the configured policy
adapter, persists the result, and records that the target action was not
executed. The test harness runs stored generic cases through simulation and
compares expected decision fields. Coverage compares Rego/default references,
catalog entries, permissions, roles, and tests.

Bundle export produces a secret-free, deterministic policy governance bundle.
The generated timestamp is metadata, not part of the content hash. Future
domain policy bundles must live outside Brain core.

## End-to-End Golden Path Harness

The End-to-End Golden Path Harness proves AION Brain v0.1 readiness through
repeatable, deterministic, side-effect-safe scenarios. It validates the full
Brain surface without introducing a domain module, UI, deployment workflow, or
external service dependency.

The Scenario Runner owns scenario execution semantics, result comparison,
scenario run records, step run records, and scenario telemetry. Default
scenarios cover generic event intake, attention, working memory, memory,
evidence, retrieval, context fusion, deterministic reasoning, planning, policy,
risk, approval, autonomy, command bus, event reaction dry-run, workflow dry-run,
cycle dry-run, module certification, sandbox validation, visual projection,
replay, regression, kernel checks, SDK smoke paths, and CLI smoke paths.

Demo Fixtures provide safe generic local records for events, evidence, memory,
module package metadata, and sandbox profile metadata. Fixture loads are dry-run
by default and must not contain secrets, external endpoints, or vertical
workflow assumptions.

The Release Baseline Service selects scenarios by ID or generic tags, runs them
in dry-run mode, combines the results with quality gate summaries, persists a
release baseline report, and emits visual telemetry. The report is the local
v0.1 readiness artifact and includes generic recommendations such as reviewing
failed scenario steps, policy coverage, OpenAPI hygiene, boundary violations,
kernel self-test output, and contract export status.

Scenarios are dry-run and generic by default because AION v0.1 needs stable
proof of system behavior before enabling domain modules, full autonomy,
external tools, optional adapters, or live providers. Future domain modules may
ship their own scenario packs outside Brain core.

## Version Manifest and Freeze Gate

The Version Manifest layer records AION Brain release metadata before future
modules depend on it. It owns version manifests, generic feature registry
entries, compatibility matrices, migration baselines, release artifact
manifests, SDK compatibility reports, and freeze gate runs.

The Freeze Gate Service coordinates local checks through existing services:
contract export, kernel diagnostics, release baseline, migration baseline,
policy coverage, OpenAPI hygiene, boundary scanning, SDK compatibility, and
release artifact metadata. It does not call shell scripts or external services.
Failures are recorded as AION contracts and persisted through the versioning
repository.

Versioning remains separate from runtime execution. It freezes the Brain public
surface and local readiness evidence; it does not enable domain modules,
optional adapters, full autonomy, external providers, or frontend behavior.

## Local Release Packager

The Local Release Packager turns release-readiness evidence into a local
handoff bundle. It gathers version manifest metadata, contract export metadata,
policy bundle metadata, migration baseline metadata, release baseline metadata,
freeze gate metadata, compatibility metadata, a deterministic source manifest,
checksums, and a placeholder SBOM.

The packager is an API service behind `KernelContainer`. API routes do not
instantiate repositories, shell commands, Docker clients, package managers, or
upload clients. The service writes only local artifacts under the configured
release package output directory and persists release package records in
Postgres.

The SBOM placeholder is intentionally metadata-only in v0.1. It reads local
project files and does not query package registries or resolve transitive
dependencies. A real SBOM generator can be added later behind an AION-owned
adapter without changing public release package contracts.

Release handoff is a local operational report. It records included reports,
known limits, next steps, and exact local verification commands. It does not
deploy, publish, enable full autonomy, run domain modules, or call external
services.

## Local Backup and Restore Preview

The Local Backup layer exports AION Brain state through application contracts,
not database dumps. `BackupExporter` asks policy, consults available
autonomy/risk/approval boundaries, reads resource records through
`ResourceReaderRegistry`, redacts sensitive data, writes local JSON/JSONL
artifacts when requested, computes checksums, and persists `BackupJob` records.

`ResourceReaderRegistry` is the infrastructure boundary for backup reads. It
returns contract-shaped dictionaries from Brain services and never exposes
SQLAlchemy rows, vendor messages, raw headers, or adapter objects. Unavailable
readers produce warnings instead of crashing broad local backups.

`RestorePreviewService` loads a stored backup job or local backup path, validates
manifest and resource checksums, detects ID conflicts, dependency gaps, scope
mismatches, version mismatches, unsupported resources, and unredacted sensitive
payloads. It persists a `RestorePreview` plan without writing restored records.

`RestoreService` records dry-run restore jobs. Restore apply is disabled by
default and returns a structured unsupported job unless explicitly enabled and
approved. v0.1 does not perform direct database restore, cloud upload, or
external storage calls.

## Resilience Control Plane

The Resilience Control Plane records local failure posture for AION Brain. It
owns dependency health records, retry policy metadata, circuit breaker state,
degraded mode events, fault injection rules, and resilience test reports.

Dependency health checks stay behind infrastructure boundaries and never crash
callers. Retry policies are bounded metadata used by services such as command
dispatch and outbox delivery; they do not create background retry loops in
v0.1. Circuit breakers gate adapter calls through AION-owned contracts.

Degraded mode records explicit fallback posture when optional adapters fail. It
does not auto-remediate or mutate infrastructure. Fault injection is disabled by
default, deterministic when enabled for local drills, and never performs
external side effects.

The freeze gate consumes the resilience test runner as a local readiness signal.
Critical unhealthy dependencies or critical degraded posture can block a local
release when configured to do so. Optional adapter warnings remain visible
without hiding the underlying fallback state.

## Dialogue Session and Response Layer

The Dialogue Session Manager is a backend contract layer for conversational
state. It owns dialogue sessions, sanitized messages, clarification requests,
feedback, and dialogue turn orchestration. It does not implement a frontend UI,
provider chat objects, external message delivery, controlled execution, or
domain-specific conversation logic.

`DialogueTurnService` coordinates policy, autonomy posture, optional Brain loop
thinking, response composition, verification, local delivery recording, audit
provenance, visual telemetry, and optional memory handoff. A dialogue turn may
ask for clarification when the goal, grounding, confidence, or policy posture is
not sufficient.

`ResponseComposer` is deterministic in v0.1. It turns AION-owned trace,
context, grounding, and clarification metadata into `ResponseDraft` contracts.
`ResponseVerifier` checks grounding, policy posture, autonomy posture, hidden
reasoning markers, and secret-like payloads before a response is treated as
ready. `ResponseDeliveryService` records local API-return delivery only.

Dialogue memory handoff is an adapter-ready governance boundary. It can create
summarized memory records from allowed dialogue content when explicitly
requested, but it must not store raw secrets, raw prompts, chain-of-thought,
hidden reasoning, or uncontrolled execution artifacts.

## Belief State Manager and Truth Maintenance

The Belief State Manager stores explicit, scoped claims in the canonical Brain
ledger. A claim has provenance, confidence, status, sensitivity, source
references, support records, contradiction records, and revision history.
Belief state is not absolute truth; it is a governed working model that
reasoning and context compilation can consult with visible status metadata.

The Claim Ledger persists `BeliefClaim`, `BeliefSupport`,
`BeliefContradiction`, `BeliefRevision`, and `TruthMaintenanceRun` contracts.
Repository methods return AION contracts only and never expose SQLAlchemy rows
or database-specific types.

Truth maintenance is deterministic in v0.1. It recomputes confidence from
support, evidence references, contradictions, source type, and staleness. It can
mark claims supported, uncertain, contradicted, stale, rejected, or archived.
It does not call external fact-checking systems, model providers, web search,
or vertical knowledge bases.

Dialogue and evidence can opt in to deterministic claim extraction. Extracted
claims still pass through policy, provenance, audit, and telemetry boundaries.
Reasoning receives belief status metadata so stale or contradicted beliefs are
visible as constraints instead of being silently treated as facts.

## Concept Registry and Entity Resolver

The Concept Registry owns generic abstract concepts such as goals, policies,
tasks, constraints, capabilities, memory types, evidence types, and system
components. It is not a domain ontology.

The Entity Registry owns canonical references. It separates raw text mentions,
aliases, unresolved references, canonical entities, merged references,
superseded references, and reference links. Entity references identify records;
they do not prove that a statement is true.

Mention extraction is deterministic in v0.1. It recognizes explicit bracketed
references, quoted names, dotted or snake-case identifiers, and generic
title-case phrases. It skips secret-like text and hidden-reasoning markers and
does not infer sensitive identity attributes.

Entity resolution is deterministic and local. It scores normalized name
matches, alias matches, shared source references, scope overlap, and mention
confidence. Dry-run resolution persists the resolution run but does not create
entities, mentions, or reference links.

Reference links connect AION-owned records across evidence, memory, beliefs,
dialogue, graph memory, traces, commands, tasks, audit entries, concepts, and
entities. They may create provenance links where a provenance service is
available.

Merge and split workflows are proposal based. AION v0.1 does not auto-merge
entities and never hard-deletes entity records or mentions. Approved merges
mark the duplicate entity as `merged`; approved splits create proposed entity
records while keeping the original entity intact.

Entity references differ from beliefs and graph nodes:

- Beliefs own explicit claims, confidence, support, contradiction, and truth
  maintenance status.
- Graph memory owns typed nodes and edges.
- Entity references only provide canonical pointers that other systems can
  attach to their own records.

## Situation Model and Temporal State Projection

The Situation Model builds a deterministic backend projection of current Brain
state. It joins generic sources into `SituationRecord`, `StateAtom`,
`StateTransition`, `TemporalStateWindow`, and `ContextContinuityRecord`
contracts.

The projection layer never mutates source records. It reads AION-owned records,
normalizes them into state atoms, detects generic transitions, and persists
projection records only in controlled mode. Dry runs persist nothing.

Context compilation can retrieve `situation_model` and `temporal_state`
sources. Retrieved atoms are treated as recall, not truth. Stale or
contradicted atoms become constraints such as `situation_projection_stale` and
`state_atom_contradicted`.

The Situation Model remains separate from frontend rendering, model providers,
and vertical workflows. AION public contracts do not expose vendor clients,
SQLAlchemy rows, or domain-specific state internals.

## Decision Intelligence Layer

AION Decision Intelligence separates situation state, beliefs, goals,
constraints, candidate options, tradeoffs, counterfactual outcomes, and journal
records. The layer includes Decision Frame Manager, Decision Options, Utility
Profiles, Option Evaluation, Tradeoff Matrix generation, Counterfactual
Simulation, and Decision Journal records.

Decision records recommend and journal only. They do not execute selected
options. Execution remains owned by explicit execution APIs and remains gated
by policy, risk, approval, and autonomy.

## Outcome Ledger and Effect Verification

The Outcome Ledger records the generic effect lifecycle:

```text
ExpectedEffect -> ObservedEffect -> OutcomeRecord -> EffectVerificationRun
```

`ExpectedEffect` captures what AION expected from a command, workflow, plan,
decision option, counterfactual, execution, task, cycle, event reaction, or
generic source. `ObservedEffect` captures what AION observed from local Brain
records. `OutcomeRecord` joins those references without mutating the source
records. `EffectVerificationRun` compares expected and observed effects using
deterministic criteria.

Outcome services sit behind `aion_brain.outcomes` boundaries. API routes,
operator summaries, command completion, workflow completion, decision
projection, visual telemetry, and learning feedback use those services instead
of reading SQLAlchemy rows directly.

Verification is not proof of truth. It is a bounded check that expected local
effects are present, missing, unexpected, or contradicted. Controlled
verification may update outcome status and score; dry-run verification does
not mutate outcomes.

The learning feedback bridge is review-only. It can create outcome feedback
records and candidate learning metadata, but it never promotes skills,
auto-remediates failures, writes source code, executes commands, or calls
external services.

## Experience Ledger and Learning Synthesis

The Experience Ledger is the canonical generic store for observed Brain
experience. It records source references, trace references, owner scope,
score, confidence, and safe metadata without mutating source command,
workflow, outcome, replay, audit, approval, or regression records.

The Learning Synthesizer reads experiences and produces deterministic,
reviewable learning material:

- `LearningPattern` records repeated generic shapes.
- `LessonRecord` stores reviewable lessons.
- `SkillCandidateSuggestion` proposes a passive candidate only.
- `RegressionCandidateSuggestion` proposes coverage only.
- `LearningSynthesisRun` records what was synthesized.

Pattern mining uses deterministic lexical grouping and bounded confidence
thresholds. The synthesizer runs in `dry_run` or `controlled` mode. Dry runs do
not persist generated learning material except the run record. Controlled runs
persist review records but still do not promote skills, create active
procedures, create regression cases, modify code, call models, or call external
services.

Operator Control Tower reads learning patterns and suggestions as action
items. Visual telemetry receives generic learning events such as
`experience_recorded`, `learning_pattern_detected`, `lesson_created`, and
`learning_synthesis_completed`.

Learning remains domain-neutral. Domain-specific learning, if introduced
later, must live outside Brain core and communicate through generic contracts.

## Self Model and Capability Awareness

The Self Model is AION Brain's canonical descriptive layer. It defines the
official AION meaning, active profile, architecture references, capability
inventory, limitation ledger, confidence calibration records, self-assessment
runs, and introspection snapshots.

Capability Awareness reads local configuration, kernel services, adapter
status, diagnostics, policy posture, autonomy posture, and optional adapter
settings to produce factual `CapabilityAwarenessRecord` entries. Disabled and
unavailable adapters must remain visible as disabled or optional-unavailable
instead of being described as active.

The Limitation Ledger stores generic disclosed limitations such as local-only
operation, disabled external delivery, disabled arbitrary code execution,
bounded autonomy, disabled optional adapters, and grounding limits.

Confidence Calibration is deterministic. It scores local evidence, belief,
memory, grounding, limitation, policy, autonomy, and verification signals. It
adds required disclosures such as low-confidence or ungrounded-response
metadata without calling model providers.

Self Assessment and Introspection Snapshots are read-only diagnostics. They
summarize local state and redacted configuration without mutating runtime
configuration, enabling adapters, promoting skills, executing capabilities, or
overriding policy.

This layer is not a personality system and not a UI. It is a Brain-owned
contract boundary for accurate self-description and limitation awareness.

## Explanation Engine and Trace Narrative Builder

The Explanation Engine builds public, deterministic explanations from
observable AION records. It never exposes hidden reasoning, chain-of-thought,
raw prompts, raw headers, provider payloads, secrets, SQLAlchemy rows, or
vendor SDK objects.

The Trace Narrative Builder joins audit records, events, commands, policy
decisions, approvals, outcomes, responses, and provenance references into an
ordered public timeline for one trace. Missing sections produce partial or
insufficient-record narratives instead of crashing.

The Why-Not service answers why a requested action did not continue using
generic blockers such as policy denial, approval requirements, autonomy mode,
risk escalation, missing grounding, disabled capability, or missing records.

Explanation services sit behind `aion_brain.explanations` boundaries. API
routes, dialogue turns, response composition, response verification, operator
action center items, visual telemetry, and SDK/CLI surfaces consume
Explanation contracts instead of subsystem internals.

All explanation creation, reading, verification, feedback, why-not, and trace
narrative operations pass through policy and fail closed.

## Instruction Hierarchy and Preference Control

The Instruction Hierarchy is the Brain-owned control layer for instructions,
preferences, constraints, style profiles, conflicts, and resolution runs.
It is not a policy replacement and not a personality system.

The resolver applies hard policy and safety constraints first, followed by
runtime configuration, autonomy, risk and approval constraints, capability and
sandbox limits, session/task/workspace instructions, confirmed preferences,
and finally learned preference candidates. Preferences shape context and
response metadata only; they never expand permissions.

The Preference Ledger stores candidate, confirmed, rejected, disabled, and
superseded generic preferences. Learned preferences remain candidates until
explicitly confirmed. Style profiles are generic response-shaping records and
cannot override response verification, grounding, policy, autonomy, approvals,
runtime config, or capability limits.

The Conflict Detector records deterministic generic conflicts such as policy
override attempts, approval bypass attempts, style conflicts, grounding
conflicts, unsupported instructions, expired instructions, and duplicates.
The Context Compiler and Dialogue layer consume `InstructionResolutionResult`
contracts rather than repository rows or hidden prompts.

## Grounding Manager and Citation Mapper

The Grounding Manager is the Brain-owned source-attribution control plane.
It converts local AION source records into citations, citation maps,
unsupported statements, verification runs, and source coverage reports.

Evidence Vault remains the owner of primary evidence. Memory remains recall,
not truth. Belief State remains the owner of claim status. Grounding joins
those references for response-level support without mutating the source
systems or inventing evidence refs.

The Citation Mapper is deterministic in v0.1. It splits public text into
statements, checks lexical support against provided grounding sources, creates
citations for supported statements, and records unsupported statements for
operator review. It does not call model providers, web search, external
observability systems, or domain-specific logic.

## Prompt Packet Compiler and Model Input Governance

The Prompt Packet Compiler is the Brain-owned model input boundary. It joins
instruction resolution, context compiler output, retrieved context, memory
recall, evidence, belief records, grounding metadata, citation refs, prompt
templates, and prompt fragments into a provider-neutral `PromptPacket`.

Prompt Templates and Prompt Fragments are generic reusable AION contracts. They
must not include provider-specific hidden syntax, chain-of-thought requests,
raw prompt storage, raw secrets, or domain prompt packs.

The Prompt Boundary Guard checks compiled sections before model routing.
Retrieved context is treated as untrusted context by default. Memory sections
must be labeled `memory_recall`. Belief sections carry status and confidence
metadata. User, memory, and retrieved content cannot override system, policy,
autonomy, risk, or approval constraints.

Prompt Injection Detection is deterministic in v0.1. It uses local pattern
checks for generic override, exfiltration, approval bypass, hidden prompt,
chain-of-thought, tool injection, and source confusion attempts. It does not
call external classifiers or model providers.

The Model Input Manifest records a provider-neutral handoff for Model Gateway:
input hash, section count, token estimate, budget metadata, grounding refs,
instruction refs, safety refs, and status. Public AION APIs expose manifests
and redacted previews only. Raw rendered prompts are not persisted by default.

Prompt governance relates to the Context Compiler and Model Gateway as follows:

`instruction/context/grounding -> prompt packet -> boundary check -> model input manifest -> model gateway`

The compiler does not decide policy, execute tools, approve actions, expand
autonomy, create truth, or expose hidden reasoning.

## Model Output Governance

Model Output Governance is the Brain-owned output boundary after Model Gateway
completion. It receives provider-neutral output, stores a raw-output hash,
persists redacted output, parses deterministic generic segments, validates
structured JSON, creates local response candidates, and captures tool intents
for review.

The governance path is:

`model gateway -> model output record -> segments -> validation -> response candidate/tool intent -> operator review`

Raw model output is not stored by default. Tool intents are not executed in
v0.1. Response candidates are proposals only until policy and response
verification allow local promotion. Public APIs return only AION-owned
contracts and never provider SDK objects, hidden reasoning, raw prompts, raw
headers, raw secrets, or domain-specific output internals.

## Action Proposal Broker and Execution Handoff Gate

The Action Proposal Broker is the Brain-owned boundary between intent and
execution. It converts reviewed generic intent from user requests, model tool
intent candidates, decision records, planner steps, operators, and internal
systems into `ActionProposal` records.

An action proposal is not execution. It stores redacted proposed payload,
scope, risk, required permissions, required approvals, blockers, references,
and metadata. It must not create command runs, workflow runs, capability
invocations, MCP calls, sandbox runs, or external side effects by itself.

Tool Intent Review is a separate policy-gated path for blocked
`ToolIntentCandidate` records from Model Output Governance. Review can create
an action proposal only when explicitly requested and safe. The default
runtime posture does not auto-create proposals from model output.

Action blockers are metadata-only records describing policy, autonomy,
approval, risk, sandbox, runtime configuration, grounding, capability, or
unsupported target constraints. Resolving a blocker does not execute an action.

Proposal Review updates proposal state and records review metadata. Approval
for handoff is not execution. A separate `ExecutionHandoffRequest` is required
before any governed target receives a request.

The Execution Handoff Gate builds target requests for governed AION systems:
Command Bus, Workflow Engine, Execution Orchestrator, Capability Runtime
Gateway, MCP Adapter, Cognitive Cycle Orchestrator, and Sandbox Control Plane.
Handoff defaults to dry-run and controlled handoff is disabled by default.

The action path is:

`tool intent / decision / plan / user request -> proposal -> review -> handoff -> governed target system`

All public APIs return AION-owned contracts and never expose target service
internals, raw provider output, hidden reasoning, raw prompts, raw headers,
secrets, SQLAlchemy rows, or domain-specific action logic.

## Run Supervision and Control

Run Supervision is the Brain-owned observation layer for governed target runs.
It registers supervised runs, samples target status through local adapters,
detects stalled or timed-out records, creates manual control requests, prepares
non-executing compensation plans, and generates operator reports.

Run supervision differs from execution. Target systems remain authoritative for
their own lifecycle state and control semantics. Supervision stores
`RunSupervisionRecord` metadata, `RunStatusSample` observations, timeout policy
metadata, `RunControlRequest` records, `CompensationPlan` records, and
`RunSupervisionReport` summaries. It does not shell out, call external systems,
force-cancel target runs, execute compensation steps, or mutate target state
outside explicit governed target APIs.

The supervision path is:

`handoff / command / workflow -> supervised run -> status sample -> control request / compensation plan -> operator review`

Control requests are dry-run by default. Timeout policies create blockers or
operator action items only. Compensation plans may be converted to action
proposals through an explicit API, but the plans and steps do not execute
themselves.

## Temporal Scheduler

The Temporal Scheduler is the Brain-owned local time coordination layer. It
stores schedules, recurrence rules, due items, reminders, tick runs, schedule
policies, and scheduler reports. It is distinct from execution, workflows,
cron, Celery, Temporal, and external calendars.

Recurrence rules are deterministic and evaluated locally in UTC. The Due Item
Ledger records due or missed schedule occurrences. The Reminder Queue stores
local reminder records only. The Local Tick Orchestrator runs only when called
through an explicit API, CLI, SDK, or governed internal service.

Scheduler tick can create scheduler-owned due items, reminders, notifications,
action proposals, and operator items. It cannot execute target actions, run
workflows, process outbox records, call external APIs, send external
reminders, or mutate source records outside scheduler-owned state.

Schedule Policies are metadata and deterministic checks around scheduler
behavior. Violations produce report findings or local records only. They do
not authorize execution.

## Incident Correlation

Incident Correlation is the Brain-owned local layer for grouping AION signals
that may require operator attention. It consumes normalized local signals from
Brain systems, stores incident-owned records, and runs deterministic grouping
by trace, source, fingerprint, correlation key, and time window.

The incident path is:

`signal -> correlation run -> incident -> root cause candidate -> recovery review -> operator review`

Dry-run correlation previews grouped incidents without persistence side
effects beyond the correlation run record. Controlled correlation may create
incident records only through policy and autonomy gates. It must not mutate
source alerts, notifications, runs, prompts, grounding records, audit records,
scheduler records, or learning records.

Root cause candidates are hypotheses with supporting references and missing
evidence. They are never stored as truth. Recovery reviews summarize local
findings and may propose local records, but they never execute remediation.

The incident layer remains generic, local, policy-gated, and frontend-agnostic.
It does not call external incident-management services, external notification
services, model providers, shell commands, or domain-specific tooling.

## Global Resource Registry

The Global Resource Registry is the Brain-owned index and link-integrity layer
for AION resources. It stores safe descriptors and registry-owned metadata for
resource references, backlinks, broken references, orphaned resources,
validation runs, rebuild runs, and snapshots.

The registry is not authoritative for the source records it indexes. Source
systems keep ownership of their records and lifecycle state. Registry rebuilds
read safe descriptors from local adapters and update the registry index only.
Reference validation reports integrity findings only. Neither path repairs
source records, mutates source lifecycle state, hard-deletes source records, or
calls external services.

Resource identity is normalized through AION-owned URIs:

`aion://{resource_type}/{resource_id}` with optional
`?trace_id={trace_id}`.

The registry joins existing Brain layers without becoming a graph database or
search index. It provides a consistent reference spine for audit, provenance,
evidence, memory, reasoning, model governance, action proposals, supervision,
notifications, scheduler records, incident records, release records, backups,
and operator surfaces while preserving each layer's ownership boundary.

Registry actions are policy-gated. Operator cards and queues can surface broken
references, orphaned resources, and rebuild runs for review, but the registry
does not execute repairs. Visual telemetry receives generic resource and
integrity events so future projection layers can show the reference spine
without coupling registry contracts to UI code.

## Data Lifecycle Manager

The Data Lifecycle Manager is the Brain-owned advisory layer for retention
policy, lifecycle classification, archive candidates, redaction candidates,
purge previews, lifecycle reviews, and lifecycle reports.

The lifecycle path is:

`registry resource -> retention classification -> candidate / preview -> review -> optional action proposal`

Source systems remain authoritative for their records. Lifecycle evaluation
reads safe descriptors from the Global Resource Registry, applies generic
retention policies, and writes lifecycle-owned records only. It does not
mutate source records, hard-delete records, execute archive, execute redaction,
call object storage, call external services, or add domain-specific retention
logic.

Archive candidates and redaction candidates are review records. Converting one
to an action proposal creates another review artifact only; it does not execute
archive or redaction. Purge previews are impact reports and always keep
`hard_delete_allowed=false` in v0.1. Backup verification is required before an
archive candidate can be converted for proposal review.

Lifecycle records feed operator cards, queues, action center items, visual
telemetry, audit, provenance, SDK, and CLI surfaces through AION contracts. No
surface may expose SQLAlchemy rows, raw headers, hidden reasoning, raw prompts,
secrets, source-system internals, or domain-specific lifecycle behavior.

## Extension Registry and Module Intake

The Extension Registry is the Brain-owned metadata boundary for future modules.
It records extension manifests, package metadata, declared capabilities,
declared dependencies, compatibility checks, reviews, and non-executable future
install plans.

The extension path is:

`manifest -> validation -> package metadata -> declarations -> compatibility -> review -> future install plan`

The registry does not load code, install packages, run shell commands, clone or
download sources, register dynamic routes, register active capabilities, create
policy actions from manifests, call external services, or activate modules.
Capability and dependency declarations remain descriptive until later governed
tasks introduce execution and installation boundaries.

Extension Registry records join existing AION infrastructure through adapters:
Contract Registry and interface drift checks, Resource Registry descriptors,
Capability Registry declarations, Policy Catalog actions, Runtime Config
flags, Sandbox and Security Baseline gates, Audit and Provenance records,
Operator queues, Notification hooks, Release Package summaries, Freeze Gate
checks, and Visual Brain telemetry. These integrations remain records-first
and policy-gated.

Install plans are advisory records only in v0.1. They always keep
`executable=false` and `execution_allowed=false`.

## Capability Binding and Module Slot Layer

The Module Slot Manager creates inactive module slot records for future module
positions. A slot may reference an extension package, declared capabilities,
contracts, policy actions, settings, sandbox profile metadata, and future mount
plans, but it never loads code or activates a runtime.

The Capability Binding Registry creates inactive binding records under module
slots. A binding describes a generic capability key, schemas, required policy
actions, required settings, required contracts, sandbox requirements, risk, and
target runtime metadata. It does not register an active capability and does not
invoke a module runtime.

Binding Validation checks staged slots and bindings against local AION records:
contract registry entries, policy catalog actions, runtime configuration flags,
sandbox requirements, activation flags, route-registration flags, and duplicate
capability keys. Dry-run validation stores only the validation run. Controlled
validation may store binding-owned conflict records, but it still does not
mutate source registries or activate anything.

Mount Plans are metadata-only future plans. They summarize required contracts,
settings, policy actions, sandbox profiles, and binding ids, and must keep
`executable=false` and `execution_allowed=false`.

Route Binding Preview records future route shapes for review. It must keep
`registration_allowed=false` and must not register FastAPI routes, SDK methods,
CLI commands, or runtime routes dynamically.

The binding path is:

`extension package -> module slot -> capability binding -> validation -> mount plan -> route preview`

Bindings differ from active capabilities and modules because they are staged
records only. Active capability registration, module loading, package
installation, route registration, runtime configuration mutation, and execution
remain outside this layer.

## Capability Conformance Harness

The Capability Conformance Harness sits after the Extension Registry and
Capability Binding Registry. It converts staged metadata into conformance
profiles, capability test vectors, schema-only mock invocation records,
conformance runs, findings, and readiness assessments.

The harness is a governance layer, not an execution layer. It validates
contracts, policy action references, settings, schema shape, sandbox metadata,
and unsafe activation flags. It never loads extension code, installs packages,
invokes capabilities, calls MCP, runs sandbox code, registers dynamic routes, or
calls external systems.

Extension readiness assessments are local records that can block future
activation. In v0.1 `activation_ready` is always false.

## Module Activation Request Gate

The Module Activation Request Gate sits after module slots, capability
bindings, conformance, and readiness. It creates explicit future activation
request records and runs deterministic blockers before any activation design is
allowed to proceed.

The activation request path is:

`module slot -> capability binding -> conformance/readiness evidence -> activation request -> gate run -> blockers -> review -> non-executable plan -> runtime registration preview`

The gate owns these boundaries:

- `ModuleActivationRequest` records the intent to evaluate future activation.
- `ActivationGateRun` records deterministic checks and blockers.
- `ActivationBlocker` records open requirements or explicit disabled gates.
- `ActivationReview` records operator review without activating anything.
- `ActivationPlan` is non-executable and keeps `executable=false`.
- `RuntimeRegistrationPreview` previews route/capability/policy/setting shape
  and keeps `registration_allowed=false`.

AION-083 is records-first. It must not load extension code, install packages,
activate capabilities, register runtime routes, mutate runtime configuration,
call external systems, invoke MCP or sandbox runtimes, approve itself, or add
domain-specific module logic.

The gate reports to operator action items through open
`module_activation_blocker` records and emits visual telemetry for activation
request, blocker, gate, review, plan, and registration-preview nodes.

## Golden Path Scenario Harness

The Golden Path Scenario Harness is the Brain-owned local end-to-end
verification layer for v0.1. It joins synthetic fixture packs, deterministic
scenario runs, step results, assertion results, reports, release smoke checks,
operator recommendations, audit/provenance links, and visual telemetry.

The harness verifies integration; it does not replace pytest, the release gate,
or the freeze gate. A scenario run may create scenario-owned records and call
existing Brain services through public service interfaces, but it must not
bypass policy, autonomy, or approval gates.

The golden path flow is:

`fixture pack -> scenario -> dry-run step -> assertion -> run report -> release smoke -> operator/freeze/release summary`

The release smoke matrix reads local service availability and the latest golden
path report. It does not spawn subprocesses, execute shell commands, call
external services, run backups, or package releases.

Golden path records feed Resource Registry indexing, Operator Control Tower
cards, queues and action items, Freeze Gate optional checks, Release Package
summaries, SDK, CLI, audit, provenance, and visual telemetry. All surfaces use
AION-owned contracts and never expose SQLAlchemy rows, raw secrets, raw prompts,
hidden reasoning, provider payloads, or frontend-specific data.

## Release Candidate Gate

The Release Candidate Gate is the v0.1 final local readiness aggregator. It
joins script-supplied checks, safe service checks, verification matrices,
findings, evidence packs, reports, operator queues, resource registry records,
visual telemetry, audit, provenance, SDK, and CLI surfaces.

The RC flow is:

`candidate -> verification matrix -> gate run -> findings -> evidence pack -> report`

RC-owned records are release metadata and evidence only. The gate does not
deploy, publish, tag, mutate source code, enable external features, execute
release packaging in controlled mode, call external services, or create
domain-specific readiness logic. Controlled mode is disabled by default and is
limited to RC-owned records when explicitly enabled.

Release readiness is computed from normalized `VerificationCheck` records.
Required missing, failed, blocked, or unknown checks fail closed. Critical
findings block readiness when the matrix requires it. Evidence packs and
reports are redacted before persistence and must not include raw prompts,
hidden reasoning, raw headers, provider payloads, secrets, or SQLAlchemy rows.

## Final Release Closure

AION-079 adds the operator runbook, local demo pack, troubleshooting guide,
release candidate checklist, final documentation audit, local demo script, and
release handoff summary. These files explain and validate the existing v0.1
runtime; they do not create a new Brain subsystem.

Release-closure docs and scripts differ from Brain runtime services:

- They call existing local APIs and scripts.
- They do not add database tables.
- They do not add API routes.
- They do not add policy actions.
- They do not deploy, provision, publish, or enable disabled features.
- They do not introduce domain-specific workflows.

## v0.1 Release Freeze

AION-080 freezes the AION Brain v0.1.0 local release baseline. It adds release
notes, a changelog, final freeze docs, final evidence summary, tagging guide,
operator acceptance checklist, known limitations, release baseline docs, and
scripts that aggregate existing gates.

The freeze layer is operational closure, not runtime architecture. It does not
add database tables, API routes, policy actions, new services, model calls,
external connectors, extension loading, capability activation, dynamic route
registration, hard delete, deployment, publishing, or domain module logic.

## Post-v0.1 Module Ecosystem

AION-082 starts module ecosystem strategy after the v0.1 release freeze. It is
docs, roadmap, activation design, threat model, selection matrix, checklist,
and metadata-only example work. It does not add a runtime subsystem.

Future modules must enter through the existing Brain gates:

`extension manifest -> extension intake -> module slot -> capability binding -> binding validation -> conformance -> readiness assessment -> operator review -> action proposal where needed -> policy/risk/approval/autonomy/sandbox -> future activation gate`

Activation remains disabled. Code loading remains disabled. Package
installation, dynamic route registration, external calls, full autonomy, and
controlled handoff remain disabled.

The first selected governed module class is Generic Knowledge Intelligence. It
is low-risk because it does not need tool execution, external actions,
controlled handoff, dynamic routes, package installation, or runtime
activation. It remains metadata-only until future activation design gates pass.

Modules must not modify Brain core. Domain modules plug into Brain through
metadata, contracts, bindings, conformance, readiness, policy, audit,
provenance, and operator review rather than Brain core code changes.

See `docs/roadmap/module-ecosystem.md` and
`docs/architecture/module-activation-design.md`.

## Generic Knowledge Intelligence Module Pack

AION-084 adds the first concrete post-v0.1 module package as metadata only.
This is a package example and readiness trail, not a runtime module and not a
new Brain subsystem.

The example path is:

`manifest -> intake -> slot -> binding -> conformance -> readiness -> activation request -> activation blocker`

The pack is stored under `examples/modules/generic-knowledge-intelligence/`.
It declares five generic capabilities, synthetic test vectors, dry-run request
fixtures, expected activation blockers, and operator review evidence.

The pack must not register runtime routes, add SDK or CLI surface, add
migrations, load code, install packages, execute tools, call external services,
mutate runtime configuration, or activate capabilities. Activation blockers
are the expected v0.1 result.

## Deterministic Module Mock Runtime

AION-085 adds a deterministic module mock runtime as a post-v0.1 readiness
evidence layer. It belongs to Brain core governance, not to any module
implementation. The runtime converts inactive capability binding metadata and a
mock profile into synthetic dry-run records:

`binding metadata -> mock profile -> redacted input -> shape checks -> synthetic output -> run record -> findings`

The runtime is adapter-ready and metadata-only. It may provide evidence to the
activation gate, conformance runner, resource registry, release packager,
freeze gate, hardening gate, and operator surfaces. Those integrations read or
create local records only.

The runtime must not load module code, install packages, invoke real
capabilities, activate modules, register dynamic routes, mutate runtime
configuration, execute shell commands, call external services, expose secrets,
or encode domain-specific workflows.

## Model Provider Hardening

AION-086 adds a provider-readiness layer before real provider enablement. It
connects prompt packets, model input manifests, provider profiles, prompt
egress previews, dry-run provider simulations, output governance, tool intent
blocking, grounding requirements, audit/provenance, and operator review.

The layer is local and metadata-only. Provider readiness is not provider
enablement, prompt egress preview is not prompt transmission, and provider
simulation is not a model call. Public contracts stay AION-owned and do not
depend on provider SDKs.

## Operator Console Planning

AION-087 keeps the post-v0.1 operator experience CLI/API-first. It adds a
local dashboard blueprint, workflow map, view spec, action boundary, data
safety model, demo map, no-go list, and future milestone sequence without
adding runtime UI.

AION-088 adds that audited view-model layer. Operator Console view models are
read-only backend contracts that summarize existing Brain state, map source
services into redacted sections, expose descriptor-only actions, and return
unavailable sections when optional services are missing. The API, SDK, and CLI
surface is read-only and frontend-agnostic.

Future UI consumes these existing APIs and CLI-backed dry-run workflows. The
console must not create privileged bypasses around policy, audit, approval,
redaction, module activation, provider hardening, runtime config, or release
gates.

AION-088 adds no runtime UI, no frontend dependencies, no migrations, no module
activation, no code loading, no package installation, no external calls, no
execution, and no runtime registration. It also preserves no raw prompt
exposure, no hidden reasoning exposure, and no secret exposure.
