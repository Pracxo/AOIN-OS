# AOIN OS Implementation Queue

## Queued

No queued tasks.

## In Progress

No tasks in progress.

## Done

### AION-001 - AION Brain v0.1 Cognitive Kernel Scaffold
Status: Done
Priority: High
Created: 2026-06-06 23:39 BST
Completed: 2026-06-06 23:39 BST

Instruction:
Create the first AION OS scaffold for AION Brain, a domain-neutral cognitive
kernel with FastAPI, Pydantic contracts, adapter placeholders, Docker Compose,
docs, tests, and quality gates.

Acceptance Evidence:
- Repository structure exists under the AOIN OS workspace.
- Brain API exposes `GET /health`.
- Docker default stack starts.
- `/health` returns the required JSON payload.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Planned imported intelligence repos appear only as adapter placeholders or docs.

### AION-002 - Core Configuration and Infrastructure Readiness
Status: Done
Priority: High
Created: 2026-06-06 23:45 BST
Completed: 2026-06-06 23:45 BST

Instruction:
Add application settings, structured logging, infrastructure readiness
boundaries, `/health/live`, `/health/ready`, tests, and docs while preserving
the original `/health` response.

Acceptance Evidence:
- `/health` response is unchanged.
- `/health/live` returns alive metadata.
- `/health/ready` reports Postgres, Redis, NATS, and OPA dependency status.
- Readiness failures are converted into degraded responses.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Docker default stack builds and starts.

### AION-003 - Event Intake Engine and Event Ledger
Status: Done
Priority: High
Created: 2026-06-06 23:50 BST
Completed: 2026-06-06 23:50 BST

Instruction:
Build the AION Event Intake Engine with `POST /brain/events`, Postgres event
ledger persistence, NATS publishing, JetStream-enabled NATS, repository tests,
and API tests.

Acceptance Evidence:
- `POST /brain/events` accepts `AIONEvent` request bodies.
- Missing trace and correlation IDs are generated during intake.
- Events persist to the canonical `aion_events` Postgres ledger.
- Accepted events publish to `aion.events.<event_type>`.
- NATS publishing failure returns `published: false` without undoing persistence.
- NATS starts with JetStream enabled.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Docker default stack builds and starts.

### AION-004 - Policy Engine and OPA Authorization Gate
Status: Done
Priority: High
Created: 2026-06-06 23:55 BST
Completed: 2026-06-06 23:55 BST

Instruction:
Add the first generic AION Policy Engine integration with `PolicyRequest`,
`OPAAdapter`, `/brain/policy/authorize`, generic Rego policy decisions, tests,
and documentation.

Acceptance Evidence:
- `PolicyRequest` and `PolicyDecision` are AION-owned contracts.
- `POST /brain/policy/authorize` returns `PolicyDecision`.
- OPA decisions are loaded from `/v1/data/aion/brain/decision`.
- OPA failures fail closed with `policy_engine_unavailable`.
- Rego policy contains only generic Brain action types.
- Low-risk `memory.retrieve` can be allowed.
- High-risk `capability.invoke` requires approval.
- Unknown risks are denied.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Docker default stack builds and starts.

### AION-005 - Memory Fabric v0.1
Status: Done
Priority: High
Created: 2026-06-07 00:00 BST
Completed: 2026-06-07 00:00 BST

Instruction:
Build AION Memory Fabric v0.1 with canonical Postgres memory metadata, a
memory service, deterministic lexical retrieval, policy-gated write/retrieve,
soft delete, adapter-ready boundaries, tests, and docs.

Acceptance Evidence:
- `POST /brain/memory` creates generic `MemoryRecord` contracts.
- `GET /brain/memory/{memory_id}` returns active records.
- `POST /brain/memory/retrieve` performs deterministic lexical recall.
- `DELETE /brain/memory/{memory_id}` soft-deletes records.
- Retrieval excludes soft-deleted records.
- Policy denial blocks memory writes.
- Memory types are restricted to generic Brain classes.
- TurboVec, pgvector, and Graphiti remain placeholders only.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Docker default stack builds and starts.

### AION-008 - Brain Runtime, Planner, and LangGraph Adapter
Status: Done
Priority: High
Created: 2026-06-07 00:11 BST
Completed: 2026-06-07 00:11 BST

Instruction:
Build the first deterministic executable AION Brain runtime with `BrainState`,
a generic deterministic planner, `BrainRuntimeAdapter`, LangGraph behind the
adapter boundary, `/brain/plan`, `/brain/think`, tests, and documentation.

Acceptance Evidence:
- `BrainState` is available as an AION-owned runtime contract.
- `Planner.create_plan` returns generic `PlanGraph` steps only.
- `LangGraphRuntimeAdapter` returns public `DecisionTrace` contracts.
- LangGraph imports remain isolated to `runtime/langgraph_runtime.py`.
- `POST /brain/plan` returns a deterministic plan graph.
- `POST /brain/think` runs Event -> Intent -> Context -> Plan -> Policy -> Trace.
- Policy denial produces a `blocked_by_policy` trace outcome.
- No LLM calls or real capability invocation occur.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.
- Docker default stack builds and starts.
- Live smoke checks passed for `/health`, `/brain/plan`, and `/brain/think`.

