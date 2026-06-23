# Operator Console Workflows

Each workflow defines the operator question, current CLI/API path, future
widgets, safe actions, blocked actions, and no-go conditions. AION-087 creates
workflow maps only; it adds no runtime UI.

## First-run readiness

Purpose: confirm the local system can start, inspect setup, run deterministic
checks, and produce an operator overview.

Operator question answered: can this local checkout be inspected safely?

Current CLI/API commands:

```bash
./scripts/setup-doctor.sh --fast --offline-ok
./scripts/seed-defaults.sh
./scripts/bootstrap-local.sh --fast
./scripts/golden-path.sh --offline-ok
./scripts/release-smoke.sh --offline-ok
./scripts/operator-overview.sh
```

Future UI widgets: setup status card, bootstrap findings table, Golden Path
result card, release-smoke summary, operator item list.

Safe actions: run setup doctor, seed local defaults, run bootstrap dry-run, run
Golden Path, run release smoke, acknowledge local findings.

Blocked actions: install packages, create production credentials, call external
services, execute tools, enable external model calls.

No-go conditions: setup critical blocker, failed health, failed readiness,
policy bypass risk, missing audit trail, secret display risk.

## Release candidate review

Purpose: review RC, evidence, freeze, and release-package dry-run state.

Operator question answered: is the candidate locally ready for operator review?

Current CLI/API commands:

```bash
./scripts/rc-check.sh --offline-ok
./scripts/rc-evidence.sh --offline-ok
./scripts/v0.1-final-verify.sh --offline-ok --skip-docker --skip-api
./scripts/v0.1-freeze.sh --offline-ok --skip-docker --skip-api
./scripts/package-release.sh --dry-run
```

Future UI widgets: RC matrix, evidence pack list, freeze result, release
package dry-run summary, no-go list.

Safe actions: run RC gate, inspect RC evidence, run freeze dry-run, run release
package dry-run, dismiss non-blocking findings with reason.

Blocked actions: push to main, move release tag, publish artifacts, bypass
freeze gates, claim production readiness.

No-go conditions: unresolved release blocker, failing RC gate, failing freeze
gate, missing evidence, unstable tag state.

## Module lifecycle review

Purpose: review the metadata-only module path without enabling activation.

Operator question answered: what blocks a module from governed activation?

Current CLI/API commands:

```bash
./scripts/module-pack-check.sh
./scripts/generic-knowledge-demo.sh --offline-ok --skip-api
./scripts/aionctl.sh --scope workspace:main extensions validate --manifest-file examples/demo/generic-extension-manifest.json
./scripts/aionctl.sh --scope workspace:main module-bindings validate --dry-run
```

Future UI widgets: extension intake card, module slot status, binding matrix,
conformance findings, readiness score, activation request, activation gate,
expected blocker list, mock-runtime dry-run result.

Safe actions: validate extension manifest, run binding validation, run
conformance dry-run, run readiness assessment, run activation gate dry-run, run
module mock invocation.

Blocked actions: activate module, activate capability, load code, install
package, register route, enable runtime registration, execute module code.

No-go conditions: activation toggle enabled, code loading enabled, package
installation enabled, runtime registration enabled, module lifecycle states
unclear.

## Provider readiness review

Purpose: inspect provider hardening posture without external calls.

Operator question answered: is a provider profile safe enough for later review?

Current CLI/API commands:

```bash
./scripts/model-provider-check.sh --offline-ok --skip-api
./scripts/aionctl.sh --scope workspace:main model-providers profiles
./scripts/aionctl.sh --scope workspace:main model-providers readiness
```

Future UI widgets: provider profile card, egress preview summary, dry-run
simulation result, readiness blockers, disabled external-call indicator.

Safe actions: run provider egress preview, run provider simulation, review
readiness blockers, create operator review record.

Blocked actions: collect credentials, enable provider, transmit prompts, call
external model providers, expose raw provider payloads.

No-go conditions: external calls enabled by default, raw prompt exposure risk,
secret display risk, provider readiness states unclear.

## Incident review

Purpose: inspect local notification, alert, incident, root-cause, and recovery
records.

Operator question answered: what happened, what is affected, and what review is
needed?

Current CLI/API commands:

```bash
./scripts/aionctl.sh --scope workspace:main notifications alerts
./scripts/aionctl.sh --scope workspace:main incidents list
```

Future UI widgets: notification feed, alert queue, incident timeline,
correlation group, root-cause candidates, recovery-review panel.

Safe actions: acknowledge notifications, dismiss non-blocking findings with
reason, create recovery review records.

Blocked actions: send external notifications, auto-remediate, mutate source
records, hard delete incident records.

No-go conditions: missing audit trail, hidden reasoning exposure, secret
display risk, external notification enabled by default.

## Registry/lifecycle integrity

Purpose: inspect resource registry, link validation, lifecycle evaluation, and
purge preview boundaries.

Operator question answered: are resource links and lifecycle actions reviewable
without destructive mutation?

Current CLI/API commands:

```bash
./scripts/aionctl.sh --scope workspace:main resources validate
./scripts/aionctl.sh --scope workspace:main lifecycle evaluate
./scripts/aionctl.sh --scope workspace:main lifecycle purge-preview
```

Future UI widgets: resource registry table, link validation findings,
lifecycle candidate list, retention status, purge preview summary.

Safe actions: run validation, run lifecycle evaluation, run purge preview,
create operator review records.

Blocked actions: hard delete records, mutate source records, bypass retention
policy, hide audit refs.

No-go conditions: hard delete enabled, lifecycle states unclear, policy bypass
risk, missing audit trail.

## AION-088 workflow extraction

AION-088 exposes workflow maps through
`GET /brain/operator-console/workflows`. The maps are read-only and describe
safe inspection order only. They add no runtime UI, no activation, no
execution, and no external calls.

Workflow sections must keep no raw prompt exposure, no hidden reasoning
exposure, and no secret exposure.

## AION-090 static module dashboard workflow

AION-090 makes the Module Lifecycle workflow visible in the static local
console. The workflow remains read-only:

```text
manifest -> intake -> slot -> bindings -> validation -> conformance
  -> readiness -> activation request -> activation gate -> blockers
  -> mock runtime -> operator review
```

The static panel shows safe blockers, synthetic mock runtime output, evidence
refs, and review checklist status. It does not add activation, execution,
runtime registration, write actions, external calls, or new API routes.

## AION-092 operator action workflow

The governed operator action workflow is:

```text
request -> redaction -> policy gate -> blockers -> preview -> review -> query
```

The workflow creates records only. It does not add an execution step.
