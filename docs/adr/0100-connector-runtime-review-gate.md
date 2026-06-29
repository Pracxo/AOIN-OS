# 0100: Connector Runtime Review Gate

## Status

Accepted.

## Context

AION-106 defined the external connector boundary and AION-108 added a disabled connector prototype. A stable safety baseline is required before future connector runtime work can begin.

## Decision

Add a connector runtime review gate.

The connector runtime remains disabled after AION-109.

External calls, credential storage, token storage, route registration, and connector activation remain blocked.

Future connector implementation requires pre-implementation gate evidence and explicit architecture review.

## Reason

AION needs a stable connector safety baseline before implementation phases.

## Consequence

Future connector tasks must pass connector runtime review and no-external-call regression.

## Constraints

- no network calls
- no credentials or tokens
- no SDK dependencies
- no privileged bypass
- no API router addition
- no migration
- no package manager files
