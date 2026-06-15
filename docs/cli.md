# aionctl CLI

`aionctl` is the command line interface for local AION Brain development. It is
implemented inside `packages/aion-sdk-python` and calls the Brain API only
through the SDK.

## Global Options

- `--base-url`
- `--actor-id`
- `--workspace-id`
- `--scope`
- `--trace-id`
- `--correlation-id`
- `--idempotency-key`
- `--json`

## Commands

```bash
./scripts/aionctl.sh health
./scripts/aionctl.sh ready
./scripts/aionctl.sh kernel status
./scripts/aionctl.sh kernel self-test
./scripts/aionctl.sh kernel contracts
./scripts/aionctl.sh kernel boundary-check
./scripts/aionctl.sh bootstrap dev
./scripts/aionctl.sh events send --event-json '{...}'
./scripts/aionctl.sh memory retrieve "remember this"
./scripts/aionctl.sh commands dispatch --command-type noop
./scripts/aionctl.sh workflows status
./scripts/aionctl.sh autonomy status
./scripts/aionctl.sh scenarios list
./scripts/aionctl.sh scenarios seed-defaults
./scripts/aionctl.sh scenarios run --scenario-id golden_path_brain
./scripts/aionctl.sh demo-fixtures list
./scripts/aionctl.sh release-baseline run --version 0.1.0
./scripts/aionctl.sh smoke run
./scripts/aionctl.sh contracts export --output artifacts/aion-contracts.json
```

## Bootstrap

`bootstrap dev` inspects `/brain/me`, optional actor/workspace records, runs a
dry kernel self-test, and can plan or apply a bounded dry-run autonomy level.
It does not enable full autonomy, external models, external tools, workers, or
schedulers.

## Smoke Run

`smoke run` checks health, kernel status, kernel self-test, autonomy status,
generic event intake, noop dry-run command dispatch, and visual map projection
when available. Optional steps are reported without making the command fail.
Critical failures produce a non-zero exit code.

## Module Commands

```bash
./scripts/aionctl.sh modules scaffold --module-id generic.example --package-name generic-example --output examples/generic-module
./scripts/aionctl.sh modules submit --manifest examples/generic-module/aion.module.json
./scripts/aionctl.sh modules certify --module-package-id module-package-id
./scripts/aionctl.sh modules list
./scripts/aionctl.sh modules compatibility --module-package-id module-package-id
./scripts/aionctl.sh modules test --module-package-id module-package-id
```

`aionctl modules` exposes the Module Developer Kit through the SDK. The scaffold
command writes static contract files only. Submit supports JSON manifests in
v0.1; YAML is included as a static human-readable example.

## Sandbox, Secrets, and Connector Commands

```bash
./scripts/aionctl.sh sandbox profile create --name generic --description "Local no-op"
./scripts/aionctl.sh sandbox profile list
./scripts/aionctl.sh sandbox profile validate --sandbox-profile-id sandbox-profile-id
./scripts/aionctl.sh sandbox run --sandbox-profile-id sandbox-profile-id
./scripts/aionctl.sh secrets create-ref --name generic --description "Reference" --external-ref env:AION_GENERIC_REF
./scripts/aionctl.sh secrets list
./scripts/aionctl.sh connectors create --name generic --description "Metadata only"
./scripts/aionctl.sh connectors list
./scripts/aionctl.sh connectors validate --connector-id connector-id
```

`aionctl` calls these APIs through `client.sandbox`. It does not accept raw
secret values, execute code, start containers, or connect to external systems.

## Scenario, Demo Fixture, and Release Baseline Commands

```bash
./scripts/aionctl.sh scenarios list
./scripts/aionctl.sh scenarios seed-defaults
./scripts/aionctl.sh scenarios run --scenario-id golden_path_brain
./scripts/aionctl.sh scenarios runs
./scripts/aionctl.sh demo-fixtures list
./scripts/aionctl.sh demo-fixtures load --fixture-id generic_event
./scripts/aionctl.sh release-baseline run --version 0.1.0
./scripts/aionctl.sh release-baseline get --release-baseline-id release-baseline-id
```

`aionctl scenarios`, `aionctl demo-fixtures`, and
`aionctl release-baseline` call the public Brain API through
`client.scenarios`. Scenario runs and release baseline runs are dry-run by
default. They must not execute domain modules, call external services, enable
full autonomy, or require optional adapters.

## Versioning and Freeze Commands

```bash
./scripts/aionctl.sh versioning manifests create --version 0.1.0
./scripts/aionctl.sh versioning manifests get --version 0.1.0
./scripts/aionctl.sh versioning manifests freeze --version 0.1.0 --reason "ready"
./scripts/aionctl.sh versioning features seed-defaults
./scripts/aionctl.sh versioning features list
./scripts/aionctl.sh versioning compatibility generate --version 0.1.0
./scripts/aionctl.sh versioning migration-baseline --version 0.1.0
./scripts/aionctl.sh versioning release-artifacts --version 0.1.0
./scripts/aionctl.sh versioning sdk-compatibility
./scripts/aionctl.sh freeze run --version 0.1.0
./scripts/aionctl.sh freeze get --freeze-gate-id freeze-gate-id
./scripts/aionctl.sh freeze list
```

`aionctl versioning` and `aionctl freeze` call `client.versioning`. They produce
metadata-only local release records and never execute shell scripts, domain
modules, optional adapters, or external services.

## Release Package Commands

```bash
./scripts/aionctl.sh release package --version 0.1.0 --dry-run
./scripts/aionctl.sh release package --version 0.1.0 --write
./scripts/aionctl.sh release package get --id release-package-id
./scripts/aionctl.sh release package list
./scripts/aionctl.sh release package validate --id release-package-id
./scripts/aionctl.sh release package handoff --id release-package-id
```

`aionctl release` calls `client.release`. It creates local package records and
handoff reports only. It does not upload artifacts, call package registries,
execute Docker, or enable domain modules.