### AION-009 - Audit Ledger, Evaluator, Learning Signals, and Visual Brain Telemetry
Status: Done
Priority: High
Created: 2026-06-07 00:18 BST
Completed: 2026-06-07 00:18 BST

Instruction:
Complete the first full deterministic Brain loop with persisted decision
traces, policy decisions, evaluation records, candidate learning signals, visual
telemetry events, trace APIs, tests, and docs.

Acceptance Evidence:
- `POST /brain/think` persists `DecisionTrace` records.
- Policy decisions from the Brain loop are persisted by trace.
- Deterministic `EvaluationRecord` creation is implemented.
- `LearningSignal` creation remains candidate-only.
- Visual telemetry events are emitted for future Brain graph visualization.
- Trace APIs expose trace, evaluation, learning, and telemetry records.
- `POST /brain/evaluate` and `POST /brain/learn` return public AION contracts.
- No UI code, LLM calls, real module execution, or uncontrolled self-modification exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-010 - Semantic Memory Baseline with pgvector and TurboVec Upgrade Path
Status: Done
Priority: High
Created: 2026-06-07 00:25 BST
Completed: 2026-06-07 00:25 BST

Instruction:
Build the first semantic memory baseline with an embedding adapter boundary,
deterministic local hash embeddings, pgvector-backed semantic recall,
semantic indexing/retrieval APIs, TurboVec placeholder boundary, tests, and
docs.

Acceptance Evidence:
- `EmbeddingAdapter` and deterministic `HashEmbeddingAdapter` are implemented.
- `SemanticMemoryAdapter` exposes AION contracts only.
- `InMemorySemanticMemoryAdapter` supports deterministic semantic tests.
- `PgVectorSemanticMemoryAdapter` indexes and retrieves through pgvector behind an adapter boundary.
- `TurboVecSemanticMemoryAdapter` remains a placeholder and does not import TurboVec.
- Docker Postgres image is now `pgvector/pgvector:pg16`.
- Semantic memory endpoints exist for index, retrieve, and reindex-all.
- No external embedding API or model provider is called.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-011 - Temporal Graph Memory Baseline and Obsidian-Style Brain Map
Status: Done
Priority: High
Created: 2026-06-07 00:36 BST
Completed: 2026-06-07 00:36 BST

Instruction:
Build generic temporal graph memory with AION graph contracts, Postgres graph
tables, graph repository and adapters, Graphiti placeholder boundary, policy
gated graph APIs, Context Compiler integration, visual telemetry activation
events, tests, and documentation.

Acceptance Evidence:
- `GraphNode`, `GraphEdge`, `GraphQuery`, `GraphQueryResult`, and `GraphUpsertResponse` are implemented.
- `GraphMemoryAdapter` is the public graph memory boundary.
- `InMemoryGraphAdapter` supports tests for scope, deletion, expiry, query, and neighbors.
- `PostgresGraphAdapter` and graph repository implement the local temporal graph baseline.
- `GraphitiGraphMemoryAdapter` remains a placeholder and does not import Graphiti.
- Graph memory endpoints exist for node/edge upsert, get, query, neighbors, and soft delete.
- Context Compiler can include graph node and edge IDs when graph context is available.
- Graph upserts emit `memory_node_activated` visual telemetry events.
- No external graph service is required.
- No domain-specific graph logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-012 - Retrieval Router and Context Fusion
Status: Done
Priority: High
Created: 2026-06-07 08:04 BST
Completed: 2026-06-07 08:04 BST

Instruction:
Build the Retrieval Router and Context Fusion layer so Context Compiler uses a
single policy-gated retrieval pipeline for lexical memory, semantic memory,
graph memory, capabilities, and optional trace candidates.

Acceptance Evidence:
- Retrieval contracts are implemented: `RetrievalRequest`, `RetrievedContextItem`, `RetrievalResult`, `ContextFusionRequest`, and `ContextBundle`.
- `RetrievalRouter` policy-gates, collects, deduplicates, scores, sorts, persists, and emits telemetry.
- `ContextFusionEngine` creates deterministic `ContextBundle` output with no LLM calls.
- `ContextCompiler` delegates retrieval to `RetrievalRouter` and fills `ContextPacket` from `ContextBundle`.
- Retrieval persistence is backed by `aion_context_retrievals`.
- Debug endpoints exist for retrieval query, fusion, and persisted retrieval lookup.
- Source policy blocks and source failures become constraints instead of crashes.
- No external AI service, real Graphiti, TurboVec, Mem0, Cognee, or LiteLLM integration exists.
- No domain-specific retrieval logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-013 - Reasoning Mesh and Model Gateway Boundary
Status: Done
Priority: High
Created: 2026-06-07 08:19 BST
Completed: 2026-06-07 08:19 BST

