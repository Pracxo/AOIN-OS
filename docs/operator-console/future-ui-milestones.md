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

## AION-091

Read-only provider hardening dashboard.

## AION-092

Governed operator actions, dry-run only.

## AION-093

Local auth design.

## AION-094

UI release gate.
