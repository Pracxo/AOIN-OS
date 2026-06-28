# Dry-Run Action Authorization

AION-097 adds a dry-run authorization gate in front of governed operator action
requests, previews, and reviews.

The gate evaluates:

- local roles from the local auth context
- local session boundary metadata
- the role permission matrix
- policy action `action_authorization.dry_run.authorize`
- action type and target type
- dry-run mode
- unsafe payload findings

Allowed decisions can create a dry-run preview or review record only. They do
not grant writes, execution, activation, external calls, or controlled handoff.

Denied decisions stay visible through authorization blockers and operator
action metadata. Preview is not execution, review is not execution, and
authorization is not execution.
