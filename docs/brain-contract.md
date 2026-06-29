# Brain Contract

The public AION Brain contract is the set of typed models that every internal
subsystem and future external module must use when crossing the Brain boundary.

The contract includes:

- `AIONEvent`: normalized incoming activity and the only accepted event input contract.
- `EventTriggerRule`: deterministic predicate for event subscription matching.
- `ConnectorSimulationRequest`: request to validate a synthetic connector
  request/response shape in dry-run mode.
- `ConnectorSimulationResult`: synthetic connector simulation result that is
  never trusted connector data and always reports runtime, external calls,
  credentials, and tokens disabled.
- `ConnectorReplayFixture`: local fixture used to replay synthetic connector
  shapes through the dry-run simulator.
- `ConnectorPolicyReadinessRequest`: request to check simulator policy action,
  sandbox, audit, and provenance readiness without runtime approval.
- `ConnectorPolicyReadinessResult`: readiness result that never permits
  external calls, credential use, or activation.
- `ConnectorSimulatorFinding`: safe connector simulator finding summary without
  blocked material values.
- `EventSubscription`: generic event reaction subscription.
- `EventSubscriptionCreateRequest`: request to create a subscription.
- `EventDispatchRequest`: request to dispatch an event through subscriptions.
- `EventReactionAction`: auditable attempted reaction action.
- `EventDispatchRecord`: persisted dispatch result.
- `EventDeadLetterRecord`: failed reaction retained for inspection or replay.
- `EventRouterStatus`: router status summary.
- `IntentFrame`: the Brain's interpretation of an event goal.
- `ContextPacket`: gathered context, constraints, and open questions.
- `BrainState`: deterministic runtime state while a Brain loop is executing.
- `MemoryRecord`: policy-aware memory metadata.
- `SemanticAdapterStatus`: public status for semantic recall adapters.
- `TurboVecIndexStatus`: public status for an AION-managed compressed recall index.
- `TurboVecRebuildRequest`: request to rebuild a compressed semantic index from canonical memory.
- `TurboVecRebuildResponse`: rebuild result with counts and public status.
- `TurboVecReindexRequest`: request to reindex one memory record through TurboVec.
- `GraphMemoryAdapterStatus`: public status summary for graph recall adapters.
- `GraphitiConfigStatus`: public status for optional Graphiti configuration.
- `GraphitiSyncRequest`: request to sync canonical graph records into Graphiti.
- `GraphitiSyncResponse`: sync result with counts and public status.
- `GraphitiEpisodeRequest`: request to add generic temporal context as an episode.
- `GraphitiEpisodeResponse`: public episode add result.
- `CapabilityManifest`: declared future module capabilities.
- `ModuleRuntime`: registered module runtime metadata.
- `CapabilityRuntimeBinding`: binding between a capability and runtime.
- `ModuleHealthCheck`: runtime health record.
- `ModuleRuntimeRegistrationRequest`: request to register a module runtime.
- `ModuleRuntimeRegistrationResponse`: runtime registration result.
- `CapabilityBindingRequest`: request to bind a capability to a runtime.
- `CapabilityInvocationRequest`: gateway invocation request.
- `CapabilityInvocationResult`: gateway invocation result.
- `MCPServerRecord`: registered optional MCP server boundary metadata.
- `MCPToolDescriptor`: normalized MCP tool metadata before mapping.
- `MCPCapabilityMapping`: AION-owned mapping from MCP tool to capability.
- `MCPServerRegistrationRequest`: request to register an MCP server boundary.
- `MCPSyncRequest`: request to discover MCP tools and optionally map them.
- `MCPSyncResponse`: tool discovery and capability mapping result.
- `MCPInvocationRequest`: request to dry-run or controlled-invoke an MCP-backed capability.
- `MCPInvocationResult`: provider-neutral MCP invocation result.
- `MCPServerHealth`: public MCP server health status.
- `MCPAdapterStatus`: process-local MCP adapter availability and safety status.
- `PromptPacket`: provider-neutral reasoning input packet.
- `ModelRouteDecision`: provider-neutral model routing decision.
- `ReasoningRequest`: generic reasoning request.
- `ReasoningResult`: generic reasoning output.
- `ModelCallRecord`: provider-neutral model call ledger record.
- `PlanGraph`: plan structure, generic steps, and dependencies.
- `ExecutionRequest`: explicit request to run a plan through the state machine.
- `ExecutionRun`: auditable execution run.
- `ExecutionStepRun`: state of a single plan step execution.
- `ApprovalCheckpoint`: pending or resolved approval gate.
- `CapabilityInvocationRecord`: provider-neutral capability invocation ledger record.
- `GoalRecord`: Brain-owned generic goal lifecycle record.
- `GoalCreateRequest`: request to create a proposed generic goal.
- `GoalTransitionRequest`: request to move a goal through the lifecycle state machine.
- `CognitiveTask`: Brain-owned generic cognitive task lifecycle record.
- `TaskCreateRequest`: request to create a proposed cognitive task.
- `TaskTransitionRequest`: request to move a task through the lifecycle state machine.
- `TaskRunRequest`: explicit request to run a task in dry-run or controlled mode.
- `TaskRunRecord`: auditable record for one task run attempt.
- `TaskLifecycleEvent`: generic goal, task, run, or schedule lifecycle event.
- `ScheduleRecord`: schedule metadata record owned by the Brain.
- `ScheduleCreateRequest`: request to store schedule metadata only.
- `CognitiveCycleStep`: one generic step in a cognitive cycle template.
- `CognitiveCycleTemplate`: stored manual cycle definition.
- `CognitiveCycleRunRequest`: explicit request to run a cycle.
- `CognitiveCycleRun`: auditable state for one cycle run.
- `CognitiveCycleStepRun`: auditable state for one cycle step.
- `SleepConsolidationRecord`: summary record from a sleep consolidation cycle.
- `SleepConsolidationRequest`: convenience request for manual sleep consolidation.
- `CycleStatus`: summary status for a generic cycle type.
- `ActorRecord`: local development actor metadata.
- `WorkspaceRecord`: workspace metadata owned by Brain core.
- `WorkspaceMembership`: actor membership and role within a workspace.
- `PermissionGrant`: generic allow or deny permission grant.
- `ActorContext`: request-time actor, workspace, role, permission, and scope context.
- `ScopeResolutionRequest`: request to resolve scopes for a generic action.
- `ScopeResolution`: resolved scope, permission, allow, and constraint result.
- `EvidenceRecord`: source evidence metadata and content addressing record.
- `EvidenceChunk`: deterministic text chunk for evidence search.
- `EvidenceIngestRequest`: request to ingest text or metadata-only evidence.
- `EvidenceIngestResponse`: evidence ingestion result.
- `EvidenceSearchRequest`: policy-gated deterministic evidence search request.
- `EvidenceSearchResult`: ranked evidence and chunk match.
- `EvidenceLink`: relation between evidence and a Brain-owned target.
- `GroundingStatement`: statement to check against evidence.
- `GroundingRequest`: request to ground statements in evidence.
- `GroundingClaim`: deterministic source support result.
- `GroundingResponse`: group of grounding claims.
- `BeliefClaim`: explicit scoped claim in the belief ledger.
- `BeliefClaimCreateRequest`: request to create a belief claim.
- `BeliefSupport`: evidence or provenance support for a claim.
- `BeliefSupportCreateRequest`: request to create a support relation.
- `BeliefContradiction`: explicit contradiction attached to a claim.
- `BeliefRevision`: immutable claim status or confidence revision.
- `BeliefQuery`: request to query belief state.
- `BeliefQueryResult`: query result with claims, supports, contradictions, and constraints.
- `TruthMaintenanceRequest`: request to run deterministic truth maintenance.
- `TruthMaintenanceRun`: persisted truth maintenance result.
- `ClaimExtractionRequest`: deterministic text-to-claim extraction request.
- `ClaimExtractionResult`: extracted claim proposals and constraints.
- `ObjectRef`: AION-owned object reference contract.
- `PolicyDecision`: authorization result.
- `RiskAssessmentRequest`: generic request to score one proposed action.
- `RiskAssessment`: persisted deterministic score, factors, decision, and constraints.
- `GuardrailRule`: generic safety rule evaluated after risk assessment.
- `GuardrailDecision`: persisted allow, approval-required, or blocked outcome.
- `RiskGuardrailEvaluationRequest`: combined risk and guardrail evaluation request.
- `RiskGuardrailEvaluation`: combined assessment, decision, and optional approval request.
- `ApprovalRequest`: pending or terminal approval record.
- `ApprovalCreateRequest`: request to create an approval item.
- `ApprovalDecisionRequest`: request to approve, deny, or cancel an item.
- `ApprovalDecision`: recorded human-control decision.
- `ApprovalInboxQuery`: scoped approval inbox query.
- `ApprovalLifecycleEvent`: approval state transition audit record.
- `DecisionTrace`: audit-ready decision record.
- `EvaluationRecord`: deterministic trace evaluation scores and lessons.
- `LearningSignal`: candidate learning signal.
- `ReflectionRecord`: deterministic review of trace, task, retrieval, planning, policy, or execution artifacts.
- `ReflectionRequest`: request to create a governed reflection from Brain-owned artifacts.
- `SkillProcedureStep`: one data-only procedural memory step.
- `SkillCandidate`: review candidate created from generic reflection evidence.
- `SkillRecord`: versioned procedural memory record stored as data.
- `SkillVersion`: immutable skill version snapshot.
- `SkillPromotionRequest`: explicit request to promote a reviewed candidate.
- `SkillPromotionResponse`: result of a promotion attempt.
- `SkillActivationRequest`: explicit request to activate, disable, or archive a skill.
- `SkillMatchRequest`: deterministic active-skill matching request.
- `SkillMatchResult`: ranked procedural memory match.
- `VisualTelemetryEvent`: graph activity event for future Brain visualization.
- `RetrievalRequest`: policy-gated request for multi-source context retrieval.
- `RetrievedContextItem`: normalized candidate from memory, capabilities, traces, or policy.
- `RetrievalResult`: ranked, deduplicated retrieval output plus constraints.
- `ContextFusionRequest`: request to assemble retrieved items for reasoning.
- `ContextBundle`: deterministic fused context that feeds `ContextPacket`.
- `ContractIndexRecord`: indexed source-code-owned contract shape.
- `InterfaceInventoryRecord`: indexed API, SDK, CLI, policy, setting, telemetry, or registry interface.
- `ContractSnapshot`: point-in-time contract and interface manifest.
- `CompatibilityRule`: deterministic interface compatibility rule.
- `CompatibilityScanRequest`: request to compare current or stored snapshots.
- `CompatibilityScan`: result of a compatibility scan.
- `InterfaceDriftFinding`: detected interface drift record.
- `MigrationNote`: informational migration guidance that does not execute.
- `ContractRegistryReport`: deterministic contract readiness summary.
- `BootstrapProfile`: local first-run profile defining required services, settings, checks, seed bundles, and constraints.
- `SeedBundle`: idempotent local seed bundle metadata with explicit idempotency keys.
- `SeedExecutionRequest`: request to dry-run or controlled-run one local seed bundle.
- `SeedExecutionRecord`: persisted result for one seed execution.
- `SetupFinding`: local setup doctor finding with severity, category, expected state, actual state, and recommended action.
- `SetupDoctorRequest`: request to inspect local setup readiness.
- `SetupDoctorResult`: deterministic setup doctor result with readiness booleans and score.
- `SetupReport`: persisted local readiness report.
- `BootstrapRunRequest`: request to run first-run bootstrap.
- `BootstrapRun`: persisted bootstrap run containing profile, seed executions, findings, readiness score, and result metadata.

