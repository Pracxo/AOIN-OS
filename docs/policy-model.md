# Policy Model

The policy engine gates every Brain action before execution or delegation.

Modules never self-authorize. They request execution through AION Brain, and the
Brain asks the policy adapter for a decision.

Policy can:

- Allow execution.
- Deny execution.
- Require human approval.
- Attach constraints.
- Increase audit level.

Open Policy Agent is prepared as the first policy adapter boundary. The public
AION API still returns `PolicyDecision`, not OPA-specific objects.

## Generic Vocabulary

AION core policy vocabulary stays generic:

- `event.ingest`
- `event.subscription.create`
- `event.subscription.read`
- `event.subscription.disable`
- `event.dispatch`
- `event.dispatch.read`
- `event.reaction.run`
- `event.reaction.noop`
- `event.dead_letter.read`
- `event.dead_letter.resolve`
- `event.dead_letter.replay`
- `memory.retrieve`
- `memory.write`
- `context.compile`
- `intent.classify`
- `plan.create`
- `plan.execute`
- `execution.step`
- `approval.request`
- `risk.assess`
- `guardrail.rule.create`
- `guardrail.rule.read`
- `guardrail.rule.disable`
- `guardrail.evaluate`
- `approval.request.create`
- `approval.request.read`
- `approval.decision.create`
- `approval.request.cancel`
- `approval.expire`
- `reasoning.run`
- `model.route`
- `model.complete`
- `response.verify`
- `response.evaluate`
- `capability.list`
- `capability.register`
- `capability.invoke`
- `capability.bind_runtime`
- `module.runtime.register`
- `module.runtime.read`
- `module.runtime.health_check`
- `mcp.server.register`
- `mcp.server.read`
- `mcp.server.disable`
- `mcp.server.health_check`
- `mcp.tools.sync`
- `mcp.tool.invoke`
- `mcp.mapping.read`
- `mcp.mapping.write`
- `goal.create`
- `goal.read`
- `goal.transition`
- `task.create`
- `task.read`
- `task.transition`
- `task.run`
- `schedule.create`
- `schedule.read`
- `schedule.update`
- `cycle.template.create`
- `cycle.template.read`
- `cycle.template.disable`
- `cycle.run`
- `cycle.read`
- `cycle.step.run`
- `cycle.status.read`
- `sleep_consolidation.run`
- `maintenance.run`
- `trace.read`
- `learning.record`
- `reflection.create`
- `reflection.read`
- `skill.candidate.create`
- `skill.candidate.read`
- `skill.candidate.update`
- `skill.promote`
- `skill.read`
- `skill.activate`
- `skill.disable`
- `skill.archive`
- `skill.match`
- `identity.actor.create`
- `identity.actor.read`
- `identity.actor.disable`
- `identity.workspace.create`
- `identity.workspace.read`
- `identity.workspace.archive`
- `identity.membership.create`
- `identity.membership.read`
- `identity.membership.revoke`
- `identity.permission.create`
- `identity.permission.read`
- `identity.permission.revoke`
- `scope.resolve`
- `evidence.create`
- `evidence.read`
- `evidence.search`
- `evidence.link`

## Connector Simulator Policy Actions

AION-110 adds policy actions for synthetic connector simulator evidence:

- `connector_simulator.simulate`
- `connector_simulator.replay`
- `connector_simulator.policy_readiness`
- `connector_simulator.status.read`
- `connector_simulator.query`

These actions authorize local dry-run simulation surfaces only. They do not
approve connector runtime, external calls, credential use, token use, route
registration, tool execution, or write execution.

## Connector Policy Action Catalog

AION-111 adds policy actions for connector policy preview:

- `connector_policy.catalog.read`
- `connector_policy.matrix.read`
- `connector_policy.dry_run`
- `connector_policy.traceability.read`

These actions authorize catalog reads, matrix reads, dry-run policy decisions,
and traceability reads only. They do not approve connector runtime, external
calls, credential access, token access, route registration, activation, tool
execution, or write execution.
- `evidence.ground`
- `evidence.delete`
- `contract_registry.contract.read`
- `contract_registry.interface.read`
- `contract_registry.snapshot.create`
- `contract_registry.snapshot.read`
- `contract_registry.rule.create`
- `contract_registry.rule.read`
- `contract_registry.compatibility.scan`
- `contract_registry.finding.read`
- `contract_registry.finding.dismiss`
- `contract_registry.migration_note.read`
- `contract_registry.report.read`
- `bootstrap.profile.create`
- `bootstrap.profile.read`
- `bootstrap.profile.update`
- `bootstrap.seed_bundle.create`
- `bootstrap.seed_bundle.read`
- `bootstrap.seed_bundle.update`
- `bootstrap.seed.execute`
- `bootstrap.doctor.run`
- `bootstrap.finding.read`
- `bootstrap.finding.update`
- `bootstrap.run`
- `bootstrap.run.read`
- `bootstrap.report.create`
- `bootstrap.report.read`
- `bootstrap.query`

Semantic adapter status reads and TurboVec status checks use the generic
`memory.retrieve` action. Semantic indexing, TurboVec rebuild, and TurboVec
single-memory reindex use the generic `memory.write` action. The policy
vocabulary does not add vector-engine-specific or domain-specific actions.

Domain policies will live outside Brain core later. Finance, trading, IT,
legal, healthcare, HR, procurement, and other vertical rules must not be encoded
in the core policy file.

## Contract Registry Policy

Contract Registry actions are generic control-plane actions. Reads are low
risk. Snapshot creation and compatibility scans are medium-risk because they
write advisory records, but they do not mutate source code. Finding dismissal is
a governed metadata update only. Migration-note reads and reports are
informational.

Policy must fail closed. The registry must not self-authorize, generate source,
execute migration steps, repair SDK or CLI methods, call external services, or
add domain-specific compatibility rules.

## Bootstrap Policy

Bootstrap actions are generic local-readiness actions. Reads are low risk.
Profile, seed-bundle, seed-execution, doctor, report, and run writes are medium
risk because they create local metadata records. Bootstrap policy requires
local scope, denies unsafe context flags, and fails closed.

Bootstrap policy must deny external calls, package installation, production
secret creation, production authentication, full-autonomy enablement, code
loading, tool or shell execution, hard delete, and source mutation. Controlled
seed execution is blocked unless explicitly enabled for safe local defaults.

## Fail Closed

Policy failures fail closed. If the policy engine is unavailable, malformed, or
returns an invalid response, AION Brain returns a deny decision with reason
`policy_engine_unavailable`.

## Event Reaction Policy

Event Reaction Router operations use generic event policy actions only.
Subscription create/read/disable controls who can define or pause reactions.
`event.dispatch` gates manual or opt-in intake dispatch. `event.reaction.run`
gates every matched reaction action before any target service is called.

Dry-run dispatch and low-risk reaction evaluation are allowed only when policy
permits the actor and scope. Controlled actions still pass autonomy, risk, and
approval gates. High and critical risk reactions require approval through the
existing elevated-risk policy path.

Dead-letter read, resolve, and replay are policy-gated. Replay is bounded,
dry-run by default, and fails closed if the original event or router is
unavailable. The core policy vocabulary stays domain-neutral and does not add
target-specific vertical verbs.

## Identity and Scope Policy

Identity and workspace operations are generic Brain control-plane actions.
Actor, workspace, membership, permission, and scope APIs all pass through the
policy adapter before persistence or scope resolution.

Policy input enrichment adds request-time actor context, roles, permissions,
resolved security scope, workspace ID, and dev-mode state to `PolicyRequest`.
Modules never self-authorize identity, workspace, membership, permission, or
scope decisions.

Development owner context may authorize local setup when `AION_ENV=development`
and dev auth is enabled. Outside that dev-mode path, identity reads require
matching generic permissions and identity mutations require owner or admin
context. Scope resolution applies deny-wins permission semantics, blocks
disabled actors, and constrains archived workspaces.

Production authentication policies will be introduced outside Brain core later.
The current policy vocabulary remains generic and does not include OAuth, SSO,
tenant billing, or vertical-domain permission names.

## External Connector Policy

AION-106 adds connector boundary design only. No connector policy action grants
runtime access, egress, ingress promotion, credential access, activation, or
execution.

Future connector operations must use generic policy actions, fail closed, and
remain subordinate to dry-run action authorization, operator review,
audit/provenance, prompt/output governance, secret handling, sandbox posture,
and release gates. Connector metadata must not create policy actions
dynamically, grant scopes, self-authorize, bypass policy, or turn capability
claims into active permissions.

Connector egress remains disabled by default. Future egress requires policy
approval before any call preview can become a runtime call. Connector ingress
must also be policy-aware before external data can be promoted into trusted
Brain records.

## Operator Action Write-Path Policy

AION-107 adds write-path architecture design only. No policy action grants
write execution, tool execution, controlled handoff execution, external calls,
activation, approval bypass, policy bypass, audit bypass, or hard delete.

