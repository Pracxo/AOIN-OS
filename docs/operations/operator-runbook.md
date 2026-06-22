# AION v0.1 Operator Runbook

## Purpose

This runbook gives a local operator one command path for starting, verifying,
demonstrating, and handing off AION Brain v0.1 as a local release candidate.

## AION Meaning

AION = Adaptive Intelligence Orchestration Nexus.

AION OS = Adaptive Intelligence Orchestration Nexus Operating System.

## Local Operator Responsibilities

- Start and stop the local Docker stack.
- Run health, readiness, setup, golden path, release smoke, RC, freeze, and
  release-package dry-run checks.
- Review operator status, notifications, incidents, findings, and release
  evidence.
- Keep v0.1 inside its local-first boundaries.

## What v0.1 Can Do

- Run deterministic Brain API health and readiness checks.
- Run first-run bootstrap and setup doctor checks.
- Run synthetic golden path scenarios.
- Run the release smoke matrix and RC gate.
- Produce RC findings, evidence packs, and reports.
- Inspect operator status, queues, action items, notifications, incidents,
  extension intake records, module binding validation, and conformance
  readiness records.

## What v0.1 Must Not Do

- v0.1 is local-first.
- v0.1 does not enable production auth.
- v0.1 does not enable full autonomy.
- v0.1 does not execute model-generated tool calls.
- v0.1 does not load extension code.
- v0.1 does not activate capability bindings.
- v0.1 does not send external notifications.
- v0.1 does not hard-delete records.

## Local Startup Sequence

```bash
docker compose config --quiet
docker compose up --build -d brain-api postgres redis nats opa
```

## Health Checks

```bash
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
```

## Setup Doctor

```bash
./scripts/setup-doctor.sh --fast --offline-ok
./scripts/aionctl.sh --scope workspace:main bootstrap doctor
```

Critical setup findings block the release candidate until reviewed and fixed.

## Golden Path

```bash
./scripts/golden-path.sh --offline-ok
./scripts/aionctl.sh --scope workspace:main golden-path run
```

Golden path proves deterministic local scenario wiring with synthetic records.

## RC Gate

```bash
./scripts/rc-check.sh --offline-ok
./scripts/rc-evidence.sh --offline-ok
./scripts/aionctl.sh --scope workspace:main rc run --no-service-checks
```

Any RC blocker is a release no-go.

## Freeze Gate

```bash
./scripts/aionctl.sh --scope workspace:main freeze run --version 0.1.0
```

Freeze stays a dry-run readiness gate until the final freeze task.

## Release Package Dry-Run

```bash
./scripts/package-release.sh --dry-run
./scripts/aionctl.sh --scope workspace:main release create --version 0.1.0
```

Package dry-run creates local release metadata only.

## Operator Control Tower

```bash
./scripts/operator-overview.sh
./scripts/aionctl.sh --scope workspace:main operator overview
./scripts/aionctl.sh --scope workspace:main operator queues
./scripts/aionctl.sh --scope workspace:main operator actions
```

## Notifications and Incidents

```bash
./scripts/aionctl.sh --scope workspace:main notifications alerts
./scripts/aionctl.sh --scope workspace:main incidents list
```

Notifications are local records in v0.1.

## Extension Intake and Module Binding Review

```bash
./scripts/aionctl.sh --scope workspace:main extensions validate --manifest-file examples/demo/generic-extension-manifest.json
./scripts/aionctl.sh --scope workspace:main extensions intake --manifest-file examples/demo/generic-extension-manifest.json
./scripts/aionctl.sh --scope workspace:main module-bindings validate --dry-run
```

Extension intake is metadata-only. Module binding validation does not activate
capabilities.

## Conformance and Readiness

```bash
./scripts/aionctl.sh --scope workspace:main conformance run --capability-binding-id <capability-binding-id>
./scripts/aionctl.sh --scope workspace:main readiness assess --capability-binding-id <capability-binding-id>
```

Conformance is schema and metadata validation only.

## Safe Shutdown

```bash
docker compose down
```

## Troubleshooting Quick Table

| Symptom | First command | Safe fix |
| --- | --- | --- |
| Health fails | `docker compose logs brain-api` | Rebuild local stack and inspect config. |
| Readiness degraded | `curl -fsS http://localhost:8080/health/ready` | Inspect the named dependency. |
| Policy denied | `./scripts/policy-coverage.sh` | Add missing generic policy coverage. |
| RC blocker | `./scripts/rc-evidence.sh --offline-ok` | Fix the failed required check. |

## Escalation Path

Escalate only with local evidence: command, status code, policy reason,
operator item id, RC run id, and report id. Do not attach secrets or private
reasoning traces.

## No-Go Conditions

Use `docs/release/v0.1-no-go-conditions.md`. Any listed no-go blocks release.

## Final Release Handoff Command Set

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
