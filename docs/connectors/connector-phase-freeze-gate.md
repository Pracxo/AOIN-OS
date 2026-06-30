# Connector Phase Freeze Gate

## Purpose

The AION-116 connector phase freeze gate locks the connector phase after the
AION-115 platform checkpoint. It requires all connector safety gates to pass
before future implementation work can be proposed.

## Frozen Connector Baseline

The frozen connector baseline includes AION-106 through AION-115:

- external connector boundary design
- disabled connector runtime preview
- connector runtime review gate
- synthetic connector dry-run simulator
- connector policy action catalog
- connector sandbox design
- connector credential store architecture
- connector release gate
- connector safety freeze
- connector platform checkpoint

## Required Safe State

- implementation approval false: `implementation_approved=false`
- runtime disabled: `connector_runtime_enabled=false`
- external calls absent: `external_calls_enabled=false`
- credentials/tokens absent: `credentials_present=false` and
  `token_storage_enabled=false`
- sandbox execution absent: `sandbox_execution_enabled=false`
- activation disabled: `connector_activation_enabled=false`
- route registration disabled: `route_registration_enabled=false`
- release gate required: `./scripts/connector-release-gate.sh`
- checkpoint required: `./scripts/connector-platform-checkpoint.sh`
- stabilization gate required: `./scripts/connector-platform-stabilization-gate.sh`
- future ADR required before implementation

## Freeze Gate Command

```bash
./scripts/connector-platform-stabilization-gate.sh
```

The gate runs the long-running connector regression matrix and, outside nested
CI/pytest contexts, runs the full repository check.

## Future ADR Requirement

Future connector implementation requires a new ADR that explicitly defines the
approved runtime boundary, egress boundary, credential boundary, sandbox
boundary, rollback path, operator approval model, and release evidence. The ADR
must pass the connector platform stabilization gate before any implementation
branch can enable runtime behavior.

## No-Go Freeze Rules

The freeze gate fails for connector runtime enablement, external calls,
credential or token storage, sandbox execution, activation, route registration,
package files, migrations, API execution routes, SDK/CLI implementation drift,
implementation approval, or privileged bypass.