Future write-path operations must obtain a current policy decision and a
current dry-run action authorization decision after production auth, role
mapping, approval workflow, connector/target boundary, rollback design,
audit/provenance, and release gates are complete. Approval records, local
roles, static console controls, connector metadata, and model output cannot
self-authorize writes.

## Evidence Policy

Evidence access uses generic `evidence.*` actions. `evidence.read` and
`evidence.search` are low-risk actions when scope permits. `evidence.create`
is allowed for low and medium risk when policy permits. `evidence.link` is a
medium-risk relation write. `evidence.ground` is allowed for low and medium
risk because it creates deterministic grounding claims without model calls.
`evidence.delete` requires approval.

Restricted evidence requires explicit `evidence.restricted.read` permission.
Policy failures fail closed. Evidence policy does not fetch URLs, parse files,
run OCR, invoke external storage SDKs, call model providers, or encode
domain-specific evidence rules.

## Execution Policy

Execution uses generic policy actions only. `plan.execute` gates the run,
`execution.step` gates each step, and `approval.request` records approval
checkpoints. `dry_run` execution is allowed for low and medium risk when policy
allows it. `controlled` execution still requires explicit policy evaluation.

High and critical risks require approval. Unknown execution modes and unknown
risks are denied. Capability invocation remains governed by `capability.invoke`
and cannot self-authorize inside a module.

## Risk, Guardrail, and Approval Policy

Risk, guardrail, and approval control-plane actions stay generic:

- `risk.assess`
- `guardrail.rule.create`
- `guardrail.rule.read`
- `guardrail.rule.disable`
- `guardrail.evaluate`
- `approval.request.create`
- `approval.request.read`
- `approval.decision.create`
- `approval.request.cancel`
- `approval.expire`

`risk.assess`, `guardrail.rule.read`, `guardrail.evaluate`,
`approval.request.read`, and `approval.expire` are low-risk control-plane
actions when scope permits. Guardrail creation, guardrail disabling, approval
creation, approval decisions, and approval cancellation require explicit policy
evaluation.

Risk and guardrails fail closed. Critical generic risk is blocked by default at
the guardrail layer, while high generic risk requires approval when approval is
absent. Approval records do not self-authorize execution. A later execution,
model, workflow, task, skill, module, or MCP request must still pass policy and
present approval evidence.

## Runtime Policy

Module runtime registration is gated by `module.runtime.register` and requires
medium-risk approval. Runtime reads use `module.runtime.read`, and health
checks use `module.runtime.health_check`. Capability-to-runtime binding is
gated by `capability.bind_runtime`.

Capability invocation is still generic `capability.invoke`. Dry-run invocation
is allowed for low and medium risk when policy allows it. Controlled invocation
is allowed for low risk, and medium controlled invocation requires approval.
High and critical invocation require approval. Unknown runtime types, unknown
risks, and unknown modes are denied.

HTTP runtime type is not executable in v0.1. MCP is an optional
disabled-by-default adapter that can dry-run mapped capabilities safely and can
perform controlled fake in-memory invocation only when explicitly enabled for
tests or local demos. Policy and gateway behavior fail closed when runtime
configuration, transport permissions, or health is unsafe.

## MCP Policy

MCP uses generic policy actions only:

- `mcp.server.register`
- `mcp.server.read`
- `mcp.server.disable`
- `mcp.server.health_check`
- `mcp.tools.sync`
- `mcp.tool.invoke`
- `mcp.mapping.read`
- `mcp.mapping.write`

Read actions are low risk and require a development owner context or explicit
MCP read permission. Registration, disable, sync, and mapping writes require an
owner/admin context or explicit action permission plus approval.

`mcp.tool.invoke` in `dry_run` mode is allowed for low and medium risk without
external execution. `controlled` mode requires `mcp_enabled=true`, generic
`capability.invoke` permission, transport safety, and approval for medium,
high, or critical risk. HTTP and SSE transports require `mcp.network.use`.
Stdio transport requires `mcp.stdio.use`. Unknown MCP actions, missing
transport permission, disabled MCP, and policy failures fail closed.

MCP policy never delegates authorization to MCP servers and never encodes
domain-specific tool rules.

## Lifecycle Policy

Goal creation, reads, and transitions use generic `goal.*` actions. Cognitive
task creation, reads, transitions, and explicit runs use generic `task.*`
actions. Schedule metadata creation, reads, pause, and cancellation use generic
`schedule.*` actions.

`task.run` evaluates the requested `run_mode`. Low and medium risk dry-runs are
allowed when policy allows the action. Controlled task runs are allowed only
after policy evaluation and remain limited by the task runner. High and
critical task runs require approval. Unknown task run modes fail closed.

No lifecycle policy contains domain-specific actions. The policy engine governs
the generic control plane only.

## Memory Governance Policy

Memory governance uses generic policy actions:

- `memory.governance.rule.create`
- `memory.governance.rule.read`
- `memory.governance.rule.disable`
- `memory.governance.evaluate`
- `memory.decay.recompute`
- `memory.retention.sweep`
- `memory.forget.request`
- `memory.forget.execute`
- `memory.conflict.scan`
- `memory.conflict.read`
- `memory.conflict.resolve`
- `memory.compact`

Rule reads, governance evaluation, decay recompute, conflict scans, conflict
reads, retention dry-runs, and forget requests are allowed only after policy
evaluation. Forget requests are allowed to enter the governed approval workflow;
forget execution remains approval-aware and high-risk targets fail closed
without approval. Rule mutation, conflict resolution, retention mutation, and
compaction pass through policy and may require approval depending on risk and
settings.

Memory policy never treats vector recall, graph recall, or compacted summaries
as truth. Governance failures fail closed, and no governance policy contains
domain-specific actions.

## Reflection and Skill Policy

Reflection creation and reads use generic `reflection.*` actions. Skill
candidate creation, reads, and review updates use `skill.candidate.*` actions.
Skill promotion, reads, lifecycle transitions, and matching use generic
`skill.*` actions.

Read and match actions are low-risk allowed when policy permits. Candidate
creation can be low or medium risk. Candidate update, skill disable, and skill
archive require policy evaluation. `skill.promote` and `skill.activate` fail
closed for high and critical risk unless approval is present.

Skills are procedural memory data. Policy never grants a skill permission to
self-authorize, rewrite source code, execute shell commands, or call external
model providers.

## Visual and Observability Policy

Visual projection and observability use generic policy actions:

- `visual.map.read`
- `visual.telemetry.read`
- `visual.stream.read`
- `visual.snapshot.create`
- `visual.snapshot.read`
- `visual.timeline.read`
- `observability.read`
- `observability.event.create`

Visual and observability reads require generic `trace.read` or
`telemetry.read` permission. Stream reads require `visual.stream.read`.
Snapshot creation requires `visual.snapshot.create`. Internal development owner
context may record local observability events. Unknown visual actions and
policy failures fail closed. No visual policy contains frontend-specific or
domain-specific rules.

## Durable Workflow Policy

Durable workflow governance uses generic policy actions:

- `workflow.create`
- `workflow.read`
- `workflow.activate`
- `workflow.disable`
- `workflow.run`
- `workflow.pause`
- `workflow.resume`
- `workflow.cancel`
- `workflow.retry`
- `workflow.scheduler.tick`
- `workflow.worker.start_once`
- `workflow.engine.status`
- `workflow.temporal.status`
- `workflow.heartbeat.write`

Workflow reads and status checks are low-risk read actions. Definition writes,
state transitions, explicit scheduler ticks, explicit worker ticks, retries,
and heartbeat writes pass through policy. High and critical workflow risk
levels require approval before controlled execution. Unknown workflow actions
fail closed. No workflow policy contains domain-specific business rules.

## Replay and Regression Policy

Cognitive replay and regression use generic policy actions:

- `snapshot.create`
- `snapshot.read`
- `replay.run`
- `replay.read`
- `regression.case.create`
- `regression.case.read`
- `regression.case.update`
- `regression.run`
- `regression.read`
- `eval.adapter.run`

Snapshot reads require trace-read permission. Replay is local and
side-effect-free. Regression runs are local deterministic operations. The
evaluation adapter action allows only the local adapter in v0.1; Promptfoo and
Ragas fail closed until a future task explicitly enables them.

## Model Gateway Policy

Model gateway governance uses generic actions:

- `model.provider.register`
- `model.provider.read`
- `model.provider.disable`
- `model.provider.health_check`
- `model.profile.register`
- `model.profile.read`
- `model.profile.disable`
- `model.gateway.complete`
- `model.route`
- `model.complete`
- `model.usage.read`
- `model.budget.create`
- `model.budget.read`
- `model.budget.update`

The deterministic provider is allowed for local development. Provider and
profile reads are low-risk reads. Provider/profile registration and disabling
require owner or admin context. External `model.complete` is denied unless
`allow_external=true`, the model gateway is explicitly enabled, and the actor
has `model.external.use`. High and critical model completion requires approval.
Budget writes require owner or admin context. Unknown model actions, provider
types, risks, and policy failures fail closed.

## Attention Policy

Attention and working memory use generic policy actions:

- `attention.focus.create`
- `attention.focus.read`
- `attention.focus.update`
- `attention.signal.create`
- `attention.signal.read`
- `attention.decide`
- `attention.signal.update`
- `working_memory.write`
- `working_memory.read`
- `working_memory.delete`
- `interrupt.create`
- `interrupt.read`
- `interrupt.decide`
- `context.budget.allocate`

Focus read is scoped. Focus create/update requires actor context in scope.
Attention signal creation is allowed for internal Brain services and scoped
actors. Working memory read/write is scoped; delete requires scoped authority.
Context budget allocation is an internal Brain control-plane action. Unknown
attention actions fail closed. No attention policy contains domain-specific
priority rules.

## Autonomy Policy

Autonomy governance uses generic policy actions:

- `autonomy.profile.create`
- `autonomy.profile.read`
- `autonomy.profile.disable`
- `autonomy.run_level.set`
- `autonomy.run_level.read`
- `autonomy.run_level.end`
- `autonomy.delegation.create`
- `autonomy.delegation.read`
- `autonomy.delegation.revoke`
- `autonomy.decide`
- `autonomy.status.read`

Profile, run-level, delegation, status, and decision reads are low-risk read
actions when scoped. Profile creation, disabling, run-level changes,
delegation creation/revocation, and autonomy decisions must pass through the
policy engine. Unknown autonomy actions fail closed.

Autonomy policy remains generic. It does not contain vertical business rules
and does not grant modules permission to self-authorize. External models,
external tools, scheduler control, background workers, skill promotion, and
memory forgetting also require the Autonomy Governor's explicit profile gates.

## Cognitive Cycle Policy

Cognitive cycles use generic policy actions:

- `cycle.template.create`
- `cycle.template.read`
- `cycle.template.disable`
- `cycle.run`
- `cycle.read`
- `cycle.step.run`
- `cycle.status.read`
- `sleep_consolidation.run`
- `maintenance.run`

Template reads, run reads, status reads, manual dry-run cycle execution, and
step dry-runs are low-risk actions when scoped. Controlled cycle mode still
passes through policy, autonomy, risk, and approval checks. Controlled mode
requires approval by default.

Sleep consolidation and maintenance actions are coordinators over existing
Brain services. They do not self-authorize memory mutation, skill promotion,
external model calls, external tool calls, hard deletion, scheduler loops, or
domain-specific behavior. Policy failures fail closed, and the cycle run is
recorded as blocked or waiting for approval instead of executing steps.

## Command and Consistency Policy

The command consistency layer uses generic policy actions:

- `command.dispatch`
- `command.read`
- `command.cancel`
- `idempotency.read`
- `outbox.enqueue`
- `outbox.read`
- `outbox.process`
- `outbox.cancel`
- `inbox.receive`
- `inbox.read`
- `inbox.process`
- `processing_lease.acquire`
- `processing_lease.release`
- `consistency.check`
- `consistency.repair`

Dry-run command dispatch is allowed for low and medium risk when scoped.
Controlled high and critical risk dispatch requires approval. Outbox enqueue
and inbox receive are internal Brain service actions. Outbox processing is
manual and non-dry-run processing requires explicit configuration and
authorization. Consistency checks are read-like diagnostics; repair requires
owner/admin authority and is limited to safe state transitions.

Unknown command, idempotency, outbox, inbox, lease, and consistency actions
fail closed. The policy vocabulary remains generic and contains no vertical
business rules.

## API Support Policy

API hardening uses generic policy actions:

- `api.request.read`
- `api.openapi_hygiene.read`
- `api.error_codes.read`

Error code reads are low-risk. Request audit reads require an owner/admin,
developer owner, `trace.read`, or `api.request.read` permission. OpenAPI
hygiene reads require owner/admin or developer owner authority. Unknown API
support actions fail closed.

## Module Developer Policy

The Module Developer Kit uses generic policy actions:

- `module.package.submit`
- `module.package.read`
- `module.package.disable`
- `module.package.certify`
- `module.contract_test.run`
- `module.scaffold.create`
- `module.compatibility.check`

Package submission, certification, disable, scaffold generation, compatibility
checks, and contract tests all pass through policy and fail closed.

## Sandbox, Secret, and Connector Policy

Sandbox governance uses generic policy actions:

- `sandbox.profile.create`
- `sandbox.profile.read`
- `sandbox.profile.disable`
- `sandbox.profile.validate`
- `sandbox.run`
- `runtime_permission.grant`
- `runtime_permission.read`
- `runtime_permission.revoke`
- `secret_ref.create`
- `secret_ref.read`
- `secret_ref.disable`
- `secret_ref.rotate`
- `connector.create`
- `connector.read`
- `connector.disable`
- `connector.validate`

Sandbox profile reads and validation are scoped read-like actions. Dry-run
sandbox runs are allowed when scoped and policy permits. Controlled sandbox
runs fail closed in v0.1 unless execution is explicitly enabled and approval is
present. Runtime permission grants and revocations require owner/admin style
authority. Secret refs never return raw secret values. Connector validation is
metadata-only and does not connect to external systems.

Unknown sandbox, secret ref, runtime permission, and connector actions are
denied. The policy vocabulary remains generic and contains no vertical
business rules.

## Policy Catalog Governance

AION Brain owns a generic policy action catalog and permission matrix. The
catalog records known action types, default risk levels, required permissions,
role templates, policy simulations, policy test cases, coverage reports, bundle
exports, and OPA status checks.

Generic policy catalog actions:

- `policy.catalog.create`
- `policy.catalog.read`
- `policy.catalog.update`
- `policy.permission.create`
- `policy.permission.read`
- `policy.permission.update`
- `policy.role_template.create`
- `policy.role_template.read`
- `policy.role_template.update`
- `policy.simulate`
- `policy.test_case.create`
- `policy.test_case.read`
- `policy.test.run`
- `policy.coverage.read`
- `policy.bundle.export`
- `policy.opa.status`

Read actions are available to owner, admin, auditor, viewer, or specifically
permissioned actors. Create/update actions require owner/admin style authority.
Simulation, test runs, bundle export, and OPA status are governance actions for
owner/admin/auditor flows. Unknown policy catalog actions fail closed.

The Brain core catalog must not contain finance, trading, IT, legal,
healthcare, HR, procurement, or other vertical policy actions. Domain policy
catalogs may be added outside Brain core later.

## Scenario and Release Baseline Policy

The scenario harness uses generic policy actions:

- `scenario.create`
- `scenario.read`
- `scenario.disable`
- `scenario.run`
- `scenario.seed_defaults`
- `demo_fixture.read`
- `demo_fixture.load`
- `release_baseline.run`
- `release_baseline.read`

Scenario reads are scoped. Scenario creation, disabling, and default seeding
require owner or admin style authority. Dry-run scenario execution is allowed
for owner, admin, or operator style authority. Controlled scenario execution is
denied by default in v0.1 unless explicit configuration changes it.

Demo fixture reads and dry-run loads are generic local validation actions.
Release baseline runs require owner or admin style authority and combine
scenario results with quality gate summaries. Unknown scenario, fixture, or
release baseline actions fail closed.

## Versioning and Freeze Gate Policy

Generic versioning and freeze actions:

- `version.manifest.create`
- `version.manifest.read`
- `version.manifest.freeze`
- `version.feature.create`
- `version.feature.read`
- `version.feature.deprecate`
- `compatibility.matrix.generate`
- `compatibility.matrix.read`
- `migration.baseline.generate`
- `release.artifact.generate`
- `freeze_gate.run`
- `freeze_gate.read`
- `release.package.create`
- `release.package.read`
- `release.package.validate`
- `release.handoff.read`
- `sdk.compatibility.check`

Read and compatibility checks are low-risk scoped actions. Manifest creation,
feature mutation, compatibility generation, migration baseline generation,
release artifact generation, freeze gate runs, and release package creation are
governance actions. They must remain generic, metadata-only, local-first, and
policy-gated. Release package reads, validation reads, and handoff reads are
scoped read actions. Unknown versioning, freeze, or release package actions fail
closed.

## Local Backup and Restore Policy

Generic backup and restore-preview actions:

- `backup.create`
- `backup.read`
- `backup.validate`
- `backup.restore.preview`
- `backup.restore.apply`

Backup reads, validation, and restore preview are low-risk scoped actions.
Backup creation is a medium-risk local operation and requires policy approval in
the default OPA policy. Restore apply is a high-risk action and must have
approval present; AION v0.1 also disables restore apply by default at the
service layer.

Backup policy never authorizes direct database restore, cloud upload, raw secret
export, or domain-specific resource actions. Unknown backup actions fail closed.

## Security Baseline Policy

Generic local security baseline actions:

- `security.scan.run`
- `security.scan.read`
- `security.threat_model.create`
- `security.threat_model.read`
- `security.threat_model.update`
- `security.control.create`
- `security.control.read`
- `security.control.update`
- `security.hardening.run`
- `security.hardening.read`

Scan and hardening runs require owner, admin, or auditor style authority because
they inspect local posture. Scan, threat model, control, and hardening reads
also require owner, admin, or auditor style authority. Threat model and control
create/update actions require owner or admin authority.

