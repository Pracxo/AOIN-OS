# Operator Console View Model Contract

AION-088 adds read-only Operator Console view models. These contracts summarize
existing Brain state for future UI consumers without adding a runtime UI.

## Contracts

`ConsoleViewModelRequest` selects a view and owner scope. Scope is mandatory so
policy can evaluate the read request.

`ConsoleViewModel` returns:

- a stable view id
- view status
- read-only sections
- global descriptor-only actions
- forbidden action descriptors
- data-source metadata
- redaction status
- safety findings

`ConsoleViewSection` contains status, severity, summaries, safe items, blockers,
warnings, refs, data sources, and descriptors. Sections may be `unavailable`
when optional services are absent.

## Required Boundaries

- read-only
- no runtime UI
- no raw prompt exposure
- no hidden reasoning exposure
- no secret exposure
- no activation
- no execution
- no source mutation
- no external calls

The contract is frontend-agnostic. Future UI code must render these contracts
without creating privileged control paths.
