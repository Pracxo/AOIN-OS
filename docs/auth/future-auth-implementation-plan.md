# Future Auth Implementation Plan

No production auth may be implemented before AION-098.

## AION-094

Local auth contract and dev-only identity simulation.

## AION-095

Read-only local session prototype.

## AION-096

Role-aware console view filtering.

## AION-097

Dry-run action authorization enforcement.

## AION-098

Production auth architecture decision.

## AION-099

Production auth prototype behind disabled flag.

## Gates

Every stage must preserve ActorContext, policy, audit, approval, autonomy, and
redaction boundaries. Any implementation that stores credentials, creates
production sessions, integrates an external identity provider, or exposes
login endpoints before its designated stage is blocked.
