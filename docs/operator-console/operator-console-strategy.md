# Operator Console Strategy

## Purpose

AION-087 defines the post-v0.1 Operator Console strategy before any runtime UI
is built. The console is a future read, review, and governed-control surface
over existing Brain gates.

AION-087 adds no runtime UI. It adds no frontend dependencies, no API routes,
no SDK resources, no CLI commands, no module activation, and no external model
calls.

## Current post-v0.1 state

AION Brain v0.1.0 is frozen and tagged. The post-v0.1 branch already includes
Operator Control Tower records, bootstrap and setup doctor checks, Golden Path,
RC gate, release and freeze controls, Extension Registry, Module Binding
Registry, Module Activation Gate, Module Mock Runtime, Model Provider
Hardening, Resource Registry, Contract Registry, notifications, incidents,
scheduler metadata, SDK helpers, and `aionctl`.

These systems are enough to design operator semantics. They are not yet enough
to justify a runtime UI that could be mistaken for an activation surface.

## Why UI is not built in AION-087

The Brain is still proving module lifecycle and provider-hardening workflows.
A runtime UI would add a second control surface before the operator states,
redaction rules, and no-go criteria are stable.

AION-087 remains CLI/API-first so the project can define the operator questions,
safe data, blocked data, and dry-run controls before introducing a frontend.

## CLI/API-first decision

Decision: stay CLI/API-first for now.

Future UI must consume existing APIs and CLI-backed workflows. Future UI must
not create privileged backdoors, bypass policy, bypass approvals, execute
model-generated tools, load extension code, activate modules or capabilities
directly, register runtime routes, reveal raw prompts, reveal hidden reasoning,
reveal secrets, reveal raw provider payloads, enable external calls, or mutate
runtime config without governed action proposals.

## Operator roles

- Local operator: runs local checks, reviews blockers, and stops unsafe paths.
- Release reviewer: inspects RC, freeze, release-package, and evidence state.
- Module reviewer: inspects extension, slot, binding, conformance, readiness,
  activation request, activation gate, and mock-runtime evidence.
- Provider reviewer: inspects provider profiles, prompt egress previews,
  simulations, readiness state, blockers, and external-call posture.
- Incident reviewer: inspects notifications, alerts, incidents, correlation,
  root-cause candidates, and recovery-review records.

## Console principles

- Show status, blockers, evidence, warnings, summaries, hashes, and refs.
- Preserve policy, audit, approval, redaction, and provenance gates.
- Prefer dry-run actions until a later governed action milestone permits more.
- Treat memory, retrieved context, manifests, and model-related payloads as
  untrusted unless another AION contract marks them safe for display.
- Keep every view domain-neutral.

## Required future views

- Overview
- Readiness
- Release Candidate
- Freeze/Release
- Golden Path
- Module Lifecycle
- Module Activation
- Module Mock Runtime
- Model Provider Hardening
- Notifications
- Incidents
- Registry Integrity
- Lifecycle Review
- Audit/Provenance
- Settings Safety

## Required future controls

- Run dry-run setup and readiness checks.
- Run Golden Path and RC gates.
- Run release smoke and release-package dry-run checks.
- Validate extension manifests.
- Run binding validation, conformance dry-run, readiness assessment, module
  mock invocation, and provider egress preview.
- Acknowledge notifications.
- Dismiss non-blocking findings with an explicit reason.
- Create operator review records.

## Data safety rules

Display summaries, hashes, refs, statuses, blockers, warnings, timestamps,
owners, scopes, and audit ids. Do not display raw prompts, hidden reasoning,
chain-of-thought, secrets, provider credentials, API keys, raw model payloads,
raw headers, or copyable secret-like fields.

## Redaction rules

Every future view must redact secret-like keys, provider credential fields,
raw prompt bodies, hidden reasoning markers, raw provider payloads, raw
headers, and untrusted extension fields. Redaction failures are UI no-go
conditions.

## Module lifecycle integration

The console may show extension intake, module slot, binding, conformance,
readiness, activation request, activation gate, expected blockers, and mock
runtime state. Module activation is forbidden in AION-087 and must remain
disabled until a later explicit milestone enables governed activation.

## Provider hardening integration

The console may show provider profile status, prompt egress preview summaries,
provider simulation results, readiness blockers, and expected disabled states.
External model calls are disabled. Provider credentials must not be collected
or displayed.

