# AGENTS.md

Instructions for future Codex runs in this repository:

- Build only AION Brain Core.
- Keep the Brain domain-neutral.
- No finance, trading, IT, legal, health, HR, procurement, or vertical workflow logic.
- Use adapter boundaries for every external system.
- Do not hard-code a model provider.
- Do not expose framework-specific objects through public AION APIs.
- Add tests for every new behavior.
- Update docs when architecture changes.
- Run pytest, ruff, and mypy before finishing.
- Prefer small files, typed contracts, and clear subsystem boundaries.
- Register new services through `KernelContainer`.
- Routes must not instantiate repositories, adapters, or service graphs.
- Keep public contracts provider-neutral.
- New routes must define tags.
- New routes must use AION contracts for request and response models.
- New exceptions must map to `AIONErrorResponse`.
- Never expose raw exceptions, provider SDK objects, SQLAlchemy rows, raw SQL, raw headers, or stack traces.
- Preserve `/health` response compatibility.
- Add tests for error behavior on new API routes.
- Run the kernel boundary check before completing architecture tasks.
- Never add domain directories under `src/aion_brain`.
- Keep `packages/aion-sdk-python` separate from the Brain API package.
- The Python SDK must not import `aion_brain`, database drivers, provider SDKs,
  or domain modules.
- `aionctl` must call AION only through the SDK client.
- SDK and CLI tests must not require Docker or live network services.
- Module developer kit work must remain generic and contract-only.
- Never execute module package code during certification tests.
- Future modules must pass Module Developer Kit certification before runtime registration.
- Never store raw secrets in Brain contracts, tests, fixtures, logs, telemetry, or docs.
- Never add Docker execution without an explicit future task.
- Never add subprocess execution in sandbox code.
- Connectors are metadata-only in v0.1 and must not call external systems.
- Disabled connector runtime work may add mock-only status, manifest
  validation, preview, blocker, and audit evidence, but it must keep runtime,
  external calls, credentials, token storage, activation, and route registration
  disabled by default.
- Connector simulator work may add deterministic synthetic dry-run, replay,
  policy readiness, audit, SDK, CLI, docs, examples, and static console
  evidence only. It must not enable runtime, external calls, credentials,
  tokens, activation, route registration, tool execution, write execution, or
  trusted connector ingress.
- Connector policy catalog work may add read-only catalog, role matrix, dry-run
  gate, denial rules, traceability, audit, SDK, CLI, docs, examples, and static
  console evidence only. It must not enable runtime allow paths, external
  calls, credentials, tokens, activation, route registration, tool execution,
  write execution, production auth, package files, lockfiles, migrations, or
  frontend dependencies.
- Connector sandbox design work may add design boundary, isolation model,
  capability rules, readiness preview, denials, audit, provenance, SDK, CLI,
  docs, examples, and static console evidence only. It must not enable real
  sandbox execution, filesystem access, network access, credentials, tokens,
  process spawning, dynamic imports, package installation, connector
  activation, route registration, tool execution, write execution, production
  auth, package files, lockfiles, migrations, or frontend dependencies.
- Post-v0.1 release candidate work is evidence-only. It may add release docs,
  examples, static console demo data, tests, and local gate scripts, but it must
  not create a release, create a v0.2 tag, move `aion-v0.1.0`, enable runtime
  implementation, approve connector implementation, approve production auth,
  approve module activation, approve operator write execution, call external
  services, store credentials or tokens, enable sandbox execution, add package
  files, add migrations, add API runtime routes, or add SDK/CLI implementations.
- Production-auth stabilization authorization work may create governance
  transactions for future disabled-core hardening only. It must not modify
  production-auth source, config, kernel wiring, API routes, SDK/CLI source,
  package files, lockfiles, migrations, runtime auth enablement, credentials,
  tokens, provider SDKs, external calls, v0.2 tags, or releases.
- Production-auth request boundary authorization work may close consumed
  production-auth stabilization authorization and create a scoped future
  request-identity-boundary authorization only. It must not modify
  production-auth implementation source, contracts, config, kernel wiring, API
  routes, SDK/CLI source, package files, lockfiles, migrations, runtime auth
  enablement, credentials, tokens, sessions, cookies, provider SDKs, external
  calls, v0.2 tags, or releases.
- Disabled production-auth request identity boundary work may add internal
  production-auth request identity contracts, disabled verifier wiring,
  observe-only middleware, anonymous request-state evidence, diagnostics, docs,
  examples, static console evidence, and local gates only. It must keep
  `production_auth_request_boundary_enabled=false` by default, never trust
  `RequestContext.actor_id`, never parse Authorization headers or cookies, add
  no public route, add no SDK/CLI runtime surface, and keep runtime auth,
  identity verification, authenticated requests, providers, packages,
  migrations, v0.2 tags, and v0.2 releases disabled or absent.
- v0.2 planning charter work is planning-only. It may add charter docs,
  decision frameworks, workstream maps, ADR requirements, gate dependency
  matrices, synthetic examples, static console demo data, tests, and local
  planning scripts, but it must not approve implementation, create a release,
  create a v0.2 tag, move `aion-v0.1.0`, enable production auth, enable
  connector runtime, enable operator write execution, enable module activation,
  call external services, store credentials or tokens, enable sandbox
  execution, add package files, add migrations, add API runtime routes, or add
  SDK/CLI implementations.
- Do not add domain-specific connectors in Brain core.
- Policy actions and permissions must remain generic dotted lowercase names.
- Keep policy simulations side-effect-free; they must never execute target actions.
- Policy tests must not require live OPA or external network services.
- Conformance harness work must remain metadata/schema-only.
- Conformance must never load package code, install packages, activate
  extensions, invoke capabilities, call MCP, call sandbox runtimes, register
  dynamic routes, or call external services.
- Readiness assessments may block future activation, but must not activate
  anything in v0.1.
- Bootstrap work must remain local first-run readiness only.
- Bootstrap and setup doctor code must never install packages, create
  production credentials, provision cloud resources, call external services,
  enable external providers, enable full autonomy, load code, execute tools,
  hard-delete records, mutate source code, or add domain-specific setup logic.
- Setup findings are operator-visible records, not automatic remediation.
- Before completing any task, run the narrow tests for the changed area.
- For architecture tasks, run boundary check and no-domain-drift.
- For API tasks, run OpenAPI hygiene.
- For policy tasks, run policy coverage.
- For SDK tasks, run SDK tests.
- Never skip failures silently.
- Report exact commands and failures.
- New major subsystems should add or update a generic scenario.
- Scenario fixtures must remain generic and secret-free.
- No domain scenario packs belong in Brain core.
- Release baseline must stay dry-run by default.
- Version manifests, compatibility matrices, migration baselines, release
  artifact manifests, and freeze gate runs must stay local and metadata-only.
- Freeze gate services must not call shell scripts, Docker, external network
  services, optional adapters, or domain modules.
- New versioning features must use generic feature keys and must pass the
  no-domain-drift rule before freezing.
- Release packages must stay local and deterministic.
- Release packaging API code must not call subprocess, Docker, package
  registries, cloud storage, external observability services, or external
  network services.
