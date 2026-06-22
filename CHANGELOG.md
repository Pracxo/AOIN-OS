# Changelog

## AION Brain v0.1.0

### Release type: local-first Brain baseline

AION Brain v0.1.0 freezes the local Brain baseline for the Adaptive
Intelligence Orchestration Nexus Operating System. The release is Docker-local
verified, dry-run safe by default, and intended for local operator validation.
AION means Adaptive Intelligence Orchestration Nexus. AION OS means Adaptive
Intelligence Orchestration Nexus Operating System.

The Brain API and Python SDK package metadata already use version `0.1.0`.
The top-level `VERSION` file now records the same release target.

### Core Brain capabilities

- Brain loop contracts and deterministic planning surfaces.
- Event intake, memory, policy, capability registry, execution records, goals,
  tasks, schedules, reasoning, evaluation, learning, reflection, audit,
  visual telemetry, dialogue, response composition, grounding, and operator
  overview surfaces.
- Version manifest, compatibility matrix, migration baseline, release artifact
  records, release candidate gate, freeze gate, and release package handoff
  records.

### Safety and governance defaults

- Dry-run defaults remain the release posture.
- Policy, approval, risk, sandbox, conformance, readiness, freeze, and no-go
  gates remain explicit.
- Extension metadata, module binding metadata, and conformance metadata remain
  records only.

### Operator and release tooling

- Added final operator runbook, local demo pack, troubleshooting, release
  handoff, evidence summary, tagging guide, release baseline, operator
  acceptance, known limitations, and final freeze documentation.
- Added final verification, freeze preview, and tag preview scripts.

### SDK and CLI coverage

- Python SDK and `aionctl` cover the public Brain APIs used by the local
  release workflow, including release package, release candidate, freeze,
  bootstrap, golden path, operator, extension, module binding, conformance,
  and readiness surfaces.

### Verification gates

- `./scripts/check.sh`
- `./scripts/final-docs-audit.sh`
- `./scripts/rc-check.sh --offline-ok`
- `./scripts/rc-evidence.sh --offline-ok`
- `./scripts/golden-path.sh --offline-ok`
- `./scripts/release-smoke.sh --offline-ok`
- `./scripts/setup-doctor.sh --fast --offline-ok`
- `docker compose config --quiet`
- `git diff --check`

### Explicitly disabled features

- No production auth claim.
- No full autonomy.
- No external model calls by default.
- No external notification delivery by default.
- No extension code loading.
- No capability activation.
- No dynamic route registration.
- No hard delete.
- No model-generated tool execution.
- No domain modules in Brain core.

### Known limitations

The release is local-first only. It does not provide a cloud deployment
profile, production authentication, external notification delivery, external
model provider activation by default, extension code loading, capability
activation, UI operator console, background scheduler loop, automatic
remediation, hard delete, legal/compliance retention guarantees, or a
performance SLA.

### Post-v0.1 direction

Post-v0.1 work starts from this frozen Brain baseline. Future module ecosystem
work must plug in through extension, binding, conformance, action proposal,
policy, sandbox, and operator gates without modifying Brain core.
