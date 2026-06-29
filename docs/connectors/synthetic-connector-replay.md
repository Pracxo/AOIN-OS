# Synthetic Connector Replay

Synthetic connector replay runs a local fixture through the dry-run simulator.
Replay fixtures are JSON shape records, not external connector calls.

Fixture constraints:

- `synthetic=true`
- `trusted=false`
- `fixture_type` is local descriptive text
- request and response shapes must not contain endpoint fields, credential
  fields, token fields, raw prompt material, or hidden reasoning material

API:

- `POST /brain/connector-simulator/replay`

Policy action:

- `connector_simulator.replay`

Replay output is still a connector simulation result. It remains read-only,
synthetic-only, and blocked from route registration, runtime activation,
external egress, tool execution, and write execution.