Security baseline policy stays generic and local. Unknown security actions fail
closed, and external scanner integrations do not define Brain core policy.

## Runtime Configuration Policy

Generic runtime configuration actions:

- `runtime_config.profile.create`
- `runtime_config.profile.read`
- `runtime_config.profile.update`
- `runtime_config.feature_override.create`
- `runtime_config.feature_override.read`
- `runtime_config.feature_override.update`
- `runtime_config.snapshot.create`
- `runtime_config.snapshot.read`
- `runtime_config.validate`
- `runtime_config.status.read`
- `runtime_config.change.read`

Profile reads are available to owner, admin, auditor, and scoped viewer style
authority. Profile mutation and feature override mutation require owner or
admin style authority. Snapshot creation, validation, and status inspection are
policy-gated local governance actions.

Runtime configuration policy never authorizes raw secret storage, process
environment mutation, unsafe default enablement, or domain-specific config
logic. Unknown runtime configuration actions fail closed.

## Resilience Policy

Generic resilience actions:

- `resilience.status.read`
- `resilience.dependency.check`
- `resilience.dependency.read`
- `resilience.retry_policy.create`
- `resilience.retry_policy.read`
- `resilience.retry_policy.update`
- `resilience.circuit_breaker.create`
- `resilience.circuit_breaker.read`
- `resilience.circuit_breaker.update`
- `resilience.degraded.read`
- `resilience.degraded.resolve`
- `resilience.fault_rule.create`
- `resilience.fault_rule.read`
- `resilience.fault_rule.update`
- `resilience.test.run`
- `resilience.test.read`

Read actions are low-risk scoped control-plane reads. Retry policy and circuit
breaker mutations are medium-risk governance actions. Fault rule creation and
updates require development context and explicit authority because fault
injection must stay disabled by default. Resilience tests are deterministic and
local.

Resilience policy never authorizes background workers, external failover,
infrastructure repair, raw secret exposure, or domain-specific recovery logic.
Unknown resilience actions fail closed.

## Dialogue and Response Policy

Generic dialogue actions:

- `dialogue.session.create`
- `dialogue.session.read`
- `dialogue.session.update`
- `dialogue.message.create`
- `dialogue.message.read`
- `dialogue.message.delete`
- `dialogue.turn`
- `dialogue.clarification.create`
- `dialogue.clarification.read`
- `dialogue.clarification.update`
- `dialogue.response.compose`
- `dialogue.response.verify`
- `dialogue.response.deliver`
- `dialogue.feedback.create`
- `dialogue.feedback.read`
- `dialogue.memory_handoff`

Dialogue policy gates backend conversation state. It never authorizes frontend
rendering, provider chat object exposure, external delivery, or controlled
execution. `dialogue.turn` is denied when the request context attempts
controlled execution mode. `dialogue.memory_handoff` is medium-risk and remains
governance-bound because it can create durable recall artifacts.

Response policy stays generic. Existing `response.draft`, `response.verify`,
and `response.evaluate` actions apply to response draft and verification
behavior. Unknown dialogue or response actions fail closed.

Generic belief actions:

- `belief.claim.create`
- `belief.claim.read`
- `belief.claim.update`
- `belief.claim.delete`
- `belief.claim.extract`
- `belief.support.create`
- `belief.support.read`
- `belief.support.delete`
- `belief.contradiction.create`
- `belief.contradiction.read`
- `belief.contradiction.resolve`
- `belief.query`
- `belief.truth_maintenance.run`
- `belief.truth_maintenance.read`

Belief actions stay domain-neutral. Modules never self-authorize belief writes
or contradiction resolution. Truth maintenance is policy-gated and fails closed
when authorization is denied. Belief state is recall and working state for the
Brain; policy must not treat retrieved belief claims as external proof.

## Concept and Entity Policy

Generic concept actions:

- `concept.create`
- `concept.read`
- `concept.update`

Generic entity actions:

- `entity.create`
- `entity.read`
- `entity.update`
- `entity.delete`
- `entity.alias.create`
- `entity.alias.read`
- `entity.alias.delete`
- `entity.mention.create`
- `entity.mention.read`
- `entity.resolve`
- `entity.reference.create`
- `entity.reference.read`
- `entity.reference.delete`
- `entity.merge.propose`
- `entity.merge.read`
- `entity.merge.approve`
- `entity.split.propose`
- `entity.split.read`
- `entity.split.approve`
- `entity.extract_mentions`

Concept and entity read actions are low-risk scoped reads. Mention extraction
and dry-run resolution are allowed only through explicit requests and scope
checks. Creating missing entities during resolution requires entity creation
authorization. Merge and split approval require explicit approval and fail
closed when policy denies.

Policy must not treat entity references as truth, infer sensitive identity
attributes, authorize image-based identification, or allow domain-specific
entity actions in Brain core. Unknown concept and entity actions fail closed.

## Situation Policy

Generic situation actions:

- `situation.create`
- `situation.read`
- `situation.update`
- `situation.project`
- `situation.atom.create`
- `situation.atom.read`
- `situation.atom.update`
- `situation.atom.delete`
- `situation.transition.read`
- `situation.temporal_window.create`
- `situation.temporal_window.read`
- `situation.continuity.record`
- `situation.continuity.read`

Situation projection, atom writes, temporal windows, and continuity records are
policy-gated. Modules never self-authorize situation state. Dry-run projection
persists nothing. Unknown situation actions fail closed.

## Decision Policy

Generic decision actions:

- `decision.frame.create`
- `decision.frame.read`
- `decision.frame.update`
- `decision.option.create`
- `decision.option.read`
- `decision.option.update`
- `decision.utility_profile.create`
- `decision.utility_profile.read`
- `decision.utility_profile.update`
- `decision.evaluate`
- `decision.counterfactual.run`
- `decision.record.create`
- `decision.record.read`
- `decision.record.update`
- `decision.recommend`

Decision policy gates evaluation, counterfactual projection, and journal
records. Decision actions must not execute selected options and fail closed
through the policy boundary.

## Outcome Policy

Generic outcome actions:

- `outcome.create`
- `outcome.read`
- `outcome.update`
- `outcome.delete`
- `outcome.expected_effect.create`
- `outcome.expected_effect.read`
- `outcome.expected_effect.delete`
- `outcome.observed_effect.create`
- `outcome.observed_effect.read`
- `outcome.observed_effect.collect`
- `outcome.verify`
- `outcome.verification.read`
- `outcome.attribution.create`
- `outcome.attribution.read`
- `outcome.feedback.create`
- `outcome.feedback.read`
- `outcome.feedback.update`
- `outcome.learning_bridge`

Outcome policy gates expected-effect writes, observed-effect writes, outcome
records, deterministic verification, causal attribution, feedback, and the
learning bridge. Outcome failures fail closed at the policy boundary.

Completion is not verification. The policy model must not allow outcome
services to mutate source commands, workflows, decisions, memories, evidence,
beliefs, or situations. Unknown outcome actions are denied.

## Learning Synthesis Policy

Generic learning actions:

- `learning.experience.create`
- `learning.experience.read`
- `learning.experience.update`
- `learning.experience.delete`
- `learning.query`
- `learning.pattern.mine`
- `learning.pattern.read`
- `learning.lesson.create`
- `learning.lesson.read`
- `learning.lesson.update`
- `learning.synthesize`
- `learning.synthesis.read`
- `learning.skill_suggestion.create`
- `learning.skill_suggestion.read`
- `learning.skill_suggestion.update`
- `learning.skill_suggestion.convert`
- `learning.regression_suggestion.create`
- `learning.regression_suggestion.read`
- `learning.regression_suggestion.update`

Learning synthesis policy gates experience writes, pattern mining, lesson
creation, synthesis runs, and suggestion review. Policy failure fails closed.

Learning policy does not authorize automatic skill promotion, automatic
regression case creation, source code modification, external calls, or
domain-specific learning behavior in Brain core.

## Self Model Policy

Generic self-model actions:

- `self_model.read`
- `self_model.update`
- `self_model.describe`
- `self_model.capability_awareness.read`
- `self_model.capability_awareness.refresh`
- `self_model.limitation.create`
- `self_model.limitation.read`
- `self_model.limitation.update`
- `self_model.confidence.calibrate`
- `self_model.confidence.read`
- `self_model.assessment.run`
- `self_model.assessment.read`
- `self_model.introspection.create`
- `self_model.introspection.read`

Self-model policy gates descriptive profile reads, capability awareness,
limitation writes, deterministic confidence calibration, self-assessment, and
introspection snapshots. Policy failures fail closed.

Self-model actions must not execute capabilities, enable adapters, mutate
runtime configuration, promote skills, override autonomy, approve actions, or
add domain-specific behavior to Brain core.

## Explanation Policy

Generic explanation actions:

- `explanation.create`
- `explanation.read`
- `explanation.verify`
- `explanation.feedback.create`
- `explanation.feedback.read`
- `explanation.why_not`
- `explanation.trace_narrative.create`
- `explanation.trace_narrative.read`