Instruction:
Build the AION Reasoning Mesh with provider-neutral reasoning contracts,
prompt packets, model route decisions, deterministic local reasoning, model
call ledger persistence, LiteLLM placeholder boundary, reasoning APIs, Brain
loop integration, visual telemetry, tests, and documentation.

Acceptance Evidence:
- `PromptPacket`, `ModelRouteDecision`, `ReasoningRequest`, `ReasoningResult`,
  and `ModelCallRecord` are Brain-owned contracts.
- `ReasoningMesh` policy-gates `reasoning.run`, `model.route`, and
  `model.complete`.
- v0.1 routes only to `aion-local` / `deterministic-reasoner-v0`.
- `DeterministicReasoningAdapter` makes no external model calls.
- LiteLLM remains a placeholder and is not imported.
- Reasoning runs and model call records persist through the ledger repository.
- `POST /brain/reason`, `GET /brain/reason/{reasoning_id}`, and
  `GET /brain/model-calls/{model_call_id}` are implemented.
- `/brain/think` includes `reasoning_refs` and the deterministic reasoning loop
  outcome.
- Visual telemetry includes reasoning and model boundary event types.
- No provider-specific SDK objects or domain-specific logic exist.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-014 - Execution Orchestrator and Plan Step State Machine
Status: Done
Priority: High
Created: 2026-06-07 08:33 BST
Completed: 2026-06-07 08:33 BST

Instruction:
Build the AION Execution Orchestrator with execution contracts, persistent
execution runs, step state machine, approval checkpoints, capability invocation
boundary, Temporal placeholder, execution APIs, trace readiness metadata,
evaluation/learning/telemetry updates, tests, and documentation.

Acceptance Evidence:
- `ExecutionRequest`, `ExecutionRun`, `ExecutionStepRun`,
  `ApprovalCheckpoint`, and `CapabilityInvocationRecord` are Brain-owned
  contracts.
- Execution state transition helpers validate allowed run and step transitions.
- `ExecutionOrchestrator` supports `dry_run` and `controlled` modes without
  external side effects.
- Dry run does not invoke capabilities.
- Controlled capability steps go through `CapabilityInvoker` and return
  structured `not_implemented` for v0.1.
- High-risk steps create approval checkpoints when approval is absent.
- Execution runs, steps, approvals, and invocation records persist through the
  execution repository.
- `POST /brain/execute`, execution lookup, steps, approvals, cancel, and
  approval resolution endpoints are implemented.
- `/brain/think` does not auto-execute and returns execution readiness metadata.
- Temporal remains a placeholder and is not imported.
- No shell, browser, external tool, external model, or domain action is
  executed.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-015 - Module Bus and Capability Runtime Gateway
Status: Done
Priority: High
Created: 2026-06-07 08:51 BST
Completed: 2026-06-07 08:51 BST

Instruction:
Build the AION Module Bus and Capability Runtime Gateway with runtime
contracts, registration, capability-to-runtime binding, safe local internal
runtime execution, placeholder HTTP/MCP runtimes, gateway-backed capability
invocation, APIs, policy updates, telemetry, tests, and documentation.

Acceptance Evidence:
- `ModuleRuntime`, `CapabilityRuntimeBinding`, `ModuleHealthCheck`,
  `ModuleRuntimeRegistrationRequest`, `CapabilityBindingRequest`,
  `CapabilityInvocationRequest`, and `CapabilityInvocationResult` are
  Brain-owned contracts.
- Runtime config rejects secret-like keys and endpoint references.
- Module runtime, capability binding, and health check ledgers persist through
  `ModuleRuntimeRepository`.
- `CapabilityRuntimeGateway` owns policy checks, binding lookup, runtime
  health checks, dry-run short-circuiting, controlled invocation, and telemetry.
- `CapabilityInvoker` delegates to the gateway when configured and preserves
  `CapabilityInvocationRecord` compatibility.
- `local_internal` executes only safe generic internal capabilities.
- `local_stub` returns `not_implemented`.
- HTTP and MCP runtimes are placeholders only; no HTTP network calls or MCP SDK
  imports exist.
- Module runtime and capability invocation APIs are implemented.
- Execution controlled mode can invoke a safe local internal capability through
  `CapabilityInvoker -> CapabilityRuntimeGateway`.
- Dry-run execution still avoids runtime adapter invocation.
- No shell, browser, SaaS, external tool, external model, or domain action is
  executed.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-016 - Goal Manager, Cognitive Task Queue, and Lifecycle Control Plane
Status: Done
Priority: High
Created: 2026-06-07 09:09 BST
Completed: 2026-06-07 09:09 BST

Instruction:
Build the generic AION Goal Manager and Cognitive Task Queue with goal records,
cognitive task records, task lifecycle transitions, explicit dry-run task
runner, schedule metadata, NATS lifecycle publishing, policy gates, audit and
telemetry integration, tests, and docs.

