# AION OS

AION OS is a brain-first AI operating architecture. Its first deliverable is
AION Brain: a domain-neutral cognitive kernel that owns the system contracts,
policies, traces, and learning signals that every future module must follow.

This repository currently contains only the AION Brain v0.1 scaffold. It does
not implement finance, trading, IT automation, legal, healthcare, HR,
procurement, business workflows, or any vertical module logic.

## AION Brain

AION Brain is the core reasoning and coordination layer. It does not depend on a
single model provider, orchestration framework, memory engine, or external
capability protocol. External systems are implementation engines only. They must
remain behind adapters.

AION Brain owns:

- Event contracts
- Intent frames
- Context packets
- Memory policy
- Memory governance rules, decisions, decay, forgetting, conflicts, and compaction
- Belief claims, supports, contradictions, revisions, and truth maintenance runs
- Capability manifest
- Module runtime contracts and bindings
- Policy decisions
- Plan graph schema
- Reasoning results
- Model routing decisions
- Model call ledger records
- Execution requests and runs
- Approval checkpoints
- Risk assessments
- Guardrail decisions
- Approval requests and decisions
- Capability invocation records
- Goal records
- Cognitive task records
- Task run records
- Schedule metadata
- Cognitive cycle templates
- Cognitive cycle runs
- Sleep consolidation records
- Lifecycle events
- Decision traces
- Evaluation records
- Learning signals
- Reflection records
- Skill candidates
- Skill records, versions, and promotion gates
- Visual telemetry events
- Notification topics, subscriptions, alerts, escalations, and digests
- Audit records

## Disabled External Connector Prototype

AION-108 adds a hard-off external connector prototype for local preview and
audit evidence only. It exposes connector runtime status, mock manifest
validation, egress preview, ingress preview, blockers, SDK/CLI preview access,
and static console demo data.

The connector runtime remains disabled. The prototype does not call external
services, add connector/provider SDKs, store credentials, store tokens, register
routes, activate capabilities, execute tools, execute write paths, or bypass
policy/audit gates.

## Connector Dry-Run Simulator

AION-110 adds a synthetic connector dry-run simulator, replay fixture path, and
policy readiness gate. These surfaces validate local request and response
shapes only. They do not execute connectors, call external services, store
credentials, store tokens, register routes, activate capabilities, execute
tools, or execute write paths.

## Connector Policy Action Catalog

AION-111 adds a connector policy action catalog, role-aware authorization
matrix, dry-run gate, denial rules, traceability evidence, SDK/CLI preview
access, and static console demo data. It keeps connector runtime disabled and
adds no external calls, credentials, tokens, activation, routes, tool
execution, write execution, frontend dependencies, package files, or
migrations.

## Connector Sandbox Design

AION-112 adds a connector sandbox design boundary, isolation model, capability
rules, readiness preview, audit/provenance evidence, SDK/CLI preview access,
and static console demo data. It does not add real sandbox execution,
filesystem access, network access, credentials, tokens, process spawning,
dynamic imports, package installation, connector activation, routes, external
calls, frontend dependencies, package files, or migrations.

## Connector Platform Checkpoint

AION-115 freezes the connector platform checkpoint after AION-106 through
AION-114. It adds closeout docs, evidence examples, static console checkpoint
data, and repository-local checkpoint scripts only. Connector implementation
remains unapproved, connector runtime remains disabled, external calls remain
absent, credentials and tokens remain absent, sandbox execution remains absent,
and activation and route registration remain disabled.

## Connector Platform Stabilization

AION-116 adds the connector platform stabilization runbook, long-running
regression matrix, phase freeze gate, evidence pack, safety baseline lock,
regression evidence, static console stabilization data, ADR 0107, and
repository-local stabilization scripts only. Connector implementation remains
unapproved, connector runtime remains disabled, external calls remain absent,
credentials and tokens remain absent, sandbox execution remains absent, and
activation and route registration remain disabled.

## v0.2 Proposal Registry Stabilization

AION-127 stabilizes the v0.2 proposal registry and approval queue preview
created in AION-126. It adds stabilization docs, ADR 0118, candidate
workstream evidence, lifecycle evidence, closeout checks, static console
preview data, and local scripts only. Proposal registry preview-only,
approval queue preview-only, approval queue item approval false, proposal
implementation approval false, runtime implementation approval false, and
workstream implementation approval false remain locked. It creates no v0.2 tag
or release and adds no runtime, external call, credential/token, sandbox,
package, migration, API, SDK, CLI, or domain module implementation.

## v0.2 Planning Master Checkpoint

AION-128 consolidates AION-119 through AION-127 into a planning master
checkpoint, proposal governance baseline, approval queue baseline, and
implementation lock freeze. It adds planning docs, ADR 0119, synthetic
examples, static console preview data, and local verification scripts only.
Proposal registry preview-only, approval queue preview-only, approval queue
item approval false, proposal implementation approval false, runtime
implementation approval false, backlog implementation approval false, and
workstream implementation approval false remain locked. It creates no v0.2
tag or release and adds no runtime, external call, credential/token, sandbox,
package, migration, API, SDK, CLI, or domain module implementation.

## Core Brain Loop

```text
Event -> Intent -> Context -> Reasoning -> Plan -> Policy -> Trace -> Evaluate -> Learn -> Telemetry
```

The v0.1 runtime performs deterministic intent classification, context
compilation, deterministic local reasoning, planning, policy checks, tracing,
evaluation, candidate learning, optional reflection, and visual telemetry
emission. It avoids external LLM calls, real capability execution, external
intelligence repos, and domain behavior.

Execution is a separate explicit step after thinking. `/brain/think` prepares a
plan and reports execution readiness; it does not execute the plan.

## Architecture

```text
Clients / Future Modules
        |
        v
  AION Brain API
        |
        v
  Brain Loop Kernel
        |
        +--> Event / Intent / Context Contracts
        +--> Memory Policy and Memory Records
        +--> Capability Registry and Manifests
        +--> Module Runtime Bindings
        +--> Plan Graph Schema
        +--> Execution Runs and Approval Checkpoints
        +--> Goals, Cognitive Tasks, and Schedule Metadata
        +--> Policy Decisions
        +--> Decision Traces and Audit Records
        +--> Learning Signals
        |
        v
  Adapter Boundary
        |
        +--> Runtime adapters
        +--> Memory adapters
        +--> Model gateway adapters
        +--> Capability protocol adapters
        +--> Policy adapters
        +--> Observability and evaluation adapters
```

## Core Subsystems

- `contracts`: Pydantic v2 public data models for Brain-owned APIs.
- `events`: event intake, event ledger persistence, and event publishing.
- `event_reactions`: subscription-based event reaction routing, dispatch
  records, action records, dead letters, and replay.
- `core`: the brain loop skeleton.
- `runtime`: future runtime orchestration adapters.
- `planning`: deterministic generic plan creation.
- `memory`: semantic and graph memory adapter interfaces.
- `memory_governance`: retention, decay, policy-gated forgetting, generic
  conflict detection, and deterministic compaction.
- `beliefs`: explicit claim ledger, support ledger, contradiction ledger,
  deterministic claim extraction, and truth maintenance.
- `reasoning`: Reasoning Mesh, local deterministic adapter, model routing, and
  gateway placeholders.
- `capabilities`: capability manifest registry and MCP boundary.
- `modules`: Module Bus, runtime registration, capability-to-runtime binding,
  and Capability Runtime Gateway.
- `policy`: policy adapter boundary for Open Policy Agent.
- `risk`: deterministic action risk scoring and persistence.
- `guardrails`: generic safety rules that allow, block, or require approval.
- `approvals`: pending human-control records and approval lifecycle decisions.
- `execution`: deterministic, policy-gated, side-effect-free execution
  orchestrator and plan step state machine.
- `goals`: generic Brain-owned goal lifecycle records.
- `tasks`: cognitive task lifecycle, explicit task runs, and lifecycle publishing.
- `schedules`: schedule metadata only; no scheduler loop in v0.1.
- `cycles`: manual cognitive cycle orchestration, sleep consolidation, and
  safe maintenance checks.
- `lifecycle`: generic goal and task transition rules.
- `evaluation`: deterministic trace scoring without model grading.
- `learning`: candidate learning signal generation without self-modification.
- `reflection`: governed trace, task, retrieval, planning, policy, and
  execution review records.
- `skills`: data-only procedural memory candidates, promotion gates, versions,
  activation policy, and deterministic matching.
- `audit`: persisted trace, decision, evaluation, learning, and telemetry ledger.
- `telemetry`: visual Brain graph event generation for future UI work.
- `observability`: tracing placeholder.
- `dialogue`: backend dialogue sessions, sanitized messages, clarification
  requests, feedback, and policy-gated dialogue turns.
- `responses`: deterministic response draft composition, verification, and
  local API delivery records.
- `notifications`: local-only notification topics, subscriptions, alert
  routing, escalation queue records, query helpers, and digests.
- `conformance`: metadata-only capability conformance profiles, test vectors,
  schema mock invocation records, findings, and extension readiness assessments.

## Imported Infrastructure

The default Docker stack includes:

- FastAPI brain API on port `8080`
- PostgreSQL
- Redis
- NATS
- Open Policy Agent

Optional Compose profiles are prepared for MinIO, Temporal, OpenTelemetry
Collector, LiteLLM, and a disabled MCP placeholder.

## Planned Future Adapters

- LangGraph behind `BrainRuntimeAdapter`
- pgvector behind `SemanticMemoryAdapter`
- TurboVec behind `SemanticMemoryAdapter` as optional compressed recall
- Graphiti behind `GraphMemoryAdapter` as optional temporal graph recall
- Cognee behind `IngestionMemoryAdapter`
- Mem0 behind `MemoryServiceAdapter`
- LiteLLM behind `ModelGatewayAdapter`
- MCP behind `CapabilityProtocolAdapter` and `MCPRuntimeAdapter`
- Langfuse behind `ObservabilityAdapter`
- Promptfoo and Ragas behind `EvaluationAdapter`

pgvector is the default semantic adapter. TurboVec and Graphiti are optional and
disabled by default. They are selected only through AION-owned adapter settings,
fall back to local baselines when configured to do so, and expose no vendor
objects through public Brain APIs.

MCP is optional and disabled by default. AION maps MCP tools into AION
capabilities, then applies AION policy, risk, memory scope, and audit rules.
MCP never defines AION permissions or self-authorizes execution.

## Local Development

```bash
./scripts/dev-up.sh
./scripts/dev-down.sh
./scripts/sdk-test.sh
```

First-run local bootstrap and setup inspection:

```bash
./scripts/setup-doctor.sh --fast
./scripts/seed-defaults.sh
./scripts/bootstrap-local.sh --fast
```

Bootstrap is local developer readiness only. It seeds AION-owned default
records through public services, runs dry-run readiness checks, creates setup
reports, and surfaces operator action items for missing setup. It does not
install packages, create production credentials, enable external providers,
mutate source code, execute tools, or provision cloud resources.

