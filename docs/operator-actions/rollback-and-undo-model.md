# Rollback And Undo Model

## Purpose

AION-107 defines the future rollback and undo model for operator write actions
without implementing write execution or rollback execution.

## Rollback plan

Every future write intent must include a rollback plan before it can become
future_execution_ready. The plan must identify the target, pre-change evidence,
post-change verification, rollback trigger, rollback actor, rollback approval
requirement, and audit refs.

## Undo feasibility

Undo feasibility must be classified before approval:

- direct_undo_available
- compensating_action_required
- irreversible_requires_confirmation
- rollback_not_supported

`rollback_not_supported` is a no-go condition unless the action is explicitly
classified as irreversible and the release gate allows that class.

## Compensating action

When direct undo is unavailable, the future plan must describe a compensating
action. The compensating action is also governed, policy-gated, audited, and
reviewed. It must not silently run.

## Irreversible action classification

Irreversible actions require explicit classification, dual-control approval,
operator confirmation, target-drift check, dry-run parity evidence, and a
documented no-hard-delete posture.

## Confirmation model

A future confirmation must name the intent, target, irreversible class,
expected effect, blocked effect, rollback limitation, approval expiry, and
audit refs. Confirmation cannot bypass policy or approval.

## Audit refs

Rollback and undo evidence must reference the original intent, preview,
approval, policy decision, authorization decision, execution attempt, result,
rollback request, rollback result, and reviewer.

## No hard delete

No hard delete is allowed. Future delete-like operations must be soft-governed,
append-only, reversible when possible, and explicitly classified when
irreversible.

## No silent rollback

No silent rollback is allowed. Rollback is a governed operator action with its
own policy, approval, audit, and review trail.

## No-go conditions

- rollback plan absent
- undo feasibility absent
- irreversible action unclassified
- hard delete enabled
- silent rollback enabled
- compensating action bypasses policy
- rollback audit refs absent