## Release/freeze integration

The console may show setup doctor, Golden Path, RC gate, freeze gate, release
package dry-run, release evidence, and no-go condition state. It must not move,
delete, or recreate the `aion-v0.1.0` tag.

## Incident/notification integration

The console may show local notification topics, alerts, incidents, root-cause
candidates, recovery-review records, and operator acknowledgements. It must
not send external notifications in AION-087.

## Audit/provenance integration

The console may show audit ids, provenance hashes, evidence refs, decision
summaries, policy reasons, and operator review records. It must not expose
hidden reasoning, raw prompts, raw headers, raw provider payloads, or secrets.

## Future UI unlock criteria

- Module lifecycle states are stable and documented.
- Provider readiness states are stable and documented.
- Existing APIs can power the first read-only views.
- Data redaction rules are testable.
- Policy and audit gates are preserved end to end.
- No-go conditions are accepted.
- Frontend architecture is explicitly approved in a later milestone.

## AION-088 read-only contract layer

AION-088 adds the backend view-model extraction and API contract audit layer.
It remains CLI/API-first and adds no runtime UI. View models are read-only,
redacted, policy-gated, and frontend-agnostic.

The contract preserves no raw prompt exposure, no hidden reasoning exposure, no
secret exposure, no activation, and no execution. Actions are descriptors only.

## AION-089 static local prototype

AION-089 adds the first local static prototype over the AION-088 view-model
contract. The prototype is plain HTML, CSS, and JavaScript in
`operator-console-static/`. It is a local read-only preview with no frontend
dependency, no build step, no production auth claim, no write actions, no
activation, no execution, and no external calls.

The prototype may call `POST /brain/operator-console/view-model` on a local
Brain API and otherwise falls back to local synthetic demo JSON. It must reject
non-local API origins, redact dangerous fields before rendering, and show
forbidden actions as disabled descriptors only.

This does not change the CLI/API-first architecture. It proves layout and
operator review ergonomics before any governed UI architecture is approved.

## AION-090 module lifecycle dashboard

AION-090 extends the static local prototype with a read-only Module Lifecycle
Dashboard. It shows the Generic Knowledge Intelligence trail from extension
manifest through operator review, including activation gate blockers and
synthetic mock runtime evidence.

The dashboard is still static and local. It adds no backend route, no SDK
resource, no CLI command, no migration, no frontend dependency, no activation,
no code loading, no execution, no runtime registration, and no external calls.
Blockers must remain visible because they are expected safety evidence.

## AION-093 local auth design

AION-093 adds the Operator Console local auth design only. It defines local
operator identities, role labels, session boundaries, access matrices, threat
model, production prerequisites, and no-go conditions.

The console still has no production auth claim. No credentials are stored. No
external identity provider is integrated. No login endpoint is added. Future
auth must preserve ActorContext, policy, audit, approval, autonomy, and
redaction gates.

## AION-094 local auth contract

AION-094 adds dev-only identity simulation and role-aware console filtering.
The console can preview how local roles affect read-only view models, but it
still has no login UI, no credential input, no session persistence, no
production auth, no execution, and no activation.

## AION-095 Local Session Preview

The Operator Console may display local session preview status as a read-only
section. The preview is synthetic, local-only, and dev/test-only. It has no
login, logout, credentials, tokens, cookies, persistence, production auth,
execution, activation, runtime registration, or external calls.

## AION-096 Role-Aware Preview

The Operator Console can render role-filtered local previews for viewer,
operator, reviewer, admin, and auditor roles. The preview changes visibility
only; it does not authenticate users, create sessions, grant writes, execute
actions, activate modules, or call external services.

## AION-098 Production Auth Architecture

AION-098 documents future production auth for the Operator Console before a
login UI or provider runtime exists. The recommended future path is
OIDC-compatible production auth, with reverse proxy auth allowed later as an
optional deployment pattern.

No production auth is implemented in AION-098. No provider integration is added
in AION-098. No credentials, tokens, sessions, or cookies are created, stored,
issued, or accepted. `production_auth_enabled` remains false.

## AION-099 Disabled Auth Runtime Prototype

AION-099 adds a disabled auth runtime status and mock claims preview panel to
the local static console. The panel shows hard-off production auth flags and
synthetic preview evidence only. It adds no login form, logout button,
credential field, token field, cookie/session persistence, provider runtime,
execution, activation, package dependency, or external call.