Acceptance Evidence:
- `GoalRecord`, `GoalCreateRequest`, and `GoalTransitionRequest` are Brain-owned contracts.
- `CognitiveTask`, `TaskCreateRequest`, `TaskTransitionRequest`, `TaskRunRequest`,
  `TaskRunRecord`, and `TaskLifecycleEvent` are Brain-owned contracts.
- `ScheduleRecord` and `ScheduleCreateRequest` store schedule metadata only.
- Goal and task lifecycle state machines validate transitions.
- Goal, task, run, lifecycle event, and schedule tables are covered by migration `0010`.
- `POST /brain/goals`, goal lookup, goal list, and goal transition endpoints are implemented.
- `POST /brain/tasks`, task lookup, task list, task transition, task run, and run list endpoints are implemented.
- `POST /brain/schedules`, schedule lookup, schedule list, pause, and cancel endpoints are implemented.
- Task runs are explicit, policy-gated, and dry-run avoids execution side effects.
- Lifecycle event publishing is best-effort and does not undo persistence.
- `/brain/think` advertises goal/task endpoints and only creates lifecycle records with explicit payload flags.
- No scheduler loop, Temporal integration, external side effects, or domain workflow logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-017 - Reflection Engine, Skill Registry, and Learning Promotion Gates
Status: Done
Priority: High
Created: 2026-06-07 09:28 BST
Completed: 2026-06-07 09:28 BST

Instruction:
Build the AION Reflection Engine and Skill Registry so evaluated traces, task
runs, retrieval results, reasoning runs, and execution outcomes can become
controlled procedural learning candidates.

Acceptance Evidence:
- `ReflectionRecord` and `ReflectionRequest` are Brain-owned contracts.
- `SkillProcedureStep`, `SkillCandidate`, `SkillRecord`, `SkillVersion`,
  `SkillPromotionRequest`, `SkillPromotionResponse`, `SkillActivationRequest`,
  `SkillMatchRequest`, and `SkillMatchResult` are Brain-owned contracts.
- Reflection and skill registry tables are covered by migration `0011`.
- `POST /brain/reflections`, reflection lookup, and reflection list endpoints are implemented.
- Skill candidate creation, candidate lookup/list/status, promotion, skill lookup/list,
  skill transition, and skill match endpoints are implemented.
- Reflection creation is policy-gated through `reflection.create`.
- Candidate creation, promotion, activation, disable/archive, and matching are policy-gated.
- Promotion creates versioned skill records but does not auto-activate unless explicitly requested and allowed.
- `/brain/think` reflects only with `reflect: true`, creates candidates only with
  `create_skill_candidate: true`, and never promotes or activates skills.
- Retrieval Router can expose active skills as `skill_registry` procedural memory.
- Planner can record matched active skill IDs in plan metadata without executing skills.
- Visual telemetry includes reflection, candidate, skill, activation, archive, and skill retrieval events.
- Skills remain data records, not generated code.
- No dynamic code execution, shell execution, external model calls, source rewriting, or domain-specific skill logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-018 - Identity, Workspace, Scope, and Permission Control Plane
Status: Done
Priority: High
Created: 2026-06-07 13:11 BST
Completed: 2026-06-07 13:11 BST

Instruction:
Build the local development identity, workspace, scope, and permission control
plane so Brain actions carry actor context, workspace context, security scope,
and generic permission metadata from the start.

Acceptance Evidence:
- `ActorRecord`, `WorkspaceRecord`, `WorkspaceMembership`, `PermissionGrant`,
  `ActorContext`, `ScopeResolutionRequest`, and `ScopeResolution` are
  Brain-owned contracts.
- Dev-mode context reads only `X-AION-*` headers and production authentication
  remains deferred.
- Actor, workspace, membership, permission, and scope APIs are implemented.
- Identity mutations and scope resolution are policy-gated.
- Permission grants use generic dotted permissions and deny grants win over
  allow grants.
- Disabled actors and archived workspaces constrain scope resolution.
- Event intake, memory retrieval, and `/brain/think` propagate actor context
  where practical.
- Identity and scope operations emit visual telemetry events.
- No OAuth, SSO, cookies, bearer-token auth, external identity provider, or
  domain-specific permission logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-019 - Evidence Vault, Source Grounding, and Content Addressing
Status: Done
Priority: High
Created: 2026-06-07 13:28 BST
Completed: 2026-06-07 13:28 BST

Instruction:
Build the AION Evidence Vault and Source Grounding layer so Brain memory,
retrieval, reasoning, plans, execution, skills, evaluations, and learning can
preserve source material and connect outputs back to evidence.

Acceptance Evidence:
- `EvidenceRecord`, `EvidenceChunk`, `EvidenceIngestRequest`,
  `EvidenceIngestResponse`, `EvidenceSearchRequest`, `EvidenceSearchResult`,
  `EvidenceLink`, `GroundingStatement`, `GroundingRequest`, `GroundingClaim`,
  `GroundingResponse`, and `ObjectRef` are Brain-owned contracts.