- Release package artifacts must never include `.env` files, cache
  directories, raw secrets, generated virtualenvs, `.aion_objects`, or
  `.aion_indexes`.
- SBOM output is a placeholder until a future task adds a real SBOM adapter.
- Release handoff reports must list local verification commands and known
  limits without enabling full autonomy or domain modules.
- Local backups must stay application-level and JSON/JSONL based.
- Backup API code must not call `pg_dump`, direct database restore commands,
  cloud storage clients, external network services, or subprocess execution.
- Restore preview must remain dry-run and conflict-aware; restore apply stays
  disabled by default unless an explicit future task changes the setting and
  adds application-level writers.
- Backup artifacts must never include raw secrets, `.env` files, raw headers,
  cache directories, generated virtualenvs, `.aion_objects`, or `.aion_indexes`.
- New major subsystems should include generic benchmark hooks where practical.
- Benchmarks must stay local, deterministic, side-effect-safe, and domain-neutral.
- Do not add cloud load tests or external provider calls to performance code.
- Do not store request bodies or response bodies in performance samples.
- Do not add domain-specific benchmark suites.
- Security tasks must avoid external scanners unless an explicit future task
  adds an adapter for them.
- Security baseline logic must stay generic and Brain-only.
- Do not add domain compliance logic to Brain core.
- Do not store raw secrets in findings, reports, logs, telemetry, tests, or docs.
- Do not expose raw secret matches in API responses or release artifacts.
- Runtime config must never store raw secrets.
- Do not mutate process environment variables from API routes.
- Feature overrides must not enable unsafe defaults.
- Runtime config keys must remain generic and Brain-level.
- Resilience retry policies must use bounded max attempts and must not create
  background retry loops unless a future task explicitly adds a worker.
- Fault injection must stay disabled by default and local-only.
- Degraded mode must record fallback posture and must not auto-remediate.
- Optional adapter fallback must be explicit, documented, and contract-shaped.
- Do not add cloud failover logic, deployment repair logic, or external
  remediation calls to Brain core resilience code.
- Major state-changing services should record audit entries through the audit
  integrity ledger when practical.
- Audit payloads must be redacted before storage and export.
- Never store chain-of-thought or hidden reasoning in audit payloads.
- Never hard-delete audit entries.
- Audit corrections, redactions, and provenance updates must be append-only.
- Operator APIs must not execute actions, approve requests, process queues,
  mutate memory, invoke capabilities, change runtime config, or remediate issues.
- Operator action recommendations must stay generic and domain-neutral.
- Operator acknowledgements must not resolve source issues.
- Operator Console view models are read-only backend contracts; they are not a
  runtime UI.
- Operator Console work must preserve no raw prompt exposure, no hidden
  reasoning exposure, no secret exposure, no activation, and no execution.
- Operator Console actions are descriptors only unless a later explicit
  milestone adds governed write behavior.
- Operator Console contract audits must fail closed when frontend package or
  config files appear in the scanned tree.
- Future UI work must consume Operator contracts rather than querying subsystem
  internals directly.
- Static Operator Console prototype work must remain dependency-free until UI
  architecture is explicitly approved.
- Static console work must not add package manager files, external scripts,
  external stylesheets, framework assets, or a build step.
- Static console work must remain read-only and must not activate modules,
  activate capabilities, execute tools, enable external calls, mutate runtime
  config, or imply production auth.
- Static console rendering must not expose raw prompts, hidden reasoning,
  chain-of-thought, raw headers, provider payloads, credentials, or secrets.
- Module lifecycle dashboard work must remain read-only.
- Do not add activation buttons or activation actions to the module dashboard.
- Expected module blockers must remain visible and must not be hidden.
- Generic Knowledge trail data must remain synthetic and metadata-only.
- Module dashboard work must not add frontend dependencies, package manager
  files, API routes, SDK resources, CLI commands, migrations, code loading,
  runtime registration, external calls, or domain-specific module logic.
- Dialogue work must remain backend contract work unless a future task
  explicitly asks for UI.
- Dialogue APIs must not expose provider-specific chat objects, frontend state,
  raw prompts, hidden reasoning, chain-of-thought, raw headers, or secrets.
- Dialogue turns must not perform controlled execution or external message
  delivery in v0.1.
- Response composition must stay deterministic and AION-contract-shaped until
  a future task explicitly adds model-backed response generation behind an
  adapter.
- Dialogue memory handoff must store summaries and references only, remain
  policy-gated, and avoid raw sensitive content.
- Belief state must remain generic, explicit, scoped, and policy-gated.
- Belief claims are not absolute truth; reasoning must see belief status,
  confidence, supports, contradictions, and constraints.
- Truth maintenance must stay deterministic and local in v0.1. Do not call
  external fact-checking systems, model providers, web search, or domain
  knowledge bases from belief services.
- Entity references are not beliefs and are not truth. They are canonical
  pointers that other AION systems may reference.
- Do not add domain-specific entity types, concept types, or ontologies to
  Brain core.
- Do not auto-merge entities. Use explicit merge proposals and approvals.
- Do not hard-delete entities, aliases, mentions, or reference links.
- Do not infer sensitive identity attributes or use image-based identification
  in entity resolution.
- Decision services must never execute selected options.
- Counterfactual services must never mutate source records.
- Utility scoring must remain generic and domain-neutral.
- Do not add domain-specific decision weights or option types to Brain core.
- Outcome verification must remain deterministic, local, and generic.
- Preferences must never override policy.
- Preferences must never bypass approval.
- Preferences must never expand autonomy.
- Preferences must never override runtime configuration, sandbox limits, or
  capability limits.
- Learned preferences must remain candidates until confirmed.
- Do not store hidden prompts, chain-of-thought, raw headers, or raw secrets in
  instruction, preference, style, conflict, or resolution records.
- Completion is not verification; source records must not be mutated by
  outcome services.
- Outcome feedback must not auto-promote skills, execute remediation, call
  external services, or add domain-specific learning logic.
- Experience ledger entries are generic learning inputs and must not replace
  source record truth.
- Pattern mining must remain deterministic and local in v0.1.
- Learning synthesis must not auto-promote skills, create active procedures,
  create regression cases, write source code, retry work, call model providers,
  call external services, or add domain-specific learning logic.
- Use Adaptive Intelligence Orchestration Nexus as the official meaning of
  AION, and Adaptive Intelligence Orchestration Nexus Operating System as the
  official meaning of AION OS.
- Self-description must not claim sentience, personality, unavailable
  features, production readiness, full autonomy, or domain expertise.
- Capability claims must come from awareness records, kernel diagnostics,
  configuration, or other governed AION contracts.
- Confidence disclosures must be explicit when grounding is weak, confidence
  is low, approval is required, or a capability is dry-run only.
- Explanations must be deterministic public narratives over observable AION
  records, not chain-of-thought or hidden reasoning.
- Explanation services must redact raw prompts, provider payload markers, raw
  headers, and secret-like keys before persistence or API return.
- Why-not answers and trace narratives must stay generic, policy-gated,
  frontend-agnostic, and domain-neutral.
- Do not invent citations or source references.
- Do not treat memory recall as primary evidence.
- Grounding must not expose chain-of-thought, hidden reasoning, raw prompts,
  raw headers, provider payloads, or secrets.
