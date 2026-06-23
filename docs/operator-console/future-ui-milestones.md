# Future UI Milestones

AION-087 remains CLI/API-first. Future console work should proceed only through
explicit milestones.

## AION-088

Operator Console API contract audit and view-model extraction.

Status: implemented as a backend-only read-only contract layer. It adds no
runtime UI, no activation, no execution, no raw prompt exposure, no hidden
reasoning exposure, and no secret exposure.

## AION-089

Static local console prototype, no auth claim, no writes by default.

Status: implemented as a local static prototype over existing read-only
view-model contracts. It uses no frontend dependency, no build step, no
production auth claim, no activation, no execution, and no external calls.

## AION-090

Read-only module lifecycle dashboard after UI architecture approval.

Status: implemented as a static local Module Lifecycle Dashboard inside the
AION-089 prototype. It remains no-build, read-only, metadata-only,
activation-blocked, execution-blocked, and offline-demo capable.

## AION-091

Read-only provider hardening dashboard.

## AION-092

Governed operator actions, dry-run only.

Status: implemented as backend dry-run request records, preview records,
blocker records, review records, SDK and CLI dry-run access, and a static
console preview panel. It remains no-execution and no-activation.

## AION-093

Local auth design.

Status: implemented as design docs, examples, threat model, access matrix,
and auth no-go conditions only. It adds no production auth, no credentials, no
external identity provider, no login endpoint, no real sessions, and no
runtime auth code.

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
