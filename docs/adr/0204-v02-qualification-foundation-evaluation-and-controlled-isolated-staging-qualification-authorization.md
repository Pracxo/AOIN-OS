# ADR 0204: v0.2 Qualification Foundation Evaluation and Controlled Isolated Staging Qualification Authorization

Status: Accepted
Date: 2026-08-01
Task: AION-240

## Context

AION-239 implemented a disabled local v0.2 production-readiness qualification foundation and retained a release hold because staging and production evidence were absent.

## Decision

Accept `AION-V02RQPE-001` with the exact PASS decision and authorize `AION-240-V02RQ-0002` for AION-241 only. AION-241 may implement one controlled isolated local staging artifact build, staging deployment and rollback drill under the recorded no-public-egress, no-production and no-release boundary.

## Boundaries

AION-240 creates no AION-241 runtime source, build, deployment, release candidate, v0.2 tag or release. Public network access, DNS, registry login, registry pull, registry push, external IdP calls, production credentials, production tokens, production databases and production deployment remain disabled.

## Consequences

AION-238-V02RQ-0001 is closed, expired and non-reusable. AION-240-V02RQ-0002 is the sole active v0.2 Release Qualification authorization. AION-242 must independently evaluate any AION-241 staging evidence before release-candidate work can be considered.