- Citation logic must remain generic, deterministic, local, and domain-neutral.
- Grounding must not call web search, model providers, or LLM citation
  extraction paths in v0.1.
- Prompt packets must remain provider-neutral and AION-contract-shaped.
- Retrieved context must be treated as untrusted unless another governed AION
  contract explicitly says otherwise.
- Memory recall in prompt packets must be labeled as memory recall.
- Do not persist raw rendered prompts by default.
- Do not store hidden reasoning or chain-of-thought in prompt governance
  records.
- Do not expose raw prompts, raw headers, provider payloads, or raw secrets
  through prompt APIs, SDK helpers, CLI commands, telemetry, audit, or docs.
- Do not add provider-specific prompt contracts or domain prompt packs to
  Brain core.
- Model output governance must store raw output hashes and redacted output
  contracts, not raw provider payloads by default.
- Model output records, segments, candidates, tool intents, telemetry, SDK
  helpers, CLI commands, and operator items must not expose hidden reasoning,
  chain-of-thought, raw prompts, raw headers, or secrets.
- Model-suggested tool intents must be captured for review and must not execute
  in v0.1.
- Response candidates from model outputs are proposals only until policy and
  response verification allow promotion.
- Action proposals must never execute themselves.
- Tool intents from model output must never execute directly.
- Controlled action handoff must remain disabled by default.
- Action handoff targets must be governed AION systems only.
- Do not add external target systems in Brain core.
- Run supervision must not own execution semantics.
- Run supervision may observe, sample, report, and request; target subsystems
  remain authoritative for execution state.
- Control requests must be dry-run by default.
- Timeout policies must not auto-cancel in v0.1.
- Compensation plans must not execute themselves.
- Do not add domain-specific compensation logic in Brain core.
- Internal notifications must remain local-only in v0.1.
- Do not add email, SMS, webhook, Slack, Teams, push, or other external
  delivery paths to Brain core.
- Alerts and escalations must not remediate, retry, cancel, resume,
  acknowledge, resolve, or otherwise mutate their source records.
- Notification payloads, alert metadata, digests, telemetry, SDK helpers, and
  CLI commands must not expose hidden reasoning, chain-of-thought, raw prompts,
  raw headers, provider payloads, or secrets.
- Do not add domain-specific notification topics, alert types, escalation
  logic, digest recommendations, or operator runbooks in Brain core.
- Scheduler tasks must not start background workers.
- Schedules must not execute target actions directly.
- Tick runs must be deterministic and local.
- Reminders must not send external messages.
- Do not add external calendar integrations in Brain core.
- Incident correlation must remain local and generic.
- Incident signals may reference source records but must not mutate them.
- Dry-run correlation is the default posture.
- Root cause candidates are hypotheses, not truth.
- Recovery reviews must not execute remediation.
- Do not add external incident-management integrations in Brain core.
- Do not add domain-specific incident rules, runbooks, or remediation logic in
  Brain core.
- Data lifecycle management is advisory in v0.1.
- Lifecycle evaluation must not mutate source records.
- Lifecycle services must not execute archive, execute redaction, purge
  records, hard-delete records, call object storage, or call external services.
- Purge previews must keep `hard_delete_allowed=false`.
- Archive and redaction conversion may create action proposals only; it must
  not perform the action.
- Do not add domain-specific lifecycle policy, classification, retention,
  archive, redaction, or purge logic in Brain core.
- Contract Registry scans are inventory only. Do not mutate source records,
  generate code, repair interfaces, execute migration steps, or call external
  services from contract registry services, SDK helpers, CLI commands,
  telemetry, reports, or docs.
- Contract Registry payloads must stay redacted and domain-neutral. Do not
  expose hidden reasoning, chain-of-thought, raw prompts, raw headers, provider
  payloads, secrets, or domain-specific compatibility rules.
- Extension Registry intake is metadata only. Do not load code, install
  packages, clone or download sources, register dynamic routes, activate
  capabilities, create policy actions from manifests, call external services,
  or run shell commands from extension registry services, SDK helpers, CLI
  commands, telemetry, reports, or docs.
- Extension manifests, package records, compatibility checks, reviews, and
  install plans must stay redacted, generic, and non-executing. Install plans
  must keep `executable=false` and `execution_allowed=false` in v0.1.
- Module slots must remain metadata-only. Do not load extension code, install
  packages, activate modules, register dynamic routes, mutate runtime config,
  call external services, or run shell commands from module slot services, SDK
  helpers, CLI commands, telemetry, reports, or docs.
- Capability bindings must not activate capabilities, register active
  capability records, invoke module runtimes, bypass policy, bypass sandbox, or
  introduce domain-specific module logic.
- Mount plans must not execute. They must keep `executable=false` and
  `execution_allowed=false` in v0.1.
- Route previews must not register routes. They must keep
  `registration_allowed=false` in v0.1.
- Golden Path Scenario Harness runs must remain local, deterministic, and
  dry-run by default.
- Golden path fixtures must be synthetic and scenario-owned. Do not use real
  user data or production records as fixture payloads.
- Golden path runs may create scenario records, fixture records, run results,
  assertion results, reports, audit/provenance links, telemetry, notifications
  when requested, and operator recommendations for failures.
- Golden path runs must not bypass policy, autonomy, or approval gates.
- Golden path runs must not call external services, call model providers,
  execute tools, execute action proposals, execute handoffs in controlled mode
  by default, run real backups, run release packaging, hard-delete fixtures, or
  mutate non-scenario source records.
- Golden path scenarios and assertions must stay generic and must not encode
  domain-specific business workflows.
- Release Candidate Gate work must remain local and records-first. It may
  create release candidate records, verification matrices, gate runs,
  findings, redacted evidence packs, reports, audit/provenance links,
  telemetry, SDK calls, CLI commands, operator queues, and resource registry
  descriptors.
- Release Candidate Gate work must not deploy, publish, tag releases
  automatically, mutate source code, enable disabled runtime features, call
  external services, execute uncontrolled release packaging, expose raw
  prompts, expose hidden reasoning, expose secrets, or add domain-specific
  release logic.
- Release handoff docs must not claim production readiness.
- Demo fixtures must be synthetic.
- Demo scripts must not call external services.
- Demo scripts must not install packages.
- Runbooks must state disabled v0.1 boundaries.
- No domain-specific demo flows.
- No raw secrets in examples.
- AION-080 closes the v0.1 release baseline. Do not add a new core subsystem
  after AION-080 without explicit architecture review.
- v0.1 release closure must protect existing tests, lint, typecheck,
  no-domain-drift, boundary, policy, OpenAPI, docs, Docker config, RC, freeze,
  and release package gates.
- Release docs must not claim production readiness.
- Release scripts must not call external services.
- Release scripts must not install packages.
- Release scripts must not publish or deploy.
- AION v0.1 tag must not be created unless final verification is green.
- After AION-080/AION-081, do not add Brain core subsystems without
  architecture review.
- Modules must not modify Brain core.
- Module activation remains disabled.
- Module code loading remains disabled.
- AION-105 module activation design review is evidence-only. It must not add a
  plugin loader, package installer, dynamic module import, runtime route
  registration, capability activation, controlled execution, module writes, or
  privileged bypass.