Public APIs must return AION contracts or plain JSON derived from them. They
must not expose framework-specific objects from external engines.

Contract Registry contracts are read-only descriptions of existing AION
interfaces. They must not become generated source, mutate source contracts,
execute migrations, expose raw prompts, expose hidden reasoning, expose raw
headers, expose provider payloads, or carry secrets. Compatibility scans and
migration notes are advisory records until another governed AION gate consumes
them.

Bootstrap contracts are local readiness contracts only. They may describe local
profiles, seed bundles, setup findings, setup reports, and first-run bootstrap
runs. They must not represent production provisioning, package installation,
secret management, external provider setup, source mutation, tool execution,
or domain-specific setup logic.

AION-106 connector boundary contracts remain design-only. Future connector
contracts must treat connector metadata, capability claims, egress previews,
ingress responses, credential references, and returned data as untrusted until
validated. Public Brain contracts must not expose connector SDK objects,
provider SDK objects, HTTP client objects, raw headers, raw responses, raw
prompts, hidden reasoning, credentials, tokens, or secrets. Connector runtime,
external calls, credential storage, token storage, dynamic routes, activation,
and execution remain absent.

AION-107 operator action write-path contracts remain design-only. Future write
contracts must preserve separate action intent, dry-run preview, approval,
policy decision, action authorization, connector/target boundary, rollback,
audit/provenance, and release-gate evidence. Public Brain contracts must not
expose tool runners, connector runtimes, provider SDKs, HTTP clients, raw
headers, raw responses, raw prompts, hidden reasoning, credentials, tokens,
cookies, or secrets. Write execution, tool execution, action proposal
execution, controlled handoff execution, external calls, activation, hard
delete, and privileged bypass remain absent.

Reasoning contracts are Brain-owned. Model providers receive inference inputs
only through `ModelGatewayAdapter` and return `ModelCallRecord`. Public APIs
must not expose provider SDK objects, LangGraph objects, LiteLLM objects, OpenAI
objects, Anthropic objects, Gemini objects, or local model runtime objects.

Execution and module runtime contracts are Brain-owned. `ExecutionOrchestrator`
accepts `ExecutionRequest` and returns `ExecutionRun`. Capability calls move
through `CapabilityInvocationRequest`, `CapabilityInvocationResult`, and
compatible `CapabilityInvocationRecord` ledgers. Public APIs must not expose
Temporal objects, MCP objects, HTTP client objects, shell objects, browser
objects, tool SDK objects, provider objects, or vendor workflow objects.

Every external signal entering AION Brain must be normalized as an `AIONEvent`.
The Brain may generate missing trace and correlation IDs during intake, then
persist the event in the event ledger before publishing it for internal
subscribers.

Every future module must communicate with the Brain through events or capability
contracts. Modules must not bypass the Brain with private domain-specific APIs.

Event reactions are Brain-owned control-plane contracts. Subscriptions declare
generic trigger rules and generic targets only. Dispatch records and action
records are audit artifacts. Dead-letter records preserve failed controlled
actions for bounded replay. The Event Reaction Router must not expose
SQLAlchemy rows, NATS messages, framework runtime objects, or domain-specific
target internals.

Event reaction trigger matching is deterministic. It supports exact event
types, simple wildcard suffix patterns, exact source filters, and safe dotted
paths such as `payload.message`, `actor_id`, `workspace_id`, `trace_id`, and
`correlation_id`. It must not use eval, regex execution, dynamic Python, or
domain-specific classification.

The runtime boundary accepts `AIONEvent` and returns `DecisionTrace`. Internal
runtime state may include `BrainState`, `IntentFrame`, `ContextPacket`,
`ReasoningResult`, and `PlanGraph`, but public APIs must still return only
AION-owned contracts or plain JSON derived from them.

Plan steps must remain generic. They may reference generic action identifiers
such as `memory.retrieve`, `memory.write`, `context.compile`, `reasoning.run`,
`model.route`, `model.complete`, `capability.list`, `plan.create`,
`plan.execute`, `execution.step`, `approval.request`, `response.draft`,
`response.verify`, `evaluation.score`, and
`clarification.ask`, but not domain-specific capability names.

The persisted Brain loop extends traces into evaluation, learning, and visual
telemetry:

```text
DecisionTrace -> EvaluationRecord -> LearningSignal -> VisualTelemetryEvent
```

Learning signals remain candidates. Visual telemetry describes graph nodes,
edges, activity, and policy blocks for future UI work, but it does not introduce
UI-specific types into Brain core.

Reflection and skill contracts are Brain-owned. `ReflectionRecord` captures
observations, proposed generic changes, risks, confidence, and status.
`SkillCandidate` captures reviewable procedural memory proposals.
`SkillRecord` and `SkillVersion` store active or draft procedures as data only.
They do not contain executable Python, generated source, shell instructions, or
provider-specific model calls.

Skill promotion is an explicit policy-gated contract flow:

```text
LearningSignal -> ReflectionRecord -> SkillCandidate -> SkillRecord -> active procedural memory
```

`/brain/think` may attach `reflection_id` and `candidate_id` to a trace outcome
when explicitly requested by event payload flags, but it must never promote or
activate skills. Promotion and activation move only through
`SkillPromotionRequest` and `SkillActivationRequest`.

Retrieval contracts are Brain-owned. External memory engines, graph engines,
capability protocols, and trace stores provide candidates only. They must not
expose vendor objects through `RetrievalResult`, `ContextBundle`, or
`ContextPacket`.

Semantic memory contracts are Brain-owned. `SemanticMemoryAdapter` may use
pgvector or optional TurboVec internally, but public APIs return only
`SemanticMemoryResult`, `SemanticAdapterStatus`, `TurboVecIndexStatus`,
`TurboVecRebuildResponse`, or `SemanticIndexResponse`. TurboVec package objects,
index handles, rows, and vendor-specific errors must not cross the Brain API
boundary.

Graph memory contracts are Brain-owned. `GraphMemoryAdapter` may use Postgres
graph memory or optional Graphiti internally, but public APIs return only
`GraphNode`, `GraphEdge`, `GraphQueryResult`, `GraphMemoryAdapterStatus`,
`GraphitiConfigStatus`, `GraphitiSyncResponse`, or `GraphitiEpisodeResponse`.
Graphiti client objects, backend sessions, Neo4j or FalkorDB handles, package
types, and vendor-specific errors must not cross the Brain API boundary.
Graphiti is disabled by default and must fail closed or fall open to Postgres
graph memory according to explicit AION settings.

Skill retrieval is also Brain-owned. `skill_registry` retrieval returns active
skills as procedural memory candidates through `RetrievedContextItem`; it does
not expose repository rows or execute any skill procedure.

Belief state contracts are Brain-owned. `BeliefClaim` records an explicit
claim, not an absolute fact. `BeliefSupport` and `BeliefContradiction` record
why a claim is supported, weakened, contradicted, or stale. `BeliefRevision`
records all status and confidence changes. `TruthMaintenanceRun` records a
deterministic maintenance pass over claims. Public APIs must not expose database
rows, vector store objects, graph engine objects, external fact-checking
responses, or provider model outputs as belief contracts.