Brain API health check:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/health/live
curl http://localhost:8080/health/ready
```

## v0.1 Release Candidate Quick Start

Use this command set for local release-candidate verification:

```bash
docker compose config --quiet
docker compose up --build -d brain-api postgres redis nats opa
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
./scripts/setup-doctor.sh --fast --offline-ok
./scripts/golden-path.sh --offline-ok
./scripts/rc-check.sh --offline-ok
./scripts/demo-local.sh --offline-ok
docker compose down
```

Release handoff docs:

- [Operator runbook](docs/operations/operator-runbook.md)
- [Local demo pack](docs/operations/local-demo-pack.md)
- [Bootstrap](docs/operations/bootstrap.md)
- [Golden path](docs/operations/golden-path.md)
- [Release candidate](docs/operations/release-candidate.md)
- [Troubleshooting](docs/operations/troubleshooting.md)
- [v0.1 release handoff](docs/operations/v0.1-release-handoff.md)
- [Final freeze](docs/release/v0.1-final-freeze.md)
- [Final evidence summary](docs/release/v0.1-final-evidence-summary.md)
- [Tagging guide](docs/release/v0.1-tagging-guide.md)
- [Release baseline](docs/release/v0.1-release-baseline.md)
- [Operator acceptance](docs/release/v0.1-operator-acceptance.md)
- [Known limitations](docs/release/v0.1-known-limitations.md)
- [Release candidate checklist](docs/release/v0.1-release-candidate-checklist.md)
- [Demo script](docs/release/v0.1-demo-script.md)
- [No-go conditions](docs/release/v0.1-no-go-conditions.md)
- [Post-v0.1 roadmap](docs/release/v0.1-post-release-roadmap.md)

## Post-v0.1 Module Ecosystem Strategy

AION Brain v0.1.0 is released as the local-first baseline. The next phase is
module ecosystem strategy, not runtime activation.

The first selected module class is Generic Knowledge Intelligence. It remains
metadata-only and uses existing Brain gates for extension intake, module slots,
capability bindings, conformance, readiness, policy, audit, and operator
review.

Activation remains disabled. Code loading remains disabled. Package
installation, dynamic routes, external calls, full autonomy, and controlled
handoff remain disabled.

Module strategy docs:

- [Module ecosystem roadmap](docs/roadmap/module-ecosystem.md)
- [Module activation design](docs/architecture/module-activation-design.md)
- [Module activation request gate](docs/module-activation-gate.md)
- [Module activation threat model](docs/security/module-activation-threat-model.md)
- [First module selection](docs/modules/first-module-selection.md)
- [Generic Knowledge Intelligence module](docs/modules/generic-knowledge-intelligence-module.md)
- [Module intake checklist](docs/modules/module-intake-checklist.md)
- [Module activation state machine](docs/modules/module-activation-state-machine.md)
- [Module risk classification](docs/modules/module-risk-classification.md)
- [Module branching and release discipline](docs/modules/module-branching-and-release-discipline.md)
- [Module activation design review](docs/modules/module-activation-design-review.md)
- [Plugin boundary evidence pack](docs/modules/plugin-boundary-evidence-pack.md)
- [Module activation pre-gate](docs/modules/module-activation-pre-gate.md)
- [Code loading disabled proof](docs/modules/code-loading-disabled-proof.md)
- [Runtime registration disabled proof](docs/modules/runtime-registration-disabled-proof.md)
- [Capability activation disabled proof](docs/modules/capability-activation-disabled-proof.md)
- [Module lifecycle traceability matrix](docs/modules/module-lifecycle-traceability-matrix.md)
- [Future activation implementation prerequisites](docs/modules/future-activation-implementation-prerequisites.md)
- [Module activation no-go regression pack](docs/modules/module-activation-no-go-regression-pack.md)
- [ADR 0073](docs/adr/0073-post-v0.1-module-ecosystem-strategy.md)
- [ADR 0075](docs/adr/0075-generic-knowledge-intelligence-module-pack.md)
- [ADR 0096](docs/adr/0096-module-activation-design-review-gate.md)

Recommended branch command:

```bash
git switch main
git pull --ff-only origin main
git switch -c phase/post-v0.1-module-strategy
```

## Generic Knowledge Intelligence Module Pack

AION-084 adds the first post-v0.1 governed module package as metadata only.
The pack lives at `examples/modules/generic-knowledge-intelligence/` and
proves the module path without activation:

`manifest -> intake -> slot -> binding -> conformance -> readiness -> activation request -> blocker -> operator review`

The pack does not add Brain runtime code, migrations, API routes, SDK
resources, CLI commands, external dependencies, package installation, route
registration, runtime registration, code loading, tool execution, or external
calls.

Run the local checks:

```bash
./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
```

Read the module pack docs:

- [Module pack README](examples/modules/generic-knowledge-intelligence/README.md)
- [Demo walkthrough](docs/modules/generic-knowledge-intelligence-demo.md)
- [Readiness trail](docs/modules/generic-knowledge-intelligence-readiness-trail.md)
- [Operator review](docs/modules/generic-knowledge-intelligence-operator-review.md)
- [No-go conditions](docs/modules/generic-knowledge-intelligence-no-go.md)

## Module Activation Design Review Gate

AION-105 freezes the module/plugin activation design before any future
activation implementation work. It adds a review gate, plugin boundary evidence
pack, pre-gate, disabled proofs, traceability matrix, and no-go regression
pack.

Run the local review gates:

```bash
./scripts/module-activation-design-review.sh
./scripts/module-activation-no-go-regression.sh
```

The gate preserves the current safe state: no module activation, no capability
activation, no code loading, no package installation, no runtime registration,
no controlled execution, no external calls, and no domain module logic.

## Operator Console Strategy

AION-087 keeps post-v0.1 operator work CLI/API-first. It creates the local
dashboard blueprint and workflow map only; it does not add runtime UI,
frontend dependencies, API routes, SDK resources, CLI commands, module
activation, code loading, package installation, external model calls, or
external services.

The future Operator Console must consume existing Brain APIs and CLI-backed
dry-run workflows. It must preserve policy, audit, approval, redaction, module
activation, and provider-hardening gates.

Operator console docs:

- [Operator console strategy](docs/operator-console/operator-console-strategy.md)
- [Operator view spec](docs/operator-console/operator-view-spec.md)
- [Operator demo map](docs/operator-console/operator-demo-map.md)
- [Operator data safety](docs/operator-console/operator-data-safety.md)
- [Operator no-go conditions](docs/operator-console/operator-console-no-go.md)

Validate the strategy artifacts:

```bash
./scripts/operator-console-check.sh
```

## Operator Console Read-Only View Models

AION-088 adds a backend-only Operator Console view-model and audit contract.
It is read-only and adds no runtime UI, no frontend dependencies, no activation,
no execution, no package installation, no route registration, and no external
calls.

The view model APIs summarize existing Brain state, redact unsafe values, return
unavailable sections when optional services are missing, and expose actions as
descriptors only. The contract preserves no raw prompt exposure, no hidden
reasoning exposure, and no secret exposure.

Endpoints:

- `GET /brain/operator-console/views`
- `POST /brain/operator-console/view-model`
- `POST /brain/operator-console/audit`
- `GET /brain/operator-console/workflows`
- `GET /brain/operator-console/demo-map`

SDK/CLI access:

```bash
aionctl operator-console views
aionctl operator-console view-model --view overview
aionctl operator-console audit
aionctl operator-console workflows
aionctl operator-console demo-map
./scripts/operator-console-contract-check.sh
```

Contract docs:

- [View model contract](docs/operator-console/view-model-contract.md)
- [Data source map](docs/operator-console/data-source-map.md)
- [API contract audit](docs/operator-console/api-contract-audit.md)
- [Read-only action model](docs/operator-console/read-only-action-model.md)
- [View redaction rules](docs/operator-console/view-redaction-rules.md)
- [Console API examples](docs/operator-console/console-api-examples.md)

## Static Operator Console Prototype

AION-089 adds a static local Operator Console prototype. It is plain HTML,
CSS, and JavaScript under `operator-console-static/`. It has no build step, no
frontend dependency, no production auth claim, no write actions, no activation,
and no external calls.

The prototype consumes the existing read-only
`POST /brain/operator-console/view-model` API when a local Brain API is
available. When the API is offline, it renders synthetic demo JSON from
`operator-console-static/demo-data/`. API overrides are accepted only for
`localhost` or `127.0.0.1`.

Run the static checks:

```bash
./scripts/operator-console-static-check.sh
./scripts/operator-console-static-demo.sh --offline-ok
python3 -m http.server 8090 --directory operator-console-static
```

Read the prototype docs:

- [Static console prototype](docs/operator-console/static-console-prototype.md)
- [Static console runbook](docs/operator-console/static-console-runbook.md)
- [Static console safety review](docs/operator-console/static-console-safety-review.md)
- [Static console test plan](docs/operator-console/static-console-test-plan.md)

## Read-Only Module Lifecycle Dashboard

AION-090 extends the static Operator Console with a read-only Module Lifecycle
Dashboard for Generic Knowledge Intelligence. It renders the metadata-only path
from manifest through intake, inactive slot, inactive bindings, validation,
conformance, readiness, activation request, activation gate, safe blockers,
synthetic mock runtime output, and operator review.

The dashboard adds no API routes, SDK resources, CLI commands, migrations,
frontend dependencies, build step, activation, execution, code loading,
runtime registration, external calls, or write actions.

Run the module dashboard check:

```bash
./scripts/module-lifecycle-dashboard-check.sh
```

Read the module dashboard docs:

- [Module lifecycle dashboard](docs/operator-console/module-lifecycle-dashboard.md)
- [Generic Knowledge trail view](docs/operator-console/generic-knowledge-trail-view.md)
- [Module review panel](docs/operator-console/module-review-panel.md)
- [Module dashboard safety review](docs/operator-console/module-dashboard-safety-review.md)

## v0.1 Final Local Release Path

AION Brain v0.1.0 is a local release baseline. The final scripts aggregate
existing gates; they do not deploy, publish, push tags, install packages, call
external services, enable production auth, enable full autonomy, load extension
code, activate capabilities, or add domain modules to Brain core.

```bash
./scripts/v0.1-tag-preview.sh
./scripts/v0.1-final-verify.sh --offline-ok
./scripts/v0.1-freeze.sh --offline-ok
```

For Docker-local validation:

```bash
docker compose up --build -d brain-api postgres redis nats opa
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
./scripts/demo-local.sh --offline-ok
docker compose down
```

Local demo:

```bash
./scripts/demo-local.sh --offline-ok
```

First-run bootstrap and setup doctor remain local setup checks. Golden path
proves deterministic synthetic scenario wiring. The RC gate aggregates local
verification evidence into release-candidate records. No-go conditions block
the v0.1 tag until fixed. The post-v0.1 roadmap starts module activation
design after Brain freeze.

Release candidate gate:

```bash
./scripts/rc-check.sh --offline-ok
./scripts/rc-evidence.sh --offline-ok
```

RC API endpoints:

- `POST /brain/rc/candidates`
- `GET /brain/rc/candidates`
- `GET /brain/rc/candidates/{release_candidate_id}`
- `POST /brain/rc/matrices`
- `GET /brain/rc/matrices`
- `POST /brain/rc/matrices/seed-defaults`
- `POST /brain/rc/gate/run`
- `GET /brain/rc/gate/runs/{rc_run_id}`
- `GET /brain/rc/findings`
- `POST /brain/rc/findings/{rc_finding_id}/dismiss`
- `GET /brain/rc/evidence-packs`
- `GET /brain/rc/evidence-packs/{evidence_pack_id}`
- `GET /brain/rc/reports`
- `GET /brain/rc/reports/{rc_report_id}`
- `POST /brain/rc/query`

The RC gate aggregates local verification evidence into Brain-owned release
candidate records, verification matrices, gate runs, findings, evidence packs,
and reports. It is a local release-readiness control plane only. It does not
deploy, publish, mutate source code, enable disabled runtime features, call
external services, or add domain-specific release logic.

Bootstrap endpoints:

```bash
curl -X POST http://localhost:8080/brain/bootstrap/doctor
curl -X POST http://localhost:8080/brain/bootstrap/run
curl http://localhost:8080/brain/bootstrap/runs
curl http://localhost:8080/brain/bootstrap/findings
curl http://localhost:8080/brain/bootstrap/reports
```

Expected `/health` response:

```json
{
  "status": "ok",
  "service": "aion-brain-api",
  "version": "0.1.0"
}
```

## Internal Notifications and Alerts

v0.1 provides a local-only Internal Notification Center. It records topics,
subscriptions, notifications, alerts, escalation records, and digests for
operator visibility. It does not send email, SMS, webhooks, Slack messages, or
other external notifications. Alerts and escalations do not remediate or mutate
source systems.

Notification endpoints:

- `POST /brain/notifications/topics`
- `GET /brain/notifications/topics`
- `POST /brain/notifications/topics/seed-defaults`
- `POST /brain/notifications/subscriptions`
- `GET /brain/notifications/subscriptions`
- `POST /brain/notifications/publish`
- `POST /brain/notifications/query`
- `POST /brain/notifications/{notification_id}/read`
- `POST /brain/notifications/{notification_id}/acknowledge`
- `POST /brain/notifications/{notification_id}/resolve`
- `POST /brain/alerts`
- `POST /brain/alerts/query`
- `POST /brain/alerts/{alert_id}/acknowledge`
- `POST /brain/alerts/{alert_id}/resolve`
- `POST /brain/escalations/policies`
- `GET /brain/escalations/policies`
- `POST /brain/escalations/evaluate`
- `GET /brain/escalations`
- `POST /brain/notifications/digests`
- `GET /brain/notifications/digests`

Notification center settings keep local delivery explicit:

- `AION_NOTIFICATIONS_ENABLED`
- `AION_ALERT_ROUTER_ENABLED`
- `AION_NOTIFICATION_SUBSCRIPTIONS_ENABLED`
- `AION_ESCALATION_QUEUE_ENABLED`
- `AION_NOTIFICATION_DIGESTS_ENABLED`
- `AION_EXTERNAL_NOTIFICATIONS_ENABLED=false`
- `AION_NOTIFICATION_LOCAL_DELIVERY_ONLY=true`

## Dialogue and Responses

v0.1 provides the backend contract layer for dialogue. It does not implement a
frontend chat UI, provider-specific chat objects, external delivery, controlled
execution, or external model calls from dialogue APIs.

Dialogue endpoints:

- `POST /brain/dialogue/sessions`
- `GET /brain/dialogue/sessions`
- `GET /brain/dialogue/sessions/{dialogue_session_id}`
- `POST /brain/dialogue/sessions/{dialogue_session_id}/close`
- `POST /brain/dialogue/messages`
- `GET /brain/dialogue/messages/{message_id}`
- `GET /brain/dialogue/sessions/{dialogue_session_id}/messages`
- `DELETE /brain/dialogue/messages/{message_id}`
- `POST /brain/dialogue/turn`
- `GET /brain/dialogue/clarifications/pending`
- `POST /brain/dialogue/clarifications/{clarification_id}/answer`
- `POST /brain/dialogue/clarifications/{clarification_id}/cancel`
- `POST /brain/dialogue/feedback`
- `GET /brain/dialogue/feedback`

Response endpoints:

- `POST /brain/responses/compose`
- `GET /brain/responses/{response_id}`
- `POST /brain/responses/{response_id}/verify`
- `POST /brain/responses/{response_id}/deliver-local`
- `GET /brain/responses/{response_id}/deliveries`

Configuration flags:

- `AION_DIALOGUE_ENABLED`
- `AION_RESPONSE_COMPOSER_ENABLED`
- `AION_CLARIFICATION_LOOP_ENABLED`
- `AION_DIALOGUE_MEMORY_HANDOFF_ENABLED`
- `AION_DIALOGUE_STORE_MESSAGES`
- `AION_DIALOGUE_REDACT_SENSITIVE_CONTENT`
- `AION_RESPONSE_REQUIRE_GROUNDING_DEFAULT`

## Belief State and Truth Maintenance

v0.1 provides a generic Belief State Manager. A belief is an explicit claim
with scope, provenance, confidence, status, and support metadata. Beliefs are
recall and working state for reasoning, not absolute truth.

Belief endpoints:

- `POST /brain/beliefs/claims`
- `GET /brain/beliefs/claims/{claim_id}`
- `POST /brain/beliefs/query`
- `POST /brain/beliefs/claims/{claim_id}/revise`
- `DELETE /brain/beliefs/claims/{claim_id}`
- `POST /brain/beliefs/supports`
- `GET /brain/beliefs/claims/{claim_id}/supports`
- `GET /brain/beliefs/contradictions`
- `POST /brain/beliefs/contradictions/{contradiction_id}/resolve`
- `POST /brain/beliefs/extract`
- `POST /brain/beliefs/truth-maintenance/run`
- `GET /brain/beliefs/truth-maintenance/{truth_run_id}`

Truth maintenance recomputes claim confidence, marks stale claims, and records
contradictions deterministically. It never calls external models or external
fact-checking systems. Dialogue and evidence claim extraction are opt-in unless
enabled by local settings.

Configuration flags:

- `AION_BELIEFS_ENABLED`
- `AION_BELIEF_TRUTH_MAINTENANCE_ENABLED`
- `AION_BELIEF_CLAIM_EXTRACTION_ENABLED`
- `AION_BELIEF_AUTO_EXTRACT_FROM_DIALOGUE`
- `AION_BELIEF_AUTO_EXTRACT_FROM_EVIDENCE`
- `AION_BELIEF_MIN_SUPPORTED_CONFIDENCE`
- `AION_BELIEF_STALE_AFTER_DAYS`
- `AION_BELIEF_CONTRADICTION_DETECTION_ENABLED`

`/health/live` reports process liveness. `/health/ready` reports dependency
readiness for Postgres, Redis, NATS, and Open Policy Agent. Readiness failures
return `degraded` and do not crash the API.

## Python SDK and aionctl

AION includes a standalone Python SDK in `packages/aion-sdk-python`. The SDK
talks only to public Brain HTTP APIs and does not import server internals.

## Security Baseline

AION v0.1 includes a local deterministic security baseline for Brain core. It
checks secret leakage, unsafe config, API exposure, optional adapter risk,
dependency metadata, threat model completeness, control catalog completeness,
backup redaction, release package safety, and hardening gate status.

The threat model records generic Brain risks and controls. The hardening gate
combines local checks into one pass, warning, or failed run that freeze and
release packaging can include.

New security endpoints:

- `POST /brain/security/scans/run`
- `GET /brain/security/scans/{security_scan_id}`
- `GET /brain/security/scans`
- `POST /brain/security/threat-models/seed-defaults`
- `POST /brain/security/threat-models`
- `GET /brain/security/threat-models`
- `POST /brain/security/threat-models/{threat_model_id}/status`
- `POST /brain/security/controls/seed-defaults`
- `POST /brain/security/controls`
- `GET /brain/security/controls`
- `POST /brain/security/controls/{control_key}/status`
- `POST /brain/security/hardening-gate/run`
- `GET /brain/security/hardening-gate/{hardening_gate_id}`
- `GET /brain/security/hardening-gate`

CLI examples:

```bash
./scripts/aionctl.sh --scope workspace:main security scan
./scripts/aionctl.sh --scope workspace:main security hardening-gate run
```

AION v0.1 security baseline is local and deterministic. It does not call
external scanners or claim production security certification.

## Runtime Configuration

AION v0.1 runtime config stores safe metadata and feature overrides. It does
not store raw secrets or mutate process environment variables.

The Runtime Configuration Control Plane lets local operators inspect active
configuration posture without editing source code. Environment variables remain
the boot-time source of truth. Config profiles are metadata records, feature
flag overrides are policy-gated, config snapshots are redacted and hashed, and
config validation checks safe defaults before freeze or release handoff.

Runtime configuration concepts:

- Config profiles: named local metadata profiles for safe values, flags,
  constraints, and active-profile inspection.
- Feature flag overrides: local, generic feature state overrides that cannot
  enable full autonomy, external tools, or external models by default.
- Config snapshots: redacted `Settings`, effective feature flags, adapter
  status, deterministic hash, and optional drift report.
- Config validation: deterministic safe-default checks used by security
  baseline, freeze gate, and version manifest metadata.

Runtime configuration endpoints:

- `POST /brain/runtime-config/profiles`
- `GET /brain/runtime-config/profiles/{config_profile_id}`
- `GET /brain/runtime-config/profiles`
- `POST /brain/runtime-config/profiles/{config_profile_id}/activate`
- `POST /brain/runtime-config/profiles/{config_profile_id}/disable`
- `POST /brain/runtime-config/feature-overrides`
- `GET /brain/runtime-config/feature-overrides`
- `POST /brain/runtime-config/feature-overrides/{feature_override_id}/disable`
- `POST /brain/runtime-config/snapshots`
- `GET /brain/runtime-config/snapshots/{config_snapshot_id}`
- `GET /brain/runtime-config/snapshots`
- `POST /brain/runtime-config/snapshots/compare`
- `POST /brain/runtime-config/validate`
- `GET /brain/runtime-config/status`

CLI examples:

```bash
./scripts/aionctl.sh --scope workspace:main config status
./scripts/aionctl.sh --scope workspace:main config validate
./scripts/aionctl.sh --scope workspace:main config snapshot
```

Common commands:

```bash
./scripts/aionctl.sh --scope workspace:main health
./scripts/aionctl.sh --scope workspace:main kernel status
./scripts/aionctl.sh --scope workspace:main kernel self-test
./scripts/aionctl.sh --scope workspace:main smoke run
./scripts/aionctl.sh contracts export \
  --output artifacts/aion-contracts.json \
  --openapi-output artifacts/openapi.json
```

The CLI supports `--base-url`, `--actor-id`, `--workspace-id`, `--scope`,
`--trace-id`, `--correlation-id`, `--idempotency-key`, and `--json`.

`bootstrap dev` prepares a safe local developer context through public APIs
only. It does not enable full autonomy, external models, external tools,
workers, schedulers, or domain modules.

See `docs/sdk.md` and `docs/cli.md`.

Event intake:

```bash
curl -X POST http://localhost:8080/brain/events \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "event-1",
    "source": "local",
    "event_type": "test.received",
    "payload_type": "test.payload",
    "payload": {"message": "hello"},
    "timestamp": "2026-06-06T23:55:00Z",
    "security_scope": ["workspace:read"]
  }'
```

The event ledger is the canonical record of accepted external signals. Each
accepted `AIONEvent` is persisted to Postgres before any publication attempt.
Accepted events are then published to NATS on `aion.events.<event_type>` so
future Brain subsystems can react without coupling directly to intake callers.
If NATS publishing fails, the event remains persisted and the response reports
`published: false`.

Event Reaction Router:

AION Brain can route persisted events through generic subscriptions. The router
matches event type patterns, source filters, and deterministic trigger rules,
then creates auditable dispatch/action records. It is enabled as a control
plane by default, but automatic dispatch from event intake is disabled by
default with `AION_EVENT_AUTO_DISPATCH_ENABLED=false`. There is no background
consumer in v0.1; dispatch runs only through explicit API calls or opt-in
best-effort intake dispatch.

The default reaction mode is `dry_run`. Controlled reactions must pass policy,
autonomy, risk, and approval gates before the action runner can call another
Brain subsystem. Workflow, cognitive-cycle, and capability targets remain
dry-run unless explicit metadata allows controlled behavior.

```bash
curl -X POST http://localhost:8080/brain/event-router/subscriptions \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Generic reaction",
    "description": "React to generic events.",
    "event_type_patterns": ["generic.*"],
    "target_type": "noop"
  }'

curl -X POST http://localhost:8080/brain/event-router/dispatch \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "event-1",
    "owner_scope": ["workspace:main"],
    "mode": "dry_run"
  }'
```

Event Reaction endpoints:

- `POST /brain/event-router/subscriptions`
- `GET /brain/event-router/subscriptions`
- `GET /brain/event-router/subscriptions/{subscription_id}`
- `POST /brain/event-router/subscriptions/{subscription_id}/disable`
- `POST /brain/event-router/dispatch`
- `GET /brain/event-router/dispatches/{dispatch_id}`
- `GET /brain/event-router/dispatches`
- `GET /brain/event-router/dead-letters`
- `POST /brain/event-router/dead-letters/{dead_letter_id}/resolve`
- `POST /brain/event-router/dead-letters/{dead_letter_id}/replay`
- `GET /brain/event-router/status`

Failed controlled actions are retained as dead letters when
`AION_EVENT_DEAD_LETTER_ENABLED=true`. Replay is policy-gated, bounded by
`AION_EVENT_REPLAY_MAX_COUNT`, and uses dry-run mode by default.

Cognitive cycles:

```bash
curl -X POST http://localhost:8080/brain/cycles/run \
  -H 'Content-Type: application/json' \
  -d '{
    "cycle_type": "review",
    "mode": "dry_run",
    "owner_scope": ["workspace:main"],
    "input": {}
  }'

curl -X POST http://localhost:8080/brain/cycles/sleep-consolidation \
  -H 'Content-Type: application/json' \
  -d '{"scope": ["workspace:main"]}'

curl http://localhost:8080/brain/cycles/status/sleep_consolidation?scope=workspace:main
```

Cycles are manual-only in v0.1. `dry_run` is the default mode, controlled mode
requires approval by default, and no automatic background cycle runner is
enabled.

Memory fabric:

```bash
curl -X POST http://localhost:8080/brain/memory \
  -H 'Content-Type: application/json' \
  -d '{
    "memory_id": "memory-1",
    "memory_type": "semantic",
    "owner_scope": ["workspace:main"],
    "source_event_id": null,
    "content_ref": "content://memory-1",
    "summary": "AION stores memory as governed metadata plus summary.",
    "confidence": 0.9,
    "sensitivity": "low",
    "created_at": "2026-06-06T23:58:00Z",
    "expires_at": null,
    "metadata": {}
  }'

curl -X POST http://localhost:8080/brain/memory/retrieve \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "governed memory",
    "scope": ["workspace:main"],
    "limit": 10,
    "memory_types": []
  }'
```

Memory records can also be read with `GET /brain/memory/{memory_id}` and
soft-deleted with `DELETE /brain/memory/{memory_id}`.

Memory governance:

```bash
curl -X POST http://localhost:8080/brain/memory/governance/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "memory": {
      "memory_id": "memory-1",
      "memory_type": "semantic",
      "owner_scope": ["workspace:main"],
      "source_event_id": null,
      "content_ref": "content://memory-1",
      "summary": "AION memory recall is governed recall.",
      "confidence": 0.9,
      "sensitivity": "internal",
      "created_at": "2026-06-06T23:58:00Z",
      "expires_at": null,
      "metadata": {}
    },
    "action_type": "memory.retrieve",
    "owner_scope": ["workspace:main"]
  }'
```

Governance endpoints:

- `POST /brain/memory/governance/rules`
- `GET /brain/memory/governance/rules`
- `POST /brain/memory/governance/rules/{governance_rule_id}/disable`
- `POST /brain/memory/governance/evaluate`
- `POST /brain/memory/decay/recompute`
- `POST /brain/memory/retention/sweep`
- `POST /brain/memory/forget`
- `GET /brain/memory/forget/{forget_request_id}`
- `POST /brain/memory/conflicts`
- `GET /brain/memory/conflicts`
- `POST /brain/memory/conflicts/{conflict_id}/resolve`
- `POST /brain/memory/compact`
- `GET /brain/memory/compact/{compaction_run_id}`

Memory Governance makes recall safe and current. It evaluates write and
retrieval rules, computes deterministic decay scores, performs retention sweeps,
creates approval-backed forgetting requests, detects generic memory conflicts,
and compacts low-level records into deterministic semantic, procedural, or
preference summaries. It never hard-deletes evidence by default, never treats
vector or graph recall as truth, and makes no external model or network calls.

Postgres is the canonical store for memory metadata. Retrieval in v0.1 is
deterministic lexical recall: exact token overlap, then recency, then confidence.
Semantic memory adds vector recall through `SemanticMemoryAdapter`. pgvector is
the local baseline, backed by the `pgvector/pgvector:pg16` Docker image.
Hash embeddings are deterministic and local; they are only a baseline for
wiring the Brain and do not call external model or embedding APIs.

TurboVec compressed semantic recall is available as an optional adapter behind
`SemanticMemoryAdapter`. It is disabled by default, uses no direct TurboVec
imports outside `aion_brain.memory.turbovec_compat`, and falls open to pgvector
when configured to do so. Postgres remains the canonical memory ledger.

Semantic memory:

```bash
curl -X POST http://localhost:8080/brain/memory/semantic/index/memory-1

curl -X POST http://localhost:8080/brain/memory/semantic/retrieve \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "governed memory",
    "scope": ["workspace:main"],
    "limit": 10,
    "memory_types": [],
    "min_score": null
  }'

curl -X POST http://localhost:8080/brain/memory/semantic/reindex-all \
  -H 'Content-Type: application/json' \
  -d '{
    "scope": ["workspace:main"],
    "limit": 100
  }'

curl http://localhost:8080/brain/memory/semantic/adapters

curl http://localhost:8080/brain/memory/semantic/turbovec/status

curl -X POST http://localhost:8080/brain/memory/semantic/turbovec/rebuild \
  -H 'Content-Type: application/json' \
  -d '{
    "index_name": "default",
    "scope": ["workspace:main"],
    "memory_types": [],
    "limit": 1000,
    "force": false,
    "dry_run": true
  }'

curl -X POST http://localhost:8080/brain/memory/semantic/turbovec/reindex/memory-1 \
  -H 'Content-Type: application/json' \
  -d '{
    "index_name": "default",
    "force": false
  }'
```

Vector memory is recall, not truth. Postgres remains the canonical store for
memory metadata, and `content_ref` remains the pointer to source evidence.
The TurboVec index stores compressed recall pointers only: memory IDs, vector
IDs, hashes, scope, memory type, and index metadata.

Temporal graph memory:

```bash
curl -X POST http://localhost:8080/brain/memory/graph/nodes \
  -H 'Content-Type: application/json' \
  -d '{
    "node_id": "node-1",
    "node_type": "concept",
    "label": "governed memory",
    "owner_scope": ["workspace:main"],
    "properties": {"summary": "generic relationship memory"},
    "source_event_id": null,
    "confidence": 0.8,
    "sensitivity": "low",
    "valid_from": null,
    "valid_to": null,
    "observed_at": "2026-06-07T00:30:00Z",
    "created_at": null,
    "updated_at": null,
    "deleted_at": null
  }'

curl -X POST http://localhost:8080/brain/memory/graph/edges \
  -H 'Content-Type: application/json' \
  -d '{
    "edge_id": "edge-1",
    "edge_type": "related_to",
    "from_node_id": "node-1",
    "to_node_id": "node-2",
    "owner_scope": ["workspace:main"],
    "properties": {},
    "source_event_id": null,
    "confidence": 0.7,
    "sensitivity": "low",
    "valid_from": null,
    "valid_to": null,
    "observed_at": "2026-06-07T00:31:00Z",
    "created_at": null,
    "updated_at": null,
    "deleted_at": null
  }'

curl 'http://localhost:8080/brain/memory/graph/nodes/node-1?scope=workspace:main'
curl 'http://localhost:8080/brain/memory/graph/edges/edge-1?scope=workspace:main'

curl -X POST http://localhost:8080/brain/memory/graph/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "governed memory",
    "scope": ["workspace:main"],
    "node_types": [],
    "edge_types": [],
    "max_depth": 2,
    "limit": 25,
    "include_expired": false
  }'