- Evidence records, chunks, links, and grounding claims are backed by migration
  `0013`.
- Content hashing normalizes text and uses deterministic SHA-256.
- Evidence chunking is deterministic and ordered.
- Text evidence ingestion and metadata-only content references are supported.
- Evidence search is deterministic, lexical, scope-filtered, and policy-gated.
- Evidence links connect source material to generic Brain-owned targets.
- Grounding claims are deterministic and never call LLMs.
- Retrieval Router can include `evidence_vault` results.
- Context Fusion preserves evidence refs.
- Prompt packets include evidence refs and a grounding instruction.
- Evaluator includes `evidence_grounding_score`.
- Visual telemetry includes evidence, chunk, link, grounding, retrieval, and
  deletion events.
- MinIO remains a placeholder and no MinIO SDK dependency is imported.
- No URL fetch, PDF parsing, OCR, binary upload handling, external AI call, or
  domain-specific evidence logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-020 - Visual Brain Projection, Telemetry Stream, and Observability Spine
Status: Done
Priority: High
Created: 2026-06-11 17:59 BST
Completed: 2026-06-11 18:03 BST

Instruction:
Build the backend Visual Brain Projection and local Observability Spine so
canonical cognitive telemetry becomes frontend-agnostic Brain Maps, pulses,
clusters, trace timelines, and an SSE stream.

Acceptance Evidence:
- Brain-owned visual node, edge, pulse, cluster, map, snapshot, telemetry query,
  trace timeline, observability event, and observability summary contracts exist.
- Migration `0014` creates Brain Map snapshot, observability event, and trace
  timeline tables.
- Brain Map projection deduplicates nodes, aggregates generic edges, builds
  clusters, creates pulses, and applies deterministic intensity decay.
- Visual telemetry query, map, snapshot, timeline, SSE, observability event,
  summary, and timeline alias APIs are implemented.
- Visual and observability access is policy-gated through generic actions.
- `/brain/think` records sanitized local observability events, and recorder
  failures do not break the Brain loop.
- Langfuse remains a placeholder with no SDK import or external call.
- No frontend code or domain-specific visualization logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-021 - Cognitive Replay, Brain Snapshots, and Regression Harness
Status: Done
Priority: High
Created: 2026-06-11 18:03 BST
Completed: 2026-06-11 18:18 BST

Instruction:
Build local, deterministic Cognitive Replay, content-addressed Brain snapshots,
semantic drift comparison, golden trace regression cases, and evaluation
adapter boundaries.

Acceptance Evidence:
- Brain snapshot, replay, comparison, regression, and evaluation adapter
  contracts are Brain-owned and typed.
- Migration `0015` creates snapshot, replay, regression case, regression run,
  and per-case result tables.
- Snapshot hashes use deterministic normalized JSON and secret-like values are
  sanitized.
- Replay loads canonical events, creates fresh replay identities, and runs the
  Brain loop with explicit side effects disabled.
- Trace comparison detects generic semantic drift without LLM calls.
- Golden trace cases and regression runs persist local deterministic reports.
- Promptfoo and Ragas remain placeholder adapters with no imports, CLI calls,
  subprocesses, or external evaluation calls.
- Replay, regression, snapshot, compare, and local eval APIs are implemented
  and policy-gated.
- Visual telemetry includes snapshot, replay, regression, and eval events.
- The rebuilt Docker stack passed live snapshot, replay, regression, compare,
  and local eval endpoint smoke checks.
- `./scripts/test.sh` passes with 333 tests.
- `./scripts/lint.sh` passes.

### AION-022 - Kernel Assembly, Dependency Container, and End-to-End Self-Test
Status: Done
Priority: High
Created: 2026-06-11 18:18 BST
Completed: 2026-06-11 19:21 BST

Instruction:
Assemble AION Brain through one composition root with typed adapter selection,
service registration, boot diagnostics, local self-test, contract export, and
architecture boundary enforcement.

Acceptance Evidence:
- `KernelContainer` is the process-wide composition root and AppFactory stores
  it on FastAPI app state.
- Kernel contracts, lifecycle repository, service registry, boot diagnostics,
  local self-test, contract export, dev bootstrap metadata, and boundary
  checker are implemented.
- Migration `0016` creates boot, service registry, and self-test tables.
- Kernel policy actions and visual telemetry event/node types are registered.
- `/health` remains unchanged.
- All kernel status, boot, services, self-test, contract, boundary, and adapter
  APIs passed live Docker smoke checks.
- Live boot status is `ready`; local self-test passed 29 checks.
- Architecture boundary scan passed across 233 Brain source files.
- Contract export generated `artifacts/aion-contracts.json`.
- Docker default stack rebuilt and is running.
- `./scripts/test.sh` passes with 348 tests.
- `./scripts/lint.sh` passes.