Explanation policy gates every explanation, trace narrative, why-not answer,
verification, and feedback operation. Policy failures fail closed.

Explanation policy does not authorize hidden reasoning disclosure, raw prompt
export, secret exposure, provider payload disclosure, or domain-specific
business rules in Brain core.

## Grounding Policy

Generic grounding actions:

- `grounding.source.create`
- `grounding.source.read`
- `grounding.citation.create`
- `grounding.citation.read`
- `grounding.citation.delete`
- `grounding.map`
- `grounding.verify`
- `grounding.coverage.read`
- `grounding.query`
- `grounding.unsupported.read`

Grounding read and query actions are scope-gated. Source and citation creation
is allowed only for internal Brain services or actors with grounding write
permission in scope. Citation delete is soft-delete only and requires owner or
admin context. Grounding verification is allowed for internal Brain services,
owners, admins, and operators. Unknown grounding actions fail closed.

Grounding policy does not authorize invented citations, web search, LLM
citation extraction, hidden reasoning disclosure, raw prompt export, secret
exposure, or domain-specific citation rules.

## Prompt Governance Policy

Generic prompt actions:

- `prompt.template.create`
- `prompt.template.read`
- `prompt.template.update`
- `prompt.fragment.create`
- `prompt.fragment.read`
- `prompt.fragment.update`
- `prompt.compile`
- `prompt.packet.read`
- `prompt.packet.delete`
- `prompt.boundary.check`
- `prompt.injection.read`
- `prompt.preview`
- `prompt.manifest.create`
- `prompt.manifest.read`

Prompt template and fragment reads are scope-gated. Template and fragment
create/update operations require owner or admin context. Prompt compilation is
allowed only for internal Brain services or actors in scope. Prompt previews
must remain redacted, metadata-only, or hashes-only. Prompt packet reads return
metadata and redacted preview only. Prompt injection reads are owner, admin,
operator, or auditor operations. Unknown prompt actions fail closed.

Prompt policy does not authorize hidden reasoning disclosure, raw prompt
export, raw rendered prompt persistence, provider-specific prompt contracts,
external model calls, or domain-specific prompt packs.

## Model Output Governance Policy

Generic model output actions:

- `model_output.create`
- `model_output.read`
- `model_output.delete`
- `model_output.parse`
- `model_output.govern`
- `model_output.structured_validate`
- `model_output.response_candidate.create`
- `model_output.response_candidate.read`
- `model_output.response_candidate.update`
- `model_output.tool_intent.create`
- `model_output.tool_intent.read`
- `model_output.tool_intent.update`

Model output reads, segment reads, structured validation, response candidate
reads, and tool-intent reads are scope-gated. Creating model output records,
running governance, deleting records, creating or promoting response
candidates, and creating or rejecting tool intents require owner, admin,
operator, or internal Brain context. Unknown model output actions fail closed.

Policy does not authorize raw provider payload exposure, hidden reasoning
disclosure, raw prompt export, direct tool execution from model output, external
observability calls, or domain-specific output rules.

## Action Proposal Policy

Generic action proposal actions:

- `action_proposal.create`
- `action_proposal.read`
- `action_proposal.update`
- `action_proposal.delete`
- `action_proposal.review`
- `action_proposal.handoff`
- `action_proposal.blocker.read`
- `action_proposal.blocker.update`
- `action_proposal.tool_intent.review`
- `action_proposal.handoff.read`

Action proposal reads are scope-gated. Create is allowed for actors in scope or
internal Brain services. Update, archive, and delete require owner, admin, or
creator context. Review and dry-run handoff require owner, admin, or operator
context. Tool intent review requires owner, admin, or operator context.

Controlled handoff remains denied unless runtime configuration explicitly
enables controlled handoff and policy, risk, autonomy, sandbox, target, and
approval gates allow it. External target systems are denied. Unknown action
proposal actions fail closed.

Policy does not authorize model-generated tool execution, proposal
self-execution, external targets, approval bypass, autonomy bypass, or
domain-specific action rules.

## Run Supervision Policy

Generic run supervision actions:

- `run_supervision.create`
- `run_supervision.read`
- `run_supervision.update`
- `run_supervision.delete`
- `run_supervision.sample`
- `run_supervision.control.request`
- `run_supervision.control.read`
- `run_supervision.control.handoff`
- `run_supervision.timeout_policy.create`
- `run_supervision.timeout_policy.read`
- `run_supervision.timeout_policy.update`
- `run_supervision.compensation.create`
- `run_supervision.compensation.read`
- `run_supervision.compensation.update`
- `run_supervision.compensation.convert`
- `run_supervision.report.create`
- `run_supervision.report.read`

Run supervision reads are scope-gated. Create, sample, reports, and dry-run
control requests are allowed only for scoped actors or internal Brain services.
Archive, delete, timeout policy mutation, compensation approval, and
compensation conversion require the stricter owner, admin, operator, approval,
or internal-service path defined by the policy engine.

Controlled control handoff remains denied unless runtime configuration,
policy, risk, autonomy, target support, and approval gates allow it. Timeout
policy evaluation does not authorize auto-cancel. Compensation policy does not
authorize direct execution. Unknown run supervision actions fail closed.

## Notification and Alert Policy

Generic notification and alert actions:

- `notification.topic.create`
- `notification.topic.read`
- `notification.topic.update`
- `notification.subscription.create`
- `notification.subscription.read`
- `notification.subscription.update`
- `notification.publish`
- `notification.read`
- `notification.update`
- `alert.create`
- `alert.read`
- `alert.update`
- `escalation.policy.create`
- `escalation.policy.read`
- `escalation.policy.update`
- `escalation.evaluate`
- `escalation.read`
- `escalation.update`
- `notification.digest.create`
- `notification.digest.read`

Notification topic, subscription, notification, alert, escalation, and digest
reads are scope-gated. Publishing notifications, creating alerts, evaluating
escalations, and mutating local acknowledgement/resolution state require the
scoped actor, operator, admin, or internal Brain context allowed by policy.

Policy does not authorize external delivery, webhooks, email, SMS, chat
delivery, source-system remediation, automatic source resolution, raw prompt
disclosure, hidden reasoning disclosure, raw header export, secret export, or
domain-specific alert rules. Unknown notification and alert actions fail
closed.

## Scheduler Policy

Generic scheduler actions:

- `scheduler.schedule.create`
- `scheduler.schedule.read`
- `scheduler.schedule.update`
- `scheduler.schedule.delete`
- `scheduler.due_item.read`
- `scheduler.due_item.update`
- `scheduler.reminder.create`
- `scheduler.reminder.read`
- `scheduler.reminder.update`
- `scheduler.tick`
- `scheduler.policy.create`
- `scheduler.policy.read`
- `scheduler.policy.update`
- `scheduler.report.create`
- `scheduler.report.read`

Schedule reads, due item reads, reminder reads, and scheduler reports are
scope-gated. Schedule create, update, delete, reminder mutation, controlled
ticks, and schedule policy mutation require the scoped owner, admin, operator,
creator, or internal Brain context permitted by policy.

Tick dry-run is allowed only for scoped operators. Controlled tick may create
scheduler-owned records only. Scheduler policy does not authorize scheduled
target execution, external calendar integration, external delivery, approval
bypass, source mutation, or domain-specific scheduling. Unknown scheduler
actions fail closed.

## Incident Policy

Generic incident actions:

- `incident.signal.create`
- `incident.signal.read`
- `incident.signal.update`
- `incident.create`
- `incident.read`
- `incident.update`
- `incident.correlate`
- `incident.rule.create`
- `incident.rule.read`
- `incident.rule.update`
- `incident.root_cause.create`
- `incident.root_cause.read`
- `incident.root_cause.update`
- `incident.recovery_review.create`
- `incident.recovery_review.read`
- `incident.recovery_review.update`

Incident reads are scope-gated. Signal creation, incident creation,
correlation, root cause candidate creation, and recovery review creation
require scoped actors, operators, admins, or internal Brain services allowed by
policy. Dry-run correlation is the default safe posture. Controlled
correlation requires policy and autonomy gates.

Incident policy does not authorize external incident system calls, automatic
remediation, source record mutation, source acknowledgement, source
resolution, command execution, workflow execution, approval bypass, raw prompt
disclosure, hidden reasoning disclosure, raw header export, secret export, or
domain-specific incident logic. Unknown incident actions fail closed.

## Resource Registry Policy

Generic registry actions:

- `registry.resource.index`
- `registry.resource.read`
- `registry.resource.query`
- `registry.link.create`
- `registry.link.read`
- `registry.backlink.read`
- `registry.validation.run`
- `registry.validation.read`
- `registry.broken_reference.read`
- `registry.broken_reference.update`
- `registry.orphaned_resource.read`
- `registry.orphaned_resource.update`
- `registry.rebuild.run`
- `registry.rebuild.read`
- `registry.snapshot.create`
- `registry.snapshot.read`

Registry reads are scope-gated. Indexing, link creation, validation, rebuilds,
snapshot creation, and integrity finding updates require scoped actors,
operators, admins, or internal Brain services allowed by policy.

