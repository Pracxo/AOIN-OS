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
