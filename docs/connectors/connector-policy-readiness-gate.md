# Connector Policy Readiness Gate

The connector policy readiness gate checks whether synthetic simulator policy
actions are declared. It is not runtime approval and does not authorize
external calls.

Required simulator actions:

- `connector_simulator.simulate`
- `connector_simulator.replay`
- `connector_simulator.policy_readiness`

API:

- `POST /brain/connector-simulator/policy-readiness`

The gate returns readiness for policy metadata, sandbox expectation, audit
expectation, and provenance expectation. It always returns:

- `external_calls_allowed=false`
- `credentials_allowed=false`
- `activation_allowed=false`

Runtime implementation still requires a future release gate before any external
connector behavior can exist.