- Future module activation work must pass
  `./scripts/module-activation-design-review.sh` and
  `./scripts/module-activation-no-go-regression.sh` before implementation.
- Module examples must be metadata-only.
- Do not add domain-specific module implementation to Brain core.
- Do not move aion-v0.1.0 tag during post-v0.1 planning.
- First module pack work must remain metadata-only.
- Generic Knowledge Intelligence examples must not execute code.
- Module pack demos must not call external services.
- Module pack fixtures must stay synthetic.
- Activation blockers are expected in v0.1.
- Do not add domain-specific workflow logic to module pack fixtures, demos, or
  docs.
- Module mock runtime work must remain deterministic, metadata-only, and
  synthetic-output-only.
- Module mock runtime must not load code, install packages, activate modules,
  execute capabilities, register routes, mutate runtime config, call external
  services, or add domain-specific module logic.
- Model provider hardening work must remain readiness-only. Provider profiles
  are not activation, prompt egress previews are not prompt transmission,
  provider simulations are not model calls, and readiness assessments are not
  provider enablement.
- Do not add provider SDKs, provider endpoints, API keys, credential commands,
  raw prompt storage, external model calls, model invocation, or tool execution
  to provider hardening work.
- Do not add frontend dependencies without explicit UI architecture approval.
- Operator console work must preserve policy, audit, and approval gates.
- Operator console must not expose raw prompts, hidden reasoning, or secrets.
- Operator console must not activate modules or capabilities.
- Operator console must not enable external model calls.
- Governed operator actions remain dry-run request, preview, blocker, and
  review records only.
- Operator action reviews must not execute.
- Operator action previews must keep execution, external calls, and activation
  disabled.
- Do not implement production auth without architecture approval.
- Do not add login endpoints in design-only tasks.
- Do not store credentials or session tokens.
- Do not integrate external identity providers without threat model and
  release gate.
- Static console remains local/read-only until auth implementation is approved.
- AION-094 local auth is dev-only simulation. It may shape ActorContext and
  console filtering for local development, but it must not authenticate real
  users, store credentials, create sessions, issue tokens, bypass policy, grant
  execution, grant activation, or enable external identity providers.
- AION-095 local sessions are read-only dev previews. They may carry synthetic
  identity context for console filtering, but they must not add login/logout,
  credentials, tokens, cookies, persistent sessions, writes, execution,
  activation, runtime registration, or external calls.
- AION-096 role filtering is visibility-only. It may hide or mark unavailable
  console views, sections, and descriptor-only actions, but forbidden actions
  and safety blockers must remain visible and no role may grant writes,
  execution, activation, hard delete, external calls, production auth, or
  credential storage.
- AION-097 dry-run action authorization may allow request, preview, or review
  records only. It must fail closed for unknown roles/actions, denied sessions,
  and policy denials, and it must not execute actions, activate modules, write
  target systems, call external services, or add auth credentials/sessions.
- AION-098 production auth architecture is design-only. It may document OIDC,
  SAML, reverse proxy auth, local enterprise SSO bridge, and future
  Passkey/WebAuthn options, but it must not add provider SDKs, login/logout
  routes, credentials, tokens, cookies, sessions, migrations, external identity
  calls, frontend package files, or production auth enablement.
- AION-099 disabled auth runtime is mock-only. It may add disabled status,
  mock-claims preview, and audit proof, but it must not add production auth,
  login/logout, provider callbacks, credential handling, token issuance, cookie
  issuance, persistent sessions, provider SDKs, migrations, external identity
  calls, frontend package files, execution, activation, or hard delete.
- AION-100 static console UI release gate is docs/scripts/static-checks only.
  It must not add frontend dependencies, build tooling, API routes, SDK
  resources, CLI commands, production auth, login/logout, credential fields,
  token or cookie storage, session persistence, provider calls, writes,
  execution, activation, external calls, or runtime registration.
- AION-101 operator platform checkpoint is evidence-only. It must pass
  `./scripts/operator-platform-checkpoint.sh` and must not add API routers, SDK
  resources, CLI commands, migrations, frontend dependencies, production auth,
  write controls, activation controls, execution controls, provider-call
  controls, external-call controls, or runtime registration.
- AION-102 operator platform stabilization is regression evidence only. It must
  pass `./scripts/operator-platform-regression.sh` and
  `./scripts/operator-platform-freeze-gate.sh`, and it must not add runtime
  subsystems, API routers, SDK resources, CLI commands, migrations, frontend
  dependencies, package installation, production auth, write controls,
  activation controls, execution controls, provider-call controls,
  external-call controls, or runtime registration.
- AION-103 static console UX refinement is static HTML/CSS/JS polish only. It
  must pass `./scripts/static-console-ux-check.sh` and must not add frontend
  dependencies, package files, build tooling, runtime subsystems, API routers,
  SDK resources, CLI commands, migrations, production auth, login/logout,
  credential controls, token or cookie issuance, session persistence, writes,
  activation, execution, provider-call controls, external-call controls, or
  runtime registration.
- AION-104 local auth prototype review is evidence-only. It must pass
  `./scripts/auth-prototype-review.sh` and
  `./scripts/auth-no-go-regression.sh`, and it must not add production auth,
  auth runtime enablement, login/logout, credentials, token issuance, cookie
  issuance, session persistence, external identity provider runtime, provider
  SDKs, package files, build tooling, API routers, SDK resources, CLI command
  implementations, migrations, writes, activation, execution, external calls,
  privileged bypass, or runtime registration.
- AION-105 module activation design review is evidence-only. It must pass
  `./scripts/module-activation-design-review.sh` and
  `./scripts/module-activation-no-go-regression.sh`, and it must not add a
  plugin loader, package installer, dynamic module import, runtime route
  registration, capability activation, controlled execution, module writes,
  policy bypass, audit bypass, or privileged bypass.
- AION-106 external connector boundary design is evidence-only. It must pass
  `./scripts/connector-boundary-design-check.sh` and
  `./scripts/connector-no-go-regression.sh`, and it must not add connector
  runtime, network clients, connector SDKs, provider SDKs, credentials, token
  storage, external calls, dynamic routes, production auth, login/logout,
  package files, migrations, API routers, SDK resources, CLI command
  implementations, activation, execution, policy bypass, audit bypass, or
  privileged bypass.
- AION-107 operator action write-path architecture is design-only. It must pass
  `./scripts/operator-action-write-path-design-check.sh` and
  `./scripts/operator-action-write-path-no-go-regression.sh`, and it must not
  add write execution, tool execution, action proposal execution, controlled
  handoff execution, connector runtime, network clients, external calls,
  production auth, login/logout, credentials, tokens, cookies, persisted
  sessions, package files, migrations, API routers, SDK resources, CLI command
  implementations, activation, policy bypass, audit bypass, approval bypass,
  hard delete, or privileged bypass.
- AION-109 connector runtime review is evidence-only. It must pass
  `./scripts/connector-runtime-review.sh` and
  `./scripts/connector-runtime-no-external-call-regression.sh`, and it must not
  add connector runtime implementation, external calls, network clients,
  connector/provider SDKs, credentials, token storage, OAuth/OIDC/SAML runtime,
  production auth, external model calls, notifications, module activation,
  capability activation, code loading, runtime registration, tool execution,
  action proposal execution, write paths, hard delete, frontend dependencies,
  package files, lockfiles, migrations, API routers, SDK resources, CLI command
  implementations, runtime config defaults, or domain module logic.
