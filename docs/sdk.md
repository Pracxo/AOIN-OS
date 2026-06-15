# AION Python SDK

The Python SDK is the supported local developer client for AION Brain. It is a
separate package under `packages/aion-sdk-python` and communicates with AION
Brain through public HTTP APIs only.

The SDK owns:

- Client configuration from environment variables
- Development identity and trace headers
- Typed error mapping for `AIONErrorResponse`
- Resource wrappers for public Brain APIs
- A small forward-compatible model layer

The SDK does not own:

- Brain server internals
- Database access
- Provider SDK calls
- Production authentication
- Domain-specific modules

## Client Example

```python
from aion_sdk import AIONClient

client = AIONClient()
print(client.health.ready())
print(client.kernel.contracts())
```

## Error Handling

AION public API errors map to SDK exceptions:

- `AIONValidationError`
- `AIONPolicyDeniedError`
- `AIONAutonomyDeniedError`
- `AIONApprovalRequiredError`
- `AIONConflictError`
- `AIONNotFoundError`
- `AIONDependencyUnavailableError`

Unknown AION errors remain `AIONAPIError`. Non-AION HTTP failures become
`AIONHTTPError`.

## Headers

The SDK builds AION development headers:

- `X-AION-Actor-ID`
- `X-AION-Workspace-ID`
- `X-AION-Roles`
- `X-AION-Permissions`
- `X-AION-Security-Scope`
- `X-AION-Trace-ID`
- `X-AION-Correlation-ID`
- `Idempotency-Key`
- `User-Agent`

It intentionally strips `Authorization` from helper-built headers.

## Modules Resource

`client.modules` supports:

- `submit_package(payload)`
- `list_packages(status=None, module_id=None)`
- `get_package(module_package_id)`
- `certify(module_package_id, payload)`
- `scaffold(payload)`
- `compatibility(module_package_id)`
- `run_contract_tests(module_package_id, dry_run=True)`

The SDK does not execute module code. It calls public Module Developer Kit HTTP
APIs only.

## Sandbox Resource

`client.sandbox` supports:

- `create_profile(payload)`
- `list_profiles(scope, status=None)`
- `validate_profile(sandbox_profile_id, scope)`
- `run(payload)`
- `create_secret_ref(payload)`
- `list_secret_refs(scope, status=None)`
- `create_connector(payload)`
- `list_connectors(scope, status=None, connector_type=None)`
- `validate_connector(connector_id, scope)`

The SDK sends metadata-only requests to the public Brain API. It does not
import `aion_brain`, access databases, execute containers, accept raw secrets,
or call external connector systems.

## Scenarios Resource

`client.scenarios` supports the end-to-end validation harness:

- `create(payload)`
- `list(status=None, scenario_type=None, tags=None)`
- `get(scenario_id, scope)`
- `run(payload)`
- `get_run(scenario_run_id, scope)`
- `runs(scope, status=None, scenario_type=None, limit=50)`
- `seed_defaults(scope, dry_run=True)`
- `list_fixtures(scope, fixture_type=None)`
- `load_fixture(payload)`
- `run_release_baseline(payload)`
- `get_release_baseline(release_baseline_id)`
- `list_release_baselines(scope, version=None, status=None, limit=50)`

The SDK calls public Brain APIs only. Scenario runs and release baselines are
dry-run by default and must not require external services, optional adapters,
full autonomy, external tool execution, or domain-specific scenario packs.

## Versioning Resource

`client.versioning` supports:

- `create_manifest(payload)`
- `get_manifest(version)`
- `list_manifests(status=None, limit=50)`
- `freeze_manifest(version, payload)`
- `seed_features(scope, dry_run=True)`
- `list_features(scope, status=None, category=None)`
- `create_feature(payload)`
- `deprecate_feature(feature_key, scope, reason)`
- `generate_compatibility(version, scope)`
- `get_compatibility(version)`
- `generate_migration_baseline(version, scope)`
- `generate_release_artifacts(version, scope, created_by=None)`
- `sdk_compatibility(scope)`
- `run_freeze_gate(payload)`
- `get_freeze_gate(freeze_gate_id)`
- `list_freeze_gates(scope, version=None, status=None)`

The SDK uses public HTTP endpoints only and does not import Brain API internals
or optional adapter clients.

## Release Resource

`client.release` supports:

- `create_package(payload)`
- `get_package(release_package_id, scope=None)`
- `list_packages(scope, version=None, status=None)`
- `validate_package(release_package_id, scope)`
- `handoff(release_package_id, scope)`

The SDK calls public release package APIs only. It does not read local files,
compute checksums, upload artifacts, call registries, or import Brain API
internals.
