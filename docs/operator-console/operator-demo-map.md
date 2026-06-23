# Operator Demo Map

AION-087 maps the local operator demo path. It does not add a runtime UI.

## Demo sequence

1. Start local stack.
2. Check health/readiness.
3. Run setup doctor.
4. Run golden path.
5. Run RC gate.
6. Run generic knowledge module pack check.
7. Run module mock runtime dry-run.
8. Run provider hardening check.
9. Inspect operator overview.
10. Stop stack.

## Commands

```bash
docker compose up --build -d brain-api postgres redis nats opa
curl -fsS http://localhost:8080/health
curl -fsS http://localhost:8080/health/ready
./scripts/setup-doctor.sh --fast --offline-ok
./scripts/golden-path.sh --offline-ok
./scripts/rc-check.sh --offline-ok
./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
./scripts/model-provider-check.sh --offline-ok --skip-api
./scripts/demo-local.sh --offline-ok
docker compose down
```

## Expected posture

The demo remains local-first. It does not activate modules, load code, install
packages, register routes, call external services, enable external model calls,
store credentials, expose raw prompts, expose hidden reasoning, or reveal
secrets.