Registry policy does not authorize source record mutation, source repair,
source acknowledgement, source deletion, external calls, command execution,
workflow execution, approval bypass, raw prompt disclosure, hidden reasoning
disclosure, raw header export, secret export, or domain-specific resource
logic. Unknown registry actions fail closed.

## Data Lifecycle Policy

Generic lifecycle actions:

- `lifecycle.policy.create`
- `lifecycle.policy.read`
- `lifecycle.policy.update`
- `lifecycle.classify`
- `lifecycle.classification.read`
- `lifecycle.evaluate`
- `lifecycle.archive_candidate.create`
- `lifecycle.archive_candidate.read`
- `lifecycle.archive_candidate.update`
- `lifecycle.redaction_candidate.create`
- `lifecycle.redaction_candidate.read`
- `lifecycle.redaction_candidate.update`
- `lifecycle.purge_preview.create`
- `lifecycle.purge_preview.read`
- `lifecycle.review.create`
- `lifecycle.review.read`
- `lifecycle.report.create`
- `lifecycle.report.read`

Lifecycle reads are scope-gated. Lifecycle writes require scoped actors,
operators, admins, or internal Brain services allowed by policy. Policy
constraints require advisory-only behavior, source records not mutated, and
hard delete disabled.

Lifecycle policy does not authorize source record mutation, automatic archive,
automatic redaction, automatic purge, hard delete, external archive storage,
external service calls, command execution, workflow execution, approval bypass,
raw prompt disclosure, hidden reasoning disclosure, raw header export, secret
export, or domain-specific retention logic. Unknown lifecycle actions fail
closed.

## Extension Registry Policy

Generic extension actions:

- `extension.package.create`
- `extension.package.read`
- `extension.package.update`
- `extension.package.delete`
- `extension.manifest.validate`
- `extension.dependency.read`
- `extension.capability_declaration.read`
- `extension.compatibility.check`
- `extension.intake`
- `extension.review`
- `extension.install_plan.create`
- `extension.install_plan.read`
- `extension.install_plan.update`
- `extension.query`

Extension reads and queries are scope-gated. Intake, package mutation,
compatibility checks, reviews, and install-plan creation require scoped actors,
operators, admins, or internal Brain services allowed by policy.

Extension policy does not authorize code loading, package installation,
external source retrieval, dynamic route registration, capability activation,
policy action activation from manifests, command execution, workflow
execution, approval bypass, raw prompt disclosure, hidden reasoning disclosure,
raw header export, secret export, or domain-specific extension behavior.
Unknown extension actions fail closed.

## Module Binding Policy

Generic module binding actions:

- `module_slot.create`
- `module_slot.read`
- `module_slot.update`
- `module_slot.delete`
- `capability_binding.create`
- `capability_binding.read`
- `capability_binding.update`
- `module_binding.validate`
- `module_binding.conflict.read`
- `module_binding.conflict.update`
- `module_mount_plan.create`
- `module_mount_plan.read`
- `module_mount_plan.update`
- `route_binding_preview.create`
- `route_binding_preview.read`
- `module_binding.query`

Module slot and capability binding reads are scope-gated. Creation, mutation,
validation, mount-plan creation, route-preview creation, and conflict updates
require scoped actors, operators, admins, or internal Brain services allowed by
policy.

Module binding policy authorizes metadata operations only. It does not
authorize code loading, package installation, capability activation, dynamic
route registration, runtime configuration mutation, shell commands, external
calls, approval bypass, raw prompt disclosure, hidden reasoning disclosure,
raw header export, secret export, or domain-specific module logic. Unknown
module binding actions fail closed.

## Module Activation Policy

Generic module activation actions:

- `module_activation.request.create`
- `module_activation.request.read`
- `module_activation.request.update`
- `module_activation.request.delete`
- `module_activation.gate.run`
- `module_activation.gate.read`
- `module_activation.blocker.read`
- `module_activation.blocker.update`
- `module_activation.review.create`
- `module_activation.review.read`
- `module_activation.plan.create`
- `module_activation.plan.read`
- `module_activation.plan.update`
- `module_activation.query.read`
- `runtime.registration.preview.create`
- `runtime.registration.preview.read`

Module activation policy authorizes metadata operations only. It does not
authorize code loading, package installation, capability execution, runtime
route registration, runtime configuration mutation, shell commands, external
calls, approval bypass, source mutation, hidden reasoning disclosure, raw
prompt disclosure, raw header export, secret export, or domain-specific module
logic.

Activation execution and runtime registration remain disabled in AION-083.
Unsafe activation contexts fail closed.

## Module Mock Runtime Policy

Generic module mock runtime actions:

- `module_mock.profile.create`
- `module_mock.profile.read`
- `module_mock.profile.update`
- `module_mock.invoke`
- `module_mock.run.read`
- `module_mock.output.read`
- `module_mock.finding.read`
- `module_mock.finding.update`
- `module_mock.query`

Module mock runtime policy authorizes deterministic dry-run metadata only. It
permits synthetic profile creation, dry-run invocation records, synthetic output
reads, finding review, and aggregate queries. It does not authorize code
loading, package installation, activation, capability execution, source-record
mutation, dynamic route registration, shell commands, external calls, hidden
reasoning disclosure, raw prompt disclosure, raw header export, secret export,
or domain-specific module behavior.

Mock invocation outputs must remain synthetic and all execution flags remain
false. Unsafe mock runtime contexts fail closed.

## Capability Conformance Policy

Generic conformance actions:

- `conformance.profile.create`
- `conformance.profile.read`
- `conformance.profile.update`
- `conformance.test_vector.create`
- `conformance.test_vector.read`
- `conformance.test_vector.update`
- `conformance.run`
- `conformance.finding.read`
- `conformance.finding.update`
- `conformance.readiness.assess`
- `conformance.readiness.read`
- `conformance.query`

Conformance policy authorizes metadata and schema checks only. Requests that
imply code loading, package installation, activation, dynamic route
registration, capability execution, MCP calls, sandbox code execution, external
calls, or source-record mutation fail closed.

## Golden Path Policy

Generic golden path actions:

- `golden_path.scenario.create`
- `golden_path.scenario.read`
- `golden_path.fixture.create`
- `golden_path.fixture.read`
- `golden_path.run`
- `golden_path.run.read`
- `golden_path.assertion.evaluate`
- `golden_path.report.create`
- `golden_path.report.read`
- `golden_path.release_smoke.run`
- `golden_path.query`

Golden path reads, queries, assertion evaluation, report reads, and release
smoke are low-risk scoped actions. Scenario and fixture creation and scenario
runs require scoped actors, operators, admins, or internal Brain services
allowed by policy.

Golden path policy authorizes local deterministic scenario work only. Requests
that imply external calls, external model calls, tool execution, shell
execution, code generation, source-record mutation, approval bypass, autonomy
bypass, raw prompt disclosure, hidden reasoning disclosure, raw header export,
secret export, or domain-specific scenario logic fail closed.

## Release Candidate Policy

Generic release candidate actions:

- `release_candidate.create`
- `release_candidate.read`
- `release_candidate.update`
- `release_candidate.query`
- `release_candidate.matrix.create`
- `release_candidate.matrix.read`
- `release_candidate.matrix.update`
- `release_candidate.gate.run`
- `release_candidate.run.read`
- `release_candidate.finding.read`
- `release_candidate.finding.update`
- `release_candidate.evidence_pack.create`
- `release_candidate.evidence_pack.read`
- `release_candidate.report.create`
- `release_candidate.report.read`

Release candidate reads and queries are low-risk scoped actions. Matrix
creation, candidate creation, finding dismissal, evidence-pack creation,
report creation, and gate runs require scoped actors, operators, admins, or
internal Brain services allowed by policy.

RC policy authorizes local metadata and evidence aggregation only. Requests
that imply deployment, publishing, external calls, source mutation, source
record mutation outside RC-owned records, enabling disabled features, code
loading, full autonomy, raw prompt disclosure, hidden reasoning disclosure,
raw header export, secret export, or domain-specific release behavior fail
closed.

## Release Handoff Policy Note

AION-079 adds no new policy actions. Existing RC, bootstrap, golden path,
release, freeze, operator, contract registry, resource registry, extension,
module binding, and conformance actions remain authoritative for local release
handoff.

## Model Provider Hardening Actions

- `model_provider.profile.create`
- `model_provider.profile.read`
- `model_provider.profile.update`
- `model_provider.egress.preview`
- `model_provider.simulate`
- `model_provider.readiness.assess`
- `model_provider.blocker.read`
- `model_provider.blocker.update`
- `model_provider.query`

Provider hardening actions are generic. External provider calls, credential
storage, prompt transmission, model invocation, and tool execution remain
denied in AION-086.

## Operator Console Policy

AION-088 adds read-only Operator Console actions:

- `operator_console.view.read`
- `operator_console.workflow.read`
- `operator_console.audit.run`
- `operator_console.action.describe`
- `operator_console.query`

View, workflow, action-descriptor, and query actions are low-risk scoped reads.
The contract audit is a read-only local verification action for owners, admins,
operators, auditors, or actors with the explicit permission.

