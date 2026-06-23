# First Governed Module Selection

## Purpose

AION-082 selects the first governed module class for post-v0.1 planning. The
selection is strategy and metadata only. No module runtime is implemented.

## Role Comparison

| Role | Priority | Selection pressure |
| --- | --- | --- |
| Platform architect | Protect Brain core boundaries | Prefer a module that plugs in through existing metadata, binding, conformance, and readiness gates |
| Security engineer | Minimize side effects | Prefer no tool execution, no external actions, no dynamic routes, and low data access |
| Release engineer | Preserve v0.1 baseline | Prefer a module that does not move the tag, change release semantics, or add runtime surface |
| Operator | Keep review practical | Prefer clear scope, clear risk, and visible rollback/disable posture |
| Product engineer | Demonstrate value | Prefer a module class that improves answers and explanations without executing actions |
| Developer experience owner | Prove the module path | Prefer a module that exercises manifests, bindings, conformance, readiness, and docs |

## Candidate Module Classes

| Candidate | Value | Side-effect risk | Activation complexity | Fit for first module |
| --- | --- | --- | --- | --- |
| Knowledge Intelligence | Retrieval, summary, grounding, explanation, answer support | Low | Low to medium | Best |
| Developer Assistance | Helps with code or build review using governed records | Medium | Medium | Later |
| Operations Review | Reviews status and runbooks | Medium | Medium | Later |
| Business Workflow Review | Reviews structured process records | Medium to high | Medium to high | Later |
| Infrastructure Planning | Plans infrastructure changes without executing them | High | High | Post-design |
| High-side-effect Regulated Workflow | Requires stronger controls and approvals | Critical | Critical | Not first |

## Decision

Select the first governed module as Generic Knowledge Intelligence Module.

## Reason

- Low side-effect risk.
- Uses evidence, memory, grounding, citations, response generation, prompt
  governance, model output governance, and registry.
- Does not need tool execution.
- Does not need external actions.
- Does not need controlled handoff.
- Demonstrates value without runtime activation risk.

The selected module remains metadata-only in AION-082.

## AION-084 Package Confirmation

AION-084 keeps the selection unchanged and creates the first governed module
package for Generic Knowledge Intelligence. The package is metadata-only and
uses the existing gates for intake, slot staging, capability binding,
conformance, readiness, activation request, blocker review, and operator
review.

No Brain core code, migration, API route, SDK resource, CLI command, runtime
registration, code loading, package installation, or external call is added by
the module pack.
