# AION Brain v0.1.0 Release Notes

## What This Release Is

AION Brain v0.1.0 is the local-first release baseline for AION OS, the
Adaptive Intelligence Orchestration Nexus Operating System. It freezes the
Brain core after the release candidate, operator runbook, demo pack, and final
docs audit work.
AION means Adaptive Intelligence Orchestration Nexus.
AION OS means Adaptive Intelligence Orchestration Nexus Operating System.

## What This Release Is Not

This is not a production deployment release. It does not enable production
auth, full autonomy, external model calls by default, external notification
delivery by default, extension code loading, capability activation, dynamic
route registration, hard delete, model-generated tool execution, or domain
modules in Brain core.

## What Changed From Architecture Build To Release Baseline

- The feature build is treated as complete for v0.1.
- Final release notes, changelog, freeze documentation, evidence summary,
  tagging guide, release baseline, operator acceptance, and known limitations
  are now present.
- Final release scripts aggregate existing checks instead of adding a new
  Brain subsystem.
- The top-level `VERSION` file records `0.1.0`; existing package version fields
  already matched `0.1.0`.

## Local Quick Start

```bash
docker compose config --quiet
docker compose up --build -d brain-api postgres redis nats opa
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
./scripts/demo-local.sh --offline-ok
docker compose down
```

## Verification Commands

```bash
./scripts/v0.1-final-verify.sh --offline-ok
./scripts/v0.1-freeze.sh --offline-ok
./scripts/v0.1-tag-preview.sh
```

## Operator Handoff

Use the operator runbook, local demo pack, final evidence summary, final freeze
guide, release handoff, and operator acceptance checklist before creating a
local tag.

## No-Go Conditions

Any failed required gate, source drift, unsafe boundary enablement, raw secret
leak, production claim, external call, or domain module logic in Brain core
blocks the tag.

## Next Milestone

AION-080 closes v0.1 locally. Post-v0.1 work starts after the local tag and
must preserve the Brain baseline boundaries.
