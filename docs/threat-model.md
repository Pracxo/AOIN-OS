# Generic AION Threat Model

AION v0.1 uses a generic local threat model for Brain core. The model focuses
on contract safety, fail-closed policy behavior, adapter boundaries, execution
control, redaction, release safety, and deterministic local operations.

## Assets

- Brain public API contracts.
- Policy requests and decisions.
- Event, command, trace, audit, memory, evidence, and telemetry records.
- Secret reference metadata.
- Connector metadata.
- Sandbox profiles and run records.
- Backup and release package metadata.
- Local configuration and dependency metadata.

## Trust Boundaries

- Public API boundary.
- Policy engine boundary.
- Adapter boundary for model, memory, MCP, observability, workflow, and storage.
- Sandbox control boundary.
- Secret reference boundary.
- Release and backup artifact boundary.
- SDK and CLI boundary.

## Core Risks

- API error leakage.
- Raw secret storage.
- External model exfiltration.
- Uncontrolled tool execution through optional protocols.
- Future sandbox escape risk.
- Backup sensitive data leakage.
- Release package secret leakage.
- Unintended autonomy.
- Policy fail-open behavior.
- Provider object leakage.
- Connector uncontrolled egress.
- Ungoverned recall.
- Evidence grounding bypass.
- Command replay duplicate effects.
- Outbox duplicate delivery.
- Restore overwrite risk.

## Default Controls

- API error contracts do not expose stack traces.
- API request audit does not store bodies.
- Policy failures fail closed.
- Full autonomy is not default.
- Sandbox execution is disabled by default.
- Secrets are metadata-only.
- Connectors are metadata-only.
- Backups use redaction by default.
- Release packages exclude `.env` files.
- Optional adapters are disabled by default.
- MCP is disabled by default.
- External model use is disabled by default.
- Restore apply is disabled by default.
- Command idempotency is supported.
- Outbox processing is manual by default.

## Residual Risk

The residual risk in v0.1 is local development risk. The baseline improves
inspectability and repeatability, but it is not production security automation
and does not replace external review before deployment.

## v0.1 Limitations

The threat model is generic and Brain-only. It does not include cloud posture,
external scanner results, production auth assurances, or domain compliance
logic. Future domain policies must live outside Brain core.
