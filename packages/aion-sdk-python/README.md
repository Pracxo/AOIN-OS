# AION Python SDK and aionctl

`aion-sdk-python` is the Python developer interface for AION Brain. It talks
only to public HTTP APIs exposed by the Brain API and does not import
`aion_brain`, database drivers, provider SDKs, or domain modules.

## Install

```bash
cd packages/aion-sdk-python
python -m pip install -e ".[dev]"
```

## Configuration

The SDK defaults to `http://localhost:8080` and reads:

- `AION_BASE_URL`
- `AION_ACTOR_ID`
- `AION_WORKSPACE_ID`
- `AION_ROLES`
- `AION_PERMISSIONS`
- `AION_SECURITY_SCOPE`
- `AION_TRACE_ID`
- `AION_CORRELATION_ID`
- `AION_IDEMPOTENCY_KEY`
- `AION_TIMEOUT_SECONDS`

Comma-separated values are supported for roles, permissions, and scope.

## Python Client

```python
from aion_sdk import AIONClient, AIONClientConfig

config = AIONClientConfig(
    base_url="http://localhost:8080",
    actor_id="dev-owner",
    workspace_id="main",
    security_scope=["workspace:main"],
)

client = AIONClient(config)
print(client.health.health())
print(client.kernel.status())
```

Resources include `health`, `kernel`, `events`, `memory`, `reasoning`,
`commands`, `workflows`, `autonomy`, `approvals`, `visual`, `modules`,
`model_outputs`, and `action_proposals`.

## aionctl

```bash
./scripts/aionctl.sh --scope workspace:main health
./scripts/aionctl.sh --json kernel status
./scripts/aionctl.sh --scope workspace:main kernel self-test
./scripts/aionctl.sh --scope workspace:main smoke run
./scripts/aionctl.sh modules scaffold --module-id generic.example --package-name generic-example --output examples/generic-module
./scripts/aionctl.sh modules certify --module-package-id module-package-id
./scripts/aionctl.sh action-proposals query
./scripts/aionctl.sh action-proposals handoff --action-proposal-id action-proposal-id --mode dry_run
```

`aionctl` uses development identity headers only. It does not send bearer tokens
or production auth secrets.

## Contract Export

```bash
./scripts/aionctl.sh contracts export \
  --output artifacts/aion-contracts.json \
  --openapi-output artifacts/openapi.json
```

## Safety

- No retries are hidden by the SDK.
- Tests use `httpx.MockTransport` or CLI fakes.
- `bootstrap dev` is conservative and does not enable full autonomy, external
  models, external tools, workers, or schedulers.
- Smoke tests use dry-run/noop requests and idempotency keys.
- Module commands are contract-only and never execute module code.
- Action proposal commands do not execute proposals. Handoff defaults to dry-run
  and controlled handoff remains disabled by default.

## v0.1 Local Demo

Use the repo-level demo script for release-candidate verification:

```bash
cd ../..
./scripts/demo-local.sh --offline-ok
```

Relevant SDK-backed CLI surfaces are `bootstrap`, `golden-path`, `rc`,
`extensions`, `module-bindings`, `conformance`, `readiness`, and `operator`.
They call public Brain APIs only and keep demo module paths metadata-only.

## v0.1 Release Closure

The final release scripts live at the repo root and aggregate SDK-backed CLI
surfaces with Brain API checks:

```bash
cd ../..
./scripts/v0.1-tag-preview.sh
./scripts/v0.1-final-verify.sh --offline-ok --skip-docker --skip-api
./scripts/v0.1-freeze.sh --offline-ok --skip-docker --skip-api
```

The SDK does not create tags, push artifacts, deploy, install packages, call
external services, or bypass Brain policy for v0.1 release closure.
