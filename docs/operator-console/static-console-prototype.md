# Static Console Prototype

## Purpose

AION-089 adds a static local Operator Console prototype. It previews how an
operator can inspect AION Brain state through existing read-only view-model
contracts without adding a production UI or a new runtime subsystem.

## Why static prototype

The prototype validates layout, data rendering, unavailable states, redaction,
and local API connection behavior before any frontend architecture is approved.
It uses plain HTML, CSS, and JavaScript so there is no frontend dependency and
no build step.

## What it demonstrates

- Existing read-only Operator Console view models can drive dashboard panels.
- Localhost-only API access can be guarded in the browser.
- Offline demo JSON can keep the preview useful when the Brain API is down.
- Forbidden actions can be shown as descriptors without creating controls.
- Redaction runs before display for sensitive key names and token-like values.

## What it does not do

The prototype does not provide production auth, write actions, activation,
external calls, module or capability execution, provider enablement, runtime
configuration mutation, route registration, or privileged bypasses.

## How to run locally

Open the file directly:

```bash
open operator-console-static/index.html
```

Serve the static directory locally:

```bash
python3 -m http.server 8090 --directory operator-console-static
open http://localhost:8090
open "http://localhost:8090?api=http://localhost:8080"
```

Run the static guards:

```bash
./scripts/operator-console-static-check.sh
./scripts/operator-console-static-demo.sh --offline-ok --skip-api
```

## API fallback behavior

The default API base is `http://localhost:8080`. The page accepts an `api`
query parameter, but the script only accepts `localhost` or `127.0.0.1`
origins. Non-local origins are blocked and the console falls back to local demo
JSON.

When the API is available, the prototype only sends a `POST` request to
`/brain/operator-console/view-model`. When that request fails or is skipped,
demo JSON renders the same read-only shape.

## Data safety model

The page redacts dangerous keys before rendering. The protected names include
raw prompt fields, hidden reasoning fields, chain-of-thought fields,
password-like values, token-like values, API key-like values, credential-like
values, authorization-like values, and private key-like values.

Demo data is synthetic and keeps `read_only=true` and `redaction_applied=true`.

## Read-only boundaries

All action-like UI is disabled. Forbidden actions are descriptors only. The
prototype must not perform `PUT`, `PATCH`, or `DELETE` requests, must not store
user input, must not use `localStorage`, and must not call external domains.

## Future UI transition

A later UI milestone may reuse the view-model contracts, safety footer,
localhost guard, redaction list, unavailable-state rendering, and descriptor
model. That future work still requires explicit architecture approval before
adding a framework, auth model, write path, or governed action flow.

## AION-092 operator actions panel

The static console includes an Operator Actions panel backed by local demo
JSON. The panel renders dry-run request previews, blocked effects, blockers,
and review state. It does not add package files, build tooling, activation,
external calls, or an execution path.

## No-go conditions

- A frontend dependency or build tool is introduced.
- A non-local API origin is accepted.
- A write method is added.
- Activation controls are enabled.
- External calls are made.
- Raw prompts, hidden reasoning, credentials, or secret-like fields are shown.
- The prototype claims production readiness or production auth.
