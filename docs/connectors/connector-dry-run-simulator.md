# Connector Dry-Run Simulator

AION-110 adds a deterministic connector dry-run simulator for local shape
validation. It validates synthetic connector request and response shapes,
returns synthetic results, emits audit and telemetry evidence, and keeps the
external connector runtime disabled.

The simulator is not connector execution. It does not create routes, load code,
activate connectors, execute tools, mutate runtime settings, call external
services, use credentials, or use tokens.

Safe defaults:

- `connector_simulator_enabled=true`
- `connector_dry_run_simulation_enabled=true`
- `connector_simulator_external_calls_enabled=false`
- `connector_simulator_credentials_enabled=false`
- `connector_simulator_tokens_enabled=false`
- `connector_simulator_runtime_activation_enabled=false`

API:

- `POST /brain/connector-simulator/simulate`
- `GET /brain/connector-simulator/status`
- `POST /brain/connector-simulator/query`

Policy actions:

- `connector_simulator.simulate`
- `connector_simulator.status.read`
- `connector_simulator.query`

The result always marks `synthetic=true`, `trusted=false`,
`external_calls_made=false`, `credentials_used=false`, `tokens_used=false`, and
`connector_runtime_enabled=false`.

## AION-111 Policy Catalog Relationship

AION-111 uses simulator actions as catalog inputs and policy dry-run evidence.
The simulator remains synthetic only; connector policy dry-run results do not
execute simulator work, call external services, access credentials, access
tokens, activate connectors, or grant runtime permission.
## AION-114 Release Gate Input

The dry-run simulator remains synthetic-only and is validated by the connector
release gate. Simulator output must not become connector execution, network
access, provider access, activation, or route registration.

## AION-115 Checkpoint Input

The dry-run simulator is included in the connector phase evidence pack. It
remains synthetic-only and does not approve trusted connector ingress or runtime
execution.
