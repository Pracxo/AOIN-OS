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

## Model Output Commands

```bash
./scripts/aionctl.sh model-outputs create --raw-output "Generic answer"
./scripts/aionctl.sh model-outputs get --model-output-id model-output-id
./scripts/aionctl.sh model-outputs query
./scripts/aionctl.sh model-outputs govern --model-output-id model-output-id
./scripts/aionctl.sh model-outputs segments --model-output-id model-output-id
./scripts/aionctl.sh model-outputs validate-structured --model-output-id model-output-id
./scripts/aionctl.sh model-outputs candidates list
./scripts/aionctl.sh model-outputs candidates promote --response-candidate-id response-candidate-id
./scripts/aionctl.sh model-outputs tool-intents list
./scripts/aionctl.sh model-outputs tool-intents reject --tool-intent-id tool-intent-id
```

`aionctl model-outputs` calls `client.model_outputs`. It does not expose raw
provider payloads, execute model-suggested tools, or bypass policy.

## Action Proposal Commands

```bash
./scripts/aionctl.sh action-proposals create --payload-file proposal.json
./scripts/aionctl.sh action-proposals query
./scripts/aionctl.sh action-proposals review --action-proposal-id action-proposal-id --decision approve_for_handoff --approval-present
./scripts/aionctl.sh action-proposals handoff --action-proposal-id action-proposal-id --mode dry_run
./scripts/aionctl.sh action-proposals blockers
./scripts/aionctl.sh action-proposals handoffs
./scripts/aionctl.sh action-proposals tool-intent review --tool-intent-id tool-intent-id
```

`aionctl action-proposals` calls `client.action_proposals`. It does not
execute proposals, dispatch commands, run workflows, invoke capabilities, call
MCP tools, run sandboxes, approve actions, or call external systems. Handoff
defaults to `dry_run`.

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

## Instruction and Preference Commands

- `aionctl instructions create`
- `aionctl instructions list`
- `aionctl instructions resolve`
- `aionctl instructions conflicts`
- `aionctl preferences create`
- `aionctl preferences list`
- `aionctl preferences confirm`
- `aionctl preferences candidates`
- `aionctl style-profiles create`
- `aionctl style-profiles list`
- `aionctl style-profiles effective`

Instruction and preference commands call the SDK only. Preferences shape
responses and context; they do not override policy, autonomy, approvals,
runtime configuration, capability limits, sandbox limits, or grounding
requirements.

## Grounding Commands

- `aionctl grounding verify`
- `aionctl grounding map-response`
- `aionctl grounding map-text`
- `aionctl grounding citations`
- `aionctl grounding unsupported`
- `aionctl grounding coverage`

Grounding commands call the SDK and public Brain APIs only. They do not perform
web search, call model providers, extract citations with an LLM, invent
sources, expose raw prompts, or expose chain-of-thought.

## Prompt Governance Commands

- `aionctl prompts templates list`
- `aionctl prompts templates seed`
- `aionctl prompts fragments list`
- `aionctl prompts compile`
- `aionctl prompts preview`
- `aionctl prompts boundary-check`
- `aionctl prompts injection-findings`
- `aionctl prompts manifests`

Prompt commands call the SDK and public Brain APIs only. Preview defaults to
safe redaction. Commands do not print raw rendered prompts, hidden reasoning,
provider payloads, raw secrets, or domain prompt packs.

## Run Supervision Commands

- `aionctl run-supervision runs`
- `aionctl run-supervision sample`
- `aionctl run-supervision sample-many`
- `aionctl run-supervision control request`
- `aionctl run-supervision control handoff`
- `aionctl run-supervision timeout-policies`
- `aionctl run-supervision compensation propose`
- `aionctl run-supervision compensation list`
- `aionctl run-supervision report`

Run supervision commands call the SDK and public Brain APIs only. Control
handoff defaults to dry-run. Timeout policy evaluation does not auto-cancel.
Compensation planning and conversion do not execute actions.

## Notification Commands

- `aionctl notifications topics create`
- `aionctl notifications topics list`
- `aionctl notifications topics seed-defaults`
- `aionctl notifications subscriptions create`
- `aionctl notifications subscriptions list`
- `aionctl notifications publish`
- `aionctl notifications query`
- `aionctl notifications acknowledge`
- `aionctl notifications alerts create`
- `aionctl notifications alerts query`
- `aionctl notifications alerts acknowledge`
- `aionctl notifications alerts resolve`
- `aionctl notifications escalations policies`
- `aionctl notifications escalations policy-create`
- `aionctl notifications escalations evaluate`
- `aionctl notifications escalations list`
- `aionctl notifications digests create`
- `aionctl notifications digests list`

Notification commands call the SDK and public Brain APIs only. They record
local notifications, alerts, escalation records, and digests. They do not send
external notifications, call webhooks, send email/SMS/chat messages, mutate
source systems, auto-resolve source records, or expose hidden reasoning,
raw prompts, raw headers, provider payloads, or secrets.

