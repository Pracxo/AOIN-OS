# Disabled Connector Prototype

## Purpose

AION-108 adds a disabled external connector prototype for local design proof.
It validates synthetic mock connector metadata and produces status, egress
preview, ingress preview, blocker, and audit evidence.

This is not connector runtime. It does not call external services, resolve DNS,
store credentials, store tokens, register routes, activate capabilities,
execute tools, or bypass policy.

## Hard-Off State

The connector prototype is guarded by these default settings:

- `AION_CONNECTOR_RUNTIME_ENABLED=false`
- `AION_CONNECTOR_EXTERNAL_CALLS_ENABLED=false`
- `AION_CONNECTOR_CREDENTIALS_ENABLED=false`
- `AION_CONNECTOR_TOKEN_STORAGE_ENABLED=false`
- `AION_CONNECTOR_ACTIVATION_ENABLED=false`
- `AION_CONNECTOR_ROUTE_REGISTRATION_ENABLED=false`

The only enabled surfaces are local mock preview, egress preview, ingress
preview, and audit evidence.

## API Surface

- `GET /brain/connector-runtime/status`
- `POST /brain/connector-runtime/mock-manifest/validate`
- `POST /brain/connector-runtime/egress-preview`
- `POST /brain/connector-runtime/ingress-preview`
- `POST /brain/connector-runtime/audit`

These endpoints produce preview evidence only. They never create connector
runtime state or perform external egress.

## AION-109 Review Gate Relationship

AION-109 reviews this disabled prototype and freezes it as the current safe
state. The prototype remains preview-only and non-executing; future work must
pass the review gate before changing runtime behavior.
