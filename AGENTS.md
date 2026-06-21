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
- Do not add domain-specific connectors in Brain core.
- Policy actions and permissions must remain generic dotted lowercase names.
- Keep policy simulations side-effect-free; they must never execute target actions.
- Policy tests must not require live OPA or external network services.
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
- Future UI work must consume Operator contracts rather than querying subsystem
  internals directly.
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