curl -X POST http://localhost:8080/brain/memory/graph/neighbors/node-1 \
  -H 'Content-Type: application/json' \
  -d '{
    "scope": ["workspace:main"],
    "max_depth": 2,
    "limit": 25
  }'

curl -X DELETE 'http://localhost:8080/brain/memory/graph/nodes/node-1?scope=workspace:main'
curl -X DELETE 'http://localhost:8080/brain/memory/graph/edges/edge-1?scope=workspace:main'
```

Graph memory stores generic temporal nodes and edges in Postgres and powers the
future Obsidian-style Brain map. It is relationship recall, not truth. Scope,
provenance, confidence, sensitivity, `valid_from`, `valid_to`, and `observed_at`
are AION-owned semantics.

Graphiti temporal graph indexing is optional, disabled by default, and lives
behind `GraphMemoryAdapter`. The default adapter remains Postgres graph memory.
If Graphiti is selected but the package or backend is unavailable,
`AION_GRAPHITI_FAIL_OPEN_TO_POSTGRES_GRAPH=true` keeps canonical graph memory
available through Postgres. The Graphiti compatibility layer is the only place
allowed to import Graphiti, and v0.1 does not call external model providers for
Graphiti.

Graphiti adapter status and sync:

```bash
curl http://localhost:8080/brain/memory/graph/adapters
curl http://localhost:8080/brain/memory/graph/graphiti/status

curl -X POST http://localhost:8080/brain/memory/graph/graphiti/sync \
  -H 'Content-Type: application/json' \
  -d '{
    "config_name": "default",
    "scope": ["workspace:main"],
    "source_types": [],
    "limit": 10000,
    "dry_run": true,
    "force": false
  }'

curl -X POST http://localhost:8080/brain/memory/graph/graphiti/episodes \
  -H 'Content-Type: application/json' \
  -d '{
    "episode_id": null,
    "trace_id": "trace-1",
    "source_type": "event",
    "source_id": "event-1",
    "content": "A generic temporal context episode.",
    "scope": ["workspace:main"],
    "observed_at": "2026-06-07T00:31:00Z",
    "metadata": {}
  }'
```

Retrieval Router and Context Fusion:

```bash
curl -X POST http://localhost:8080/brain/retrieval/query \
  -H 'Content-Type: application/json' \
  -d '{
    "retrieval_id": "retrieval-1",
    "trace_id": "trace-1",
    "intent_id": "intent-1",
    "query": "governed memory",
    "scope": ["workspace:main"],
    "requested_sources": ["lexical_memory", "semantic_memory", "graph_memory"],
    "memory_types": [],
    "capability_ids": [],
    "limit": 10,
    "min_score": null,
    "include_graph": true,
    "include_capabilities": true,
    "include_recent_traces": false,
    "metadata": {}
  }'

curl -X POST http://localhost:8080/brain/retrieval/fuse \
  -H 'Content-Type: application/json' \
  -d '{
    "retrieval_result": "<RetrievalResult object>",
    "goal": "answer with clean context",
    "max_items": 10,
    "max_chars": 12000,
    "metadata": {}
  }'

curl http://localhost:8080/brain/retrieval/retrieval-1
```

The Retrieval Router selects, filters, ranks, deduplicates, persists, and emits
telemetry for context candidates. The Context Fusion Engine turns those
candidates into a deterministic `ContextBundle` that feeds `ContextPacket`.
This layer powers the future Brain view and reasoning layer without LLM calls,
external AI calls, or domain-specific retrieval rules.

Reasoning Mesh and model gateway boundary:

```bash
curl -X POST http://localhost:8080/brain/reason \
  -H 'Content-Type: application/json' \
  -d '{
    "reasoning_id": "reasoning-1",
    "trace_id": "trace-1",
    "intent": null,
    "context": {
      "context_id": "context-1",
      "intent_id": "intent-1",
      "goal": "answer a generic question",
      "known_context": [{"source": "intent", "intent_type": "question.answer"}],
      "retrieved_memory_ids": [],
      "available_capability_ids": [],
      "constraints": [],
      "open_questions": [],
      "execution_limits": {"no_external_model_calls": true}
    },
    "mode": "analyze",
    "risk_level": "low",
    "metadata": {"security_scope": ["workspace:main"]}
  }'

curl http://localhost:8080/brain/reason/reasoning-1
curl http://localhost:8080/brain/model-calls/model-call-prompt-reasoning-1
```

The Reasoning Mesh calls `ModelGatewayAdapter` through AION-owned contracts
only. v0.1 routes to `aion-local` / `deterministic-reasoner-v0`, persists
reasoning runs and model call records, and emits visual telemetry for reasoning
activity. LiteLLM is a placeholder adapter only. No OpenAI, Anthropic, Gemini,
Ollama, LiteLLM, or external model service is called.

Policy authorization:

```bash
curl -X POST http://localhost:8080/brain/policy/authorize \
  -H 'Content-Type: application/json' \
  -d '{
    "request_id": "policy-request-1",
    "trace_id": "trace-1",
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "action_type": "memory.retrieve",
    "resource_type": "memory",
    "resource_id": "memory-1",
    "risk_level": "low",
    "approval_present": false,
    "requested_permissions": ["memory:read"],
    "security_scope": ["memory:read"],
    "context": {}
  }'
```

Open Policy Agent is the local policy engine for v0.1. AION Brain posts generic
`PolicyRequest` contracts to OPA and returns AION-owned `PolicyDecision`
contracts. Policy engine failures fail closed with `allow: false` and reason
`policy_engine_unavailable`.

Risk, guardrails, and approvals:

```bash
curl -X POST http://localhost:8080/brain/risk/assess \
  -H 'Content-Type: application/json' \
  -d '{
    "action_type": "capability.invoke",
    "resource_type": "capability",
    "requested_risk_level": "high",
    "payload": {},
    "context": {"security_scope": ["workspace:main"]}
  }'

curl -X POST http://localhost:8080/brain/risk/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "risk": {
      "action_type": "capability.invoke",
      "resource_type": "capability",
      "requested_risk_level": "high",
      "payload": {},
      "context": {"security_scope": ["workspace:main"]}
    }
  }'

curl http://localhost:8080/brain/approvals?scope=workspace:main
curl -X POST http://localhost:8080/brain/approvals/approval-1/decide \
  -H 'Content-Type: application/json' \
  -d '{"approval_request_id": "approval-1", "decision": "approve"}'
```

The Risk Engine produces deterministic `RiskAssessment` records. Guardrails
evaluate generic safety rules and can require approval or block an action.
Approvals are explicit pending records; approving a request does not
automatically execute the original action. A caller must submit a new governed
request with approval evidence.

Risk and approval endpoints:

- `POST /brain/risk/assess`
- `POST /brain/risk/evaluate`
- `POST /brain/guardrails`
- `GET /brain/guardrails`
- `POST /brain/guardrails/{guardrail_id}/disable`
- `POST /brain/guardrails/evaluate`
- `POST /brain/approvals`
- `GET /brain/approvals`
- `GET /brain/approvals/{approval_request_id}`
- `POST /brain/approvals/{approval_request_id}/decide`
- `POST /brain/approvals/{approval_request_id}/cancel`
- `POST /brain/approvals/{approval_request_id}/expire`

Module Bus and Capability Runtime Gateway:

```bash
curl -X POST http://localhost:8080/brain/capabilities/register \
  -H 'Content-Type: application/json' \
  -d '{
    "module_id": "test.module",
    "version": "0.1.0",
    "capabilities": [{"capability_id": "aion.internal.noop"}],
    "permissions_required": [],
    "memory_read_scopes": [],
    "memory_write_scopes": [],
    "events_subscribed": [],
    "events_published": [],
    "execution_mode": "sync"
  }'

curl -X POST http://localhost:8080/brain/modules/runtimes/register \
  -H 'Content-Type: application/json' \
  -d '{
    "runtime": {
      "runtime_id": "runtime-1",
      "module_id": "test.module",
      "version": "0.1.0",
      "runtime_type": "local_internal",
      "endpoint_ref": null,
      "status": "registered",
      "health_status": "unknown",
      "config": {},
      "created_at": null,
      "updated_at": null,
      "last_health_check_at": null
    },
    "bind_capabilities": [],
    "activate": true
  }'

curl http://localhost:8080/brain/modules/runtimes
curl http://localhost:8080/brain/modules/runtimes/runtime-1
curl -X POST http://localhost:8080/brain/modules/runtimes/runtime-1/health-check

curl -X POST http://localhost:8080/brain/capabilities/aion.internal.noop/bind-runtime \
  -H 'Content-Type: application/json' \
  -d '{
    "capability_id": "aion.internal.noop",
    "module_id": "test.module",
    "runtime_id": "runtime-1",
    "invocation_mode": "dry_run",
    "status": "active"
  }'

curl -X POST http://localhost:8080/brain/capabilities/invoke \
  -H 'Content-Type: application/json' \
  -d '{
    "invocation_id": "invocation-1",
    "trace_id": "trace-1",
    "execution_id": null,
    "step_run_id": null,
    "capability_id": "aion.internal.noop",
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "mode": "dry_run",
    "payload": {},
    "approval_present": false,
    "metadata": {}
  }'
```

The Capability Registry stores what can be done. Module Runtime records store
where and how it can be done. Capability Runtime Binding connects a capability
to a runtime, and Capability Runtime Gateway is the only invocation path.
Runtime registration does not imply execution approval.

v0.1 module runtime is local, deterministic, and side-effect-free. HTTP and MCP
runtimes do not execute real external tools by default. The only ordinary
controlled executable runtime is `local_internal`, and it supports only safe
generic internal capabilities:
`aion.internal.noop`, `aion.internal.echo`,
`aion.internal.validate_payload`, and `aion.internal.describe_invocation`.

MCP Capability Protocol Adapter:

MCP is optional and disabled by default. AION Capability Manifest is the
internal governance contract; MCP tools are interoperability metadata that can
be mapped into AION capabilities. AION supplies risk, permissions, memory
scope, execution mode, audit level, policy gates, invocation records, and
telemetry. MCP does not self-authorize.

Safe defaults:

- `AION_MCP_ENABLED=false`
- `AION_MCP_ALLOW_NETWORK=false`
- `AION_MCP_ALLOW_STDIO=false`
- normal tests do not require the MCP SDK
- dry-run invocation does not call MCP
- real network and stdio transports are blocked unless explicitly enabled

To enable MCP later, install the optional dependency group, set
`AION_MCP_ENABLED=true`, explicitly allow network or stdio if needed, register
a server, sync tools, and map tools into AION capabilities. Stdio config rejects
shell control characters, and MCP config rejects secret-like keys.

```bash
curl http://localhost:8080/brain/mcp/status

curl -X POST http://localhost:8080/brain/mcp/servers \
  -H 'Content-Type: application/json' \
  -d '{
    "server": {
      "mcp_server_id": "mcp-server-1",
      "server_name": "test-server",
      "transport_type": "in_memory_fake",
      "endpoint_ref": null,
      "status": "registered",
      "health_status": "unknown",
      "config": {},
      "owner_scope": ["workspace:main"],
      "created_at": null,
      "updated_at": null,
      "last_health_check_at": null,
      "disabled_at": null
    },
    "activate": true,
    "discover_tools": false,
    "metadata": {}
  }'

curl -X POST http://localhost:8080/brain/mcp/sync \
  -H 'Content-Type: application/json' \
  -d '{
    "mcp_server_id": "mcp-server-1",
    "dry_run": true,
    "auto_register_capabilities": false,
    "default_risk_level": "medium",
    "default_permissions_required": [],
    "owner_scope": ["workspace:main"],
    "metadata": {}
  }'

curl http://localhost:8080/brain/mcp/mappings

curl -X POST http://localhost:8080/brain/mcp/invoke \
  -H 'Content-Type: application/json' \
  -d '{
    "mcp_invocation_id": null,
    "invocation_id": "invocation-1",
    "mcp_server_id": "mcp-server-1",
    "mcp_tool_name": "echo",
    "capability_id": "mcp.test-server.echo",
    "trace_id": null,
    "execution_id": null,
    "step_run_id": null,
    "actor_id": null,
    "workspace_id": null,
    "mode": "dry_run",
    "payload": {},
    "approval_present": false,
    "metadata": {}
  }'
```

MCP endpoints:

- `GET /brain/mcp/status`
- `POST /brain/mcp/servers`
- `GET /brain/mcp/servers`
- `GET /brain/mcp/servers/{mcp_server_id}`
- `POST /brain/mcp/servers/{mcp_server_id}/disable`
- `POST /brain/mcp/servers/{mcp_server_id}/health-check`
- `POST /brain/mcp/sync`
- `GET /brain/mcp/mappings`
- `POST /brain/mcp/invoke`

Deterministic Brain runtime:

```bash
curl -X POST http://localhost:8080/brain/plan \
  -H 'Content-Type: application/json' \
  -d '{
    "context": {
      "context_id": "context-1",
      "intent_id": "intent-1",
      "goal": "answer a generic question",
      "known_context": [{"source": "intent", "intent_type": "question.answer"}],
      "retrieved_memory_ids": [],
      "available_capability_ids": [],
      "constraints": [],
      "open_questions": [],
      "execution_limits": {"no_model_calls": true}
    }
  }'

curl -X POST http://localhost:8080/brain/think \
  -H 'Content-Type: application/json' \
  -d '{
    "event_id": "event-1",
    "source": "local",
    "event_type": "question.answer",
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "payload_type": "test.payload",
    "payload": {"question": "what should happen?"},
    "timestamp": "2026-06-07T00:00:00Z",
    "correlation_id": "corr-1",
    "trace_id": "trace-1",
    "security_scope": ["workspace:main"]
  }'
```

`/brain/think` runs and persists the deterministic v0.1 loop:

```text
Event -> Intent -> Context -> Reasoning -> Plan -> Policy -> Trace -> Evaluate -> Learn -> Telemetry
```

The runtime uses LangGraph only behind `BrainRuntimeAdapter`. Public AION APIs
return AION contracts and never expose LangGraph or provider SDK objects. The
v0.1 reasoning step is deterministic-local only: no external LLM calls or real
capability invocation occur.

Execution Orchestrator:

```bash
curl -X POST http://localhost:8080/brain/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "execution_id": "execution-1",
    "trace_id": "trace-1",
    "plan": {
      "plan_id": "plan-1",
      "intent_id": "intent-1",
      "goal": "answer a generic question",
      "steps": [
        {
          "step_id": "retrieve_context",
          "action_type": "memory.retrieve",
          "capability_required": "memory.retrieve",
          "risk_level": "low",
          "status": "pending"
        }
      ],
      "dependencies": [],
      "risk_level": "low",
      "approval_required": false,
      "status": "draft",
      "metadata": {}
    },
    "requested_by": "actor-1",
    "workspace_id": "workspace-1",
    "mode": "dry_run",
    "approval_present": false,
    "max_steps": 50,
    "metadata": {"security_scope": ["workspace:main"]}
  }'

curl http://localhost:8080/brain/executions/execution-1
curl http://localhost:8080/brain/executions/execution-1/steps
curl http://localhost:8080/brain/executions/execution-1/approvals

curl -X POST http://localhost:8080/brain/executions/execution-1/cancel \
  -H 'Content-Type: application/json' \
  -d '{"reason": "operator requested stop"}'

curl -X POST http://localhost:8080/brain/approvals/approval-1/resolve \
  -H 'Content-Type: application/json' \
  -d '{"approved": true, "approved_by": "actor-2", "reason": "approved"}'
```

v0.1 execution is deterministic, policy-gated, and side-effect-free. `dry_run`
is the default mode and validates steps without invoking capabilities.
`controlled` mode only completes safe internal Brain steps and capability
steps through `CapabilityInvoker -> CapabilityRuntimeGateway`. The Brain never
calls module code, MCP servers, HTTP endpoints, shell commands, browser
drivers, SaaS APIs, or vendor SDKs directly. Temporal remains a placeholder
behind an adapter and is not imported.

Goal Manager and Cognitive Task Queue:

```bash
curl -X POST http://localhost:8080/brain/goals \
  -H 'Content-Type: application/json' \
  -d '{
    "goal_id": "goal-1",
    "trace_id": "trace-1",
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "title": "Hold a generic objective",
    "description": "Track a domain-neutral goal over time.",
    "priority": "normal",
    "risk_level": "medium",
    "owner_scope": ["workspace:main"],
    "constraints": [],
    "success_criteria": [],
    "metadata": {}
  }'

curl http://localhost:8080/brain/goals/goal-1?scope=workspace:main
curl http://localhost:8080/brain/goals?scope=workspace:main
curl -X POST http://localhost:8080/brain/goals/goal-1/transition \
  -H 'Content-Type: application/json' \
  -d '{"to_status": "active", "reason": "ready"}'

curl -X POST http://localhost:8080/brain/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "task_id": "task-1",
    "goal_id": "goal-1",
    "trace_id": "trace-1",
    "plan_id": "plan-1",
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "title": "Review the generic plan",
    "description": "Store an explicit cognitive task.",
    "task_type": "brain.plan",
    "priority": "normal",
    "risk_level": "medium",
    "owner_scope": ["workspace:main"],
    "input": {},
    "constraints": [],
    "metadata": {}
  }'

curl http://localhost:8080/brain/tasks/task-1?scope=workspace:main
curl http://localhost:8080/brain/tasks?scope=workspace:main
curl -X POST http://localhost:8080/brain/tasks/task-1/transition \
  -H 'Content-Type: application/json' \
  -d '{"to_status": "queued", "reason": "ready"}'
curl -X POST http://localhost:8080/brain/tasks/task-1/run \
  -H 'Content-Type: application/json' \
  -d '{"run_mode": "dry_run", "approval_present": false, "metadata": {}}'
curl http://localhost:8080/brain/tasks/task-1/runs

curl -X POST http://localhost:8080/brain/schedules \
  -H 'Content-Type: application/json' \
  -d '{
    "schedule_id": "schedule-1",
    "owner_type": "task",
    "owner_id": "task-1",
    "schedule_type": "once",
    "schedule_expression": "2026-06-07T09:00:00Z",
    "timezone": "UTC",
    "metadata": {}
  }'

curl http://localhost:8080/brain/schedules/schedule-1
curl http://localhost:8080/brain/schedules?owner_type=task
curl -X POST http://localhost:8080/brain/schedules/schedule-1/pause
curl -X POST http://localhost:8080/brain/schedules/schedule-1/cancel
```

Goal and task state is owned by AION Brain. Future modules may request
lifecycle changes through events or capability contracts, but modules do not
own Brain lifecycle state. Task runs are explicit and policy-gated. NATS
lifecycle publishing is best-effort: publish failures are logged and never undo
persisted goal, task, run, schedule, or lifecycle records. Schedule support is
metadata only in v0.1; there is no background scheduler loop and no Temporal
integration yet.

`/brain/think` advertises `goal_endpoint` and `task_endpoint` in the returned
trace outcome. It creates proposed `GoalRecord` or `CognitiveTask` records only
when the event payload explicitly sets `create_goal: true` or
`create_task: true`.

Trace, evaluation, learning, and telemetry APIs:

```bash
curl http://localhost:8080/brain/traces/trace-1
curl http://localhost:8080/brain/traces/trace-1/evaluation
curl http://localhost:8080/brain/traces/trace-1/learning
curl http://localhost:8080/brain/traces/trace-1/telemetry

curl -X POST http://localhost:8080/brain/evaluate \
  -H 'Content-Type: application/json' \
  -d '<DecisionTrace JSON>'

curl -X POST http://localhost:8080/brain/learn \
  -H 'Content-Type: application/json' \
  -d '{
    "trace": "<DecisionTrace object>",
    "evaluation": "<EvaluationRecord object>"
  }'
```

Visual telemetry records are stored for the future Brain visualization. They
represent active nodes and edges across events, intents, contexts, memories,
reasoning runs, model routes, capabilities, plans, policies, evaluations,
execution runs, approval checkpoints, learning signals, and traces. No UI code
is implemented in v0.1.

Reflection Engine and Skill Registry:

```bash
curl -X POST http://localhost:8080/brain/reflections \
  -H 'Content-Type: application/json' \
  -d '{
    "reflection_id": "reflection-1",
    "reflection_type": "trace_review",
    "metadata": {}
  }'

curl http://localhost:8080/brain/reflections/reflection-1
curl 'http://localhost:8080/brain/reflections?trace_id=trace-1&status=recorded'

curl -X POST http://localhost:8080/brain/skills/candidates/from-reflection/reflection-1
curl http://localhost:8080/brain/skills/candidates/candidate-1
curl http://localhost:8080/brain/skills/candidates
curl -X POST http://localhost:8080/brain/skills/candidates/candidate-1/status \
  -H 'Content-Type: application/json' \
  -d '{"status": "approved", "reason": "reviewed"}'

curl -X POST http://localhost:8080/brain/skills/promote \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_id": "candidate-1",
    "owner_scope": ["workspace:main"],
    "activate": false,
    "reason": "approved procedural memory"
  }'

curl 'http://localhost:8080/brain/skills/skill-1?scope=workspace:main'
curl 'http://localhost:8080/brain/skills?scope=workspace:main&status=active'
curl -X POST http://localhost:8080/brain/skills/skill-1/transition \
  -H 'Content-Type: application/json' \
  -d '{"to_status": "active", "reason": "operator approved"}'
