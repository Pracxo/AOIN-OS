# 0208: Final v0.2.0-rc.1 Candidate Evaluation and GitHub Prerelease Publication

## Status
Accepted

## Context
AION-243 produced a deterministic local `aion-v0.2.0-rc.1` candidate from source commit `d35f1caa234d35dce1dfc0a80bc4c8e327a8373e` and retained the bundle and local image pending final evaluation.

## Decision
AION-244 evaluates the retained candidate with 32 hard gates. On PASS, it closes `AION-242-V02RQ-0003` as consumed by AION-243 and creates `AION-244-V02REL-0001` as the single active, single-use authorization for one annotated `aion-v0.2.0-rc.1` tag and one GitHub prerelease.

The annotated tag must target the candidate source commit, not the evidence, merge, authorization, or reconciliation commits.

## Consequences
The RC1 prerelease may be published only after the authorization PR merges with green CI. Stable v0.2.0 publication, production deployment, registry push, public package upload, and promotion remain prohibited. A reconciliation PR must record the actual tag, release, asset verification, and authorization closeout.
