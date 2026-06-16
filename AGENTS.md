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