curl -X POST http://localhost:8080/brain/skills/match \
  -H 'Content-Type: application/json' \
  -d '{"query": "question plan", "scope": ["workspace:main"], "limit": 10}'
```

Reflections convert evaluated traces, task runs, retrieval outcomes, reasoning
results, and execution outcomes into deterministic review records. Skill
candidates can be created from generic reflections, but candidates require
review, promotion requires policy, and activation requires policy. Skills are
procedural memory data records, not generated code or executable source.

`/brain/think` creates a reflection only when the event payload explicitly sets
`reflect: true`. It creates a skill candidate only when the payload also sets
`create_skill_candidate: true`. It never promotes or activates a skill.

v0.1 learning creates reflections and skill candidates. It never rewrites code
and never promotes skills automatically.

Identity, workspace, scope, and permission control plane:

```bash
curl http://localhost:8080/brain/me

curl -X POST http://localhost:8080/brain/identity/actors \
  -H 'Content-Type: application/json' \
  -H 'X-AION-Actor-ID: dev-user' \
  -H 'X-AION-Workspace-ID: dev-workspace' \
  -d '{
    "actor_id": "actor-1",
    "actor_type": "user",
    "display_name": "Local Operator",
    "status": "active",
    "metadata": {}
  }'

curl http://localhost:8080/brain/identity/actors/actor-1
curl http://localhost:8080/brain/identity/actors
curl -X POST http://localhost:8080/brain/identity/actors/actor-1/disable \
  -H 'Content-Type: application/json' \
  -d '{"reason": "local test complete"}'

curl -X POST http://localhost:8080/brain/workspaces \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id": "workspace-1",
    "name": "Main Workspace",
    "status": "active",
    "owner_actor_id": "actor-1",
    "metadata": {}
  }'

curl http://localhost:8080/brain/workspaces/workspace-1
curl http://localhost:8080/brain/workspaces
curl -X POST http://localhost:8080/brain/workspaces/workspace-1/archive \
  -H 'Content-Type: application/json' \
  -d '{"reason": "local archive test"}'

curl -X POST http://localhost:8080/brain/workspaces/workspace-1/memberships \
  -H 'Content-Type: application/json' \
  -d '{
    "membership_id": "membership-1",
    "workspace_id": "workspace-1",
    "actor_id": "actor-1",
    "role": "owner",
    "status": "active",
    "metadata": {}
  }'

curl http://localhost:8080/brain/workspaces/workspace-1/memberships
curl -X POST \
  http://localhost:8080/brain/workspaces/workspace-1/memberships/membership-1/revoke \
  -H 'Content-Type: application/json' \
  -d '{"reason": "local revoke test"}'

curl -X POST http://localhost:8080/brain/identity/permissions \
  -H 'Content-Type: application/json' \
  -d '{
    "grant_id": "grant-1",
    "actor_id": "actor-1",
    "workspace_id": null,
    "role": null,
    "permission": "memory.read",
    "resource_type": "memory",
    "resource_id": null,
    "effect": "allow",
    "status": "active",
    "metadata": {}
  }'

curl http://localhost:8080/brain/identity/permissions?actor_id=actor-1
curl -X POST http://localhost:8080/brain/identity/permissions/grant-1/revoke \
  -H 'Content-Type: application/json' \
  -d '{"reason": "local revoke test"}'

curl -X POST http://localhost:8080/brain/scopes/resolve \
  -H 'Content-Type: application/json' \
  -H 'X-AION-Actor-ID: actor-1' \
  -H 'X-AION-Workspace-ID: workspace-1' \
  -H 'X-AION-Roles: owner' \
  -H 'X-AION-Security-Scope: workspace:workspace-1' \
  -d '{
    "actor_id": "actor-1",
    "workspace_id": "workspace-1",
    "action_type": "memory.retrieve",
    "resource_type": "memory",
    "resource_id": null,
    "requested_scopes": ["workspace:workspace-1"]
  }'
```

v0.1 identity is local development metadata and header-based dev context.
Production authentication is deferred. Dev context reads only `X-AION-*`
headers and never cookies, bearer tokens, OAuth sessions, SSO, or external
identity provider state.

The control plane owns `ActorRecord`, `WorkspaceRecord`,
`WorkspaceMembership`, `PermissionGrant`, `ActorContext`,
`ScopeResolutionRequest`, and `ScopeResolution`. Permission grants use generic
dotted permissions, deny grants override allow grants, disabled actors cannot
resolve scopes, and archived workspaces block normal activity. Metadata rejects
secret-like keys. Identity and scope activity emits visual telemetry for the
future Brain graph.

Evidence Vault and source grounding:

```bash
curl -X POST http://localhost:8080/brain/evidence \
  -H 'Content-Type: application/json' \
  -H 'X-AION-Actor-ID: dev-user' \
  -H 'X-AION-Workspace-ID: dev-workspace' \
  -H 'X-AION-Roles: owner' \
  -H 'X-AION-Security-Scope: workspace:main' \
  -d '{
    "evidence_id": "evidence-1",
    "trace_id": "trace-1",
    "source_type": "text",
    "source_ref": null,
    "owner_scope": ["workspace:main"],
    "title": "Local source note",
    "content_text": "AION Evidence stores source material for grounding.",
    "summary": null,
    "content_ref": null,
    "media_type": "text/plain",
    "sensitivity": "internal",
    "confidence": 1.0,
    "metadata": {},
    "chunk_size_chars": 500,
    "chunk_overlap_chars": 50
  }'

curl 'http://localhost:8080/brain/evidence/evidence-1?scope=workspace:main'
curl 'http://localhost:8080/brain/evidence/evidence-1/chunks?scope=workspace:main'

curl -X POST http://localhost:8080/brain/evidence/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "source grounding", "scope": ["workspace:main"], "limit": 10}'

curl -X POST http://localhost:8080/brain/evidence/links \
  -H 'Content-Type: application/json' \
  -d '{
    "link_id": "link-1",
    "evidence_id": "evidence-1",
    "target_type": "memory",
    "target_id": "memory-1",
    "relation_type": "supports",
    "trace_id": "trace-1",
    "confidence": 0.9,
    "metadata": {}
  }'

curl 'http://localhost:8080/brain/evidence/evidence-1/links?scope=workspace:main'

curl -X POST http://localhost:8080/brain/evidence/ground \
  -H 'Content-Type: application/json' \
  -d '{
    "trace_id": "trace-1",
    "statements": [
      {"statement_id": "statement-1", "statement": "Evidence stores source material."}
    ],
    "scope": ["workspace:main"],
    "limit_per_statement": 5
  }'

curl -X DELETE 'http://localhost:8080/brain/evidence/evidence-1?scope=workspace:main'
```

The Evidence Vault stores source metadata, text chunks, content hashes,
evidence links, and deterministic grounding claims. Memory may recall; evidence
must ground. AION Brain must never treat vector memory, graph memory, or model
output as truth without evidence linkage.

v0.1 evidence ingestion supports text and metadata-only content references. It
does not fetch URLs, parse files, run OCR, or process binary uploads. MinIO is
reserved behind a future object storage adapter; AION contracts remain
independent of MinIO internals.

## Visual Brain Projection and Observability Spine

AION Visual Brain Projection converts canonical cognitive telemetry into a
frontend-agnostic Brain Map. A map contains nodes, typed edges, short-lived
pulses, deterministic clusters, a trace timeline, and intensity values with
time decay. Nodes represent Brain-owned cognitive artifacts. Edges preserve
generic relationships. Pulses represent recent activity. Clusters group related
memory, reasoning, execution, lifecycle, learning, identity, capability,
evidence, and trace nodes.

The Observability Spine records sanitized local lifecycle events for the Brain
loop and summarizes them with visual telemetry. The v0.1 adapter is local.
Langfuse remains a placeholder behind an AION-owned adapter boundary and is not
imported or called.

Visual and observability endpoints:

- `POST /brain/visual/map`
- `GET /brain/visual/map/traces/{trace_id}`
- `POST /brain/visual/snapshots`
- `GET /brain/visual/snapshots/{snapshot_id}`
- `POST /brain/visual/telemetry/query`
- `GET /brain/visual/telemetry/recent`
- `POST /brain/visual/timeline`
- `GET /brain/visual/timeline/{trace_id}`
- `GET /brain/visual/stream`
- `POST /brain/observability/events`
- `GET /brain/observability/summary`
- `GET /brain/observability/traces/{trace_id}/timeline`

Example:

```bash
curl -X POST http://localhost:8080/brain/visual/map \
  -H 'Content-Type: application/json' \
  -H 'X-AION-Security-Scope: workspace:main' \
  -d '{"trace_id": "trace-1", "scope": ["workspace:main"]}'

curl 'http://localhost:8080/brain/visual/stream?scope=workspace:main&max_events=5'
curl 'http://localhost:8080/brain/observability/summary?scope=workspace:main'
```

v0.1 provides the backend data form for the Brain visualization. It does not
implement frontend UI.

## Cognitive Replay and Regression

AION Brain can capture content-addressed Brain snapshots, replay a completed
trace through the deterministic Brain loop, compare semantic outcomes, and run
golden trace regression cases. Snapshot hashes use normalized JSON. Comparison
ignores identity and timestamp noise while detecting drift in plans, policy
outcomes, evaluation scores, required sections, and final outcome status.

Replay mode is enforced inside the Brain loop. It disables lifecycle,
reflection, skill, scheduling, controlled execution, and external side effects
while still allowing local replay traces, telemetry, evaluation, and learning
signals. Regression reports provide generic architecture recommendations only.

Replay and regression endpoints:

- `POST /brain/snapshots`
- `POST /brain/snapshots/from-trace/{trace_id}`
- `GET /brain/snapshots/{snapshot_id}`
- `GET /brain/snapshots`
- `POST /brain/replay`
- `GET /brain/replay/{replay_id}`
- `POST /brain/replay/compare`
- `POST /brain/regression/cases`
- `GET /brain/regression/cases/{case_id}`
- `GET /brain/regression/cases`
- `POST /brain/regression/cases/{case_id}/disable`
- `POST /brain/regression/run`
- `GET /brain/regression/runs/{regression_run_id}`
- `POST /brain/eval/adapters/run`

v0.1 replay and regression are local, deterministic, and side-effect-free.
Promptfoo and Ragas are adapter placeholders only.

## Durable Workflows

AION Brain v0.1 includes a generic durable workflow engine for long-running
Brain work. Workflows are Brain-owned contracts and local database records;
they are not business-process modules. The default engine is local,
deterministic, and side-effect-free unless a run explicitly uses controlled
mode and passes policy.

The local scheduler and worker are disabled by default and never start a
background loop automatically. They run only through explicit one-shot API
calls or `./scripts/run-local-worker.sh`. Temporal is an optional future
adapter boundary; the SDK is not required for the default stack.

Workflow endpoints:

- `POST /brain/workflows`
- `GET /brain/workflows`
- `GET /brain/workflows/{workflow_id}`
- `POST /brain/workflows/{workflow_id}/activate`
- `POST /brain/workflows/{workflow_id}/disable`
- `POST /brain/workflows/run`
- `GET /brain/workflows/runs`
- `GET /brain/workflows/runs/{workflow_run_id}`
- `POST /brain/workflows/runs/{workflow_run_id}/pause`
- `POST /brain/workflows/runs/{workflow_run_id}/resume`
- `POST /brain/workflows/runs/{workflow_run_id}/cancel`
- `POST /brain/workflows/runs/{workflow_run_id}/retry`
- `POST /brain/workflows/scheduler/tick`
- `POST /brain/workflows/worker/start-once`
- `GET /brain/workflows/engine/status`
- `GET /brain/workflows/temporal/status`

Task runs may create workflow runs only when task or request metadata contains
`run_workflow=true` and a `workflow_id`. That handoff defaults to dry-run mode.

## Attention Controller And Working Memory

AION v0.1 attention is deterministic. Working memory is short-lived cognitive
state, not long-term truth or chain-of-thought storage.

The Attention Controller scores generic signals, maintains focus sessions,
routes interrupts, and allocates context budgets before context fusion. The
Context Compiler consumes `AttentionDecision` and `ContextBudget`; it does not
own attention.

New endpoints:

- `POST /brain/attention/signals`
- `GET /brain/attention/signals`
- `POST /brain/attention/decide`
- `POST /brain/attention/signals/{attention_signal_id}/handled`
- `POST /brain/focus`
- `GET /brain/focus/active`
- `GET /brain/focus/{focus_session_id}`
- `GET /brain/focus`
- `POST /brain/focus/{focus_session_id}/transition`
- `POST /brain/working-memory`
- `POST /brain/working-memory/query`
- `GET /brain/working-memory/{slot_id}`
- `POST /brain/working-memory/{slot_id}/pin`
- `POST /brain/working-memory/{slot_id}/unpin`
- `DELETE /brain/working-memory/{slot_id}`
- `POST /brain/working-memory/sweep-expired`
- `POST /brain/interrupts`
- `GET /brain/interrupts`
- `POST /brain/interrupts/{interrupt_id}/decide`
- `POST /brain/context-budget/allocate`

## Testing

```bash
./scripts/test.sh
./scripts/lint.sh
```

From the service directory:

```bash
cd services/brain-api
pytest
ruff check .
mypy src
```

## Kernel Assembly

AION Brain v0.1 is assembled through a composition root. External systems
remain behind adapters. `KernelContainer` owns process-wide construction,
adapter selection, service registration, boot diagnostics, the deterministic
self-test harness, contract export, and architecture boundary checks. Routes
can obtain the container from FastAPI app state and must not construct vendor
clients or service graphs themselves.

Kernel endpoints:

- `GET /brain/kernel/status`
- `GET /brain/kernel/boot/latest`
- `GET /brain/kernel/services`
- `POST /brain/kernel/self-test`
- `GET /brain/kernel/self-test/latest`
- `GET /brain/kernel/contracts`
- `POST /brain/kernel/boundary-check`
- `GET /brain/kernel/adapters`

The self-test is local, deterministic, dry-run by default, and does not call
external AI providers or execute modules. Contract export returns the current
OpenAPI document plus JSON schemas for core AION contracts. The boundary
checker prevents vendor imports, shell execution, production auth providers,
and domain directories from leaking into Brain core.

Operator scripts:

```bash
./scripts/self-test.sh
./scripts/export-contracts.sh
```

## Model Gateway

AION v0.1 uses deterministic local reasoning by default. External model calls
require explicit configuration, policy permission, and budget approval.

The Model Gateway adds a provider-neutral inference boundary without binding
AION Brain to any one model vendor. It includes a Provider Registry, Model
Profile Registry, deterministic router, prompt redaction, Budget Guard, usage
ledger, provider health checks, and optional LiteLLM-compatible and
OpenAI-compatible HTTP adapter boundaries. External model calls are disabled by
default.

Model Gateway endpoints:

- `POST /brain/model-providers`
- `GET /brain/model-providers`
- `GET /brain/model-providers/{provider_id}`
- `POST /brain/model-providers/{provider_id}/disable`
- `POST /brain/model-providers/{provider_id}/health-check`
- `POST /brain/model-profiles`
- `GET /brain/model-profiles`
- `GET /brain/model-profiles/{model_profile_id}`
- `POST /brain/model-profiles/{model_profile_id}/disable`
- `POST /brain/model-gateway/complete`
- `GET /brain/model-usage`
- `POST /brain/model-budgets`
- `GET /brain/model-budgets`

Prompt redaction blocks secret-like content by default. The Budget Guard blocks
external providers when no active budget exists and the default budget is zero.
The deterministic provider/profile remain available as the local fallback.

## Autonomy Governor

AION Brain v0.1 includes an Autonomy Governor that decides what operating mode
the Brain may use before execution-capable paths run. It is generic, policy
gated, and conservative by default. There is no full autonomy default.

Operating modes:

- `disabled`
- `observe`
- `assist`
- `plan_only`
- `dry_run`
- `supervised_controlled`
- `delegated_controlled`

The default development profile uses `assist` with `dry_run` as the maximum
mode, `medium` as the maximum risk, and external models/tools, schedulers,
background workers, skill promotion, and memory forgetting disabled unless
explicitly configured. Delegated controlled work requires an active delegation.

Autonomy endpoints:

- `POST /brain/autonomy/profiles`
- `GET /brain/autonomy/profiles`
- `GET /brain/autonomy/profiles/{autonomy_profile_id}`
- `POST /brain/autonomy/profiles/{autonomy_profile_id}/disable`
- `POST /brain/autonomy/run-levels`
- `GET /brain/autonomy/run-levels/active`
- `GET /brain/autonomy/run-levels`
- `POST /brain/autonomy/run-levels/{run_level_id}/end`
- `POST /brain/autonomy/delegations`
- `GET /brain/autonomy/delegations/{delegation_id}`
- `GET /brain/autonomy/delegations`
- `POST /brain/autonomy/delegations/{delegation_id}/revoke`
- `POST /brain/autonomy/decide`
- `GET /brain/autonomy/status`

Autonomy decisions are integrated into `/brain/think`, execution, durable
workflows, scheduler ticks, worker ticks, task runs, model completion, MCP tool
invocation, capability runtime invocation, skill activation, and memory
forgetting. Autonomy denial returns structured blocked results and does not
authorize side effects.

## Cognitive Cycles

AION Brain v0.1 includes a manual Cognitive Cycle Orchestrator for safe
operating rhythms. It owns domain-neutral templates, run records, step records,
sleep consolidation summaries, and maintenance previews. The orchestrator does
not start background loops and never runs automatically.

Supported cycle types:

- `wake`
- `active`
- `review`
- `sleep_consolidation`
- `maintenance`
- `shutdown`

Cycle endpoints:

- `POST /brain/cycles/templates`
- `GET /brain/cycles/templates`
- `POST /brain/cycles/templates/{cycle_template_id}/disable`
- `POST /brain/cycles/run`
- `POST /brain/cycles/sleep-consolidation`
- `GET /brain/cycles/runs`
- `GET /brain/cycles/runs/{cycle_run_id}`
- `GET /brain/cycles/status/{cycle_type}`
- `GET /brain/cycles/sleep-consolidation/{cycle_run_id}`

Sleep consolidation coordinates existing Brain boundaries only: attention
review, working-memory sweep, memory decay, conflict scan, compaction,
optional reflection/candidate creation, optional regression checks, visual
snapshot metadata, and local observability summary. Dry-run mode previews work
without mutation. Skill candidates are created only when explicitly requested,
and skills are never promoted by the cycle layer.

## Command Bus and Consistency

AION Brain v0.1 includes a generic consistency layer for retry-safe operations.
The Command Bus records intended Brain operations as `BrainCommand` records,
then gates dispatch through policy, autonomy, risk, and approval before a safe
handler runs. Idempotency records suppress duplicate HTTP/event retries.

The Transactional Outbox records messages that should be delivered after local
persistence. Inbox deduplication records incoming messages before processing so
future queues or module runtimes do not rely on at-most-once delivery.
Processing leases prevent duplicate local processing, and the Consistency
Checker reports stale leases, stuck outbox messages, failed inbox records, and
kernel boundary findings.

AION v0.1 command and outbox processing is manual. No background processor
starts automatically.

## Module Developer Kit

AION Brain includes a generic Module Developer Kit and Capability Certification
Harness. Module packages must prove their contracts before runtime
registration. Certification validates schemas, risk, permissions, memory scope,
policy, autonomy, dry-run behavior, and audit metadata without executing module
code.

The repository includes a generic contract-only example in
`examples/generic-module`.

Command and consistency endpoints:

- `POST /brain/commands`
- `GET /brain/commands/{command_id}`
- `GET /brain/commands`
- `POST /brain/commands/{command_id}/cancel`
- `GET /brain/idempotency/{idempotency_key}`
- `POST /brain/idempotency/expire-old`
- `POST /brain/outbox`
- `GET /brain/outbox/{outbox_id}`
- `GET /brain/outbox`
- `POST /brain/outbox/process-once`
- `POST /brain/outbox/{outbox_id}/cancel`
- `POST /brain/inbox/receive`
- `GET /brain/inbox`
- `POST /brain/inbox/{inbox_id}/processed`
- `POST /brain/inbox/{inbox_id}/failed`
- `POST /brain/consistency/check`
- `POST /brain/leases/acquire`
- `POST /brain/leases/{lease_id}/release`

## API Contract Hardening

AION Brain v0.1 includes a generic API hardening layer for SDK-ready public
contracts. It adds request context middleware, standard error responses,
pagination and filtering helpers, safe request audit records, and OpenAPI
hygiene checks. AION v0.1 public API errors use `AIONErrorResponse`. Success
responses remain backward-compatible where earlier contracts already exist.

Standard request/response headers:

- `X-AION-Request-ID`
- `X-AION-Trace-ID`
- `X-AION-Correlation-ID`
- `X-AION-Idempotency-Key`
- `X-AION-Version`

Request audit records store method, path, route, status, duration, safe client
host/user-agent metadata, trace ID, correlation ID, and idempotency key. They
do not store request bodies or raw headers.

API hardening endpoints:

- `GET /brain/api/requests/{request_id}`
- `GET /brain/api/requests`
- `GET /brain/api/openapi-hygiene`
- `GET /brain/api/error-codes`

## Codex Working Rules

- Build only AION Brain Core until the architecture explicitly expands.
- Keep the Brain domain-neutral.
- Use adapter boundaries for every external system.
- Do not hard-code a model provider.
- Do not expose framework-specific objects through public AION APIs.
- Add tests for every new behavior.
- Update docs when architecture changes.

## Sandbox, Secrets, and Connectors

AION v0.1 defines sandbox, secret reference, and connector boundaries. It does
not execute containers, run untrusted code, store raw secrets, or connect to
external systems.

The Sandbox Control Plane owns sandbox profiles, resource limits, egress rules,
filesystem rules, runtime permission grants, validation records, and sandbox
run records. Sandbox runs are dry-run validation by default. Controlled
execution returns `unsupported` while `AION_SANDBOX_EXECUTION_ENABLED=false`.
Docker and Firecracker adapters are placeholders only.

The Secret Reference Vault stores metadata-only `SecretRef` records. Secret
material must live outside AION Brain and is referenced through `external_ref`.
The Connector Registry stores connector metadata only. Connector validation
checks local metadata and secret references without making network calls.

AION-106 adds the external connector boundary design before any connector
runtime exists. Connectors are untrusted by default, external calls remain
disabled, credentials and tokens remain absent, and future connector work must
pass connector boundary and no-go regression gates.

Sandbox endpoints:

- `POST /brain/sandbox/profiles`
- `GET /brain/sandbox/profiles/{sandbox_profile_id}`
- `GET /brain/sandbox/profiles`
- `POST /brain/sandbox/profiles/{sandbox_profile_id}/disable`
- `POST /brain/sandbox/profiles/{sandbox_profile_id}/validate`
- `POST /brain/sandbox/run`
- `POST /brain/sandbox/runtime-permissions`
- `GET /brain/sandbox/runtime-permissions`
- `POST /brain/sandbox/runtime-permissions/{runtime_permission_id}/revoke`

Secret reference endpoints:

- `POST /brain/secret-refs`
- `GET /brain/secret-refs/{secret_ref_id}`
- `GET /brain/secret-refs`
- `POST /brain/secret-refs/{secret_ref_id}/disable`
- `POST /brain/secret-refs/{secret_ref_id}/rotate-metadata`

Connector endpoints:

- `POST /brain/connectors`
- `GET /brain/connectors/{connector_id}`
- `GET /brain/connectors`
- `POST /brain/connectors/{connector_id}/disable`
- `POST /brain/connectors/{connector_id}/validate`

## Policy Catalog and Permission Matrix

AION v0.1 includes a generic policy governance catalog for Brain actions,
permissions, role templates, simulations, test cases, coverage, bundle export,
and OPA status checks. It is Brain-only and domain-neutral.

Policy catalog endpoints:

- `POST /brain/policy-catalog/actions`
- `GET /brain/policy-catalog/actions`
- `GET /brain/policy-catalog/actions/{action_type}`
- `POST /brain/policy-catalog/actions/{action_type}/disable`
- `POST /brain/policy-catalog/seed-defaults`
- `POST /brain/policy-catalog/permissions`
- `GET /brain/policy-catalog/permissions`
- `POST /brain/policy-catalog/roles`
- `GET /brain/policy-catalog/roles`
- `POST /brain/policy-catalog/roles/seed-defaults`
- `POST /brain/policy/simulate`
- `POST /brain/policy/tests`
- `GET /brain/policy/tests`
- `POST /brain/policy/tests/run`
- `GET /brain/policy/coverage`
- `POST /brain/policy/bundles/export`
- `GET /brain/policy/bundles/{policy_bundle_id}`
- `GET /brain/policy/bundles`
- `GET /brain/policy/opa/status`

`aionctl policy` exposes matching developer commands for actions,
permissions, roles, seeding defaults, simulations, test runs, coverage, bundle
export, and OPA status.

Policy simulations are side-effect-free and never execute the target action.
Policy tests do not require live OPA by default. Policy bundles are
deterministically hashed and must not contain raw secrets.

## Repository Quality And Release Control

AION v0.1 includes local and CI quality gates for maintainability:

- `scripts/check.sh`
- `scripts/test-all.sh`
- `scripts/lint.sh`
- `scripts/typecheck.sh`
- `scripts/docker-build.sh`
- `scripts/migration-check.sh`
- `scripts/verify-no-domain-drift.sh`
- `scripts/boundary-check.sh`
- `scripts/openapi-hygiene.sh`
- `scripts/policy-coverage.sh`
- `scripts/release-candidate-check.sh`

The root `Makefile` calls these scripts and keeps command details in one
place. GitHub Actions mirror the same gates for Brain API, SDK, contracts,
policy, repository hygiene, and Docker build checks.

Operations docs live under `docs/operations/`. The ADR index lives at
`docs/adr/README.md`. v0.1 does not add cloud deployment, production auth, or
new vertical modules.

## End-to-End Scenario Harness

AION v0.1 includes a deterministic scenario harness for release readiness.
Scenarios validate the complete Brain through generic, side-effect-safe steps:
event intake, attention, memory, evidence, retrieval, context, reasoning,
planning, policy, risk, approvals, command bus, workflow dry-run, cycle
dry-run, module certification, sandbox validation, visual projection, replay,
regression, kernel self-test, API contracts, SDK, and CLI access.

Demo fixtures provide safe generic event, evidence, memory, module package, and
sandbox profile records. Release baselines combine selected scenario runs with
quality gate summaries into one persisted readiness report.

Scenario endpoints:

- `POST /brain/scenarios`
- `GET /brain/scenarios`
- `GET /brain/scenarios/{scenario_id}`
- `POST /brain/scenarios/{scenario_id}/disable`
- `POST /brain/scenarios/run`
- `GET /brain/scenarios/runs/{scenario_run_id}`
- `GET /brain/scenarios/runs`
- `POST /brain/scenarios/seed-defaults`
- `GET /brain/demo-fixtures`
- `POST /brain/demo-fixtures/load`
- `POST /brain/release-baseline/run`
- `GET /brain/release-baseline/{release_baseline_id}`
- `GET /brain/release-baseline`

CLI examples:

```bash
aionctl scenarios seed-defaults
aionctl scenarios run --scenario-id golden_path_brain
aionctl release-baseline run --version 0.1.0
```

AION v0.1 scenarios are generic, deterministic, and dry-run by default. They do
not exercise domain modules or external services.

## Versioning And Freeze Gate

AION v0.1 includes a local release versioning layer. It records version
manifests, generic feature registry entries, compatibility matrices, migration
baselines, release artifact manifests, SDK compatibility reports, and freeze
gate runs.

Versioning endpoints:

- `POST /brain/versioning/manifests`
- `GET /brain/versioning/manifests/{version}`
- `GET /brain/versioning/manifests`
- `POST /brain/versioning/manifests/{version}/freeze`
- `POST /brain/versioning/features/seed-defaults`
- `GET /brain/versioning/features`
- `POST /brain/versioning/features`
- `POST /brain/versioning/features/{feature_key}/deprecate`
- `POST /brain/versioning/compatibility/generate`
- `GET /brain/versioning/compatibility/{version}`
- `POST /brain/versioning/migration-baseline/generate`
- `POST /brain/versioning/release-artifacts/generate`
- `GET /brain/versioning/sdk-compatibility`
- `POST /brain/freeze-gate/run`
- `GET /brain/freeze-gate/{freeze_gate_id}`
- `GET /brain/freeze-gate`

CLI examples:

```bash
./scripts/aionctl.sh --scope workspace:main versioning manifests create --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning features seed-defaults
./scripts/aionctl.sh --scope workspace:main versioning compatibility generate --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning migration-baseline --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning release-artifacts --version 0.1.0
./scripts/aionctl.sh --scope workspace:main versioning sdk-compatibility
./scripts/aionctl.sh --scope workspace:main freeze run --version 0.1.0
```

The freeze gate is deterministic and local. It does not call shell scripts,
package artifacts, upload files, call external observability services, require
optional adapters, enable full autonomy, or execute domain modules.

## Local Release Packaging

AION v0.1 includes a local release packager for final handoff. It creates a
deterministic local package record, source manifest, generated report artifacts,
checksums, SBOM placeholder, and handoff report. The packager does not upload
files, call external package registries, call cloud services, execute Docker,
or run shell commands from the API path.

Release package endpoints:

- `POST /brain/release-package/create`
- `GET /brain/release-package/{release_package_id}`
- `GET /brain/release-package`
- `POST /brain/release-package/{release_package_id}/validate`
- `GET /brain/release-package/{release_package_id}/handoff`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main release package --version 0.1.0 --dry-run
./scripts/aionctl.sh --scope workspace:main release package --version 0.1.0 --write
./scripts/aionctl.sh --scope workspace:main release package validate --id <release_package_id>
./scripts/aionctl.sh --scope workspace:main release package handoff --id <release_package_id>
./scripts/package-release.sh
./scripts/verify-release-package.sh
```