Claim extraction is deterministic in v0.1. `ClaimExtractionRequest` can produce
`BeliefClaimCreateRequest` proposals from dialogue or evidence only when
explicitly requested or locally configured. Extracted claims still pass through
policy and storage boundaries. Raw secrets, hidden reasoning, chain-of-thought,
and raw prompts must not be stored as claims.

Reasoning is recall and synthesis over supplied context, not unbounded truth.
The trace stores `reasoning_refs`, while the model call ledger stores
provider-neutral request and response records for audit.

Thinking and execution are separate. `DecisionTrace.execution_refs` defaults to
an empty list unless execution was explicitly requested through the execution
API.

Lifecycle contracts are Brain-owned. Goals, cognitive tasks, task runs,
schedules, and lifecycle events are generic and domain-neutral. Future modules
may request lifecycle changes through `AIONEvent` or capability contracts, but
they do not own lifecycle state or bypass the Brain lifecycle state machine.

Task runs are explicit. `TaskRunRequest.run_mode` can be `dry_run` or
`controlled`; there is no background worker mode in v0.1. `ScheduleRecord`
stores metadata only and does not imply automatic execution.

Identity and scope contracts are Brain-owned. `ActorRecord`, `WorkspaceRecord`,
`WorkspaceMembership`, and `PermissionGrant` remain local metadata in v0.1;
they are not production authentication records. `ActorContext` may be derived
from development `X-AION-*` headers only. Production authentication, OAuth,
SSO, cookies, bearer token parsing, and external identity providers are
deferred.

Permission grants use generic dotted permissions such as `memory.read`,
`memory.write`, `capability.read`, `trace.read`, `policy.authorize`, and
`scope.resolve`. They must not encode vertical domain rights. Deny grants
override allow grants during scope resolution. Disabled actors and archived
workspaces constrain actions before policy can authorize execution.

Risk, guardrail, and approval contracts are Brain-owned governance contracts.
`RiskAssessment` records describe risk; they do not authorize execution by
themselves. `GuardrailDecision` records describe the generic safety outcome.
`ApprovalRequest` records represent pending human control, and
`ApprovalDecision` records are evidence for a later governed request. Approval
does not automatically resume or run a prior action in v0.1.

Risk and guardrail APIs must return AION contracts only. They must not expose
OPA responses, SQLAlchemy rows, adapter exceptions, vendor SDK objects, raw
headers, or secret payloads.

Event intake, memory retrieval, and Brain thinking may carry actor ID,
workspace ID, security scope, trace ID, and correlation ID forward from
`ActorContext`, but public APIs still return only AION contracts or plain JSON
derived from them.

Evidence contracts are Brain-owned. `EvidenceRecord`, `EvidenceChunk`,
`EvidenceLink`, and `GroundingClaim` preserve source material, content hashes,
source provenance, and deterministic grounding state. Memory, graph memory,
retrieval, reasoning, plans, executions, skills, evaluations, and learning
signals can reference evidence IDs, but they must not treat recall or generated
output as truth without evidence linkage.

`EvidenceIngestRequest` supports text evidence and metadata-only content
references in v0.1. It must not fetch URLs, parse PDFs, run OCR, or process
binary uploads. `ObjectRef` is an AION-owned object reference; future object
stores such as MinIO remain behind adapter boundaries and do not leak storage
SDK objects through Brain public contracts.

Capability runtime contracts are the only accepted module runtime boundary.
Future modules may provide implementations, but Brain public contracts remain
`ModuleRuntime`, `CapabilityRuntimeBinding`, `ModuleHealthCheck`,
`CapabilityInvocationRequest`, and `CapabilityInvocationResult`. Modules never
self-authorize, and runtime registration never implies execution approval.

MCP contracts are Brain-owned. `MCPServerRecord`, `MCPToolDescriptor`,
`MCPCapabilityMapping`, `MCPServerRegistrationRequest`, `MCPSyncRequest`,
`MCPSyncResponse`, `MCPInvocationRequest`, `MCPInvocationResult`,
`MCPServerHealth`, and `MCPAdapterStatus` describe the optional MCP boundary
without exposing MCP SDK objects. MCP tool descriptors are candidates only;
AION mapping supplies capability IDs, risk level, permissions, memory scopes,
execution mode, and audit semantics.

MCP is disabled by default. A registered MCP capability does not imply
controlled execution permission. Dry-run remains the safe path, while
controlled invocation must pass AION policy and transport safety checks. Public
Brain APIs must never expose MCP clients, sessions, transports, prompts,
resources, raw tool payload wrappers, or SDK-specific errors.

Visual projection contracts are Brain-owned and frontend-agnostic:

- `BrainVisualNode` defines node identity, type, status, intensity, scope, and references.
- `BrainVisualEdge` defines typed generic relations between nodes.
- `BrainPulse` defines short-lived activity against a node or edge.
- `BrainVisualCluster` defines deterministic node-family groupings.
- `BrainMapRequest` and `BrainMap` define projection input and output.
- `BrainMapSnapshot` defines a persisted projection.
- `VisualTelemetryQuery` defines scoped telemetry reads.
- `TraceTimelineRequest`, `TraceTimelineEvent`, and `TraceTimeline` define
  ordered trace projection.
- `ObservabilityEvent` and `ObservabilitySummary` define the local
  observability boundary.

These contracts contain no frontend framework objects, renderer state, vendor
observability objects, raw headers, or secret payloads.

## Memory Governance Contracts

Memory governance contracts are Brain-owned and domain-neutral:

- `MemoryGovernanceRule` defines a generic lifecycle rule, scope, sensitivity,
  conditions, action, priority, and metadata.
- `MemoryGovernanceDecision` records the selected action and matched rules for
  one memory lifecycle evaluation.
- `MemoryDecayRecord` records deterministic decay scoring and factors.
- `MemoryGovernanceEvaluationRequest` evaluates one `MemoryRecord` for a
  generic action such as `memory.write`, `memory.retrieve`, or `memory.decay`.
- `ForgetMemoryRequest` and `ForgetMemoryResult` define policy-gated,
  approval-aware soft forgetting.
- `MemoryConflictScanRequest`, `MemoryConflictResolutionRequest`, and
  `MemoryConflict` define generic conflict detection and resolution records.
- `MemoryCompactionRequest` and `MemoryCompactionResult` define deterministic,
  model-free compaction.
- `MemoryRetentionSweepRequest` and `MemoryRetentionSweepResult` define
  retention and decay sweeps.

These contracts never expose vector database rows, graph engine records, raw
evidence content, approval internals, policy engine internals, or domain-specific
memory rules. Semantic and graph memory engines provide recall candidates only;
governance decides lifecycle status before recall becomes context.

## Durable Workflow Contracts

Durable workflow contracts are Brain-owned and domain-neutral:

- `WorkflowStep` defines one generic step with action type, risk, optional
  capability ID, input template, output expectation, timeout, retryability, and
  metadata.
- `WorkflowRetryPolicy` defines bounded retry attempts and deterministic
  backoff.
- `WorkflowDefinition` defines persistent workflow metadata, trigger type,
  owner scope, steps, retry policy, timeout, risk, status, and creator.
- `WorkflowCreateRequest` requests definition creation.
- `WorkflowRunRequest` requests a dry-run or controlled workflow run.
- `WorkflowRun` records durable run state, trigger, input, output, error,
  retry count, step runs, and timestamps.
- `WorkflowStepRun` records one step attempt.
- `WorkflowTransitionRequest` requests pause, resume, cancel, retry, or other
  governed run transition.
- `WorkflowHeartbeat` records bounded worker or scheduler heartbeat state.
- `WorkflowWorkerRecord` records local worker lifecycle state.
- `WorkflowEngineStatus` reports local engine readiness and counts.
- `TemporalAdapterStatus` reports the optional Temporal adapter boundary.

Workflow contracts never expose Temporal SDK objects, queue clients, database
rows, shell commands, provider clients, or domain-specific business processes.
Task metadata may explicitly request a workflow handoff, but it does not
authorize execution by itself.

## Replay and Regression Contracts

- `BrainSnapshot` is immutable, scoped, content-addressed Brain state.
- `SnapshotCreateRequest` requests a sanitized snapshot.
- `ReplayRequest` requests a local dry-run or deterministic replay.
- `ReplayRun` records replay identity, snapshots, status, and comparison.
- `TraceComparison` records normalized differences, score, and drift.
- `RegressionCase` and `RegressionCaseCreateRequest` define golden traces.
- `RegressionRunRequest`, `RegressionRunResult`, and `RegressionRun` define
  selected local regression execution and reporting.
- `EvalAdapterRunRequest` and `EvalAdapterRunResult` preserve an AION-owned
  boundary around optional evaluation systems.

No replay or regression contract exposes runtime graph objects, database rows,
external evaluation objects, raw headers, or secret values.

## Kernel Contracts

- `KernelAdapterConfig` records selected provider-neutral adapter names.
- `KernelBootRecord` records deterministic boot diagnostics and outcome.
- `KernelServiceRecord` describes one assembled repository, adapter, service,
  runtime, or infrastructure boundary.
- `DiagnosticCheck` is one typed, secret-free diagnostic result.
- `KernelSelfTestRequest` and `KernelSelfTestResult` define local dry self-test
  input and output.
- `KernelStatus` reports current assembly, services, boot, and self-test state.
- `ContractExport` contains OpenAPI and AION-owned JSON schemas.
- `ArchitectureBoundaryReport` records source-boundary violations.