### AION-023 - Model Gateway Activation, Provider Registry, and Budget Guard
Status: Done
Priority: High
Created: 2026-06-11 19:21 BST
Completed: 2026-06-11 19:49 BST

Instruction:
Build the AION Model Gateway activation layer with provider-neutral contracts,
provider/profile registries, deterministic fallback, optional LiteLLM and
OpenAI-compatible HTTP adapter boundaries, prompt redaction, budget guard,
usage ledger, policy gates, APIs, ReasoningMesh integration, tests, and docs.

Acceptance Evidence:
- Brain-owned model provider, profile, gateway request/response, budget,
  usage, health, and prompt redaction contracts are implemented.
- Migration `0017` creates model provider, profile, budget, usage, and prompt
  redaction tables.
- `ModelGatewayService` policy-gates gateway completion, route selection, and
  model completion before invoking adapter boundaries.
- Deterministic provider/profile bootstrap is available and remains the default
  safe route when external model calls are disabled.
- LiteLLM-compatible and OpenAI-compatible HTTP adapters use `httpx` boundaries
  only; no provider SDKs are imported.
- Prompt redaction blocks or redacts secret-like content before model calls.
- Budget guard estimates tokens and cost, blocks over-budget external routes,
  and records local deterministic usage at zero cost.
- ReasoningMesh is wired through the kernel container to use
  `ModelGatewayService`.
- Model provider, profile, gateway completion, usage, and budget APIs are
  implemented and policy-gated.
- Model gateway policy actions are registered in OPA, with model registry reads
  handled by model-specific policy rules.
- Visual telemetry includes model gateway, provider, profile, budget, prompt,
  and usage events.
- External model calls remain disabled by default.
- Docker default stack rebuilt and is running.
- Live `/health` smoke check passed with the unchanged health payload.
- Live kernel self-test passed 38 checks with no failures.
- Live deterministic `POST /brain/model-gateway/complete` returned
  `status: completed` and recorded usage for provider `deterministic`.
- `./scripts/test.sh` passes with 384 tests.
- `./scripts/lint.sh` passes.
- Architecture boundary scan passed across 245 Brain source files.

### AION-024 - TurboVec Compressed Semantic Memory Adapter
Status: Done
Priority: High
Created: 2026-06-11 19:49 BST
Completed: 2026-06-11 20:06 BST

Instruction:
Activate optional TurboVec compressed semantic recall behind
`SemanticMemoryAdapter` while keeping pgvector as the default baseline and
Postgres as canonical memory truth.

Acceptance Evidence:
- TurboVec public contracts are implemented for adapter status, index status,
  rebuild, and single-memory reindex requests.
- `TurboVecCompat` is the only TurboVec package boundary; no direct TurboVec
  import exists in Brain source.
- `TurboVecRepository` persists AION-owned index and entry metadata without
  exposing SQLAlchemy rows.
- `TurboVecSemanticMemoryAdapter` supports status, remember, retrieve, forget,
  rebuild, and reindex through AION contracts.
- Kernel and API dependency wiring select TurboVec only when configured, fall
  open to pgvector when enabled, and can fail closed when fallback is disabled.
- Semantic adapter status, TurboVec status, rebuild, and reindex endpoints are
  implemented.
- Retrieval Router preserves adapter metadata for semantic memory results.
- Kernel diagnostics include TurboVec checks without making TurboVec mandatory.
- Docker Compose mounts a local TurboVec index volume.
- Docs and ADR `0019` describe the optional compressed recall boundary.
- `./scripts/test.sh` passes with 404 tests.
- `./scripts/lint.sh` passes.

### AION-025 - Graphiti Temporal Knowledge Graph Adapter
Status: Done
Priority: High
Created: 2026-06-12 02:11 BST
Completed: 2026-06-12 02:11 BST

Instruction:
Activate the optional Graphiti temporal knowledge graph adapter behind
`GraphMemoryAdapter` while keeping Postgres graph memory as the default
canonical baseline.

Acceptance Evidence:
- Graphiti public contracts are implemented for adapter status, configuration
  status, graph sync, and generic temporal episodes.
- `GraphitiCompat` is the only Graphiti package import boundary; no Graphiti
  SDK types cross Brain public APIs.
- `GraphitiRepository` persists AION-owned config and sync metadata.
- `GraphitiGraphMemoryAdapter` supports optional node/edge indexing, query
  fallback, dry-run sync, real sync metadata, and episode responses.
- Kernel and API dependency wiring select Graphiti only when configured, fall
  open to Postgres graph memory when enabled, and can fail closed when fallback
  is disabled.
- Graph adapter, Graphiti status, sync, and episode endpoints are implemented.
- Retrieval Router and Context Compiler preserve graph adapter metadata in
  retrieved context.