## Scheduler Commands

- `aionctl scheduler schedules create`
- `aionctl scheduler schedules list`
- `aionctl scheduler schedules pause`
- `aionctl scheduler schedules resume`
- `aionctl scheduler due-items`
- `aionctl scheduler reminders create`
- `aionctl scheduler reminders list`
- `aionctl scheduler reminders acknowledge`
- `aionctl scheduler tick`
- `aionctl scheduler report`

Scheduler commands call the SDK and public Brain APIs only. Tick defaults to
`dry_run`. Commands do not start background workers, execute target actions,
call external calendars, send external reminders, mutate source records, or add
domain-specific scheduling behavior.

## Incident Commands

- `aionctl incidents signals create`
- `aionctl incidents signals list`
- `aionctl incidents create`
- `aionctl incidents query`
- `aionctl incidents acknowledge`
- `aionctl incidents resolve`
- `aionctl incidents rules list`
- `aionctl incidents rules seed-defaults`
- `aionctl incidents correlate`
- `aionctl incidents root-causes generate`
- `aionctl incidents recovery-review`

Incident commands call the SDK and public Brain APIs only. Correlation defaults
to `dry_run`. Commands do not call external incident systems, execute
remediation, mutate source records, acknowledge source records, resolve source
records, expose hidden reasoning, print raw prompts, or add domain-specific
incident behavior.

## Resource Registry Commands

- `aionctl registry query`
- `aionctl registry get`
- `aionctl registry upsert`
- `aionctl registry links`
- `aionctl registry link`
- `aionctl registry backlinks`
- `aionctl registry validate`
- `aionctl registry broken`
- `aionctl registry orphaned`
- `aionctl registry rebuild`
- `aionctl registry snapshot`
- `aionctl registry snapshots`

Registry commands call the SDK and public Brain APIs only. Validation and
rebuild commands default to dry-run. Commands do not repair source records,
mutate source lifecycle state, hard-delete source records, call external
services, expose hidden reasoning, print raw prompts, or add domain-specific
resource behavior.

## Data Lifecycle Commands

- `aionctl lifecycle seed-defaults`
- `aionctl lifecycle policies`
- `aionctl lifecycle create-policy`
- `aionctl lifecycle evaluate`
- `aionctl lifecycle classifications`
- `aionctl lifecycle archive-candidates`
- `aionctl lifecycle redaction-candidates`
- `aionctl lifecycle purge-preview`
- `aionctl lifecycle reviews`
- `aionctl lifecycle report`

Lifecycle commands call the SDK and public Brain APIs only. Evaluation defaults
to `dry_run`. Commands create policies, advisory classifications, candidates,
previews, reviews, and reports. They do not mutate source records, execute
archive, execute redaction, purge records, call object storage, call external
services, expose hidden reasoning, print raw prompts, or add domain-specific
retention behavior.

## Contract Registry Commands

- `aionctl contracts list`
- `aionctl contracts interfaces`
- `aionctl contracts snapshot`
- `aionctl contracts snapshots`
- `aionctl contracts rules`
- `aionctl contracts rules seed`
- `aionctl contracts scan`
- `aionctl contracts findings`
- `aionctl contracts migration-notes`
- `aionctl contracts report`

Contract commands call the SDK and public Brain APIs only. Scans default to
`dry_run`. Commands do not mutate source records, generate code, repair SDK or
CLI methods, execute migration steps, call external services, print raw
prompts, expose hidden reasoning, expose raw headers, or add domain-specific
compatibility logic.

## Module Binding Commands

- `aionctl module-slots create`
- `aionctl module-slots list`
- `aionctl capability-bindings create`
- `aionctl capability-bindings list`
- `aionctl module-bindings validate`
- `aionctl module-bindings conflicts`
- `aionctl module-bindings mount-plan`
- `aionctl module-bindings route-preview`
- `aionctl module-bindings query`

Module binding commands call the SDK and public Brain APIs only. Validation
defaults to `dry_run` and also accepts `--dry-run` explicitly. Commands create
metadata records, conflict records, non-executable mount plans, and route
previews only. They do not load extension code, install packages, activate
capabilities, register routes, mutate runtime configuration, execute mount
plans, call external services, print raw prompts, expose hidden reasoning, or
add domain-specific module behavior.

## Conformance Commands

The CLI exposes the local conformance harness through SDK calls:

```bash
aionctl conformance profiles
aionctl conformance profiles seed
aionctl conformance test-vectors
aionctl conformance test-vectors generate <capability-binding-id>
aionctl conformance run --capability-binding-id <capability-binding-id>
aionctl conformance findings
aionctl readiness assess --capability-binding-id <capability-binding-id>
aionctl readiness list
aionctl conformance query
```

These commands create or read conformance records only. They do not execute
package code, invoke capabilities, activate modules, or call external systems.
