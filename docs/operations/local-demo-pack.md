# AION v0.1 Local Demo Pack

## Purpose

The local demo pack shows that AION Brain v0.1 can start locally, verify core
readiness, run deterministic synthetic scenarios, inspect operator status, and
review metadata-only extension/module paths without loading code.

## Demo Prerequisites

- Docker Desktop or compatible local Docker engine.
- Repo-local Brain and SDK virtual environments already prepared.
- No production credentials required.

## Demo Safety Boundaries

The demo does not install packages, call external services, enable production
authorization, enable full autonomy, send notifications outside the local
ledger, load extension code, activate capability bindings, or hard-delete
records.

## Start Local Stack

```bash
docker compose config --quiet
docker compose up --build -d brain-api postgres redis nats opa
```

## Check Health

```bash
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
```

## Run Setup Doctor

```bash
./scripts/setup-doctor.sh
```

## Seed Defaults

```bash
./scripts/seed-defaults.sh
```

## Run Golden Path

```bash
./scripts/golden-path.sh --offline-ok
```

## Run RC Gate

```bash
./scripts/rc-check.sh --offline-ok
```

## Inspect Operator Overview

```bash
examples/demo/operator-overview-curl.sh
```

## Validate Extension Manifest

```bash
./scripts/aionctl.sh --scope workspace:main extensions validate --manifest-file examples/demo/generic-extension-manifest.json
```

## Run Extension Intake Dry-Run

```bash
./scripts/aionctl.sh --scope workspace:main extensions intake --manifest-file examples/demo/generic-extension-manifest.json
```

## Run Module Binding Validation Dry-Run

```bash
./scripts/aionctl.sh --scope workspace:main module-bindings validate --dry-run
```

## Run Conformance Readiness Dry-Run

```bash
./scripts/aionctl.sh --scope workspace:main conformance run --capability-binding-id <capability-binding-id>
./scripts/aionctl.sh --scope workspace:main readiness assess --capability-binding-id <capability-binding-id>
```

## Inspect Notifications and Incidents

```bash
./scripts/aionctl.sh --scope workspace:main notifications alerts
./scripts/aionctl.sh --scope workspace:main incidents list
```

## Run Release Smoke

```bash
./scripts/release-smoke.sh --offline-ok
```

## Stop Local Stack

```bash
docker compose down
```

## One Command Demo

```bash
./scripts/demo-local.sh --offline-ok
```

## Final Release Demo Sequence

```bash
./scripts/v0.1-tag-preview.sh
./scripts/v0.1-final-verify.sh --offline-ok --skip-docker --skip-api
./scripts/v0.1-freeze.sh --offline-ok --skip-docker --skip-api
```

Use the full Docker-local sequence before tagging when Docker is available:

```bash
docker compose up --build -d brain-api postgres redis nats opa
./scripts/demo-local.sh --offline-ok
./scripts/v0.1-final-verify.sh --offline-ok
docker compose down
```

## Expected Outputs

- `/health` returns `status=ok`.
- `/health/ready` reports dependency status.
- Setup doctor returns local setup status or local file/compose readiness when
  offline mode is used.
- Golden path produces deterministic dry-run scenario output when the API is
  reachable.
- RC gate produces local check results and posts an RC run when the API is
  reachable.
- Extension validation returns metadata validation only.

## Demo Failure Handling

Do not bypass policy or enable disabled features to make the demo pass. Capture
the failing command, inspect `docs/operations/troubleshooting.md`, then rerun
the smallest failed check.

## Operator Console Demo Map

AION-087 maps the future console demo without adding runtime UI. The demo uses
existing local checks:

```bash
./scripts/setup-doctor.sh --fast --offline-ok
./scripts/golden-path.sh --offline-ok
./scripts/rc-check.sh --offline-ok
./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
./scripts/model-provider-check.sh --offline-ok --skip-api
./scripts/demo-local.sh --offline-ok
```

See `docs/operator-console/operator-demo-map.md`. The path remains local-first
and must not activate modules, load code, install packages, register routes,
call external services, enable external model calls, or reveal prompt bodies,
private reasoning traces, or secrets.