- Kernel diagnostics include Graphiti checks without making Graphiti mandatory.
- Docs and ADR `0020` describe the optional temporal graph boundary.
- `./scripts/test.sh` passes with 417 tests.
- `./scripts/lint.sh` passes.

### AION-026 - MCP Capability Protocol Adapter and External Tool Boundary
Status: Done
Priority: High
Created: 2026-06-12 02:27 BST
Completed: 2026-06-12 02:27 BST

Instruction:
Activate MCP as an optional capability protocol adapter behind AION contracts
while keeping MCP disabled by default and preserving AION Capability Manifest
as the internal governance contract.

Acceptance Evidence:
- MCP public contracts are implemented for server records, tool descriptors,
  capability mappings, sync requests/responses, invocation requests/results,
  health, and adapter status.
- Migration `0020` creates MCP server, mapping, sync, and invocation metadata
  tables.
- `MCPCompat` is the only MCP SDK import boundary; no direct MCP import exists
  outside `aion_brain/mcp/compat.py`.
- MCP security blocks disabled external MCP, network transports without
  opt-in, stdio without opt-in, shell control characters, and secret-like
  config.
- MCP tools map into AION capabilities through deterministic generic IDs,
  AION-owned risk metadata, permissions, memory scopes, execution mode, and
  audit level.
- `MCPService` owns policy-gated server registration, health checks, tool sync,
  invocation records, and visual telemetry.
- `MCPRuntimeAdapter` and `CapabilityRuntimeGateway` return AION invocation
  contracts only and never expose MCP SDK objects.
- The built-in `in_memory_fake` server supports deterministic generic test
  tools without network or shell execution.
- MCP API status, server registration, health check, sync, mappings, disable,
  and invocation endpoints are implemented.
- Kernel diagnostics include MCP enabled/package/network/stdio/runtime/default
  execution checks.
- OPA includes generic MCP actions and fail-closed transport and invocation
  policy.
- Docs and ADR `0021` describe MCP as optional, disabled by default, and
  governed by AION contracts.
- No finance, trading, IT, legal, healthcare, HR, procurement, shell,
  subprocess, or domain-specific MCP logic exists.
- `./scripts/test.sh` passes.
- `./scripts/lint.sh` passes.

### AION-027 - Durable Workflow Engine and Temporal Adapter Boundary
Status: Done
Priority: High
Created: 2026-06-12 02:51 BST
Completed: 2026-06-12 02:51 BST

Instruction:
Build the generic durable workflow engine for AION Brain v0.1, with local
database-backed workflow state, explicit one-shot worker and scheduler controls,
policy gates, workflow telemetry, and an optional Temporal adapter boundary.

Acceptance Evidence:
- Workflow contracts are implemented for definitions, steps, retry policy,
  run requests, runs, step runs, transitions, heartbeats, worker records,
  engine status, and Temporal adapter status.
- The local workflow repository persists definitions, runs, step runs,
  heartbeats, worker records, and workflow events.
- The local workflow engine supports dry-run execution, controlled-action
  boundaries, policy denials, approval waits, pause/resume/cancel/retry, and
  deterministic retry scheduling.
- The scheduler and local worker are disabled by default and run only through
  explicit one-shot controls.
- Temporal remains optional and disabled by default; `TemporalCompat` is the
  only SDK lookup boundary and the SDK is not required for tests.
- Workflow API endpoints are implemented under `/brain/workflows`.
- Task runner workflow handoff requires explicit `run_workflow=true` metadata
  and defaults to dry-run.
- Kernel composition, diagnostics, contract export, visual telemetry contract
  values, OPA policy vocabulary, settings, docs, ADR `0022`, and
  `scripts/run-local-worker.sh` are updated.
- `./scripts/lint.sh` passes.
- `./scripts/test.sh` passes with 472 tests.
- `docker compose config --quiet` and
  `docker compose --profile workflow config --quiet` pass.

### AION-028 - Risk Engine, Guardrails, and Approval Control Plane
Status: Done
Priority: High
Created: 2026-06-12 03:12 BST
Completed: 2026-06-12 03:12 BST

Instruction:
Build the generic risk engine, guardrail layer, and approval control plane for
AION Brain v0.1. Keep the implementation Brain-only, deterministic,
domain-neutral, and free of external notification or post-approval execution
side effects.

Acceptance Evidence:
- Risk, guardrail, and approval contracts are implemented and exported.
- Risk assessments persist deterministic scores, factors, constraints, and
  decisions.
- Guardrail rules and guardrail decisions persist through the generic
  repository boundary.
- Default guardrail rules are domain-neutral and cover critical risk,
  controlled execution, external effects, secret-like payload signals,
  external model use, MCP use, and skill activation effects.
- Approval requests, decisions, inbox queries, and lifecycle events persist
  through the approval repository.
- Approval state transitions are pending-to-terminal only.
- Risk, guardrail, and approval APIs are implemented.
- Execution, workflows, task runs, skills, model gateway, module runtime, and
  MCP controlled invocation call the approval gate before side effects.
