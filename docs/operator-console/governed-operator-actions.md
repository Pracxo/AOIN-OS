# Governed Operator Actions

AION-092 adds governed operator action requests as local dry-run records.

An operator action request records intent, target metadata, scope, redacted
payload hash, required policy actions, required approvals, evidence references,
blockers, preview reference, and review reference. It is not an execution
request.

Allowed operations:

- Create a dry-run request record.
- Create a dry-run preview.
- Create blocker records.
- Create review records.
- Query records within scope.
- Emit audit, provenance, and visual telemetry records.

Hard boundaries:

- `mode` is always `dry_run`.
- `execution_allowed` is always `false`.
- `external_calls_allowed` is always `false`.
- `activation_allowed` is always `false`.
- Approval is review context only.
- Blocker dismissal does not unlock execution.

Public APIs:

- `POST /brain/operator-actions/requests`
- `GET /brain/operator-actions/requests/{operator_action_request_id}`
- `GET /brain/operator-actions/requests`
- `POST /brain/operator-actions/requests/{operator_action_request_id}/preview`
- `GET /brain/operator-actions/previews`
- `GET /brain/operator-actions/blockers`
- `POST /brain/operator-actions/blockers/{operator_action_blocker_id}/dismiss`
- `POST /brain/operator-actions/requests/{operator_action_request_id}/review`
- `GET /brain/operator-actions/reviews`
- `POST /brain/operator-actions/query`

The Operator Console may render these records, but it must not convert them
into runtime writes.
