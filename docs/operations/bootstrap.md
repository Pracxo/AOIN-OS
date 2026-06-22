# First-Run Bootstrap Runbook

AION first-run bootstrap prepares local Brain readiness. It is not production
provisioning, deployment, package installation, secret management, or cloud
setup.

## Local Commands

```bash
./scripts/setup-doctor.sh --fast
./scripts/seed-defaults.sh
./scripts/bootstrap-local.sh --fast
```

Use `--fast` to skip the full repo check stack while iterating. Remove `--fast`
before a local release check.

## API Commands

```bash
curl -X POST http://localhost:8080/brain/bootstrap/doctor
curl -X POST http://localhost:8080/brain/bootstrap/run
curl http://localhost:8080/brain/bootstrap/runs
curl http://localhost:8080/brain/bootstrap/findings
curl http://localhost:8080/brain/bootstrap/reports
```

## Safety Rules

Bootstrap must remain local-only and dry-run by default. It must not install
packages, create production credentials, enable external providers, call
external services, enable full autonomy, load code, execute tools, perform
controlled handoffs, hard-delete records, or mutate source code.

Setup findings are records for operator review. They do not remediate the
source condition automatically.

## Release Handoff Usage

For v0.1 release handoff, run:

```bash
./scripts/setup-doctor.sh --fast --offline-ok
```

Critical setup findings are no-go conditions for the release candidate.