- Pending approvals stop adapters, model calls, capability invocations, and
  external protocol calls before they happen.
- OPA includes generic risk, guardrail, and approval actions.
- Kernel composition, diagnostics, settings, visual telemetry values, docs, and
  ADR `0023` are updated.
- Focused AION-028 pytest coverage passes.

### AION-029 - Memory Governance, Decay, Forgetting, and Compaction
Status: Done
Priority: High
Created: 2026-06-12 08:15 BST
Completed: 2026-06-12 08:15 BST

Instruction:
Build the generic Memory Governance layer for AION Brain v0.1, including
retention rules, governance decisions, deterministic decay, approval-aware
forgetting, conflict detection and resolution, compaction, API routes, policy
vocabulary, telemetry vocabulary, docs, and migration support.

Acceptance Evidence:
- Memory governance contracts, repository, rules engine, decay, retention,
  forgetting, conflict, and compaction services are implemented.
- MemoryService and RetrievalRouter apply governance to writes and recall.
- Forgetting soft-deletes memory-owned targets and preserves evidence by
  default; evidence-link deletion disables only the link.
- Generic conflict detection and deterministic compaction contain no vertical
  workflow logic and make no model or external network calls.
- Governance APIs are implemented under `/brain/memory/...`.
- OPA includes memory governance, decay, retention, forgetting, conflict, and
  compaction actions.
- Kernel composition, contract export, settings, visual telemetry values, docs,
  ADR `0024`, and migration `0023` are updated.
- `./scripts/test.sh` passes with 497 tests.
- `./scripts/lint.sh` passes.
- `docker compose up --build --detach`, health probes, and governance endpoint
  smoke test pass.

### AION-030 - Attention Controller, Working Memory Stack, and Focus Manager
Status: Done
Priority: High
Created: 2026-06-12 09:08 BST
Completed: 2026-06-12 09:08 BST

Instruction:
Build the generic Attention Controller, Working Memory Stack, Focus Manager,
interrupt routing, and context budget controls for AION Brain v0.1. Keep the
implementation Brain-only, deterministic, domain-neutral, and free of model
calls or external network scoring.

Acceptance Evidence:
- Attention, focus, interrupt, context budget, and working memory contracts are
  implemented and exported.
- Attention signals, decisions, focus sessions, interrupts, context budgets,
  and working memory slots persist through repository boundaries.
- Deterministic scoring covers urgency, importance, confidence, recency,
  working memory priority, TTL, pinning, and focus alignment.
- Attention APIs are implemented under `/brain/attention`, `/brain/focus`,
  `/brain/interrupts`, and `/brain/context-budget`.
- Working memory APIs are implemented under `/brain/working-memory`.
- Event intake, context compilation, retrieval routing, brain loop,
  memory governance conflicts, kernel composition, diagnostics, OPA policy,
  visual telemetry, settings, docs, and ADR `0025` are updated.
- Retrieval includes `working_memory` as a generic source and applies
  attention-selected deterministic boosts.
- Brain loop records focus and attention metadata and writes short-lived
  working memory snapshots without storing raw secrets.
- `pytest` passes with 524 tests.
- `ruff check .` passes.
- `mypy src/aion_brain` passes.
- `docker compose config --quiet` passes.
- `docker compose up --build -d`, health probes, attention decision smoke,
  and working memory smoke pass.

### AION-031 - Autonomy Governor, Operating Modes, and Delegation Control
Status: Done
Priority: High
Created: 2026-06-12 10:18 BST
Completed: 2026-06-12 10:18 BST

Instruction:
Build the generic Autonomy Governor for AION Brain v0.1, including operating
modes, autonomy profiles, run levels, delegations, decisions, lifecycle events,
policy actions, API routes, kernel wiring, and enforcement across execution
capable paths.

Acceptance Evidence:
- Autonomy contracts, mode/risk helpers, default profile, repository,
  governor, run-level service, delegation service, API router, migration, and
  kernel wiring are implemented.
- Default autonomy is conservative: assist mode, dry-run ceiling, medium risk
  ceiling, and no external models/tools, schedulers, background workers, skill
  promotion, or memory forgetting unless explicitly enabled.
- Brain loop, execution, workflows, scheduler, worker, tasks, model gateway,
  module runtime, MCP, skill activation, and memory forgetting consult the
  Autonomy Governor before side effects.
- OPA includes generic autonomy policy actions.
- Visual telemetry contracts include autonomy, delegation, and run-level
  events and node types.
- README, architecture, brain contract, policy docs, and ADR `0026` are
  updated.
- Focused AION-031 pytest coverage passes with 38 tests.
- `pytest` passes with 562 tests.
- `ruff check .` passes.
- `mypy src/aion_brain` passes.
- `docker compose config --quiet` passes.
- `docker compose up --build -d`, `/health`, `/brain/autonomy/status`, and
  `/brain/autonomy/decide` smoke tests pass.

## Blocked

No blocked tasks.