Generated package outputs live under `artifacts/releases/` by default and are
ignored by git. The SBOM is a local metadata placeholder only; it reads local
project metadata and does not resolve transitive dependencies or query package
registries.

See `docs/operations/release-packaging.md` and
`docs/operations/final-handoff.md`.

## Local Backup and Restore Preview

AION v0.1 includes a local, application-level backup and restore-preview layer.
It exports Brain contracts as deterministic JSON and JSONL files, records a
manifest, computes checksums, and persists backup job metadata. It does not use
`pg_dump`, direct database restore, cloud upload, or external storage services.

AION v0.1 backup is local and application-level. Restore apply is disabled by default.

Backup concepts:

- `BackupManifest`: portable summary, resource list, redaction mode, counts,
  compatibility metadata, and root checksum.
- `BackupFile`: one exported JSONL resource file and checksum.
- `RestorePreview`: conflict-aware dry-run restore plan.
- `RestoreJob`: dry-run or guarded apply record; v0.1 writes no restored data
  unless a future task explicitly enables application writers.

Backup endpoints:

- `POST /brain/backups/export`
- `GET /brain/backups/{backup_job_id}`
- `GET /brain/backups`
- `POST /brain/backups/{backup_job_id}/validate`
- `POST /brain/backups/validate-path`
- `POST /brain/restore/preview`
- `GET /brain/restore/previews/{restore_preview_id}`
- `POST /brain/restore/apply`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main backups export
./scripts/aionctl.sh --scope workspace:main backups export --write
./scripts/aionctl.sh --scope workspace:main backups validate --id <backup_job_id>
./scripts/aionctl.sh --scope workspace:main restore preview --backup-path artifacts/backups/<backup_id>
./scripts/aionctl.sh --scope workspace:main restore apply --preview-id <restore_preview_id>
./scripts/backup-local.sh
./scripts/restore-preview.sh artifacts/backups/<backup_id>
```

Generated backup outputs live under `artifacts/backups/` by default and are
ignored by git. See `docs/operations/local-backup-restore.md`.

## Performance Benchmarks and Capacity Baselines

AION v0.1 includes a local benchmark harness, performance sample records,
capacity baselines, resource budget profiles, and regression comparison.

AION v0.1 benchmarks are local, deterministic, and side-effect-safe. They do not perform cloud load testing or call external providers.

Performance concepts:

- `PerformanceSample`: one timing record for a generic Brain operation.
- `BenchmarkDefinition`: deterministic local benchmark steps and thresholds.
- `BenchmarkRun`: executed benchmark report with samples and summary.
- `CapacityBaseline`: p50/p95/p99/max metrics built from benchmark runs.
- `ResourceBudgetProfile`: report-only generic resource thresholds.
- `PerformanceRegressionReport`: comparison against a capacity baseline.

Performance endpoints:

- `POST /brain/performance/benchmarks`
- `GET /brain/performance/benchmarks`
- `GET /brain/performance/benchmarks/{benchmark_id}`
- `POST /brain/performance/benchmarks/seed-defaults`
- `POST /brain/performance/benchmarks/run`
- `GET /brain/performance/benchmarks/runs/{benchmark_run_id}`
- `GET /brain/performance/benchmarks/runs`
- `POST /brain/performance/baselines/from-runs`
- `GET /brain/performance/baselines/{capacity_baseline_id}`
- `GET /brain/performance/baselines`
- `POST /brain/performance/regression/compare`
- `POST /brain/performance/budgets`
- `GET /brain/performance/budgets`
- `GET /brain/performance/summary`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main performance benchmarks seed-defaults
./scripts/aionctl.sh --scope workspace:main performance run
./scripts/aionctl.sh --scope workspace:main performance baselines create --run-id <benchmark_run_id>
./scripts/aionctl.sh --scope workspace:main performance summary
./scripts/benchmark-local.sh
./scripts/capacity-baseline.sh
```

See `docs/operations/performance-benchmarking.md`.

## Resilience Control Plane

AION v0.1 includes a local resilience control plane for dependency health,
bounded retry policies, circuit breakers, degraded mode, fault injection rules,
and deterministic resilience test runs.

AION v0.1 resilience checks are local and deterministic. Fault injection is
disabled by default and does not start background workers.

Resilience concepts:

- `DependencyHealth`: bounded local dependency check result.
- `RetryPolicy`: bounded retry metadata with max attempts and backoff.
- `CircuitBreaker`: closed, open, half-open, or disabled call gate state.
- `DegradedModeEvent`: explicit fallback posture and constraints.
- `FaultInjectionRule`: local deterministic rule, inert unless enabled.
- `ResilienceTestRun`: combined local resilience readiness report.

Resilience endpoints:

- `GET /brain/resilience/status`
- `POST /brain/resilience/dependencies/check`
- `GET /brain/resilience/dependencies`
- `POST /brain/resilience/retry-policies`
- `GET /brain/resilience/retry-policies`
- `POST /brain/resilience/retry-policies/seed-defaults`
- `POST /brain/resilience/circuit-breakers`
- `GET /brain/resilience/circuit-breakers`
- `POST /brain/resilience/circuit-breakers/{name}/reset`
- `GET /brain/resilience/degraded`
- `POST /brain/resilience/degraded/{degraded_event_id}/resolve`
- `POST /brain/resilience/fault-rules`
- `GET /brain/resilience/fault-rules`
- `POST /brain/resilience/fault-rules/{fault_rule_id}/disable`
- `POST /brain/resilience/test/run`
- `GET /brain/resilience/test-runs/{resilience_test_run_id}`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main resilience status
./scripts/aionctl.sh --scope workspace:main resilience dependencies check
./scripts/aionctl.sh --scope workspace:main resilience retry-policies seed
./scripts/aionctl.sh --scope workspace:main resilience test run
./scripts/resilience-check.sh
./scripts/fault-injection-dry-run.sh
```

See `docs/operations/resilience.md`.

## Audit Integrity and Provenance

AION v0.1 includes a local tamper-evident audit ledger and provenance chain.
Audit entries are append-only, redacted before hashing, linked by sha256 hashes,
and checkpointed locally. Provenance links connect generic Brain records such as
events, commands, policy decisions, approvals, model calls, backups, and release
packages.

AION v0.1 audit integrity is local and tamper-evident. It does not provide
external notarization or compliance certification.

Audit endpoints:

- `POST /brain/audit/entries`
- `GET /brain/audit/entries/{audit_entry_id}`
- `GET /brain/audit/entries/by-sequence/{sequence_number}`
- `GET /brain/audit/entries`
- `GET /brain/audit/status`
- `POST /brain/audit/checkpoints`
- `GET /brain/audit/checkpoints`
- `POST /brain/audit/verify`
- `GET /brain/audit/verify/{audit_verification_id}`
- `POST /brain/audit/export`
- `POST /brain/provenance/links`
- `GET /brain/provenance/links`
- `GET /brain/provenance/traces/{trace_id}`
- `DELETE /brain/provenance/links/{provenance_link_id}`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main audit status
./scripts/aionctl.sh --scope workspace:main audit verify
./scripts/aionctl.sh --scope workspace:main provenance trace --trace-id <trace_id>
./scripts/audit-verify.sh
./scripts/audit-export.sh
```

See `docs/operations/audit-integrity.md`.

## Operator Control Tower

AION v0.1 includes an Operator Control Tower backend API. It aggregates local
Brain state into status cards, queue summaries, action-center recommendations,
readiness reports, snapshots, acknowledgements, and runbook links.

The Action Center recommends generic next steps only. It does not execute,
approve, cancel, retry, remediate, mutate memory, process queues, invoke
capabilities, or change runtime configuration.

Operator endpoints:

- `POST /brain/operator/overview`
- `GET /brain/operator/status-cards`
- `GET /brain/operator/queues`
- `GET /brain/operator/actions`
- `POST /brain/operator/actions/acknowledge`
- `GET /brain/operator/acknowledgements`
- `GET /brain/operator/readiness`
- `POST /brain/operator/snapshots`
- `GET /brain/operator/snapshots/{operator_snapshot_id}`
- `GET /brain/operator/snapshots`
- `GET /brain/operator/runbooks`

CLI and local scripts:

```bash
./scripts/aionctl.sh --scope workspace:main operator overview
./scripts/aionctl.sh --scope workspace:main operator readiness
./scripts/aionctl.sh --scope workspace:main operator actions
./scripts/operator-overview.sh
./scripts/operator-readiness.sh
```

AION v0.1 Operator Control Tower is a backend API only. It does not implement a
frontend or automatic remediation.

See `docs/operations/operator-control-tower.md`.

## Concept Registry and Entity Resolver

AION v0.1 includes a generic Concept Registry, Entity Registry, deterministic
Mention Extractor, Entity Resolver, Canonical Reference Link layer, and
merge/split proposal workflow.

The Concept Registry owns abstract Brain concepts. The Entity Registry owns
canonical references, aliases, mentions, unresolved references, merged
references, and reference links. Entity references can connect evidence,
memory, beliefs, graph records, dialogue, responses, traces, audit entries, and
provenance links.

AION v0.1 entity resolution is deterministic and generic. Entity references
are canonical pointers, not verified truth.

Concept endpoints:

- `POST /brain/concepts`
- `GET /brain/concepts/{concept_id}`
- `GET /brain/concepts`
- `POST /brain/concepts/{concept_id}/archive`

Entity endpoints:

- `POST /brain/entities`
- `GET /brain/entities/{entity_id}`
- `POST /brain/entities/query`
- `POST /brain/entities/{entity_id}/archive`
- `DELETE /brain/entities/{entity_id}`
- `POST /brain/entities/aliases`
- `GET /brain/entities/{entity_id}/aliases`
- `POST /brain/entities/mentions`
- `GET /brain/entities/{entity_id}/mentions`
- `POST /brain/entities/extract-mentions`
- `POST /brain/entities/resolve`
- `GET /brain/entities/resolution-runs/{resolution_run_id}`
- `POST /brain/entities/references`
- `GET /brain/entities/references`
- `POST /brain/entities/merge-proposals`
- `GET /brain/entities/merge-proposals`
- `POST /brain/entities/merge-proposals/{merge_proposal_id}/approve`
- `POST /brain/entities/merge-proposals/{merge_proposal_id}/reject`
- `POST /brain/entities/split-proposals`
- `GET /brain/entities/split-proposals`
- `POST /brain/entities/split-proposals/{split_proposal_id}/approve`
- `POST /brain/entities/split-proposals/{split_proposal_id}/reject`

CLI examples:

```bash
./scripts/aionctl.sh entities query --query "AION"
./scripts/aionctl.sh entities resolve --text "AION Brain uses memory governance"
```

The resolver does not call external NLP services, model providers, image
identification systems, or domain modules. It does not infer sensitive identity
attributes, auto-merge entities, or hard-delete canonical records.

See `docs/adr/0047-concept-registry-entity-resolver.md`.

## Situation Model and Temporal State

AION v0.1 includes a backend Situation Model that projects generic current
Brain state into situations, state atoms, transitions, temporal windows, and
context continuity records.

Situation projection is deterministic and local. It does not call LLMs, mutate
source records, execute actions, or introduce domain-specific world models.
State atoms are recall, not truth.

Situation endpoints:

- `POST /brain/situations`
- `GET /brain/situations/{situation_id}`
- `POST /brain/situations/query`
- `POST /brain/situations/{situation_id}/close`
- `POST /brain/situations/state-atoms`
- `GET /brain/situations/state-atoms/{state_atom_id}`
- `GET /brain/situations/state-atoms`
- `POST /brain/situations/project`
- `GET /brain/situations/projection-runs/{projection_run_id}`
- `GET /brain/situations/transitions`
- `POST /brain/situations/temporal-windows`
- `GET /brain/situations/temporal-windows/{temporal_window_id}`
- `GET /brain/situations/temporal-windows`
- `POST /brain/situations/continuity`
- `GET /brain/situations/continuity`

CLI examples:

```bash
./scripts/aionctl.sh --scope workspace:main situations query
./scripts/aionctl.sh --scope workspace:main situations project
./scripts/aionctl.sh --scope workspace:main situations atoms
```

See `docs/situation-model.md` and
`docs/adr/0048-situation-model-temporal-state.md`.
## Decision Intelligence

AION Brain v0.1 includes a Decision Frame Manager, Option Evaluator,
Counterfactual Simulator, and Decision Journal. Decisions recommend but do not
execute. Execution remains gated by policy, risk, approval, autonomy, and
explicit execution APIs.

Decision endpoints:

- `POST /brain/decisions/frames`
- `GET /brain/decisions/frames/{decision_frame_id}`
- `GET /brain/decisions/frames`
- `POST /brain/decisions/frames/{decision_frame_id}/close`
- `POST /brain/decisions/options`
- `GET /brain/decisions/frames/{decision_frame_id}/options`
- `POST /brain/decisions/options/{decision_option_id}/archive`
- `POST /brain/decisions/utility-profiles`
- `GET /brain/decisions/utility-profiles`
- `POST /brain/decisions/utility-profiles/seed-defaults`
- `POST /brain/decisions/evaluate`
- `POST /brain/decisions/recommend/{decision_frame_id}`
- `POST /brain/decisions/counterfactuals/run`
- `GET /brain/decisions/counterfactuals/{counterfactual_run_id}`
- `POST /brain/decisions/journal`
- `GET /brain/decisions/journal/{decision_record_id}`
- `GET /brain/decisions/journal`
- `POST /brain/decisions/journal/{decision_record_id}/supersede`

CLI examples:

```bash
aionctl decisions frame create --title "Choose next step" --question "What should happen next?"
aionctl decisions evaluate --frame-id decision-frame-1
aionctl decisions counterfactual run --frame-id decision-frame-1
```

## Outcome Ledger and Effect Verification

AION Brain v0.1 includes an Outcome Ledger for generic expected effects,
observed effects, outcome records, verification runs, causal attributions, and
outcome feedback.

Outcome verification is deterministic and local. Completion is not treated as
verification, and verification does not mutate source command, workflow,
decision, plan, memory, evidence, belief, or situation records.

Outcome endpoints:

- `POST /brain/outcomes`
- `GET /brain/outcomes/{outcome_id}`
- `POST /brain/outcomes/query`
- `POST /brain/outcomes/{outcome_id}/close`
- `DELETE /brain/outcomes/{outcome_id}`
- `POST /brain/outcomes/expected-effects`
- `GET /brain/outcomes/expected-effects/{expected_effect_id}`
- `POST /brain/outcomes/observed-effects`
- `GET /brain/outcomes/observed-effects/{observed_effect_id}`
- `POST /brain/outcomes/verify`
- `GET /brain/outcomes/verifications/{verification_run_id}`
- `POST /brain/outcomes/attributions`
- `GET /brain/outcomes/attributions`
- `POST /brain/outcomes/feedback`
- `GET /brain/outcomes/feedback`
- `POST /brain/outcomes/feedback/{feedback_id}/resolve`
- `POST /brain/outcomes/learning-bridge`

CLI examples:

```bash
./scripts/aionctl.sh outcomes query --source-type command
./scripts/aionctl.sh outcomes verify --source-type command --source-id command-id
./scripts/aionctl.sh outcomes feedback list
./scripts/aionctl.sh outcomes learning-bridge --outcome-id outcome-id --dry-run
```

The learning bridge creates reviewable feedback only. It does not promote
skills, auto-remediate failures, call model providers, call external systems,
or add domain-specific logic.

See `docs/adr/0050-outcome-ledger-effect-verification.md`.

## Experience Ledger and Learning Synthesis

AION Brain v0.1 now includes a generic Experience Ledger and deterministic
Learning Synthesizer. Outcomes, feedback, commands, workflows, approvals,
replays, regressions, audit records, and manual observations can be normalized
into `ExperienceRecord` entries. Pattern mining groups repeated generic
experience shapes, lesson synthesis records reviewable lessons, and suggestion
services create passive skill and regression candidates.

Learning synthesis is review-only. It does not promote skills, create active
skills, create regression cases, modify source code, retry failed work, call
model providers, call external services, or mutate source records.

Learning endpoints:

- `POST /brain/learning/experiences`
- `GET /brain/learning/experiences/{experience_id}`
- `POST /brain/learning/query`
- `POST /brain/learning/experiences/{experience_id}/archive`
- `POST /brain/learning/patterns/mine`
- `GET /brain/learning/patterns`
- `GET /brain/learning/lessons`
- `POST /brain/learning/synthesize`
- `GET /brain/learning/synthesis/{synthesis_run_id}`
- `GET /brain/learning/skill-suggestions`
- `POST /brain/learning/skill-suggestions/{suggestion_id}/accept`
- `POST /brain/learning/skill-suggestions/{suggestion_id}/reject`
- `POST /brain/learning/skill-suggestions/{suggestion_id}/convert-to-candidate`
- `GET /brain/learning/regression-suggestions`
- `POST /brain/learning/regression-suggestions/{suggestion_id}/accept`
- `POST /brain/learning/regression-suggestions/{suggestion_id}/reject`

CLI examples:

```bash
./scripts/aionctl.sh learning experiences create --source-type generic --source-id source-id --title "Observed outcome" --summary "Generic experience"
./scripts/aionctl.sh learning patterns mine --dry-run
./scripts/aionctl.sh learning synthesize --experience-id experience-id --mode dry_run
./scripts/aionctl.sh learning skill-suggestions list --status suggested
```

See `docs/adr/0051-experience-ledger-learning-synthesis.md`.

## Self Model and Capability Awareness

AION means Adaptive Intelligence Orchestration Nexus. AION OS means Adaptive
Intelligence Orchestration Nexus Operating System.

AION Brain v0.1 includes a descriptive Self Model, Capability Awareness
inventory, Limitation Ledger, deterministic Confidence Calibration,
Self-Assessment records, and Introspection Snapshots. This layer tells
operators and clients what AION is, what is active, what is disabled or
optional, which limitations need disclosure, and when responses should expose
uncertainty.

AION v0.1 self model is descriptive and diagnostic. It does not claim
sentience, production readiness, or full autonomy.

Self-model endpoints:

- `GET /brain/self`
- `POST /brain/self/describe`
- `GET /brain/self/capabilities`
- `POST /brain/self/capabilities/refresh`
- `POST /brain/self/limitations`
- `GET /brain/self/limitations`
- `POST /brain/self/limitations/seed-defaults`
- `POST /brain/self/limitations/{limitation_id}/resolve`
- `POST /brain/self/confidence/calibrate`
- `GET /brain/self/confidence`
- `POST /brain/self/assessment/run`
- `GET /brain/self/assessment/{self_assessment_id}`
- `POST /brain/self/introspection`
- `GET /brain/self/introspection/{introspection_snapshot_id}`
- `GET /brain/self/introspection`

CLI examples:

```bash
./scripts/aionctl.sh self describe
./scripts/aionctl.sh self capabilities
./scripts/aionctl.sh self assessment run
```

See `docs/adr/0052-self-model-capability-awareness.md`.

## Explanation Engine and Trace Narratives

AION Brain v0.1 includes a deterministic Explanation Engine for public,
grounded "why" and "why-not" answers. It builds explanation records from
observable AION contracts only: policy decisions, approvals, audit records,
provenance links, memory/evidence refs, response records, outcome records,
capability awareness, and local diagnostics.

Explanations are not chain-of-thought. They are public narratives over
recorded system state. The engine redacts secret-like keys, raw prompt markers,
and hidden reasoning markers before persistence or API return.

Explanation endpoints:

- `POST /brain/explanations`
- `GET /brain/explanations/{explanation_id}`
- `GET /brain/explanations`
- `POST /brain/explanations/{explanation_id}/verify`
- `POST /brain/explanations/why-not`
- `GET /brain/explanations/why-not/{why_not_id}`
- `POST /brain/traces/{trace_id}/narrative`
- `GET /brain/traces/narratives/{trace_narrative_id}`
- `GET /brain/traces/{trace_id}/narratives`
- `POST /brain/explanations/feedback`
- `GET /brain/explanations/feedback`

SDK and CLI examples:

```bash
./scripts/aionctl.sh explain target --target-type trace --target-id trace-id
./scripts/aionctl.sh explain why-not --target-type trace --trace-id trace-id
./scripts/aionctl.sh explain trace --trace-id trace-id
./scripts/aionctl.sh explain verify --explanation-id explanation-id
```

`client.explanations` exposes the same public Brain APIs. The SDK does not
import Brain internals, database clients, frontend code, provider SDKs, or
external observability clients.

See `docs/adr/0053-explanation-engine-trace-narratives.md`.

## Instruction Hierarchy and Preference Ledger

AION Brain v0.1 includes a generic Instruction Hierarchy, Preference Ledger,
Constraint Resolver, Style Profile Manager, and Instruction Conflict Detector.
AION v0.1 preferences shape responses and context. They do not override
policy, autonomy, approvals, runtime config, or capability limits.

Instruction and preference endpoints:

- `POST /brain/instructions`
- `GET /brain/instructions/{instruction_id}`
- `GET /brain/instructions`
- `POST /brain/instructions/{instruction_id}/disable`
- `POST /brain/instructions/resolve`
- `GET /brain/instructions/conflicts`
- `POST /brain/instructions/conflicts/{conflict_id}/resolve`
- `POST /brain/preferences`
- `GET /brain/preferences`
- `POST /brain/preferences/{preference_id}/confirm`
- `POST /brain/preferences/{preference_id}/reject`
- `POST /brain/preferences/{preference_id}/disable`
- `POST /brain/preferences/candidates`
- `GET /brain/preferences/candidates`
- `POST /brain/preferences/candidates/{candidate_id}/confirm`
- `POST /brain/preferences/candidates/{candidate_id}/reject`
- `POST /brain/style-profiles`
- `GET /brain/style-profiles`
- `GET /brain/style-profiles/effective`
- `POST /brain/style-profiles/{style_profile_id}/disable`

CLI examples:

```bash
./scripts/aionctl.sh instructions create --text "Keep responses concise."
./scripts/aionctl.sh instructions resolve
./scripts/aionctl.sh preferences confirm --id preference-id --reason explicit
./scripts/aionctl.sh style-profiles effective
```

See `docs/instruction-hierarchy.md` and
`docs/adr/0054-instruction-hierarchy-preference-ledger.md`.

## Grounding Manager and Source Attribution

AION v0.1 grounding is deterministic. It does not invent citations, call web
search, or treat memory recall as truth. The Grounding Manager maps public
response and explanation statements to local source records, citations,
unsupported statements, verification runs, and source coverage reports.

Grounding endpoints:

- `POST /brain/grounding/sources`
- `GET /brain/grounding/sources/{grounding_source_id}`
- `POST /brain/grounding/citations`
- `GET /brain/grounding/citations`
- `POST /brain/grounding/map-response/{response_id}`
- `POST /brain/grounding/map-text`
- `POST /brain/grounding/verify`
- `GET /brain/grounding/verifications/{grounding_verification_id}`
- `POST /brain/grounding/coverage`
- `POST /brain/grounding/query`
- `GET /brain/grounding/unsupported`

CLI examples:

```bash
./scripts/aionctl.sh grounding verify --response-id response-id
./scripts/aionctl.sh grounding unsupported --response-id response-id
```

See `docs/grounding-model.md` and
`docs/adr/0055-grounding-citation-source-attribution.md`.

## Prompt Packet and Model Input Governance

AION Brain v0.1 includes a provider-neutral Prompt Packet Compiler, Prompt
Boundary Guard, deterministic Prompt Injection Detector, safe Prompt Preview,
and Model Input Manifest service. This layer prepares governed model input for
the Model Gateway only. It does not call external model providers, optimize
prompts with an LLM, execute tools, approve actions, or create truth.

Prompt endpoints:

- `POST /brain/prompts/templates`
- `GET /brain/prompts/templates`
- `GET /brain/prompts/templates/{prompt_template_id}`
- `POST /brain/prompts/templates/{prompt_template_id}/disable`
- `POST /brain/prompts/templates/seed-defaults`
- `POST /brain/prompts/fragments`
- `GET /brain/prompts/fragments`
- `POST /brain/prompts/compile`
- `GET /brain/prompts/packets/{prompt_packet_id}`
- `GET /brain/prompts/packets`
- `POST /brain/prompts/preview`
- `POST /brain/prompts/boundary-check`
- `GET /brain/prompts/injection-findings`
- `GET /brain/prompts/model-input-manifests/{model_input_manifest_id}`
- `GET /brain/prompts/model-input-manifests`

CLI examples:

```bash
./scripts/aionctl.sh prompts compile --user-message "Answer generically."
./scripts/aionctl.sh prompts preview --prompt-packet-id prompt-packet-id
./scripts/aionctl.sh prompts injection-findings
```

AION v0.1 prompt packets are provider-neutral and governed. Raw rendered
prompts are not persisted by default.

See `docs/prompt-governance.md` and
`docs/adr/0056-prompt-packet-model-input-governance.md`.

### Model Output Governance

AION v0.1 receives model outputs through a provider-neutral governance layer.
The Brain stores raw output hashes and redacted output records, parses generic
segments, validates structured JSON, creates local response candidates, and
captures model-suggested tool intents for review. Raw model outputs are not
stored by default, and tool intents are blocked by default.

Model output endpoints:

- `POST /brain/model-outputs`
- `GET /brain/model-outputs/{model_output_id}`
- `POST /brain/model-outputs/query`
- `DELETE /brain/model-outputs/{model_output_id}`
- `POST /brain/model-outputs/{model_output_id}/govern`
- `GET /brain/model-outputs/governance/{output_governance_id}`
- `GET /brain/model-outputs/{model_output_id}/segments`
- `POST /brain/model-outputs/{model_output_id}/validate-structured`
- `GET /brain/model-outputs/response-candidates`
- `POST /brain/model-outputs/response-candidates/{response_candidate_id}/promote`
- `GET /brain/model-outputs/tool-intents`
- `POST /brain/model-outputs/tool-intents/{tool_intent_id}/reject`

```bash
./scripts/aionctl.sh model-outputs create --raw-output "Generic answer"
./scripts/aionctl.sh model-outputs query
./scripts/aionctl.sh model-outputs candidates list
./scripts/aionctl.sh model-outputs tool-intents list
```

See `docs/model-output-governance.md` and
`docs/adr/0057-model-output-governance.md`.

## Action Proposal Broker and Execution Handoff Gate

AION v0.1 action proposals do not execute themselves. Model-generated tool
intents are captured, reviewed, and blocked by default.

The Action Proposal Broker turns reviewed generic intent into
`ActionProposal` records. Tool Intent Review handles captured model tool
intent candidates without executing them. The Execution Handoff Gate builds an
explicit handoff record to governed AION target systems and defaults to dry-run.
Controlled handoff is disabled by default.

Action proposal endpoints:

- `POST /brain/action-proposals`
- `GET /brain/action-proposals/{action_proposal_id}`
- `POST /brain/action-proposals/query`
- `POST /brain/action-proposals/{action_proposal_id}/archive`
- `DELETE /brain/action-proposals/{action_proposal_id}`
- `POST /brain/action-proposals/tool-intents/{tool_intent_id}/review`
- `GET /brain/action-proposals/tool-intent-reviews`
- `POST /brain/action-proposals/{action_proposal_id}/review`
- `GET /brain/action-proposals/{action_proposal_id}/reviews`
- `GET /brain/action-proposals/blockers`
- `POST /brain/action-proposals/blockers/{action_blocker_id}/resolve`
- `POST /brain/action-proposals/handoff`
- `GET /brain/action-proposals/handoffs/{execution_handoff_id}`
- `GET /brain/action-proposals/handoffs`

CLI examples:

```bash
./scripts/aionctl.sh action-proposals query
./scripts/aionctl.sh action-proposals review --action-proposal-id action-proposal-id
./scripts/aionctl.sh action-proposals handoff --action-proposal-id action-proposal-id --mode dry_run
```

See `docs/adr/0058-action-proposal-broker-execution-handoff.md`.

## Run Supervision, Control, Timeout, and Compensation

AION v0.1 run supervision observes and requests. It does not auto-cancel,
auto-remediate, or execute compensation.

Run Supervision registers target-neutral records for governed runs and samples
their status through local target adapters. Cancellation and control requests
are manual records and default to dry-run. Timeout policies detect stale,
stalled, or timed-out runs without forcing cancellation. The Compensation
Planner creates proposed recovery plans only; plans and steps never execute
themselves.

Run supervision endpoints:

- `POST /brain/run-supervision/runs`
- `GET /brain/run-supervision/runs/{run_supervision_id}`
- `GET /brain/run-supervision/runs`
- `POST /brain/run-supervision/runs/{run_supervision_id}/sample`
- `POST /brain/run-supervision/sample-many`
- `POST /brain/run-supervision/runs/{run_supervision_id}/archive`
- `POST /brain/run-supervision/control-requests`
- `GET /brain/run-supervision/control-requests`
- `POST /brain/run-supervision/control-requests/{run_control_request_id}/handoff`
- `POST /brain/run-supervision/timeout-policies`
- `GET /brain/run-supervision/timeout-policies`
- `POST /brain/run-supervision/compensation-plans`
- `POST /brain/run-supervision/runs/{run_supervision_id}/propose-compensation`
- `GET /brain/run-supervision/compensation-plans/{compensation_plan_id}`
- `GET /brain/run-supervision/compensation-plans`
- `POST /brain/run-supervision/compensation-plans/{compensation_plan_id}/approve`
- `POST /brain/run-supervision/compensation-plans/{compensation_plan_id}/convert-to-action-proposals`
- `POST /brain/run-supervision/reports`

CLI examples:

```bash
./scripts/aionctl.sh run-supervision sample --run-supervision-id run-supervision-id
./scripts/aionctl.sh run-supervision compensation propose --run-supervision-id run-supervision-id
```

See `docs/adr/0059-run-supervision-cancellation-compensation.md`.

## Temporal Scheduler, Reminder Queue, and Local Tick

AION v0.1 scheduler is local and tick-driven. It does not start background
workers or execute scheduled target actions.

The Temporal Scheduler stores generic schedules, recurrence rules, due items,
reminders, tick runs, schedule policies, and scheduler reports. A tick may
create scheduler-owned due items, local reminders, local notifications,
operator items, or action proposals when both the schedule and tick request
explicitly allow it. It must not run commands, workflows, backups, release
gates, freeze gates, security checks, resilience tests, external calendars, or
external reminders.

Scheduler endpoints:

- `POST /brain/scheduler/schedules`
- `GET /brain/scheduler/schedules/{schedule_id}`
- `GET /brain/scheduler/schedules`
- `POST /brain/scheduler/schedules/{schedule_id}/pause`
- `POST /brain/scheduler/schedules/{schedule_id}/resume`
- `POST /brain/scheduler/schedules/{schedule_id}/disable`
- `DELETE /brain/scheduler/schedules/{schedule_id}`
- `GET /brain/scheduler/due-items`
- `POST /brain/scheduler/reminders`
- `GET /brain/scheduler/reminders`
- `POST /brain/scheduler/reminders/{reminder_id}/acknowledge`
- `POST /brain/scheduler/reminders/{reminder_id}/snooze`
- `POST /brain/scheduler/reminders/{reminder_id}/dismiss`
- `POST /brain/scheduler/tick`
- `GET /brain/scheduler/tick-runs/{tick_run_id}`
- `POST /brain/scheduler/policies`
- `GET /brain/scheduler/policies`
- `POST /brain/scheduler/report`

CLI examples:

```bash
./scripts/aionctl.sh scheduler tick --dry-run
./scripts/aionctl.sh scheduler reminders list
./scripts/aionctl.sh scheduler report
```

See `docs/adr/0061-temporal-scheduler-local-tick.md`.

## Incident Correlation and Recovery Review

AION v0.1 incident correlation is a local Brain layer. It normalizes internal
signals, groups related signals into AION-owned incident records, proposes
root cause candidates, and creates recovery reviews for operator assessment.
It does not call external incident systems, execute remediation, mutate source
records, or add domain-specific runbooks.

Incident correlation defaults to dry-run. Controlled correlation may create
incident records only after policy and autonomy gates allow it.

Incident endpoints:

- `POST /brain/incidents/signals`
- `GET /brain/incidents/signals`
- `POST /brain/incidents/signals/{incident_signal_id}/dismiss`
- `POST /brain/incidents`
- `GET /brain/incidents/{incident_id}`
- `POST /brain/incidents/query`
- `POST /brain/incidents/{incident_id}/acknowledge`
- `POST /brain/incidents/{incident_id}/resolve`
- `POST /brain/incidents/{incident_id}/dismiss`
- `POST /brain/incidents/{incident_id}/archive`
- `POST /brain/incidents/rules`
- `GET /brain/incidents/rules`
- `POST /brain/incidents/rules/seed-defaults`
- `POST /brain/incidents/correlate`
- `GET /brain/incidents/correlation-runs/{correlation_run_id}`
- `POST /brain/incidents/{incident_id}/root-cause-candidates/generate`
- `POST /brain/incidents/root-cause-candidates`
- `GET /brain/incidents/root-cause-candidates`
- `POST /brain/incidents/root-cause-candidates/{root_cause_candidate_id}/confirm`
- `POST /brain/incidents/root-cause-candidates/{root_cause_candidate_id}/dismiss`
- `POST /brain/incidents/recovery-reviews`
- `GET /brain/incidents/recovery-reviews/{recovery_review_id}`
- `GET /brain/incidents/recovery-reviews`

CLI examples:

```bash
./scripts/aionctl.sh incidents query
./scripts/aionctl.sh incidents correlate --dry-run
./scripts/aionctl.sh incidents root-causes generate --incident-id incident-id
./scripts/aionctl.sh incidents recovery-review --incident-id incident-id
```