- AION-111 connector policy action catalog is preview-only. It must pass
  `./scripts/connector-policy-check.sh` and
  `./scripts/connector-policy-no-go-regression.sh`, and it must not add
  connector runtime enablement, external calls, network clients,
  connector/provider SDKs, credentials, token storage, OAuth/OIDC/SAML runtime,
  production auth, external model calls, notifications, module activation,
  capability activation, code loading, runtime registration, tool execution,
  write paths, hard delete, frontend dependencies, package files, lockfiles,
  migrations, runtime policy allow paths, policy bypass, audit bypass, or
  privileged bypass.
- AION-113 connector credential store architecture is design/readiness only.
  It must pass `./scripts/connector-credential-check.sh` and
  `./scripts/connector-credential-no-go-regression.sh`, and it must not add
  credential storage, token storage, secret material persistence,
  OAuth/OIDC/SAML runtime, external identity binding, connector runtime
  credential access, external calls, frontend dependencies, package files,
  lockfiles, migrations, runtime registration, tool execution, write paths, or
  privileged bypass.
- AION-114 connector release gate is release evidence only. It must pass
  `./scripts/connector-release-gate.sh`,
  `./scripts/connector-safety-freeze.sh`, and
  `./scripts/connector-release-no-go-regression.sh`, and it must not add API
  routers, SDK resources, CLI command implementations, runtime config defaults,
  connector runtime enablement, external calls, credential or token storage,
  OAuth/OIDC/SAML runtime, sandbox execution, package files, lockfiles,
  migrations, activation, route registration, code loading, tool execution, or
  privileged bypass.
- AION-115 connector platform checkpoint is closeout evidence only. It must
  pass `./scripts/connector-platform-checkpoint.sh` and
  `./scripts/connector-platform-freeze-check.sh`, and it must not add API
  routers, SDK resources, CLI command implementations, runtime config defaults,
  connector runtime enablement, external calls, credential or token storage,
  OAuth/OIDC/SAML runtime, sandbox execution, package files, lockfiles,
  migrations, activation, route registration, code loading, tool execution, or
  privileged bypass.
- AION-116 connector platform stabilization is regression/freeze evidence only.
  It must pass `./scripts/connector-platform-regression.sh` and
  `./scripts/connector-platform-stabilization-gate.sh`, and it must not add API
  routers, SDK resources, CLI command implementations, runtime config defaults,
  connector runtime enablement, external calls, network clients, connector or
  provider SDK dependencies, credential or token storage, OAuth/OIDC/SAML
  runtime, sandbox execution, package files, lockfiles, migrations, activation,
  route registration, code loading, tool execution, write execution, hard
  delete, implementation approval, or privileged bypass.
- AION-117 post-v0.1 platform integration checkpoint is cross-phase evidence
  only. It must pass `./scripts/platform-integration-checkpoint.sh`,
  `./scripts/platform-integration-freeze-check.sh`, and
  `./scripts/platform-integration-no-go-regression.sh`, and it must not add API
  routers, SDK resources, CLI command implementations, runtime config defaults,
  connector runtime enablement, operator write execution, production auth,
  module activation, external calls, network clients, connector/provider/auth
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, route registration,
  code loading, tool execution, hard delete, implementation approval, or
  privileged bypass.
- AION-120 v0.2 planning stabilization is governance/freeze evidence only. It
  must pass `./scripts/v02-planning-stabilization-gate.sh`,
  `./scripts/v02-planning-freeze-check.sh`, and
  `./scripts/v02-planning-stabilization-no-go-regression.sh`, and it must not
  add API routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, v0.2 tag creation, v0.2 release creation, or
  privileged bypass.
- AION-121 v0.2 readiness final review is planning closeout evidence only. It
  must pass `./scripts/v02-readiness-final-review.sh`,
  `./scripts/v02-readiness-final-freeze.sh`, and
  `./scripts/v02-readiness-final-no-go-regression.sh`, and it must not add API
  routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, v0.2 tag creation, v0.2 release creation, or
  privileged bypass.
- AION-122 v0.2 implementation kickoff boundary is approval-workflow design
  only. It must pass `./scripts/v02-implementation-kickoff-boundary-check.sh`,
  `./scripts/v02-implementation-kickoff-freeze.sh`, and
  `./scripts/v02-implementation-kickoff-no-go-regression.sh`, and it must not
  add API routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, approval workflow bypass, ADR dependency bypass,
  gate dependency bypass, v0.2 tag creation, v0.2 release creation, or
  privileged bypass.
- AION-123 v0.2 approval workflow stabilization is approval-intake evidence
  only. It must pass
  `./scripts/v02-approval-workflow-stabilization-gate.sh`,
  `./scripts/v02-approval-workflow-freeze.sh`, and
  `./scripts/v02-approval-workflow-no-go-regression.sh`, and it must not add
  API routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, approval workflow bypass, ADR dependency bypass,
  gate dependency bypass, approval expiry bypass, approval revocation bypass,
  dual-control bypass, v0.2 tag creation, v0.2 release creation, or privileged
  bypass.
- AION-131 v0.2 implementation request pack is request/evidence-boundary work
  only. It must pass `./scripts/v02-implementation-request-pack-check.sh`,
  `./scripts/v02-request-pack-freeze.sh`, and
  `./scripts/v02-request-pack-no-go-regression.sh`, and it must keep request
  package implementation approval false, proposal template implementation
  approval false, approval evidence approval false, approval queue item
  approval false, proposal implementation approval false, runtime
  implementation approval false, no v0.2 tag, no v0.2 release, no package
  files, no lockfiles, no migrations, and no runtime route, SDK, CLI,
  connector, auth, module, sandbox, external-call, credential, token, or write
  execution implementation.
- AION-132 v0.2 request pack stabilization is evidence completeness and
  submission freeze work only. It must pass
  `./scripts/v02-request-pack-stabilization-gate.sh`,
  `./scripts/v02-request-pack-submission-freeze.sh`, and
  `./scripts/v02-request-pack-stabilization-no-go-regression.sh`, and it must
  keep request pack approval false, evidence completeness bypass false,
  submission freeze bypass false, approval queue item approval false, proposal
  implementation approval false, runtime implementation approval false, no
  v0.2 tag, no v0.2 release, no package files, no lockfiles, no migrations,
  and no runtime route, SDK, CLI, connector, auth, module, sandbox,
  external-call, credential, token, or write execution implementation.
- AION-133 v0.2 request pack final review is pre-approval submission evidence
  only. It must pass `./scripts/v02-request-pack-final-review.sh`,
  `./scripts/v02-preapproval-submission-freeze.sh`, and
  `./scripts/v02-request-pack-final-no-go-regression.sh`, and it must keep
  request pack approval false, submission approval false, preapproval gate
  bypass false, approval queue item approval false, proposal implementation
  approval false, runtime implementation approval false, no v0.2 tag, no v0.2
  release, no package files, no lockfiles, no migrations, and no runtime route,
  SDK, CLI, connector, auth, module, sandbox, external-call, credential, token,
  or write execution implementation.
