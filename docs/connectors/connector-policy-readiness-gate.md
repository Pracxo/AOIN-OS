# Connector Policy Readiness Gate

The connector policy readiness gate checks whether synthetic simulator policy
actions are declared. It is not runtime approval and does not authorize
external calls.

Required simulator actions:

- `connector_simulator.simulate`
- `connector_simulator.replay`
- `connector_simulator.policy_readiness`

Required AION-111 policy actions:

- `connector_policy.catalog.read`
- `connector_policy.matrix.read`
- `connector_policy.dry_run`
- `connector_policy.traceability.read`

API:

- `POST /brain/connector-simulator/policy-readiness`

The gate returns readiness for policy metadata, sandbox expectation, audit
expectation, and provenance expectation. It always returns:

- `external_calls_allowed=false`
- `credentials_allowed=false`
- `activation_allowed=false`

Runtime implementation still requires a future release gate before any external
connector behavior can exist.

AION-111 extends this readiness evidence with a read-only catalog, matrix, and
policy dry-run gate. Those additions do not authorize runtime allow paths,
external calls, credential access, token access, activation, route
registration, tool execution, or write execution.
