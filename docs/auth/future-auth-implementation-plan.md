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

## AION-094 Completed Scope

AION-094 completes the safe local contract and simulation step only. It does
not move production auth forward. Production authentication remains blocked
until the later architecture decision and gated prototype milestones.

## AION-095 Future Session Prerequisites

Read-only local session previews do not unlock production auth. Any future
production session implementation still requires a separate ADR, threat model,
policy update, credential and token handling decision, browser-state security
review, and migration approval.

## AION-096 Future Role Filtering Prerequisites

Role-aware filtering is still not production authorization. Future auth work
must decide how real identities map into the proof matrix without bypassing
policy, audit, redaction, or the forbidden-action guarantees.

## AION-097 Future Write Authorization Prerequisite

Future production or write authorization must extend the AION-097 dry-run model
instead of bypassing it. Real identity, session, and policy decisions must keep
denied decisions visible and must not weaken no-execution, no-activation,
no-external-call, and no-credential-storage guarantees.
