# 0096: Module Activation Design Review Gate

## Status

Accepted.

## Context

AION Brain v0.1.0 is frozen and tagged. Post-v0.1 module work has added
metadata-only extension intake, module slots, capability bindings,
conformance, readiness, activation request records, runtime registration
previews, module mock runtime evidence, and read-only operator review. None of
those surfaces enable real activation.

AION needs a stable module and plugin safety baseline before future
implementation phases can propose code loading, package installation, runtime
registration, capability activation, or controlled execution.

## Decision

Add a module activation design review gate for AION-105.

Activation remains disabled after AION-105.

Code loading, package installation, runtime registration, capability
activation, and controlled execution remain blocked.

Future activation work requires pre-gate evidence and explicit architecture
review.

## Reason

AION needs a stable module/plugin safety baseline before implementation phases.
The baseline must be visible in docs, examples, regression scripts, and
operator evidence before any future activation implementation can be reviewed.

## Consequences

Future activation tasks must pass module activation design review and no-go
regression checks before implementation work starts.

The AION-105 gate becomes a release blocker for future module/plugin work if
it fails.

## Constraints

- no code loading
- no package installation
- no runtime registration
- no privileged bypass
- no capability activation
- no controlled execution
- no external dependency download
- no executable payload acceptance