- AION-124 v0.2 workstream intake readiness is workstream planning evidence
  only. It must pass `./scripts/v02-workstream-intake-readiness-gate.sh`,
  `./scripts/v02-workstream-intake-freeze.sh`, and
  `./scripts/v02-workstream-intake-no-go-regression.sh`, and it must not add
  API routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, workstream implementation approval, approval
  workflow bypass, approval record missing, ADR dependency bypass, gate
  dependency bypass, approval expiry bypass, approval revocation bypass,
  dual-control bypass, v0.2 tag creation, v0.2 release creation, or privileged
  bypass.
- AION-130 v0.2 planning track closeout is governance handoff evidence only.
  It must pass `./scripts/v02-planning-track-closeout.sh`,
  `./scripts/v02-planning-track-handoff-freeze.sh`, and
  `./scripts/v02-planning-track-closeout-no-go-regression.sh`, and it must
  keep proposal registry preview-only true, approval queue preview-only true,
  approval queue item approval false, proposal implementation approval false,
  runtime implementation approval false, backlog implementation approval
  false, workstream implementation approval false, approval workflow bypass
  false, approval record missing false, ADR dependency bypass false, gate
  dependency bypass false, no v0.2 tag, no v0.2 release, no runtime
  enablement, no external calls, no credentials/tokens, no sandbox execution,
  no package files, no lockfiles, no migrations, and no runtime route, SDK, or
  CLI implementation.

- AION-129 is the v0.2 final planning release gate. Treat
  `docs/release/v02-final-planning-release-gate.md`,
  `docs/release/v02-governance-baseline-evidence.md`,
  `docs/release/v02-no-implementation-freeze.md`,
  `docs/release/v02-final-approval-lock-evidence.md`,
  `docs/release/v02-planning-release-gate-matrix.md`, and
  `docs/adr/0120-v02-final-planning-release-gate.md` as planning evidence
  only. Do not create a v0.2 tag or release, do not move `aion-v0.1.0`, and do
  not approve runtime, backlog, workstream, proposal, queue, connector, auth,
  module, external-call, credential/token, sandbox, write-path, package,
  migration, SDK, CLI, or API runtime implementation scope.
- AION-126 v0.2 workstream proposal registry is proposal registry and queue
  preview only. It must pass
  `./scripts/v02-workstream-proposal-registry-check.sh`,
  `./scripts/v02-proposal-registry-freeze.sh`, and
  `./scripts/v02-proposal-registry-no-go-regression.sh`, and it must keep
  proposal registry preview-only true, approval queue preview-only true,
  approval queue item approval false, runtime implementation approval false,
  backlog implementation approval false, workstream implementation approval
  false, approval workflow bypass false, approval record missing false, ADR
  dependency bypass false, gate dependency bypass false, no v0.2 tag, no
  v0.2 release, no runtime enablement, no external calls, no
  credentials/tokens, no sandbox execution, no package files, no lockfiles, no
  migrations, and no runtime route, SDK, or CLI implementation.
- AION-127 v0.2 proposal registry stabilization is proposal registry
  stabilization and approval queue freeze only. It must pass
  `./scripts/v02-proposal-registry-stabilization-gate.sh`,
  `./scripts/v02-approval-queue-freeze.sh`, and
  `./scripts/v02-approval-queue-no-go-regression.sh`, and it must keep
  proposal registry preview-only true, approval queue preview-only true,
  approval queue item approval false, proposal implementation approval false,
  runtime implementation approval false, backlog implementation approval
  false, workstream implementation approval false, approval workflow bypass
  false, approval record missing false, ADR dependency bypass false, gate
  dependency bypass false, no v0.2 tag, no v0.2 release, no runtime
  enablement, no external calls, no credentials/tokens, no sandbox execution,
  no package files, no lockfiles, no migrations, and no runtime route, SDK, or
  CLI implementation.
- AION-128 v0.2 planning master checkpoint is planning governance evidence
  only. It must pass `./scripts/v02-planning-master-checkpoint.sh`,
  `./scripts/v02-planning-master-freeze.sh`, and
  `./scripts/v02-planning-master-no-go-regression.sh`, and it must keep
  proposal registry preview-only true, approval queue preview-only true,
  approval queue item approval false, proposal implementation approval false,
  runtime implementation approval false, backlog implementation approval
  false, workstream implementation approval false, approval workflow bypass
  false, approval record missing false, ADR dependency bypass false, gate
  dependency bypass false, no v0.2 tag, no v0.2 release, no runtime
  enablement, no external calls, no credentials/tokens, no sandbox execution,
  no package files, no lockfiles, no migrations, and no runtime route, SDK, or
  CLI implementation.
- AION-125 v0.2 pre-implementation master freeze is final planning baseline
  evidence only. It must pass `./scripts/v02-preimplementation-master-freeze.sh`,
  `./scripts/v02-preimplementation-final-baseline-check.sh`, and
  `./scripts/v02-preimplementation-master-no-go-regression.sh`, and it must not
  add API routers, SDK resources, CLI command implementations, runtime config
  defaults, connector runtime enablement, operator write execution, production
  auth, module activation, external calls, network clients, connector/provider
  SDK dependencies, credential or token storage, OAuth/OIDC/SAML runtime,
  sandbox execution, package files, lockfiles, migrations, runtime route
  registration, code loading, tool execution, hard delete, backlog
  implementation approval, workstream implementation approval, approval
  workflow bypass, approval record missing, ADR dependency bypass, gate
  dependency bypass, approval expiry bypass, approval revocation bypass,
  dual-control bypass, v0.2 tag creation, v0.2 release creation, or privileged
  bypass.
- AION-134 v0.2 submission registry preview is registry and pre-approval queue
  boundary evidence only. It must pass
  `./scripts/v02-submission-registry-preview-check.sh`,
  `./scripts/v02-preapproval-queue-freeze.sh`, and
  `./scripts/v02-preapproval-queue-no-go-regression.sh`, and it must keep
  submission registry preview-only true, pre-approval queue preview-only true,
  preapproval queue item approval false, request pack approval false,
  submission approval false, proposal registry preview-only true, approval
  queue preview-only true, runtime implementation approval false, proposal
  implementation approval false, approval workflow bypass false, approval
  record missing false, ADR dependency bypass false, gate dependency bypass
  false, no v0.2 tag, no v0.2 release, no runtime enablement, no external
  calls, no credentials/tokens, no sandbox execution, no package files, no
  lockfiles, no migrations, and no runtime route, SDK, or CLI implementation.
- AION-135 v0.2 submission registry stabilization is stabilization evidence
  only. It must pass `./scripts/v02-submission-registry-stabilization-gate.sh`,
  `./scripts/v02-submission-registry-freeze.sh`, and
  `./scripts/v02-submission-registry-stabilization-no-go-regression.sh`, and it
  must keep submission registry stabilized as preview-only evidence,
  pre-approval queue preview-only true, preapproval queue item approval false,
  request pack approval false, submission approval false, proposal registry
  preview-only true, approval queue preview-only true, runtime implementation
  approval false, backlog implementation approval false, workstream
  implementation approval false, proposal implementation approval false,
  approval workflow bypass false, approval record missing false, ADR dependency
  bypass false, gate dependency bypass false, no v0.2 tag, no v0.2 release, no
  runtime enablement, no external calls, no credentials/tokens, no sandbox
  execution, no package files, no lockfiles, no migrations, and no runtime
  route, SDK, or CLI implementation.