Policy must fail closed. Operator Console policy does not authorize runtime UI
creation, frontend package files, activation, execution, code loading, package
installation, dynamic route registration, external calls, raw prompt exposure,
hidden reasoning exposure, secret exposure, or policy bypass.

## Governed Operator Action Policy

AION-092 adds generic operator action policy verbs:

- `operator_action.request.create`
- `operator_action.request.read`
- `operator_action.request.update`
- `operator_action.preview.create`
- `operator_action.preview.read`
- `operator_action.blocker.read`
- `operator_action.blocker.update`
- `operator_action.review`
- `operator_action.query`

Read and query actions require scoped operator read access. Request creation,
preview creation, blocker updates, and review records require scoped operator
write access. Policy constraints remain `dry_run_only`, `no_execution`,
`no_external_calls`, and `no_activation`.

## Local Auth Design Policy

AION-093 adds no new policy action. It documents the future Operator Console
role model and access matrix only. ActorContext remains the current internal
context mechanism, and policy remains authoritative for backend access.

No production auth is implemented. No credentials are stored. No external
identity provider is integrated. No login endpoint is added. Future auth work
must bind role decisions to policy, audit, approval, autonomy, and redaction
gates before any runtime session or production identity integration exists.

## Local Auth Runtime Policy

AION-094 adds generic policy actions:

- `local_auth.roles.read`
- `local_auth.identity.simulate`
- `local_auth.console.filter`
- `local_auth.audit.run`
- `local_auth.status.read`

These actions are scoped to dev-only local auth simulation, read-only status,
role-aware console filtering, and local audit. Login, credential storage,
session creation, production auth, external identity integration, execution,
activation, and unknown local auth actions remain denied by default.

## Local Session Runtime Policy

AION-095 adds local session policy actions:

- `local_session.preview.create`
- `local_session.context.read`
- `local_session.status.read`
- `local_session.boundary.check`
- `local_session.audit.run`

These actions are scoped to dev-only read-only session previews. Production
auth, credential backing, token issuance, cookie issuance, persistence,
external identity integration, execution, activation, external calls, and
unknown local session actions remain denied by default.

## AION-096 Role Matrix Policy Actions

- `local_auth.role_matrix.read`
- `local_auth.role_matrix.audit`
- `local_auth.console.filter`

These actions are local/dev read-only controls. Unknown local auth actions,
production auth enablement, credential storage, session persistence, execution,
activation, and external calls remain denied by default.

## AION-097 Action Authorization Policy Actions

- `action_authorization.dry_run.authorize`
- `action_authorization.audit.run`
- `action_authorization.decision.read`

The authorize action is dry-run only and record-only. Policy denies any context
that requests writes, execution, activation, external calls, or non-dry-run
authorization.

## AION-098 Production Auth Architecture Policy

AION-098 adds no production auth runtime and no new policy action. It documents
the future provider boundary only. The recommended future path is
OIDC-compatible production auth, with reverse proxy auth as an optional
deployment pattern later.

`production_auth_enabled` remains false. No provider integration is added in
AION-098. No credentials, tokens, sessions, or cookies are created, stored,
issued, or accepted. Future production identity must not self-authorize Brain
actions; policy, audit, ActorContext, role mapping, and dry-run action
authorization remain authoritative.

## AION-099 Disabled Auth Runtime Policy

AION-099 adds auth runtime preview policy actions:

- `auth_runtime.status.read`
- `auth_runtime.mock_claims.preview`
- `auth_runtime.audit.run`

These actions are local/dev, read-only or preview-only controls. Policy denies
production auth enablement, login, logout, token issuance, cookie issuance,
session persistence, credential handling, external identity providers,
execution, activation, external calls, and unknown auth runtime actions.
## Connector Runtime Preview Actions

AION-108 adds scoped policy actions for disabled connector preview evidence:

- `connector_runtime.status.read`
- `connector_runtime.mock_manifest.validate`
- `connector_runtime.egress.preview`
- `connector_runtime.ingress.preview`
- `connector_runtime.audit.run`

These actions do not grant connector execution, external calls, credential
storage, token storage, route registration, module activation, or capability
activation. Unknown connector runtime actions fail closed.

## AION-109 Connector Review Policy Boundary

AION-109 does not add policy actions. It reviews the existing disabled
connector preview actions and freezes the requirement that future connector
implementation must pass policy review, no-external-call regression, operator
review, audit/provenance proof, and the connector pre-implementation gate.

## AION-113 Connector Credential Policy Actions

AION-113 registers only connector credential read/preview actions: boundary
read, lifecycle read, authorization read, readiness preview, redaction preview,
and status read. Future credential, token, OAuth/OIDC/SAML, and external
identity actions remain denied by the connector credential denial service.
AION-114 connector release gate policy: connector implementation remains denied
until a future ADR explicitly approves runtime scope and the release gate
evidence remains green. Policy runtime allow paths, external calls, storage
material access, sandbox execution, activation, and route registration are
release blockers.

## AION-115 Connector Platform Checkpoint Policy

AION-115 adds no new policy allow path. The connector platform checkpoint
keeps runtime allow paths, external calls, credential/token access, sandbox
execution, activation, route registration, tool execution, and write execution
denied until a future ADR and gate evidence explicitly change scope.

## AION-116 Connector Platform Stabilization Policy

AION-116 adds no new policy allow path. The connector platform stabilization
gate preserves the frozen connector baseline and keeps implementation approval
false. Runtime allow paths, external calls, credential/token access, sandbox
execution, activation, route registration, tool execution, write execution,
hard delete, and privileged bypass remain denied until a future ADR and
stabilization evidence explicitly change scope.

## AION-117 Platform Integration Policy

AION-117 adds no new policy allow path. The platform integration checkpoint
keeps operator write execution, connector implementation, production auth,
module activation, external calls, credential/token access, sandbox execution,
runtime route registration, tool execution, write execution, hard delete, and
privileged bypass denied until future ADRs and release gates explicitly change
scope.

## AION-118 Release Candidate Policy

AION-118 adds no new policy allow path. The release candidate gate records that
v0.2 planning remains blocked from runtime implementation until a future ADR
and implementation gate explicitly approve a narrower scope. Policy bypass,
audit bypass, privileged bypass, connector runtime execution, operator write
execution, production auth, module activation, external calls,
credential/token access, sandbox execution, and v0.2 release approval remain
no-go conditions.

## AION-119 v0.2 Planning Policy

AION-119 adds no new policy allow path. The v0.2 planning charter defines
future decision criteria and gate dependencies while keeping every runtime
approval false.

Any future v0.2 implementation work must add a scoped ADR, policy enforcement
model, no-go regression, audit/provenance evidence, rollback evidence, and
operator review evidence before an allow path can be considered.

## AION-120 v0.2 Planning Stabilization Policy

AION-120 adds no new policy allow path. The stabilization gate freezes backlog
governance and readiness scoring while keeping runtime implementation and
backlog implementation approval false.

Future v0.2 implementation work remains blocked until planning review, a scoped
ADR, scoped gate evidence, security review, rollback evidence, audit/provenance
evidence, operator review evidence, and no-go regression all pass.

## AION-121 v0.2 Readiness Final Review Policy

AION-121 adds no new policy allow path. The final readiness review closes
planning evidence while keeping runtime implementation, backlog implementation,
operator write execution, connector implementation, production auth, module
activation, external calls, credential/token access, sandbox execution,
release creation, tag creation, and privileged bypass denied.

Future v0.2 implementation work remains blocked until a scoped ADR, scoped
gate evidence, security review, rollback evidence, audit/provenance evidence,
operator review evidence, and no-go regression all pass.

## AION-122 v0.2 Implementation Kickoff Policy

AION-122 adds no new policy allow path. It defines the approval workflow that a
future implementation task must satisfy while keeping runtime implementation,
backlog implementation, approval workflow bypass, ADR dependency bypass, gate
dependency bypass, operator write execution, connector implementation,
production auth, module activation, external calls, credential/token access,
sandbox execution, release creation, tag creation, and privileged bypass
denied.

Future v0.2 implementation work remains blocked until a scoped request,
approval decision record, scoped ADR, scoped gate evidence, security review,
rollback evidence, audit/provenance evidence, operator review evidence, and
no-go regression all pass.

## AION-123 v0.2 Approval Workflow Stabilization Policy

AION-123 adds no new policy allow path. It stabilizes approval intake,
decision evidence, expiry, revocation, and dual-control review while keeping
runtime implementation, backlog implementation, approval workflow bypass, ADR
dependency bypass, gate dependency bypass, approval expiry bypass, approval
revocation bypass, dual-control bypass, operator write execution, connector
implementation, production auth, module activation, external calls,
credential/token access, sandbox execution, release creation, tag creation, and
privileged bypass denied.

Future v0.2 implementation work remains blocked until a scoped request,
approval decision record, scoped ADR, scoped gate evidence, security review,
rollback evidence, audit/provenance evidence, operator review evidence,
expiry and revocation evidence, dual-control evidence where required, and
no-go regression all pass.

