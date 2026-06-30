# Connector Safety Baseline Lock

## Purpose

AION-116 locks the connector safe baseline after the AION-115 checkpoint. These
values are required by the connector regression and stabilization gates.

## Locked Values

- `connector_runtime_enabled=false`
- `external_calls_enabled=false`
- `credentials_present=false`
- `token_storage_enabled=false`
- `sandbox_execution_enabled=false`
- `connector_activation_enabled=false`
- `route_registration_enabled=false`
- `implementation_approved=false`
- `package_files_added=false`
- `migrations_added=false`

## Enforcement

The baseline is enforced by:

```bash
./scripts/connector-platform-regression.sh
./scripts/connector-platform-stabilization-gate.sh
```

The scripts also call the release, checkpoint, runtime, simulator, policy,
sandbox, credential, docs, domain drift, and boundary gates.

## Lock Decision

Connector implementation remains unapproved. Runtime enablement, external
calls, credential/token storage, sandbox execution, activation, route
registration, package files, and migrations are release blockers.

## AION-117 Platform Lock

AION-117 extends the lock to the integrated platform approval state:
`operator_write_execution_approved=false`,
`connector_implementation_approved=false`,
`production_auth_approved=false`, `module_activation_approved=false`,
`external_calls_approved=false`, `credential_storage_approved=false`,
`token_storage_approved=false`, and `sandbox_execution_approved=false`.
The lock is enforced by `./scripts/platform-integration-no-go-regression.sh`.