Kernel contracts never contain vendor client objects, database rows, secrets,
or domain-specific behavior.

## Model Gateway Contracts

- `ModelProvider` defines a provider boundary by ID, type, endpoint reference,
  safe config metadata, status, and health.
- `ModelProfile` defines a model profile with mode, privacy level, risk level,
  token limits, cost hints, latency class, and safe metadata.
- `ModelGatewayRequest` wraps a `PromptPacket`, mode, risk, scope, actor and
  workspace IDs, an optional preferred profile, and external-use intent.
- `ModelGatewayResponse` returns a provider-neutral `ModelCallRecord`,
  `ModelUsageRecord`, optional `PromptRedactionRecord`, route decision, output,
  and status.
- `PromptRedactionRecord` records deterministic prompt inspection without
  storing secret values.
- `ModelBudgetRecord` defines local budget controls.
- `ModelUsageRecord` records token and cost estimates.
- `ModelProviderHealth` records local health status.

Model gateway contracts never expose provider SDK clients, raw provider
responses, API keys, auth headers, or vendor-specific response objects.
AION v0.1 uses deterministic local reasoning by default. External model calls
require explicit configuration, policy permission, and budget approval.

## Autonomy Governor Contracts

Autonomy contracts are Brain-owned and domain-neutral:

- `AutonomyProfile` defines default mode, maximum mode, maximum risk, allowed
  and denied generic actions, approval modes, and explicit capability gates.
- `AutonomyProfileCreateRequest` creates a bounded profile. Defaults are
  conservative and do not enable full autonomy.
- `RunLevelRecord` and `SetRunLevelRequest` define temporary operating mode
  overrides.
- `DelegationGrant` and `DelegationGrantRequest` define scoped, risk-bounded
  controlled delegation.
- `AutonomyDecisionRequest` asks whether one generic action may proceed.
- `AutonomyDecision` records requested mode, resolved mode, allow/deny,
  approval requirement, constraints, profile, run level, and delegation refs.
- `AutonomyStatus` reports the current profile, active run level, delegations,
  effective mode, risk ceiling, and constraints.
- `AutonomyLifecycleEvent` records profile, run-level, delegation, and decision
  changes for audit and visual telemetry.

Autonomy contracts never expose external tool clients, model SDK objects,
workflow engines, raw headers, secrets, or domain-specific rules. Autonomy is a
governance boundary, not an execution engine.

## Cognitive Cycle Contracts

Cognitive cycle contracts are Brain-owned, manual, and domain-neutral:

- `CognitiveCycleStep` declares a generic step type, risk level, required flag,
  input template, and metadata.
- `CognitiveCycleTemplate` stores a named cycle template with type, status,
  owner scope, steps, risk, and approval requirement.
- `CognitiveCycleRunRequest` asks AION Brain to run exactly one cycle in
  `dry_run` or `controlled` mode.
- `CognitiveCycleRun` records status, actor, workspace, owner scope, step runs,
  output, error, risk, approval, and autonomy decision references.
- `CognitiveCycleStepRun` records one step state and output.
- `SleepConsolidationRecord` records reviewed working-memory slots, decayed
  memories, detected conflicts, compaction runs, reflections, skill candidate
  counts, regression checks, visual snapshots, and summary output.
- `CycleStatus` reports the newest run and run counts for a cycle type.

Cycle contracts never expose scheduler loops, workflow-engine clients,
database rows, policy-engine internals, raw headers, secrets, model provider
objects, vector database clients, or domain-specific business rules. Sleep
consolidation is a governed summary of existing Brain services, not a memory
truth engine and not an execution engine.

## Attention and Working Memory Contracts

- `FocusSession` records active, paused, or ended cognitive focus.
- `FocusSessionCreateRequest` requests an explicit focus session.
- `FocusTransitionRequest` moves focus through allowed lifecycle states.
- `WorkingMemorySlot` stores short-lived cognitive state and compact refs.
- `WorkingMemoryWriteRequest` writes one scoped working-memory slot.
- `WorkingMemoryQuery` retrieves active working-memory slots.
- `AttentionSignal` records a generic signal competing for focus.
- `AttentionSignalCreateRequest` requests signal creation.
- `AttentionDecisionRequest` asks AION to choose focus inputs.
- `AttentionDecision` records selected signals, slots, and references.
- `ContextBudget` records deterministic source allocation and overflow.
- `ContextBudgetRequest` requests a scoped context budget.
- `InterruptRecord` records a pending or decided interruption.
- `InterruptCreateRequest` requests an interrupt.
- `InterruptDecisionRequest` accepts, defers, dismisses, or resolves one.

Attention contracts are generic and domain-neutral. Working memory is
short-lived state, not long-term truth and not chain-of-thought storage.

## Command and Consistency Contracts

Command and consistency contracts are Brain-owned and domain-neutral:

- `BrainCommand` records command type, target, mode, status, payload, result,
  error, and policy/autonomy/risk/approval references.
- `CommandDispatchRequest` asks the Command Bus to record and dispatch one
  generic Brain operation.
- `CommandDispatchResult` returns the command record, duplicate flag,
  idempotency key, outbox IDs, and message.
- `IdempotencyRecord`, `IdempotencyCheckRequest`, and
  `IdempotencyCheckResult` define retry-safe duplicate detection.
- `OutboxMessage`, `OutboxPublishRequest`, `OutboxProcessRequest`, and
  `OutboxProcessResult` define the manual transactional outbox.
- `InboxMessage`, `InboxReceiveRequest`, and `InboxReceiveResult` define
  inbound message deduplication.
- `ProcessingLease` defines local processing leases.
- `ConsistencyCheckRequest` and `ConsistencyCheckResult` define safe
  consistency checks and limited repairs.

These contracts do not expose SQLAlchemy rows, queue messages, NATS clients,
shell execution, worker loops, raw headers, secrets, or domain-specific logic.

## API Hardening Contracts

API hardening contracts are Brain-owned and provider-neutral:

- `AIONError` defines the stable public error shape with code, category,
  message, detail, trace ID, correlation ID, request ID, retryability, and
  timestamp.
- `AIONErrorResponse` wraps every public error.
- `AIONSuccessEnvelope` is available for new support endpoints without forcing
  older successful routes to change shape.
- `AIONPageRequest`, `AIONPageInfo`, and `AIONPage` define cursor-oriented
  pagination.
- `AIONFilter` and `AIONSort` define safe generic filtering and sorting
  expressions.
- `RequestContext` defines per-request IDs and propagation metadata.
- `APIRequestRecord` defines safe request audit records without bodies or raw
  headers.
- `OpenAPIHygieneReport` defines schema hygiene results.

API contracts never expose raw exceptions, stack traces, provider SDK objects,
SQLAlchemy rows, raw SQL, raw headers, secrets, or domain-specific API rules.

## Module Developer Contracts

- `ModulePackage`
- `ModulePackageCreateRequest`
- `CapabilityCertificationCheck`
- `CapabilityCertification`
- `ModuleCertificationRun`
- `ModuleCertificationRequest`
- `ModuleCompatibilityReport`
- `ModuleContractTestCase`
- `ModuleScaffoldRequest`
- `ModuleScaffold`

These contracts are generic, provider-neutral, and contract-only. They do not
contain executable module code or domain workflow logic.

## Sandbox, Secret, and Connector Contracts

AION Brain owns these generic control-plane contracts:

- `ResourceLimits`
- `EgressRule`
- `FilesystemRule`
- `RuntimePermission`
- `SandboxProfile`
- `SandboxProfileCreateRequest`
- `SandboxValidationCheck`
- `SandboxValidationResult`
- `SandboxRunRequest`
- `SandboxRunResult`
- `SecretRef`
- `SecretRefCreateRequest`
- `ConnectorDefinition`
- `ConnectorCreateRequest`
- `RuntimePermissionGrant`
- `RuntimePermissionGrantRequest`

`SandboxRunRequest` validates a proposed run; it does not authorize direct code
execution. `SecretRef` stores references only and never raw secret material.
`ConnectorDefinition` stores connector metadata only and never opens external
connections in v0.1. Runtime permission grants are explicit, scoped, and
metadata-only.

These contracts never expose Docker clients, Firecracker tooling, subprocesses,
SQLAlchemy rows, raw secrets, raw headers, external connector clients, or
domain-specific connector semantics.

## Policy Catalog Contracts

AION Brain owns these generic policy governance contracts:

- `PolicyActionCatalogEntry`
- `PermissionCatalogEntry`
- `RoleTemplate`
- `PolicySimulationRequest`
- `PolicySimulationResult`
- `PolicyTestCase`
- `PolicyTestRunRequest`
- `PolicyTestRun`
- `PolicyCoverageReport`
- `PolicyBundleExportRequest`
- `PolicyBundleRecord`
- `OPAStatus`

Policy action and permission names are dotted lowercase generic identifiers.
They must not use domain-specific prefixes. Role templates are reusable
permission collections; modules do not self-authorize through them.

## Scenario and Release Baseline Contracts

AION Brain owns these release-readiness contracts:

- `ScenarioStep` defines one deterministic validation step.
- `ScenarioDefinition` defines a scoped reusable scenario.
- `ScenarioCreateRequest` requests scenario creation.
- `ScenarioRunRequest` requests a dry-run or controlled scenario run.
- `ScenarioStepRun` records one step result.
- `ScenarioRun` records a complete scenario result and comparison.
- `DemoFixture` defines a safe generic local fixture.
- `DemoFixtureLoadRequest` requests dry-run or controlled fixture loading.
- `DemoFixtureLoadResult` records fixture load results.
- `ReleaseBaselineRequest` selects scenarios and quality gates for a release.
- `ReleaseBaselineReport` records the combined readiness result.

Persisted scenario definitions and fixture records require non-empty
`owner_scope`. API routes may fill missing request scope from `ActorContext`,
but stored records and run records remain explicitly scoped.

Scenario contracts must remain deterministic, generic, and secret-free. They
must not call external providers, require optional adapters, enable full
autonomy, execute external tools, or encode vertical workflow logic. Future
domain scenario packs must live outside Brain core.

`PolicySimulationRequest` is explicitly side-effect-free and returns a
`PolicySimulationResult` that includes the decision and an explanation showing
the target action was not executed. `PolicyTestCase` defines deterministic
expected decision fields. `PolicyBundleRecord` stores secret-free exported
catalog/test/Rego content with a deterministic content hash.

These contracts never expose raw OPA responses, OPA clients, SQLAlchemy rows,
raw secrets, raw headers, or domain-specific policy rules.

## Versioning and Freeze Contracts

AION Brain owns these release freeze contracts:

- `VersionManifest`
- `FeatureRegistryEntry`
- `DeprecationPolicy`
- `CompatibilityMatrix`
- `MigrationBaseline`
- `ReleaseArtifactManifest`
- `SDKCompatibilityReport`
- `FreezeGateCheck`
- `FreezeGateRunRequest`
- `FreezeGateRun`
- `ReleasePackageFile`
- `ReleasePackageManifest`
- `ReleasePackageValidation`
- `ReleaseHandoffReport`
- `ReleasePackageRequest`
- `ReleasePackage`
- `SBOMPlaceholder`

Versioning contracts define release metadata only. They never expose
SQLAlchemy rows, optional adapter SDK objects, shell command results, raw
headers, raw secrets, package upload handles, or domain module internals.

`VersionManifest` records the frozen release surface. `FeatureRegistryEntry`
records generic Brain feature keys and status. `MigrationBaseline` records
migration hashes and destructive migration findings. `ReleaseArtifactManifest`
records metadata-only file checksums. `FreezeGateRun` records local readiness
checks and recommendations.

Release package contracts define local handoff artifacts only.
`ReleasePackageRequest` asks for a local dry-run or package creation.
`ReleasePackageManifest` records included artifacts, exclusions, counts, and a
root checksum. `ReleasePackageValidation` records deterministic package checks.
`ReleaseHandoffReport` records local verification commands, known limits, and
next steps. `SBOMPlaceholder` is metadata-only and does not represent a full
transitive SBOM.

## Backup and Restore Preview Contracts

AION Brain owns local backup and restore-preview contracts:

- `BackupResourceType`
- `BackupManifest`
- `BackupRequest`
- `BackupFile`
- `BackupJob`
- `RestoreConflict`
- `RestorePreviewRequest`
- `RestorePreview`
- `RestoreRequest`
- `RestoreJob`
- `BackupValidationReport`

Backup contracts are application-level and local. They describe exported AION
records, resource JSONL files, checksums, redaction mode, owner scope,
compatibility metadata, restore-preview conflicts, and validation reports. They
never expose SQLAlchemy rows, raw database snapshots, `pg_dump` output, raw
headers, raw secrets, cloud upload handles, or domain module internals.

Restore preview is a planning contract only. It records conflicts, missing
dependencies, restorable counts, blocked counts, and a plan. Restore apply is
disabled by default in v0.1 and must remain approval-gated before any future
application writer can use it.

## Resilience Contracts

AION Brain owns these resilience control-plane contracts:

- `DependencyHealth`
- `RetryPolicy`
- `CircuitBreaker`
- `DegradedModeEvent`
- `FaultInjectionRule`
- `ResilienceTestRunRequest`
- `ResilienceTestRun`
- `ResilienceStatus`

Resilience contracts describe local posture only. They never expose raw
infrastructure clients, raw SQLAlchemy rows, transport messages, secrets, raw
headers, background worker handles, or external failover mechanisms.

`RetryPolicy` records bounded retry metadata. `CircuitBreaker` records local
breaker state. `DegradedModeEvent` records fallback posture and constraints.
`FaultInjectionRule` is inert unless local fault injection is explicitly
enabled. `ResilienceTestRun` is a deterministic local readiness report used by
operators and the freeze gate.

## Dialogue and Response Contracts

AION Brain owns these dialogue contracts:

- `DialogueSession`
- `DialogueSessionCreateRequest`
- `DialogueMessage`
- `DialogueMessageCreateRequest`
- `DialogueTurnRequest`
- `DialogueTurnResult`
- `ClarificationRequest`
- `ClarificationAnswerRequest`
- `DialogueFeedback`

AION Brain owns these response contracts:

- `ResponseComposeRequest`
- `ResponseDraft`
- `ResponseVerification`
- `ResponseDeliveryRecord`

Dialogue contracts describe backend session state only. They never expose
frontend component state, provider-specific chat objects, external delivery
handles, raw headers, raw prompts, hidden reasoning, chain-of-thought, raw
secrets, SQLAlchemy rows, or domain module internals.

`DialogueTurnResult` is the public result of one bounded dialogue turn. It can
include a sanitized user message, decision trace reference, response draft,
verification record, local delivery record, clarification request, memory
handoff records, and policy decisions. It never performs controlled execution.

`ResponseDraft` is a deterministic local draft. It records status, content hash,
grounding references, memory references, evidence references, clarification
references, constraints, and metadata. Verification and delivery are separate
contracts so future interfaces can render or transport responses without
changing AION Brain semantics.

## Concept and Entity Contracts

AION Brain owns these concept contracts:

- `ConceptRecord`
- `ConceptCreateRequest`
- `ConceptArchiveRequest`

AION Brain owns these entity and canonical reference contracts:

- `EntityRecord`
- `EntityCreateRequest`
- `EntityAlias`
- `EntityAliasCreateRequest`
- `EntityMention`
- `EntityMentionCreateRequest`
- `ReferenceLink`
- `ReferenceLinkCreateRequest`
- `EntityResolutionRequest`
- `EntityResolutionCandidate`
- `EntityResolutionResult`
- `EntityQuery`
- `EntityQueryResult`
- `EntityMergeProposal`
- `EntityMergeProposalCreateRequest`
- `EntitySplitProposal`
- `EntitySplitProposalCreateRequest`

Concept and entity contracts are generic Brain contracts. They never expose
SQLAlchemy rows, NATS messages, external NLP objects, provider chat objects,
frontend component state, raw headers, raw secrets, hidden reasoning, or
domain-specific ontology internals.

Entity references are canonical pointers, not verified truth. They can connect
dialogue, responses, evidence, memories, beliefs, graph nodes, traces, commands,
tasks, audit entries, concepts, and other entities through reference links.
Belief contracts still own claims and truth-maintenance state.

## Situation and Temporal State Contracts

AION Brain owns these situation contracts:

- `SituationRecord`
- `SituationCreateRequest`
- `SituationQuery`
- `SituationQueryResult`
- `SituationProjectionRequest`
- `SituationProjectionResult`
- `ContextContinuityRecord`
- `ContextContinuityRequest`

AION Brain owns these temporal state contracts:

- `StateAtom`
- `StateAtomCreateRequest`
- `StateTransition`
- `TemporalStateWindow`
- `TemporalStateWindowRequest`

Situation contracts describe current projected Brain state only. They never
expose source database rows, raw headers, raw prompts, hidden reasoning,
secrets, model-provider objects, frontend state, or domain-specific workflow
internals.

State atoms are projected observations with provenance references. They are
recall and context continuity aids, not canonical truth.

## Decision Contracts

AION Brain owns these decision contracts:

- `DecisionFrame`
- `DecisionFrameCreateRequest`
- `DecisionOption`
- `DecisionOptionCreateRequest`
- `UtilityProfile`
- `UtilityProfileCreateRequest`
- `OptionEvaluation`
- `DecisionEvaluationRequest`
- `TradeoffMatrix`
- `CounterfactualRunRequest`
- `CounterfactualRun`
- `DecisionRecord`
- `DecisionRecordRequest`
- `DecisionRecommendation`

Decision records are not execution requests. Counterfactuals project declared
generic effects only. Utility weights stay generic and domain-neutral.

## Outcome and Effect Contracts

AION Brain owns these outcome contracts:

- `ExpectedEffect`
- `ExpectedEffectCreateRequest`
- `ObservedEffect`
- `ObservedEffectCreateRequest`
- `OutcomeRecord`
- `OutcomeCreateRequest`
- `EffectVerificationRequest`
- `EffectVerificationRun`
- `CausalAttribution`
- `OutcomeFeedback`
- `OutcomeQuery`
- `OutcomeQueryResult`

Expected effects describe intended generic effects. Observed effects describe
local Brain observations. Outcome records join references and verification
state. Verification runs compare effects but do not prove truth.

Outcome contracts must not expose SQLAlchemy rows, provider SDK objects,
external observability objects, raw headers, raw secrets, hidden reasoning,
or domain-specific workflow internals.

Outcome feedback is a governed learning input only. It is never automatic
remediation, skill promotion, source mutation, or external execution.