## AION-124 v0.2 Workstream Intake Readiness Policy

AION-124 adds no new policy allow path. It stabilizes workstream intake,
approval record evidence, sequencing, readiness scoring, and rejection rules
while keeping runtime implementation, backlog implementation, workstream
implementation approval, approval workflow bypass, approval record missing,
ADR dependency bypass, gate dependency bypass, approval expiry bypass,
approval revocation bypass, dual-control bypass, operator write execution,
connector implementation, production auth, module activation, external calls,
credential/token access, sandbox execution, release creation, tag creation, and
privileged bypass denied.

Future v0.2 implementation work remains blocked until a scoped workstream
intake record, approval record, ADR, gate evidence, security review,
architecture review, operator review, rollback/audit evidence, expiry and
revocation status, sequencing evidence, and no-go regression all pass.
AION-125 preserves the policy model as a planning-only master freeze. The
policy posture is fail-closed for implementation approval, workstream
implementation approval, approval workflow bypass, missing approval records,
ADR or gate dependency bypass, expiry or revocation bypass, dual-control
bypass, external calls, credential/token storage, sandbox execution, operator
write execution, connector runtime, production auth, module activation,
package files, migrations, v0.2 tag creation, and v0.2 release creation.

## AION-126 Proposal Registry Policy

AION-126 keeps policy fail-closed while adding proposal registry review rules.
Policy treats proposal registry records and approval queue preview records as
planning evidence only. Missing evidence, duplicate unresolved proposals,
unsupported runtime capability requests, missing security review, missing
architecture review, missing operator review, missing rollback/audit evidence,
ADR dependency bypass, gate dependency bypass, approval workflow bypass,
approval record missing, and approval queue item approval are no-go conditions.
All implementation and runtime approvals remain false.

## AION-127 Proposal Registry Stabilization Policy

AION-127 keeps policy fail-closed while freezing the approval queue preview.
Policy treats stabilization records, candidate workstream evidence, lifecycle
matrix entries, and queue freeze entries as planning evidence only. Approval
queue item approval, proposal implementation approval, implementation approval,
workstream implementation approval, backlog implementation approval, approval
workflow bypass, missing approval records, ADR dependency bypass, gate
dependency bypass, approval expiry bypass, approval revocation bypass, and
dual-control bypass remain no-go conditions. All implementation and runtime
approvals remain false.

## AION-128 Planning Master Checkpoint Policy

AION-128 keeps policy fail-closed while consolidating AION-119 through
AION-127 into the planning master checkpoint. Policy treats planning master
checkpoint records, proposal governance baseline records, implementation lock
freeze records, approval queue baseline records, and evidence matrix entries
as planning evidence only. v0.2 tag creation, v0.2 release creation, approval
queue item approval, proposal implementation approval, implementation
approval, workstream implementation approval, backlog implementation approval,
approval workflow bypass, missing approval records, ADR dependency bypass,
gate dependency bypass, runtime enablement, external calls, credential/token
storage, sandbox execution, package files, migrations, and runtime API
execution routes remain no-go conditions.

## AION-129 Policy Gate

AION-129 promotes the v0.2 planning baseline into a final planning release gate
without changing policy enforcement. The no-go policy still blocks v0.2 tag
creation, v0.2 release creation, runtime implementation approval, proposal
implementation approval, approval queue item approval, approval workflow
bypass, missing approval records, ADR dependency bypass, gate dependency
bypass, production auth, connector runtime, operator write execution, module
activation, external calls, credential/token storage, sandbox execution,
package files, migrations, and runtime API execution routes.

## AION-130 Policy Handoff

AION-130 closes the v0.2 planning track without changing policy enforcement.
Policy still treats the proposal registry and approval queue as preview-only
evidence and blocks v0.2 tag creation, v0.2 release creation, runtime
implementation approval, proposal implementation approval, approval queue item
approval, approval workflow bypass, missing approval records, ADR dependency
bypass, gate dependency bypass, production auth, connector runtime, operator
write execution, module activation, external calls, credential/token storage,
sandbox execution, package files, migrations, and runtime API execution routes.

## AION-131 Request Pack Policy Boundary

AION-131 adds request-package review policy evidence without changing policy
enforcement. Policy still treats request packs, proposal templates, proposal
registry entries, and approval queue entries as preview-only unless a later
scoped task supplies explicit approval records, ADRs, gate evidence, security
review, architecture review, operator review, rollback/audit evidence, and
no-go regression evidence. Request package implementation approval, proposal
template implementation approval, approval evidence approval, proposal
implementation approval, approval queue item approval, runtime implementation
approval, v0.2 tag creation, and v0.2 release creation remain false.

## AION-132 Request Pack Stabilization Policy

AION-132 adds evidence completeness and submission freeze policy evidence
without changing policy enforcement. Policy still treats request packs,
proposal templates, proposal registry entries, approval queue entries, and
evidence completeness results as preview-only unless a later scoped task
supplies explicit approval records, ADRs, gate evidence, review evidence,
rollback/audit evidence, and no-go regression evidence. Request pack approval,
evidence completeness bypass, submission freeze bypass, proposal
implementation approval, approval queue item approval, runtime implementation
approval, v0.2 tag creation, and v0.2 release creation remain false.

## AION-133 Request Pack Final Review Policy

AION-133 adds request pack final review, evidence boundary closeout,
pre-approval submission, and request approval guard policy evidence without
changing policy enforcement. Policy still treats request packs, submissions,
proposal registry entries, approval queue entries, and reviewer evidence as
preview-only unless a later scoped task supplies explicit approval records,
ADRs, gate evidence, review evidence, rollback/audit evidence, and no-go
regression evidence. Request pack approval, submission approval, preapproval
gate bypass, proposal implementation approval, approval queue item approval,
runtime implementation approval, v0.2 tag creation, and v0.2 release creation
remain false.

## AION-134 Submission Registry Policy Boundary

AION-134 adds submission registry preview and pre-approval queue policy
evidence without changing policy enforcement. Policy still treats submission
registry records, pre-approval queue records, request packs, proposal registry
entries, approval queue entries, and reviewer evidence as preview-only unless a
later scoped task supplies explicit approval records, ADRs, gate evidence,
review evidence, rollback/audit evidence, and no-go regression evidence.
Preapproval queue item approval, request pack approval, submission approval,
proposal implementation approval, approval queue item approval, runtime
implementation approval, v0.2 tag creation, and v0.2 release creation remain
false.

## AION-135 Submission Registry Stabilization Policy

AION-135 keeps the submission registry and pre-approval queue in a preview-only
policy state. Policy evaluation must treat queue placement, reviewer evidence,
ADR dependencies, and gate dependencies as planning evidence only. Any attempt
to mark submission approval, request pack approval, preapproval queue item
approval, proposal implementation approval, workstream implementation approval,
backlog implementation approval, or runtime implementation approval as true is
a release blocker.

AION-136 extends the policy lock to review-board routing. Review board decision
approval, reviewer sign-off, routing readiness, ADR readiness, gate readiness,
and evidence readiness are policy inputs only; any attempt to set review board
decision approval, preapproval queue item approval, request pack approval,
submission approval, approval queue approval, proposal implementation approval,
workstream implementation approval, backlog implementation approval, or runtime
implementation approval to true is a release blocker.

## AION-137 Review Board Stabilization Policy

AION-137 freezes the same policy lock for review routing. Review board
stabilization, routing freeze, quorum evidence, reviewer sign-off, ADR
dependency evidence, gate dependency evidence, closeout checklist evidence, and
decision-readiness evidence are policy inputs only. Any attempt to mark review
board decision approval, routing decision approval, reviewer sign-off
implementation approval, preapproval queue item approval, request pack
approval, submission approval, approval queue item approval, proposal
implementation approval, workstream implementation approval, backlog
implementation approval, or runtime implementation approval as true is a
release blocker.

## AION-138 Decision Package Policy

AION-138 extends the policy lock to the decision package preview. Decision
package completeness, approval-readiness evidence, runtime decision boundary
state, evidence matrix rows, checklist evidence, ADR dependency evidence, and
gate dependency evidence are policy inputs only. Any attempt to mark decision
package approval, approval readiness approval, review board decision approval,
routing decision approval, reviewer sign-off implementation approval,
preapproval queue item approval, request pack approval, submission approval,
approval queue item approval, proposal implementation approval, workstream
implementation approval, backlog implementation approval, or runtime
implementation approval as true is a release blocker.

## AION-139 Decision Package Stabilization Policy

AION-139 extends the policy lock to decision package stabilization and runtime
decision closeout. Stabilization, approval-readiness freeze, runtime decision
closeout, evidence baseline, status summary, ADR dependency evidence, and gate
dependency evidence are policy inputs only. Any attempt to mark runtime
decision readiness approval, decision package approval, approval readiness
approval, review board decision approval, routing decision approval, reviewer
sign-off implementation approval, preapproval queue item approval, request pack
approval, submission approval, approval queue item approval, proposal
implementation approval, workstream implementation approval, backlog
implementation approval, or runtime implementation approval as true is a
release blocker.