See `docs/adr/0062-incident-correlation-root-cause-review.md`.

## Global Resource Registry and Link Integrity

AION v0.1 Global Resource Registry is the Brain-owned index and integrity
layer for AION resources. It records safe descriptors, directed links,
backlinks, broken references, orphaned resources, validation runs, rebuild
runs, and registry snapshots. It is not the source of truth for the resources
it indexes.

Canonical resource URIs use:

```text
aion://{resource_type}/{resource_id}
aion://{resource_type}/{resource_id}?trace_id={trace_id}
```

Registry validation and rebuilds are deterministic, local, policy-gated, and
non-repairing. They do not mutate source records, hard-delete source records,
call external services, or infer domain-specific meaning.

Registry endpoints:

- `POST /brain/registry/resources`
- `GET /brain/registry/resources/by-uri`
- `GET /brain/registry/resources/{resource_type}/{resource_id}`
- `POST /brain/registry/query`
- `POST /brain/registry/links`
- `GET /brain/registry/links`
- `GET /brain/registry/backlinks`
- `POST /brain/registry/validate`
- `GET /brain/registry/validation-runs/{validation_run_id}`
- `GET /brain/registry/broken-references`
- `POST /brain/registry/broken-references/{broken_reference_id}/dismiss`
- `GET /brain/registry/orphaned-resources`
- `POST /brain/registry/orphaned-resources/{orphaned_resource_id}/dismiss`
- `POST /brain/registry/rebuild`
- `GET /brain/registry/rebuild-runs/{rebuild_run_id}`
- `POST /brain/registry/snapshots`
- `GET /brain/registry/snapshots/{registry_snapshot_id}`
- `GET /brain/registry/snapshots`

CLI examples:

```bash
./scripts/aionctl.sh registry query
./scripts/aionctl.sh registry validate --dry-run
./scripts/aionctl.sh registry rebuild --dry-run
./scripts/aionctl.sh registry broken
./scripts/aionctl.sh registry snapshot
```

See `docs/resource-registry.md` and
`docs/adr/0063-global-resource-registry-link-integrity.md`.

## Data Lifecycle Manager

AION v0.1 Data Lifecycle Manager is a Brain-owned advisory layer for generic
retention policy, lifecycle classification, archive candidates, redaction
candidates, purge previews, lifecycle reviews, and lifecycle reports. It reads
safe resource descriptors from the Global Resource Registry and writes
lifecycle-owned records only.

The lifecycle layer does not mutate source records, execute archive, execute
redaction, purge records, hard-delete records, call object storage, call
external services, or add domain-specific retention rules. Purge previews
always return `hard_delete_allowed=false` in v0.1. Archive and redaction
candidate conversion creates action proposals only; it does not perform the
action.

Lifecycle endpoints:

- `POST /brain/lifecycle/policies`
- `POST /brain/lifecycle/policies/seed-defaults`
- `GET /brain/lifecycle/policies`
- `GET /brain/lifecycle/policies/{lifecycle_policy_id}`
- `POST /brain/lifecycle/evaluate`
- `GET /brain/lifecycle/evaluations/{lifecycle_evaluation_id}`
- `GET /brain/lifecycle/classifications`
- `GET /brain/lifecycle/archive-candidates`
- `POST /brain/lifecycle/archive-candidates/{archive_candidate_id}/dismiss`
- `POST /brain/lifecycle/archive-candidates/{archive_candidate_id}/convert-to-action-proposal`
- `GET /brain/lifecycle/redaction-candidates`
- `POST /brain/lifecycle/redaction-candidates/{redaction_candidate_id}/dismiss`
- `POST /brain/lifecycle/redaction-candidates/{redaction_candidate_id}/convert-to-action-proposal`
- `POST /brain/lifecycle/purge-preview`
- `GET /brain/lifecycle/purge-previews`
- `POST /brain/lifecycle/reviews`
- `GET /brain/lifecycle/reviews`
- `POST /brain/lifecycle/report`

CLI examples:

```bash
./scripts/aionctl.sh lifecycle seed-defaults
./scripts/aionctl.sh lifecycle evaluate
./scripts/aionctl.sh lifecycle purge-preview --resource-uri aion://generic/res-1
./scripts/aionctl.sh lifecycle report
```

See `docs/adr/0064-data-lifecycle-retention-archive-preview.md`.

## Contract Registry and Interface Drift

AION v0.1 Contract Registry is a local, advisory interface-readiness layer. It
indexes AION-owned contracts, API routes, SDK resources, CLI commands, policy
actions, settings, visual telemetry vocabulary, and registry resource types. It
creates snapshots, runs deterministic compatibility scans, records interface
drift findings, generates informational migration notes, and produces contract
readiness reports.

The registry does not mutate source records, generate code, repair SDK or CLI
methods, execute migration steps, call external services, expose hidden
reasoning, print raw prompts, or add domain-specific compatibility logic.
Source code remains the source of truth.

Contract Registry endpoints:

- `GET /brain/contracts/contracts`
- `GET /brain/contracts/interfaces`
- `POST /brain/contracts/snapshots`
- `GET /brain/contracts/snapshots`
- `GET /brain/contracts/snapshots/{contract_snapshot_id}`
- `POST /brain/contracts/rules/seed-defaults`
- `GET /brain/contracts/rules`
- `POST /brain/contracts/compatibility/scan`
- `GET /brain/contracts/compatibility/scans/{compatibility_scan_id}`
- `GET /brain/contracts/findings`
- `POST /brain/contracts/findings/{drift_finding_id}/dismiss`
- `GET /brain/contracts/migration-notes`
- `POST /brain/contracts/report`

CLI examples:

```bash
./scripts/aionctl.sh contracts list
./scripts/aionctl.sh contracts interfaces
./scripts/aionctl.sh contracts snapshot
./scripts/aionctl.sh contracts scan
./scripts/aionctl.sh contracts findings
./scripts/aionctl.sh contracts report
```

The Python SDK exposes the same surface through `client.contracts`.

See `docs/adr/0065-contract-registry-interface-drift.md`.

## Extension Registry and Module Intake

AION v0.1 Extension Registry is a metadata-only intake layer for future
modules. It validates local manifests, records package metadata, declared
capabilities, declared dependencies, compatibility checks, reviews, and
non-executable future install plans.

The registry does not load code, install packages, run shell commands, clone or
download sources, register dynamic routes, activate capabilities, create policy
actions from manifests, call external services, or add domain-specific module
logic. Install plans always keep `executable=false` and
`execution_allowed=false` in v0.1.

Extension Registry endpoints:

- `POST /brain/extensions/manifests/validate`
- `POST /brain/extensions/intake`
- `GET /brain/extensions/intake-runs/{extension_intake_id}`
- `GET /brain/extensions/packages/{extension_package_id}`
- `POST /brain/extensions/query`
- `POST /brain/extensions/packages/{extension_package_id}/archive`
- `DELETE /brain/extensions/packages/{extension_package_id}`
- `GET /brain/extensions/packages/{extension_package_id}/capabilities`
- `GET /brain/extensions/packages/{extension_package_id}/dependencies`
- `POST /brain/extensions/compatibility/check`
- `GET /brain/extensions/compatibility/{extension_compatibility_id}`
- `POST /brain/extensions/packages/{extension_package_id}/review`
- `GET /brain/extensions/reviews`
- `POST /brain/extensions/packages/{extension_package_id}/install-plan`
- `GET /brain/extensions/install-plans/{install_plan_id}`
- `GET /brain/extensions/install-plans`

CLI examples:

```bash
./scripts/aionctl.sh extensions validate --manifest-file ./manifest.json
./scripts/aionctl.sh extensions intake --manifest-file ./manifest.json
./scripts/aionctl.sh extensions query
./scripts/aionctl.sh extensions compatibility-check extension-package-1
./scripts/aionctl.sh extensions install-plan extension-package-1
```

The Python SDK exposes the same surface through `client.extensions`.

See `docs/extensions.md` and
`docs/adr/0066-extension-registry-module-intake.md`.

## Module Slots and Capability Bindings

The Module Slot Manager and Capability Binding Registry provide AION's staging
layer between metadata-only extension intake and any future runtime activation.
Module slots record inactive future module positions. Capability bindings
record inactive mappings from module slots to declared capability metadata.

Binding validation checks contracts, policy actions, runtime settings, sandbox
requirements, activation flags, and route-registration flags. Mount plans are
non-executable future records. Route binding previews describe future route
metadata without registering routes.

AION v0.1 module slots and capability bindings are metadata-only. They do not
load code, install packages, activate capabilities, or register routes.

Module binding endpoints:

- `POST /brain/module-slots`
- `GET /brain/module-slots/{module_slot_id}`
- `GET /brain/module-slots`
- `POST /brain/module-slots/{module_slot_id}/archive`
- `DELETE /brain/module-slots/{module_slot_id}`
- `POST /brain/capability-bindings`
- `GET /brain/capability-bindings/{capability_binding_id}`
- `GET /brain/capability-bindings`
- `POST /brain/capability-bindings/{capability_binding_id}/disable`
- `POST /brain/module-bindings/validate`
- `GET /brain/module-bindings/validations/{binding_validation_id}`
- `GET /brain/module-bindings/conflicts`
- `POST /brain/module-bindings/conflicts/{binding_conflict_id}/dismiss`
- `POST /brain/module-bindings/mount-plans`
- `GET /brain/module-bindings/mount-plans/{mount_plan_id}`
- `GET /brain/module-bindings/mount-plans`
- `POST /brain/module-bindings/route-previews`
- `GET /brain/module-bindings/route-previews`
- `POST /brain/module-bindings/query`

CLI examples:

```bash
./scripts/aionctl.sh module-slots list
./scripts/aionctl.sh capability-bindings list
./scripts/aionctl.sh module-bindings validate --dry-run
```

The Python SDK exposes the same surface through `client.module_bindings`.

See `docs/adr/0067-capability-binding-module-slot-manager.md`.

## Module Activation Request Gate

AION-083 adds a metadata-only Module Activation Request Gate. It lets
operators create future activation requests, run deterministic blockers, record
reviews, create non-executable activation plans, and generate runtime
registration previews.

The gate is not an activation layer. It does not load code, install packages,
register routes, mutate runtime configuration, invoke capabilities, call
external services, enable full autonomy, or activate modules. All public
records keep activation, execution, and runtime registration disabled.

Module activation endpoints:

- `POST /brain/module-activation/requests`
- `GET /brain/module-activation/requests`
- `GET /brain/module-activation/requests/{activation_request_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/archive`
- `DELETE /brain/module-activation/requests/{activation_request_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/gate`
- `GET /brain/module-activation/requests/{activation_request_id}/gate-runs`
- `GET /brain/module-activation/blockers`
- `POST /brain/module-activation/blockers/{activation_blocker_id}/dismiss`
- `POST /brain/module-activation/reviews`
- `GET /brain/module-activation/reviews`
- `POST /brain/module-activation/requests/{activation_request_id}/plans`
- `GET /brain/module-activation/plans`
- `GET /brain/module-activation/plans/{activation_plan_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/runtime-registration-preview`
- `GET /brain/module-activation/runtime-registration-previews`
- `GET /brain/module-activation/runtime-registration-previews/{registration_preview_id}`
- `POST /brain/module-activation/query`

CLI examples:

```bash
./scripts/aionctl.sh module-activation request <module-slot-id>
./scripts/aionctl.sh module-activation gate <activation-request-id>
./scripts/aionctl.sh module-activation blockers
./scripts/aionctl.sh module-activation plan <activation-request-id>
./scripts/aionctl.sh module-activation runtime-preview <activation-request-id>
./scripts/aionctl.sh module-activation query
```

The Python SDK exposes the same surface through `client.module_activation`.

See `docs/module-activation-gate.md` and
`docs/adr/0074-module-activation-request-gate.md`.

## Capability Conformance Harness

AION v0.1 includes a Capability Conformance Harness for staged module and
capability metadata. It validates schemas, required policy actions, settings,
sandbox declarations, and safe metadata flags before a future activation layer
exists.

The mock invocation simulator is schema-only. It hashes and redacts input
payloads, returns deterministic placeholder output shapes, and never invokes a
capability, loads package code, installs packages, calls MCP, calls sandbox
runtimes, registers routes, or contacts external services.

Readiness assessments consume conformance runs and produce local readiness
records. `activation_ready` remains false in v0.1.

Conformance endpoints:

- `POST /brain/conformance/profiles`
- `GET /brain/conformance/profiles/{conformance_profile_id}`
- `GET /brain/conformance/profiles`
- `POST /brain/conformance/profiles/seed-defaults`
- `POST /brain/conformance/test-vectors`
- `GET /brain/conformance/test-vectors/{test_vector_id}`
- `GET /brain/conformance/test-vectors`
- `POST /brain/conformance/test-vectors/generate-for-binding/{capability_binding_id}`
- `POST /brain/conformance/run`
- `GET /brain/conformance/runs/{conformance_run_id}`
- `GET /brain/conformance/findings`
- `POST /brain/conformance/findings/{conformance_finding_id}/dismiss`
- `POST /brain/readiness/assess`
- `GET /brain/readiness/assessments/{readiness_assessment_id}`
- `GET /brain/readiness/assessments`
- `POST /brain/conformance/query`

Developer commands:

```bash
./scripts/aionctl.sh --scope workspace:main conformance profiles
./scripts/aionctl.sh --scope workspace:main conformance profiles seed
./scripts/aionctl.sh --scope workspace:main conformance test-vectors
./scripts/aionctl.sh --scope workspace:main conformance test-vectors generate <capability-binding-id>
./scripts/aionctl.sh --scope workspace:main conformance run --capability-binding-id <capability-binding-id>
./scripts/aionctl.sh --scope workspace:main conformance findings
./scripts/aionctl.sh --scope workspace:main readiness assess --capability-binding-id <capability-binding-id>
./scripts/aionctl.sh --scope workspace:main readiness list
./scripts/aionctl.sh --scope workspace:main conformance query
```

The Python SDK exposes the same surface through `client.conformance`.

See `docs/adr/0068-capability-conformance-readiness-gate.md`.

## Golden Path Scenario Harness

AION v0.1 includes a local deterministic Golden Path Scenario Harness. It
verifies core Brain integration through synthetic fixture packs, scenario-owned
records, dry-run steps, assertion results, reports, and a release smoke matrix.

The harness is not a frontend demo, production monitor, load test, model
benchmark, or domain test suite. It does not call external services, call model
providers, execute tools, execute action proposals, run handoffs in controlled
mode by default, hard-delete fixtures, or mutate non-scenario source records.

Golden path endpoints:

- `POST /brain/golden-path/scenarios/seed-defaults`
- `POST /brain/golden-path/scenarios`
- `GET /brain/golden-path/scenarios`
- `GET /brain/golden-path/scenarios/{scenario_key}`
- `POST /brain/golden-path/fixtures/seed-defaults`
- `GET /brain/golden-path/fixtures`
- `POST /brain/golden-path/run`
- `GET /brain/golden-path/runs`
- `GET /brain/golden-path/runs/{golden_path_run_id}`
- `POST /brain/golden-path/release-smoke`
- `GET /brain/golden-path/reports`
- `GET /brain/golden-path/reports/{golden_path_report_id}`
- `POST /brain/golden-path/query`

Developer commands:

```bash
./scripts/golden-path.sh
./scripts/release-smoke.sh
./scripts/aionctl.sh --scope workspace:main golden-path scenarios
./scripts/aionctl.sh --scope workspace:main golden-path fixtures
./scripts/aionctl.sh --scope workspace:main golden-path run
./scripts/aionctl.sh --scope workspace:main golden-path reports
./scripts/aionctl.sh --scope workspace:main golden-path release-smoke
```

The Python SDK exposes the same surface through `client.golden_path`.

See `docs/operations/golden-path.md` and
`docs/adr/0069-golden-path-scenario-harness.md`.

## Deterministic Module Mock Runtime

AION-085 adds a deterministic module mock runtime for post-v0.1 module
readiness. It records mock profiles, dry-run invocation requests, synthetic
outputs, run records, findings, and aggregate query results. It does not load
code, install packages, activate modules, execute capabilities, register
routes, mutate runtime configuration, call external services, or add
domain-specific logic.

Module mock runtime endpoints:

- `POST /brain/module-mock/profiles`
- `POST /brain/module-mock/profiles/seed-defaults`
- `GET /brain/module-mock/profiles`
- `GET /brain/module-mock/profiles/{mock_profile_id}`
- `POST /brain/module-mock/invoke`
- `GET /brain/module-mock/runs`
- `GET /brain/module-mock/runs/{module_mock_run_id}`
- `GET /brain/module-mock/outputs`
- `GET /brain/module-mock/outputs/{module_mock_output_id}`
- `GET /brain/module-mock/findings`
- `POST /brain/module-mock/findings/{module_mock_finding_id}/dismiss`
- `POST /brain/module-mock/query`

The `/brain/module-mock-runtime/*` prefix remains a compatibility alias for
local tooling created during the AION-085 implementation.

Developer commands:

```bash
./scripts/aionctl.sh --scope workspace:main module-mock seed-profiles
./scripts/aionctl.sh --scope workspace:main module-mock invoke <capability-binding-id> --capability-key generic.example
./scripts/aionctl.sh --scope workspace:main module-mock runs
./scripts/aionctl.sh --scope workspace:main module-mock outputs
./scripts/aionctl.sh --scope workspace:main module-mock findings
./scripts/aionctl.sh --scope workspace:main module-mock query
```

The Python SDK exposes the same surface through `client.module_mock_runtime`.

Generic Knowledge Intelligence includes mock runtime fixtures and docs at
`docs/modules/generic-knowledge-intelligence-mock-runtime.md`.

## Model Provider Hardening

AION-086 adds model provider hardening before any real provider can be enabled.
It creates provider profiles, prompt egress previews, dry-run simulations,
readiness assessments, blockers, and aggregate queries. It does not call model
providers, transmit prompts, store provider credentials, invoke models, execute
tools, or enable external model calls.

Model provider endpoints:

- `POST /brain/model-providers/profiles`
- `GET /brain/model-providers/profiles`
- `GET /brain/model-providers/profiles/{provider_profile_id}`
- `POST /brain/model-providers/profiles/seed-defaults`
- `POST /brain/model-providers/egress-preview`
- `POST /brain/model-providers/simulate`
- `POST /brain/model-providers/readiness`
- `GET /brain/model-providers/blockers`
- `POST /brain/model-providers/blockers/{provider_blocker_id}/dismiss`
- `POST /brain/model-providers/query`

Developer commands:

```bash
./scripts/model-provider-check.sh --offline-ok --skip-api
./scripts/aionctl.sh --scope workspace:main model-providers profiles seed
./scripts/aionctl.sh --scope workspace:main model-providers simulate generic.metadata_only
./scripts/aionctl.sh --scope workspace:main model-providers readiness generic.metadata_only
./scripts/aionctl.sh --scope workspace:main model-providers blockers
```

The Python SDK exposes the same surface through
`client.model_provider_hardening`.

## Governed Operator Actions

AION-092 adds dry-run governed operator action records:

- `POST /brain/operator-actions/requests`
- `GET /brain/operator-actions/requests/{operator_action_request_id}`
- `GET /brain/operator-actions/requests`
- `POST /brain/operator-actions/requests/{operator_action_request_id}/preview`
- `GET /brain/operator-actions/previews`
- `GET /brain/operator-actions/blockers`
- `POST /brain/operator-actions/blockers/{operator_action_blocker_id}/dismiss`
- `POST /brain/operator-actions/requests/{operator_action_request_id}/review`
- `GET /brain/operator-actions/reviews`
- `POST /brain/operator-actions/query`

Requests, previews, blockers, and reviews are local governance records only.
They keep `mode=dry_run`, `execution_allowed=false`,
`external_calls_allowed=false`, and `activation_allowed=false`.

Developer commands:

```bash
./scripts/operator-actions-check.sh
./scripts/aionctl.sh --scope workspace:main operator-actions request --action-key operator.review
./scripts/aionctl.sh --scope workspace:main operator-actions requests
./scripts/aionctl.sh --scope workspace:main operator-actions blockers
```

## Local Auth

AION-093 adds the local auth design for the future Operator Console. AION-094
adds the dev-only local auth contract, synthetic identity simulation,
role-aware console filtering, status, and audit surfaces.

No production auth is implemented. No credentials are stored. No sessions are
created. No external identity provider is integrated. No login endpoint is
added. ActorContext remains the current internal context mechanism, and policy
remains authoritative for backend access.

AION-095 adds a read-only local session prototype for the Operator Console. It
creates synthetic session previews and role-aware session context only. It does
not add production auth, login/logout, credential storage, token or cookie
issuance, browser session storage, persistent session tables, writes,
execution, activation, runtime registration, or external calls.

Primary docs:

- `docs/auth/local-auth-design.md`
- `docs/auth/operator-identity-model.md`
- `docs/auth/operator-session-boundary.md`
- `docs/auth/operator-role-model.md`
- `docs/auth/operator-access-matrix.md`
- `docs/auth/operator-auth-threat-model.md`
- `docs/auth/production-auth-prerequisites.md`
- `docs/auth/auth-no-go-conditions.md`
- `docs/auth/future-auth-implementation-plan.md`
- `docs/auth/local-auth-contract.md`
- `docs/auth/dev-identity-simulation.md`
- `docs/auth/role-aware-console-filtering.md`
- `docs/auth/local-auth-audit.md`
- `docs/auth/local-auth-runtime-boundaries.md`
- `docs/auth/local-session-prototype.md`
- `docs/auth/local-session-boundary.md`
- `docs/auth/session-safety-audit.md`
- `docs/auth/session-preview-console-panel.md`
- `docs/auth/future-session-implementation-plan.md`
- `docs/auth/production-auth-architecture.md`
- `docs/auth/auth-provider-evaluation-matrix.md`
- `docs/auth/identity-provider-boundary-model.md`
- `docs/auth/token-session-storage-decision.md`
- `docs/auth/credential-handling-no-go-rules.md`
- `docs/auth/production-auth-threat-model.md`
- `docs/auth/production-auth-release-gates.md`
- `docs/auth/disabled-auth-prototype-plan.md`
- `docs/auth/disabled-production-auth-prototype.md`
- `docs/auth/mock-claims-adapter.md`
- `docs/auth/auth-runtime-gate.md`
- `docs/auth/auth-runtime-audit.md`
- `docs/auth/auth-runtime-no-go.md`

Developer command:

```bash
./scripts/auth-design-check.sh
./scripts/local-auth-check.sh
./scripts/local-session-check.sh
./scripts/role-filter-check.sh
./scripts/production-auth-architecture-check.sh
```

### AION-096 Role-Aware Console Filtering

AION-096 adds a read-only role permission proof matrix, role-aware console view
filtering, access audit reports, and static role preview data. It does not add
production auth, login/logout, credential storage, session persistence,
execution, activation, or external calls.

### AION-097 Dry-Run Action Authorization

AION-097 adds dry-run authorization enforcement for governed operator action
requests, previews, and reviews. It connects local auth roles, local session
context, the role permission matrix, policy, action type, target type, and
safety blockers. It remains dry-run only and does not add writes, execution,
activation, external calls, production auth, or frontend dependencies.

Developer command:

```bash
./scripts/action-authorization-check.sh
```

### AION-098 Production Auth Architecture

AION-098 decides the future production auth architecture without implementing
it. The recommended future path is OIDC-compatible production auth, with
reverse proxy auth allowed later as an optional deployment pattern.

No production auth is implemented in AION-098. No provider integration is added
in AION-098. No credentials, tokens, sessions, or cookies are created, stored,
issued, or accepted. `production_auth_enabled` remains false. AION-099 may add
a disabled mock-only prototype behind flags only.

### AION-099 Disabled Production Auth Prototype

AION-099 adds disabled auth runtime status, mock-claims preview, and audit
contracts. It remains mock-only and disabled by default. It does not add
production auth, login/logout, provider callbacks, credential storage, token or
cookie issuance, persistent sessions, frontend dependencies, migrations,
external identity calls, execution, activation, or hard delete.

Developer command:

```bash
./scripts/auth-runtime-check.sh
```

### AION-100 Static Console UI Release Gate

AION-100 adds the static console UI release gate and post-v0.1 operator
platform checkpoint. It keeps the Operator Console local, read-only,
dependency-free, build-free, login-free, provider-call-free, activation-free,
and execution-free.

Primary docs:

- `docs/operator-console/ui-release-gate.md`
- `docs/operator-console/static-console-safety-matrix.md`
- `docs/operator-console/operator-platform-checkpoint.md`
- `docs/operator-console/post-v0.1-ui-no-go-conditions.md`
- `docs/operator-console/static-console-artifact-manifest.md`
- `docs/operator-console/ui-release-evidence-summary.md`

Developer command:

```bash
./scripts/static-console-safety-check.sh
./scripts/ui-release-gate.sh
```

### AION-101 Operator Platform Checkpoint

AION-101 closes the post-v0.1 Operator Platform phase with a checkpoint
evidence pack. It proves the static console remains safe, read-only,
local-only, dependency-free, auth-disabled or mock-only, and not production UI
before AION-102 planning.

Primary docs:

- `docs/operator-console/operator-platform-phase-checkpoint.md`
- `docs/operator-console/operator-platform-evidence-pack.md`
- `docs/operator-console/operator-platform-risk-register.md`
- `docs/operator-console/operator-platform-next-phase.md`
- `docs/operator-console/operator-platform-release-readiness.md`
- `docs/adr/0092-operator-platform-checkpoint.md`

Developer command:

```bash
./scripts/operator-platform-checkpoint.sh
```

### AION-102 Operator Platform Stabilization Gate

AION-102 converts the Operator Platform checkpoint into a long-running
regression matrix and checkpoint freeze gate. It is stabilization evidence only:
no runtime subsystem, frontend dependency, production auth, write path,
activation path, execution path, provider call, external call, package
installation, or migration is added.

Primary docs:

- `docs/operator-console/operator-platform-regression-matrix.md`
- `docs/operator-console/operator-platform-freeze-gate.md`
- `docs/operator-console/operator-platform-long-running-checks.md`
- `docs/operator-console/operator-platform-stabilization-runbook.md`
- `docs/operator-console/operator-platform-regression-evidence.md`
- `docs/adr/0093-operator-platform-stabilization-gate.md`

Developer command:

```bash
./scripts/operator-platform-regression.sh
./scripts/operator-platform-freeze-gate.sh
```

### AION-103 Static Console UX Refinement

AION-103 refines the static local Operator Console UX. It adds navigation
groups, a skip link, section shortcuts, visible focus states, a safety blocker
view, and safe copy support for approved local read-only checks only. It keeps
the console static, dependency-free, build-free, login-free,
credential-control-free, provider-call-free, activation-free, execution-free,
write-free, and external-call-free.

Primary docs:

- `docs/operator-console/static-console-ux-refinement.md`
- `docs/operator-console/static-console-accessibility-checklist.md`
- `docs/operator-console/static-console-navigation-model.md`
- `docs/operator-console/static-console-information-architecture.md`
- `docs/adr/0094-static-console-ux-refinement.md`

Developer command:

```bash
./scripts/static-console-ux-check.sh
```

### AION-104 Local Auth Prototype Review Gate

AION-104 reviews and freezes the local auth and disabled auth prototype path
before future auth implementation work. It adds auth safety evidence, disabled
runtime proof, traceability, no-go regression evidence, and a
pre-implementation gate. It remains evidence-only: no production auth,
login/logout, credentials, tokens, cookies, persisted sessions, external
identity runtime, provider SDK, migration, API router, package file, write
path, activation path, execution path, or external call is added.

Primary docs:

- `docs/auth/local-auth-prototype-review.md`
- `docs/auth/auth-safety-evidence-pack.md`
- `docs/auth/auth-runtime-disabled-proof.md`
- `docs/auth/auth-traceability-matrix.md`
- `docs/auth/auth-no-go-regression-pack.md`
- `docs/auth/pre-implementation-auth-gate.md`
- `docs/adr/0095-local-auth-prototype-review-gate.md`

Developer command:

```bash
./scripts/auth-prototype-review.sh
./scripts/auth-no-go-regression.sh
```

### AION-106 External Connector Boundary Design

AION-106 designs the external connector boundary before connector runtime
exists. It adds connector trust, credential, egress, ingress, capability
declaration, threat model, release gate, no-go regression, and future
implementation prerequisite docs. It remains evidence-only: no connector
runtime, network client, connector SDK, provider SDK, credential, token,
external call, dynamic route, migration, API router, SDK resource, CLI command,
activation, execution, or package file is added.

Primary docs:

- `docs/connectors/external-connector-boundary-design.md`
- `docs/connectors/connector-trust-model.md`
- `docs/connectors/connector-credential-boundary.md`
- `docs/connectors/connector-egress-guard.md`
- `docs/connectors/connector-ingress-guard.md`
- `docs/connectors/connector-capability-declaration.md`
- `docs/connectors/connector-threat-model.md`
- `docs/connectors/connector-release-gates.md`
- `docs/connectors/connector-no-go-regression-pack.md`
- `docs/connectors/future-connector-implementation-prerequisites.md`
- `docs/adr/0097-external-connector-boundary-design.md`

Developer command:

```bash
./scripts/connector-boundary-design-check.sh
./scripts/connector-no-go-regression.sh
```

### AION-107 Operator Action Write-Path Architecture

AION-107 designs the future operator action write path before any execution
capability exists. It adds write-path architecture, approval boundary,
execution boundary, lifecycle, rollback, separation-of-duties, threat model,
release gates, no-go regression docs, synthetic examples, and local gate
scripts. It remains design-only: no write execution, tool execution, action
proposal execution, controlled handoff execution, connector runtime, external
call, module activation, capability activation, production auth, login/logout,
session persistence, migration, API router, SDK resource, CLI command, package
file, or frontend dependency is added.

Primary docs:

- `docs/operator-actions/write-path-architecture.md`
- `docs/operator-actions/approval-boundary-design.md`
- `docs/operator-actions/execution-boundary-design.md`
- `docs/operator-actions/action-intent-lifecycle.md`
- `docs/operator-actions/controlled-execution-prerequisites.md`
- `docs/operator-actions/rollback-and-undo-model.md`
- `docs/operator-actions/separation-of-duties.md`
- `docs/operator-actions/write-path-threat-model.md`
- `docs/operator-actions/write-path-release-gates.md`
- `docs/operator-actions/write-path-no-go-regression-pack.md`
- `docs/adr/0098-operator-action-write-path-architecture.md`

Developer command:

```bash
./scripts/operator-action-write-path-design-check.sh
./scripts/operator-action-write-path-no-go-regression.sh
```

## AION-109 Connector Runtime Review Gate

AION-109 reviews and freezes the disabled connector runtime path before any
future connector implementation. It adds the connector runtime review gate,
no-external-call evidence pack, credential/token absence proof,
egress/ingress traceability matrix, disabled runtime proof,
pre-implementation gate, no-go review pack, future implementation plan, ADR
0100, and local review scripts.

Developer command:

```bash
./scripts/connector-runtime-review.sh
./scripts/connector-runtime-no-external-call-regression.sh
```

## AION-111 Connector Policy Action Catalog

AION-111 adds policy action catalog proof before any future connector runtime
work. It introduces `GET /brain/connector-policy/catalog`,
`GET /brain/connector-policy/matrix`, `POST /brain/connector-policy/dry-run`,
`POST /brain/connector-policy/traceability/query`, and
`GET /brain/connector-policy/status`. The SDK and CLI expose catalog, matrix,
dry-run, traceability query, and status preview helpers only.

Developer command:

```bash
./scripts/connector-policy-check.sh
./scripts/connector-policy-no-go-regression.sh
```

## AION-113 Connector Credential Store Architecture

AION-113 adds the design-only connector credential store architecture,
readiness gate, redaction preview, SDK/CLI preview surface, static console
panels, and no-go regressions. Credential storage, token storage, secret
material, external identity runtime, connector runtime credential access,
external calls, package dependencies, and migrations remain absent.

Developer command:

```bash
./scripts/connector-credential-check.sh
./scripts/connector-credential-no-go-regression.sh
```

## AION-114 Connector Release Gate

AION-114 adds the connector release gate, safety freeze, end-to-end readiness
evidence, implementation readiness decision, static console release panels, and
release no-go regression. Connector implementation remains unapproved:
runtime, external calls, credentials, tokens, sandbox execution, activation,
route registration, package files, migrations, API routes, SDK resources, and
CLI implementations remain unchanged.

Developer command:

```bash
./scripts/connector-release-gate.sh
./scripts/connector-safety-freeze.sh
./scripts/connector-release-no-go-regression.sh
```

## AION-116 Connector Platform Stabilization Gate

AION-116 adds the connector platform stabilization runbook, long-running
regression matrix, connector phase freeze gate, stabilization evidence pack,
safety baseline lock, regression evidence examples, static console
stabilization panels, ADR 0107, and stabilization scripts. It is
stabilization-only: connector implementation remains unapproved, runtime
remains disabled, external calls remain absent, credentials/tokens remain
absent, sandbox execution remains absent, activation and route registration
remain disabled, and no package files or migrations are added.

Developer command:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
```

## AION-117 Post-v0.1 Platform Integration Checkpoint

AION-117 adds the cross-phase platform integration checkpoint, evidence pack,
operator/connector boundary matrix, future runtime boundary freeze, platform
risk register, approval state summary, closeout checklist, static console
integration panels, ADR 0108, and repository-local platform scripts. It is
checkpoint-only: operator write execution remains unapproved, connector
implementation remains unapproved, production auth remains unapproved, module
activation remains unapproved, external calls remain absent, credentials/tokens
remain absent, sandbox execution remains absent, and no API routes, SDK/CLI
implementations, package files, lockfiles, migrations, or frontend dependencies
are added.

Developer command:

```bash
./scripts/platform-integration-checkpoint.sh
./scripts/platform-integration-freeze-check.sh
./scripts/platform-integration-no-go-regression.sh
```

## AION-118 Post-v0.1 Release Candidate Gate

AION-118 adds the post-v0.1 release candidate gate, cross-phase freeze
evidence, release candidate checklist, v0.2 planning boundary, implementation
approval lock, release no-go regression, static console release candidate
panels, ADR 0109, and repository-local release candidate scripts. It is
release-candidate evidence only: no release is created, no v0.2 tag is
created, `aion-v0.1.0` is not moved, runtime implementation remains
unapproved, external calls remain absent, credentials/tokens remain absent,
sandbox execution remains absent, and no API routes, SDK/CLI implementations,
package files, lockfiles, migrations, or frontend dependencies are added.

Developer command:

```bash
./scripts/post-v01-release-candidate-gate.sh
./scripts/post-v01-release-candidate-freeze.sh
./scripts/post-v01-release-candidate-no-go-regression.sh
```

## AION-119 v0.2 Planning Charter

AION-119 adds the v0.2 planning charter, runtime implementation decision
framework, candidate workstream map, ADR requirements, gate dependency matrix,
backlog intake criteria, planning closeout checklist, static console planning
panels, ADR 0110, and repository-local planning checks. It is planning-only:
runtime implementation remains unapproved, no v0.2 release or tag is created,
external calls remain absent, credentials and tokens remain absent, sandbox
execution remains absent, package files remain absent, and migrations remain
absent.

Developer command:

```bash
./scripts/v02-planning-charter-check.sh
./scripts/v02-planning-no-go-regression.sh
```

## AION-120 v0.2 Planning Stabilization Gate

AION-120 stabilizes the v0.2 planning charter and freezes backlog governance
before implementation work can be accepted. It adds the planning stabilization
gate, backlog governance freeze, implementation readiness scorecard, evidence
pack, decision review calendar, blocked work register, ADR 0111, static console
planning stabilization panels, and repository-local planning freeze checks. It
is planning stabilization only: runtime implementation and backlog
implementation approval remain false, no v0.2 release or tag is created,
external calls remain absent, credentials and tokens remain absent, sandbox
execution remains absent, package files remain absent, and migrations remain
absent.

Developer command:

```bash
./scripts/v02-planning-stabilization-gate.sh
./scripts/v02-planning-freeze-check.sh
./scripts/v02-planning-stabilization-no-go-regression.sh
```

## AION-121 v0.2 Readiness Final Review

AION-121 closes the v0.2 planning phase for review purposes only. It adds the
readiness final review, planning phase closeout report, implementation approval
guard, readiness evidence matrix, blocked implementation summary, final no-go
review, final checklist, ADR 0112, static console final review panels, and
repository-local final review checks. It does not approve implementation: no
v0.2 release or tag is created, runtime implementation remains unapproved,
backlog implementation approval remains false, external calls remain absent,
credentials and tokens remain absent, sandbox execution remains absent, package
files remain absent, and migrations remain absent.

Developer command:

```bash
./scripts/v02-readiness-final-review.sh
./scripts/v02-readiness-final-freeze.sh
./scripts/v02-readiness-final-no-go-regression.sh
```

## AION-122 v0.2 Implementation Kickoff Boundary

AION-122 adds the implementation kickoff boundary, approval workflow
blueprint, runtime workstream lock, implementation request template, approval
decision record, workstream sequencing plan, kickoff no-go review, ADR 0113,
static console kickoff panels, and repository-local kickoff checks. It does not
approve implementation: runtime implementation remains unapproved, backlog
implementation approval remains false, approval workflow bypass remains false,
external calls remain absent, credentials and tokens remain absent, sandbox
execution remains absent, no v0.2 release or tag is created, package files
remain absent, and migrations remain absent.

Developer command:

```bash
./scripts/v02-implementation-kickoff-boundary-check.sh
./scripts/v02-implementation-kickoff-freeze.sh
./scripts/v02-implementation-kickoff-no-go-regression.sh
```

## AION-123 v0.2 Approval Workflow Stabilization

AION-123 stabilizes the approval workflow created in AION-122. It adds the
approval workflow stabilization gate, implementation request intake validation,
approval decision evidence matrix, expiry and revocation model, dual-control
review model, approval workflow no-go review, stabilization checklist, ADR
0114, static console approval workflow panels, and repository-local approval
workflow checks. It does not approve implementation: runtime implementation
remains unapproved, backlog implementation approval remains false, approval
workflow bypass remains false, approval expiry and revocation bypass remain
false, dual-control bypass remains false, external calls remain absent,
credentials and tokens remain absent, sandbox execution remains absent, no v0.2
release or tag is created, package files remain absent, and migrations remain
absent.

Developer command:

```bash
./scripts/v02-approval-workflow-stabilization-gate.sh
./scripts/v02-approval-workflow-freeze.sh
./scripts/v02-approval-workflow-no-go-regression.sh
```

## AION-124 v0.2 Workstream Intake Readiness

AION-124 defines the v0.2 workstream intake readiness gate, workstream intake
evidence pack, approval record evidence pack, implementation sequencing freeze,
workstream readiness scorecard, rejection rules, intake no-go review, ADR 0115,
static console workstream intake panels, and repository-local workstream intake
checks. It does not approve implementation: runtime implementation remains
unapproved, backlog implementation approval remains false, workstream
implementation approval remains false, approval workflow bypass remains false,
approval record missing remains false, external calls remain absent,
credentials and tokens remain absent, sandbox execution remains absent, no v0.2
release or tag is created, package files remain absent, and migrations remain
absent.

Developer command:

```bash
./scripts/v02-workstream-intake-readiness-gate.sh
./scripts/v02-workstream-intake-freeze.sh
./scripts/v02-workstream-intake-no-go-regression.sh
```

## AION-125 v0.2 Pre-Implementation Master Freeze

AION-125 creates the v0.2 pre-implementation master freeze, final planning
baseline, workstream governance closeout, approval workflow closeout evidence,
implementation lock summary, master no-go regression, final checklist, ADR
0116, static console master freeze panels, and repository-local master freeze
checks. It does not approve implementation: runtime implementation remains
unapproved, backlog implementation approval remains false, workstream
implementation approval remains false, approval workflow bypass remains false,
approval record missing remains false, external calls remain absent,
credentials and tokens remain absent, sandbox execution remains absent, no v0.2
release or tag is created, package files remain absent, and migrations remain
absent.

Developer command:

```bash
./scripts/v02-preimplementation-master-freeze.sh
./scripts/v02-preimplementation-final-baseline-check.sh
./scripts/v02-preimplementation-master-no-go-regression.sh
```

## AION-126 v0.2 Workstream Proposal Registry

AION-126 adds the v0.2 workstream proposal registry, implementation request
index, proposal state machine, proposal evidence requirements, and approval
queue preview on top of the AION-125 master freeze. This is proposal registry
and queue preview only. It does not approve implementation, create a v0.2 tag,
create a release, enable runtime, enable external calls, store credentials or
tokens, enable sandbox execution, add package files, add migrations, or add
runtime API, SDK, or CLI implementation.

Developer command:

```bash
./scripts/v02-workstream-proposal-registry-check.sh
./scripts/v02-proposal-registry-freeze.sh
./scripts/v02-proposal-registry-no-go-regression.sh
```

### AION-129 v0.2 Final Planning Release Gate

AION-129 adds the final v0.2 planning release gate, governance baseline
evidence, no-implementation freeze, final approval lock evidence, planning
release gate matrix, final planning no-go regression, ADR 0120, and static
console preview data. It does not create a v0.2 tag or release and keeps
runtime implementation, backlog implementation, workstream implementation,
proposal implementation, approval queue item approval, connector
implementation, production auth, module activation, external calls,
credential storage, token storage, and sandbox execution unapproved.

```bash
./scripts/v02-final-planning-release-gate.sh
./scripts/v02-final-planning-freeze.sh
./scripts/v02-final-planning-no-go-regression.sh
```

### AION-130 v0.2 Planning Track Closeout

AION-130 adds the v0.2 planning track closeout report, governance handoff
pack, implementation request phase boundary, final approval-state ledger,
proposal queue status summary, evidence index, no-go regression, ADR 0121, and
static console preview data. It closes planning only: proposal registry remains
preview-only, approval queue remains preview-only, implementation approvals
remain false, no v0.2 tag is created, and no v0.2 release is created.

```bash
./scripts/v02-planning-track-closeout.sh
./scripts/v02-planning-track-handoff-freeze.sh
./scripts/v02-planning-track-closeout-no-go-regression.sh
```