## Experience and Learning Synthesis Contracts

AION Brain owns these learning synthesis contracts:

- `ExperienceRecord`
- `ExperienceCreateRequest`
- `ExperienceQuery`
- `ExperienceQueryResult`
- `LearningPattern`
- `PatternMiningRequest`
- `PatternMiningRun`
- `LessonRecord`
- `LearningSynthesisRequest`
- `LearningSynthesisRun`
- `SkillCandidateSuggestion`
- `RegressionCandidateSuggestion`

`ExperienceRecord` is the only generic observed-experience ledger contract.
It references source records and never replaces their canonical lifecycle.

`LearningPattern` and `LessonRecord` are review contracts. They summarize
generic repeated experience shapes and lessons without executing behavior.

`SkillCandidateSuggestion` is not an active skill, and
`RegressionCandidateSuggestion` is not a regression case. Conversion and
acceptance are review state only in v0.1.

Learning synthesis contracts must not expose SQLAlchemy rows, provider SDK
objects, external intelligence repository internals, raw prompts, raw headers,
secrets, generated code, executable test bodies, or domain-specific workflow
internals.

## Self Model Contracts

AION Brain owns these self-model contracts:

- `SelfModelProfile`
- `SelfDescriptionRequest`
- `SelfDescription`
- `CapabilityAwarenessRecord`
- `LimitationRecord`
- `LimitationCreateRequest`
- `ConfidenceCalibration`
- `ConfidenceCalibrationRequest`
- `SelfAssessmentRequest`
- `SelfAssessmentRun`
- `IntrospectionSnapshotRequest`
- `IntrospectionSnapshot`

Self-model contracts are descriptive and diagnostic. They must not execute
capabilities, approve actions, override policy, override autonomy, enable
adapters, mutate runtime configuration, promote skills, or invent capabilities.

Capability and limitation claims must come from awareness records, local
configuration, kernel diagnostics, and governed AION contracts. They must not
claim sentience, production readiness, full autonomy, unavailable integrations,
or domain expertise.

## Explanation Contracts

AION Brain owns these explanation contracts:

- `ExplanationStep`
- `ExplanationRecord`
- `ExplanationRequest`
- `WhyNotRequest`
- `WhyNotAnswer`
- `TraceNarrativeRequest`
- `TraceNarrative`
- `ExplanationVerification`
- `ExplanationFeedback`

Explanation contracts describe observable system state only. They may include
references to evidence, memory, beliefs, decisions, outcomes, audit entries,
provenance links, policy decisions, autonomy decisions, risk assessments, and
approval requests.

Explanation contracts must not include chain-of-thought, hidden reasoning,
raw prompts, raw headers, provider payloads, raw third-party client objects,
SQLAlchemy rows, secrets, or domain-specific workflow internals.

Why-not answers expose generic blockers and next possible steps. Trace
narratives expose ordered public timeline events, key decisions, blockers,
approvals, outcomes, evidence refs, and audit refs.

## Instruction and Preference Contracts

AION Brain owns these instruction and preference contracts:

- `InstructionRecord`
- `InstructionCreateRequest`
- `PreferenceRecord`
- `PreferenceCreateRequest`
- `ConstraintRecord`
- `StyleProfile`
- `StyleProfileCreateRequest`
- `InstructionConflict`
- `InstructionResolutionRequest`
- `InstructionResolutionResult`
- `PreferenceLearningCandidate`

Instruction contracts must not store hidden prompts, chain-of-thought, raw
secrets, raw headers, provider payloads, SQLAlchemy rows, or domain-specific
workflow internals. Preferences are not policy. Style preferences and learned
preference candidates cannot override policy, autonomy, approval requirements,
runtime configuration, sandbox limits, capability limits, or grounding rules.

## Grounding and Citation Contracts

AION Brain owns these grounding contracts:

- `GroundingSource`
- `GroundingSourceCreateRequest`
- `CitationRecord`
- `CitationCreateRequest`
- `UnsupportedStatement`
- `ResponseCitationMap`
- `GroundingVerificationRequest`
- `GroundingVerificationRun`
- `SourceCoverageReport`
- `GroundingQuery`
- `GroundingQueryResult`

Grounding contracts must not include hidden reasoning, chain-of-thought, raw
prompts, raw headers, provider payloads, raw third-party client objects,
SQLAlchemy rows, secrets, or domain-specific citation internals.

Grounding validates support. It does not create truth. Memory recall remains
weak support unless backed by evidence or supported belief, and contradicted
beliefs cannot strongly ground a response.

## Prompt and Model Input Contracts

AION Brain owns these prompt governance contracts:

- `PromptSection`
- `PromptTemplate`
- `PromptTemplateCreateRequest`
- `PromptFragment`
- `PromptFragmentCreateRequest`
- `PromptPacket`
- `PromptCompileRequest`
- `PromptCompileResult`
- `PromptBoundaryCheck`
- `PromptInjectionFinding`
- `PromptPreviewRequest`
- `PromptPreview`
- `ModelInputManifest`

Prompt contracts are provider-neutral. They must not include provider SDK
objects, provider-specific hidden prompt schemas, chain-of-thought, hidden
reasoning, raw rendered prompts, raw headers, raw secrets, SQLAlchemy rows, or
domain-specific prompt packs.

Retrieved context is untrusted unless another governed AION contract says
otherwise. Memory recall must be labeled `memory_recall`; memory recall is not
truth. Model input manifests store hashes and metadata for the Model Gateway
handoff, not raw provider payloads.

## Model Output Governance Contracts

AION Brain owns these model output governance contracts:

- `ModelOutputCreateRequest`
- `ModelOutputRecord`
- `ModelOutputSegment`
- `StructuredOutputValidation`
- `ResponseCandidate`
- `ToolIntentCandidate`
- `OutputGovernanceRequest`
- `OutputGovernanceRun`
- `ModelOutputQuery`
- `ModelOutputQueryResult`

Model output contracts are provider-neutral. They must not expose provider SDK
objects, provider chat objects, raw provider payloads, raw prompts, raw
headers, hidden reasoning, chain-of-thought, raw secrets, SQLAlchemy rows, or
domain-specific output internals.

`ModelOutputRecord` stores a raw-output hash and redacted output. Raw output is
not stored by default. `ModelOutputSegment` represents deterministic parsed
output only. `StructuredOutputValidation` validates generic JSON-like output.
`ResponseCandidate` is a local proposal, not delivery. `ToolIntentCandidate`
captures model-suggested tool or capability intents without executing them.

## Action Proposal and Handoff Contracts

AION Brain owns these action proposal contracts:

- `ActionProposal`
- `ActionProposalCreateRequest`
- `ActionBlocker`
- `ActionProposalReview`
- `ActionProposalReviewRequest`
- `ExecutionHandoffRequest`
- `ExecutionHandoff`
- `ToolIntentReview`
- `ToolIntentReviewRequest`
- `ActionProposalQuery`
- `ActionProposalQueryResult`

Action proposal contracts are provider-neutral, target-neutral, and
domain-neutral. They describe proposed actions, blockers, reviews, and handoff
metadata only. They must not execute actions, approve actions automatically,
dispatch commands, run workflows, invoke capabilities, call MCP tools, run
sandboxes, call external services, expose hidden reasoning, expose raw prompts,
store raw secrets, or include domain-specific action types.

`ToolIntentReview` converts captured tool-intent candidates into review
records and, only when explicitly requested and safe, action proposals.
`ExecutionHandoffRequest` is the explicit gate for handoff to governed AION
systems. Dry-run handoff builds the target request without dispatching it.

## Run Supervision Contracts

AION Brain owns these run supervision and control contracts:

- `RunTargetRef`
- `RunSupervisionRecord`
- `RunSupervisionCreateRequest`
- `RunStatusSample`
- `RunControlRequest`
- `RunControlRequestCreateRequest`
- `RunTimeoutPolicy`
- `CompensationPlan`
- `CompensationStep`
- `CompensationPlanCreateRequest`
- `RunSupervisionReport`
- `RunSupervisionReportRequest`

Run supervision contracts are target-neutral and domain-neutral. They describe
observation, status sampling, manual control requests, timeout policies,
compensation planning, and reports. They must not execute target actions,
start background supervisors, auto-cancel runs, auto-resume runs, execute
compensation, call external systems, bypass target APIs, expose raw headers,
store raw secrets, or include domain-specific remediation logic.

`RunSupervisionRecord` tracks the Brain-owned observation record for a target
run. `RunStatusSample` captures deterministic local status polling.
`RunControlRequest` is a manual request and defaults to dry-run.
`RunTimeoutPolicy` detects stale or timed-out runs without auto-cancelling.
`CompensationPlan` and `CompensationStep` are proposals only until explicitly
converted into action proposals.

## Notification and Alert Contracts

AION Brain owns these internal notification contracts:

- `NotificationTopic`
- `NotificationSubscription`
- `NotificationPublishRequest`
- `NotificationRecord`
- `NotificationQuery`
- `AlertCreateRequest`
- `AlertRecord`
- `AlertQuery`
- `EscalationPolicy`
- `EscalationRecord`
- `NotificationDigest`

Notification contracts are generic, local-only, and operator-facing. They must
not expose external notification provider objects, webhook payloads, email/SMS
clients, raw headers, hidden reasoning, raw prompts, provider payloads, secrets,
SQLAlchemy rows, or domain-specific alert logic.