- AION-136 adds the v0.2 pre-approval review board, submission review routing,
  reviewer role matrix, decision readiness boundary, evidence pack, and
  no-go/check/freeze scripts as planning artifacts only. Review board decision
  approval remains false; preapproval queue item approval, request pack
  approval, submission approval, approval queue approval, proposal approval,
  workstream approval, backlog approval, and runtime implementation approval all
  remain false. Do not treat reviewer routing, ADR readiness, gate readiness,
  or evidence readiness as implementation approval.
- AION-137 stabilizes the v0.2 review board, freezes review routing, defines
  reviewer quorum evidence, and records decision-readiness evidence as planning
  artifacts only. Review board decision approval, routing decision approval,
  reviewer sign-off implementation approval, preapproval queue approval, request
  pack approval, submission approval, approval queue approval, proposal
  approval, workstream approval, backlog approval, and runtime implementation
  approval must all remain false. Do not treat quorum, routing freeze, reviewer
  sign-off, ADR dependency, gate dependency, or closeout evidence as
  implementation approval.
- AION-138 creates the v0.2 decision package preview and approval-readiness
  evidence bundle as planning artifacts only. Decision package approval,
  approval readiness approval, review board decision approval, routing decision
  approval, reviewer sign-off implementation approval, preapproval queue
  approval, request pack approval, submission approval, approval queue
  approval, proposal approval, workstream approval, backlog approval, and
  runtime implementation approval must all remain false. Do not treat decision
  package completeness, evidence matrix completeness, checklist completion,
  ADR dependency, gate dependency, static console evidence, or freeze evidence
  as implementation approval.
- AION-139 stabilizes the v0.2 decision package and freezes approval readiness
  as planning artifacts only. Decision package approval, approval readiness
  approval, runtime decision readiness approval, review board decision
  approval, routing decision approval, reviewer sign-off implementation
  approval, preapproval queue approval, request pack approval, submission
  approval, approval queue approval, proposal approval, workstream approval,
  backlog approval, and runtime implementation approval must all remain false.
  Do not treat stabilization, closeout, readiness freeze, ADR dependency, gate
  dependency, static console evidence, or no-go evidence as runtime decision
  approval, implementation approval, tag creation, or release creation.
- AION-140 finalizes the v0.2 decision package review and creates the runtime
  decision lock as planning artifacts only. Runtime decision lock release
  approval, decision package approval, approval readiness approval, runtime
  decision readiness approval, review board decision approval, routing decision
  approval, reviewer sign-off implementation approval, preapproval queue
  approval, request pack approval, submission approval, approval queue
  approval, proposal approval, workstream approval, backlog approval, and
  runtime implementation approval must all remain false. Do not treat final
  review, approval readiness closeout, runtime decision lock, ADR dependency,
  gate dependency, static console evidence, or no-go evidence as runtime
  enablement, implementation approval, tag creation, or release creation.
- AION-141 creates the v0.2 approval docket preview, runtime approval review
  boundary, and implementation decision record guard as planning artifacts only.
  Approval docket item approval, implementation decision record approval,
  runtime approval review approval, runtime decision lock release approval,
  decision package approval, approval readiness approval, review board decision
  approval, routing decision approval, reviewer sign-off implementation
  approval, request pack approval, submission approval, approval queue approval,
  proposal approval, workstream approval, backlog approval, and runtime
  implementation approval must all remain false. Do not treat docket readiness,
  decision record completeness, reviewer evidence, ADR dependency, gate
  dependency, static console evidence, or no-go evidence as runtime enablement,
  implementation approval, tag creation, or release creation.

- AION-144 extends the boundary with a runtime approval board preview, approval
  vote record guard, and implementation go/no-go ledger boundary. Runtime
  approval board decision approval, approval vote record approval, approval vote
  record runtime effect, implementation go status, go/no-go ledger runtime
  effect, runtime approval lock release approval, and runtime implementation
  approval must remain false.
- AION-145 stabilizes the runtime approval board layer as evidence only. Runtime
  approval board stabilization approval, runtime approval board decision
  approval, approval vote record approval, approval vote record runtime effect,
  implementation go status, go/no-go ledger runtime effect, runtime approval
  lock release approval, runtime approval review approval, and runtime
  implementation approval must remain false. Do not treat stabilization,
  approval vote record freeze, lifecycle evidence, go/no-go evidence, reviewer
  evidence, ADR dependency, gate dependency, static console evidence, or no-go
  evidence as runtime enablement, implementation approval, tag creation, or
  release creation.
- AION-146 finalizes the runtime approval board layer as evidence only.
  Runtime approval board final review approval, runtime approval board decision
  approval, runtime approval board stabilization approval, approval vote record
  approval, approval vote record closeout approval, approval vote record runtime
  effect, implementation go status, implementation go final approval, runtime
  approval lock release approval, runtime approval review approval, and runtime
  implementation approval must remain false. Do not treat final review, vote
  record closeout, go/no-go ledger final lock, ADR dependency, gate dependency,
  static console evidence, or no-go evidence as runtime enablement,
  implementation approval, tag creation, or release creation.
- AION-147 defines the implementation authorization preview, explicit approval
  record schema, and runtime enablement guard boundary as evidence only.
  Implementation authorization approval, explicit approval record approval,
  runtime enablement guard release approval, runtime approval board approval,
  approval vote record approval, implementation go status, and runtime
  implementation approval must remain false. Do not treat authorization preview,
  schema fields, guard evidence, ADR dependency, gate dependency, static console
  evidence, or no-go evidence as runtime enablement, implementation approval,
  tag creation, or release creation.
- AION-142 stabilizes the v0.2 approval docket and freezes implementation
  decision records as planning artifacts only. Approval docket stabilization
  approval, approval docket item approval, implementation decision record freeze
  approval, implementation decision record approval, runtime approval review
  approval, runtime decision lock release approval, decision package approval,
  approval readiness approval, review board decision approval, routing decision
  approval, reviewer sign-off implementation approval, request pack approval,
  submission approval, approval queue approval, proposal approval, workstream
  approval, backlog approval, and runtime implementation approval must all
  remain false. Do not treat stabilization, record freeze, lifecycle evidence,
  reviewer evidence, ADR dependency, gate dependency, static console evidence,
  or no-go evidence as runtime enablement, implementation approval, tag
  creation, or release creation.
- AION-143 finalizes the v0.2 approval docket review and creates the runtime
  approval lock as planning artifacts only. Approval docket final review
  approval, approval docket item approval, implementation decision record
  closeout approval, implementation decision record approval, runtime approval
  lock release approval, runtime approval review approval, runtime decision
  lock release approval, decision package approval, approval readiness approval,
  review board decision approval, routing decision approval, reviewer sign-off
  implementation approval, request pack approval, submission approval, approval
  queue approval, proposal approval, workstream approval, backlog approval, and
  runtime implementation approval must all remain false. Do not treat final
  review, record closeout, runtime approval lock, ADR dependency, gate
  dependency, static console evidence, or no-go evidence as runtime enablement,
  implementation approval, tag creation, or release creation.

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

