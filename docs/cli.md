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

## Dialogue and Response Commands

```bash
./scripts/aionctl.sh dialogue start --title "Local session"
./scripts/aionctl.sh dialogue send --message "Remember this context" --remember
./scripts/aionctl.sh dialogue sessions
./scripts/aionctl.sh dialogue messages --session-id dialogue-session-id
./scripts/aionctl.sh dialogue clarifications
./scripts/aionctl.sh dialogue answer --clarification-id clarification-id --answer "Use the scoped goal."
./scripts/aionctl.sh responses get --response-id response-id
./scripts/aionctl.sh responses verify --response-id response-id
```

`aionctl dialogue` and `aionctl responses` call the public Brain API through
the SDK. They do not render a frontend chat UI, call provider chat APIs, send
external messages, expose hidden reasoning, or trigger controlled execution.

## Belief Commands

```bash
./scripts/aionctl.sh beliefs create --claim "A generic claim exists."
./scripts/aionctl.sh beliefs query --query "generic"
./scripts/aionctl.sh beliefs extract --text "A generic claim can be extracted."
./scripts/aionctl.sh beliefs contradictions
./scripts/aionctl.sh beliefs truth-maintenance run
./scripts/aionctl.sh beliefs truth-maintenance get --truth-run-id truth-run-id
```

`aionctl beliefs` calls `client.beliefs`. It creates, queries, extracts, and
maintains local belief records through Brain APIs only. It does not call
external fact-checking services, model providers, frontend renderers, or
domain-specific modules.

## Concept and Entity Commands

```bash
./scripts/aionctl.sh concepts create --name "Generic Concept" --description "A generic concept."
./scripts/aionctl.sh concepts list --query "generic"
./scripts/aionctl.sh entities create --name "Canonical Reference"
./scripts/aionctl.sh entities query --query "Canonical"
./scripts/aionctl.sh entities extract-mentions --text "Use [[Canonical Reference]]."
./scripts/aionctl.sh entities resolve --text "AION Brain uses memory governance"
./scripts/aionctl.sh entities references --entity-id entity-id
./scripts/aionctl.sh entities merge propose --primary entity-1 --duplicate entity-2 --reason "same generic reference"
./scripts/aionctl.sh entities merge approve merge-proposal-id --reason "approved" --approved
./scripts/aionctl.sh entities split propose --entity-id entity-1 --reason "too broad"
```

`aionctl concepts` and `aionctl entities` call the SDK only. Entity resolution
defaults to dry-run. Merge and split approvals require explicit operator input.
The CLI does not call external NLP services, model providers, image
identification services, or domain-specific modules.
## Decision Commands

- `aionctl decisions frame create`
- `aionctl decisions frames`
- `aionctl decisions option add`
- `aionctl decisions evaluate`
- `aionctl decisions recommend`
- `aionctl decisions counterfactual run`
- `aionctl decisions journal record`
- `aionctl decisions journal list`

Evaluation and counterfactual commands default to dry-run behavior. Journal
commands record a decision only; they do not execute the selected option.

## Outcome Commands

- `aionctl outcomes create`
- `aionctl outcomes query`
- `aionctl outcomes expected add`
- `aionctl outcomes observed add`
- `aionctl outcomes verify`
- `aionctl outcomes feedback list`
- `aionctl outcomes feedback resolve`
- `aionctl outcomes learning-bridge`

Outcome commands call the SDK and public Brain APIs only. Verification defaults
to deterministic local checks. The learning bridge defaults to dry-run and
does not promote skills, execute remediation, or call external services.

## Learning Commands

- `aionctl learning experiences create`
- `aionctl learning experiences get`
- `aionctl learning experiences query`
- `aionctl learning patterns mine`
- `aionctl learning patterns list`
- `aionctl learning lessons list`
- `aionctl learning synthesize`
- `aionctl learning skill-suggestions list`
- `aionctl learning skill-suggestions accept`
- `aionctl learning skill-suggestions reject`
- `aionctl learning skill-suggestions convert`
- `aionctl learning regression-suggestions list`
- `aionctl learning regression-suggestions accept`
- `aionctl learning regression-suggestions reject`

Learning commands are review-only. They do not promote skills, create active
procedures, create regression cases, modify source code, or call external
services.

## Self Model Commands

- `aionctl self describe`
- `aionctl self capabilities`
- `aionctl self capabilities refresh`
- `aionctl self limitations`
- `aionctl self limitations seed`
- `aionctl self confidence calibrate`
- `aionctl self assessment run`
- `aionctl self introspection create`
- `aionctl self introspection list`

Self-model commands call the SDK only. They describe local AION capability
awareness, limitations, confidence calibration, self-assessment, and
introspection records without executing capabilities, enabling adapters,
changing runtime config, or calling external services.

## Explanation Commands

- `aionctl explain target`
- `aionctl explain why-not`
- `aionctl explain trace`
- `aionctl explain verify`
- `aionctl explain feedback`

Explanation commands call the SDK and public Brain APIs only. They build
deterministic public explanations and trace narratives from observable records.
They do not reveal chain-of-thought, raw prompts, raw headers, secrets, or
provider payloads.