`NotificationTopic` defines local topic metadata. `NotificationSubscription`
declares local channels such as `operator_inbox`, `actor_inbox`,
`workspace_feed`, `audit_feed`, `visual_feed`, and `local_digest`.
`NotificationRecord` is a delivered local record and does not imply external
delivery. `AlertRecord` is a local review signal and does not mutate source
systems. `EscalationRecord` is a local queue record with `local_only=true`.
`NotificationDigest` summarizes local notifications and alerts
deterministically.

## Temporal Scheduler Contracts

AION Brain owns these local scheduler contracts:

- `RecurrenceRule`
- `ScheduleRecord`
- `ScheduleCreateRequest`
- `ScheduleDueItem`
- `ReminderRecord`
- `ReminderCreateRequest`
- `SchedulerTickRequest`
- `SchedulerTickRun`
- `SchedulePolicy`
- `SchedulerReport`

Scheduler contracts are generic and domain-neutral. `RecurrenceRule` defines
local recurrence semantics. `ScheduleRecord` stores scheduler metadata and
the next due boundary. `ScheduleDueItem` records a due occurrence and does not
execute a target. `ReminderRecord` is local-only and does not send external
messages. `SchedulerTickRequest` is the explicit entry point for dry-run or
controlled local tick evaluation. `SchedulerTickRun` is the audit record for
one tick. `SchedulePolicy` and `SchedulerReport` describe scheduler posture
without running target actions.

Public scheduler contracts may use compatibility aliases such as
`recurrence_rule` for `recurrence`, `owner_scope` for tick `scope`,
`schedule_policy_id` for `policy_id`, and `rule` for policy `conditions`.
The Brain keeps the scheduler local, deterministic, and non-executing in
v0.1.

## Incident Contracts

AION Brain owns these incident correlation contracts:

- `IncidentSignal`
- `IncidentSignalCreateRequest`
- `IncidentRecord`
- `IncidentCreateRequest`
- `IncidentQuery`
- `IncidentCorrelationRule`
- `IncidentCorrelationRequest`
- `IncidentCorrelationRun`
- `RootCauseCandidate`
- `RootCauseCandidateRequest`
- `RecoveryReview`
- `RecoveryReviewRequest`

Incident contracts are local, generic, and Brain-owned. `IncidentSignal`
normalizes a local AION signal without changing the source record.
`IncidentRecord` is an AION-owned grouping record and is not remediation.
`IncidentCorrelationRun` records deterministic grouping results. Root cause
candidates are hypotheses, not truth. Recovery reviews are operator review
artifacts, not execution plans.

Incident contracts must not expose external incident system payloads, raw
headers, hidden reasoning, raw prompts, provider payloads, secrets, SQLAlchemy
rows, source-system internals, or domain-specific incident logic.

## Global Resource Registry Contracts

AION Brain owns these registry and link-integrity contracts:

- `ResourceDescriptor`
- `ResourceIndexRecord`
- `ResourceIndexUpsertRequest`
- `ResourceReferenceLink`
- `ResourceReferenceCreateRequest`
- `BrokenReference`
- `OrphanedResource`
- `ReferenceValidationRequest`
- `ReferenceValidationRun`
- `RegistryRebuildRequest`
- `RegistryRebuildRun`
- `RegistrySnapshot`
- `ResourceRegistryQuery`
- `ResourceRegistryQueryResult`

`ResourceDescriptor` is a safe descriptor for a source-system record. It uses
the canonical URI form `aion://{resource_type}/{resource_id}` with optional
`?trace_id={trace_id}`. Descriptors contain metadata, summary, scope, status,
visibility, sensitivity, references, and hashes; they do not make the registry
the source of truth.

`ResourceReferenceLink` is a registry-owned directed link between two resource
URIs. `BrokenReference` and `OrphanedResource` are integrity findings only.
They do not repair, acknowledge, delete, or mutate source records.

`ReferenceValidationRun` records deterministic link checks. `RegistryRebuildRun`
records deterministic index rebuilds from local safe descriptors.
`RegistrySnapshot` records a deterministic snapshot of registry-owned index and
link metadata.

Registry contracts must not expose raw headers, hidden reasoning, raw prompts,
provider payloads, secrets, SQLAlchemy rows, source-system internals, or
domain-specific resource logic.

## Data Lifecycle Contracts

AION Brain owns these lifecycle contracts:

- `LifecyclePolicy`
- `LifecyclePolicyCreateRequest`
- `RetentionClassification`
- `LifecycleEvaluationRequest`
- `LifecycleEvaluationRun`
- `ArchiveCandidate`
- `RedactionCandidate`
- `PurgePreview`
- `LifecycleReviewRecord`
- `LifecycleReport`

Lifecycle contracts are advisory and generic. `LifecyclePolicy` describes
retention class, timing, backup, approval, and action-on-match metadata.
`RetentionClassification` records how a registry resource is classified for
review. `LifecycleEvaluationRun` records deterministic evaluation output and
explicit created counts. `ArchiveCandidate` and `RedactionCandidate` are review
candidates only. `PurgePreview` is an impact report and must keep
`hard_delete_allowed=false`. `LifecycleReviewRecord` records manual review
decisions. `LifecycleReport` summarizes local lifecycle posture.

Lifecycle contracts must not mutate source records, execute archive, execute
redaction, execute purge, call object stores, call external services, expose
raw headers, hidden reasoning, raw prompts, provider payloads, secrets,
SQLAlchemy rows, source-system internals, or domain-specific retention logic.

## Extension Registry Contracts

AION Brain owns these extension registry contracts:

- `ExtensionManifest`
- `ExtensionPackage`
- `ExtensionCapabilityDeclaration`
- `ExtensionDependencyDeclaration`
- `ExtensionCompatibilityRequest`
- `ExtensionCompatibilityRun`
- `ExtensionIntakeRequest`
- `ExtensionIntakeRun`
- `ExtensionReviewRequest`
- `ExtensionReview`
- `ExtensionInstallPlan`
- `ExtensionQuery`
- `ExtensionQueryResult`

`ExtensionManifest` is a metadata-only declaration. It may describe generic
capabilities, dependencies, policy action names, settings, routes, events,
resources, and sandbox requirements, but it must not include executable code,
package bytes, raw secret access, unrestricted autonomy, external execution, or
domain-specific workflow logic.

`ExtensionPackage` stores manifest metadata after controlled intake.
`ExtensionCapabilityDeclaration` and `ExtensionDependencyDeclaration` are
descriptive records only and do not activate capabilities or install
dependencies. `ExtensionCompatibilityRun` records local deterministic checks.
`ExtensionReview` records operator review. `ExtensionInstallPlan` is a future
install record and must keep `executable=false` and
`execution_allowed=false`.

Extension Registry contracts must not expose raw headers, hidden reasoning,
raw prompts, provider payloads, secrets, SQLAlchemy rows, third-party module
internals, source code payloads, or domain-specific module behavior.

## Module Binding Contracts

AION Brain owns these module slot and capability binding contracts:

- `ModuleSlot`
- `ModuleSlotCreateRequest`
- `CapabilityBinding`
- `CapabilityBindingCreateRequest`
- `BindingValidationRequest`
- `BindingValidationRun`
- `ModuleMountPlan`
- `RouteBindingPreview`
- `BindingConflict`
- `ModuleBindingQuery`
- `ModuleBindingQueryResult`

`ModuleSlot` is an inactive metadata record for a future module position. It
may reference extension packages, declared capabilities, contracts, policy
actions, settings, sandbox profiles, mount plans, and owner scope. It is not a
loaded module.

`CapabilityBinding` is an inactive metadata record for a future capability
mapping. It may declare schemas, required policy actions, required settings,
required contracts, risk level, sandbox requirements, and target runtime
metadata. It is not an active capability and must not register itself.

`BindingValidationRun` records deterministic local checks. `BindingConflict`
records binding-owned findings only. `ModuleMountPlan` is non-executable and
must keep `executable=false` and `execution_allowed=false`. `RouteBindingPreview`
is preview-only and must keep `registration_allowed=false`.

Module binding contracts must not expose raw headers, hidden reasoning, raw
prompts, provider payloads, secrets, SQLAlchemy rows, source code payloads,
runtime client objects, third-party module internals, or domain-specific module
logic.

## Module Activation Contracts

AION Brain owns these module activation request gate contracts:

- `ModuleActivationRequest`
- `ModuleActivationCreateRequest`
- `ActivationBlocker`
- `ActivationGateRun`
- `ActivationReviewRequest`
- `ActivationReview`
- `ActivationPlan`
- `RuntimeRegistrationPreview`
- `ModuleActivationQuery`
- `ModuleActivationQueryResult`

`ModuleActivationRequest` is a metadata-only request to evaluate future
activation. It must keep `activation_allowed=false` and
`execution_allowed=false`.

`ActivationGateRun` records deterministic checks and blockers. Gate runs may
report blocked status, but they must not mutate module runtime state.

`ActivationPlan` is a non-executable plan and must keep `executable=false` and
`execution_allowed=false`.

`RuntimeRegistrationPreview` previews possible runtime registration metadata
and must keep `registration_allowed=false`.

Module activation contracts must not expose raw headers, hidden reasoning, raw
prompts, provider payloads, secrets, SQLAlchemy rows, runtime client objects,
package internals, source code payloads, capability execution results, or
domain-specific module logic.

## Capability Conformance Contracts

AION Brain owns these generic conformance contracts:

- `ConformanceProfile`
- `CapabilityTestVector`
- `MockInvocationRecord`
- `ConformanceRun`
- `ConformanceFinding`
- `ReadinessAssessment`
- `ConformanceQuery`
- `ConformanceQueryResult`

`MockInvocationRecord` is a schema-only simulation record. It stores hashes,
redacted inputs, placeholder output shapes, booleans for schema/policy/sandbox
validity, and findings. It must not represent real capability execution.

`ReadinessAssessment` summarizes local extension/module/binding readiness. It
must keep `activation_ready=false` in v0.1 and may block future activation when
required conformance records are missing or failing.

Conformance contracts must not expose raw headers, hidden reasoning, raw
prompts, provider payloads, secrets, SQLAlchemy rows, source code payloads,
runtime client objects, package bytes, third-party module internals,
capability execution results, or domain-specific module logic.

## Golden Path Contracts

AION Brain owns these golden path contracts:

- `GoldenPathScenario`
- `GoldenPathFixturePack`
- `GoldenPathRunRequest`
- `GoldenPathStepResult`
- `GoldenPathAssertionResult`
- `GoldenPathRun`
- `GoldenPathReport`
- `GoldenPathQuery`

`GoldenPathScenario` defines one deterministic local scenario. `GoldenPathFixturePack`
contains synthetic scenario-owned fixtures only. `GoldenPathRunRequest` defaults
to dry-run mode. `GoldenPathStepResult` records local service availability and
dry-run output summaries. `GoldenPathAssertionResult` records deterministic
assertion outcomes and fails closed for unknown assertion types.

`GoldenPathRun` is the canonical run record. It must report no external calls,
no tool execution, and no non-scenario source mutation. `GoldenPathReport`
summarizes release readiness and blocks release readiness when critical
assertions fail or a run is blocked.

Golden path contracts must not expose raw headers, hidden reasoning, raw
prompts, provider payloads, secrets, SQLAlchemy rows, source-system internals,
external service clients, frontend framework objects, or domain-specific
workflow logic.

## Release Candidate Contracts

AION Brain owns these release candidate contracts:

- `ReleaseCandidate`
- `ReleaseCandidateCreateRequest`
- `VerificationCheck`
- `VerificationMatrix`
- `VerificationMatrixCreateRequest`
- `RCGateRunRequest`
- `RCGateRun`
- `RCFinding`
- `RCEvidencePack`
- `RCReport`
- `RCQuery`

`ReleaseCandidate` is a local readiness shell for one version or candidate key.
`VerificationMatrix` defines required and optional generic checks.
`VerificationCheck` normalizes local script and service evidence.
`RCGateRun` aggregates checks into readiness score, blockers, warnings, and
release-ready status. `RCFinding` stores reviewable blockers and warnings.
`RCEvidencePack` and `RCReport` store redacted evidence and operator-facing
summaries only.

Release candidate contracts must not expose raw headers, hidden reasoning, raw
prompts, provider payloads, secrets, SQLAlchemy rows, deployment credentials,
external service clients, source-code patches, or domain-specific release
logic.

## Release Handoff Contract Note

AION-079 adds no new runtime contracts. It documents and validates existing
release candidate, bootstrap, golden path, freeze, release package, operator,
extension, module binding, conformance, SDK, and CLI interfaces for local
handoff.

## Module Mock Runtime Contracts

AION Brain owns these module mock runtime contracts:

- `ModuleMockProfile`
- `ModuleMockProfileCreateRequest`
- `ModuleMockInvocationRequest`
- `ModuleMockInvocationCreateRequest`
- `ModuleMockRun`
- `ModuleMockOutput`
- `ModuleMockFinding`
- `ModuleMockQuery`
- `ModuleMockQueryResult`

`ModuleMockProfile` describes deterministic simulation rules and JSON-like
shape hints. `ModuleMockInvocationRequest` stores redacted dry-run input and
expected output shape metadata. `ModuleMockRun` is the canonical dry-run
result. `ModuleMockOutput` stores synthetic output only. `ModuleMockFinding`
stores reviewable metadata problems. `ModuleMockQuery` and
`ModuleMockQueryResult` aggregate local records.

Module mock runtime contracts must keep activation, execution, external-call,
and code-loading flags false. They must not expose raw headers, hidden
reasoning, raw prompts, provider payloads, secrets, SQLAlchemy rows, source
code payloads, package bytes, third-party module internals, live runtime
client objects, real capability execution results, or domain-specific module
logic.

## Model Provider Hardening Contracts

AION-086 adds provider-readiness contracts:

- `ModelProviderProfile`
- `PromptEgressPreview`
- `ModelProviderSimulation`
- `ModelProviderReadiness`
- `ModelProviderBlocker`
- `ProviderHardeningQuery`

These contracts describe readiness metadata only. They must not include API
keys, provider SDK objects, provider endpoints, raw prompts, hidden reasoning,
credential payloads, model invocation results, or tool execution records.

## Operator Console Contracts

AION-088 adds read-only Operator Console contracts:

- `ConsoleView`
- `ConsoleDataSource`
- `ConsoleActionDescriptor`
- `ConsoleViewSection`
- `ConsoleViewModelRequest`
- `ConsoleViewModel`
- `ConsoleAuditRequest`
- `ConsoleAuditResult`
- `ConsoleWorkflowStep`
- `ConsoleWorkflowMap`

These contracts summarize existing Brain state for future UI consumers. They
are redacted and read-only, expose actions as descriptors only, and return
unavailable sections when optional source services are missing.

Operator Console contracts must preserve no runtime UI, no raw prompt exposure,
no hidden reasoning exposure, no secret exposure, no activation, no execution,
no external calls, no package installation, no code loading, and no privileged
policy bypass.

## Governed Operator Action Contracts

AION-092 adds:

- `OperatorActionRequest`
- `OperatorActionCreateRequest`
- `OperatorActionPreview`
- `OperatorActionBlocker`
- `OperatorActionReviewRequest`
- `OperatorActionReview`
- `OperatorActionQuery`
- `OperatorActionQueryResult`

These contracts are dry-run governance records. `mode` must be `dry_run`.
`execution_allowed`, `external_calls_allowed`, and `activation_allowed` must
remain `false`. Reviews record decisions only; approval does not execute.
Payloads are redacted before storage and contracts reject protected prompt,
hidden reasoning, and secret-like content.

## Local Auth Contracts

AION-094 adds `LocalOperatorIdentity`, `LocalAuthContext`,
`DevIdentitySimulationRequest`, `RolePermission`, `ConsoleRoleFilterRequest`,
`ConsoleRoleFilterResult`, `LocalAuthAuditRequest`, and
`LocalAuthAuditResult`.

These contracts are dev-only and non-privileged. They require
`production_auth=false`, `credentials_present=false`, `session_present=false`,
`write_allowed=false`, `execute_allowed=false`, `activation_allowed=false`, and
`external_calls_allowed=false` where applicable.

## Local Session Contracts

AION-095 adds `LocalSessionPreview`, `LocalSessionPreviewRequest`,
`LocalSessionContext`, `LocalSessionBoundaryCheck`,
`LocalSessionAuditRequest`, and `LocalSessionAuditResult`.

Local session contracts are synthetic and read-only. `production_session=false`,
`credential_backed=false`, `token_issued=false`, `cookie_issued=false`,
`persistent=false`, `write_allowed=false`, `execute_allowed=false`,
`activation_allowed=false`, and `external_calls_allowed=false` are contract
invariants.

## Role Access Contracts

AION-096 extends local auth contracts with `RoleAccessDecision` and
`RoleAccessAudit`. Decisions fail closed for unknown roles or views and carry
hard-false write, execution, activation, and external-call flags. Audits pass
only when forbidden actions remain visible and redaction is applied.

## Action Authorization Contracts

AION-097 adds `DryRunActionAuthorizationRequest`,
`DryRunActionAuthorizationDecision`, `ActionAuthorizationBlocker`,
`ActionAuthorizationAuditRequest`, and `ActionAuthorizationAuditResult`.
Decisions can allow dry-run preview or review records only. Contract invariants
keep `write_allowed=false`, `execution_allowed=false`,
`activation_allowed=false`, and `external_calls_allowed=false`.

## Auth Runtime Contracts

AION-099 adds `AuthRuntimeStatus`, `MockClaimsPreviewRequest`,
`MockClaimsPreviewResult`, `AuthRuntimeBlocker`, `AuthRuntimeAuditRequest`, and
`AuthRuntimeAuditResult`.

These contracts are disabled-auth and mock-only. Production auth, external
identity, credentials, token issuance, cookie issuance, session persistence,
login endpoints, and logout endpoints must remain false. Mock claims preview
maps synthetic claims to a preview ActorContext only and does not authenticate,
authorize execution, or bypass the local role matrix.
## Connector Runtime Contracts

AION-108 adds `aion_brain.contracts.connector_runtime` for disabled connector
runtime evidence. The contracts cover hard-off status, mock connector manifests,
egress preview requests/results, ingress preview requests/results, blockers,
and audit requests/results.

Contract validation keeps runtime-enabling fields false: external calls,
credentials, token storage, activation, and route registration remain disabled.

## AION-109 Connector Review Contract Boundary

AION-109 adds no new runtime contracts. It documents the review gate and
regression evidence that prove the AION-108 connector contracts remain
disabled, preview-only, synthetic, and non-executing before future connector
implementation phases.