AION-149 closes implementation authorization into final review evidence only.
Implementation authorization approval, implementation authorization final review
approval, explicit approval record approval, explicit approval record closeout
approval, runtime enablement guard release approval, runtime enablement guard
final lock release approval, runtime approval board approval, implementation go
status, and runtime implementation approval must remain false. Do not treat
final review, explicit approval record closeout, runtime guard final lock, ADR
dependency, gate dependency, static console evidence, or no-go evidence as
runtime enablement, implementation approval, tag creation, or release creation.
## AION-150 Authorization Track Closeout

AION-150 closes the v0.2 authorization governance track as documentation, examples, static-console preview data, scripts, and tests only. The baseline is complete for planning evidence, but runtime implementation remains unapproved and no implementation authorization is granted.

Agents must keep `runtime_implementation_approved=false`, `implementation_authorization_approved=false`, `explicit_approval_record_approval=false`, `runtime_enablement_master_lock_release_approved=false`, `runtime_enablement_guard_release_approved=false`, `implementation_go_status=false`, and `implementation_no_go_status=true`. Do not create a v0.2 tag or release, and do not enable runtime, external calls, credentials, tokens, sandbox execution, operator writes, connector runtime, production auth, or module activation.

## AION-151 Scoped Production Auth Authorization

AION-151 adds the canonical scoped authorization transaction `AION-151-PA-0001` for `production-auth-core` and future task `AION-152`. The authorization is limited to the `disabled-production-auth-core` implementation scope. Production-auth runtime remains disabled, runtime guard releases remain false, endpoint/storage/provider/external-call approvals remain false, package and migration changes remain false, and no v0.2 tag or release is created.

## AION-154 Production Auth Core Stabilization

AION-154 may harden the internal disabled `aion_brain.production_auth` package
only under `AION-153-PA-0002`. Preserve AION-151 implementation lineage and add
AION-153 stabilization lineage as separate fields. Keep
`aion_brain.auth_runtime` separate from `aion_brain.production_auth`.

Agents must keep `production_auth_runtime_enabled=false`,
`runtime_no_go_status=true`, `runtime_implementation_approved=false`,
`runtime_enablement_guard_release_approved=false`, endpoint/storage/provider/
external-call flags false, no production-auth API router, no package files, no
lockfiles, no migrations, no SDK or CLI runtime surfaces, no v0.2 tag, and no
v0.2 release.

## AION-155 Production Auth Request Boundary Authorization

AION-155 closes `AION-153-PA-0002` as inactive, consumed, expired, and
non-reusable, then creates `AION-155-PA-0003` for future AION-156 disabled
request identity boundary work. The task is governance and evidence only. It
must keep production-auth runtime disabled, identity verification disabled,
authenticated requests disabled, header/cookie parsing prohibited, credential
and token handling prohibited, sessions prohibited, provider integration
prohibited, external calls prohibited, and v0.2 tag or release creation false.

## AION-157 Request Identity Stabilization Authorization

AION-157 marks `AION-155-PA-0003` inactive, consumed by AION-156 PR 66,
expired, and non-reusable. It created `AION-157-PA-0004` for AION-158 request
identity boundary stabilization; AION-159 now marks that authorization
inactive, consumed by AION-158 PR 68, expired, and non-reusable.

Agents must not modify request identity implementation source during AION-157.
Keep identity verification, authenticated requests, Authorization or Cookie
parsing, credentials, passwords, tokens, sessions, external providers, network
calls, auth endpoints, OpenAPI security, package files, lockfiles, migrations,
SDK/CLI runtime surfaces, connector runtime, operator writes, module
activation, sandbox execution, runtime guard release, v0.2 tags, and v0.2
releases blocked.

## AION-158 Request Identity Stabilization

AION-158 may stabilize only the disabled request identity boundary under
`AION-157-PA-0004`. Preserve original implementation lineage
`AION-155-PA-0003` / `AION-156` separately from stabilization lineage
`AION-157-PA-0004` / `AION-158`.

Agents must keep `ProductionAuthRequestIdentityMiddleware` pure ASGI, with
non-HTTP bypass, receive/send passthrough, streaming and request-body
preservation, cancellation propagation, client-disconnect cleanup, forged-state
replacement, duplicate-registration prevention, and anonymous disabled evidence
only. Do not add authentication behavior, header/cookie/query/body identity
parsing, credentials, tokens, sessions, providers, endpoints, OpenAPI security,
packages, lockfiles, migrations, SDK/CLI runtime surfaces, connector runtime,
operator writes, module activation, sandbox execution, runtime guard release,
v0.2 tags, or v0.2 releases.

## AION-159 Actor Context Trust Boundary Authorization

AION-159 marks `AION-157-PA-0004` inactive, consumed by AION-158 PR 68,
expired, and non-reusable. It creates `AION-159-PA-0005` as the only active
authorization for AION-160 actor-context trust-boundary remediation.

Agents must not modify actor-context implementation source during AION-159:
`identity/dev_auth.py`, production-auth source, contracts, config, kernel, API,
API support, SDK/CLI source, package files, lockfiles, and migrations are out
of scope. Document the current non-development identity-header trust fallback
only as observed behavior. AION-160 owns the fail-closed remediation and must
keep runtime authentication, credential/token/session handling, providers,
external calls, auth endpoints, OpenAPI security, connector runtime, operator
writes, module activation, sandbox execution, runtime guard release, v0.2
tags, and v0.2 releases blocked.

## AION-161 Offline Identity Assertion Verification Authorization

AION-161 is governance-only. Agents must not modify actor-context,
request-identity, production-auth implementation source, config, kernel,
api-support, API routers, SDK source, migrations, package manifests, lockfiles,
or `services/brain-api/pyproject.toml` for AION-161.

`AION-159-PA-0005` is historical after AION-160 PR 70. `AION-161-PA-0006` is
the sole active authorization for AION-162 offline Ed25519 identity assertion
verification. The future scope is public-key-only verification with fixed
Ed25519 signatures and no request authentication, no ActorContext application,
no RequestIdentityContext application, no HTTP parsing, no runtime private
keys, no provider network, no replay cache, no endpoints, no SDK/CLI runtime
surface, and no v0.2 tag or release.

## AION-162 Offline Identity Assertion Verification

AION-162 may change only the scoped offline assertion verification artifacts.
It is authorized by `AION-161-PA-0006` and adds exactly one dependency:
`cryptography>=49.0.0,<50.0.0` in `services/brain-api/pyproject.toml`.

Keep the verifier public-key-only and unintegrated. Do not add request
authentication, ActorContext application, RequestIdentityContext application,
HTTP parsing, middleware registration, runtime signing material, provider
networking, replay caches, endpoints, OpenAPI security, SDK/CLI runtime
surfaces, package manifests, lockfiles, migrations, runtime guard release,
v0.2 tags, or v0.2 releases. Formal authorization lifecycle closeout belongs
to AION-163.
